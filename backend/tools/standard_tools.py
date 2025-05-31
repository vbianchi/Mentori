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

# LangChain Tool Imports
from langchain_core.tools import Tool, BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
# from langchain_community.tools import DuckDuckGoSearchRun # <<< REMOVED
# PythonREPL is now handled by PythonREPLTool class
from Bio import Entrez
from urllib.error import HTTPError
try:
    import pypdf
    logger_pypdf = logging.getLogger(__name__)
except ImportError:
    logger_pypdf = logging.getLogger(__name__)
    logger_pypdf.warning("pypdf not installed. PDF reading functionality will be unavailable.")
    pypdf = None

# Project Imports
from backend.config import settings
from backend.tool_loader import load_tools_from_config, ToolLoadingError
# Specific tool class imports are generally not needed here if primarily loaded via config
from backend.tools.tavily_search_tool import TavilyAPISearchTool # Kept for DeepResearchTool if it needs it
from backend.tools.deep_research_tool import DeepResearchTool # Kept for manual add for now


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
    # This function remains unchanged
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

# Helper function fetch_and_parse_url remains (used by WebPageReaderTool)
async def fetch_and_parse_url(url: str) -> str:
    tool_name = "web_page_reader_logic"; logger.info(f"Helper '{tool_name}' received raw input: '{url}'")
    if not isinstance(url, str) or not url.strip(): logger.error(f"Helper '{tool_name}' received invalid input."); return "Error: Invalid input. Expected a non-empty URL string."
    max_length = settings.tool_web_reader_max_length; timeout = settings.tool_web_reader_timeout
    HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    clean_url = url.strip().replace('\n', '').replace('\r', '').replace('\t', '').strip('`')
    if not clean_url: logger.error(f"Helper '{tool_name}' input resulted in empty URL after cleaning."); return "Error: Received an empty URL after cleaning."
    if not re.match(r"^[a-zA-Z]+://", clean_url): logger.info(f"Helper '{tool_name}': No scheme found, prepending https:// to '{clean_url}'"); clean_url = f"https://{clean_url}"
    logger.info(f"Helper '{tool_name}' attempting to fetch and parse cleaned URL: {clean_url} (Timeout: {timeout}s)")
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=HEADERS) as client:
            response = await client.get(clean_url); response.raise_for_status()
            content_type = response.headers.get("content-type", "").lower()
            if "html" not in content_type: logger.warning(f"Helper '{tool_name}': Cannot parse content type '{content_type}' for URL {clean_url}"); return f"Error: Cannot parse content type '{content_type}'. Only HTML is supported."
            html_content = response.text; soup = BeautifulSoup(html_content, 'lxml')
            content_tags = soup.find('article') or soup.find('main') or soup.find('body')
            if content_tags: texts = content_tags.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td', 'th']); extracted_text = "\n".join(t.get_text(strip=True) for t in texts if t.get_text(strip=True))
            else: extracted_text = soup.get_text(separator="\n", strip=True)
            if not extracted_text: logger.warning(f"Helper '{tool_name}': Could not extract meaningful text from {clean_url}"); return "Error: Could not extract meaningful text from the page."
            truncated_text = extracted_text[:max_length]
            if len(extracted_text) > max_length: truncated_text += "..."
            logger.info(f"Helper '{tool_name}': Successfully extracted ~{len(truncated_text)} chars from {clean_url}")
            return truncated_text
    except httpx.TimeoutException: logger.error(f"Helper '{tool_name}': Timeout fetching {clean_url}"); return f"Error: Timeout fetching URL."
    except httpx.InvalidURL as e: logger.error(f"Helper '{tool_name}': Invalid URL format for {clean_url}: {e}"); return f"Error: Invalid URL format: {e}"
    except httpx.RequestError as e: logger.error(f"Helper '{tool_name}': Request error fetching {clean_url}: {e}"); return f"Error: Could not fetch URL: {e}"
    except httpx.HTTPStatusError as e: logger.error(f"Helper '{tool_name}': HTTP error fetching {clean_url}: {e.response.status_code}"); return f"Error: HTTP {e.response.status_code} fetching URL."
    except ImportError: logger.error(f"Helper '{tool_name}': lxml not installed."); return "Error: HTML parser (lxml) not installed."
    except Exception as e: logger.error(f"Helper '{tool_name}': Error parsing {clean_url}: {e}", exc_info=True); return f"Error parsing URL: {e}"

