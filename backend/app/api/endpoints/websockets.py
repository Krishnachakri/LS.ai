import asyncio
import datetime
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ...websocket_manager import manager
from ...realtime_incident_cache import incidents_cache

router = APIRouter()
logger = logging.getLogger("lifesaver.websockets")

async def send_heartbeat_pings(websocket: WebSocket):
    """Sends a heartbeat PING message to the client every 30 seconds."""
    try:
        while True:
            await asyncio.sleep(30)
            await websocket.send_json({
                "event": "PING",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "payload": {}
            })
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.warning(f"Heartbeat ping failed: {e}")

@router.websocket("/live")
async def websocket_endpoint(websocket: WebSocket):
    # Accept and register connection
    await manager.connect(websocket)
    active_count = len(manager.active_connections)
    logger.info(f"Dashboard connected. Active Connections: {active_count}")
    
    heartbeat_task = None
    
    try:
        # 1. Standardized Initial Sync Payload
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        await websocket.send_json({
            "event": "INITIAL_SYNC",
            "timestamp": now,
            "payload": list(incidents_cache)
        })
        
        # 2. Launch background heartbeat loop
        heartbeat_task = asyncio.create_task(send_heartbeat_pings(websocket))
        
        while True:
            # Maintain socket state and listen for client heartbeats (PONG)
            data = await websocket.receive_text()
            
    except WebSocketDisconnect:
        logger.info("Dashboard WebSocket client disconnected.")
    except Exception as e:
        logger.error(f"WebSocket communication error: {e}")
    finally:
        # 3. Cancel task and clean connection registry
        if heartbeat_task:
            heartbeat_task.cancel()
        manager.disconnect(websocket)
        active_count = len(manager.active_connections)
        logger.info(f"Dashboard disconnected. Active Connections: {active_count}")
