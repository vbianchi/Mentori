# G20 reading (D260): qwen3-coder:30b, draw 1, the 46 questions of D239 amended (G19's design)

Written by `uv run --frozen python scripts/S595_g20_reading.py --runs-root /Users/valeriobianchi/s3_inputs/g20 --r-t2 /Users/valeriobianchi/s3_inputs/t2lqcoder_20261104T070834Z/runs/exp_01__rlm_10__exp_v4_s20_n0+qwen3-coder-30b --r-t2x /Users/valeriobianchi/s3_inputs/g20/r_t2x/exp_01__rlm_10__exp_v4_s20_n0+qwen3-coder-30b --manifest /Users/valeriobianchi/s3_inputs/g20/g20_stored_R.json --judge /Users/valeriobianchi/s3_inputs/g20/out_s6_w_g20 --r-collect-t2x /Users/valeriobianchi/s3_inputs/g20/t2xqcoder_collect.jsonl` at 2026-11-06T17:39:36Z (HEAD 6d755e05; code dependencies changed from HEAD: none). One draw, descriptive: no hypothesis is held or not held here, and no P value is computed (D260: a replication on another generator, not a test). R ran at T2's code (the T2 qwen3-coder clone, 73c326a6) and T2X's PIN, A, B and C at G20's PIN, so B and C differ from R in code as well as in their switch (G20_runs/README.md).

## Reproduced first

- S518.read_rows, merge and analyse on the T2 collect = qwen3-coder.json's stored result (D_one, D_many, I, intervals, P), exactly (findings/recompute/S518_split_confirmation/qwen3-coder.json).
- R's T2 cells equal S518.read_rows' for 29 keys; R's T2X cells equal S518.t2x_cells' for 17 keys.
- The answer judged is the answer read for 184 answers (S512 item_sha256).
- Concept recall (S577): exp_01 path 86 of 86 equal L3_d181; package path 86 of 86 equal L2_d181. S518 and T2X stored no concept recall for R.

## By arm and question type

Pass at 4 and 3: share of answers scoring at least 4 (3), failed answers as fails, unscored left out. Concept recall: mean, failed answers 0. Other cells: median [quartile 25, quartile 75] over answers (S571's definitions; papers for R, B, C are those among the passages returned to the code, an upper bound; for A those matched in a successful sub-call's prompt).

| Arm | Type | Answers | Pass at 4 | Pass at 3 | Concept recall | Sub-calls | With paper text | Papers | Every key paper | Root turns | Words | Model calls | Tokens | Wall s | Failed | Unscored |
|---|---|---:|---:|---:|---:|---|---|---|---|---|---|---|---|---|---:|---:|
| R Mentori RLM-10 (stored, qwen3-coder:30b) | one-paper | 20 | 95.0% | 95.0% | 0.766 | 4 [3, 4] | 3 [2, 4] | 1 [1, 2] | 20/20 | 2 [2, 7] | 879 [576, 1117] | 8 [6, 11] | 39366 [24615, 70080] | 4420 [1954, 7326] | 0 | 0 |
| R Mentori RLM-10 (stored, qwen3-coder:30b) | many-paper | 26 | 50.0% | 88.5% | 0.554 | 4 [3, 7] | 4 [2, 6] | 3 [2, 4] | 21/26 | 2 [2, 6] | 1123 [826, 1665] | 10 [7, 12] | 61680 [45231, 85159] | 745 [571, 1397] | 0 | 0 |
| R Mentori RLM-10 (stored, qwen3-coder:30b) | all | 46 | 69.6% | 91.3% | 0.646 | 4 [3, 5] | 3 [2, 4] | 2 [1, 4] | 41/46 | 2 [2, 6] | 1014 [738, 1351] | 9 [6, 12] | 50932 [30682, 76088] | 1581 [671, 4077] | 0 | 0 |
| A package RLM | one-paper | 20 | 5.0% | 25.0% | 0.033 | 0 [0, 2] | 0 [0, 0] | 0 [0, 0] | 5/20 | 2 [1, 2] | 91 [38, 171] | 2 [2, 7] | 21170 [7303, 64942] | 104 [34, 225] | 3 | 0 |
| A package RLM | many-paper | 26 | 0.0% | 53.8% | 0.196 | 2 [0, 6] | 0 [0, 0] | 0 [0, 0] | 1/26 | 2 [1, 2] | 216 [131, 312] | 6 [2, 9] | 14854 [8000, 96962] | 122 [81, 401] | 4 | 0 |
| A package RLM | all | 46 | 2.2% | 41.3% | 0.125 | 0 [0, 5] | 0 [0, 0] | 0 [0, 0] | 6/46 | 2 [1, 2] | 174 [57, 258] | 6 [2, 9] | 17335 [7765, 96962] | 110 [70, 337] | 7 | 0 |
| B search off | one-paper | 20 | 65.0% | 70.0% | 0.581 | 3 [3, 4] | 3 [1, 4] | 1 [1, 4] | 20/20 | 2 [2, 9] | 634 [198, 1046] | 9 [7, 10] | 48346 [29644, 80136] | 153 [119, 211] | 2 | 0 |
| B search off | many-paper | 26 | 46.2% | 84.6% | 0.541 | 6 [4, 9] | 5 [4, 6] | 3 [2, 4] | 19/26 | 2 [1, 2] | 1568 [1115, 2203] | 10 [8, 13] | 64840 [52458, 132779] | 227 [162, 343] | 0 | 0 |
| B search off | all | 46 | 54.3% | 78.3% | 0.558 | 4 [3, 7] | 4 [3, 6] | 2 [1, 4] | 39/46 | 2 [1, 3] | 1152 [686, 1738] | 10 [7, 12] | 57420 [38202, 127111] | 181 [140, 334] | 2 | 0 |
| C gate off | one-paper | 20 | 75.0% | 85.0% | 0.538 | 2 [1, 2] | 2 [1, 2] | 1 [1, 1] | 19/20 | 2 [1, 6] | 409 [274, 582] | 6 [3, 8] | 22553 [7169, 41084] | 87 [39, 191] | 0 | 0 |
| C gate off | many-paper | 26 | 34.6% | 80.8% | 0.468 | 4 [3, 7] | 4 [1, 6] | 3 [2, 4] | 19/26 | 2 [1, 6] | 880 [545, 1555] | 8 [6, 12] | 49062 [27913, 89937] | 287 [203, 426] | 0 | 0 |
| C gate off | all | 46 | 52.2% | 82.6% | 0.498 | 3 [2, 5] | 2 [1, 4] | 2 [1, 4] | 38/46 | 2 [1, 6] | 590 [349, 918] | 7 [5, 10] | 35486 [14257, 62025] | 209 [89, 303] | 0 | 0 |

