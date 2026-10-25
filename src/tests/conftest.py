"""Every /api route needs a caller (api/auth.py), so route tests call as mdc.

CORS_ORIGINS is read when config is first imported, before main builds the
app's middleware, so it is set here, ahead of any test module's import of main.
"""

import os

import pytest

os.environ["CORS_ORIGINS"] = "https://roxana.rvanegas.co,https://noesis.rvanegas.co"

MDC_TOKEN = "test-mdc-token"
MDC_AUTH = {"Authorization": f"Bearer {MDC_TOKEN}"}


@pytest.fixture(autouse=True)
def mdc_token_configured(monkeypatch):
    import config
    monkeypatch.setattr(config, "MDC_TOKEN", MDC_TOKEN)
