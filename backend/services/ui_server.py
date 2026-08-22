import asyncio
import websockets
import json
import threading

# Global set of connected clients
CONNECTED_CLIENTS = set()
SERVER_LOOP = None

def is_ui_connected():
    return len(CONNECTED_CLIENTS) > 0

# Current state of the UI string (e.g. idle, listening, thinking, speaking)
CURRENT_STATE = "idle"

async def ws_handler(websocket):
    """Handles incoming websocket connections."""
    global CURRENT_STATE
    # Register the new client
    CONNECTED_CLIENTS.add(websocket)
    try:
        # Upon connecting, send the current state immediately
        await websocket.send(json.dumps({"state": CURRENT_STATE}))
        
        # Keep connection alive
        async for message in websocket:
            pass # We don't expect messages from UI to backend for now
            
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        # Unregister client
        CONNECTED_CLIENTS.remove(websocket)

async def _run_server():
    global SERVER_LOOP
    SERVER_LOOP = asyncio.get_running_loop()
    async with websockets.serve(ws_handler, "localhost", 8765):
        await asyncio.Future()  # run forever

def start_server_loop():
    """Starts the asyncio event loop for the websocket server."""
    asyncio.run(_run_server())

def start_ui_server():
    """Spawns the websocket server on a background thread."""
    t = threading.Thread(target=start_server_loop, daemon=True)
    t.start()
    print("UI WebSocket Server started on ws://localhost:8765")

def update_ui_state(new_state, message=None):
    """
    Called by other modules (TTS, command listener) to update the UI.
    """
    global CURRENT_STATE
    # We always allow update if a message is present to refresh text
    if CURRENT_STATE == new_state and not message:
        return # Skip if no change and no text

    CURRENT_STATE = new_state
    
    # Broadcast to all connected clients
    if CONNECTED_CLIENTS and SERVER_LOOP is not None and SERVER_LOOP.is_running():
        payload = {"state": CURRENT_STATE}
        if message:
            payload["text"] = message
            
        json_message = json.dumps(payload)
        for client in list(CONNECTED_CLIENTS):
            try:
                asyncio.run_coroutine_threadsafe(client.send(json_message), SERVER_LOOP)
            except Exception as e:
                print(f"Error broadcasting UI state: {e}")
