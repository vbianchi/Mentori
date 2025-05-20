import asyncio
import logging
from typing import Optional, List, Type, Any
from pathlib import Path
import urllib.parse # Added for URL decoding

from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic.v1 import BaseModel, Field # Using pydantic.v1 for Langchain compatibility

from playwright.async_api import async_playwright, Page, Browser, BrowserContext, Error as PlaywrightException

logger = logging.getLogger(__name__)

# --- Input Schema for the Tool ---
class PlaywrightSearchInput(BaseModel):
    query: str = Field(description="The search query string.")
    # num_results: int = Field(default=3, description="Number of search results to return.")

class PlaywrightSearchTool(BaseTool):
    """
    A tool that uses Playwright to perform a web search on a search engine
    (currently defaults to Google) and returns a list of search results
    including titles, URLs, and snippets.
    """
    name: str = "playwright_web_search"
    description: str = (
        "Performs a web search using a headless browser (Playwright) and returns search results. "
        "Input should be a search query string. "
        "Useful for finding up-to-date information or discovering web pages related to a topic."
    )
    args_schema: Type[BaseModel] = PlaywrightSearchInput

    search_engine_url: str = "https://www.google.com/search"
    num_results_to_fetch: int = 3
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36" # Updated Chrome version
    )
    headless_mode: bool = True

    async def _arun(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any
    ) -> str:
        logger.info(f"PlaywrightSearchTool: Starting search for query: '{query}'")
        results_output: List[str] = []
        browser: Optional[Browser] = None
        context: Optional[BrowserContext] = None
        page: Optional[Page] = None
        
        screenshots_dir = Path("workspace/screenshots")
        try:
            screenshots_dir.mkdir(parents=True, exist_ok=True)
        except Exception as dir_e:
            logger.error(f"PlaywrightSearchTool: Could not create screenshots directory at {screenshots_dir}: {dir_e}")

        try:
            async with async_playwright() as p:
                try:
                    browser = await p.chromium.launch(headless=self.headless_mode)
                    logger.info(f"PlaywrightSearchTool: Chromium browser launched (headless: {self.headless_mode}).")
                except PlaywrightException as e:
                    logger.error(f"PlaywrightSearchTool: Failed to launch browser: {e}")
                    return f"Error: Failed to launch browser. {str(e)}"

                context = await browser.new_context(user_agent=self.user_agent)
                page = await context.new_page()
                
                encoded_query = urllib.parse.quote_plus(query) # More robust URL encoding
                full_search_url = f"{self.search_engine_url}?q={encoded_query}&hl=en"
                
                logger.info(f"PlaywrightSearchTool: Navigating to search engine: {full_search_url}")

                try:
                    await page.goto(full_search_url, timeout=30000, wait_until="domcontentloaded")
                    logger.info(f"PlaywrightSearchTool: Page loaded for query '{query}'")

                    if not self.headless_mode:
                        logger.info("PlaywrightSearchTool: Running in non-headless mode. Pausing for 15 seconds for inspection. Check browser window.")
                        await asyncio.sleep(15) 
                        logger.info("Continuing after pause/sleep.")

                except PlaywrightException as e:
                    logger.error(f"PlaywrightSearchTool: Error navigating or loading page for query '{query}': {e}")
                    screenshot_path_nav_error = screenshots_dir / f"debug_playwright_nav_error_{query[:20].replace(' ','_').replace('/','')}.png"
                    try:
                        await page.screenshot(path=screenshot_path_nav_error)
                        logger.info(f"PlaywrightSearchTool: Saved screenshot on navigation error to {screenshot_path_nav_error}")
                    except Exception as ss_e:
                        logger.error(f"PlaywrightSearchTool: Failed to take screenshot on navigation error: {ss_e}")
                    return f"Error: Could not navigate to search results page. {str(e)}"
                
                result_item_selectors = [
                    "div.g",                    
                    "div.Gx5Zad",               
                    "div.kvH3mc",               
                    "div.MjjYud",               
                    "div.sV13ff",               
                    "div.Ww4FFb",               
                    # MODIFIED: Removed invalid selector "div. বৃত্তাকার"
                    "div[jscontroller][data-hp]", 
                    "div.hlcw0c"                
                ]
                
                item_locators = None
                found_selector = "N/A"

                for selector in result_item_selectors:
                    logger.debug(f"PlaywrightSearchTool: Trying result item selector: '{selector}'")
                    current_locators = page.locator(selector)
                    if await current_locators.count() > 0:
                        item_locators = current_locators
                        found_selector = selector
                        logger.info(f"PlaywrightSearchTool: Found {await item_locators.count()} potential result items with selector '{selector}'.")
                        break
                    else:
                        logger.debug(f"PlaywrightSearchTool: No results with selector '{selector}'.")
                
                if not item_locators or await item_locators.count() == 0:
                    logger.warning(f"PlaywrightSearchTool: No result items found with any known selectors for query '{query}'. Page structure might have changed or CAPTCHA present.")
                    screenshot_path_no_match = screenshots_dir / f"debug_playwright_no_selectors_match_{query[:20].replace(' ','_').replace('/','')}.png"
                    try:
                        await page.screenshot(path=screenshot_path_no_match)
                        logger.info(f"PlaywrightSearchTool: Saved screenshot for debugging (no selectors matched) to {screenshot_path_no_match}")
                        return f"No search results found (selectors did not match). A debug screenshot was saved: {screenshot_path_no_match}"
                    except Exception as ss_e:
                        logger.error(f"PlaywrightSearchTool: Failed to take screenshot: {ss_e}")
                        return "No search results found (selectors did not match), and failed to take debug screenshot."

                count = 0
                for i in range(min(await item_locators.count(), self.num_results_to_fetch + 2)): 
                    if count >= self.num_results_to_fetch:
                        break
                    
                    item = item_locators.nth(i)
                    
                    title_text = "N/A"
                    url_attribute = "N/A"
                    snippet_text = "N/A"

                    title_elements = item.locator('h3')
                    if await title_elements.count() > 0:
                        title_content = await title_elements.first.text_content(timeout=2000)
                        title_text = title_content.strip() if title_content else "N/A"

                    link_elements = item.locator('a[href]:has(h3), h3 a[href], a[jsname]')
                    if await link_elements.count() > 0:
                        href_val = await link_elements.first.get_attribute('href', timeout=1000)
                        if href_val and (href_val.startswith("http://") or href_val.startswith("https://")):
                             url_attribute = href_val
                        elif href_val and href_val.startswith("/url?q="): 
                            try:
                                actual_url_encoded = href_val.split("/url?q=")[1].split("&")[0]
                                url_attribute = urllib.parse.unquote(actual_url_encoded) 
                            except Exception as url_e:
                                logger.warning(f"Could not parse Google redirect URL {href_val}: {url_e}")
                                url_attribute = href_val # Fallback to original redirect
                    
                    snippet_selector_candidates = [
                        'div[data-sncf="1"]', 'div.VwiC3b', 'div.MUxGbd span', 
                        'div.wwHVDd', 'span.FCUp0c', 'div.Uroaid', 'div.gGqAYc'
                    ]
                    for snip_sel_str in snippet_selector_candidates:
                        snippet_loc = item.locator(snip_sel_str)
                        if await snippet_loc.count() > 0:
                            all_text_parts = await snippet_loc.all_text_contents()
                            if all_text_parts:
                                full_snippet = " ".join([part.strip() for part in all_text_parts if part.strip()])
                                if len(full_snippet) > 20: 
                                    snippet_text = full_snippet.replace("\n", " ").strip()
                                    break 
                    
                    if title_text != "N/A" and url_attribute != "N/A" and not url_attribute.startswith("/search?"):
                        results_output.append(f"Title: {title_text}\nURL: {url_attribute}\nSnippet: {snippet_text}\n---")
                        count += 1
                
                if not results_output:
                    logger.warning(f"PlaywrightSearchTool: No valid results extracted after iterating items for query '{query}'. Used item selector: '{found_selector}'")
                    screenshot_path_no_extract = screenshots_dir / f"debug_playwright_no_extraction_{query[:20].replace(' ','_').replace('/','')}.png"
                    try:
                        await page.screenshot(path=screenshot_path_no_extract)
                        logger.info(f"PlaywrightSearchTool: Saved screenshot (no extraction) for debugging to {screenshot_path_no_extract}")
                        return f"No search results extracted (parsing failed with item selector '{found_selector}'). A debug screenshot was saved: {screenshot_path_no_extract}"
                    except Exception as ss_e:
                        logger.error(f"PlaywrightSearchTool: Failed to take screenshot: {ss_e}")
                        return "No search results extracted (parsing failed), and failed to take debug screenshot."

                logger.info(f"PlaywrightSearchTool: Extracted {len(results_output)} results for query '{query}'.")
                return "\n".join(results_output)

        except PlaywrightException as e:
            logger.error(f"PlaywrightSearchTool: A Playwright error occurred: {e}", exc_info=True)
            return f"Error during Playwright operation: {e}"
        except Exception as e:
            logger.error(f"PlaywrightSearchTool: An unexpected error occurred: {e}", exc_info=True)
            return f"An unexpected error occurred during web search: {e}"
        finally:
            if page:
                try: await page.close()
                except Exception as e_page: logger.warning(f"PlaywrightSearchTool: Error closing page: {e_page}")
            if context:
                try: await context.close()
                except Exception as e_context: logger.warning(f"PlaywrightSearchTool: Error closing context: {e_context}")
            if browser:
                try:
                    await browser.close()
                    logger.info("PlaywrightSearchTool: Browser closed.")
                except Exception as e_browser: logger.warning(f"PlaywrightSearchTool: Error closing browser: {e_browser}")

    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        raise NotImplementedError("PlaywrightSearchTool does not support synchronous execution.")

async def main():
    tool = PlaywrightSearchTool(headless_mode=True) 
    
    test_queries = ["latest AI research trends", "how to make pasta carbonara", "benefits of unit testing"]
    
    for test_query in test_queries:
        print(f"\nTesting PlaywrightSearchTool with query: '{test_query}'")
        results = await tool.arun({"query": test_query}) 
        print("\n--- Search Results ---")
        print(results)
        print("--------------------")
        if not tool.headless_mode:
            await asyncio.sleep(5)
        else:
            await asyncio.sleep(1)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(name)s - %(module)s - %(funcName)s - Line %(lineno)d - %(message)s'
    )
    logging.getLogger("playwright").setLevel(logging.WARNING)
    # MODIFIED: Import urllib.parse for the main test block if needed, though it's used in _arun now
    import urllib.parse 
    asyncio.run(main())
