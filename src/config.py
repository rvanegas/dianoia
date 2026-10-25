"""Configuration — reads from the platform config dir with env var fallbacks."""
import os
import sys
import tomllib
from pathlib import Path


def _config_dir() -> Path:
    if sys.platform == "win32":
        import platformdirs
        return Path(platformdirs.user_config_dir("dianoia", appauthor=False))
    return Path.home() / ".config" / "dianoia"


_config_path = _config_dir() / "config.toml"
_toml: dict = {}
if _config_path.exists():
    with open(_config_path, "rb") as _f:
        _toml = tomllib.load(_f)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY") or _toml.get("anthropic_api_key")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL") or _toml.get("model", "claude-sonnet-4-6")
MDC_TOKEN = os.getenv("MDC_TOKEN") or _toml.get("mdc_token")


def _list(env: str, key: str) -> list[str]:
    raw = os.getenv(env)
    values = raw.split(",") if raw is not None else _toml.get(key, [])
    return [v.strip() for v in values if v.strip()]


# Roxana's Cognito user pool, whose ID tokens Roxana and noesis send, and the
# app clients those tokens may be issued to (their `aud`). Unset, no user token
# is accepted.
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID") or _toml.get("cognito_user_pool_id")
COGNITO_CLIENT_IDS = _list("COGNITO_CLIENT_IDS", "cognito_client_ids")
# Browser origins allowed to call the API. Unset, no browser may.
CORS_ORIGINS = _list("CORS_ORIGINS", "cors_origins")
