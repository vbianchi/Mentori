# Supplementary Table 66 questions

Draw 1 of corpus scaling, gemini-3-flash-preview, judged by devstral-small-2:24b. Groups are never pooled. Refused: a refusal accuracy of 3 or more under the decline prompt. Each interval is two-sided 95% (percentile bootstrap, 10,000 resamples of the questions); at 100% refused the cell gives the one-sided lower bound, at 0% the one-sided upper bound. Provisional: 864 answerable answers await S6G4 and are read on key v2.4 until it ends. Run to run gives the lowest to the highest rate over the draws on the fixed third of each group, and stays blank until a second draw is read. Failed answers are kept in every rate, as not passed and not refused.

| Group | Core papers | Strategy | Questions | Pass rate 4+ (%) | Interval 4+ (two-sided 95%) | Pass rate 3+ (%) | Interval 3+ (two-sided 95%) | Answers awaiting S6G4 | Run to run |
|---|---|---|---|---|---|---|---|---|---|
| 22 answerable questions | 5 | single pass | 22 | 81.8 | 65.2 to 95.5 | 90.9 | 77.3 to 100.0 | 36 |  |
| 22 answerable questions | 5 | multi-hop | 22 | 77.3 | 60.6 to 90.9 | 97.0 | 90.9 to 100.0 | 36 |  |
| 22 answerable questions | 5 | verified pass | 22 | 86.4 | 72.7 to 98.5 | 87.9 | 74.2 to 100.0 | 36 |  |
| 22 answerable questions | 5 | RLM-5 | 22 | 66.7 | 51.5 to 80.3 | 92.4 | 84.8 to 98.5 | 36 |  |
| 22 answerable questions | 5 | RLM-10 | 22 | 77.3 | 65.2 to 87.9 | 90.9 | 83.3 to 97.0 | 36 |  |
| 22 answerable questions | 5 | RLM-20 | 22 | 74.2 | 59.1 to 86.4 | 95.5 | 90.9 to 100.0 | 36 |  |
| 22 answerable questions | 10 | single pass | 22 | 81.8 | 63.6 to 95.5 | 90.9 | 77.3 to 100.0 | 36 |  |
| 22 answerable questions | 10 | multi-hop | 22 | 74.2 | 57.6 to 89.4 | 95.5 | 87.9 to 100.0 | 36 |  |
| 22 answerable questions | 10 | verified pass | 22 | 78.8 | 63.6 to 92.4 | 87.9 | 74.2 to 100.0 | 36 |  |
| 22 answerable questions | 10 | RLM-5 | 22 | 74.2 | 62.1 to 86.4 | 92.4 | 86.4 to 98.5 | 36 |  |
| 22 answerable questions | 10 | RLM-10 | 22 | 71.2 | 57.6 to 83.3 | 97.0 | 92.4 to 100.0 | 36 |  |
| 22 answerable questions | 10 | RLM-20 | 22 | 74.2 | 60.6 to 86.4 | 97.0 | 92.4 to 100.0 | 36 |  |
| 22 answerable questions | 20 | single pass | 22 | 78.8 | 60.6 to 95.5 | 90.9 | 77.3 to 100.0 | 36 |  |
| 22 answerable questions | 20 | multi-hop | 22 | 86.4 | 72.7 to 97.0 | 100.0 | 100.0 to 100.0 | 36 |  |
| 22 answerable questions | 20 | verified pass | 22 | 83.3 | 68.2 to 95.5 | 87.9 | 74.2 to 100.0 | 36 |  |
| 22 answerable questions | 20 | RLM-5 | 22 | 71.2 | 56.1 to 84.8 | 84.8 | 72.7 to 95.5 | 36 |  |
| 22 answerable questions | 20 | RLM-10 | 22 | 77.3 | 65.2 to 87.9 | 93.9 | 84.8 to 100.0 | 36 |  |
| 22 answerable questions | 20 | RLM-20 | 22 | 71.2 | 56.1 to 84.8 | 89.4 | 80.3 to 97.0 | 36 |  |
| 22 answerable questions | 50 | single pass | 22 | 84.8 | 69.7 to 97.0 | 90.9 | 77.3 to 100.0 | 36 |  |
| 22 answerable questions | 50 | multi-hop | 22 | 78.8 | 63.6 to 92.4 | 98.5 | 95.5 to 100.0 | 36 |  |
| 22 answerable questions | 50 | verified pass | 22 | 87.9 | 74.2 to 98.5 | 90.9 | 77.3 to 100.0 | 36 |  |
| 22 answerable questions | 50 | RLM-5 | 22 | 75.8 | 62.1 to 87.9 | 90.9 | 81.8 to 98.5 | 36 |  |
| 22 answerable questions | 50 | RLM-10 | 22 | 69.7 | 54.5 to 83.3 | 97.0 | 92.4 to 100.0 | 36 |  |
| 22 answerable questions | 50 | RLM-20 | 22 | 75.8 | 65.2 to 84.8 | 93.9 | 87.9 to 98.5 | 36 |  |

