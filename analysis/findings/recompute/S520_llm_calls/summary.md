<!-- provenance: scripts/S520_llm_calls.py sha256 312cedbe6967d0a4, HEAD not stamped (report --frozen), written not stamped (report --frozen) -->
# Language-model calls of the study

**Unmapped: 258 call-log files no rule names, not opened and not counted: studio:mentori-runs/recompute/G13_runs/inputs/runs/exp_01__matched_budget__exp_v4_s20_n0/calls.jsonl (2,890,136 bytes), studio:mentori-runs/recompute/G17_runs/out_s6_w_g17/check_11453/check_calls.jsonl (618,078 bytes), studio:mentori-runs/recompute/G17_runs/out_s6_w_g17/judge/exp_01__rlm_10_ctrl__exp_v4_s20_n0/judge_passages_calls.jsonl (506,118 bytes), studio:mentori-runs/recompute/G17_runs/out_s6_w_g17/judge/exp_01__rlm_10_ctrl__exp_v4_s20_n0/judge_passages_recheck_calls.jsonl (58,819 bytes), studio:mentori-runs/recompute/G17_runs/out_s6_w_g17/judge/exp_01__rlm_10_nogate__exp_v4_s20_n0/judge_passages_calls.jsonl (509,602 bytes), studio:mentori-runs/recompute/G17_runs/out_s6_w_g17/judge/exp_01__rlm_10_nogate__exp_v4_s20_n0/judge_passages_recheck_calls.jsonl (59,031 bytes), studio:mentori-runs/recompute/G17_runs/out_s6_w_g17/judge/exp_01__rlm_10_nosearch__exp_v4_s20_n0/judge_passages_calls.jsonl (510,770 bytes), studio:mentori-runs/recompute/G17_runs/out_s6_w_g17/judge/exp_01__rlm_10_nosearch__exp_v4_s20_n0/judge_passages_recheck_calls.jsonl (59,281 bytes), studio:mentori-runs/recompute/G17_runs/out_s6_w_g17_d23/check_11454/check_calls.jsonl (618,272 bytes), studio:mentori-runs/recompute/G17_runs/out_s6_w_g17_d23/check_11455/check_calls.jsonl (618,274 bytes), studio:mentori-runs/recompute/G17_runs/out_s6_w_g17_d23/judge/exp_01__rlm_10_ctrl__exp_v4_s20_n0/judge_passages_calls.jsonl (1,017,924 bytes), studio:mentori-runs/recompute/G17_runs/out_s6_w_g17_d23/judge/exp_01__rlm_10_ctrl__exp_v4_s20_n0/judge_passages_recheck_calls.jsonl (59,824 bytes), studio:mentori-runs/recompute/G17_runs/out_s6_w_g17_d23/judge/exp_01__rlm_10_nogate__exp_v4_s20_n0/judge_passages_calls.jsonl (1,015,595 bytes), studio:mentori-runs/recompute/G17_runs/out_s6_w_g17_d23/judge/exp_01__rlm_10_nogate__exp_v4_s20_n0/judge_passages_recheck_calls.jsonl (58,106 bytes), studio:mentori-runs/recompute/G17_runs/out_s6_w_g17_d23/judge/exp_01__rlm_10_nosearch__exp_v4_s20_n0/judge_passages_calls.jsonl (1,019,589 bytes), studio:mentori-runs/recompute/G17_runs/out_s6_w_g17_d23/judge/exp_01__rlm_10_nosearch__exp_v4_s20_n0/judge_passages_recheck_calls.jsonl (57,880 bytes), studio:mentori-runs/recompute/R0_pilot_studio/proxy_calls.jsonl (5,049,298 bytes), studio:mentori-runs/recompute/S18f_runs/out_v25/B2_shard0of2/judge_evidence_v25_calls.jsonl (1,120,949 bytes), studio:mentori-runs/recompute/S18f_runs/out_v25/B2_shard1of2/judge_evidence_v25_calls.jsonl (1,091,676 bytes), studio:mentori-runs/recompute/S18f_runs/out_v25/B_shard0of2/judge_evidence_v25_calls.jsonl (1,120,388 bytes) and 238 more (summary.json).**

Read at: beelink 2026-11-07T05:33:50Z to 2026-11-07T05:34:10Z; laptop 2026-11-07T05:34:18Z to 2026-11-07T05:35:31Z; studio 2026-11-07T05:27:31Z to 2026-11-07T05:30:24Z

