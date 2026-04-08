"""
Debug tests for Ollama Vision Model issues.

Run with: uv run python tests/test_vision_debug.py

This script tests the vision model in isolation to identify:
1. API connectivity issues
2. Model availability
3. Image encoding issues
4. Prompt/response issues
5. Timeout/performance issues
"""

import asyncio
import aiohttp
import base64
import json
import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configuration
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
VISION_MODEL = os.getenv("VISION_MODEL", "qwen3-vl:8b")  # Change to your model


def create_test_image_base64():
    """Create a simple test image using PIL for proper PNG encoding."""
    try:
        from PIL import Image
        import io

        # Create a small 100x100 test image with some text-like content
        img = Image.new('RGB', (100, 100), color='white')

        # Draw some simple shapes to give the model something to "see"
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.rectangle([10, 10, 90, 30], fill='black')
        draw.text((20, 40), "TEST", fill='black')
        draw.rectangle([10, 60, 90, 90], outline='blue', width=2)

        # Save to bytes
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        return base64.b64encode(buffer.read()).decode("utf-8")
    except ImportError:
        # Fallback: use a known-good minimal PNG
        # This is a valid 1x1 white pixel PNG
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        return base64.b64encode(png_data).decode("utf-8")


async def test_1_ollama_connectivity():
    """Test 1: Basic Ollama API connectivity."""
    print("\n" + "="*60)
    print("TEST 1: Ollama API Connectivity")
    print("="*60)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{OLLAMA_URL}/api/tags",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    models = [m['name'] for m in data.get('models', [])]
                    print(f"✓ Connected to Ollama at {OLLAMA_URL}")
                    print(f"  Available models: {len(models)}")
                    for m in models[:10]:
                        print(f"    - {m}")
                    if len(models) > 10:
                        print(f"    ... and {len(models) - 10} more")
                    return True, models
                else:
                    print(f"✗ Ollama returned status {response.status}")
                    return False, []
    except aiohttp.ClientConnectorError as e:
        print(f"✗ Cannot connect to Ollama at {OLLAMA_URL}")
        print(f"  Error: {e}")
        print(f"  Is Ollama running? Try: ollama serve")
        return False, []
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False, []


async def test_2_model_availability(models: list):
    """Test 2: Check if vision model is available."""
    print("\n" + "="*60)
    print(f"TEST 2: Vision Model Availability ({VISION_MODEL})")
    print("="*60)

    found = any(VISION_MODEL in m for m in models)
    if found:
        print(f"✓ Model '{VISION_MODEL}' is available")
        return True
    else:
        print(f"✗ Model '{VISION_MODEL}' NOT found")
        print(f"  Available vision-capable models might be:")
        vision_models = [m for m in models if any(v in m.lower() for v in ['vision', 'vl', 'llava', 'ocr'])]
        for m in vision_models:
            print(f"    - {m}")
        if not vision_models:
            print("    (none found - try: ollama pull llama3.2-vision:11b)")
        return False


async def test_3_simple_text_generation():
    """Test 3: Simple text generation (no image) to verify model works."""
    print("\n" + "="*60)
    print("TEST 3: Simple Text Generation (no image)")
    print("="*60)

    payload = {
        "model": VISION_MODEL,
        "prompt": "Say 'hello' and nothing else.",
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_ctx": 2048,
        }
    }

    try:
        start = time.time()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{OLLAMA_URL}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                elapsed = time.time() - start

                if response.status == 200:
                    result = await response.json()
                    text = result.get("response", "")
                    tokens_in = result.get("prompt_eval_count", 0)
                    tokens_out = result.get("eval_count", 0)

                    print(f"✓ Text generation works ({elapsed:.1f}s)")
                    print(f"  Response: {text[:100]}...")
                    print(f"  Tokens: {tokens_in} in, {tokens_out} out")
                    return True
                else:
                    error = await response.text()
                    print(f"✗ Generation failed with status {response.status}")
                    print(f"  Error: {error[:200]}")
                    return False

    except asyncio.TimeoutError:
        print(f"✗ Timeout after 60s - model may be loading or stuck")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


