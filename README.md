# LifeSaver.ai (LS.ai)

**LifeSaver.ai (LS.ai)** is a real-time AI-powered emergency coordination platform that transforms unstructured emergency voice or text reports into structured, actionable incident summaries for dispatchers and responders. By combining explainable AI parsing with deterministic severity scoring, it optimizes triage routing to save lives during critical first-response minutes.

---

## Why We Built This
LifeSaver.ai was created with a simple purpose: to help reduce the communication delays that often occur during the first few minutes of a medical emergency. 

The name **LS** has a personal meaning. It represents **Lokesh** and **Sasi**, my parents. The project is inspired by my family's experience and my belief that better coordination during emergencies can save lives. While the inspiration is personal, the mission is universal—to make emergency communication faster, clearer, and more reliable.

---

## Problem & Solution
- **The Problem:** Panicked emergency callers struggle to convey structured facts (incident type, victim counts, injuries). Language barriers and lack of automated triage delay dispatch, costing precious seconds.
- **The Solution:** A direct, zero-install mobile caller interface with automatic multi-lingual speech transcription that pipes unstructured data into a deterministic triage engine, instantly broadcasting parsed emergencies to a professional dispatch-console.

---

## Tech Stack
* **Frontend:** Next.js (App Router), TypeScript, Vanilla CSS (RapidSOS-inspired dashboard console styling)
* **Backend:** FastAPI (Python), Uvicorn ASGI Server
* **AI Ingestion (Multimodal Transcription):** Gemini API (Multimodal Audio Transcription)
* **AI Parser (Emergency Context Extraction):** Gemini API (Structured JSON Schema generation)
* **Realtime Protocol:** WebSockets (`/api/v1/incidents/live`)
* **State Management:** In-memory `collections.deque` cache (holds last 20 active incidents for live display)

---

## Architecture & System Flow

```text
Caller Mobile UI (Microphone/Text Input)
          │
          ▼
 FastAPI Backend Ingestion API
          │
          ├──► Stage A: Multimodal Audio Transcription (Gemini API)
          │      Extracts raw text transcript & detects language (en/te)
          │
          ├──► Stage B: Emergency Context Parser (Gemini API)
          │      Extracts structured JSON facts (breathing difficulty, bleeding, etc.)
          │
          ├──► Stage C: Pydantic Validator & Schema Sanitation
          │
          ├──► Stage D: Deterministic Severity Triage Engine
          │      Evaluates override triggers and calculates safety priority scores
          │
          └──► Stage E: Real-time Gateway (FastAPI WebSockets)
                    │
                    ▼
     Responder Dispatch Dashboard Console (Live Updates)
```

---

## Severity Logic
To guarantee 100% explainable and reproducible decisions, we separate language comprehension from triage scoring. The LLM parses unstructured facts; a deterministic Python rules engine computes severity:

1. **Critical Overrides:** Unconsciousness, severe breathing difficulty, chest pain, or suspected cardiac emergency immediately overrides the scoring logic and sets severity to **Critical** (Score 100).
2. **Point Rubric:** If no overrides trigger, points accumulate:
   * Suspected skeletal fracture: **+15 points**
   * Head injury: **+15 points**
   * Multiple victims (>2): **+10 points**
3. **Threshold Classifications:** 
   * **Critical:** Overrides triggered OR Score >= 40
   * **Urgent:** Score 15 - 39
   * **Stable:** Score < 15

---

## Setup & Local Run Instructions

### 1. Prerequisites
- Python 3.10+
- Node.js 18+

### 2. Environment Variables Configuration

Create a `.env` file in the `backend/` directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Create a `.env.local` file in the `frontend/` directory:
```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

### 3. Run Backend
From the root workspace directory:
```bash
cd backend
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 4. Run Frontend
From the root workspace directory in a new terminal tab:
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:3000/caller](http://localhost:3000/caller) for the Mobile Caller portal, and [http://localhost:3000/dashboard](http://localhost:3000/dashboard) to view the dispatch dashboard.

---

## Current Known Limitations
> [!WARNING]
> **Voice transcription and fact parsing depend on an external Gemini API key quota.** Local voice functionality requires an active Gemini developer quota. If the quota is exhausted (generating HTTP 429), the backend gracefully degrades to Raw Transcript / Text fallback mode to keep the emergency pipeline operational.
