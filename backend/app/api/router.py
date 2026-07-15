from fastapi import APIRouter
from .endpoints import incidents, websockets

api_router = APIRouter()

# Register HTTP and WebSocket routes under appropriate prefixes
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
api_router.include_router(websockets.router, prefix="/incidents", tags=["websockets"])
