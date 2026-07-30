"""Shared persona base class.

Adapted from Sanadi's agent pattern: every MEDSENTINEL persona is a small class
with a name, an emoji, a one-line role, and a system prompt. The orchestrator
and the UI use these fields to attribute output to a named "digital team
member" (Triage, Dr. Sentinel, Overseer, ...).
"""
from __future__ import annotations

from backend.ai.gemini_client import gemini


class Persona:
    name: str = "agent"
    emoji: str = "🤖"
    role: str = ""
    system_prompt: str = ""
    temperature: float = 0.4

    async def say(self, prompt: str) -> str:
        return await gemini.generate(
            prompt, system_instruction=self.system_prompt, temperature=self.temperature
        )

    def card(self) -> dict:
        return {"name": self.name, "emoji": self.emoji, "role": self.role}
