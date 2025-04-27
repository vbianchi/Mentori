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
        # Fallback to base workspace might be problematic if tools expect a task-specific one.
        # Consider raising an error or having a dedicated "no-task" workspace if needed.
        # For now, returning base, assuming tools handle this gracefully or context is always set.
        return BASE_WORKSPACE_ROOT
    # Sanitize task_id to prevent path traversal or invalid characters if needed
    # Basic check: Ensure it doesn't contain '..' or slashes. UUIDs are generally safe.
    if ".." in task_id or "/" in task_id or "\\" in task_id:
         logger.error(f"Invalid characters detected in task_id: {task_id}. Denying workspace path creation.")
         raise ValueError(f"Invalid task_id format: {task_id}")

    task_workspace = BASE_WORKSPACE_ROOT / task_id
    try:
        os.makedirs(task_workspace, exist_ok=True)
    except OSError as e:
        logger.error(f"Could not create task workspace directory at {task_workspace}: {e}", exc_info=True)
        # Fallback might hide errors. Raising might be better.
        raise OSError(f"Could not create task workspace {task_workspace}: {e}") from e
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
        # Remove potential workspace prefixes inserted by the LLM
        if relative_path_str.startswith((f"workspace/{task_workspace.name}/", f"workspace\\{task_workspace.name}\\" ,f"{task_workspace.name}/", f"{task_workspace.name}\\")):
             relative_path_str = re.sub(r"^[\\/]?(workspace[\\/])?%s[\\/]" % task_workspace.name, "", relative_path_str)
             logger.info(f"Stripped workspace/task prefix, using relative path: {relative_path_str}")
        elif relative_path_str.startswith(("workspace/", "workspace\\")):
             relative_path_str = re.sub(r"^[\\/]?(workspace[\\/])+", "", relative_path_str)
             logger.info(f"Stripped generic 'workspace/' prefix, using: {relative_path_str}")

        if not relative_path_str: return "Error: File path cannot be empty after cleaning."
        # Decode unicode escapes (e.g., \n -> newline) common in LLM outputs
        try: text_content = codecs.decode(raw_text_content, 'unicode_escape'); logger.info("Decoded unicode escapes.")
        except Exception as decode_err: logger.warning(f"Could not decode unicode escapes, using raw content: {decode_err}"); text_content = raw_text_content
        # Remove markdown code fences if present
        text_content = re.sub(r"^```[a-zA-Z]*\s*\n", "", text_content)
        text_content = re.sub(r"\n```$", "", text_content)
        text_content = text_content.strip()

        # Security Check: Ensure relative path does not try to escape the workspace
        relative_path = Path(relative_path_str)
        if relative_path.is_absolute() or '..' in relative_path.parts:
            logger.error(f"Security Error: Invalid file path '{relative_path_str}' attempts traversal.")
            return f"Error: Invalid file path '{relative_path_str}'. Path must be relative and within the workspace."

        full_path = task_workspace.joinpath(relative_path).resolve()

        # Security Check: Ensure the resolved path is truly within the intended workspace
        if not full_path.is_relative_to(task_workspace.resolve()):
             logger.error(f"Security Error: Write path resolves outside task workspace! Task: {task_workspace.name}, Resolved: {full_path}")
             return "Error: File path resolves outside the designated task workspace."

        # Create parent directories if they don't exist
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the file asynchronously
        async with aiofiles.open(full_path, mode='w', encoding='utf-8') as f:
            await f.write(text_content)

        logger.info(f"Successfully wrote {len(text_content)} bytes to {full_path}")
        # Return confirmation relative to the workspace for clarity
        return f"Successfully wrote content to '{relative_path_str}' in the task workspace."
    except Exception as e:
        logger.error(f"Error writing file '{relative_path_str}' to workspace {task_workspace.name}: {e}", exc_info=True)
        return f"Error: Failed to write file '{relative_path_str}'. Reason: {type(e).__name__}"


