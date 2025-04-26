# backend/tools.py
import logging
import httpx
from bs4 import BeautifulSoup
from pathlib import Path
import os
import re # Import regex for validation
import aiofiles
import codecs
import asyncio
import sys # Import sys to get current python executable
from typing import List, Optional, Dict, Any # Added Dict, Any

# LangChain Tool Imports
from langchain_core.tools import Tool, BaseTool
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.tools.file_management import ReadFileTool
# Import the underlying REPL utility
from langchain_experimental.utilities import PythonREPL
# Imports for PubMed Search
from Bio import Entrez
from urllib.error import HTTPError
# ------------------------------------

logger = logging.getLogger(__name__)

# --- Define Base Workspace Path ---
try:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    BASE_WORKSPACE_ROOT = PROJECT_ROOT / "workspace"
    os.makedirs(BASE_WORKSPACE_ROOT, exist_ok=True)
    logger.info(f"Base workspace directory ensured at: {BASE_WORKSPACE_ROOT}")
except OSError as e:
    logger.error(f"Could not create base workspace directory: {e}", exc_info=True)
    raise OSError(f"Required base workspace directory {BASE_WORKSPACE_ROOT} could not be created.") from e
except Exception as e:
    logger.error(f"Error resolving project/workspace path: {e}", exc_info=True)
    raise

# Define recognizable text extensions
TEXT_EXTENSIONS = {".txt", ".py", ".js", ".css", ".html", ".json", ".csv", ".md", ".log", ".yaml", ".yml"}


# --- Helper Function to get Task-Specific Workspace ---
def get_task_workspace_path(task_id: Optional[str]) -> Path:
    """
    Constructs and ensures the path for a specific task's workspace.
    Returns BASE_WORKSPACE_ROOT if task_id is None or invalid.
    """
    if not task_id or not isinstance(task_id, str):
        logger.warning(f"Invalid or missing task_id ('{task_id}') provided for workspace path. Using base workspace.")
        return BASE_WORKSPACE_ROOT
    # Sanitize task_id to prevent path traversal or invalid characters if needed
    # For now, assume task_id is reasonably safe (e.g., UUID-like)
    task_workspace = BASE_WORKSPACE_ROOT / task_id
    try:
        os.makedirs(task_workspace, exist_ok=True)
    except OSError as e:
        logger.error(f"Could not create task workspace directory at {task_workspace}: {e}", exc_info=True)
        return BASE_WORKSPACE_ROOT # Fallback
    return task_workspace


# --- Tool Implementation Functions ---

async def fetch_and_parse_url(url: str) -> str:
    """Fetches and parses URL content."""
    MAX_CONTENT_LENGTH = 4000; REQUEST_TIMEOUT = 15.0
    HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'} # Mimic browser
    if not isinstance(url, str): return "Error: Invalid URL input (must be a string)."
    clean_url = url.strip().replace('\n', '').replace('\r', '').replace('\t', '').strip('`')
    if not clean_url: return "Error: Received an empty URL."
    if not re.match(r"^[a-zA-Z]+://", clean_url): clean_url = f"https://{clean_url}"
    logger.info(f"Attempting to fetch and parse cleaned URL: {clean_url}")
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, follow_redirects=True, headers=HEADERS) as client:
            response = await client.get(clean_url); response.raise_for_status()
            content_type = response.headers.get("content-type", "").lower()
            if "html" not in content_type: return f"Error: Cannot parse content type '{content_type}'."
            html_content = response.text; soup = BeautifulSoup(html_content, 'lxml')
            content_tags = soup.find('article') or soup.find('main') or soup.find('body')
            if content_tags: texts = content_tags.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td', 'th']); extracted_text = "\n".join(t.get_text(strip=True) for t in texts if t.get_text(strip=True))
            else: extracted_text = soup.get_text(separator="\n", strip=True)
            if not extracted_text: return "Error: Could not extract meaningful text."
            truncated_text = extracted_text[:MAX_CONTENT_LENGTH]
            if len(extracted_text) > MAX_CONTENT_LENGTH: truncated_text += "..."
            logger.info(f"Successfully extracted ~{len(truncated_text)} chars from {clean_url}")
            return truncated_text
    except httpx.TimeoutException: logger.error(f"Timeout fetching {clean_url}"); return f"Error: Timeout fetching URL."
    except httpx.InvalidURL as e: logger.error(f"Invalid URL format for {clean_url}: {e}"); return f"Error: Invalid URL format: {e}"
    except httpx.RequestError as e: logger.error(f"Request error fetching {clean_url}: {e}"); return f"Error: Could not fetch URL: {e}"
    except httpx.HTTPStatusError as e: logger.error(f"HTTP error fetching {clean_url}: {e.response.status_code}"); return f"Error: HTTP {e.response.status_code} fetching URL."
    except ImportError: logger.error("lxml not installed."); return "Error: HTML parser not installed."
    except Exception as e: logger.error(f"Error parsing {clean_url}: {e}", exc_info=True); return f"Error parsing URL: {e}"