Stop reasons (all answers; failed answers in brackets):

- R Mentori RLM-10 (stored, qwen3-coder:30b): final 43, final_after_max_rejections 1, max_turns_partial 2 (none failed); gate rejected at least once 24; under 3 sub-calls 3
- A package RLM: answer_ready 39, root_call_failed 7 (root_call_failed 7); forced final 0, retried attempts 0; under 3 sub-calls 29
- B search off: final 39, max_turns_auto_generated 1, max_turns_empty 2, max_turns_partial 4 (max_turns_empty 2); gate rejected at least once 24; refused search attempts 0 in 0 answers; under 3 sub-calls 6
- C gate off: final 46 (none failed); gate rejected at least once 0; under 3 sub-calls 20

## Paired contrasts, a minus b per question (read as O1)

Per question one value per arm by O1's rule (a failed answer passes nothing and scores concept recall 0; an unscored judge cell counts as not passing). Pass at 4 in points, concept recall as a share; mean difference with Rule 2's 95% percentile interval (S576_d249.diff_interval: 10,000 question resamples, seed 20261013), descriptive; questions where a or b is higher.

| a | b | Type | Metric | n | Mean a | Mean b | a - b | 95% interval | a higher | b higher |
|---|---|---|---|---:|---:|---:|---:|---|---:|---:|
| A | R | one-paper | pass4 | 20 | 5.0 | 95.0 | -90.0 | -100.0 to -75.0 | 0 | 18 |
| A | R | one-paper | cr | 20 | 0.033 | 0.766 | -0.733 | -0.845 to -0.607 | 0 | 19 |
| A | R | many-paper | pass4 | 26 | 0.0 | 50.0 | -50.0 | -69.2 to -30.8 | 0 | 13 |
| A | R | many-paper | cr | 26 | 0.196 | 0.554 | -0.358 | -0.491 to -0.223 | 2 | 20 |
| A | R | all | pass4 | 46 | 2.2 | 69.6 | -67.4 | -80.4 to -54.3 | 0 | 31 |
| A | R | all | cr | 46 | 0.125 | 0.646 | -0.521 | -0.625 to -0.414 | 2 | 39 |
| B | R | one-paper | pass4 | 20 | 65.0 | 95.0 | -30.0 | -55.0 to -5.0 | 1 | 7 |
| B | R | one-paper | cr | 20 | 0.581 | 0.766 | -0.186 | -0.413 to 0.038 | 6 | 8 |
| B | R | many-paper | pass4 | 26 | 46.2 | 50.0 | -3.8 | -26.9 to 19.3 | 5 | 6 |
| B | R | many-paper | cr | 26 | 0.541 | 0.554 | -0.013 | -0.148 to 0.122 | 8 | 9 |
| B | R | all | pass4 | 46 | 54.3 | 69.6 | -15.2 | -32.6 to 2.2 | 6 | 13 |
| B | R | all | cr | 46 | 0.558 | 0.646 | -0.088 | -0.216 to 0.035 | 14 | 17 |
| C | R | one-paper | pass4 | 20 | 75.0 | 95.0 | -20.0 | -40.0 to -5.0 | 0 | 4 |
| C | R | one-paper | cr | 20 | 0.538 | 0.766 | -0.229 | -0.389 to -0.090 | 1 | 10 |
| C | R | many-paper | pass4 | 26 | 34.6 | 50.0 | -15.4 | -34.6 to 3.8 | 2 | 6 |
| C | R | many-paper | cr | 26 | 0.468 | 0.554 | -0.086 | -0.213 to 0.040 | 5 | 8 |
| C | R | all | pass4 | 46 | 52.2 | 69.6 | -17.4 | -32.6 to -4.3 | 2 | 10 |
| C | R | all | cr | 46 | 0.498 | 0.646 | -0.148 | -0.249 to -0.053 | 6 | 18 |
| B | A | one-paper | pass4 | 20 | 65.0 | 5.0 | 60.0 | 35.0 to 85.0 | 13 | 1 |
| B | A | one-paper | cr | 20 | 0.581 | 0.033 | 0.547 | 0.344 to 0.735 | 14 | 1 |
| B | A | many-paper | pass4 | 26 | 46.2 | 0.0 | 46.2 | 26.9 to 65.4 | 12 | 0 |
| B | A | many-paper | cr | 26 | 0.541 | 0.196 | 0.345 | 0.224 to 0.464 | 19 | 2 |
| B | A | all | pass4 | 46 | 54.3 | 2.2 | 52.2 | 37.0 to 67.4 | 25 | 1 |
| B | A | all | cr | 46 | 0.558 | 0.125 | 0.433 | 0.319 to 0.542 | 33 | 3 |
| C | A | one-paper | pass4 | 20 | 75.0 | 5.0 | 70.0 | 50.0 to 90.0 | 14 | 0 |
| C | A | one-paper | cr | 20 | 0.538 | 0.033 | 0.504 | 0.352 to 0.658 | 16 | 0 |
| C | A | many-paper | pass4 | 26 | 34.6 | 0.0 | 34.6 | 15.4 to 53.8 | 9 | 0 |
| C | A | many-paper | cr | 26 | 0.468 | 0.196 | 0.272 | 0.165 to 0.380 | 18 | 3 |
| C | A | all | pass4 | 46 | 52.2 | 2.2 | 50.0 | 34.8 to 65.2 | 23 | 0 |
| C | A | all | cr | 46 | 0.498 | 0.125 | 0.373 | 0.280 to 0.470 | 34 | 3 |

