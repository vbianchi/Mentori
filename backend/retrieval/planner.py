import fitz  # pymupdf
from dataclasses import dataclass
from typing import List, Dict, Any, Literal
import logging

logger = logging.getLogger(__name__)

@dataclass
class PageStrategy:
    page_num: int
    action: Literal["text", "ocr", "table"]
    reason: str
    confidence: float

@dataclass
class IngestionStrategy:
    file_path: str
    is_scanned: bool
    page_strategies: List[PageStrategy]
    estimated_tokens: int

    @property
    def ocr_pages(self) -> List[int]:
        return [p.page_num for p in self.page_strategies if p.action == "ocr"]

class DocumentAnalyzer:
    """
    Analyzes a PDF to determine the best ingestion strategy.
    
    Decisions:
    - Text vs OCR: Based on text density (chars per page).
    - Table Extraction: Based on layout analysis (e.g. finding explicit grid lines or table structures).
    """
    
    def __init__(self, min_text_density: int = 50):
        self.min_text_density = min_text_density

    def analyze(self, file_path: str) -> IngestionStrategy:
        """
        Analyze the document and return an execution plan.
        """
        doc = fitz.open(file_path)
        page_strategies = []
        is_scanned_doc = True # Assume scanned until proven otherwise
        total_chars = 0
        
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text()
            char_count = len(text.strip())
            total_chars += char_count
            
            # 1. Check for Tables (Simple Heuristic for now)
            # In Phase 2, we might manually flag pages, or use simple distinct keywords/layout
            # For now, we'll focus on Scanned vs Text. 
            # Future: Use fitz.Page.find_tables() if available or heuristics
            
            # 2. Check Text Density
            if char_count > self.min_text_density:
                strategy = PageStrategy(
                    page_num=page_num,
                    action="text",
                    reason="Sufficient text layer detected",
                    confidence=1.0
                )
                is_scanned_doc = False # Found at least one good page
            else:
                strategy = PageStrategy(
                    page_num=page_num,
                    action="ocr",
                    reason="Low text density (likely image/scanned)",
                    confidence=0.9
                )
            
            page_strategies.append(strategy)
            
        return IngestionStrategy(
            file_path=file_path,
            is_scanned=is_scanned_doc,
            page_strategies=page_strategies,
            estimated_tokens=total_chars // 4 # Rough estimate
        )
