# backend/mcp/custom/vision_tools.py
"""
Vision tools for image analysis.

Provides image analysis capabilities:
- read_image: Analyze images using vision-capable models
- describe_figure: Specialized analysis for scientific figures
"""
import os
import base64
import ollama
from pathlib import Path
from backend.mcp.decorator import mentori_tool
from backend.agents.session_context import get_logger
from backend.agents.prompts import get_vision_prompt
from backend.config import settings

logger = get_logger(__name__)

# Supported image formats
SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp'}


def _encode_image_to_base64(image_path: str) -> tuple[str, str]:
    """
    Read an image file and encode it to base64.
    Returns (base64_data, mime_type).
    """
    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported image format: {suffix}. Supported: {SUPPORTED_FORMATS}")

    # Determine MIME type
    mime_map = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.bmp': 'image/bmp',
    }
    mime_type = mime_map.get(suffix, 'image/png')

    with open(path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')

    return image_data, mime_type


@mentori_tool(
    category="vision",
    agent_role="vision",
    is_llm_based=True,
    secrets=["workspace_path", "vision_model"]  # Injected from session context
)
def read_image(
    path: str,
    prompt: str = "Describe this image in detail.",
    workspace_path: str = None,
    vision_model: str = None
) -> str:
    """
    Analyze an image file using a vision-capable model.

    Uses the user's configured Vision Agent model automatically.

    Args:
        path: Path to the image file (PNG, JPG, GIF, WebP, BMP)
        prompt: Question or instruction about the image

    Returns:
        Text description/analysis of the image
    """
    # Internal call with injected context
    return _read_image_internal(
        path=path,
        prompt=prompt,
        model=vision_model,
        workspace_path=workspace_path
    )


def _read_image_internal(
    path: str,
    prompt: str = "Describe this image in detail.",
    model: str = None,
    workspace_path: str = None
) -> str:
    """
    Internal implementation of read_image with model override support.
    Used by other vision tools like describe_figure and compare_images.

    Args:
        path: Image file path (relative or absolute)
        prompt: The prompt to send to the vision model
        model: Model identifier (injected from session or fallback)
        workspace_path: Workspace path for resolving relative paths (injected from session)
    """
    from backend.agents.session_context import get_session_context

    # Try to get context (works if running in same process, e.g., tests)
    ctx = get_session_context()

    # 1. Model Resolution - prefer injected, then context
    # Model should come from user's Agent Roles settings (vision → default fallback)
    if not model or model == "default":
        if ctx:
            model = ctx.agent_roles.get("vision")
            if not model:
                model = ctx.agent_roles.get("default")
            logger.info(f"[VISION] Model from session context: {model}")

    # No hardcoded fallback - user must configure Agent Roles
    if not model:
        error_msg = "No vision model configured. Please go to Settings → Agent Roles and configure a Vision agent (or at least a Default agent)."
        logger.error(f"[VISION] {error_msg}")
        return f"Error: {error_msg}"

    # Use centralized parser for model identifier
    from backend.agents.models.utils import parse_model_identifier
    parsed = parse_model_identifier(model)
    model = parsed.model_name
    think_param = parsed.think  # False, True, or "low"/"medium"/"high"

    logger.info(f"Using vision model: {model} (think={think_param})")

    # 2. Resolve workspace_path - prefer injected, then context
    if not workspace_path and ctx:
        workspace_path = ctx.workspace_path
        logger.info(f"[VISION] Workspace from session context: {workspace_path}")

    # 3. Resolve Path
    image_path = Path(path)
    logger.info(f"[VISION] Input path: '{path}', is_absolute: {image_path.is_absolute()}, workspace: {workspace_path}")

    if not image_path.is_absolute() and workspace_path:
        workspace = Path(workspace_path)

        # Try direct resolution first
        potential_path = workspace / image_path
        logger.info(f"[VISION] Trying direct path: {potential_path}, exists: {potential_path.exists()}")

        if potential_path.exists():
            image_path = potential_path
            logger.info(f"Resolved relative path '{path}' to '{image_path}'")
        else:
            # Also try parent directory (user workspace) since files may be stored there
            user_workspace = workspace.parent
            parent_path = user_workspace / Path(path).name
            logger.info(f"[VISION] Trying user workspace: {parent_path}, exists: {parent_path.exists()}")

            if parent_path.exists():
                image_path = parent_path
                logger.info(f"Found file in user workspace: {image_path}")
            else:
                # Recursive search in task workspace
                logger.info(f"[VISION] Starting recursive search in: {workspace}")
                found = False

                # Get just the filename for search
                filename = Path(path).name

                for root, dirs, files in os.walk(workspace):
                    if filename in files:
                        image_path = Path(root) / filename
                        logger.info(f"Found file via recursive search at: {image_path}")
                        found = True
                        break

                # If still not found, search user workspace too
                if not found and user_workspace.exists():
                    logger.info(f"[VISION] Searching user workspace: {user_workspace}")
                    for root, dirs, files in os.walk(user_workspace):
                        if filename in files:
                            image_path = Path(root) / filename
                            logger.info(f"Found file in user workspace at: {image_path}")
                            found = True
                            break

                if not found:
                    # Keep original resolution for valid error message
                    image_path = potential_path
                    logger.warning(f"[VISION] Image NOT found: {path} (searched: {workspace} and {user_workspace})")
    elif not image_path.is_absolute() and not workspace_path:
        logger.warning(f"[VISION] Cannot resolve relative path - no workspace_path provided!")

    # Update path to string for logging/usage
    path_str = str(image_path)

    logger.info(f"Analyzing image: {path_str} with model: {model} prompt: {prompt[:50]}...")

    try:
        # Encode image
        image_data, mime_type = _encode_image_to_base64(path_str)

        # Remove provider prefix if present (e.g. ollama::)
        if "::" in model:
            model = model.split("::")[-1]

        # Get Ollama URL from settings (respects OLLAMA_BASE_URL env var)
        ollama_url = settings.OLLAMA_BASE_URL
        logger.info(f"[VISION] Calling Ollama at: {ollama_url}")

        # Call Ollama vision model using ollama library chat API
        client = ollama.Client(host=ollama_url)

        # Build chat options
        chat_kwargs = {
            "model": model,
            "messages": [{
                'role': 'user',
                'content': prompt,
                'images': [image_data]
            }]
        }

        # Enable thinking mode if specified in model config
        if think_param:
            chat_kwargs["think"] = think_param  # True or "low"/"medium"/"high"
            logger.info(f"[VISION] Thinking mode enabled for {model}: think={think_param}")

        response = client.chat(**chat_kwargs)

        response_text = response.get("message", {}).get("content", "")

        # 4. Extract token usage from ollama response
        input_tokens = response.get("prompt_eval_count", 0)
        output_tokens = response.get("eval_count", 0)
        total_tokens = input_tokens + output_tokens

        logger.info(f"[VISION] Token usage: in={input_tokens}, out={output_tokens}, total={total_tokens}")

        # 4b. Write audit file to outputs/vision/ for transparency
        if workspace_path:
            try:
                from datetime import datetime
                ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                img_stem = Path(path_str).stem[:40]
                outputs_dir = Path(workspace_path) / "outputs" / "vision"
                outputs_dir.mkdir(parents=True, exist_ok=True)
                audit_path = outputs_dir / f"{ts}_{img_stem}.md"
                audit_content = (
                    f"# Vision Analysis\n\n"
                    f"**Image:** `{path_str}`\n"
                    f"**Model:** {model}\n"
                    f"**Prompt:** {prompt}\n"
                    f"**Tokens:** {total_tokens} (in={input_tokens}, out={output_tokens})\n\n"
                    f"## Analysis\n\n{response_text}\n"
                )
                audit_path.write_text(audit_content, encoding="utf-8")
                logger.info(f"[VISION] Audit file written: {audit_path}")
            except Exception as audit_err:
                logger.warning(f"[VISION] Failed to write audit file: {audit_err}")

        # 5. Return formatted result with Model Attribution and Token Usage marker
        # The token usage marker allows chat_loop to accumulate LLM tool costs
        result = f"[Analysis by {model}]\n{response_text}"

        # Append token usage marker (parsed by chat_loop)
        if total_tokens > 0:
            result += f"\n<!--TOOL_TOKEN_USAGE:{{\"input\":{input_tokens},\"output\":{output_tokens},\"total\":{total_tokens}}}-->"

        return result

    except Exception as e:
        logger.error(f"Vision tool failed: {e}")
        return f"Error executing vision analysis: {str(e)}"


@mentori_tool(
    category="vision",
    agent_role="vision",
    is_llm_based=True,
    secrets=["workspace_path", "vision_model"]
)
def describe_figure(
    path: str,
    figure_type: str = "auto",
    workspace_path: str = None,
    vision_model: str = None
) -> str:
    """
    Specialized analysis for scientific figures and plots.

    Analyzes scientific figures with domain-specific prompts for:
    - Plots (scatter, line, bar, box, violin)
    - Heatmaps
    - Volcano plots
    - Network diagrams
    - Microscopy images

    Uses the user's configured Vision Agent model automatically.

    Args:
        path: Path to the figure image
        figure_type: Type of figure (auto, plot, heatmap, volcano, network, microscopy)

    Returns:
        Structured analysis of the scientific figure
    """
    logger.info(f"Analyzing scientific figure: {path} (type: {figure_type})")

    # Get specialized prompt based on figure type (from centralized prompts.py)
    prompt_key = f"describe_figure_{figure_type}"
    prompt = get_vision_prompt(prompt_key)

    # Use the internal function with the specialized prompt and injected secrets
    return _read_image_internal(
        path=path,
        prompt=prompt,
        model=vision_model,
        workspace_path=workspace_path
    )


@mentori_tool(
    category="vision",
    agent_role="vision",
    is_llm_based=True,
    secrets=["workspace_path", "vision_model"]
)
def compare_images(
    path1: str,
    path2: str,
    comparison_type: str = "general",
    workspace_path: str = None,
    vision_model: str = None
) -> str:
    """
    Compare two images and describe differences.

    Useful for before/after comparisons, quality checks, or verifying
    that generated outputs match expectations.

    Uses the user's configured Vision Agent model automatically.

    Args:
        path1: Path to the first image
        path2: Path to the second image
        comparison_type: Type of comparison (general, before_after, quality)

    Returns:
        Comparison analysis of the two images
    """
    logger.info(f"Comparing images: {path1} vs {path2}")

    # Analyze each image separately (since most vision models don't support multi-image)
    analysis1 = _read_image_internal(
        path=path1,
        prompt="Describe this image in detail, noting specific visual elements, colors, layout, and content.",
        model=vision_model,
        workspace_path=workspace_path
    )

    analysis2 = _read_image_internal(
        path=path2,
        prompt="Describe this image in detail, noting specific visual elements, colors, layout, and content.",
        model=vision_model,
        workspace_path=workspace_path
    )

    # Return structured comparison
    comparison_prompts = {
        "general": "general similarities and differences",
        "before_after": "changes between the before (first) and after (second) states",
        "quality": "quality differences, noting which image is clearer, more detailed, or better formatted"
    }

    comparison_focus = comparison_prompts.get(comparison_type, comparison_prompts["general"])

    return f"""## Image Comparison

### Image 1: {path1}
{analysis1}

### Image 2: {path2}
{analysis2}

### Comparison Focus: {comparison_focus}
Based on the analyses above, compare the two images noting {comparison_focus}."""
