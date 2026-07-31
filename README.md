# MEDSENTINEL AI

**Multi-agent, camera-driven mass-casualty triage & medical-team allocation — a
decision-support prototype.**

### ▶️ Live demo: https://khadejaahmedkz.github.io/medsentinel-ai/

The live demo runs **entirely in your browser** (no server, no sign-in) on a
built-in sample scene — pick a role and explore. For live image analysis, run
the backend locally with a `GEMINI_API_KEY` (see below).

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

## The agent team — all 8 built

| Persona | Role | Where |
|---|---|---|
| 🧭 **Scout** | Reports scene hazards and a safe-approach recommendation + sector breakdown | `core/scout.py` |
| 🎯 **Triage** | Scans the scene image, detects casualties + hazards, reports START inputs | `agents/triage_agent.py` |
| 🩺 **Dr. Sentinel** | Per-casualty MARCH clinical prompts + NFC history summary & allergy/drug risk flags | `core/clinical.py` |
| ✍️ **Scribe** | Treatment log from quick-adds + voice dictation; downloadable casualty report | frontend (Web Speech API) |
| 🛡️ **Guardian** | Medic stress from real workload → break prompt, breathing exercise, calming tone | frontend |
| 🛰️ **Overseer** | Allocates the team front/back line and summarises for the commander | `core/allocation.py` + route |
| 📦 **Logistician** | Medical readiness (supplies have/need) + MEDEVAC plan | `core/logistics.py` |
| 🏛️ **Architect** | After-action review compiled from the session + auto recommendations | frontend |

The categorisation logic lives in [`backend/core/triage.py`](backend/core/triage.py)
as an explicit, auditable START decision tree — **not** inside the model. The
vision model only reports observations; the rule decides the category.

Three roles, each with a tailored view: **Medic** (triage cards, body maps, NFC
scan, clinical prompts, Scribe, Guardian), **Commander** (Scout, allocation,
evacuation, readiness, Overseer, Architect AAR), **Soldier** (NFC medical record).

## Architecture

```
camera / photo / live webcam
      │
      ▼
🧭 Scout ◄─ hazards ─ 🎯 Triage agent ─(observations JSON)─► core/triage.py (START rank)
                            │                                        │
                     (offline: sample scene)                        ▼
   🩺 Dr. Sentinel ◄─ NFC brief ── /api/soldiers/{id}/brief    core/allocation.py (front/back)
                                                                     │
   📦 Logistician (readiness + evac) ◄───────────────────────────────┤
                                                                     ▼
   ✍️ Scribe · 🛡️ Guardian (medic view)          🛰️ Overseer + 🏛️ Architect (commander) ─► dashboard
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
