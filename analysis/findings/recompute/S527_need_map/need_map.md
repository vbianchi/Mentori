# The map of needs (D194 Q2)

Written by scripts/S527_need_map.py, sha256 9a1b60ba35c4d6f1. Descriptive: no cell recommends an option. N5 and N11 say which strategy a rule or a signal placed highest. Whose sentence says whether the words are attack.md's or this script's. Every value's key is in need_map.json.

7 sentences held to their values, 11 stated values held, 0 to restate.

## Needs

| | Need | What the data support | Values | Stands on | Whose sentence | Row behind it |
|---|---|---|---|---|---|---|
| N1 | Any question, with the budget to read widely | Given RLM-10's tokens per question, one call passed 94.6%. | one call at RLM-10's budget: 94.6 %; single pass: 83.3 %; RLM-10: 74.8 %. | judge on key v2.4, draws 1 to 3, 86 questions | attack.md's sentence | attack.md row 1, WEAKEN |
| N2 | One-paper questions | RLM-10 lost by the judge, not by concept recall. | single pass, judge at 4: 97.2 %; RLM-10, judge at 4: 70.6 %; single pass, concept recall: 78.4 %; RLM-10, concept recall: 80.0 %. | judge on key v2.4, draws 1 to 3, 60 questions; concept recall on key v2.5, draws 1 to 3, 60 questions | attack.md's sentence | attack.md rows 2 and 3, WEAKEN |
| N3 | Many-paper questions | On many-paper questions the judge and concept recall agree, and reading more text explains much of RLM-10's gain. | single pass, judge at 4: 51.3 %; RLM-10, judge at 4: 84.6 %; one call at RLM-10's budget, judge at 4: 85.9 %; single pass, concept recall: 48.5 %; RLM-10, concept recall: 67.5 %. | judge on key v2.4, draws 1 to 3, 26 questions; concept recall on key v2.5, draws 1 to 3, 26 questions | this script's, on attack.md's reason | attack.md row 4, KEEP, exploratory |
| N4 | Answers supported by the papers | No clear rise in support from verification. | verified pass, Papers precision: 83.7 %; single pass, Papers precision: 80.9 %; verified pass minus single pass: 2.8 points; its 95% interval, lower end, two-sided: -0.5 points; its 95% interval, upper end, two-sided: 6.2 points. | draw 1, 81 questions with a value in every strategy | this script's, picked by the values | attack.md row 5, WEAKEN |
| N5 | Declining what the papers cannot answer | Single pass and verified pass refused every out-of-scope answer, by judge score. | single pass, answers refusing, refusal score 3 or more: 117 of 117; verified pass, answers refusing, refusal score 3 or more: 117 of 117; RLM-10, answers refusing, refusal score 3 or more: 114 of 117; not told apart from single pass, the highest, tied with verified pass: verified pass, RLM-10, RLM-20. | draws 1 to 3, 39 questions; each answer's key v2.5 row where one exists, else its key v2.4 row | this script's, picked by the values | attack.md row 6, WEAKEN |
| N6 | A large corpus | 50 core papers, the largest tested. | single pass, judge at 4: 81.4 %; RLM-10, judge at 4: 64.0 %; P, Bonferroni over 12 cells, two-sided: 0.071; answers still read from key v2.4: 0 answers. | draw 1, every covered question (D98's main estimate), 86 questions; key v2.5 where S6 has judged, else key v2.4 | attack.md's sentence | attack.md row 7, KEEP |
| N7 | Time per answer | Time per answer, with verified pass's time mostly spent waiting. | single pass, seconds: 42.1 s; verified pass, seconds: 372.4 s; of which waiting: 275.3 s; RLM-10, seconds: 129.0 s. | draws 1 to 3, 86 questions | this script's, on attack.md's reason | attack.md row 8, KEEP, no best |
| N8 | Code | Best-of-3 showed no clear gain. | pairs: 220 pairs; pass with best-of-3 only: 19 pairs; pass with free-form only: 13 pairs; P, McNemar, two-sided: 0.38. | 2,420 of 2,420 attempts, 11 of 11 variants complete, records of 2026-11-04 08:35 CET; after the S4 reruns (D75, D80 V1, D81) | attack.md's sentence | attack.md row 9, WEAKEN |
| N9 | The choice of generator | blank | Needs T2's generators. D195: closed until S518 runs on Valerio's word. | | | attack.md row 10, KEEP until T2 |
| N10 | The choice of judge | blank | Needs the second judge. D195: closed until S518 runs on Valerio's word. | | | attack.md row 12, KEEP, no pick |
| N11 | More than one signal | Signals differ on which strategy is highest, and no signal separates its highest from the next. | highest by the judge at 4: single pass, 0.4 points ahead of verified pass (95% interval -5.4 to +6.2, two-sided); highest by concept recall: RLM-10, 1.1 points ahead of RLM-20 (95% interval -2.4 to +4.5, two-sided); highest by Papers precision: verified pass, 2.8 points ahead of single pass (95% interval -0.5 to +6.2, two-sided). | the judge at 4: draws 1 to 3, 86 questions; concept recall: draws 1 to 3, 86 questions; Papers precision: draw 1, 81 questions | this script's, picked by the values | attack.md row 13, WEAKEN |
| N12 | An orchestrated pipeline | No clear change in any orchestrator set-up; the intervals are wide. | lowest end of any interval, from routing fix: -18.6 points; highest end of any interval, from no synthesizer: 14.0 points; set-ups, each against the full pipeline: 5 set-ups. | draw 1, 86 questions; key v2.5 judge rows: RLM-10's 60 from S6G1 after phase 3 (frozen fig3_s6_inputs, S528), G3's 600 | this script's, on attack.md's reason | attack.md row 15, WEAKEN |
| N13 | A flat wide call, fixed in advance | blank | G10 is not judged yet (D196): no committed output holds its pass rates. | | | not a verdict row: attack.md's action A2 |
| N14 | The old 800-character cut under the lock | blank | G11 is not judged yet (D196): no committed output holds its pass rates. | | | not in attack.md: D194 Q4 |

## Measures

| | Need | What the data support | Values | Stands on | Whose sentence | Row behind it |
|---|---|---|---|---|---|---|
| M1 | Judge correctness | Separates question types, which is not the same as being right. | RLM-10, one-paper: 70.6 %; RLM-10, many-paper: 84.6 %. | judge on key v2.4, draws 1 to 3, 60 questions; judge on key v2.4, draws 1 to 3, 26 questions | this script's, on attack.md's reason | attack.md second table, WEAKEN |
| M2 | Concepts | Reads whether the key's concepts are stated. Descriptive. | RLM-10 minus single pass, judge at 4: -8.5 points; RLM-10 minus single pass, concept recall: 6.8 points. | concept recall on key v2.5, draws 1 to 3, 86 questions | this script's, on attack.md's reason | attack.md second table, KEEP |
| M3 | Papers | Provisional: the stored values count source-list lines as claims. D172's filter (minicheck_filter.py) is not applied here, and its heading rule is set. | change in RLM-10 minus single pass when S526 drops source-list lines: 17.6 points. | draw 1, 81 questions, S526's approximate filter | this script's, on attack.md's reason | attack.md second table, WEAKEN |
| M4 | METEOR | blank | Its number stands only in a scratch output (ev_fast.py), and this script reads none. | | | attack.md second table, WEAKEN |
| M5 | Citations | blank | Its number comes from S483's composite, closed here beside the second judge. D195: closed until S518 runs on Valerio's word. | | | attack.md second table, WEAKEN |
| M6 | Refusal score | blank | The only signal for this need, by design; its values are N5's. | | | attack.md second table, KEEP |
| M7 | RAGChecker | blank | K1's rows are partial until the pull (build_order.md section 7). | | | attack.md second table, WEAKEN |

## Sources

- findings/figures_provisional/fig3_strategies/ranking.json
- findings/figures_provisional/fig4/figure5_numbers.json
- findings/figures_provisional/fig6/fig6_numbers.json
- findings/recompute/G4_fig3c_d185/verdicts.json
- findings/recompute/S511_g2_budget/results.json
- findings/recompute/S526_instrument_swaps/results.json