# Helper function write_to_file_in_task_workspace remains
async def write_to_file_in_task_workspace(input_str: str, task_workspace: Path) -> str:
    tool_name = "write_file_logic"; logger.debug(f"Helper '{tool_name}': Raw input_str: '{input_str[:200]}{'...' if len(input_str) > 200 else ''}' for workspace: {task_workspace.name}")
    if not isinstance(input_str, str) or ':::' not in input_str: logger.error(f"Helper '{tool_name}' received invalid input format."); return "Error: Invalid input format. Expected 'file_path:::text_content'."
    relative_path_str = ""
    try:
        parts = input_str.split(':::', 1);
        if len(parts) != 2: logger.error(f"Helper '{tool_name}': Input split failed."); return "Error: Invalid input format after splitting."
        relative_path_str = parts[0].strip().strip('\'"`'); raw_text_content = parts[1]
        logger.debug(f"Helper '{tool_name}': Parsed relative_path_str: '{relative_path_str}', raw_text_content length: {len(raw_text_content)}")
        cleaned_relative_path = relative_path_str
        if cleaned_relative_path.startswith((f"workspace/{task_workspace.name}/", f"workspace\\{task_workspace.name}\\" ,f"{task_workspace.name}/", f"{task_workspace.name}\\")):
            cleaned_relative_path = re.sub(r"^[\\/]?(workspace[\\/])?%s[\\/]" % re.escape(task_workspace.name), "", cleaned_relative_path)
            logger.info(f"Helper '{tool_name}': Stripped workspace/task prefix, using relative path: {cleaned_relative_path}")
        elif cleaned_relative_path.startswith(("workspace/", "workspace\\")):
            cleaned_relative_path = re.sub(r"^[\\/]?(workspace[\\/])+", "", cleaned_relative_path)
            logger.info(f"Helper '{tool_name}': Stripped generic 'workspace/' prefix, using: {cleaned_relative_path}")
        if not cleaned_relative_path: logger.error(f"Helper '{tool_name}': File path became empty after cleaning."); return "Error: File path cannot be empty after cleaning."
        try: text_content = codecs.decode(raw_text_content, 'unicode_escape'); logger.debug(f"Helper '{tool_name}': Decoded unicode escapes.")
        except Exception as decode_err: logger.warning(f"Helper '{tool_name}': Could not decode unicode escapes, using raw content: {decode_err}"); text_content = raw_text_content
        text_content = re.sub(r"^```[a-zA-Z]*\s*\n", "", text_content); text_content = re.sub(r"\n```$", "", text_content); text_content = text_content.strip()
        relative_path = Path(cleaned_relative_path)
        if relative_path.is_absolute() or '..' in relative_path.parts: logger.error(f"Helper '{tool_name}': Security Error - Invalid file path '{cleaned_relative_path}' attempts traversal."); return f"Error: Invalid file path '{cleaned_relative_path}'. Path must be relative and within the workspace."
        full_path = task_workspace.joinpath(relative_path).resolve()
        logger.info(f"Helper '{tool_name}': Attempting to write to resolved full_path: '{full_path}'")
        if not full_path.is_relative_to(task_workspace.resolve()): logger.error(f"Helper '{tool_name}': Security Error - Write path resolves outside task workspace!"); return "Error: File path resolves outside the designated task workspace."
        full_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(full_path, mode='w', encoding='utf-8') as f: await f.write(text_content)
        logger.info(f"Helper '{tool_name}': Successfully wrote {len(text_content)} bytes to '{full_path}'.")
        return f"SUCCESS::write_file:::{cleaned_relative_path}"
    except Exception as e: logger.error(f"Helper '{tool_name}': Error writing file '{relative_path_str}': {e}", exc_info=True); return f"Error: Failed to write file '{relative_path_str}'. Reason: {type(e).__name__}"

