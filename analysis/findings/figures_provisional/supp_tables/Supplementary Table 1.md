# Supplementary Table 1 | Choosing the judge

How the judge was chosen, in two rounds (Supplementary Note 2). In round 1, 22 candidate judges each scored the same 107 answers; in round 2, 4 of them each scored the same 1,500 answers. Composite: the mean of three Pearson correlations, each between a judge score and a measure that needs no judge (correctness with semantic similarity to the expected answer, completeness with concept recall, citation quality with an automatic citation score). 95% interval: percentile interval over 2,000 bootstrap resamples of the answers. Judges are named by their Ollama tag; qwen3.8:27b-mlx is the MLX build of qwen3.8:27b (Methods). Answers scored: answers that received a score, of those sent.

| Round | Judge | Answers scored | Composite | 95% interval | Correctness against semantic similarity (r) | Completeness against concept recall (r) | Citation against citation score (r) |
|---|---|---|---|---|---|---|---|
| 1 (107 answers) | qwen3.8:27b-mlx | 107 of 107 | 0.53 | 0.451 to 0.608 | 0.47 | 0.762 | 0.357 |
| 1 (107 answers) | ministral-3:14b | 107 of 107 | 0.529 | 0.456 to 0.599 | 0.514 | 0.7 | 0.373 |
| 1 (107 answers) | devstral-small-2:24b | 107 of 107 | 0.503 | 0.410 to 0.583 | 0.549 | 0.667 | 0.291 |
| 1 (107 answers) | ministral-3:8b | 107 of 107 | 0.496 | 0.412 to 0.565 | 0.575 | 0.65 | 0.264 |
| 1 (107 answers) | gpt-oss:20b | 107 of 107 | 0.474 | 0.383 to 0.573 | 0.416 | 0.704 | 0.303 |
| 1 (107 answers) | gpt-oss:120b | 107 of 107 | 0.472 | 0.392 to 0.548 | 0.406 | 0.694 | 0.317 |
| 1 (107 answers) | gemma4:31b | 107 of 107 | 0.47 | 0.365 to 0.579 | 0.476 | 0.666 | 0.269 |
| 1 (107 answers) | qwen3.5:122b | 107 of 107 | 0.464 | 0.385 to 0.542 | 0.385 | 0.702 | 0.305 |
| 1 (107 answers) | qwen3-coder:latest | 107 of 107 | 0.463 | 0.367 to 0.543 | 0.559 | 0.71 | 0.119 |
| 1 (107 answers) | gemma4:26b | 107 of 107 | 0.46 | 0.356 to 0.564 | 0.496 | 0.646 | 0.24 |
| 1 (107 answers) | glm-4.7-flash:latest | 107 of 107 | 0.45 | 0.373 to 0.538 | 0.361 | 0.69 | 0.3 |
| 1 (107 answers) | gemma3:27b | 107 of 107 | 0.432 | 0.309 to 0.549 | 0.559 | 0.633 | 0.105 |
| 1 (107 answers) | ministral-3:3b | 107 of 107 | 0.43 | 0.335 to 0.510 | 0.447 | 0.51 | 0.332 |
| 1 (107 answers) | gemma3:27b-it-qat | 107 of 107 | 0.413 | 0.299 to 0.518 | 0.536 | 0.638 | 0.066 |
| 1 (107 answers) | qwen3-coder-next:q4_K_M | 107 of 107 | 0.405 | 0.313 to 0.491 | 0.47 | 0.605 | 0.141 |
| 1 (107 answers) | deepseek-r1:70b | 107 of 107 | 0.402 | 0.297 to 0.495 | 0.547 | 0.634 | 0.024 |
| 1 (107 answers) | qwen3:235b | 107 of 107 | 0.393 | 0.287 to 0.500 | 0.39 | 0.736 | 0.054 |
| 1 (107 answers) | olmo-3:latest | 103 of 107 | 0.375 | 0.280 to 0.447 | 0.396 | 0.642 | 0.088 |
| 1 (107 answers) | gemma3n:latest | 106 of 107 | 0.352 | 0.220 to 0.466 | 0.252 | 0.515 | 0.288 |
| 1 (107 answers) | gemma3:latest | 107 of 107 | 0.27 | 0.123 to 0.406 | 0.205 | 0.371 | 0.233 |
| 1 (107 answers) | mistral:latest | 107 of 107 | 0.242 | 0.101 to 0.373 | 0.364 | 0.198 | 0.163 |
| 1 (107 answers) | llama3.2:latest | 106 of 107 | 0.189 | 0.045 to 0.326 | 0.127 | 0.226 | 0.213 |
| 2 (1,500 answers) | qwen3.8:27b-mlx | 1,500 | 0.628 | 0.606 to 0.649 | 0.67 | 0.718 | 0.495 |
| 2 (1,500 answers) | devstral-small-2:24b | 1,500 | 0.576 | 0.553 to 0.598 | 0.715 | 0.631 | 0.381 |
| 2 (1,500 answers) | ministral-3:14b | 1,500 | 0.544 | 0.518 to 0.568 | 0.688 | 0.624 | 0.32 |
| 2 (1,500 answers) | qwen3-coder:latest | 1,500 | 0.537 | 0.510 to 0.562 | 0.712 | 0.609 | 0.29 |
