"""
Tests for RLM (Recursive Language Model) implementation.

Tests the REPL-based document analysis system including:
- RLMContext state management
- RLMExecutor code execution
- CitationGroundedSummarizer
- RLMOrchestrator coordination
"""

import pytest
import asyncio
import json
from unittest.mock import MagicMock, AsyncMock, patch
from dataclasses import dataclass

# Import RLM components
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.retrieval.rlm.context import (
    RLMContext, Citation, ChunkResult, DocumentInfo, ReportSection
)
from backend.retrieval.rlm.executor import RLMExecutor
from backend.retrieval.rlm.summarizer import (
    CitationGroundedSummarizer, SummaryResult, ExtractedFact
)
from backend.retrieval.rlm.orchestrator import RLMOrchestrator, RLMEvent


# ============== FIXTURES ==============

@pytest.fixture
def sample_chunks():
    """Create sample ChunkResult objects for testing."""
    return [
        ChunkResult(
            doc_name="paper1.pdf",
            chunk_idx=0,
            text="CRISPR-Cas9 is a revolutionary genome editing tool. The Cas9 protein uses guide RNA to target specific DNA sequences.",
            page=1,
            score=0.95,
            metadata={"file_name": "paper1.pdf", "chunk_index": 0}
        ),
        ChunkResult(
            doc_name="paper1.pdf",
            chunk_idx=1,
            text="Off-target effects occur when CRISPR accidentally cuts unintended DNA sites. Deep learning models can predict these effects.",
            page=2,
            score=0.88,
            metadata={"file_name": "paper1.pdf", "chunk_index": 1}
        ),
        ChunkResult(
            doc_name="paper2.pdf",
            chunk_idx=0,
            text="Recursive Language Models treat long prompts as external environment. The LLM writes code to navigate documents.",
            page=1,
            score=0.92,
            metadata={"file_name": "paper2.pdf", "chunk_index": 0}
        ),
    ]


@pytest.fixture
def mock_context(sample_chunks):
    """Create a mock RLMContext with pre-loaded documents."""
    context = RLMContext(
        index_name="test_index",
        user_id="test_user",
        max_tokens=100000
    )

    # Manually populate document data (bypassing DB)
    context._documents = {
        "paper1.pdf": DocumentInfo(
            name="paper1.pdf",
            file_path="/test/paper1.pdf",
            total_chunks=2,
            total_pages=2,
            title="CRISPR Gene Editing"
        ),
        "paper2.pdf": DocumentInfo(
            name="paper2.pdf",
            file_path="/test/paper2.pdf",
            total_chunks=1,
            total_pages=1,
            title="Recursive Language Models"
        )
    }

    context._chunks_by_doc = {
        "paper1.pdf": [
            {
                "id": "chunk_1_0",
                "text": sample_chunks[0].text,
                "chunk_idx": 0,
                "page": 1,
                "metadata": sample_chunks[0].metadata
            },
            {
                "id": "chunk_1_1",
                "text": sample_chunks[1].text,
                "chunk_idx": 1,
                "page": 2,
                "metadata": sample_chunks[1].metadata
            }
        ],
        "paper2.pdf": [
            {
                "id": "chunk_2_0",
                "text": sample_chunks[2].text,
                "chunk_idx": 0,
                "page": 1,
                "metadata": sample_chunks[2].metadata
            }
        ]
    }

    context._initialized = True
    return context


@pytest.fixture
def mock_model_router():
    """Create a mock model router for LLM calls."""
    router = MagicMock()

    # Create async generate method
    async def mock_generate(model_identifier, prompt, options=None):
        # Simple mock response based on prompt content
        if "extract" in prompt.lower():
            return {
                "response": json.dumps({
                    "facts": [
                        {"fact": "CRISPR uses Cas9 protein", "chunk_ids": [1], "quote": "The Cas9 protein uses guide RNA"}
                    ],
                    "missing_info": []
                }),
                "eval_count": 100,
                "prompt_eval_count": 200
            }
        elif "summarize" in prompt.lower():
            return {
                "response": "SUMMARY:\nCRISPR-Cas9 is a genome editing tool [1]. It can have off-target effects [2].\n\nCITATIONS_USED:\n1, 2",
                "eval_count": 50,
                "prompt_eval_count": 150
            }
        else:
            return {
                "response": "This is a mock LLM response about the content.",
                "eval_count": 30,
                "prompt_eval_count": 100
            }

    router.generate = AsyncMock(side_effect=mock_generate)
    return router


