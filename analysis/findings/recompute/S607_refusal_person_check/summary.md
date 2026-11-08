# S607: the person's refusal check against the judge (D223, D227, D306)

Script `scripts/S607_refusal_person_check.py` sha256 `feaf879914cd1734657217b61ca5da3b0538e500d2e4a8ccb9e8fa93658fab37`, commit `5a6fdeaaa`, written 2026-11-08T15:06:31+00:00.
Command: `uv run python scripts/S607_refusal_person_check.py`.

Inputs (sha256), outside git:

- `~/Mentori_scratch_keep/refusal_check_2026-11/refusal_check_done_20261103.xlsx` `67656c4e527b4da3b68614783d1e560874ebaff3bdbdfa3ee5189d1f07e4df45`
- `~/Mentori_scratch_keep/refusal_check_2026-11/refusal_check_KEY.csv` `fcf0b8688f35bfdeaeb7fb2f76a5f4ea09dd82828adfa3fba3a5016488bb3a47`
- `~/Mentori_scratch_keep/refusal_check_2026-11/comparison_20261103.md` `664204a47c38e4180b0cc5a82adbaa5709c9db1f3e40a85e4b091bcd27992e19`

REPRODUCED comparison_20261103.md: the 3 breakdown rows of each strategy, the D227 and re-reading tables, agreement 77 of 78.

Valerio's blind reading (D223) of the 78 answers of single pass and Mentori RLM-10 to the 39 out-of-scope questions, draw 1 of Figure 3's run, against the judge's refusal (score 3 or more). Counts of answers.
No per-row reading is written here (D306).

## Final reading (D227: partly counts as refused; D227 note: R24, R48 refused, R65 answered)

| | person refused | judge refused | agreement | both refused | person only | judge only | both not | kappa |
|---|---|---|---|---|---|---|---|---|
| Single pass | 39 of 39 | 39 of 39 | 39 of 39 | 39 | 0 | 0 | 0 | not defined |
| RLM-10 | 38 of 39 | 39 of 39 | 38 of 39 | 38 | 0 | 1 | 0 | not defined |
| Total | 77 of 78 | 78 of 78 | 77 of 78 | 77 | 0 | 1 | 0 | not defined |

Kappa: not defined: the judge gave one category to all 78 answers, so chance agreement equals observed agreement.

## Reading before D227 ('partly' counted as answered)

| | person refused | judge refused | agreement | both refused | person only | judge only | both not | kappa |
|---|---|---|---|---|---|---|---|---|
| Single pass | 39 of 39 | 39 of 39 | 39 of 39 | 39 | 0 | 0 | 0 | not defined |
| RLM-10 | 29 of 39 | 39 of 39 | 29 of 39 | 29 | 0 | 10 | 0 | not defined |
| Total | 68 of 78 | 78 of 78 | 68 of 78 | 68 | 0 | 10 | 0 | not defined |

Kappa: not defined: the judge gave one category to all 78 answers, so chance agreement equals observed agreement.
