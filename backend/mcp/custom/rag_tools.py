"""
RAG Tools for Mentori Agent
Exposes document retrieval capabilities as MCP tools.

This is the agent-facing layer that wraps the backend/retrieval/ infrastructure.
"""

from backend.mcp.decorator import mentori_tool
from backend.agents.session_context import get_logger
from backend.retrieval.response_cache import response_cache
from backend.mcp.progress import emit_progress
from backend.agents.token_utils import safe_char_budget
from typing import Optional, Union
import json
import os

logger = get_logger(__name__)







@mentori_tool(
    category="RAG",
    agent_role="editor",
    is_llm_based=False
)
def list_document_indexes(user_id: str) -> str:
    """
    List all available Document Indexes (Collections).

    Args:
        user_id: [Auto-injected] Current user ID

    Returns:
        JSON list of indexes with status (READY, PROCESSING, etc.)
    """
    logger.info(f"Listing document indexes for user")

    try:
        from backend.retrieval.models import UserCollection
        from backend.database import engine
        from sqlmodel import Session, select

        with Session(engine) as session:
            indexes = session.exec(
                select(UserCollection)
                .where(UserCollection.user_id == user_id)
                .order_by(UserCollection.created_at.desc())
            ).all()

            output = []
            for idx in indexes:
                # Parse metrics for richer status
                metrics = idx.metrics
                processed = metrics.get("processed_files", 0)
                total_files = metrics.get("total_files", len(idx.file_paths))
                
                status_display = idx.status.value
                if idx.status.value == "PROCESSING":
                    # Show progress: "PROCESSING (3/10)"
                    status_display = f"PROCESSING ({processed}/{total_files})"
                
                elif idx.status.value == "FAILED":
                     # Show "FAILED (0/5)"
                     status_display = f"FAILED ({processed}/{total_files})"
                
                # Extract top errors if any
                file_errors = metrics.get("file_errors", [])
                top_errors = [f"{e['file']}: {e['error']}" for e in file_errors[:3]]
                if len(file_errors) > 3:
                     top_errors.append(f"...and {len(file_errors)-3} more.")

                output.append({
                    "id": idx.id,
                    "name": idx.name,
                    "description": idx.description,
                    "status": status_display,
                    "files": len(idx.file_paths),
                    "file_names": [fp.split("/")[-1] for fp in idx.file_paths],  # Just filenames for readability
                    "chunks": metrics.get("total_chunks", 0),
                    "ocr_tool": idx.ocr_tool,
                    "transcriber_model": idx.transcriber_model,
                    "error_message": idx.error_message if idx.status.value == "FAILED" else None,
                    "errors": top_errors if top_errors else None,
                    "created_at": idx.created_at.isoformat()
                })

        logger.info(f"Found {len(indexes)} indexes")
        return json.dumps(output, indent=2)
    except Exception as e:
        logger.error(f"Failed to list indexes: {str(e)}")
        return f"[Error] Failed to list indexes: {str(e)}"


@mentori_tool(
    category="RAG",
    agent_role="editor",
    is_llm_based=False
)
async def query_documents(
    query: str,
    max_results: int = 5,
    index_name: Optional[str] = None,
    retrieval_mode: str = "single_pass",
    task_id: str = None,
    user_id: str = None
) -> str:
    """
    Search for information in documents.

    Args:
        query: Question or search query
        max_results: Number of relevant passages (default: 5)
        index_name: Optional. Name of a specific User Index to search (e.g., "Biology Research").
                    If not provided, searches the current task's ad-hoc index.
        retrieval_mode: Strategy hint for this query:
            - "single_pass": Fast lookup for simple factual questions. Use for direct
              lookups where one or two passages will suffice. (default)
            - "verified": Important claims requiring broader evidence. Automatically
              retrieves more passages (3× max_results) for stronger grounding.
            - "deep": Comprehensive multi-document analysis. Use deep_research_rlm
              instead for this — query_documents will redirect with a suggestion.
        task_id: [Auto-injected]
        user_id: [Auto-injected]

    Returns:
        Formatted results with retrieved passages and citations.
    """
    # Apply retrieval_mode adjustments
    if retrieval_mode == "verified":
        max_results = max(max_results, 15)  # Wider net for important claims
    elif retrieval_mode == "deep":
        return (
            "[Retrieval] deep mode selected. For comprehensive multi-document analysis "
            "use the deep_research_rlm tool instead — it performs recursive, "
            "citation-grounded coverage that query_documents cannot match."
        )

    logger.info(f"Querying documents: query='{query[:50]}...', index='{index_name}', max_results={max_results}, mode={retrieval_mode}")

    try:
        from backend.retrieval.retriever import SimpleRetriever
        from backend.retrieval.models import UserCollection, IndexStatus
        from backend.database import engine
        from sqlmodel import Session, select

        # Determine target collection(s)
        collection_names = []

        if index_name:
            # Look up the persistent user collection
            logger.info(f"Looking up index '{index_name}' for user")
            with Session(engine) as session:
                idx = session.exec(
                    select(UserCollection)
                    .where(UserCollection.user_id == user_id, UserCollection.name == index_name)
                    .where(UserCollection.status == IndexStatus.READY)
                ).first()

                if idx and idx.vector_db_collection_name:
                    collection_names.append(idx.vector_db_collection_name)
                    logger.info(f"Found index, using collection: {idx.vector_db_collection_name}")
                else:
                    logger.warning(f"Index '{index_name}' not found or not ready")
                    return f"[Warning] Index '{index_name}' not found or not ready."
        else:
            # Default to task-specific ad-hoc collection
            target = f"task_{task_id}"
            collection_names.append(target)
            logger.info(f"No index specified, using task collection: {target}")

        # Retrieve from all targets (merged)
        # For Phase 1.5, we'll just pick the first one or default.
        # Ideally SimpleRetriever support multi-collection or we loop.

        target_collection = collection_names[0]

        # Check cache first (using empty doc_ids for pre-retrieval cache)
        # This caches by query + collection, useful for repeated identical queries
        cache_key_docs = [target_collection]  # Use collection as pseudo-doc-id for cache key
        cached_response = response_cache.get(query, target_collection, cache_key_docs)
        if cached_response:
            logger.info(f"Cache hit for query in '{target_collection}'")
            return cached_response

        # Look up the collection's embedding model so retriever uses the same model
        embedding_model = None
        use_reranker = False # Disable by default for small corpora
        if index_name:
            try:
                with Session(engine) as session:
                    idx = session.exec(
                        select(UserCollection)
                        .where(UserCollection.user_id == user_id, UserCollection.name == index_name)
                    ).first()
                    if idx and idx.embedding_model:
                        embedding_model = idx.embedding_model
                    
                    # Estimate if corpus > 20 papers (assuming ~40 chunks per paper = 800 chunks)
                    from backend.retrieval.vector_store import VectorStore
                    vs = VectorStore(collection_name=target_collection)
                    chunk_count = vs.count(target_collection)
                    if chunk_count > 800:
                        use_reranker = True
                        logger.info(f"Large corpus detected ({chunk_count} chunks). Enabling reranker.")
            except Exception as e:
                logger.warning(f"Error checking corpus size for reranker: {e}")

        retriever = SimpleRetriever(embedding_model=embedding_model, use_reranker=use_reranker)
        results = retriever.retrieve(
            query=query,
            collection_name=target_collection,
            top_k=max_results
        )

        if not results:
            logger.info(f"No results found in collection '{target_collection}'")
            return f"No relevant information found for '{query}' in '{target_collection}'."

        logger.info(f"Retrieved {len(results)} results from '{target_collection}'")
        formatted_output = [f"Found {len(results)} relevant passages in '{index_name or 'Task Documents'}':\n"]

        for i, res in enumerate(results, 1):
            meta = res.get("metadata", {})
            # Fix: Handle multiple possible metadata key names
            source = meta.get("source") or meta.get("file_path") or meta.get("file_name") or "Unknown"
            page = meta.get("page") or meta.get("page_num") or "?"

            # Extract just filename for readability
            if source != "Unknown" and "/" in source:
                source = os.path.basename(source)

            citation_info = f" [Cites: {meta.get('citation_count', 0)} refs]" if "citation_count" in meta else ""

            formatted_output.append(
                f"[{i}] \"{res['text']}\"\n"
                f"    Source: {source} (Page {page}){citation_info}"
            )

        # Cache the formatted response for future identical queries
        final_response = "\n".join(formatted_output)
        response_cache.set(query, target_collection, cache_key_docs, final_response)

        return final_response

    except ImportError:
        logger.error("RAG backend not fully linked")
        return "[Error] RAG backend not fully linked yet."
    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        return f"[Error] Query failed: {str(e)}"


@mentori_tool(
    category="RAG",
    agent_role="editor",
    is_llm_based=False
)
def extract_citations(text: str, task_id: str) -> str:
    """
    Extract and validate citations from text.

    Args:
        text: Text containing citation references (e.g., "(Smith, 2020)")
        task_id: [Auto-injected] Current task ID

    Returns:
        JSON-formatted string of extracted citations.
    """
    try:
        from backend.retrieval.parsers.citations import CitationExtractor
        extractor = CitationExtractor()
        
        citations = extractor.extract_citations(text)
        dois = extractor.extract_dois(text)
        
        output = {
            "citation_count": len(citations),
            "citations": citations,
            "dois": dois
        }
        
        return json.dumps(output, indent=2)

    except Exception as e:
        return f"[Error] Extraction failed: {str(e)}"


@mentori_tool(
    category="RAG",
    agent_role="editor",
    is_llm_based=False
)
def inspect_document_index(index_name: str, user_id: str) -> str:
    """
    List ALL documents contained in a specific index.
    
    Use this to see what knowledge is available before searching, or to find 
    names/IDs of documents to read directly.

    Args:
        index_name: Name of the index to inspect
        user_id: [Auto-injected]

    Returns:
        JSON list of documents with IDs, filenames, and metadata summaries.
    """
    logger.info(f"Inspecting index '{index_name}' for user")
    
    try:
        from backend.retrieval.models import UserCollection, IndexStatus
        from backend.database import engine
        from backend.retrieval.vector_store import VectorStore
        from sqlmodel import Session, select
        
        # 1. Resolve Index Name to Collection ID
        with Session(engine) as session:
            idx = session.exec(
                select(UserCollection)
                .where(UserCollection.user_id == user_id, UserCollection.name == index_name)
            ).first()
            
            if not idx:
                return f"[Error] Index '{index_name}' not found."
            
            if idx.status != IndexStatus.READY:
                return f"[Warning] Index '{index_name}' is not READY (Status: {idx.status})."
                
            collection_name = idx.vector_db_collection_name
            if not collection_name:
                 return f"[Error] Index '{index_name}' has no linked vector collection."

        # 2. Query Vector DB for unique documents
        # We fetch all metadatas to aggregate unique files
        store = VectorStore(collection_name=collection_name)
        
        # This can be heavy for huge indexes, but fine for MVP sizes
        all_data = store.get_collection(collection_name).get(include=["metadatas"])
        metadatas = all_data.get("metadatas", [])
        
        # Aggregate by source/filename
        unique_docs = {}
        for meta in metadatas:
            src = meta.get("file_path") or meta.get("source") or "unknown"
            if src not in unique_docs:
                unique_docs[src] = {
                    "file_path": src,
                    "file_name": meta.get("file_name", os.path.basename(src)),
                    "chunks": 0,
                    "example_id": None, # ID of one chunk to use as reference
                    "title": meta.get("title"),
                    "author": meta.get("author")
                }
            unique_docs[src]["chunks"] += 1
            
        # Format output
        output = []
        for doc in unique_docs.values():
            output.append({
                "file_name": doc["file_name"],
                "path": doc["file_path"],
                "total_chunks": doc["chunks"],
                "metadata": {
                    "title": doc["title"],
                    "author": doc["author"]
                }
            })
            
        return json.dumps(output, indent=2)

    except Exception as e:
        logger.error(f"Failed to inspect index: {e}")
        return f"[Error] Inspection failed: {str(e)}"


