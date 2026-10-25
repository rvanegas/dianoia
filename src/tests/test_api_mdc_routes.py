"""
Tests for the routes mdc uses: extract and evaluate, behind mdc's bearer token.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from services.agent_coordinator import coordinator

client = TestClient(app)

TOKEN = "test-mdc-token"
AUTH = {"Authorization": f"Bearer {TOKEN}"}

ARGUMENT = [
    {"symbol": "1", "proposition": "All humans are mortal.", "justifiers": [], "truth_score": "1.0"},
    {"symbol": "2", "proposition": "Socrates is a human.", "justifiers": [], "truth_score": "1.0"},
    {"symbol": "3", "proposition": "Socrates is mortal.", "justifiers": ["1", "2"], "truth_score": "1.0"},
]


class TestMdcToken:
    """The token dependency guards both routes"""

    def test_missing_token_is_rejected(self):
        with patch("config.MDC_TOKEN", TOKEN):
            response = client.post("/api/argument/extract", json={"text": "x"})
        assert response.status_code == 401

    def test_wrong_token_is_rejected(self):
        with patch("config.MDC_TOKEN", TOKEN):
            response = client.post("/api/argument/evaluate", json={"argument": ARGUMENT},
                                   headers={"Authorization": "Bearer wrong"})
        assert response.status_code == 401

    def test_non_bearer_scheme_is_rejected(self):
        with patch("config.MDC_TOKEN", TOKEN):
            response = client.post("/api/argument/extract", json={"text": "x"},
                                   headers={"Authorization": f"Basic {TOKEN}"})
        assert response.status_code == 401

    def test_unconfigured_token_refuses_everyone(self):
        # Refused by the route-wide caller check before extract's own, which
        # would answer 503: with no token configured nobody is mdc.
        with patch("config.MDC_TOKEN", None):
            response = client.post("/api/argument/extract", json={"text": "x"}, headers=AUTH)
        assert response.status_code == 401


class TestExtractEndpoint:
    """POST /api/argument/extract"""

    def test_returns_extracted_argument(self):
        extracted = {"argument": ARGUMENT}
        with patch("config.MDC_TOKEN", TOKEN), \
             patch("api.argument.extract_argument", return_value=extracted) as mock_extract:
            response = client.post("/api/argument/extract",
                                   json={"text": "Socrates is mortal because…", "max_props": 5},
                                   headers=AUTH)
        assert response.status_code == 200
        assert response.json() == extracted
        mock_extract.assert_called_once_with("Socrates is mortal because…", max_props=5)

    def test_failed_extraction_is_422(self):
        with patch("config.MDC_TOKEN", TOKEN), \
             patch("api.argument.extract_argument",
                   side_effect=ValueError("extraction produced no argument steps")):
            response = client.post("/api/argument/extract", json={"text": "hello"}, headers=AUTH)
        assert response.status_code == 422
        assert "no argument steps" in response.json()["detail"]


class TestEvaluateEndpoint:
    """POST /api/argument/evaluate"""

    def test_starts_agents_and_returns_poll_ids(self):
        with patch("config.MDC_TOKEN", TOKEN), \
             patch.object(coordinator, "react_to_user_argument_change") as mock_react:
            response = client.post("/api/argument/evaluate", json={"argument": ARGUMENT}, headers=AUTH)
        assert response.status_code == 200
        body = response.json()
        assert body["conversation_id"].endswith(":mdc")
        assert body["snapshot_id"] == "1"
        conversation_id, snapshot_id, argument_data = mock_react.call_args.args
        assert (conversation_id, snapshot_id) == (body["conversation_id"], body["snapshot_id"])
        assert [s.symbol for s in argument_data.argument] == ["1", "2", "3"]

    def test_each_call_gets_its_own_conversation(self):
        with patch("config.MDC_TOKEN", TOKEN), \
             patch.object(coordinator, "react_to_user_argument_change"):
            first = client.post("/api/argument/evaluate", json={"argument": ARGUMENT}, headers=AUTH)
            second = client.post("/api/argument/evaluate", json={"argument": ARGUMENT}, headers=AUTH)
        assert first.json()["conversation_id"] != second.json()["conversation_id"]

    def test_results_route_reports_completion(self):
        """mdc polls GET /api/agents/results until tasks_complete; it must be present"""
        response = client.get("/api/agents/results",
                              params={"conversation_id": "nothing-here:mdc", "snapshot_id": "1"},
                              headers=AUTH)
        assert response.status_code == 200
        assert response.json()["tasks_complete"] is True
