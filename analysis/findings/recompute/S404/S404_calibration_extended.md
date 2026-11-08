# S404 judging step (2026-10-13 07:27)

1500 planned answers, key <repo>/data/ground_truth_v2/all_v2_4.json (sha256 5d8362ae931d), plan sha256 6ca17c0431ed, script sha256 042accc8dfb6. This session 561 min, judges devstral-small-2:24b, qwen3.8:27b-mlx, ministral-3:14b, qwen3-coder:latest.

| Judge | Rows | Scored | Not scored (status) | Left | Ports | Ollama | Digest | Median s | Mean s | Max prompt tokens | Max output tokens |
|---|---:|---:|---|---:|---|---|---|---:|---:|---:|---:|
| devstral-small-2:24b | 1500 | 1500 | none | 0 | 11451 | 0.40.2 | 33af3142213a | 16.2 | 17.0 | 10730 | 264 |
| qwen3.8:27b-mlx | 1500 | 1500 | none | 0 | 11462 | 0.40.2 | 5642e97495e1 | 19.1 | 20.0 | 8377 | 409 |
| ministral-3:14b | 1500 | 1500 | none | 0 | 11453 | 0.40.2 | 129e04c05b56 | 21.1 | 22.4 | 10729 | 834 |
| qwen3-coder:latest | 1500 | 1500 | none | 0 | 11452 | 0.40.2 | 06c1097efce0 | 10.6 | 10.9 | 8357 | 247 |

Median and mean s are per answer on one server (wall_s, retries included); servers on one machine share its GPU.

R2 lines of this plan, every session (S404_gate.jsonl): three S376 answers per port at the start of a session and again when the port's queue is empty.

| Judge | Port | Start lines | Start passed | End lines | End passed | End with S376's text | Text check waived |
|---|---:|---:|---:|---:|---:|---:|---|
| devstral-small-2:24b | 11451 | 3 | 3 | 3 | 3 | 3 | no |
| ministral-3:14b | 11453 | 3 | 3 | 3 | 3 | 3 | no |
| qwen3-coder:latest | 11452 | 3 | 3 | 3 | 3 | 3 | no |
| qwen3.8:27b-mlx | 11462 | 3 | 3 | 3 | 3 | 0 | yes |