@mentori_tool(
    category="RAG",
    agent_role="editor",  # Note: uses vision agent if use_vision=True
    is_llm_based=False    # Default is fast (deterministic), vision path is LLM-based
)
async def read_document(
    file_path: str,
    start_page: int = 1,
    end_page: int = None,
    mode: str = "fast",
    user_id: str = None,
    task_id: str = None
) -> str:
    """
    Read content from a document (PDF, TXT, MD) within your workspace.
    
    Modes:
    - 'fast': Extracts text directly (best for most documents).
    - 'vision': Uses OCR/Vision (best for scanned PDFs or charts).
    
    Args:
        file_path: Path to the file (e.g. 'files/paper.pdf')
        start_page: Page number to start reading from (1-based)
        end_page: Page number to stop reading (optional)
        mode: 'fast' or 'vision'
    """
    logger.info(f"Checking request: read_document(file_path='{file_path}', user_id='{user_id}', task_id='{task_id}')")
    
    try:
        if not user_id:
            return "[Error] System Error: user_id not injected locally."

        # resolve path
        from pathlib import Path
        from backend.config import settings
        
        user_root = (Path(settings.WORKSPACE_DIR) / str(user_id)).resolve()
        input_path = Path(file_path)
        
        path = None
        
        # 1. Check direct/user path
        if input_path.is_absolute():
            resolved_path = input_path.resolve()
        else:
            resolved_path = (user_root / input_path).resolve()
            
        logger.info(f"[READ_DEBUG] Checking User Root: {resolved_path}")
        if resolved_path.exists() and str(resolved_path).startswith(str(user_root)):
            path = str(resolved_path)
        else:
             # Fallback: Check Task Workspace
             # If exact match failed, files might be in the task-specific folder
             if task_id:
                 from backend.models.task import Task
                 from backend.database import engine
                 from sqlmodel import Session, select
                 
                 with Session(engine) as session:
                     task = session.exec(select(Task).where(Task.id == task_id)).first()
                     if task and task.workspace_path:
                         task_root = Path(task.workspace_path).resolve()
                         task_resolved = (task_root / input_path).resolve()
                         
                         # DEBUG LOGGING
                         logger.info(f"[READ_DEBUG] Fallback Check:")
                         logger.info(f"  Task ID: {task_id}")
                         logger.info(f"  Task Workspace Path (DB): {task.workspace_path}")
                         logger.info(f"  Task Root (Resolved): {task_root}")
                         logger.info(f"  Input Path: {input_path}")
                         logger.info(f"  Task Resolved Path: {task_resolved}")
                         logger.info(f"  Exists? {task_resolved.exists()}")
                         logger.info(f"  In Root? {str(task_resolved).startswith(str(task_root))}")

                         if task_resolved.exists() and str(task_resolved).startswith(str(task_root)):
                             path = str(task_resolved)
                             logger.info(f"Found file in Task workspace: {path}")

             if not path:
                 logger.error(f"[READ_DEBUG] File finally not found. Checked: {resolved_path} and task locations.")
                 return f"[Error] File not found: {resolved_path}"

            
        # -- VISION PATH --
        if mode == "vision":
            logger.info("Engaging Vision Agent for document reading")
            from backend.retrieval.agents.transcriber import AgentFactory
            from backend.models.user import User
            from backend.database import engine
            from sqlmodel import Session
            
            # Get user settings to configure agent
            transcriber = None
            with Session(engine) as session:
                user = session.get(User, user_id)
                if user and user.settings:
                    agent_roles = user.settings.get("agent_roles", {})
                    transcriber = await AgentFactory.get_transcriber(agent_roles)
            
            if not transcriber:
                return "[Error] Vision Agent not configured. Please enable 'Transcriber' in settings."

            # Use Ingestor's logic but just for reading
            # We don't want to store, just return text.
            # But the transcriber works page-by-page.

            from pdf2image import convert_from_path
            import tempfile

            full_text = []

            # Reset token counters before processing
            if hasattr(transcriber, 'reset_token_usage'):
                transcriber.reset_token_usage()

            with tempfile.TemporaryDirectory() as temp_dir:
                # Limit to first 5 pages for responsiveness in chat
                images = convert_from_path(path, dpi=300, last_page=5)

                for i, image in enumerate(images):
                    page_path = os.path.join(temp_dir, f"page_{i}.png")
                    image.save(page_path, "PNG")

                    # VLM Transcribe
                    # Note: We skip the HybridValidator loop here for speed,
                    # just trusting the VLM's "eyes"
                    text = await transcriber.transcribe_page(page_path)
                    full_text.append(f"--- Page {i+1} (Vision) ---\n{text}\n")

                if len(images) == 5:
                    full_text.append("\n[...Stopped after 5 pages for speed...]")

            result = "\n".join(full_text)

            # Append token usage marker for chat_loop to track (LLM-based tool)
            if hasattr(transcriber, 'get_token_usage'):
                tokens = transcriber.get_token_usage()
                if tokens.get("total", 0) > 0:
                    result += f"\n<!--TOOL_TOKEN_USAGE:{{\"input\":{tokens['input']},\"output\":{tokens['output']},\"total\":{tokens['total']}}}-->"
                    logger.info(f"[READ_DOCUMENT] Vision path token usage: {tokens}")

            return result

        # -- FAST PATH (Standard Parsers) --
        else:
            from backend.retrieval.parsers.pdf import PDFParser
            
            if path.lower().endswith(".pdf"):
                parser = PDFParser(extract_citations=True)
                result = parser.parse(path)
                
                # Format a nice report
                meta = result.get("metadata", {})
                authors = meta.get("author") or "Unknown"
                title = meta.get("title") or "Unknown"
                
                header = (
                    f"Document: {os.path.basename(path)}\n"
                    f"Title: {title}\n"
                    f"Authors: {authors}\n"
                    f"Pages: {result['num_pages']}\n"
                    f"{'-'*40}\n"
                )
                
                # Truncate if too long (chatbot context limit)
                # 50,000 chars is roughly 10-15k tokens. Safe for most large context models.
                text_content = result["text"]
                if len(text_content) > 50000:
                    text_content = text_content[:50000] + "\n\n[...Truncated due to length...]"
                    
                return header + text_content
            
            else:
                # Fallback for text files
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()

    except Exception as e:
        logger.error(f"Read document failed: {e}")
        return f"[Error] Failed to read document: {str(e)}"


@mentori_tool(
    category="RAG",
    agent_role="handyman",
    is_llm_based=True
)
async def deep_research(
    topic: str,
    user_id: str,
    task_id: str,
    max_depth: int = 3,
    index_name: str = None
) -> str:
    """
    Perform a "Deep Research" on a topic using the Handyman Agent.
    
    Instead of a single search, this tool:
    1. PLANS a search strategy (breaking topic into sub-questions).
    2. EXECUTES searches for each sub-question.
    3. VERIFIES results to filter out low-quality hits (e.g. just bibliography).
    4. SYNTHESIZES a detailed, grounded report.
    
    Use this for complex topics where a simple query returns poor results.
    
    Args:
        topic: The research topic or question.
        user_id: [Auto-injected]
        task_id: [Auto-injected]
        max_depth: limit sub-queries (default 3)
        index_name: Optional. Name of the index to search.
        
    Returns:
        A markdown report grounded in the retrieved documents.
    """
    logger.info(f"Starting Deep Research on: '{topic}' (Index: {index_name})")
    
    try:
        from backend.agents.model_router import ModelRouter
        from backend.models.user import User
        from backend.database import engine
        from sqlmodel import Session
        
        # 1. Identify Handyman Model
        model_identifier = "ollama::llama3.2:latest" # Default fallback
        
        with Session(engine) as session:
            user = session.get(User, user_id)
            if user and user.settings and "agent_roles" in user.settings:
                # Prefer Handyman, then Default
                roles = user.settings["agent_roles"]
                model_identifier = roles.get("handyman") or roles.get("default") or model_identifier
                
        logger.info(f"Using Handyman Model: {model_identifier}")
        
        router = ModelRouter()
        
        # 2. PLAN: Generate Sub-Queries
        plan_prompt = (
            f"You are a Research Planner. The user wants to know about: '{topic}'.\\n"
            f"Generate {max_depth} specific search queries to gather comprehensive facts.\\n"
            f"Avoid generic queries. Focus on definitions, findings, and limitations.\\n"
            f"Output ONLY the queries, one per line."
        )
        
        plan_response = await router.generate(
            model_identifier=model_identifier, 
            prompt=plan_prompt,
            options={"temperature": 0.3}
        )
        
        queries = [line.strip().replace("- ", "").replace("* ", "") 
                  for line in plan_response.get("response", "").split("\\n") 
                  if line.strip()]
        
        queries = queries[:max_depth]
        logger.info(f"Research Plan: {queries}")
        
        # 3. EXECUTE & VERIFY Loop
        verified_facts = []
        
        for q in queries:
            logger.info(f"Researching sub-query: {q}")
            
            # Call query_documents directly (re-using logic)
            # Note: query_documents expects injected args, so we pass them
            # We use a higher max_results (15) to ensure we get body text even if
            # the top results are clogged with bibliography citations.
            raw_results = await query_documents(
                query=q, 
                max_results=15, 
                user_id=user_id, 
                task_id=task_id,
                index_name=index_name
            )
            
            # Check for empty/error
            if "[Error]" in raw_results or "No relevant information" in raw_results:
                continue
                
            # Verify: Is this just bibliography?
            verify_prompt = (
                f"Analyze these search results for the query '{q}':\\n\\n"
                f"{raw_results[:2000]}\\n\\n" # Truncate to save context
                f"Task: Extract actual FACTS and CONTENT.\\n"
                f"WARNING: Ignore lines that are just bibliography references (starting with [1], containing URLs, DOIs, etc).\\n"
                f"If the text is ONLY bibliography/titles with no body content, reply 'NO_CONTENT'.\\n"
                f"Otherwise, summarize the key findings found in the text."
            )
            
            verify_response = await router.generate(
                model_identifier=model_identifier,
                prompt=verify_prompt,
                options={"temperature": 0.1}
            )
            
            content = verify_response.get("response", "").strip()
            
            if "NO_CONTENT" in content:
                logger.warning(f"Query '{q}' returned only bibliography/noise. Discarding.")
            else:
                verified_facts.append(f"### Findings for '{q}':\\n{content}")
                
        if not verified_facts:
            return "Deep Research failed to find grounded content. The documents might not contain body text for this topic."
            
        # 4. SYNTHESIZE
        logger.info("Synthesizing final report...")
        all_facts = "\\n\\n".join(verified_facts)
        
        synthesis_prompt = (
            f"You are a Senior Researcher. Write a detailed report on '{topic}' based ONLY on the following verified facts:\\n\\n"
            f"{all_facts}\\n\\n"
            f"Structure:\\n"
            f"1. Executive Summary\\n"
            f"2. Integrated Findings (use tables if appropriate)\\n"
            f"3. Conclusion\\n"
            f"IMPORTANT: Do not hallucinate. If facts are missing, state that."
        )
        
        final_response = await router.generate(
            model_identifier=model_identifier,
            prompt=synthesis_prompt,
            options={"temperature": 0.3}
        )
        
        report = final_response.get("response", "")
        
        return report

    except Exception as e:
        logger.error(f"Deep Research failed: {e}")
        return f"[Error] Deep Research failed: {str(e)}"


