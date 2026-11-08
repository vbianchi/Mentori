<!-- provenance
{
 "script": "scripts/S601_retrieval_sweep_provenance.py",
 "script_sha256": "fbf065f679d817d4545e0a304c4439ff1270833ced582182e6874fdd88680e22",
 "command": "uv run --frozen python scripts/S601_retrieval_sweep_provenance.py",
 "backup_repo": "../Mentori-backup",
 "backup_head": "39bc3f4af796eddce697aed4701ea5c2f83492b6",
 "inputs_sha256": {
  "findings/recompute/S222_corpus_papers_corrected.csv": "1020bccbb72b1f4c71551d4cf2eda93a037b16536478314d348ae4520035ccbd",
  "findings/recompute/D75_Q51_corpus/corpus_core_deposit.csv": "bde0b3b3aa2ca6e311702cf216ed2a2f9a05966788361a6a3a448023859cbe7d"
 },
 "rulings": "rulings page 6 Nov, M7: O2; R12: O2"
}
-->

# S601: the February retrieval sweep (M7, R12)

Reproduced first:

- (1) n_queries 28 and 28 equal the queries with a source file in the ground truth each script read at its commit
- (2) exp01's models (4) equal the script's MODEL_ALIASES and its corpus sizes [5, 10, 15, 20, 30] the commit message's

## Which script wrote each retrieval result (M7)

| repo file | experiment | timestamp | Mentori-backup commit | script | is_relevant cases | ground truth: queries, with source, with source and keywords |
|---|---|---|---|---|---|---|
| exp01_embedding_latest.json | exp2_embedding_comparison | 20260211_174232 | fad8cfdc (2026-02-11) | tests/experiments/exp2_embedding_comparison.py | 6 of 6 | 30, 28, 28 (tests/experiments/ground_truth_retrieval.json) |
| exp02_search_latest.json | exp3_hybrid_search_ablation | 20260211_180248 | 116ab13b (2026-02-11) | tests/experiments/exp3_hybrid_search_ablation.py | 6 of 6 | 30, 28, 28 (tests/experiments/ground_truth_retrieval.json) |
| exp03a_chunking_latest.json | exp4_chunking_comparison | 20260213_142928 | bd3185ca (2026-02-13) | tests/experiments/exp4_chunking_comparison.py | 6 of 6 | not named |
| exp03b_scalability_latest.json | exp3c_scalability | 20260216_090601 | 7a21e287 (2026-02-16) | tests/experiments/exp3c_scalability.py | 6 of 6 | not named |

The rule, as the embedding script states it:

```python
def is_relevant(result: Dict, query_gt: Dict) -> bool:
    """Check if a result is relevant to the ground truth query.

    Relevant = comes from expected source file AND contains at least one
    expected keyword (case-insensitive).
    """
    source_files = query_gt.get("source_files", [])
    expected_keywords = query_gt.get("expected_in_chunk", [])

    if not source_files:
        return False  # Unanswerable queries have no relevant results

    result_source = result.get("source_file", "")
    if result_source not in source_files:
        return False

    if not expected_keywords:
        # No keywords specified — any chunk from the right source is relevant
        return True

    text_lower = result.get("text", "").lower()
    for kw in expected_keywords:
        if kw.lower() in text_lower:
            return True

    return False
```

Every script passes the same made-up cases: a chunk counts as relevant only when it comes from one of the query's source files and, when the query lists expected keywords, holds at least one of them (case ignored); a query with no source file has no relevant chunk.

## The five retrieval papers in the corpus (R12)

read by file name from ../Mentori-backup/data/workspace/c87ca97f-d5b8-41c5-a670-e91fb618d7ba/papers; the sweep's own folder tests/test_files_rag/papers/ is in neither that repository's history nor on this machine.

| file | DOI printed | found on | corpus paper | bucket | corpus file | same bytes as indexed |
|---|---|---|---|---|---|---|
| fgene-07-00075.pdf | 10.3389/fgene.2016.00075 | first two pages | 47 | core | 47_htsflow.pdf | yes |
| 1-s2.0-S1046202318304742-main.pdf | 10.1016/j.ymeth.2019.07.014 | first two pages | 50 | core | 50_4cseq_protocol.pdf | yes |
| 1471-2105-13-S4-S17.pdf | 10.1186/1471-2105-13-S4-S17 | later page, holds the file name | 49 | core | 49_pdbinder.pdf | yes |
| 3463.pdf | 10.1158/0008-5472.CAN-16-0316 | first two pages | 48 | core | 48_myc_oncogene.pdf | not in the core deposit list |
| s12859-015-0742-6.pdf | 10.1186/s12859-015-0742-6 | first two pages | 46 | core | 46_methylpipe.pdf | yes |
