# Supplementary Table answer counts | Answer counts by experiment

Stored answers per experiment, counted from the run records (S492's unit: one generation row, whether or not a judge scored it). Provisional: a blank row is not counted yet (none), and counts rise as frozen copies land.

| Row | Experiment | Design | Answers |
|---|---|---|---|
| 1 | Model selection | not re-run | 408 |
| 2 | Retrieval optimization | not re-run | 2336 |
| 3 | Generation strategies | 6 strategies x 135 questions | 2430 |
| 4 | Matched-budget arm | 1 arm (single pass given more passages) x 135 | 405 |
| 5 | Zhang RLM at caps 5, 10 and 20 | 3 caps x 135 questions | 1215 |
| 6 | Retrieval depth | 10 depths x 86 questions (gemini) | 2580 |
| 7 | Retrieval depth, local models | 4 local models (devstral, gemma3, qwen3-coder, qwen3-coder-next) x 6 caps (1, 3, 5, 7, 20, 50) x 15 questions | 360 |
| 8 | Zhang RLM at the depth caps | 7 caps (1 2 3 7 15 30 50) x 86 questions | 1806 |
| 9 | Corpus scaling | 12 indexes x 6 strategies x questions per size | 18162 |
| 10 | Flat wide call | 3 indexes x 1 call at a fixed passage count | 585 |
| 11 | Short-passage single pass | single pass with each passage cut to its first 800 characters | 225 |
| 12 | Pipeline ablation | 8 set-ups x 135 questions | 1373 |
| 13 | No retrieval and naive RAG | 2 baselines x 135 questions | 810 |
| 14 | Always distil (stress) | 2 set-ups x 135 questions | 450 |
| 15 | Component benchmarks | 6 models x 832 benchmark items | 6656 |
| 16 | Distiller intervention | 2 prompts x 6 models x 97 items | 1164 |
| 17 | Code generation | 121 model and strategy set-ups x 20 operations | 2420 |
| 18 | Strategy replication | 4 generators x 6 strategies x 135 questions | 7054 |
| 19 | Plant-science reuse demonstration | Figure 3's six strategies x 5 questions on 5 papers | 90 |
| 20 | RLM ablation | 3 arms (control, search off, gate off) x 86 questions | 774 |
| 21 | RLM ablation, local generators | 3 arms x 2 generators x 46 questions | 276 |
| 22 | Judge with evidence | 4 arms (no source, own papers, unrelated papers, repeat) x 366 answers (S18f, key v2.5) | 0 |
| | Total counted | | 51579 |
