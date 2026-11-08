# S404 extended judge calibration on ground truth v2.4 (2026-10-13 07:33)

1500 of 1500 planned answers scored by all of devstral-small-2:24b, qwen3.8:27b-mlx, ministral-3:14b, qwen3-coder:latest. Bootstrap 2000 resamples, seed 20261012. A1: S376b reproduced to 1.1e-16.

## Rule (the plan's, written before the run)

The judge with the highest composite in table A (the answers all four judges scored) is selected if the 95% interval of its difference from every other judge, over 2,000 paired bootstrap resamples of those answers (seed 20261012), excludes 0. Otherwise the result is a tie among it and every judge whose interval with it includes 0, and D8 is decided among the tied judges by the O50 repeatability results (S377).

The result below is computed by this script's code (analyze(), the block that sets decision), which reads neither text. Script sha256 042accc8dfb6; the plan was written by script sha256 042accc8dfb6 (the same).

## Result

qwen3.8:27b-mlx is selected: its interval excludes 0 against every other judge

R2 at the end of the run: passed on every server, as at the start.

## A. Answers scored by every judge

| Judge | Composite (95% CI) | Corr~sim | Compl~recall | Cite~cite | Question bootstrap CI |
|---|---|---:|---:|---:|---|
| qwen3.8:27b-mlx | 0.628 (0.606 to 0.649) | 0.670 | 0.718 | 0.495 | 0.598 to 0.656 |
| devstral-small-2:24b | 0.576 (0.553 to 0.598) | 0.715 | 0.631 | 0.381 | 0.543 to 0.604 |
| ministral-3:14b | 0.544 (0.518 to 0.568) | 0.688 | 0.624 | 0.320 | 0.512 to 0.574 |
| qwen3-coder:latest | 0.537 (0.510 to 0.562) | 0.712 | 0.609 | 0.290 | 0.504 to 0.569 |

| Pair (higher composite first) | Difference | 95% CI | Resamples first ahead | Question bootstrap CI |
|---|---:|---|---:|---|
| qwen3.8:27b-mlx - devstral-small-2:24b | +0.052 | +0.040 to +0.064 | 1.000 | +0.038 to +0.066 |
| qwen3.8:27b-mlx - ministral-3:14b | +0.084 | +0.066 to +0.103 | 1.000 | +0.062 to +0.105 |
| qwen3.8:27b-mlx - qwen3-coder:latest | +0.091 | +0.073 to +0.111 | 1.000 | +0.069 to +0.114 |
| devstral-small-2:24b - ministral-3:14b | +0.032 | +0.015 to +0.051 | 1.000 | +0.013 to +0.051 |
| devstral-small-2:24b - qwen3-coder:latest | +0.039 | +0.020 to +0.058 | 1.000 | +0.019 to +0.061 |
| ministral-3:14b - qwen3-coder:latest | +0.007 | -0.015 to +0.028 | 0.757 | -0.014 to +0.030 |

## Reported, not used by the rule

Each judge on all the answers it scored (S376b's table A):

| Judge | Scored / calls | Statuses | Composite (95% CI) |
|---|---|---|---|
| devstral-small-2:24b | 1500/1500 | ok 1500 | 0.576 (0.553 to 0.598) |
| qwen3.8:27b-mlx | 1500/1500 | ok 1500 | 0.628 (0.606 to 0.649) |
| ministral-3:14b | 1500/1500 | ok 1500 | 0.544 (0.518 to 0.568) |
| qwen3-coder:latest | 1500/1500 | ok 1500 | 0.537 (0.510 to 0.562) |

Table B, without the answers of each judge's own developer:

| Judge | n | Composite (95% CI) |
|---|---:|---|
| devstral-small-2:24b | 1487 | 0.575 (0.553 to 0.598) |
| qwen3.8:27b-mlx | 1399 | 0.632 (0.610 to 0.654) |
| ministral-3:14b | 1487 | 0.544 (0.518 to 0.568) |
| qwen3-coder:latest | 1399 | 0.540 (0.512 to 0.567) |

| Pair, on answers of neither developer | n | 95% CI |
|---|---:|---|
| qwen3.8:27b-mlx - devstral-small-2:24b | 1386 | +0.042 to +0.067 |
| qwen3.8:27b-mlx - ministral-3:14b | 1386 | +0.068 to +0.108 |
| qwen3.8:27b-mlx - qwen3-coder:latest | 1399 | +0.072 to +0.113 |
| devstral-small-2:24b - ministral-3:14b | 1487 | +0.014 to +0.050 |
| devstral-small-2:24b - qwen3-coder:latest | 1386 | +0.018 to +0.058 |
| ministral-3:14b - qwen3-coder:latest | 1386 | -0.016 to +0.027 |

Table A with the citation composite of the 20 generator-selection (exp00) answers computed from final_citations, S376b's input, instead of the count of the answer text:

| Judge | Composite |
|---|---:|
| qwen3.8:27b-mlx | 0.627 |
| devstral-small-2:24b | 0.576 |
| ministral-3:14b | 0.544 |
| qwen3-coder:latest | 0.537 |

| Pair | 95% CI |
|---|---|
| qwen3.8:27b-mlx - devstral-small-2:24b | +0.040 to +0.064 |
| qwen3.8:27b-mlx - ministral-3:14b | +0.065 to +0.103 |
| qwen3.8:27b-mlx - qwen3-coder:latest | +0.071 to +0.110 |
| devstral-small-2:24b - ministral-3:14b | +0.015 to +0.051 |
| devstral-small-2:24b - qwen3-coder:latest | +0.019 to +0.057 |
| ministral-3:14b - qwen3-coder:latest | -0.015 to +0.027 |

R2, the three S376 answers judged again on each server at the start of a session (start) and when its queue is empty (end), every session:

| Judge | Machine | Port | Ollama | Digest | Start: passed lines | Start: failed lines | Start: S376's text | Start: S376's scores | Text check waived | End: lines | End: passed | End: S376's text | End: S376's scores |
|---|---|---:|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|
| devstral-small-2:24b | Bioinfos-Mac-Studio.local | 11451 | 0.40.2 | 33af3142213a | 3 | 0 | 3 | 3 | no | 3 | 3 | 3 | 3 |
| qwen3.8:27b-mlx | Bioinfos-Mac-Studio.local | 11462 | 0.40.2 | 5642e97495e1 | 3 | 0 | 0 | 3 | yes | 3 | 3 | 0 | 3 |
| ministral-3:14b | Bioinfos-Mac-Studio.local | 11453 | 0.40.2 | 129e04c05b56 | 3 | 0 | 3 | 3 | no | 3 | 3 | 3 | 3 |
| qwen3-coder:latest | Bioinfos-Mac-Studio.local | 11452 | 0.40.2 | 06c1097efce0 | 3 | 0 | 3 | 3 | no | 3 | 3 | 3 | 3 |

Plan sha256 6ca17c0431ed (citation count: text), key sha256 5d8362ae931d, script sha256 042accc8dfb6, ledgers <repo>/findings/recompute/S404/S404_calibration_extended.jsonl 3cfce804be64.
