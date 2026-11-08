# S404 plan: 1500 answers for the extended judge calibration (2026-10-12T21:57:30)

Key <repo>/data/ground_truth_v2/all_v2_4.json (sha256 5d8362ae931d), v1-format <repo>/data/ground_truth_v2/ground_truth_v2_4_as_v1.json (e971de522df6). Seed 20261012. Citation count: text. BGE-M3 on cpu.

## Rule when this plan was written

The judge with the highest composite in table A (the answers all four judges scored) is selected if the 95% interval of its difference from every other judge, over 2,000 paired bootstrap resamples of those answers (seed 20261012), excludes 0. Otherwise the result is a tie among it and every judge whose interval with it includes 0, and D8 is decided among the tied judges by the O50 repeatability results (S377).

The judging does not read the rule; the analysis says whether the rule it applies is this one.

## Gates

- A1 S376b's composites, intervals and differences from qwen3-coder reproduced for the four judges, largest difference 1.1e-16
- G1 S376b's reference measures on its 107 answers reproduced, largest differences {"concept_recall": 0.0, "cite_composite": 0.0, "semantic_similarity": 0.0} (similarity recomputed on 107 of the 107)
- G2 S141's v2.4 similarity equals this script's on 224 of the 224 drawn S141 campaign answers (0 have no S141 row to compare), largest difference 1.4e-06
- G3 S403's two intervals reproduced (power table below)

## Sample size

| Pair | 95% interval on the 107 | sd | n for 80% power at 0.03 | half-width at N | power at N |
|---|---|---:|---:|---:|---:|
| devstral-small-2:24b - qwen3.8:27b-mlx | -0.0932 to +0.0295 | 0.0317 | 941 | 0.0166 | 0.943 |
| devstral-small-2:24b - ministral-3:14b | -0.0732 to +0.0147 | 0.0223 | 464 | 0.0117 | 0.999 |
| devstral-small-2:24b - qwen3-coder:latest | -0.0328 to +0.1235 | 0.0399 | 1487 | 0.0209 | 0.803 |
| qwen3.8:27b-mlx - ministral-3:14b | -0.0447 to +0.0482 | 0.0241 | 540 | 0.0126 | 0.997 |
| qwen3.8:27b-mlx - qwen3-coder:latest | +0.0001 to +0.1507 | 0.0385 | 1380 | 0.0201 | 0.832 |
| ministral-3:14b - qwen3-coder:latest | +0.0088 to +0.1399 | 0.0338 | 1068 | 0.0177 | 0.913 |

## Frame, by file

