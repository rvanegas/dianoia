"""Bearer-token checks.

Two kinds of caller hold a token. noesis, a service, holds a static one
(`NOESIS_TOKEN`). People, through Roxana, hold an access token from noesis's
OAuth server, issued to Roxana's client; it is opaque, so it is checked by
asking noesis's /me, whose answer is kept for a minute. Every /api route
requires one or the other; extract and evaluate, which spend the most per call
and only noesis uses, require noesis's.
"""

import hashlib
import hmac
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

from fastapi import Header, HTTPException

import config

ME_TTL = 60
_me_cache: dict[str, tuple[float, str]] = {}


@dataclass(frozen=True)
class Caller:
    kind: str  # "noesis" or "user"
    name: str  # "noesis", or the noesis user name


def _bearer(authorization: str | None) -> str:
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Invalid or missing bearer token")
    return token


def _is_noesis_token(token: str) -> bool:
    return bool(config.NOESIS_TOKEN) and hmac.compare_digest(token, config.NOESIS_TOKEN)


def require_noesis_token(authorization: str | None = Header(default=None)) -> None:
    """Reject requests that don't carry noesis's service token."""
    if not config.NOESIS_TOKEN:
        raise HTTPException(status_code=503, detail="NOESIS_TOKEN is not configured")
    if not _is_noesis_token(_bearer(authorization)):
        raise HTTPException(status_code=401, detail="Invalid or missing bearer token")


class NoesisUnavailable(Exception):
    pass


def _ask_noesis(token: str) -> dict | None:
    """noesis's /me for this token: None if noesis refuses it."""
    request = urllib.request.Request(f"{config.NOESIS_URL}/me", headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            return None
        raise NoesisUnavailable(f"noesis /me answered {exc.code}") from None
    except (OSError, ValueError) as exc:
        raise NoesisUnavailable(str(exc)) from None


def user_for_noesis_token(token: str) -> str | None:
    """The noesis user an access token belongs to, if issued to one of NOESIS_CLIENT_IDS."""
    key = hashlib.sha256(token.encode()).hexdigest()
    now = time.monotonic()
    cached = _me_cache.get(key)
    if cached and cached[0] > now:
        return cached[1]
    me = _ask_noesis(token)
    if not me or me.get("client") not in config.NOESIS_CLIENT_IDS or not me.get("user"):
        return None
    if len(_me_cache) > 1000:
        _me_cache.clear()
    _me_cache[key] = (now + ME_TTL, me["user"])
    return me["user"]


def require_caller(authorization: str | None = Header(default=None)) -> Caller:
    """Accept noesis's token or a person's noesis access token issued to Roxana."""
    token = _bearer(authorization)
    if _is_noesis_token(token):
        return Caller(kind="noesis", name="noesis")
    if not (config.NOESIS_URL and config.NOESIS_CLIENT_IDS):
        raise HTTPException(status_code=401, detail="Invalid or missing bearer token")
    try:
        user = user_for_noesis_token(token)
    except NoesisUnavailable:
        raise HTTPException(status_code=503, detail="noesis, which checks this token, did not answer")
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or missing bearer token")
    return Caller(kind="user", name=user)