@mentori_tool(
    category="RAG",
    agent_role="coder",  # Uses coder role - generates Python code in REPL blocks
    is_llm_based=True
)
async def deep_research_rlm(
    task: str,
    index_name: Optional[str] = None,
    file_path: Optional[str] = None,
    user_id: Optional[str] = None,
    task_id: Optional[str] = None,
    workspace_path: Optional[str] = None,
    max_turns: int = 10,
    token_budget: int = 500000,
    verify: bool = False
) -> str:
    """
    Perform deep research using true Recursive Language Model (RLM) approach.

    Unlike simple RAG, this tool:
    - Treats documents as an EXTERNAL ENVIRONMENT the LLM interacts with via code
    - Uses PROGRAMMATIC filtering (regex, keywords) BEFORE sending to LLM
    - Makes RECURSIVE sub-LLM calls on specific content chunks
    - GUARANTEES citation tracking - every claim is grounded in source material
    - Produces SYSTEMATIC coverage - processes documents/sections in order

    Best for:
    - Long document summarization (chapter by chapter)
    - Multi-paper analysis (strengths, weaknesses, gaps)
    - Any task requiring comprehensive, hallucination-free analysis
    - Reading specific files from the workspace (set file_path)

    Args:
        task: Research task description. Examples:
            - "Summarize each chapter, preserving key findings and tables"
            - "Analyze strengths/weaknesses of each paper, then identify research gaps"
            - "Extract all methods and results across these studies"
        index_name: Name of the document index to analyze (optional if file_path is set)
        file_path: Optional. Specific file to read/analyze. If provided, it will be ingested into a temporary index.
        user_id: [Auto-injected]
        task_id: [Auto-injected]
        workspace_path: [Auto-injected]
        max_turns: Maximum REPL iterations (default: 20)
        token_budget: Maximum tokens to use (default: 500k)
        verify: If True, run a verification pass on the final report.
                Each claim is checked against its cited source. Default off
                (approximately doubles LLM cost).

    Returns:
        Markdown report with:
        - Structured content based on task
        - Inline citations [doc_name:page]
        - Reference list at the end
        - Processing statistics
    """
    logger.info(f"Starting RLM Deep Research on index_name='{index_name}', file_path='{file_path}': {task[:100]}...")

    try:
        from backend.retrieval.rlm import RLMContext, RLMOrchestrator
        from backend.agents.model_router import ModelRouter
        from backend.agents.models.utils import parse_model_identifier
        from backend.agents.session_context import resolve_model_for_chat
        from backend.models.user import User
        from backend.models.task import Task
        from backend.database import engine
        from backend.config import settings
        from sqlmodel import Session, select
        import httpx
        from pathlib import Path
        
        # 0. Ad-hoc Ingestion for file_path
        if file_path or (index_name and ("/" in index_name or "." in index_name)):
            # If index_name looks like a file, treat it as file_path if file_path is empty
            if not file_path and index_name and ("/" in index_name or "." in index_name):
                file_path = index_name
                logger.info(f"Interpreting index_name '{index_name}' as file_path")

            if file_path:
                # Resolve Path (reuse logic from read_document)
                # 1. Resolve User Workspace Root
                user_root = (Path(settings.WORKSPACE_DIR) / str(user_id)).resolve()
                input_path = Path(file_path)
                
                path_to_ingest = None
                
                # Check User Root
                if input_path.is_absolute():
                    resolved_path = input_path.resolve()
                else:
                    resolved_path = (user_root / input_path).resolve()
                    
                if resolved_path.exists() and str(resolved_path).startswith(str(user_root)):
                    path_to_ingest = str(resolved_path)
                else:
                    # Check Task Root
                    if task_id:
                         with Session(engine) as session:
                             task_obj = session.exec(select(Task).where(Task.id == task_id)).first()
                             if task_obj and task_obj.workspace_path:
                                 task_root = Path(task_obj.workspace_path).resolve()
                                 task_resolved = (task_root / input_path).resolve()
                                 
                                 logger.info(f"[RLM_DEBUG] Task ID: {task_id}")
                                 logger.info(f"[RLM_DEBUG] Task Workspace: {task_obj.workspace_path}")
                                 logger.info(f"[RLM_DEBUG] Task Resolved: {task_resolved}")
                                 logger.info(f"[RLM_DEBUG] Exists? {task_resolved.exists()}")
                                 
                                 if task_resolved.exists() and str(task_resolved).startswith(str(task_root)):
                                     path_to_ingest = str(task_resolved)
                                     logger.info(f"Found file in Task workspace: {path_to_ingest}")

                if not path_to_ingest:
                    # If index_name is also provided (and isn't the same file path),
                    # fall back to using the index instead of failing
                    original_index = index_name
                    if original_index and original_index != file_path and "/" not in original_index and "." not in original_index:
                        logger.warning(
                            f"file_path '{file_path}' not found, falling back to index_name '{original_index}'"
                        )
                        file_path = None  # Clear file_path so we skip ingestion
                    else:
                        task_ws = task_obj.workspace_path if task_id and 'task_obj' in dir() and task_obj else 'N/A'
                        check_path = task_resolved if task_id and 'task_resolved' in dir() else 'N/A'
                        return f"[Error] File not found: {file_path}. Debug: TaskID={task_id}, TaskWS={task_ws}, CheckPath={check_path}"

                # Ingest into task-specific collection (only if file was found)
                if path_to_ingest:
                    from backend.retrieval.ingestor import SimpleIngestor
                    from backend.retrieval.models import UserCollection, IndexStatus
                    from backend.database import engine as db_engine
                    from sqlmodel import Session as DBSession

                    target_collection = f"task_{task_id}"
                    logger.info(f"Ingesting '{path_to_ingest}' into ad-hoc collection '{target_collection}'")

                    try:
                        ingestor = SimpleIngestor(collection_name=target_collection)
                        res = await ingestor.ingest_file(path_to_ingest)
                        if res.get("status") == "error":
                            return f"[Error] Failed to ingest file: {res.get('error')}"

                        # Create a UserCollection record so from_index() can find it
                        with DBSession(db_engine) as db_session:
                            existing = db_session.get(UserCollection, target_collection)
                            if not existing:
                                import uuid
                                adhoc_record = UserCollection(
                                    id=target_collection,
                                    user_id=user_id,
                                    name=target_collection,
                                    description=f"Ad-hoc RLM collection for {os.path.basename(str(path_to_ingest))}",
                                    status=IndexStatus.READY,
                                    vector_db_collection_name=target_collection,
                                    file_paths_json=json.dumps([str(path_to_ingest)]),
                                )
                                db_session.add(adhoc_record)
                                db_session.commit()
                                logger.info(f"Created UserCollection record for ad-hoc index '{target_collection}'")

                        # Switch index_name to target
                        index_name = target_collection

                    except Exception as e:
                         logger.error(f"Ad-hoc ingestion failed: {e}")
                         return f"[Error] Failed to prepare file for research: {e}"

        if not index_name:
             return "[Error] Please provide 'index_name' (e.g. 'papers') or 'file_path'."

        # 1. Determine model to use - prefer coder for RLM (code generation)
        # NOTE: RLM requires a model that properly follows instructions to use ```repl blocks.
        # Models like qwen3-coder work well. Models like gpt-oss may output raw code that
        # triggers Ollama's tool call parser, causing failures.
        model_identifier = None
        resolved_role = None

        with Session(engine) as session:
            user = session.get(User, user_id)
            if user and user.settings and "agent_roles" in user.settings:
                roles = user.settings["agent_roles"]
                # Prefer coder role for RLM - it needs to generate Python code in blocks
                model_identifier, resolved_role = resolve_model_for_chat(roles, preferred_role="coder")
                logger.info(f"RLM resolved model: {model_identifier} (role: {resolved_role})")

        if not model_identifier:
            return "[Error] No model configured. Please set up a 'coder' or 'default' agent role in Settings.\n\nRLM works best with code-focused models like qwen3-coder."

        logger.info(f"RLM using model: {model_identifier}")

        # 1b. Health check for Ollama - use centralized parsing and ModelRouter
        router = ModelRouter()
        parsed = parse_model_identifier(model_identifier)

        if parsed.provider == "ollama":
            try:
                is_available, available_models = await router.check_model_available(model_identifier)

                if not is_available:
                    return (
                        f"[Error] Model '{parsed.model_name}' not found in Ollama.\n"
                        f"Available models: {', '.join(available_models[:5])}\n\n"
                        f"Please update your 'coder' agent role in Settings to use an available model.\n"
                        f"Recommended: qwen3-coder:30b or qwen3-coder:latest"
                    )

                # Warm-up test: Try a simple chat to catch model loading issues
                # We disable thinking mode for RLM (the REPL loop IS the reasoning)
                logger.info(f"RLM warmup test for model: {model_identifier}")
                try:
                    warmup_response = await router.chat(
                        model_identifier=model_identifier,
                        messages=[{"role": "user", "content": "Say 'ready' in one word."}],
                        options={"num_predict": 10},
                        think=False  # RLM uses REPL loop for reasoning, not model thinking
                    )
                    warmup_content = warmup_response.get("message", {}).get("content", "")
                    logger.info(f"RLM warmup successful: {warmup_content[:50]}")
                except Exception as warmup_err:
                    error_msg = str(warmup_err)
                    # Check for common issues
                    if "think" in error_msg.lower():
                        return (
                            f"[Error] Model '{parsed.model_name}' does not support the 'think' parameter.\n"
                            f"Your model is configured as '{model_identifier}' which requests thinking mode.\n\n"
                            f"Either:\n"
                            f"1. Remove the [think:...] suffix from your lead_researcher agent role, or\n"
                            f"2. Use a model that supports thinking (e.g., qwen3, deepseek-r1)"
                        )
                    else:
                        return (
                            f"[Error] Model '{parsed.model_name}' failed warmup test.\n"
                            f"Error: {error_msg}\n\n"
                            f"This usually means the model is not loaded or has memory issues."
                        )

            except httpx.ConnectError:
                return f"[Error] Cannot connect to Ollama at {settings.OLLAMA_BASE_URL}. Is Ollama running?"
            except Exception as e:
                logger.warning(f"Ollama health check failed: {e}")

        # 2. Initialize RLM Context from index
        try:
            context = await RLMContext.from_index(
                index_name=index_name,
                user_id=user_id,
                max_tokens=token_budget
            )
        except ValueError as e:
             # Index not found or not ready
             return f"[Error] Document Index '{index_name}' not accessible: {e}. If using a file, please provide 'file_path'."

        logger.info(f"RLM Context initialized: {len(context._documents)} documents, "
                   f"{sum(d.total_chunks for d in context._documents.values())} chunks")

        # 3. Initialize orchestrator (reuse router from health check)
        orchestrator = RLMOrchestrator(
            model_router=router,
            model_identifier=model_identifier,
            max_turns=max_turns,
            verify=verify,
        )

        # 4. Create output directory for this RLM run (inside user's workspace)
        import uuid
        from datetime import datetime

        run_id = uuid.uuid4().hex[:8]
        output_dir = os.path.join(workspace_path, "outputs", f"rlm_{run_id}")
        os.makedirs(output_dir, exist_ok=True)

        # Save run metadata
        run_metadata = {
            "task": task,
            "index_name": index_name,
            "model": model_identifier,
            "max_turns": max_turns,
            "token_budget": token_budget,
            "started_at": datetime.utcnow().isoformat()
        }
        with open(os.path.join(output_dir, "metadata.json"), "w") as f:
            json.dump(run_metadata, f, indent=2)

        # 5. Run RLM loop (streaming — forward progress events to frontend)
        result = None
        async for event in orchestrator.run_stream(task, context):
            if event.type == "progress":
                turn = event.metadata.get("turn", 0) if event.metadata else 0
                await emit_progress(
                    task_id, "deep_research_rlm",
                    event.content,
                    phase="rlm", step=turn, total_steps=max_turns,
                )
            elif event.type == "final":
                result = event.content
            elif event.type == "error":
                return f"[Error] RLM error: {event.content}"

        if result is None:
            return "[Error] RLM loop ended without producing a result"

        # 6. Save outputs to folder
        stats = context.get_progress()

        # Save final report
        with open(os.path.join(output_dir, "final_report.md"), "w") as f:
            f.write(result)

        # Save citations
        citations_data = [
            {"doc_name": c.doc_name, "page": c.page, "quote": c.quote[:500]}
            for c in context.citations
        ]
        with open(os.path.join(output_dir, "citations.json"), "w") as f:
            json.dump(citations_data, f, indent=2)

        # Update metadata with completion info
        run_metadata["completed_at"] = datetime.utcnow().isoformat()
        run_metadata["statistics"] = stats
        with open(os.path.join(output_dir, "metadata.json"), "w") as f:
            json.dump(run_metadata, f, indent=2)

        # 7. Append statistics to result
        result += f"\n\n---\n**Processing Statistics:**\n"
        result += f"- Documents analyzed: {stats['documents']}\n"
        result += f"- Chunks processed: {stats['total_chunks']}\n"
        result += f"- LLM calls made: {stats['llm_calls']}\n"
        result += f"- Citations collected: {stats['citations_collected']}\n"
        result += f"- Tokens used: {stats['tokens_used']:,}\n"
        result += f"\n📁 **Output saved to:** `{output_dir}/`\n"

        # Append token usage marker for chat_loop
        result += f"\n<!--TOOL_TOKEN_USAGE:{{\"total\":{stats['tokens_used']}}}-->"

        logger.info(f"RLM Deep Research completed: {stats['llm_calls']} LLM calls, "
                   f"{stats['citations_collected']} citations. Output: {output_dir}")

        return result

    except ValueError as e:
        logger.error(f"RLM initialization error: {e}")
        return f"[Error] {str(e)}"
    except Exception as e:
        logger.error(f"RLM Deep Research failed: {e}", exc_info=True)
        return f"[Error] RLM Deep Research failed: {str(e)}"


