"""root python from uvicorn"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1.argument import router as argument_router
from api.v1.agents import router as agents_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(argument_router, prefix="/api/v1")
app.include_router(agents_router, prefix="/api/v1/agents")