async def test_4_minimal_image_generation():
    """Test 4: Minimal image generation with tiny test image."""
    print("\n" + "="*60)
    print("TEST 4: Minimal Image Generation (1x1 pixel)")
    print("="*60)

    b64_image = create_test_image_base64()
    print(f"  Test image size: {len(b64_image)} bytes (base64)")

    payload = {
        "model": VISION_MODEL,
        "prompt": "What do you see? Reply with one word.",
        "images": [b64_image],
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_ctx": 2048,
            "num_keep": 0,
        }
    }

    try:
        start = time.time()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{OLLAMA_URL}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                elapsed = time.time() - start

                if response.status == 200:
                    result = await response.json()
                    text = result.get("response", "")

                    print(f"✓ Image generation works ({elapsed:.1f}s)")
                    print(f"  Response: {text[:100]}")
                    return True
                else:
                    error = await response.text()
                    print(f"✗ Generation failed with status {response.status}")
                    print(f"  Error: {error[:500]}")

                    if "SameBatch" in error:
                        print("\n  >> SameBatch ERROR detected!")
                        print("  >> This is an Ollama context caching bug.")
                        print("  >> Try: pkill ollama && ollama serve")

                    return False

    except asyncio.TimeoutError:
        print(f"✗ Timeout after 120s")
        print("  The model is likely stuck or GPU memory exhausted")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


async def test_5_real_pdf_image(pdf_path: str = None):
    """Test 5: Test with a real PDF page image."""
    print("\n" + "="*60)
    print("TEST 5: Real PDF Page Analysis")
    print("="*60)

    # Find a test PDF
    if not pdf_path:
        # Look for any PDF in common locations
        search_paths = [
            Path.home() / "Downloads",
            Path("/tmp"),
            Path("."),
        ]
        for search_path in search_paths:
            if search_path.exists():
                pdfs = list(search_path.glob("*.pdf"))[:1]
                if pdfs:
                    pdf_path = str(pdfs[0])
                    break

    if not pdf_path:
        print("  Skipping - no PDF found for testing")
        print("  Provide a PDF path as argument to test")
        return None

    print(f"  Using PDF: {pdf_path}")

    # Convert first page to image
    try:
        from pdf2image import convert_from_path
        images = convert_from_path(pdf_path, dpi=150, first_page=1, last_page=1)
        if not images:
            print("  ✗ Failed to convert PDF to image")
            return False

        # Save to temp and encode
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            images[0].save(f.name, "PNG")
            temp_path = f.name

        with open(temp_path, "rb") as f:
            b64_image = base64.b64encode(f.read()).decode("utf-8")

        os.unlink(temp_path)

        print(f"  Image size: {len(b64_image) / 1024:.1f} KB (base64)")

    except ImportError:
        print("  ✗ pdf2image not installed")
        return None
    except Exception as e:
        print(f"  ✗ PDF conversion failed: {e}")
        return False

    # Test with the page analysis prompt
    prompt = '''Analyze this document page. Return JSON with:
{
  "page_type": "title|content|other",
  "title": "document title if visible",
  "authors": ["author names if visible"]
}
Return only valid JSON.'''

    payload = {
        "model": VISION_MODEL,
        "prompt": prompt,
        "images": [b64_image],
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_ctx": 4096,
            "num_keep": 0,
            "num_batch": 512,
        }
    }

    try:
        start = time.time()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{OLLAMA_URL}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as response:
                elapsed = time.time() - start

                if response.status == 200:
                    result = await response.json()
                    text = result.get("response", "")
                    tokens_in = result.get("prompt_eval_count", 0)
                    tokens_out = result.get("eval_count", 0)

                    print(f"✓ PDF page analysis works ({elapsed:.1f}s)")
                    print(f"  Tokens: {tokens_in} in, {tokens_out} out")
                    print(f"  Response:\n{text[:500]}")

                    # Try to parse JSON
                    try:
                        # Extract JSON from response
                        json_str = text.strip()
                        if "```" in json_str:
                            json_str = json_str.split("```")[1]
                            if json_str.startswith("json"):
                                json_str = json_str[4:]
                        data = json.loads(json_str)
                        print(f"\n  Parsed JSON successfully:")
                        print(f"    page_type: {data.get('page_type')}")
                        print(f"    title: {data.get('title', 'N/A')[:50]}")
                        print(f"    authors: {data.get('authors', [])}")
                    except json.JSONDecodeError:
                        print(f"\n  Warning: Could not parse response as JSON")

                    return True
                else:
                    error = await response.text()
                    print(f"✗ Analysis failed with status {response.status}")
                    print(f"  Error: {error[:500]}")
                    return False

    except asyncio.TimeoutError:
        print(f"✗ Timeout after 300s (5 minutes)")
        print("  The model cannot process this image in reasonable time")
        print("  Consider using a smaller/faster model")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