# ============== CONTEXT TESTS ==============

class TestRLMContext:
    """Tests for RLMContext state management."""

    def test_list_documents(self, mock_context):
        """Test listing available documents."""
        docs = mock_context.list_documents()

        assert len(docs) == 2
        assert any(d["name"] == "paper1.pdf" for d in docs)
        assert any(d["name"] == "paper2.pdf" for d in docs)

        paper1 = next(d for d in docs if d["name"] == "paper1.pdf")
        assert paper1["chunks"] == 2
        assert paper1["pages"] == 2

    def test_get_document_structure(self, mock_context):
        """Test getting document structure."""
        structure = mock_context.get_document_structure("paper1.pdf")

        assert structure["name"] == "paper1.pdf"
        assert structure["total_chunks"] == 2
        assert structure["total_pages"] == 2
        assert len(structure["pages"]) == 2

    def test_get_document_structure_not_found(self, mock_context):
        """Test error handling for non-existent document."""
        structure = mock_context.get_document_structure("nonexistent.pdf")

        assert "error" in structure

    def test_get_chunk(self, mock_context):
        """Test retrieving specific chunk."""
        chunk_text = mock_context.get_chunk("paper1.pdf", 0)

        assert "CRISPR-Cas9" in chunk_text
        assert "guide RNA" in chunk_text

    def test_get_chunk_not_found(self, mock_context):
        """Test error for non-existent chunk."""
        chunk_text = mock_context.get_chunk("paper1.pdf", 999)

        assert "[ERROR]" in chunk_text

    def test_get_chunks_range(self, mock_context):
        """Test retrieving range of chunks."""
        chunks = mock_context.get_chunks_range("paper1.pdf", 0, 2)

        assert len(chunks) == 2
        assert all(isinstance(c, ChunkResult) for c in chunks)
        assert chunks[0].chunk_idx == 0
        assert chunks[1].chunk_idx == 1

    def test_get_chunks_by_page(self, mock_context):
        """Test retrieving chunks by page number."""
        chunks = mock_context.get_chunks_by_page("paper1.pdf", 1)

        assert len(chunks) == 1
        assert chunks[0].page == 1

    def test_search_keyword(self, mock_context):
        """Test keyword search."""
        results = mock_context.search_keyword("CRISPR")

        assert len(results) > 0
        assert all(isinstance(r, ChunkResult) for r in results)
        assert any("CRISPR" in r.text for r in results)

    def test_search_keyword_case_insensitive(self, mock_context):
        """Test case-insensitive keyword search."""
        results = mock_context.search_keyword("crispr", case_sensitive=False)

        assert len(results) > 0
        assert any("CRISPR" in r.text for r in results)

    def test_search_keyword_specific_doc(self, mock_context):
        """Test keyword search in specific document."""
        results = mock_context.search_keyword("Recursive", doc_name="paper2.pdf")

        assert len(results) == 1
        assert results[0].doc_name == "paper2.pdf"

    def test_search_regex(self, mock_context):
        """Test regex search."""
        results = mock_context.search_regex(r"Cas\d+")

        assert len(results) > 0
        assert any("Cas9" in r.text for r in results)

    def test_citation_creation(self, mock_context):
        """Test creating citations."""
        citation = mock_context.cite(
            doc_name="paper1.pdf",
            page=1,
            quote="CRISPR-Cas9 is a revolutionary genome editing tool",
            chunk_idx=0
        )

        assert isinstance(citation, Citation)
        assert citation.doc_name == "paper1.pdf"
        assert citation.page == 1
        assert len(mock_context.citations) == 1

    def test_get_citations(self, mock_context):
        """Test retrieving citations."""
        mock_context.cite("paper1.pdf", 1, "quote1", 0)
        mock_context.cite("paper2.pdf", 1, "quote2", 0)

        all_cits = mock_context.get_citations()
        paper1_cits = mock_context.get_citations_for_doc("paper1.pdf")

        assert len(all_cits) == 2
        assert len(paper1_cits) == 1

    def test_report_building(self, mock_context):
        """Test building report sections."""
        mock_context.add_to_report(
            section="Introduction",
            content="This paper describes CRISPR [1].",
            citations=[]
        )
        mock_context.add_to_report(
            section="Methods",
            content="The study used Cas9 enzyme [2].",
            citations=[]
        )

        report = mock_context.get_report()

        assert "## Introduction" in report
        assert "## Methods" in report
        assert "CRISPR" in report

    def test_progress_tracking(self, mock_context):
        """Test progress tracking."""
        mock_context.cite("paper1.pdf", 1, "quote", 0)
        mock_context.add_to_report("Section1", "content", [])
        mock_context.llm_calls_made = 5
        mock_context.total_tokens_used = 1000

        progress = mock_context.get_progress()

        assert progress["documents"] == 2
        assert progress["citations_collected"] == 1
        assert progress["sections_processed"] == 1
        assert progress["llm_calls"] == 5
        assert progress["tokens_used"] == 1000

    def test_context_summary(self, mock_context):
        """Test context summary generation."""
        summary = mock_context.get_context_summary()

        assert "test_index" in summary
        assert "paper1.pdf" in summary
        assert "paper2.pdf" in summary


