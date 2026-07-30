"""Team allocation — the 'Overseer' logic.

Given the triaged casualties and how many medics are available, decide who
works the **front line** (immediate, life-saving stabilisation of RED
casualties) and who works the **back line** (delayed care, walking wounded,
and evacuation staging of YELLOW/GREEN).

The rule is deliberately simple and explainable:

* Front-line medics are assigned one-to-one to RED casualties in priority
  order. If REDs outnumber medics, the rest form a prioritised front-line
  *queue*.
* Once every RED has a medic (or the front line is full), any spare medics
  drop back to work the highest YELLOW casualties.
* GREEN (walking wounded) are directed to a casualty collection point for the
  back line to reassess — they rarely need a dedicated medic.
* BLACK (expectant) are documented, not assigned, so no resource is pulled
  from a savable casualty. This is the hardest and most important START rule.
"""
from __future__ import annotations

from backend.core.triage import Casualty, Category


def allocate(casualties: list[Casualty], front_medics: int, back_medics: int) -> dict:
    """Return a team plan. ``casualties`` must already be triaged & sorted."""
    reds = [c for c in casualties if c.category == Category.RED]
    yellows = [c for c in casualties if c.category == Category.YELLOW]
    greens = [c for c in casualties if c.category == Category.GREEN]
    blacks = [c for c in casualties if c.category == Category.BLACK]

    assignments: list[dict] = []
    front_queue: list[dict] = []

    medic_no = 1
    available_front = max(front_medics, 0)

    # 1. Front line: one medic per RED, most urgent first.
    for c in reds:
        if available_front > 0:
            assignments.append({
                "medic": f"Front Medic {medic_no}",
                "line": "front",
                "casualty_id": c.id,
                "category": c.category.value,
                "priority": c.priority,
                "task": "Immediate stabilisation (control bleeding / airway).",
            })
            medic_no += 1
            available_front -= 1
        else:
            front_queue.append({
                "casualty_id": c.id,
                "category": c.category.value,
                "priority": c.priority,
                "task": "Awaiting free front-line medic — highest priority.",
            })

    # 2. Spare front-line medics drop back to the most urgent YELLOWs.
    back_no = 1
    yellow_idx = 0
    while available_front > 0 and yellow_idx < len(yellows):
        c = yellows[yellow_idx]
        assignments.append({
            "medic": f"Front Medic {medic_no}",
            "line": "back",
            "casualty_id": c.id,
            "category": c.category.value,
            "priority": c.priority,
            "task": "Delayed care — reassess and treat.",
        })
        medic_no += 1
        available_front -= 1
        yellow_idx += 1

    # 3. Dedicated back-line medics take remaining YELLOWs.
    available_back = max(back_medics, 0)
    while available_back > 0 and yellow_idx < len(yellows):
        c = yellows[yellow_idx]
        assignments.append({
            "medic": f"Back Medic {back_no}",
            "line": "back",
            "casualty_id": c.id,
            "category": c.category.value,
            "priority": c.priority,
            "task": "Delayed care — reassess and treat.",
        })
        back_no += 1
        available_back -= 1
        yellow_idx += 1

    back_queue = [
        {
            "casualty_id": c.id,
            "category": c.category.value,
            "priority": c.priority,
            "task": "Delayed — awaiting back-line medic.",
        }
        for c in yellows[yellow_idx:]
    ]

    collection_point = [
        {"casualty_id": c.id, "category": c.category.value,
         "task": "Direct to casualty collection point; self-evacuate if able."}
        for c in greens
    ]

    expectant = [
        {"casualty_id": c.id, "category": c.category.value,
         "task": "Document. Reassess only if resources free up."}
        for c in blacks
    ]

    return {
        "front_line_medics": front_medics,
        "back_line_medics": back_medics,
        "assignments": assignments,
        "front_line_queue": front_queue,
        "back_line_queue": back_queue,
        "collection_point": collection_point,
        "expectant": expectant,
        "unassigned_red": len(front_queue),
        "advice": _advice(len(reds), front_medics, len(front_queue)),
    }


def _advice(num_red: int, front_medics: int, queued: int) -> str:
    """A one-line commander-facing readiness note."""
    if num_red == 0:
        return "No immediate (RED) casualties. Front line can support back-line care."
    if queued > 0:
        return (
            f"{queued} immediate casualty(ies) have no free medic. "
            f"Request reinforcement or accelerate evacuation of stabilised RED cases."
        )
    return f"All {num_red} immediate casualties have a front-line medic assigned."