One call is one line in a named call log (rule in scripts/S520_llm_calls.py; rule 5 ruled by D201 Q7: replaced answers in their own column). The total counts run tier only.

## Total

| Calls | Ok | Failed | Replaced | Of those, on no answer line | Could not be joined |
|---|---|---|---|---|---|
| 1,158,418 | 1,155,810 | 2,608 | 34,178 | 7,504 | 17,883 |

Failed by status: blocked 55, empty 154, error 1,064, length 934, malformed_function_call 57, malformed_response 234, proxy_error 2, recitation 105, stalled 1, unexpected_tool_call 2

Figure 1 legend total: 1,158,418.

Of the replaced calls, 12,461 are the main judge's key v2.4 calls on the 132 questions key v2.5 changed, each judged again in the matching S6 out.

## Methods groups

| Group | Calls | Ok | Failed |
|---|---|---|---|
| RAGAS and RAGChecker | 818,897 | 818,855 | 42 |
| generation | 273,575 | 271,267 | 2,308 |
| judges | 65,946 | 65,688 | 258 |

G5 and T1 cannot join ctx_uid: exp_06 keeps their answers in a results file outside the sink (experiments/scorers/records.py:15-16), so their 17,883 calls read not_joined.

Outside the total: checks 111,816, smokes 4,098, dropped by decision (nemotron, D116; deepseek-r1-70b, glm-4.7-flash, D265) 2,533, not mapped 0.

Scorers with no language-model call: MiniCheck, text overlap, concept recall, bge-m3 and the other encoders.

## By role

| Role | Calls | Ok | Failed | Replaced |
|---|---|---|---|---|
| RAGChecker check | 800,640 | 800,639 | 1 | 14,153 |
| RLM sub-call | 119,792 | 119,715 | 77 | 1,458 |
| RLM root | 72,829 | 71,511 | 1,318 | 687 |
| judge (a) | 43,935 | 43,935 | 0 | 11,352 |
| code generation | 37,850 | 37,197 | 653 | 5,110 |
| generator | 29,067 | 28,815 | 252 | 84 |
| RAGAS | 17,516 | 17,488 | 28 | 0 |
| second judge | 12,234 | 12,182 | 52 | 0 |
| orchestrator component | 9,122 | 9,114 | 8 | 14 |
| judge (b) | 6,217 | 6,011 | 206 | 1,109 |
| verifier | 4,915 | 4,915 | 0 | 27 |
| judge (evidence) | 2,662 | 2,662 | 0 | 0 |
| code judge | 888 | 888 | 0 | 133 |
| RAGChecker extract | 741 | 728 | 13 | 51 |
| judge (recheck) | 10 | 10 | 0 | 0 |

## By model

| Model | Calls | Ok | Failed |
|---|---|---|---|
| devstral-small-2:24b | 877,399 | 877,104 | 295 |
| gemini-3-flash-preview | 201,491 | 199,963 | 1,528 |
| gpt-oss:20b-date20261010 | 15,939 | 15,840 | 99 |
| gemini-2.5-pro | 13,991 | 13,867 | 124 |
| claude-haiku-4-5 | 13,668 | 13,545 | 123 |
| qwen3.8:27b | 12,234 | 12,182 | 52 |
| qwen3-coder:30b | 10,025 | 10,024 | 1 |
| gemma3:27b | 8,225 | 7,845 | 380 |
| qwen3-coder-next:q4_K_M | 5,444 | 5,440 | 4 |
| ? | 2 | 0 | 2 |

## By experiment

| Experiment | Calls | Ok | Failed | Replaced |
|---|---|---|---|---|
| Generation strategies | 846,196 | 846,046 | 150 | 16,632 |
| Corpus scaling | 113,243 | 112,238 | 1,005 | 6,067 |
| Strategy replication | 47,821 | 47,474 | 347 | 2,219 |
| Code generation | 38,738 | 38,085 | 653 | 5,243 |
| Package RLM depth caps | 30,511 | 30,359 | 152 | 977 |
| Package RLM at caps 5 10 20 | 30,295 | 30,235 | 60 | 1,357 |
| Pipeline ablation | 19,587 | 19,500 | 87 | 458 |
| Retrieval depth | 16,471 | 16,377 | 94 | 520 |
| Distiller on every step (stress) | 7,962 | 7,928 | 34 | 130 |
| Retrieval depth, local models | 2,779 | 2,779 | 0 | 0 |
| No retrieval and naive RAG | 2,060 | 2,060 | 0 | 380 |
| Matched-budget arm | 1,338 | 1,329 | 9 | 195 |
| Flat wide call | 585 | 585 | 0 | 0 |
| Plant-science reuse demonstration | 548 | 531 | 17 | 0 |
| Short-passage single pass | 225 | 225 | 0 | 0 |
| Judge on the 49 rated answers | 59 | 59 | 0 | 0 |

