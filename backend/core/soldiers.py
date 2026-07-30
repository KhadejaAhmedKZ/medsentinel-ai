"""Sample soldier medical profiles (the data an NFC dog-tag would unlock).

Static demo data for the Soldier role and, later, for matching an identified
casualty to their record. Not real people.
"""
from __future__ import annotations

SOLDIERS = [
    {
        "id": "SD-4471",
        "name": "Cpl. A. Rahman",
        "rank": "Corporal",
        "unit": "2nd Field Company",
        "blood_type": "O+",
        "allergies": ["Penicillin"],
        "medications": ["None"],
        "conditions": ["Mild asthma"],
        "last_updated": "2026-05-12",
        "notes": "Carries a personal tourniquet, left cargo pocket.",
    },
    {
        "id": "SD-3820",
        "name": "Sgt. L. Osei",
        "rank": "Sergeant",
        "unit": "1st Recon Platoon",
        "blood_type": "A-",
        "allergies": ["Latex", "Sulfa drugs"],
        "medications": ["Lisinopril 10mg"],
        "conditions": ["Hypertension"],
        "last_updated": "2026-06-30",
        "notes": "Prior right-knee reconstruction (2024).",
    },
    {
        "id": "SD-9155",
        "name": "Pvt. M. Haddad",
        "rank": "Private",
        "unit": "3rd Support Company",
        "blood_type": "B+",
        "allergies": ["None known"],
        "medications": ["None"],
        "conditions": ["None"],
        "last_updated": "2026-07-19",
        "notes": "No significant medical history.",
    },
]

BY_ID = {s["id"]: s for s in SOLDIERS}
