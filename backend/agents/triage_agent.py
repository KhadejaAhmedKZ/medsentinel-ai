"""Triage agent — scans a scene image and returns detected casualties.

Online: one multimodal Gemini call reads the photo and reports observable
START inputs per person. Offline (no API key, or a failed call): a deterministic
sample scene is returned so the full pipeline and dashboard still demo end to
end. Either way the raw observations are handed to ``core.triage`` which applies
the START decision tree — the categorisation logic never lives in the model.
"""
from __future__ import annotations

import logging

from backend.agents.base import Persona
from backend.ai.gemini_client import gemini
from backend.ai.prompts import TRIAGE_SCAN
from backend.core.triage import Casualty

logger = logging.getLogger("medsentinel.triage")

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}
MAX_IMAGE_BYTES = 8 * 1024 * 1024  # 8 MB


class TriageAgent(Persona):
    name = "Triage"
    emoji = "🎯"
    role = "Scans the scene and detects casualties"

    async def scan(self, image_bytes: bytes, mime_type: str) -> tuple[list[Casualty], str, list[str], bool]:
        """Return (casualties, scene_note, hazards, used_ai)."""
        if gemini.online and image_bytes:
            data = await gemini.analyze_image_json(
                image_bytes, mime_type, "Analyze this scene.", system_instruction=TRIAGE_SCAN
            )
            casualties = _parse(data)
            if casualties:
                hazards = [str(h)[:80] for h in data.get("hazards", []) if h][:6]
                return casualties, str(data.get("scene_note", "")), hazards, True
            logger.info("Triage AI returned no casualties; using sample scene.")
        from backend.core.scout import SAMPLE_HAZARDS
        return (_sample_scene(),
                "Sample scene (offline mode — no live image analysis).",
                list(SAMPLE_HAZARDS), False)


def _parse(data: dict) -> list[Casualty]:
    raw = data.get("casualties") if isinstance(data, dict) else None
    if not isinstance(raw, list):
        return []
    out: list[Casualty] = []
    for i, r in enumerate(raw, 1):
        if not isinstance(r, dict):
            continue
        out.append(
            Casualty(
                id=str(r.get("id") or f"C{i}"),
                x=_num(r.get("x")),
                y=_num(r.get("y")),
                can_walk=_tri(r.get("can_walk")),
                breathing=_breath(r.get("breathing")),
                responsive=_tri(r.get("responsive")),
                signs=[str(s)[:80] for s in r.get("signs", []) if s][:6],
                note=str(r.get("note") or "")[:160],
            )
        )
    return out


def _num(v) -> float | None:
    try:
        f = float(v)
        return min(max(f, 0.0), 1.0)
    except (TypeError, ValueError):
        return None


def _tri(v):
    if v is True or v is False:
        return v
    return None


def _breath(v) -> str:
    v = str(v or "unknown").lower()
    return v if v in {"normal", "rapid", "absent", "unknown"} else "unknown"


def _sample_scene() -> list[Casualty]:
    """A realistic four-casualty room used for offline demos and tests."""
    return [
        Casualty(id="C1", x=0.22, y=0.55, can_walk=False, breathing="rapid",
                 responsive=False,
                 signs=["arterial bleeding right thigh", "shrapnel wound to chest",
                        "laceration to the head"],
                 note="Lying still near the doorway, not moving; multiple wounds."),
        Casualty(id="C2", x=0.48, y=0.40, can_walk=False, breathing="normal",
                 responsive=True, signs=["deformed left forearm"],
                 note="Sitting against the wall, alert, holding arm."),
        Casualty(id="C3", x=0.70, y=0.62, can_walk=True, breathing="normal",
                 responsive=True, signs=["minor facial cut"],
                 note="Standing, walking, mild bleeding to face."),
        Casualty(id="C4", x=0.86, y=0.35, can_walk=False, breathing="absent",
                 responsive=False, signs=["no movement", "no respiration"],
                 note="Prone, no observable breathing after airway."),
    ]


triage_agent = TriageAgent()
