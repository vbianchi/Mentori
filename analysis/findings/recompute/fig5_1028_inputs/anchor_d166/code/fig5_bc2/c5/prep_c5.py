"""Figure 5 panel c, design c5 (scratch, exploratory): head-to-head counts, question by question.
Reads, never writes, the repository. Runs S473's own reading path on the 28 October pull (pull_sources, reproduce,
S463.read_collect, read_l3, read_l1, check_same_answers, compute), rebuilds the per-question matrix compute keeps
local (per W question and strategy: judge correctness and loose concept recall averaged over draws 1 to 3, MiniCheck
precision from draw 1; a 'failed' judge cell counts 0), checks it gives compute's configuration means, and counts,
for every pair of strategies and every signal, the questions where the first scores strictly higher, ties (equal to
1e-9) and the second scores strictly higher. Writes c5_counts.json here."""
import hashlib
import importlib.util
import itertools
import json
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path("/Users/valeriobianchi/projects/Mentori-reanalysis")
HERE = Path(__file__).resolve().parent
PULL = HERE.parent.parent.parent / "fig5_pull_1028"
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
spec = importlib.util.spec_from_file_location("S473", ROOT / "scripts/S473_fig5_panels.py")
S473 = importlib.util.module_from_spec(spec)
sys.modules["S473"] = S473
spec.loader.exec_module(S473)
S463 = S473.S463
CONFIGS = S473.CONFIGS
SIGS = ("judge", "concept", "papers")
TIE = 1e-9


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


with tempfile.TemporaryDirectory(prefix="fig5c5_") as tmpd:
    tmp = Path(tmpd)
    srcs = S473.pull_sources(PULL.resolve(), tmp)
    rep = S473.reproduce()
    groups = S463.key_groups()
    answers, ans_inputs, _ = S463.read_answers(srcs["ans_dirs"])
    read = S463.read_collect(srcs["collect"], list(S473.DRAWS), groups, S463.rerun_keys(), None, answers)
    l3 = S473.read_l3(groups)
    l1 = S473.read_l1(srcs["l1"], l3["header"], groups)
    S473.check_same_answers(l1, l3)
    txt = S473.answer_text_sha(srcs["ans_dirs"])
    diff = [k for (c, q, d), r in l3["rows"].items()
            for k in [f"{S473.INDEX}|{c}|{q}|d{d}"] if txt.get(k) != r.get("answer_sha256")]
    assert not diff, diff[:3]
    faith_rows = {}
    for x in S473.read_jsonl(srcs["collect"]):
        b = x.get("b") or {}
        v = (b.get("scores") or {}).get("faithfulness") if b.get("status") == "ok" else None
        faith_rows[(x["config"], x["question_id"], x["draw"])] = (b.get("status"), v, b.get("error"))
    fn = S473.compute(read, l3, l1, faith_rows, groups)
    cc = fn["c"]
    inputs_sha = dict(srcs["sha"])

    cells = read["cells"]
    judge = {}
    for (c, q, d), cell in cells.items():
        if groups[q] == "answerable":
            judge[(c, q, d)] = cell["score"] if cell["kind"] == "scored" else 0 if cell["kind"] == "failed" else None
    concept = {}
    for (c, q, d), r in l3["rows"].items():
        if groups[q] == "answerable":
            concept[(c, q, d)] = r["concept_recall_loose"] if r["status"] in ("ok", "no_answer", "error") else None
    papers = {}
    for (c, q, d), r in l1["stages"]["papers"].items():
        if groups[q] == "answerable":
            papers[(c, q, d)] = (r.get("signals") or {}).get("precision")

qw = cc["questions"]
sig_d = {"judge": (judge, S473.DRAWS), "concept": (concept, S473.DRAWS), "papers": (papers, (1,))}


def qmean(sig, c, q, draws):
    v = [sig[(c, q, d)] for d in draws if (c, q, d) in sig and sig[(c, q, d)] is not None]
    return (float(np.mean(v)) if v else None), len(v)


V, NV = {}, {}
for s, (sig, dr) in sig_d.items():
    V[s] = np.array([[np.nan if qmean(sig, c, q, dr)[0] is None else qmean(sig, c, q, dr)[0] for c in CONFIGS]
                     for q in qw])
    NV[s] = [[qmean(sig, c, q, dr)[1] for c in CONFIGS] for q in qw]
