import os
import uuid
import datetime
import time
import tempfile
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
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

@router.get("", response_model=list[Incident])
def get_incidents():
    """
    Returns the last 20 cached incidents.
    Used for initial page loads of historical data.
    """
    return list(incidents_cache)

@router.post("/report", response_model=Incident)
async def report_incident(
    audio: Optional[UploadFile] = File(None),
    text_fallback: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    language_code: Optional[str] = Form(None),
    incidentMode: str = Form("voice")  # "voice" | "text"
):
    """
    Ingests an emergency description (audio or text), transcribes it using Whisper,
    extracts structured facts using the Emergency Context Parser, sanitizes data via the Validator,
    calculates severity deterministically, and broadcasts it in real-time.
    """
    total_start = time.perf_counter()
    now = datetime.datetime.now(datetime.timezone.utc)
    
    # 1. Validation check
    if not audio and not text_fallback:
        raise HTTPException(status_code=400, detail="Missing emergency voice or text input")

    incident_id = str(uuid.uuid4())
    
    # Initialize metric timers
    transcription_time_ms = 0
    parser_time_ms = 0
    
    caller_transcript = ""
    detected_lang_str = language_code or "en"

    # 2. Ingest Voice (if audio uploaded)
    if audio and incidentMode == "voice":
        try:
            asr_start = time.perf_counter()
            
            # Save UploadFile to a temporary file for processing
            suffix = os.path.splitext(audio.filename)[1] if audio.filename else ".tmp"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_audio:
                content = await audio.read()
                temp_audio.write(content)
                temp_path = temp_audio.name

            try:
                # Transcribe via SpeechTranscriber
                asr_result = asr_service.transcribe(temp_path)
                caller_transcript = asr_result["transcript"]
                detected_lang_str = asr_result["language"]
            finally:
                # Cleanup temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
            transcription_time_ms = int((time.perf_counter() - asr_start) * 1000)
            
        except Exception as e:
            # If ASR fails, fall back to text_fallback if provided, otherwise raise error
            import traceback
            traceback.print_exc()
            if text_fallback:
                caller_transcript = text_fallback
                incidentMode = "text"
            else:
                raise HTTPException(status_code=500, detail=f"ASR Transcribe Error: {e}")
    else:
        # Direct Text Input Ingestion
        caller_transcript = text_fallback or ""
        incidentMode = "text"

    # Parse detected language code
    try:
        lang_enum = Language(detected_lang_str)
    except ValueError:
        lang_enum = Language.ENGLISH

    # 3. Parse Emergency Context with Graceful Degradation
    try:
        # Call LLM Parser
        parsed_context, parser_time_ms = parser_service.parse_transcript(caller_transcript)
        
        # Run pipeline validator step
        validated_context = EmergencyContextValidator.validate_and_sanitize(parsed_context)
        
        extracted_facts = validated_context.structured_facts
        extracted_type = validated_context.incident_type
        extracted_victim_count = validated_context.victim_count

        # Run deterministic severity calculation
        severity_result = evaluate_incident_severity(extracted_facts, extracted_victim_count)
        
        severity_enum = severity_result.severity
        severity_score = severity_result.score
        severity_reason = severity_result.reason

    except (ParserException, Exception) as e:
        # --- GRACEFUL DEGRADATION: RAW TRANSCRIPT FALLBACK ---
        import traceback
        traceback.print_exc()
        
        extracted_facts = StructuredFacts()  # Empty flags (default false)
        extracted_type = IncidentType.MEDICAL # Safety default
        extracted_victim_count = 1
        
        # Safe default severity for unparsed incidents
        severity_enum = Severity.URGENT
        severity_score = 15
        severity_reason = "Raw Transcript Mode: AI parser bypassed due to service timeout/error."
        parser_time_ms = 0

    # 4. Construct GPS Details
    gps_lat = latitude
    gps_lng = longitude
    gps_src = "browser" if (latitude is not None and longitude is not None) else "unknown"

    # 5. Formulate Timeline & Metrics
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

    # 6. Cache and Broadcast in real-time
    incident_json = incident.model_dump(mode='json')
    incidents_cache.appendleft(incident_json)
    
    await manager.broadcast({
        "event": "NEW_INCIDENT",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "payload": incident_json
    })
    
    return incident
