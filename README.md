# MEDSENTINEL AI

**Multi-agent, camera-driven mass-casualty triage & medical-team allocation — a
decision-support prototype.**

Point a camera at a scene of injured people. MEDSENTINEL detects each casualty,
scores them with the international **START** triage protocol
(🔴 Immediate / 🟡 Delayed / 🟢 Minor / ⚫ Expectant), ranks them most-urgent-first,
and allocates the medical team into a **front line** (immediate stabilisation of
the critical) and a **back line** (delayed care + evacuation staging).

> ⚠️ **Scope & safety.** This is a *simulation / training* decision-support tool.
> It suggests a prioritisation to assist a human; a qualified medic is
> responsible for every triage and treatment decision. It is not wired to any
> weapon, targeting, or live operational system.

---

## The agent team

| Persona | Role | Status |
|---|---|---|
| 🎯 **Triage** | Scans the scene image, detects casualties, reports observable START inputs | ✅ working (Gemini vision + offline sample scene) |
| 🛰️ **Overseer** | Allocates the team front/back line and summarises for the commander | ✅ working |
| 🩺 **Dr. Sentinel** | Clinical decision support per casualty | 🔜 prompt ready (`ai/prompts.py`) |
| ✍️ Scribe · 🛡️ Guardian · 📦 Logistician · 🧭 Scout · 🏛️ Architect | see proposal | 🔜 roadmap |

The categorisation logic lives in [`backend/core/triage.py`](backend/core/triage.py)
as an explicit, auditable START decision tree — **not** inside the model. The
vision model only reports observations; the rule decides the category.

## Architecture

```
camera / photo
      │
      ▼
🎯 Triage agent  ──(observations JSON)──►  core/triage.py  (START scoring + rank)
      │                                          │
   (offline: sample scene)                       ▼
                                          core/allocation.py  (front / back line)
                                                 │
                                                 ▼
                                          🛰️ Overseer summary  ──►  dashboard
```

## Run it

```bash
cd ~/Desktop/MEDSENTINEL
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # optional: add a GEMINI_API_KEY for live vision
uvicorn backend.main:app --reload
```

Open **http://localhost:8000/** for the dashboard, or **/docs** for the API.

- **No API key?** It runs fully offline on a built-in 4-casualty sample scene.
- **With a key?** Upload a real photo and the Triage agent reads it live.

## Test

```bash
python -m backend.core.test_triage
```

## API

`POST /api/scan` — multipart: `image` (optional), `front_medics`, `back_medics`
→ returns triaged casualties, category summary, team allocation, and the
Overseer summary. `GET /api/health`, `GET /api/agents`.

## Adapted from Sanadi AI

Reuses the Sanadi multi-agent patterns — the async Gemini wrapper with graceful
offline degradation, the persona/agent base class, and JSON-structured
multimodal calls — retargeted from a patient companion to battlefield
mass-casualty coordination.