# --- Custom Shell Tool operating in Task Workspace ---
class TaskWorkspaceShellTool(BaseTool):
    name: str = "workspace_shell"
    description: str = (
        f"Use this tool ONLY to execute **non-interactive** shell commands directly within the **current task's dedicated workspace**. "
        f"Useful for running scripts (e.g., 'python my_script.py', 'Rscript analysis.R'), listing files (`ls -l`), checking file details (`wc`, `head`), etc. "
        f"Input MUST be a valid shell command string. Do NOT include path prefixes like 'workspace/task_id/'. "
        f"**DO NOT use this for 'pip install' or 'uv venv' or environment modifications.** Use the dedicated 'python_package_installer' tool for installations."
    )
    task_workspace: Path
    # FUTURE: task_venv_path: Optional[Path] = None # If implementing per-task venvs

    def _run(self, command: str) -> str:
        """Synchronous execution wrapper (avoid if possible)."""
        logger.warning("Running TaskWorkspaceShellTool synchronously using _run.")
        # This is generally discouraged in an async application but provides compatibility.
        try:
            loop = asyncio.get_running_loop()
            result = loop.run_until_complete(self._arun_internal(command))
        except RuntimeError: # No running event loop
            logger.warning("No running event loop, creating new one for TaskWorkspaceShellTool._run")
            # Note: asyncio.run() creates a new event loop, runs the coroutine, and closes the loop.
            # This might have implications if used heavily within an existing async context.
            result = asyncio.run(self._arun_internal(command))
        return result

    async def _arun(self, command: str) -> str:
         """Asynchronous execution entry point."""
         return await self._arun_internal(command)

    async def _arun_internal(self, command: str) -> str:
        """Internal async helper for running the command in the specific task workspace."""
        # Ensure task workspace path is absolute for cwd safety
        cwd = str(self.task_workspace.resolve())
        logger.info(f"TaskWorkspaceShellTool executing command: '{command}' in CWD: {cwd}")
        process = None
        stdout_str = ""
        stderr_str = ""

        # *** FUTURE: Per-Task Venv Activation ***
        # if self.task_venv_path and self.task_venv_path.exists():
        #     # Example: Modify command to run within the venv
        #     # This could involve sourcing activate or directly calling the venv's python
        #     venv_python = self.task_venv_path / "bin" / "python" # Adjust path for Windows
        #     if venv_python.exists() and command.startswith("python "):
        #          command_parts = command.split(" ", 1)
        #          command = f"{str(venv_python)} {command_parts[1]}"
        #          logger.info(f"Modified command to use task venv python: {command}")
        #     # else: Handle activation for general shell commands if needed (more complex)
        # else:
        #     logger.info("No task venv specified or found, using default environment.")
        # ****************************************

        try:
            clean_command = command.strip().strip('`');
            if not clean_command:
                return "Error: Received empty command."

            # Security: Basic check for potentially harmful patterns - not foolproof!
            # Avoid common ways to break out or modify environment outside workspace focus.
            # This is a weak defense; containerization is the primary security layer.
            if '&&' in clean_command or '||' in clean_command or ';' in clean_command or '`' in clean_command or '$(' in clean_command:
                 # Allow simple pipelining
                 if '|' not in clean_command: # Allow single pipes for common workflows like grep
                    logger.warning(f"Potentially unsafe shell characters detected in command: {clean_command}")
                    # Decide whether to block or allow with warning. Blocking is safer.
                    # return "Error: Command contains potentially unsafe shell characters (&&, ||, ;, `, $())."

            process = await asyncio.create_subprocess_shell(
                clean_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )

            # Set a timeout for the command execution (e.g., 60 seconds)
            TIMEOUT_SECONDS = 60
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=TIMEOUT_SECONDS)
            except asyncio.TimeoutError:
                 logger.error(f"Timeout executing command: {clean_command}")
                 if process and process.returncode is None:
                     try: process.terminate()
                     except ProcessLookupError: pass # Process might have ended already
                     await process.wait() # Wait for termination
                 return f"Error: Command timed out after {TIMEOUT_SECONDS} seconds."

            stdout_str = stdout.decode(errors='replace').strip()
            stderr_str = stderr.decode(errors='replace').strip()
            return_code = process.returncode

            result = ""
            if stdout_str:
                result += f"STDOUT:\n{stdout_str}\n"

            if return_code != 0:
                # Command failed
                logger.warning(f"TaskWorkspaceShellTool command '{clean_command}' failed. Exit: {return_code}. Stderr: {stderr_str}")
                result += f"STDERR:\n{stderr_str}\n" if stderr_str else ""
                result += f"ERROR: Command failed with exit code {return_code}"
            elif stderr_str:
                # Command succeeded but produced stderr output (often warnings)
                 logger.info(f"TaskWorkspaceShellTool command '{clean_command}' succeeded (Exit: {return_code}) but produced STDERR:\n{stderr_str}")
                 result += f"STDERR (Warnings/Info):\n{stderr_str}\n"


            logger.info(f"TaskWorkspaceShellTool command finished. Exit code: {return_code}. Reporting result length: {len(result)}")
            # Limit output size to prevent overwhelming the UI/LLM
            MAX_OUTPUT_LENGTH = 3000
            if len(result) > MAX_OUTPUT_LENGTH:
                result = result[:MAX_OUTPUT_LENGTH] + f"\n... (output truncated after {MAX_OUTPUT_LENGTH} characters)"

            return result.strip()

        except FileNotFoundError:
            cmd_part = clean_command.split()[0] if clean_command else "Unknown"
            logger.warning(f"TaskWorkspaceShellTool command not found: {cmd_part}")
            return f"Error: Command not found: {cmd_part}"
        except Exception as e:
            logger.error(f"Error executing command '{clean_command}' in task workspace: {e}", exc_info=True)
            return f"Error executing command: {type(e).__name__}"
        finally:
            # Ensure process is cleaned up if it was started but something went wrong
            if process and process.returncode is None:
                logger.warning(f"Process '{clean_command}' still running in finally block, attempting termination.")
                try:
                    process.terminate()
                    await process.wait() # Give it a moment to terminate
                except ProcessLookupError:
                    pass # Process already finished
                except Exception as term_e:
                    logger.error(f"Error during final termination attempt: {term_e}")



