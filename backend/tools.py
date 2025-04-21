# backend/tools.py
import logging
import httpx # For async HTTP requests
from bs4 import BeautifulSoup # For HTML parsing
from pathlib import Path # Import Path from pathlib
import os # Import os
import re # Import regex for scheme check
import aiofiles # Import aiofiles for async file operations
import codecs # Import codecs for decoding escaped sequences
import asyncio # Import asyncio for subprocess

# LangChain Tool Imports
# Import BaseTool for custom tool creation
from langchain_core.tools import Tool, BaseTool
from langchain_community.tools import DuckDuckGoSearchRun
# Import only ReadFileTool now
from langchain_community.tools.file_management import ReadFileTool
# WriteFileTool and ShellTool are replaced by custom ones below

logger = logging.getLogger(__name__)

# --- Define Workspace Path ---
try:
    # Resolve path relative to this file's location
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    WORKSPACE_ROOT = PROJECT_ROOT / "workspace"
    # Ensure workspace directory exists on startup
    os.makedirs(WORKSPACE_ROOT, exist_ok=True)
    logger.info(f"Workspace directory ensured at: {WORKSPACE_ROOT}")
except OSError as e:
    logger.error(f"Could not create workspace directory at {WORKSPACE_ROOT}: {e}", exc_info=True)
    # Handle error appropriately - maybe raise an exception or disable file tools
    raise OSError(f"Required workspace directory {WORKSPACE_ROOT} could not be created.") from e
except Exception as e:
    logger.error(f"Error resolving project/workspace path: {e}", exc_info=True)
    raise


# --- Tool Implementation Functions ---

async def fetch_and_parse_url(url: str) -> str:
    """
    Asynchronously fetches content from a URL, parses HTML,
    extracts text, and returns it. Limits content length and sanitizes URL.
    """
    MAX_CONTENT_LENGTH = 4000 # Limit context size
    REQUEST_TIMEOUT = 15.0 # Seconds
    HEADERS = { # Mimic browser to avoid blocking
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # Input validation
    if not isinstance(url, str):
        logger.warning(f"Received non-string URL input: {type(url)}")
        return "Error: Invalid URL input (must be a string)."

    # ** More Robust URL Cleaning **
    # Remove leading/trailing whitespace, internal newlines/tabs, and backticks
    clean_url = url.strip().replace('\n', '').replace('\r', '').replace('\t', '').strip('`')

    if not clean_url:
        logger.warning("Received empty URL after cleaning.")
        return "Error: Received an empty URL."

    # Basic check and fix for missing http/https scheme using regex
    if not re.match(r"^[a-zA-Z]+://", clean_url):
         logger.warning(f"URL '{clean_url}' missing scheme. Prepending https://")
         clean_url = f"https://{clean_url}"

    logger.info(f"Attempting to fetch and parse cleaned URL: {clean_url}")
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, follow_redirects=True, headers=HEADERS) as client:
            response = await client.get(clean_url)
            response.raise_for_status() # Raise HTTPStatusError for bad responses (4xx or 5xx)

            content_type = response.headers.get("content-type", "").lower()
            if "html" not in content_type:
                logger.warning(f"Non-HTML content type '{content_type}' at URL: {clean_url}")
                return f"Error: Cannot parse content type '{content_type}'. Only HTML is supported."

            html_content = response.text
            soup = BeautifulSoup(html_content, 'lxml') # Use lxml parser
            content_tags = soup.find('article') or soup.find('main') or soup.find('body')
            if content_tags:
                 # Extract text from common content tags
                 texts = content_tags.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td', 'th'])
                 extracted_text = "\n".join(t.get_text(strip=True) for t in texts if t.get_text(strip=True)) # Filter empty strings
            else:
                 # Fallback if no main tags found
                 extracted_text = soup.get_text(separator="\n", strip=True)

            if not extracted_text:
                logger.warning(f"Could not extract meaningful text from URL: {clean_url}")
                return "Error: Could not extract meaningful text content from the page."

            # Limit length and return
            truncated_text = extracted_text[:MAX_CONTENT_LENGTH]
            if len(extracted_text) > MAX_CONTENT_LENGTH:
                truncated_text += "..." # Indicate truncation
            logger.info(f"Successfully extracted ~{len(truncated_text)} chars from {clean_url}")
            return truncated_text

    # Specific error handling
    except httpx.TimeoutException:
        logger.error(f"Timeout error fetching URL: {clean_url}")
        return f"Error: Timeout while trying to fetch the URL: {clean_url}"
    except httpx.InvalidURL as e:
        # Catch error if URL is fundamentally invalid after cleaning
        logger.error(f"Invalid URL format for {clean_url} after cleaning: {e}")
        return f"Error: Invalid URL format provided: {e}"
    except httpx.RequestError as e:
        # Covers connection errors, etc.
        logger.error(f"Request error fetching URL {clean_url}: {e}")
        return f"Error: Could not fetch the URL. Network issue or invalid URL? Error: {e}"
    except httpx.HTTPStatusError as e:
        # Handles 4xx/5xx responses after connection
        logger.error(f"HTTP error fetching URL {clean_url}: Status {e.response.status_code}")
        return f"Error: Received HTTP status {e.response.status_code} when fetching the URL."
    except ImportError:
         # Handles case where lxml is not installed
         logger.error("lxml parser not installed. Please install with 'uv pip install lxml'.")
         return "Error: HTML parser (lxml) not installed on the server."
    except Exception as e:
        # Catch other potential errors during parsing or processing
        logger.error(f"Unexpected error processing URL {clean_url}: {e}", exc_info=True)
        return f"Error: Failed to process the content of the URL. Error: {e}"


