"""GET /healthz — what is deployed, for bin/deploy and anyone checking."""

import json
from pathlib import Path

from fastapi import APIRouter

router = APIRouter()

# Written by bin/deploy into src/ before the image is built, so it is baked in
# with the code it describes. Absent in a checkout, where the answer is "dev".
_DEPLOYED = Path(__file__).resolve().parent.parent / "deployed.json"


def _deployed() -> dict:
    try:
        return json.loads(_DEPLOYED.read_text())
    except (OSError, ValueError):
        return {"commit": "dev"}


@router.get("/healthz")
def healthz() -> dict:
    """Unauthenticated: it says nothing but which commit is running."""
    return {"ok": True, **_deployed()}