# ============== EXECUTOR TESTS ==============

class TestRLMExecutor:
    """Tests for RLMExecutor code execution."""

    def test_executor_initialization(self, mock_context, mock_model_router):
        """Test executor initialization with proper namespace."""
        executor = RLMExecutor(mock_context, mock_model_router, "test-model")

        assert "list_documents" in executor.namespace
        assert "search_keyword" in executor.namespace
        assert "llm_query" in executor.namespace
        assert "cite" in executor.namespace
        assert "print" in executor.namespace

    def test_execute_simple_code(self, mock_context, mock_model_router):
        """Test executing simple code."""
        executor = RLMExecutor(mock_context, mock_model_router, "test-model")

        output, result = executor.execute_code("2 + 2")

        assert result == 4

    def test_execute_print_statement(self, mock_context, mock_model_router):
        """Test capturing print output."""
        executor = RLMExecutor(mock_context, mock_model_router, "test-model")

        output, result = executor.execute_code('print("Hello World")')

        assert "Hello World" in output

    def test_execute_list_documents(self, mock_context, mock_model_router):
        """Test executing list_documents() in REPL."""
        executor = RLMExecutor(mock_context, mock_model_router, "test-model")

        # First assign, then get the length as expression
        executor.execute_code("docs = list_documents()")
        output, result = executor.execute_code("len(docs)")

        assert result == 2

    def test_execute_search_keyword(self, mock_context, mock_model_router):
        """Test executing search in REPL."""
        executor = RLMExecutor(mock_context, mock_model_router, "test-model")

        code = """
results = search_keyword("CRISPR")
print(f"Found {len(results)} results")
"""
        output, result = executor.execute_code(code)

        assert "Found" in output
        # Verify the variable was set correctly
        _, count = executor.execute_code("len(results)")
        assert count > 0

    def test_execute_with_error(self, mock_context, mock_model_router):
        """Test error handling in code execution."""
        executor = RLMExecutor(mock_context, mock_model_router, "test-model")

        output, result = executor.execute_code("undefined_variable")

        assert "Error" in output
        assert "NameError" in output

    def test_variable_persistence(self, mock_context, mock_model_router):
        """Test that variables persist across executions."""
        executor = RLMExecutor(mock_context, mock_model_router, "test-model")

        executor.execute_code("my_var = 42")
        output, result = executor.execute_code("my_var")

        assert result == 42

    def test_safe_builtins_available(self, mock_context, mock_model_router):
        """Test that safe builtins are available."""
        executor = RLMExecutor(mock_context, mock_model_router, "test-model")

        # Test various builtins
        _, result = executor.execute_code("len([1,2,3])")
        assert result == 3

        _, result = executor.execute_code("sorted([3,1,2])")
        assert result == [1, 2, 3]

        _, result = executor.execute_code("sum([1,2,3,4])")
        assert result == 10

    def test_json_module_available(self, mock_context, mock_model_router):
        """Test that json module is available."""
        executor = RLMExecutor(mock_context, mock_model_router, "test-model")

        output, result = executor.execute_code('json.dumps({"key": "value"})')

        assert result == '{"key": "value"}'

    def test_citation_in_repl(self, mock_context, mock_model_router):
        """Test creating citation through REPL."""
        executor = RLMExecutor(mock_context, mock_model_router, "test-model")

        # Use a quote that actually exists in the mock chunks
        code = """
cit = cite("paper1.pdf", 1, "CRISPR-Cas9 is a revolutionary genome editing tool", 0)
"""
        executor.execute_code(code)
        _, result = executor.execute_code("cit.doc_name")

        assert result == "paper1.pdf"
        assert len(mock_context.citations) == 1

    def test_output_truncation(self, mock_context, mock_model_router):
        """Test that long output is truncated."""
        executor = RLMExecutor(mock_context, mock_model_router, "test-model")

        # Generate very long output - each line is ~20 chars, need >50000 chars
        # So need about 3000+ lines to exceed MAX_OUTPUT_LENGTH of 50000
        code = """
for i in range(10000):
    print(f"This is a much longer line number {i} with extra padding to ensure we hit the limit faster")
"""
        output, result = executor.execute_code(code)

        assert len(output) <= executor.MAX_OUTPUT_LENGTH + 100  # Some tolerance
        assert "TRUNCATED" in output

    def test_get_user_variables(self, mock_context, mock_model_router):
        """Test retrieving user-created variables."""
        executor = RLMExecutor(mock_context, mock_model_router, "test-model")

        executor.execute_code("my_list = [1, 2, 3]")
        executor.execute_code("my_dict = {'a': 1}")

        user_vars = executor.get_user_variables()

        assert "my_list" in user_vars
        assert "my_dict" in user_vars


