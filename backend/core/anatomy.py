"""Map free-text injury signs to body-map regions.

The vision agent reports short phrases like "arterial bleeding right thigh".
This turns those into structured region ids the dashboard's body map can
highlight. Purely keyword based and side-aware ("left"/"right").

Region ids used by the front-end SVG:
  head, neck, chest, abdomen, left_arm, right_arm, left_leg, right_leg
"""
from __future__ import annotations

import re

REGIONS = ["head", "neck", "chest", "abdomen",
           "left_arm", "right_arm", "left_leg", "right_leg"]

_PART_KEYWORDS = {
    "head": ["head", "skull", "face", "facial", "jaw", "eye", "ear", "scalp",
             "cranial", "nose", "forehead"],
    "neck": ["neck", "throat", "cervical"],
    "chest": ["chest", "thorax", "thoracic", "rib", "sternum", "lung",
              "breast", "clavicle", "shoulder", "collarbone"],
    "abdomen": ["abdomen", "abdominal", "stomach", "belly", "pelvis",
                "pelvic", "groin", "flank", "hip"],
    "arm": ["arm", "forearm", "upperarm", "elbow", "hand", "wrist", "bicep",
            "tricep", "finger"],
    "leg": ["leg", "thigh", "knee", "shin", "calf", "foot", "ankle",
            "femur", "fibula", "tibia", "toe"],
}


def _side(phrase: str, default: str = "right") -> str:
    if "left" in phrase:
        return "left"
    if "right" in phrase:
        return "right"
    return default


def derive_regions(signs: list[str], note: str = "") -> list[str]:
    """Return the ordered, de-duplicated body regions implicated by the text."""
    phrases = [s.lower() for s in signs] + ([note.lower()] if note else [])
    found: list[str] = []
    for phrase in phrases:
        for part, words in _PART_KEYWORDS.items():
            # Match a keyword only at a word boundary ("ear" won't match
            # "near"/"forearm"); a leading boundary still allows plurals
            # ("rib" -> "ribs", "leg" -> "legs").
            if any(re.search(r"\b" + re.escape(w), phrase) for w in words):
                if part in ("arm", "leg"):
                    region = f"{_side(phrase)}_{part}"
                else:
                    region = part
                if region not in found:
                    found.append(region)
    return found
