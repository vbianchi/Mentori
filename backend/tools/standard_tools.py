# backend/tools/standard_tools.py
import logging
import httpx
from bs4 import BeautifulSoup
from pathlib import Path
import os
import re
import aiofiles
import codecs
import asyncio
import sys
from typing import List, Optional, Dict, Any, Type
import functools # Added for functools.partial if needed, though not used in current proposal

# LangChain Tool Imports
from langchain_core.tools import Tool, BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_experimental.utilities import PythonREPL
from Bio import Entrez
from urllib.error import HTTPError

# PDF Import
try:
    import pypdf
    logger_pypdf = logging.getLogger(__name__)
except ImportError:
    logger_pypdf = logging.getLogger(__name__)
    logger_pypdf.warning("pypdf not installed. PDF reading functionality will be unavailable.")
    pypdf = None

# Project Imports
from backend.config import settings
from backend.tool_loader import load_tools_from_config, ToolLoadingError # <<< NEW IMPORT
from .tavily_search_tool import TavilyAPISearchTool # Keep for type hinting or if DeepResearch needs it directly
from .deep_research_tool import DeepResearchTool # Keep for manual add for now

logger = logging.getLogger(__name__)

# --- Define Base Workspace Path ---
try:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    BASE_WORKSPACE_ROOT = PROJECT_ROOT / "workspace"
    os.makedirs(BASE_WORKSPACE_ROOT, exist_ok=True)
    logger.info(f"Base workspace directory ensured at: {BASE_WORKSPACE_ROOT}")
except OSError as e:
    logger.error(f"Could not create base workspace directory: {e}", exc_info=True)
    raise OSError(f"Required base workspace directory {BASE_WORKSPACE_ROOT} could not be created.") from e
except Exception as e:
    logger.error(f"Error resolving project/workspace path: {e}", exc_info=True)
    raise

TEXT_EXTENSIONS = {".txt", ".py", ".js", ".css", ".html", ".json", ".csv", ".md", ".log", ".yaml", ".yml"}

def get_task_workspace_path(task_id: Optional[str], create_if_not_exists: bool = True) -> Path:
    logger.debug(f"get_task_workspace_path called for task_id: '{task_id}', create_if_not_exists: {create_if_not_exists}")
    if not task_id or not isinstance(task_id, str):
        msg = f"Invalid or missing task_id ('{task_id}') provided for workspace path."
        logger.error(msg)
        raise ValueError(msg)

    sane_task_id = re.sub(r'[^\w\-.]', '_', task_id)
    if not sane_task_id:
        msg = f"Task_id '{task_id}' resulted in an empty sanitized ID. Cannot create workspace."
        logger.error(msg)
        raise ValueError(msg)

    if ".." in sane_task_id or "/" in sane_task_id or "\\" in sane_task_id:
        msg = f"Invalid characters detected in sanitized task_id: {sane_task_id} (original: {task_id}). Denying workspace path creation."
        logger.error(msg)
        raise ValueError(msg)

    task_workspace = BASE_WORKSPACE_ROOT / sane_task_id
    # logger.info(f"Resolved task workspace path: {task_workspace}") # Reduced verbosity

    if create_if_not_exists:
        try:
            if not task_workspace.exists():
                os.makedirs(task_workspace, exist_ok=True)
                logger.info(f"Created task workspace directory: {task_workspace}")
            else:
                logger.debug(f"Task workspace directory already exists: {task_workspace}")
        except OSError as e:
            logger.error(f"Could not create task workspace directory at {task_workspace}: {e}", exc_info=True)
            raise OSError(f"Could not create task workspace {task_workspace}: {e}") from e
    elif not task_workspace.exists():
        logger.warning(f"Task workspace directory does not exist and create_if_not_exists is False: {task_workspace}")

    return task_workspace

async def fetch_and_parse_url(url: str) -> str: # Content remains the same
    tool_name = "web_page_reader"
    logger.info(f"Tool '{tool_name}' received raw input: '{url}'")
    if not isinstance(url, str) or not url.strip():
        logger.error(f"Tool '{tool_name}' received invalid input: Must be a non-empty string.")
        return "Error: Invalid input. Expected a non-empty URL string."
    max_length = settings.tool_web_reader_max_length
    timeout = settings.tool_web_reader_timeout
    HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    clean_url = url.strip().replace('\n', '').replace('\r', '').replace('\t', '').strip('`')
    if not clean_url:
        logger.error(f"Tool '{tool_name}' input resulted in empty URL after cleaning.")
        return "Error: Received an empty URL after cleaning."
    if not re.match(r"^[a-zA-Z]+://", clean_url):
        logger.info(f"Tool '{tool_name}': No scheme found, prepending https:// to '{clean_url}'")
        clean_url = f"https://{clean_url}"
    logger.info(f"Tool '{tool_name}' attempting to fetch and parse cleaned URL: {clean_url} (Timeout: {timeout}s)")
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=HEADERS) as client:
            response = await client.get(clean_url); response.raise_for_status()
            content_type = response.headers.get("content-type", "").lower()
            if "html" not in content_type:
                logger.warning(f"Tool '{tool_name}': Cannot parse content type '{content_type}' for URL {clean_url}")
                return f"Error: Cannot parse content type '{content_type}'. Only HTML is supported."
            html_content = response.text; soup = BeautifulSoup(html_content, 'lxml')
            content_tags = soup.find('article') or soup.find('main') or soup.find('body')
            if content_tags: texts = content_tags.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td', 'th']); extracted_text = "\n".join(t.get_text(strip=True) for t in texts if t.get_text(strip=True))
            else: extracted_text = soup.get_text(separator="\n", strip=True)
            if not extracted_text:
                logger.warning(f"Tool '{tool_name}': Could not extract meaningful text from {clean_url}")
                return "Error: Could not extract meaningful text from the page."
            truncated_text = extracted_text[:max_length]
            if len(extracted_text) > max_length: truncated_text += "..."
            logger.info(f"Tool '{tool_name}': Successfully extracted ~{len(truncated_text)} chars from {clean_url}")
            return truncated_text
    except httpx.TimeoutException: logger.error(f"Tool '{tool_name}': Timeout fetching {clean_url}"); return f"Error: Timeout fetching URL."
    except httpx.InvalidURL as e: logger.error(f"Tool '{tool_name}': Invalid URL format for {clean_url}: {e}"); return f"Error: Invalid URL format: {e}"
    except httpx.RequestError as e: logger.error(f"Tool '{tool_name}': Request error fetching {clean_url}: {e}"); return f"Error: Could not fetch URL: {e}"
    except httpx.HTTPStatusError as e: logger.error(f"Tool '{tool_name}': HTTP error fetching {clean_url}: {e.response.status_code}"); return f"Error: HTTP {e.response.status_code} fetching URL."
    except ImportError: logger.error(f"Tool '{tool_name}': lxml not installed."); return "Error: HTML parser (lxml) not installed."
    except Exception as e: logger.error(f"Tool '{tool_name}': Error parsing {clean_url}: {e}", exc_info=True); return f"Error parsing URL: {e}"


