import asyncio
import logging
from typing import Optional, List, Type, Any
from pathlib import Path # Corrected: Import Path

from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic.v1 import BaseModel, Field # Using pydantic.v1 for Langchain compatibility

from playwright.async_api import async_playwright, Page, Browser, BrowserContext, Error as PlaywrightException

logger = logging.getLogger(__name__)

# --- Input Schema for the Tool ---
class PlaywrightSearchInput(BaseModel):
    query: str = Field(description="The search query string.")
    # num_results: int = Field(default=5, description="Number of search results to return.")
    # search_engine_url: str = Field(default="https://www.google.com/search", description="The base URL of the search engine to use.")


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

    search_engine_url: str = "https://www.google.com/search" # Default, can be changed
    num_results_to_fetch: int = 5
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36" # Keep this updated
    )
    headless_mode: bool = True # Added attribute for easier toggling


    async def _arun(
        self,
        query: str, # This matches the 'query' field in PlaywrightSearchInput
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any # Collect any other kwargs that might be passed
    ) -> str:
        """
        Asynchronously performs a web search using Playwright.

        Args:
            query: The search query string.
            run_manager: Langchain callback manager.

        Returns:
            A string containing formatted search results (titles, URLs, snippets),
            or an error message if the search fails.
        """
        logger.info(f"PlaywrightSearchTool: Starting search for query: '{query}'")
        results_output: List[str] = []
        browser: Optional[Browser] = None
        context: Optional[BrowserContext] = None
        page: Optional[Page] = None

        try:
            async with async_playwright() as p:
                try:
                    # Use the headless_mode attribute
                    browser = await p.chromium.launch(headless=self.headless_mode) 
                    logger.info(f"PlaywrightSearchTool: Chromium browser launched (headless: {self.headless_mode}).")
                except PlaywrightException as e:
                    logger.error(f"PlaywrightSearchTool: Failed to launch browser: {e}")
                    return f"Error: Failed to launch browser. {str(e)}"

                context = await browser.new_context(user_agent=self.user_agent)
                page = await context.new_page()
                
                encoded_query = query.replace(" ", "+")
                full_search_url = f"{self.search_engine_url}?q={encoded_query}"
                
                logger.info(f"PlaywrightSearchTool: Navigating to search engine: {full_search_url}")

                try:
                    await page.goto(full_search_url, timeout=30000) 
                    await page.wait_for_load_state('domcontentloaded', timeout=15000)
                    logger.info(f"PlaywrightSearchTool: Page loaded for query '{query}'")

                    # --- IMPORTANT: SELECTOR DEBUGGING ---
                    # If selectors fail, set headless_mode=False when creating the tool instance,
                    # and uncomment the next line.
                    # This will pause execution, allowing you to inspect the page in the Playwright browser.
                    # await page.pause() 
                    # --- END SELECTOR DEBUGGING ---

                except PlaywrightException as e: 
                    logger.error(f"PlaywrightSearchTool: Error navigating or loading page for query '{query}': {e}")
                    try:
                        Path("workspace/screenshots").mkdir(parents=True, exist_ok=True)
                        screenshot_path_nav_error = f"workspace/screenshots/debug_playwright_nav_error_{query[:20].replace(' ','_').replace('/','')}.png"
                        await page.screenshot(path=screenshot_path_nav_error)
                        logger.info(f"PlaywrightSearchTool: Saved screenshot on navigation error to {screenshot_path_nav_error}")
                    except Exception as ss_e:
                        logger.error(f"PlaywrightSearchTool: Failed to take screenshot on navigation error: {ss_e}")
                    return f"Error: Could not navigate to search results page. {str(e)}"
                
                result_item_selectors = [
                    "div.g", "div.Gx5Zad", "div.kvH3mc", "div.MjjYud",
                    "div.sV13ff", "div.Ww4FFb",
                ]
                
                item_locators = None
                found_selector = None
                for selector in result_item_selectors:
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
                    try:
                        Path("workspace/screenshots").mkdir(parents=True, exist_ok=True)
                        screenshot_path = f"workspace/screenshots/debug_playwright_no_selectors_match_{query[:20].replace(' ','_').replace('/','')}.png"
                        await page.screenshot(path=screenshot_path)
                        logger.info(f"PlaywrightSearchTool: Saved screenshot for debugging (no selectors matched) to {screenshot_path}")
                        return f"No search results found (selectors did not match). A debug screenshot was saved: {screenshot_path}"
                    except Exception as ss_e:
                        logger.error(f"PlaywrightSearchTool: Failed to take screenshot: {ss_e}")
                        return "No search results found (selectors did not match), and failed to take debug screenshot."

                count = 0
                for i in range(await item_locators.count()):
                    if count >= self.num_results_to_fetch:
                        break
                    
                    item = item_locators.nth(i)
                    
                    title_text = "N/A"
                    title_elements = item.locator('h3')
                    if await title_elements.count() > 0:
                        title_content = await title_elements.first.text_content(timeout=2000)
                        title_text = title_content.strip() if title_content else "N/A"

                    url_attribute = "N/A"
                    link_elements = item.locator('a[href]')
                    if await link_elements.count() > 0:
                        href_val = await link_elements.first.get_attribute('href', timeout=1000)
                        url_attribute = href_val if href_val else "N/A"
                    
                    snippet_text = "N/A"
                    snippet_selector_candidates = [
                        item.locator('div.VwiC3b span[role="text"]').first,
                        item.locator('div.MUxGbd span').first,
                        item.locator('div.wwHVDd').first,
                        item.locator('span.FCUp0c').first,
                        item.locator('div[data-sncf="1"]').first
                    ]
                    for snip_loc in snippet_selector_candidates:
                        if await snip_loc.count() > 0:
                            snip_content = await snip_loc.text_content(timeout=1000)
                            if snip_content and len(snip_content.strip()) > 10 :
                                snippet_text = snip_content.strip().replace("\n", " ")
                                break 
                    
                    if title_text != "N/A" and url_attribute != "N/A":
                        results_output.append(f"Title: {title_text}\nURL: {url_attribute}\nSnippet: {snippet_text}\n---")
                        count += 1
                
                if not results_output:
                    logger.warning(f"PlaywrightSearchTool: No results extracted after iterating items for query '{query}'. Used selector: '{found_selector}'")
                    try:
                        Path("workspace/screenshots").mkdir(parents=True, exist_ok=True)
                        screenshot_path_no_extract = f"workspace/screenshots/debug_playwright_no_extraction_{query[:20].replace(' ','_').replace('/','')}.png"
                        await page.screenshot(path=screenshot_path_no_extract)
                        logger.info(f"PlaywrightSearchTool: Saved screenshot (no extraction) for debugging to {screenshot_path_no_extract}")
                        return f"No search results extracted (parsing failed with selector '{found_selector}'). A debug screenshot was saved: {screenshot_path_no_extract}"
                    except Exception as ss_e:
                        logger.error(f"PlaywrightSearchTool: Failed to take screenshot: {ss_e}")
                        return "No search results extracted (parsing failed), and failed to take debug screenshot."

                logger.info(f"PlaywrightSearchTool: Extracted {len(results_output)} results for query '{query}'.")
                return "\n".join(results_output) if results_output else "No results found."

        except PlaywrightException as e:
            logger.error(f"PlaywrightSearchTool: A Playwright error occurred: {e}", exc_info=True)
            return f"Error during Playwright operation: {e}"
        except Exception as e:
            logger.error(f"PlaywrightSearchTool: An unexpected error occurred: {e}", exc_info=True)
            return f"An unexpected error occurred during web search: {e}"
        finally:
            if page:
                try:
                    await page.close()
                except Exception as e_page: 
                    logger.warning(f"PlaywrightSearchTool: Error closing page: {e_page}")
            if context:
                try:
                    await context.close()
                except Exception as e_context:
                    logger.warning(f"PlaywrightSearchTool: Error closing context: {e_context}")
            if browser:
                try:
                    await browser.close()
                    logger.info("PlaywrightSearchTool: Browser closed.")
                except Exception as e_browser:
                    logger.warning(f"PlaywrightSearchTool: Error closing browser: {e_browser}")

    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        raise NotImplementedError(
            "PlaywrightSearchTool does not support synchronous execution. "
            "Use arun or astream instead."
        )

# --- Basic Test Block ---
async def main():
    # To make debugging selectors easier, you can set headless_mode to False
    tool = PlaywrightSearchTool(headless_mode=True) # Set to False to see browser
    
    test_queries = ["latest AI research trends", "how to make pasta carbonara", "benefits of unit testing"]
    
    for test_query in test_queries:
        print(f"\nTesting PlaywrightSearchTool with query: '{test_query}'")
        # MODIFIED: Call arun with a dictionary matching args_schema
        results = await tool.arun({"query": test_query}) 
        print("\n--- Search Results ---")
        print(results)
        print("--------------------")
        await asyncio.sleep(2) 


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(name)s - %(module)s - %(funcName)s - Line %(lineno)d - %(message)s'
    )
    logging.getLogger("playwright").setLevel(logging.WARNING)
    
    asyncio.run(main())