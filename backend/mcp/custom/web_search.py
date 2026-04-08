"""
Web Search Tool with Comprehensive Documentation

This module implements web search with three modes:
1. Raw: Returns Tavily results as a table (no LLM processing)
2. Filtered (llm_filter): LLM evaluates each result, removes irrelevant rows
3. Deep (llm_deep): Iterative research with source tracking

ALL modes produce a comprehensive markdown document saved to the workspace,
ensuring scientists can always access the objective raw data.
"""

import logging
import httpx
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from backend.mcp.decorator import mentori_tool
from backend.agents.session_context import get_session_context

logger = logging.getLogger(__name__)

# Tavily API configuration
TAVILY_URL = "https://api.tavily.com/search"
TAVILY_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    before_sleep=lambda retry_state: logger.warning(
        f"web_search retry {retry_state.attempt_number}/3 after {retry_state.outcome.exception()}"
    ),
)
def _fetch_tavily(payload: dict) -> dict:
    """
    Fetch search results from Tavily with retry logic.
    Retries on timeout and connection errors with exponential backoff.
    """
    with httpx.Client(timeout=TAVILY_TIMEOUT) as client:
        resp = client.post(TAVILY_URL, json=payload)
        resp.raise_for_status()
        return resp.json()


def _generate_document_path(workspace_path: str, search_type: str) -> Path:
    """Generate a unique document path with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    outputs_dir = Path(workspace_path) / "outputs" / "web_searches"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    return outputs_dir / f"{timestamp}_web_search_{search_type}.md"


def _format_results_table(results: List[Dict], include_score: bool = False) -> str:
    """Format Tavily results as a markdown table."""
    if not results:
        return "| # | Title | URL | Content |\n|---|-------|-----|---------|  \n| - | No results found | - | - |"

    lines = []
    if include_score:
        lines.append("| # | Score | Title | URL | Content Preview |")
        lines.append("|---|-------|-------|-----|-----------------|")
    else:
        lines.append("| # | Title | URL | Content Preview |")
        lines.append("|---|-------|-----|-----------------|")

    for i, res in enumerate(results, 1):
        title = res.get("title", "No Title").replace("|", "\\|")[:60]
        url = res.get("url", "#")
        content = res.get("content", "")[:150].replace("|", "\\|").replace("\n", " ")
        score = res.get("score", 0)

        if include_score:
            lines.append(f"| {i} | {score:.2f} | {title} | [{url[:40]}...]({url}) | {content}... |")
        else:
            lines.append(f"| {i} | {title} | [{url[:40]}...]({url}) | {content}... |")

    return "\n".join(lines)


def _format_full_results_list(results: List[Dict]) -> str:
    """Format results as a detailed list with full content."""
    if not results:
        return "No results found."

    lines = []
    for i, res in enumerate(results, 1):
        title = res.get("title", "No Title")
        url = res.get("url", "#")
        content = res.get("content", "No content available")
        score = res.get("score", 0)

        lines.append(f"### [{i}] {title}")
        lines.append(f"**URL:** {url}")
        lines.append(f"**Relevance Score:** {score:.2f}")
        lines.append(f"**Content:**\n{content}")
        lines.append("")

    return "\n".join(lines)


@mentori_tool(
    category="research",
    secrets=["TAVILY_API_KEY", "user_id", "workspace_path"],
    agent_role="handyman",
    is_llm_based=True
)
async def web_search(
    query: str,
    max_results: int = 5,
    llm_filter: bool = False,
    llm_deep: bool = False,
    TAVILY_API_KEY: str = None,
    user_id: str = None,
    workspace_path: str = None
) -> str:
    """
    Search the web using Tavily. ALL searches produce a comprehensive document.

    Args:
        query: Search query
        max_results: Max links to return (default 5)
        llm_filter: If True, LLM evaluates each result and removes irrelevant ones.
                    Returns: Original table + filtered table + LLM reasoning.
                    Document shows exactly which rows were removed and why.
        llm_deep: If True, performs iterative multi-round research.
                  Continues until knowledge gaps are filled or max iterations reached.
                  Document tracks ALL sources found across ALL iterations.
        TAVILY_API_KEY: [Auto-injected]
        user_id: [Auto-injected]
        workspace_path: [Auto-injected]

    Returns:
        Markdown string with summary + path to comprehensive document.
        The document contains the objective truth (raw data, tables, sources).
    """
    # Validate API key
    if not TAVILY_API_KEY:
        logger.error("[WEB_SEARCH] TAVILY_API_KEY is None/empty!")
        return "Error: TAVILY_API_KEY is missing. Please configure it in User Settings."

    import re
    clean_key = re.sub(r'[\s\u00a0\u200b\u200c\u200d\ufeff]+', '', TAVILY_API_KEY)

    # Get workspace path from context if not provided
    if not workspace_path:
        ctx = get_session_context()
        workspace_path = ctx.workspace_path if ctx else "/tmp"

    # Route to appropriate handler
    if llm_deep:
        return await _deep_web_research(query, user_id, clean_key, workspace_path, max_iterations=5)
    elif llm_filter:
        return await _filtered_web_search(query, user_id, clean_key, workspace_path, max_results)
    else:
        return await _raw_web_search(query, clean_key, workspace_path, max_results)


async def _raw_web_search(query: str, api_key: str, workspace_path: str, max_results: int) -> str:
    """
    Basic web search with no LLM processing.
    Returns raw Tavily results as a table + saves comprehensive document.
    """
    logger.info(f"[WEB_SEARCH:RAW] Query: '{query}'")

    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "max_results": max_results,
        "include_answer": True
    }

    try:
        data = _fetch_tavily(payload)
        results = data.get("results", [])
        tavily_answer = data.get("answer", "")

        # Generate document
        doc_path = _generate_document_path(workspace_path, "raw")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        doc_content = f"""# Web Search Results (Raw)