async def write_to_file_in_task_workspace(input_str: str, task_workspace: Path) -> str: # Content remains the same
    tool_name = "write_file"
    logger.debug(f"Tool '{tool_name}': Raw input_str: '{input_str[:200]}{'...' if len(input_str) > 200 else ''}' for workspace: {task_workspace.name}")
    if not isinstance(input_str, str) or ':::' not in input_str:
        logger.error(f"Tool '{tool_name}' received invalid input format. Expected 'file_path:::text_content'. Got: '{input_str[:100]}...'")
        return "Error: Invalid input format. Expected 'file_path:::text_content'."
    relative_path_str = ""
    try:
        parts = input_str.split(':::', 1)
        if len(parts) != 2:
            logger.error(f"Tool '{tool_name}': Input split failed unexpectedly. Got: {parts}")
            return "Error: Invalid input format after splitting. Expected 'file_path:::text_content'."
        relative_path_str = parts[0].strip().strip('\'"`')
        raw_text_content = parts[1]
        logger.debug(f"Tool '{tool_name}': Parsed relative_path_str: '{relative_path_str}', raw_text_content length: {len(raw_text_content)}")
        cleaned_relative_path = relative_path_str
        if cleaned_relative_path.startswith((f"workspace/{task_workspace.name}/", f"workspace\\{task_workspace.name}\\" ,f"{task_workspace.name}/", f"{task_workspace.name}\\")):
            cleaned_relative_path = re.sub(r"^[\\/]?(workspace[\\/])?%s[\\/]" % re.escape(task_workspace.name), "", cleaned_relative_path)
            logger.info(f"Tool '{tool_name}': Stripped workspace/task prefix, using relative path: {cleaned_relative_path}")
        elif cleaned_relative_path.startswith(("workspace/", "workspace\\")):
            cleaned_relative_path = re.sub(r"^[\\/]?(workspace[\\/])+", "", cleaned_relative_path)
            logger.info(f"Tool '{tool_name}': Stripped generic 'workspace/' prefix, using: {cleaned_relative_path}")
        if not cleaned_relative_path:
            logger.error(f"Tool '{tool_name}': File path became empty after cleaning.")
            return "Error: File path cannot be empty after cleaning."
        try: text_content = codecs.decode(raw_text_content, 'unicode_escape'); logger.debug(f"Tool '{tool_name}': Decoded unicode escapes.")
        except Exception as decode_err: logger.warning(f"Tool '{tool_name}': Could not decode unicode escapes, using raw content: {decode_err}"); text_content = raw_text_content
        text_content = re.sub(r"^```[a-zA-Z]*\s*\n", "", text_content) # Strip markdown code blocks
        text_content = re.sub(r"\n```$", "", text_content)
        text_content = text_content.strip()
        relative_path = Path(cleaned_relative_path)
        if relative_path.is_absolute() or '..' in relative_path.parts:
            logger.error(f"Tool '{tool_name}': Security Error - Invalid file path '{cleaned_relative_path}' attempts traversal.")
            return f"Error: Invalid file path '{cleaned_relative_path}'. Path must be relative and within the workspace."
        full_path = task_workspace.joinpath(relative_path).resolve()
        logger.info(f"Tool '{tool_name}': Attempting to write to resolved full_path: '{full_path}'")
        if not full_path.is_relative_to(task_workspace.resolve()):
            logger.error(f"Tool '{tool_name}': Security Error - Write path resolves outside task workspace! Task: {task_workspace.name}, Resolved: {full_path}")
            return "Error: File path resolves outside the designated task workspace."
        full_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(full_path, mode='w', encoding='utf-8') as f:
            await f.write(text_content)
        logger.info(f"Tool '{tool_name}': Successfully wrote {len(text_content)} bytes to '{full_path}'. First 100 chars: '{text_content[:100]}{'...' if len(text_content) > 100 else ''}'")
        return f"SUCCESS::write_file:::{cleaned_relative_path}" # Return relative path for consistency
    except Exception as e:
        logger.error(f"Tool '{tool_name}': Error writing file '{relative_path_str}' to workspace {task_workspace.name}: {e}", exc_info=True)
        return f"Error: Failed to write file '{relative_path_str}'. Reason: {type(e).__name__}"

