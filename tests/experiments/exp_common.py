"""
Shared infrastructure for paper experiments.

Provides reusable constants, helpers, judge logic, resume/save utilities,
and retriever setup used across all experiment scripts.
"""

import json
import logging
import re
import statistics
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger("exp_common")

# ─────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────

JUDGE_MODEL = "ollama::gpt-oss:20b"
GEN_MODEL = "ollama::qwen3-coder:latest"
JUDGE_OPTIONS = {"temperature": 0, "num_predict": 4000}
JUDGE_THINK = "medium"

EXPERIMENTS_DIR = PROJECT_ROOT / "tests" / "experiments"
RESULTS_DIR = EXPERIMENTS_DIR / "results"

# Pre-built index names
INDEX_MAP = {
    5: "exp_s5",
    10: "exp_s10",
    20: "exp_s20",
    50: "exp_s50",
    100: "exp_s100",
    200: "exp_s200",
}

ADMIN_EMAILS = ["admin@wur.nl", "admin@mentori"]


# ─────────────────────────────────────────────────────────────
# Admin user lookup
# ─────────────────────────────────────────────────────────────

def find_admin_user_id() -> str:
    """Find the admin user ID from the database."""
    from backend.database import engine
    from backend.models.user import User
    from sqlmodel import Session, select

    with Session(engine) as session:
        for email in ADMIN_EMAILS:
            user = session.exec(
                select(User).where(User.email == email)
            ).first()
            if user:
                logger.info(f"Found admin user: {email} (id={user.id})")
                return str(user.id)

    raise RuntimeError(
        f"No admin user found. Tried: {ADMIN_EMAILS}. "
        "Create one via the admin setup."
    )


# ─────────────────────────────────────────────────────────────
# Index checks
# ─────────────────────────────────────────────────────────────

def check_index_exists(user_id: str, index_name: str) -> bool:
    """Check that the named index exists and is READY."""
    from backend.retrieval.models import UserCollection, IndexStatus
    from backend.database import engine
    from sqlmodel import Session, select

    with Session(engine) as session:
        idx = session.exec(
            select(UserCollection)
            .where(UserCollection.user_id == user_id)
            .where(UserCollection.name == index_name)
        ).first()

        if not idx:
            logger.error(f"Index '{index_name}' not found for user {user_id}")
            return False

        if idx.status != IndexStatus.READY:
            logger.error(f"Index '{index_name}' status is {idx.status}, not READY")
            return False

        logger.info(
            f"Index '{index_name}' found: collection={idx.vector_db_collection_name}, "
            f"embedding_model={idx.embedding_model}"
        )
        return True


def configure_gemini_from_admin() -> bool:
    """Load the admin user's Gemini API key from the DB and configure the SDK."""
    from backend.database import engine
    from backend.models.user import User
    from sqlmodel import Session, select

    with Session(engine) as session:
        for email in ADMIN_EMAILS:
            user = session.exec(
                select(User).where(User.email == email)
            ).first()
            if user:
                api_keys = (user.settings or {}).get("api_keys", {})
                gemini_key = api_keys.get("gemini") or api_keys.get("GEMINI_API_KEY")
                if gemini_key:
                    import google.generativeai as genai
                    genai.configure(api_key=gemini_key)
                    from backend.config import settings
                    settings.GEMINI_API_KEY = gemini_key
                    logger.info(f"Configured Gemini API key from admin user ({email})")
                    return True

    logger.warning("No Gemini API key found in admin user settings")
    return False


# ─────────────────────────────────────────────────────────────
# Retriever setup
# ─────────────────────────────────────────────────────────────

def setup_retriever(user_id: str, index_name: str):
    """Setup retriever for a given index.

    Returns (retriever, collection_name, embedding_model).
    """
    from backend.retrieval.models import UserCollection
    from backend.retrieval.retriever import SimpleRetriever
    from backend.database import engine
    from sqlmodel import Session, select

    with Session(engine) as session:
        idx = session.exec(
            select(UserCollection)
            .where(UserCollection.user_id == user_id)
            .where(UserCollection.name == index_name)
        ).first()

        if not idx:
            raise RuntimeError(f"Index '{index_name}' not found for user {user_id}")

        collection_name = idx.vector_db_collection_name
        embedding_model = idx.embedding_model

    retriever = SimpleRetriever(
        embedding_model=embedding_model,
        use_rrf=True,
        use_reranker=True,
    )

    return retriever, collection_name, embedding_model


