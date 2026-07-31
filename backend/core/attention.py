"""Per-region attention ranking — *which wound to treat first*.

A casualty with several injuries needs the medic to act in the right order.
This classifies each injured body region by the injury described there and ranks
them by the combat-casualty **MARCH** priority (Massive haemorrhage → Airway →
Respiration → …), so the dashboard can show a "treat this first" body map.

Decision-support only; the human medic makes the final call.
"""
from __future__ import annotations

from backend.core.anatomy import derive_regions

# Injury signatures, ordered high-to-low priority. First match wins, so a phrase
# with several cues is scored by its most urgent one.
_INJURY = [
    (("arterial", "spurting", "amputat", "massive bleed"),
     {"level": "critical", "weight": 100, "march": "M",
      "action": "Control massive haemorrhage first — tourniquet high & tight or wound packing."}),
    (("not breathing", "airway", "choking", "obstruct"),
     {"level": "critical", "weight": 92, "march": "A",
      "action": "Open and protect the airway now."}),
    (("sucking chest", "tension", "pneumothorax", "flail"),
     {"level": "critical", "weight": 88, "march": "R",
      "action": "Seal the chest wound; watch for tension pneumothorax."}),
    (("gunshot", "gsw", "shrapnel", "penetrat", "frag", "blast"),
     {"level": "high", "weight": 78, "march": "M",
      "action": "Penetrating wound — expose, pack, and monitor for internal bleeding."}),
    (("bleed", "blood", "haemorrhage", "hemorrhage"),
     {"level": "high", "weight": 60, "march": "M",
      "action": "Control bleeding with direct pressure and a dressing."}),
    (("burn", "scald"),
     {"level": "high", "weight": 52, "march": "-",
      "action": "Cool and cover the burn; protect the airway if facial."}),
    (("deformed", "fracture", "broken", "dislocat"),
     {"level": "moderate", "weight": 42, "march": "-",
      "action": "Splint and immobilise the limb."}),
    (("laceration", "cut", "abrasion", "graze", "wound"),
     {"level": "moderate", "weight": 35, "march": "-",
      "action": "Clean and dress the wound."}),
]
_DEFAULT = {"level": "moderate", "weight": 30, "march": "-",
            "action": "Assess and treat as indicated."}


def _classify(phrase: str) -> dict:
    low = phrase.lower()
    for keywords, meta in _INJURY:
        if any(k in low for k in keywords):
            return dict(meta)
    return dict(_DEFAULT)


def region_attention(signs: list[str], note: str, regions: list[str]) -> list[dict]:
    """Rank the casualty's injured ``regions`` by treat-first priority.

    Each entry: region, the driving sign, level, weight, march letter, action,
    and a 1-based ``rank``. Same region set the body map highlights, so the map
    and the ranking stay in lock-step.
    """
    phrases = list(signs) + ([note] if note else [])
    ranked: list[dict] = []
    for region in regions:
        best: dict | None = None
        for ph in phrases:
            if region in derive_regions([ph], ""):
                cls = _classify(ph)
                if best is None or cls["weight"] > best["weight"]:
                    best = {**cls, "sign": ph, "region": region}
        if best is None:
            best = {**_DEFAULT, "sign": "", "region": region}
        ranked.append(best)
    ranked.sort(key=lambda x: x["weight"], reverse=True)
    for i, item in enumerate(ranked, 1):
        item["rank"] = i
    return ranked
