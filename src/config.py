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
NOESIS_TOKEN = os.getenv("NOESIS_TOKEN") or _toml.get("noesis_token")


def _list(env: str, key: str) -> list[str]:
    raw = os.getenv(env)
    values = raw.split(",") if raw is not None else _toml.get(key, [])
    return [v.strip() for v in values if v.strip()]


# noesis's OAuth server, which signs Roxana's people in: a person's access token
# is checked by asking noesis's /me, which says whose it is and which client it
# was issued to, one of NOESIS_CLIENT_IDS. Unset, no user token is accepted.
NOESIS_URL = (os.getenv("NOESIS_URL") or _toml.get("noesis_url") or "").rstrip("/")
NOESIS_CLIENT_IDS = _list("NOESIS_CLIENT_IDS", "noesis_client_ids")
# Browser origins allowed to call the API. Unset, no browser may.
CORS_ORIGINS = _list("CORS_ORIGINS", "cors_origins")
