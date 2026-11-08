"""Recount for Figure 5 panel b, option b3-8 (scratch). Reads only raw files and imports nothing of S463, S473 or the
earlier builders:
  judge   s3/out/judge/<run>/judge_passages.jsonl (the latest row of each answer in a file), then the rows of
          s3/out_g1r15/judge/<run>/judge_passages.jsonl replace those answers (G1's 15 reruns), as s3_guard.py collect
          documents (findings/recompute/S3_runs/s3_guard.py:76-82). Variant (a), the judge without passages:
          status ok -> scores.correctness; status no_answer -> 0 (an answer with no text fails); other -> left out.
  papers  l1/papers/*.jsonl: signals.precision, checked against detail.per_claim (supported / n_claims) as a fraction.
  concept findings/recompute/L3/concept_recall.jsonl (repo): found_loose / n_concepts as a fraction, checked against
          concept_recall_loose; status ok, no_answer or error counts, as S473.compute does.
Answer set: draw 1, answerable questions (L3 group) whose six strategies all have an L1 papers row (the W set), and
the answer has all three values. Pass = correctness >= 4.
Then compares with g1_collect.jsonl (the collected copy) and with the old b8_numbers.json and writes recount.json."""
import ast, glob, hashlib, json
from collections import Counter, defaultdict
from fractions import Fraction as F
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
SCR = HERE.parents[2]
PULL = SCR / "fig5_pull_1028"
OLD = SCR / "figopts_1028/fig5_bc2/b8/b8_numbers.json"
ROOT = Path("/Users/valeriobianchi/projects/Mentori-reanalysis")
L3F = ROOT / "findings/recompute/L3/concept_recall.jsonl"
CONFIGS = ["single_pass", "multi_hop", "verified_pass", "rlm_5", "rlm_10", "rlm_20"]
PASS_T = 4
jl = lambda p: [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

def ident(d):
    return (d["config"], d["question_id"], d["draw"])

def latest(out_dir):
    got, files = {}, {}
    for f in sorted(glob.glob(str(out_dir / "judge/*/judge_passages.jsonl"))):
        for d in jl(f):
            got[ident(d)] = d          # later line wins
        files[str(Path(f).relative_to(PULL))] = sha(f)
    return got, files

J0, jfiles = latest(PULL / "s3/out")
JR, rfiles = latest(PULL / "s3/out_g1r15")
replaced = sum(1 for k in JR if k in J0)
JROW = {**J0, **JR}

def jscore(d):
    a = d["a"]; st = a["status"]
    if st == "ok":
        v = (a.get("scores") or {}).get("correctness")
        return v if isinstance(v, int) and not isinstance(v, bool) else None
    if st == "no_answer":
        return 0
    return None

# cross-check with the collected copy
COL = {ident(r): r for r in jl(PULL / "s3/g1_collect.jsonl")}
col_mism = [k for k in set(COL) | set(JROW) if (k in COL) != (k in JROW) or
            (k in COL and jscore(COL[k]) != jscore(JROW[k]))]

L3, group = {}, {}
for r in jl(L3F):
    k = ident(r); assert k not in L3, k; L3[k] = r; group[r["question_id"]] = r["group"]
L1 = {}
for f in sorted(glob.glob(str(PULL / "l1/papers/*.jsonl"))):
    for r in jl(f):
        k = ident(r); assert k not in L1, k; L1[k] = r
        assert group.get(r["question_id"]) == r["group"], k

def conc(k):
    r = L3.get(k)
    if not r or r["status"] not in ("ok", "no_answer", "error"):
        return None, None
    if r.get("n_concepts"):
        fr = F(r["found_loose"], r["n_concepts"])
        assert abs(float(fr) - r["concept_recall_loose"]) <= 5.01e-5, (k, fr)
        return fr, (r["found_loose"], r["n_concepts"])
    v = r.get("concept_recall_loose")
    return (None, None) if v is None else (F(v).limit_denominator(1000), None)

def pap(k):
    r = L1.get(k)
    if not r: return None, None
    v = (r.get("signals") or {}).get("precision")
    if v is None: return None, None
    det = r.get("detail"); det = ast.literal_eval(det) if isinstance(det, str) else (det or {})
    pc = det.get("per_claim") or []; n = det.get("n_claims")
    if pc and n == len(pc):
        s = sum(1 for c in pc if c["supported"]); fr = F(s, n)
        assert abs(float(fr) - v) <= 5.01e-5, (k, fr, v)
        return fr, (s, n)
    return F(v).limit_denominator(1000), None

qa = sorted(q for q, g in group.items() if g == "answerable")
QW = [q for q in qa if all((c, q, 1) in L1 for c in CONFIGS)]
PTS, LEFT = [], []
for q in QW:
    for c in CONFIGS:
        k = (c, q, 1)
        p, pn = pap(k); cv, cn = conc(k)
        jv = jscore(JROW[k]) if k in JROW else None
        if p is None or cv is None or jv is None:
            LEFT.append({"strategy": c, "question_id": q, "papers": None if p is None else float(p),
                         "concept": None if cv is None else float(cv), "judge": jv}); continue
        PTS.append({"strategy": c, "question_id": q, "draw": 1, "judge": jv, "pass": int(jv >= PASS_T),
                    "concept_recall": cv, "concepts_found_of": cn, "papers_precision": p, "claims_supported_of": pn,
                    "a_status": JROW[k]["a"]["status"]})

N = {1: sum(p["pass"] for p in PTS), 0: sum(1 - p["pass"] for p in PTS)}
binx = lambda fr: min(int(fr * 10), 9)
counts = {}
for key in ("papers_precision", "concept_recall"):
    for jp in (1, 0):
        c = [0] * 10
        for p in PTS:
            if p["pass"] == jp: c[binx(p[key])] += 1
        counts[f"{key}|{'pass' if jp else 'fail'}"] = c
summ = {}
for key in ("papers_precision", "concept_recall"):
    for jp in (1, 0):
        v = [p[key] for p in PTS if p["pass"] == jp]
        summ[f"{key}_{'pass' if jp else 'fail'}"] = {
            "n": len(v), "median": round(float(median(v)), 4), "eq_1": sum(x == 1 for x in v),
            "at_least_0.9": sum(x >= F(9, 10) for x in v), "below_0.5": sum(x < F(1, 2) for x in v),
            "eq_0": sum(x == 0 for x in v)}

# the overlap regions
fail_all = [p for p in PTS if not p["pass"] and p["concept_recall"] == 1]
pass_lt_half_c = [p for p in PTS if p["pass"] and p["concept_recall"] < F(1, 2)]
pass_lt_half_p = [p for p in PTS if p["pass"] and p["papers_precision"] < F(1, 2)]
fail_ge_half_c = [p for p in PTS if not p["pass"] and p["concept_recall"] >= F(1, 2)]
by = lambda L, f: dict(Counter(f(p) for p in L))
strat = lambda p: p["strategy"]
fam = lambda p: "rlm" if p["strategy"].startswith("rlm") else "other"
per_strategy = {c: {"n": sum(p["strategy"] == c for p in PTS), "pass": sum(p["strategy"] == c and p["pass"] for p in PTS),
                    "fail_all_concepts": sum(p["strategy"] == c for p in fail_all),
                    "fail": sum(p["strategy"] == c and not p["pass"] for p in PTS),
                    "pass_concept_lt_half": sum(p["strategy"] == c for p in pass_lt_half_c),
                    "pass_papers_lt_half": sum(p["strategy"] == c for p in pass_lt_half_p),
                    "all_concepts": sum(p["strategy"] == c and p["concept_recall"] == 1 for p in PTS)} for c in CONFIGS}
all_concepts = [p for p in PTS if p["concept_recall"] == 1]
all_concepts_by_family = {f: {"n": sum(fam(p) == f for p in all_concepts),
                              "fail": sum(fam(p) == f and not p["pass"] for p in all_concepts)} for f in ("rlm", "other")}
rlm_fail_scores = by([p for p in PTS if fam(p) == "rlm" and not p["pass"]], lambda p: p["judge"])
fail_scores = dict(sorted(Counter(p["judge"] for p in PTS if not p["pass"]).items()))

import re
WRONG = re.compile(r"contradict|conflict|incorrect|inconsisten|initially|wrong", re.I)
for p in fail_all:
    j = JROW[(p["strategy"], p["question_id"], 1)]["a"].get("justification") or ""
    p["justification_words"] = sorted({m.lower() for m in WRONG.findall(j)})
fail_all_wrong_words = sum(1 for p in fail_all if p["justification_words"])

ser = lambda p: {**{k: v for k, v in p.items() if k not in ("concept_recall", "papers_precision")},
                 "concept_recall": round(float(p["concept_recall"]), 4), "papers_precision": round(float(p["papers_precision"]), 4)}

# compare with the old b8 numbers
T = json.loads(OLD.read_text())
changed = []
if {"1": N[1], "0": N[0]} != {str(k): v for k, v in T["n"].items()}: changed.append(("n", N, T["n"]))
for k in counts:
    if counts[k] != T["counts"][k]: changed.append((k, counts[k], T["counts"][k]))
for k, v in summ.items():
    for kk in ("n", "median", "at_least_0.9", "below_0.5"):
        if abs(v[kk] - T["summaries_not_drawn"][k][kk]) > 6e-5: changed.append((f"{k} {kk}", v[kk], T["summaries_not_drawn"][k][kk]))
if sorted((x["strategy"], x["question_id"]) for x in LEFT) != sorted((x["strategy"], x["question_id"]) for x in T["left_out_rows"]):
    changed.append(("left out", LEFT, T["left_out_rows"]))

out = {
    "what": "recount from raw files for option b3-8 (see the docstring of recount.py)",
    "W_questions": len(QW), "answerable_questions": len(qa), "answers": len(PTS), "N": {"pass": N[1], "fail": N[0]},
    "left_out": LEFT, "judge_rows_replaced_by_g1r15": replaced,
    "judge_raw_vs_g1_collect_mismatches": [list(k) for k in col_mism],
    "counts_bins_of_0.1": counts, "summaries": summ,
    "fail_all_concepts": {"n": len(fail_all), "by_strategy": by(fail_all, strat), "by_judge_score": by(fail_all, lambda p: p["judge"]),
                          "justification_names_a_wrong_or_conflicting_statement": {"n": fail_all_wrong_words, "rule": WRONG.pattern + " (case ignored), in the judge's (a) justification; a keyword count, not drawn"},
                          "rows": [ser(p) for p in fail_all]},
    "fail_concept_ge_half": {"n": len(fail_ge_half_c), "by_family": by(fail_ge_half_c, fam)},
    "pass_concept_lt_half": {"n": len(pass_lt_half_c), "by_strategy": by(pass_lt_half_c, strat), "rows": [ser(p) for p in pass_lt_half_c]},
    "pass_papers_lt_half": {"n": len(pass_lt_half_p), "by_strategy": by(pass_lt_half_p, strat)},
    "all_concepts_by_family": all_concepts_by_family,
    "fail_judge_scores": fail_scores, "rlm_fail_judge_scores": rlm_fail_scores,
    "per_strategy": per_strategy,
    "changed_vs_old_b8_numbers": changed,
    "inputs_sha256": {"concept_recall.jsonl": sha(L3F), "g1_collect.jsonl (cross-check only)": sha(PULL / "s3/g1_collect.jsonl"),
                      "judge out": jfiles, "judge out_g1r15": rfiles,
                      "l1 papers": {Path(f).name: sha(f) for f in sorted(glob.glob(str(PULL / "l1/papers/*.jsonl")))}},
}
(HERE / "recount.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
(HERE / "points.json").write_text(json.dumps([ser(p) for p in PTS], indent=0, default=str) + "\n")
show = {k: v for k, v in out.items() if k not in ("inputs_sha256", "counts_bins_of_0.1")}
show["fail_all_concepts"] = {k: v for k, v in out["fail_all_concepts"].items() if k != "rows"}
show["pass_concept_lt_half"] = {k: v for k, v in out["pass_concept_lt_half"].items() if k != "rows"}
print(json.dumps(show, indent=1, default=str))