# Helper function read_file_content remains
async def read_file_content(relative_path_str: str, task_workspace: Path) -> str:
    tool_name = "read_file_logic"; logger.debug(f"Helper '{tool_name}': Raw relative_path_str: '{relative_path_str[:100]}{'...' if len(relative_path_str) > 100 else ''}' in workspace: {task_workspace.name}")
    if not isinstance(relative_path_str, str) or not relative_path_str.strip(): logger.error(f"Helper '{tool_name}': Received invalid input."); return "Error: Invalid input. Expected a non-empty relative file path string."
    first_line = relative_path_str.splitlines()[0] if relative_path_str else ""; cleaned_relative_path = first_line.strip().strip('\'"`')
    logger.info(f"Helper '{tool_name}': Cleaned relative_path for reading: '{cleaned_relative_path}'")
    if not cleaned_relative_path: logger.error(f"Helper '{tool_name}': File path became empty after cleaning."); return "Error: File path cannot be empty after cleaning."
    relative_path = Path(cleaned_relative_path)
    if relative_path.is_absolute() or '..' in relative_path.parts: logger.error(f"Helper '{tool_name}': Security Error - Invalid read file path '{cleaned_relative_path}'."); return f"Error: Invalid file path '{cleaned_relative_path}'. Path must be relative and within the workspace."
    full_path = task_workspace.joinpath(relative_path).resolve()
    logger.info(f"Helper '{tool_name}': Attempting to read resolved full_path: '{full_path}'")
    if not full_path.is_relative_to(task_workspace.resolve()): logger.error(f"Helper '{tool_name}': Security Error - Read path resolves outside task workspace!"); return "Error: File path resolves outside the designated task workspace."
    if not full_path.exists(): logger.warning(f"Helper '{tool_name}': File not found at {full_path}"); return f"Error: File not found at path '{cleaned_relative_path}'."
    if not full_path.is_file(): logger.warning(f"Helper '{tool_name}': Path is not a file: {full_path}"); return f"Error: Path '{cleaned_relative_path}' is not a file."
    file_extension = full_path.suffix.lower(); content = ""
    try:
        if file_extension == ".pdf":
            if pypdf is None: logger.error(f"Helper '{tool_name}': Attempted to read PDF, but pypdf library is not installed."); return "Error: PDF reading library (pypdf) is not installed on the server."
            def read_pdf_sync():
                extracted_text = ""
                try:
                    reader = pypdf.PdfReader(str(full_path)); num_pages = len(reader.pages)
                    logger.info(f"Helper '{tool_name}': Reading {num_pages} pages from PDF: {full_path.name}")
                    for i, page in enumerate(reader.pages):
                        try:
                            page_text = page.extract_text()
                            if page_text:
                                extracted_text += page_text + "\n"
                        except Exception as page_err:
                            logger.warning(f"Helper '{tool_name}': Error extracting text from page {i+1} of {full_path.name}: {page_err}")
                            extracted_text += f"\n--- Error reading page {i+1} ---\n"
                    return extracted_text.strip()
                except pypdf.errors.PdfReadError as pdf_err: logger.error(f"Helper '{tool_name}': Error reading PDF file {full_path.name}: {pdf_err}"); raise RuntimeError(f"Error reading PDF: {pdf_err}") from pdf_err
                except Exception as e: logger.error(f"Helper '{tool_name}': Unexpected error reading PDF {full_path.name}: {e}", exc_info=True); raise RuntimeError(f"Unexpected error reading PDF: {e}") from e
            loop = asyncio.get_running_loop(); content = await loop.run_in_executor(None, read_pdf_sync)
            actual_length = len(content); logger.info(f"Helper '{tool_name}': Successfully read {actual_length} chars from PDF '{cleaned_relative_path}'.")
            warning_length = settings.tool_pdf_reader_warning_length
            if actual_length > warning_length: content += f"\n\n[SYSTEM WARNING: Full PDF content read ({actual_length} chars), exceeds warning threshold of {warning_length} chars.]"; logger.warning(f"Helper '{tool_name}': PDF content length ({actual_length}) exceeds warning threshold ({warning_length}).")
        elif file_extension in TEXT_EXTENSIONS:
            async with aiofiles.open(full_path, mode='r', encoding='utf-8', errors='ignore') as f: content = await f.read()
            logger.info(f"Helper '{tool_name}': Successfully read {len(content)} chars from text file '{cleaned_relative_path}'.")
        else: logger.warning(f"Helper '{tool_name}': Unsupported file extension '{file_extension}' for file '{cleaned_relative_path}'"); return f"Error: Cannot read file. Unsupported file extension: '{file_extension}'. Supported text: {', '.join(TEXT_EXTENSIONS)}, .pdf"
        return content
    except RuntimeError as rt_err: return str(rt_err)
    except Exception as e: logger.error(f"Helper '{tool_name}': Error reading file '{cleaned_relative_path}': {e}", exc_info=True); return f"Error: Failed to read file '{cleaned_relative_path}'. Reason: {type(e).__name__}"


