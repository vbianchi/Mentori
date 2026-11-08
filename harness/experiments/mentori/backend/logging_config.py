import logging
import sys
from datetime import datetime
from backend.agents.session_context import get_session_context

class UserContextFilter(logging.Filter):
    """
    A filter that injects user and task context into logs.
    
    Priority:
    1. Explicit 'user_id'/'task_id' in record (passed via extra={...})
    2. SessionContext (thread-local)
    3. Defaults ('system', 'N/A')
    """
    def filter(self, record):
        # 1. Check existing record attributes (explicit overrides)
        # Note: We don't want to overwrite if they exist, but if they are missing we inject.
        
        ctx = get_session_context()
        
        if not hasattr(record, 'user_id'):
            if ctx and ctx.user_id:
                record.user_id = ctx.user_id
            else:
                record.user_id = 'system'
                
        if not hasattr(record, 'task_id'):
            if ctx and ctx.task_display_id:
                record.task_id = f"task_{ctx.task_display_id}"
            else:
                record.task_id = 'N/A'
                
        return True

def setup_logging():
    # Clear any existing handlers attached to the root logger or 'mentori'
    # to avoid duplication if called multiple times or after basicConfig
    logger = logging.getLogger("mentori")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    # Also configure 'backend' logger since most modules are under 'backend' package
    backend_logger = logging.getLogger("backend")
    backend_logger.setLevel(logging.INFO)
    backend_logger.handlers.clear()
    backend_logger.propagate = False
    
    handler = logging.StreamHandler(sys.stdout)
    
    # [TIME] - [USER] - [TASK] - [INFO] - [FILE:LINE] - [MS]
    formatter = logging.Formatter(
        '[%(asctime)s] - [%(user_id)s] - [%(task_id)s] - [%(levelname)s] - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%SZ'
    )
    handler.setFormatter(formatter)
    
    # Apply filter to the handler so it applies to all records going through it
    handler.addFilter(UserContextFilter())
    
    logger.addHandler(handler)
    backend_logger.addHandler(handler)

    # File Handler
    try:
        import os
        log_dir = "backend/logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        file_handler = logging.FileHandler(f"{log_dir}/app.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        backend_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Failed to setup file logging: {e}")
    
    # Database Handler
    db_handler = DatabaseHandler()
    logger.addHandler(db_handler)
    backend_logger.addHandler(db_handler)
    
    # Best practice: Add filter to Loggers as well to filter before handler dispatch if needed,
    # but since handler has it, it's safe.
    # However, let's attach to logger to be sure for other handlers added later.
    logger.addFilter(UserContextFilter())
    backend_logger.addFilter(UserContextFilter())

    # Return 'mentori' or 'backend'? 
    # Usually we return one, but the side effect of configuring 'backend' is what matters.
    return logger

class DatabaseHandler(logging.Handler):
    """
    Custom handler to save logs to the database using SQLModel.
    Imports are done lazily to avoid circular dependencies during startup.
    """
    def emit(self, record):
        from sqlmodel import Session
        from backend.database import engine
        from backend.models.log import TaskLog

        try:
            # Only log if task_id is present and valid
            if hasattr(record, 'task_id') and record.task_id != 'N/A':
                 log_entry = TaskLog(
                     task_id=record.task_id,
                     level=record.levelname,
                     message=record.getMessage(),
                     timestamp=datetime.fromtimestamp(record.created)
                 )
                 # Use a short-lived session for safety
                 with Session(engine) as session:
                     session.add(log_entry)
                     session.commit()
        except Exception:
            self.handleError(record)

logger = setup_logging()
