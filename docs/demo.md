# LifeSaver.ai (LS.ai) Demo & Presentation Script

This document maps out the live demonstration sequence, timing thresholds, expected judge questions, backup procedures, and fail-safe triggers for LifeSaver.ai.

---

## 1. Demo Script (Step-by-Step)

### Phase 1: Ingestion & In-Memory Live Trigger (0m - 1m)
1. **Action:** Open the **Caller View** on a mobile screen (or chrome viewport-simulated window) alongside the **Responder Dashboard** on the desktop side.
2. **Action:** Press the emergency button. Trigger GPS browser location.
3. **Action:** Speak Telugu: *"నాకు చాతి నొప్పిగా ఉంది, శ్వాస తీసుకోవడం కష్టంగా ఉంది"* (I have chest pain, breathing is difficult).
4. **Action:** Whisper transcribes the audio, auto-detects Telugu, and updates the caller UI labels dynamically to Telugu.

### Phase 2: Live Timeline & Deterministic Severity (1m - 2m)
1. **Action:** The incident pops up instantly in the **Live Incident Feed** (Left Panel) of the Responder Dashboard with a **Critical** badge (color-coded red).
2. **Action:** Click the card. Review the **Lifecycle Timeline** (Center Panel):
   * `INCIDENT_CREATED` -> `TRANSCRIPT_RECEIVED` -> `SEVERITY_COMPUTED` -> `BROADCASTED`.
3. **Action:** Point out the **Metrics telemetry**:
   * Processing time: ~1.8 seconds.
   * Detected Language: Telugu.
   * Severity Score: 100 (due to Critical Overrides).
4. **Action:** Highlight the **Structured Facts** checklist (Right Panel) showing `breathing_difficulty` and `chest_pain` checked, and contrast it with the raw transcript translation.

### Phase 3: Fallback & Graceful Degradation Demo (2m - 3m)
1. **Action:** Turn off browser microphone permissions.
2. **Action:** Notice the Caller UI instantly expands the text fallback area.
3. **Action:** Type a road accident report: *"Car crash on main street, conscious driver with head impact."*
4. **Action:** Show the dashboard update: Severity: **Urgent** (Score: 15 due to head injury, no critical overrides). GPS source labeled as `"caller_described"`.

---

## 2. Demo Timing (3 Minutes Max)
* **0:00 - 0:30:** The Problem & Vision (PANIC vs. STRUCTURED ACTION).
* **0:30 - 1:15:** Live Voice Emergency Demo (Telugu -> Whisper -> Live Broadcaster).
* **1:15 - 2:00:** Responder UI Walkthrough (Timeline, Severity Override explanation, metrics).
* **2:00 - 2:30:** Fail-safe & Geolocation fallback demo (Text mode + caller-described GPS).
* **2:30 - 3:00:** Summary & Closing (Initial LS father/mother tribute, V1 MVP lock).

---

## 3. Judge Questions & Defensible Answers

#### Q: Why not let the LLM output the severity rating directly?
**A:** *"LLMs are highly non-deterministic and can return different severity ratings for identical symptoms depending on prompt styling. In emergency response, this variability is unacceptable. We isolate the LLM's role to parsing unstructured text into boolean facts, while our Python severity engine runs deterministic override rules and point rubrics. This makes the classification 100% reproducible and explainable to medical coordinators."*

#### Q: How does the system work if internet connectivity drops?
**A:** *"LifeSaver.ai is designed as a swappable modular pipeline. In this hackathon MVP, we use hosted Whisper and OpenAI APIs for deployment speed. However, the backend services operate through standard interfaces. We can swap the hosted ASR service with an on-device local engine (like Whisper.cpp or ONNX) and the parser with a local LLM running in-house, enabling fully offline operation."*

#### Q: Why did you choose Telugu as your second language?
**A:** *"We wanted to prove true zero-config multilingual ingestion. The caller speaks Telugu, the backend detects it automatically on transcription, and the dashboard translates it for the responder in real time. We chose Telugu to demonstrate authentic local utility without bloating our V1 scope."*

---

## 4. Failure Cases & Backup Demo Plan

| Risk | Diagnostic | Backup Action |
| :--- | :--- | :--- |
| **OpenAI Whisper API Outage** | Audio upload returns 502/Timeout | Shift the caller UI to **Text Fallback Mode** instantly. The user types the text directly. |
| **Emergency Context Parser Failure** | LLM parsing returns parsing error | Trigger **Raw Transcript Mode**: Backend bypasses structure extraction, flags severity as `"Urgent"` for safety, and streams the raw transcript text directly to the responder. |
| **GPS Geolocation Denied** | Geolocation error handler fires | UI falls back to manual text entry for address/landmarks. Sets GPS source to `"caller_described"`. |
| **WebSocket Connection Drops** | Socket client disconnected | Automatic exponential backoff reconnect loop in dashboard. |
| **Hosted Backend Sleeps (Render free tier)** | First request latency spike | Pre-warm the backend by sending a `/health` request 5 minutes before the presentation starts. |
