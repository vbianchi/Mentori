# backend/db_utils.py
import aiosqlite
import logging
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Define DB path relative to this file's parent (project root)
DB_DIR = Path(__file__).resolve().parent.parent / "database"
DB_PATH = DB_DIR / "agent_history.db"

# Ensure DB directory exists
try:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Database directory ensured at: {DB_DIR}")
except OSError as e:
    logger.error(f"Could not create database directory at {DB_DIR}: {e}", exc_info=True)
    raise

async def init_db():
    """Initializes the SQLite database and creates tables if they don't exist."""
    logger.info(f"Initializing database at {DB_PATH}...")
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            # Create tasks table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            ''')
            # Create messages table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    message_type TEXT NOT NULL, -- 'user', 'agent_message', 'status_message', 'monitor_log', 'error_agent', etc.
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (task_id) REFERENCES tasks (task_id) ON DELETE CASCADE
                )
            ''')
            # Create an index for faster message retrieval by task_id
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_message_task_id ON messages (task_id)
            ''')
            await db.commit()
        logger.info("Database tables ensured (tasks, messages).")
    except Exception as e:
        logger.error(f"Error initializing database: {e}", exc_info=True)
        raise # Re-raise exception to potentially halt server startup

async def add_task(task_id: str, title: str, created_at: str):
    """Adds a new task to the database, ignoring if it already exists."""
    logger.debug(f"Attempting to add task to DB: ID={task_id}, Title={title}")
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            # Use INSERT OR IGNORE to avoid errors if task_id already exists
            await db.execute(
                "INSERT OR IGNORE INTO tasks (task_id, title, created_at) VALUES (?, ?, ?)",
                (task_id, title, created_at)
            )
            await db.commit()
            # Log whether insert happened (optional check)
            # cursor = await db.execute("SELECT changes()")
            # changes = await cursor.fetchone()
            # if changes and changes[0] > 0: logger.info(f"Added new task to DB: {task_id}")
            # else: logger.debug(f"Task {task_id} already exists in DB.")
    except Exception as e:
        logger.error(f"Error adding task {task_id} to DB: {e}", exc_info=True)

async def add_message(task_id: str, session_id: str, message_type: str, content: str):
    """Adds a message associated with a task to the database."""
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    logger.debug(f"Adding message to DB: Task={task_id}, Type={message_type}, Content='{content[:50]}...'")
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """INSERT INTO messages (task_id, session_id, message_type, content, timestamp)
                   VALUES (?, ?, ?, ?, ?)""",
                (task_id, session_id, message_type, content, timestamp)
            )
            await db.commit()
    except Exception as e:
        logger.error(f"Error adding message for task {task_id} to DB: {e}", exc_info=True)

# *** NEW FUNCTION ***
async def get_messages_for_task(task_id: str) -> List[Dict[str, Any]]:
    """Retrieves all messages for a given task_id, ordered by timestamp."""
    logger.info(f"Retrieving messages from DB for task_id: {task_id}")
    messages = []
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            # Ensure row factory is set to return dictionaries
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT message_type, content, timestamp
                   FROM messages
                   WHERE task_id = ?
                   ORDER BY timestamp ASC""", # Retrieve in chronological order
                (task_id,)
            ) as cursor:
                async for row in cursor:
                    # Convert row object to dictionary
                    messages.append(dict(row))
        logger.info(f"Retrieved {len(messages)} messages for task {task_id}.")
        return messages
    except Exception as e:
        logger.error(f"Error retrieving messages for task {task_id} from DB: {e}", exc_info=True)
        return [] # Return empty list on error


# --- Functions for Deleting Tasks (Phase 2.2) ---
async def delete_task_and_messages(task_id: str) -> bool:
    """Deletes a task and all associated messages from the database."""
    logger.warning(f"Attempting to delete task and messages from DB for task_id: {task_id}")
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            # Enable foreign key support (important for CASCADE delete)
            await db.execute("PRAGMA foreign_keys = ON")
            # Deleting the task will automatically cascade delete related messages
            # due to the FOREIGN KEY constraint defined in the messages table.
            cursor = await db.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
            await db.commit()
            if cursor.rowcount > 0:
                logger.info(f"Successfully deleted task {task_id} and associated messages from DB.")
                return True
            else:
                logger.warning(f"Task {task_id} not found in DB for deletion.")
                return False
    except Exception as e:
        logger.error(f"Error deleting task {task_id} from DB: {e}", exc_info=True)
        return False