**Generated:** {timestamp}
**Query:** `{query}`
**Max Results:** {max_results}
**Mode:** Raw (no LLM processing)

---

## Tavily's Answer
{tavily_answer if tavily_answer else "_No answer provided by Tavily_"}

---

## Results Table

{_format_results_table(results, include_score=True)}

---

## Full Results (with complete content)

{_format_full_results_list(results)}

---

## Metadata
- Total results returned: {len(results)}
- Search depth: basic
- Document path: `{doc_path}`
"""

        # Save document
        doc_path.write_text(doc_content, encoding="utf-8")
        logger.info(f"[WEB_SEARCH:RAW] Document saved: {doc_path}")

        # Return summary for orchestrator
        relative_path = doc_path.relative_to(Path(workspace_path))
        return f"""## Web Search Results for: "{query}"

**Tavily Answer:** {tavily_answer[:300] if tavily_answer else "None provided"}...

### Results Summary
{_format_results_table(results[:5], include_score=True)}

📄 **Full documentation saved to:** `{relative_path}`
   Open this file to see complete content from all sources.

**Total results:** {len(results)}
"""

    except httpx.HTTPStatusError as e:
        error_body = e.response.text[:500] if e.response.text else "No response body"
        logger.error(f"[WEB_SEARCH:RAW] Tavily API error: HTTP {e.response.status_code} - {error_body}")
        if e.response.status_code == 401:
            return f"Search failed: Invalid API key (HTTP 401). Please check your TAVILY_API_KEY in User Settings."
        return f"Search failed: HTTP {e.response.status_code}"
    except Exception as e:
        logger.error(f"[WEB_SEARCH:RAW] Failed: {type(e).__name__}: {e}")
        return f"Search failed: {str(e)}"


async def _filtered_web_search(query: str, user_id: str, api_key: str, workspace_path: str, max_results: int) -> str:
    """
    LLM-filtered web search.

    Process:
    1. Fetch Tavily results
    2. LLM evaluates EACH result individually (keep/remove + reason)
    3. Document shows: original table, filtering decisions, filtered table
    4. LLM provides brief synthesis (separate from objective data)
    """
    from backend.agents.model_router import ModelRouter
    from backend.models.user import User
    from backend.database import engine
    from sqlmodel import Session

    logger.info(f"[WEB_SEARCH:FILTERED] Query: '{query}'")

    # Fetch results
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "max_results": max_results,
        "include_answer": True
    }

    try:
        data = _fetch_tavily(payload)
    except Exception as e:
        logger.error(f"[WEB_SEARCH:FILTERED] Tavily fetch failed: {e}")
        return f"Search failed: {str(e)}"

    results = data.get("results", [])
    tavily_answer = data.get("answer", "")

    if not results:
        return "No search results found for your query."

    # Resolve model
    model_identifier = "ollama::llama3.2:latest"
    with Session(engine) as session:
        user = session.get(User, user_id)
        if user and user.settings and "agent_roles" in user.settings:
            roles = user.settings["agent_roles"]
            model_identifier = roles.get("handyman") or roles.get("default") or model_identifier

    router = ModelRouter()

    # Evaluate each result
    filter_decisions = []
    for i, res in enumerate(results, 1):
        prompt = f"""You are a scientific research filter. Evaluate this search result for relevance to the query.

