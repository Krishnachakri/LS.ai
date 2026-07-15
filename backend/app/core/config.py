import os

class Settings:
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash"
    CORS_ORIGINS: list[str] = []
    
    def __init__(self):
        # 1. Load from environment variable (highest priority)
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
        self.GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
        
        # 2. If missing, attempt to load from a local .env file in the backend root
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        env_path = os.path.join(backend_dir, ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped and not stripped.startswith("#") and "=" in stripped:
                        key, val = stripped.split("=", 1)
                        k = key.strip()
                        v = val.strip().strip('"').strip("'")
                        if k == "OPENAI_API_KEY" and not self.OPENAI_API_KEY:
                            self.OPENAI_API_KEY = v
                        elif k == "GEMINI_API_KEY" and not self.GEMINI_API_KEY:
                            self.GEMINI_API_KEY = v
                            os.environ["GEMINI_API_KEY"] = v
                        elif k == "GEMINI_MODEL" and (not self.GEMINI_MODEL or self.GEMINI_MODEL == "gemini-3.5-flash"):
                            self.GEMINI_MODEL = v
        
        # Load CORS origins
        raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
        self.CORS_ORIGINS = [
            origin.strip()
            for origin in raw_origins.split(",")
            if origin.strip()
        ]

settings = Settings()