async def write_to_file_in_task_workspace(input_str: str, task_workspace: Path) -> str:
    """Writes text content to a file within the SPECIFIED task workspace."""
    logger.info(f"Write tool received input: {input_str[:100]}... for workspace {task_workspace.name}")
    relative_path_str = ""
    try:
        parts = input_str.split(':::', 1)
        if len(parts) != 2: return "Error: Invalid input format. Expected 'file_path:::text_content'."
        relative_path_str = parts[0].strip().strip('\'"`')
        raw_text_content = parts[1]
        if relative_path_str.startswith(("workspace/", "workspace\\")): relative_path_str = re.sub(r"^[\\/]?(workspace[\\/])+", "", relative_path_str); logger.info(f"Stripped 'workspace/' prefix, using: {relative_path_str}")
        if not relative_path_str: return "Error: File path cannot be empty after cleaning."
        try: text_content = codecs.decode(raw_text_content, 'unicode_escape'); logger.info("Decoded escapes.")
        except Exception as decode_err: logger.warning(f"Could not decode escapes, using raw: {decode_err}"); text_content = raw_text_content
        text_content = re.sub(r"^```[a-zA-Z]*\s*\n", "", text_content); text_content = re.sub(r"\n```$", "", text_content); text_content = text_content.strip()
        relative_path = Path(relative_path_str)
        if relative_path.is_absolute() or '..' in relative_path.parts: return f"Error: Invalid file path '{relative_path_str}'."
        full_path = task_workspace.joinpath(relative_path).resolve()
        if task_workspace not in full_path.parents and full_path != task_workspace: logger.error(f"Security Error: Write outside task workspace! Task: {task_workspace.name}, Resolved: {full_path}"); return "Error: File path resolves outside workspace."
        full_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(full_path, mode='w', encoding='utf-8') as f: await f.write(text_content)
        logger.info(f"Successfully wrote {len(text_content)} bytes to {full_path}")
        return f"Successfully wrote content to '{relative_path_str}' in the task workspace."
    except Exception as e: logger.error(f"Error writing file '{relative_path_str}': {e}", exc_info=True); return f"Error: Failed to write file '{relative_path_str}'. Reason: {type(e).__name__}"