async def read_file_content(relative_path_str: str, task_workspace: Path) -> str: # Content remains the same
    tool_name = "read_file"
    logger.debug(f"Tool '{tool_name}': Raw relative_path_str: '{relative_path_str[:100]}{'...' if len(relative_path_str) > 100 else ''}' in workspace: {task_workspace.name}")
    if not isinstance(relative_path_str, str) or not relative_path_str.strip():
        logger.error(f"Tool '{tool_name}': Received invalid input. Expected a non-empty relative file path string.")
        return "Error: Invalid input. Expected a non-empty relative file path string."
    first_line = relative_path_str.splitlines()[0] if relative_path_str else ""
    cleaned_relative_path = first_line.strip().strip('\'"`')
    logger.info(f"Tool '{tool_name}': Cleaned relative_path for reading: '{cleaned_relative_path}'")
    if not cleaned_relative_path:
        logger.error(f"Tool '{tool_name}': File path became empty after cleaning.")
        return "Error: File path cannot be empty after cleaning."
    relative_path = Path(cleaned_relative_path)
    if relative_path.is_absolute() or '..' in relative_path.parts:
        logger.error(f"Tool '{tool_name}': Security Error - Invalid read file path '{cleaned_relative_path}' attempts traversal.")
        return f"Error: Invalid file path '{cleaned_relative_path}'. Path must be relative and within the workspace."
    full_path = task_workspace.joinpath(relative_path).resolve()
    logger.info(f"Tool '{tool_name}': Attempting to read resolved full_path: '{full_path}'")
    if not full_path.is_relative_to(task_workspace.resolve()):
        logger.error(f"Tool '{tool_name}': Security Error - Read path resolves outside task workspace! Task: {task_workspace.name}, Resolved: {full_path}")
        return "Error: File path resolves outside the designated task workspace."
    if not full_path.exists():
        logger.warning(f"Tool '{tool_name}': File not found at {full_path}")
        return f"Error: File not found at path '{cleaned_relative_path}'."
    if not full_path.is_file():
        logger.warning(f"Tool '{tool_name}': Path is not a file: {full_path}")
        return f"Error: Path '{cleaned_relative_path}' is not a file."
    file_extension = full_path.suffix.lower()
    content = ""
    try:
        if file_extension == ".pdf":
            if pypdf is None:
                logger.error(f"Tool '{tool_name}': Attempted to read PDF, but pypdf library is not installed.")
                return "Error: PDF reading library (pypdf) is not installed on the server."
            def read_pdf_sync():
                extracted_text = ""
                try:
                    reader = pypdf.PdfReader(str(full_path))
                    num_pages = len(reader.pages)
                    logger.info(f"Tool '{tool_name}': Reading {num_pages} pages from PDF: {full_path.name}")
                    for i, page in enumerate(reader.pages):
                        try:
                            page_text = page.extract_text()
                            if page_text: extracted_text += page_text + "\n"
                        except Exception as page_err:
                            logger.warning(f"Tool '{tool_name}': Error extracting text from page {i+1} of {full_path.name}: {page_err}")
                            extracted_text += f"\n--- Error reading page {i+1} ---\n"
                    return extracted_text.strip()
                except pypdf.errors.PdfReadError as pdf_err:
                    logger.error(f"Tool '{tool_name}': Error reading PDF file {full_path.name}: {pdf_err}")
                    raise RuntimeError(f"Error: Could not read PDF file '{cleaned_relative_path}'. It might be corrupted or encrypted. Error: {pdf_err}") from pdf_err
                except Exception as e:
                    logger.error(f"Tool '{tool_name}': Unexpected error reading PDF {full_path.name}: {e}", exc_info=True)
                    raise RuntimeError(f"Error: An unexpected error occurred while reading PDF '{cleaned_relative_path}'.") from e
            loop = asyncio.get_running_loop()
            content = await loop.run_in_executor(None, read_pdf_sync)
            actual_length = len(content)
            logger.info(f"Tool '{tool_name}': Successfully read {actual_length} chars from PDF '{cleaned_relative_path}'. First 100 chars: '{content[:100]}{'...' if actual_length > 100 else ''}'")
            warning_length = settings.tool_pdf_reader_warning_length
            if actual_length > warning_length:
                warning_message = f"\n\n[SYSTEM WARNING: Full PDF content read ({actual_length} chars), which exceeds the warning threshold of {warning_length} chars. This may be too long for the current LLM's context window.]"
                content += warning_message
                logger.warning(f"Tool '{tool_name}': PDF content length ({actual_length}) exceeds warning threshold ({warning_length}). Appending warning.")
        elif file_extension in TEXT_EXTENSIONS:
            async with aiofiles.open(full_path, mode='r', encoding='utf-8', errors='ignore') as f:
                content = await f.read()
            logger.info(f"Tool '{tool_name}': Successfully read {len(content)} chars from text file '{cleaned_relative_path}'. First 100 chars: '{content[:100]}{'...' if len(content) > 100 else ''}'")
        else:
            logger.warning(f"Tool '{tool_name}': Unsupported file extension '{file_extension}' for file '{cleaned_relative_path}'")
            return f"Error: Cannot read file. Unsupported file extension: '{file_extension}'. Supported text: {', '.join(TEXT_EXTENSIONS)}, .pdf"
        return content
    except RuntimeError as rt_err:
        return str(rt_err)
    except Exception as e:
        logger.error(f"Tool '{tool_name}': Error reading file '{cleaned_relative_path}' in workspace {task_workspace.name}: {e}", exc_info=True)
        return f"Error: Failed to read file '{cleaned_relative_path}'. Reason: {type(e).__name__}"

