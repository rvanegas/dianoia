"""
Tests for the caller check every /api route has (api/auth.py): noesis's token, or a
person's noesis access token issued to Roxana, checked by asking noesis's /me; and
for CORS, which only the browser apps' origins pass.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api import auth
from conftest import NOESIS_AUTH
from main import app

client = TestClient(app)

ROXANA_CLIENT = "roxana"

ARGUMENT = [
    {"symbol": "1", "proposition": "All humans are mortal.", "justifiers": [], "truth_score": "1.0"},
    {"symbol": "2", "proposition": "Socrates is a human.", "justifiers": [], "truth_score": "1.0"},
    {"symbol": "3", "proposition": "Socrates is mortal.", "justifiers": ["1", "2"], "truth_score": "1.0"},
]

# What noesis's /me answers, by token; a token it does not know gets None (its 401).
ME = {
    "roxana-token": {"user": "rodvandur", "client": ROXANA_CLIENT},
    "thefloor-token": {"user": "rodvandur", "client": "thefloor"},
    "nobody-token": {"user": "", "client": ROXANA_CLIENT},
}


@pytest.fixture(autouse=True)
def noesis_configured(monkeypatch):
    import config
    monkeypatch.setattr(config, "NOESIS_URL", "https://noesis.example")
    monkeypatch.setattr(config, "NOESIS_CLIENT_IDS", [ROXANA_CLIENT])
    auth._me_cache.clear()
    with patch("api.auth._ask_noesis", side_effect=lambda token: ME.get(token)) as asked:
        yield asked


def audit(headers=None):
    # Deterministic and model-free, so a 200 here costs nothing.
    return client.post("/api/argument/audit", json={"argument": ARGUMENT}, headers=headers or {})


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


class TestCallers:
    def test_no_token_is_refused(self):
        assert audit().status_code == 401

    def test_noesis_token_is_accepted(self):
        assert audit(NOESIS_AUTH).status_code == 200

    def test_a_roxana_users_token_is_accepted(self):
        assert audit(bearer("roxana-token")).status_code == 200
        assert auth.require_caller("Bearer roxana-token") == auth.Caller(kind="user", name="rodvandur")

    def test_noesis_is_asked_once_a_minute(self, noesis_configured):
        audit(bearer("roxana-token"))
        audit(bearer("roxana-token"))
        assert noesis_configured.call_count == 1

    def test_agents_routes_need_a_caller_too(self):
        query = "conversation_id=s:c&snapshot_id=1"
        assert client.get(f"/api/agents/results?{query}").status_code == 401
        assert client.get(f"/api/agents/results?{query}", headers=bearer("roxana-token")).status_code == 200


class TestRefusedTokens:
    @pytest.mark.parametrize("token", ["thefloor-token", "nobody-token", "unknown-token"],
                             ids=["another client's", "no user", "unknown to noesis"])
    def test_is_refused(self, token):
        assert audit(bearer(token)).status_code == 401

    def test_user_tokens_refused_when_noesis_is_unconfigured(self, monkeypatch):
        import config
        monkeypatch.setattr(config, "NOESIS_URL", "")
        assert audit(bearer("roxana-token")).status_code == 401

    def test_noesis_down_is_not_a_bad_token(self, noesis_configured):
        noesis_configured.side_effect = auth.NoesisUnavailable("down")
        assert audit(bearer("roxana-token")).status_code == 503

    def test_user_tokens_cannot_reach_noesis_only_routes(self):
        response = client.post("/api/argument/extract", json={"text": "x"}, headers=bearer("roxana-token"))
        assert response.status_code == 401


class TestOpenRoutes:
    def test_healthz_and_the_contract_need_no_token(self):
        assert client.get("/healthz").status_code == 200
        assert client.get("/openapi.json").status_code == 200


class TestCors:
    def preflight(self, origin):
        return client.options("/api/argument/audit", headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        })

    @pytest.mark.parametrize("origin", ["https://roxana.rvanegas.co", "https://noesis.rvanegas.co"])
    def test_the_browser_apps_are_allowed(self, origin):
        response = self.preflight(origin)
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin

    def test_a_foreign_origin_is_not(self):
        response = self.preflight("https://example.com")
        assert "access-control-allow-origin" not in response.headers
