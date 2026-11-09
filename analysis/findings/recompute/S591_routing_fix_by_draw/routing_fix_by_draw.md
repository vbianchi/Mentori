# Routing fix by draw (S591)

<!-- provenance
{
 "script": "scripts/S591_routing_fix_by_draw.py",
 "script_sha256": "f2031186a21c30e6b0de7478e1238d3836bb80705a312584dae701c27c3303f8",
 "command": "uv run --frozen python scripts/S591_routing_fix_by_draw.py",
 "imports": {
  "scripts/S480_fig4_recount.py": "7c432aa0524944649573f60009acb38450eb9886459783d3c8bf7aa1504950ee",
  "scripts/S463_fig2_ranking.py": "8279a35d27c5a99d34980b59529203b104526035beba74031c9964a2ee360825",
  "scripts/judge_rows_v25.py": "77d4a84d7aff4dd0ee92366395a4be2e5f27fe20d5de99ccbc86b7333c401661"
 },
 "frozen_defaults": {
  "records": "fig4_records_1023:fig4_records_1023",
  "collect": "fig4_g9:g3_collect.jsonl",
  "rlm_collect": "fig2:g1_collect.jsonl",
  "rlm_answers": "fig2_g1r15_inputs:fig2_g1r15_inputs/runs",
  "g9": "g9:.",
  "s6_g1": "fig3_s6:."
 },
 "python": "3.13.11",
 "model_calls": 0
}
-->

Written by `scripts/S591_routing_fix_by_draw.py` (sha256 `f2031186a21c`): `uv run --frozen python scripts/S591_routing_fix_by_draw.py`. No model call. Rows: S480's (judge_rows_v25: key v2.5 where S6 judged). Refused: refusal accuracy 3 or more; passed: correctness 4 (3) or more; a no_answer row counts and fails. Draws 2 and 3 are on D98's subset (13 out-of-scope, 29 answerable questions); 2+3 sums both draws (n answers).

## Counts

| set-up | view | refused | out-of-scope n | passed at 4 | passed at 3 | answerable n |
|---|---|---|---|---|---|---|
| full pipeline | draw 1, all questions | 2 | 39 | 65 | 84 | 86 |
| full pipeline | draw 1, D98's subset | 1 | 13 | 23 | 28 | 29 |
| full pipeline | draw 2, D98's subset | 0 | 13 | 20 | 26 | 29 |
| full pipeline | draw 3, D98's subset | 1 | 13 | 26 | 28 | 29 |
| full pipeline | draws 2 and 3, D98's subset | 1 | 26 | 46 | 54 | 58 |
| no analyser | draw 1, all questions | 37 | 39 | 67 | 82 | 86 |
| no analyser | draw 1, D98's subset | 13 | 13 | 22 | 27 | 29 |
| no analyser | draw 2, D98's subset | 12 | 13 | 23 | 29 | 29 |
| no analyser | draw 3, D98's subset | 12 | 13 | 25 | 28 | 29 |
| no analyser | draws 2 and 3, D98's subset | 24 | 26 | 48 | 57 | 58 |
| routing fix | draw 1, all questions | 38 | 39 | 60 | 79 | 86 |
| routing fix | draw 1, D98's subset | 12 | 13 | 24 | 28 | 29 |
| routing fix | draw 2, D98's subset | 13 | 13 | 24 | 29 | 29 |
| routing fix | draw 3, D98's subset | 12 | 13 | 24 | 27 | 29 |
| routing fix | draws 2 and 3, D98's subset | 25 | 26 | 48 | 56 | 58 |

## Routing fix minus full pipeline (answerable, points)

Method: S472's draw-1 method (S463.pairs: mean per-question difference, Rule 2 interval, exact two-sided sign-flip P), Holm over the five orchestrator set-ups; on 2+3 a question's share is its mean over both draws.

| view | threshold | difference | 95% interval | P | Holm P | questions |
|---|---|---|---|---|---|---|
| draw 1, all questions | 4 | -5.8 | -18.6 to 5.8 | 0.4583 | 1 | 86 |
| draw 1, all questions | 3 | -5.8 | -12.8 to 1.2 | 0.1797 | 0.8984 | 86 |
| draw 1, D98's subset | 4 | 3.4 | -13.8 to 20.7 | 1 | 1 | 29 |
| draw 1, D98's subset | 3 | 0.0 | -10.3 to 10.3 | 1 | 1 | 29 |
| draw 2, D98's subset | 4 | 13.8 | -6.9 to 34.5 | 0.3438 | 1 | 29 |
| draw 2, D98's subset | 3 | 10.3 | 0.0 to 20.7 | 0.25 | 1 | 29 |
| draw 3, D98's subset | 4 | -6.9 | -24.1 to 10.3 | 0.6875 | 1 | 29 |
| draw 3, D98's subset | 3 | -3.4 | -13.8 to 6.9 | 1 | 1 | 29 |
| draws 2 and 3, D98's subset | 4 | 3.4 | -6.9 to 15.5 | 0.7812 | 1 | 29 |
| draws 2 and 3, D98's subset | 3 | 3.4 | -3.4 to 12.1 | 0.75 | 1 | 29 |

## Refusal rate (out of scope, %, Rule 2 interval)

No paired test of refusal: S472 computes none on draw 1, so none is computed here.

| view | full pipeline | no analyser | routing fix |
|---|---|---|---|
| draw 1, all questions | 5.1 (0.0 to 12.8) | 94.9 (87.2 to 100.0) | 97.4 (92.3 to 100.0) |
| draw 1, D98's subset | 7.7 (0.0 to 23.1) | 100.0 (100.0 to 100.0) | 92.3 (76.9 to 100.0) |
| draw 2, D98's subset | 0.0 (0.0 to 0.0) | 92.3 (76.9 to 100.0) | 100.0 (100.0 to 100.0) |
| draw 3, D98's subset | 7.7 (0.0 to 23.1) | 92.3 (76.9 to 100.0) | 92.3 (76.9 to 100.0) |
| draws 2 and 3, D98's subset | 3.8 (0.0 to 11.5) | 92.3 (80.8 to 100.0) | 96.2 (88.5 to 100.0) |

Reproduced first: draw 1 equal to KNOWN (refused 2, 37, 38 of 39; passed at 4 65, 60 of 86), to S480.count and the committed S480 recount (inputs sha256 equal), its draw_counts on draws 1 to 3, and Figure 5's Source Data (Fig. 5a and 5b setup rows, comparison and Holm P included)
