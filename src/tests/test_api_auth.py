"""
Tests for the caller check every /api route has (api/auth.py): mdc's token, or a
Cognito ID token from Roxana's user pool; and for CORS, which only the browser
apps' origins pass.
"""

import time
from unittest.mock import patch

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from conftest import MDC_AUTH
from main import app

client = TestClient(app)

POOL = "us-west-2_TESTPOOL"
ISSUER = f"https://cognito-idp.us-west-2.amazonaws.com/{POOL}"
ROXANA_CLIENT = "roxana-client"
NOESIS_CLIENT = "noesis-client"

SIGNING_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)

ARGUMENT = [
    {"symbol": "1", "proposition": "All humans are mortal.", "justifiers": [], "truth_score": "1.0"},
    {"symbol": "2", "proposition": "Socrates is a human.", "justifiers": [], "truth_score": "1.0"},
    {"symbol": "3", "proposition": "Socrates is mortal.", "justifiers": ["1", "2"], "truth_score": "1.0"},
]


class _Keys:
    """Stands in for PyJWKClient: always hands back the pool's public key."""

    def get_signing_key_from_jwt(self, token):
        class _Key:
            key = SIGNING_KEY.public_key()
        return _Key()


def id_token(key=SIGNING_KEY, **overrides):
    claims = {
        "sub": "a1b2c3",
        "cognito:username": "rodvandur",
        "token_use": "id",
        "aud": ROXANA_CLIENT,
        "iss": ISSUER,
        "exp": int(time.time()) + 3600,
    }
    claims.update(overrides)
    return jwt.encode(claims, key, algorithm="RS256", headers={"kid": "test"})


@pytest.fixture(autouse=True)
def cognito_configured(monkeypatch):
    import config
    monkeypatch.setattr(config, "COGNITO_USER_POOL_ID", POOL)
    monkeypatch.setattr(config, "COGNITO_CLIENT_IDS", [ROXANA_CLIENT, NOESIS_CLIENT])
    with patch("api.auth._signing_keys", return_value=_Keys()):
        yield


def audit(headers=None):
    # Deterministic and model-free, so a 200 here costs nothing.
    return client.post("/api/argument/audit", json={"argument": ARGUMENT}, headers=headers or {})


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


class TestCallers:
    def test_no_token_is_refused(self):
        assert audit().status_code == 401

    def test_mdc_token_is_accepted(self):
        assert audit(MDC_AUTH).status_code == 200

    def test_roxana_id_token_is_accepted(self):
        assert audit(bearer(id_token())).status_code == 200

    def test_noesis_id_token_is_accepted(self):
        assert audit(bearer(id_token(aud=NOESIS_CLIENT))).status_code == 200

    def test_agents_routes_need_a_caller_too(self):
        query = "conversation_id=s:c&snapshot_id=1"
        assert client.get(f"/api/agents/results?{query}").status_code == 401
        assert client.get(f"/api/agents/results?{query}", headers=bearer(id_token())).status_code == 200


class TestRefusedTokens:
    @pytest.mark.parametrize("token", [
        id_token(exp=int(time.time()) - 60),
        id_token(aud="some-other-client"),
        id_token(iss="https://cognito-idp.us-west-2.amazonaws.com/us-west-2_OTHER"),
        id_token(token_use="access"),
        id_token(key=OTHER_KEY),
        "not-a-jwt",
    ], ids=["expired", "other client", "other pool", "access token", "forged signature", "garbage"])
    def test_is_refused(self, token):
        assert audit(bearer(token)).status_code == 401

    def test_user_tokens_refused_when_cognito_is_unconfigured(self, monkeypatch):
        import config
        monkeypatch.setattr(config, "COGNITO_USER_POOL_ID", None)
        assert audit(bearer(id_token())).status_code == 401

    def test_user_tokens_cannot_reach_mdc_only_routes(self):
        response = client.post("/api/argument/extract", json={"text": "x"}, headers=bearer(id_token()))
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