# --- Python Package Installer Tool Implementation ---
PACKAGE_SPEC_REGEX = re.compile(r"^[a-zA-Z0-9_.-]+(?:\[[a-zA-Z0-9_,-]+\])?(?:[=<>!~]=?\s*[a-zA-Z0-9_.*-]+)?$")

async def install_python_package(package_specifier: str) -> str:
    """
    Installs a Python package using the system's Python environment (or a task-specific one in future).
    SECURITY WARNING: Modifies the Python environment where the backend runs. Use with extreme caution.
    """
    package_specifier = package_specifier.strip().strip('\'"`')
    logger.info(f"Received request to install package: '{package_specifier}'")

    if not package_specifier:
        return "Error: No package specified."

    # Validate package specifier format
    if not PACKAGE_SPEC_REGEX.match(package_specifier):
        logger.error(f"Invalid package specifier format rejected: '{package_specifier}'")
        return f"Error: Invalid package specifier format: '{package_specifier}'. Only package names, extras ([...]), and version specifiers (==, >=, etc.) are allowed."

    # Basic check against command injection characters (though regex helps)
    if ';' in package_specifier or '&' in package_specifier or '|' in package_specifier or '`' in package_specifier or '$(' in package_specifier:
        logger.error(f"Potential command injection detected in package specifier: '{package_specifier}'")
        return "Error: Invalid characters detected in package specifier."

    # Determine the python executable and pip command
    # *** FUTURE: Per-Task Venv Activation ***
    # task_venv_path = get_current_task_venv_path() # Need a way to get this context
    # if task_venv_path and task_venv_path.exists():
    #     python_executable = str(task_venv_path / "bin" / "python") # Adjust for Windows
    #     pip_command = [python_executable, "-m", "pip"]
    #     logger.info(f"Using task venv pip for installation: {python_executable}")
    # else:
    #     # Default to the system python (or the one running the backend)
    #     python_executable = sys.executable
    #     pip_command = [python_executable, "-m", "pip"]
    #     logger.info(f"Using system pip for installation: {python_executable}")
    # ****************************************
    # For now, always use the backend's environment python
    python_executable = sys.executable
    # Use uv if available and preferred, otherwise fallback to pip
    # This check assumes 'uv' is installed in the environment (as per Dockerfile)
    # We could make this configurable. For now, let's prefer uv if detected.
    installer_command_base = [python_executable, "-m", "uv", "pip"] # Prefer uv
    try:
        # Quick check if uv is importable/runnable - might need refinement
        test_process = await asyncio.create_subprocess_exec(
            python_executable, "-m", "uv", "--version",
            stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
        await test_process.wait()
        if test_process.returncode == 0:
            logger.info("Detected uv, using 'uv pip install'.")
        else:
            logger.info("uv check failed or not found, falling back to 'pip install'.")
            installer_command_base = [python_executable, "-m", "pip"]
    except FileNotFoundError:
         logger.info(f"Could not execute '{python_executable} -m uv', falling back to 'pip install'.")
         installer_command_base = [python_executable, "-m", "pip"]
    except Exception as e:
         logger.warning(f"Error checking for uv, falling back to pip: {e}")
         installer_command_base = [python_executable, "-m", "pip"]


    command = installer_command_base + ["install", package_specifier]

    logger.info(f"Executing installation command: {' '.join(command)}")
    process = None
    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Set a timeout for installation (can take time)
        TIMEOUT_SECONDS = 300 # 5 minutes
        try:
             stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=TIMEOUT_SECONDS)
        except asyncio.TimeoutError:
            logger.error(f"Timeout installing package: {package_specifier}")
            if process and process.returncode is None:
                 try: process.terminate()
                 except ProcessLookupError: pass
                 await process.wait()
            return f"Error: Package installation timed out after {TIMEOUT_SECONDS} seconds."


        stdout_str = stdout.decode(errors='replace').strip()
        stderr_str = stderr.decode(errors='replace').strip()
        return_code = process.returncode

        result = f"Installation command executed for '{package_specifier}'. Exit Code: {return_code}\n"
        if stdout_str:
            result += f"--- Installer STDOUT ---\n{stdout_str}\n"
        if stderr_str:
            result += f"--- Installer STDERR ---\n{stderr_str}\n" # Pip often uses stderr for info too

        if return_code == 0:
            logger.info(f"Successfully installed package: {package_specifier}")
            # Return concise success message, full log might be too verbose
            success_msg = f"Successfully installed {package_specifier}."
            # Append stderr if it exists, as it might contain warnings even on success
            if stderr_str:
                success_msg += f"\nNotes/Warnings:\n{stderr_str[:500]}{'...' if len(stderr_str)>500 else ''}"
            return success_msg
        else:
            logger.error(f"Failed to install package: {package_specifier}. Exit code: {return_code}. Stderr: {stderr_str}")
            # Return error details
            error_details = stderr_str or stdout_str # Provide whichever stream has content
            return f"Error: Failed to install {package_specifier}. Exit code: {return_code}.\nDetails:\n{error_details[:1000]}{'...' if len(error_details)>1000 else ''}"

    except FileNotFoundError:
        logger.error(f"Error installing package: '{installer_command_base[0]}' command not found.")
        return f"Error: Could not find Python executable '{installer_command_base[0]}'."
    except Exception as e:
        logger.error(f"Error installing package '{package_specifier}': {e}", exc_info=True)
        return f"Error during installation: {type(e).__name__}"
    finally:
         if process and process.returncode is None:
             logger.warning(f"Installer process '{' '.join(command)}' still running in finally block, attempting termination.")
             try:
                 process.terminate()
                 await process.wait()
             except ProcessLookupError: pass
             except Exception as term_e: logger.error(f"Error during final termination attempt of installer: {term_e}")


