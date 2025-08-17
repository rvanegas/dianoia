"""
Tests for Phase 1 Part 1: Input Normalization
Tests the Step model updates and normalized agent input schema.
"""

import pytest
from schemas.step import Step
from schemas.agent_input import AgentInput, AgentContext, TaskData, AgentMetadata, FilteredAgentInput


class TestStepModelUpdates:
    """Test the enhanced Step model with new attributes"""
    
    def test_step_with_new_attributes(self):
        """Test creating a Step with new rearchitecture attributes"""
        step = Step(
            symbol="A",
            proposition="Socrates is mortal",
            justifiers=[],
            truth="1.0",
            valid="1.0",
            valid_content="0.9",
            valid_formal="1.0",
            formalization="∀x(Mortal(x) → Socrates(x))"
        )
        
        assert step.symbol == "A"
        assert step.proposition == "Socrates is mortal"
        assert step.valid_content == "0.9"
        assert step.valid_formal == "1.0"
        assert step.formalization == "∀x(Mortal(x) → Socrates(x))"
    
    def test_step_backward_compatibility(self):
        """Test that Step maintains backward compatibility"""
        step = Step(
            symbol="B",
            proposition="All men are mortal",
            justifiers=["A"],
            truth="1.0",
            valid="1.0"
        )
        
        # New attributes should have default values
        assert step.valid_content is None
        assert step.valid_formal is None
        assert step.formalization is None
    
    def test_step_formalization_filtering(self):
        """Test filtering formalization from Step for content evaluation"""
        step = Step(
            symbol="C",
            proposition="Socrates is a man",
            justifiers=["B"],
            truth="1.0",
            valid="1.0",
            valid_content="0.95",
            valid_formal="1.0",
            formalization="Man(Socrates)"
        )
        
        # Test setting formalization to None for content evaluation
        step.formalization = None
        assert step.formalization is None
        assert step.proposition == "Socrates is a man"  # Content preserved


class TestNormalizedAgentInput:
    """Test the normalized agent input schema"""
    
    def test_agent_input_creation(self):
        """Test creating a normalized AgentInput"""
        context = AgentContext(
            assumptions=[
                Step(symbol="A", proposition="Background assumption", justifiers=[], truth="1.0", valid="1.0")
            ],
            argument=[
                Step(symbol="B", proposition="Main argument", justifiers=["A"], truth="0.8", valid="0.9")
            ],
            file_ids=["file1.pdf", "file2.pdf"]
        )
        
        task_data = TaskData(
            target_type="argument",
            target_content=None
        )
        
        metadata = AgentMetadata(
            triggered_by="user_action",
            trigger_source="proposition_added",
            ttl_seconds=3600
        )
        
        agent_input = AgentInput(
            conversation_id="conv_123",
            snapshot_id="snap_456",
            context=context,
            task_data=task_data,
            metadata=metadata
        )
        
        assert agent_input.conversation_id == "conv_123"
        assert agent_input.snapshot_id == "snap_456"
        assert len(agent_input.context.assumptions) == 1
        assert len(agent_input.context.argument) == 1
        assert len(agent_input.context.file_ids) == 2
    
    def test_filtered_input_for_content_evaluation(self):
        """Test creating filtered input for content evaluation agent"""
        # Create step with formalization
        step = Step(
            symbol="A",
            proposition="Test proposition",
            justifiers=[],
            truth="1.0",
            valid="1.0",
            formalization="Test formalization"
        )
        
        context = AgentContext(
            assumptions=[step],
            argument=[step],
            file_ids=[]
        )
        
        agent_input = AgentInput(
            conversation_id="conv_123",
            snapshot_id="snap_456",
            context=context,
            task_data=TaskData(target_type="argument"),
            metadata=AgentMetadata(triggered_by="user_action", trigger_source="test")
        )
        
        # Create filtered input for content evaluation
        filtered_input = FilteredAgentInput.for_content_evaluation(agent_input)
        
        # Formalization should be excluded
        assert filtered_input.context.assumptions[0].formalization is None
        assert filtered_input.context.argument[0].formalization is None
        # Content should be preserved
        assert filtered_input.context.assumptions[0].proposition == "Test proposition"
    
    def test_filtered_input_for_formal_evaluation(self):
        """Test creating filtered input for formal evaluation agent"""
        # Create steps with content and formalization
        step = Step(
            symbol="A",
            proposition="Test proposition",
            justifiers=["B"],
            truth="0.9",
            valid="0.95",
            valid_content="0.9",
            valid_formal="1.0",
            formalization="Test formalization"
        )
        
        context = AgentContext(
            assumptions=[step],
            argument=[step],
            file_ids=[]
        )
        
        agent_input = AgentInput(
            conversation_id="conv_123",
            snapshot_id="snap_456",
            context=context,
            task_data=TaskData(target_type="argument"),
            metadata=AgentMetadata(triggered_by="user_action", trigger_source="test")
        )
        
        # Create filtered input for formal evaluation
        filtered_input = FilteredAgentInput.for_formal_evaluation(agent_input)
        
        # All steps should be included (parallel to for_content_evaluation)
        assert len(filtered_input.context.assumptions) == 1
        assert len(filtered_input.context.argument) == 1
        
        # Content should be stripped out (parallel to for_content_evaluation)
        assert filtered_input.context.assumptions[0].proposition is None
        assert filtered_input.context.argument[0].proposition is None
        
        # Other attributes should be preserved
        assert filtered_input.context.assumptions[0].formalization == "Test formalization"
        assert filtered_input.context.assumptions[0].symbol == "A"
        assert filtered_input.context.assumptions[0].justifiers == ["B"]
        assert filtered_input.context.assumptions[0].truth == "0.9"
    

    
    def test_task_data_proposition_target(self):
        """Test task data with proposition target"""
        task_data = TaskData(
            target_type="proposition",
            target_content="Socrates is mortal"
        )
        
        assert task_data.target_type == "proposition"
        assert task_data.target_content == "Socrates is mortal"
    

    
    def test_filtered_agent_input_inheritance(self):
        """Test that FilteredAgentInput properly inherits from AgentInput"""
        # Create a base agent input
        context = AgentContext(
            assumptions=[Step(symbol="A", proposition="Test", justifiers=[], truth="1.0", valid="1.0")],
            argument=[],
            file_ids=[]
        )
        
        base_input = AgentInput(
            conversation_id="conv_123",
            snapshot_id="snap_456",
            context=context,
            task_data=TaskData(target_type="argument"),
            metadata=AgentMetadata(triggered_by="user_action", trigger_source="test")
        )
        
        # Test that FilteredAgentInput is an instance of AgentInput
        filtered_input = FilteredAgentInput.for_content_evaluation(base_input)
        assert isinstance(filtered_input, AgentInput)
        assert isinstance(filtered_input, FilteredAgentInput)
        
        # Test that all AgentInput attributes are preserved
        assert filtered_input.conversation_id == base_input.conversation_id
        assert filtered_input.snapshot_id == base_input.snapshot_id
        assert filtered_input.task_data == base_input.task_data
        assert filtered_input.metadata == base_input.metadata
    



if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
