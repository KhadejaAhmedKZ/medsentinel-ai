"""Scout — scene assessment and safe-approach guidance.

Scout is "the eyes before the medics arrive". It takes the environmental
hazards reported by the Triage vision pass (or a sample set offline) plus the
casualty layout, and produces a commander/medic-facing read of the scene:

* a normalised hazard list,
* a recommended approach direction (derived from where the highest-priority
  casualties and the hazards sit in the frame),
* a coarse left / centre / right sector breakdown of casualties.

Deterministic and offline-safe. Advisory only — the team commander decides how
to actually approach.
"""
from __future__ import annotations

from backend.core.triage import Casualty, Category


def _sector(x: float | None) -> str:
    if x is None:
        return "centre"
    if x < 0.34:
        return "left"
    if x > 0.66:
        return "right"
    return "centre"


def assess(casualties: list[Casualty], hazards: list[str]) -> dict:
    hazards = [str(h)[:80] for h in (hazards or []) if h][:6]

    # Sector breakdown.
    sectors = {"left": 0, "centre": 0, "right": 0}
    for c in casualties:
        sectors[_sector(c.x)] += 1

    # Where is the most urgent casualty? Approach should reach them first while
    # staying clear of hazard-heavy sectors.
    reds = [c for c in casualties if c.category == Category.RED]
    focus = reds[0] if reds else (casualties[0] if casualties else None)
    focus_sector = _sector(focus.x) if focus else "centre"

    hazard_text = " ".join(hazards).lower()
    hazard_side = None
    for side in ("left", "right"):
        if side in hazard_text:
            hazard_side = side

    if focus and hazard_side and hazard_side == focus_sector:
        approach = (f"Highest-priority casualty ({focus.id}) is on the {focus_sector}, "
                    f"but hazards are also there — approach with caution and clear the "
                    f"hazard or use cover.")
    elif focus:
        approach = (f"Approach from the {focus_sector}: highest-priority casualty "
                    f"({focus.id}) is there.")
    else:
        approach = "No casualties detected — hold and reassess."
    if hazard_side and (not focus or hazard_side != focus_sector):
        approach += f" Keep clear of the {hazard_side} — hazards present."

    return {
        "hazards": hazards,
        "hazard_count": len(hazards),
        "approach": approach,
        "sectors": sectors,
    }


SAMPLE_HAZARDS = [
    "Structural debris near entrance",
    "Limited cover on the open right side",
]