@mentori_tool(
    category="RAG",
    agent_role="editor",
    is_llm_based=False
)
async def smart_query(
    query: str,
    index_name: str,
    mode: str = "auto",
    user_id: str = None,
    task_id: str = None,
    workspace_path: str = None,
) -> str:
    """
    Intelligently route a query to the best RAG strategy.

    Instead of choosing between query_documents / deep_research_rlm /
    inspect_document_index yourself, call this tool and it will:
    1. Analyse the query to determine its type (metadata, factual, deep, verified).
    2. Check the collection size.
    3. Dispatch to the optimal tool with tuned parameters.

    Args:
        query: Natural-language question about the documents.
        index_name: Name of the document index to search.
        mode: "auto" (recommended), "simple", "deep", or "verified".
        user_id: [Auto-injected]
        task_id: [Auto-injected]
        workspace_path: [Auto-injected]

    Returns:
        The result from whichever tool was chosen, prefixed with the routing
        decision for transparency.
    """
    logger.info(f"smart_query: query='{query[:60]}...', index='{index_name}', mode={mode}")

    try:
        from backend.retrieval.context_engine import ContextEngine, Strategy
        from backend.retrieval.vector_store import VectorStore
        from backend.retrieval.models import UserCollection, IndexStatus
        from backend.database import engine as db_engine
        from sqlmodel import Session, select

        # Determine collection size
        collection_size = 0
        with Session(db_engine) as session:
            idx = session.exec(
                select(UserCollection)
                .where(UserCollection.user_id == user_id, UserCollection.name == index_name)
                .where(UserCollection.status == IndexStatus.READY)
            ).first()
            if idx and idx.vector_db_collection_name:
                try:
                    vs = VectorStore(collection_name=idx.vector_db_collection_name)
                    collection_size = vs.count(idx.vector_db_collection_name)
                except Exception:
                    pass

        # Route
        router = ContextEngine()
        decision = router.route(
            query=query,
            collection_size=collection_size,
            user_preference=mode if mode != "auto" else None,
        )

        logger.info(
            f"smart_query routed to {decision.strategy} ({decision.tool_name}): "
            f"{decision.reasoning}"
        )

        await emit_progress(
            task_id, "smart_query",
            f"Strategy: {decision.strategy} → {decision.tool_name}",
            phase="routing",
        )

        prefix = (
            f"**Strategy**: {decision.strategy} → `{decision.tool_name}`\n"
            f"**Reason**: {decision.reasoning}\n\n"
        )

        # Dispatch
        if decision.strategy == Strategy.METADATA_LOOKUP:
            result = inspect_document_index(index_name=index_name, user_id=user_id)
        elif decision.strategy == Strategy.SIMPLE_RAG:
            result = await query_documents(
                query=query,
                index_name=index_name,
                max_results=decision.suggested_params.get("max_results", 5),
                user_id=user_id,
                task_id=task_id,
            )
        elif decision.strategy == Strategy.CROSS_DOC:
            result = await cross_document_analysis(
                task=query,
                index_name=index_name,
                user_id=user_id,
                task_id=task_id,
                workspace_path=workspace_path,
            )
        elif decision.strategy == Strategy.TRIAGE:
            result = await paper_triage(
                query=query,
                index_name=index_name,
                user_id=user_id,
                task_id=task_id,
            )
        elif decision.strategy == Strategy.CORPUS_ANALYSIS:
            result = await analyze_corpus(
                task=query,
                index_name=index_name,
                user_id=user_id,
                task_id=task_id,
                workspace_path=workspace_path,
            )
        elif decision.strategy in (Strategy.RLM_ANALYSIS, Strategy.TWO_PASS):
            result = await deep_research_rlm(
                task=query,
                index_name=index_name,
                user_id=user_id,
                task_id=task_id,
                workspace_path=workspace_path,
                max_turns=decision.suggested_params.get("max_turns", 15),
                verify=decision.suggested_params.get("verify", False),
            )
        else:
            result = await query_documents(
                query=query,
                index_name=index_name,
                user_id=user_id,
                task_id=task_id,
            )

        return prefix + result

    except Exception as e:
        logger.error(f"smart_query failed: {e}", exc_info=True)
        return f"[Error] smart_query failed: {str(e)}"


# ─── Schema derivation for cross-document analysis ─────────────────────────

def _derive_schema(task: str) -> dict:
    """Derive an extraction schema from the task description using keyword matching."""
    task_lower = task.lower()
    if any(kw in task_lower for kw in ["method", "protocol", "technique", "procedure"]):
        return {"methods": "str", "sample_size": "str", "model_organism": "str", "key_reagents": "str"}
    elif any(kw in task_lower for kw in ["gap", "limitation", "future", "missing"]):
        return {"main_findings": "str", "limitations": "str", "future_work": "str", "open_questions": "str"}
    elif any(kw in task_lower for kw in ["grant", "proposal", "significance", "rationale"]):
        return {"main_findings": "str", "significance": "str", "open_questions": "str", "potential_impact": "str"}
    elif any(kw in task_lower for kw in ["systematic", "review", "table", "comparison"]):
        return {"study_design": "str", "population": "str", "intervention": "str", "outcome": "str", "main_result": "str"}
    else:
        return {"main_topic": "str", "key_findings": "str", "methods_used": "str", "limitations": "str"}


def _filter_documents(docs: list, doc_filter: str, chunks_by_doc: dict) -> list:
    """Filter documents based on a comma-separated list of names or a keyword."""
    if not doc_filter:
        return docs

    parts = [p.strip() for p in doc_filter.split(",")]

    # Check if filter items look like filenames (contain '.')
    if any("." in p for p in parts):
        # Exact filename match
        filter_set = {p.lower() for p in parts}
        return [d for d in docs if d["name"].lower() in filter_set]
    else:
        # Keyword match against document name/title
        keyword = doc_filter.lower()
        return [d for d in docs if keyword in d["name"].lower() or keyword in (d.get("title") or "").lower()]


def _safe_doc_filename(doc_name: str, idx: int, max_len: int = 40) -> str:
    """Convert an arbitrary document name to a safe filesystem filename.

    Strips extension, replaces non-alphanumeric chars with underscores,
    collapses runs, truncates to max_len, and prefixes with a zero-padded index.
    """
    import re as _re
    base = doc_name.rsplit(".", 1)[0] if "." in doc_name else doc_name
    safe = _re.sub(r"[^\w\-]", "_", base)
    safe = _re.sub(r"_+", "_", safe).strip("_")[:max_len]
    return f"paper_{idx:03d}_{safe}"


