import asyncio
import json
import sys

# We can import websockets which is bundled with uvicorn[standard]
try:
    import websockets
except ImportError:
    print("[!] Error: 'websockets' package is required. Install it using: pip install websockets")
    sys.exit(1)

async def listen_for_incidents():
    url = "ws://127.0.0.1:8000/api/v1/incidents/live"
    print(f"[*] Connecting to local WebSocket gateway at: {url}...")
    
    try:
        async with websockets.connect(url) as ws:
            print("[+] Connection established successfully.")
            
            # Wait for the initial synchronization message containing cached items
            initial_sync = await ws.recv()
            sync_data = json.loads(initial_sync)
            print("\n==========================================")
            print(f" EVENT: {sync_data.get('event')}")
            print("==========================================")
            print(f"Loaded {len(sync_data.get('payload', []))} incidents from in-memory cache.")
            print("==========================================\n")
            
            print("[*] Monitoring for live emergency broadcasts... (Trigger a report to view broadcast)")
            while True:
                message = await ws.recv()
                broadcast_data = json.loads(message)
                
                # Ignore heartbeat ping events in printing
                if broadcast_data.get("event") == "PING":
                    continue
                
                print("\n==========================================")
                print(f" LIVE BROADCAST: {broadcast_data.get('event')}")
                print("==========================================")
                print(json.dumps(broadcast_data.get('payload', {}), indent=2))
                print("==========================================\n")
                
    except ConnectionRefusedError:
        print("[!] Connection refused. Ensure the backend uvicorn server is running on port 8000.")
    except Exception as e:
        print(f"[!] WebSocket client error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(listen_for_incidents())
    except KeyboardInterrupt:
        print("\n[*] WebSocket client shut down.")
