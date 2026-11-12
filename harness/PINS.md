# Which code ran which run

Built by `scripts/S609_release_harness.py` from Mentori-reanalysis `7c02e422`. The harness in this folder
is the code at that one commit. The runs of the paper used earlier commits: there is no single commit that
ran every experiment. This file lists what the records themselves say.

## The commit each frozen record names

Call records written since D92 Q199 carry `code_commit` and `code_dirty`
(`experiments/runner/ollama_client.py`, `code_version`). Earlier records carry none. Counted over every
`.jsonl` line of each run folder in the 14 frozen tars of the Zenodo record (a line can be a call or an
answer that embeds its calls, so the counts are occurrences, not calls).

| tar | run folder | lines | code_commit (code_dirty): occurrences |
|---|---|---|---|
| answer_lengths_20261020 | `answer_lengths_20261020/G1/runs/exp_01__multi_hop__exp_v4_s20_n0` | 407 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G1/runs/exp_01__rlm_10__exp_v4_s20_n0` | 408 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G1/runs/exp_01__rlm_20__exp_v4_s20_n0` | 406 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G1/runs/exp_01__rlm_5__exp_v4_s20_n0` | 407 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G1/runs/exp_01__single_pass__exp_v4_s20_n0` | 406 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G1/runs/exp_01__verified_pass__exp_v4_s20_n0` | 406 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G1R15/runs/exp_01__rlm_10__exp_v4_s20_n0` | 409 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G1R15/runs/exp_01__rlm_20__exp_v4_s20_n0` | 407 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G1R15/runs/exp_01__rlm_5__exp_v4_s20_n0` | 408 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G1R15/runs/exp_01__verified_pass__exp_v4_s20_n0` | 407 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G2/runs/exp_01__matched_budget__exp_v4_s20_n0` | 406 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s10_n0` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s10_n1` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s10_n3` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s20_n0` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s20_n1` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s20_n3` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s50_n0` | 245 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s50_n1` | 245 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s50_n3` | 245 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s5_n0` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s5_n1` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s5_n3` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s10_n0` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s10_n1` | 137 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s10_n3` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s20_n0` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s20_n1` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s20_n3` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s50_n0` | 245 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s50_n1` | 246 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s50_n3` | 245 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s5_n0` | 137 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s5_n1` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s5_n3` | 137 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s10_n0` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s10_n1` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s10_n3` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s20_n0` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s20_n1` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s20_n3` | 137 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s50_n0` | 245 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s50_n1` | 245 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s50_n3` | 245 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s5_n0` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s5_n1` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s5_n3` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s10_n0` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s10_n1` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s10_n3` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s20_n0` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s20_n1` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s20_n3` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s50_n0` | 245 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s50_n1` | 245 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s50_n3` | 245 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s5_n0` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s5_n1` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s5_n3` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__single_pass__exp_v4_s10_n0` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__single_pass__exp_v4_s10_n1` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__single_pass__exp_v4_s10_n3` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__single_pass__exp_v4_s20_n0` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__single_pass__exp_v4_s20_n1` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__single_pass__exp_v4_s20_n3` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__single_pass__exp_v4_s50_n0` | 245 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__single_pass__exp_v4_s50_n1` | 245 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__single_pass__exp_v4_s50_n3` | 245 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__single_pass__exp_v4_s5_n0` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__single_pass__exp_v4_s5_n1` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__single_pass__exp_v4_s5_n3` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s10_n0` | 102 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s10_n1` | 118 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s10_n3` | 85 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s20_n0` | 137 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s20_n1` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s20_n3` | 136 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s50_n0` | 96 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s50_n1` | 73 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s50_n3` | 73 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s5_n0` | 79 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s5_n1` | 96 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G4/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s5_n3` | 61 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G6/runs/b4_rlm_ref__cap10__all135` | 405 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G6/runs/b4_rlm_ref__cap20__all135` | 405 | none recorded |
| answer_lengths_20261020 | `answer_lengths_20261020/G6/runs/b4_rlm_ref__cap5__all135` | 405 | none recorded |
| count_records_20261106 | `count_records_20261106/g10/runs/exp_01__matched_budget__exp_v4_s20_n0` | 136 | none recorded |
| count_records_20261106 | `count_records_20261106/g10/runs/exp_01__matched_budget__exp_v4_s20_n3` | 227 | none recorded |
| count_records_20261106 | `count_records_20261106/g10/runs/exp_01__matched_budget__exp_v4_s50_n3` | 227 | none recorded |
| count_records_20261106 | `count_records_20261106/g11/runs/exp_01__single_pass_cut800__exp_v4_s20_n0` | 227 | none recorded |
| count_records_20261106 | `count_records_20261106/g19/runs/b4_rlm_ref_gemma3__cap10__d239a46` | 606 | `4a4e99bf` (false): 560 |
| count_records_20261106 | `count_records_20261106/g19/runs/exp_01__rlm_10_nogate__exp_v4_s20_n0+gemma3-27b` | 47 | none recorded |
| count_records_20261106 | `count_records_20261106/g19/runs/exp_01__rlm_10_nosearch__exp_v4_s20_n0+gemma3-27b` | 48 | none recorded |
| count_records_20261106 | `count_records_20261106/t2/claude-haiku-4-5/runs/exp_01__multi_hop__exp_v4_s20_n0+claude-haiku-4-5` | 407 | none recorded |
| count_records_20261106 | `count_records_20261106/t2/claude-haiku-4-5/runs/exp_01__rlm_10__exp_v4_s20_n0+claude-haiku-4-5` | 408 | none recorded |
| count_records_20261106 | `count_records_20261106/t2/claude-haiku-4-5/runs/exp_01__rlm_20__exp_v4_s20_n0+claude-haiku-4-5` | 408 | none recorded |
| count_records_20261106 | `count_records_20261106/t2/claude-haiku-4-5/runs/exp_01__rlm_5__exp_v4_s20_n0+claude-haiku-4-5` | 407 | none recorded |
| count_records_20261106 | `count_records_20261106/t2/claude-haiku-4-5/runs/exp_01__single_pass__exp_v4_s20_n0+claude-haiku-4-5` | 407 | none recorded |
| count_records_20261106 | `count_records_20261106/t2/claude-haiku-4-5/runs/exp_01__verified_pass__exp_v4_s20_n0+claude-haiku-4-5` | 410 | none recorded |
| count_records_20261106 | `count_records_20261106/t2/gemini-2.5-pro/runs/exp_01__multi_hop__exp_v4_s20_n0+gemini-2.5-pro` | 227 | none recorded |
| count_records_20261106 | `count_records_20261106/t2/gemini-2.5-pro/runs/exp_01__rlm_10__exp_v4_s20_n0+gemini-2.5-pro` | 227 | none recorded |
| count_records_20261106 | `count_records_20261106/t2/gemini-2.5-pro/runs/exp_01__rlm_20__exp_v4_s20_n0+gemini-2.5-pro` | 227 | none recorded |
| count_records_20261106 | `count_records_20261106/t2/gemini-2.5-pro/runs/exp_01__rlm_5__exp_v4_s20_n0+gemini-2.5-pro` | 227 | none recorded |
| count_records_20261106 | `count_records_20261106/t2/gemini-2.5-pro/runs/exp_01__single_pass__exp_v4_s20_n0+gemini-2.5-pro` | 227 | none recorded |
| count_records_20261106 | `count_records_20261106/t2/gemini-2.5-pro/runs/exp_01__verified_pass__exp_v4_s20_n0+gemini-2.5-pro` | 227 | none recorded |
| count_records_20261106 | `count_records_20261106/t2/gemma3-27b/runs/exp_01__multi_hop__exp_v4_s20_n0+gemma3-27b` | 408 | none recorded |
| count_records_20261106 | `count_records_20261106/t2/gemma3-27b/runs/exp_01__rlm_10__exp_v4_s20_n0+gemma3-27b` | 138 | none recorded |
| count_records_20261106 | `count_records_20261106/t2/gemma3-27b/runs/exp_01__rlm_20__exp_v4_s20_n0+gemma3-27b` | 139 | none recorded |
| count_records_20261106 | `count_records_20261106/t2/gemma3-27b/runs/exp_01__rlm_5__exp_v4_s20_n0+gemma3-27b` | 139 | none recorded |
| count_records_20261106 | `count_records_20261106/t2/gemma3-27b/runs/exp_01__single_pass__exp_v4_s20_n0+gemma3-27b` | 407 | none recorded |
| count_records_20261106 | `count_records_20261106/t2/gemma3-27b/runs/exp_01__verified_pass__exp_v4_s20_n0+gemma3-27b` | 407 | none recorded |
| count_records_20261106 | `count_records_20261106/t2/qwen3-coder-30b/runs/exp_01__multi_hop__exp_v4_s20_n0+qwen3-coder-30b` | 408 | none recorded |
| count_records_20261106 | `count_records_20261106/t2/qwen3-coder-30b/runs/exp_01__rlm_10__exp_v4_s20_n0+qwen3-coder-30b` | 137 | none recorded |
| count_records_20261106 | `count_records_20261106/t2/qwen3-coder-30b/runs/exp_01__rlm_20__exp_v4_s20_n0+qwen3-coder-30b` | 138 | none recorded |
| count_records_20261106 | `count_records_20261106/t2/qwen3-coder-30b/runs/exp_01__rlm_5__exp_v4_s20_n0+qwen3-coder-30b` | 138 | none recorded |
| count_records_20261106 | `count_records_20261106/t2/qwen3-coder-30b/runs/exp_01__single_pass__exp_v4_s20_n0+qwen3-coder-30b` | 407 | none recorded |
| count_records_20261106 | `count_records_20261106/t2/qwen3-coder-30b/runs/exp_01__verified_pass__exp_v4_s20_n0+qwen3-coder-30b` | 407 | none recorded |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04__analyzer__devstral-small-2-24b` | 690 | `df0cd717` (false): 345 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04__analyzer__gemini-3-flash-preview` | 2,070 | `df0cd717` (false): 1,035 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04__analyzer__gemma3-27b` | 690 | `df0cd717` (false): 345 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04__analyzer__gpt-oss-20b` | 690 | `df0cd717` (false): 345 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04__analyzer__llama3-8b` | 690 | `df0cd717` (false): 345 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04__analyzer__qwen3-coder-30b` | 690 | `df0cd717` (false): 345 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04__distiller__devstral-small-2-24b` | 194 | `df0cd717` (false): 97 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04__distiller__gemini-3-flash-preview` | 582 | `df0cd717` (false): 291 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04__distiller__gemma3-27b` | 194 | `df0cd717` (false): 97 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04__distiller__gpt-oss-20b` | 194 | `df0cd717` (false): 97 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04__distiller__llama3-8b` | 194 | `df0cd717` (false): 97 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04__distiller__qwen3-coder-30b` | 194 | `df0cd717` (false): 97 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04__planner__devstral-small-2-24b` | 180 | `df0cd717` (false): 90 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04__planner__gemini-3-flash-preview` | 540 | `df0cd717` (false): 270 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04__planner__gemma3-27b` | 180 | `df0cd717` (false): 90 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04__planner__gpt-oss-20b` | 180 | `df0cd717` (false): 90 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04__planner__llama3-8b` | 180 | `df0cd717` (false): 90 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04__planner__qwen3-coder-30b` | 180 | `df0cd717` (false): 90 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04__supervisor__devstral-small-2-24b` | 400 | `df0cd717` (false): 200 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04__supervisor__gemini-3-flash-preview` | 1,200 | `df0cd717` (false): 600 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04__supervisor__gemma3-27b` | 400 | `df0cd717` (false): 200 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04__supervisor__gpt-oss-20b` | 400 | `df0cd717` (false): 200 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04__supervisor__llama3-8b` | 400 | `df0cd717` (false): 200 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04__supervisor__qwen3-coder-30b` | 400 | `df0cd717` (false): 200 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04__synthesizer__devstral-small-2-24b` | 200 | `df0cd717` (false): 100 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04__synthesizer__gemini-3-flash-preview` | 600 | `df0cd717` (false): 300 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04__synthesizer__gemma3-27b` | 200 | `df0cd717` (false): 100 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04__synthesizer__gpt-oss-20b` | 200 | `df0cd717` (false): 100 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04__synthesizer__llama3-8b` | 200 | `df0cd717` (false): 100 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04__synthesizer__qwen3-coder-30b` | 200 | `df0cd717` (false): 100 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04b__F1__devstral-small-2-24b` | 194 | `df0cd717` (false): 97 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04b__F1__gemini-3-flash-preview` | 194 | `df0cd717` (false): 97 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04b__F1__gemma3-27b` | 194 | `df0cd717` (false): 97 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04b__F1__gpt-oss-20b` | 194 | `df0cd717` (false): 97 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04b__F1__llama3-8b` | 194 | `df0cd717` (false): 97 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04b__F1__qwen3-coder-30b` | 194 | `df0cd717` (false): 97 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04b__baseline__devstral-small-2-24b` | 194 | `df0cd717` (false): 97 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04b__baseline__gemini-3-flash-preview` | 194 | `df0cd717` (false): 97 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04b__baseline__gemma3-27b` | 194 | `df0cd717` (false): 97 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04b__baseline__gpt-oss-20b` | 194 | `df0cd717` (false): 97 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04b__baseline__llama3-8b` | 194 | `df0cd717` (false): 97 |
| count_records_20261106 | `count_records_20261106/t3/T3_frozen_20261104T131439Z/sinks/exp_04b__baseline__qwen3-coder-30b` | 194 | `df0cd717` (false): 97 |
| count_records_20261108 | `count_records_20261108/t2x/gemma3-27b/runs/exp_01__rlm_10__exp_v4_s20_n0+gemma3-27b` | 200 | `43899c16` (false): 175 |
| count_records_20261108 | `count_records_20261108/t2x/qwen3-coder-30b/runs/exp_01__rlm_10__exp_v4_s20_n0+qwen3-coder-30b` | 201 | `43899c16` (false): 159 |
| count_records_20261109 | `count_records_20261109/g20/runs/b4_rlm_ref_qwen3coder__cap10__d239a46` | 341 | `a0749d02` (false): 295 |
| count_records_20261109 | `count_records_20261109/g20/runs/exp_01__rlm_10_nogate__exp_v4_s20_n0+qwen3-coder-30b` | 47 | none recorded |
| count_records_20261109 | `count_records_20261109/g20/runs/exp_01__rlm_10_nosearch__exp_v4_s20_n0+qwen3-coder-30b` | 47 | none recorded |
| fig2_g1r15_inputs | `fig2_g1r15_inputs/runs/exp_01__rlm_10__exp_v4_s20_n0` | 405 | none recorded |
| fig2_g1r15_inputs | `fig2_g1r15_inputs/runs/exp_01__rlm_20__exp_v4_s20_n0` | 405 | none recorded |
| fig2_g1r15_inputs | `fig2_g1r15_inputs/runs/exp_01__rlm_5__exp_v4_s20_n0` | 405 | none recorded |
| fig2_g1r15_inputs | `fig2_g1r15_inputs/runs/exp_01__verified_pass__exp_v4_s20_n0` | 405 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s10_n0` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s10_n1` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s10_n3` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s20_n0` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s20_n1` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s20_n3` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s50_n0` | 244 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s50_n1` | 244 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s50_n3` | 244 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s5_n0` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s5_n1` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s5_n3` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s10_n0` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s10_n1` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s10_n3` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s20_n0` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s20_n1` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s20_n3` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s50_n0` | 244 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s50_n1` | 244 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s50_n3` | 244 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s5_n0` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s5_n1` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s5_n3` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s10_n0` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s10_n1` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s10_n3` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s20_n0` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s20_n1` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s20_n3` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s50_n0` | 244 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s50_n1` | 244 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s50_n3` | 244 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s5_n0` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s5_n1` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s5_n3` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s10_n0` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s10_n1` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s10_n3` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s20_n0` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s20_n1` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s20_n3` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s50_n0` | 244 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s50_n1` | 244 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s50_n3` | 244 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s5_n0` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s5_n1` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s5_n3` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__single_pass__exp_v4_s10_n0` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__single_pass__exp_v4_s10_n1` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__single_pass__exp_v4_s10_n3` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__single_pass__exp_v4_s20_n0` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__single_pass__exp_v4_s20_n1` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__single_pass__exp_v4_s20_n3` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__single_pass__exp_v4_s50_n0` | 244 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__single_pass__exp_v4_s50_n1` | 244 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__single_pass__exp_v4_s50_n3` | 244 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__single_pass__exp_v4_s5_n0` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__single_pass__exp_v4_s5_n1` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__single_pass__exp_v4_s5_n3` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s10_n0` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s10_n1` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s10_n3` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s20_n0` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s20_n1` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s20_n3` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s50_n0` | 244 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s50_n1` | 244 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s50_n3` | 244 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s5_n0` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s5_n1` | 135 | none recorded |
| fig3_g4_inputs | `fig3_g4_inputs/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s5_n3` | 135 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s10_n0` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s10_n1` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s10_n3` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s20_n0` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s20_n1` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s20_n3` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s50_n0` | 337 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s50_n1` | 337 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s50_n3` | 337 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s5_n0` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s5_n1` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__multi_hop__exp_v4_s5_n3` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s10_n0` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s10_n1` | 230 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s10_n3` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s20_n0` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s20_n1` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s20_n3` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s50_n0` | 337 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s50_n1` | 338 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s50_n3` | 337 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s5_n0` | 229 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s5_n1` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_10__exp_v4_s5_n3` | 230 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s10_n0` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s10_n1` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s10_n3` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s20_n0` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s20_n1` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s20_n3` | 229 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s50_n0` | 337 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s50_n1` | 337 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s50_n3` | 337 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s5_n0` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s5_n1` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_20__exp_v4_s5_n3` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s10_n0` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s10_n1` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s10_n3` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s20_n0` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s20_n1` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s20_n3` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s50_n0` | 337 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s50_n1` | 337 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s50_n3` | 337 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s5_n0` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s5_n1` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__rlm_5__exp_v4_s5_n3` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__single_pass__exp_v4_s10_n0` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__single_pass__exp_v4_s10_n1` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__single_pass__exp_v4_s10_n3` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__single_pass__exp_v4_s20_n0` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__single_pass__exp_v4_s20_n1` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__single_pass__exp_v4_s20_n3` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__single_pass__exp_v4_s50_n0` | 337 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__single_pass__exp_v4_s50_n1` | 337 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__single_pass__exp_v4_s50_n3` | 337 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__single_pass__exp_v4_s5_n0` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__single_pass__exp_v4_s5_n1` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__single_pass__exp_v4_s5_n3` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s10_n0` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s10_n1` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s10_n3` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s20_n0` | 229 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s20_n1` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s20_n3` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s50_n0` | 337 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s50_n1` | 337 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s50_n3` | 337 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s5_n0` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s5_n1` | 228 | none recorded |
| g4_draws_20261101 | `g4_draws_20261101/runs/exp_02_scaling_factorial__verified_pass__exp_v4_s5_n3` | 228 | none recorded |
| g6_calls_after_d135 | `g6_calls_after_d135/b4_rlm_ref__cap10__all135` | 9,612 | `e27a3f18` (true): 85 |
| g6_calls_after_d135 | `g6_calls_after_d135/b4_rlm_ref__cap20__all135` | 12,005 | `e27a3f18` (true): 360 |
| g6_calls_after_d135 | `g6_calls_after_d135/b4_rlm_ref__cap5__all135` | 6,814 | `e27a3f18` (true): 94 |
| g6_calls_before_d89 | `g6_calls_before_d89/b4_rlm_ref__cap10__all135` | 9,527 | none recorded |
| g6_calls_before_d89 | `g6_calls_before_d89/b4_rlm_ref__cap20__all135` | 11,645 | none recorded |
| g6_calls_before_d89 | `g6_calls_before_d89/b4_rlm_ref__cap5__all135` | 6,720 | none recorded |
| k1_inputs_runs | `k1_inputs_runs/exp_01__multi_hop__exp_v4_s20_n0` | 407 | none recorded |
| k1_inputs_runs | `k1_inputs_runs/exp_01__rlm_10__exp_v4_s20_n0` | 408 | none recorded |
| k1_inputs_runs | `k1_inputs_runs/exp_01__rlm_20__exp_v4_s20_n0` | 406 | none recorded |
| k1_inputs_runs | `k1_inputs_runs/exp_01__rlm_5__exp_v4_s20_n0` | 407 | none recorded |
| k1_inputs_runs | `k1_inputs_runs/exp_01__single_pass__exp_v4_s20_n0` | 406 | none recorded |
| k1_inputs_runs | `k1_inputs_runs/exp_01__verified_pass__exp_v4_s20_n0` | 406 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/laptop/mentori-runs-s2-laptop/runs/exp_05__coder_v2_n1__gpt-oss-20b+low` | 889 | `92f1d3ef` (false): 225 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/laptop/mentori-runs-s2-laptop/runs/exp_05__coder_v2_n1_cell3_best__gpt-oss-20b+low` | 1,317 | `92f1d3ef` (false): 416 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/laptop/mentori-runs-s2-laptop/runs/exp_05__coder_v2_n1_cell3_combined__gpt-oss-20b+low` | 1,159 | `92f1d3ef` (false): 328 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/laptop/mentori-runs-s2-laptop/runs/exp_05__coder_v2_n3__gpt-oss-20b+low` | 1,034 | `92f1d3ef` (false): 365 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/laptop/mentori-runs-s2-laptop/runs/exp_05__error_recovery_introspect__gpt-oss-20b+low` | 29 | `92f1d3ef` (false): 3 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/laptop/mentori-runs-s2-laptop/runs/exp_05__free_form__gpt-oss-20b+low` | 26 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/laptop/mentori-runs-s2-laptop/runs/exp_05__free_form_n3_best__gpt-oss-20b+low` | 84 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/laptop/mentori-runs-s2-laptop/runs/exp_05__free_form_n3_combined__gpt-oss-20b+low` | 86 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/laptop/mentori-runs-s2-laptop/runs/exp_05__introspect_then_code__gpt-oss-20b+low` | 46 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/laptop/mentori-runs-s2-laptop/runs/exp_05__introspect_with_recovery__gpt-oss-20b+low` | 48 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/laptop/mentori-runs-s2-laptop/runs/exp_05__thinker_coder_split__gpt-oss-20b+low` | 62 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__coder_v2_n1__devstral-small-2-24b+default` | 668 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__coder_v2_n1__gpt-oss-20b+medium` | 466 | `92f1d3ef` (false): 72 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__coder_v2_n1_cell3_best__devstral-small-2-24b+default` | 1,070 | `92f1d3ef` (false): 43 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__coder_v2_n1_cell3_best__gpt-oss-20b+medium` | 708 | `92f1d3ef` (false): 88 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__coder_v2_n1_cell3_combined__devstral-small-2-24b+default` | 1,240 | `92f1d3ef` (false): 82 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__coder_v2_n1_cell3_combined__gpt-oss-20b+medium` | 825 | `92f1d3ef` (false): 202 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__coder_v2_n3__devstral-small-2-24b+default` | 813 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__coder_v2_n3__gpt-oss-20b+medium` | 758 | `92f1d3ef` (false): 192 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__error_recovery_introspect__devstral-small-2-24b+default` | 27 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__error_recovery_introspect__gpt-oss-20b+medium` | 27 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__free_form__devstral-small-2-24b+default` | 26 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__free_form__gpt-oss-20b+medium` | 25 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__free_form_n3_best__devstral-small-2-24b+default` | 86 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__free_form_n3_best__gpt-oss-20b+medium` | 84 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__free_form_n3_combined__devstral-small-2-24b+default` | 86 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__free_form_n3_combined__gpt-oss-20b+medium` | 86 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__introspect_then_code__devstral-small-2-24b+default` | 44 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__introspect_then_code__gpt-oss-20b+medium` | 46 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__introspect_with_recovery__devstral-small-2-24b+default` | 47 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__introspect_with_recovery__gpt-oss-20b+medium` | 46 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__thinker_coder_split__devstral-small-2-24b+default` | 68 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__thinker_coder_split__gpt-oss-20b+medium` | 67 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1__deepseek-r1-70b+default` | 244 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1__gemini-2.5-pro+default` | 596 | `0b8074d7` (false): 84 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1__gemini-2.5-pro+off` | 681 | `0b8074d7` (false): 34 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1__gemini-3-flash-preview+default` | 405 | `0b8074d7` (false): 40 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1__gemini-3-flash-preview+off` | 486 | `0b8074d7` (false): 71 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1__gpt-oss-20b+high` | 586 | `0b8074d7` (false): 267 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1__qwen3-coder-30b+default` | 705 | `0b8074d7` (false): 59 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1__qwen3-coder-next-q4_K_M+default` | 892 | `0b8074d7` (false): 43 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1_cell3_best__deepseek-r1-70b+default` | 248 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1_cell3_best__gemini-2.5-pro+default` | 907 | `0b8074d7` (false): 113 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1_cell3_best__gemini-2.5-pro+off` | 1,296 | `0b8074d7` (false): 225 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1_cell3_best__gemini-3-flash-preview+default` | 645 | `0b8074d7` (false): 94 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1_cell3_best__gemini-3-flash-preview+off` | 638 | `0b8074d7` (false): 34 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1_cell3_best__gpt-oss-20b+high` | 719 | `0b8074d7` (false): 280 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1_cell3_best__qwen3-coder-30b+default` | 1,131 | `0b8074d7` (false): 183 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1_cell3_best__qwen3-coder-next-q4_K_M+default` | 1,370 | `0b8074d7` (false): 339 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1_cell3_combined__deepseek-r1-70b+default` | 219 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1_cell3_combined__gemini-2.5-pro+default` | 928 | `0b8074d7` (false): 136 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1_cell3_combined__gemini-2.5-pro+off` | 1,193 | `0b8074d7` (false): 141 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1_cell3_combined__gemini-3-flash-preview+default` | 597 | `0b8074d7` (false): 33 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1_cell3_combined__gemini-3-flash-preview+off` | 646 | `0b8074d7` (false): 34 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1_cell3_combined__gpt-oss-20b+high` | 803 | `0b8074d7` (false): 433 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1_cell3_combined__qwen3-coder-30b+default` | 1,186 | `0b8074d7` (false): 180 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1_cell3_combined__qwen3-coder-next-q4_K_M+default` | 1,291 | `0b8074d7` (false): 119 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__coder_v2_n3__gemini-2.5-pro+default` | 648 | `0b8074d7` (false): 68 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__coder_v2_n3__gemini-2.5-pro+off` | 612 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__coder_v2_n3__gemini-3-flash-preview+default` | 462 | `0b8074d7` (false): 25 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__coder_v2_n3__gemini-3-flash-preview+off` | 664 | `0b8074d7` (false): 80 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__coder_v2_n3__gpt-oss-20b+high` | 944 | `0b8074d7` (false): 466 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__coder_v2_n3__qwen3-coder-30b+default` | 669 | `0b8074d7` (false): 41 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__coder_v2_n3__qwen3-coder-next-q4_K_M+default` | 897 | `0b8074d7` (false): 81 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__error_recovery_introspect__gemini-2.5-pro+default` | 25 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__error_recovery_introspect__gemini-2.5-pro+off` | 27 | `0b8074d7` (false): 2 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__error_recovery_introspect__gemini-3-flash-preview+default` | 22 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__error_recovery_introspect__gemini-3-flash-preview+off` | 23 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__error_recovery_introspect__gpt-oss-20b+high` | 28 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__error_recovery_introspect__qwen3-coder-30b+default` | 21 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__error_recovery_introspect__qwen3-coder-next-q4_K_M+default` | 28 | `0b8074d7` (false): 3 |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__free_form__deepseek-r1-70b+default` | 26 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__free_form__gemini-2.5-pro+default` | 26 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__free_form__gemini-2.5-pro+off` | 25 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__free_form__gemini-3-flash-preview+default` | 22 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__free_form__gemini-3-flash-preview+off` | 22 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__free_form__gpt-oss-20b+high` | 27 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__free_form__qwen3-coder-30b+default` | 21 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__free_form__qwen3-coder-next-q4_K_M+default` | 25 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__free_form_n3_best__deepseek-r1-70b+default` | 87 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__free_form_n3_best__gemini-2.5-pro+default` | 83 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__free_form_n3_best__gemini-2.5-pro+off` | 86 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__free_form_n3_best__gemini-3-flash-preview+default` | 82 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__free_form_n3_best__gemini-3-flash-preview+off` | 82 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__free_form_n3_best__gpt-oss-20b+high` | 85 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__free_form_n3_best__qwen3-coder-30b+default` | 82 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__free_form_n3_best__qwen3-coder-next-q4_K_M+default` | 85 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__free_form_n3_combined__deepseek-r1-70b+default` | 93 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__free_form_n3_combined__gemini-2.5-pro+default` | 84 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__free_form_n3_combined__gemini-2.5-pro+off` | 86 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__free_form_n3_combined__gemini-3-flash-preview+default` | 84 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__free_form_n3_combined__gemini-3-flash-preview+off` | 86 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__free_form_n3_combined__gpt-oss-20b+high` | 86 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__free_form_n3_combined__qwen3-coder-30b+default` | 83 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__free_form_n3_combined__qwen3-coder-next-q4_K_M+default` | 84 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__introspect_then_code__gemini-2.5-pro+default` | 43 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__introspect_then_code__gemini-2.5-pro+off` | 46 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__introspect_then_code__gemini-3-flash-preview+default` | 42 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__introspect_then_code__gemini-3-flash-preview+off` | 42 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__introspect_then_code__gpt-oss-20b+high` | 45 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__introspect_then_code__qwen3-coder-30b+default` | 44 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__introspect_then_code__qwen3-coder-next-q4_K_M+default` | 43 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__introspect_with_recovery__gemini-2.5-pro+default` | 46 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__introspect_with_recovery__gemini-2.5-pro+off` | 47 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__introspect_with_recovery__gemini-3-flash-preview+default` | 42 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__introspect_with_recovery__gemini-3-flash-preview+off` | 42 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__introspect_with_recovery__gpt-oss-20b+high` | 45 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__introspect_with_recovery__qwen3-coder-30b+default` | 46 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__introspect_with_recovery__qwen3-coder-next-q4_K_M+default` | 47 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__thinker_coder_split__gemini-2.5-pro+default` | 61 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__thinker_coder_split__gemini-2.5-pro+off` | 65 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__thinker_coder_split__gemini-3-flash-preview+default` | 63 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__thinker_coder_split__gemini-3-flash-preview+off` | 62 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__thinker_coder_split__gpt-oss-20b+high` | 62 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__thinker_coder_split__qwen3-coder-30b+default` | 63 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2/runs/exp_05__thinker_coder_split__qwen3-coder-next-q4_K_M+default` | 65 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2-d75/runs/exp_05__coder_v2_n1__gemma3-27b+default` | 250 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2-d75/runs/exp_05__coder_v2_n1__glm-4.7-flash-bf16+default` | 394 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2-d75/runs/exp_05__coder_v2_n1__nemotron-3-nano-30b+default` | 510 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2-d75/runs/exp_05__coder_v2_n1__nemotron-3-nano-30b+off` | 91 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2-d75/runs/exp_05__coder_v2_n1_cell3_best__gemma3-27b+default` | 250 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2-d75/runs/exp_05__coder_v2_n1_cell3_combined__gemma3-27b+default` | 244 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2-d75/runs/exp_05__coder_v2_n3__gemma3-27b+default` | 316 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2-d75/runs/exp_05__error_recovery_introspect__gemma3-27b+default` | 28 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2-d75/runs/exp_05__free_form__gemma3-27b+default` | 29 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2-d75/runs/exp_05__free_form__glm-4.7-flash-bf16+default` | 28 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2-d75/runs/exp_05__free_form__nemotron-3-nano-30b+default` | 28 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2-d75/runs/exp_05__free_form__nemotron-3-nano-30b+off` | 31 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2-d75/runs/exp_05__free_form_n3_best__gemma3-27b+default` | 88 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2-d75/runs/exp_05__free_form_n3_best__glm-4.7-flash-bf16+default` | 88 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2-d75/runs/exp_05__free_form_n3_best__nemotron-3-nano-30b+default` | 89 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2-d75/runs/exp_05__free_form_n3_best__nemotron-3-nano-30b+off` | 90 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2-d75/runs/exp_05__free_form_n3_combined__gemma3-27b+default` | 86 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2-d75/runs/exp_05__free_form_n3_combined__glm-4.7-flash-bf16+default` | 87 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2-d75/runs/exp_05__free_form_n3_combined__nemotron-3-nano-30b+default` | 90 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2-d75/runs/exp_05__free_form_n3_combined__nemotron-3-nano-30b+off` | 90 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2-d75/runs/exp_05__introspect_then_code__gemma3-27b+default` | 50 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2-d75/runs/exp_05__introspect_with_recovery__gemma3-27b+default` | 49 | none recorded |
| s2_after_s4_20261105 | `s2_after_s4_20261105/studio/mentori-runs-s2-d75/runs/exp_05__thinker_coder_split__gemma3-27b+default` | 67 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/laptop/mentori-runs-s2-laptop/runs/exp_05__coder_v2_n1__gpt-oss-20b+low` | 664 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/laptop/mentori-runs-s2-laptop/runs/exp_05__coder_v2_n1_cell3_best__gpt-oss-20b+low` | 901 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/laptop/mentori-runs-s2-laptop/runs/exp_05__coder_v2_n1_cell3_combined__gpt-oss-20b+low` | 831 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/laptop/mentori-runs-s2-laptop/runs/exp_05__coder_v2_n3__gpt-oss-20b+low` | 669 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/laptop/mentori-runs-s2-laptop/runs/exp_05__error_recovery_introspect__gpt-oss-20b+low` | 26 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/laptop/mentori-runs-s2-laptop/runs/exp_05__free_form__gpt-oss-20b+low` | 26 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/laptop/mentori-runs-s2-laptop/runs/exp_05__free_form_n3_best__gpt-oss-20b+low` | 84 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/laptop/mentori-runs-s2-laptop/runs/exp_05__free_form_n3_combined__gpt-oss-20b+low` | 86 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/laptop/mentori-runs-s2-laptop/runs/exp_05__introspect_then_code__gpt-oss-20b+low` | 46 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/laptop/mentori-runs-s2-laptop/runs/exp_05__introspect_with_recovery__gpt-oss-20b+low` | 48 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/laptop/mentori-runs-s2-laptop/runs/exp_05__thinker_coder_split__gpt-oss-20b+low` | 62 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__coder_v2_n1__devstral-small-2-24b+default` | 668 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__coder_v2_n1__gpt-oss-20b+medium` | 394 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__coder_v2_n1_cell3_best__devstral-small-2-24b+default` | 1,027 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__coder_v2_n1_cell3_best__gpt-oss-20b+medium` | 620 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__coder_v2_n1_cell3_combined__devstral-small-2-24b+default` | 1,158 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__coder_v2_n1_cell3_combined__gpt-oss-20b+medium` | 623 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__coder_v2_n3__devstral-small-2-24b+default` | 813 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__coder_v2_n3__gpt-oss-20b+medium` | 566 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__error_recovery_introspect__devstral-small-2-24b+default` | 27 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__error_recovery_introspect__gpt-oss-20b+medium` | 27 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__free_form__devstral-small-2-24b+default` | 26 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__free_form__gpt-oss-20b+medium` | 25 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__free_form_n3_best__devstral-small-2-24b+default` | 86 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__free_form_n3_best__gpt-oss-20b+medium` | 84 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__free_form_n3_combined__devstral-small-2-24b+default` | 86 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__free_form_n3_combined__gpt-oss-20b+medium` | 86 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__introspect_then_code__devstral-small-2-24b+default` | 44 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__introspect_then_code__gpt-oss-20b+medium` | 46 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__introspect_with_recovery__devstral-small-2-24b+default` | 47 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__introspect_with_recovery__gpt-oss-20b+medium` | 46 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__thinker_coder_split__devstral-small-2-24b+default` | 68 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/laptop/mentori-runs-s2-laptop-d75/runs/exp_05__thinker_coder_split__gpt-oss-20b+medium` | 67 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1__deepseek-r1-70b+default` | 244 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1__gemini-2.5-pro+default` | 512 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1__gemini-2.5-pro+off` | 647 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1__gemini-3-flash-preview+default` | 365 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1__gemini-3-flash-preview+off` | 415 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1__gpt-oss-20b+high` | 319 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1__qwen3-coder-30b+default` | 646 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1__qwen3-coder-next-q4_K_M+default` | 849 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1_cell3_best__deepseek-r1-70b+default` | 248 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1_cell3_best__gemini-2.5-pro+default` | 794 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1_cell3_best__gemini-2.5-pro+off` | 1,071 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1_cell3_best__gemini-3-flash-preview+default` | 551 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1_cell3_best__gemini-3-flash-preview+off` | 604 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1_cell3_best__gpt-oss-20b+high` | 439 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1_cell3_best__qwen3-coder-30b+default` | 948 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1_cell3_best__qwen3-coder-next-q4_K_M+default` | 1,031 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1_cell3_combined__deepseek-r1-70b+default` | 219 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1_cell3_combined__gemini-2.5-pro+default` | 792 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1_cell3_combined__gemini-2.5-pro+off` | 1,052 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1_cell3_combined__gemini-3-flash-preview+default` | 564 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1_cell3_combined__gemini-3-flash-preview+off` | 612 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1_cell3_combined__gpt-oss-20b+high` | 370 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1_cell3_combined__qwen3-coder-30b+default` | 1,006 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__coder_v2_n1_cell3_combined__qwen3-coder-next-q4_K_M+default` | 1,172 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__coder_v2_n3__gemini-2.5-pro+default` | 580 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__coder_v2_n3__gemini-2.5-pro+off` | 612 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__coder_v2_n3__gemini-3-flash-preview+default` | 437 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__coder_v2_n3__gemini-3-flash-preview+off` | 584 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__coder_v2_n3__gpt-oss-20b+high` | 478 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__coder_v2_n3__qwen3-coder-30b+default` | 628 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__coder_v2_n3__qwen3-coder-next-q4_K_M+default` | 816 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__error_recovery_introspect__gemini-2.5-pro+default` | 25 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__error_recovery_introspect__gemini-2.5-pro+off` | 25 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__error_recovery_introspect__gemini-3-flash-preview+default` | 22 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__error_recovery_introspect__gemini-3-flash-preview+off` | 23 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__error_recovery_introspect__gpt-oss-20b+high` | 28 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__error_recovery_introspect__qwen3-coder-30b+default` | 21 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__error_recovery_introspect__qwen3-coder-next-q4_K_M+default` | 25 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__free_form__deepseek-r1-70b+default` | 26 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__free_form__gemini-2.5-pro+default` | 26 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__free_form__gemini-2.5-pro+off` | 25 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__free_form__gemini-3-flash-preview+default` | 22 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__free_form__gemini-3-flash-preview+off` | 22 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__free_form__gpt-oss-20b+high` | 27 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__free_form__qwen3-coder-30b+default` | 21 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__free_form__qwen3-coder-next-q4_K_M+default` | 25 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__free_form_n3_best__deepseek-r1-70b+default` | 87 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__free_form_n3_best__gemini-2.5-pro+default` | 83 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__free_form_n3_best__gemini-2.5-pro+off` | 86 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__free_form_n3_best__gemini-3-flash-preview+default` | 82 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__free_form_n3_best__gemini-3-flash-preview+off` | 82 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__free_form_n3_best__gpt-oss-20b+high` | 85 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__free_form_n3_best__qwen3-coder-30b+default` | 82 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__free_form_n3_best__qwen3-coder-next-q4_K_M+default` | 85 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__free_form_n3_combined__deepseek-r1-70b+default` | 93 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__free_form_n3_combined__gemini-2.5-pro+default` | 84 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__free_form_n3_combined__gemini-2.5-pro+off` | 86 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__free_form_n3_combined__gemini-3-flash-preview+default` | 84 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__free_form_n3_combined__gemini-3-flash-preview+off` | 86 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__free_form_n3_combined__gpt-oss-20b+high` | 86 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__free_form_n3_combined__qwen3-coder-30b+default` | 83 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__free_form_n3_combined__qwen3-coder-next-q4_K_M+default` | 84 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__introspect_then_code__gemini-2.5-pro+default` | 43 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__introspect_then_code__gemini-2.5-pro+off` | 46 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__introspect_then_code__gemini-3-flash-preview+default` | 42 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__introspect_then_code__gemini-3-flash-preview+off` | 42 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__introspect_then_code__gpt-oss-20b+high` | 45 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__introspect_then_code__qwen3-coder-30b+default` | 44 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__introspect_then_code__qwen3-coder-next-q4_K_M+default` | 43 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__introspect_with_recovery__gemini-2.5-pro+default` | 46 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__introspect_with_recovery__gemini-2.5-pro+off` | 47 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__introspect_with_recovery__gemini-3-flash-preview+default` | 42 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__introspect_with_recovery__gemini-3-flash-preview+off` | 42 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__introspect_with_recovery__gpt-oss-20b+high` | 45 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__introspect_with_recovery__qwen3-coder-30b+default` | 46 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__introspect_with_recovery__qwen3-coder-next-q4_K_M+default` | 47 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__thinker_coder_split__gemini-2.5-pro+default` | 61 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__thinker_coder_split__gemini-2.5-pro+off` | 65 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__thinker_coder_split__gemini-3-flash-preview+default` | 63 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__thinker_coder_split__gemini-3-flash-preview+off` | 62 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__thinker_coder_split__gpt-oss-20b+high` | 62 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__thinker_coder_split__qwen3-coder-30b+default` | 63 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2/runs/exp_05__thinker_coder_split__qwen3-coder-next-q4_K_M+default` | 65 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2-d75/runs/exp_05__coder_v2_n1__gemma3-27b+default` | 250 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2-d75/runs/exp_05__coder_v2_n1__glm-4.7-flash-bf16+default` | 394 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2-d75/runs/exp_05__coder_v2_n1__nemotron-3-nano-30b+default` | 357 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2-d75/runs/exp_05__coder_v2_n1__nemotron-3-nano-30b+off` | 48 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2-d75/runs/exp_05__coder_v2_n1_cell3_best__gemma3-27b+default` | 250 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2-d75/runs/exp_05__coder_v2_n1_cell3_combined__gemma3-27b+default` | 244 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2-d75/runs/exp_05__coder_v2_n3__gemma3-27b+default` | 316 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2-d75/runs/exp_05__error_recovery_introspect__gemma3-27b+default` | 28 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2-d75/runs/exp_05__free_form__gemma3-27b+default` | 29 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2-d75/runs/exp_05__free_form__glm-4.7-flash-bf16+default` | 28 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2-d75/runs/exp_05__free_form__nemotron-3-nano-30b+default` | 28 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2-d75/runs/exp_05__free_form__nemotron-3-nano-30b+off` | 31 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2-d75/runs/exp_05__free_form_n3_best__gemma3-27b+default` | 88 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2-d75/runs/exp_05__free_form_n3_best__glm-4.7-flash-bf16+default` | 88 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2-d75/runs/exp_05__free_form_n3_best__nemotron-3-nano-30b+default` | 89 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2-d75/runs/exp_05__free_form_n3_best__nemotron-3-nano-30b+off` | 90 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2-d75/runs/exp_05__free_form_n3_combined__gemma3-27b+default` | 86 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2-d75/runs/exp_05__free_form_n3_combined__glm-4.7-flash-bf16+default` | 87 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2-d75/runs/exp_05__free_form_n3_combined__nemotron-3-nano-30b+default` | 90 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2-d75/runs/exp_05__free_form_n3_combined__nemotron-3-nano-30b+off` | 90 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2-d75/runs/exp_05__introspect_then_code__gemma3-27b+default` | 50 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2-d75/runs/exp_05__introspect_with_recovery__gemma3-27b+default` | 49 | none recorded |
| s2_length_retries_20261021 | `s2_length_retries_20261021/studio/mentori-runs-s2-d75/runs/exp_05__thinker_coder_split__gemma3-27b+default` | 67 | none recorded |
| s457_mirror_20261022 | `s457_mirror_20261022/matched_budget` | 405 | none recorded |
| s457_mirror_20261022 | `s457_mirror_20261022/multi_hop` | 405 | none recorded |
| s457_mirror_20261022 | `s457_mirror_20261022/rlm_10` | 405 | none recorded |
| s457_mirror_20261022 | `s457_mirror_20261022/rlm_20` | 405 | none recorded |
| s457_mirror_20261022 | `s457_mirror_20261022/rlm_5` | 405 | none recorded |
| s457_mirror_20261022 | `s457_mirror_20261022/single_pass` | 405 | none recorded |
| s457_mirror_20261022 | `s457_mirror_20261022/verified_pass` | 405 | none recorded |

## The commits pinned by the launchers

Each launcher of Mentori-reanalysis that pins a commit (`PIN=`), at the line that pins it. The launchers
themselves are not in this folder: they name the paper's machines and ports.

| launcher | commit |
|---|---|
| `findings/recompute/S18f_runs/run_s18f_studio.sh:23` | `b292315f` |
| `findings/recompute/S3_runs/s6/start_s6w_laptop.sh:13` | `46a60e5a` |
| `findings/recompute/S3_runs/s6/start_s6w_second_beelink.sh:24` | `34bb2d55` |
| `findings/recompute/S3_runs/s6/start_s6w_second_laptop.sh:18` | `99357a12` |
| `findings/recompute/S3_runs/s6/start_s6w_second_local.sh:53` | `34bb2d55` |
| `findings/recompute/S3_runs/s6/start_s6w_studio.sh:22` | `46a60e5a` |
| `findings/recompute/S3_runs/s6/start_s6wt2g_rest_laptop.sh:15` | `99357a12` |
| `findings/recompute/S3_runs/s6/start_t2q_second_studio.sh:8` | `99357a12` |
| `findings/recompute/S564_claimify_selection/start_s564_laptop.sh:14` | `5f20c8c3` |
| `findings/recompute/T3_runs/launch_t3.sh:24` | `df0cd717` |

## How far each commit is from this folder

Files that differ between the commit and `7c02e422` in the harness folders (`experiments/mentori`, `experiments/runner`, `experiments/scorers`, `experiments/rlm_ref`, `experiments/reuse_demo`, `tools/mentori_cli`, `experiments/LOCK.toml`).

| commit | date | ancestor of the release commit | files that differ |
|---|---|---|---|
| `0b8074d7` | 2026-10-29 | True | 48 |
| `34bb2d55` | 2026-11-02 | True | 46 |
| `43899c16` | 2026-11-04 | True | 36 |
| `46a60e5a` | 2026-11-02 | True | 46 |
| `4a4e99bf` | 2026-11-05 | True | 32 |
| `5f20c8c3` | 2026-11-02 | True | 42 |
| `92f1d3ef` | 2026-10-29 | True | 48 |
| `99357a12` | 2026-11-02 | True | 42 |
| `a0749d02` | 2026-11-06 | True | 10 |
| `b292315f` | 2026-11-04 | True | 35 |
| `df0cd717` | 2026-11-02 | True | 42 |
| `e27a3f18` | 2026-10-24 | True | 73 |

The history itself is not released (RELEASE_DESIGN.md Q7): to rebuild the exact code of one run, one
would need Mentori-reanalysis at that commit. Whether to ship a patch per commit is open (Q7, O2).
