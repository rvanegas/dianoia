import pytest
import time
import json
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestArgueEndpoint:
    """Test the /argue endpoint and verify agent results"""
    
    def test_argue_endpoint_produces_expected_agents(self):
        """Test that calling /argue produces builder, formalizer, content evaluator, and form evaluator results"""
        
        # Create a session and conversation
        session_id = "test_session_123"
        conversation_id = "1"
        
        # First, create a thesis
        thesis_data = {
            "thesis": "Mice are large.",
            "counter_thesis": "Mice are small.",
            "presupposition": "",
            "assumptions": [],
            "argument": [],
            "counter_argument": [],
            "proposition": "Mice are large."
        }
        
        thesis_response = client.post(
            f"/api/argument/theses?session_id={session_id}&conversation_id={conversation_id}",
            json=thesis_data
        )
        assert thesis_response.status_code == 200
        
        # Now call the argue endpoint - this will add the thesis as a proposition to the argument
        argue_data = {
            "thesis": "Mice are large.",
            "counter_thesis": "Mice are small.",
            "presupposition": "",
            "assumptions": [],
            "argument": [],
            "counter_argument": [],
            "loc": "argument"
        }
        
        argue_response = client.post(
            f"/api/argument/argue?session_id={session_id}&conversation_id={conversation_id}",
            json=argue_data
        )
        assert argue_response.status_code == 200
        
        # Wait for agents to complete (with timeout)
        max_wait_time = 30  # 30 seconds
        wait_interval = 1  # Check every second
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            # Get agent results
            results_response = client.get(
                f"/api/agents/results/{session_id}%3A{conversation_id}"
            )
            assert results_response.status_code == 200
            
            results_data = results_response.json()
            results_by_agent = results_data.get("results_by_agent", {})
            
            # Check if we have all expected agents
            builder_results = results_by_agent.get("builder", [])
            formalizer_results = results_by_agent.get("formalizer", [])
            content_evaluator_results = results_by_agent.get("content_evaluator", [])
            form_evaluator_results = results_by_agent.get("form_evaluator", [])
            
            print(f"Time {elapsed_time}s - Builder: {len(builder_results)}, Formalizer: {len(formalizer_results)}, Content Evaluator: {len(content_evaluator_results)}, Form Evaluator: {len(form_evaluator_results)}")
            
            # If we have all expected results, we're done
            if (len(builder_results) >= 1 and
                len(formalizer_results) >= 1 and
                len(content_evaluator_results) >= 1 and
                len(form_evaluator_results) >= 1):
                print("✅ All expected agents completed!")
                break
            
            time.sleep(wait_interval)
            elapsed_time += wait_interval
        
        # Final verification
        results_response = client.get(
            f"/api/agents/results/{session_id}%3A{conversation_id}"
        )
        assert results_response.status_code == 200
        
        results_data = results_response.json()
        results_by_agent = results_data.get("results_by_agent", {})
        
        # Assert we have the expected results
        assert len(results_by_agent.get("builder", [])) >= 1, "Builder should have at least one result"
        assert len(results_by_agent.get("formalizer", [])) >= 1, "Formalizer should have at least one result"
        assert len(results_by_agent.get("content_evaluator", [])) >= 1, "Content evaluator should have at least one result"
        assert len(results_by_agent.get("form_evaluator", [])) >= 1, "Form evaluator should have at least one result"
        
        # Print final results for debugging
        print(f"\nFinal Results:")
        print(f"Builder results: {len(results_by_agent.get('builder', []))}")
        print(f"Formalizer results: {len(results_by_agent.get('formalizer', []))}")
        print(f"Content evaluator results: {len(results_by_agent.get('content_evaluator', []))}")
        print(f"Form evaluator results: {len(results_by_agent.get('form_evaluator', []))}")
        
        print("✅ Test passed - all expected agents completed successfully!")
    
    def test_argue_endpoint_with_multiple_propositions(self):
        """Test with multiple propositions to ensure form evaluator is queued correctly"""
        
        # Create a session and conversation
        session_id = "test_session_multi"
        conversation_id = "1"
        
        # First, create a thesis
        thesis_data = {
            "thesis": "Socrates is mortal.",
            "counter_thesis": "Socrates is immortal.",
            "presupposition": "",
            "assumptions": [],
            "argument": [],
            "counter_argument": [],
            "proposition": "Socrates is mortal."
        }
        
        thesis_response = client.post(
            f"/api/argument/theses?session_id={session_id}&conversation_id={conversation_id}",
            json=thesis_data
        )
        assert thesis_response.status_code == 200
        
        # Now call the argue endpoint multiple times to add propositions
        argue_data = {
            "thesis": "Socrates is mortal.",
            "counter_thesis": "Socrates is immortal.",
            "presupposition": "",
            "assumptions": [],
            "argument": [],
            "counter_argument": [],
            "loc": "argument"
        }
        
        # Call argue endpoint multiple times
        for i in range(3):
            argue_response = client.post(
                f"/api/argument/argue?session_id={session_id}&conversation_id={conversation_id}",
                json=argue_data
            )
            assert argue_response.status_code == 200
            
            # Wait a bit between calls
            time.sleep(2)
        
        # Wait for agents to complete (with timeout)
        max_wait_time = 30  # 30 seconds
        wait_interval = 1  # Check every second
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            # Get agent results
            results_response = client.get(
                f"/api/agents/results/{session_id}%3A{conversation_id}"
            )
            assert results_response.status_code == 200
            
            results_data = results_response.json()
            results_by_agent = results_data.get("results_by_agent", {})
            
            # Check if we have all expected agents
            builder_results = results_by_agent.get("builder", [])
            formalizer_results = results_by_agent.get("formalizer", [])
            content_evaluator_results = results_by_agent.get("content_evaluator", [])
            form_evaluator_results = results_by_agent.get("form_evaluator", [])
            
            print(f"Time {elapsed_time}s - Builder: {len(builder_results)}, Formalizer: {len(formalizer_results)}, Content Evaluator: {len(content_evaluator_results)}, Form Evaluator: {len(form_evaluator_results)}")
            
            # For multiple propositions, we expect at least one of each agent type
            if (len(builder_results) >= 1 and
                len(formalizer_results) >= 1 and
                len(content_evaluator_results) >= 1 and
                len(form_evaluator_results) >= 1):
                print("✅ All expected agents completed for multiple propositions!")
                break
            
            time.sleep(wait_interval)
            elapsed_time += wait_interval
        
        # Final verification
        results_response = client.get(
            f"/api/agents/results/{session_id}%3A{conversation_id}"
        )
        assert results_response.status_code == 200
        
        results_data = results_response.json()
        results_by_agent = results_data.get("results_by_agent", {})
        
        # Assert we have the expected results (at least one of each)
        assert len(results_by_agent.get("builder", [])) >= 1, "Builder should have at least one result"
        assert len(results_by_agent.get("formalizer", [])) >= 1, "Formalizer should have at least one result"
        assert len(results_by_agent.get("content_evaluator", [])) >= 1, "Content evaluator should have at least one result"
        assert len(results_by_agent.get("form_evaluator", [])) >= 1, "Form evaluator should have at least one result"
        
        # Print final results for debugging
        print(f"\nFinal Results for Multiple Propositions:")
        print(f"Builder results: {len(results_by_agent.get('builder', []))}")
        print(f"Formalizer results: {len(results_by_agent.get('formalizer', []))}")
        print(f"Content evaluator results: {len(results_by_agent.get('content_evaluator', []))}")
        print(f"Form evaluator results: {len(results_by_agent.get('form_evaluator', []))}")
        
        print("✅ Test passed - all expected agents completed for multiple propositions!") 