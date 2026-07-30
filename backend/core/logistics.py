"""Logistician — medical readiness and evacuation planning.

Two commander-facing outputs derived from the triaged casualties:

* **Readiness** — compares on-hand supplies against demand implied by the
  casualties (each RED needs a tourniquet + blood pack + litter, etc.) and
  flags shortfalls.
* **Evacuation** — a simple MEDEVAC picture: who needs urgent evac, how many
  litters, and a placeholder ETA the commander can override.

All deterministic and offline-safe. Inventory is demo data; a real deployment
would read it from a supply system.
"""
from __future__ import annotations

from backend.core.triage import Casualty, Category

# On-hand demo inventory.
DEFAULT_INVENTORY = {
    "tourniquets": 6,
    "blood_packs": 4,
    "litters": 3,
    "iv_kits": 8,
    "chest_seals": 5,
}

# Per-category demand (units consumed per casualty).
_DEMAND = {
    Category.RED: {"tourniquets": 1, "blood_packs": 1, "litters": 1,
                   "iv_kits": 1, "chest_seals": 1},
    Category.YELLOW: {"litters": 1, "iv_kits": 1},
    Category.GREEN: {},
    Category.BLACK: {},
}

_LABELS = {
    "tourniquets": "Tourniquets", "blood_packs": "Blood packs",
    "litters": "Litters", "iv_kits": "IV kits", "chest_seals": "Chest seals",
}


def assess_readiness(casualties: list[Casualty], inventory: dict | None = None) -> dict:
    inv = dict(inventory or DEFAULT_INVENTORY)
    need = {k: 0 for k in inv}
    for c in casualties:
        for item, qty in _DEMAND.get(c.category, {}).items():
            need[item] = need.get(item, 0) + qty

    items = []
    worst = "ok"
    for key in inv:
        have, want = inv[key], need.get(key, 0)
        if want == 0:
            status = "ok"
        elif have >= want:
            status = "ok"
        elif have >= want * 0.5:
            status = "low"
        else:
            status = "critical"
        if status == "critical" or (status == "low" and worst != "critical"):
            worst = status
        items.append({"item": _LABELS.get(key, key), "have": have,
                      "need": want, "status": status})

    return {"status": worst, "items": items}


def plan_evacuation(casualties: list[Casualty]) -> dict:
    """Simple MEDEVAC picture. Priority = urgent evac (RED), routine = YELLOW."""
    reds = [c for c in casualties if c.category == Category.RED]
    yellows = [c for c in casualties if c.category == Category.YELLOW]

    lines = []
    for i, c in enumerate(reds):
        lines.append({
            "casualty_id": c.id, "precedence": "URGENT",
            "status": "Priority MEDEVAC requested" if i == 0 else "MEDEVAC requested",
            "eta_min": 10 + i * 5,
        })
    for c in yellows:
        lines.append({
            "casualty_id": c.id, "precedence": "ROUTINE",
            "status": "Routine evacuation", "eta_min": None,
        })

    return {
        "urgent": len(reds),
        "routine": len(yellows),
        "litters_required": len(reds) + len(yellows),
        "lines": lines,
    }