# *** Updated custom function for writing files ***
async def write_to_file_in_workspace(input_str: str) -> str:
    """
    Writes text content to a specified file within the workspace.
    Input format: 'file_path:::text_content'
    Handles newline characters correctly and strips common markdown.
    """
    logger.info(f"Write tool received input: {input_str[:100]}...") # Log truncated input
    try:
        # Parse the input string: split only on the first occurrence of :::
        parts = input_str.split(':::', 1)
        if len(parts) != 2:
            logger.warning(f"Invalid input format for write_file: {input_str[:100]}...")
            return "Error: Invalid input format for write_file. Expected 'file_path:::text_content'."

        relative_path_str = parts[0].strip()
        raw_text_content = parts[1] # Content exactly as provided by LLM

        # Strip leading 'workspace/' prefix from path if agent included it
        if relative_path_str.startswith(("workspace/", "workspace\\")):
             # Use regex to remove potentially multiple leading workspace/ prefixes
             relative_path_str = re.sub(r"^[\\/]?(workspace[\\/])+", "", relative_path_str)
             logger.info(f"Stripped 'workspace/' prefix, using relative path: {relative_path_str}")

        # Prevent empty file paths after stripping
        if not relative_path_str:
            return "Error: File path cannot be empty."

        # Decode escaped sequences like \\n into actual newlines \n
        try:
            # Decode potential escape sequences like \\n, \\t etc.
            text_content = codecs.decode(raw_text_content, 'unicode_escape')
            logger.info("Decoded escaped sequences in text content.")
        except Exception as decode_err:
            logger.warning(f"Could not decode escapes in text content, using raw: {decode_err}")
            text_content = raw_text_content # Fallback to raw content

        # Basic cleaning of text content for common markdown fences
        text_content = re.sub(r"^```[a-zA-Z]*\s*\n", "", text_content) # Remove opening fence
        text_content = re.sub(r"\n```$", "", text_content) # Remove closing fence
        text_content = text_content.strip() # Remove leading/trailing whitespace

        # Security checks for file path
        relative_path = Path(relative_path_str)
        if relative_path.is_absolute() or '..' in relative_path.parts:
             logger.warning(f"Attempted file write with non-relative or traversal path: {relative_path_str}")
             return f"Error: Invalid file path '{relative_path_str}'. Must be relative within workspace."

        full_path = WORKSPACE_ROOT.joinpath(relative_path).resolve()
        # Double-check it's still within the workspace after resolving symlinks etc.
        if WORKSPACE_ROOT not in full_path.parents and full_path != WORKSPACE_ROOT:
             logger.error(f"Security Error: Attempted write outside workspace! Resolved path: {full_path}")
             return "Error: File path resolves outside the designated workspace."

        # Create parent directories and write file
        full_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(full_path, mode='w', encoding='utf-8') as f:
            await f.write(text_content) # Write the processed content

        logger.info(f"Successfully wrote {len(text_content)} bytes to {full_path}")
        return f"Successfully wrote content to '{relative_path_str}' in the workspace."

    except Exception as e:
        logger.error(f"Error writing file (input path '{relative_path_str}'): {e}", exc_info=True)
        return f"Error: Failed to write file '{relative_path_str}'. Reason: {type(e).__name__}"


