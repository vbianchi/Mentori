# backend/routers/tasks.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func
from typing import List, Optional
import uuid
import random
import string
from backend.database import get_session
from backend.models.task import Task, Message
from backend.models.task import Task, Message
from backend.models.user import User
from backend.models.log import TaskLog
from backend.retrieval.models import UserCollection, IndexStatus
# ModelConfig import removed - thinking config now parsed from model identifier suffix
from backend.auth import get_current_user
from backend.workspace.manager import WorkspaceManager
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from backend.agents.model_router import ModelRouter
from backend.database import engine
from backend.logging_config import logger
from backend.agents.session_context import (
    SessionContext,
    set_session_context,
    resolve_model_for_chat,
    validate_agent_config
)
from backend.agents.orchestrator.schemas import CollaborationResponse
from backend.agents.prompts import get_agent_prompt
from backend.agents.debug_logger import get_debugger, is_debug_enabled
import re


def _strip_visible_thinking(content: str) -> str:
    """
    Strip visible thinking/reasoning blocks from model output.

    Some models output their reasoning as visible text (e.g., "[Thinking Process]:").
    This pollutes the conversation history and can cause context drift.
    We keep these blocks for display but strip them from what goes back to the model.
    """
    if not content:
        return content

    original = content

    # Pattern 1: [Thinking Process]: ... [Answer]:
    pattern1a = r'\[Thinking Process\]:.*?\[Answer\]:\s*'
    content = re.sub(pattern1a, '', content, flags=re.DOTALL | re.IGNORECASE)

    # Pattern 1b: [Thinking Process]: ... (standalone)
    pattern1b = r'\[Thinking Process\]:.*$'
    content = re.sub(pattern1b, '', content, flags=re.DOTALL | re.IGNORECASE)

    # Pattern 2: <thinking>...</thinking>
    pattern2 = r'<thinking>.*?</thinking>\s*'
    content = re.sub(pattern2, '', content, flags=re.DOTALL | re.IGNORECASE)

    # Pattern 3a: **Thinking:** ... **Answer:**
    pattern3a = r'\*\*Thinking:\*\*.*?\*\*Answer:\*\*\s*'
    content = re.sub(pattern3a, '', content, flags=re.DOTALL | re.IGNORECASE)

    # Pattern 3b: **Thinking:** ... (standalone)
    pattern3b = r'\*\*Thinking:\*\*.*$'
    content = re.sub(pattern3b, '', content, flags=re.DOTALL | re.IGNORECASE)

    # Clean up multiple newlines
    content = re.sub(r'\n{3,}', '\n\n', content)

    if content != original:
        stripped_len = len(original) - len(content)
        logger.info(f"Stripped {stripped_len} chars of visible thinking from model output")

    return content.strip()

model_router = ModelRouter()

router = APIRouter(prefix="/tasks", tags=["tasks"])

def generate_display_id():
    """
    Generate a date-based display ID with timestamp and short random suffix.

    Format: YYYYMMDD_HHMMSS_xxx (e.g., '20260203_143052_a7k')
    - Includes full date and time for uniqueness and sorting
    - Short random suffix handles multiple tasks created in same second
    - Human-readable: users can see when task was created
    """
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Add short random suffix for uniqueness (3 chars)
    chars = string.ascii_lowercase + string.digits
    suffix = ''.join(random.choice(chars) for _ in range(3))
    return f"{timestamp}_{suffix}"

class TaskCreate(BaseModel):
    title: str = "New Task"
    mode: str = "chat"
    model_identifier: str = "ollama::llama3.2:latest"

class TaskUpdate(BaseModel):
    title: Optional[str] = None

class TaskReorder(BaseModel):
    task_ids: List[str]  # List of task IDs in desired order

class TaskRead(BaseModel):
    id: str
    title: str
    mode: str
    model_identifier: str
    created_at: str
    status: str = "active" # Placeholder for now
    display_id: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

class MessageCreate(BaseModel):
    content: str
    role: str = "user"
    token_budget: Optional[int] = None  # Optional token budget limit
    role: str = "user"
    token_budget: Optional[int] = None  # Optional token budget limit
    orchestrated: bool = True  # Use new multi-agent orchestration system (default=True)
    is_coder_mode: bool = False # Direct access to Coder Agent (Jupyter)

class MessageRead(BaseModel):
    id: int
    role: str
    content: str
    timestamp: str
    thinking: Optional[str] = None
    model: Optional[str] = None
    tool_calls: Optional[List[dict]] = None
    tool_name: Optional[str] = None
    agent_role: Optional[str] = None
    metadata_blob: Optional[dict] = None