QUERY: "{query}"

RESULT #{i}:
- Title: {res.get('title', 'No title')}
- URL: {res.get('url', '#')}
- Content: {res.get('content', 'No content')[:500]}

DECISION REQUIRED:
Reply with EXACTLY this format (no other text):
DECISION: KEEP or REMOVE
RELEVANCE: (0-100 score)
REASON: (one sentence explaining why)
"""

        try:
            response = await router.generate(
                model_identifier=model_identifier,
                prompt=prompt,
                options={"temperature": 0.1}
            )
            resp_text = response.get("response", "")

            # Parse decision
            decision = "KEEP" if "KEEP" in resp_text.upper() else "REMOVE"

            # Extract relevance score
            relevance = 50  # default
            if "RELEVANCE:" in resp_text.upper():
                try:
                    rel_part = resp_text.upper().split("RELEVANCE:")[1].split("\n")[0]
                    relevance = int(''.join(filter(str.isdigit, rel_part[:5])))
                except:
                    pass

            # Extract reason
            reason = "No reason provided"
            if "REASON:" in resp_text.upper():
                reason = resp_text.split("REASON:")[-1].strip().split("\n")[0][:200]

            filter_decisions.append({
                "index": i,
                "result": res,
                "decision": decision,
                "relevance": relevance,
                "reason": reason
            })

        except Exception as e:
            logger.warning(f"[WEB_SEARCH:FILTERED] Failed to evaluate result {i}: {e}")
            filter_decisions.append({
                "index": i,
                "result": res,
                "decision": "KEEP",  # Keep on error
                "relevance": 50,
                "reason": f"Evaluation failed: {str(e)[:50]}"
            })

    # Separate kept and removed
    kept_results = [d for d in filter_decisions if d["decision"] == "KEEP"]
    removed_results = [d for d in filter_decisions if d["decision"] == "REMOVE"]

    # Generate synthesis from kept results only
    synthesis = ""
    if kept_results:
        synthesis_prompt = f"""Based on these filtered search results for "{query}", provide a brief synthesis (2-3 sentences).
Focus only on facts from the sources. Do not add information not present in the results.

KEPT RESULTS:
"""
        for d in kept_results:
            synthesis_prompt += f"\n- [{d['index']}] {d['result'].get('title')}: {d['result'].get('content', '')[:300]}"

        try:
            response = await router.generate(
                model_identifier=model_identifier,
                prompt=synthesis_prompt,
                options={"temperature": 0.2}
            )
            synthesis = response.get("response", "").strip()
        except Exception as e:
            synthesis = f"(Synthesis failed: {e})"

    # Generate document
    doc_path = _generate_document_path(workspace_path, "filtered")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Build filtering decisions table
    filter_table_lines = ["| # | Title | Decision | Relevance | Reason |", "|---|-------|----------|-----------|--------|"]
    for d in filter_decisions:
        title = d["result"].get("title", "No title")[:40]
        emoji = "✅" if d["decision"] == "KEEP" else "❌"
        filter_table_lines.append(f"| {d['index']} | {title} | {emoji} {d['decision']} | {d['relevance']}/100 | {d['reason'][:60]} |")
    filter_table = "\n".join(filter_table_lines)

    # Build kept results table
    kept_table_lines = ["| # | Title | URL | Content Preview |", "|---|-------|-----|-----------------|"]
    for d in kept_results:
        res = d["result"]
        title = res.get("title", "No title")[:50]
        url = res.get("url", "#")
        content = res.get("content", "")[:100].replace("|", "\\|").replace("\n", " ")
        kept_table_lines.append(f"| {d['index']} | {title} | [{url[:30]}...]({url}) | {content}... |")
    kept_table = "\n".join(kept_table_lines) if kept_results else "| - | No results kept | - | - |"

    doc_content = f"""# Web Search Results (LLM Filtered)