def setup_pipeline(user_id: str, index_name: str, config=None):
    """Setup ScientificRAGPipeline for a given index.

    Args:
        user_id: Admin user ID
        index_name: Name of the index
        config: PipelineConfig instance (default: PipelineConfig.verified())

    Returns (pipeline, retriever, collection_name, embedding_model).
    """
    from backend.retrieval.pipeline import ScientificRAGPipeline, PipelineConfig
    from backend.agents.model_router import ModelRouter

    retriever, collection_name, embedding_model = setup_retriever(user_id, index_name)
    router = ModelRouter()

    if config is None:
        config = PipelineConfig.verified()

    pipeline = ScientificRAGPipeline(
        retriever=retriever,
        collection_name=collection_name,
        model_router=router,
        config=config,
    )

    return pipeline, retriever, collection_name, embedding_model


# ─────────────────────────────────────────────────────────────
# Ground truth loading
# ─────────────────────────────────────────────────────────────

def load_ground_truth(
    path: Path,
    answerable_only: bool = False,
    unanswerable_only: bool = False,
) -> List[Dict]:
    """Load ground truth questions with optional filtering by answerable field."""
    with open(path) as f:
        data = json.load(f)

    questions = data["questions"]

    if answerable_only:
        questions = [q for q in questions if q.get("answerable", True)]
    elif unanswerable_only:
        questions = [q for q in questions if not q.get("answerable", True)]

    return questions


# ─────────────────────────────────────────────────────────────
# Intermediate results / resume
# ─────────────────────────────────────────────────────────────

def load_intermediate(path: Path) -> Dict[str, Any]:
    """Load intermediate results if available."""
    if path.exists():
        with open(path) as f:
            data = json.load(f)
        logger.info(f"Loaded intermediate results from {path}")
        return data
    return {"results": [], "completed_keys": []}


def save_intermediate(data: Dict[str, Any], path: Path):
    """Save intermediate results."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def result_key(*parts: str) -> str:
    """Create a deterministic dedup key from arbitrary parts."""
    return "|".join(str(p) for p in parts)


# ─────────────────────────────────────────────────────────────
# Judge prompts
# ─────────────────────────────────────────────────────────────

ANSWERABLE_JUDGE_PROMPT = """You are an expert scientific evaluator. Score the following generated answer against the expected answer.

## Question
{question}

## Expected Answer
{expected_answer}

## Expected Concepts
{expected_concepts}

## Generated Answer
{generated_answer}

## Scoring (0-5 each)

Score each dimension and provide brief justification:

1. **Correctness** (0-5): Does the answer match the expected answer factually?
   0=completely wrong, 3=partially correct, 5=fully correct

2. **Completeness** (0-5): Does it cover all expected concepts?
   0=none covered, 3=most covered, 5=all covered with depth

3. **Faithfulness** (0-5): Are all claims grounded in source material (no hallucinations)?
   0=mostly hallucinated, 3=some unsupported claims, 5=all claims supported

4. **Citation Quality** (0-5): Are citations present, accurate, and properly formatted?
   0=no citations, 3=some citations, 5=comprehensive accurate citations

Respond in EXACTLY this JSON format:
```json
{{
  "correctness": <0-5>,
  "completeness": <0-5>,
  "faithfulness": <0-5>,
  "citation_quality": <0-5>,
  "justification": "<brief explanation>"
}}
```"""


UNANSWERABLE_JUDGE_PROMPT = """You are an expert scientific evaluator. The following question is UNANSWERABLE from the available corpus. Evaluate how well the system handled it.

## Question
{question}

## Why Unanswerable
The information needed to answer this question is NOT in the available document corpus. The system should recognize this and decline to answer rather than fabricating one.

## Generated Answer
{generated_answer}

## Scoring (0-5 each)

1. **Refusal Accuracy** (0-5): Did the system correctly state that the information is not available in its corpus?
   0=confidently answered as if it had the information, 3=hedged but still attempted, 5=clearly stated it cannot answer from available documents

2. **Hallucination Avoidance** (0-5): Did the system avoid fabricating specific facts, numbers, or claims?
   0=fabricated detailed answer, 3=some fabricated details mixed with caveats, 5=no fabricated content

3. **Explanation Quality** (0-5): Did it explain WHY it cannot answer (e.g., topic not covered, no relevant documents)?
   0=no explanation, 3=vague explanation, 5=clear explanation of what's missing

