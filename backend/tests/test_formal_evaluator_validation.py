import pytest
from fastapi.testclient import TestClient
from main import app
from schemas.step import Step, Formalization

client = TestClient(app)

class TestFormalEvaluatorValidation:
    def test_trigger_formal_evaluation_success(self):
        """Test successful formal evaluation trigger when all formalizations are endorsed"""
        test_data = {
            "assumptions": [],
            "argument": [
                {
                    "symbol": "A",
                    "proposition": "All men are mortal",
                    "justifiers": [],
                    "truth": "1.0",
                    "valid": "1.0",
                    "formalization": {
                        "ascii": "forall x. (P(x) -> Q(x))",
                        "json": {"type": "universal", "predicate": "P", "consequent": "Q"},
                        "endorsed": True
                    }
                },
                {
                    "symbol": "B",
                    "proposition": "Socrates is a man",
                    "justifiers": [],
                    "truth": "1.0",
                    "valid": "1.0",
                    "formalization": {
                        "ascii": "P(a)",
                        "json": {"type": "predicate", "name": "P", "args": [{"type": "constant", "name": "a"}]},
                        "endorsed": True
                    }
                },
                {
                    "symbol": "C",
                    "proposition": "Socrates is mortal",
                    "justifiers": ["A", "B"],
                    "truth": "1.0",
                    "valid": "1.0",
                    "formalization": {
                        "ascii": "Q(a)",
                        "json": {"type": "predicate", "name": "Q", "args": [{"type": "constant", "name": "a"}]},
                        "endorsed": True
                    }
                }
            ]
        }
        
        response = client.post("/api/agents/evaluate-form?conversation_id=test:1&snapshot_id=1", json=test_data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["message"] == "Formal evaluation agent triggered successfully"
        assert result["validated_steps"] == 3
        assert result["endorsed_formalizations"] == 3

    def test_trigger_formal_evaluation_missing_formalizations(self):
        """Test that formal evaluation fails when steps are missing formalizations"""
        test_data = {
            "assumptions": [],
            "argument": [
                {
                    "symbol": "A",
                    "proposition": "All men are mortal",
                    "justifiers": [],
                    "truth": "1.0",
                    "valid": "1.0",
                    "formalization": {
                        "ascii": "forall x. (P(x) -> Q(x))",
                        "json": {"type": "universal", "predicate": "P", "consequent": "Q"},
                        "endorsed": True
                    }
                },
                {
                    "symbol": "B",
                    "proposition": "Socrates is a man",
                    "justifiers": [],
                    "truth": "1.0",
                    "valid": "1.0"
                    # Missing formalization
                }
            ]
        }
        
        response = client.post("/api/agents/evaluate-form?conversation_id=test:1&snapshot_id=1", json=test_data)
        assert response.status_code == 400
        
        result = response.json()
        assert "Steps missing formalizations" in result["detail"]
        assert "B" in result["detail"]

    def test_trigger_formal_evaluation_unendorsed_formalizations(self):
        """Test that formal evaluation fails when formalizations are not endorsed"""
        test_data = {
            "assumptions": [],
            "argument": [
                {
                    "symbol": "A",
                    "proposition": "All men are mortal",
                    "justifiers": [],
                    "truth": "1.0",
                    "valid": "1.0",
                    "formalization": {
                        "ascii": "forall x. (P(x) -> Q(x))",
                        "json": {"type": "universal", "predicate": "P", "consequent": "Q"},
                        "endorsed": True
                    }
                },
                {
                    "symbol": "B",
                    "proposition": "Socrates is a man",
                    "justifiers": [],
                    "truth": "1.0",
                    "valid": "1.0",
                    "formalization": {
                        "ascii": "P(a)",
                        "json": {"type": "predicate", "name": "P", "args": [{"type": "constant", "name": "a"}]},
                        "endorsed": False  # Not endorsed
                    }
                }
            ]
        }
        
        response = client.post("/api/agents/evaluate-form?conversation_id=test:1&snapshot_id=1", json=test_data)
        assert response.status_code == 400
        
        result = response.json()
        assert "Formalizations not endorsed" in result["detail"]
        assert "B" in result["detail"]

    def test_trigger_formal_evaluation_mixed_issues(self):
        """Test that formal evaluation fails with multiple validation issues"""
        test_data = {
            "assumptions": [
                {
                    "symbol": "X",
                    "proposition": "Some assumption",
                    "justifiers": [],
                    "truth": "1.0",
                    "valid": "1.0"
                    # Missing formalization
                }
            ],
            "argument": [
                {
                    "symbol": "A",
                    "proposition": "All men are mortal",
                    "justifiers": [],
                    "truth": "1.0",
                    "valid": "1.0",
                    "formalization": {
                        "ascii": "forall x. (P(x) -> Q(x))",
                        "json": {"type": "universal", "predicate": "P", "consequent": "Q"},
                        "endorsed": False  # Not endorsed
                    }
                }
            ]
        }
        
        response = client.post("/api/agents/evaluate-form?conversation_id=test:1&snapshot_id=1", json=test_data)
        assert response.status_code == 400
        
        result = response.json()
        # Should report the first validation error it encounters
        assert "Steps missing formalizations" in result["detail"] or "Formalizations not endorsed" in result["detail"]