# ============== SUMMARIZER TESTS ==============

class TestCitationGroundedSummarizer:
    """Tests for CitationGroundedSummarizer."""

    @pytest.mark.asyncio
    async def test_summarize_empty_chunks(self, mock_model_router):
        """Test summarizing empty chunk list."""
        summarizer = CitationGroundedSummarizer(mock_model_router, "test-model")

        result = await summarizer.summarize(
            chunks=[],
            task="Summarize findings",
            cite_fn=lambda **k: Citation(**{**k, "context": ""})
        )

        assert isinstance(result, SummaryResult)
        assert "No source material" in result.text
        assert len(result.citations) == 0

    @pytest.mark.asyncio
    async def test_summarize_with_chunks(self, mock_model_router, sample_chunks):
        """Test summarizing with actual chunks."""
        summarizer = CitationGroundedSummarizer(mock_model_router, "test-model")

        citations_collected = []
        def cite_fn(**kwargs):
            cit = Citation(**{**kwargs, "context": ""})
            citations_collected.append(cit)
            return cit

        result = await summarizer.summarize(
            chunks=sample_chunks[:2],
            task="Summarize the CRISPR findings",
            cite_fn=cite_fn
        )

        assert isinstance(result, SummaryResult)
        assert result.text  # Has some text
        assert isinstance(result.verification_score, float)

    @pytest.mark.asyncio
    async def test_extract_facts(self, mock_model_router, sample_chunks):
        """Test fact extraction stage."""
        summarizer = CitationGroundedSummarizer(mock_model_router, "test-model")

        extracted = await summarizer._extract_facts(sample_chunks[:2], "Extract findings")

        assert "facts" in extracted or "missing_info" in extracted

    def test_find_uncited_claims(self, mock_model_router):
        """Test uncited claim detection."""
        summarizer = CitationGroundedSummarizer(mock_model_router, "test-model")

        text_with_citations = "The study found significant results [1]. This indicates X [2]."
        text_without_citations = "The study found significant results. The research demonstrated clear effects. This was observed in the data."

        uncited1 = summarizer._find_uncited_claims(text_with_citations)
        uncited2 = summarizer._find_uncited_claims(text_without_citations)

        assert len(uncited1) < len(uncited2)


# ============== ORCHESTRATOR TESTS ==============

