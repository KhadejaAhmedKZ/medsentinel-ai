"""Dr. Sentinel — deterministic clinical-support tips per casualty.

Generates a short, protocol-aligned prompt following the combat-casualty
**MARCH** sequence (Massive haemorrhage, Airway, Respiration, Circulation,
Hypothermia/Head). Deterministic so it works offline and stays consistent; an
online model could later enrich it, but the safe fallback lives here.

This is decision-support only — every tip ends by deferring to the human medic.
"""
from __future__ import annotations

_DEFER = "Confirm against your protocol — you make the final call."

_BLEED_WORDS = ("bleed", "blood", "haemorrhage", "hemorrhage", "arterial",
                "spurting", "amputat")
_LIMB_REGIONS = {"left_arm", "right_arm", "left_leg", "right_leg"}


def clinical_tip(category: str, breathing: str, responsive, signs: list[str],
                 regions: list[str]) -> str:
    text = " ".join(signs).lower()

    if category == "BLACK":
        return ("Expectant under START: no spontaneous breathing after airway "
                "positioning. Do not commit resources while savable casualties "
                f"wait; reassess only if the situation changes. {_DEFER}")

    tips: list[str] = []

    if any(w in text for w in _BLEED_WORDS):
        if set(regions) & _LIMB_REGIONS:
            tips.append("M — Massive haemorrhage: apply a tourniquet high and "
                        "tight on the affected limb; note the time.")
        else:
            tips.append("M — Massive haemorrhage: wound-pack and apply firm "
                        "direct pressure.")

    if breathing == "rapid" or "chest" in regions or "chest" in text:
        tips.append("R — Respiration: assess for tension pneumothorax; seal any "
                    "open chest wound.")

    if responsive is False or "head" in regions or "neck" in regions:
        tips.append("A — Airway: protect the airway, consider recovery "
                    "position, and monitor consciousness.")

    if category == "RED" and not tips:
        tips.append("Immediate: work the MARCH sequence and reassess vitals "
                    "frequently.")
    if category == "YELLOW" and not tips:
        tips.append("Delayed: splint and immobilise, control minor bleeding, "
                    "watch for deterioration.")
    if category == "GREEN" and not tips:
        tips.append("Minor: self- or buddy-aid; direct to the collection "
                    "point; recheck if status changes.")

    return " ".join(tips[:3]) + " " + _DEFER
