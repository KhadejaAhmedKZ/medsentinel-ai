"""MEDSENTINEL AI — FastAPI entrypoint.

Serves the coordination API and the single-file dashboard. Run:

    uvicorn backend.main:app --reload

Then open http://localhost:8000/ for the dashboard, or /docs for the API.
"""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.api.coordinator_routes import router as coordinator_router
from backend.config import settings

logging.basicConfig(level=logging.INFO)

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.allowed_origins == "*"
    else [o.strip() for o in settings.allowed_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(coordinator_router)

_FRONTEND = Path(__file__).resolve().parent.parent / "frontend"


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(_FRONTEND / "index.html")


if _FRONTEND.exists():
    app.mount("/static", StaticFiles(directory=_FRONTEND), name="static")