# --- Routes ---
@router.post("/", response_model=TaskRead)
def create_task(
    task_in: TaskCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    task_id = str(uuid.uuid4())
    display_id = generate_display_id()
    folder_name = f"task_{display_id}"

    # 1. Create Workspace
    try:
        # Use display_id-based folder name for consistency with UI
        workspace_path = WorkspaceManager.create_workspace(current_user.id, folder_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create workspace: {str(e)}")

    # 3. Create Task DB Entry
    new_task = Task(
        id=task_id,
        user_id=current_user.id,
        title=task_in.title,
        mode=task_in.mode,
        model_identifier=task_in.model_identifier,
        workspace_path=workspace_path,
        display_id=display_id
    )
    session.add(new_task)
    session.commit()
    session.refresh(new_task)

    logger.info(f"Created task '{new_task.title}'", extra={"user_id": current_user.email, "task_id": folder_name})

    return TaskRead(
        id=new_task.id,
        title=new_task.title,
        mode=new_task.mode,
        model_identifier=new_task.model_identifier,
        created_at=new_task.created_at.isoformat(),
        display_id=new_task.display_id,
        input_tokens=new_task.input_tokens,
        output_tokens=new_task.output_tokens,
        total_tokens=new_task.total_tokens
    )

@router.delete("/{task_id}")
def delete_task(
    task_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    task = session.exec(select(Task).where(Task.id == task_id, Task.user_id == current_user.id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    display_id = task.display_id
    task_title = task.title
    
    # Clean up workspace files
    try:
        from pathlib import Path
        folder_name = Path(task.workspace_path).name
        WorkspaceManager.cleanup_workspace(current_user.id, folder_name)
    except Exception as e:
        logger.error(f"Failed to cleanup workspace for task {task_id}: {e}", extra={"user_id": current_user.email})

    session.delete(task)
    session.commit()

    logger.info(f"Deleted task '{task_title}'", extra={"user_id": current_user.email, "task_id": f"task_{display_id}"})
    return {"ok": True}

@router.put("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: str,
    task_in: TaskUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    task = session.exec(select(Task).where(Task.id == task_id, Task.user_id == current_user.id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    old_title = task.title
    if task_in.title is not None:
        task.title = task_in.title

    session.add(task)
    session.commit()
    session.refresh(task)

    logger.info(f"Renamed task from '{old_title}' to '{task.title}'", extra={"user_id": current_user.email, "task_id": f"task_{task.display_id}"})
    return TaskRead(
        id=task.id,
        title=task.title,
        mode=task.mode,
        model_identifier=task.model_identifier,
        created_at=task.created_at.isoformat(),
        display_id=task.display_id,
        input_tokens=task.input_tokens,
        output_tokens=task.output_tokens,
        total_tokens=task.total_tokens
    )

@router.get("/", response_model=List[TaskRead])
def list_tasks(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Order by sort_order first (lower = first), then by created_at desc as fallback
    tasks = session.exec(
        select(Task)
        .where(Task.user_id == current_user.id)
        .order_by(Task.sort_order.asc(), Task.created_at.desc())
    ).all()
    return [
        TaskRead(
            id=t.id,
            title=t.title,
            mode=t.mode,
            model_identifier=t.model_identifier,
            created_at=t.created_at.isoformat(),
            display_id=t.display_id,
            input_tokens=t.input_tokens,
            output_tokens=t.output_tokens,
            total_tokens=t.total_tokens
        ) for t in tasks
    ]

@router.post("/reorder")
def reorder_tasks(
    reorder_in: TaskReorder,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Reorder tasks by setting sort_order based on provided task_ids list."""
    # Verify all tasks belong to user and update sort_order
    for index, task_id in enumerate(reorder_in.task_ids):
        task = session.exec(
            select(Task).where(Task.id == task_id, Task.user_id == current_user.id)
        ).first()
        if task:
            task.sort_order = index
            session.add(task)

    session.commit()
    logger.info(f"Reordered {len(reorder_in.task_ids)} tasks", extra={"user_id": current_user.email})
    return {"ok": True, "reordered": len(reorder_in.task_ids)}

@router.get("/{task_id}", response_model=TaskRead)
def get_task(
    task_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    task = session.exec(select(Task).where(Task.id == task_id, Task.user_id == current_user.id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskRead(
        id=task.id,
        title=task.title,
        mode=task.mode,
        model_identifier=task.model_identifier,
        created_at=task.created_at.isoformat(),
        display_id=task.display_id,
        input_tokens=task.input_tokens,
        output_tokens=task.output_tokens,
        total_tokens=task.total_tokens
    )

@router.get("/{task_id}/messages", response_model=List[MessageRead])
def list_task_messages(
    task_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Verify Task ownership
    task = session.exec(select(Task).where(Task.id == task_id, Task.user_id == current_user.id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    msgs = session.exec(select(Message).where(Message.task_id == task_id).order_by(Message.sequence)).all()

    logger.info(f"[LOAD_MESSAGES] Loaded {len(msgs)} messages for task {task_id}")
    for m in msgs:
        logger.debug(f"[LOAD_MESSAGES] seq={m.sequence} role={m.role} content_len={len(m.content or '')}")

    return [
        MessageRead(
            id=m.id,
            role=m.role,
            content=m.content,
            timestamp=m.timestamp.isoformat(),
            model=m.metadata_blob.get("model") if m.metadata_blob else None,
            tool_calls=m.metadata_blob.get("tool_calls") if m.metadata_blob else None,
            tool_name=m.metadata_blob.get("tool_name") if m.metadata_blob else None,
            thinking=m.metadata_blob.get("thinking") if m.metadata_blob else None,
            agent_role=m.metadata_blob.get("agent_role") if m.metadata_blob else None,
            metadata_blob=m.metadata_blob
        ) for m in msgs
    ]

@router.get("/{task_id}/logs")
def get_task_logs(
    task_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Verify Task ownership
    task = session.exec(select(Task).where(Task.id == task_id, Task.user_id == current_user.id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Logs are stored with task_id string "task_{display_id}"
    log_task_id = f"task_{task.display_id}"
    
    logs = session.exec(
        select(TaskLog)
        .where(TaskLog.task_id == log_task_id)
        .order_by(TaskLog.timestamp)
    ).all()

    return [
        {
            "timestamp": l.timestamp.isoformat(),
            "level": l.level,
            "message": l.message
        } for l in logs
    ]

@router.post("/{task_id}/chat")
async def chat_with_task(
    task_id: str,
    message_in: MessageCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # 1. Verify Task
    task = session.exec(select(Task).where(Task.id == task_id, Task.user_id == current_user.id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 2. Resolve model from user's agent role configuration
    # For agentic mode: use Lead Researcher agent
    # For basic chat: use Editor agent
    # Both fallback to Default if their specific role is not configured
    agent_roles = current_user.settings.get("agent_roles", {})

    # Validate that user has configured their agents
    is_valid, error_msg = validate_agent_config(agent_roles)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=error_msg
        )

    # Resolve which model to use (Lead Researcher → Default fallback)
    # IF Coder Mode is enabled, force 'coder' role
    if message_in.is_coder_mode:
        resolved_role = "coder"
        resolved_model = agent_roles.get("coder")
        if not resolved_model:
            # Fallback if coder not explicitly set
            resolved_model = agent_roles.get("default")
            
        # FORCE override orchestration to False for direct mode
        message_in.orchestrated = False
        logger.info(f"[DIRECT_MODE] User requested Direct Coder Mode. Role forced to 'coder'. Orchestration disabled.")
    else:
        resolved_model, resolved_role = resolve_model_for_chat(agent_roles, preferred_role="lead_researcher")

    if not resolved_model:
        raise HTTPException(
            status_code=400,
            detail="No model configured. Please go to Settings → Agent Roles and assign a Lead Researcher or Default agent."
        )

    logger.info(f"Resolved agent role '{resolved_role}' → model '{resolved_model}'")

    # Get user's available document indexes for context injection
    user_indexes = session.exec(
        select(UserCollection)
        .where(UserCollection.user_id == current_user.id)
        .where(UserCollection.status == IndexStatus.READY)
    ).all()
    available_indexes = ", ".join([idx.name for idx in user_indexes]) if user_indexes else "default"
    logger.info(f"Available document indexes for user: {available_indexes}")

    # Include resolved role and available indexes in agent_roles for the session
    agent_roles_with_resolved = {
        **agent_roles,
        "_resolved_role": resolved_role,  # Special key for current active role
        "_resolved_model": resolved_model,
        "_available_indexes": available_indexes  # List of user's document indexes
    }

    # Dynamic Workspace Path Resolution
    # We resolve the path at runtime because the container config (WORKSPACE_DIR) might have changed
    # since the task was created. The DB stored path might be stale (e.g. /app/workspace vs /workspace_data).
    try:
        if task.display_id:
            # Reconstruct path: WORKSPACE_DIR / user_id / task_{display_id}
            # This ensures we always point to the currently mounted volume
            dynamic_path = str(WorkspaceManager.get_task_path(current_user.id, f"task_{task.display_id}"))
            logger.info(f"Resolved dynamic workspace path: {dynamic_path}")
        else:
            # Fallback for old tasks without display_id
            dynamic_path = task.workspace_path
            logger.warning(f"Using stored workspace path (no display_id): {dynamic_path}")
    except Exception as e:
        logger.error(f"Failed to resolve dynamic workspace path: {e}")
        dynamic_path = task.workspace_path

    # Build session context early for logging
    # DEBUG: Log api_keys being loaded from user settings
    user_api_keys = current_user.settings.get("api_keys", {})
    api_key_names = list(user_api_keys.keys()) if user_api_keys else []
    has_tavily = "TAVILY_API_KEY" in user_api_keys and bool(user_api_keys.get("TAVILY_API_KEY"))
    logger.info(f"[SESSION_CONTEXT] Loading api_keys: keys={api_key_names}, has_TAVILY={has_tavily}")
    if has_tavily:
        tavily_len = len(user_api_keys.get("TAVILY_API_KEY", ""))
        logger.info(f"[SESSION_CONTEXT] TAVILY_API_KEY present, length={tavily_len}")

    # Fetch user's available RAG indexes for injection into prompts
    user_indexes = session.exec(
        select(UserCollection)
        .where(UserCollection.user_id == current_user.id)
        .where(UserCollection.status == IndexStatus.READY)
        .order_by(UserCollection.created_at.desc())
    ).all()
    available_indexes = [
        {
            "name": idx.name,
            "description": idx.description or "",
            "file_count": len(idx.file_paths) if idx.file_paths else 0,
        }
        for idx in user_indexes
    ]
    logger.info(f"[SESSION_CONTEXT] Found {len(available_indexes)} ready indexes for user")

    session_ctx_temp = SessionContext(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role,
        user_first_name=current_user.first_name,
        user_last_name=current_user.last_name,
        user_preferences=current_user.preferences,
        task_id=task.id,
        task_display_id=task.display_id,
        task_title=task.title,
        workspace_path=dynamic_path, # Use dynamic path
        model_identifier=resolved_model,  # Use resolved model from agent roles
        mode=task.mode,
        api_keys=user_api_keys,
        rag_preferences=current_user.settings.get("rag_preferences", {}),
        agent_roles=agent_roles_with_resolved,  # Include full agent roles + resolved info
        require_plan_approval=current_user.settings.get("require_plan_approval", False),
        available_indexes=available_indexes,  # User's ready RAG indexes for document queries
    )
    set_session_context(session_ctx_temp)

    logger.info(f"Received message: '{message_in.content[:50]}...'")

    # 2. Save User Message
    # Get current sequence
    last_msg = session.exec(select(Message).where(Message.task_id == task_id).order_by(Message.sequence.desc())).first()
    next_seq = (last_msg.sequence + 1) if last_msg else 1

    user_msg = Message(
        task_id=task_id,
        role="user",
        content=message_in.content,
        sequence=next_seq
    )
    session.add(user_msg)
    session.commit()
    session.refresh(user_msg)

    # 3. Prepare History (Entire history for now, could limit later)
    history_msgs = session.exec(
        select(Message)
        .where(Message.task_id == task_id)
        .order_by(Message.sequence)
    ).all()

    # Build chat history, stripping thinking blocks from assistant messages
    # This prevents old thinking from polluting the model's context
    chat_history = []
    stripped_count = 0
    for m in history_msgs:
        if m.role == "assistant":
            # Strip visible thinking from assistant messages
            original_content = m.content or ""
            original_len = len(original_content)
            cleaned_content = _strip_visible_thinking(original_content)

            # DEBUG: Log what we're stripping
            if "[Thinking Process]" in original_content or "<thinking>" in original_content:
                logger.info(f"[STRIP_DEBUG] Found thinking pattern in message seq={m.sequence}")
                logger.info(f"[STRIP_DEBUG] Original length: {original_len}, Cleaned length: {len(cleaned_content)}")
                if original_len > 0:
                    logger.info(f"[STRIP_DEBUG] Original preview: {original_content[:200]}...")
                    logger.info(f"[STRIP_DEBUG] Cleaned preview: {cleaned_content[:200]}...")

            if len(cleaned_content) < original_len:
                stripped_count += 1
                logger.info(f"[STRIP] Stripped {original_len - len(cleaned_content)} chars from seq={m.sequence}")
            
            # Reconstruct message with tool calls if present
            msg_dict = {"role": m.role, "content": cleaned_content}
            if m.metadata_blob and m.metadata_blob.get("tool_calls"):
                 msg_dict["tool_calls"] = m.metadata_blob.get("tool_calls")
            
            chat_history.append(msg_dict)
        elif m.role == "tool":
            # Reconstruct tool message with name
            msg_dict = {"role": m.role, "content": m.content}
            if m.metadata_blob and m.metadata_blob.get("tool_name"):
                msg_dict["name"] = m.metadata_blob.get("tool_name")
            chat_history.append(msg_dict)
        else:
            chat_history.append({"role": m.role, "content": m.content})

    if stripped_count > 0:
        logger.info(f"[STRIP] Total: Stripped thinking from {stripped_count} assistant messages in history")
    else:
        logger.info(f"[STRIP] No thinking patterns found in {len([m for m in history_msgs if m.role == 'assistant'])} assistant messages")

    # Debug: Log history loading details
    if is_debug_enabled():
        debugger = get_debugger(task_id)
        debugger.log_history_loading(history_msgs, stripped_count)

    # 4a. Inject Agent System Prompt (defines agent identity and behavior)
    agent_system_prompt = get_agent_prompt(resolved_role)
    chat_history.insert(0, {"role": "system", "content": agent_system_prompt})
    logger.info(f"Injected system prompt for role '{resolved_role}'")

    # 4b. Inject User Context (for personalization)
    user_context_parts = []
    if session_ctx_temp.user_first_name or session_ctx_temp.user_last_name:
        user_context_parts.append(f"User Name: {session_ctx_temp.user_display_name}")
    if session_ctx_temp.user_preferences:
        user_context_parts.append(f"User Preferences & Context:\n{session_ctx_temp.user_preferences}")

    if user_context_parts:
        user_context = "# User Information\n\n" + "\n\n".join(user_context_parts)
        # Insert at beginning of conversation
        chat_history.insert(0, {"role": "system", "content": user_context})
        logger.info(f"Injected user context for {session_ctx_temp.user_display_name}")

    # 4c. Inject Knowledge Base context (using UserCollection imported at module level)
    try:
        ready_indexes = session.exec(
            select(UserCollection)
            .where(UserCollection.user_id == current_user.id)
            .where(UserCollection.status == IndexStatus.READY)
            .order_by(UserCollection.created_at.desc())
        ).all()

        if ready_indexes:
            index_list = "\n".join([
                f"  - '{idx.name}' ({len(idx.file_paths)} files, created {idx.created_at.strftime('%Y-%m-%d')})"
                for idx in ready_indexes
            ])

            kb_context = (
                "# Knowledge Base Available\n\n"
                f"You have access to {len(ready_indexes)} document indexes:\n"
                f"{index_list}\n\n"
                "To query an index, use: query_documents(query='...', index_name='exact_name_from_above')\n"
                "To list all indexes, use: list_document_indexes()"
            )

            # Insert as first system message (after any existing system messages)
            system_msg = {"role": "system", "content": kb_context}

            # Find position after existing system messages
            insert_pos = 0
            for i, msg in enumerate(chat_history):
                if msg.get("role") == "system":
                    insert_pos = i + 1
                else:
                    break

            chat_history.insert(insert_pos, system_msg)
            logger.info(f"Injected {len(ready_indexes)} Knowledge Base indexes into agent context")
        else:
            logger.debug("No ready Knowledge Base indexes found for user")

    except Exception as e:
        logger.warning(f"Failed to inject Knowledge Base context: {e}")
        # Continue without KB context - not critical

    # 4. Start Background Task
    from backend.agents.task_manager import task_manager

    # Check if we should allow multiple concurrent runs? 
    # For now, start_chat_task handles deduplication log
    
    # We parse thinking config here to pass to task manager (or let task manager do it? 
    # TaskManager calls chat_loop, which takes 'model_identifier' and 'think'. 
    # Logic was in endpoint previously. Let's move parsing to TaskManager or keep here.
    # PREVIOUSLY: logic was inside response_generator.
    # Let's clean it up by passing raw model ID and letting TaskManager/ChatLoop handle?
    # chat_loop takes `think` param. So we should parse it here or there.
    # Let's keep parsing here to be consistent with previous logic.
    
    # Parse model identifier for thinking suffix
    actual_model = resolved_model
    think_param = False

    if "[think" in resolved_model:
        base_model, think_suffix = resolved_model.split("[think", 1)
        actual_model = base_model
        if think_suffix == "]":
            think_param = True
        elif think_suffix.startswith(":"):
            level = think_suffix[1:-1]
            think_param = level

    # Choose between orchestrated (new multi-agent) and legacy chat loop
    if message_in.orchestrated:
        logger.info(f"Starting orchestrated chat task for {task_id}")
        await task_manager.start_orchestrated_task(
            task_id=task_id,
            model_router=model_router,
            model_identifier=actual_model,
            messages=chat_history,
            session_context=session_ctx_temp,
            max_steps=10,
            think=think_param,
            display_model=resolved_model,
            token_budget=message_in.token_budget
        )
    else:
        logger.info(f"Starting legacy chat task for {task_id}")
        await task_manager.start_chat_task(
            task_id=task_id,
            model_router=model_router,
            model_identifier=actual_model,
            messages=chat_history,
            session_context=session_ctx_temp,
            max_steps=10,
            think=think_param,
            display_model=resolved_model,
            token_budget=message_in.token_budget
        )

    return {"status": "started", "detail": "Background task initiated", "orchestrated": message_in.orchestrated}

@router.get("/{task_id}/events")
async def task_events(
    task_id: str,
    session: Session = Depends(get_session),
    # Current user check? Events might be public for shareable links later?
    # For now restrict.
    # Note: EventSource in browser doesn't send headers easily. 
    # We might need query param for token? Or cookies.
    # For Mentori local, we might skip strict auth on this specific endpoint OR rely on header if client supports it (fetch-based SSE).
    # Dashboard uses 'fetch' with headers, so headers work.
    current_user: User = Depends(get_current_user) 
):
    from backend.agents.task_manager import task_manager
    
    async def event_generator():
        # Subscribe
        # Yield initial connection msg?
        # yield "data: {}\n\n"
        
        async for msg_json in task_manager.subscribe(task_id):
            yield f"{msg_json}\n" # chat_loop output is lines of JSON. 
            # If we want SSE standard:
            # yield f"data: {msg_json.strip()}\n\n"
            # But frontend currently expects raw JSON lines stream (ndjson style)?
            # Dashboard.jsx uses: `reader.read() ... buffer.split('\n')`. 
            # So simple newline-delimited JSON is what consistent with current frontend.
            # We don't need "data: " prefix unless we switch to EventSource API.
            # Plan said "SSE endpoint", but Dashboard currently does fetch stream.
            # Let's stick to NDJSON for compatibility with current parsing logic 
            # (which we will adapt to persistent connection, but format can stay same).
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")


# =========================================
# TOOL PROGRESS ENDPOINT (internal, from tool-server)
# =========================================

class ToolProgressPayload(BaseModel):
    tool_name: str
    message: str
    phase: str = ""
    step: int = 0
    total_steps: int = 0


@router.post("/{task_id}/progress")
async def receive_tool_progress(task_id: str, payload: ToolProgressPayload):
    """
    Receive a progress event from a running tool and broadcast it to
    frontend subscribers via the existing WebSocket/SSE system.

    This endpoint is called by the tool server (internal network only).
    No auth required — it's same-host / internal Docker network.
    """
    from backend.agents.task_manager import task_manager

    event = {
        "type": "tool_progress",
        "tool_name": payload.tool_name,
        "message": payload.message,
        "phase": payload.phase,
        "step": payload.step,
        "total_steps": payload.total_steps,
    }

    await task_manager.broadcast_event(task_id, event)
    return {"ok": True}


# =========================================
# CODER ENDPOINT (Notebook-based coding)
# =========================================

class CoderMessageCreate(BaseModel):
    """Request body for coder chat endpoint."""
    content: str
    role: str = "user"


@router.post("/{task_id}/coder/chat")
async def coder_chat(
    task_id: str,
    message_in: CoderMessageCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Coder mode chat with Jupyter notebook integration.

    This endpoint provides a specialized coder agent that operates
    on a Jupyter notebook attached to the task. The agent can:
    - Add and execute code cells iteratively
    - Fix errors at the cell level
    - Create visualizations and data analysis
    - Save notebooks as .ipynb files

    The notebook is persisted in the task workspace and can be
    opened in Jupyter if needed.
    """
    # 1. Verify Task
    task = session.exec(select(Task).where(Task.id == task_id, Task.user_id == current_user.id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 2. Resolve coder model from user's agent role configuration
    agent_roles = current_user.settings.get("agent_roles", {})

    # Validate that user has configured their agents
    is_valid, error_msg = validate_agent_config(agent_roles)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # Resolve coder model (coder → default fallback)
    resolved_model = agent_roles.get("coder") or agent_roles.get("default")

    if not resolved_model:
        raise HTTPException(
            status_code=400,
            detail="No coder model configured. Please go to Settings → Agent Roles and assign a Coder or Default agent."
        )

    logger.info(f"Coder chat: resolved model '{resolved_model}' for task {task_id}")

    # 3. Build workspace path dynamically
    try:
        if task.display_id:
            dynamic_path = str(WorkspaceManager.get_task_path(current_user.id, f"task_{task.display_id}"))
        else:
            dynamic_path = task.workspace_path
    except Exception as e:
        logger.error(f"Failed to resolve workspace path: {e}")
        dynamic_path = task.workspace_path

    # 4. Build session context for coder
    agent_roles_with_resolved = {
        **agent_roles,
        "_resolved_role": "coder",
        "_resolved_model": resolved_model,
    }

    session_ctx = SessionContext(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role,
        user_first_name=current_user.first_name,
        user_last_name=current_user.last_name,
        user_preferences=current_user.preferences,
        task_id=task.id,
        task_display_id=task.display_id,
        task_title=task.title,
        workspace_path=dynamic_path,
        model_identifier=resolved_model,
        mode="coder",
        api_keys=current_user.settings.get("api_keys", {}),
        agent_roles=agent_roles_with_resolved,
    )
    set_session_context(session_ctx)

    logger.info(f"Coder chat: received message '{message_in.content[:50]}...'")

    # 5. Save User Message to DB
    last_msg = session.exec(select(Message).where(Message.task_id == task_id).order_by(Message.sequence.desc())).first()
    next_seq = (last_msg.sequence + 1) if last_msg else 1

    user_msg = Message(
        task_id=task_id,
        role="user",
        content=message_in.content,
        sequence=next_seq,
        metadata_blob={"mode": "coder"}
    )
    session.add(user_msg)
    session.commit()

    # 6. Build message list
    # Context for follow-up requests comes from:
    # - Memory vault (session summaries) → injected into system prompt
    # - Notebook state (existing cells with code) → injected into system prompt
    # - Kernel state (variables in memory) → injected into system prompt
    # - Chat History (past 20 messages) → injected here
    
    # Fetch recent history (limit to 20 to prevent context overflow)
    history_msgs = session.exec(
        select(Message)
        .where(Message.task_id == task_id)
        .order_by(Message.sequence.desc())
        .limit(20)
    ).all()
    history_msgs.reverse()  # Restore chronological order

    # Build history list
    messages = []
    
    for m in history_msgs:
        if m.role == "assistant":
            # Strip thinking blocks to save context
            clean_content = _strip_visible_thinking(m.content or "")
            
            # Helper to truncate tool result content in history
            # (Rationale: The Agent can see the actual cell output in NotebookState, 
            # so we don't need the full 100K char output in the chat history)
            tool_calls = m.metadata_blob.get("tool_calls") if m.metadata_blob else None
            
            messages.append({
                "role": "assistant",
                "content": clean_content,
                "tool_calls": tool_calls
            })
            
        elif m.role == "tool":
            # Truncate tool outputs in history
            content = m.content or ""
            if len(content) > 1000:
                content = content[:500] + f"\n...[truncated {len(content)-1000} chars]...\n" + content[-500:]
                
            tool_name = m.metadata_blob.get("tool_name") if m.metadata_blob else None
            
            messages.append({
                "role": "tool",
                "content": content,
                "name": tool_name
            })
            
        elif m.role == "user":
            messages.append({"role": "user", "content": m.content})
            
    # Helper for stripping thinking (copy from above or import?)
    # Since _strip_visible_thinking is defined in this module (it was used in main chat), we can use it.
    # Note: Check if _strip_visible_thinking is available in scope or needs to be moved.
    # It was used in chat endpoint around line 536. If it's a helper function in the module, we can use it.
    # If it's inline logic, we need to duplicate or refactor.
    # checking file content... it was a helper call `_strip_visible_thinking`.


    # 7. Parse thinking config
    actual_model = resolved_model
    think_param = False

    if "[think" in resolved_model:
        base_model, think_suffix = resolved_model.split("[think", 1)
        actual_model = base_model
        if think_suffix == "]":
            think_param = True
        elif think_suffix.startswith(":"):
            level = think_suffix[1:-1]
            think_param = level

    # 8. Start coder task
    from backend.agents.task_manager import task_manager

    logger.info(f"Starting coder task for {task_id}")
    await task_manager.start_coder_task(
        task_id=task_id,
        model_router=model_router,
        model_identifier=actual_model,
        messages=messages,
        session_context=session_ctx,
        max_steps=100,
        think=think_param,
        display_model=resolved_model,
    )

    return {
        "status": "started",
        "detail": "Coder task initiated",
        "mode": "coder",
        "notebook_path": f"notebooks/{task.display_id}_*.ipynb"
    }


# =========================================
# NOTEBOOK ENDPOINTS
# =========================================

@router.get("/{task_id}/notebooks")
def list_notebooks(
    task_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    List all notebooks for a task.

    Returns a list of notebook names (without .ipynb extension).
    """
    from pathlib import Path

    task = session.exec(select(Task).where(Task.id == task_id, Task.user_id == current_user.id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Build workspace path
    try:
        if task.display_id:
            workspace_path = WorkspaceManager.get_task_path(current_user.id, f"task_{task.display_id}")
        else:
            workspace_path = Path(task.workspace_path)
    except Exception as e:
        logger.error(f"Failed to resolve workspace path: {e}")
        workspace_path = Path(task.workspace_path)

    notebooks_dir = workspace_path / "notebooks"

    if not notebooks_dir.exists():
        return {"notebooks": [], "count": 0}

    import json as _json
    notebooks = []
    for path in sorted(notebooks_dir.glob("*.ipynb")):
        meta = {"name": path.stem, "kernel": "python3", "kernel_display": "Python 3",
                "cell_count": 0, "code_cells": 0, "modified": None}
        try:
            with open(path, "r", encoding="utf-8") as f:
                nb = _json.load(f)
            cells = nb.get("cells", [])
            meta["cell_count"] = len(cells)
            meta["code_cells"] = sum(1 for c in cells if c.get("cell_type") == "code")
            ks = nb.get("metadata", {}).get("kernelspec", {})
            meta["kernel"] = ks.get("name", "python3")
            meta["kernel_display"] = ks.get("display_name", "Python 3")
            meta["modified"] = path.stat().st_mtime
        except Exception:
            pass
        notebooks.append(meta)

    return {
        "notebooks": notebooks,
        "count": len(notebooks)
    }


@router.post("/{task_id}/notebooks")
def create_notebook(
    task_id: str,
    body: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new empty Jupyter notebook for a task.

    Body: { "name": "analysis" }   (no extension — .ipynb is added automatically)
    Returns: { "name": str, "path": str }
    """
    import re as _re
    import json as _json
    from pathlib import Path

    name = (body.get("name") or "notebook").strip()
    # Sanitise: allow only alphanumeric, dash, underscore, dot
    if not _re.match(r'^[\w\-\.]+$', name):
        raise HTTPException(status_code=400, detail="Invalid notebook name. Use only letters, numbers, dashes, underscores, or dots.")
    if len(name) > 80:
        raise HTTPException(status_code=400, detail="Notebook name too long (max 80 chars).")

    # Kernel selection: "python3" (default) or "ir" (R via IRkernel)
    kernel = (body.get("kernel") or "python3").strip()
    _KERNELS = {
        "python3": {"display_name": "Python 3", "language": "python", "lang_info": {"name": "python", "version": "3.12.0"}},
        "ir":      {"display_name": "R",         "language": "R",      "lang_info": {"name": "R",      "version": "4.5.0"}},
    }
    if kernel not in _KERNELS:
        raise HTTPException(status_code=400, detail=f"Unsupported kernel '{kernel}'. Supported: {list(_KERNELS)}")
    k = _KERNELS[kernel]

    task = session.exec(select(Task).where(Task.id == task_id, Task.user_id == current_user.id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    try:
        if task.display_id:
            workspace_path = WorkspaceManager.get_task_path(current_user.id, f"task_{task.display_id}")
        else:
            workspace_path = Path(task.workspace_path)
    except Exception:
        workspace_path = Path(task.workspace_path)

    notebooks_dir = workspace_path / "notebooks"
    notebooks_dir.mkdir(parents=True, exist_ok=True)

    nb_path = notebooks_dir / f"{name}.ipynb"
    if nb_path.exists():
        raise HTTPException(status_code=409, detail=f"Notebook '{name}' already exists.")

    empty_notebook = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": k["display_name"], "language": k["language"], "name": kernel},
            "language_info": k["lang_info"],
        },
        "cells": []
    }
    with open(nb_path, "w") as f:
        _json.dump(empty_notebook, f, indent=2)

    return {"name": name, "path": f"./notebooks/{name}.ipynb", "kernel": kernel}


@router.get("/{task_id}/notebooks/{notebook_name}")
def get_notebook(
    task_id: str,
    notebook_name: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Load a specific notebook's content.

    Returns the notebook with all cells and their outputs.
    """
    from pathlib import Path
    from backend.agents.notebook.manager import NotebookManager

    task = session.exec(select(Task).where(Task.id == task_id, Task.user_id == current_user.id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Build workspace path
    try:
        if task.display_id:
            workspace_path = str(WorkspaceManager.get_task_path(current_user.id, f"task_{task.display_id}"))
        else:
            workspace_path = task.workspace_path
    except Exception as e:
        logger.error(f"Failed to resolve workspace path: {e}")
        workspace_path = task.workspace_path

    # Load notebook
    try:
        manager = NotebookManager(workspace_path, str(task.display_id or task.id))
        notebook = manager.load_notebook(notebook_name)

        # Convert to JSON-serializable format
        cells_data = []
        for cell in notebook.cells:
            cell_data = {
                "id": cell.id,
                "cell_type": cell.cell_type,
                "source": cell.source,
                "status": cell.status,
                "execution_count": cell.execution_count,
                "outputs": [o.to_dict() for o in cell.outputs]
            }
            cells_data.append(cell_data)

        return {
            "name": notebook.name,
            "path": notebook.path,
            "kernel": notebook.kernel_name,
            "cells": cells_data,
            "cell_count": len(cells_data)
        }

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Notebook '{notebook_name}' not found")
    except Exception as e:
        logger.error(f"Failed to load notebook: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load notebook: {str(e)}")


class CellUpdate(BaseModel):
    """Request body for updating a cell."""
    source: str


@router.put("/{task_id}/notebooks/{notebook_name}/cells/{cell_id}")
def update_cell(
    task_id: str,
    notebook_name: str,
    cell_id: str,
    cell_update: CellUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Update a cell's source code.

    This clears the cell's outputs (needs re-execution).
    """
    from pathlib import Path
    from backend.agents.notebook.manager import NotebookManager

    task = session.exec(select(Task).where(Task.id == task_id, Task.user_id == current_user.id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Build workspace path
    try:
        if task.display_id:
            workspace_path = str(WorkspaceManager.get_task_path(current_user.id, f"task_{task.display_id}"))
        else:
            workspace_path = task.workspace_path
    except Exception as e:
        logger.error(f"Failed to resolve workspace path: {e}")
        workspace_path = task.workspace_path

    # Load and update notebook
    try:
        manager = NotebookManager(workspace_path, str(task.display_id or task.id))
        notebook = manager.load_notebook(notebook_name)

        # Find and update cell
        cell = notebook.get_cell(cell_id)
        if not cell:
            raise HTTPException(status_code=404, detail=f"Cell '{cell_id}' not found")

        cell.source = cell_update.source
        cell.clear_outputs()  # Clear outputs since source changed

        # Save notebook
        manager.save_notebook(notebook)

        return {
            "success": True,
            "cell_id": cell_id,
            "message": "Cell updated successfully"
        }

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Notebook '{notebook_name}' not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update cell: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update cell: {str(e)}")


class AddCellRequest(BaseModel):
    """Request body for adding a cell."""
    source: str
    cell_type: str = "code"  # "code" or "markdown"
    position: Optional[int] = None  # Insert at position, or append if None


@router.post("/{task_id}/notebooks/{notebook_name}/cells")
def add_cell(
    task_id: str,
    notebook_name: str,
    cell_request: AddCellRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Add a new cell to the notebook.
    """
    from pathlib import Path
    from backend.agents.notebook.manager import NotebookManager

    task = session.exec(select(Task).where(Task.id == task_id, Task.user_id == current_user.id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Build workspace path
    try:
        if task.display_id:
            workspace_path = str(WorkspaceManager.get_task_path(current_user.id, f"task_{task.display_id}"))
        else:
            workspace_path = task.workspace_path
    except Exception as e:
        logger.error(f"Failed to resolve workspace path: {e}")
        workspace_path = task.workspace_path

    try:
        manager = NotebookManager(workspace_path, str(task.display_id or task.id))
        notebook = manager.load_notebook(notebook_name)

        # Add cell
        cell = notebook.add_cell(
            source=cell_request.source,
            cell_type=cell_request.cell_type,
            position=cell_request.position
        )

        # Save notebook
        manager.save_notebook(notebook)

        return {
            "success": True,
            "cell_id": cell.id,
            "cell_type": cell.cell_type,
            "index": notebook.get_cell_index(cell.id),
            "message": "Cell added successfully"
        }

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Notebook '{notebook_name}' not found")
    except Exception as e:
        logger.error(f"Failed to add cell: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add cell: {str(e)}")


@router.delete("/{task_id}/notebooks/{notebook_name}/cells/{cell_id}")
def delete_cell(
    task_id: str,
    notebook_name: str,
    cell_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a cell from the notebook.
    """
    from pathlib import Path
    from backend.agents.notebook.manager import NotebookManager

    task = session.exec(select(Task).where(Task.id == task_id, Task.user_id == current_user.id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Build workspace path
    try:
        if task.display_id:
            workspace_path = str(WorkspaceManager.get_task_path(current_user.id, f"task_{task.display_id}"))
        else:
            workspace_path = task.workspace_path
    except Exception as e:
        logger.error(f"Failed to resolve workspace path: {e}")
        workspace_path = task.workspace_path

    try:
        manager = NotebookManager(workspace_path, str(task.display_id or task.id))
        notebook = manager.load_notebook(notebook_name)

        # Delete cell
        if not notebook.delete_cell(cell_id):
            raise HTTPException(status_code=404, detail=f"Cell '{cell_id}' not found")

        # Save notebook
        manager.save_notebook(notebook)

        return {
            "success": True,
            "cell_id": cell_id,
            "message": "Cell deleted successfully"
        }

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Notebook '{notebook_name}' not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete cell: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete cell: {str(e)}")


@router.post("/{task_id}/notebooks/{notebook_name}/cells/{cell_id}/execute")
async def execute_cell(
    task_id: str,
    notebook_name: str,
    cell_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Execute a single cell and return the result.

    This is a synchronous execution (waits for completion).
    For streaming execution, use the SSE endpoint.
    """
    from pathlib import Path
    from backend.agents.notebook.manager import NotebookManager
    from backend.agents.notebook.kernel import KernelRegistry
    from backend.agents.notebook.schema import CellOutput

    task = session.exec(select(Task).where(Task.id == task_id, Task.user_id == current_user.id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Build workspace path
    try:
        if task.display_id:
            workspace_path = str(WorkspaceManager.get_task_path(current_user.id, f"task_{task.display_id}"))
        else:
            workspace_path = task.workspace_path
    except Exception as e:
        logger.error(f"Failed to resolve workspace path: {e}")
        workspace_path = task.workspace_path

    try:
        manager = NotebookManager(workspace_path, str(task.display_id or task.id))
        notebook = manager.load_notebook(notebook_name)

        # Find cell
        cell = notebook.get_cell(cell_id)
        if not cell:
            raise HTTPException(status_code=404, detail=f"Cell '{cell_id}' not found")

        if cell.cell_type != "code":
            return {
                "success": True,
                "cell_id": cell_id,
                "status": "success",
                "message": "Markdown cells don't need execution",
                "outputs": []
            }

        # Get kernel — use the kernel spec stored in the notebook's metadata
        full_path = manager.get_full_notebook_path(notebook.name)
        kernel = await KernelRegistry.get_kernel(
            full_path, workspace_path, kernel_name=notebook.kernel_name
        )

        # Clear previous outputs and set running
        cell.clear_outputs()
        cell.status = "running"

        # Execute and collect outputs
        outputs = []
        has_error = False

        async for output in kernel.execute(cell.source, timeout=60):
            cell.outputs.append(output)
            outputs.append(output.to_dict())
            if output.output_type == "error":
                has_error = True

        # Update cell status
        cell.status = "error" if has_error else "success"
        cell.execution_count = kernel.execution_count

        # Save notebook
        manager.save_notebook(notebook)

        return {
            "success": not has_error,
            "cell_id": cell_id,
            "status": cell.status,
            "execution_count": cell.execution_count,
            "outputs": outputs
        }

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Notebook '{notebook_name}' not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute cell: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute cell: {str(e)}")


@router.post("/{task_id}/notebooks/{notebook_name}/execute-all")
async def execute_all_cells(
    task_id: str,
    notebook_name: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Execute all code cells in order, top to bottom.

    This re-establishes kernel state by running every code cell sequentially.
    Useful after a backend restart or kernel timeout.

    Returns a summary with per-cell results.
    """
    from pathlib import Path
    from backend.agents.notebook.manager import NotebookManager
    from backend.agents.notebook.kernel import KernelRegistry

    task = session.exec(select(Task).where(Task.id == task_id, Task.user_id == current_user.id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Build workspace path
    try:
        if task.display_id:
            workspace_path = str(WorkspaceManager.get_task_path(current_user.id, f"task_{task.display_id}"))
        else:
            workspace_path = task.workspace_path
    except Exception as e:
        logger.error(f"Failed to resolve workspace path: {e}")
        workspace_path = task.workspace_path

    try:
        manager = NotebookManager(workspace_path, str(task.display_id or task.id))
        notebook = manager.load_notebook(notebook_name)

        # Get kernel — use the kernel spec stored in the notebook's metadata
        full_path = manager.get_full_notebook_path(notebook.name)
        kernel = await KernelRegistry.get_kernel(
            full_path, workspace_path, kernel_name=notebook.kernel_name
        )

        # Execute all code cells in order
        results = []
        total_errors = 0

        for cell in notebook.cells:
            cid = cell.id if hasattr(cell, 'id') else cell.get('id', '')
            c_type = cell.cell_type if hasattr(cell, 'cell_type') else cell.get('cell_type', 'code')

            if c_type != "code":
                continue

            source = cell.source if hasattr(cell, 'source') else cell.get('source', '')
            if not source.strip():
                continue

            # Clear previous outputs
            if hasattr(cell, 'clear_outputs'):
                cell.clear_outputs()
            elif hasattr(cell, 'outputs'):
                cell.outputs = []
            if hasattr(cell, 'status'):
                cell.status = "running"

            # Execute
            outputs = []
            has_error = False
            try:
                async for output in kernel.execute(source, timeout=60):
                    if hasattr(cell, 'outputs'):
                        cell.outputs.append(output)
                    outputs.append(output.to_dict() if hasattr(output, 'to_dict') else output)
                    out_type = output.output_type if hasattr(output, 'output_type') else output.get('output_type', '')
                    if out_type == "error":
                        has_error = True
            except Exception as exec_err:
                has_error = True
                outputs.append({"output_type": "error", "ename": "ExecutionError", "evalue": str(exec_err), "traceback": []})

            # Update cell status
            status = "error" if has_error else "success"
            if hasattr(cell, 'status'):
                cell.status = status
            if hasattr(cell, 'execution_count'):
                cell.execution_count = kernel.execution_count

            if has_error:
                total_errors += 1

            results.append({
                "cell_id": cid,
                "status": status,
                "execution_count": kernel.execution_count if hasattr(kernel, 'execution_count') else None,
                "outputs": outputs,
            })

        # Save notebook
        manager.save_notebook(notebook)

        return {
            "success": total_errors == 0,
            "cells_executed": len(results),
            "errors": total_errors,
            "results": results,
        }

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Notebook '{notebook_name}' not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute all cells: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute all cells: {str(e)}")


# =========================================
# MEMORY ENDPOINTS (Phase 2B)
# =========================================

class MemorySettingsUpdate(BaseModel):
    max_context_tokens: Optional[int] = None


@router.get("/{task_id}/memory")
def get_task_memory(
    task_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get memory vault stats for a task."""
    from pathlib import Path
    from backend.agents.orchestrator.memory import TaskMemoryVault

    task = session.exec(select(Task).where(Task.id == task_id, Task.user_id == current_user.id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    try:
        vault = TaskMemoryVault(
            task_id=task.id,
            user_id=current_user.id,
            workspace_path=Path(task.workspace_path),
        ).load()

        return vault.get_stats()
    except Exception as e:
        logger.warning(f"Failed to load memory vault: {e}")
        return {
            "session_count": 0,
            "total_tokens": 0,
            "max_tokens": 8000,
            "usage_percent": 0,
            "sessions": []
        }


@router.delete("/{task_id}/memory/sessions/{session_id}")
def delete_memory_session(
    task_id: str,
    session_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Remove a specific session from the memory vault."""
    from pathlib import Path
    from backend.agents.orchestrator.memory import TaskMemoryVault

    task = session.exec(select(Task).where(Task.id == task_id, Task.user_id == current_user.id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    try:
        vault = TaskMemoryVault(
            task_id=task.id,
            user_id=current_user.id,
            workspace_path=Path(task.workspace_path),
        ).load()

        success = vault.remove_session(session_id)
        if success:
            logger.info(f"Removed memory session {session_id} from task {task_id}")
            return {"ok": True, "removed": session_id}
        else:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove memory session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove session: {str(e)}")


@router.patch("/{task_id}/memory/settings")
def update_memory_settings(
    task_id: str,
    settings_in: MemorySettingsUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update memory vault settings (e.g., max context tokens)."""
    from pathlib import Path
    from backend.agents.orchestrator.memory import TaskMemoryVault
    import json

    task = session.exec(select(Task).where(Task.id == task_id, Task.user_id == current_user.id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    try:
        vault = TaskMemoryVault(
            task_id=task.id,
            user_id=current_user.id,
            workspace_path=Path(task.workspace_path),
        ).load()

        updated = {}
        if settings_in.max_context_tokens is not None:
            vault.max_context_tokens = settings_in.max_context_tokens
            updated["max_context_tokens"] = settings_in.max_context_tokens

        # Save updated metadata
        vault._save_metadata()
        vault._update_summary()

        logger.info(f"Updated memory settings for task {task_id}: {updated}")
        return {"ok": True, "updated": updated, "stats": vault.get_stats()}
    except Exception as e:
        logger.error(f"Failed to update memory settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")

@router.post("/{task_id}/collaborate")
async def respond_to_collaboration(
    task_id: str,
    response: CollaborationResponse,  # Assuming user sends a matching JSON
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Respond to a collaboration request (e.g., plan approval, question answer).
    This resumes the paused agent task.
    """
    from backend.agents.task_manager import task_manager
    
    # Verify task ownership
    task = session.exec(select(Task).where(Task.id == task_id, Task.user_id == current_user.id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    # Ensure tool_name and task_id match
    if response.task_id != task_id:
        response.task_id = task_id
        
    # Inject response
    success = task_manager.set_collaboration_response(task_id, response)
    
    if not success:
        # If no active task or task not waiting, maybe it finished or timed out?
        # But maybe we just queued it?
        # For now, return 400 if we couldn't deliver
        raise HTTPException(status_code=400, detail="Failed to deliver response. Task may be completed or not running.")
        
    return {"status": "accepted", "detail": "Response delivered to agent."}


@router.post("/{task_id}/stop")
async def stop_task(
    task_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Stop a running task. This cancels the backend execution.
    """
    from backend.agents.task_manager import task_manager

    # Verify task ownership
    task = session.exec(select(Task).where(Task.id == task_id, Task.user_id == current_user.id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Cancel the task
    success = task_manager.cancel_task(task_id)

    if success:
        logger.info(f"Task {task_id} stopped by user {current_user.id}")
        return {"status": "cancelled", "detail": "Task stopped successfully."}
    else:
        # Task may already be finished or not running
        return {"status": "not_running", "detail": "Task was not running or already completed."}


# =========================================
# KERNEL CONTROL ENDPOINTS
# =========================================

@router.post("/{task_id}/notebooks/{notebook_name}/kernel/stop")
async def stop_kernel(
    task_id: str,
    notebook_name: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Stop (interrupt) the kernel for a specific notebook.

    This sends an interrupt signal, stopping any running cell without
    destroying the kernel state (variables are preserved).
    """
    from backend.agents.notebook.manager import NotebookManager
    from backend.agents.notebook.kernel import KernelRegistry

    task = session.exec(select(Task).where(Task.id == task_id, Task.user_id == current_user.id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    try:
        if task.display_id:
            workspace_path = str(WorkspaceManager.get_task_path(current_user.id, f"task_{task.display_id}"))
        else:
            workspace_path = task.workspace_path
    except Exception as e:
        workspace_path = task.workspace_path

    try:
        manager = NotebookManager(workspace_path, str(task.display_id or task.id))
        full_path = manager.get_full_notebook_path(notebook_name.replace(".ipynb", ""))
        kernel = KernelRegistry._kernels.get(full_path)
        if kernel and kernel.is_alive():
            await kernel.interrupt()
            return {"status": "interrupted", "notebook": notebook_name}
        return {"status": "not_running", "detail": "No active kernel for this notebook"}
    except Exception as e:
        logger.error(f"Failed to stop kernel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/notebooks/{notebook_name}/kernel/restart")
async def restart_kernel(
    task_id: str,
    notebook_name: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Restart the kernel for a notebook, clearing all variables and state.
    """
    from backend.agents.notebook.manager import NotebookManager
    from backend.agents.notebook.kernel import KernelRegistry

    task = session.exec(select(Task).where(Task.id == task_id, Task.user_id == current_user.id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    try:
        if task.display_id:
            workspace_path = str(WorkspaceManager.get_task_path(current_user.id, f"task_{task.display_id}"))
        else:
            workspace_path = task.workspace_path
    except Exception as e:
        workspace_path = task.workspace_path

    try:
        manager = NotebookManager(workspace_path, str(task.display_id or task.id))
        full_path = manager.get_full_notebook_path(notebook_name.replace(".ipynb", ""))
        # Stop existing kernel and remove from registry — next execute will auto-start a fresh one
        await KernelRegistry.stop_kernel(full_path)
        logger.info(f"Kernel restarted for {notebook_name} (task {task_id})")
        return {"status": "restarted", "notebook": notebook_name}
    except Exception as e:
        logger.error(f"Failed to restart kernel: {e}")
        raise HTTPException(status_code=500, detail=str(e))
