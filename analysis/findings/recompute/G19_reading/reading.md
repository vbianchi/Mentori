# G19 reading (D249 O2): gemma3:27b, draw 1, the 46 questions of D239 amended

Written by `uv run --frozen python scripts/S578_g19_reading.py --runs-root /Users/valeriobianchi/s3_inputs/g19 --r-t2 /Users/valeriobianchi/s3_inputs/t2lgemma_20261104T070719Z/runs/exp_01__rlm_10__exp_v4_s20_n0+gemma3-27b --r-t2x /Users/valeriobianchi/s3_inputs/g19/r_t2x/exp_01__rlm_10__exp_v4_s20_n0+gemma3-27b --manifest /Users/valeriobianchi/s3_inputs/g19/g19_stored_R.json --judge /Users/valeriobianchi/s3_inputs/g19/out_s6_w_g19 --r-collect-t2x /Users/valeriobianchi/s3_inputs/g19/t2xgemma_collect.jsonl` at 2026-11-06T07:30:08Z (HEAD 1ca32046; code dependencies changed from HEAD: scripts/S578_g19_reading.py). One draw, descriptive: no hypothesis is held or not held here, and no P value is computed (D249 O2: a replication on another generator, not a test). R ran at T2's code (99bbc951), A, B and C at G19's PIN, so B and C differ from R in code as well as in their switch (G19_runs/README.md R1).

## Reproduced first

- S518.read_rows, merge and analyse on the T2 collect = gemma3.json's stored result (D_one, D_many, I, intervals, P), exactly (findings/recompute/S518_split_confirmation/gemma3.json).
- R's T2 cells equal S518.read_rows' for 29 keys; R's T2X cells equal S518.t2x_cells' for 17 keys.
- The answer judged is the answer read for 184 answers (S512 item_sha256).
- Concept recall (S577): exp_01 path 86 of 86 equal L3_d181; package path 86 of 86 equal L2_d181. S518 and T2X stored no concept recall for R.

## By arm and question type

Pass at 4 and 3: share of answers scoring at least 4 (3), failed answers as fails, unscored left out. Concept recall: mean, failed answers 0. Other cells: median [quartile 25, quartile 75] over answers (S571's definitions; papers for R, B, C are those among the passages returned to the code, an upper bound; for A those matched in a successful sub-call's prompt).

| Arm | Type | Answers | Pass at 4 | Pass at 3 | Concept recall | Sub-calls | With paper text | Papers | Every key paper | Root turns | Words | Model calls | Tokens | Wall s | Failed | Unscored |
|---|---|---:|---:|---:|---:|---|---|---|---|---|---|---|---|---|---:|---:|
| R Mentori RLM-10 (stored) | one-paper | 20 | 100.0% | 100.0% | 0.822 | 3 [3, 3] | 3 [3, 3] | 1 [1, 1] | 20/20 | 9 [8, 10] | 620 [542, 801] | 12 [11, 13] | 47774 [42038, 49482] | 3750 [2932, 5056] | 0 | 0 |
| R Mentori RLM-10 (stored) | many-paper | 26 | 53.8% | 92.3% | 0.562 | 3 [3, 4] | 3 [3, 4] | 3 [2, 4] | 20/26 | 6 [5, 8] | 1124 [893, 1379] | 10 [9, 12] | 46256 [32992, 59828] | 834 [660, 1203] | 0 | 0 |
| R Mentori RLM-10 (stored) | all | 46 | 73.9% | 95.7% | 0.675 | 3 [3, 4] | 3 [3, 3] | 2 [1, 3] | 40/46 | 8 [5, 10] | 864 [657, 1150] | 11 [10, 12] | 47512 [39473, 54094] | 2000 [814, 3575] | 0 | 0 |
| A package RLM | one-paper | 20 | 10.0% | 10.0% | 0.059 | 2 [1, 2] | 0 [0, 0] | 0 [0, 0] | 1/20 | 6 [4, 8] | 36 [28, 82] | 7 [4, 11] | 40324 [23202, 68008] | 100 [54, 144] | 0 | 0 |
| A package RLM | many-paper | 26 | 0.0% | 30.8% | 0.064 | 4 [1, 5] | 0 [0, 2] | 0 [0, 2] | 4/26 | 8 [6, 10] | 72 [40, 143] | 12 [10, 15] | 82687 [50455, 104150] | 175 [111, 270] | 0 | 0 |
| A package RLM | all | 46 | 4.3% | 21.7% | 0.062 | 2 [1, 4] | 0 [0, 1] | 0 [0, 1] | 5/46 | 8 [4, 10] | 48 [32, 111] | 10 [6, 14] | 60912 [29637, 95527] | 142 [88, 197] | 0 | 0 |
| B search off | one-paper | 20 | 75.0% | 95.0% | 0.764 | 3 [3, 3] | 3 [3, 3] | 1 [1, 2] | 19/20 | 9 [8, 10] | 722 [524, 954] | 12 [11, 13] | 52300 [46049, 59088] | 1130 [1034, 1213] | 0 | 0 |
| B search off | many-paper | 26 | 46.2% | 92.3% | 0.533 | 3 [3, 4] | 3 [3, 4] | 2 [2, 3] | 19/26 | 6 [5, 8] | 1275 [1040, 1797] | 11 [9, 12] | 49872 [38234, 97874] | 1705 [1327, 1959] | 0 | 0 |
| B search off | all | 46 | 58.7% | 93.5% | 0.633 | 3 [3, 4] | 3 [3, 4] | 2 [1, 3] | 38/46 | 8 [6, 9] | 1044 [675, 1322] | 11 [10, 13] | 52006 [40838, 71935] | 1335 [1045, 1798] | 0 | 0 |
| C gate off | one-paper | 20 | 95.0% | 95.0% | 0.636 | 1 [1, 1] | 1 [1, 1] | 1 [1, 1] | 20/20 | 4 [4, 5] | 253 [161, 308] | 5 [5, 6] | 17380 [14045, 21948] | 354 [296, 426] | 0 | 0 |
| C gate off | many-paper | 26 | 42.3% | 84.6% | 0.498 | 3 [2, 4] | 3 [2, 4] | 2 [2, 4] | 22/26 | 5 [4, 5] | 1000 [698, 1249] | 8 [6, 9] | 36562 [26854, 45445] | 579 [372, 892] | 0 | 0 |
| C gate off | all | 46 | 65.2% | 89.1% | 0.558 | 2 [1, 3] | 2 [1, 3] | 2 [1, 3] | 42/46 | 5 [4, 5] | 532 [271, 1058] | 6 [5, 8] | 24886 [17997, 38846] | 426 [317, 588] | 0 | 0 |

