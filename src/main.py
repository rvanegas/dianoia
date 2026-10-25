"""root python from uvicorn"""
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from api.argument import router as argument_router
from api.agents import router as agents_router
from api.auth import require_caller
from api.health import router as health_router

# Initialize GPT instances at server startup
from services.startup_init import run_startup_initialization
from core.utils import logger

run_startup_initialization()

app = FastAPI()

# Only the browser apps' own origins (CORS_ORIGINS); mdc is not a browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

# Every /api route needs a caller (api/auth.py); /healthz and the published
# contract (/openapi.json, /docs) stay open.
app.include_router(argument_router, prefix="/api/argument", dependencies=[Depends(require_caller)])
app.include_router(agents_router, prefix="/api/agents", dependencies=[Depends(require_caller)])
app.include_router(health_router)

logger.info("Server is ready and accepting requests.")
