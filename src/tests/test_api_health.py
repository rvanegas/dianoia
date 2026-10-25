"""
Tests for GET /healthz, which reports the commit bin/deploy stamped.
"""

import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestHealthz:
    """The deployed commit is read from deployed.json"""

    def test_reports_the_stamped_commit(self, tmp_path):
        stamp = tmp_path / "deployed.json"
        stamp.write_text(json.dumps({"commit": "abc1234", "deployedAt": "2026-10-24T00:00:00Z"}))
        with patch("api.health._DEPLOYED", stamp):
            response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"ok": True, "commit": "abc1234", "deployedAt": "2026-10-24T00:00:00Z"}

    def test_a_checkout_reports_dev(self, tmp_path):
        with patch("api.health._DEPLOYED", tmp_path / "missing.json"):
            response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"ok": True, "commit": "dev"}

    def test_needs_no_token(self):
        with patch("config.MDC_TOKEN", "test-mdc-token"):
            response = client.get("/healthz")
        assert response.status_code == 200