# --- PubMed Search Tool Implementation ---
# Ensure ENTREZ_EMAIL is set in .env
Entrez.email = os.getenv("ENTREZ_EMAIL", None)
if not Entrez.email:
    logger.critical("ENTREZ_EMAIL not set in environment or .env file. PubMed search tool will likely fail or be blocked by NCBI.")
    # raise ValueError("ENTREZ_EMAIL is required for PubMed Tool.") # Or allow to fail at runtime

async def search_pubmed(query: str, max_results: int = 5) -> str:
    """Searches PubMed for biomedical literature."""
    if not Entrez.email:
         return "Error: PubMed Search tool is not configured. Missing NCBI Entrez email address."

    logger.info(f"Received PubMed search request: '{query}'")
    # Extract max_results parameter if present
    match = re.search(r"\s+max_results=(\d+)$", query)
    if match:
        try:
            num_res = int(match.group(1))
            # Limit max_results to a reasonable number (e.g., 1-20)
            max_results = min(max(1, num_res), 20)
            query = query[:match.start()].strip() # Remove max_results part from query
            logger.info(f"Using max_results={max_results}")
        except ValueError:
            logger.warning(f"Invalid max_results value in query '{query}', using default {max_results}.")

    if not query:
        return "Error: No search query provided for PubMed."

    try:
        # Perform the search asynchronously using asyncio.to_thread
        handle = await asyncio.to_thread(
            Entrez.esearch,
            db="pubmed",
            term=query,
            retmax=str(max_results),
            sort="relevance" # or 'pub date'
        )
        search_results = await asyncio.to_thread(Entrez.read, handle)
        await asyncio.to_thread(handle.close)

        id_list = search_results["IdList"]
        if not id_list:
            return f"No results found on PubMed for query: '{query}'"

        # Fetch the details for the found IDs
        handle = await asyncio.to_thread(
            Entrez.efetch,
            db="pubmed",
            id=id_list,
            rettype="abstract",
            retmode="xml"
        )
        records = await asyncio.to_thread(Entrez.read, handle)
        await asyncio.to_thread(handle.close)

        summaries = []
        # Ensure records['PubmedArticle'] is iterable, default to empty list if not found
        pubmed_articles = records.get('PubmedArticle', [])
        if not isinstance(pubmed_articles, list):
            logger.warning(f"Unexpected PubMed fetch format for query '{query}': Expected list for PubmedArticle, got {type(pubmed_articles)}. Records: {records}")
            # Attempt to handle single article case if dict
            if isinstance(pubmed_articles, dict):
                 pubmed_articles = [pubmed_articles]
            else:
                 return "Error: Could not parse PubMed results (unexpected format)."


        for i, record in enumerate(pubmed_articles):
            # Sometimes efetch returns fewer records than requested
            if i >= max_results: break
            pmid = "Unknown PMID" # Default
            try:
                # Safely access nested dictionary keys
                medline_citation = record.get('MedlineCitation', {})
                article = medline_citation.get('Article', {})
                pmid = str(medline_citation.get('PMID', 'Unknown PMID')) # Ensure PMID is string
                title = article.get('ArticleTitle', 'No Title')
                # Handle potential variations in title structure (e.g., XML object)
                if not isinstance(title, str): title = str(title)


                # Extract Authors
                authors_list = article.get('AuthorList', [])
                author_names = []
                if isinstance(authors_list, list):
                    for author in authors_list:
                         if isinstance(author, dict):
                             last_name = author.get('LastName', '')
                             initials = author.get('Initials', '')
                             if last_name: # Only include authors with at least a last name
                                 author_names.append(f"{last_name} {initials}".strip())
                authors = ", ".join(author_names) or "No Authors Listed"


                # Extract Abstract Snippet
                abstract_text = ""
                abstract_section = article.get('Abstract', {}).get('AbstractText', [])
                if isinstance(abstract_section, list):
                     # Handle abstract sections which might be dicts with attributes or just strings
                     section_texts = []
                     for sec in abstract_section:
                         if isinstance(sec, str): section_texts.append(sec)
                         elif isinstance(sec, dict): section_texts.append(sec.get('#text', '')) # Common structure
                         elif hasattr(sec, 'attributes') and 'Label' in sec.attributes: # Handle sections like OBJECTIVE: ...
                             section_texts.append(f"{sec.attributes['Label']}: {str(sec)}")
                         else: section_texts.append(str(sec)) # Fallback
                     abstract_text = " ".join(filter(None, section_texts)) # Join non-empty sections
                elif isinstance(abstract_section, str):
                    abstract_text = abstract_section
                else: # Handle cases where abstract is not a list or string
                    abstract_text = str(abstract_section) if abstract_section else "No Abstract Available"

                # Limit abstract length
                MAX_ABSTRACT_SNIPPET = 250
                abstract_snippet = abstract_text[:MAX_ABSTRACT_SNIPPET].strip()
                if len(abstract_text) > MAX_ABSTRACT_SNIPPET:
                    abstract_snippet += "..."
                if not abstract_snippet: abstract_snippet = "No Abstract Available"


                # Extract DOI and construct link
                doi = None
                article_ids = record.get('PubmedData', {}).get('ArticleIdList', [])
                if isinstance(article_ids, list):
                    for article_id in article_ids:
                         # ArticleId objects might have attributes property
                         if hasattr(article_id, 'attributes') and article_id.attributes.get('IdType') == 'doi':
                             doi = str(article_id) # Convert ID object to string
                             break
                         # Handle simpler list of dicts format if encountered
                         elif isinstance(article_id, dict) and article_id.get('IdType') == 'doi':
                              doi = article_id.get('#text')
                              break

                link = f"https://doi.org/{doi}" if doi else f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                link_text = f"DOI:{doi}" if doi else f"PMID:{pmid}"

                summaries.append(f"**Result {i+1}:**\n"
                                 f"**Title:** {title}\n"
                                 f"**Authors:** {authors}\n"
                                 f"**Link:** [{link_text}]({link})\n"
                                 f"**Abstract Snippet:** {abstract_snippet}\n"
                                 f"---")
            except Exception as parse_err:
                logger.error(f"Error parsing PubMed record {i+1} (PMID: {pmid}) for query '{query}': {parse_err}", exc_info=True)
                summaries.append(f"**Result {i+1}:**\nError parsing record (PMID: {pmid}).\n---")

        return "\n".join(summaries) if summaries else "No valid PubMed records processed."

    except HTTPError as e:
        logger.error(f"HTTP Error fetching PubMed data for query '{query}': {e.code} {e.reason}")
        return f"Error: Failed to fetch data from PubMed (HTTP Error {e.code}). Check network or NCBI status."
    except Exception as e:
        logger.error(f"Error searching PubMed for '{query}': {e}", exc_info=True)
        return f"Error: An unexpected error occurred during PubMed search: {type(e).__name__}"


