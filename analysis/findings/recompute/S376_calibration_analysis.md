# S376 judge calibration against ground truth v2.4

Ledger S376_judge_calibration.jsonl: 2354 judge calls, 22 judges. Reference measures on the 107 answers against v2.4 (similarity on complete answers; 0 answers past BGE-M3's limit). Composite = mean of the three Pearson r, as in the original. Bootstrap 2000 resamples, seed 20261009.

## A. All 107 answers

| Rank | Judge | Group | Scored | Composite (95% CI) | Corr~sim | Compl~recall | Cite~cite | Diff vs qwen3-coder (95% CI) | Original composite |
|---:|---|---|---:|---|---:|---:|---:|---|---:|
| 1 | qwen3.8:27b-mlx | later_check | 107/107 | 0.530 (0.451 to 0.608) | 0.470 | 0.762 | 0.357 | +0.000 to +0.151 | nan |
| 2 | ministral-3:14b | selection | 107/107 | 0.529 (0.456 to 0.599) | 0.514 | 0.700 | 0.373 | +0.009 to +0.140 | 0.512 |
| 3 | devstral-small-2:24b | selection | 107/107 | 0.503 (0.410 to 0.583) | 0.549 | 0.667 | 0.291 | -0.033 to +0.123 | 0.545 |
| 4 | ministral-3:8b | selection | 107/107 | 0.496 (0.412 to 0.565) | 0.575 | 0.650 | 0.264 | -0.048 to +0.120 | 0.464 |
| 5 | gpt-oss:20b | selection | 107/107 | 0.474 (0.383 to 0.573) | 0.416 | 0.704 | 0.303 | -0.063 to +0.107 | 0.512 |
| 6 | gpt-oss:120b | selection | 107/107 | 0.472 (0.392 to 0.548) | 0.406 | 0.694 | 0.317 | -0.057 to +0.087 | 0.554 |
| 7 | gemma4:31b | later_check | 107/107 | 0.470 (0.365 to 0.579) | 0.476 | 0.666 | 0.269 | -0.074 to +0.108 | nan |
| 8 | qwen3.5:122b | selection | 107/107 | 0.464 (0.385 to 0.542) | 0.385 | 0.702 | 0.305 | -0.078 to +0.099 | 0.531 |
| 9 | qwen3-coder:latest | selection | 107/107 | 0.463 (0.367 to 0.543) | 0.559 | 0.710 | 0.119 | +0.000 to +0.000 | 0.567 |
| 10 | gemma4:26b | later_check | 107/107 | 0.460 (0.356 to 0.564) | 0.496 | 0.646 | 0.240 | -0.090 to +0.097 | nan |
| 11 | glm-4.7-flash:latest | selection | 107/107 | 0.450 (0.373 to 0.538) | 0.361 | 0.690 | 0.300 | -0.084 to +0.088 | 0.349 |
| 12 | gemma3:27b | selection | 107/107 | 0.432 (0.309 to 0.549) | 0.559 | 0.633 | 0.105 | -0.144 to +0.066 | 0.502 |
| 13 | ministral-3:3b | selection | 107/107 | 0.430 (0.335 to 0.510) | 0.447 | 0.510 | 0.332 | -0.123 to +0.066 | 0.470 |
| 14 | gemma3:27b-it-qat | selection | 107/107 | 0.413 (0.299 to 0.518) | 0.536 | 0.638 | 0.066 | -0.159 to +0.047 | 0.502 |
| 15 | qwen3-coder-next:q4_K_M | selection | 107/107 | 0.405 (0.313 to 0.491) | 0.470 | 0.605 | 0.141 | -0.153 to +0.042 | 0.499 |
| 16 | deepseek-r1:70b | selection | 107/107 | 0.402 (0.297 to 0.495) | 0.547 | 0.634 | 0.024 | -0.171 to +0.039 | 0.468 |
| 17 | qwen3:235b | selection | 107/107 | 0.393 (0.287 to 0.500) | 0.390 | 0.736 | 0.054 | -0.153 to +0.034 | 0.406 |
| 18 | olmo-3:latest | selection | 103/107 | 0.375 (0.280 to 0.447) | 0.396 | 0.642 | 0.088 | -0.186 to +0.001 | 0.285 |
| 19 | gemma3n:latest | selection | 106/107 | 0.352 (0.220 to 0.466) | 0.252 | 0.515 | 0.288 | -0.246 to +0.014 | 0.511 |
| 20 | gemma3:latest | selection | 107/107 | 0.270 (0.123 to 0.406) | 0.205 | 0.371 | 0.233 | -0.355 to -0.037 | 0.395 |
| 21 | mistral:latest | selection | 107/107 | 0.242 (0.101 to 0.373) | 0.364 | 0.198 | 0.163 | -0.355 to -0.094 | 0.214 |
| 22 | llama3.2:latest | selection | 106/107 | 0.189 (0.045 to 0.326) | 0.127 | 0.226 | 0.213 | -0.428 to -0.131 | 0.296 |

## B. Without the answers of each judge's own developer

| Rank | Judge | Group | Scored | Composite (95% CI) | Corr~sim | Compl~recall | Cite~cite | Diff vs qwen3-coder (95% CI) | Original composite |
|---:|---|---|---:|---|---:|---:|---:|---|---:|
| 1 | qwen3.8:27b-mlx | later_check | 79/107 | 0.530 (0.435 to 0.621) | 0.440 | 0.753 | 0.396 | -0.022 to +0.161 | nan |
| 2 | ministral-3:14b | selection | 93/107 | 0.526 (0.444 to 0.609) | 0.558 | 0.699 | 0.320 | -0.014 to +0.150 | 0.512 |
| 3 | ministral-3:8b | selection | 93/107 | 0.504 (0.414 to 0.583) | 0.618 | 0.647 | 0.247 | -0.068 to +0.143 | 0.464 |
| 4 | devstral-small-2:24b | selection | 93/107 | 0.493 (0.388 to 0.587) | 0.586 | 0.667 | 0.226 | -0.056 to +0.128 | 0.545 |
| 5 | gpt-oss:20b | selection | 92/107 | 0.489 (0.383 to 0.594) | 0.380 | 0.736 | 0.352 | -0.090 to +0.146 | 0.512 |
| 6 | gpt-oss:120b | selection | 92/107 | 0.488 (0.399 to 0.573) | 0.390 | 0.725 | 0.351 | -0.074 to +0.119 | 0.554 |
| 7 | qwen3-coder:latest | selection | 79/107 | 0.473 (0.356 to 0.561) | 0.558 | 0.702 | 0.160 | +0.000 to +0.000 | 0.567 |
| 8 | glm-4.7-flash:latest | selection | 107/107 | 0.450 (0.373 to 0.538) | 0.361 | 0.690 | 0.300 | -0.102 to +0.095 | 0.349 |
| 9 | qwen3.5:122b | selection | 79/107 | 0.447 (0.351 to 0.543) | 0.338 | 0.695 | 0.307 | -0.117 to +0.094 | 0.531 |
| 10 | gemma4:26b | later_check | 77/107 | 0.445 (0.320 to 0.564) | 0.504 | 0.591 | 0.240 | -0.144 to +0.107 | nan |
| 11 | gemma4:31b | later_check | 77/107 | 0.442 (0.315 to 0.570) | 0.479 | 0.612 | 0.235 | -0.139 to +0.097 | nan |
| 12 | ministral-3:3b | selection | 93/107 | 0.435 (0.326 to 0.526) | 0.492 | 0.530 | 0.283 | -0.137 to +0.074 | 0.470 |
| 13 | gemma3:27b | selection | 77/107 | 0.429 (0.299 to 0.561) | 0.571 | 0.596 | 0.120 | -0.173 to +0.077 | 0.502 |
| 14 | gemma3:27b-it-qat | selection | 77/107 | 0.424 (0.302 to 0.542) | 0.525 | 0.671 | 0.076 | -0.172 to +0.064 | 0.502 |
| 15 | qwen3-coder-next:q4_K_M | selection | 79/107 | 0.400 (0.289 to 0.504) | 0.437 | 0.594 | 0.168 | -0.190 to +0.059 | 0.499 |
| 16 | deepseek-r1:70b | selection | 99/107 | 0.387 (0.272 to 0.488) | 0.476 | 0.636 | 0.049 | -0.211 to +0.034 | 0.468 |
| 17 | olmo-3:latest | selection | 103/107 | 0.375 (0.280 to 0.447) | 0.396 | 0.642 | 0.088 | -0.206 to +0.006 | 0.285 |
| 18 | qwen3:235b | selection | 79/107 | 0.372 (0.242 to 0.504) | 0.356 | 0.714 | 0.045 | -0.195 to +0.028 | 0.406 |
| 19 | gemma3n:latest | selection | 77/107 | 0.335 (0.187 to 0.460) | 0.299 | 0.456 | 0.251 | -0.290 to +0.006 | 0.511 |
| 20 | gemma3:latest | selection | 77/107 | 0.277 (0.114 to 0.425) | 0.290 | 0.332 | 0.210 | -0.373 to -0.011 | 0.395 |
| 21 | mistral:latest | selection | 93/107 | 0.213 (0.086 to 0.334) | 0.397 | 0.260 | -0.019 | -0.398 to -0.102 | 0.214 |
| 22 | llama3.2:latest | selection | 106/107 | 0.189 (0.045 to 0.326) | 0.127 | 0.226 | 0.213 | -0.441 to -0.130 | 0.296 |

## O9 (fixed before the run)

- gemma4:26b: composite 0.460 against 0.463; difference -0.090 to +0.097: not a winner under O9
- gemma4:31b: composite 0.470 against 0.463; difference -0.074 to +0.108: not a winner under O9
- qwen3.8:27b-mlx: composite 0.530 against 0.463; difference +0.000 to +0.151: INDISPUTABLE WINNER under O9