def _write_json_safe(path: str, data: dict) -> None:
    """Write JSON to path, silently logging any errors (never raises)."""
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to write JSON file {path}: {e}")


def _collect_chunks_for_paper(context, doc_name: str, total_chunks: int, task: str, cap: int = 20) -> list:
    """Collect representative chunks for a single paper.

    Strategy: intro (first 4) + conclusion (last 4) + semantic search on task (top 12),
    deduped by chunk_idx, sorted by position, capped at `cap`.
    Using semantic search instead of keyword search because the task is a free-form
    sentence ("main findings") rather than a domain keyword.
    """
    seen, chunks = set(), []

    # 1. Intro: first 4 chunks (title/abstract/introduction)
    for c in context.get_chunks_range(doc_name, 0, 4):
        if c.chunk_idx not in seen:
            seen.add(c.chunk_idx)
            chunks.append(c)

    # 2. Conclusion: last 4 chunks (discussion/conclusions)
    end_start = max(0, total_chunks - 4)
    for c in context.get_chunks_range(doc_name, end_start, total_chunks):
        if c.chunk_idx not in seen:
            seen.add(c.chunk_idx)
            chunks.append(c)

    # 3. Task-relevant chunks via semantic search (most robust for free-form tasks)
    try:
        for c in context.search_semantic(task, top_k=12, doc_name=doc_name):
            if c.chunk_idx not in seen:
                seen.add(c.chunk_idx)
                chunks.append(c)
    except Exception as e:
        logger.warning(f"Semantic search failed for {doc_name}: {e}")

    return sorted(chunks, key=lambda c: c.chunk_idx)[:cap]


@mentori_tool(
    category="RAG",
    agent_role="editor",
    is_llm_based=True
)
async def cross_document_analysis(
    task: str,
    index_name: str,
    extraction_schema: Optional[Union[str, dict]] = None,
    doc_filter: Optional[str] = None,
    output_format: str = "report",
    user_id: str = None,
    task_id: str = None,
    workspace_path: str = None,
) -> str:
    """
    Analyze ALL documents in an index with guaranteed 100% coverage.

    Unlike search-based tools, this iterates deterministically over every
    document, extracts structured data from each, then synthesizes across all.

    Best for:
    - "Compare methods across ALL papers"
    - "Create a systematic review table"
    - "Identify research gaps across the corpus"
    - "Extract statistical tests from each paper"

    Args:
        task: What to analyze/extract (e.g., "Compare experimental methods")
        index_name: Name of the document index
        extraction_schema: Optional JSON schema for structured extraction.
            Example: '{"methods": "str", "sample_size": "str"}'
            If omitted, a schema is auto-derived from the task.
        doc_filter: Optional filter — comma-separated filenames or a keyword.
            Examples: "paper1.pdf,paper2.pdf" or "crispr"
        output_format: "report" (narrative + table) or "table" (compact table only)
        user_id: [Auto-injected]
        task_id: [Auto-injected]
        workspace_path: [Auto-injected]

    Returns:
        Markdown report with per-document extractions, synthesis, and citations.
    """
    import uuid
    from datetime import datetime

    logger.info(f"Starting cross-document analysis: task='{task[:80]}', index='{index_name}'")

    try:
        from backend.retrieval.rlm import RLMContext
        from backend.agents.model_router import ModelRouter
        from backend.agents.session_context import resolve_model_for_chat
        from backend.models.user import User
        from backend.database import engine
        from sqlmodel import Session

        # ── Resolve model ────────────────────────────────────────────────
        model_identifier = None
        with Session(engine) as session:
            user = session.get(User, user_id)
            if user and user.settings and "agent_roles" in user.settings:
                roles = user.settings["agent_roles"]
                model_identifier, resolved_role = resolve_model_for_chat(roles, preferred_role="editor")
                logger.info(f"Cross-doc using model: {model_identifier} (role: {resolved_role})")

        if not model_identifier:
            return "[Error] No model configured. Please set up an 'editor' or 'default' agent role in Settings."

        router = ModelRouter()

        # ── Initialize context ────────────────────────────────────────────
        try:
            context = await RLMContext.from_index(index_name, user_id)
        except ValueError as e:
            return f"[Error] Index '{index_name}' not accessible: {e}"

        all_docs = context.list_documents()
        if not all_docs:
            return f"[Error] Index '{index_name}' contains no documents."

        # Apply filter
        docs_to_analyze = _filter_documents(all_docs, doc_filter, context._chunks_by_doc)
        if not docs_to_analyze:
            return f"[Error] No documents match filter '{doc_filter}'. Available: {', '.join(d['name'] for d in all_docs[:5])}"

        logger.info(f"Analyzing {len(docs_to_analyze)}/{len(all_docs)} documents")

        # ── Resolve schema ────────────────────────────────────────────────
        if extraction_schema:
            if isinstance(extraction_schema, dict):
                # Already a dict (LLM sent object directly)
                schema = extraction_schema
            else:
                # String - parse as JSON
                try:
                    schema = json.loads(extraction_schema)
                except json.JSONDecodeError:
                    return f"[Error] Invalid extraction_schema JSON: {extraction_schema}"
        else:
            schema = _derive_schema(task)

        schema_fields = list(schema.keys())
        logger.info(f"Extraction schema: {schema_fields}")

        # ── Phase 1: Per-document extraction ──────────────────────────────
        per_doc_results = {}
        total_llm_calls = 0
        num_docs = len(docs_to_analyze)

        await emit_progress(
            task_id, "cross_document_analysis",
            f"Starting analysis of {num_docs} documents",
            phase="extraction", step=0, total_steps=num_docs,
        )

        for doc_idx, doc_info in enumerate(docs_to_analyze):
            doc_name = doc_info["name"]
            total_chunks = doc_info["chunks"]
            logger.info(f"Processing document: {doc_name} ({total_chunks} chunks)")

            await emit_progress(
                task_id, "cross_document_analysis",
                f"Extracting from {doc_name}",
                phase="extraction", step=doc_idx + 1, total_steps=num_docs,
            )

            # Collect representative chunks
            collected_chunks = []
            seen_idx = set()

            # 1. Task-relevant chunks via keyword search
            # Extract key terms from task for searching
            task_words = [w for w in task.lower().split() if len(w) > 3 and w not in
                          {"from", "each", "across", "that", "this", "with", "what", "which",
                           "compare", "extract", "identify", "analyze", "papers", "paper",
                           "documents", "document", "index", "every", "used", "using"}]
            for keyword in task_words[:3]:
                hits = context.search_keyword(keyword, doc_name=doc_name)
                for hit in hits[:3]:
                    if hit.chunk_idx not in seen_idx:
                        seen_idx.add(hit.chunk_idx)
                        collected_chunks.append(hit)

            # 2. Intro chunks (first 3)
            intro = context.get_chunks_range(doc_name, 0, 3)
            for chunk in intro:
                if chunk.chunk_idx not in seen_idx:
                    seen_idx.add(chunk.chunk_idx)
                    collected_chunks.append(chunk)

            # 3. Conclusion chunks (last 3)
            end_start = max(0, total_chunks - 3)
            conclusion = context.get_chunks_range(doc_name, end_start, total_chunks)
            for chunk in conclusion:
                if chunk.chunk_idx not in seen_idx:
                    seen_idx.add(chunk.chunk_idx)
                    collected_chunks.append(chunk)

            # Cap at 15 chunks per document
            collected_chunks = sorted(collected_chunks, key=lambda c: c.chunk_idx)[:15]

            if not collected_chunks:
                logger.warning(f"No chunks found for {doc_name}, skipping")
                per_doc_results[doc_name] = {field: "N/A" for field in schema_fields}
                continue

            # Build extraction prompt
            chunks_text = "\n\n---\n\n".join(
                f"[Chunk {c.chunk_idx}, Page {c.page}]\n{c.text}" for c in collected_chunks
            )

            extraction_prompt = (
                f"You are extracting structured information from a scientific document.\n\n"
                f"## Task\n{task}\n\n"
                f"## Document: {doc_name}\n\n"
                f"## Content\n{chunks_text}\n\n"
                f"## Required Fields\n"
                f"Extract the following fields as a JSON object. "
                f"Use 'N/A' if information is not found.\n\n"
                f"Fields: {json.dumps(schema)}\n\n"
                f"IMPORTANT: Return ONLY a valid JSON object, no markdown fences, no explanation."
            )

            # LLM extraction call
            try:
                response = await router.chat(
                    model_identifier=model_identifier,
                    messages=[{"role": "user", "content": extraction_prompt}],
                    options={"temperature": 0.1, "num_predict": 1024},
                    think=False,
                )
                total_llm_calls += 1

                raw_content = response.get("message", {}).get("content", "")
                # Parse JSON from response (strip markdown fences if present)
                json_str = raw_content.strip()
                if json_str.startswith("```"):
                    json_str = json_str.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

                extracted = json.loads(json_str)
                per_doc_results[doc_name] = extracted

                # Track token usage
                if "prompt_eval_count" in response:
                    context.total_tokens_used += response.get("prompt_eval_count", 0) + response.get("eval_count", 0)
                context.llm_calls_made += 1

            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse extraction for {doc_name}: {e}")
                per_doc_results[doc_name] = {field: "extraction failed" for field in schema_fields}

            # Register citations for chunks used
            for chunk in collected_chunks[:5]:  # Cite top 5 chunks per doc
                context.cite(
                    doc_name=doc_name,
                    page=chunk.page,
                    quote=chunk.text[:200],
                    chunk_idx=chunk.chunk_idx,
                )

        # ── Phase 2: Cross-document synthesis ─────────────────────────────
        logger.info(f"Phase 2: Synthesizing across {len(per_doc_results)} documents")

        await emit_progress(
            task_id, "cross_document_analysis",
            f"Synthesizing across {len(per_doc_results)} documents",
            phase="synthesis",
        )

        synthesis_prompt = (
            f"You are a senior researcher synthesizing findings across multiple documents.\n\n"
            f"## Task\n{task}\n\n"
            f"## Per-Document Extractions\n"
            f"```json\n{json.dumps(per_doc_results, indent=2)}\n```\n\n"
            f"## Instructions\n"
            f"1. Write a synthesis that addresses the task across ALL {len(per_doc_results)} documents.\n"
            f"2. Highlight commonalities, differences, and gaps.\n"
            f"3. Reference documents by name when making specific claims.\n"
            f"4. Be precise and evidence-based — do NOT hallucinate.\n\n"
            f"Write in markdown. Start with a brief overview paragraph, then detailed sections."
        )

        synthesis_response = await router.chat(
            model_identifier=model_identifier,
            messages=[{"role": "user", "content": synthesis_prompt}],
            options={"temperature": 0.2, "num_predict": 4096},
            think=False,
        )
        total_llm_calls += 1
        synthesis_text = synthesis_response.get("message", {}).get("content", "")

        if "prompt_eval_count" in synthesis_response:
            context.total_tokens_used += synthesis_response.get("prompt_eval_count", 0) + synthesis_response.get("eval_count", 0)
        context.llm_calls_made += 1

        # ── Phase 3: Format output ───────────────────────────────────────
        await emit_progress(
            task_id, "cross_document_analysis",
            "Formatting report",
            phase="formatting",
        )

        report_parts = []
        report_parts.append(f"# Cross-Document Analysis: {index_name}\n")
        report_parts.append(f"**Task:** {task}\n")
        report_parts.append(f"**Documents analyzed:** {len(per_doc_results)}/{len(all_docs)}\n")

        # Summary table
        report_parts.append("\n## Summary Table\n")
        # Table header
        header = "| Document | " + " | ".join(schema_fields) + " |"
        separator = "|" + "|".join(["---"] * (len(schema_fields) + 1)) + "|"
        report_parts.append(header)
        report_parts.append(separator)

        for doc_name, extracted in per_doc_results.items():
            short_name = doc_name[:30] + "..." if len(doc_name) > 30 else doc_name
            values = []
            for field in schema_fields:
                val = str(extracted.get(field, "N/A"))
                # Truncate long values for table
                val = val[:60] + "..." if len(val) > 60 else val
                # Escape pipe characters
                val = val.replace("|", "\\|")
                values.append(val)
            report_parts.append(f"| {short_name} | " + " | ".join(values) + " |")

        # Synthesis narrative
        if output_format != "table":
            report_parts.append(f"\n## Synthesis\n\n{synthesis_text}")

        # Citations
        corpus_citations = [c for c in context.citations if c.citation_type.value == "corpus"]
        if corpus_citations:
            report_parts.append("\n---\n## Sources\n")
            seen = set()
            for i, cit in enumerate(corpus_citations, 1):
                key = (cit.doc_name, cit.page)
                if key not in seen:
                    seen.add(key)
                    verified_tag = "" if cit.verified else " (unverified)"
                    quote_preview = cit.quote[:100].replace("\n", " ")
                    report_parts.append(f"[{i}] {cit.doc_name}, page {cit.page}: \"{quote_preview}...\"{verified_tag}")

        result = "\n".join(report_parts)

        # Save to workspace
        if workspace_path:
            run_id = uuid.uuid4().hex[:8]
            output_dir = os.path.join(workspace_path, "outputs", f"cross_doc_{run_id}")
            os.makedirs(output_dir, exist_ok=True)

            with open(os.path.join(output_dir, "report.md"), "w") as f:
                f.write(result)

            with open(os.path.join(output_dir, "extractions.json"), "w") as f:
                json.dump(per_doc_results, f, indent=2)

            with open(os.path.join(output_dir, "metadata.json"), "w") as f:
                json.dump({
                    "task": task,
                    "index_name": index_name,
                    "schema": schema,
                    "doc_filter": doc_filter,
                    "documents_analyzed": len(per_doc_results),
                    "llm_calls": total_llm_calls,
                    "completed_at": datetime.utcnow().isoformat(),
                }, f, indent=2)

        # Append statistics
        stats = context.get_progress()
        result += f"\n\n---\n**Processing Statistics:**\n"
        result += f"- Documents analyzed: {len(per_doc_results)}/{len(all_docs)}\n"
        result += f"- LLM calls made: {total_llm_calls}\n"
        result += f"- Citations collected: {stats['citations_collected']}\n"
        result += f"- Tokens used: {stats['tokens_used']:,}\n"
        if workspace_path:
            result += f"\n**Output saved to:** `{output_dir}/`\n"

        if stats['tokens_used'] > 0:
            result += f"\n<!--TOOL_TOKEN_USAGE:{{\"total\":{stats['tokens_used']}}}-->"

        logger.info(f"Cross-document analysis completed: {len(per_doc_results)} docs, {total_llm_calls} LLM calls")
        return result

    except Exception as e:
        logger.error(f"Cross-document analysis failed: {e}", exc_info=True)
        return f"[Error] Cross-document analysis failed: {str(e)}"


