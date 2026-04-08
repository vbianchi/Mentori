import pytest
import asyncio
from typing import Dict
from unittest.mock import AsyncMock, patch, MagicMock

from backend.retrieval.agents.transcriber import AgentFactory, DeepSeekTranscriber
from backend.retrieval.validation import HybridValidator

@pytest.mark.asyncio
async def test_agent_factory_creates_transcriber():
    """Test that factory creates agent when model is available."""
    config = {"transcriber": "ollama::deepseek-ocr:3b"}
    
    with patch("backend.retrieval.agents.transcriber.DeepSeekTranscriber.check_availability", new_callable=AsyncMock) as mock_check:
        mock_check.return_value = True
        
        agent = await AgentFactory.get_transcriber(config)
        assert agent is not None
        assert isinstance(agent, DeepSeekTranscriber)
        assert agent.model_name == "deepseek-ocr:3b"

@pytest.mark.asyncio
async def test_agent_factory_returns_none_if_missing():
    """Test that factory returns None when model check fails."""
    config = {"transcriber": "ollama::ghost-model"}
    
    with patch("backend.retrieval.agents.transcriber.DeepSeekTranscriber.check_availability", new_callable=AsyncMock) as mock_check:
        mock_check.return_value = False
        
        agent = await AgentFactory.get_transcriber(config)
        assert agent is None

def test_hybrid_validator_high_similarity():
    """Test that validator returns VLM text when similarity is high."""
    validator = HybridValidator()
    vlm_text = "The quick brown fox jumps over the dog."
    ocr_text = "The quick brown fox jumps over the dog" # almost identical
    
    result = validator.validate(vlm_text, ocr_text)
    assert result == vlm_text
    assert "Appendix" not in result

def test_hybrid_validator_merges_missing_text():
    """Test that validator merges OCR text if VLM missed a lot."""
    validator = HybridValidator()
    vlm_text = "Figure 1: A fox."
    # OCR saw the whole paragraph that VLM ignored
    ocr_text = "Figure 1: A fox. " + "This is a very long paragraph describing the fox in detail that the vision model decided to skip for some reason. " * 5
    
    result = validator.validate(vlm_text, ocr_text)
    
    assert "Grounding Alert" in result
    assert "OCR Appendix" in result
    assert "This is a very long paragraph" in result