async def test_6_check_gpu_memory():
    """Test 6: Check GPU memory (NVIDIA only)."""
    print("\n" + "="*60)
    print("TEST 6: GPU Memory Check")
    print("="*60)

    try:
        import subprocess
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.used,memory.total,utilization.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            for line in lines:
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 4:
                    name, mem_used, mem_total, util = parts
                    mem_pct = float(mem_used) / float(mem_total) * 100
                    print(f"  GPU: {name}")
                    print(f"  Memory: {mem_used} / {mem_total} MB ({mem_pct:.1f}%)")
                    print(f"  Utilization: {util}%")

                    if mem_pct > 90:
                        print(f"\n  ⚠ GPU memory is almost full!")
                        print(f"    This may cause Ollama to hang or fail")
                        print(f"    Try: ollama stop {VISION_MODEL}")
            return True
        else:
            print("  nvidia-smi failed")
            return False
    except FileNotFoundError:
        print("  nvidia-smi not found (no NVIDIA GPU or drivers not installed)")
        print("  If using CPU-only, vision models will be very slow")
        return None
    except Exception as e:
        print(f"  Error checking GPU: {e}")
        return None


async def run_all_tests(pdf_path: str = None):
    """Run all diagnostic tests."""
    print("\n" + "#"*60)
    print("# Ollama Vision Model Diagnostic Tests")
    print(f"# URL: {OLLAMA_URL}")
    print(f"# Model: {VISION_MODEL}")
    print("#"*60)

    # Test 1: Connectivity
    connected, models = await test_1_ollama_connectivity()
    if not connected:
        print("\n\n>>> STOP: Cannot connect to Ollama. Fix this first.")
        return

    # Test 2: Model availability
    model_ok = await test_2_model_availability(models)
    if not model_ok:
        print(f"\n\n>>> STOP: Model '{VISION_MODEL}' not available.")
        print(f"    Install with: ollama pull {VISION_MODEL}")
        return

    # Test 3: Simple text generation
    text_ok = await test_3_simple_text_generation()
    if not text_ok:
        print("\n\n>>> STOP: Basic text generation failed.")
        print("    The model may be corrupted or Ollama has issues.")
        print("    Try: ollama rm {VISION_MODEL} && ollama pull {VISION_MODEL}")
        return

    # Test 4: Minimal image
    image_ok = await test_4_minimal_image_generation()
    if not image_ok:
        print("\n\n>>> ISSUE: Minimal image generation failed.")
        print("    This suggests a fundamental issue with vision capabilities.")
        print("    Try restarting Ollama: pkill ollama && ollama serve")

    # Test 5: Real PDF
    await test_5_real_pdf_image(pdf_path)

    # Test 6: GPU check
    await test_6_check_gpu_memory()

    print("\n" + "#"*60)
    print("# Diagnostic Complete")
    print("#"*60)


if __name__ == "__main__":
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else None

    # Allow overriding model via env
    if len(sys.argv) > 2:
        VISION_MODEL = sys.argv[2]

    asyncio.run(run_all_tests(pdf_path))
