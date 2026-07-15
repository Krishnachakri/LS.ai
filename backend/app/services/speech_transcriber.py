import os
import base64
import httpx
from openai import OpenAI
from ..core.config import settings

class SpeechTranscriberService:
    def __init__(self):
        # Retrieve keys and config from settings or environment
        self.openai_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")
        self.gemini_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        self.gemini_model = settings.GEMINI_MODEL
        self.client = OpenAI(api_key=self.openai_key) if self.openai_key else None

    def transcribe(self, file_path: str) -> dict:
        """
        Sends local audio file to OpenAI's Whisper API or Gemini's Multimodal Audio API for speech-to-text.
        Returns a dict containing:
          - transcript: The transcribed text string.
          - language: Standardized language code ('te' or 'en').
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found at: {file_path}")

        # 1. Gemini Multimodal Audio Transcription Pathway
        if self.gemini_key:
            return self._transcribe_gemini(file_path)

        # 2. OpenAI Whisper Ingestion Pathway
        if not self.client:
            raise ValueError("OpenAI API Key is not configured. Please set the OPENAI_API_KEY environment variable.")
        
        with open(file_path, "rb") as audio_file:
            response = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json"
            )
            
            transcript_text = getattr(response, "text", "")
            detected_lang = getattr(response, "language", "english")
            
            lang_lower = detected_lang.lower()
            lang_code = "te" if ("telugu" in lang_lower or lang_lower == "te") else "en"
                
            return {
                "transcript": transcript_text,
                "language": lang_code
            }

    def _transcribe_gemini(self, file_path: str) -> dict:
        """
        Performs multimodal audio transcription using Gemini API.
        """
        with open(file_path, "rb") as f:
            audio_data = f.read()
        encoded_audio = base64.b64encode(audio_data).decode("utf-8")
        
        mime_type = "audio/webm"
        if file_path.endswith(".wav"):
            mime_type = "audio/wav"
        elif file_path.endswith(".mp3"):
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
                            "text": (
                                "Listen to this audio file. Perform two tasks:\n"
                                "1. Transcribe the audio accurately into text in its original language (Telugu or English).\n"
                                "2. Detect the language. Output 'te' if it is Telugu, or 'en' if it is English.\n\n"
                                "Return the output in this JSON format:\n"
                                "{\n"
                                "  \"transcript\": \"transcription text\",\n"
                                "  \"language\": \"en\" or \"te\"\n"
                                "}"
                            )
                        }
                    ]
                }
            ],
            "generationConfig": {
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
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                raise ValueError(f"Gemini API returned error {response.status_code}: {response.text}")
                
            data = response.json()
            try:
                text_out = data["candidates"][0]["content"]["parts"][0]["text"]
                import json
                parsed = json.loads(text_out)
                return {
                    "transcript": parsed.get("transcript", ""),
                    "language": parsed.get("language", "en")
                }
            except Exception as e:
                raise ValueError(f"Failed to parse Gemini transcription output: {e}. Raw: {text_out}")