@mentori_tool(
    category="RAG",
    agent_role="editor",
    is_llm_based=True,
)
async def paper_triage(
    query: str,
    index_name: str,
    top_k: int = 5,
    user_id: str = None,
    task_id: str = None,
    workspace_path: str = None,
) -> str:
    """
    Rank documents by relevance to a query — lightweight per-document scoring.

    Use this to find which papers in a collection are most relevant before
    doing deeper analysis. Each document gets a 0-10 relevance score with
    a brief rationale.

    Args:
        query: What you're looking for (e.g., "flow cytometry methods")
        index_name: Name of the document index
        top_k: Number of top results to return (default: 5, use 0 for all)
        user_id: [Auto-injected]
        task_id: [Auto-injected]

    Returns:
        JSON list of documents ranked by relevance with scores and reasons.
    """
    logger.info(f"Starting paper triage: query='{query[:60]}', index='{index_name}'")

    try:
        from backend.retrieval.rlm import RLMContext
        from backend.agents.model_router import ModelRouter
        from backend.agents.session_context import resolve_model_for_chat
        from backend.models.user import User
        from backend.database import engine
        from sqlmodel import Session

        # ── Resolve model ────────────────────────────────────────────────
        model_identifier = None
        with Session(engine) as session:
            user = session.get(User, user_id)
            if user and user.settings and "agent_roles" in user.settings:
                roles = user.settings["agent_roles"]
                model_identifier, resolved_role = resolve_model_for_chat(roles, preferred_role="editor")

        if not model_identifier:
            return "[Error] No model configured. Please set up an 'editor' or 'default' agent role in Settings."

        router = ModelRouter()

        # ── Initialize context ────────────────────────────────────────────
        try:
            context = await RLMContext.from_index(index_name, user_id)
        except ValueError as e:
            return f"[Error] Index '{index_name}' not accessible: {e}"

        all_docs = context.list_documents()
        if not all_docs:
            return f"[Error] Index '{index_name}' contains no documents."

        logger.info(f"Triaging {len(all_docs)} documents")

        # ── Score each document ───────────────────────────────────────────
        scored_docs = []
        num_docs = len(all_docs)

        for doc_idx, doc_info in enumerate(all_docs):
            doc_name = doc_info["name"]

            await emit_progress(
                task_id, "paper_triage",
                f"Scoring {doc_name}",
                phase="scoring", step=doc_idx + 1, total_steps=num_docs,
            )

            # Collect representative content: intro + keyword hits
            collected_chunks = []
            seen_idx = set()

            # Intro chunks (first 3)
            intro = context.get_chunks_range(doc_name, 0, 3)
            for chunk in intro:
                if chunk.chunk_idx not in seen_idx:
                    seen_idx.add(chunk.chunk_idx)
                    collected_chunks.append(chunk)

            # Query-relevant chunks via keyword search
            query_words = [w for w in query.lower().split() if len(w) > 3]
            for keyword in query_words[:3]:
                hits = context.search_keyword(keyword, doc_name=doc_name)
                for hit in hits[:2]:
                    if hit.chunk_idx not in seen_idx:
                        seen_idx.add(hit.chunk_idx)
                        collected_chunks.append(hit)

            # Cap at 6 chunks for quick scoring
            collected_chunks = sorted(collected_chunks, key=lambda c: c.chunk_idx)[:6]

            if not collected_chunks:
                scored_docs.append({
                    "doc_name": doc_name,
                    "relevance": 0,
                    "reason": "No content accessible",
                    "chunks": doc_info["chunks"],
                    "pages": doc_info["pages"],
                })
                continue

            chunks_text = "\n\n".join(
                f"[Chunk {c.chunk_idx}] {c.text[:300]}" for c in collected_chunks
            )

            scoring_prompt = (
                f"Rate the relevance of this document to the query.\n\n"
                f"Query: {query}\n\n"
                f"Document: {doc_name}\n"
                f"Content sample:\n{chunks_text}\n\n"
                f"Return ONLY a JSON object: {{\"relevance\": <0-10>, \"reason\": \"<1 sentence>\"}}"
            )

            try:
                response = await router.chat(
                    model_identifier=model_identifier,
                    messages=[{"role": "user", "content": scoring_prompt}],
                    options={"temperature": 0.0, "num_predict": 128},
                    think=False,
                )
                context.llm_calls_made += 1

                raw = response.get("message", {}).get("content", "").strip()
                # Strip markdown fences if present
                if raw.startswith("```"):
                    raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

                score_data = json.loads(raw)
                scored_docs.append({
                    "doc_name": doc_name,
                    "relevance": int(score_data.get("relevance", 0)),
                    "reason": score_data.get("reason", ""),
                    "chunks": doc_info["chunks"],
                    "pages": doc_info["pages"],
                })

                if "prompt_eval_count" in response:
                    context.total_tokens_used += response.get("prompt_eval_count", 0) + response.get("eval_count", 0)

            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"Failed to score {doc_name}: {e}")
                scored_docs.append({
                    "doc_name": doc_name,
                    "relevance": -1,
                    "reason": "scoring failed",
                    "chunks": doc_info["chunks"],
                    "pages": doc_info["pages"],
                })

        # ── Sort and format ───────────────────────────────────────────────
        scored_docs.sort(key=lambda d: d["relevance"], reverse=True)

        if top_k > 0:
            scored_docs = scored_docs[:top_k]

        # Build readable output
        output_parts = [f"# Paper Triage: \"{query}\"\n"]
        output_parts.append(f"**Index:** {index_name} ({len(all_docs)} documents)\n")
        output_parts.append(f"**Showing:** top {len(scored_docs)} results\n")
        output_parts.append("\n| Rank | Document | Relevance | Reason |")
        output_parts.append("|------|----------|-----------|--------|")

        for i, doc in enumerate(scored_docs, 1):
            name = doc["doc_name"][:40]
            score = doc["relevance"]
            bar = "#" * score + "." * (10 - max(0, score))
            reason = doc["reason"][:80]
            output_parts.append(f"| {i} | {name} | {score}/10 [{bar}] | {reason} |")

        output_parts.append(f"\n**LLM calls:** {context.llm_calls_made}")

        # Also return raw JSON for programmatic use
        output_parts.append(f"\n<details><summary>Raw JSON</summary>\n\n```json\n{json.dumps(scored_docs, indent=2)}\n```\n</details>")

        stats = context.get_progress()
        if stats['tokens_used'] > 0:
            output_parts.append(f"\n<!--TOOL_TOKEN_USAGE:{{\"total\":{stats['tokens_used']}}}-->")

        final_output = "\n".join(output_parts)

        # Write triage report to outputs/ for audit trail
        if workspace_path:
            try:
                from pathlib import Path as _Path
                from datetime import datetime as _dt
                ts = _dt.utcnow().strftime("%Y%m%d_%H%M%S")
                safe_task = (task_id or "task")[:16].replace("-", "")
                outputs_dir = _Path(workspace_path) / "outputs"
                outputs_dir.mkdir(parents=True, exist_ok=True)
                triage_path = outputs_dir / f"triage_{ts}_{safe_task}.md"
                triage_path.write_text(final_output, encoding="utf-8")
                logger.info(f"[TRIAGE] Report written: {triage_path}")
            except Exception as _e:
                logger.warning(f"[TRIAGE] Failed to write report: {_e}")

        logger.info(f"Paper triage completed: {len(scored_docs)} docs scored, {context.llm_calls_made} LLM calls")
        return final_output

    except Exception as e:
        logger.error(f"Paper triage failed: {e}", exc_info=True)
        return f"[Error] Paper triage failed: {str(e)}"


