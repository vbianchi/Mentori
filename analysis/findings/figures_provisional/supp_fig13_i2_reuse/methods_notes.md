# Supplementary Figure 13, notes for the Methods

Written by `scripts/S570_supp_i2_reuse.py figure`.

Reproduced before drawing: {"headers": {"concepts_null": 18, "papers_null": 20}, "known": {"answers": 90, "concepts_null": 18, "judge_rows": 90, "papers_null": 20}, "pass_counts": "i2_report.build equals the raw count", "reproduced": {"answers": 90, "concepts_null": 18, "judge_rows": 90, "papers_null": 20}}

No rate or test against the main benchmark: I2's report rule (experiments/reuse_demo/i2_report.py, i2_plan.md Q-I2b) gives counts only at five questions. Panels b and c mark each strategy's median of its question means (sheet Supplementary Fig. 13 medians); the main benchmark's median is not drawn (D300, Valerio, 7 November: the plate shows the transfer to another field, not a comparison with the main benchmark).

Claim, written from the counts: With a key written for five open-access papers on lettuce resistance to downy mildew, Figure 3's six strategies answered the five questions in 3 draws. The judge scored all 90 answers. Concepts and Papers scored the 72 answers to questions 1 to 4, Papers 70 of them (2 over the encoder's input limit). Passed at judge score 4 of the answerable and false-premise answers, and refused of the out-of-scope ones: single pass 12 of 12 and 3 of 3; multi-hop 10 of 12 and 0 of 3; verified pass 12 of 12 and 3 of 3; RLM-5 6 of 12 and 0 of 3; RLM-10 3 of 12 and 1 of 3; RLM-20 5 of 12 and 2 of 3.

Not closed by this plate: the letter's bracket "[PENDING: I2 results and the time its key took]" asks for the time as well. Its one source is experiments/reuse_demo/SIGNOFF.md:205-216 (16 October, part measured from file times, part estimated) and no script regenerates it, so the time half stays open.