# the matrix gives compute's configuration means (the same matrix S473 ranks for W)
for s in SIGS:
    for i, c in enumerate(CONFIGS):
        col = V[s][:, i]
        assert abs(np.nanmean(col) - cc["means"][s][c]) < 1e-12, (s, c)
missing = {s: int(np.isnan(V[s]).sum()) for s in SIGS}

pairs = {}
for a, b in itertools.combinations(CONFIGS, 2):
    ia, ib = CONFIGS.index(a), CONFIGS.index(b)
    row = {}
    for s in SIGS:
        x, y = V[s][:, ia], V[s][:, ib]
        ok = ~(np.isnan(x) | np.isnan(y))
        d = x[ok] - y[ok]
        row[s] = {"first_higher": int((d > TIE).sum()), "tie": int((np.abs(d) <= TIE).sum()),
                  "second_higher": int((d < -TIE).sum()), "n": int(ok.sum())}
    pairs[f"{a}|{b}"] = row

# the counts the spec says were checked on the 28 October pull (single pass higher / tie / other higher)
CHECK = {"multi_hop": [(31, 40, 12), (66, 11, 6), (52, 21, 9)],
         "verified_pass": [(15, 50, 18), (25, 35, 23), (23, 24, 36)],
         "rlm_5": [(53, 14, 16), (23, 17, 43), (74, 0, 8)],
         "rlm_10": [(49, 14, 20), (25, 13, 45), (75, 2, 5)],
         "rlm_20": [(54, 14, 15), (29, 18, 36), (77, 0, 6)]}
for o, trip in CHECK.items():
    for s, t in zip(SIGS, trip):
        r = pairs[f"single_pass|{o}"][s]
        assert (r["first_higher"], r["tie"], r["second_higher"]) == t, (o, s, r, t)
r = pairs["rlm_5|rlm_10"]
assert [(r[s]["first_higher"], r[s]["tie"], r[s]["second_higher"]) for s in SIGS] == [(28, 27, 28), (29, 20, 34),
                                                                                       (38, 6, 38)], r

out = {
    "what": "Figure 5 panel c, design c5: head-to-head counts per pair of strategies and signal, on the W set",
    "provisional": ["concept recall: L3 loose matcher (D12), provisional until P2's hand labels choose the matcher",
                    "papers: MiniCheck precision, draw 1 only; W set = answerable questions whose six draw-1 "
                    "answers all have a papers row (S473 Rule 7 provisional)"],
    "reproduced": rep,
    "rule": "per question: judge correctness (0 to 5, failed = 0) and loose concept recall averaged over draws "
            "1 to 3; MiniCheck precision from draw 1; a win is a strictly higher value, a tie equal to 1e-9",
    "strategies": CONFIGS, "label": S473.LABEL, "questions": qw, "n_questions": len(qw),
    "missing_cells": missing,
    "W": cc["W"], "P": cc["P"], "means": cc["means"],
    "pairs": pairs,
    "per_question": {s: {"rows_question": qw, "cols_strategy": CONFIGS,
                         "values": [[None if np.isnan(v) else float(v) for v in row] for row in V[s]],
                         "n_values": NV[s]} for s in SIGS},
    "inputs": {"pull_dir": str(PULL.resolve()), "sha256": inputs_sha,
               "l3": {"path": "findings/recompute/L3/concept_recall.jsonl",
                      "sha256": sha(ROOT / "findings/recompute/L3/concept_recall.jsonl")},
               "scripts_sha256": {p: sha(ROOT / p) for p in ("scripts/S473_fig5_panels.py",
                                                             "scripts/S463_fig2_ranking.py",
                                                             "scripts/S457_fig2_panels.py")}},
}
(HERE / "c5_counts.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
print("questions", len(qw), "W", cc["W"], "P", cc["P"], "missing", missing)
for o in CONFIGS[1:]:
    r = pairs[f"single_pass|{o}"]
    print(o, [(r[s]["first_higher"], r[s]["tie"], r[s]["second_higher"]) for s in SIGS])