@mentori_tool(
    category="RAG",
    agent_role="editor",
    is_llm_based=True
)
async def analyze_corpus(
    task: str,
    index_name: str,
    doc_filter: Optional[str] = None,
    chunks_per_paper: int = 20,
    user_id: str = None,
    task_id: str = None,
    workspace_path: str = None,
) -> str:
    """
    Analyze every paper in an index with one dedicated LLM call per paper.

    Unlike cross_document_analysis (structured JSON extraction) this tool produces
    free-form narrative analyses — ideal for "what are the main findings of each paper?"

    Each paper's analysis is saved immediately to workspace as it completes, so the
    user can read intermediate results while the tool is still running.  A final
    synthesis LLM call produces a cross-paper summary after all papers are done.

    Use for:
    - "Analyze the papers in the index. What are the main findings from each?"
    - "Summarize each paper's contribution"
    - "What does each paper say about X?"

    Args:
        task: What to find/analyze in each paper (e.g. "main findings and methods")
        index_name: Name of the document index
        doc_filter: Optional filter — comma-separated filenames or a keyword.
        chunks_per_paper: Max chunks to sample per paper (default 20).
            Lower = faster but less thorough; raise for long papers.
        user_id: [Auto-injected]
        task_id: [Auto-injected]
        workspace_path: [Auto-injected]

    Returns:
        Compact summary with paths to per-paper files and synthesis.
        Full analyses saved under outputs/corpus_analysis_{run_id}/.
    """
    import uuid
    from datetime import datetime

    logger.info(f"Starting analyze_corpus: task='{task[:80]}', index='{index_name}'")

    if not workspace_path:
        return "[Error] analyze_corpus requires a workspace_path (should be auto-injected)."

    try:
        from backend.retrieval.rlm import RLMContext
        from backend.agents.model_router import ModelRouter
        from backend.agents.session_context import resolve_model_for_chat
        from backend.models.user import User
        from backend.database import engine
        from sqlmodel import Session

        # ── Resolve model (editor role) ───────────────────────────────────
        model_identifier = None
        with Session(engine) as session:
            user = session.get(User, user_id)
            if user and user.settings and "agent_roles" in user.settings:
                roles = user.settings["agent_roles"]
                model_identifier, resolved_role = resolve_model_for_chat(roles, preferred_role="editor")
                logger.info(f"analyze_corpus using model: {model_identifier} (role: {resolved_role})")

        if not model_identifier:
            return "[Error] No model configured. Please set up an 'editor' or 'default' agent role in Settings."

        router = ModelRouter()

        # ── Initialize RLM context ─────────────────────────────────────────
        try:
            context = await RLMContext.from_index(index_name, user_id)
        except ValueError as e:
            return f"[Error] Index '{index_name}' not accessible: {e}"

        all_docs = context.list_documents()
        if not all_docs:
            return f"[Error] Index '{index_name}' contains no documents."

        docs_to_analyze = _filter_documents(all_docs, doc_filter, context._chunks_by_doc)
        if not docs_to_analyze:
            sample = ", ".join(d["name"] for d in all_docs[:5])
            return (
                f"[Error] No documents match filter '{doc_filter}'. "
                f"Available (sample): {sample}"
            )

        num_docs = len(docs_to_analyze)
        logger.info(f"analyze_corpus: {num_docs}/{len(all_docs)} docs to analyze")

        # ── Create output directory ────────────────────────────────────────
        run_id = uuid.uuid4().hex[:8]
        output_dir = os.path.join(workspace_path, "outputs", f"corpus_analysis_{run_id}")
        papers_dir = os.path.join(output_dir, "papers")
        os.makedirs(papers_dir, exist_ok=True)

        metadata_path = os.path.join(output_dir, "metadata.json")
        progress_path = os.path.join(output_dir, "progress.json")
        synthesis_path = os.path.join(output_dir, "synthesis.md")

        # Write initial metadata
        started_at = datetime.utcnow().isoformat()
        _write_json_safe(metadata_path, {
            "task": task,
            "index_name": index_name,
            "doc_filter": doc_filter,
            "docs_to_analyze": [d["name"] for d in docs_to_analyze],
            "total_docs": num_docs,
            "chunks_per_paper": chunks_per_paper,
            "model": model_identifier,
            "started_at": started_at,
            "output_dir": output_dir,
        })

        # Init progress tracker (all pending)
        progress_data = {d["name"]: {"status": "pending"} for d in docs_to_analyze}
        _write_json_safe(progress_path, progress_data)

        await emit_progress(
            task_id, "analyze_corpus",
            f"Starting corpus analysis: {num_docs} papers",
            phase="start", step=0, total_steps=num_docs,
        )

        # ── Per-paper loop ─────────────────────────────────────────────────
        per_paper_analyses = {}   # doc_name → analysis text (for synthesis)
        completed_docs = []
        total_llm_calls = 0
        total_tokens = 0

        for doc_idx, doc_info in enumerate(docs_to_analyze):
            doc_name = doc_info["name"]
            total_chunks = doc_info["chunks"]
            title = doc_info.get("title") or ""
            author = doc_info.get("author") or ""

            await emit_progress(
                task_id, "analyze_corpus",
                f"Analyzing paper {doc_idx + 1}/{num_docs}: {doc_name}",
                phase="per_paper", step=doc_idx + 1, total_steps=num_docs,
            )

            progress_data[doc_name] = {"status": "processing"}
            _write_json_safe(progress_path, progress_data)

            # Collect chunks: intro + conclusion + semantic search on task
            chunks = _collect_chunks_for_paper(
                context, doc_name, total_chunks, task, cap=chunks_per_paper
            )

            if not chunks:
                logger.warning(f"No chunks found for {doc_name}, skipping")
                progress_data[doc_name] = {
                    "status": "skipped",
                    "reason": "no chunks found",
                }
                _write_json_safe(progress_path, progress_data)
                continue

            # Build prompt
            chunks_text = "\n\n".join(
                f"[Chunk {c.chunk_idx}, Page {c.page}]\n{c.text}"
                for c in chunks
            )
            title_line = f"**Title:** {title}\n" if title else ""
            author_line = f"**Author(s):** {author}\n" if author else ""

            per_paper_prompt = (
                f"You are a scientific analyst reading a single paper.\n\n"
                f"## Your Task\n{task}\n\n"
                f"## Paper: {doc_name}\n"
                f"{title_line}"
                f"{author_line}\n"
                f"## Content ({len(chunks)} excerpts, ordered by position)\n\n"
                f"{chunks_text}\n\n"
                f"## Instructions\n"
                f"Write a structured markdown analysis of THIS paper only (~300-400 words):\n"
                f"1. **Main Question / Objective** — what the paper set out to do\n"
                f"2. **Key Findings** — the most important results (be specific: include numbers, "
                f"effect sizes, p-values if present in the excerpts)\n"
                f"3. **Methods** — key experimental/analytical approach in 1-2 sentences\n"
                f"4. **Limitations** — if explicitly stated in the excerpts\n"
                f"5. **Key Quote** — 1 verbatim excerpt that best captures the main finding "
                f"(include chunk number and page)\n\n"
                f"Grounded only in the provided excerpts. "
                f"Write 'not found in sampled text' for any section not covered."
            )

            try:
                response = await router.chat(
                    model_identifier=model_identifier,
                    messages=[{"role": "user", "content": per_paper_prompt}],
                    options={"temperature": 0.15, "num_predict": 1500},
                    think=False,
                )
                analysis_text = response.get("message", {}).get("content", "").strip()
                total_tokens += (
                    response.get("prompt_eval_count", 0) +
                    response.get("eval_count", 0)
                )
                total_llm_calls += 1
            except Exception as e:
                logger.error(f"LLM call failed for {doc_name}: {e}")
                analysis_text = f"[Analysis failed: {str(e)}]"

            if not analysis_text:
                analysis_text = "[Analysis not available — model returned empty response]"

            # Save per-paper file immediately
            safe_name = _safe_doc_filename(doc_name, doc_idx + 1)
            paper_path = os.path.join(papers_dir, safe_name + ".md")
            try:
                with open(paper_path, "w", encoding="utf-8") as f:
                    f.write(f"# Analysis: {doc_name}\n\n")
                    if title:
                        f.write(f"**Title:** {title}  \n")
                    if author:
                        f.write(f"**Author(s):** {author}  \n")
                    f.write(f"**Task:** {task}  \n")
                    f.write(f"**Chunks sampled:** {len(chunks)}/{total_chunks}  \n\n")
                    f.write("---\n\n")
                    f.write(analysis_text)
                    f.write("\n")
            except Exception as e:
                logger.error(f"Failed to write per-paper file for {doc_name}: {e}")

            per_paper_analyses[doc_name] = analysis_text
            completed_docs.append(doc_name)

            progress_data[doc_name] = {
                "status": "complete",
                "file": f"./outputs/corpus_analysis_{run_id}/papers/{safe_name}.md",
                "completed_at": datetime.utcnow().isoformat(),
            }
            _write_json_safe(progress_path, progress_data)
            logger.info(f"Completed paper {doc_idx + 1}/{num_docs}: {doc_name}")

        # ── Final synthesis ────────────────────────────────────────────────
        synthesis_text = ""
        if per_paper_analyses:
            await emit_progress(
                task_id, "analyze_corpus",
                f"Synthesizing findings across {len(completed_docs)} papers",
                phase="synthesis", step=num_docs, total_steps=num_docs,
            )

            # Truncate each paper's analysis to bound the synthesis prompt.
            # Use 50% of the model's safe char budget split across all papers
            # (the other 50% is for the system prompt, task, and output).
            synthesis_char_budget = safe_char_budget(fraction=0.50)
            max_per_paper = max(300, synthesis_char_budget // max(len(per_paper_analyses), 1))
            synthesis_sections = "\n\n".join(
                f"### {name}\n{text[:max_per_paper]}"
                + ("..." if len(text) > max_per_paper else "")
                for name, text in per_paper_analyses.items()
            )

            synthesis_prompt = (
                f"You are a senior scientist synthesizing findings across "
                f"{len(per_paper_analyses)} papers.\n\n"
                f"## Original Request\n{task}\n\n"
                f"## Per-Paper Analyses\n\n"
                f"{synthesis_sections}\n\n"
                f"## Instructions\n"
                f"Write a synthesis in markdown (~400-600 words) covering:\n"
                f"1. **Cross-Cutting Themes** — findings that appear across multiple papers\n"
                f"2. **Points of Divergence** — where papers disagree or take different approaches\n"
                f"3. **Overall Conclusion** — what can be said about the corpus as a whole\n"
                f"4. **Gaps** — what questions the papers collectively do not answer\n\n"
                f"Reference specific papers by filename when making comparative claims. "
                f"Do NOT repeat the per-paper analyses verbatim — synthesize them."
            )

            try:
                synth_response = await router.chat(
                    model_identifier=model_identifier,
                    messages=[{"role": "user", "content": synthesis_prompt}],
                    options={"temperature": 0.2, "num_predict": 2048},
                    think=False,
                )
                synthesis_text = synth_response.get("message", {}).get("content", "").strip()
                total_tokens += (
                    synth_response.get("prompt_eval_count", 0) +
                    synth_response.get("eval_count", 0)
                )
                total_llm_calls += 1
            except Exception as e:
                logger.error(f"Synthesis LLM call failed: {e}")
                synthesis_text = f"[Synthesis failed: {str(e)}]"

            if synthesis_text:
                try:
                    with open(synthesis_path, "w", encoding="utf-8") as f:
                        f.write(f"# Corpus Synthesis\n\n")
                        f.write(f"**Task:** {task}  \n")
                        f.write(f"**Papers analyzed:** {len(completed_docs)}/{num_docs}  \n\n")
                        f.write("---\n\n")
                        f.write(synthesis_text)
                        f.write("\n")
                except Exception as e:
                    logger.error(f"Failed to write synthesis.md: {e}")

        # ── Finalize metadata ──────────────────────────────────────────────
        _write_json_safe(metadata_path, {
            "task": task,
            "index_name": index_name,
            "doc_filter": doc_filter,
            "docs_to_analyze": [d["name"] for d in docs_to_analyze],
            "total_docs": num_docs,
            "completed_docs": len(completed_docs),
            "skipped_docs": num_docs - len(completed_docs),
            "chunks_per_paper": chunks_per_paper,
            "model": model_identifier,
            "started_at": started_at,
            "completed_at": datetime.utcnow().isoformat(),
            "total_llm_calls": total_llm_calls,
            "output_dir": output_dir,
        })

        # ── Build return value ─────────────────────────────────────────────
        # Return the full synthesis so the supervisor can score it as complete.
        # For large corpora the observation distiller will condense it if needed,
        # which is still better than a truncated preview that triggers retries.
        skipped = [n for n, d in progress_data.items() if d.get("status") == "skipped"]
        paper_file_lines = "\n".join(
            f"  - {d['file']}"
            for d in progress_data.values()
            if d.get("status") == "complete"
        )
        skipped_note = f"\n**Skipped:** {', '.join(skipped)}" if skipped else ""

        compact_result = (
            f"**Corpus Analysis Complete**\n"
            f"- Index: `{index_name}`\n"
            f"- Papers analyzed: {len(completed_docs)}/{num_docs}{skipped_note}\n"
            f"- LLM calls: {total_llm_calls}\n"
            f"- Output directory: `./outputs/corpus_analysis_{run_id}/`\n\n"
            f"**Per-paper analyses** (one file each):\n"
            f"{paper_file_lines}\n\n"
            f"**Synthesis:** `./outputs/corpus_analysis_{run_id}/synthesis.md`\n"
            f"**Progress log:** `./outputs/corpus_analysis_{run_id}/progress.json`\n\n"
            f"{synthesis_text}"
        )

        if total_tokens > 0:
            compact_result += f"\n\n<!--TOOL_TOKEN_USAGE:{{\"total\":{total_tokens}}}-->"

        logger.info(
            f"analyze_corpus completed: {len(completed_docs)}/{num_docs} papers, "
            f"{total_llm_calls} LLM calls, run_id={run_id}"
        )
        return compact_result

    except Exception as e:
        logger.error(f"analyze_corpus failed: {e}", exc_info=True)
        return f"[Error] analyze_corpus failed: {str(e)}"


@mentori_tool(
    category="RAG",
    agent_role="editor",
    is_llm_based=True
)
async def summarize_document_pages(
    index_name: str,
    doc_name: str,
    user_id: str,
    task_id: str,
    workspace_path: str,
    pages: str = "all",
    words_per_page: int = 200
) -> str:
    """
    Create a deterministic page-by-page summary of a document.

    This tool processes EVERY page sequentially (no AI deciding what to analyze).
    Perfect for:
    - Long documents (100+ pages) that need complete coverage
    - When you need predictable, reproducible summaries
    - Creating condensed versions of large documents

    NOTE: This tool CONDENSES content (reduces each page to ~200 words).
    The result can then be used for further analysis or Q&A.

    Args:
        index_name: Name of the document index
        doc_name: Specific document to summarize (e.g., "report.pdf")
        user_id: [Auto-injected]
        task_id: [Auto-injected]
        pages: Which pages to process:
               - "all" (default): All pages
               - "1-10": Pages 1 through 10
               - "1,3,5,7": Specific pages
        words_per_page: Target words per page summary (default: 200)

    Returns:
        Markdown document with:
        - One summary section per page
        - Reference list
        - Path to full output folder with individual page files
    """
    import uuid
    from datetime import datetime

    logger.info(f"Starting page-by-page summarization for '{doc_name}' in '{index_name}'")

    try:
        from backend.retrieval.rlm import RLMContext
        from backend.retrieval.rlm.summarizer import PageSummarizer
        from backend.agents.model_router import ModelRouter
        from backend.agents.session_context import resolve_model_for_chat
        from backend.models.user import User
        from backend.database import engine
        from sqlmodel import Session

        # Get model - prefer editor role for document operations
        model_identifier = None
        with Session(engine) as session:
            user = session.get(User, user_id)
            if user and user.settings and "agent_roles" in user.settings:
                roles = user.settings["agent_roles"]
                model_identifier, resolved_role = resolve_model_for_chat(roles, preferred_role="editor")
                logger.info(f"Page summarizer using model: {model_identifier} (role: {resolved_role})")

        if not model_identifier:
            return "[Error] No model configured. Please set up agent roles in your settings (editor or default)."

        # Initialize context
        context = await RLMContext.from_index(index_name, user_id)

        # Check document exists
        docs = context.list_documents()
        doc_names = [d['name'] for d in docs]
        if doc_name not in doc_names:
            # Try partial match
            matches = [d for d in doc_names if doc_name.lower() in d.lower()]
            if matches:
                doc_name = matches[0]
                logger.info(f"Matched document name to: {doc_name}")
            else:
                available = ", ".join(doc_names[:5])
                return f"[Error] Document '{doc_name}' not found. Available: {available}"

        # Parse pages parameter
        structure = context.get_document_structure(doc_name)
        total_pages = structure.get("total_pages", 0)
        total_chunks = structure.get("total_chunks", 0)

        logger.info(f"Document structure: {total_pages} pages, {total_chunks} chunks")
        logger.info(f"Pages in structure: {[p.get('page') for p in structure.get('pages', [])]}")

        # If pages metadata is missing/broken (all chunks on page 1), use chunk-based pagination
        if total_pages <= 1 and total_chunks > 10:
            logger.warning(f"Page metadata appears broken ({total_pages} pages, {total_chunks} chunks). "
                          f"Using chunk-based pagination instead.")
            # Treat every ~5 chunks as a "page" for summarization
            chunks_per_page = 5
            total_pages = (total_chunks + chunks_per_page - 1) // chunks_per_page
            logger.info(f"Created {total_pages} virtual pages from {total_chunks} chunks")

            # Override to use chunk-based processing
            # The PageSummarizer will need to handle this differently
            # For now, just note this in the output
            structure["virtual_pages"] = True
            structure["chunks_per_page"] = chunks_per_page
            structure["total_pages"] = total_pages

        pages_list = None  # None means all pages
        if pages != "all":
            pages_list = []
            for part in pages.split(","):
                part = part.strip()
                if "-" in part:
                    start, end = part.split("-")
                    pages_list.extend(range(int(start), int(end) + 1))
                else:
                    pages_list.append(int(part))
            # Filter to valid pages
            pages_list = [p for p in pages_list if 1 <= p <= total_pages]
            logger.info(f"Requested pages {pages} -> filtered to {pages_list}")

        # Create output directory (inside user's workspace)
        run_id = uuid.uuid4().hex[:8]
        output_dir = os.path.join(workspace_path, "outputs", f"summary_{run_id}")

        # Run summarizer
        router = ModelRouter()
        summarizer = PageSummarizer(router, model_identifier)

        # Check if we need chunk-based pagination (page metadata broken)
        use_chunk_pagination = structure.get("virtual_pages", False)
        chunks_per_page = structure.get("chunks_per_page", 5)

        result = await summarizer.summarize_pages(
            context=context,
            doc_name=doc_name,
            pages=pages_list,
            words_per_page=words_per_page,
            include_context_overlap=True,
            output_dir=output_dir,
            use_chunk_pagination=use_chunk_pagination,
            chunks_per_page=chunks_per_page
        )

        if "error" in result:
            return f"[Error] {result['error']}"

        # Build response
        stats = result["statistics"]
        output = result["full_summary"]

        # Add processing info
        output += f"\n\n---\n**Processing Statistics:**\n"
        output += f"- Pages processed: {stats['pages_processed']}\n"
        output += f"- Chunks analyzed: {stats['total_chunks']}\n"
        output += f"- Total words in summary: {stats['total_words']}\n"
        output += f"- LLM calls made: {stats['llm_calls']}\n"
        output += f"- Citations collected: {stats['total_citations']}\n"

        # Append token usage marker for chat_loop
        if 'tokens_used' in stats:
             output += f"- Tokens used: {stats['tokens_used']:,}\n"
             output += f"\n<!--TOOL_TOKEN_USAGE:{{\"total\":{stats['tokens_used']}}}-->"

        if result.get("output_files"):
            output += f"\n📁 **Output saved to:** `{output_dir}/`\n"
            output += f"- Full summary: `full_summary.md`\n"
            output += f"- Individual pages: `pages/page_XXX.md`\n"
            output += f"- Citations: `citations.json`\n"

        logger.info(f"Page summarization completed: {stats['pages_processed']} pages, {stats['llm_calls']} LLM calls")

        # Prepare concise return for the agent (prevent context pollution)
        agent_return = (
            f"**Summarization Complete**\n"
            f"- Document: {doc_name}\n"
            f"- Pages processed: {stats['pages_processed']}\n"
            f"- Total words: {stats['total_words']}\n"
            f"- Output saved to: `{output_dir}/full_summary.md`\n"
            f"\nI have saved the full summary to the workspace. You can read specific sections if needed."
        )

        return agent_return

    except Exception as e:
        logger.error(f"Page summarization failed: {e}", exc_info=True)
        return f"[Error] Summarization failed: {str(e)}"
