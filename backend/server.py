import asyncio
import websockets
import json
import datetime

# Keep track of connected clients (optional, but useful for broadcast later)
connected_clients = set()

# --- CORRECTED LINE: Added 'path' parameter ---
async def handler(websocket, path):
    """Handles incoming WebSocket connections and messages."""
    # We don't use 'path' in this simple example, but the function needs to accept it.
    print(f"Client connected from {websocket.remote_address} on path '{path}'")
    connected_clients.add(websocket)
    try:
        # Send initial connection confirmation
        await websocket.send(json.dumps({
            "type": "status_message",
            "content": "Connection established with backend server."
        }))
        await websocket.send(json.dumps({
            "type": "monitor_log",
            "content": f"[{datetime.datetime.now().isoformat(timespec='milliseconds')}] New client connection: {websocket.remote_address}"
        }))

        # Listen for messages from the client
        async for message in websocket:
            print(f"Received message: {message}")
            try:
                data = json.loads(message)
                message_type = data.get("type")
                content = data.get("content")

                if message_type == "user_message":
                    # Simulate processing and send back responses/logs
                    await websocket.send(json.dumps({
                        "type": "monitor_log",
                        "content": f"[{datetime.datetime.now().isoformat(timespec='milliseconds')}] Received user message: {content}"
                    }))
                    await asyncio.sleep(0.5) # Simulate thinking time

                    await websocket.send(json.dumps({
                         "type": "status_message",
                         "content": "Processing request..."
                    }))
                    await websocket.send(json.dumps({
                        "type": "monitor_log",
                        "content": f"[{datetime.datetime.now().isoformat(timespec='milliseconds')}] Agent processing: {content}"
                    }))
                    await asyncio.sleep(1.5) # Simulate processing time

                    # Remove "Processing..." status - Find a better way later if needed
                    # await websocket.send(json.dumps({"type": "remove_last_status"}))

                    await websocket.send(json.dumps({
                        "type": "agent_message",
                        "content": f"Backend received: '{content}'. This is a simulated response."
                    }))
                    await websocket.send(json.dumps({
                        "type": "monitor_log",
                        "content": f"[{datetime.datetime.now().isoformat(timespec='milliseconds')}] Agent response sent."
                    }))
                
                # Handle other message types if needed (e.g., context switch, new task)
                elif message_type == "context_switch":
                     await websocket.send(json.dumps({
                        "type": "monitor_log",
                        "content": f"[{datetime.datetime.now().isoformat(timespec='milliseconds')}] Received context switch: {data.get('task')}"
                    }))
                elif message_type == "new_task":
                     await websocket.send(json.dumps({
                        "type": "monitor_log",
                        "content": f"[{datetime.datetime.now().isoformat(timespec='milliseconds')}] Received new task request."
                    }))
                elif message_type == "action_command":
                     await websocket.send(json.dumps({
                        "type": "monitor_log",
                        "content": f"[{datetime.datetime.now().isoformat(timespec='milliseconds')}] Received action command: {data.get('command')}"
                    }))


                else:
                    print(f"Unknown message type received: {message_type}")
                    await websocket.send(json.dumps({
                        "type": "monitor_log",
                        "content": f"[{datetime.datetime.now().isoformat(timespec='milliseconds')}] Received unknown message type: {message_type}"
                    }))

            except json.JSONDecodeError:
                print(f"Received non-JSON message: {message}")
                await websocket.send(json.dumps({
                    "type": "monitor_log",
                    "content": f"[{datetime.datetime.now().isoformat(timespec='milliseconds')}] Error: Received non-JSON message."
                }))
            except Exception as e:
                print(f"Error processing message: {e}")
                await websocket.send(json.dumps({
                    "type": "monitor_log",
                    "content": f"[{datetime.datetime.now().isoformat(timespec='milliseconds')}] Error processing message: {e}"
                }))


    except websockets.exceptions.ConnectionClosedOK:
        print(f"Client disconnected: {websocket.remote_address}")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Connection closed with error: {websocket.remote_address} - {e}")
    finally:
        # Remove client upon disconnection
        connected_clients.remove(websocket)
        print(f"Client removed: {websocket.remote_address}")


async def main():
    host = "localhost"
    port = 8765 # Use a different port than the HTTP server
    async with websockets.serve(handler, host, port):
        print(f"WebSocket server started on ws://{host}:{port}")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped manually.")