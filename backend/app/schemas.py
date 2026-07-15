from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime

class IncidentMode(str, Enum):
    VOICE = "voice"
    TEXT = "text"

class Language(str, Enum):
    ENGLISH = "en"
    TELUGU = "te"

class IncidentType(str, Enum):
    ROAD_ACCIDENT = "Road Traffic Accident"
    MEDICAL = "Medical Emergency"
    UNKNOWN = "Unknown"

class Severity(str, Enum):
    CRITICAL = "Critical"
    URGENT = "Urgent"
    STABLE = "Stable"

class GPS(BaseModel):
    lat: Optional[float] = None
    lng: Optional[float] = None
    source: str = "unknown"  # "browser" | "caller_described" | "unknown"

class StructuredFacts(BaseModel):
    unconsciousness: bool = False
    breathing_difficulty: bool = False
    severe_bleeding: bool = False
    suspected_cardiac_emergency: bool = False
    head_injury: bool = False
    suspected_fracture: bool = False

class Metrics(BaseModel):
    processingTimeMs: int = 0
    transcriptionTimeMs: int = 0
    parserTimeMs: int = 0

class TimelineEvent(BaseModel):
    event: str
    timestamp: datetime

class SeverityResult(BaseModel):
    severity: Severity
    score: int
    reason: str

class Incident(BaseModel):
    incidentId: str
    timestamp: datetime
    incidentMode: IncidentMode
    language: Language
    incidentType: IncidentType
    severity: Severity
    severityScore: int
    severityReason: str
    victimCount: int
    gps: GPS
    callerTranscript: str
    structuredFacts: StructuredFacts
    metrics: Metrics
    timeline: List[TimelineEvent]
