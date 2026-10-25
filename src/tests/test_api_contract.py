"""
The published contract (schemas/api_results.py) against what dianoia really
returns.

fixtures/agents_results.json is a real GET /api/agents/results response,
recorded 2026-10-25 through mdc for a three-proposition argument (every agent
but name_generator, which only gen-name runs). The models forbid undeclared
fields, so an agent whose output changes fails here until the model and the
fixture are updated together — re-record by running one evaluation and saving
the final poll.
"""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from main import app
from schemas.api_results import AgentResultsResponse, EvaluateStarted

FIXTURE = Path(__file__).parent / "fixtures" / "agents_results.json"

client = TestClient(app)


def test_a_recorded_response_matches_the_contract():
    recorded = json.loads(FIXTURE.read_text())
    response = AgentResultsResponse.model_validate(recorded)
    assert response.tasks_complete
    # Each list is typed by its agent: the discriminator picked the right model.
    for agent_type, results in response.results_by_agent.items():
        for result in results:
            assert result.agent_type == agent_type


def test_evaluate_answers_with_the_ids_to_poll():
    EvaluateStarted.model_validate({"conversation_id": "x:mdc", "snapshot_id": "1"})


def test_the_routes_publish_their_responses():
    spec = client.get("/openapi.json").json()

    def published(path, method):
        # A model used in requests too is published as "<Name>-Output" here.
        content = spec["paths"][path][method]["responses"]["200"]["content"]
        name = content["application/json"]["schema"]["$ref"].rsplit("/", 1)[-1]
        return name.removesuffix("-Output")

    assert published("/api/agents/results", "get") == "AgentResultsResponse"
    assert published("/api/argument/evaluate", "post") == "EvaluateStarted"
    assert published("/api/argument/extract", "post") == "Arguments"
    assert published("/api/argument/audit", "post") == "AuditResult"
