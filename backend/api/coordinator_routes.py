"""The one coordination endpoint: scan a scene -> triage -> allocate the team.

This is the MEDSENTINEL vertical slice. It chains the personas:
  Triage (scan)  ->  core START scoring  ->  Overseer (allocate + summarise)
"""
from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.agents.base import Persona
from backend.agents.triage_agent import ALLOWED_MIME_TYPES, MAX_IMAGE_BYTES, triage_agent
from backend.ai.gemini_client import gemini
from backend.ai.prompts import OVERSEER
from backend.core import allocation, triage
from backend.core.soldiers import BY_ID, SOLDIERS
from backend.schemas import ScanResponse

router = APIRouter(prefix="/api", tags=["coordinator"])


class Overseer(Persona):
    name = "Overseer"
    emoji = "🛰️"
    role = "Summarises the scene for the commander"
    system_prompt = OVERSEER
    temperature = 0.3


overseer = Overseer()

_AGENT_CARDS = [triage_agent.card(), overseer.card()]


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "ai_online": gemini.online}


@router.get("/agents")
async def agents() -> dict:
    return {"agents": _AGENT_CARDS, "ai_online": gemini.online}


@router.get("/soldiers")
async def soldiers() -> dict:
    return {"soldiers": SOLDIERS}


@router.get("/soldiers/{soldier_id}")
async def soldier(soldier_id: str) -> dict:
    s = BY_ID.get(soldier_id)
    if not s:
        raise HTTPException(404, "Soldier not found")
    return s


@router.post("/scan", response_model=ScanResponse)
async def scan(
    image: UploadFile | None = File(default=None),
    front_medics: int = Form(default=2),
    back_medics: int = Form(default=1),
) -> ScanResponse:
    image_bytes = b""
    mime = "image/jpeg"
    if image is not None:
        mime = image.content_type or "image/jpeg"
        if mime not in ALLOWED_MIME_TYPES:
            raise HTTPException(415, f"Unsupported image type: {mime}")
        image_bytes = await image.read()
        if len(image_bytes) > MAX_IMAGE_BYTES:
            raise HTTPException(413, "Image too large (max 8 MB).")

    front_medics = max(0, min(front_medics, 50))
    back_medics = max(0, min(back_medics, 50))

    # 1. Triage agent reads the scene.
    casualties, scene_note, used_ai = await triage_agent.scan(image_bytes, mime)

    # 2. START scoring (deterministic) + sort most-urgent first.
    ranked = triage.triage_all(casualties)
    summary = triage.summarize(ranked)

    # 3. Allocate the team front/back line.
    plan = allocation.allocate(ranked, front_medics, back_medics)

    # 4. Overseer one-liner for the commander (AI if online, else a local line).
    overseer_text = _local_overseer(summary, plan)
    if gemini.online:
        prompt = (
            f"Triage summary: {summary}\n"
            f"Immediate (RED) with no medic: {plan['unassigned_red']}\n"
            f"Front-line medics: {front_medics}, back-line medics: {back_medics}\n"
            f"Advice from allocator: {plan['advice']}"
        )
        ai_text = await overseer.say(prompt)
        if ai_text and not ai_text.startswith("[offline]"):
            overseer_text = ai_text

    return ScanResponse(
        used_ai=used_ai,
        scene_note=scene_note,
        summary=summary,
        casualties=[c.to_dict() for c in ranked],
        allocation=plan,
        overseer=overseer_text,
        agents=_AGENT_CARDS,
    )


def _local_overseer(summary: dict, plan: dict) -> str:
    counts = summary["counts"]
    return (
        f"{summary['total']} casualties: {counts['RED']} immediate, "
        f"{counts['YELLOW']} delayed, {counts['GREEN']} minor, "
        f"{counts['BLACK']} expectant. {plan['advice']}"
    )
