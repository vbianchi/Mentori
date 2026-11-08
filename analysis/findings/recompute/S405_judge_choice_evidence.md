# S405: the four judges of S404 compared, for D8 (13 October 2026)

Computed by scripts/S405_judge_choice_evidence.py (sha256 a482544b9b46) from the S404 plan (sha256 6ca17c0431ed), its ledger (3cfce804be64), the S376 ledger (753e7ee80a8d), S376b's reference measures of the 107 answers (S376_calibration_analysis.json), the 107 answer texts (for the citation count of section H) and the S377 passes; the JSON's provenance block lists every input with its sha256. Judges: devstral = devstral-small-2:24b, qwen3.8 = qwen3.8:27b-mlx, ministral = ministral-3:14b, qwen3-coder = qwen3-coder:latest. The composite is the mean of three Pearson r: correctness with semantic similarity, completeness with concept recall, citation quality with the citation composite. Intervals are 95% percentile intervals of paired resamples: S404's answer bootstrap (seed 20261012, 2,000 resamples) unless a section names another. This file reports numbers; the decision and its reasons are in notes/DECISIONS_2026-10-13.md. The 18 other judges of S376 are not computed here.

Gates passed before anything was written: G1, S404's table A reproduced to 0.0e+00; G2, S376b's composites on the 107 answers reproduced to 1.1e-16; G3, 1,500 scored ledger rows for each of the four judges, every row with the plan's sha256; G4, the plan's citation count and citation composite reproduced from the answer text to 0.0e+00 and S376b's citation composite of the 107 answers from final_citations to 0.0e+00; counts 1,151 answers with a citation and 349 without, 323 answers scored 0 on correctness by all four judges, and O50's counts of equal scores and equal text between the passes o50a and o50b of each judge.

## A. Each judge on the 1,500 answers

Per judge over the 1,500 answers: the composite (the mean of the three Pearson r), the three r and the share of answers with a correctness score of 3 or more; intervals from S404's answer bootstrap.

| Judge | n | Composite (95% CI) | Correctness with similarity | Completeness with concept recall | Citation quality with citation composite | Pass rate (95% CI) | Passes |
|---|---:|---|---:|---:|---:|---|---:|
| qwen3.8 | 1,500 | 0.628 (0.606 to 0.649) | 0.670 | 0.718 | 0.495 | 0.473 (0.449 to 0.499) | 710 |
| devstral | 1,500 | 0.576 (0.553 to 0.598) | 0.715 | 0.631 | 0.381 | 0.593 (0.569 to 0.618) | 890 |
| ministral | 1,500 | 0.544 (0.518 to 0.568) | 0.688 | 0.624 | 0.320 | 0.521 (0.497 to 0.545) | 782 |
| qwen3-coder | 1,500 | 0.537 (0.510 to 0.562) | 0.712 | 0.609 | 0.290 | 0.629 (0.604 to 0.653) | 943 |

## B. The six pairs of judges

For each pair (the judge with the higher composite first): the difference on the composite and on each of the three r over the 1,500 answers, with the interval from S404's answer bootstrap and, for the composite and the correctness r, from S404's question bootstrap (195 questions).

| Pair | Composite (95% CI) | Composite, question bootstrap | Correctness r (95% CI) | Correctness r, question bootstrap | Completeness r (95% CI) | Citation r (95% CI) |
|---|---|---|---|---|---|---|
| qwen3.8 - devstral | +0.052 (+0.040 to +0.064) | +0.038 to +0.066 | -0.045 (-0.057 to -0.034) | -0.061 to -0.028 | +0.087 (+0.071 to +0.102) | +0.114 (+0.086 to +0.144) |
| qwen3.8 - ministral | +0.084 (+0.066 to +0.103) | +0.062 to +0.105 | -0.018 (-0.036 to +0.002) | -0.041 to +0.008 | +0.094 (+0.075 to +0.113) | +0.175 (+0.130 to +0.225) |
| qwen3.8 - qwen3-coder | +0.091 (+0.073 to +0.111) | +0.069 to +0.114 | -0.042 (-0.063 to -0.021) | -0.066 to -0.016 | +0.109 (+0.088 to +0.132) | +0.206 (+0.158 to +0.254) |
| devstral - ministral | +0.032 (+0.015 to +0.051) | +0.013 to +0.051 | +0.027 (+0.010 to +0.047) | +0.005 to +0.052 | +0.007 (-0.010 to +0.025) | +0.061 (+0.018 to +0.109) |
| devstral - qwen3-coder | +0.039 (+0.020 to +0.058) | +0.019 to +0.061 | +0.003 (-0.017 to +0.024) | -0.018 to +0.027 | +0.023 (+0.003 to +0.044) | +0.091 (+0.043 to +0.139) |
| ministral - qwen3-coder | +0.007 (-0.015 to +0.028) | -0.014 to +0.030 | -0.024 (-0.043 to -0.006) | -0.044 to -0.003 | +0.016 (-0.006 to +0.038) | +0.031 (-0.028 to +0.085) |

