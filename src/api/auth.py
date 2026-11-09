"""Bearer-token checks.

Two kinds of caller hold a token. noesis, a service, holds a static one
(`NOESIS_TOKEN`). People, through Roxana, hold an access token from auth
(`auth.rvanegas.co`, which signs people in for every project), issued to
Roxana's client: a JWT, checked against auth's published keys (kept a few
minutes, asked again for a key not known) by issuer, audience and expiry.
Every /api route requires one or the other; extract and evaluate, which spend
the most per call and only noesis uses, require noesis's.
"""

import hmac
import json
import time
import urllib.request
from dataclasses import dataclass

import jwt
from fastapi import Header, HTTPException

import config

JWKS_TTL = 5 * 60
# However often an unknown key is shown, auth is asked again at most this often.
JWKS_RETRY = 30
_jwks: dict = {"keys": {}, "fetched": 0.0, "tried": -JWKS_RETRY}


@dataclass(frozen=True)
class Caller:
    kind: str  # "noesis" or "user"
    name: str  # "noesis", or the user name


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


def _fetch_keys() -> dict:
    with urllib.request.urlopen(f"{config.AUTH_URL}/.well-known/jwks.json", timeout=10) as response:
        found = json.loads(response.read())
    return {k["kid"]: jwt.PyJWK.from_dict(k).key for k in found.get("keys", []) if k.get("kid")}


def _key(kid: str):
    now = time.monotonic()
    stale = now - _jwks["fetched"] > JWKS_TTL
    if (stale or kid not in _jwks["keys"]) and now - _jwks["tried"] >= JWKS_RETRY:
        _jwks["tried"] = now
        try:
            _jwks["keys"], _jwks["fetched"] = _fetch_keys(), now
        except (OSError, ValueError):
            pass  # auth unreachable: the keys already known still verify
    return _jwks["keys"].get(kid)


def user_for_auth_token(token: str) -> str | None:
    """The user an access token from auth belongs to, if issued to one of AUTH_CLIENT_IDS."""
    try:
        kid = jwt.get_unverified_header(token).get("kid")
    except jwt.PyJWTError:
        return None
    key = _key(kid) if kid else None
    if key is None:
        return None
    try:
        claims = jwt.decode(token, key, algorithms=["EdDSA"], issuer=config.AUTH_URL, audience=config.AUTH_URL)
    except jwt.PyJWTError:
        return None
    if claims.get("client_id") not in config.AUTH_CLIENT_IDS or not claims.get("sub"):
        return None
    return claims["sub"]


def require_caller(authorization: str | None = Header(default=None)) -> Caller:
    """Accept noesis's token or a person's access token from auth issued to Roxana."""
    token = _bearer(authorization)
    if _is_noesis_token(token):
        return Caller(kind="noesis", name="noesis")
    if not (config.AUTH_URL and config.AUTH_CLIENT_IDS):
        raise HTTPException(status_code=401, detail="Invalid or missing bearer token")
    user = user_for_auth_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or missing bearer token")
    return Caller(kind="user", name=user)
