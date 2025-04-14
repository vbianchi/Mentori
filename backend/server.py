import asyncio
import websockets
import json
import datetime
import asyncio.subprocess # Needed for running commands

# Keep track of connected clients
connected_clients = set()

# --- Helper function to read streams and send to WebSocket ---
async def read_stream(stream, websocket, stream_name):
    """Reads lines from a stream and sends them over WebSocket as monitor logs."""
    while True:
        line = await stream.readline()
        if not line:
            break
        # Try decoding, replace errors if needed
        log_content = f"[{stream_name}] {line.decode(errors='replace').rstrip()}"
        await websocket.send(json.dumps({
            "type": "monitor_log",
            "content": log_content
        }))
    print(f"{stream_name} stream finished.")


# --- WebSocket Handler ---
async def handler(websocket):
    """Handles incoming WebSocket connections and messages."""
    print(f"Client connected from {websocket.remote_address}")
    connected_clients.add(websocket)
    current_task = None # Track task state per connection

    try:
        # Send initial connection confirmation
        await websocket.send(json.dumps({
            "type": "status_message",
            "content": "Connection established. Ready for task."
        }))
        await websocket.send(json.dumps({
            "type": "monitor_log",
            "content": f"[{datetime.datetime.now().isoformat(timespec='milliseconds')}] New client connection: {websocket.remote_address}"
        }))

        # Listen for messages from the client
        async for message in websocket:
            print(f"Received message: {message}")
            log_prefix = f"[{datetime.datetime.now().isoformat(timespec='milliseconds')}]"
            try:
                data = json.loads(message)
                message_type = data.get("type")
                content = data.get("content")

                # --- USER MESSAGE HANDLING (Task Intake / Follow-up) ---
                if message_type == "user_message":
                    await websocket.send(json.dumps({"type": "monitor_log", "content": f"{log_prefix} Received user message: {content}"}))

                    if current_task is None:
                        # Treat as new task goal
                        current_task = content
                        print(f"Received new task: {current_task}")
                        await websocket.send(json.dumps({"type": "status_message", "content": f"Acknowledged task: '{current_task[:50]}...'. Starting process."}))
                        await asyncio.sleep(0.5)
                        await websocket.send(json.dumps({"type": "monitor_log", "content": f"{log_prefix} Starting task: {current_task}"}))
                        # TODO: Add actual planning/execution logic here later
                        await asyncio.sleep(1.0)
                        await websocket.send(json.dumps({"type": "agent_message", "content": f"Okay, I've started the task: '{current_task}'. I will report progress."}))

                    else:
                        # Treat as follow-up message within the current task
                        print(f"Received follow-up message: {content}")
                        await websocket.send(json.dumps({"type": "status_message", "content": f"Received follow-up: '{content[:50]}...'. Processing."}))
                        await asyncio.sleep(0.5)
                        # TODO: Integrate follow-up into agent logic
                        await websocket.send(json.dumps({"type": "agent_message", "content": f"I received your follow-up: '{content}'. (Current backend doesn't act on this yet)."}))


                # --- COMMAND EXECUTION HANDLING ---
                elif message_type == "run_command":
                    command = data.get("command")
                    if not command:
                        await websocket.send(json.dumps({"type": "monitor_log", "content": f"{log_prefix} Error: Received 'run_command' with no command."}))
                        continue

                    await websocket.send(json.dumps({"type": "monitor_log", "content": f"{log_prefix} Executing command: {command}"}))
                    await websocket.send(json.dumps({"type": "status_message", "content": f"Running: {command[:50]}..."}))

                    try:
                        # Create subprocess asynchronously
                        process = await asyncio.create_subprocess_shell(
                            command,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )

                        # Create tasks to read stdout and stderr concurrently
                        # Pass log_prefix to ensure timestamps roughly match execution start
                        stdout_task = asyncio.create_task(read_stream(process.stdout, websocket, "stdout"))
                        stderr_task = asyncio.create_task(read_stream(process.stderr, websocket, "stderr"))

                        # Wait for both stream readers to finish
                        await asyncio.gather(stdout_task, stderr_task)

                        # Wait for the process to exit and get return code
                        return_code = await process.wait()
                        await websocket.send(json.dumps({"type": "monitor_log", "content": f"{log_prefix} Command '{command[:50]}...' finished with exit code: {return_code}"}))
                        await websocket.send(json.dumps({"type": "status_message", "content": f"Command finished (Code: {return_code})."}))

                    except FileNotFoundError:
                         await websocket.send(json.dumps({"type": "monitor_log", "content": f"{log_prefix} Error: Command not found: {command.split()[0]}"}))
                         await websocket.send(json.dumps({"type": "status_message", "content": f"Error: Command not found."}))
                    except Exception as e:
                        print(f"Error running command '{command}': {e}")
                        await websocket.send(json.dumps({"type": "monitor_log", "content": f"{log_prefix} Error running command: {e}"}))
                        await websocket.send(json.dumps({"type": "status_message", "content": f"Error executing command."}))


                # --- OTHER MESSAGE TYPE HANDLING ---
                elif message_type == "context_switch":
                     await websocket.send(json.dumps({"type": "monitor_log", "content": f"{log_prefix} Received context switch: {data.get('task')}"}))
                     current_task = data.get('task') # Update task context if switched
                elif message_type == "new_task":
                     await websocket.send(json.dumps({"type": "monitor_log", "content": f"{log_prefix} Received new task request."}))
                     current_task = None # Reset task state
                     await websocket.send(json.dumps({"type": "status_message", "content": "Ready for new task."}))
                elif message_type == "action_command":
                     await websocket.send(json.dumps({"type": "monitor_log", "content": f"{log_prefix} Received action command: {data.get('command')}"}))
                     # TODO: Implement action command logic

                else:
                    print(f"Unknown message type received: {message_type}")
                    await websocket.send(json.dumps({"type": "monitor_log", "content": f"{log_prefix} Received unknown message type: {message_type}"}))

            except json.JSONDecodeError:
                print(f"Received non-JSON message: {message}")
                await websocket.send(json.dumps({"type": "monitor_log", "content": f"{log_prefix} Error: Received non-JSON message."}))
            except Exception as e:
                print(f"Error processing message: {e}")
                # Send specific error details to monitor log for debugging
                await websocket.send(json.dumps({"type": "monitor_log", "content": f"{log_prefix} Error processing message: {type(e).__name__} - {e}"}))


    except websockets.exceptions.ConnectionClosedOK:
        print(f"Client disconnected: {websocket.remote_address}")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Connection closed with error: {websocket.remote_address} - {e}")
    finally:
        connected_clients.remove(websocket)
        print(f"Client removed: {websocket.remote_address}")


async def main():
    host = "localhost"
    port = 8765
    async with websockets.serve(handler, host, port):
        print(f"WebSocket server started on ws://{host}:{port}")
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped manually.")