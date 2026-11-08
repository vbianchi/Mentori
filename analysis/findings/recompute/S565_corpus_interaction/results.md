# S565, D213 (2): strategy by corpus size

G4 draw 1, final key; pass at score 4 primary, 3 secondary. Interaction = change in log odds of passing against single pass per doubling of core papers (two strategies per model, S11's form, plus distractor level). Interval: two-sided 95% percentile, cluster bootstrap of questions.

## Reproduced first

- Supplementary Figure 9 was drawn from the grid_pairs.jsonl read here (sha256 82a5c4ddf3b6)
- (1) all in scope: 48 values (n pairs, n questions, pass rate; single pass and RLM-10; 4 sizes; score 4 and 3) equal Supplementary Fig. 9b and 9c
- (2) the 22: 8 rates equal Figure 3e's Source Data block 'The same 22' (score 4) and 16 equal q66_tables.json pooled_over_ratios (score 4 and 3); Supplementary Figure 9's Source Data holds no 22-question rows
- (3) RLM-10 minus single pass, score 4, all in scope: 20 core papers -8.1395, 50 core papers -12.4031 points, equal to Figure 3e and Supplementary Fig. 9a
- (3) the letter's values: 20 core papers letter -6.2, final key -8.1, key v2.4 anchor -6.2; 50 core papers letter -13.6, final key -12.4, key v2.4 anchor -13.6

## Interaction (primary first)

| set | score | strategy | n rows | n questions | estimate | OR per doubling | bootstrap 95% (D213) | Wald 95% (not D213's method) | Wald P (not D213's method) | refits ok | singular |
|---|---|---|---|---|---|---|---|---|---|---|---|
| same22 | 4 | rlm_10 | 528 | 22 | -0.070 | 0.933 | [-0.454, +0.384] | [-0.433, +0.294] | 0.7071 | 10000 of 10000 | 0 |
| same22 | 4 | multi_hop | 528 | 22 | +0.176 | 1.192 | [-0.485, +0.799] | [-0.372, +0.724] | 0.5294 | 9999 of 10000 | 0 |
| same22 | 4 | rlm_20 | 528 | 22 | +0.071 | 1.074 | [-0.255, +0.447] | [-0.300, +0.442] | 0.7077 | 10000 of 10000 | 0 |
| same22 | 4 | rlm_5 | 528 | 22 | +0.176 | 1.193 | [-0.188, +0.648] | [-0.186, +0.539] | 0.3406 | 10000 of 10000 | 0 |
| same22 | 4 | verified_pass | 528 | 22 | +0.283 | 1.328 | [-0.714, +2.277] | [-0.375, +0.941] | 0.3985 | 9999 of 10000 | 0 |
| all_in_scope | 4 | rlm_10 | 1428 | 86 | -0.135 | 0.874 | [-0.547, +0.383] | [-0.406, +0.136] | 0.3281 | 10000 of 10000 | 0 |
| all_in_scope | 4 | multi_hop | 1428 | 86 | +0.055 | 1.057 | [-0.493, +0.837] | [-0.343, +0.453] | 0.7866 | 10000 of 10000 | 0 |
| all_in_scope | 4 | rlm_20 | 1428 | 86 | -0.046 | 0.956 | [-0.444, +0.443] | [-0.316, +0.225] | 0.7419 | 10000 of 10000 | 0 |
| all_in_scope | 4 | rlm_5 | 1428 | 86 | -0.048 | 0.954 | [-0.478, +0.482] | [-0.312, +0.217] | 0.7246 | 10000 of 10000 | 0 |
| all_in_scope | 4 | verified_pass | 1428 | 86 | +0.095 | 1.100 | [-0.833, +1.203] | [-0.365, +0.555] | 0.6856 | 10000 of 10000 | 0 |
| same22 | 3 | rlm_10 | 528 | 22 | +0.562 | 1.754 | [-0.047, +20.194] | [-0.167, +1.291] | 0.1308 | 10000 of 10000 | 7 |
| same22 | 3 | multi_hop | 528 | 22 | +0.518 | 1.678 | [-4.024, +7.464] | [-0.562, +1.598] | 0.3472 | 9602 of 10000 | 0 |
| same22 | 3 | rlm_20 | 528 | 22 | -0.336 | 0.715 | [-0.993, +0.278] | [-0.987, +0.316] | 0.3130 | 10000 of 10000 | 73 |
| same22 | 3 | rlm_5 | 528 | 22 | -0.145 | 0.865 | [-0.567, +0.388] | [-0.691, +0.402] | 0.6034 | 10000 of 10000 | 0 |
| same22 | 3 | verified_pass | 528 | 22 | +1.199 | 3.316 | [-0.182, +2.021] | [-3.455, +5.852] | 0.6136 | 9613 of 10000 | 0 |
| all_in_scope | 3 | rlm_10 | 1428 | 86 | -0.004 | 0.996 | [-0.754, +0.954] | [-0.474, +0.467] | 0.9873 | 10000 of 10000 | 0 |
| all_in_scope | 3 | multi_hop | 1428 | 86 | +0.019 | 1.019 | [-1.013, +1.670] | [-0.583, +0.622] | 0.9504 | 10000 of 10000 | 0 |
| all_in_scope | 3 | rlm_20 | 1428 | 86 | -0.373 | 0.688 | [-0.916, +0.400] | [-0.818, +0.071] | 0.0999 | 10000 of 10000 | 0 |
| all_in_scope | 3 | rlm_5 | 1428 | 86 | -0.119 | 0.888 | [-0.698, +0.607] | [-0.529, +0.291] | 0.5687 | 10000 of 10000 | 0 |
| all_in_scope | 3 | verified_pass | 1428 | 86 | +1.015 | 2.759 | [-0.571, +2.222] | [+0.143, +1.887] | 0.0226 | 10000 of 10000 | 0 |

## Companion: RLM-10 minus single pass, 50 minus 20 core papers, the 86 questions

| score | d at 20 (95%) | d at 50 (95%) | gap 50 minus 20 | 95% |
|---|---|---|---|---|
| score 4 | -8.1 [-16.3, +0.4] | -12.4 [-22.5, -2.3] | -4.3 | [-10.9, +2.3] |
| score 3 | +2.3 [-3.9, +9.3] | +1.6 [-4.3, +8.1] | -0.8 | [-5.8, +3.9] |

Runtime: 45604 s in all, 45603 s in R.