| Experiment and file | Kept | Refused (reason count) |
|---|---:|---|
| Component benchmark: synthesizer (exp07)|exp07_bench_synthesizer_devstral-small-2-24b.json | 78 | d7_question_changed 2, out_of_domain 20 |
| Component benchmark: synthesizer (exp07)|exp07_bench_synthesizer_gemini-3-flash-preview.json | 78 | d7_question_changed 2, out_of_domain 20 |
| Component benchmark: synthesizer (exp07)|exp07_bench_synthesizer_gemini-3-flash-preview_think-on.json | 12 | d7_question_changed 2, out_of_domain 20, duplicate_answer 66 |
| Component benchmark: synthesizer (exp07)|exp07_bench_synthesizer_gemma3-27b.json | 78 | d7_question_changed 2, out_of_domain 20 |
| Component benchmark: synthesizer (exp07)|exp07_bench_synthesizer_gpt-oss-20b.json | 74 | no_answer 4, d7_question_changed 2, out_of_domain 20 |
| Component benchmark: synthesizer (exp07)|exp07_bench_synthesizer_gpt-oss-20b_think-high.json | 46 | no_answer 30, d7_question_changed 2, out_of_domain 20, duplicate_answer 2 |
| Component benchmark: synthesizer (exp07)|exp07_bench_synthesizer_gpt-oss-20b_think-low.json | 77 | d7_question_changed 2, out_of_domain 20, duplicate_answer 1 |
| Component benchmark: synthesizer (exp07)|exp07_bench_synthesizer_gpt-oss-20b_think-medium.json | 69 | no_answer 4, d7_question_changed 2, out_of_domain 20, duplicate_answer 5 |
| Component benchmark: synthesizer (exp07)|exp07_bench_synthesizer_llama3-8b.json | 78 | d7_question_changed 2, out_of_domain 20 |
| Component benchmark: synthesizer (exp07)|exp07_bench_synthesizer_nemotron-3-nano-30b.json | 78 | d7_question_changed 2, out_of_domain 20 |
| Component benchmark: synthesizer (exp07)|exp07_bench_synthesizer_olmo-3-32b.json | 27 | no_answer 51, d7_question_changed 2, out_of_domain 20 |
| Component benchmark: synthesizer (exp07)|exp07_bench_synthesizer_qwen3-coder-latest.json | 78 | d7_question_changed 2, out_of_domain 20 |
| Component benchmark: synthesizer (exp07)|exp07_bench_synthesizer_qwen3.5-122b.json | 78 | d7_question_changed 2, out_of_domain 20 |
| Component benchmark: synthesizer (exp07)|exp07_bench_synthesizer_qwen3.5-122b_think-on.json | 78 | d7_question_changed 2, out_of_domain 20 |
| Component benchmark: synthesizer (exp07)|exp07_bench_synthesizer_qwen3.5-35b.json | 78 | d7_question_changed 2, out_of_domain 20 |
| Component benchmark: synthesizer (exp07)|exp07_bench_synthesizer_qwen3.5-35b_think-on.json | 78 | d7_question_changed 2, out_of_domain 20 |
| Corpus scaling (exp05)|exp05_scaling_latest.json | 6098 | out_of_domain 3589, d7_question_changed 126, encoder_limit 41, duplicate_answer 40 |
| Generation strategies (exp04)|exp04_generation_latest.json | 510 | d7_question_changed 12, out_of_domain 300, duplicate_answer 3, encoder_limit 3 |
| Generator selection (exp00 rlm_models)|exp00_rlm_models_latest.json | 212 | no_answer 27, duplicate_answer 1 |
| Naive RAG baseline|analysis_naive_baseline_latest.json | 86 | d7_question_changed 2, out_of_domain 50 |
| Orchestration (exp06)|exp06_orchestration_ablation_latest.json | 258 | d7_question_changed 8, out_of_domain 200, duplicate_answer 86 |
| Retrieval depth (exp09)|exp09_depth_sweep_devstral-small-2-24b_merged.json | 0 | no_answer 75 |
| Retrieval depth (exp09)|exp09_depth_sweep_gemini-3-flash-preview_merged.json | 766 | no_answer 53, d7_question_changed 20, duplicate_answer 1 |
| Retrieval depth (exp09)|exp09_depth_sweep_gemma3-27b_merged.json | 0 | no_answer 75 |
| Retrieval depth (exp09)|exp09_depth_sweep_glm-4.7-flash_merged.json | 0 | no_answer 75 |
| Retrieval depth (exp09)|exp09_depth_sweep_gpt-oss_20b_merged.json | 33 | no_answer 101, duplicate_answer 1 |
| Retrieval depth (exp09)|exp09_depth_sweep_llama3-8b_merged.json | 57 | no_answer 18 |
| Retrieval depth (exp09)|exp09_depth_sweep_nemotron-3-nano_30b_merged.json | 135 | none |
| Retrieval depth (exp09)|exp09_depth_sweep_qwen3-coder-next_q4_K_M_merged.json | 134 | no_answer 1 |
| Retrieval depth (exp09)|exp09_depth_sweep_qwen3-coder_latest_merged.json | 135 | no_answer 2 |
| S141 campaign (strategy replication, multi-generator)|anthropic_claude-haiku-4-5__draw1 | 507 | d7_question_changed 12, out_of_domain 300, no_answer 9 |
| S141 campaign (strategy replication, multi-generator)|anthropic_claude-haiku-4-5__draw2 | 488 | d7_question_changed 12, out_of_domain 300, no_answer 5, duplicate_answer 21, encoder_limit 2 |
| S141 campaign (strategy replication, multi-generator)|anthropic_claude-haiku-4-5__draw3 | 487 | d7_question_changed 12, out_of_domain 300, no_answer 9, duplicate_answer 19, encoder_limit 1 |
| S141 campaign (strategy replication, multi-generator)|gemini_gemini-3-flash-preview__draw1 | 505 | d7_question_changed 12, out_of_domain 300, no_answer 5, duplicate_answer 2, encoder_limit 4 |
| S141 campaign (strategy replication, multi-generator)|gemini_gemini-3-flash-preview__draw1__thinkoff | 86 | d7_question_changed 2, out_of_domain 50 |
| S141 campaign (strategy replication, multi-generator)|gemini_gemini-3-flash-preview__draw2 | 504 | d7_question_changed 12, out_of_domain 300, no_answer 4, duplicate_answer 3, encoder_limit 5 |
| S141 campaign (strategy replication, multi-generator)|gemini_gemini-3-flash-preview__draw3 | 506 | d7_question_changed 12, out_of_domain 300, no_answer 3, duplicate_answer 3, encoder_limit 4 |
| S141 campaign (strategy replication, multi-generator)|ollama_gemma3_27b__draw1 | 410 | d7_question_changed 12, out_of_domain 300, duplicate_answer 106 |
| S141 campaign (strategy replication, multi-generator)|ollama_gemma3_27b__draw2 | 371 | d7_question_changed 12, out_of_domain 300, no_answer 2, duplicate_answer 143 |
| S141 campaign (strategy replication, multi-generator)|ollama_gemma3_27b__draw3 | 326 | d7_question_changed 12, out_of_domain 300, no_answer 1, duplicate_answer 189 |
| S141 campaign (strategy replication, multi-generator)|ollama_glm-4.7-flash_latest__draw1 | 110 | d7_question_changed 12, out_of_domain 300, no_answer 6, duplicate_answer 399, encoder_limit 1 |
| S141 campaign (strategy replication, multi-generator)|ollama_glm-4.7-flash_latest__draw1__thinkoff | 445 | d7_question_changed 12, out_of_domain 300, no_answer 5, encoder_limit 2, duplicate_answer 64 |
| S141 campaign (strategy replication, multi-generator)|ollama_glm-4.7-flash_latest__draw2 | 365 | d7_question_changed 12, out_of_domain 300, no_answer 2, duplicate_answer 149 |
| S141 campaign (strategy replication, multi-generator)|ollama_glm-4.7-flash_latest__draw3 | 330 | d7_question_changed 12, out_of_domain 300, no_answer 5, duplicate_answer 179, encoder_limit 2 |
| S141 campaign (strategy replication, multi-generator)|ollama_nemotron-3-nano_30b__draw1 | 431 | d7_question_changed 12, out_of_domain 300, no_answer 8, duplicate_answer 77 |
| S141 campaign (strategy replication, multi-generator)|ollama_nemotron-3-nano_30b__draw2 | 397 | d7_question_changed 12, out_of_domain 300, no_answer 4, duplicate_answer 115 |
| S141 campaign (strategy replication, multi-generator)|ollama_nemotron-3-nano_30b__draw3 | 391 | d7_question_changed 12, out_of_domain 300, no_answer 5, duplicate_answer 120 |
| S141 mini arm (step 4.3, s50)|mini__anthropic_claude-haiku-4-5 | 378 | no_answer 2, d7_question_changed 10, out_of_domain 100, encoder_limit 1, duplicate_answer 9 |
| S141 mini arm (step 4.3, s50)|mini__gemini_gemini-3-flash-preview | 385 | d7_question_changed 10, no_answer 1, out_of_domain 100, duplicate_answer 4 |
| S141 mini arm (step 4.3, s50)|mini__ollama_gemma3_27b | 337 | d7_question_changed 10, out_of_domain 100, duplicate_answer 53 |
| S141 mini arm (step 4.3, s50)|mini__ollama_glm-4.7-flash_latest | 316 | no_answer 14, d7_question_changed 10, out_of_domain 100, encoder_limit 1, duplicate_answer 59 |
| S141 mini arm (step 4.3, s50)|mini__ollama_nemotron-3-nano_30b | 317 | no_answer 13, d7_question_changed 10, out_of_domain 100, duplicate_answer 60 |
| S141 timing (step 4.4)|timing__anthropic_claude-haiku-4-5 | 54 | duplicate_answer 6 |
| S141 timing (step 4.4)|timing__gemini_gemini-3-flash-preview | 57 | no_answer 1, encoder_limit 2 |
| S141 timing (step 4.4)|timing__ollama_gemma3_27b | 19 | duplicate_answer 41 |
| S141 timing (step 4.4)|timing__ollama_glm-4.7-flash_latest | 26 | no_answer 1, duplicate_answer 32, encoder_limit 1 |
| S141 timing (step 4.4)|timing__ollama_nemotron-3-nano_30b | 9 | duplicate_answer 51 |
| S314 verified_pass rerun (exp05 indexes)|S314_verified_pass_raw.jsonl | 1045 | out_of_domain 600, d7_question_changed 21, duplicate_answer 14 |
| S357 Gemini paired arm|results.json | 179 | encoder_limit 1 |
| Strategy replication (published)|reviewer_strategy_replication.json | 255 | d7_question_changed 6, out_of_domain 150, duplicate_answer 1, encoder_limit 2 |
| Strategy replication (published)|reviewer_strategy_replication_122b.json | 257 | d7_question_changed 6, out_of_domain 150, no_answer 1 |

