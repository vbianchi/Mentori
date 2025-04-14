# backend/server.py
import asyncio
import websockets
import json
import datetime
import logging
import asyncio.subprocess # Needed for running commands
import shlex # Better for parsing command strings if needed later

# Import configuration and planners
from backend.config import load_settings, Settings
from backend.llm_planners import get_planner, LLMPlanner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Load Settings and Planner (at startup) ---
try:
    settings: Settings = load_settings()
    planner: LLMPlanner = get_planner(settings)
    logger.info(f"Planner instance created successfully for provider: {settings.ai_provider}")
except Exception as e:
    logger.critical(f"FATAL: Failed during startup initialization: {e}", exc_info=True)
    exit(1)

connected_clients = set()

# --- Helper: Read Stream ---
async def read_stream(stream, websocket, stream_name):
    """Reads lines from a stream and sends them over WebSocket as monitor logs."""
    while True:
        line = await stream.readline()
        if not line:
            break
        log_content = f"[{stream_name}] {line.decode(errors='replace').rstrip()}"
        timestamp = datetime.datetime.now().isoformat(timespec='milliseconds')
        try:
            await websocket.send(json.dumps({
                "type": "monitor_log",
                "content": f"[{timestamp}] {log_content}"
            }))
        except websockets.exceptions.ConnectionClosed:
            logger.warning(f"WebSocket closed while trying to send {stream_name} log.")
            break # Stop reading if connection is closed
    logger.debug(f"{stream_name} stream finished.")

# --- Helper: Execute Shell Command ---
async def execute_shell_command(command: str, websocket) -> bool:
    """Executes a shell command asynchronously and streams output."""
    log_prefix = f"[{datetime.datetime.now().isoformat(timespec='milliseconds')}]"
    logger.info(f"Executing command: {command}")
    await websocket.send(json.dumps({"type": "monitor_log", "content": f"{log_prefix} Executing: {command}"}))
    await websocket.send(json.dumps({"type": "status_message", "content": f"Running: {command[:60]}..."}))

    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Stream stdout and stderr concurrently
        stdout_task = asyncio.create_task(read_stream(process.stdout, websocket, "stdout"))
        stderr_task = asyncio.create_task(read_stream(process.stderr, websocket, "stderr"))
        await asyncio.gather(stdout_task, stderr_task)

        # Wait for completion and check return code
        return_code = await process.wait()
        success = return_code == 0
        status_msg = "succeeded" if success else f"failed (Code: {return_code})"

        await websocket.send(json.dumps({"type": "monitor_log", "content": f"{log_prefix} Command '{command[:60]}...' finished, {status_msg}."}))
        await websocket.send(json.dumps({"type": "status_message", "content": f"Step finished ({status_msg})."}))
        return success # Return True if command succeeded, False otherwise

    except FileNotFoundError:
        await websocket.send(json.dumps({"type": "monitor_log", "content": f"{log_prefix} Error: Command not found: {shlex.split(command)[0]}"}))
        await websocket.send(json.dumps({"type": "status_message", "content": f"Error: Command not found."}))
        return False
    except Exception as e:
        logger.error(f"Error running command '{command}': {e}", exc_info=True)
        await websocket.send(json.dumps({"type": "monitor_log", "content": f"{log_prefix} Error running command: {e}"}))
        await websocket.send(json.dumps({"type": "status_message", "content": f"Error executing command."}))
        return False

