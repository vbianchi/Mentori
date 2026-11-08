# Supplementary Figure 18, notes for the Methods

Written by `scripts/S542_supp_evaluators.py figure`.

- Ranks in b are draw 1 on 75 questions, so they can differ from Figure 6b, which uses three draws.
- The Concepts and Papers rows meet the letter's promise of a comparison with "our three signals" (Reviewer 1, Comment 1.2).
- The 60 false-premise answers are out of both panels (FF27 a).
- FF27 a names no statistic for the order column; Spearman's rho is one of the two the letter's method uses.
- The BERTScore row in a is S596's windowed F1 (findings/recompute/S596_windowed_bertscore, 510-piece windows at stride 255, roberta-large); D274 places it here and leaves Figure 6e as D200 drew it. It is not in b, whose question set needs every score of the 20 rank rows.
- Median RAGAS faithfulness is 0.84 at judge score 2 or less and 1.00 at 4 or more (a result, so out of the legend since S3, 7 November; for the text).
