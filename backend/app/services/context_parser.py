import time
import os
import logging
from openai import OpenAI, APIConnectionError, APITimeoutError
from pydantic import BaseModel, Field
from ..core.config import settings
from ..schemas import StructuredFacts, IncidentType

# Set up logging for emergency context parsing
logger = logging.getLogger("lifesaver.parser")
logging.basicConfig(level=logging.INFO)

# Custom Exception Hierarchy for production-quality error handling
class ParserException(Exception):
    """Base exception for parsing errors."""
    pass

class ParserUnavailable(ParserException):
    """Raised when OpenAI API is unreachable or times out."""
    pass

class ParserRefusal(ParserException):
    """Raised when the LLM refuses to parse the transcript."""
    pass

class InvalidParserOutput(ParserException):
    """Raised when the parsed JSON does not match the expected schema."""
    pass

class ParsedEmergencyContext(BaseModel):
    incident_type: IncidentType = Field(
        ..., 
        description="The category of the emergency. Must be 'Road Traffic Accident' for collisions, crashes, or vehicle/pedestrian impacts. Must be 'Medical Emergency' for physiological emergencies, falls, or cardiac events. Default to 'Medical Emergency' if uncertain — never output 'Unknown'."
    )
    victim_count: int = Field(
        1, 
        description="Estimated number of injured victims. If unclear, default to 1."
    )
    structured_facts: StructuredFacts = Field(
        ..., 
        description="Structured boolean flags representing present symptoms or injuries. Set true only if mentioned or strongly implied."
    )

class EmergencyContextParser:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def parse_transcript(self, transcript: str) -> tuple[ParsedEmergencyContext, int]:
        """
        Uses OpenAI's Structured Outputs API or Gemini's Structured JSON API to extract
        Pydantic structured facts from raw transcripts.
        
        Returns a tuple of (ParsedEmergencyContext, parser_time_ms).
        """
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        if gemini_key:
            return self._parse_transcript_gemini(transcript, gemini_key)

        if not self.client:
            raise ParserUnavailable("Parser service temporarily unavailable.")

        system_prompt = (
            "You are an Emergency Information Extraction System for LifeSaver.ai. "
            "Your task is ONLY to convert caller descriptions into structured factual information. "
            "Do NOT diagnose. "
            "Do NOT recommend treatment. "
            "Do NOT assume facts not present in the text. "
            "If uncertain, leave the corresponding field false. "
            "Your output must strictly follow the schema. "
            "Never select 'Unknown' for incident category; default to 'Medical Emergency' if unclear."
        )

        max_attempts = 2
        last_error = None
        
        for attempt in range(1, max_attempts + 1):
            try:
                start_time = time.perf_counter()
                
                completion = self.client.beta.chat.completions.parse(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Transcript: \"{transcript}\""}
                    ],
                    response_format=ParsedEmergencyContext,
                    temperature=0.0,
                    timeout=10.0
                )
                
                elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                
                parsed_message = completion.choices[0].message
                if parsed_message.refusal:
                    raise ParserRefusal("Emergency context parsing refused by model.")
                    
                return parsed_message.parsed, elapsed_ms

            except (APIConnectionError, APITimeoutError) as e:
                last_error = e
                logger.warning(f"OpenAI API attempt {attempt} failed: {e}. Retrying..." if attempt < max_attempts else "")
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Pydantic validation failed: {e}")
                raise InvalidParserOutput("Invalid parser output format.")

        logger.error(f"OpenAI service unavailable after {max_attempts} attempts. Internal error: {last_error}")
        raise ParserUnavailable("Parser service temporarily unavailable.")

    def _parse_transcript_gemini(self, transcript: str, gemini_key: str) -> tuple[ParsedEmergencyContext, int]:
        import httpx
        import json
        
        start_time = time.perf_counter()
        
        system_prompt = (
            "You are an Emergency Information Extraction System for LifeSaver.ai. "
            "Your task is ONLY to convert caller descriptions into structured factual information. "
            "Do NOT diagnose. "
            "Do NOT recommend treatment. "
            "Do NOT assume facts not present in the text. "
            "If uncertain, leave the corresponding field false. "
            "Your output must strictly follow the schema. "
            "Never select 'Unknown' for incident category; default to 'Medical Emergency' if unclear."
        )
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={gemini_key}"
        
        # Define JSON response schema matching ParsedEmergencyContext
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"Transcript: \"{transcript}\""}
                    ]
                }
            ],
            "systemInstruction": {
                "parts": [
                    {"text": system_prompt}
                ]
            },
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": {
                    "type": "OBJECT",
                    "properties": {
                        "incident_type": {
                            "type": "STRING",
                            "enum": ["Road Traffic Accident", "Medical Emergency"]
                        },
                        "victim_count": {
                            "type": "INTEGER"
                        },
                        "structured_facts": {
                            "type": "OBJECT",
                            "properties": {
                                "unconsciousness": {"type": "BOOLEAN"},
                                "breathing_difficulty": {"type": "BOOLEAN"},
                                "severe_bleeding": {"type": "BOOLEAN"},
                                "suspected_cardiac_emergency": {"type": "BOOLEAN"},
                                "head_injury": {"type": "BOOLEAN"},
                                "suspected_fracture": {"type": "BOOLEAN"}
                            },
                            "required": [
                                "unconsciousness",
                                "breathing_difficulty",
                                "severe_bleeding",
                                "suspected_cardiac_emergency",
                                "head_injury",
                                "suspected_fracture"
                            ]
                        }
                    },
                    "required": ["incident_type", "victim_count", "structured_facts"]
                }
            }
        }
        
        headers = {"Content-Type": "application/json"}
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                raise ParserUnavailable(f"Gemini API returned error {response.status_code}: {response.text}")
                
            data = response.json()
            try:
                text_out = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed_json = json.loads(text_out)
                
                # Convert incident_type string to enum
                inc_type_str = parsed_json.get("incident_type", "Medical Emergency")
                if inc_type_str == "Road Traffic Accident":
                    inc_type_val = IncidentType.ROAD_ACCIDENT
                else:
                    inc_type_val = IncidentType.MEDICAL
                    
                sf_json = parsed_json.get("structured_facts", {})
                sf = StructuredFacts(
                    unconsciousness=sf_json.get("unconsciousness", False),
                    breathing_difficulty=sf_json.get("breathing_difficulty", False),
                    severe_bleeding=sf_json.get("severe_bleeding", False),
                    suspected_cardiac_emergency=sf_json.get("suspected_cardiac_emergency", False),
                    head_injury=sf_json.get("head_injury", False),
                    suspected_fracture=sf_json.get("suspected_fracture", False)
                )
                
                parsed_context = ParsedEmergencyContext(
                    incident_type=inc_type_val,
                    victim_count=parsed_json.get("victim_count", 1),
                    structured_facts=sf
                )
                
                elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                return parsed_context, elapsed_ms
            except Exception as e:
                logger.error(f"Gemini parsing/validation failed: {e}. Raw: {text_out}")
                raise InvalidParserOutput("Invalid parser output format.")