## Supplementary Figure 1 boxes

| Box | Calls |
|---|---|
| G1 | 846,196 |
| G4 | 113,243 |
| T2 | 47,821 |
| S2 | 38,738 |
| G6D | 30,511 |
| G6C | 30,295 |
| G3A | 19,587 |
| G5 | 16,471 |
| G9 | 7,962 |
| T1 | 2,779 |
| G3B | 2,060 |
| G2 | 1,338 |
| not in a box | 869 |
| I2 | 548 |
| RO | kept from April |
| MS | kept from April |
| T3C | 0 |
| T3D | 0 |

G7 and G8 sit in G3, G4 and G5; K1 and S18f sit in G1. G10, G11 and S508's 49 answers are not in a box.

## Still running at read time

No log written in the last 30 minutes on the machines read.

## Planned calls left (about)

| Job | Unit | Due | Done | Calls per answer so far | Calls left, about | Source |
|---|---|---|---|---|---|---|
| G10 flat wide call | answers | 585 | 585 | 1.0 | 0 | experiments/draws.csv row Flat wide call |
| G11 short-passage single pass | answers | 225 | 225 | 1.0 | 0 | experiments/draws.csv row Short-passage single pass |
| T2 four generators | answers | 7,020 | 7,033 | 4.722 | 0 | experiments/draws.csv row Strategy replication (D178); D197 paused the local multi_hop, rlm_5 and rlm_20, and whether they resume is open, so this due can fall |
| G7 judging on G4 and G3 | judged answers | 7,153 | 7,153 | 1.112 | 0 | experiments/RUNNING.md:146 (dry runs: S6G7G4 6,433, S6G7G3 720); D198 O2 and D199 keep phase 2 on these two sets, so S6G7G5 is left out |
| S6 on G4 | judged answers | 5,574 | 5,574 | 1.129 | 0 | experiments/RUNNING.md:137 |

No planned count: T3 component benchmarks and distiller prompts (not started; draws.csv holds no call or answer count for it (D198 O7: the 59-hour core)); Second judge outside 3f, 5e and S14 (held by D198 O4 (2,025 calls)); S4 gpt-oss-20b high (its end is UNVERIFIED; its calls fall in S2's sinks).

## Not counted, and why

- Embeddings lines: 1,152 (a call to an encoder, rule 4).
- April: 37,449 is the evaluation count (S13), and April's records hold only `llm_calls` per answer.
- Pre-lock work (S141_campaign, S373, S18e), by name, unopened: {"beelink": {"April or pre-lock work (rule 8)": 240, "a copy of records another source holds": 64}, "laptop": {"April or pre-lock work (rule 8)": 336, "a copy of records another source holds": 282}, "studio": {"April or pre-lock work (rule 8)": 1152, "a copy of records another source holds": 284}}.
- Duplicates removed: 289,539 lines (the same bytes in another source).
- Lines found only in a copy, not counted: {"mentori-runs": 0, "mentori-runs-s2": 0, "Mentori-reanalysis": 0, "mentori-runs-s2-laptop": 0, "mentori-runs-s2-laptop-d75": 0}.
- Call-log names no rule covers, unopened: 258.
- Clones not in the table: {"studio": ["mentori-runs-g13", "mentori-runs-g17", "mentori-runs-g19", "mentori-runs-g20", "mentori-runs-g3w", "mentori-runs-k1-11452", "mentori-runs-k1-cut", "mentori-runs-l1", "mentori-runs-s2-d114", "mentori-runs-s564", "mentori-runs-s584", "mentori-runs-s6w", "mentori-runs-second-studio", "mentori-runs-t2x", "mentori-runs-t3"], "beelink": ["mentori-runs-l1", "mentori-runs-s6w-second", "mentori-runs-t3"], "laptop": ["mentori-runs-s564", "mentori-runs-s6g7", "mentori-runs-s6w", "mentori-runs-second-laptop"]}.

## Checks on these numbers

Gates passed: 48 of 48. Sinks whose kept lines differ from the answers' llm_calls: 12 of 303.
Files read 2,429, lines 1,567,556, bad lines 1, unfinished last lines 0.
