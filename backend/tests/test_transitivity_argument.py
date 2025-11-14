import pytest
import time
import json
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestTransitivityArgument:
    """Test the transitivity argument scenario with /argue and /ui-justify calls"""
    
    def test_transitivity_argument_scenario(self):
        """Test the exact scenario: /argue followed by two /ui-justify calls with transitivity argument"""
        
        # Create a session and conversation
        session_id = "test_session_transitivity"
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
        
        # Step 1: Call /argue - this adds the thesis as a proposition to the argument
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
        
        # Wait a bit for the first round of agents to complete
        time.sleep(5)
        
        # Get the current argument state after /argue
        results_response = client.get(
            f"/api/agents/results/{session_id}%3A{conversation_id}"
        )
        assert results_response.status_code == 200
        
        # Step 2: First /user-justify call - add "All elephants are mice"
        justify_data_1 = {
            "thesis": "Mice are large.",
            "counter_thesis": "Mice are small.",
            "presupposition": "",
            "assumptions": [],
            "argument": [{"symbol": "A", "proposition": "Mice are large.", "justifiers": [], "truth": "0.0", "valid": "0.0"}],
            "counter_argument": [],
            "loc": "argument",
            "index": 0,
            "proposition": "All elephants are mice."
        }
        
        justify_response_1 = client.post(
            f"/api/argument/user-justify?session_id={session_id}&conversation_id={conversation_id}",
            json=justify_data_1
        )
        assert justify_response_1.status_code == 200
        
        # Wait a bit for the second round of agents to complete
        time.sleep(5)
        
        # Step 3: Second /user-justify call - add "Elephants are large"
        justify_data_2 = {
            "thesis": "Mice are large.",
            "counter_thesis": "Mice are small.",
            "presupposition": "",
            "assumptions": [],
            "argument": [{"symbol": "A", "proposition": "Mice are large.", "justifiers": [], "truth": "0.0", "valid": "0.0"}],
            "counter_argument": [],
            "loc": "argument",
            "index": 0,
            "proposition": "Elephants are large."
        }
        
        justify_response_2 = client.post(
            f"/api/argument/user-justify?session_id={session_id}&conversation_id={conversation_id}",
            json=justify_data_2
        )
        assert justify_response_2.status_code == 200
        
        # Wait for all agents to complete (with timeout)
        max_wait_time = 60  # 60 seconds for multiple agent rounds
        wait_interval = 2  # Check every 2 seconds
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
        print(f"\nFinal Results for Transitivity Argument:")
        print(f"Builder results: {len(results_by_agent.get('builder', []))}")
        print(f"Formalizer results: {len(results_by_agent.get('formalizer', []))}")
        print(f"Content evaluator results: {len(results_by_agent.get('content_evaluator', []))}")
        print(f"Form evaluator results: {len(results_by_agent.get('form_evaluator', []))}")
        
        # Check the form evaluator result specifically
        form_evaluator_results = results_by_agent.get("form_evaluator", [])
        if form_evaluator_results:
            latest_form_result = form_evaluator_results[-1]
            print(f"\nLatest Form Evaluator Result:")
            print(f"Validity: {latest_form_result.get('data', {}).get('argument_validity', 'N/A')}")
            print(f"Logical Issues: {latest_form_result.get('data', {}).get('logical_issues', [])}")
            print(f"Recommendations: {latest_form_result.get('data', {}).get('recommendations', [])}")
        
        print("✅ Test passed - transitivity argument scenario completed successfully!") 