Frame 19802 answers on 195 questions.

## Strata

| Generator / strategy | Frame | Drawn |
|---|---:|---:|
| anthropic::claude-haiku-4-5 / multi_hop | 260 | 20 |
| anthropic::claude-haiku-4-5 / rlm | 970 | 72 |
| anthropic::claude-haiku-4-5 / single_pass | 434 | 33 |
| anthropic::claude-haiku-4-5 / verified_pass | 250 | 19 |
| gemini::gemini-3-flash-preview / multi_hop | 1346 | 100 |
| gemini::gemini-3-flash-preview / naive_rag | 172 | 14 |
| gemini::gemini-3-flash-preview / no_retrieval | 86 | 7 |
| gemini::gemini-3-flash-preview / orchestrator | 86 | 7 |
| gemini::gemini-3-flash-preview / rlm | 5252 | 386 |
| gemini::gemini-3-flash-preview / single_pass | 1602 | 118 |
| gemini::gemini-3-flash-preview / synthesizer | 90 | 8 |
| gemini::gemini-3-flash-preview / verified_pass | 2455 | 181 |
| ollama::deepseek-r1:70b / rlm | 8 | 2 |
| ollama::devstral-small-2:24b / rlm | 15 | 2 |
| ollama::devstral-small-2:24b / synthesizer | 78 | 7 |
| ollama::gemma3:27b / multi_hop | 236 | 18 |
| ollama::gemma3:27b / rlm | 650 | 49 |
| ollama::gemma3:27b / single_pass | 362 | 28 |
| ollama::gemma3:27b / synthesizer | 78 | 7 |
| ollama::gemma3:27b / verified_pass | 230 | 18 |
| ollama::glm-4.7-flash:latest / multi_hop | 239 | 18 |
| ollama::glm-4.7-flash:latest / rlm | 673 | 50 |
| ollama::glm-4.7-flash:latest / single_pass | 389 | 29 |
| ollama::glm-4.7-flash:latest / verified_pass | 306 | 23 |
| ollama::gpt-oss:120b / rlm | 15 | 2 |
| ollama::gpt-oss:20b / rlm | 35 | 4 |
| ollama::gpt-oss:20b / synthesizer | 266 | 20 |
| ollama::llama3:8b / rlm | 57 | 5 |
| ollama::llama3:8b / synthesizer | 78 | 7 |
| ollama::ministral-3:14b / rlm | 12 | 2 |
| ollama::ministral-3:8b / rlm | 12 | 2 |
| ollama::nemotron-3-nano:30b / multi_hop | 254 | 20 |
| ollama::nemotron-3-nano:30b / rlm | 791 | 59 |
| ollama::nemotron-3-nano:30b / single_pass | 392 | 30 |
| ollama::nemotron-3-nano:30b / synthesizer | 78 | 7 |
| ollama::nemotron-3-nano:30b / verified_pass | 258 | 20 |
| ollama::olmo-3:32b / rlm | 15 | 2 |
| ollama::olmo-3:32b / synthesizer | 27 | 3 |
| ollama::qwen3-coder-next:q4_K_M / rlm | 149 | 12 |
| ollama::qwen3-coder:latest / rlm | 236 | 18 |
| ollama::qwen3-coder:latest / single_pass | 84 | 7 |
| ollama::qwen3-coder:latest / synthesizer | 78 | 7 |
| ollama::qwen3-coder:latest / verified_pass | 85 | 7 |
| ollama::qwen3.5:122b / rlm | 99 | 8 |
| ollama::qwen3.5:122b / single_pass | 86 | 7 |
| ollama::qwen3.5:122b / synthesizer | 156 | 12 |
| ollama::qwen3.5:122b / verified_pass | 86 | 7 |
| ollama::qwen3.5:35b / rlm | 15 | 2 |
| ollama::qwen3.5:35b / synthesizer | 156 | 12 |
| ollama::qwen3.5:9b / rlm | 15 | 2 |