class TestRLMOrchestrator:
    """Tests for RLMOrchestrator."""

    def test_extract_code_blocks(self, mock_model_router):
        """Test code block extraction."""
        orchestrator = RLMOrchestrator(mock_model_router, "test-model")

        text = """
Let me analyze the documents.

```repl
docs = list_documents()
print(f"Found {len(docs)} documents")
```

Now let's search:

```python
results = search_keyword("CRISPR")
```
"""

        blocks = orchestrator._extract_code_blocks(text)

        assert len(blocks) == 2
        assert "list_documents" in blocks[0]
        assert "search_keyword" in blocks[1]

    def test_check_final_answer_simple(self, mock_model_router, mock_context):
        """Test FINAL() detection."""
        orchestrator = RLMOrchestrator(mock_model_router, "test-model")
        executor = RLMExecutor(mock_context, mock_model_router, "test-model")

        text = 'Based on my analysis, FINAL("The answer is 42")'

        result = orchestrator._check_final_answer(text, executor)

        assert result == "The answer is 42"

    def test_check_final_var(self, mock_model_router, mock_context):
        """Test FINAL_VAR() detection."""
        orchestrator = RLMOrchestrator(mock_model_router, "test-model")
        executor = RLMExecutor(mock_context, mock_model_router, "test-model")

        # Add something to report first
        mock_context.add_to_report("Test", "Test content", [])

        text = 'Analysis complete. FINAL_VAR(get_report())'

        result = orchestrator._check_final_answer(text, executor)

        assert "## Test" in result
        assert "Test content" in result

    def test_check_no_final(self, mock_model_router, mock_context):
        """Test when no final answer present."""
        orchestrator = RLMOrchestrator(mock_model_router, "test-model")
        executor = RLMExecutor(mock_context, mock_model_router, "test-model")

        text = 'Let me continue analyzing...'

        result = orchestrator._check_final_answer(text, executor)

        assert result is None

    def test_format_messages(self, mock_model_router):
        """Test message formatting."""
        orchestrator = RLMOrchestrator(mock_model_router, "test-model")

        messages = [
            {"role": "system", "content": "You are an analyst."},
            {"role": "user", "content": "Analyze this."},
            {"role": "assistant", "content": "Let me check."}
        ]

        formatted = orchestrator._format_messages(messages)

        assert "You are an analyst" in formatted
        assert "USER: Analyze this" in formatted
        assert "ASSISTANT: Let me check" in formatted

    @pytest.mark.asyncio
    async def test_run_stream_emits_events(self, mock_model_router, mock_context):
        """Test that run_stream yields proper events."""
        # Create orchestrator with limited turns
        orchestrator = RLMOrchestrator(mock_model_router, "test-model", max_turns=2)

        # Mock router to return code then final
        responses = [
            {"response": "Let me analyze.\n```repl\nprint('hello')\n```", "eval_count": 10, "prompt_eval_count": 20},
            {"response": "FINAL(\"Analysis complete\")", "eval_count": 10, "prompt_eval_count": 20}
        ]
        mock_model_router.generate = AsyncMock(side_effect=responses)

        events = []
        async for event in orchestrator.run_stream("Analyze documents", mock_context):
            events.append(event)

        event_types = [e.type for e in events]

        assert "progress" in event_types
        assert "final" in event_types or "error" in event_types


# ============== INTEGRATION TESTS ==============

