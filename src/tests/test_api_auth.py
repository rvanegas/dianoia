"""
Tests for the caller check every /api route has (api/auth.py): noesis's token, or a
person's access token from auth issued to Roxana, a JWT checked against auth's
published keys; and for CORS, which only the browser apps' origins pass.
"""

import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient

from api import auth
from conftest import NOESIS_AUTH
from main import app

client = TestClient(app)

AUTH = "https://auth.example"
ROXANA_CLIENT = "roxana"
KEY = Ed25519PrivateKey.generate()
STRANGER = Ed25519PrivateKey.generate()

ARGUMENT = [
    {"symbol": "1", "proposition": "All humans are mortal.", "justifiers": [], "truth_score": "1.0"},
    {"symbol": "2", "proposition": "Socrates is a human.", "justifiers": [], "truth_score": "1.0"},
    {"symbol": "3", "proposition": "Socrates is mortal.", "justifiers": ["1", "2"], "truth_score": "1.0"},
]


def token(user="rodvandur", client_id=ROXANA_CLIENT, aud=AUTH, ttl=900, key=KEY, issuer=AUTH, kid="k1"):
    now = int(time.time())
    return jwt.encode({"iss": issuer, "sub": user, "aud": aud, "client_id": client_id, "scope": "identity",
                       "iat": now, "exp": now + ttl}, key, algorithm="EdDSA", headers={"kid": kid})


@pytest.fixture(autouse=True)
def auth_configured(monkeypatch):
    import config
    monkeypatch.setattr(config, "AUTH_URL", AUTH)
    monkeypatch.setattr(config, "AUTH_CLIENT_IDS", [ROXANA_CLIENT])
    fetched = []
    monkeypatch.setattr(auth, "_fetch_keys", lambda: fetched.append(1) or {"k1": KEY.public_key()})
    monkeypatch.setattr(auth, "_jwks", {"keys": {}, "fetched": 0.0, "tried": -auth.JWKS_RETRY})
    return fetched


def audit(headers=None):
    # Deterministic and model-free, so a 200 here costs nothing.
    return client.post("/api/argument/audit", json={"argument": ARGUMENT}, headers=headers or {})


def bearer(value):
    return {"Authorization": f"Bearer {value}"}


class TestCallers:
    def test_no_token_is_refused(self):
        assert audit().status_code == 401

    def test_noesis_token_is_accepted(self):
        assert audit(NOESIS_AUTH).status_code == 200

    def test_a_roxana_users_token_is_accepted(self):
        assert audit(bearer(token())).status_code == 200
        assert auth.require_caller(f"Bearer {token()}") == auth.Caller(kind="user", name="rodvandur")

    def test_auths_keys_are_fetched_once_for_many_calls(self, auth_configured):
        audit(bearer(token()))
        audit(bearer(token()))
        assert len(auth_configured) == 1

    def test_agents_routes_need_a_caller_too(self):
        query = "conversation_id=s:c&snapshot_id=1"
        assert client.get(f"/api/agents/results?{query}").status_code == 401
        assert client.get(f"/api/agents/results?{query}", headers=bearer(token())).status_code == 200


class TestRefusedTokens:
    @pytest.mark.parametrize("value", [
        token(client_id="thefloor"), token(user=""), token(ttl=-60), token(key=STRANGER),
        token(issuer="https://elsewhere.example"), token(aud="https://noesis.example/mcp"),
        token(kid="unknown"), "not-a-token"],
        ids=["another client's", "no user", "expired", "not auth's key", "not auth", "for noesis",
             "an unknown key", "not a JWT"])
    def test_is_refused(self, value):
        assert audit(bearer(value)).status_code == 401

    def test_user_tokens_refused_when_auth_is_unconfigured(self, monkeypatch):
        import config
        monkeypatch.setattr(config, "AUTH_URL", "")
        assert audit(bearer(token())).status_code == 401

    def test_auth_down_still_verifies_with_the_keys_known(self, monkeypatch):
        assert audit(bearer(token())).status_code == 200

        def down():
            raise OSError("auth is down")
        monkeypatch.setattr(auth, "_fetch_keys", down)
        auth._jwks["fetched"] -= auth.JWKS_TTL + 1
        auth._jwks["tried"] -= auth.JWKS_RETRY
        assert audit(bearer(token())).status_code == 200

    def test_user_tokens_cannot_reach_noesis_only_routes(self):
        response = client.post("/api/argument/extract", json={"text": "x"}, headers=bearer(token()))
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
