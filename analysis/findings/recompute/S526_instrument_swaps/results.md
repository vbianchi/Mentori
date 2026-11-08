# The swaps behind the thesis

Written by scripts/S526_instrument_swaps.py, sha256 d000347e37f5794d. Gap: RLM-10 minus single pass, in points. Intervals: 10,000 question resamples, seed 20261013. Every gate passed before this was written: 29 of 29.

## The numbers the thesis states

| Number | Value | 95% interval | First stated at |
|---|---:|---|---|
| judge to concepts, change in the gap | 15.37 | 6.76 to 24.32 | instruments.md:7 |
| judge to concepts, noise | 3.5 |  | instruments.md:7 |
| judge to concepts, one-paper | 28.28 | 18.66 to 38.02 | instruments.md:7 |
| Mentori minus package, cap 10 | 10.9 | 4.78 to 16.73 | instruments.md:8 |
| source lists, change in the gap | 17.6 | 15.0 to 20.33 | instruments.md:11 |
| single pass, April answers, devstral, at 4 | 33.7 |  | compare.md:29 |
| single pass, re-run, at 4 | 83.3 |  | compare.md:29 |

## Every swap

| Swap | Questions | Gap before | Gap after | Change | 95% interval | Noise |
|---|---:|---:|---:|---:|---|---:|
| pass mark 4 to 3, all 86 | 86 | -8.53 | -1.16 | 7.36 | -0.0 to 14.73 | 3.5 |
| pass mark 4 to 3, one-paper 60 | 60 | -26.67 | -10.56 | 16.11 | 8.89 to 23.33 |  |
| pass mark 4 to 3, many-paper 26 | 26 | 33.33 | 20.51 | -12.82 | -28.21 to 2.56 |  |
| pass mark 4 to 5, all 86 | 86 | -8.53 | -25.97 | -17.44 | -26.74 to -8.14 |  |
| judge plain to passages, pass at 4 | 86 | -8.53 | -14.53 | -6.01 | -11.63 to -0.97 | 3.5 |
| judge plain to passages, pass at 3 | 86 | -1.16 | -5.04 | -3.88 | -8.53 to 0.0 | 2.3 |
| judge plain to passages, one-paper, pass at 4 | 60 | -26.67 | -27.78 | -1.11 | -6.11 to 3.06 |  |
| judge plain to passages, many-paper, pass at 4 | 26 | 33.33 | 16.03 | -17.31 | -30.77 to -5.13 |  |
| judge plain to passages, mean faithfulness (0-100 scale, score x 20) | 86 | -11.43 | -14.96 | -3.53 | -6.2 to -0.85 |  |
| judge plain to passages, mean citation_quality (0-100 scale, score x 20) | 86 | -3.95 | -19.07 | -15.12 | -19.11 to -11.12 |  |
| judge plain to passages, mean correctness (0-100 scale, score x 20) | 86 | -8.18 | -11.47 | -3.29 | -5.27 to -1.32 |  |
| judge plain to passages, mean completeness (0-100 scale, score x 20) | 86 | -1.32 | -9.22 | -7.91 | -10.04 to -5.74 |  |
| MiniCheck key to papers precision, as stored (draw 1) | 81 | -28.16 | -25.49 | 2.66 | -3.61 to 9.38 | 0.2 |
| MiniCheck key to papers precision, source lists dropped (draw 1) | 81 | -18.18 | -7.89 | 10.29 | 4.09 to 17.02 | 0.2 |
| MiniCheck key F1 to papers precision, as stored (draw 1) | 80 | -11.96 | -24.81 | -12.85 | -19.01 to -6.24 |  |
| MiniCheck papers precision, source lists kept to dropped | 81 | -25.49 | -7.89 | 17.6 | 15.0 to 20.33 |  |
| MiniCheck key to papers, as stored, verified_pass minus rlm_10 | 81 | 32.39 | 28.33 | -4.06 | -10.39 to 2.05 |  |
| MiniCheck key to papers, source dropped, one-paper | 58 | -22.13 | -8.34 | 13.79 | 5.8 to 22.34 |  |
| MiniCheck key to papers, source dropped, many-paper | 23 | -8.23 | -6.77 | 1.46 | -6.6 to 9.11 |  |
| exp04 MiniCheck key precision to source k3 precision | 86 | -15.26 | -18.67 | -3.41 | -8.98 to 2.37 |  |
| exp04 MiniCheck key F1 to source k3 precision | 86 | 8.83 | -18.67 | -27.5 | -33.67 to -21.19 |  |
| exp04 MiniCheck key F1 to source k3, verified_pass minus rlm_10 | 86 | -11.04 | 22.4 | 33.44 | 26.86 to 39.89 |  |
| old judge (corrected state, key v1) to devstral (key v2.4), exp04, pass at 3 | 86 | 11.63 | 11.63 | 0.0 | -6.98 to 6.98 |  |
| old judge (published, key v1) to devstral (key v2.4), exp04, pass at 3 | 86 | 10.47 | 11.63 | 1.16 | -5.81 to 8.14 |  |
| old judge to devstral, exp04, verified_pass minus rlm_10, at 3 | 86 | -24.42 | -31.4 | -6.98 | -16.28 to 2.33 |  |
| submitted answers (exp04) to re-run (G1 3 draws), devstral v2.4, pass at 3 | 86 | 11.63 | -1.16 | -12.79 | -24.42 to -1.16 | 2.3 |
| old judge (corrected state, key v1) to devstral (key v2.4), exp04, pass at 4 | 86 | 24.42 | 33.72 | 9.3 | -3.49 to 22.09 |  |
| old judge (published, key v1) to devstral (key v2.4), exp04, pass at 4 | 86 | 20.93 | 33.72 | 12.79 | 0.0 to 25.58 |  |
| old judge to devstral, exp04, verified_pass minus rlm_10, at 4 | 86 | -38.37 | -41.86 | -3.49 | -16.28 to 9.3 |  |
| submitted answers (exp04) to re-run (G1 3 draws), devstral v2.4, pass at 4 | 86 | 33.72 | -8.53 | -42.25 | -60.85 to -24.02 | 3.5 |
| key v2.4 to v2.5, judge plain, changed answerable, pass at 4 | 54 | -6.79 | -7.41 | -0.62 | -3.7 to 2.47 | 9.2 |
| key v2.4 to v2.5, judge plain, all 86, pass at 4 | 86 | -8.53 | -8.91 | -0.39 | -2.33 to 1.55 | 3.5 |
| key v2.4 to v2.5, judge plain, one-paper, pass at 4 | 60 | -26.67 | -26.11 | 0.56 | -1.11 to 2.22 |  |
| key v2.4 to v2.5, judge plain, many-paper, pass at 4 | 26 | 33.33 | 30.77 | -2.56 | -7.69 to 2.56 |  |
| key v2.4 to v2.5, judge plain, changed answerable, pass at 3 | 54 | 0.0 | 0.0 | 0.0 | 0.0 to 0.0 | 5.6 |
| key v2.4 to v2.5, judge plain, all 86, pass at 3 | 86 | -1.16 | -1.16 | 0.0 | 0.0 to 0.0 | 2.3 |
| key v2.4 to v2.5, judge plain, one-paper, pass at 3 | 60 | -10.56 | -10.56 | 0.0 | 0.0 to 0.0 |  |
| key v2.4 to v2.5, judge plain, many-paper, pass at 3 | 26 | 20.51 | 20.51 | 0.0 | 0.0 to 0.0 |  |
| concept v2.4 loose to v2.5 D181, all 86 | 86 | 8.45 | 6.85 | -1.6 | -5.19 to 1.89 | 2.7 |
| concept v2.4 loose to v2.5 loose base (key only), all 86 | 86 | 8.45 | 5.3 | -3.15 | -5.92 to -0.6 | 2.7 |
| concept v2.5 loose base to v2.5 D181 (question rule only), all 86 | 86 | 5.3 | 6.85 | 1.55 | -0.36 to 3.61 | 2.7 |
| concept v2.4 loose to v2.5 D181, changed judge questions | 54 | 10.86 | 6.28 | -4.58 | -9.56 to 0.43 | 2.7 |
| concept v2.4 loose to v2.5 D181, one-paper | 60 | 1.46 | 1.62 | 0.16 | -4.16 to 4.39 |  |
| concept v2.4 loose to v2.5 D181, many-paper | 26 | 24.59 | 18.92 | -5.67 | -11.71 to 0.05 |  |
| signal swap: judge pass at 4 to concept recall D181, all 86 | 86 | -8.53 | 6.85 | 15.37 | 6.76 to 24.32 | 3.5 |
| signal swap: judge pass at 4 to concept recall D181, one-paper | 60 | -26.67 | 1.62 | 28.28 | 18.66 to 38.02 |  |
| signal swap: judge pass at 4 to concept recall D181, many-paper | 26 | 33.33 | 18.92 | -14.42 | -26.83 to -1.72 |  |
| signal swap: judge pass at 4 to MiniCheck papers source dropped, draw 1 | 81 | -6.17 | -7.89 | -1.72 | -13.13 to 10.28 |  |
