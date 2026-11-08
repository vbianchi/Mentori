# S440 - devstral at the lock's settings against its present settings (A11, D30)

Rows: 214 (present 107, lock 107). Judge devstral-small-2:24b, complete answers, key v2.4 (107 calibration answers, S376.answers_and_key).

## Pass present

Options {"temperature": 0, "num_ctx": 32768, "num_predict": 8192}, request fields {}, lock sha256 None, server http://127.0.0.1:21451 Ollama 0.40.2, model digest [('33af3142213a', 107)].
Status {'ok': 107}; stop reasons {'stop': 107}.
Largest prompt 6986 tokens, longest output 240.

- total_s: median 7.34, mean 7.62, max 18.52
- load_s: median 0.02, mean 0.07, max 2.84
- prompt_eval_s: median 2.43, mean 2.89, max 13.54
- eval_s: median 4.55, mean 4.60, max 6.94
- wall_s: median 7.51, mean 7.82, max 18.72

## Pass lock

Options {"temperature": 0, "num_ctx": 131072, "num_predict": -1, "num_batch": 1024}, request fields {"truncate": false, "shift": false}, lock sha256 4a5eb100986a2d71944628e0e8316333410814a3c5b7078c11854a104b74858a, server http://127.0.0.1:21451 Ollama 0.40.2, model digest [('33af3142213a', 107)].
Status {'ok': 107}; stop reasons {'stop': 107}.
Largest prompt 6986 tokens, longest output 240.

- total_s: median 7.33, mean 7.63, max 18.52
- load_s: median 0.02, mean 0.09, max 4.14
- prompt_eval_s: median 2.43, mean 2.89, max 13.54
- eval_s: median 4.52, mean 4.59, max 6.96
- wall_s: median 7.55, mean 7.83, max 18.75

## Present against lock (same server, one after the other)

107 of 107 answers have every score equal; 107 of 107 have identical judge text.

- no difference

## Each pass against the S376 ledger (other servers, earlier days)

- present vs S376 rows on Ollama 0.40.1: 26 of 29 all scores equal, 21 of 29 identical text
- present vs S376 rows on Ollama 0.40.2: 78 of 78 all scores equal, 78 of 78 identical text
- lock vs S376 rows on Ollama 0.40.1: 26 of 29 all scores equal, 21 of 29 identical text
- lock vs S376 rows on Ollama 0.40.2: 78 of 78 all scores equal, 78 of 78 identical text

## Verdict

Every score held (107 of 107): the existing devstral judgments stand under the lock.