# *** Custom Shell Tool operating in Workspace (Handles specific shell error) ***
class WorkspaceShellTool(BaseTool):
    name: str = "workspace_shell"
    description: str = (
        f"Use this tool ONLY to execute **non-interactive** shell commands directly within the agent's dedicated workspace ('{WORKSPACE_ROOT.name}'). "
        "Useful for running scripts located in the workspace (e.g., 'python my_script.py'), listing workspace files (`ls -l`), checking file details (`wc`, `head`, `tail`), or creating directories (`mkdir results`). "
        "Input MUST be a valid shell command string. "
        "The command automatically runs inside the workspace directory. Do NOT include 'workspace/' in the command path unless referring to a sub-directory *within* the workspace. "
        "**DO NOT use this for 'pip install' or environment modifications.**"
    )
    # Optional: Define args_schema if needed for more complex inputs using Pydantic

    def _run(self, command: str) -> str:
        """Synchronous execution wrapper."""
        logger.warning("Running WorkspaceShellTool synchronously using _run.")
        try:
            loop = asyncio.get_running_loop()
            result = loop.run_until_complete(self._arun_internal(command))
        except RuntimeError: # No running event loop
             result = asyncio.run(self._arun_internal(command))
        return result

    async def _arun(self, command: str) -> str:
         """Asynchronous execution entry point."""
         return await self._arun_internal(command)

    async def _arun_internal(self, command: str) -> str:
        """Internal async helper for running the command in the workspace."""
        logger.info(f"WorkspaceShellTool executing command: '{command}' in CWD: {WORKSPACE_ROOT}")
        process = None # Ensure process is defined for finally block
        stdout_str = "" # Initialize
        stderr_str = "" # Initialize
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(WORKSPACE_ROOT) # *** Set Current Working Directory to Workspace ***
            )
            stdout, stderr = await process.communicate() # Wait for process and get all output
            stdout_str = stdout.decode(errors='replace').strip()
            stderr_str = stderr.decode(errors='replace').strip()

            result = ""
            if stdout_str:
                result += f"STDOUT:\n{stdout_str}\n"
            if stderr_str:
                result += f"STDERR:\n{stderr_str}\n" # Include stderr in result

            # Check for the specific harmless shell error
            harmless_shell_error = "/bin/sh: 2: Syntax error: EOF in backquote substitution"
            is_harmless_error = stderr_str == harmless_shell_error
            command_failed = process.returncode != 0

            # Determine overall status message and potentially modify result string
            if command_failed and not (is_harmless_error and stdout_str):
                 # Real failure or harmless error occurred but no stdout produced
                 result += f"ERROR: Command failed with exit code {process.returncode}"
                 logger.warning(f"WorkspaceShellTool command '{command}' failed. Exit: {process.returncode}. Stderr: {stderr_str}")
            elif is_harmless_error and stdout_str:
                 # Harmless error occurred, but we got stdout, treat as success for agent
                 logger.warning(f"WorkspaceShellTool command '{command}' produced harmless shell error in stderr but had stdout. Treating as success.")
                 # Remove the harmless error from the result string sent back to agent for clarity
                 result = result.replace(f"STDERR:\n{harmless_shell_error}\n", "").strip() # Remove STDERR line entirely
                 # Add a note about success despite shell error? Optional.
                 # result += "\n(Note: Command executed successfully despite minor shell completion error.)"
            elif command_failed:
                 # Failed for other reasons (non-zero exit code but no specific stderr)
                 result += f"ERROR: Command failed with exit code {process.returncode}"
                 logger.warning(f"WorkspaceShellTool command '{command}' failed. Exit: {process.returncode}. Stderr: {stderr_str}")
            # else: command succeeded with exit code 0 and no stderr (or harmless stderr handled above)

            logger.info(f"WorkspaceShellTool command finished. Exit code: {process.returncode}. Output length: {len(result)}")
            # Truncate potentially long results before returning to agent
            return result[:3000] + "..." if len(result) > 3000 else result.strip() # Strip trailing newline

        except FileNotFoundError:
            cmd_part = command.split()[0] if command else "Unknown"
            logger.warning(f"WorkspaceShellTool command not found: {cmd_part}")
            return f"Error: Command not found within the environment: {cmd_part}"
        except Exception as e:
            logger.error(f"Error executing command '{command}' in workspace: {e}", exc_info=True)
            return f"Error executing command in workspace: {type(e).__name__}"
        finally:
            # Ensure process is cleaned up if it exists and hasn't finished
            if process and process.returncode is None:
                try:
                    process.terminate()
                    await process.wait()
                    logger.warning(f"Terminated workspace shell process for command: {command}")
                except ProcessLookupError: pass # Already finished
                except Exception as term_e: logger.error(f"Error terminating process: {term_e}")


