# S596, windowed BERTScore against the judge (Figure 5 e form)

Written by `uv run --frozen python scripts/S596_windowed_bertscore.py run` at 2026-11-06T09:55:45Z, git f3ccbde8, script b25cb9fdc4ca. rulings page 6 Nov, RUN-BERTSCORE: O1.

Answers: 516 draw-1 answerable (Figure 5 e's table); scored 514, no answer 2. L1 had scored 164: 350 over the 512-token limit, 2 no answer. Here 324 answers and 26 of 86 keys span more than one window; longest answer 6,953 word pieces, 27 windows.

| row | judge signal | rho | 95% interval | resample quartiles | within-question rho | answers | questions |
|---|---|---|---|---|---|---|---|
| BERTScore (windowed) | Judge correctness | 0.58 | 0.48 to 0.66 | 0.55, 0.58, 0.61 | 0.39 | 514 | 86 |
| BERTScore (windowed) | Judge faithfulness | 0.37 | 0.25 to 0.48 | 0.33, 0.37, 0.41 | 0.35 | 511 | 86 |
| BERTScore, answers that fit 512 only | Judge correctness | 0.47 | 0.32 to 0.61 | 0.42, 0.48, 0.52 | 0.37 | 164 | 58 |
| BERTScore, answers that fit 512 only | Judge faithfulness | 0.23 | 0.07 to 0.38 | 0.18, 0.24, 0.29 | 0.29 | 164 | 58 |

Gates:
- G1: S540.evaluator_rows on S497's table equals all 20 drawn Fig. 5e records of findings/figures_provisional/fig5/figure5_numbers.json at HEAD (2 held there, D195, not compared)
- G2: all 516 answers' sha256 equal L1's overlap rows; every word-piece count equals L1's
- G3: on the 164 answers L1 scored (answer and key within 512), the windowed F1 equals L1's BERTScore F1, largest difference 8.9e-07 (tolerance 0.0001)