**Generated:** {timestamp}
**Query:** `{query}`
**Max Results:** {max_results}
**Mode:** LLM Filtered (llm_filter=True)
**Model Used:** {model_identifier}

---

## Executive Summary

**Tavily's Answer:** {tavily_answer if tavily_answer else "_None provided_"}

**LLM Synthesis (based on kept results only):**
{synthesis if synthesis else "_No synthesis generated_"}

---

## Filtering Statistics

- **Total results from Tavily:** {len(results)}
- **Kept after filtering:** {len(kept_results)}
- **Removed as irrelevant:** {len(removed_results)}
- **Keep rate:** {len(kept_results)/len(results)*100:.1f}%

---

## Original Results Table (Before Filtering)

{_format_results_table(results, include_score=True)}

---

## Filtering Decisions

The LLM evaluated each result for relevance to the query.

{filter_table}

---

## Filtered Results Table (After Filtering)

These results were deemed relevant by the LLM:

{kept_table}

---

## Removed Results (for transparency)

These results were removed and why:

"""

    for d in removed_results:
        res = d["result"]
        doc_content += f"""
### ❌ [{d['index']}] {res.get('title', 'No title')}
- **URL:** {res.get('url', '#')}
- **Reason for removal:** {d['reason']}
- **Relevance score:** {d['relevance']}/100
"""

    doc_content += f"""
---

## Full Content of Kept Results

"""

    for d in kept_results:
        res = d["result"]
        doc_content += f"""
### ✅ [{d['index']}] {res.get('title', 'No title')}
- **URL:** {res.get('url', '#')}
- **Relevance score:** {d['relevance']}/100
- **Keep reason:** {d['reason']}

**Full Content:**
{res.get('content', 'No content available')}

"""

    doc_content += f"""
---

## Metadata
- Document path: `{doc_path}`
- Model: {model_identifier}
- Processing time: {timestamp}
"""

    # Save document
    doc_path.write_text(doc_content, encoding="utf-8")
    logger.info(f"[WEB_SEARCH:FILTERED] Document saved: {doc_path}")

    # Return summary for orchestrator
    relative_path = doc_path.relative_to(Path(workspace_path))

    return f"""## Filtered Search Results for: "{query}"

### LLM Synthesis
{synthesis if synthesis else "No synthesis available"}

### Filtering Summary
- **Kept:** {len(kept_results)}/{len(results)} results
- **Removed:** {len(removed_results)} results (irrelevant)

### Kept Results
{kept_table}

📄 **Full documentation saved to:** `{relative_path}`
   Contains: original results, filtering decisions with reasons, removed results, full content.

