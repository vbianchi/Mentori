# S440 - devstral at the lock's settings on beelink, against the Studio (D42)

Rows 107; server http://127.0.0.1:21434 Ollama 0.40.2; model digest [('33af3142213a', 107)]; options {"temperature": 0, "num_ctx": 131072, "num_predict": -1, "num_batch": 1024}, request fields {"truncate": false, "shift": false}, lock sha256 2e4d05c2f950f2369e9d4104749ea174608915cc2222053fd5b95c1290ca1ed6.
Status {'ok': 107}; stop reasons {'stop': 107}.

- total_s: median 15.49, mean 16.05, max 33.24
- prompt_eval_s: median 3.27, mean 3.93, max 18.70
- eval_s: median 11.73, mean 11.92, max 17.54
- wall_s: median 15.56, mean 16.11, max 33.31

Against the Studio's lock pass: 95 of 107 answers with every score equal; 24 of 107 with identical judge text.

- gemini::gemini-3-flash-preview|01_sarek_FR1: citation_quality 4 -> 5
- gemini::gemini-3-flash-preview|02_snakemake_CO2: correctness 5 -> 4; faithfulness 5 -> 4; citation_quality 4 -> 3
- gemini::gemini-3-flash-preview|SY_003: citation_quality 3 -> 4
- ollama::deepseek-r1:70b|02_snakemake_CO2: citation_quality 3 -> 2
- ollama::devstral-small-2:24b|CD_001: faithfulness 4 -> 3
- ollama::devstral-small-2:24b|SY_002: correctness 3 -> 2; citation_quality 2 -> 1
- ollama::gemma3:27b|01_sarek_TE3: correctness 2 -> 3; faithfulness 3 -> 4
- ollama::gpt-oss:120b|06_star_aligner_TE3: faithfulness 3 -> 0; citation_quality 5 -> 0
- ollama::nemotron-3-nano:30b|06_star_aligner_TE3: completeness 3 -> 2; citation_quality 2 -> 1
- ollama::nemotron-3-nano:30b|CD_002: correctness 0 -> 2; completeness 0 -> 1; faithfulness 0 -> 3; citation_quality 0 -> 4
- ollama::qwen3-coder:latest|01_sarek_FR1: completeness 4 -> 5; faithfulness 5 -> 4
- ollama::qwen3-coder:latest|02_snakemake_CO2: correctness 5 -> 4; completeness 5 -> 4; citation_quality 5 -> 3

## Verdict

beelink differs on 12 of 107 answers: it does not share devstral judging.
