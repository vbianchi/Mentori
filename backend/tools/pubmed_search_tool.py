# backend/tools/pubmed_search_tool.py
import logging
import asyncio
import re
from typing import Optional, Type, Any # Added Any

from langchain_core.tools import BaseTool, ToolException
from langchain_core.callbacks import CallbackManagerForToolRun
# <<< MODIFIED IMPORT: Using Pydantic v2 directly --- >>>
from pydantic import BaseModel, Field
# <<< --- END MODIFIED IMPORT --- >>>
from Bio import Entrez
from urllib.error import HTTPError

from backend.config import settings

logger = logging.getLogger(__name__)

class PubMedSearchInput(BaseModel): # <<< Now inherits from Pydantic v2 BaseModel
    query: str = Field(description="The search query string for PubMed. Optionally, ' max_results=N' can be appended to specify the number of results.")
    # No model_config needed for this simple model

class PubMedSearchTool(BaseTool):
    name: str = "pubmed_search"
    description: str = (
        f"Use this tool ONLY to search for biomedical literature abstracts on PubMed. "
        f"Input MUST be a search query string (e.g., 'CRISPR gene editing cancer therapy'). "
        f"You can optionally append ' max_results=N' (space required before 'max_results') to the end of the query "
        f"string to specify the number of results (default is {settings.tool_pubmed_default_max_results}, max is 20). "
        f"Returns formatted summaries including title, authors, link (DOI or PMID), and abstract snippet "
        f"(max {settings.tool_pubmed_max_snippet} chars)."
    )
    args_schema: Type[BaseModel] = PubMedSearchInput

    async def _arun(
        self,
        query: str, # Accepts the string directly
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any # <<< Any is now defined
    ) -> str:
        tool_name = self.name
        logger.info(f"Tool '{tool_name}' received raw input: '{query}'")
        if not isinstance(query, str) or not query.strip():
            logger.error(f"Tool '{tool_name}': Received invalid input. Expected a non-empty search query string.")
            raise ToolException("Invalid input. Expected a non-empty search query string.")

        entrez_email = settings.entrez_email
        default_max_results = settings.tool_pubmed_default_max_results
        max_snippet_len = settings.tool_pubmed_max_snippet

        if not entrez_email:
            logger.error(f"Tool '{tool_name}': Entrez email not configured in settings.")
            raise ToolException("PubMed Search tool is not configured (Missing Entrez email).")
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
            raise ToolException("No search query provided after processing options.")

        try:
            # Entrez calls are synchronous, so run them in a thread pool
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
                    raise ToolException("Could not parse PubMed results (unexpected format).")

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
                            if isinstance(part, str): abstract_text_parts.append(part)
                            elif hasattr(part, 'attributes') and 'Label' in part.attributes: abstract_text_parts.append(f"\n**{part.attributes['Label']}**: {str(part)}")
                            elif isinstance(part, dict) and '#text' in part: abstract_text_parts.append(part['#text'])
                            else: abstract_text_parts.append(str(part))
                    full_abstract = " ".join(filter(None, abstract_text_parts)).strip()
                    if not full_abstract: full_abstract = "No Abstract Available"
                    abstract_snippet = full_abstract[:max_snippet_len]
                    if len(full_abstract) > max_snippet_len: abstract_snippet += "..."

                    doi = None
                    article_ids = record.get('PubmedData', {}).get('ArticleIdList', [])
                    if isinstance(article_ids, list):
                        for article_id_node in article_ids:
                            if hasattr(article_id_node, 'attributes') and article_id_node.attributes.get('IdType') == 'doi': doi = str(article_id_node); break
                            elif isinstance(article_id_node, dict) and article_id_node.get('IdType') == 'doi': doi = article_id_node.get('#text'); break
                    link = f"https://doi.org/{doi}" if doi else f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"; link_text = f"DOI:{doi}" if doi else f"PMID:{pmid}"
                    summaries.append(f"**Result {i+1}:**\n**Title:** {title}\n**Authors:** {authors_str}\n**Link:** [{link_text}]({link})\n**Abstract Snippet:** {abstract_snippet}\n---")
                except Exception as parse_err:
                    logger.error(f"Tool '{tool_name}': Error parsing PubMed record {i+1} (PMID: {pmid}) for query '{cleaned_query}': {parse_err}", exc_info=True)
                    summaries.append(f"**Result {i+1}:**\nError parsing record (PMID: {pmid}).\n---")
            return "\n".join(summaries) if summaries else "No valid PubMed records processed."
        except HTTPError as e:
            logger.error(f"Tool '{tool_name}': HTTP Error fetching PubMed data for query '{cleaned_query}': {e.code} {e.reason}")
            raise ToolException(f"Failed to fetch data from PubMed (HTTP Error {e.code}). Check network or NCBI status.")
        except Exception as e:
            logger.error(f"Tool '{tool_name}': Error searching PubMed for '{cleaned_query}': {e}", exc_info=True)
            raise ToolException(f"An unexpected error occurred during PubMed search: {type(e).__name__}")

    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None, **kwargs: Any) -> str:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                future = asyncio.run_coroutine_threadsafe(self._arun(query=query, run_manager=run_manager, **kwargs), loop)
                return future.result(timeout=60) # Adjust timeout as needed
            else:
                return asyncio.run(self._arun(query=query, run_manager=run_manager, **kwargs))
        except Exception as e:
            logger.error(f"Error running PubMedSearchTool synchronously for '{query}': {e}", exc_info=True)
            return f"Error: {e}"