**Note:** The document above contains the objective truth. My synthesis is based only on kept results.
"""


async def _deep_web_research(topic: str, user_id: str, api_key: str, workspace_path: str, max_iterations: int = 5) -> str:
    """
    Iterative deep web research.

    Process:
    1. Initial broad search
    2. Identify knowledge gaps
    3. Generate targeted follow-up queries
    4. Repeat until gaps filled or max iterations
    5. Document tracks ALL sources across ALL iterations
    """
    from backend.agents.model_router import ModelRouter
    from backend.models.user import User
    from backend.database import engine
    from sqlmodel import Session

    logger.info(f"[WEB_SEARCH:DEEP] Starting deep research on: '{topic}'")

    # Resolve model
    model_identifier = "ollama::llama3.2:latest"
    with Session(engine) as session:
        user = session.get(User, user_id)
        if user and user.settings and "agent_roles" in user.settings:
            roles = user.settings["agent_roles"]
            model_identifier = roles.get("handyman") or roles.get("default") or model_identifier

    router = ModelRouter()

    # Track all sources across iterations
    all_sources: List[Dict[str, Any]] = []
    iteration_logs: List[Dict[str, Any]] = []
    knowledge_gaps: List[str] = [topic]  # Start with the main topic as a "gap"

    for iteration in range(1, max_iterations + 1):
        if not knowledge_gaps:
            logger.info(f"[WEB_SEARCH:DEEP] No more gaps at iteration {iteration}, stopping")
            break

        current_query = knowledge_gaps.pop(0)
        logger.info(f"[WEB_SEARCH:DEEP] Iteration {iteration}: '{current_query}'")

        # Search
        payload = {
            "api_key": api_key,
            "query": current_query,
            "search_depth": "advanced",  # Use advanced for deep research
            "max_results": 10,
            "include_answer": True
        }

        try:
            data = _fetch_tavily(payload)
            results = data.get("results", [])
            tavily_answer = data.get("answer", "")
        except Exception as e:
            logger.warning(f"[WEB_SEARCH:DEEP] Iteration {iteration} failed: {e}")
            iteration_logs.append({
                "iteration": iteration,
                "query": current_query,
                "status": "failed",
                "error": str(e),
                "results_count": 0,
                "new_sources": 0
            })
            continue

        # Extract facts from each result
        new_sources = []
        for res in results:
            url = res.get("url", "")
            # Check if we already have this source
            if any(s["url"] == url for s in all_sources):
                continue

            source_entry = {
                "iteration": iteration,
                "query": current_query,
                "title": res.get("title", "No title"),
                "url": url,
                "content": res.get("content", ""),
                "score": res.get("score", 0),
                "tavily_answer": tavily_answer if not all_sources else ""  # Only include for first query
            }
            new_sources.append(source_entry)
            all_sources.append(source_entry)

        # Log iteration
        iteration_logs.append({
            "iteration": iteration,
            "query": current_query,
            "status": "success",
            "results_count": len(results),
            "new_sources": len(new_sources),
            "tavily_answer": tavily_answer[:200] if tavily_answer else ""
        })

        # Identify knowledge gaps (if not last iteration)
        if iteration < max_iterations and len(knowledge_gaps) < 2:
            # Summarize what we know so far
            known_facts = "\n".join([f"- {s['title']}: {s['content'][:200]}" for s in all_sources[-10:]])

            gap_prompt = f"""You are a research assistant identifying knowledge gaps.

RESEARCH TOPIC: "{topic}"

WHAT WE KNOW SO FAR (from {len(all_sources)} sources):
{known_facts}

TASK: Identify 1-2 specific knowledge gaps or follow-up questions that would make this research more complete.
Only suggest gaps if there are genuine missing pieces. If the research seems comprehensive, say "COMPLETE".

Reply with ONLY the follow-up queries (one per line) or "COMPLETE":
"""

            try:
                response = await router.generate(
                    model_identifier=model_identifier,
                    prompt=gap_prompt,
                    options={"temperature": 0.3}
                )
                gap_response = response.get("response", "").strip()

                if "COMPLETE" not in gap_response.upper():
                    # Parse new queries
                    new_queries = [q.strip().replace("- ", "").replace("* ", "")
                                   for q in gap_response.split("\n")
                                   if q.strip() and len(q.strip()) > 10]
                    knowledge_gaps.extend(new_queries[:2])
                    logger.info(f"[WEB_SEARCH:DEEP] Identified gaps: {new_queries[:2]}")
            except Exception as e:
                logger.warning(f"[WEB_SEARCH:DEEP] Gap identification failed: {e}")

    # Generate final synthesis
    synthesis = ""
    if all_sources:
        # Build source summary for synthesis
        source_summary = ""
        for s in all_sources:
            source_summary += f"\n[{s['url']}]: {s['title']}\n{s['content'][:400]}\n"

        synthesis_prompt = f"""Based on the following sources gathered through deep research on "{topic}", provide a comprehensive synthesis.

IMPORTANT RULES:
1. Only include facts that appear in the sources below
2. Cite sources using [URL] format
3. Organize by sub-topic if applicable
4. Note any remaining uncertainties or gaps

SOURCES:
{source_summary[:8000]}

