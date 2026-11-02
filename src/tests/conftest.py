"""Every /api route needs a caller (api/auth.py), so route tests call as noesis.

CORS_ORIGINS is read when config is first imported, before main builds the
app's middleware, so it is set here, ahead of any test module's import of main.
"""

import os

import pytest

os.environ["CORS_ORIGINS"] = "https://roxana.rvanegas.co,https://noesis.rvanegas.co"

NOESIS_TOKEN = "test-noesis-token"
NOESIS_AUTH = {"Authorization": f"Bearer {NOESIS_TOKEN}"}


@pytest.fixture(autouse=True)
def noesis_token_configured(monkeypatch):
    import config
    monkeypatch.setattr(config, "NOESIS_TOKEN", NOESIS_TOKEN)