## D249's hypotheses, read on one draw

As D249 states them (package = A, control = R, search off = B, gate off = C), read descriptively: whether the difference has the direction D249 states, or whether the interval contains 0 where D249 states that. Not a test (D249 O2).

- **H1** (D249): package minus control on concept recall below 0.
- **H2** (D249): search off minus control on concept recall below 0, and search off minus package on concept recall with an interval containing 0.
- **H3** (D249): gate off minus control on concept recall below 0.
- **H4** (D249): for B and for C, (control minus arm) on one-paper questions minus (control minus arm) on many-paper questions above 0, on concept recall.
- **H5** (D249): search off minus control and gate off minus control on pass at 4 below 0; package minus control on pass at 4 with an interval containing 0.

Computed by O1's reader, S576_d249.evaluate(verdict=False), on the draw-1 values.

| Hypothesis | Part | Contrast | Value | 95% interval | Stated | Reading |
|---|---|---|---:|---|---|---|
| H1 | H1 | A package RLM minus R Mentori RLM-10 (stored, qwen3-coder:30b), concept recall, all 46 | -0.521 | -0.625 to -0.414 | below 0 | direction as H1 |
| H2 | H2a | B search off minus R Mentori RLM-10 (stored, qwen3-coder:30b), concept recall, all 46 | -0.088 | -0.216 to 0.035 | below 0 | direction as H2 |
| H2 | H2b | B search off minus A package RLM, concept recall, all 46 | 0.433 | 0.319 to 0.542 | contains 0 | interval excludes 0, not as H2 states |
| H3 | H3 | C gate off minus R Mentori RLM-10 (stored, qwen3-coder:30b), concept recall, all 46 | -0.148 | -0.249 to -0.053 | below 0 | direction as H3 |
| H4 | H4 B | (R minus B) on one-paper minus (R minus B) on many-paper, concept recall | 0.172 | -0.090 to 0.441 | above 0 | direction as H4 |
| H4 | H4 C | (R minus C) on one-paper minus (R minus C) on many-paper, concept recall | 0.142 | -0.052 to 0.348 | above 0 | direction as H4 |
| H5 | H5a | B search off minus R Mentori RLM-10 (stored, qwen3-coder:30b), pass at 4 (points), all 46 | -15.2 | -32.6 to 2.2 | below 0 | direction as H5 |
| H5 | H5b | C gate off minus R Mentori RLM-10 (stored, qwen3-coder:30b), pass at 4 (points), all 46 | -17.4 | -32.6 to -4.3 | below 0 | direction as H5 |
| H5 | H5c | A package RLM minus R Mentori RLM-10 (stored, qwen3-coder:30b), pass at 4 (points), all 46 | -67.4 | -80.4 to -54.3 | contains 0 | interval excludes 0, not as H5 states |
