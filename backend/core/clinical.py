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


# ---------------------------------------------------------------------------
# Dr. Sentinel — profile brief (used when a medic scans an NFC tag)
# ---------------------------------------------------------------------------

# Allergy -> what to avoid. Keyed by a substring of the allergy name.
_ALLERGY_GUIDANCE = {
    "penicillin": "Avoid penicillins (amoxicillin, ampicillin, flucloxacillin); "
                  "use a non-beta-lactam alternative.",
    "sulfa": "Avoid sulfonamide antibiotics (e.g. co-trimoxazole).",
    "latex": "Use latex-free gloves, tourniquets and dressings.",
    "morphine": "Avoid morphine; consider an alternative analgesic per protocol.",
    "aspirin": "Avoid aspirin/NSAIDs; consider paracetamol per protocol.",
    "iodine": "Avoid iodine-based antiseptics; use chlorhexidine.",
}

# Condition -> a caution the medic should keep in mind.
_CONDITION_GUIDANCE = {
    "asthma": "Asthma — watch respiratory effort; avoid known triggers.",
    "hypertension": "Hypertension — expect altered baseline BP; note home meds.",
    "diabet": "Diabetes — check blood glucose; consider hypo/hyperglycaemia.",
    "epilep": "Epilepsy — seizure precautions.",
    "haemophil": "Bleeding disorder — haemorrhage control is higher priority.",
    "hemophil": "Bleeding disorder — haemorrhage control is higher priority.",
}


def soldier_brief(soldier: dict) -> dict:
    """Turn an NFC medical profile into a Dr. Sentinel summary + risk flags.

    Deterministic and offline-safe. ``risks`` is ordered most-important first;
    each has a ``level`` ("critical" | "caution") the UI can colour.
    """
    allergies = [a for a in soldier.get("allergies", [])
                 if a and a.lower() not in ("none", "none known")]
    meds = [m for m in soldier.get("medications", []) if m and m.lower() != "none"]
    conditions = [c for c in soldier.get("conditions", []) if c and c.lower() != "none"]

    # One-line clinical summary.
    parts = [f"{soldier.get('name', 'Unknown')}",
             f"blood {soldier.get('blood_type', '?')}"]
    if allergies:
        parts.append("allergies: " + ", ".join(allergies))
    if conditions:
        parts.append("history: " + ", ".join(conditions))
    summary = " · ".join(parts) + "."

    risks: list[dict] = []
    for a in allergies:
        low = a.lower()
        guidance = next((g for k, g in _ALLERGY_GUIDANCE.items() if k in low), None)
        risks.append({
            "level": "critical",
            "text": f"⚠️ Allergy: {a}." + (f" {guidance}" if guidance else
                    " Confirm before administering any medication."),
        })
    for c in conditions:
        low = c.lower()
        guidance = next((g for k, g in _CONDITION_GUIDANCE.items() if k in low), None)
        if guidance:
            risks.append({"level": "caution", "text": guidance})
    if meds:
        risks.append({"level": "caution",
                      "text": "On medication: " + ", ".join(meds)
                              + " — check for interactions."})

    return {
        "summary": summary,
        "risks": risks,
        "emergency_contact": soldier.get("emergency_contact"),
    }