# --- Tool Class Definitions (Task-Specific) ---
class ReadFileTool(BaseTool):
    name: str = "read_file"; description: str = (...); task_workspace: Path
    def _run(self, relative_path_str: str) -> str:
        logger.warning(f"ReadFileTool synchronously called for: {relative_path_str}. This may block if the underlying operation is truly async.")
        try: return asyncio.run(read_file_content(relative_path_str, self.task_workspace))
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e): logger.error(f"ReadFileTool _run called from a running event loop. Error for {relative_path_str}: {e}"); return f"Error: ReadFileTool's synchronous _run method was called from an active event loop. Path: {relative_path_str}"
            logger.error(f"Error running ReadFileTool synchronously for {relative_path_str}: {e}", exc_info=True); return f"Error reading file (sync): {e}"
        except Exception as e: logger.error(f"Unexpected error running ReadFileTool synchronously for {relative_path_str}: {e}", exc_info=True); return f"Unexpected error reading file (sync): {e}"
    async def _arun(self, relative_path_str: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        return await read_file_content(relative_path_str, self.task_workspace)

class WriteFileTool(BaseTool):
    name: str = "write_file"; description: str = (...); task_workspace: Path
    def _run(self, input_str: str) -> str:
        logger.warning(f"WriteFileTool synchronously called for input: {input_str[:50]}... This may block.")
        try: return asyncio.run(write_to_file_in_task_workspace(input_str, self.task_workspace))
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e): logger.error(f"WriteFileTool _run called from a running event loop. Input: {input_str[:50]}. Error: {e}"); return f"Error: WriteFileTool's synchronous _run method was called from an active event loop. Input: {input_str[:50]}"
            logger.error(f"Error running WriteFileTool synchronously for {input_str[:50]}: {e}", exc_info=True); return f"Error writing file (sync): {e}"
        except Exception as e: logger.error(f"Unexpected error running WriteFileTool synchronously for {input_str[:50]}: {e}", exc_info=True); return f"Unexpected error writing file (sync): {e}"
    async def _arun(self, input_str: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        return await write_to_file_in_task_workspace(input_str, self.task_workspace)

class TaskWorkspaceShellTool(BaseTool):
    name: str = "workspace_shell"; description: str = (...); task_workspace: Path; timeout: int = settings.tool_shell_timeout; max_output: int = settings.tool_shell_max_output
    def _run(self, command: str) -> str: # ... (content remains the same)
        logger.warning("Running TaskWorkspaceShellTool synchronously using _run.")
        try:
            loop = asyncio.get_event_loop();
            if loop.is_running(): logger.warning("TaskWorkspaceShellTool _run: Event loop is running. Using asyncio.run_coroutine_threadsafe."); future = asyncio.run_coroutine_threadsafe(self._arun_internal(command), loop); return future.result(timeout=self.timeout + 5)
            else: logger.info("TaskWorkspaceShellTool _run: Event loop is not running. Using asyncio.run()."); return asyncio.run(self._arun_internal(command))
        except RuntimeError as e:
            if "no running event loop" in str(e).lower() or "cannot be called from a running event loop" in str(e).lower(): logger.warning(f"TaskWorkspaceShellTool _run: Runtime error with event loop, trying fresh asyncio.run: {e}"); return asyncio.run(self._arun_internal(command))
            logger.error(f"TaskWorkspaceShellTool _run: Runtime error: {e}", exc_info=True); return f"Error executing shell command (sync wrapper): {e}"
        except Exception as e: logger.error(f"TaskWorkspaceShellTool _run: Unexpected error: {e}", exc_info=True); return f"Unexpected error executing shell command (sync wrapper): {e}"
    async def _arun(self, command: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str: return await self._arun_internal(command)
    async def _arun_internal(self, command: str) -> str: # ... (content remains the same)
        tool_name = self.name; logger.info(f"Tool '{tool_name}' received raw input: '{command}'")
        if not isinstance(command, str) or not command.strip(): logger.error(f"Tool '{tool_name}': Received invalid input."); return "Error: Invalid input. Expected a non-empty command string."
        cwd = str(self.task_workspace.resolve()); logger.info(f"Tool '{tool_name}' executing command: '{command}' in CWD: {cwd} (Timeout: {self.timeout}s)")
        process = None; stdout_str = ""; stderr_str = ""
        try:
            clean_command = command.strip().strip('`');
            if not clean_command: logger.error(f"Tool '{tool_name}': Command became empty after cleaning."); return "Error: Received empty command after cleaning."
            if '&&' in clean_command or '||' in clean_command or ';' in clean_command or '`' in clean_command or '$(' in clean_command:
                if '|' not in clean_command: logger.warning(f"Tool '{tool_name}': Potentially unsafe shell characters detected: {clean_command}")
            process = await asyncio.create_subprocess_shell(clean_command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=cwd)
            TIMEOUT_SECONDS = self.timeout
            try: stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=TIMEOUT_SECONDS)
            except asyncio.TimeoutError:
                logger.error(f"Tool '{tool_name}': Timeout executing command: {clean_command}")
                if process and process.returncode is None:
                    try: process.terminate()
                    except ProcessLookupError: pass
                    await process.wait()
                return f"Error: Command timed out after {TIMEOUT_SECONDS} seconds."
            stdout_str = stdout.decode(errors='replace').strip(); stderr_str = stderr.decode(errors='replace').strip(); return_code = process.returncode
            result = ""
            if stdout_str: result += f"STDOUT:\n{stdout_str}\n"
            if return_code != 0: logger.warning(f"Tool '{tool_name}' command '{clean_command}' failed. Exit: {return_code}. Stderr: {stderr_str}"); result += f"STDERR:\n{stderr_str}\n" if stderr_str else ""; result += f"ERROR: Command failed with exit code {return_code}"
            elif stderr_str: logger.info(f"Tool '{tool_name}' command '{clean_command}' succeeded but produced STDERR:\n{stderr_str}"); result += f"STDERR (Warnings/Info):\n{stderr_str}\n"
            logger.info(f"Tool '{tool_name}' command finished. Exit code: {return_code}. Result length: {len(result)}")
            MAX_OUTPUT_LENGTH = self.max_output
            if len(result) > MAX_OUTPUT_LENGTH: result = result[:MAX_OUTPUT_LENGTH] + f"\n... (output truncated after {MAX_OUTPUT_LENGTH} characters)"
            return result.strip() if result.strip() else "Command executed successfully with no output to STDOUT or STDERR."
        except FileNotFoundError: cmd_part = clean_command.split()[0] if 'clean_command' in locals() and clean_command else "Unknown"; logger.warning(f"Tool '{tool_name}' command not found: {cmd_part}"); return f"Error: Command not found: {cmd_part}"
        except Exception as e: logger.error(f"Tool '{tool_name}': Error executing command '{clean_command if 'clean_command' in locals() else command}': {e}", exc_info=True); return f"Error executing command: {type(e).__name__}"
        finally:
            if process and process.returncode is None:
                logger.warning(f"Tool '{tool_name}': Shell process '{clean_command if 'clean_command' in locals() else command}' still running, attempting termination.")
                try: process.terminate(); await process.wait()
                except ProcessLookupError: pass
                except Exception as term_e: logger.error(f"Tool '{tool_name}': Error during final termination of shell process: {term_e}")

# --- get_dynamic_tools Function ---
def get_dynamic_tools(current_task_id: Optional[str]) -> List[BaseTool]:
    dynamically_loaded_tools: List[BaseTool] = []
    try:
        dynamically_loaded_tools = load_tools_from_config()
        logger.info(f"Dynamically loaded {len(dynamically_loaded_tools)} tools from config for task '{current_task_id or 'N/A'}'.")
    except ToolLoadingError as e:
        logger.error(f"ToolLoadingError in get_dynamic_tools: {e}. Proceeding with manually defined tools only.")
    except Exception as e:
        logger.error(f"Unexpected error loading tools from config: {e}. Proceeding with manually defined tools.", exc_info=True)

    tools: List[BaseTool] = list(dynamically_loaded_tools)

    # --- REMOVED DuckDuckGoSearchRun fallback logic ---
    # Web search tools (like Tavily) are now expected to be loaded from config.
    # If no search tool is configured and enabled, the agent won't have one.
    tavily_loaded = any(tool.name == "tavily_search_api" for tool in tools)
    if not tavily_loaded and (hasattr(settings, 'tavily_api_key') and settings.tavily_api_key):
        logger.warning("Tavily API key is set in .env, but TavilyAPISearchTool was not found or not enabled in tool_config.json.")
    elif not tavily_loaded:
        logger.warning("No primary web search tool (e.g., Tavily) loaded from config. Agent may lack web search capabilities.")


    # DeepResearchTool is now expected to be loaded via tool_config.json
    # Manual addition is removed.
    deep_research_tool_loaded = any(tool.name == "deep_research_synthesizer" for tool in tools)
    if not deep_research_tool_loaded:
        # This log remains to indicate if it's missing, but we won't manually add it.
        logger.warning("DeepResearchTool not found in dynamically loaded tools. Ensure it's in tool_config.json and enabled if needed.")


    # Task-specific tools that require current_task_id for workspace path
    # These remain manually instantiated.
    if not current_task_id:
        logger.warning("No active task ID provided to get_dynamic_tools. Task-specific tools (read_file, write_file, workspace_shell) will not be added.")
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
                 if not any(t.name == ts_tool.name for t in tools):
                    tools.append(ts_tool)
                    logger.info(f"Manually added task-specific tool: {ts_tool.name}")
        except (ValueError, OSError) as e:
            logger.error(f"Failed to get or create task workspace for {current_task_id}: {e}. "
                         f"Workspace-dependent tools will not be added manually.")

    final_tool_names = [tool.name for tool in tools]
    logger.info(f"Final list of tools for task '{current_task_id or 'N/A'}': {final_tool_names}")
    return tools
