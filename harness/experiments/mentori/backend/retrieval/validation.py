from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)

class HybridValidator:
    """
    Validates and merges VLM transcription with Tesseract OCR grounding.
    """
    
    def validate(self, vlm_text: str, ocr_text: str) -> str:
        """
        Smart Merge of VLM (Rich) and OCR (Grounding) outputs.
        
        Strategy:
        1. Calculate Similarity.
        2. If high similarity (> 0.85): Trust VLM (it's likely just better formatting).
        3. If low similarity: 
           - Check if VLM has *more* content (likely figure descriptions).
           - Check if VLM is missing content (hallucination/omission).
           - MERGE: Return VLM text + Appendix of missing OCR text if significant.
           
        Args:
            vlm_text: Output from TranscriberAgent (Markdown).
            ocr_text: Output from Tesseract (Raw Text).
            
        Returns:
            str: The final, safest representation of the text.
        """
        
        # Normalize for comparison
        clean_vlm = " ".join(vlm_text.split())
        clean_ocr = " ".join(ocr_text.split())
        
        similarity = SequenceMatcher(None, clean_vlm, clean_ocr).ratio()
        
        logger.info(f"Hybrid Validation Similarity: {similarity:.2f}")
        
        if similarity > 0.85:
            # High confidence, trust the VLM's superior formatting
            return vlm_text
            
        # If disparate, we want to keep the "Richness" of VLM but warn about missing text.
        # Simple heuristic: If OCR has significantly more characters, VLM might have hallucinated/truncated.
        
        len_diff = len(clean_ocr) - len(clean_vlm)
        if len_diff > 100: # Arbitrary threshold for "Significant missing text"
            warning = "\n\n> [!WARNING] Grounding Alert\n> The vision model may have missed some text detected by OCR. See below:\n\n"
            return vlm_text + warning + "### OCR Appendix\n" + ocr_text
            
        # Otherwise, trust the VLM (it might have described a graph that OCR couldn't read, 
        # hence low similarity but valid new info)
        return vlm_text
