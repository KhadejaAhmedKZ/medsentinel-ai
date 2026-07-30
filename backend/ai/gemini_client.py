"""Thin async wrapper around the Google Gemini SDK (``google-genai``).

Adapted from the Sanadi AI project. Exposes the two helpers MEDSENTINEL needs:

* ``analyze_image_json`` — a multimodal call (scene image + prompt) that returns
  parsed JSON, used by the Triage agent to read a scanned room.
* ``generate`` — free-form text, used by the language personas.

With no API key configured the client runs in a degraded "offline" mode so the
Triage agent can fall back to a deterministic sample scene and the rest of the
system stays fully testable without network access.
"""
from __future__ import annotations

import json
import logging

from backend.config import settings

logger = logging.getLogger("medsentinel.gemini")


class GeminiClient:
    def __init__(self) -> None:
        self._model = settings.gemini_model
        self._client = None
        if settings.gemini_api_key:
            try:
                from google import genai

                self._client = genai.Client(api_key=settings.gemini_api_key)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Could not initialise Gemini client: %s", exc)
                self._client = None
        else:
            logger.warning("GEMINI_API_KEY not set — running in offline mode.")

    @property
    def online(self) -> bool:
        return self._client is not None

    async def generate(
        self, prompt: str, system_instruction: str = "", temperature: float = 0.4
    ) -> str:
        if not self._client:
            return "[offline] Gemini API key not configured."
        from google.genai import types

        try:
            resp = await self._client.aio.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction or None,
                    temperature=temperature,
                ),
            )
            return (resp.text or "").strip()
        except Exception as exc:
            logger.error("Gemini generate failed: %s", exc)
            return "Language service unavailable right now."

    async def analyze_image_json(
        self,
        image_bytes: bytes,
        mime_type: str,
        prompt: str,
        system_instruction: str = "",
        temperature: float = 0.2,
    ) -> dict:
        """Multimodal generation forced to a JSON object. ``{}`` on any error."""
        if not self._client:
            return {}
        from google.genai import types

        try:
            image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            resp = await self._client.aio.models.generate_content(
                model=self._model,
                contents=[image_part, prompt],
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction or None,
                    temperature=temperature,
                    response_mime_type="application/json",
                ),
            )
            return json.loads(resp.text or "{}")
        except Exception as exc:
            logger.error("Gemini analyze_image_json failed: %s", exc)
            return {}


# Shared singleton
gemini = GeminiClient()