# --- WebSocket Handler ---
async def handler(websocket):
    """Handles incoming WebSocket connections and messages."""
    logger.info(f"Client connected from {websocket.remote_address}")
    connected_clients.add(websocket)
    current_task = None
    current_plan_steps = [] # Store plan as a list of steps

    try:
        timestamp = datetime.datetime.now().isoformat(timespec='milliseconds')
        await websocket.send(json.dumps({
            "type": "status_message",
            "content": f"Connected to backend (Using AI: {settings.ai_provider}). Ready for task."
        }))
        # ... (initial monitor log) ...

        async for message in websocket:
            logger.info(f"Received message: {message}")
            log_prefix = f"[{datetime.datetime.now().isoformat(timespec='milliseconds')}]"
            try:
                data = json.loads(message)
                message_type = data.get("type")
                content = data.get("content")

                # --- USER MESSAGE HANDLING ---
                if message_type == "user_message":
                    await websocket.send(json.dumps({"type": "monitor_log", "content": f"{log_prefix} Received user message: {content}"}))

                    if current_task is None:
                        # --- NEW TASK: Generate Plan & Start Execution ---
                        current_task = content
                        current_plan_steps = [] # Reset plan
                        logger.info(f"Received new task: {current_task}")
                        # ... (Acknowledge task, log generation start) ...
                        await websocket.send(json.dumps({"type": "status_message", "content": f"Acknowledged task: '{current_task[:50]}...'. Generating plan..."}))
                        await websocket.send(json.dumps({"type": "monitor_log", "content": f"{log_prefix} Generating plan for task: {current_task}"}))

                        try:
                            # --- Call Planner ---
                            plan_result_str = await planner.generate_plan(current_task)
                            await websocket.send(json.dumps({"type": "monitor_log", "content": f"{log_prefix} Plan received from {settings.ai_provider}."}))

                            if plan_result_str.lower().startswith("error:"):
                                # ... (Handle planning error) ...
                                logger.error(f"Planner returned an error: {plan_result_str}")
                                await websocket.send(json.dumps({"type": "status_message", "content": "Failed to generate plan."}))
                                await websocket.send(json.dumps({"type": "agent_message", "content": plan_result_str}))
                                current_task = None
                            else:
                                logger.info(f"Generated Plan:\n{plan_result_str}")
                                # --- Parse and Display Plan ---
                                # Simple parsing: split by newline, ignore empty lines
                                current_plan_steps = [step.strip() for step in plan_result_str.split('\n') if step.strip()]

                                if not current_plan_steps:
                                     await websocket.send(json.dumps({"type": "agent_message", "content": "The AI generated an empty plan. Please try rephrasing the task."}))
                                     await websocket.send(json.dumps({"type": "status_message", "content": "Plan generation resulted in empty plan."}))
                                     current_task = None # Reset
                                else:
                                    plan_display_message = f"Okay, planning complete for '{current_task}'. Starting execution:\n---\n" + "\n".join(f"- {step}" for step in current_plan_steps) + "\n---"
                                    await websocket.send(json.dumps({"type": "agent_message", "content": plan_display_message}))
                                    await websocket.send(json.dumps({"type": "status_message", "content": "Plan generated. Starting execution..."}))

                                    # --- Execute Plan ---
                                    execution_success = True
                                    for i, step in enumerate(current_plan_steps):
                                        step_log_prefix = f"{log_prefix} [Step {i+1}/{len(current_plan_steps)}]"
                                        await websocket.send(json.dumps({"type": "monitor_log", "content": f"{step_log_prefix} Preparing to execute: {step}"}))
                                        await websocket.send(json.dumps({"type": "status_message", "content": f"Executing step {i+1}: {step[:50]}..."}))

                                        # Assuming step is a shell command for now
                                        # TODO: Add logic here to parse step type (e.g., run_command, browse_url)
                                        step_success = await execute_shell_command(step, websocket)

                                        if not step_success:
                                            logger.warning(f"Step {i+1} failed: {step}")
                                            await websocket.send(json.dumps({"type": "monitor_log", "content": f"{step_log_prefix} Step failed!"}))
                                            await websocket.send(json.dumps({"type": "status_message", "content": f"Execution stopped due to failure in step {i+1}."}))
                                            await websocket.send(json.dumps({"type": "agent_message", "content": f"Execution failed on step: {step}"}))
                                            execution_success = False
                                            break # Stop execution on failure

                                        await asyncio.sleep(0.2) # Small delay between steps

                                    # --- Report Final Status ---
                                    if execution_success:
                                        logger.info(f"Plan execution completed successfully for task: {current_task}")
                                        await websocket.send(json.dumps({"type": "status_message", "content": "Plan execution finished successfully."}))
                                        await websocket.send(json.dumps({"type": "agent_message", "content": f"Finished executing the plan for task: '{current_task}'."}))
                                    else:
                                         logger.warning(f"Plan execution failed for task: {current_task}")
                                         # Status already sent by the failing step loop

                                    # Reset task state after execution attempt
                                    current_task = None
                                    current_plan_steps = []


                        except Exception as e:
                            # ... (Handle critical planning error) ...
                            logger.error(f"Error during planning/execution phase: {e}", exc_info=True)
                            await websocket.send(json.dumps({"type": "monitor_log", "content": f"{log_prefix} CRITICAL Error during planning/execution: {e}"}))
                            await websocket.send(json.dumps({"type": "status_message", "content": "Error during task processing."}))
                            await websocket.send(json.dumps({"type": "agent_message", "content": f"Sorry, an internal error occurred: {e}"}))
                            current_task = None # Reset task state

                    else:
                        # --- FOLLOW-UP MESSAGE ---
                        # ... (follow-up logic remains the same) ...
                        logger.info(f"Received follow-up message: {content}")
                        await websocket.send(json.dumps({"type": "status_message", "content": f"Received follow-up: '{content[:50]}...'. Processing."}))
                        await asyncio.sleep(0.1)
                        await websocket.send(json.dumps({"type": "agent_message", "content": f"Received follow-up: '{content}'. (Agent cannot act on this yet)."}))


                # --- COMMAND EXECUTION HANDLING (Direct) ---
                elif message_type == "run_command":
                    # Use the refactored function
                    command = data.get("command")
                    if command:
                        await execute_shell_command(command, websocket)
                    else:
                        await websocket.send(json.dumps({"type": "monitor_log", "content": f"{log_prefix} Error: Received 'run_command' with no command."}))


                # --- OTHER MESSAGE TYPE HANDLING ---
                # ... (context_switch, new_task, action_command logic remains the same, resetting state) ...
                elif message_type == "context_switch":
                     await websocket.send(json.dumps({"type": "monitor_log", "content": f"{log_prefix} Received context switch: {data.get('task')}"}))
                     current_task = None; current_plan_steps = []
                     await websocket.send(json.dumps({"type": "status_message", "content": f"Switched context to: {data.get('task')}. Ready for new goal."}))
                elif message_type == "new_task":
                     await websocket.send(json.dumps({"type": "monitor_log", "content": f"{log_prefix} Received new task request."}))
                     current_task = None; current_plan_steps = []
                     await websocket.send(json.dumps({"type": "status_message", "content": "Ready for new task."}))
                elif message_type == "action_command":
                     await websocket.send(json.dumps({"type": "monitor_log", "content": f"{log_prefix} Received action command: {data.get('command')}"}))
                     # TODO: Implement action command logic (e.g., trigger execution of stored plan?)

                else: # Unknown message type
                     logger.warning(f"Unknown message type received: {message_type}")
                     await websocket.send(json.dumps({"type": "monitor_log", "content": f"{log_prefix} Received unknown message type: {message_type}"}))

            # ... (Error handling for message processing remains the same) ...
            except json.JSONDecodeError: # ...
                 logger.error(f"Received non-JSON message: {message}", exc_info=True)
                 await websocket.send(json.dumps({"type": "monitor_log", "content": f"{log_prefix} Error: Received non-JSON message."}))
            except Exception as e: # ...
                 logger.error(f"Error processing message: {e}", exc_info=True)
                 await websocket.send(json.dumps({"type": "monitor_log", "content": f"{log_prefix} Error processing message: {type(e).__name__} - {e}"}))

    # ... (Connection closed handling remains the same) ...
    except websockets.exceptions.ConnectionClosedOK: # ...
        logger.info(f"Client disconnected: {websocket.remote_address}")
    except websockets.exceptions.ConnectionClosedError as e: # ...
        logger.warning(f"Connection closed with error: {websocket.remote_address} - {e}")
    except Exception as e: # ...
        logger.error(f"Unhandled error in handler for {websocket.remote_address}: {e}", exc_info=True)
    finally: # ...
        connected_clients.remove(websocket)
        logger.info(f"Client removed: {websocket.remote_address}")


async def main():
    # ... (main function remains the same) ...
    host = "localhost"
    port = 8765
    logger.info(f"Starting WebSocket server on ws://{host}:{port}")
    async with websockets.serve(handler, host, port):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    # ... (__main__ block remains the same) ...
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped manually.")
    except Exception as e:
        logger.critical(f"Server failed to start or encountered critical error: {e}", exc_info=True)