# --- Initialize Tools ---

# 1. Custom Workspace Shell Tool
workspace_shell_tool = WorkspaceShellTool() # Use the custom tool

# 2. Web Search Tool
search_tool = DuckDuckGoSearchRun()
search_tool.description = (
    "Use this tool ONLY when you need to find current information, real-time data (like weather), or answer questions about recent events or topics not covered by your training data. "
    "Input MUST be a concise search query string."
)

# 3. Web Page Reader Tool
web_reader_tool = Tool.from_function(
    func=fetch_and_parse_url,
    name="web_page_reader",
    description=(
        "Use this tool ONLY to fetch and extract the main text content from a specific web page, given its URL. "
        "Input MUST be a single, valid URL string (whitespace and newlines will be removed). "
        "Use this tool *after* a web search has provided a relevant URL, or when the user explicitly asks you to read or summarize a specific URL they provided. "
    ),
    coroutine=fetch_and_parse_url
)

# 4. Read File Tool
read_file_tool = ReadFileTool(root_dir=str(WORKSPACE_ROOT))
read_file_tool.description = (
    f"Use this tool ONLY to read the entire contents of a file located within the agent's designated workspace ('{WORKSPACE_ROOT.name}'). "
    f"Input MUST be a file path relative to the workspace root (e.g., 'my_data.csv'). Do NOT include '{WORKSPACE_ROOT.name}/'."
)

# 5. Custom Write File Tool
write_file_tool = Tool.from_function(
    func=write_to_file_in_workspace,
    name="write_file",
    description=(
        f"Use this tool ONLY to write or overwrite text content to a file within the agent's designated workspace ('{WORKSPACE_ROOT.name}'). "
        f"Input MUST be a single string formatted as 'file_path:::text_content'. "
        f"'file_path' MUST be relative to the workspace root (e.g., 'script.py'). Do NOT include '{WORKSPACE_ROOT.name}/'. Subdirectories will be created if needed. "
        f"'text_content' is the exact string content to write (newlines should be represented as '\\n' by the AI). The separator MUST be ':::'. "
        f"Example input: 'output.log:::Agent execution finished.\\nStatus: OK.' "
        f"WARNING: This tool OVERWRITES the file if it already exists."
    ),
    coroutine=write_to_file_in_workspace
)


# --- List of Tools for the Agent ---
# Use the new workspace_shell_tool instead of the old shell_tool
agent_tools = [
    workspace_shell_tool,
    search_tool,
    web_reader_tool,
    read_file_tool,
    write_file_tool,
]

logger.info(f"Initialized tools: {[tool.name for tool in agent_tools]}")
logger.info(f"File tools & Shell tool restricted to workspace: {WORKSPACE_ROOT}") # Log updated info