Write a detailed research synthesis:
"""

        try:
            response = await router.generate(
                model_identifier=model_identifier,
                prompt=synthesis_prompt,
                options={"temperature": 0.2}
            )
            synthesis = response.get("response", "").strip()
        except Exception as e:
            synthesis = f"(Synthesis generation failed: {e})"

    # Generate document
    doc_path = _generate_document_path(workspace_path, "deep")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Build iteration log table
    iter_table_lines = ["| Iteration | Query | Status | Results | New Sources |", "|-----------|-------|--------|---------|-------------|"]
    for log in iteration_logs:
        status_emoji = "✅" if log["status"] == "success" else "❌"
        iter_table_lines.append(f"| {log['iteration']} | {log['query'][:50]}... | {status_emoji} | {log['results_count']} | {log['new_sources']} |")
    iter_table = "\n".join(iter_table_lines)

    # Build master source table
    source_table_lines = ["| # | Iteration | Title | URL | Score |", "|---|-----------|-------|-----|-------|"]
    for i, s in enumerate(all_sources, 1):
        title = s["title"][:40]
        url = s["url"]
        source_table_lines.append(f"| {i} | {s['iteration']} | {title} | [{url[:30]}...]({url}) | {s['score']:.2f} |")
    source_table = "\n".join(source_table_lines) if all_sources else "| - | No sources found | - | - | - |"

    doc_content = f"""# Deep Web Research Report

**Generated:** {timestamp}
**Topic:** `{topic}`
**Mode:** Deep Research (llm_deep=True)
**Model Used:** {model_identifier}
**Total Iterations:** {len(iteration_logs)}
**Total Unique Sources:** {len(all_sources)}

---

## Executive Summary

### LLM Synthesis
{synthesis if synthesis else "_No synthesis generated_"}

---

## Research Statistics

- **Iterations completed:** {len(iteration_logs)}
- **Total unique sources found:** {len(all_sources)}
- **Queries explored:** {', '.join([f'"{log["query"][:30]}..."' for log in iteration_logs])}

---

## Research Iteration Log

{iter_table}

---

## Master Source Table

All unique sources discovered across all iterations:

{source_table}

---

## Detailed Iteration Reports

"""

    for log in iteration_logs:
        doc_content += f"""
### Iteration {log['iteration']}: "{log['query']}"

- **Status:** {"✅ Success" if log["status"] == "success" else "❌ Failed"}
- **Results found:** {log['results_count']}
- **New unique sources:** {log['new_sources']}
"""
        if log.get("tavily_answer"):
            doc_content += f"- **Tavily's answer:** {log['tavily_answer']}\n"
        if log.get("error"):
            doc_content += f"- **Error:** {log['error']}\n"

    doc_content += """
---

## Full Source Content

Each source with complete content for verification:

"""

    for i, s in enumerate(all_sources, 1):
        doc_content += f"""
### [{i}] {s['title']}

- **URL:** {s['url']}
- **Found in iteration:** {s['iteration']}
- **Query used:** "{s['query']}"
- **Relevance score:** {s['score']:.2f}

**Full Content:**
{s['content']}

---
"""

    doc_content += f"""
## Remaining Knowledge Gaps

"""

    if knowledge_gaps:
        for gap in knowledge_gaps:
            doc_content += f"- {gap}\n"
    else:
        doc_content += "_Research appears comprehensive - no significant gaps identified._\n"

    doc_content += f"""
---

## Metadata
- Document path: `{doc_path}`
- Model: {model_identifier}
- Max iterations configured: {max_iterations}
- Processing completed: {timestamp}
"""

    # Save document
    doc_path.write_text(doc_content, encoding="utf-8")
    logger.info(f"[WEB_SEARCH:DEEP] Document saved: {doc_path}")

    # Return summary for orchestrator
    relative_path = doc_path.relative_to(Path(workspace_path))

    # Build brief source summary
    brief_sources = "\n".join([f"| {i} | {s['title'][:40]} | [{s['url'][:30]}...]({s['url']}) |"
                               for i, s in enumerate(all_sources[:10], 1)])

    return f"""## Deep Research Results: "{topic}"

### Research Summary
- **Iterations completed:** {len(iteration_logs)}
- **Unique sources found:** {len(all_sources)}

### LLM Synthesis
{synthesis[:1000] if synthesis else "No synthesis available"}...

### Top Sources Found
| # | Title | URL |
|---|-------|-----|
{brief_sources}

{"..." if len(all_sources) > 10 else ""}

📄 **Full research documentation saved to:** `{relative_path}`
   Contains: all {len(all_sources)} sources, iteration logs, full content, knowledge gaps.

**Note:** The document contains ALL sources discovered. My synthesis is my interpretation - verify against the sources.
"""