## Sample spread

| Generator | Frame share | Drawn |
|---|---:|---:|
| gemini::gemini-3-flash-preview | 0.560 | 821 |
| anthropic::claude-haiku-4-5 | 0.097 | 144 |
| ollama::nemotron-3-nano:30b | 0.090 | 136 |
| ollama::glm-4.7-flash:latest | 0.081 | 120 |
| ollama::gemma3:27b | 0.079 | 120 |
| ollama::qwen3-coder:latest | 0.024 | 39 |
| ollama::qwen3.5:122b | 0.022 | 34 |
| ollama::gpt-oss:20b | 0.015 | 24 |
| ollama::qwen3.5:35b | 0.009 | 14 |
| ollama::qwen3-coder-next:q4_K_M | 0.008 | 12 |
| ollama::llama3:8b | 0.007 | 12 |
| ollama::devstral-small-2:24b | 0.005 | 9 |
| ollama::olmo-3:32b | 0.002 | 5 |
| ollama::gpt-oss:120b | 0.001 | 2 |
| ollama::qwen3.5:9b | 0.001 | 2 |
| ollama::ministral-3:14b | 0.001 | 2 |
| ollama::ministral-3:8b | 0.001 | 2 |
| ollama::deepseek-r1:70b | 0.000 | 2 |