# --- ReadFileTool Class Definition ---
class ReadFileTool(BaseTool):
    name: str = "read_file"
    description: str = (
        f"Use this tool ONLY to read the entire contents of a file (including text and PDF files) "
        f"located within the current task's workspace. Input MUST be the relative path string "
        f"to the file from the workspace root (e.g., 'my_data.csv', 'report.pdf', 'scripts/analysis.py'). "
        f"Returns the full text content or an error message. For PDFs, a warning is appended if "
        f"the content exceeds {settings.tool_pdf_reader_warning_length} characters."
    )
    task_workspace: Path

    def _run(self, relative_path_str: str) -> str:
        logger.warning(f"ReadFileTool synchronously called for: {relative_path_str}. This may block if the underlying operation is truly async.")
        try:
            # Attempt to run the async version in a blocking way
            return asyncio.run(read_file_content(relative_path_str, self.task_workspace))
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e):
                # This is a common issue if _run is called from an already running asyncio loop
                # A more sophisticated solution might involve nest_asyncio or careful loop management.
                # For now, we log and return an error.
                logger.error(f"ReadFileTool _run called from a running event loop. This is not supported directly. Error for {relative_path_str}: {e}")
                return f"Error: ReadFileTool's synchronous _run method was called from an active event loop, which is problematic. Path: {relative_path_str}"
            logger.error(f"Error running ReadFileTool synchronously for {relative_path_str}: {e}", exc_info=True)
            return f"Error reading file (sync): {e}"
        except Exception as e:
            logger.error(f"Unexpected error running ReadFileTool synchronously for {relative_path_str}: {e}", exc_info=True)
            return f"Unexpected error reading file (sync): {e}"


    async def _arun(self, relative_path_str: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        return await read_file_content(relative_path_str, self.task_workspace)

# --- WriteFileTool Class Definition ---
class WriteFileTool(BaseTool):
    name: str = "write_file"
    description: str = (
        f"Use this tool ONLY to write or overwrite text content to a file within the current task's workspace. "
        f"Input MUST be a single string in the format 'relative_file_path:::text_content' "
        f"(e.g., 'results.txt:::Analysis complete.\\nFinal score: 95'). Handles subdirectory creation. "
        f"Do NOT use workspace path prefix in 'relative_file_path'."
    )
    task_workspace: Path

    def _run(self, input_str: str) -> str:
        logger.warning(f"WriteFileTool synchronously called for input: {input_str[:50]}... This may block.")
        try:
            return asyncio.run(write_to_file_in_task_workspace(input_str, self.task_workspace))
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e):
                logger.error(f"WriteFileTool _run called from a running event loop. Input: {input_str[:50]}. Error: {e}")
                return f"Error: WriteFileTool's synchronous _run method was called from an active event loop. Input: {input_str[:50]}"
            logger.error(f"Error running WriteFileTool synchronously for {input_str[:50]}: {e}", exc_info=True)
            return f"Error writing file (sync): {e}"
        except Exception as e:
            logger.error(f"Unexpected error running WriteFileTool synchronously for {input_str[:50]}: {e}", exc_info=True)
            return f"Unexpected error writing file (sync): {e}"

    async def _arun(self, input_str: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        return await write_to_file_in_task_workspace(input_str, self.task_workspace)


# --- TaskWorkspaceShellTool (already a class) ---
class TaskWorkspaceShellTool(BaseTool):
    name: str = "workspace_shell"
    description: str = (
        f"Use this tool ONLY to execute **non-interactive** shell commands directly within the **current task's dedicated workspace**. "
        f"Useful for running scripts (e.g., 'python my_script.py', 'Rscript analysis.R'), listing files (`ls -l`), checking file details (`wc`, `head`), etc. "
        f"Input MUST be a single, valid, non-interactive shell command string. Do NOT include path prefixes like 'workspace/task_id/'. "
        f"**DO NOT use this for 'pip install' or 'uv venv' or environment modifications.** Use the dedicated 'python_package_installer' tool for installations."
        f"Timeout: {settings.tool_shell_timeout}s. Max output length: {settings.tool_shell_max_output} chars."
    )
    task_workspace: Path
    timeout: int = settings.tool_shell_timeout
    max_output: int = settings.tool_shell_max_output

    def _run(self, command: str) -> str:
        logger.warning("Running TaskWorkspaceShellTool synchronously using _run.")
        try:
            # Try to get the current loop; if none, asyncio.run will create one.
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # This is tricky. If _run is called from a thread not owning the loop,
                # run_coroutine_threadsafe is better. If called from the loop's thread
                # but in a sync context that blocks the loop, it's still an issue.
                # Langchain often handles this if the tool primarily implements _arun.
                logger.warning("TaskWorkspaceShellTool _run: Event loop is running. Using asyncio.run_coroutine_threadsafe.")
                future = asyncio.run_coroutine_threadsafe(self._arun_internal(command), loop)
                return future.result(timeout=self.timeout + 5) # Add buffer to timeout
            else:
                logger.info("TaskWorkspaceShellTool _run: Event loop is not running. Using asyncio.run().")
                return asyncio.run(self._arun_internal(command))
        except RuntimeError as e:
             # If "cannot be called from a running event loop"
            if "no running event loop" in str(e).lower() or "cannot be called from a running event loop" in str(e).lower():
                 logger.warning(f"TaskWorkspaceShellTool _run: Runtime error with event loop, trying fresh asyncio.run: {e}")
                 return asyncio.run(self._arun_internal(command)) # Try a new loop
            logger.error(f"TaskWorkspaceShellTool _run: Runtime error: {e}", exc_info=True)
            return f"Error executing shell command (sync wrapper): {e}"
        except Exception as e:
            logger.error(f"TaskWorkspaceShellTool _run: Unexpected error: {e}", exc_info=True)
            return f"Unexpected error executing shell command (sync wrapper): {e}"


    async def _arun(self, command: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        return await self._arun_internal(command)

    async def _arun_internal(self, command: str) -> str: # Content of this method remains the same
        tool_name = self.name
        logger.info(f"Tool '{tool_name}' received raw input: '{command}'")
        if not isinstance(command, str) or not command.strip():
            logger.error(f"Tool '{tool_name}': Received invalid input. Expected a non-empty command string.")
            return "Error: Invalid input. Expected a non-empty command string."

        cwd = str(self.task_workspace.resolve())
        logger.info(f"Tool '{tool_name}' executing command: '{command}' in CWD: {cwd} (Timeout: {self.timeout}s)")
        process = None
        stdout_str = ""
        stderr_str = ""
        try:
            clean_command = command.strip().strip('`');
            if not clean_command:
                logger.error(f"Tool '{tool_name}': Command became empty after cleaning.")
                return "Error: Received empty command after cleaning."

            if '&&' in clean_command or '||' in clean_command or ';' in clean_command or '`' in clean_command or '$(' in clean_command:
                if '|' not in clean_command:
                    logger.warning(f"Tool '{tool_name}': Potentially unsafe shell characters detected in command: {clean_command}")

            process = await asyncio.create_subprocess_shell(
                clean_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            TIMEOUT_SECONDS = self.timeout
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=TIMEOUT_SECONDS)
            except asyncio.TimeoutError:
                logger.error(f"Tool '{tool_name}': Timeout executing command: {clean_command}")
                if process and process.returncode is None:
                    try: process.terminate()
                    except ProcessLookupError: pass
                    await process.wait()
                return f"Error: Command timed out after {TIMEOUT_SECONDS} seconds."

            stdout_str = stdout.decode(errors='replace').strip()
            stderr_str = stderr.decode(errors='replace').strip()
            return_code = process.returncode

            result = ""
            if stdout_str:
                result += f"STDOUT:\n{stdout_str}\n"

            if return_code != 0:
                logger.warning(f"Tool '{tool_name}' command '{clean_command}' failed. Exit: {return_code}. Stderr: {stderr_str}")
                result += f"STDERR:\n{stderr_str}\n" if stderr_str else ""
                result += f"ERROR: Command failed with exit code {return_code}"
            elif stderr_str:
                logger.info(f"Tool '{tool_name}' command '{clean_command}' succeeded (Exit: {return_code}) but produced STDERR:\n{stderr_str}")
                result += f"STDERR (Warnings/Info):\n{stderr_str}\n"

            logger.info(f"Tool '{tool_name}' command finished. Exit code: {return_code}. Reporting result length: {len(result)}")

            MAX_OUTPUT_LENGTH = self.max_output
            if len(result) > MAX_OUTPUT_LENGTH:
                result = result[:MAX_OUTPUT_LENGTH] + f"\n... (output truncated after {MAX_OUTPUT_LENGTH} characters)"

            return result.strip() if result.strip() else "Command executed successfully with no output to STDOUT or STDERR."

        except FileNotFoundError:
            cmd_part = clean_command.split()[0] if 'clean_command' in locals() and clean_command else "Unknown"
            logger.warning(f"Tool '{tool_name}' command not found: {cmd_part}")
            return f"Error: Command not found: {cmd_part}"
        except Exception as e:
            logger.error(f"Tool '{tool_name}': Error executing command '{clean_command if 'clean_command' in locals() else command}' in task workspace: {e}", exc_info=True)
            return f"Error executing command: {type(e).__name__}"
        finally:
            if process and process.returncode is None:
                logger.warning(f"Tool '{tool_name}': Shell process '{clean_command if 'clean_command' in locals() else command}' still running in finally block, attempting termination.")
                try:
                    process.terminate()
                    await process.wait()
                except ProcessLookupError: pass
                except Exception as term_e:
                    logger.error(f"Tool '{tool_name}': Error during final termination attempt of shell process: {term_e}")


async def install_python_package(package_specifiers_str: str) -> str: # Content remains the same
    tool_name = "python_package_installer"
    logger.info(f"Tool '{tool_name}' received raw input: '{package_specifiers_str}'")
    if not isinstance(package_specifiers_str, str) or not package_specifiers_str.strip():
        logger.error(f"Tool '{tool_name}': Received invalid input. Expected a non-empty string of package specifiers.")
        return "Error: Invalid input. Expected a non-empty string of package specifiers (space or comma separated)."

    timeout = settings.tool_installer_timeout
    individual_specs = [spec.strip() for spec in re.split(r'[\s,]+', package_specifiers_str) if spec.strip()]

    if not individual_specs:
        logger.error(f"Tool '{tool_name}': No valid package specifiers found after splitting input: '{package_specifiers_str}'.")
        return "Error: No package specifiers provided after cleaning the input string."

    results_summary = []
    all_successful = True

    python_executable = sys.executable
    installer_command_base_parts = [python_executable, "-m"]
    try:
        uv_check_process = await asyncio.create_subprocess_exec(python_executable, "-m", "uv", "--version", stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
        await uv_check_process.wait()
        if uv_check_process.returncode == 0:
            logger.info(f"Tool '{tool_name}': Detected uv, using 'uv pip install'.")
            installer_command_base_parts.extend(["uv", "pip"])
        else:
            logger.info(f"Tool '{tool_name}': uv check failed or not found, falling back to 'pip install'.")
            installer_command_base_parts.append("pip")
    except Exception as uv_err:
        logger.warning(f"Tool '{tool_name}': Error checking for uv, falling back to pip: {uv_err}")
        installer_command_base_parts.append("pip")

    for single_spec in individual_specs:
        cleaned_package_specifier = single_spec.strip().strip('\'"`')
        if not cleaned_package_specifier:
            results_summary.append(f"Skipped empty specifier derived from input '{single_spec}'.")
            continue

        if not PACKAGE_SPEC_REGEX.match(cleaned_package_specifier):
            logger.error(f"Tool '{tool_name}': Invalid package specifier format rejected: '{cleaned_package_specifier}'.")
            results_summary.append(f"Error: Invalid package specifier format for '{cleaned_package_specifier}'. Installation skipped.")
            all_successful = False
            continue

        if ';' in cleaned_package_specifier or '&' in cleaned_package_specifier or '|' in cleaned_package_specifier or '`' in cleaned_package_specifier or '$(' in cleaned_package_specifier:
            logger.error(f"Tool '{tool_name}': Potential command injection detected in package specifier: '{cleaned_package_specifier}'.")
            results_summary.append(f"Error: Invalid characters detected in package specifier '{cleaned_package_specifier}'. Installation skipped.")
            all_successful = False
            continue

        logger.info(f"Tool '{tool_name}': Requesting install for package: '{cleaned_package_specifier}' (Timeout: {timeout}s)")

        command_to_run = installer_command_base_parts + ["install", cleaned_package_specifier]
        logger.info(f"Tool '{tool_name}': Executing installation command: {' '.join(command_to_run)}")

        process = None
        try:
            process = await asyncio.create_subprocess_exec(*command_to_run, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            TIMEOUT_SECONDS = timeout
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=TIMEOUT_SECONDS)
            except asyncio.TimeoutError:
                logger.error(f"Tool '{tool_name}': Timeout installing package: {cleaned_package_specifier}")
                if process and process.returncode is None:
                    try: process.terminate()
                    except ProcessLookupError: pass
                    await process.wait()
                results_summary.append(f"Error installing '{cleaned_package_specifier}': Package installation timed out after {TIMEOUT_SECONDS} seconds.")
                all_successful = False
                continue

            stdout_str = stdout.decode(errors='replace').strip()
            stderr_str = stderr.decode(errors='replace').strip()
            return_code = process.returncode

            log_output_details = ""
            if stdout_str: log_output_details += f"--- STDOUT for {cleaned_package_specifier} ---\n{stdout_str}\n"
            if stderr_str: log_output_details += f"--- STDERR for {cleaned_package_specifier} ---\n{stderr_str}\n"

            if return_code == 0:
                logger.info(f"Tool '{tool_name}': Successfully installed package: {cleaned_package_specifier}")
                success_msg = f"Successfully installed '{cleaned_package_specifier}'."
                if stderr_str:
                    success_msg += f" Notes/Warnings: {stderr_str[:200]}{'...' if len(stderr_str)>200 else ''}"
                results_summary.append(success_msg)
                if log_output_details: logger.debug(f"Tool '{tool_name}': Full log for '{cleaned_package_specifier}':\n{log_output_details}")
            else:
                logger.error(f"Tool '{tool_name}': Failed to install package: {cleaned_package_specifier}. Exit code: {return_code}. Stderr: {stderr_str}")
                error_details_for_summary = stderr_str if stderr_str else stdout_str
                results_summary.append(f"Error installing '{cleaned_package_specifier}': Failed (Code: {return_code}). Details: {error_details_for_summary[:300]}{'...' if len(error_details_for_summary)>300 else ''}")
                all_successful = False
                if log_output_details: logger.debug(f"Tool '{tool_name}': Full log for failed '{cleaned_package_specifier}':\n{log_output_details}")

        except FileNotFoundError:
            logger.error(f"Tool '{tool_name}': Error installing package: '{installer_command_base_parts[0]}' command not found.")
            results_summary.append(f"Error installing '{cleaned_package_specifier}': Installer command ('{installer_command_base_parts[0]}') not found.")
            all_successful = False
        except Exception as e:
            logger.error(f"Tool '{tool_name}': Error installing package '{cleaned_package_specifier}': {e}", exc_info=True)
            results_summary.append(f"Error installing '{cleaned_package_specifier}': {type(e).__name__}.")
            all_successful = False
        finally:
            if process and process.returncode is None:
                logger.warning(f"Tool '{tool_name}': Installer process '{' '.join(command_to_run)}' still running in finally block, attempting termination.")
                try: process.terminate(); await process.wait()
                except ProcessLookupError: pass
                except Exception as term_e: logger.error(f"Tool '{tool_name}': Error during final termination attempt of installer: {term_e}")

    final_message = "Package installation process finished.\n" + "\n".join(results_summary)
    if not all_successful:
        return f"FAIL::python_package_installer:::One or more packages failed to install. Full log:\n{final_message}"
    return final_message


async def search_pubmed(query: str) -> str: # Content remains the same
    tool_name = "pubmed_search"
    logger.info(f"Tool '{tool_name}' received raw input: '{query}'")
    if not isinstance(query, str) or not query.strip():
        logger.error(f"Tool '{tool_name}': Received invalid input. Expected a non-empty search query string.")
        return "Error: Invalid input. Expected a non-empty search query string."
    entrez_email = settings.entrez_email
    default_max_results = settings.tool_pubmed_default_max_results
    max_snippet_len = settings.tool_pubmed_max_snippet

    if not entrez_email:
        logger.error(f"Tool '{tool_name}': Entrez email not configured in settings.")
        return "Error: PubMed Search tool is not configured (Missing Entrez email)."
    Entrez.email = entrez_email

    cleaned_query = query.strip()
    logger.info(f"Tool '{tool_name}': Searching PubMed with query: '{cleaned_query}' (Default Max: {default_max_results})")

    current_max_results = default_max_results
    match = re.search(r"\smax_results=(\d+)\b", cleaned_query, re.IGNORECASE)
    if match:
        try:
            num_res = int(match.group(1))
            current_max_results = min(max(1, num_res), 20)
            cleaned_query = cleaned_query[:match.start()] + cleaned_query[match.end():]
            cleaned_query = cleaned_query.strip()
            logger.info(f"Tool '{tool_name}': Using max_results={current_max_results} from query. Effective query: '{cleaned_query}'")
        except ValueError:
            logger.warning(f"Tool '{tool_name}': Invalid max_results value in query '{query}', using default {current_max_results}.")

    if not cleaned_query:
        logger.error(f"Tool '{tool_name}': Query became empty after processing max_results.")
        return "Error: No search query provided after processing options."

    try:
        handle = await asyncio.to_thread(Entrez.esearch, db="pubmed", term=cleaned_query, retmax=str(current_max_results), sort="relevance")
        search_results = await asyncio.to_thread(Entrez.read, handle)
        await asyncio.to_thread(handle.close)

        id_list = search_results["IdList"]
        if not id_list:
            logger.info(f"Tool '{tool_name}': No results found on PubMed for query: '{cleaned_query}'")
            return f"No results found on PubMed for query: '{cleaned_query}'"

        handle = await asyncio.to_thread(Entrez.efetch, db="pubmed", id=id_list, rettype="abstract", retmode="xml")
        records = await asyncio.to_thread(Entrez.read, handle)
        await asyncio.to_thread(handle.close)

        summaries = []
        pubmed_articles = records.get('PubmedArticle', [])

        if not isinstance(pubmed_articles, list):
            if isinstance(pubmed_articles, dict):
                pubmed_articles = [pubmed_articles]
            else:
                logger.warning(f"Tool '{tool_name}': Unexpected PubMed fetch format for query '{cleaned_query}'. Records: {str(records)[:500]}")
                return "Error: Could not parse PubMed results (unexpected format)."

        for i, record in enumerate(pubmed_articles):
            if i >= current_max_results: break

            pmid = "Unknown PMID"
            try:
                medline_citation = record.get('MedlineCitation', {})
                article = medline_citation.get('Article', {})
                pmid = str(medline_citation.get('PMID', 'Unknown PMID'))

                title_node = article.get('ArticleTitle', 'No Title')
                title = str(title_node) if isinstance(title_node, str) else title_node.get('#text', 'No Title Available') if isinstance(title_node, dict) else 'No Title Available'

                authors_list = article.get('AuthorList', [])
                author_names = []
                if isinstance(authors_list, list):
                    for author_node in authors_list:
                        if isinstance(author_node, dict):
                            last_name = author_node.get('LastName', '')
                            initials = author_node.get('Initials', '')
                            if last_name:
                                author_names.append(f"{last_name} {initials}".strip())
                authors_str = ", ".join(author_names) if author_names else "No Authors Listed"

                abstract_text_parts = []
                abstract_node = article.get('Abstract', {}).get('AbstractText', [])
                if isinstance(abstract_node, str):
                    abstract_text_parts.append(abstract_node)
                elif isinstance(abstract_node, list):
                    for part in abstract_node:
                        if isinstance(part, str):
                            abstract_text_parts.append(part)
                        elif hasattr(part, 'attributes') and 'Label' in part.attributes:
                            abstract_text_parts.append(f"\n**{part.attributes['Label']}**: {str(part)}")
                        elif isinstance(part, dict) and '#text' in part:
                             abstract_text_parts.append(part['#text'])
                        else:
                             abstract_text_parts.append(str(part))

                full_abstract = " ".join(filter(None, abstract_text_parts)).strip()
                if not full_abstract: full_abstract = "No Abstract Available"

                abstract_snippet = full_abstract[:max_snippet_len]
                if len(full_abstract) > max_snippet_len: abstract_snippet += "..."

                doi = None
                article_ids = record.get('PubmedData', {}).get('ArticleIdList', [])
                if isinstance(article_ids, list):
                    for article_id_node in article_ids:
                        if hasattr(article_id_node, 'attributes') and article_id_node.attributes.get('IdType') == 'doi':
                            doi = str(article_id_node)
                            break
                        elif isinstance(article_id_node, dict) and article_id_node.get('IdType') == 'doi':
                            doi = article_id_node.get('#text')
                            break

                link = f"https://doi.org/{doi}" if doi else f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                link_text = f"DOI:{doi}" if doi else f"PMID:{pmid}"

                summaries.append(f"**Result {i+1}:**\n**Title:** {title}\n**Authors:** {authors_str}\n**Link:** [{link_text}]({link})\n**Abstract Snippet:** {abstract_snippet}\n---")

            except Exception as parse_err:
                logger.error(f"Tool '{tool_name}': Error parsing PubMed record {i+1} (PMID: {pmid}) for query '{cleaned_query}': {parse_err}", exc_info=True)
                summaries.append(f"**Result {i+1}:**\nError parsing record (PMID: {pmid}).\n---")

        return "\n".join(summaries) if summaries else "No valid PubMed records processed."

    except HTTPError as e:
        logger.error(f"Tool '{tool_name}': HTTP Error fetching PubMed data for query '{cleaned_query}': {e.code} {e.reason}")
        return f"Error: Failed to fetch data from PubMed (HTTP Error {e.code}). Check network or NCBI status."
    except Exception as e:
        logger.error(f"Tool '{tool_name}': Error searching PubMed for '{cleaned_query}': {e}", exc_info=True)
        return f"Error: An unexpected error occurred during PubMed search: {type(e).__name__}"

PACKAGE_SPEC_REGEX = re.compile(r"^[a-zA-Z0-9_.-]+(?:\[[a-zA-Z0-9_,-]+\])?(?:[=<>!~]=?\s*[a-zA-Z0-9_.*-]+)?$")

try:
    python_repl_utility = PythonREPL()
except ImportError:
    logger.warning("Could not import PythonREPL. The Python_REPL tool will not be available.")
    python_repl_utility = None

def get_dynamic_tools(current_task_id: Optional[str]) -> List[BaseTool]:
    """
    Returns a list of BaseTool instances available for the agent.
    Combines tools loaded from configuration with manually instantiated tools.
    """
    dynamically_loaded_tools: List[BaseTool] = []
    try:
        # Load tools defined in tool_config.json (e.g., TavilyAPISearchTool)
        dynamically_loaded_tools = load_tools_from_config() # Assumes tool_loader.CONFIG_FILE_PATH is correct
        logger.info(f"Dynamically loaded {len(dynamically_loaded_tools)} tools from config for task '{current_task_id or 'N/A'}'.")
    except ToolLoadingError as e:
        logger.error(f"ToolLoadingError in get_dynamic_tools: {e}. Proceeding with manually defined tools only.")
    except Exception as e:
        logger.error(f"Unexpected error loading tools from config: {e}. Proceeding with manually defined tools.", exc_info=True)

    # Initialize the final list of tools with those loaded from config
    tools: List[BaseTool] = list(dynamically_loaded_tools)

    # --- Fallback Search & Other Manually Instantiated Tools ---
    # (These will be migrated to tool_config.json in later phases)

    # Check if Tavily was loaded successfully, if not, add DuckDuckGo as fallback
    tavily_loaded = any(tool.name == "tavily_search_api" for tool in tools)
    if not tavily_loaded and (hasattr(settings, 'tavily_api_key') and settings.tavily_api_key):
        logger.warning("Tavily API key is set, but TavilyAPISearchTool was not loaded from config. Check config file and loader logs.")
    
    # Add DuckDuckGo if Tavily isn't configured/loaded OR as an explicit fallback strategy
    # For Phase 1 of tool refactor, let's keep DDG if Tavily isn't loaded by the new system.
    if not tavily_loaded:
        logger.info("Tavily Search tool not loaded from config. Adding DuckDuckGoSearchRun as a search tool.")
        tools.append(DuckDuckGoSearchRun(description=(
            "A wrapper around DuckDuckGo Search. Useful for when you need to answer questions "
            "about current events or things you don't know. Input MUST be a search query string."
        )))

    # DeepResearchTool (manual addition for now, can be moved to config later)
    # Check if it was loaded dynamically before adding manually
    deep_research_tool_loaded = any(tool.name == "deep_research_synthesizer" for tool in tools)
    if not deep_research_tool_loaded:
        try:
            deep_research_tool = DeepResearchTool() # Assumes its __init__ handles sub-tool setup
            tools.append(deep_research_tool)
            logger.info(f"Manually added DeepResearchTool for task '{current_task_id or 'N/A'}'.")
        except Exception as e:
            logger.error(f"Failed to manually initialize DeepResearchTool: {e}", exc_info=True)


    # Stateless tools (can be moved to config later)
    stateless_tools_to_add = [
        Tool.from_function(
            func=fetch_and_parse_url,
            name="web_page_reader",
            description=(
                f"Use this tool ONLY to fetch and extract the main text content from a given URL. "
                f"Input MUST be a single, valid URL string (e.g., 'https://example.com/page'). "
                f"Max content length: {settings.tool_web_reader_max_length} chars."
            ),
            coroutine=fetch_and_parse_url # Ensure the async version is correctly specified
        ),
        Tool.from_function(
            func=install_python_package,
            name="python_package_installer",
            description=(
                f"Use this tool ONLY to install Python packages into the environment using 'uv pip install' or 'pip install'. "
                f"Input MUST be a string of one or more package specifiers, separated by spaces or commas "
                f"(e.g., 'numpy pandas', 'matplotlib==3.5.0', 'scikit-learn>=1.0 bokeh'). "
                f"**SECURITY WARNING:** This installs packages into the main environment. Avoid installing untrusted packages. "
                f"Timeout: {settings.tool_installer_timeout}s."
            ),
            coroutine=install_python_package # Ensure the async version is correctly specified
        ),
    ]
    for st_tool in stateless_tools_to_add:
        if not any(t.name == st_tool.name for t in tools): # Avoid duplicates if already loaded from config
            tools.append(st_tool)

    if settings.entrez_email:
        if not any(t.name == "pubmed_search" for t in tools):
            tools.append(
                Tool.from_function(
                    func=search_pubmed,
                    name="pubmed_search",
                    description=(
                        f"Use this tool ONLY to search for biomedical literature abstracts on PubMed. "
                        f"Input MUST be a search query string (e.g., 'CRISPR gene editing cancer therapy'). "
                        f"You can optionally append ' max_results=N' (space required before 'max_results') to the end of the query "
                        f"string to specify the number of results (default is {settings.tool_pubmed_default_max_results}, max is 20). "
                        f"Returns formatted summaries including title, authors, link (DOI or PMID), and abstract snippet "
                        f"(max {settings.tool_pubmed_max_snippet} chars)."
                    ),
                    coroutine=search_pubmed # Ensure the async version is correctly specified
                )
            )
    else:
        logger.warning("Skipping PubMed tool creation as ENTREZ_EMAIL is not set.")

    if python_repl_utility:
        if not any(t.name == "Python_REPL" for t in tools):
            tools.append(Tool.from_function(
                func=python_repl_utility.run, # PythonREPL's run might be sync, check its async capabilities if needed for full async flow
                name="Python_REPL",
                description=(
                    "Executes a single, simple Python expression or a very short, self-contained snippet of Python code. "
                    "Input MUST be valid Python code that can be evaluated as a single block. "
                    "Use this for straightforward operations like basic arithmetic (e.g., '2 + 2', '10 / 5 * 2'), "
                    "simple string manipulations, or quick checks. "
                    "**DO NOT use this for defining multi-line functions or classes, complex scripts, file I/O, or installing packages.** "
                    "For writing and then running Python scripts, use the `write_file` tool followed by the `workspace_shell` "
                    "tool (e.g., 'python your_script_name.py'). "
                    "Output will be the result of the expression or `print()` statements. "
                    "**Security Note:** This executes code directly in the backend environment. Be extremely cautious."
                )
                # is_coroutine=False (or check if PythonREPL().arun exists and use that if it does)
            ))
    else:
        logger.warning("Python REPL tool not created (utility unavailable).")

    # Task-specific tools that require current_task_id for workspace path
    if not current_task_id:
        logger.warning("No active task ID provided to get_dynamic_tools. Workspace-dependent tools (read_file, write_file, workspace_shell) will not be added if not already task-agnostically loaded from config.")
    else:
        try:
            task_workspace = get_task_workspace_path(current_task_id, create_if_not_exists=True)
            logger.info(f"Configuring task-specific tools for workspace: {task_workspace}")

            task_specific_tools_to_add_manually = [
                ReadFileTool(task_workspace=task_workspace),
                WriteFileTool(task_workspace=task_workspace),
                TaskWorkspaceShellTool(task_workspace=task_workspace),
            ]
            for ts_tool in task_specific_tools_to_add_manually:
                 if not any(t.name == ts_tool.name for t in tools): # Avoid duplicates
                    tools.append(ts_tool)

        except (ValueError, OSError) as e:
            logger.error(f"Failed to get or create task workspace for {current_task_id}: {e}. "
                         f"Workspace-dependent tools will not be added manually.")

    final_tool_names = [tool.name for tool in tools]
    logger.info(f"Final list of tools for task '{current_task_id or 'N/A'}': {final_tool_names}")
    return tools