## C. Citation presence

The 1,500 answers split by whether the answer text carries a citation (the plan's text_citation_count above 0: 1,151 with, 349 without); per judge the composite inside each group, with the interval from S404's answer bootstrap applied inside the group.

| Group | n | devstral | qwen3.8 | ministral | qwen3-coder |
|---|---:|---|---|---|---|
| with citation | 1,151 | 0.602 (0.576 to 0.627) | 0.601 (0.576 to 0.625) | 0.518 (0.487 to 0.546) | 0.517 (0.489 to 0.544) |
| without citation | 349 | 0.564 (0.513 to 0.614) | 0.593 (0.542 to 0.643) | 0.514 (0.464 to 0.566) | 0.547 (0.495 to 0.597) |

qwen3.8 minus devstral inside each group, on the composite and on each r: answer bootstrap and question bootstrap (the group's questions: 195 with citation, 174 without citation), both inside the group.

| Group | n | Quantity | Difference (95% CI) | Question bootstrap |
|---|---:|---|---|---|
| with citation | 1,151 | composite | -0.001 (-0.022 to +0.021) | -0.025 to +0.024 |
| with citation | 1,151 | correctness~semantic_similarity | -0.051 (-0.065 to -0.038) | -0.069 to -0.032 |
| with citation | 1,151 | completeness~concept_recall | +0.085 (+0.069 to +0.102) | +0.064 to +0.106 |
| with citation | 1,151 | citation_quality~cite_composite | -0.037 (-0.094 to +0.022) | -0.099 to +0.028 |
| without citation | 349 | composite | +0.029 (+0.008 to +0.050) | +0.009 to +0.049 |
| without citation | 349 | correctness~semantic_similarity | -0.033 (-0.063 to -0.005) | -0.060 to -0.006 |
| without citation | 349 | completeness~concept_recall | +0.087 (+0.040 to +0.137) | +0.029 to +0.134 |
| without citation | 349 | citation_quality~cite_composite | +0.034 (-0.013 to +0.080) | -0.009 to +0.081 |

Citation presence held fixed over the 1,500 answers: every score and every reference measure is centred on the mean of its group (with or without a citation) inside each resample, then the three r are taken over all answers; S404's answer bootstrap.

| Quantity | n | devstral | qwen3.8 | ministral | qwen3-coder | qwen3.8 minus devstral (95% CI) |
|---|---:|---:|---:|---:|---:|---|
| composite | 1,500 | 0.594 | 0.603 | 0.519 | 0.531 | +0.009 (-0.007 to +0.025) |
| correctness~semantic_similarity | 1,500 | 0.714 | 0.668 | 0.686 | 0.710 | -0.046 (-0.058 to -0.035) |
| completeness~concept_recall | 1,500 | 0.620 | 0.709 | 0.612 | 0.598 | +0.089 (+0.073 to +0.105) |
| citation_quality~cite_composite | 1,500 | 0.449 | 0.432 | 0.260 | 0.285 | -0.017 (-0.057 to +0.026) |

## D. Agreement between judges, no reference

For each pair of judges over the 1,500 answers: the quadratic-weighted kappa of their scores on each of the four dimensions, with the interval from S404's answer bootstrap.

| Pair | n | correctness | completeness | faithfulness | citation_quality |
|---|---:|---|---|---|---|
| devstral, qwen3.8 | 1,500 | 0.910 (0.900 to 0.919) | 0.876 (0.863 to 0.888) | 0.216 (0.164 to 0.267) | 0.651 (0.615 to 0.685) |
| devstral, ministral | 1,500 | 0.931 (0.916 to 0.943) | 0.932 (0.918 to 0.945) | 0.789 (0.754 to 0.819) | 0.619 (0.579 to 0.658) |
| devstral, qwen3-coder | 1,500 | 0.889 (0.871 to 0.905) | 0.876 (0.858 to 0.892) | 0.588 (0.543 to 0.633) | 0.547 (0.504 to 0.587) |
| qwen3.8, ministral | 1,500 | 0.910 (0.895 to 0.924) | 0.873 (0.855 to 0.889) | 0.254 (0.203 to 0.300) | 0.584 (0.543 to 0.620) |
| qwen3.8, qwen3-coder | 1,500 | 0.826 (0.806 to 0.844) | 0.801 (0.780 to 0.820) | 0.397 (0.332 to 0.454) | 0.541 (0.495 to 0.582) |
| ministral, qwen3-coder | 1,500 | 0.879 (0.862 to 0.895) | 0.852 (0.833 to 0.869) | 0.588 (0.547 to 0.629) | 0.499 (0.454 to 0.542) |

For each pair over the 1,500 answers: the share with the same score per dimension, the share with the same pass or fail (correctness of 3 or more), Cohen's kappa on pass and the counts of answers the first judge passes and the second fails, and the reverse.

| Pair (first, second) | Same score: correctness | Same score: completeness | Same score: faithfulness | Same score: citation_quality | Same pass or fail (95% CI) | Kappa on pass | First passes, second fails | First fails, second passes |
|---|---:|---:|---:|---:|---|---:|---:|---:|
| devstral, qwen3.8 | 0.602 | 0.528 | 0.465 | 0.515 | 0.875 (0.858 to 0.891) | 0.752 | 184 | 4 |
| devstral, ministral | 0.715 | 0.713 | 0.629 | 0.509 | 0.911 (0.897 to 0.925) | 0.820 | 121 | 13 |
| devstral, qwen3-coder | 0.720 | 0.631 | 0.607 | 0.523 | 0.927 (0.914 to 0.940) | 0.847 | 28 | 81 |
| qwen3.8, ministral | 0.629 | 0.567 | 0.430 | 0.431 | 0.907 (0.892 to 0.921) | 0.814 | 34 | 106 |
| qwen3.8, qwen3-coder | 0.515 | 0.463 | 0.589 | 0.485 | 0.835 (0.815 to 0.853) | 0.675 | 7 | 240 |
| ministral, qwen3-coder | 0.603 | 0.548 | 0.482 | 0.475 | 0.878 (0.861 to 0.893) | 0.753 | 11 | 172 |

## E. Correctness under other definitions

Spearman correlation of each judge's correctness score with semantic similarity over the 1,500 answers (ranks taken again inside every resample of S404's answer bootstrap), and qwen3.8 minus devstral.

| n | devstral | qwen3.8 | ministral | qwen3-coder | qwen3.8 minus devstral (95% CI) |
|---:|---|---|---|---|---|
| 1,500 | 0.705 (0.674 to 0.733) | 0.698 (0.667 to 0.728) | 0.696 (0.663 to 0.726) | 0.673 (0.639 to 0.705) | -0.006 (-0.019 to +0.006) |

The AUC of semantic similarity for a judge's pass, with pass set at a correctness score of 2, 3 and 4 or more (the number of passes in brackets), and two paired differences.

| Pass at | n | devstral | qwen3.8 | ministral | qwen3-coder | qwen3.8 minus devstral (95% CI) | devstral minus qwen3-coder (95% CI) |
|---|---:|---:|---:|---:|---:|---|---|
| 2 or more | 1,500 | 0.903 (1,026) | 0.885 (863) | 0.887 (935) | 0.920 (1,146) | -0.017 (-0.033 to -0.004) | -0.017 (-0.033 to -0.004) |
| 3 or more | 1,500 | 0.889 (890) | 0.851 (710) | 0.861 (782) | 0.875 (943) | -0.039 (-0.055 to -0.023) | +0.014 (+0.001 to +0.027) |
| 4 or more | 1,500 | 0.847 (577) | 0.810 (440) | 0.839 (590) | 0.840 (662) | -0.038 (-0.054 to -0.021) | +0.007 (-0.007 to +0.020) |

Pass rates brought close: devstral's pass at 3 or more against qwen3.8's pass at 2 or more, the AUC of similarity for each and the paired difference.

| n | devstral at 3: pass rate | devstral at 3: AUC | qwen3.8 at 2: pass rate | qwen3.8 at 2: AUC | AUC, qwen3.8 at 2 minus devstral at 3 (95% CI) |
|---:|---:|---:|---:|---:|---|
| 1,500 | 0.593 | 0.889 | 0.575 | 0.885 | -0.004 (-0.017 to +0.007) |

## F. Weights of the three r

With weight w on the correctness r and (1 - w) / 2 on each of the other two, over the 1,500 answers: the w at which qwen3.8's weighted composite equals devstral's (closed form, the weighted difference being linear in w), its interval from S404's answer bootstrap and the two points of a 0.01 grid on either side of it.

| n | Crossing w (95% CI) | Last grid w with qwen3.8 above | First grid w with devstral above | Resamples with no crossing between 0 and 1 |
|---:|---|---:|---:|---:|
| 1,500 | 0.691 (0.625 to 0.755) | 0.69 | 0.70 | 0 |

qwen3.8 minus devstral on the weighted composite at four values of w.

| w on correctness | n | qwen3.8 minus devstral (95% CI) |
|---:|---:|---|
| 0.60 | 1,500 | +0.013 (+0.004 to +0.023) |
| 0.65 | 1,500 | +0.006 (-0.004 to +0.015) |
| 0.70 | 1,500 | -0.001 (-0.011 to +0.008) |
| 0.80 | 1,500 | -0.016 (-0.026 to -0.006) |

## G. qwen3.8 minus devstral on the composite under other samples

The difference (+0.052 on the 1,500 answers) with the interval from a bootstrap of each unit: answers and questions with S404's scheme, then whole questions, generators, experiments and strata drawn with replacement (10,000 resamples, seed 20261013). The generators and the experiments are few and unequal clusters, so their intervals are a stress test and are not calibrated.

| Unit resampled | Units | Largest unit (answers) | Resamples | Seed | 95% CI | SD | Share of resamples above 0 |
|---|---:|---:|---:|---:|---|---:|---:|
| answers | 1,500 | 1 | 2,000 | 20261012 | +0.040 to +0.064 | 0.0061 | 1.0000 |
| questions | 195 | 8 | 2,000 | 20261012 | +0.038 to +0.066 | 0.0071 | 1.0000 |
| questions | 195 | 8 | 10,000 | 20261013 | +0.038 to +0.066 | 0.0070 | 1.0000 |
| generators | 18 | 821 | 10,000 | 20261013 | +0.035 to +0.064 | 0.0068 | 0.9993 |
| experiments | 13 | 530 | 10,000 | 20261013 | +0.035 to +0.069 | 0.0086 | 0.9997 |
| strata | 50 | 386 | 10,000 | 20261013 | +0.035 to +0.067 | 0.0079 | 1.0000 |

One experiment, generator or strategy family left out at a time: the range of the difference over the runs, and the lowest lower bound of its interval (S404's answer bootstrap inside the answers that remain).

| Left out, one at a time | Runs | n that remain | Difference, lowest to highest | Lowest lower bound | Left out at the lowest lower bound |
|---|---:|---|---|---:|---|
| experiment | 13 | 970 to 1,499 | +0.048 to +0.056 | +0.034 | S141 mini arm (step 4.3, s50) (393 answers) |
| generator | 18 | 679 to 1,498 | +0.049 to +0.053 | +0.031 | gemini::gemini-3-flash-preview (821 answers) |
| strategy family | 8 | 821 to 1,493 | +0.049 to +0.052 | +0.034 | rlm (679 answers) |

2,000 subsamples of the answers drawn without replacement at each size (seed 20261014): the share of subsamples in which each judge has the highest composite, and the share in which the interval difference +/- 1.960 * 0.00608 * sqrt(1,500 / n) lies above 0 (0.00608 is the SD of the answer-bootstrap differences on the 1,500).

| Subsample n | Subsamples | Highest: devstral | Highest: qwen3.8 | Highest: ministral | Highest: qwen3-coder | Half-width | Interval above 0 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 107 | 2,000 | 0.0110 | 0.9800 | 0.0050 | 0.0040 | 0.0446 | 0.6210 |
| 300 | 2,000 | 0.0005 | 0.9995 | 0.0000 | 0.0000 | 0.0266 | 0.9840 |
| 500 | 2,000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0206 | 1.0000 |
| 1,000 | 2,000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0146 | 1.0000 |

## H. The 107 answers of S376

Per judge on S376's 107 answers (current-key rows, 15 questions): the composite and the three r with S376b's reference measures, and the interval of the composite from S376b's bootstrap (seed 20261009).

| Judge | n | Composite (95% CI) | Correctness with similarity | Completeness with concept recall | Citation quality with citation composite |
|---|---:|---|---:|---:|---:|
| devstral | 107 | 0.503 (0.410 to 0.583) | 0.549 | 0.667 | 0.291 |
| qwen3.8 | 107 | 0.530 (0.451 to 0.608) | 0.470 | 0.762 | 0.357 |
| ministral | 107 | 0.529 (0.456 to 0.599) | 0.514 | 0.700 | 0.373 |
| qwen3-coder | 107 | 0.463 (0.367 to 0.543) | 0.559 | 0.710 | 0.119 |

qwen3.8 minus devstral on the 107 answers, on the composite and on each r, same bootstrap.

| Quantity | n | Difference (95% CI) |
|---|---:|---|
| composite | 107 | +0.027 (-0.029 to +0.093) |
| correctness~semantic_similarity | 107 | -0.079 (-0.152 to +0.002) |
| completeness~concept_recall | 107 | +0.095 (+0.043 to +0.150) |
| citation_quality~cite_composite | 107 | +0.066 (-0.083 to +0.231) |

The same composite when the citation composite of the 107 answers is computed from the count of citations in the answer text (S404's definition) in place of final_citations (S376b's input, the citations the run collected). The count in the text is 0 on 2 of the 107 answers, final_citations is 0 on 4 and both are 0 on 1; the two counts are equal on 5 of the 107 and the citation composite differs on 7.

| n | devstral | qwen3.8 | ministral | qwen3-coder | qwen3.8 minus devstral (95% CI) | Citation r, qwen3.8 minus devstral (95% CI) |
|---:|---:|---:|---:|---:|---|---|
| 107 | 0.546 | 0.591 | 0.568 | 0.487 | +0.045 (-0.006 to +0.100) | +0.119 (+0.008 to +0.239) |

Each judge's composite on the 107 answers in every pass on file: its S376 rows and the three O50 passes of S377 (S376b's reference measures).

| Judge | n | S376 rows | o50a | o50b | o50solo |
|---|---:|---:|---:|---:|---:|
| devstral | 107 | 0.5026 | 0.5034 | 0.5034 | 0.5034 |
| qwen3.8 | 107 | 0.5299 | 0.5295 | 0.5304 | 0.5317 |
| ministral | 107 | 0.5290 | 0.5290 | 0.5290 | 0.5290 |
| qwen3-coder | 107 | 0.4628 | 0.4628 | 0.4628 | no file |

Of the 107 answers, the number with equal scores (the four dimensions of the reply) and with equal text (the complete reply) in two passes of the same judge: o50a against o50b (both on Ollama 0.40.2), and the judge's S376 rows against o50a, with the Ollama versions of the S376 rows.

| Judge | n | o50a, o50b: equal scores | o50a, o50b: equal text | S376 rows, o50a: equal scores | S376 rows, o50a: equal text | Ollama of the S376 rows (rows) |
|---|---:|---:|---:|---:|---:|---|
| devstral | 107 | 107 of 107 | 107 of 107 | 104 of 107 | 99 of 107 | 0.40.1 (29), 0.40.2 (78) |
| qwen3.8 | 107 | 104 of 107 | 52 of 107 | 102 of 107 | 45 of 107 | 0.40.1 (29), 0.40.2 (78) |
| ministral | 107 | 107 of 107 | 107 of 107 | 107 of 107 | 89 of 107 | 0.40.1 (29), 0.40.2 (78) |
| qwen3-coder | 107 | 107 of 107 | 107 of 107 | 107 of 107 | 107 of 107 | 0.40.1 (29), 0.40.2 (78) |

## I. Pass rate by strategy family and by generator (indication only)

The 1,500 answers are a stratified calibration sample (strata of generator and strategy family; 821 answers from one generator), not the designs of the experiments, so the numbers below describe this sample and estimate no experiment's contrast.

Pass rate (correctness of 3 or more) per strategy family with 50 answers or more, under each judge.

| Strategy family | n | devstral | qwen3.8 | ministral | qwen3-coder |
|---|---:|---:|---:|---:|---:|
| rlm | 679 | 0.504 | 0.415 | 0.454 | 0.523 |
| verified_pass | 275 | 0.618 | 0.447 | 0.509 | 0.673 |
| single_pass | 252 | 0.714 | 0.540 | 0.603 | 0.762 |
| multi_hop | 176 | 0.580 | 0.477 | 0.557 | 0.642 |
| synthesizer | 90 | 0.911 | 0.833 | 0.833 | 0.911 |

The 5 groups from the highest pass rate to the lowest under each judge.

| Judge | Order |
|---|---|
| devstral | synthesizer > single_pass > verified_pass > multi_hop > rlm |
| qwen3.8 | synthesizer > single_pass > multi_hop > verified_pass > rlm |
| ministral | synthesizer > single_pass > multi_hop > verified_pass > rlm |
| qwen3-coder | synthesizer > single_pass > verified_pass > multi_hop > rlm |

Kendall tau-b between two judges' pass rates over the 5 groups, with the interval from S404's answer bootstrap.

| Pair | Groups | tau-b (95% CI) |
|---|---:|---|
| devstral, qwen3.8 | 5 | 0.80 (0.60 to 1.00) |
| devstral, ministral | 5 | 0.80 (0.60 to 1.00) |
| devstral, qwen3-coder | 5 | 1.00 (0.80 to 1.00) |
| qwen3.8, ministral | 5 | 1.00 (0.60 to 1.00) |
| qwen3.8, qwen3-coder | 5 | 0.80 (0.60 to 1.00) |
| ministral, qwen3-coder | 5 | 0.80 (0.60 to 1.00) |

Pairs of these groups that two of the judges order differently (1): the first group's pass rate minus the second's under each judge, with the interval from S404's answer bootstrap.

| Pair (first minus second) | n of the two groups | devstral | qwen3.8 | ministral | qwen3-coder |
|---|---|---|---|---|---|
| verified_pass - multi_hop | 275, 176 | +0.039 (-0.053 to +0.135) | -0.030 (-0.123 to +0.067) | -0.048 (-0.145 to +0.053) | +0.031 (-0.058 to +0.125) |

Pass rate (correctness of 3 or more) per generator with 30 answers or more, under each judge.

| Generator | n | devstral | qwen3.8 | ministral | qwen3-coder |
|---|---:|---:|---:|---:|---:|
| gemini-3-flash-preview | 821 | 0.625 | 0.521 | 0.551 | 0.658 |
| claude-haiku-4-5 | 144 | 0.562 | 0.486 | 0.521 | 0.625 |
| nemotron-3-nano:30b | 136 | 0.500 | 0.279 | 0.426 | 0.581 |
| gemma3:27b | 120 | 0.508 | 0.350 | 0.417 | 0.542 |
| glm-4.7-flash:latest | 120 | 0.425 | 0.317 | 0.367 | 0.467 |
| qwen3-coder:latest | 39 | 0.615 | 0.487 | 0.538 | 0.590 |
| qwen3.5:122b | 34 | 0.824 | 0.706 | 0.735 | 0.853 |

The 7 groups from the highest pass rate to the lowest under each judge.

| Judge | Order |
|---|---|
| devstral | qwen3.5:122b > gemini-3-flash-preview > qwen3-coder:latest > claude-haiku-4-5 > gemma3:27b > nemotron-3-nano:30b > glm-4.7-flash:latest |
| qwen3.8 | qwen3.5:122b > gemini-3-flash-preview > qwen3-coder:latest > claude-haiku-4-5 > gemma3:27b > glm-4.7-flash:latest > nemotron-3-nano:30b |
| ministral | qwen3.5:122b > gemini-3-flash-preview > qwen3-coder:latest > claude-haiku-4-5 > nemotron-3-nano:30b > gemma3:27b > glm-4.7-flash:latest |
| qwen3-coder | qwen3.5:122b > gemini-3-flash-preview > claude-haiku-4-5 > qwen3-coder:latest > nemotron-3-nano:30b > gemma3:27b > glm-4.7-flash:latest |

Kendall tau-b between two judges' pass rates over the 7 groups, with the interval from S404's answer bootstrap.

| Pair | Groups | tau-b (95% CI) |
|---|---:|---|
| devstral, qwen3.8 | 7 | 0.90 (0.52 to 1.00) |
| devstral, ministral | 7 | 0.90 (0.62 to 1.00) |
| devstral, qwen3-coder | 7 | 0.81 (0.52 to 1.00) |
| qwen3.8, ministral | 7 | 0.81 (0.52 to 1.00) |
| qwen3.8, qwen3-coder | 7 | 0.71 (0.33 to 0.90) |
| ministral, qwen3-coder | 7 | 0.90 (0.52 to 1.00) |

Pairs of these groups that two of the judges order differently (3): the first group's pass rate minus the second's under each judge, with the interval from S404's answer bootstrap.

| Pair (first minus second) | n of the two groups | devstral | qwen3.8 | ministral | qwen3-coder |
|---|---|---|---|---|---|
| claude-haiku-4-5 - qwen3-coder:latest | 144, 39 | -0.053 (-0.225 to +0.118) | -0.001 (-0.178 to +0.174) | -0.018 (-0.195 to +0.160) | +0.035 (-0.142 to +0.210) |
| nemotron-3-nano:30b - gemma3:27b | 136, 120 | -0.008 (-0.137 to +0.117) | -0.071 (-0.179 to +0.041) | +0.010 (-0.105 to +0.134) | +0.039 (-0.081 to +0.162) |
| nemotron-3-nano:30b - glm-4.7-flash:latest | 136, 120 | +0.075 (-0.048 to +0.196) | -0.037 (-0.145 to +0.069) | +0.060 (-0.063 to +0.176) | +0.114 (-0.008 to +0.238) |

## J. Faithfulness (in no term of the composite)

On the 323 answers that all four judges score 0 on correctness: each judge's mean faithfulness score and the number of those answers it scores 5 and 0 on faithfulness.

| Judge | n | Mean faithfulness | Scored 5 | Scored 0 |
|---|---:|---:|---:|---:|
| devstral | 323 | 0.91 | 39 | 251 |
| qwen3.8 | 323 | 4.15 | 266 | 53 |
| ministral | 323 | 1.26 | 76 | 238 |
| qwen3-coder | 323 | 2.72 | 161 | 138 |

Over the 1,500 answers: each judge's mean faithfulness score and the Pearson r of its faithfulness with its own correctness.

| Judge | n | Mean faithfulness | r with own correctness |
|---|---:|---:|---:|
| devstral | 1,500 | 3.27 | 0.790 |
| qwen3.8 | 1,500 | 4.08 | 0.312 |
| ministral | 1,500 | 3.11 | 0.720 |
| qwen3-coder | 1,500 | 3.92 | 0.545 |
