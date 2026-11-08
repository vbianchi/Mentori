# S571_rlm_reading

Written by `uv run --frozen python scripts/S571_rlm_reading.py` (test: `scripts/S571_rlm_reading_test.py`). Code line
numbers are at commit 6318e8e8 (orchestrator.py and exp1_rlm_vs_singlepass.py have uncommitted edits since).

What the code does:

1. Reads Figure 3a's judge cells for Mentori RLM-10 (G1 `rlm_10`) and package RLM-10 (G6 `cap10`) with the functions
   Figure 3 itself uses (`S463.read_answers`, `read_collect`, `judge_rows` through `judge_rows_v25`, `read_extra`), on
   the same frozen inputs `S463 rebuild` reads. Question types from `S511.questions()` (60 one-paper, 26 many-paper,
   10 false premise, 39 not answerable).
2. Reproduces Figure 3a's committed pass rates at score 4 (Source Data Fig. 3, sheet Fig. 3a, rows 'strategy,
   question group') for both strategies on one-paper and many-paper questions, and Mentori RLM-10's every-key-paper
   counts in S511's results.json; refuses on any difference.
3. Per answer: all successful sub-calls, successful sub-calls that carried paper text, root turns, distinct papers
   read, gate rejections and their kinds (Mentori), answer words, pass at 4.
   - Mentori (record line S463 read; `generation.rlm.metadata`, written by exp1_rlm_vs_singlepass.py:627 from
     orchestrator.py:157-189; `generation.calls`, one summary per call, n_passages from pipeline.py:42):
     all sub-calls = `sub_calls_ok` (executor.py:268-271), what the gate counts: every successful
     llm_summarize/llm_query/llm_extract call except one handed an empty list, so it includes llm_query(prompt) with
     no passages. With paper text = calls with `n_passages` > 0 not listed in `sub_call_failures` (passages handed
     as strings carry no id, so a lower bound). Papers = distinct `file_name` (paper store, `S511.paper_map`) of
     `passages_seen`, every chunk a search or a navigation read returned to the code: a proxy and an upper bound, because the record
     holds each sub-call's passage count but not its ids.
   - Mentori gate: FINAL is rejected when `sub_calls_ok < 3 or not has_substance` (orchestrator.py:440), at most 3
     times; `rejections` counts both kinds and the record does not say which. S571 places the root calls in the
     call list (first call root; a root call carries no ids; root prompt_tokens rise strictly) and counts the
     successful sub-calls before each rejection: under 3 means the count alone rejected; 3 or more means the answer
     lacked substance; otherwise, or when the possible placements disagree, the kind is "cannot tell".
   - Package (g6_d135 answers.jsonl, adapter.py:1185-1200; frozen g6_calls_after_d135 calls.jsonl, adapter.py:747-776):
     all sub-calls = `calls.sub - calls.sub_failed`, checked against the call records; root turns = `turns_used`;
     papers = papers whose text appears in a successful sub-call's `prompt_sent`: every 64-character run of each
     paper's text in B4_rlm_ref_context.json (whitespace collapsed, runs shared by two papers dropped) is indexed,
     the prompt is sampled at every 32nd position, and a paper with 2 or more sampled windows found counts as read
     (a copy of 127 characters or more of text found in only one paper is always found). With paper text = successful sub-calls with at least one
     paper read. A paper is read in depth when the distinct characters of it covered by the windows found (each
     window counting its first 32), across the answer's successful sub-calls, reach 2,000: text sent to two
     sub-calls counts once.
4. Tables by strategy and type; gate rejections by kind; pass at 4 by whether every key paper was read (S511's
   definition) and by whether the gate rejected; a per-question paired view on many-paper questions with Pearson r
   and a 10,000-resample percentile bootstrap (seed 20261013); all questions where one strategy passes 3 of 3 draws
   and the other 0 of 3. Association only.

Files: results.json (every number and every answer's row, with `_provenance`), results.md (the tables), header.json
(the same provenance: script and code sha256, git HEAD, whether tracked files differ from HEAD, UTC time, input
sha256).
