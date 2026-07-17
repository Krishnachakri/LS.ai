import uuid
import datetime
import time
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional

from ...schemas import Incident, GPS, StructuredFacts, Metrics, TimelineEvent, IncidentMode, Language, IncidentType, Severity
from ...realtime_incident_cache import incidents_cache
from ...websocket_manager import manager
from ...services.speech_transcriber import SpeechTranscriberService
from ...services.context_parser import EmergencyContextParser, ParserException
from ...services.validator import EmergencyContextValidator
from ...services.severity_rubric import evaluate_incident_severity

router = APIRouter()

# Instantiate services
asr_service = SpeechTranscriberService()
parser_service = EmergencyContextParser()

async def run_websocket_broadcast(message: dict):
    """Asynchronous background wrapper to execute and measure WebSocket broadcasting."""
    broadcast_start = time.perf_counter()
    try:
        await manager.broadcast(message)
    except Exception as e:
        print(f"[Telemetry] WebSocket Broadcast failed: {e}")
    broadcast_elapsed = int((time.perf_counter() - broadcast_start) * 1000)
    print(f"[Telemetry] WebSocket Broadcast: {broadcast_elapsed} ms")

async def broadcast_progress(incident_id: str, stage: str, message: str):
    try:
        await manager.broadcast({
            "event": "INCIDENT_PROGRESS",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "payload": {
                "incidentId": incident_id,
                "stage": stage,
                "message": message
            }
        })
    except Exception as e:
        print(f"[Telemetry] Progress broadcast failed: {e}")

@router.get("", response_model=list[Incident])
def get_incidents():
    """
    Returns the last 20 cached incidents.
    Used for initial page loads of historical data.
    """
    return list(incidents_cache)

@router.post("/report")
async def report_incident(
    background_tasks: BackgroundTasks,
    audio: Optional[UploadFile] = File(None),
    text_fallback: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    language_code: Optional[str] = Form(None),
    incidentMode: str = Form("voice"),  # "voice" | "text"
    incident_id: Optional[str] = Form(None)
):
    """
    Ingests an emergency description (audio or text), transcribes it in-memory,
    extracts structured facts, calculates severity, broadcasts to dispatch dashboard,
    and logs precise performance metrics.
    """
    total_start = time.perf_counter()
    now = datetime.datetime.now(datetime.timezone.utc)

    if not audio and not text_fallback:
        raise HTTPException(status_code=400, detail="Missing emergency voice or text input")

    if not incident_id:
        incident_id = str(uuid.uuid4())
        
    await broadcast_progress(incident_id, "received", "Audio Received")
    
    # Initialize metric timers
    transcription_time_ms = 0
    parser_time_ms = 0
    
    caller_transcript = ""
    detected_lang_str = language_code or "en"

    if audio and incidentMode == "voice":
        try:
            await broadcast_progress(incident_id, "transcribing", "Transcribing Voice...")
            asr_start = time.perf_counter()
            content = await audio.read()
            
            asr_result = asr_service.transcribe_bytes(content, filename=audio.filename)
            caller_transcript = asr_result["transcript"]
            detected_lang_str = asr_result["language"]
            
            transcription_time_ms = int((time.perf_counter() - asr_start) * 1000)
            
        except Exception as e:
            # If ASR fails, fall back to text_fallback if provided, otherwise raise error
            print(f"[!] ASR Ingestion pipeline failure: Type={type(e).__name__}, Error={str(e)}")
            import traceback
            traceback.print_exc()
            if text_fallback:
                caller_transcript = text_fallback
                incidentMode = "text"
            else:
                raise HTTPException(status_code=500, detail=f"ASR Transcribe Error: {e}")
    else:
        caller_transcript = text_fallback or ""
        incidentMode = "text"

    try:
        lang_enum = Language(detected_lang_str)
    except ValueError:
        lang_enum = Language.ENGLISH

    # Parse Emergency Context with Graceful Degradation
    try:
        await broadcast_progress(incident_id, "extracting", "Extracting Emergency Facts...")
        parsed_context, parser_time_ms = parser_service.parse_transcript(caller_transcript)
        
        validated_context = EmergencyContextValidator.validate_and_sanitize(parsed_context)
        
        extracted_facts = validated_context.structured_facts
        extracted_type = validated_context.incident_type
        extracted_victim_count = validated_context.victim_count

        await broadcast_progress(incident_id, "computing", "Computing Severity...")
        severity_start = time.perf_counter()
        severity_result = evaluate_incident_severity(extracted_facts, extracted_victim_count)
        severity_elapsed = int((time.perf_counter() - severity_start) * 1000)
        print(f"[Telemetry] Severity Engine calculation: {severity_elapsed} ms")
        
        severity_enum = severity_result.severity
        severity_score = severity_result.score
        severity_reason = severity_result.reason

    except (ParserException, Exception) as e:
        # --- GRACEFUL DEGRADATION: RAW TRANSCRIPT FALLBACK ---
        print(f"[!] Context Parser pipeline failure: Type={type(e).__name__}, Error={str(e)}")
        import traceback
        traceback.print_exc()
        
        extracted_facts = StructuredFacts()
        extracted_type = IncidentType.MEDICAL
        extracted_victim_count = 1
        
        severity_enum = Severity.URGENT
        severity_score = 15
        severity_reason = f"Raw Transcript Mode: AI parser bypassed due to timeout/error: {type(e).__name__}."
        parser_time_ms = 0
    gps_lat = latitude
    gps_lng = longitude
    gps_src = "browser" if (latitude is not None and longitude is not None) else "unknown"

    total_processing_ms = int((time.perf_counter() - total_start) * 1000)
    
    mock_timeline = [
        TimelineEvent(event="INCIDENT_CREATED", timestamp=now),
        TimelineEvent(event="TRANSCRIPT_RECEIVED", timestamp=now),
        TimelineEvent(event="SEVERITY_COMPUTED", timestamp=now),
        TimelineEvent(event="BROADCASTED", timestamp=now)
    ]
    
    incident = Incident(
        incidentId=incident_id,
        timestamp=now,
        incidentMode=IncidentMode(incidentMode),
        language=lang_enum,
        incidentType=extracted_type,
        severity=severity_enum,
        severityScore=severity_score,
        severityReason=severity_reason,
        victimCount=extracted_victim_count,
        gps=GPS(lat=gps_lat, lng=gps_lng, source=gps_src),
        callerTranscript=caller_transcript,
        structuredFacts=extracted_facts,
        metrics=Metrics(
            processingTimeMs=total_processing_ms,
            transcriptionTimeMs=transcription_time_ms,
            parserTimeMs=parser_time_ms
        ),
        timeline=mock_timeline
    )

    # Cache immediately
    incident_json = incident.model_dump(mode='json')
    incidents_cache.appendleft(incident_json)
    
    await broadcast_progress(incident_id, "broadcasting", "Alerting Responders...")
    background_tasks.add_task(
        run_websocket_broadcast,
        {
            "event": "NEW_INCIDENT",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "payload": incident_json
        }
    )
    
    await broadcast_progress(incident_id, "sent", "Emergency Sent")
    
    total_time_ms = int((time.perf_counter() - total_start) * 1000)
    print(f"[Telemetry] Total request processing: {total_time_ms} ms")
    
    # Return JSONResponse directly to avoid double validation/serialization of the model
    return JSONResponse(content=incident_json)

