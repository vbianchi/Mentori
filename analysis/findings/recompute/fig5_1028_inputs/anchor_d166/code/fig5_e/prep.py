"""Figure 5 panel e options (scratch, 28 Oct): S473's own read and compute on today's pull, nothing drawn.

Mirrors S473._figure up to compute() (same calls, same checks, same order) and writes e_data.json in this folder:
panel e's answer points (draw 1, faithfulness with passages scored ok, MiniCheck precision against the papers not
null), each with its judge correctness (plain call) and concept recall (loose matcher, provisional), plus S473's
own rho_all, rho_3to5 and e9, and the sha256 of every input S473 recorded.
"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path("/Users/valeriobianchi/projects/Mentori-reanalysis")
HERE = Path(__file__).resolve().parent
PULL = HERE.parent.parent / "fig5_pull_1028"
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
import importlib.util
spec = importlib.util.spec_from_file_location("S473", ROOT / "scripts/S473_fig5_panels.py")
S473 = importlib.util.module_from_spec(spec); sys.modules["S473"] = S473; spec.loader.exec_module(S473)
S463 = S473.S463

if S463.sha256_file(S463.LOCK_TOML) != S463.LOCK_WANT:
    raise SystemExit("LOCK.toml differs")
S473.S457.figure_lock_agreed()
with tempfile.TemporaryDirectory(prefix="fig5e_") as tmp:
    srcs = S473.pull_sources(PULL.resolve(), Path(tmp))
    rep = S473.reproduce()
    groups = S463.key_groups()
    answers, ans_inputs, _ = S463.read_answers(srcs["ans_dirs"])
    read = S463.read_collect(srcs["collect"], list(S473.DRAWS), groups, S463.rerun_keys(), None, answers)
    l3 = S473.read_l3(groups); rep.append(l3["reproduced"])
    l1 = S473.read_l1(srcs["l1"], l3["header"], groups)
    S473.check_same_answers(l1, l3)
    txt = S473.answer_text_sha(srcs["ans_dirs"])
    diff = [k for (c, q, d), r in l3["rows"].items() for k in [f"{S473.INDEX}|{c}|{q}|d{d}"]
            if txt.get(k) != r.get("answer_sha256")]
    if diff:
        raise SystemExit(f"{len(diff)} answer texts differ")
    faith_rows = {}
    for x in S473.read_jsonl(srcs["collect"]):
        b = x.get("b") or {}
        v = (b.get("scores") or {}).get("faithfulness") if b.get("status") == "ok" else None
        faith_rows[(x["config"], x["question_id"], x["draw"])] = (b.get("status"), v, b.get("error"))
    fn = S473.compute(read, l3, l1, faith_rows, groups)
    collect_sha = S473.sha256_file(srcs["collect"])
    run_sha = str(read["run_sha256"])

# judge and concept per answer for the points (the same dicts compute builds)
cells = read["cells"]
pts = []
for p in fn["e"]["points"]:
    c, q = p["strategy"], p["question_id"]
    cell = cells[(c, q, 1)]
    js = cell["score"] if cell["kind"] == "scored" else 0 if cell["kind"] == "failed" else None
    cr = l3["rows"].get((c, q, 1))
    cv = cr["concept_recall_loose"] if cr and cr["status"] in ("ok", "no_answer", "error") else None
    pts.append(dict(p, label=S473.LABEL[c], judge_correctness=js, judge_kind=cell["kind"], concept_recall_loose=cv))
# counts of what panel e leaves out (draw 1, answerable)
qa = fn["qa"]
papers = l1["stages"]["papers"]
lo = {"draw1_answerable": 6 * len(qa), "papers_row": 0, "papers_null": 0, "faith_not_ok": {}, "no_papers_row": 0}
for c in S473.CONFIGS:
    for q in qa:
        r = papers.get((c, q, 1))
        if r is None:
            lo["no_papers_row"] += 1; continue
        lo["papers_row"] += 1
        if (r.get("signals") or {}).get("precision") is None:
            lo["papers_null"] += 1; continue
        st = faith_rows.get((c, q, 1), (None,))[0]
        if st != "ok":
            lo["faith_not_ok"][str(st)] = lo["faith_not_ok"].get(str(st), 0) + 1
out = {"what": "Figure 5 panel e inputs, S473 compute() on fig5_pull_1028",
       "reproduced": rep, "configs": S473.CONFIGS, "labels": {c: S473.LABEL[c] for c in S473.CONFIGS},
       "points": pts, "rho_all": fn["e"]["rho_all"], "rho_3to5": fn["e"]["rho_3to5"], "e9": fn["e"]["e9"],
       "left_out": lo, "d_all": fn["d_all"], "have": fn["have"], "all4": fn["all4"],
       "W_questions": len(fn["c"]["questions"]),
       "inputs": {"s3_collect": {"path": "fig5_pull_1028/s3/g1_collect.jsonl", "sha256": collect_sha,
                                 "run_sha256": run_sha},
                  "l3": {"path": "findings/recompute/L3/concept_recall.jsonl",
                         "sha256": S473.sha256_file(S473.L3_DIR / "concept_recall.jsonl")},
                  "inputs_sha256": dict(sorted(srcs["sha"].items()))},
       "code": {"S473_fig5_panels.py": S473.sha256_file(ROOT / "scripts/S473_fig5_panels.py"),
                "S463_fig2_ranking.py": S473.sha256_file(ROOT / "scripts/S463_fig2_ranking.py"),
                "prep.py": S473.sha256_file(Path(__file__))}}
(HERE / "e_data.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
print("\n".join(rep))
print(len(pts), "points;", fn["e"]["rho_all"], fn["e"]["rho_3to5"], fn["e"]["e9"], lo)