Stop reasons (all answers; failed answers in brackets):

- R Mentori RLM-10 (stored): final 41, final_after_max_rejections 1, max_turns_partial 4 (none failed); gate rejected at least once 32; under 3 sub-calls 5
- A package RLM: answer_ready 46 (none failed); forced final 0, retried attempts 0; under 3 sub-calls 28
- B search off: final 44, final_after_max_rejections 2 (none failed); gate rejected at least once 31; refused search attempts 0 in 0 answers; under 3 sub-calls 2
- C gate off: final 46 (none failed); gate rejected at least once 0; under 3 sub-calls 30

## Paired contrasts, a minus b per question (read as O1)

Per question one value per arm by O1's rule (a failed answer passes nothing and scores concept recall 0; an unscored judge cell counts as not passing). Pass at 4 in points, concept recall as a share; mean difference with Rule 2's 95% percentile interval (S576_d249.diff_interval: 10,000 question resamples, seed 20261013), descriptive; questions where a or b is higher.

| a | b | Type | Metric | n | Mean a | Mean b | a - b | 95% interval | a higher | b higher |
|---|---|---|---|---:|---:|---:|---:|---|---:|---:|
| A | R | one-paper | pass4 | 20 | 10.0 | 100.0 | -90.0 | -100.0 to -75.0 | 0 | 18 |
| A | R | one-paper | cr | 20 | 0.059 | 0.822 | -0.763 | -0.883 to -0.639 | 0 | 20 |
| A | R | many-paper | pass4 | 26 | 0.0 | 53.8 | -53.8 | -73.1 to -34.6 | 0 | 14 |
| A | R | many-paper | cr | 26 | 0.064 | 0.562 | -0.499 | -0.598 to -0.389 | 1 | 25 |
| A | R | all | pass4 | 46 | 4.3 | 73.9 | -69.6 | -82.6 to -56.5 | 0 | 32 |
| A | R | all | cr | 46 | 0.062 | 0.675 | -0.614 | -0.700 to -0.525 | 1 | 45 |
| B | R | one-paper | pass4 | 20 | 75.0 | 100.0 | -25.0 | -45.0 to -5.0 | 0 | 5 |
| B | R | one-paper | cr | 20 | 0.764 | 0.822 | -0.058 | -0.190 to 0.048 | 4 | 6 |
| B | R | many-paper | pass4 | 26 | 46.2 | 53.8 | -7.7 | -30.8 to 15.4 | 4 | 6 |
| B | R | many-paper | cr | 26 | 0.533 | 0.562 | -0.029 | -0.118 to 0.058 | 8 | 8 |
| B | R | all | pass4 | 46 | 58.7 | 73.9 | -15.2 | -30.4 to 0.0 | 4 | 11 |
| B | R | all | cr | 46 | 0.633 | 0.675 | -0.042 | -0.117 to 0.026 | 12 | 14 |
| C | R | one-paper | pass4 | 20 | 95.0 | 100.0 | -5.0 | -15.0 to 0.0 | 0 | 1 |
| C | R | one-paper | cr | 20 | 0.636 | 0.822 | -0.186 | -0.325 to -0.068 | 1 | 9 |
| C | R | many-paper | pass4 | 26 | 42.3 | 53.8 | -11.5 | -30.8 to 7.7 | 2 | 5 |
| C | R | many-paper | cr | 26 | 0.498 | 0.562 | -0.065 | -0.149 to 0.015 | 4 | 12 |
| C | R | all | pass4 | 46 | 65.2 | 73.9 | -8.7 | -19.6 to 2.2 | 2 | 6 |
| C | R | all | cr | 46 | 0.558 | 0.675 | -0.117 | -0.193 to -0.046 | 5 | 21 |
| B | A | one-paper | pass4 | 20 | 75.0 | 10.0 | 65.0 | 45.0 to 85.0 | 13 | 0 |
| B | A | one-paper | cr | 20 | 0.764 | 0.059 | 0.705 | 0.577 to 0.825 | 19 | 0 |
| B | A | many-paper | pass4 | 26 | 46.2 | 0.0 | 46.2 | 26.9 to 65.4 | 12 | 0 |
| B | A | many-paper | cr | 26 | 0.533 | 0.064 | 0.469 | 0.346 to 0.585 | 24 | 2 |
| B | A | all | pass4 | 46 | 58.7 | 4.3 | 54.3 | 39.1 to 69.6 | 25 | 0 |
| B | A | all | cr | 46 | 0.633 | 0.062 | 0.572 | 0.478 to 0.662 | 43 | 2 |
| C | A | one-paper | pass4 | 20 | 95.0 | 10.0 | 85.0 | 70.0 to 100.0 | 17 | 0 |
| C | A | one-paper | cr | 20 | 0.636 | 0.059 | 0.577 | 0.431 to 0.725 | 19 | 0 |
| C | A | many-paper | pass4 | 26 | 42.3 | 0.0 | 42.3 | 23.1 to 61.5 | 11 | 0 |
| C | A | many-paper | cr | 26 | 0.498 | 0.064 | 0.434 | 0.310 to 0.551 | 23 | 1 |
| C | A | all | pass4 | 46 | 65.2 | 4.3 | 60.9 | 45.7 to 73.9 | 28 | 0 |
| C | A | all | cr | 46 | 0.558 | 0.062 | 0.496 | 0.400 to 0.592 | 42 | 1 |

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
| H1 | H1 | A package RLM minus R Mentori RLM-10 (stored), concept recall, all 46 | -0.614 | -0.700 to -0.525 | below 0 | direction as H1 |
| H2 | H2a | B search off minus R Mentori RLM-10 (stored), concept recall, all 46 | -0.042 | -0.117 to 0.026 | below 0 | direction as H2 |
| H2 | H2b | B search off minus A package RLM, concept recall, all 46 | 0.572 | 0.478 to 0.662 | contains 0 | interval excludes 0, not as H2 states |
| H3 | H3 | C gate off minus R Mentori RLM-10 (stored), concept recall, all 46 | -0.117 | -0.193 to -0.046 | below 0 | direction as H3 |
| H4 | H4 B | (R minus B) on one-paper minus (R minus B) on many-paper, concept recall | 0.028 | -0.114 to 0.191 | above 0 | direction as H4 |
| H4 | H4 C | (R minus C) on one-paper minus (R minus C) on many-paper, concept recall | 0.121 | -0.023 to 0.279 | above 0 | direction as H4 |
| H5 | H5a | B search off minus R Mentori RLM-10 (stored), pass at 4 (points), all 46 | -15.2 | -30.4 to 0.0 | below 0 | direction as H5 |
| H5 | H5b | C gate off minus R Mentori RLM-10 (stored), pass at 4 (points), all 46 | -8.7 | -19.6 to 2.2 | below 0 | direction as H5 |
| H5 | H5c | A package RLM minus R Mentori RLM-10 (stored), pass at 4 (points), all 46 | -69.6 | -82.6 to -56.5 | contains 0 | interval excludes 0, not as H5 states |
