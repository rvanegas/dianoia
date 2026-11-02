"""Bearer-token checks.

Two kinds of caller hold a token. noesis, a service, holds a static one
(`NOESIS_TOKEN`). People, through Roxana and noesis, hold a Cognito ID token from
Roxana's user pool, verified here against the pool's published signing keys.
Every /api route requires one or the other; extract and evaluate, which spend
the most per call and only noesis uses, require noesis's.
"""

import hmac
from dataclasses import dataclass
from functools import lru_cache

import jwt
from fastapi import Header, HTTPException

import config


@dataclass(frozen=True)
class Caller:
    kind: str  # "noesis" or "user"
    name: str  # "noesis", or the Cognito username


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


def _issuer() -> str:
    region = config.COGNITO_USER_POOL_ID.split("_", 1)[0]
    return f"https://cognito-idp.{region}.amazonaws.com/{config.COGNITO_USER_POOL_ID}"


@lru_cache(maxsize=1)
def _signing_keys() -> jwt.PyJWKClient:
    # Fetched once and cached; a token signed with a key it has not seen makes
    # it fetch again, which is how Cognito's key rotation is picked up.
    return jwt.PyJWKClient(f"{_issuer()}/.well-known/jwks.json", cache_keys=True)


def verify_cognito_id_token(token: str) -> str:
    """Return the username an ID token was issued to, or raise jwt.PyJWTError."""
    key = _signing_keys().get_signing_key_from_jwt(token).key
    claims = jwt.decode(
        token,
        key,
        algorithms=["RS256"],
        audience=config.COGNITO_CLIENT_IDS,
        issuer=_issuer(),
        options={"require": ["exp", "iss", "aud", "token_use"]},
    )
    # An access token is signed by the same keys; only an ID token says who.
    if claims["token_use"] != "id":
        raise jwt.InvalidTokenError("not an ID token")
    return claims.get("cognito:username") or claims["sub"]


def require_caller(authorization: str | None = Header(default=None)) -> Caller:
    """Accept noesis's token or a Cognito ID token from Roxana's user pool."""
    token = _bearer(authorization)
    if _is_noesis_token(token):
        return Caller(kind="noesis", name="noesis")
    if not (config.COGNITO_USER_POOL_ID and config.COGNITO_CLIENT_IDS):
        raise HTTPException(status_code=401, detail="Invalid or missing bearer token")
    try:
        return Caller(kind="user", name=verify_cognito_id_token(token))
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or missing bearer token")
