import os
import base64
import httpx
from typing import Optional
from openai import OpenAI
from ..core.config import settings


class SpeechTranscriberService:
    def __init__(self):
        self.openai_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")
        self.gemini_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        self.gemini_model = settings.GEMINI_MODEL
        self.client = OpenAI(api_key=self.openai_key) if self.openai_key else None

    def transcribe(self, file_path: str) -> dict:
        """
        Sends local audio file to OpenAI's Whisper API or Gemini's Multimodal Audio API for speech-to-text.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found at: {file_path}")
        
        with open(file_path, "rb") as f:
            audio_data = f.read()
            
        return self.transcribe_bytes(audio_data, filename=os.path.basename(file_path))

    def transcribe_bytes(self, audio_data: bytes, filename: Optional[str] = None) -> dict:
        """
        Transcribes audio data directly from memory, bypassing disk writes.
        """
        # Gemini Multimodal Audio Transcription Pathway
        if self.gemini_key:
            return self._transcribe_gemini_bytes(audio_data, filename)

        # OpenAI Whisper Ingestion Pathway
        if not self.client:
            raise ValueError("OpenAI API Key is not configured. Please set the OPENAI_API_KEY environment variable.")
        
        import io
        import time
        
        buffer = io.BytesIO(audio_data)
        buffer.name = filename or "recording.webm"
        
        asr_start = time.perf_counter()
        response = self.client.audio.transcriptions.create(
            model="whisper-1",
            file=buffer,
            response_format="verbose_json"
        )
        asr_elapsed = int((time.perf_counter() - asr_start) * 1000)
        print(f"[Telemetry] OpenAI Whisper ASR Response Time: {asr_elapsed} ms")
        
        parse_start = time.perf_counter()
        transcript_text = getattr(response, "text", "")
        detected_lang = getattr(response, "language", "english")
        
        lang_lower = detected_lang.lower()
        lang_code = "te" if ("telugu" in lang_lower or lang_lower == "te") else "en"
        parse_elapsed = int((time.perf_counter() - parse_start) * 1000)
        print(f"[Telemetry] OpenAI ASR Parsing & Mapping: {parse_elapsed} ms")
            
        return {
            "transcript": transcript_text,
            "language": lang_code
        }

    def _transcribe_gemini_bytes(self, audio_data: bytes, filename: Optional[str] = None) -> dict:
        """
        Performs multimodal audio transcription using Gemini API from in-memory bytes.
        """
        import time
        import json
        
        encoding_start = time.perf_counter()
        encoded_audio = base64.b64encode(audio_data).decode("utf-8")
        encoding_elapsed = int((time.perf_counter() - encoding_start) * 1000)
        print(f"[Telemetry] Audio base64 encoding (Backend): {encoding_elapsed} ms")
        
        mime_type = "audio/webm"
        if filename:
            if filename.endswith(".wav"):
                mime_type = "audio/wav"
            elif filename.endswith(".mp3"):
                mime_type = "audio/mp3"
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": mime_type,
                                "data": encoded_audio
                            }
                        },
                        {
                            "text": "Transcribe the audio accurately. Detect if the language is 'te' (Telugu) or 'en' (English)."
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.0,
                "responseMimeType": "application/json",
                "responseSchema": {
                    "type": "OBJECT",
                    "properties": {
                        "transcript": {
                            "type": "STRING"
                        },
                        "language": {
                            "type": "STRING",
                            "enum": ["en", "te"]
                        }
                    },
                    "required": ["transcript", "language"]
                }
            }
        }
        
        headers = {"Content-Type": "application/json"}
        
        gemini_start = time.perf_counter()
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)
            gemini_elapsed = int((time.perf_counter() - gemini_start) * 1000)
            
            if response.status_code != 200:
                raise ValueError(f"Gemini API returned error {response.status_code}: {response.text}")
                
            print(f"[Telemetry] Gemini ASR Response Time: {gemini_elapsed} ms")
            
            parse_start = time.perf_counter()
            data = response.json()
            try:
                text_out = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(text_out)
                parse_elapsed = int((time.perf_counter() - parse_start) * 1000)
                print(f"[Telemetry] ASR JSON Parsing: {parse_elapsed} ms")
                return {
                    "transcript": parsed.get("transcript", ""),
                    "language": parsed.get("language", "en")
                }
            except Exception as e:
                raise ValueError(f"Failed to parse Gemini transcription output: {e}. Raw: {data}")


