# backend/tools.py
import logging
import httpx # For async HTTP requests
from bs4 import BeautifulSoup # For HTML parsing
from langchain_core.tools import Tool # Use Tool class directly for async func
from langchain_community.tools import ShellTool, DuckDuckGoSearchRun

logger = logging.getLogger(__name__)

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

    # *** Sanitize URL input ***
    # Remove leading/trailing whitespace (like newlines from copy-paste)
    clean_url = url.strip()
    if not clean_url:
        logger.warning("Received empty URL for web reader.")
        return "Error: Received an empty URL."

    # Basic check and fix for missing http/https scheme
    if not clean_url.startswith(('http://', 'https://')):
         logger.warning(f"URL '{clean_url}' missing scheme. Prepending https://")
         clean_url = f"https://{clean_url}"

    logger.info(f"Attempting to fetch and parse URL: {clean_url}")
    try:
        # Use httpx for async requests
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, follow_redirects=True, headers=HEADERS) as client:
            # Use the cleaned URL
            response = await client.get(clean_url)
            response.raise_for_status() # Raise HTTPStatusError for bad responses (4xx or 5xx)

            # Check content type - only parse HTML
            content_type = response.headers.get("content-type", "").lower()
            if "html" not in content_type:
                logger.warning(f"Non-HTML content type '{content_type}' at URL: {clean_url}")
                return f"Error: Cannot parse content type '{content_type}'. Only HTML is supported."

            html_content = response.text
            # Use BeautifulSoup with lxml parser for speed and robustness
            soup = BeautifulSoup(html_content, 'lxml')

            # Basic text extraction: find main content area, then extract text from relevant tags
            content_tags = soup.find('article') or soup.find('main') or soup.find('body')
            if content_tags:
                 texts = content_tags.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td', 'th']) # Added table cells
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
    except httpx.RequestError as e:
        # Covers connection errors, invalid URL structures caught by httpx itself etc.
        logger.error(f"Request error fetching URL {clean_url}: {e}", exc_info=True)
        return f"Error: Could not fetch the URL. Network issue or invalid URL? Error: {e}"
    except httpx.HTTPStatusError as e:
        # Handles 4xx/5xx responses after connection
        logger.error(f"HTTP error fetching URL {clean_url}: Status {e.response.status_code}", exc_info=True)
        return f"Error: Received HTTP status {e.response.status_code} when fetching the URL."
    except ImportError:
         # Handles case where lxml is not installed
         logger.error("lxml parser not installed. Please install with 'uv pip install lxml'.")
         return "Error: HTML parser (lxml) not installed on the server."
    except Exception as e:
        # Catch other potential errors during parsing or processing
        logger.error(f"Unexpected error processing URL {clean_url}: {e}", exc_info=True)
        return f"Error: Failed to process the content of the URL. Error: {e}"


# --- Initialize Tools ---

# 1. Shell Tool
shell_tool = ShellTool()
shell_tool.description = (
    "Use this tool ONLY to execute shell commands in a Linux-like environment. "
    "Useful for file system operations (ls, pwd, cat), checking versions, or running specific command-line programs. "
    "Input MUST be a valid shell command string. Do NOT use for asking questions or searching."
)

# 2. Web Search Tool
search_tool = DuckDuckGoSearchRun()
search_tool.description = (
    "Use this tool ONLY when you need to find current information, real-time data (like weather), or answer questions about recent events or topics not covered by your training data. "
    "Input MUST be a concise search query string. Do NOT use it if you already know the answer or if the user provides a specific URL to read."
)

# 3. Web Page Reader Tool
web_reader_tool = Tool.from_function(
    func=fetch_and_parse_url, # Uses the updated function with sanitization
    name="web_page_reader",
    description=(
        "Use this tool ONLY to fetch and extract the main text content from a specific web page, given its URL. "
        "Input MUST be a single, valid URL string (whitespace will be trimmed, http/https added if missing). " # Updated description
        "Use this tool *after* a web search has provided a relevant URL, or when the user explicitly asks you to read or summarize a specific URL they provided. "
        "Do NOT use this tool for general web searching."
    ),
    coroutine=fetch_and_parse_url # Specify the coroutine for async execution
)


# --- List of Tools for the Agent ---
agent_tools = [
    shell_tool,
    search_tool,
    web_reader_tool,
]

logger.info(f"Initialized tools: {[tool.name for tool in agent_tools]}")

