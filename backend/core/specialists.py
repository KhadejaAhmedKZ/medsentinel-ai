"""Specialist consult team — a virtual panel of field specialists.

The medic on the ground is one person; MEDSENTINEL assembles a *reach-back*
consult team around each casualty. Based on the injuries detected, the relevant
specialists "join" and each gives one focused, field-specific recommendation —
a trauma surgeon for a chest wound, vascular for a massive bleed, neuro for a
head injury, and so on. A complex casualty pulls in several at once.

Deterministic and offline-safe (the panel is stable and auditable). An online
model could later expand each note, but the safe baseline lives here.

Decision-support only; the human medic owns every decision.
"""
from __future__ import annotations

# Each specialist: identity + trigger keywords (matched against the casualty's
# signs / notes) + a focused recommendation. ``priority`` orders the panel so
# the most time-critical specialist is listed first (MARCH-aligned).
SPECIALISTS = [
    {"key": "hemorrhage", "name": "Dr. Vale", "field": "Vascular & Haemorrhage",
     "emoji": "🩸", "priority": 100,
     "triggers": ["arterial", "spurting", "amputat", "massive", "bleed", "blood",
                  "haemorrhage", "hemorrhage"],
     "rec": "Massive-haemorrhage first: tourniquet 5–7 cm proximal, high & tight; "
            "if junctional, pack with haemostatic gauze + 3 min direct pressure. "
            "Mark the TQ time and reassess the distal pulse."},
    {"key": "airway", "name": "Dr. Reyes", "field": "Airway & Anaesthesia",
     "emoji": "🫁", "priority": 92,
     "triggers": ["airway", "choking", "obstruct", "not breathing"],
     "rec": "Secure the airway: jaw-thrust/chin-lift, clear obstruction, NPA if "
            "tolerated, position for drainage. Prepare a surgical airway if you "
            "cannot ventilate."},
    {"key": "thoracic", "name": "Dr. Chen", "field": "Thoracic & Trauma Surgery",
     "emoji": "🫀", "priority": 85,
     "triggers": ["chest", "sucking chest", "pneumothorax", "tension", "thorax",
                  "rib", "flail", "penetrat", "gunshot", "gsw", "shrapnel", "frag"],
     "rec": "Apply a vented chest seal to any open wound. Watch for tension "
            "pneumothorax (rising distress, absent breath sounds, tracheal shift) "
            "and needle-decompress 2nd ICS mid-clavicular if it develops."},
    {"key": "neuro", "name": "Dr. Ilic", "field": "Neurosurgery & Head Injury",
     "emoji": "🧠", "priority": 70,
     "triggers": ["head", "skull", "cranial", "unconscious", "concussion", "brain"],
     "rec": "Protect the airway and C-spine, keep the head neutral, elevate 30° if "
            "no spinal concern. Track GCS/AVPU — a falling conscious level is a "
            "surgical emergency; expedite evacuation."},
    {"key": "burns", "name": "Dr. Haddad", "field": "Burns & Plastics",
     "emoji": "🔥", "priority": 55,
     "triggers": ["burn", "scald"],
     "rec": "Stop the burning, remove hot clothing/jewellery, cover with a clean "
            "dry dressing. Estimate %TBSA (rule of nines), begin fluid planning, "
            "and watch for airway burns if facial/inhalation."},
    {"key": "ortho", "name": "Dr. Okafor", "field": "Orthopaedics",
     "emoji": "🦴", "priority": 42,
     "triggers": ["deformed", "fracture", "broken", "dislocat", "femur", "tibia"],
     "rec": "Splint in the position of function, immobilise the joint above and "
            "below, and recheck distal pulse/sensation before and after. Consider "
            "a traction splint for a mid-shaft femur."},
]

_GENERAL = {"key": "general", "name": "Dr. Novak",
            "field": "General Trauma & Combat Medicine", "emoji": "💉", "priority": 20,
            "rec": "Coordinate the MARCH sweep, expose and log every wound, prevent "
                   "hypothermia, reassess vitals every few minutes, and prepare a "
                   "clear evac handover."}


def consult_team(category: str, signs: list[str], note: str,
                 breathing: str, responsive) -> list[dict]:
    """Return the specialists activated for this casualty, most-critical first."""
    if category == "BLACK":
        return []  # expectant — no active consult; documented only

    text = (" ".join(signs) + " " + (note or "")).lower()
    panel: list[dict] = []
    for spec in SPECIALISTS:
        findings = [s for s in signs if any(t in s.lower() for t in spec["triggers"])]
        keyword_hit = findings or any(t in text for t in spec["triggers"])
        vital_hit = (
            (spec["key"] == "airway" and breathing in ("absent", "rapid")) or
            (spec["key"] == "neuro" and responsive is False)
        )
        if keyword_hit or vital_hit:
            reason = "; ".join(findings) if findings else (
                "respiratory distress" if spec["key"] == "airway" else
                "altered consciousness" if spec["key"] == "neuro" else "on assessment")
            panel.append({
                "name": spec["name"], "field": spec["field"], "emoji": spec["emoji"],
                "priority": spec["priority"], "recommendation": spec["rec"],
                "reason": reason,
            })

    # General trauma always coordinates as the baseline team member.
    panel.append({
        "name": _GENERAL["name"], "field": _GENERAL["field"], "emoji": _GENERAL["emoji"],
        "priority": _GENERAL["priority"], "recommendation": _GENERAL["rec"],
        "reason": "baseline coordination",
    })
    panel.sort(key=lambda s: s["priority"], reverse=True)
    return panel
