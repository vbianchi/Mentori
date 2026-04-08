# backend/database.py
import logging
from sqlmodel import SQLModel, create_engine, Session, select
from sqlalchemy import text, inspect
from backend.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}, # Needed for SQLite
    echo=False
)


def _run_migrations():
    """Run database migrations for schema changes."""
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    # --- ModelConfig migrations ---
    if 'modelconfig' in table_names:
        columns = [col['name'] for col in inspector.get_columns('modelconfig')]
        if 'thinking_type' not in columns:
            logger.info("Running migration: Adding 'thinking_type' column to modelconfig table")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE modelconfig ADD COLUMN thinking_type VARCHAR"))
                conn.commit()
            logger.info("Migration complete: 'thinking_type' column added")

    # --- User migrations ---
    if 'user' in table_names:
        columns = [col['name'] for col in inspector.get_columns('user')]
        with engine.connect() as conn:
            if 'first_name' not in columns:
                logger.info("Running migration: Adding 'first_name' column to user table")
                conn.execute(text("ALTER TABLE user ADD COLUMN first_name VARCHAR"))
            if 'last_name' not in columns:
                logger.info("Running migration: Adding 'last_name' column to user table")
                conn.execute(text("ALTER TABLE user ADD COLUMN last_name VARCHAR"))
            if 'preferences' not in columns:
                logger.info("Running migration: Adding 'preferences' column to user table")
                conn.execute(text("ALTER TABLE user ADD COLUMN preferences TEXT"))
            conn.commit()

    # --- Task migrations ---
    if 'task' in table_names:
        columns = [col['name'] for col in inspector.get_columns('task')]
        if 'sort_order' not in columns:
            logger.info("Running migration: Adding 'sort_order' column to task table")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE task ADD COLUMN sort_order INTEGER DEFAULT 0"))
                conn.commit()
            logger.info("Migration complete: 'sort_order' column added")

    # --- UserCollection migrations ---
    if 'user_collections' in table_names:
        columns = [col['name'] for col in inspector.get_columns('user_collections')]
        with engine.connect() as conn:
            if 'description' not in columns:
                logger.info("Running migration: Adding 'description' column to user_collections table")
                conn.execute(text("ALTER TABLE user_collections ADD COLUMN description TEXT"))
                logger.info("Migration complete: 'description' column added")
            # Ingestion settings columns (v2.1)
            if 'use_vlm' not in columns:
                logger.info("Running migration: Adding ingestion settings columns to user_collections table")
                conn.execute(text("ALTER TABLE user_collections ADD COLUMN use_vlm BOOLEAN DEFAULT 0"))
                conn.execute(text("ALTER TABLE user_collections ADD COLUMN chunk_size INTEGER DEFAULT 1000"))
                conn.execute(text("ALTER TABLE user_collections ADD COLUMN chunk_overlap INTEGER DEFAULT 2"))
                conn.execute(text("ALTER TABLE user_collections ADD COLUMN embedding_model VARCHAR DEFAULT 'all-MiniLM-L6-v2'"))
                logger.info("Migration complete: ingestion settings columns added")
            # chunking_strategy added in P1-B (V2-3: simple wins over semantic)
            if 'chunking_strategy' not in columns:
                logger.info("Running migration: Adding 'chunking_strategy' column to user_collections table")
                conn.execute(text("ALTER TABLE user_collections ADD COLUMN chunking_strategy VARCHAR DEFAULT 'simple'"))
                logger.info("Migration complete: 'chunking_strategy' column added")
            conn.commit()

def get_session():
    with Session(engine) as session:
        yield session

# Default admin credentials.
# These are placeholders, intentionally insecure. Override BOTH via the
# environment before running Mentori in any non-local context:
#   export MENTORI_ADMIN_EMAIL="you@example.org"
#   export MENTORI_ADMIN_PASSWORD="<a long random string>"
# The default password below is deliberately invalid-looking so that any
# install with the defaults left in place is obvious.
import os
DEFAULT_ADMIN_EMAIL = os.getenv("MENTORI_ADMIN_EMAIL", "admin@mentori")
DEFAULT_ADMIN_PASSWORD = os.getenv("MENTORI_ADMIN_PASSWORD", "CHANGE_ME_ON_FIRST_LOGIN")

def _create_default_admin():
    """Create default admin account if no admin exists."""
    import bcrypt
    from backend.models.user import User
    from backend.models.system_settings import SystemSettings  # Ensure table is created

    with Session(engine) as session:
        # Check if any admin user exists
        existing_admin = session.exec(
            select(User).where(User.role == "admin")
        ).first()

        if existing_admin:
            logger.info(f"Admin account already exists: {existing_admin.email}")
            return

        # Check if default admin email is already taken (but not admin role)
        existing_user = session.exec(
            select(User).where(User.email == DEFAULT_ADMIN_EMAIL)
        ).first()

        if existing_user:
            # Promote existing user to admin
            existing_user.role = "admin"
            session.add(existing_user)
            session.commit()
            logger.info(f"Promoted existing user {DEFAULT_ADMIN_EMAIL} to admin")
            return

        # Create new default admin
        hashed_pw = bcrypt.hashpw(
            DEFAULT_ADMIN_PASSWORD.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        admin_user = User(
            email=DEFAULT_ADMIN_EMAIL,
            password_hash=hashed_pw,
            role="admin"
        )
        session.add(admin_user)
        session.commit()
        logger.info(f"Created default admin account: {DEFAULT_ADMIN_EMAIL}")

def init_db():
    # Run migrations before create_all to handle existing databases
    _run_migrations()
    SQLModel.metadata.create_all(engine)
    _create_default_admin()
