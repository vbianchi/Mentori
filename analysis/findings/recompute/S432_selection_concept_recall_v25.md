# S432 --v25: concept recall of the generator-selection answers (phase 2) on answer key v2.5

Computed by scripts/S432_selection_concept_recall_v24.py (sha256 3e76906959d9) with `uv run python scripts/S432_selection_concept_recall_v24.py --v25`, rulings page 6 Nov, GM2: O1 (run S432 on key v2.5). Key data/ground_truth_v2/ground_truth_v2_5_as_v1.json (sha256 a42161841980, version 2.5). Matcher: D181: S505's loose matcher with the question rule, Q-need, reading (b) (scripts/S505_question_aware_matcher.py recall_q(text, concepts, question, 'loose', 'need', 'b')): content words of a concept that also occur in its question do not count, the loose need rule applies to the words left, a concept made only of question words leaves the denominator; key v2.5. 120 rows, 107 completed answers, 13 failed generations counted as 0 (D16). The 15 questions hold 88 concepts on v2.5 (1 to 9 each); 10 of them have other concepts than on v2.4. Every v2.4 gate of this script passed before a v2.5 value was computed. No model is called.

## Mean concept recall per model, failed generations as 0

| Model | Completed of its questions | D181: loose with the question rule (Q-need, reading b) | Loose, as written, on the v2.5 concepts | Exact, substring test, on the v2.5 concepts |
|---|---:|---:|---:|---:|
| gemini::gemini-3-flash-preview | 15 of 15 | 0.7876 | 0.8209 | 0.3778 |
| ollama::deepseek-r1:70b | 8 of 15 | 0.2250 | 0.2250 | 0.0944 |
| ollama::devstral-small-2:24b | 14 of 15 | 0.4440 | 0.5524 | 0.2361 |
| ollama::gemma3:27b | 15 of 15 | 0.6077 | 0.6234 | 0.2438 |
| ollama::gpt-oss:120b | 15 of 15 | 0.4667 | 0.4750 | 0.0417 |
| ollama::nemotron-3-nano:30b | 12 of 15 | 0.3915 | 0.3999 | 0.2336 |
| ollama::qwen3-coder-next:q4_K_M | 15 of 15 | 0.4792 | 0.5638 | 0.2167 |
| ollama::qwen3-coder:latest | 13 of 15 | 0.4438 | 0.4688 | 0.2530 |

## gemini::gemini-3-flash-preview against the local models

| Reading | Mean of gemini::gemini-3-flash-preview | Largest local mean | Local model or models with it | Difference, points | gemini::gemini-3-flash-preview above every other model |
|---|---:|---:|---|---:|---|
| D181: loose with the question rule (Q-need, reading b) | 0.7876 | 0.6077 | ollama::gemma3:27b | 17.99 | yes |
| Loose, as written, on the v2.5 concepts | 0.8209 | 0.6234 | ollama::gemma3:27b | 19.75 | yes |
| Exact, substring test, on the v2.5 concepts | 0.3778 | 0.2530 | ollama::qwen3-coder:latest | 12.47 | yes |
| v2.4, loose as written (this script's v2.4 file) | 0.7500 | 0.6000 | ollama::gemma3:27b | 15.00 | |

## Gates passed before anything was written

- G0a: the sha256 of 4 deposit files (exp00_phase2_latest.json, exp00_objective_latest.json, exp_00_objective_metrics.py, exp_06_depth_sweep.py) is the one data/upstream/MANIFEST.sha256 lists: 4 of 4
- G0b: the v1 key data/replication_inputs/ground_truth.json (sha256 37d731f9f152) is the source the v1-format key names: True; the two v2.4 key files (sha256 e971de522df6 and 5d8362ae931d) are the ones the loader's checked context holds: True and True
- G0c: the text of compute_concept_recall in recovered_harness/tests/experiments_v4/exp_v4_0_objective_metrics.py (sha256 66f2c6cbe94e) and in deposit/publication/scripts/exp_00_objective_metrics.py (sha256 66f2c6cbe94e) is the same: True
- G1: 8 models by 15 questions, 120 rows, 107 completed answers and 13 failed generations; one row per model and question: True; the models are the header's model_ids: True; the questions are the header's question_ids: True; n_models and n_questions are their numbers: True; the counts are KNOWN_DESIGN: True; one model is gemini::gemini-3-flash-preview and the others start with ollama::: True; the objective file holds the same pairs in the same order: True; and the same completed flags: True; the completed answers are the keys of S376's reference_measures, each with its model as generator: True
- G2a: the registry's two derivations (scripts/s323/r03a_methods.py, called through its entries) give 0.6941266666666667 and 14.380666666666663; findings/recompute/S323_docx_numbers.json records 0.694127 and 14.380667 with the verdicts OK and OK; rounded half up the two derived values print as 0.69 and 14.4, and the Methods print 0.69 and 14.4
- G2b: this script's summary of the stored values against the registry's: the mean of every model: True; the mean of gemini-3-flash: True; the difference: True; the values typed in KNOWN_V1: True (gemini-3-flash 0.6941, largest local mean 0.5503 of ollama::qwen3-coder-next:q4_K_M, difference 14.38 points)
- G3: 120 of 120 stored concept recalls of deposit/publication/results/exp00_objective_latest.json reproduced from the phase 2 answers with the deposited scorer on the v1 key at four decimals, a failed generation as 0.0
- G4a: of the 15 questions, 0 are among the 6 D7 questions of the key file and 15 are of the group answerable
- G4b: the expected_concepts of data/ground_truth_v2/ground_truth_v2_4_as_v1.json are the key_concepts phrases of data/ground_truth_v2/all_v2_4.json for 15 of the 15 questions
- G5a: concept_match_loose.spec_failures() returns 0 failures over its 25 rule cases and its stop-word checks
- G5b: on the 107 completed answers: the concepts the loose matcher marks found by its rule 1 give the depth sweep's function on 107; the single-concept decisions of the deposited scorer give its value on the whole list on 107; the detail of the loose matcher gives its value on 107; the loose value is not below the substring value on 107
- G6: the deposited scorer on the v1-format key's concepts equals the concept_recall of findings/recompute/S376_calibration_analysis.json on 107 of 107 completed answers (largest difference 0.0e+00)
- G7: d181_concept_recall.spec_failures() returns 0 failures
- G8: score() with an empty question on the v2.4 concepts gives this run's loose value on 107 of 107 completed answers
- G9: 107 of 107 completed answers have at least one counted concept on v2.5
