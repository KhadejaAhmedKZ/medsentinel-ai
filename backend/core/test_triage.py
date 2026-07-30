"""Fast unit tests for the START logic and allocation — no network needed.

Run:  python -m pytest backend/core/test_triage.py   (or just run this file)
"""
from backend.core.triage import Casualty, Category, triage_all, summarize
from backend.core import allocation, scout, logistics


def test_walking_wounded_is_green():
    c = Casualty(id="C1", can_walk=True, breathing="normal", responsive=True)
    triage_all([c])
    assert c.category == Category.GREEN


def test_absent_breathing_is_black():
    c = Casualty(id="C1", can_walk=False, breathing="absent", responsive=False)
    triage_all([c])
    assert c.category == Category.BLACK


def test_rapid_breathing_is_red():
    c = Casualty(id="C1", can_walk=False, breathing="rapid", responsive=True)
    triage_all([c])
    assert c.category == Category.RED


def test_unresponsive_is_red():
    c = Casualty(id="C1", can_walk=False, breathing="normal", responsive=False)
    triage_all([c])
    assert c.category == Category.RED


def test_critical_sign_overrides_walking():
    c = Casualty(id="C1", can_walk=True, breathing="normal", responsive=True,
                 signs=["arterial bleeding"])
    triage_all([c])
    assert c.category == Category.RED


def test_stable_serious_is_yellow():
    c = Casualty(id="C1", can_walk=False, breathing="normal", responsive=True,
                 signs=["deformed forearm"])
    triage_all([c])
    assert c.category == Category.YELLOW


def test_sorted_most_urgent_first():
    ranked = triage_all([
        Casualty(id="G", can_walk=True, breathing="normal", responsive=True),
        Casualty(id="R", can_walk=False, breathing="rapid", responsive=True),
    ])
    assert ranked[0].id == "R"


def test_allocation_assigns_front_to_red_and_queues_overflow():
    ranked = triage_all([
        Casualty(id="R1", can_walk=False, breathing="rapid", responsive=True),
        Casualty(id="R2", can_walk=False, breathing="rapid", responsive=True),
        Casualty(id="Y1", can_walk=False, breathing="normal", responsive=True,
                 signs=["broken leg"]),
    ])
    plan = allocation.allocate(ranked, front_medics=1, back_medics=1)
    front = [a for a in plan["assignments"] if a["line"] == "front"]
    assert len(front) == 1                     # only 1 front medic
    assert plan["unassigned_red"] == 1         # the other RED is queued
    assert len(plan["back_line_queue"]) == 0   # the YELLOW got the back medic


def test_expectant_never_assigned():
    ranked = triage_all([
        Casualty(id="B1", can_walk=False, breathing="absent", responsive=False),
    ])
    plan = allocation.allocate(ranked, front_medics=3, back_medics=3)
    assert plan["assignments"] == []
    assert len(plan["expectant"]) == 1


def test_scout_approach_points_at_most_urgent():
    ranked = triage_all([
        Casualty(id="R1", x=0.1, can_walk=False, breathing="rapid", responsive=True),
        Casualty(id="G1", x=0.9, can_walk=True, breathing="normal", responsive=True),
    ])
    rep = scout.assess(ranked, ["fire, right side"])
    assert rep["sectors"] == {"left": 1, "centre": 0, "right": 1}
    assert "left" in rep["approach"]        # R1 (RED) is on the left
    assert rep["hazard_count"] == 1


def test_readiness_flags_shortfall():
    reds = [Casualty(id=f"R{i}", can_walk=False, breathing="rapid", responsive=True)
            for i in range(5)]
    ranked = triage_all(reds)
    r = logistics.assess_readiness(ranked, {"blood_packs": 1})
    assert r["items"][0]["need"] == 5 and r["items"][0]["have"] == 1
    assert r["status"] == "critical"


def test_evac_marks_first_red_priority():
    ranked = triage_all([
        Casualty(id="R1", can_walk=False, breathing="rapid", responsive=True),
        Casualty(id="R2", can_walk=False, breathing="rapid", responsive=True),
    ])
    e = logistics.plan_evacuation(ranked)
    assert e["urgent"] == 2 and e["litters_required"] == 2
    assert "Priority" in e["lines"][0]["status"]


def test_clinical_brief_flags_allergy():
    from backend.core.clinical import soldier_brief
    b = soldier_brief({"name": "Test", "blood_type": "O+",
                       "allergies": ["Penicillin"], "medications": ["None"],
                       "conditions": ["None"]})
    assert b["risks"] and b["risks"][0]["level"] == "critical"
    assert "penicillin" in b["risks"][0]["text"].lower()


def test_anatomy_word_boundary_no_false_head():
    from backend.core.anatomy import derive_regions
    # "near" contains "ear", "forearm" contains "ear" — must NOT map to head.
    regions = derive_regions(["deformed left forearm"], "lying near the doorway")
    assert "head" not in regions
    assert "left_arm" in regions


if __name__ == "__main__":
    import sys
    fns = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\nAll {len(fns)} tests passed.")
    sys.exit(0)
