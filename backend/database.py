# -----------------------------------------------------------------------------
# Mentor::i Database Setup (Phase 17 - Dedicated Data Directory)
#
# This version refines the database location for better architectural separation.
#
# Key Architectural Changes:
# 1.  **New Database Path**: The `DATABASE_URL` now points to
#     `/app/data/mentori.db` instead of `/app/workspace/mentori.db`. This
#     separates the application's persistent state from the agent's sandboxed
#     working directory.
# 2.  **Directory Creation**: The `init_db` function now includes a line to
#     programmatically create the `/app/data` directory if it doesn't exist,
#     ensuring the database can always be created successfully.
# -----------------------------------------------------------------------------

import os
import logging
import json
from sqlalchemy import create_engine, Column, String, Text, ForeignKey
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column, relationship
from typing import List

logger = logging.getLogger(__name__)

# --- Database Configuration ---
# --- MODIFIED: Point to a dedicated /app/data directory ---
DATA_DIR = "/app/data"
DATABASE_URL = f"sqlite:///{DATA_DIR}/mentori.db"

# The engine is the entry point to the database.
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

# The SessionLocal class is a factory for creating new database session objects.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Base Model Class ---
class Base(DeclarativeBase):
    pass

# --- ORM Models (Unchanged) ---

class Task(Base):
    """
    Represents a single, stateful task in the application.
    """
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    messages: Mapped[List["MessageHistory"]] = relationship(
        "MessageHistory", back_populates="task", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Task(id={self.id}, name='{self.name}')>"

class MessageHistory(Base):
    """
    Represents a single message in a task's conversation history.
    """
    __tablename__ = "message_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), index=True)
    message_json: Mapped[str] = mapped_column(Text, nullable=False)
    task: Mapped["Task"] = relationship("Task", back_populates="messages")

    def __repr__(self):
        return f"<MessageHistory(id={self.id}, task_id='{self.task_id}')>"


# --- Database Initialization Function (MODIFIED) ---
def init_db():
    """
    Creates the data directory and all tables in the database.
    """
    try:
        logger.info("Initializing database...")
        # --- NEW: Ensure the data directory exists before creating the DB ---
        os.makedirs(DATA_DIR, exist_ok=True)
        
        logger.info("Creating tables if they don't exist...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialization complete.")
    except Exception as e:
        logger.error(f"An error occurred during database initialization: {e}", exc_info=True)