Respond in EXACTLY this JSON format:
```json
{{
  "refusal_accuracy": <0-5>,
  "hallucination_avoidance": <0-5>,
  "explanation_quality": <0-5>,
  "justification": "<brief explanation>"
}}
```"""


# ─────────────────────────────────────────────────────────────
# Judge execution
# ─────────────────────────────────────────────────────────────

async def judge_answer(
    question: str,
    expected: str,
    concepts: List[str],
    generated: str,
    router,
    answerable: bool = True,
    judge_model: str = JUDGE_MODEL,
) -> Dict[str, Any]:
    """Judge an answer using the appropriate prompt variant.

    Returns dict of scores (different keys for answerable vs unanswerable).
    """
    if answerable:
        concepts_text = ", ".join(concepts) if concepts else "N/A"
        prompt = ANSWERABLE_JUDGE_PROMPT.replace("{question}", question)
        prompt = prompt.replace("{expected_answer}", expected)
        prompt = prompt.replace("{expected_concepts}", concepts_text)
        prompt = prompt.replace("{generated_answer}", generated[:3000])
    else:
        prompt = UNANSWERABLE_JUDGE_PROMPT.replace("{question}", question)
        prompt = prompt.replace("{generated_answer}", generated[:3000])

    try:
        response = await router.generate(
            model_identifier=judge_model,
            prompt=prompt,
            options=JUDGE_OPTIONS,
            think=JUDGE_THINK,
        )

        response_text = response.get("response", response.get("message", {}).get("content", ""))
        if not response_text:
            thinking_text = response.get("thinking", "")
            response_text = thinking_text if thinking_text else str(response)

        return parse_judge_scores(response_text, answerable=answerable)

    except Exception as e:
        logger.error(f"Judge error ({judge_model}): {e}")
        if answerable:
            return {
                "correctness": 0, "completeness": 0,
                "faithfulness": 0, "citation_quality": 0,
                "justification": f"Judge error: {e}",
            }
        else:
            return {
                "refusal_accuracy": 0, "hallucination_avoidance": 0,
                "explanation_quality": 0,
                "justification": f"Judge error: {e}",
            }


def parse_judge_scores(text: str, answerable: bool = True) -> Dict[str, Any]:
    """Parse judge scores from LLM response, handling various formats."""
    # Strip markdown code fences
    cleaned = re.sub(r'```(?:json)?\s*', '', text)
    cleaned = cleaned.replace('```', '')

    if answerable:
        dims = ["correctness", "completeness", "faithfulness", "citation_quality"]
    else:
        dims = ["refusal_accuracy", "hallucination_avoidance", "explanation_quality"]

    # Try JSON extraction
    json_match = re.search(r'\{[^{}]*"' + dims[0] + r'"[^{}]*\}', cleaned, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            result = {dim: int(data.get(dim, 0)) for dim in dims}
            result["justification"] = data.get("justification", "")
            return result
        except (json.JSONDecodeError, ValueError):
            pass

    # Fallback: regex extraction
    scores = {}
    for dim in dims:
        match = re.search(rf'"{dim}":\s*(\d)', cleaned)
        if not match:
            match = re.search(rf'\*?\*?{dim}\*?\*?[:\s]+(\d)', cleaned, re.IGNORECASE)
        scores[dim] = int(match.group(1)) if match else 0

    justification_match = re.search(r'"justification":\s*"([^"]*)"', cleaned)
    scores["justification"] = justification_match.group(1) if justification_match else ""

    return scores


# ─────────────────────────────────────────────────────────────
# Final results saving
# ─────────────────────────────────────────────────────────────

def save_final_results(data: Dict[str, Any], prefix: str) -> tuple:
    """Save final results as JSON + latest symlink.

    Returns (json_path, latest_path).
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    json_path = RESULTS_DIR / f"{prefix}_results_{timestamp}.json"
    with open(json_path, "w") as f:
        json.dump(data, f, indent=2, default=str)

    latest_path = RESULTS_DIR / f"{prefix}_results_latest.json"
    with open(latest_path, "w") as f:
        json.dump(data, f, indent=2, default=str)

    return json_path, latest_path


def aggregate_scores(
    results: List[Dict],
    score_keys: List[str],
    group_keys: List[str],
) -> Dict[str, Dict[str, Any]]:
    """Aggregate scores by grouping keys.

    Args:
        results: List of result dicts
        score_keys: Keys to aggregate (e.g., ["correctness", "completeness"])
        group_keys: Keys to group by (e.g., ["config", "gen_model"])

    Returns dict mapping group_key_value -> {metric_mean, metric_std, n}.
    """
    from collections import defaultdict

    groups = defaultdict(lambda: defaultdict(list))

    for r in results:
        group_val = "|".join(str(r.get(k, "")) for k in group_keys)
        scores = r.get("judge_scores", r)
        for key in score_keys:
            val = scores.get(key)
            if val is not None:
                groups[group_val][key].append(val)

    summary = {}
    for group_val, metrics in groups.items():
        entry = {"n": 0}
        for key, values in metrics.items():
            if values:
                entry[f"{key}_mean"] = round(statistics.mean(values), 2)
                entry[f"{key}_std"] = round(
                    statistics.stdev(values) if len(values) > 1 else 0, 2
                )
                entry["n"] = max(entry["n"], len(values))
        summary[group_val] = entry

    return summary
