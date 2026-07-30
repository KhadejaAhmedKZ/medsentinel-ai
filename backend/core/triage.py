"""START triage model and scoring.

MEDSENTINEL uses the internationally recognised **START** protocol (Simple
Triage And Rapid Treatment) for mass-casualty prioritisation. Each casualty is
sorted into one of four categories:

* ``RED``   — Immediate: life-threatening but survivable with prompt care.
* ``YELLOW``— Delayed: serious injuries that can tolerate a short wait.
* ``GREEN`` — Minor: the "walking wounded".
* ``BLACK`` — Expectant/Deceased: no spontaneous breathing after airway.

The vision agent supplies *observations* (can the casualty walk, are they
breathing, do they respond). This module turns those observations into a
category and a numeric priority the allocator can rank — so the final decision
follows a consistent, auditable clinical rule rather than a black-box guess.

This is a **decision-support** aid. A qualified human remains responsible for
every triage and treatment decision.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum

from backend.core.anatomy import derive_regions
from backend.core.clinical import clinical_tip


class Category(str, Enum):
    RED = "RED"        # Immediate
    YELLOW = "YELLOW"  # Delayed
    GREEN = "GREEN"    # Minor / walking wounded
    BLACK = "BLACK"    # Expectant / deceased


# Human-readable labels + a base priority per category. Priority is 0-100;
# higher means "treat sooner". BLACK is intentionally low: under START, no
# resources are committed to the expectant while savable casualties wait.
CATEGORY_META = {
    Category.RED: {"label": "Immediate", "line": "front", "base": 90},
    Category.YELLOW: {"label": "Delayed", "line": "back", "base": 55},
    Category.GREEN: {"label": "Minor", "line": "back", "base": 25},
    Category.BLACK: {"label": "Expectant", "line": "none", "base": 5},
}


@dataclass
class Casualty:
    """One person detected in the scanned scene."""

    id: str
    # Normalised position in the image (0-1), for the map overlay. Optional.
    x: float | None = None
    y: float | None = None
    # Raw observations from the vision agent.
    can_walk: bool | None = None          # walking wounded?
    breathing: str = "unknown"            # normal | rapid | absent | unknown
    responsive: bool | None = None        # obeys commands?
    signs: list[str] = field(default_factory=list)  # e.g. "visible leg bleeding"
    note: str = ""                        # free-text observation
    # Filled in by score().
    category: Category | None = None
    priority: int = 0
    rationale: str = ""
    regions: list[str] = field(default_factory=list)  # body-map regions
    clinical_tip: str = ""                # Dr. Sentinel MARCH prompt

    def to_dict(self) -> dict:
        d = asdict(self)
        d["category"] = self.category.value if self.category else None
        d["label"] = CATEGORY_META[self.category]["label"] if self.category else None
        return d


# Keywords that hint at a critical, RED-worthy bleed/injury even when vitals
# read as borderline. Purely to *raise* urgency, never to lower it.
_CRITICAL_SIGNS = (
    "arterial", "spurting", "massive bleed", "amputation", "amputated",
    "not breathing", "unconscious", "unresponsive", "sucking chest",
)


def score(c: Casualty) -> Casualty:
    """Apply the START decision tree, then compute a priority number.

    START order of operations:
      1. Walking?            -> GREEN
      2. Not breathing?      -> BLACK (after implied airway)
      3. Breathing rapid?    -> RED
      4. No/weak perfusion?  -> RED   (approximated by 'responsive' + signs)
      5. Doesn't obey?       -> RED
      6. Otherwise           -> YELLOW
    """
    signs_text = " ".join(c.signs).lower() + " " + c.note.lower()
    critical_sign = any(k in signs_text for k in _CRITICAL_SIGNS)

    if c.breathing == "absent":
        c.category = Category.BLACK
        c.rationale = "No spontaneous breathing observed (expectant under START)."
    elif c.can_walk and not critical_sign:
        c.category = Category.GREEN
        c.rationale = "Able to walk — minor / walking wounded."
    elif c.breathing == "rapid":
        c.category = Category.RED
        c.rationale = "Rapid respiration (>30/min) — immediate."
    elif c.responsive is False:
        c.category = Category.RED
        c.rationale = "Does not obey commands / altered consciousness — immediate."
    elif critical_sign:
        c.category = Category.RED
        c.rationale = "Life-threatening sign observed — immediate."
    else:
        c.category = Category.YELLOW
        c.rationale = "Serious but currently stable — delayed."

    # Priority = category base, nudged up by number/severity of visible signs.
    base = CATEGORY_META[c.category]["base"]
    bump = min(len(c.signs) * 3, 9)
    if critical_sign and c.category == Category.RED:
        bump += 5
    c.priority = min(base + bump, 100)

    # Body-map regions + Dr. Sentinel clinical prompt (deterministic).
    c.regions = derive_regions(c.signs, c.note)
    c.clinical_tip = clinical_tip(
        c.category.value, c.breathing, c.responsive, c.signs, c.regions
    )
    return c


def triage_all(casualties: list[Casualty]) -> list[Casualty]:
    """Score every casualty and return them sorted most-urgent first."""
    for c in casualties:
        score(c)
    return sorted(casualties, key=lambda c: c.priority, reverse=True)


def summarize(casualties: list[Casualty]) -> dict:
    """Category counts for the commander's overview panel."""
    counts = {cat.value: 0 for cat in Category}
    for c in casualties:
        if c.category:
            counts[c.category.value] += 1
    return {
        "total": len(casualties),
        "counts": counts,
    }
