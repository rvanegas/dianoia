import pytest
import json
from unittest.mock import patch, MagicMock
from models.argument import ArgumentsWithStep, Step
from services.agent_coordinator import coordinator


class TestArgumentRemove:
    """Test that argument.remove() behaves the same before and after changes"""
    
    def test_remove_step_from_argument_with_justifiers(self):
        """Test removing a step that has justifiers and is referenced by other steps"""
        # Create an argument with multiple steps and justifiers
        argument_data = {
            "thesis": "Socrates is mortal",
            "counter_thesis": "Socrates is not mortal", 
            "presupposition": "",
            "assumptions": [],
            "argument": [
                Step(symbol="A", proposition="Socrates is a man", justifiers=[], truth="1.0", valid="1.0"),
                Step(symbol="B", proposition="All men are mortal", justifiers=["A"], truth="1.0", valid="1.0"),
                Step(symbol="C", proposition="Socrates is mortal", justifiers=["B"], truth="1.0", valid="1.0")
            ],
            "counter_argument": [],
            "loc": "argument",
            "index": 1,  # Remove step B (All men are mortal)
            "conversation_id": "test_session:1"
        }
        
        # Create the argument object
        args = ArgumentsWithStep(**argument_data)
        
        # Mock the coordinator to avoid actual agent queuing
        with patch.object(coordinator, 'queue_task') as mock_queue:
            # Call remove
            result = args.remove()
            
            # Verify the step was removed
            assert len(args.argument) == 2
            assert args.argument[0].symbol == "A"
            assert args.argument[1].symbol == "C"
            
            # Verify justifiers were properly transferred
            # Step C should now have justifiers ["A"] (B's justifiers) instead of ["B"]
            assert args.argument[1].justifiers == ["A"]
            
            # Verify the result structure (result is a JSON string)
            result_dict = json.loads(result)
            assert "argument" in result_dict
            assert len(result_dict["argument"]) == 2
            
            # Verify that argument state change was queued (twice - builder and content evaluator)
            assert mock_queue.call_count == 2
            
            # Verify the calls were made with correct parameters
            calls = mock_queue.call_args_list
            agent_types = [call[1]['agent_type'] for call in calls]
            assert 'builder' in agent_types
            assert 'content_evaluator' in agent_types
    
    def test_remove_step_from_argument_without_justifiers(self):
        """Test removing a step that has no justifiers"""
        argument_data = {
            "thesis": "Socrates is mortal",
            "counter_thesis": "Socrates is not mortal",
            "presupposition": "",
            "assumptions": [],
            "argument": [
                Step(symbol="A", proposition="Socrates is a man", justifiers=[], truth="1.0", valid="1.0"),
                Step(symbol="B", proposition="All men are mortal", justifiers=[], truth="1.0", valid="1.0"),
                Step(symbol="C", proposition="Socrates is mortal", justifiers=["A"], truth="1.0", valid="1.0")
            ],
            "counter_argument": [],
            "loc": "argument", 
            "index": 1,  # Remove step B (All men are mortal)
            "conversation_id": "test_session:1"
        }
        
        args = ArgumentsWithStep(**argument_data)
        
        with patch.object(coordinator, 'queue_task') as mock_queue:
            result = args.remove()
            
            # Verify the step was removed
            assert len(args.argument) == 2
            assert args.argument[0].symbol == "A"
            assert args.argument[1].symbol == "C"
            
            # Verify justifiers were not changed (B had no justifiers)
            assert args.argument[1].justifiers == ["A"]
            
            # Verify the result structure (result is a JSON string)
            result_dict = json.loads(result)
            assert "argument" in result_dict
            assert len(result_dict["argument"]) == 2
    
    def test_remove_step_from_assumptions(self):
        """Test removing a step from assumptions (should not transfer justifiers)"""
        argument_data = {
            "thesis": "Socrates is mortal",
            "counter_thesis": "Socrates is not mortal",
            "presupposition": "",
            "assumptions": [
                Step(symbol="A", proposition="Socrates is a man", justifiers=[], truth="1.0", valid="1.0"),
                Step(symbol="B", proposition="All men are mortal", justifiers=["A"], truth="1.0", valid="1.0")
            ],
            "argument": [],
            "counter_argument": [],
            "loc": "assumptions",
            "index": 1,  # Remove step B from assumptions
            "conversation_id": "test_session:1"
        }
        
        args = ArgumentsWithStep(**argument_data)
        
        with patch.object(coordinator, 'queue_task') as mock_queue:
            result = args.remove()
            
            # Verify the step was removed from assumptions
            assert len(args.assumptions) == 1
            assert args.assumptions[0].symbol == "A"
            
            # Verify the result structure (result is a JSON string)
            result_dict = json.loads(result)
            assert "assumptions" in result_dict
            assert len(result_dict["assumptions"]) == 1
    
    def test_remove_step_with_complex_justifier_transfer(self):
        """Test removing a step with complex justifier relationships"""
        argument_data = {
            "thesis": "Complex argument",
            "counter_thesis": "Counter argument",
            "presupposition": "",
            "assumptions": [],
            "argument": [
                Step(symbol="A", proposition="Premise A", justifiers=[], truth="1.0", valid="1.0"),
                Step(symbol="B", proposition="Premise B", justifiers=["A"], truth="1.0", valid="1.0"),
                Step(symbol="C", proposition="Premise C", justifiers=["A", "B"], truth="1.0", valid="1.0"),
                Step(symbol="D", proposition="Conclusion", justifiers=["C"], truth="1.0", valid="1.0")
            ],
            "counter_argument": [],
            "loc": "argument",
            "index": 2,  # Remove step C (Premise C)
            "conversation_id": "test_session:1"
        }
        
        args = ArgumentsWithStep(**argument_data)
        
        with patch.object(coordinator, 'queue_task') as mock_queue:
            result = args.remove()
            
            # Verify the step was removed
            assert len(args.argument) == 3
            assert args.argument[0].symbol == "A"
            assert args.argument[1].symbol == "B"
            assert args.argument[2].symbol == "D"
            
            # Verify justifiers were properly transferred
            # Step D should now have justifiers ["A", "B"] (C's justifiers) instead of ["C"]
            assert set(args.argument[2].justifiers) == {"A", "B"}
            
            # Verify the result structure (result is a JSON string)
            result_dict = json.loads(result)
            assert "argument" in result_dict
            assert len(result_dict["argument"]) == 3
    
    def test_remove_step_queues_argument_state_change(self):
        """Test that remove() queues argument state change"""
        argument_data = {
            "thesis": "Test thesis",
            "counter_thesis": "Test counter thesis",
            "presupposition": "",
            "assumptions": [],
            "argument": [
                Step(symbol="A", proposition="Step A", justifiers=[], truth="1.0", valid="1.0"),
                Step(symbol="B", proposition="Step B", justifiers=["A"], truth="1.0", valid="1.0")
            ],
            "counter_argument": [],
            "loc": "argument",
            "index": 1,
            "conversation_id": "test_session:1"
        }
        
        args = ArgumentsWithStep(**argument_data)
        
        with patch.object(coordinator, 'queue_task') as mock_queue:
            args.remove()
            
            # Verify that queue_task was called twice (once for builder, once for content evaluator)
            assert mock_queue.call_count == 2
            
            # Verify the calls were made with correct parameters
            calls = mock_queue.call_args_list
            agent_types = [call[1]['agent_type'] for call in calls]
            assert 'builder' in agent_types
            assert 'content_evaluator' in agent_types
            
            # Verify conversation_id was passed correctly
            for call in calls:
                assert call[1]['conversation_id'] == 'test_session:1'
    
    def test_remove_step_preserves_other_arguments(self):
        """Test that remove() doesn't affect other arguments (counter_argument)"""
        argument_data = {
            "thesis": "Test thesis",
            "counter_thesis": "Test counter thesis", 
            "presupposition": "",
            "assumptions": [],
            "argument": [
                Step(symbol="A", proposition="Step A", justifiers=[], truth="1.0", valid="1.0"),
                Step(symbol="B", proposition="Step B", justifiers=["A"], truth="1.0", valid="1.0")
            ],
            "counter_argument": [
                Step(symbol="X", proposition="Counter X", justifiers=[], truth="1.0", valid="1.0"),
                Step(symbol="Y", proposition="Counter Y", justifiers=["X"], truth="1.0", valid="1.0")
            ],
            "loc": "argument",
            "index": 1,
            "conversation_id": "test_session:1"
        }
        
        args = ArgumentsWithStep(**argument_data)
        
        # Store original counter_argument
        original_counter = args.counter_argument.copy()
        
        with patch.object(coordinator, 'queue_task'):
            result = args.remove()
            
            # Verify counter_argument was not affected
            assert len(args.counter_argument) == len(original_counter)
            assert args.counter_argument[0].symbol == original_counter[0].symbol
            assert args.counter_argument[1].symbol == original_counter[1].symbol
            assert args.counter_argument[1].justifiers == original_counter[1].justifiers
