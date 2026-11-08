"""The corpus-scaling experiment's passage-verification arm, as the paper reports it.

WHY. In the deposited exp05 file, the verifier of the verified_pass strategy let every passage
through on 970 of the 1,662 rows (S309, S316). S314 regenerated all 1,662 rows with the verifier
attached and logged (failed open on 0) and S315 judged them on complete answer text with the S21
arm-F protocol. Valerio adopted the rerun on 28 September: the paper's verified_pass rows in exp05
are these, and every consumer of exp05 (S49, S281, S66, S77) takes them from here, so there is one
definition of the arm.

    from exp05_final import rerun_rows
    rows = rerun_rows()        # {(index_name, question_id): FinalRow}

Each FinalRow carries what the deposited row carried and a consumer reads: answer, latency_s,
llm_calls, retrieved_passages, error, and judge_scores (correctness, completeness, faithfulness,
citation_quality for answerable questions; refusal_accuracy, hallucination_avoidance,
explanation_quality for the out-of-domain ones), plus the verifier outcome.

Gated on every call (reproduce before anyone uses it):
  G1  exactly one S314 row and one parsed S315 judgement for each of the deposit's 1,662
      verified_pass (index, question) keys, and no extra key
  G2  no generation error, no empty answer, verifier attached on every row
  G3  the answerable pass rate at correctness >= 3 is 0.704 over 1,062 rows, as S316 reports
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from machine import RECOMPUTE, RESULTS

S314 = RECOMPUTE / "S314_verified_pass_raw.jsonl"
S315 = RECOMPUTE / "S315_verified_pass_rejudge_raw.jsonl"
DEPOSIT = RESULTS / "exp05_scaling_latest.json"
PASS_AT = 3


def _jsonl(path: Path):
    for line in open(path):
        d = json.loads(line)
        if "_header" not in d:
            yield d


@lru_cache(maxsize=1)
def rerun_rows() -> dict:
    dep = {(r["index_name"], r["question_id"]): r
           for r in json.load(open(DEPOSIT))["per_question_results"] if r["config"] == "verified_pass"}
    gen = {}
    for d in _jsonl(S314):                       # the run's own rows; S316 reads them the same way
        if d.get("phase") in ("repro", "full") and d.get("mode") == "separate":
            gen[(d["index"], d["question_id"])] = d          # a later line wins
    judged = {}
    for d in _jsonl(S315):
        judged[(d["index"], d["question_id"])] = d
    fails = []
    if set(gen) != set(dep) or set(judged) != set(dep):                                   # G1
        fails.append(f"G1 keys: deposit {len(dep)}, S314 {len(gen)}, S315 {len(judged)}, "
                     f"missing {len(set(dep) - set(gen))}/{len(set(dep) - set(judged))}")
    bad_parse = [k for k, j in judged.items() if not j.get("parsed")]
    if bad_parse:
        fails.append(f"G1 {len(bad_parse)} S315 rows without a parsed judgement")
    bad = [k for k, g in gen.items() if g.get("error") or not (g.get("answer") or "").strip()
           or not g.get("verifier_attached")]
    if bad:                                                                                # G2
        fails.append(f"G2 {len(bad)} rows with an error, an empty answer or no verifier")
    if fails:
        raise SystemExit("exp05_final REFUSED\n  " + "\n  ".join(fails))
    out = {}
    for k, g in gen.items():
        p = judged[k]["parsed"]
        scores = {x: p[x] for x in ("correctness", "completeness", "faithfulness", "citation_quality",
                                    "refusal_accuracy", "hallucination_avoidance", "explanation_quality")
                  if x in p}
        out[k] = {"answer": g["answer"], "latency_s": g["latency_s"], "llm_calls": g["llm_calls"],
                  "retrieved_passages": g["retrieved_passages"], "error": g.get("error"),
                  "answerable": bool(dep[k]["answerable"]), "judge_scores": scores,
                  "verifier_outcome": g["verifier_outcome"]}
    ans = [r for r in out.values() if r["answerable"]]
    rate = sum(r["judge_scores"].get("correctness", 0) >= PASS_AT for r in ans) / len(ans)
    if len(ans) != 1062 or round(rate, 3) != 0.704:                                       # G3
        raise SystemExit(f"exp05_final REFUSED\n  G3 answerable pass rate {rate:.4f} over {len(ans)}, "
                         "S316 reports 0.704 over 1,062")
    return out


if __name__ == "__main__":
    rows = rerun_rows()
    ans = [r for r in rows.values() if r["answerable"]]
    print(f"PASSED  {len(rows)} rerun rows, {len(ans)} answerable, pass rate "
          f"{sum(r['judge_scores']['correctness'] >= PASS_AT for r in ans) / len(ans):.4f}")
