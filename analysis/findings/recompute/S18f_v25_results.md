# S18f results: devstral-small-2:24b on key v2.5, S512's call (2026-11-05 08:38)

61 questions, 366 answers per arm (S18's frozen set less D7 ['CD_015'], less key v2.5's drops none). Rows: 8 files, run_sha256 cf05e84cf800.
This analysis code reproduces S18e_results.json from S18e's ledger: 366 answers; contrasts True, shares True, noise rule True, B/B2 True; C vs D 44.26 [36.34, 52.46].
Noise floor within 3 points: True. B and B2 identical on all four dimensions: 366 of 366.

| arm | counted | 5/5 faithfulness | max prompt tokens | S18e (v2.4) |
|---|---|---|---|---|
| B | 366 of 366 | 40.44% | 11850 | 41.26% |
| C | 366 of 366 | 54.92% | 36393 | 54.92% |
| D | 366 of 366 | 10.66% | 36294 | 10.66% |
| B2 | 366 of 366 | 40.44% | 11850 | 41.26% |

| contrast | n | 5/5 x | 5/5 y | difference, points | 95% CI | TOST equivalent at 5 |
|---|---|---|---|---|---|---|
| B vs B2 (noise floor: identical inputs, two runs) | 366 | 40.44% | 40.44% | 0.0 | [0.0, 0.0] | True |
| C vs B (evidence effect, total) | 366 | 54.92% | 40.44% | 14.48 | [7.65, 20.77] | False |
| D vs B (irrelevant-text effect: same bulk, wrong paper) | 366 | 10.66% | 40.44% | -29.78 | [-36.61, -23.5] | False |
| C vs D (PRIMARY: evidence content effect) | 366 | 54.92% | 10.66% | 44.26 | [36.07, 52.73] | False |

Full statistics: findings/recompute/S18f_v25_results.json.
