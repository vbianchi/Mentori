"""
Page-by-page VLM analyzer for comprehensive document extraction.

Analyzes EVERY page of a document with a unified prompt that extracts:
- Metadata (title, authors, abstract, keywords, journal, DOI)
- Figures with descriptions
- Tables with descriptions
- References (parsed bibliography)
- Equations
- Section headings

The VLM decides what's relevant on each page - no assumptions about structure.
"""

import json
import logging
import os
import base64
import tempfile
from typing import List, Optional, Dict, Any
from pathlib import Path

import aiohttp
import httpx
from pdf2image import convert_from_path

from backend.retrieval.schema.document import (
    PageAnalysisResult,
    FigureDescription,
    TableDescription,
    EquationDescription,
    Reference,
)

logger = logging.getLogger(__name__)


# The unified prompt for analyzing any page
PAGE_ANALYSIS_PROMPT = '''Analyze this document page and extract ALL relevant information present.

Return a JSON object with ONLY the fields that have content on this page. Omit empty fields.

{
  "page_type": "title|content|figures|tables|references|appendix|mixed",

  "metadata": {
    "title": "Full document title if visible",
    "authors": ["Author One", "Author Two"],
    "abstract": "Full abstract text if this page contains it",
    "keywords": ["keyword1", "keyword2"],
    "journal": "Journal name if visible",
    "doi": "DOI if visible (10.xxxx/...)",
    "date": "Publication date if visible"
  },

  "figures": [
    {
      "figure_id": "Figure 1",
      "caption": "Caption text if present",
      "description": "Detailed description of what the figure shows - data trends, key findings, visual elements",
      "figure_type": "plot|heatmap|diagram|microscopy|photo|schematic|flowchart|other"
    }
  ],

  "tables": [
    {
      "table_id": "Table 1",
      "caption": "Caption text if present",
      "description": "What data the table contains, key findings, structure",
      "columns": ["Column1", "Column2"],
      "row_count": 10
    }
  ],

  "equations": [
    {
      "equation_id": "Eq. 1",
      "latex": "E = mc^2",
      "description": "What this equation represents"
    }
  ],

  "references": [
    {
      "ref_id": "[1]",
      "authors": ["Smith J", "Doe A"],
      "title": "Title of the referenced paper",
      "journal": "Journal Name",
      "year": "2023",
      "volume": "10",
      "pages": "1-10",
      "doi": "10.xxxx/..."
    }
  ],

  "section_headings": ["Introduction", "Methods", "2.1 Data Collection"]
}

IMPORTANT:
- Only include fields that have actual content on THIS page
- For figures/tables, provide detailed descriptions of what they show
- For references, parse each reference into structured fields
- Return valid JSON only, no markdown or explanations'''


