import pytest
import asyncio
import json
import logging
from unittest.mock import MagicMock, AsyncMock, patch
from backend.agents.orchestrator.engine import orchestrated_chat, OrchestratorState
from backend.agents.session_context import SessionContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock data
MOCK_USER_QUERY = "Test query"
MOCK_TASK_ID = "test-task-123"
MOCK_MODEL = "ollama::llama3.2:latest"

@pytest.fixture
def mock_session_context():
    ctx = MagicMock(spec=SessionContext)
    ctx.task_id = MOCK_TASK_ID
    ctx.agent_roles = {
        "_resolved_role": "lead_researcher",
        "lead_researcher": MOCK_MODEL,
        "default": MOCK_MODEL
    }
    ctx.workspace_path = "/tmp/test_workspace"
    return ctx

@pytest.fixture
def mock_model_router():
    router = MagicMock()
    
    # Mock chat_stream to simulate thinking streaming
    async def async_gen(*args, **kwargs):
        # Simulate thinking chunks
        thinking_chunks = ["Hmm", ", ", "I ", "need ", "to ", "think ", "about ", "this."]
        for chunk in thinking_chunks:
            yield json.dumps({
                "message": {"thinking": chunk}
            })
            await asyncio.sleep(0.001) # Small delay to simulate network/processing
            
        # Simulate content chunks
        yield json.dumps({
            "message": {"content": '{"decision": "needs_plan", "steps": [{"step_id": "step_1", "description": "test", "agent_role": "default", "tool_name": "test_tool", "tool_args": {}}]}'}
        })
        
        # Simulate usage
        yield json.dumps({
            "done": True,
            "eval_count": 10,
            "prompt_eval_count": 5
        })

    # IMPORTANT: chat_stream must be a MagicMock that returns the async generator 
    # when called, NOT an AsyncMock (which would return a coroutine).
    router.chat_stream = MagicMock(side_effect=async_gen)
    return router

@pytest.mark.asyncio
async def test_streaming_granularity(mock_model_router, mock_session_context):
    """
    Verify that thinking is streamed in multiple small chunks, not one big block.
    """
    messages = [{"role": "user", "content": MOCK_USER_QUERY}]
    events = []
    
    # Mocking sse_client to return an async context manager that yields a mock transport
    mock_transport = (MagicMock(), MagicMock())
    
    mock_sse_cm = MagicMock()
    mock_sse_cm.__aenter__ = AsyncMock(return_value=mock_transport)
    mock_sse_cm.__aexit__ = AsyncMock(return_value=None)
    
    mock_sse_client = MagicMock(return_value=mock_sse_cm)

    # Mocking ClientSession
    mock_session = AsyncMock()
    mock_session.initialize = AsyncMock()
    mock_session.list_tools = AsyncMock(return_value=MagicMock(tools=[]))
    
    mock_session_cm = MagicMock()
    mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_cm.__aexit__ = AsyncMock(return_value=None)
    
    with patch("backend.agents.orchestrator.engine.sse_client", mock_sse_client), \
         patch("backend.agents.orchestrator.engine.ClientSession", return_value=mock_session_cm):
        
        async for event in orchestrated_chat(
            model_router=mock_model_router,
            model_identifier=MOCK_MODEL,
            messages=messages,
            session_context=mock_session_context,
            think=True 
        ):
            if event["type"] == "orchestrator_thinking":
                events.append(event)
            elif event.get("type") == "error":
                pytest.fail(f"Orchestrator error: {event['message']}")

    # Verification: We expect multiple thinking events
    thinking_count = len(events)
    logger.info(f"Received {thinking_count} thinking events")
    
    # If blocking, we might get 0 or 1 big chunk designated as "thinking" (if logic allows) 
    # or none if it's swallowed until the end.
    # The current engine implementation likely swallows them in `analyze_query` and yields nothing 
    # until the function returns, or yields them all at once if the accumulation happens there.
    # But wait, `analyze_query` DOES yield to a callback. 
    # The issue described is "blocking". 
    # If `analyze_query` is awaited, the `orchestrated_chat` loop is blocked at that line.
    
    # Assert we got significant granularity
    assert thinking_count >= 5, f"Expected > 5 thinking chunks, got {thinking_count}. Streaming might be blocked."

@pytest.mark.asyncio
async def test_event_ordering_direct_answer(mock_model_router, mock_session_context):
    """
    Verify the strict order of events for a direct answer flow.
    """
    # Mock analyzer to return direct answer
    async def mock_analyzer_stream(*args, **kwargs):
        yield json.dumps({"message": {"thinking": "Analyzing..."}})
        yield json.dumps({"message": {"content": '{"decision": "direct_answer", "reasoning": "Simple"}'}})
        
    mock_model_router.chat_stream = mock_analyzer_stream

    messages = [{"role": "user", "content": MOCK_USER_QUERY}]
    event_types = []

    # Mocking sse_client to return an async context manager that yields a mock transport
    mock_transport = (MagicMock(), MagicMock())
    
    mock_sse_cm = MagicMock()
    mock_sse_cm.__aenter__ = AsyncMock(return_value=mock_transport)
    mock_sse_cm.__aexit__ = AsyncMock(return_value=None)
    
    mock_sse_client = MagicMock(return_value=mock_sse_cm)

    # Mocking ClientSession
    mock_session = AsyncMock()
    mock_session.initialize = AsyncMock()
    mock_session.list_tools = AsyncMock(return_value=MagicMock(tools=[]))
    
    mock_session_cm = MagicMock()
    mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_cm.__aexit__ = AsyncMock(return_value=None)
    
    with patch("backend.agents.orchestrator.engine.sse_client", mock_sse_client), \
         patch("backend.agents.orchestrator.engine.ClientSession", return_value=mock_session_cm):
        
        async for event in orchestrated_chat(
            model_router=mock_model_router,
            model_identifier=MOCK_MODEL,
            messages=messages,
            session_context=mock_session_context,
            think=True
        ):
            event_types.append(event["type"])

    # Expected Sequence
    # session_info -> status(Analyzing) -> orchestrator_thinking_start(analyzing) -> orchestrator_thinking -> direct_answer_mode 
    
    logger.info(f"Event sequence: {event_types}")
    
    assert "session_info" in event_types
    assert "orchestrator_thinking_start" in event_types
    
    # Analyze phase check
    try:
        start_idx = event_types.index("orchestrator_thinking_start")
        mode_idx = event_types.index("direct_answer_mode")
        assert start_idx < mode_idx, "Thinking start must precede direct answer mode"
    except ValueError as e:
        pytest.fail(f"Missing expected event: {e}")

if __name__ == "__main__":
    # Allow running directly
    pytest.main([__file__, "-v"])
