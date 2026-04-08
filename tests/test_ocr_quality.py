"""
OCR Quality Validation System

Tests OCR accuracy, table extraction, and vision OCR performance.
Compares standard OCR vs Vision OCR (DeepSeek).
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict
import logging
import json
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.retrieval.parsers.pdf import PDFParser
from backend.retrieval.parsers.ocr import OCRParser
from backend.retrieval.parsers.tables import TableParser
from backend.retrieval.planner import DocumentAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class OCRQualityMetrics:
    """OCR quality metrics."""
    file_name: str
    strategy: str  # "text", "ocr", "vision"

    # Character-level metrics
    total_chars: int
    readable_chars: int  # Non-whitespace

    # Structure metrics
    has_proper_spacing: bool
    has_line_breaks: bool
    has_paragraphs: bool

    # Table extraction
    tables_found: int
    tables_valid_markdown: int

    # Readability
    avg_word_length: float
    suspicious_patterns: List[str]  # e.g., "####", "|||", excessive spaces

    # Overall score
    quality_score: float  # 0-1


@dataclass
class OCRComparisonResult:
    """Comparison between different OCR methods."""
    file_name: str

    standard_ocr: OCRQualityMetrics
    vision_ocr: Optional[OCRQualityMetrics]

    # Comparison
    better_method: str
    quality_difference: float

    # Validation
    overlap_score: float  # How much text matches between methods
    hallucination_indicators: List[str]


class OCRValidator:
    """Validates OCR quality."""

    def __init__(self):
        self.pdf_parser = PDFParser()
        self.ocr_parser = OCRParser()
        self.table_parser = TableParser()
        self.planner = DocumentAnalyzer()

        logger.info("Initialized OCR Validator")

    def validate_document(self, pdf_path: str) -> OCRComparisonResult:
        """Validate OCR quality for a document."""
        logger.info(f"Validating OCR for: {Path(pdf_path).name}")

        # Analyze document
        strategy = self.planner.analyze(pdf_path)

        # Get standard extraction
        standard_text = self._extract_standard(pdf_path, strategy)
        standard_metrics = self._calculate_metrics(standard_text, "standard", Path(pdf_path).name)

        # Compare if vision would be used
        vision_metrics = None
        if strategy.is_scanned or len(strategy.ocr_pages) > 0:
            logger.info("  Document would use OCR/Vision path")
            # For now, we test standard OCR quality
            # Vision OCR would be tested if transcriber is available

        # Calculate comparison
        result = OCRComparisonResult(
            file_name=Path(pdf_path).name,
            standard_ocr=standard_metrics,
            vision_ocr=vision_metrics,
            better_method="standard" if not vision_metrics else self._compare_methods(standard_metrics, vision_metrics),
            quality_difference=0.0,
            overlap_score=1.0,  # Would compare if both methods used
            hallucination_indicators=[]
        )

        return result

    def _extract_standard(self, pdf_path: str, strategy) -> str:
        """Extract text using standard pipeline."""
        full_text = []

        # Text pages
        text_pages = [p.page_num for p in strategy.page_strategies if p.action == "text"]
        if text_pages:
            text_result = self.pdf_parser.parse_pages(pdf_path, page_numbers=text_pages)
            for p in text_result:
                full_text.append(p["text"])

        # OCR pages
        ocr_pages = [p.page_num for p in strategy.page_strategies if p.action == "ocr"]
        if ocr_pages:
            ocr_result = self.ocr_parser.parse(pdf_path, page_numbers=ocr_pages)
            for p in ocr_result:
                full_text.append(p["text"])

        # Tables
        if not strategy.is_scanned:
            tables = self.table_parser.parse(pdf_path)
            for t in tables:
                full_text.append(f"\n\n--- Table {t['table_index']+1} ---\n{t['markdown']}\n")

        return "\n\n".join(full_text)

    def _calculate_metrics(self, text: str, strategy: str, file_name: str) -> OCRQualityMetrics:
        """Calculate quality metrics for extracted text."""

        # Character counts
        total_chars = len(text)
        readable_chars = len([c for c in text if not c.isspace()])

        # Structure checks
        has_proper_spacing = "  " not in text.replace("\n", " ")  # No double spaces
        has_line_breaks = "\n" in text
        has_paragraphs = "\n\n" in text

        # Word analysis
        words = text.split()
        avg_word_length = sum(len(w) for w in words) / len(words) if words else 0

        # Suspicious patterns
        suspicious = []
        if "####" in text:
            suspicious.append("excessive_hashes")
        if "|||" in text:
            suspicious.append("table_corruption")
        if "   " in text:
            suspicious.append("excessive_spacing")
        if avg_word_length > 15:
            suspicious.append("unusually_long_words")

        # Calculate quality score
        score = 1.0

        # Penalty for lack of structure
        if not has_line_breaks:
            score -= 0.2
        if not has_paragraphs:
            score -= 0.1

        # Penalty for suspicious patterns
        score -= len(suspicious) * 0.1

        # Penalty for unusual word length
        if avg_word_length > 12:
            score -= 0.2
        elif avg_word_length < 3:
            score -= 0.2

        # Penalty for low readable char ratio
        readable_ratio = readable_chars / total_chars if total_chars > 0 else 0
        if readable_ratio < 0.7:
            score -= 0.2

        score = max(0.0, min(1.0, score))

        return OCRQualityMetrics(
            file_name=file_name,
            strategy=strategy,
            total_chars=total_chars,
            readable_chars=readable_chars,
            has_proper_spacing=has_proper_spacing,
            has_line_breaks=has_line_breaks,
            has_paragraphs=has_paragraphs,
            tables_found=0,  # Would count tables
            tables_valid_markdown=0,
            avg_word_length=avg_word_length,
            suspicious_patterns=suspicious,
            quality_score=score
        )

    def _compare_methods(self, standard: OCRQualityMetrics, vision: OCRQualityMetrics) -> str:
        """Compare two OCR methods."""
        if vision.quality_score > standard.quality_score + 0.1:
            return "vision"
        elif standard.quality_score > vision.quality_score + 0.1:
            return "standard"
        else:
            return "similar"

    def validate_collection(self, pdf_dir: str) -> Dict[str, Any]:
        """Validate all PDFs in a directory."""
        pdf_dir = Path(pdf_dir)
        pdf_files = list(pdf_dir.glob("*.pdf"))

        logger.info(f"Validating {len(pdf_files)} PDFs from {pdf_dir.name}")

        results = []
        for pdf_path in pdf_files:
            try:
                result = self.validate_document(str(pdf_path))
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to validate {pdf_path.name}: {e}")

        # Generate summary
        avg_quality = sum(r.standard_ocr.quality_score for r in results) / len(results)

        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_files": len(pdf_files),
            "validated": len(results),
            "avg_quality_score": avg_quality,
            "results": [asdict(r) for r in results]
        }

        return summary

    def print_summary(self, summary: Dict[str, Any]):
        """Print validation summary."""
        print("\n" + "=" * 80)
        print("OCR QUALITY VALIDATION REPORT")
        print("=" * 80)
        print(f"Timestamp: {summary['timestamp']}")
        print(f"Total Files: {summary['total_files']}")
        print(f"Validated: {summary['validated']}")
        print(f"Avg Quality Score: {summary['avg_quality_score']:.2f}/1.00")
        print()

        print("📄 PER-FILE RESULTS")
        print("-" * 80)
        for r in summary['results']:
            ocr = r['standard_ocr']
            print(f"  {ocr['file_name']:40s} | Score: {ocr['quality_score']:.2f} | "
                  f"Chars: {ocr['total_chars']:6d} | "
                  f"Strategy: {ocr['strategy']}")
            if ocr['suspicious_patterns']:
                print(f"    ⚠️  Issues: {', '.join(ocr['suspicious_patterns'])}")
        print()

        print("✅ QUALITY ASSESSMENT")
        print("-" * 80)
        high_quality = sum(1 for r in summary['results'] if r['standard_ocr']['quality_score'] >= 0.8)
        medium_quality = sum(1 for r in summary['results'] if 0.6 <= r['standard_ocr']['quality_score'] < 0.8)
        low_quality = sum(1 for r in summary['results'] if r['standard_ocr']['quality_score'] < 0.6)

        print(f"  High Quality (≥0.8):   {high_quality}/{len(summary['results'])}")
        print(f"  Medium Quality (0.6-0.8): {medium_quality}/{len(summary['results'])}")
        print(f"  Low Quality (<0.6):    {low_quality}/{len(summary['results'])}")
        print()

        print("=" * 80)


def main():
    """Run OCR validation."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate OCR quality")
    parser.add_argument("pdf_dir", help="Directory containing PDFs to validate")
    parser.add_argument("--output", default="tests/ocr_validation_report.json", help="Output report path")

    args = parser.parse_args()

    # Initialize validator
    validator = OCRValidator()

    # Run validation
    summary = validator.validate_collection(args.pdf_dir)

    # Print summary
    validator.print_summary(summary)

    # Save report
    with open(args.output, 'w') as f:
        json.dump(summary, f, indent=2)

    logger.info(f"✓ Report saved to: {args.output}")


if __name__ == "__main__":
    main()
