# backend/tools/web_page_reader_tool.py
import logging
import httpx
from bs4 import BeautifulSoup
import re
from typing import Optional, Type, Any 

from langchain_core.tools import BaseTool, ToolException
from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic.v1 import BaseModel, Field

from backend.config import settings

logger = logging.getLogger(__name__)

class WebPageReaderInput(BaseModel):
    url: str = Field(description="The URL of the web page to read.")

class WebPageReaderTool(BaseTool):
    name: str = "web_page_reader"
    description: str = (
        f"Use this tool ONLY to fetch and extract the main text content from a given URL. "
        f"Input MUST be a single, valid URL string (e.g., 'https://example.com/page'). "
        f"Max content length: {settings.tool_web_reader_max_length} chars. "
        f"Returns the main text content of the page or an error message."
    )
    args_schema: Type[BaseModel] = WebPageReaderInput

    async def _arun(
        self,
        url: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any # <<< Any is now defined
    ) -> str:
        logger.info(f"Tool '{self.name}' received URL: '{url}'")
        if not isinstance(url, str) or not url.strip():
            logger.error(f"Tool '{self.name}' received invalid input: Must be a non-empty string.")
            raise ToolException("Invalid input. Expected a non-empty URL string.")

        max_length = settings.tool_web_reader_max_length
        timeout = settings.tool_web_reader_timeout
        HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

        clean_url = url.strip().replace('\n', '').replace('\r', '').replace('\t', '').strip('`')
        if not clean_url:
            logger.error(f"Tool '{self.name}' input resulted in empty URL after cleaning.")
            raise ToolException("Received an empty URL after cleaning.")

        if not re.match(r"^[a-zA-Z]+://", clean_url):
            logger.info(f"Tool '{self.name}': No scheme found, prepending https:// to '{clean_url}'")
            clean_url = f"https://{clean_url}"

        logger.info(f"Tool '{self.name}' attempting to fetch and parse cleaned URL: {clean_url} (Timeout: {timeout}s)")
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=HEADERS) as client:
                response = await client.get(clean_url)
                response.raise_for_status()

                content_type = response.headers.get("content-type", "").lower()
                if "html" not in content_type:
                    logger.warning(f"Tool '{self.name}': Cannot parse content type '{content_type}' for URL {clean_url}")
                    raise ToolException(f"Cannot parse content type '{content_type}'. Only HTML is supported.")

                html_content = response.text
                soup = BeautifulSoup(html_content, 'lxml')

                content_tags = soup.find('article') or soup.find('main') or soup.find('body')
                if content_tags:
                    texts = content_tags.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td', 'th'])
                    extracted_text = "\n".join(t.get_text(strip=True) for t in texts if t.get_text(strip=True))
                else:
                    extracted_text = soup.get_text(separator="\n", strip=True)

                if not extracted_text:
                    logger.warning(f"Tool '{self.name}': Could not extract meaningful text from {clean_url}")
                    return "Error: Could not extract meaningful text from the page."

                truncated_text = extracted_text[:max_length]
                if len(extracted_text) > max_length:
                    truncated_text += "..."
                logger.info(f"Tool '{self.name}': Successfully extracted ~{len(truncated_text)} chars from {clean_url}")
                return truncated_text
        except httpx.TimeoutException:
            logger.error(f"Tool '{self.name}': Timeout fetching {clean_url}")
            raise ToolException("Error: Timeout fetching URL.")
        except httpx.InvalidURL as e:
            logger.error(f"Tool '{self.name}': Invalid URL format for {clean_url}: {e}")
            raise ToolException(f"Error: Invalid URL format: {e}")
        except httpx.RequestError as e:
            logger.error(f"Tool '{self.name}': Request error fetching {clean_url}: {e}")
            raise ToolException(f"Error: Could not fetch URL: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Tool '{self.name}': HTTP error fetching {clean_url}: {e.response.status_code}")
            raise ToolException(f"Error: HTTP {e.response.status_code} fetching URL.")
        except ImportError:
            logger.error(f"Tool '{self.name}': lxml not installed.")
            raise ToolException("Error: HTML parser (lxml) not installed.")
        except Exception as e:
            logger.error(f"Tool '{self.name}': Error parsing {clean_url}: {e}", exc_info=True)
            raise ToolException(f"Error parsing URL: {e}")

    def _run(self, url: str, run_manager: Optional[CallbackManagerForToolRun] = None, **kwargs: Any) -> str:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                future = asyncio.run_coroutine_threadsafe(self._arun(url=url, run_manager=run_manager, **kwargs), loop)
                return future.result(timeout=settings.tool_web_reader_timeout + 5)
            else:
                return asyncio.run(self._arun(url=url, run_manager=run_manager, **kwargs))
        except Exception as e:
            logger.error(f"Error running WebPageReaderTool synchronously for {url}: {e}", exc_info=True)
            return f"Error: {e}"
