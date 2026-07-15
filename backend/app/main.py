import sys

# Ensure Windows console supports Telugu characters in print statements
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.router import api_router
from .core.config import settings

app = FastAPI(
    title="LifeSaver.ai (LS.ai) API",
    description="Emergency Intake & Coordination Layer Backend Server",
    version="1.0.0"
)

# Setup CORS middleware with configured origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint for monitoring and cloud environment checks
@app.get("/health", tags=["health"])
def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0"
    }

# Mount v1 API endpoints
app.include_router(api_router, prefix="/api/v1")