| Strategy | Frame share | Drawn |
|---|---:|---:|
| rlm | 0.455 | 679 |
| verified_pass | 0.185 | 275 |
| single_pass | 0.169 | 252 |
| multi_hop | 0.118 | 176 |
| synthesizer | 0.055 | 90 |
| naive_rag | 0.009 | 14 |
| no_retrieval | 0.004 | 7 |
| orchestrator | 0.004 | 7 |

Questions: 195 of 195 in the frame have at least one drawn answer. Answers per question in the sample: 7 answers on 60 questions, 8 answers on 135 questions (in the frame a question has 26 to 283 answers, median 31).

The draw keeps the frame's mix of generators and strategies and evens the questions out; it does not keep the frame's mix of experiments:

| Experiment | Frame | Frame share | Drawn | Drawn share |
|---|---:|---:|---:|---:|
| S141 campaign (strategy replication, multi-generator) | 6659 | 0.336 | 224 | 0.149 |
| Corpus scaling (exp05) | 6098 | 0.308 | 530 | 0.353 |
| S141 mini arm (step 4.3, s50) | 1733 | 0.088 | 393 | 0.262 |
| Retrieval depth (exp09) | 1260 | 0.064 | 52 | 0.035 |
| Component benchmark: synthesizer (exp07) | 1085 | 0.055 | 90 | 0.060 |
| S314 verified_pass rerun (exp05 indexes) | 1045 | 0.053 | 89 | 0.059 |
| Strategy replication (published) | 512 | 0.026 | 53 | 0.035 |
| Generation strategies (exp04) | 510 | 0.026 | 14 | 0.009 |
| Orchestration (exp06) | 258 | 0.013 | 20 | 0.013 |
| Generator selection (exp00 rlm_models) | 212 | 0.011 | 20 | 0.013 |
| S357 Gemini paired arm | 179 | 0.009 | 6 | 0.004 |
| S141 timing (step 4.4) | 165 | 0.008 | 1 | 0.001 |
| Naive RAG baseline | 86 | 0.004 | 8 | 0.005 |

Drawn answers that carry the RLM's note "Analysis reached turn limit": 22; drawn answers under 60 characters: 0. They are answers of the study, which the main judge also scores, so they stay in the frame.

## Reference measures on the sample

| Measure | Mean | sd | Min | Max |
|---|---:|---:|---:|---:|
| concept_recall | 0.282 | 0.303 | 0.000 | 1.000 |
| semantic_similarity | 0.755 | 0.114 | 0.305 | 0.972 |
| cite_composite | 0.714 | 0.338 | 0.000 | 1.000 |

## Expected judging time

Answer length: mean 2108 characters (S376's 107: 3924), median 1423, max 21771. S377 measured devstral at 8.1 answers per minute on one idle server (S376's 107 answers, <repo>/findings/recompute/S377_devstral-small-2_24b_repeatability.md); at that rate 1500 answers take 186 min for devstral on one server. Its spread pass, four servers with one request each, judged 9.2 answers per minute in total: servers on one machine share its GPU, so the estimate for four judges is the sum of their single-server times. The other three judges' speeds on an idle server are O50's to measure (S377); none is read here.

Timing here: G1 similarity 70.7 s, the sample's reference measures 650.7 s, total 733.8 s.
