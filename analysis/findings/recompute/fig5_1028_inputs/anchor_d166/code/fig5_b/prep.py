"""Figure 5 panel b alternatives, data step (scratch, not a plate).

Runs S473's own readers, checks and compute() on today's read-only pull (fig5_pull_1028), exactly as S473 figure
--from does up to the point where it draws, and writes panel b's rows (fn["b"]: each draw-1 answer on the W questions
with concept recall, MiniCheck precision against the papers and the judge's correctness score) to b_points.json, with
the sha256 of every input S473 recorded. Nothing in the repository is written.
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

with tempfile.TemporaryDirectory(prefix="fig5b_") as tmp:
    S473.S457.figure_lock_agreed()
    if S473.S463.sha256_file(S473.S463.LOCK_TOML) != S473.S463.LOCK_WANT:
        raise SystemExit("LOCK.toml is not D88's")
    srcs = S473.pull_sources(PULL.resolve(), Path(tmp))
    rep = S473.reproduce()
    groups = S473.S463.key_groups()
    answers, ans_inputs, _ = S473.S463.read_answers(srcs["ans_dirs"])
    read = S473.S463.read_collect(srcs["collect"], list(S473.DRAWS), groups, S473.S463.rerun_keys(), None, answers)
    l3 = S473.read_l3(groups); rep.append(l3["reproduced"])
    l1 = S473.read_l1(srcs["l1"], l3["header"], groups)
    S473.check_same_answers(l1, l3)
    txt = S473.answer_text_sha(srcs["ans_dirs"])
    diff = [k for (c, q, d), r in l3["rows"].items() for k in [f"{S473.INDEX}|{c}|{q}|d{d}"]
            if txt.get(k) != r.get("answer_sha256")]
    if diff:
        raise SystemExit(f"{len(diff)} judged answers differ from L3's texts")
    faith_rows = {}
    for x in S473.read_jsonl(srcs["collect"]):
        b = x.get("b") or {}
        v = (b.get("scores") or {}).get("faithfulness") if b.get("status") == "ok" else None
        faith_rows[(x["config"], x["question_id"], x["draw"])] = (b.get("status"), v, b.get("error"))
    fn = S473.compute(read, l3, l1, faith_rows, groups)
    sheets = S473.build_sheets(fn, "scratch")
    # every draw-1 answerable answer on the W questions, including those b leaves out (a null), for the notes
    qw = fn["c"]["questions"]
    left_out = []
    papers = {k: r for k, r in l1["stages"]["papers"].items()}
    for q in qw:
        for c in S473.CONFIGS:
            pr = papers[(c, q, 1)]
            pv = (pr.get("signals") or {}).get("precision")
            cr = l3["rows"].get((c, q, 1))
            cell = read["cells"][(c, q, 1)]
            if pv is None or cr is None or cell["kind"] == "unscored":
                left_out.append({"strategy": c, "question_id": q, "papers_status": pr["status"],
                                 "papers_null_reason": (pr.get("null_reasons") or {}).get("precision"),
                                 "concept_status": cr["status"] if cr else None, "judge_kind": cell["kind"]})
    l3_rows_q = {f"{c}|{q}": {"concepts_total": (l3["rows"][(c, q, 1)].get("n_concepts")),
                              "keys": sorted(l3["rows"][(c, q, 1)].keys())}
                 for q in qw[:1] for c in S473.CONFIGS[:1]}
    out = {"what": "S473.compute() on fig5_pull_1028, panel b rows (fn['b']); judge pass = score >= S473.PASS_T",
           "pass_t": S473.PASS_T, "pass_relaxed": S473.PASS_RELAXED,
           "configs": S473.CONFIGS, "labels": S473.LABEL, "W_questions": qw,
           "partial_blocks_left_out": fn["c"]["partial_blocks_left_out"],
           "b": fn["b"], "b_left_out": left_out, "sheet_b": sheets["Fig. 5b"],
           "c": {k: v for k, v in fn["c"].items() if k in ("W", "P", "W_ci", "corr", "means", "ranks_low1")},
           "have": fn["have"], "all4": fn["all4"], "reproduced": rep,
           "l3_row_keys_example": l3_rows_q,
           "inputs_sha256": dict(sorted(srcs["sha"].items())),
           "collect": {"path": str(srcs["collect"]), "sha256": S473.sha256_file(srcs["collect"])},
           "s473_sha256": S473.sha256_file(ROOT / "scripts/S473_fig5_panels.py")}
    (HERE / "b_points.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    print("\n".join(rep))
    print(len(fn["b"]), "answers on", len(qw), "questions;", len(left_out), "left out; all4", fn["all4"])
