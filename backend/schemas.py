"""Pydantic response models for the API."""
from __future__ import annotations

from pydantic import BaseModel


class TeamConfig(BaseModel):
    front_medics: int = 2
    back_medics: int = 1


class ScanResponse(BaseModel):
    used_ai: bool
    scene_note: str
    summary: dict
    casualties: list[dict]
    allocation: dict
    overseer: str
    readiness: dict
    evacuation: dict
    agents: list[dict]