# --- Custom Shell Tool operating in Task Workspace ---
class TaskWorkspaceShellTool(BaseTool):
    name: str = "workspace_shell"
    description: str = (f"Use this tool ONLY to execute **non-interactive** shell commands directly within the **current task's dedicated workspace**. Useful for running scripts (e.g., 'python my_script.py'), listing files (`ls -l`), checking file details (`wc`, `head`), etc. Input MUST be a valid shell command string. Do NOT include path prefixes. **DO NOT use this for 'pip install' or environment modifications.**")
    task_workspace: Path

    def _run(self, command: str) -> str:
        """Synchronous execution wrapper."""
        logger.warning("Running TaskWorkspaceShellTool synchronously using _run.")
        # *** CORRECTED SYNTAX: Indent try/except block ***
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
        """Internal async helper for running the command in the specific task workspace."""
        cwd = str(self.task_workspace); logger.info(f"TaskWorkspaceShellTool executing command: '{command}' in CWD: {cwd}")
        process = None; stdout_str = ""; stderr_str = ""
        try:
            clean_command = command.strip().strip('`');
            if not clean_command: return "Error: Received empty command."
            process = await asyncio.create_subprocess_shell(clean_command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=cwd)
            stdout, stderr = await process.communicate(); stdout_str = stdout.decode(errors='replace').strip(); stderr_str = stderr.decode(errors='replace').strip(); return_code = process.returncode
            result = "";
            if stdout_str: result += f"STDOUT:\n{stdout_str}\n"
            harmless_shell_error = "/bin/sh: 2: Syntax error: EOF in backquote substitution"; is_harmless_error_only = stderr_str == harmless_shell_error or not stderr_str; command_failed_exit_code = return_code != 0
            if command_failed_exit_code and not is_harmless_error_only:
                 if stderr_str: result += f"STDERR:\n{stderr_str}\n"; result += f"ERROR: Command failed with exit code {return_code}"; logger.warning(f"TaskWorkspaceShellTool command '{clean_command}' failed. Exit: {return_code}. Stderr: {stderr_str}")
            elif command_failed_exit_code and is_harmless_error_only and not stdout_str:
                 if stderr_str: result += f"STDERR:\n{stderr_str}\n"; result += f"ERROR: Command failed with exit code {return_code} and produced no output."; logger.warning(f"TaskWorkspaceShellTool command '{clean_command}' failed (exit {return_code}) with harmless/no stderr but no stdout.")
            elif is_harmless_error_only and stdout_str:
                 logger.warning(f"TaskWorkspaceShellTool command '{clean_command}' finished (exit {return_code}) with stdout but only harmless/no stderr. Reporting success."); result = result.replace(f"STDERR:\n{harmless_shell_error}\n", "").strip();
                 if command_failed_exit_code: result += "\n(Command executed successfully - minor shell error ignored)"
            elif stderr_str: result += f"STDERR:\n{stderr_str}\n"
            logger.info(f"TaskWorkspaceShellTool command finished. Exit code: {process.returncode}. Reporting result length: {len(result)}")
            return result[:3000] + "..." if len(result) > 3000 else result.strip()
        except FileNotFoundError: cmd_part = clean_command.split()[0] if clean_command else "Unknown"; logger.warning(f"TaskWorkspaceShellTool command not found: {cmd_part}"); return f"Error: Command not found: {cmd_part}"
        except Exception as e: logger.error(f"Error executing command '{clean_command}' in task workspace: {e}", exc_info=True); return f"Error executing command: {type(e).__name__}"
        finally:
            # Indent try/except block correctly
            if process and process.returncode is None:
                try:
                    process.terminate()
                    await process.wait()
                    logger.warning(f"Terminated task workspace shell process: {clean_command}")
                except Exception as term_e:
                     logger.error(f"Error terminating process: {term_e}")
                     pass # Ignore errors during cleanup