# Create PythonREPL utility instance
# This utility itself doesn't have inherent async methods for _arun
# Langchain's Tool.from_function handles wrapping sync functions for _arun if needed.
try:
    python_repl_utility = PythonREPL()
except ImportError:
    logger.warning("Could not import PythonREPL. The Python_REPL tool will not be available.")
    python_repl_utility = None

# --- Tool Factory Function ---
def get_dynamic_tools(current_task_id: Optional[str]) -> List[BaseTool]:
    """
    Creates tool instances dynamically, configured for the current task's workspace.
    Returns only non-file tools if current_task_id is None.
    """
    # Always include stateless tools (or tools configured globally)
    stateless_tools = [
        DuckDuckGoSearchRun(description=(
            "Use this tool for general web searches to find current information, real-time data (like weather), "
            "or answer questions about topics not covered by training data. Input MUST be a concise search query string. "
            "**DO NOT use this tool for searching specific databases like PubMed if a dedicated tool for that database exists.**"
        )),
        Tool.from_function(
            func=fetch_and_parse_url,
            name="web_page_reader",
            description=(
                "Use this tool ONLY to fetch and extract the main text content from a specific web page, given its URL. "
                "Input MUST be a single, valid URL string (whitespace and newlines will be removed). "
                "It's best for reading articles or documentation pages. It might struggle with highly dynamic web apps."
            ),
            coroutine=fetch_and_parse_url # Provide the async function directly
        ),
        Tool.from_function(
            func=install_python_package,
            name="python_package_installer",
            description=(
                "Use this tool ONLY to install a Python package using pip/uv if it's missing and required for another step "
                "(like running a script with the 'workspace_shell' tool). Input MUST be a valid package name or specifier "
                "(e.g., 'pandas', 'matplotlib>=3.5', 'seaborn==0.12.0', 'package-name[extra]'). "
                "**SECURITY WARNING:** This installs packages directly into the backend server's environment (or task venv in future). Use with extreme caution. "
                "Do NOT use this for general shell commands or updating existing packages unless necessary."
            ),
            coroutine=install_python_package # Provide the async function
        ),
         Tool.from_function(
             func=search_pubmed,
             name="pubmed_search",
             description=(
                 "Use this tool ONLY to search for biomedical literature on PubMed. Input MUST be a search query string relevant to medicine, biology, or health. "
                 "Optionally, you can specify the number of results by adding ' max_results=N' at the end (e.g., 'crispr cas9 review max_results=10'). Default is 5, max is 20. "
                 "Returns summaries of the top matching articles, including Title, Authors, Link (DOI or PubMed URL), and Abstract Snippet."
             ),
             coroutine=search_pubmed # Provide the async function
        )
    ]

    # Add Python REPL tool conditionally if the utility was loaded
    if python_repl_utility:
        stateless_tools.append(
            Tool.from_function(
                func=python_repl_utility.run, # python_repl_utility.run is synchronous
                name="Python_REPL",
                description=(
                    "Use this tool to execute Python code snippets directly in the backend environment. "
                    "Input MUST be valid, complete Python code. Handles single and multi-line inputs. Use standard Python syntax for newlines within the input string. "
                    "Useful for quick calculations, data manipulation (if libraries like pandas are installed), or simple logic. Output will be the stdout or error from the execution. "
                    "**Security Note:** Code execution is NOT sandboxed from the backend process. Be extremely cautious. Prefer using 'write_file' and 'workspace_shell' for complex or file-interacting scripts."
                    # No coroutine specified as python_repl_utility.run is sync
                 )
            )
        )
    else:
         logger.warning("Python REPL tool not available because PythonREPL utility failed to load.")


    if not current_task_id:
        logger.warning("No active task ID, returning only stateless tools.")
        return stateless_tools

    # Get the specific workspace path for the current task
    try:
        task_workspace = get_task_workspace_path(current_task_id)
        logger.info(f"Configuring file/shell tools for workspace: {task_workspace}")
    except (ValueError, OSError) as e:
         logger.error(f"Failed to get or create task workspace for {current_task_id}: {e}. Returning only stateless tools.")
         return stateless_tools


    # *** FUTURE: Per-Task Venv Path ***
    # task_venv_path = task_workspace / ".venv" # Example path
    # if not task_venv_path.exists():
    #     # Logic to potentially create the venv here or ensure it's created elsewhere
    #     logger.info(f"Task venv path configured (but might not exist yet): {task_venv_path}")
    #     task_venv_path = None # Or handle creation
    # else:
    #     logger.info(f"Task venv path found: {task_venv_path}")
    # ***********************************
    task_venv_path = None # Placeholder for now


    # Create instances of tools that depend on the task workspace
    task_specific_tools = [
        TaskWorkspaceShellTool(
            task_workspace=task_workspace,
            # FUTURE: task_venv_path=task_venv_path
        ),
        ReadFileTool(
             # Langchain's ReadFileTool expects root_dir to be string
            root_dir=str(task_workspace.resolve()),
            description=(
                f"Use this tool ONLY to read the entire contents of a file located within the current task's workspace ('{task_workspace.name}'). "
                f"Input MUST be a file path relative to this workspace (e.g., 'my_data.csv', 'subdir/results.txt'). "
                f"Do NOT use absolute paths or '..' ."
            )
        ),
        Tool.from_function(
            # Use lambda to pass the dynamically determined task_workspace
            func=lambda input_str: write_to_file_in_task_workspace(input_str, task_workspace),
            name="write_file",
            description=(
                f"Use this tool ONLY to write or overwrite text content to a file within the current task's workspace ('{task_workspace.name}'). "
                f"Input MUST be a single string formatted as 'relative_file_path:::text_content'. "
                f"'relative_file_path' MUST be relative to the task workspace root (e.g., 'script.py', 'output/data.json'). Subdirectories will be created if they don't exist. "
                f"'text_content' is the exact string content to write (standard Python escape sequences like '\\n' for newline should be used if needed). "
                f"The separator MUST be ':::'. Example: 'output.log:::Agent execution finished.\\nStatus: OK.' "
                f"WARNING: This tool OVERWRITES files if they already exist."
            ),
            # Define the coroutine similarly using lambda
            coroutine=lambda input_str: write_to_file_in_task_workspace(input_str, task_workspace)
        )
    ]

    all_tools = stateless_tools + task_specific_tools
    logger.info(f"Returning tools for task {current_task_id}: {[tool.name for tool in all_tools]}")
    return all_tools