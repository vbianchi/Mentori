
from backend.mcp.decorator import mentori_tool

@mentori_tool(category="Genomics", agent_role=None, is_llm_based=False)
def calculate_gc_content(sequence: str) -> str:
    """
    Calculates the GC content percentage of a DNA sequence.
    
    Args:
        sequence: A DNA sequence string (e.g., "ATGC")
        
    Returns:
        String with GC percentage.
    """
    if not sequence:
        return "Error: Empty sequence"
        
    seq_upper = sequence.upper()
    g_count = seq_upper.count('G')
    c_count = seq_upper.count('C')
    total = len(seq_upper)
    
    if total == 0:
        return "0%"
        
    gc_percent = (g_count + c_count) / total * 100
    return f"{gc_percent:.2f}%"