# --- Python Package Installer Tool Implementation ---
PACKAGE_SPEC_REGEX = re.compile(r"^[a-zA-Z0-9_.-]+(?:\[[a-zA-Z0-9_,-]+\])?(?:[=<>!~]=?\s*[a-zA-Z0-9_.*-]+)?$")
async def install_python_package(package_specifier: str) -> str:
    # ... (remains the same) ...
    package_specifier = package_specifier.strip().strip('\'"`')
    logger.info(f"Received request to install package: '{package_specifier}'")
    if not package_specifier: return "Error: No package specified."
    if not PACKAGE_SPEC_REGEX.match(package_specifier): logger.error(f"Invalid package specifier format rejected: '{package_specifier}'"); return f"Error: Invalid package specifier format: '{package_specifier}'. Only package names, extras ([...]), and version specifiers (==, >=, etc.) are allowed."
    if ';' in package_specifier or '&' in package_specifier or '|' in package_specifier: logger.error(f"Potential command injection detected in package specifier: '{package_specifier}'"); return "Error: Invalid characters detected in package specifier."
    command = [sys.executable, "-m", "pip", "install", package_specifier]
    logger.info(f"Executing installation command: {' '.join(command)}")
    process = None
    try:
        process = await asyncio.create_subprocess_exec( *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        stdout_str = stdout.decode(errors='replace').strip(); stderr_str = stderr.decode(errors='replace').strip(); return_code = process.returncode
        result = f"Installation command executed for '{package_specifier}'. Exit Code: {return_code}\n"
        if stdout_str: result += f"--- PIP STDOUT ---\n{stdout_str}\n"
        if stderr_str: result += f"--- PIP STDERR ---\n{stderr_str}\n"
        if return_code == 0: logger.info(f"Successfully installed package: {package_specifier}"); return f"Successfully installed {package_specifier}."
        else: logger.error(f"Failed to install package: {package_specifier}. Exit code: {return_code}. Stderr: {stderr_str}"); return f"Error: Failed to install {package_specifier}. Exit code: {return_code}.\nDetails:\n{stderr_str or stdout_str}"
    except FileNotFoundError: logger.error(f"Error installing package: '{sys.executable} -m pip' command not found."); return f"Error: Could not find '{sys.executable} -m pip'. Is pip installed correctly?"
    except Exception as e: logger.error(f"Error installing package '{package_specifier}': {e}", exc_info=True); return f"Error during installation: {type(e).__name__}"
    finally: pass

# --- PubMed Search Tool Implementation ---
Entrez.email = os.getenv("ENTREZ_EMAIL", "your.email@example.com")
if Entrez.email == "your.email@example.com": logger.warning("Using default placeholder email for Entrez. NCBI requires a valid email.")

async def search_pubmed(query: str, max_results: int = 5) -> str:
    # ... (remains the same) ...
    logger.info(f"Received PubMed search request: '{query}'")
    match = re.search(r"\s+max_results=(\d+)$", query)
    if match:
        try: num_res = int(match.group(1)); max_results = min(max(1, num_res), 20); query = query[:match.start()].strip(); logger.info(f"Using max_results={max_results}")
        except ValueError: logger.warning("Invalid max_results value, using default.")
    if not query: return "Error: No search query provided."
    try:
        handle = await asyncio.to_thread(Entrez.esearch, db="pubmed", term=query, retmax=str(max_results), sort="relevance")
        search_results = await asyncio.to_thread(Entrez.read, handle); await asyncio.to_thread(handle.close)
        id_list = search_results["IdList"]
        if not id_list: return f"No results found on PubMed for query: '{query}'"
        handle = await asyncio.to_thread(Entrez.efetch, db="pubmed", id=id_list, rettype="abstract", retmode="xml")
        records = await asyncio.to_thread(Entrez.read, handle); await asyncio.to_thread(handle.close)
        summaries = []; pubmed_articles = records.get('PubmedArticle', [])
        if not isinstance(pubmed_articles, list): logger.warning(f"Unexpected PubMed format: {type(pubmed_articles)}."); return str(records)
        for i, record in enumerate(pubmed_articles):
            if i >= max_results: break
            pmid = "Unknown PMID"
            try:
                article = record.get('MedlineCitation', {}).get('Article', {}); pmid = record.get('MedlineCitation', {}).get('PMID', 'Unknown PMID'); title = article.get('ArticleTitle', 'No Title')
                authors_list = article.get('AuthorList', []); authors = ", ".join([f"{a.get('LastName', '')} {a.get('Initials', '')}" for a in authors_list if isinstance(a, dict)]) or "No Authors"
                abstract_text = ""; abstract_section = article.get('Abstract', {}).get('AbstractText', [])
                if isinstance(abstract_section, list): abstract_text = " ".join([str(sec) for sec in abstract_section])
                elif isinstance(abstract_section, str): abstract_text = abstract_section
                else: abstract_text = "No Abstract Available"
                abstract_snippet = abstract_text[:250] + "..." if len(abstract_text) > 250 else abstract_text
                doi = None; article_ids = record.get('PubmedData', {}).get('ArticleIdList', [])
                if isinstance(article_ids, list):
                    for article_id in article_ids:
                        if article_id.attributes.get('IdType') == 'doi': doi = str(article_id); break
                link = f"https://doi.org/{doi}" if doi else f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"; link_text = doi if doi else pmid
                summaries.append(f"**Result {i+1}:**\n**PMID:** {pmid}\n**Title:** {title}\n**Authors:** {authors}\n**Link:** [{link_text}]({link})\n**Abstract Snippet:** {abstract_snippet}\n---")
            except Exception as parse_err: logger.error(f"Error parsing PubMed record {i+1} (PMID: {pmid}): {parse_err}", exc_info=True); summaries.append(f"**Result {i+1}:**\nError parsing record (PMID: {pmid}).\n---")
        return "\n".join(summaries) if summaries else "No valid records processed."
    except HTTPError as e: logger.error(f"HTTP Error fetching PubMed data: {e.code} {e.reason}"); return f"Error: Failed to fetch data from PubMed (HTTP {e.code})."
    except Exception as e: logger.error(f"Error searching PubMed for '{query}': {e}", exc_info=True); return f"Error: An unexpected error occurred during PubMed search: {type(e).__name__}"


# Create PythonREPL utility instance
python_repl_utility = PythonREPL()

# --- Tool Factory Function ---
def get_dynamic_tools(current_task_id: Optional[str]) -> List[BaseTool]:
    """
    Creates tool instances dynamically, configured for the current task's workspace.
    Returns only non-file tools if current_task_id is None.
    """
    # Always include stateless tools
    stateless_tools = [
        DuckDuckGoSearchRun(description=( "Use this tool for general web searches to find current information, real-time data (like weather), or answer questions about topics not covered by training data. Input MUST be a concise search query string. **DO NOT use this tool for searching specific databases like PubMed if a dedicated tool for that database exists.**")),
        Tool.from_function( func=fetch_and_parse_url, name="web_page_reader", description=( "Use this tool ONLY to fetch and extract the main text content from a specific web page, given its URL. Input MUST be a single, valid URL string (whitespace and newlines will be removed). "), coroutine=fetch_and_parse_url),
         Tool.from_function( func=install_python_package, name="python_package_installer", description=( "Use this tool ONLY to install a Python package using pip if it's missing and required for another step (like running a script). Input MUST be a valid package name or specifier (e.g., 'pandas', 'matplotlib>=3.5', 'seaborn==0.12.0', 'package-name[extra]'). **SECURITY WARNING:** This installs packages directly into the server's environment. Use with caution. Do NOT use this for general shell commands."), coroutine=install_python_package),
         Tool.from_function( func=python_repl_utility.run, name="Python_REPL", description=( "Use this tool to execute Python code snippets directly in the backend environment. Input MUST be valid, complete Python code. Handles single and multi-line inputs. Use standard Python syntax for newlines within the input string. Useful for quick calculations, data manipulation (if libraries like pandas are installed), or simple logic. Output will be the stdout or error from the execution. **Security Note:** Code execution is NOT sandboxed. Be extremely cautious. Prefer using 'write_file' and 'workspace_shell' for complex or file-interacting scripts.")),
         Tool.from_function( func=search_pubmed, name="pubmed_search", description=( "Use this tool ONLY to search for biomedical literature on PubMed. Input MUST be a search query string relevant to medicine, biology, or health. Optionally, you can specify the number of results by adding ' max_results=N' (e.g., 'crispr cas9 review max_results=10'). Default is 5, max is 20. Returns summaries of the top matching articles, including PMID, Title, Authors, Link (DOI or PubMed URL), and Abstract Snippet."), coroutine=search_pubmed)
    ]

    if not current_task_id:
        logger.warning("No active task ID, returning only stateless tools.")
        return stateless_tools

    # Get the specific workspace path for the current task
    task_workspace = get_task_workspace_path(current_task_id)
    logger.info(f"Configuring file/shell tools for workspace: {task_workspace}")

    # Create instances of tools that depend on the task workspace
    task_specific_tools = [
        TaskWorkspaceShellTool(task_workspace=task_workspace),
        ReadFileTool(root_dir=str(task_workspace), description=( f"Use this tool ONLY to read the entire contents of a file located within the current task's workspace ('{task_workspace.name}'). Input MUST be a file path relative to this workspace (e.g., 'my_data.csv').")),
        Tool.from_function( func=lambda input_str: write_to_file_in_task_workspace(input_str, task_workspace), name="write_file", description=( f"Use this tool ONLY to write or overwrite text content to a file within the current task's workspace ('{task_workspace.name}'). Input MUST be a single string formatted as 'file_path:::text_content'. 'file_path' MUST be relative to the task workspace root (e.g., 'script.py'). Subdirectories will be created. 'text_content' is the exact string content to write (newlines should be '\\n'). The separator MUST be ':::'. Example: 'output.log:::Agent execution finished.\\nStatus: OK.' WARNING: This tool OVERWRITES files."), coroutine=lambda input_str: write_to_file_in_task_workspace(input_str, task_workspace))
    ]

    all_tools = stateless_tools + task_specific_tools
    logger.info(f"Returning tools for task {current_task_id}: {[tool.name for tool in all_tools]}")
    return all_tools
