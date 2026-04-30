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
