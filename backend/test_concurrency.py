# -----------------------------------------------------------------------------
# Test Script for WebSocket Concurrency (Phase 12.5 Debug - FIX)
#
# Goal:
# Prove that a background task can be launched and run to completion,
# totally independent of the WebSocket connection that started it. This
# script isolates the core concurrency problem from the main application.
#
# How it Works (Producer-Consumer Pattern):
# 1. WORKERS: Long-running agent processes. They are the "producers" of
#    messages. They don't know anything about who is connected; they just
#    put their status updates into a universal message queue.
# 2. MESSAGE_QUEUE: A single, shared asyncio.Queue that holds all messages
#    from all running workers.
# 3. Message Senders (`client_message_sender`): One of these is created for
#    each connected client. They are the "consumers." Their only job is to
#    get messages from the shared queue and send them to their specific client.
#
# FIX: The `main_handler` function signature was changed from
# `async def main_handler(websocket, path):` to `async def main_handler(websocket):`
# to resolve a TypeError and match the calling convention of the websockets library.
#
# How to Test:
# 1. Run this script: `python3 test_concurrency.py`
# 2. Open a browser tab and connect with a WebSocket client (e.g., using an
#    online tool like https://www.piesocket.com/websocket-tester).
#    - URL: ws://localhost:8765
# 3. Send the message: `{"action": "start", "task_id": "task_A"}`
#    - You will see messages like "Worker A: Step 1/10" appearing.
# 4. **Close the browser tab completely.**
# 5. Look at your Python console. You will see "Worker A" is STILL PRINTING
#    messages, proving it is running independently.
# 6. Open a NEW browser tab and reconnect to the WebSocket.
#    - You will immediately start seeing the remaining messages from "Worker A".
# 7. Start another task: `{"action": "start", "task_id": "task_B"}`
#    - You will now see interleaved messages from both Worker A and Worker B.
#
# This test will prove the architecture is sound before we re-integrate it
# into the main application.
# -----------------------------------------------------------------------------
import asyncio
import json
import logging
import websockets
import time
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# --- Global State ---
# Holds references to the running asyncio.Task objects for our workers
RUNNING_WORKERS = {}
# A single, shared queue for all messages from all workers
MESSAGE_QUEUE = asyncio.Queue()

# --- The Worker (Message Producer) ---
async def worker(task_id: str):
    """
    Simulates a long-running agent task. It is completely independent
    of any client connection.
    """
    logging.info(f"[{task_id}] Worker starting its 10-step process...")
    for i in range(1, 11):
        await asyncio.sleep(2)  # Simulate doing work
        step_message = f"[{task_id}] Worker completed step {i}/10"
        logging.info(step_message)
        # Put the result into the shared queue for any listener to pick up
        await MESSAGE_QUEUE.put({"task_id": task_id, "message": step_message})
    
    final_message = f"[{task_id}] Worker finished."
    logging.info(final_message)
    await MESSAGE_QUEUE.put({"task_id": task_id, "message": final_message, "is_done": True})

# --- The Message Sender (Message Consumer) ---
async def client_message_sender(websocket, client_id):
    """
    This task is created for each connected client. It consumes messages
    from a separate, temporary queue that gets its items from the main queue.
    """
    # Each client gets its own queue to avoid race conditions
    client_queue = asyncio.Queue()
    # This task will multiplex messages from the main queue to this client's queue
    multiplexer_task = asyncio.create_task(multiplex_main_queue(client_queue))
    
    logging.info(f"[Client {client_id}] Message sender started.")
    while True:
        try:
            message = await client_queue.get()
            await websocket.send(json.dumps(message))
            client_queue.task_done()
        except websockets.exceptions.ConnectionClosed:
            logging.info(f"[Client {client_id}] Connection closed. Stopping message sender.")
            break
        except Exception as e:
            logging.error(f"[Client {client_id}] Error in message sender: {e}")
            break
    # When the loop breaks, cancel the multiplexer for this client
    multiplexer_task.cancel()


async def multiplex_main_queue(client_queue: asyncio.Queue):
    """
    A helper task that fans out messages from the single main queue
    to an individual client's queue. This is more efficient than having
    every client listen to the main queue directly.
    """
    # This is a bit of a workaround to iterate over an asyncio.Queue
    # without a sentinel value that would close all listeners.
    # A more advanced implementation might use a Pub/Sub library.
    while True:
        try:
            # We get from the main queue
            message = await MESSAGE_QUEUE.get()
            # And put it into the specific client's queue
            await client_queue.put(message)
            MESSAGE_QUEUE.task_done() # Acknowledge we've processed it
        except asyncio.CancelledError:
            break

# --- Main WebSocket Handler (FIXED) ---
async def main_handler(websocket):
    """Handles incoming WebSocket connections and messages."""
    client_id = str(websocket.remote_address)
    logging.info(f"[Client {client_id}] Connected.")
    
    # Start the dedicated message sender for this client
    sender_task = asyncio.create_task(client_message_sender(websocket, client_id))

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                action = data.get("action")
                task_id = data.get("task_id")

                if action == "start" and task_id:
                    if task_id in RUNNING_WORKERS and not RUNNING_WORKERS[task_id].done():
                        logging.warning(f"[{task_id}] Worker is already running.")
                        continue
                    
                    logging.info(f"[{task_id}] Received start command from {client_id}.")
                    # Launch the worker as a truly independent background task
                    worker_task = asyncio.create_task(worker(task_id))
                    RUNNING_WORKERS[task_id] = worker_task
                
                elif action == "stop" and task_id:
                    if task_id in RUNNING_WORKERS and not RUNNING_WORKERS[task_id].done():
                         logging.info(f"[{task_id}] Received stop command from {client_id}.")
                         RUNNING_WORKERS[task_id].cancel()
                    else:
                        logging.warning(f"[{task_id}] Stop requested, but worker not running.")

            except json.JSONDecodeError:
                logging.error(f"[Client {client_id}] Received invalid JSON.")
            except Exception as e:
                logging.error(f"[Client {client_id}] Error processing message: {e}")

    finally:
        logging.info(f"[Client {client_id}] Disconnected. Cleaning up sender task.")
        sender_task.cancel()


async def main():
    """Starts the WebSocket server."""
    logging.info("Starting robust concurrency test server on ws://localhost:8765")
    async with websockets.serve(main_handler, "localhost", 8765):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Server shut down.")
