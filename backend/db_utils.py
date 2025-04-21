# backend/db_utils.py
import aiosqlite
import logging
import uuid
from pathlib import Path
import datetime

logger = logging.getLogger(__name__)

# Define database path (relative to this file's parent directory - i.e., project root)
DB_DIR = Path(__file__).parent.parent
DB_PATH = DB_DIR / "agent_history.db"

async def init_db():
    """Initializes the SQLite database and creates tables if they don't exist."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            # Create tasks table (if not exists)
            # Stores overall tasks initiated by the user
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_timestamp TEXT NOT NULL
                )
            """)
            # Create messages table (if not exists)
            # Stores individual messages/logs associated with a task
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    message_type TEXT NOT NULL, -- 'user', 'agent', 'status', 'monitor_log', 'tool_input', 'tool_output' etc.
                    content TEXT NOT NULL,
                    FOREIGN KEY (task_id) REFERENCES tasks (task_id)
                )
            """)
            # Optional: Create index for faster retrieval
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_task_id_timestamp ON messages (task_id, timestamp)
            """)
            await db.commit()
        logger.info(f"Database initialized successfully at {DB_PATH}")
    except Exception as e:
        logger.error(f"Failed to initialize database at {DB_PATH}: {e}", exc_info=True)
        raise

async def add_task(task_id: str, title: str, timestamp: str):
    """Adds a new task to the database."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT OR IGNORE INTO tasks (task_id, title, created_timestamp) VALUES (?, ?, ?)",
                (task_id, title, timestamp)
            )
            await db.commit()
            logger.debug(f"Task added/ignored in DB: {task_id} - {title}")
    except Exception as e:
        logger.error(f"Failed to add task {task_id} to DB: {e}", exc_info=True)

async def add_message(task_id: str, session_id: str, message_type: str, content: str):
    """Adds a message/log entry to the database for a given task."""
    if not task_id:
        logger.warning(f"Attempted to add message with no task_id. Type: {message_type}, Content: {content[:100]}...")
        return # Cannot save without a task context

    message_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """INSERT INTO messages
                   (message_id, task_id, session_id, timestamp, message_type, content)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (message_id, task_id, session_id, timestamp, message_type, content)
            )
            await db.commit()
            logger.debug(f"Message added to DB for task {task_id}: Type={message_type}")
    except Exception as e:
        logger.error(f"Failed to add message for task {task_id} to DB: {e}", exc_info=True)

async def get_messages_for_task(task_id: str) -> list:
    """Retrieves all messages for a specific task, ordered by timestamp."""
    if not task_id: return []
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row # Return rows as dict-like objects
            async with db.execute(
                "SELECT timestamp, message_type, content FROM messages WHERE task_id = ? ORDER BY timestamp ASC",
                (task_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                logger.info(f"Retrieved {len(rows)} messages for task {task_id}")
                # Convert Row objects to simple dictionaries for easier handling/JSON serialization
                return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Failed to retrieve messages for task {task_id}: {e}", exc_info=True)
        return []