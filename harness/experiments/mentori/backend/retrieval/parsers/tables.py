import tabula
from typing import List, Dict, Any
import logging
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)

class TableParser:
    """
    Extracts tables from PDFs using tabula-py (wrapper around tabula-java).
    """
    
    def __init__(self):
        pass
        
    def parse(self, file_path: str, page_numbers: List[int] = None) -> List[Dict[str, Any]]:
        """
        Extract tables from specific pages.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        logger.info(f"Extracting tables from {path.name} (pages: {page_numbers or 'all'})")
        
        results = []
        
        target_pages = page_numbers if page_numbers else "all"
        
        try:
            # Read PDF into list of DataFrames
            dfs = tabula.read_pdf(
                file_path, 
                pages=target_pages, 
                multiple_tables=True,
                silent=True
            )
            
            for i, df in enumerate(dfs):
                if isinstance(df, pd.DataFrame) and not df.empty:
                    # Convert to Markdown for LLM consumption
                    markdown = df.to_markdown(index=False)
                    
                    # Store result
                    results.append({
                        "table_index": i,
                        "markdown": markdown,
                        "rows": len(df),
                        "cols": len(df.columns)
                        # Note: Tabula doesn't always give page number easily in the list output
                        # We might need to map it back if critical, or run per-page.
                        # For now, batching is faster.
                    })
                    
        except Exception as e:
            logger.error(f"Table extraction failed: {e}")
            # Do not raise, just return empty results (tables are optional enhancement)
            
        return results
