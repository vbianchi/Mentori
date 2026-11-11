# Figure 3, first ranking: draws 1, 2, 3 of 3, provisional (D82, D88)

draws 1, 2, 3 of 3 (D82, D88), 14,860 of 21,402 answers read from their final-key row (G1 2,430, G2 and G6 810, G4 11,620), 2,425 G1 answers judged (devstral-small-2:24b, plain call), collect of 2026-10-23T09:41:17, run_sha256 38ae79ab023b; concept recall: D181's reading on key v2.5, L3_d181 rows of 2026-10-31T00:03:05Z.

Read by `scripts/S463_fig2_ranking.py rank` from `g1_collect.jsonl`: 2430 rows under one run_sha256 (38ae79ab023b) and lock d66daa28 (D88). 2430 answers of the draws read: 2425 went to the judge, 5 had no text and no judge call. The judge is devstral-small-2:24b (digest 33af3142213a, checked in each unit's headers), the plain call (a), with no passages in its prompt. Each of the 10 judging units read passed its recheck (the first answers judged again after a fresh load gave the same scores). G1's reruns of 18 October in the draws read (15 answers) come from their own pass (D93 Q-c), checked row by row. The rules are experiments/LIST.md's (Rules 2, 3, 4, 5, 6, 9, 10, 11, 12); no rule is new (D84).

Judge rows (D186 (3)): each answer is read through scripts/judge_rows_v25.py, its key v2.5 row where one exists, else its key v2.4 row; key v2.5 for every answer of the 132 changed questions read (1,080).

## In short

At judge score 4 or more, the pass rate (draws 1, 2, 3 of 3): verified pass has the highest mean, but the test cannot tell it apart from single pass, multi-hop, RLM-10; RLM-20 has the lowest mean, but the test cannot tell it apart from multi-hop, RLM-5, RLM-10. Every number below rests on all three draws and stays provisional (D82) until the plate is made final.

## Pass rate on the 86 answerable questions, highest first

The pass rate is the share of answers the judge scores 4 or more; 3 or more is the relaxed threshold (LIST.md Rule 5, D154). Rank by the pass rate at 4.

| Rank | Strategy | Score 4 or more, the pass rate (95% interval) | Score 3 or more, relaxed (95% interval) | Failed answers on the 86, counted as fails | Judge calls with no score on the 86, left out |
|---|---|---|---|---|---|
| 1 | verified pass | 83.3% (76.4 to 89.9) | 93.0% (88.0 to 97.3) | 1 | 0 |
| 2 | single pass | 82.9% (75.2 to 89.9) | 93.4% (87.6 to 98.1) | 0 | 0 |
| 3 | multi-hop | 78.7% (71.3 to 86.0) | 95.7% (92.6 to 98.4) | 0 | 0 |
| 4 | RLM-10 | 74.0% (67.8 to 79.8) | 92.2% (88.0 to 95.7) | 1 | 0 |
| 5 | RLM-5 | 73.3% (66.3 to 79.8) | 93.4% (89.5 to 96.9) | 1 | 0 |
| 6 | RLM-20 | 70.5% (63.2 to 77.1) | 93.8% (90.3 to 96.9) | 0 | 0 |

Each rate is the mean over the questions of each question's pass share over the draws read (draws 1, 2, 3 of 3); the interval resamples the questions 10,000 times (Rule 2). Questions with a share: single pass 86, multi-hop 86, verified pass 86, RLM-5 86, RLM-10 86, RLM-20 86. The failed answers count for every strategy, on all three groups of questions; the table gives those on the 86.

## Which pairs the test separates (all 15, unadjusted)

Rule 3's exact two-sided sign-flip test on the per-question differences (on one draw, the exact McNemar test), P < 0.05, not adjusted for the 15 pairs (Rule 12). This describes; it claims nothing: a sentence about one pair rests on Rule 3 or Rule 6 for a comparison named there (the claims below). Each pair's difference, interval and P value are in ranking.json and the Source Data.

| Strategy | Score 4 or more: above | below | not told apart from | Score 3 or more: above | below | not told apart from |
|---|---|---|---|---|---|---|
| verified pass | RLM-5, RLM-20 | none | single pass, multi-hop, RLM-10 | none | none | single pass, multi-hop, RLM-5, RLM-10, RLM-20 |
| single pass | RLM-5, RLM-20 | none | multi-hop, verified pass, RLM-10 | none | none | multi-hop, verified pass, RLM-5, RLM-10, RLM-20 |
| multi-hop | none | none | single pass, verified pass, RLM-5, RLM-10, RLM-20 | none | none | single pass, verified pass, RLM-5, RLM-10, RLM-20 |
| RLM-10 | none | none | single pass, multi-hop, verified pass, RLM-5, RLM-20 | none | none | single pass, multi-hop, verified pass, RLM-5, RLM-20 |
| RLM-5 | none | single pass, verified pass | multi-hop, RLM-10, RLM-20 | none | none | single pass, multi-hop, verified pass, RLM-10, RLM-20 |
| RLM-20 | none | single pass, verified pass | multi-hop, RLM-5, RLM-10 | none | none | single pass, multi-hop, verified pass, RLM-5, RLM-10 |

## Highest and lowest (Rule 6) and the letter's claims (Rule 11)

Rule 6 is stated at threshold 4, the pass rate (LIST.md Rule 6, D154). It is also given at 3, the relaxed threshold, because Rule 5 reports every pass-based statistic at both and Rule 11 gives a verdict at each threshold (D115 F2Q1 O-a: both thresholds kept).

- Score 4 or more, highest by mean: verified pass. Rule 6 is not met: it cannot be told apart from single pass, multi-hop, RLM-10.
- Score 4 or more, lowest by mean: RLM-20. Rule 6 is not met: it cannot be told apart from multi-hop, RLM-5, RLM-10.
- Score 3 or more, highest by mean: multi-hop. Rule 6 is not met: it cannot be told apart from single pass, verified pass, RLM-5, RLM-10, RLM-20.
- Score 3 or more, lowest by mean: RLM-10. Rule 6 is not met: it cannot be told apart from single pass, multi-hop, verified pass, RLM-5, RLM-20.

| Claim | Score 4 or more | Score 3 or more | With failed answers left out (4; 3) | Without the verified-pass answers whose verifier was not ok (4; 3) |
|---|---|---|---|---|
| RLM-10 has the highest pass rate of the six strategies (E1a) | reverses | reverses | reverses; reverses | reverses; reverses |
| verified pass has the lowest pass rate of the six strategies (E1b) | reverses | reverses | reverses; reverses | reverses; reverses |
| RLM-10 passes more than verified pass (E4) | reverses | reverses | reverses; reverses | reverses; reverses |
| RLM-10 passes more than single pass (E5) | reverses | reverses | reverses; reverses | reverses; reverses |
| verified pass passes less than single pass (R11) | reverses | weakens | reverses; weakens | reverses; weakens |
| RLM-10 refuses more not-answerable questions than multi-hop (E6) | - | holds | -; holds | -; holds |

E6 is on refusal, which Rule 9 defines at score 3 only, so it has no verdict at 4. Verdict changed by leaving the failed answers out (Rule 10's sensitivity): none. Every verdict here rests on draws 1, 2, 3 of 3 and is provisional.

## Refusal on the 39 questions the papers cannot answer (Rule 9)

| Strategy | Refused, refusal score 3 or more (95% interval) | False-premise passed, correctness 4 or more | Correctness 3 or more (relaxed) |
|---|---|---|---|
| single pass | 100% (at least 92.6%, one-sided 95% lower bound) | 30 of 30 | 30 of 30 |
| multi-hop | 88.0% (80.3 to 94.9) | 28 of 30 | 30 of 30 |
| verified pass | 100% (at least 92.6%, one-sided 95% lower bound) | 28 of 30 | 29 of 30 |
| RLM-5 | 70.1% (59.8 to 79.5) | 26 of 30 | 29 of 30 |
| RLM-10 | 97.4% (94.0 to 100.0) | 25 of 30 | 30 of 30 |
| RLM-20 | 96.6% (90.6 to 100.0) | 26 of 30 | 29 of 30 |

Highest refusal by mean: single pass (tied with verified pass); the test cannot tell it apart from verified pass, RLM-10, RLM-20. An answer with no text counts as not refused. The false-premise questions are counts only: ten questions give no interval and no test (Rule 9). Refusal is read at refusal score 3 or more only: Rule 9 defines it so, and Rule 5's second threshold is for pass-based statistics.

## Concept recall on the 86 answerable questions (sheet Fig. 3a, not drawn)

D181's reading on key v2.5: S505's loose matcher with the question rule, Q-need, reading (b) (findings/recompute/L3_d181, S471 --d181), rows of 2026-10-31T00:03:05Z. L3_d181 held to L3: both files at their pinned sha256, the header S471's final D181 reading on key v2.5 of L3's answer copy, its 2,430 rows L3's answers one for one, and on the 36 scored questions (answerable and false premise) whose concepts v2.5 left unchanged the loose base of 648 scored rows equal to L3's loose value. Read first: plan row L3's loose reading on key v2.4 (S471, 2026-10-22T12:09:49Z); S471's gate: S432 reproduced on 107 of 107 completed answers; every answerable L3 row was scored again here from the generation record S3 judged and gave the same values; panel b's v2.4 anchor: L3's loose reading gives the committed panel b (ranking.json at 56478637) on all 6 strategies (mean, interval, exact value, failed answers). Per answer, the key's expected concepts found in it over the concepts counted (D181: a concept made only of words of its question is not counted); per question the mean over draws 1, 2, 3 of 3; the mean over the 86 questions with the Rule 2 interval. An answer with no text scores 0 and stays in (Rule 10): 3 answers. An RLM answer whose record flags Mentor::i's fixed turn-limit note is scored with the note removed (D115 L1e O-a): 7 answers.

| Strategy | Concept recall (95% interval) | Exact substring, every concept (95% interval) | Failed answers, scored 0 |
|---|---|---|---|
| RLM-10 | 76.2% (71.6 to 80.4) | 36.4% (30.4 to 42.9) | 1 |
| RLM-20 | 75.1% (70.8 to 79.4) | 36.3% (30.7 to 42.2) | 0 |
| RLM-5 | 74.0% (69.4 to 78.4) | 37.5% (31.8 to 43.6) | 1 |
| verified pass | 69.7% (64.1 to 75.2) | 29.0% (23.2 to 35.4) | 1 |
| single pass | 69.3% (63.7 to 74.9) | 28.5% (22.6 to 34.8) | 0 |
| multi-hop | 54.0% (48.0 to 60.2) | 23.3% (17.6 to 29.6) | 0 |

- Concept recall, highest by mean: RLM-10. Rule 6 is not met: it cannot be told apart from RLM-5, RLM-20.
- Concept recall, lowest by mean: multi-hop. Rule 6 is met: the test separates it from every other strategy.

Rule 6 runs Rule 3's test on per-question means of the signal (LIST.md, Rule 6). All 15 pairs, unadjusted, are in the Source Data (sheet Fig. 3a) and ranking.json.

## Quality against cost (panel d)

Model calls per answer are the entries of each answer's generation.calls; clock time is generation.latency_s (S457.exp01_row reads both). Per question the mean over its draws, then the mean over the questions, with the Rule 2 interval from the same resamples as the pass rates. Failed answers count (their calls were made).

| Strategy | Pass rate, score 4 or more (86) | Model calls per answer, 86 (95% interval) | all 135 | Clock time per answer (s), 86 | all 135 | of which waiting for the local server (s), 86 |
|---|---|---|---|---|---|---|
| single pass | 82.9% | 1.00 (1.00 to 1.00) | 1.00 | 42.1 | 41.4 | 0.0 |
| multi-hop | 78.7% | 1.49 (1.27 to 1.74) | 2.76 | 61.3 | 112.7 | 0.0 |
| verified pass | 83.3% | 2.00 (2.00 to 2.00) | 2.00 | 372.4 | 330.1 | 275.3 |
| RLM-5 | 73.3% | 6.16 (5.90 to 6.43) | 6.18 | 121.9 | 113.6 | 0.0 |
| RLM-10 | 74.0% | 6.31 (5.98 to 6.71) | 7.29 | 129.0 | 137.2 | 0.0 |
| RLM-20 | 70.5% | 6.55 (6.19 to 6.96) | 7.39 | 124.4 | 126.7 | 0.0 |

RLM-10 over single pass: 7.29 times the model calls and 3.31 times the clock time on all 135 questions (6.31 and 3.07 on the 86). The letter's 5.87 calls against 1.00 and 82.4 s against 10.4 (six and eight times) come from the submitted run (findings/recompute/S77_r2q2_cost.json, reproduced by this run); claims.md sets them against these records (C22, C47).

## Each strategy against single pass (panel c, Rule 4)

Every single-pass draw of a question against every draw of the strategy (9 pairings). Harmed and helped are means over the pairings of the questions changed; the shares are Rule 4's two denominators with the Rule 2 interval; P is Rule 3's exact two-sided sign-flip test (harmed minus helped is s - v per question). Same-draw totals are Rule 4 (a)'s three draw-d-against-draw-d tables added up.

| Strategy | Score | Harmed | Helped | Harmful share of changed (95% interval) | Single pass's correct answers degraded (95% interval) | P | Same-draw totals, harmed / helped |
|---|---|---|---|---|---|---|---|
| multi-hop | 4 | 8.22 | 4.56 | 64.3% (44.1 to 82.0) | 11.5% (6.1 to 17.4) | 0.203 | 27 / 16 |
| verified pass | 4 | 5.56 | 5.89 | 48.5% (28.2 to 73.4) | 7.8% (4.0 to 12.2) | 1.000 | 17 / 18 |
| RLM-5 | 4 | 17.11 | 8.78 | 66.1% (51.3 to 80.5) | 24.0% (17.5 to 30.9) | 0.042 | 51 / 26 |
| RLM-10 | 4 | 17.44 | 9.78 | 64.1% (50.0 to 78.5) | 24.5% (18.2 to 30.9) | 0.067 | 52 / 29 |
| RLM-20 | 4 | 19.56 | 8.89 | 68.8% (54.5 to 82.3) | 27.4% (20.2 to 35.2) | 0.014 | 59 / 27 |
| multi-hop | 3 | 2.44 | 4.44 | 35.5% (10.0 to 71.4) | 3.0% (0.7 to 5.9) | 0.465 | 8 / 14 |
| verified pass | 3 | 2.67 | 2.33 | 53.3% (18.8 to 100.0) | 3.3% (0.8 to 6.3) | 1.000 | 8 / 7 |
| RLM-5 | 3 | 5.67 | 5.67 | 50.0% (27.0 to 79.3) | 7.1% (3.4 to 11.3) | 1.000 | 17 / 17 |
| RLM-10 | 3 | 6.67 | 5.67 | 54.1% (32.1 to 81.5) | 8.3% (4.6 to 12.7) | 0.825 | 20 / 17 |
| RLM-20 | 3 | 5.33 | 5.67 | 48.5% (26.3 to 77.8) | 6.6% (3.3 to 10.4) | 1.000 | 16 / 17 |

Noise baseline (Rule 4 (b)): each strategy's draws against each other, the share of a question's pairs of draws that disagree, and the fewest to the most questions passing on one draw and failing on another over the ordered pairs of draws (single pass's is the panel's band).

| Strategy | Score | Disagreeing pairs of draws | Fewest to most per ordered pair |
|---|---|---|---|
| single pass | 4 | 6.2% | 2 to 4 |
| multi-hop | 4 | 14.7% | 3 to 9 |
| verified pass | 4 | 10.9% | 2 to 7 |
| RLM-5 | 4 | 29.5% | 10 to 16 |
| RLM-10 | 4 | 32.6% | 13 to 15 |
| RLM-20 | 4 | 29.5% | 9 to 15 |
| single pass | 3 | 0.8% | 0 to 1 |
| multi-hop | 3 | 6.2% | 1 to 4 |
| verified pass | 3 | 4.7% | 1 to 3 |
| RLM-5 | 3 | 9.3% | 3 to 5 |
| RLM-10 | 3 | 11.6% | 4 to 6 |
| RLM-20 | 3 | 10.1% | 3 to 5 |

Verified pass without its 1 answers whose verifier was not ok (Q78): harmful share 48.5% at score 4 and 53.3% at 3; degraded 7.8% and 3.3%.

## Verified pass: answers whose verifier was not ok (Rule 4, Q78)

Of the 405 verified-pass answers in the draws read, 1 had a verifier status other than ok (empty 1), and 0 stopped before the verifier ran. Their keys: exp_v4_s20_n0|verified_pass|OOD_030|d3.

Verified pass's verifier model: gpt-oss:20b-date20261010 (gpt-oss:20b with the date fixed, LOCK [date]), the local model of the verified-pass answers' calls in the draws read, named as S457 names it (F3-04, rulings page 6 Nov).

Verified pass with them: pass rate 83.3% at score 4, 93.0% at 3, refused 100.0%. Without them: 83.3% at 4, 93.0% at 3, refused 100.0%.

## Failed answers and other outcomes (Rule 10)

- verified pass: failed, counted as fails: 1 stopped by Google (blocked; stop reason blocked).
- RLM-5: failed, counted as fails: 3 max_turns_empty; a Gemini reply returned with its status, scored as written: 1 malformed_response; cut, scored as written: 67 max_turns_partial.
- RLM-10: failed, counted as fails: 1 max_turns_empty; a Gemini reply returned with its status, scored as written: 1 empty; cut, scored as written: 10 max_turns_partial.
- RLM-20: stopped by Google, scored as written: 1 stopped by Google (recitation); a Gemini reply returned with its status, scored as written: 1 malformed_response; cut, scored as written: 2 max_turns_partial.

The answer keys behind every count are in ranking.json. claims.md sets every number the main text, the submitted Figure 2 legend and the letter give for panels a, c, d and e against these values (D82).

## What this does not show yet

- The replication on other generators (panel e, plan row T2): not drawn yet; its frame is empty.
