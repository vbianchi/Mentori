
import asyncio
import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure we can import backend modules
sys.path.append("/app")

from backend.retrieval.extractors.page_analyzer import create_page_analyzer
from backend.retrieval.parsers.pdf import PDFParser
from pdf2image import convert_from_path
import tempfile

TEST_PDF_SOURCE = "tests/test_files_rag/papers/fgene-07-00075.pdf"

async def run_single_page_test():
    """
    Isolate the VLM analysis for the first page.
    """
    print(f"Testing Single Page Analysis for {TEST_PDF_SOURCE}")
    
    # 1. Setup Configuration with VISION role
    agent_roles = {
        "default": "ollama::llama3.2:latest",
        "transcriber": "ollama::llama3.2-vision:latest",
        "vision": "ollama::qwen3-vl:4b"  # Switched to 4b as pulled by user 
    }
    
    # 2. Initialize Page Analyzer
    print(f"Initializing PageAnalyzer with roles: {agent_roles}...")
    analyzer = await create_page_analyzer(agent_roles)
    
    if not analyzer:
        print("FAILED: Could not create PageAnalyzer. Check agent roles and availability.")
        return

    print(f"SUCCESS: PageAnalyzer created. Model: {analyzer.model_name}")
    
    # 3. Prepare Image (First Page Only)
    print("Converting PDF first page to image...")
    if not os.path.exists(TEST_PDF_SOURCE):
        print(f"ERROR: File not found at {TEST_PDF_SOURCE}")
        return

    # Use static path for verification
    debug_dir = Path("/app/tests/debug_output")
    debug_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        images = convert_from_path(TEST_PDF_SOURCE, dpi=72, first_page=1, last_page=1)
        if not images:
            print("ERROR: No images converted.")
            return
        
        page_path = debug_dir / "page_1.png"
        images[0].save(page_path, "PNG")
        print(f"Page 1 saved to {page_path}")
        
        # 4. Run Analysis
        print("Running VLM Analysis on Page 1...")
        result = await analyzer.analyze_page(
            image_path=str(page_path),
            page_number=1,
            ocr_text="<Mock OCR Text for Validation>" 
        )
            
        # 5. Output Results
        print("\n" + "="*50)
        print("ANALYSIS RESULT (Page 1)")
        print("="*50)
        print(f"Page Type: {result.page_type}")
        print(f"Title: {result.title}")
        print(f"Authors: {result.authors}")
        print(f"Abstract: {result.abstract[:100]}..." if result.abstract else "Abstract: None")
        print(f"Figures Found: {len(result.figures)}")
        print(f"Tables Found: {len(result.tables)}")
        print("="*50 + "\n")
        
        if result.title:
            print("VERIFICATION PASSED: VLM successfully extracted metadata.")
        else:
            print("VERIFICATION WARNING: VLM ran but extracted no title.")
            
    except Exception as e:
        print(f"ERROR during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Ensure correct OLLAMA URL inside container
    # os.environ["OLLAMA_BASE_URL"] = "http://host.docker.internal:11434" # Should be set by Docker, but just in case
    asyncio.run(run_single_page_test())
