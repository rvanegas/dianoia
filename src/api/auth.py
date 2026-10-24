"""Bearer-token check for service clients (mdc)."""

import hmac

from fastapi import Header, HTTPException

import config


def require_mdc_token(authorization: str | None = Header(default=None)) -> None:
    """Reject requests that don't carry mdc's service token."""
    if not config.MDC_TOKEN:
        raise HTTPException(status_code=503, detail="MDC_TOKEN is not configured")
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not hmac.compare_digest(token, config.MDC_TOKEN):
        raise HTTPException(status_code=401, detail="Invalid or missing bearer token")