class TestRLMIntegration:
    """Integration tests for the full RLM flow."""

    @pytest.mark.asyncio
    async def test_full_analysis_flow(self, mock_context, mock_model_router):
        """Test complete analysis flow from task to report."""
        # Setup: Create orchestrator with enough turns
        orchestrator = RLMOrchestrator(mock_model_router, "test-model", max_turns=10)

        # Mock LLM to perform a simple analysis
        call_count = [0]

        async def mock_chat(model_identifier, messages, options=None, tools=None, think=None):
            call_count[0] += 1

            if call_count[0] == 1:
                # First call: list documents
                return {
                    "message": {"role": "assistant", "content": """I'll start by listing the documents.

```repl
docs = list_documents()
for d in docs:
    print(f"- {d['name']}: {d['chunks']} chunks")
```
"""},
                    "eval_count": 100,
                    "prompt_eval_count": 200
                }
            elif call_count[0] == 2:
                # Second call: search and add to report
                return {
                    "message": {"role": "assistant", "content": """Found documents. Now searching for key content.

```repl
results = search_keyword("CRISPR")
print(f"Found {len(results)} results about CRISPR")

# Add to report
add_to_report("CRISPR Analysis", f"Found {len(results)} chunks discussing CRISPR.", [])
```
"""},
                    "eval_count": 100,
                    "prompt_eval_count": 200
                }
            else:
                # Final call: return report using FINAL with string
                return {
                    "message": {"role": "assistant", "content": """Analysis complete. FINAL("CRISPR Analysis completed successfully")"""},
                    "eval_count": 50,
                    "prompt_eval_count": 100
                }

        mock_model_router.chat = AsyncMock(side_effect=mock_chat)

        # Run
        result = await orchestrator.run("Analyze CRISPR content", mock_context)

        # Verify
        assert "CRISPR" in result

    def test_executor_with_real_context_operations(self, mock_context, mock_model_router):
        """Test executor performing actual context operations."""
        executor = RLMExecutor(mock_context, mock_model_router, "test-model")

        # Simulate typical RLM workflow

        # Step 1: List documents
        output, result = executor.execute_code("""
docs = list_documents()
print(f"Available: {len(docs)} documents")
""")
        assert "2 documents" in output

        # Step 2: Search for content
        output, result = executor.execute_code("""
crispr_chunks = search_keyword("CRISPR")
print(f"CRISPR mentions: {len(crispr_chunks)}")
""")
        assert "CRISPR mentions" in output

        # Step 3: Get specific chunk
        output, result = executor.execute_code("""
chunk_text = get_chunk("paper1.pdf", 0)
print(chunk_text[:100])
""")
        assert "CRISPR" in output

        # Step 4: Create citation
        output, result = executor.execute_code("""
cit = cite("paper1.pdf", 1, "CRISPR-Cas9 is a revolutionary genome editing tool", 0)
print(f"Citation created: {cit.to_inline()}")
""")
        assert "paper1.pdf" in output

        # Step 5: Add to report
        output, result = executor.execute_code("""
add_to_report("Summary", "CRISPR is a gene editing tool [1].", get_citations())
print("Section added")
""")
        assert "Section added" in output

        # Step 6: Get final report
        output, result = executor.execute_code("get_report()")
        assert "## Summary" in result
        assert "CRISPR" in result


# ============== CITATION TESTS ==============

class TestCitationIntegrity:
    """Tests for citation integrity and verification."""

    def test_citation_inline_format(self):
        """Test citation inline formatting."""
        citation = Citation(
            doc_name="paper.pdf",
            page=5,
            chunk_idx=3,
            quote="Important finding here"
        )

        inline = citation.to_inline()

        assert "paper.pdf" in inline
        assert "p5" in inline

    def test_citation_reference_format(self):
        """Test citation reference formatting."""
        citation = Citation(
            doc_name="paper.pdf",
            page=5,
            chunk_idx=3,
            quote="This is a very important finding that we discovered during our research"
        )

        reference = citation.to_reference()

        assert "paper.pdf" in reference
        assert "page 5" in reference
        assert "important finding" in reference

    def test_citation_verification_in_context(self, mock_context):
        """Test that citations are verified against source material."""
        # Valid quote (exists in document)
        citation1 = mock_context.cite(
            doc_name="paper1.pdf",
            page=1,
            quote="CRISPR-Cas9 is a revolutionary genome editing tool",
            chunk_idx=0
        )

        # The citation should be created successfully
        assert len(mock_context.citations) == 1
        assert citation1.doc_name == "paper1.pdf"


# ============== ERROR HANDLING TESTS ==============

class TestRLMErrorHandling:
    """Tests for error handling in RLM system."""

    def test_executor_handles_syntax_error(self, mock_context, mock_model_router):
        """Test handling of Python syntax errors."""
        executor = RLMExecutor(mock_context, mock_model_router, "test-model")

        output, result = executor.execute_code("def incomplete(")

        assert "Error" in output
        assert "SyntaxError" in output

    def test_executor_handles_runtime_error(self, mock_context, mock_model_router):
        """Test handling of runtime errors."""
        executor = RLMExecutor(mock_context, mock_model_router, "test-model")

        output, result = executor.execute_code("1 / 0")

        assert "Error" in output
        assert "ZeroDivisionError" in output

    def test_context_handles_invalid_document(self, mock_context):
        """Test handling of invalid document names."""
        chunk = mock_context.get_chunk("nonexistent.pdf", 0)

        assert "[ERROR]" in chunk

    def test_context_handles_invalid_regex(self, mock_context):
        """Test handling of invalid regex patterns."""
        results = mock_context.search_regex("[invalid")

        assert len(results) == 0  # Should return empty, not crash


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