class PageAnalyzer:
    """
    Analyzes document pages using VLM to extract structured information.

    Processes every page with a unified prompt, letting the VLM decide
    what's relevant on each page.
    """

    def __init__(
        self,
        model_name: str,
        ollama_url: str = None,
        dpi: int = 200
    ):
        """
        Initialize the page analyzer.

        Args:
            model_name: Ollama model name (e.g., "deepseek-ocr:3b")
            ollama_url: Ollama API URL
            dpi: DPI for PDF to image conversion
        """
        self.model_name = model_name
        self.ollama_url = ollama_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.dpi = dpi
        self._available = False

        # Token tracking
        self._total_input_tokens = 0
        self._total_output_tokens = 0

    async def check_availability(self) -> bool:
        """Check if the VLM model is available."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_url}/api/tags") as response:
                    if response.status != 200:
                        return False

                    data = await response.json()
                    models = [m['name'] for m in data.get('models', [])]

                    is_found = any(self.model_name in m for m in models)
                    self._available = is_found

                    if is_found:
                        logger.info(f"PageAnalyzer VLM available: {self.model_name}")
                    else:
                        logger.warning(f"PageAnalyzer VLM not found: {self.model_name}")

                    return is_found
        except Exception as e:
            logger.error(f"Failed to check VLM availability: {e}")
            return False

    def get_token_usage(self) -> Dict[str, int]:
        """Get accumulated token usage."""
        return {
            "input": self._total_input_tokens,
            "output": self._total_output_tokens,
            "total": self._total_input_tokens + self._total_output_tokens
        }

    def reset_token_usage(self):
        """Reset token counters."""
        self._total_input_tokens = 0
        self._total_output_tokens = 0

    def _sync_vlm_call(
        self,
        payload: dict,
        page_number: int,
        max_retries: int = 3
    ) -> Optional[dict]:
        """
        Synchronous VLM call using httpx library.

        This runs in a thread pool to avoid event loop contention that causes
        "Connection closed" errors when running inside FastAPI BackgroundTasks.

        Args:
            payload: The request payload for Ollama
            page_number: Page number for logging
            max_retries: Maximum retry attempts

        Returns:
            Response JSON dict or None if failed
        """
        import time

        last_error = None
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    logger.info(f"Retry {attempt}: Retrying VLM call for page {page_number}...")
                    time.sleep(2)

                # Use httpx sync client with long timeout (10 minutes)
                # Create fresh client for each request to avoid connection reuse issues
                with httpx.Client(timeout=httpx.Timeout(600.0, connect=30.0)) as client:
                    response = client.post(
                        f"{self.ollama_url}/api/generate",
                        json=payload
                    )

                if response.status_code != 200:
                    error_text = response.text

                    # Check for retryable errors (Ollama batch/sequence issues)
                    if "SameBatch" in error_text or "sequence" in error_text.lower():
                        last_error = error_text
                        wait_time = (attempt + 1) * 5
                        logger.warning(
                            f"Ollama SameBatch error on page {page_number}, "
                            f"will retry {attempt + 1}/{max_retries} after {wait_time}s"
                        )
                        time.sleep(wait_time)
                        continue

                    logger.error(f"VLM call failed for page {page_number}: {error_text}")
                    return None

                return response.json()

            except httpx.TimeoutException:
                last_error = "timeout"
                wait_time = (attempt + 1) * 5
                logger.warning(
                    f"VLM timeout on page {page_number}, "
                    f"retry {attempt + 1}/{max_retries} after {wait_time}s"
                )
                time.sleep(wait_time)
                continue

            except Exception as e:
                last_error = str(e)
                logger.error(f"VLM request failed for page {page_number}: {e}")
                if attempt < max_retries - 1:
                    time.sleep((attempt + 1) * 5)
                    continue
                break

        logger.error(f"VLM analysis failed after {max_retries} retries for page {page_number}: {last_error}")
        return None

    async def analyze_page(
        self,
        image_path: str,
        page_number: int,
        ocr_text: Optional[str] = None,
        max_retries: int = 3
    ) -> PageAnalysisResult:
        """
        Analyze a single page image with VLM.

        Args:
            image_path: Path to page image file
            page_number: 1-indexed page number
            ocr_text: Optional OCR text for this page (for validation)
            max_retries: Maximum retry attempts for transient errors

        Returns:
            PageAnalysisResult with extracted information
        """
        import asyncio

        if not self._available:
            if not await self.check_availability():
                logger.warning(f"VLM not available, returning empty result for page {page_number}")
                return PageAnalysisResult(page_number=page_number, ocr_text=ocr_text)

        # Read and encode image
        try:
            with open(image_path, "rb") as img_file:
                b64_image = base64.b64encode(img_file.read()).decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to read page image: {e}")
            return PageAnalysisResult(page_number=page_number, ocr_text=ocr_text)

        # Build payload
        # CRITICAL: Use num_keep=0 to disable context caching, which causes SameBatch errors
        payload = {
            "model": self.model_name,
            "prompt": PAGE_ANALYSIS_PROMPT,
            "images": [b64_image],
            "stream": False,
            "keep_alive": "5m",  # Keep model loaded between pages
            "options": {
                "temperature": 0.1,  # Low temp for factual extraction
                "num_ctx": 4096,  # Limit context window
                "num_keep": 0,  # CRITICAL: Don't keep any context between requests (fixes SameBatch)
                "num_batch": 512,  # Reasonable batch size
            }
        }

        # Run synchronous HTTP call in thread pool to avoid event loop contention
        # This fixes "Connection closed" errors when running in FastAPI BackgroundTasks
        logger.info(f"Analyzing page {page_number} with VLM (running in thread pool)...")
        result = await asyncio.to_thread(
            self._sync_vlm_call,
            payload,
            page_number,
            max_retries
        )

        if result is None:
            return PageAnalysisResult(page_number=page_number, ocr_text=ocr_text)

        # Track tokens
        self._total_input_tokens += result.get("prompt_eval_count", 0)
        self._total_output_tokens += result.get("eval_count", 0)

        # Parse response
        vlm_response = result.get("response", "")
        return self._parse_vlm_response(vlm_response, page_number, ocr_text)

    def _parse_vlm_response(
        self,
        response: str,
        page_number: int,
        ocr_text: Optional[str]
    ) -> PageAnalysisResult:
        """Parse VLM JSON response into PageAnalysisResult."""
        import re

        result = PageAnalysisResult(page_number=page_number, ocr_text=ocr_text)

        if not response or not response.strip():
            logger.warning(f"Empty VLM response for page {page_number}")
            return result

        # Try to extract JSON from response with multiple strategies
        json_str = response.strip()

        # Strategy 1: Remove thinking tags (common in some models)
        # Handles <think>...</think>, <thinking>...</thinking>, etc.
        json_str = re.sub(r'<think(?:ing)?[^>]*>.*?</think(?:ing)?>', '', json_str, flags=re.DOTALL | re.IGNORECASE)

        # Strategy 2: Remove markdown code blocks
        if "```" in json_str:
            # Extract content between ```json and ``` or just ``` and ```
            match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', json_str)
            if match:
                json_str = match.group(1)
            else:
                # Fallback: remove all ``` lines
                lines = json_str.split("\n")
                json_str = "\n".join(line for line in lines if not line.strip().startswith("```"))

        # Strategy 3: Find JSON object by looking for { ... }
        json_str = json_str.strip()
        if not json_str.startswith("{"):
            # Try to find JSON object in the response
            match = re.search(r'\{[\s\S]*\}', json_str)
            if match:
                json_str = match.group(0)

        # Try to parse
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            # Log the actual response for debugging
            logger.warning(f"Failed to parse VLM JSON for page {page_number}: {e}")
            logger.warning(f"Raw response (first 500 chars): {response[:500]}")
            logger.warning(f"Cleaned response (first 500 chars): {json_str[:500]}")
            return result

        # Extract page type
        result.page_type = data.get("page_type", "content")

        # Extract metadata
        metadata = data.get("metadata", {})
        if metadata:
            result.title = metadata.get("title")
            result.authors = metadata.get("authors", [])
            result.abstract = metadata.get("abstract")
            result.keywords = metadata.get("keywords", [])
            result.journal = metadata.get("journal")
            result.doi = metadata.get("doi")
            result.date = metadata.get("date")

        # Extract figures
        for fig_data in data.get("figures", []):
            fig = FigureDescription(
                figure_id=fig_data.get("figure_id", f"Figure (page {page_number})"),
                page=page_number,
                caption=fig_data.get("caption"),
                description=fig_data.get("description", ""),
                figure_type=fig_data.get("figure_type")
            )
            result.figures.append(fig)

        # Extract tables
        for table_data in data.get("tables", []):
            table = TableDescription(
                table_id=table_data.get("table_id", f"Table (page {page_number})"),
                page=page_number,
                caption=table_data.get("caption"),
                description=table_data.get("description", ""),
                columns=table_data.get("columns", []),
                row_count=table_data.get("row_count")
            )
            result.tables.append(table)

        # Extract equations
        for eq_data in data.get("equations", []):
            eq = EquationDescription(
                equation_id=eq_data.get("equation_id", f"Eq. (page {page_number})"),
                page=page_number,
                latex=eq_data.get("latex"),
                description=eq_data.get("description", "")
            )
            result.equations.append(eq)

        # Extract references
        for ref_data in data.get("references", []):
            ref = Reference(
                ref_id=ref_data.get("ref_id", ""),
                authors=ref_data.get("authors", []),
                title=ref_data.get("title"),
                journal=ref_data.get("journal"),
                year=ref_data.get("year"),
                volume=ref_data.get("volume"),
                pages=ref_data.get("pages"),
                doi=ref_data.get("doi"),
                pmid=ref_data.get("pmid"),
                raw_text=ref_data.get("raw_text", "")
            )
            result.references.append(ref)

        # Extract section headings
        result.section_headings = data.get("section_headings", [])

        logger.debug(
            f"Page {page_number}: type={result.page_type}, "
            f"figs={len(result.figures)}, tables={len(result.tables)}, "
            f"refs={len(result.references)}"
        )

        return result

    async def analyze_pdf(
        self,
        pdf_path: str,
        ocr_texts: Optional[List[str]] = None,
        max_concurrent: int = 2
    ) -> List[PageAnalysisResult]:
        """
        Analyze all pages of a PDF document with parallel processing.

        Args:
            pdf_path: Path to PDF file
            ocr_texts: Optional list of OCR text per page (for validation)
            max_concurrent: Maximum concurrent page analyses (default 2)
                           Set to 1 for sequential processing.

        Returns:
            List of PageAnalysisResult, one per page (ordered by page number)
        """
        import asyncio

        results = []

        with tempfile.TemporaryDirectory() as temp_dir:
            # Convert PDF to images
            try:
                images = convert_from_path(pdf_path, dpi=self.dpi)
                logger.info(f"Converted {len(images)} pages from {Path(pdf_path).name}")
            except Exception as e:
                logger.error(f"Failed to convert PDF to images: {e}")
                return results

            # Save all images first
            page_data = []
            for i, image in enumerate(images):
                page_num = i + 1
                page_path = os.path.join(temp_dir, f"page_{page_num}.png")
                image.save(page_path, "PNG")
                ocr_text = ocr_texts[i] if ocr_texts and i < len(ocr_texts) else None
                page_data.append((page_path, page_num, ocr_text))

            # Process pages with limited concurrency
            # Ollama queues requests internally, so we can overlap upload/processing
            semaphore = asyncio.Semaphore(max_concurrent)

            async def analyze_with_semaphore(page_path: str, page_num: int, ocr_text: Optional[str]):
                async with semaphore:
                    logger.info(f"Starting analysis of page {page_num}/{len(images)}")
                    result = await self.analyze_page(page_path, page_num, ocr_text)
                    logger.info(f"Completed page {page_num}/{len(images)}")
                    return result

            # Run all pages concurrently (semaphore limits actual parallelism)
            tasks = [
                analyze_with_semaphore(page_path, page_num, ocr_text)
                for page_path, page_num, ocr_text in page_data
            ]
            results = await asyncio.gather(*tasks)

            logger.info(f"Analyzed all {len(images)} pages")

        return list(results)


async def create_page_analyzer(agent_roles: Dict[str, str]) -> Optional[PageAnalyzer]:
    """
    Factory function to create a PageAnalyzer from user agent configuration.

    Args:
        agent_roles: User's agent_roles config, e.g., {"vision": "ollama::qwen-vl:latest"}

    Returns:
        PageAnalyzer if VLM is configured and available, else None
    """
    model_identifier = agent_roles.get("vision")
    
    # Try preferred model first
    if model_identifier:
        if "::" in model_identifier:
            provider, model_name = model_identifier.split("::", 1)
        else:
            provider = "ollama"
            model_name = model_identifier

        if provider.lower() == "ollama":
            ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            analyzer = PageAnalyzer(model_name=model_name, ollama_url=ollama_url)
            if await analyzer.check_availability():
                return analyzer
    
    # Fallback to DEFAULT role
    logger.warning("Vision agent unavailable or missing. Falling back to DEFAULT role.")
    default_model = agent_roles.get("default")
    if default_model:
        if "::" in default_model:
            provider, model_name = default_model.split("::", 1)
        else:
            provider = "ollama"
            model_name = default_model
            
        if provider.lower() == "ollama":
            ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            analyzer = PageAnalyzer(model_name=model_name, ollama_url=ollama_url)
            if await analyzer.check_availability():
                logger.info(f"Using DEFAULT role for page analysis: {model_name}")
                return analyzer

    return None