| Group | Core papers | Distractors per core paper | Strategy | Questions | Refused (%) | Interval or bound | Answers awaiting S6G4 | Run to run |
|---|---|---|---|---|---|---|---|---|
| 39 out-of-scope questions | 5 | pooled | single pass | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 5 | 0 | single pass | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 5 | 1 | single pass | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 5 | 3 | single pass | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 5 | pooled | multi-hop | 39 | 80.3 | 71.8 to 88.0 | 0 |  |
| 39 out-of-scope questions | 5 | 0 | multi-hop | 39 | 89.7 | 79.5 to 97.4 | 0 |  |
| 39 out-of-scope questions | 5 | 1 | multi-hop | 39 | 82.1 | 69.2 to 92.3 | 0 |  |
| 39 out-of-scope questions | 5 | 3 | multi-hop | 39 | 69.2 | 53.8 to 82.1 | 0 |  |
| 39 out-of-scope questions | 5 | pooled | verified pass | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 5 | 0 | verified pass | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 5 | 1 | verified pass | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 5 | 3 | verified pass | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 5 | pooled | RLM-5 | 39 | 84.6 | 76.9 to 91.5 | 0 |  |
| 39 out-of-scope questions | 5 | 0 | RLM-5 | 39 | 94.9 | 87.2 to 100.0 | 0 |  |
| 39 out-of-scope questions | 5 | 1 | RLM-5 | 39 | 84.6 | 71.8 to 94.9 | 0 |  |
| 39 out-of-scope questions | 5 | 3 | RLM-5 | 39 | 74.4 | 59.0 to 87.2 | 0 |  |
| 39 out-of-scope questions | 5 | pooled | RLM-10 | 39 | 94.0 | 88.9 to 98.3 | 0 |  |
| 39 out-of-scope questions | 5 | 0 | RLM-10 | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 5 | 1 | RLM-10 | 39 | 97.4 | 92.3 to 100.0 | 0 |  |
| 39 out-of-scope questions | 5 | 3 | RLM-10 | 39 | 84.6 | 71.8 to 94.9 | 0 |  |
| 39 out-of-scope questions | 5 | pooled | RLM-20 | 39 | 94.9 | 89.7 to 99.1 | 0 |  |
| 39 out-of-scope questions | 5 | 0 | RLM-20 | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 5 | 1 | RLM-20 | 39 | 94.9 | 87.2 to 100.0 | 0 |  |
| 39 out-of-scope questions | 5 | 3 | RLM-20 | 39 | 89.7 | 79.5 to 97.4 | 0 |  |
| 39 out-of-scope questions | 10 | pooled | single pass | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 10 | 0 | single pass | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 10 | 1 | single pass | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 10 | 3 | single pass | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 10 | pooled | multi-hop | 39 | 70.1 | 59.8 to 79.5 | 0 |  |
| 39 out-of-scope questions | 10 | 0 | multi-hop | 39 | 92.3 | 82.1 to 100.0 | 0 |  |
| 39 out-of-scope questions | 10 | 1 | multi-hop | 39 | 61.5 | 46.2 to 76.9 | 0 |  |
| 39 out-of-scope questions | 10 | 3 | multi-hop | 39 | 56.4 | 41.0 to 71.8 | 0 |  |
| 39 out-of-scope questions | 10 | pooled | verified pass | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 10 | 0 | verified pass | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 10 | 1 | verified pass | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 10 | 3 | verified pass | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 10 | pooled | RLM-5 | 39 | 83.8 | 76.9 to 90.6 | 0 |  |
| 39 out-of-scope questions | 10 | 0 | RLM-5 | 39 | 92.3 | 82.1 to 100.0 | 0 |  |
| 39 out-of-scope questions | 10 | 1 | RLM-5 | 39 | 74.4 | 59.0 to 87.2 | 0 |  |
| 39 out-of-scope questions | 10 | 3 | RLM-5 | 39 | 84.6 | 71.8 to 94.9 | 0 |  |
| 39 out-of-scope questions | 10 | pooled | RLM-10 | 39 | 94.0 | 88.9 to 98.3 | 0 |  |
| 39 out-of-scope questions | 10 | 0 | RLM-10 | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 10 | 1 | RLM-10 | 39 | 92.3 | 82.1 to 100.0 | 0 |  |
| 39 out-of-scope questions | 10 | 3 | RLM-10 | 39 | 89.7 | 79.5 to 97.4 | 0 |  |
| 39 out-of-scope questions | 10 | pooled | RLM-20 | 39 | 94.0 | 88.9 to 98.3 | 0 |  |
| 39 out-of-scope questions | 10 | 0 | RLM-20 | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 10 | 1 | RLM-20 | 39 | 97.4 | 92.3 to 100.0 | 0 |  |
| 39 out-of-scope questions | 10 | 3 | RLM-20 | 39 | 84.6 | 71.8 to 94.9 | 0 |  |
| 39 out-of-scope questions | 20 | pooled | single pass | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 20 | 0 | single pass | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 20 | 1 | single pass | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 20 | 3 | single pass | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 20 | pooled | multi-hop | 39 | 73.5 | 63.2 to 82.9 | 0 |  |
| 39 out-of-scope questions | 20 | 0 | multi-hop | 39 | 89.7 | 79.5 to 97.4 | 0 |  |
| 39 out-of-scope questions | 20 | 1 | multi-hop | 39 | 66.7 | 51.3 to 79.5 | 0 |  |
| 39 out-of-scope questions | 20 | 3 | multi-hop | 39 | 64.1 | 48.7 to 79.5 | 0 |  |
| 39 out-of-scope questions | 20 | pooled | verified pass | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 20 | 0 | verified pass | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 20 | 1 | verified pass | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 20 | 3 | verified pass | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 20 | pooled | RLM-5 | 39 | 76.1 | 69.2 to 82.1 | 0 |  |
| 39 out-of-scope questions | 20 | 0 | RLM-5 | 39 | 79.5 | 66.7 to 92.3 | 0 |  |
| 39 out-of-scope questions | 20 | 1 | RLM-5 | 39 | 69.2 | 53.8 to 82.1 | 0 |  |
| 39 out-of-scope questions | 20 | 3 | RLM-5 | 39 | 79.5 | 66.7 to 92.3 | 0 |  |
| 39 out-of-scope questions | 20 | pooled | RLM-10 | 39 | 93.2 | 88.9 to 97.4 | 0 |  |
| 39 out-of-scope questions | 20 | 0 | RLM-10 | 39 | 94.9 | 87.2 to 100.0 | 0 |  |
| 39 out-of-scope questions | 20 | 1 | RLM-10 | 39 | 92.3 | 82.1 to 100.0 | 0 |  |
| 39 out-of-scope questions | 20 | 3 | RLM-10 | 39 | 92.3 | 82.1 to 100.0 | 0 |  |
| 39 out-of-scope questions | 20 | pooled | RLM-20 | 39 | 92.3 | 87.2 to 96.6 | 0 |  |
| 39 out-of-scope questions | 20 | 0 | RLM-20 | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 20 | 1 | RLM-20 | 39 | 89.7 | 79.5 to 97.4 | 0 |  |
| 39 out-of-scope questions | 20 | 3 | RLM-20 | 39 | 87.2 | 76.9 to 97.4 | 0 |  |
| 39 out-of-scope questions | 50 | pooled | single pass | 39 | 99.1 | 97.4 to 100.0 | 0 |  |
| 39 out-of-scope questions | 50 | 0 | single pass | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 50 | 1 | single pass | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 50 | 3 | single pass | 39 | 97.4 | 92.3 to 100.0 | 0 |  |
| 39 out-of-scope questions | 50 | pooled | multi-hop | 39 | 67.5 | 58.1 to 76.9 | 0 |  |
| 39 out-of-scope questions | 50 | 0 | multi-hop | 39 | 89.7 | 79.5 to 97.4 | 0 |  |
| 39 out-of-scope questions | 50 | 1 | multi-hop | 39 | 69.2 | 53.8 to 82.1 | 0 |  |
| 39 out-of-scope questions | 50 | 3 | multi-hop | 39 | 43.6 | 28.2 to 59.0 | 0 |  |
| 39 out-of-scope questions | 50 | pooled | verified pass | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 50 | 0 | verified pass | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 50 | 1 | verified pass | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 50 | 3 | verified pass | 39 | 100.0 | one-sided lower bound 92.6 | 0 |  |
| 39 out-of-scope questions | 50 | pooled | RLM-5 | 39 | 75.2 | 67.5 to 82.1 | 0 |  |
| 39 out-of-scope questions | 50 | 0 | RLM-5 | 39 | 87.2 | 76.9 to 97.4 | 0 |  |
| 39 out-of-scope questions | 50 | 1 | RLM-5 | 39 | 71.8 | 56.4 to 84.6 | 0 |  |
| 39 out-of-scope questions | 50 | 3 | RLM-5 | 39 | 66.7 | 51.3 to 82.1 | 0 |  |
| 39 out-of-scope questions | 50 | pooled | RLM-10 | 39 | 93.2 | 88.0 to 97.4 | 0 |  |
| 39 out-of-scope questions | 50 | 0 | RLM-10 | 39 | 94.9 | 87.2 to 100.0 | 0 |  |
| 39 out-of-scope questions | 50 | 1 | RLM-10 | 39 | 89.7 | 79.5 to 97.4 | 0 |  |
| 39 out-of-scope questions | 50 | 3 | RLM-10 | 39 | 94.9 | 87.2 to 100.0 | 0 |  |
| 39 out-of-scope questions | 50 | pooled | RLM-20 | 39 | 90.6 | 84.6 to 95.7 | 0 |  |
| 39 out-of-scope questions | 50 | 0 | RLM-20 | 39 | 97.4 | 92.3 to 100.0 | 0 |  |
| 39 out-of-scope questions | 50 | 1 | RLM-20 | 39 | 87.2 | 76.9 to 97.4 | 0 |  |
| 39 out-of-scope questions | 50 | 3 | RLM-20 | 39 | 87.2 | 76.9 to 97.4 | 0 |  |

The 5 false-premise questions: Supplementary Figure 4c.
