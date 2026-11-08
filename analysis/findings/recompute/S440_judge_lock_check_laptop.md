# S440 - devstral at the lock's settings on laptop, against the Studio (D42)

Rows 107; server http://127.0.0.1:11434 Ollama 0.40.2; model digest [('33af3142213a', 107)]; options {"temperature": 0, "num_ctx": 131072, "num_predict": -1, "num_batch": 1024}, request fields {"truncate": false, "shift": false}, lock sha256 3e47d386a23dc462fed05d7fc3c64b5dca78ce21e59b347430b9befdcbc155ab.
Status {'ok': 107}; stop reasons {'stop': 107}.

- total_s: median 13.93, mean 14.73, max 42.16
- prompt_eval_s: median 6.30, mean 7.20, max 33.67
- eval_s: median 7.29, mean 7.40, max 10.85
- wall_s: median 13.94, mean 14.74, max 42.19

Against the Studio's lock pass: 107 of 107 answers with every score equal; 107 of 107 with identical judge text.

- no difference

## Verdict

laptop gives the Studio's scores on all 107 answers: it can share devstral judging.
