# S606 prediction, written before any classification result is read

Written 8 November 2026, before any classification call of `scripts/S606_unsupported_claim_types.py` was made and
before any of its labels was read. Committed in the same commit as the script's prompt (PROMPT_TEMPLATE), and
before the smoke run.

The question (Valerio, 8 November, "Go Q1"; from Jing et al. 2025, Findings of NAACL, ref. 38 of the manuscript):
judges catch claims that contradict the source better than claims the source does not support. Is that the kind of
unsupported claim our answers carry?

The units: the sentences MiniCheck (lytang/MiniCheck-Flan-T5-Large) found unsupported by the source papers in the
502 draw-1 answers behind Supplementary Figure 12d (369 answers the judge scored 5/5 for faithfulness, 133 scored
below 5), each paired with the source piece MiniCheck gave its highest probability. Each pair is labelled by
devstral-small-2:24b and, separately, by qwen3.8:27b as SUPPORTED, CONTRADICTED or NOT_MENTIONED.

## Predictions

- **P1.** Among the unsupported sentences, NOT_MENTIONED outnumbers CONTRADICTED under both classifiers
  (devstral-small-2:24b and qwen3.8:27b), each counted on its own parsed labels.
- **P2.** The share of NOT_MENTIONED among the unsupported sentences is higher in the answers the judge scored 5/5
  for faithfulness than in the answers it scored below 5.

How each is read (`S606 report`): P1 holds for a classifier when its NOT_MENTIONED count exceeds its CONTRADICTED
count; the difference of the two shares is given with a two-sided 95% percentile interval over 10,000 question
resamples. P2 holds for a classifier when its NOT_MENTIONED share at 5/5 exceeds its share below 5; the difference
is given with the same interval. Both are reported for each classifier, whatever the result.
