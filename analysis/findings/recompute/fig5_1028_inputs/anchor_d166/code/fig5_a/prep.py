"""Figure 5 panel a options (scratch, not a plate): panel a's numbers on the 28 October pull, through S473's own
read and compute functions (no number computed by another rule). Writes a_data.json beside this file: per strategy
and question the judge pass share at 4 (three draws), concept recall (loose matcher, mean over draws, provisional),
MiniCheck precision against the papers (draw 1), plus S473's own panel a summary, and the input files' sha256."""
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path("/Users/valeriobianchi/projects/Mentori-reanalysis")
HERE = Path(__file__).resolve().parent
PULL = Path("/private/tmp/claude-501/-Users-valeriobianchi-projects-Mentori-reanalysis/86d0d6d8-e2f1-40c7-88a7-ffa55b1ee47a/scratchpad/fig5_pull_1028")
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
spec = importlib.util.spec_from_file_location("S473", ROOT / "scripts/S473_fig5_panels.py")
M = importlib.util.module_from_spec(spec); sys.modules["S473"] = M; spec.loader.exec_module(M)
S463, S457 = M.S463, M.S457

with tempfile.TemporaryDirectory(prefix="views_", dir=HERE) as tmp:
    srcs = M.pull_sources(PULL, Path(tmp))
    rep = M.reproduce()
    groups = S463.key_groups()
    answers, ans_inputs, _ = S463.read_answers(srcs["ans_dirs"])
    read = S463.read_collect(srcs["collect"], list(M.DRAWS), groups, S463.rerun_keys(), None, answers)
    l3 = M.read_l3(groups)
    l1 = M.read_l1(srcs["l1"], l3["header"], groups)
    M.check_same_answers(l1, l3)
    txt = M.answer_text_sha(srcs["ans_dirs"])
    diff = [k for (c, q, d), r in l3["rows"].items() for k in [f"{M.INDEX}|{c}|{q}|d{d}"]
            if txt.get(k) != r.get("answer_sha256")]
    assert not diff, diff[:3]
    faith_rows = {}
    for x in M.read_jsonl(srcs["collect"]):
        b = x.get("b") or {}
        v = (b.get("scores") or {}).get("faithfulness") if b.get("status") == "ok" else None
        faith_rows[(x["config"], x["question_id"], x["draw"])] = (b.get("status"), v, b.get("error"))
    fn = M.compute(read, l3, l1, faith_rows, groups)
    sha = dict(srcs["sha"])

qa = fn["qa"]
cells = read["cells"]
C = M.CONFIGS
# concept recall per answer and per question (Rule 7: the question's mean over its draws; Rule 10: an empty answer 0)
conc = {}
for (c, q, d), r in l3["rows"].items():
    if groups[q] == "answerable":
        conc[(c, q, d)] = r["concept_recall_loose"] if r["status"] in ("ok", "no_answer", "error") else None
conc_status = {}
for (c, q, d), r in l3["rows"].items():
    if groups[q] == "answerable":
        conc_status[r["status"]] = conc_status.get(r["status"], 0) + 1
papers = {(c, q, d): ((r.get("signals") or {}).get("precision"), r["status"])
          for (c, q, d), r in l1["stages"]["papers"].items() if groups[q] == "answerable"}
qw = fn["c"]["questions"]
out = {"configs": C, "labels": {c: M.LABEL[c] for c in C}, "questions": qa, "W_questions": qw,
       "pass_t": M.PASS_T, "per_q": {}, "per_answer": {}, "S473_a": {}, "c_means": fn["c"].get("means"),
       "c_ranks_low1": fn["c"].get("ranks_low1"), "W": fn["c"].get("W"), "P": fn["c"].get("P"),
       "have": fn["have"], "all4": fn["all4"], "reproduced": rep, "concept_status_answerable": conc_status,
       "papers_rows_answerable": len(papers), "papers_rows_all": len(l1["stages"]["papers"]),
       "papers_null_answerable": sum(1 for v in papers.values() if v[0] is None),
       "inputs_sha256": sha, "collect_run_sha256": str(read["run_sha256"])}
for c in C:
    a = fn["a"][c]
    out["S473_a"][c] = {"pass": {"s": a["pass"]["s"], "answers": a["pass"]["answers"], "unscored": a["pass"]["unscored"]},
                        "papers": {"s": a["papers"]["s"], "answers": a["papers"]["answers"], "null": a["papers"]["null"]}}
    pq = {}
    pass_q = dict(a["pass"]["per_q"])
    for q in qa:
        cv = [conc[(c, q, d)] for d in M.DRAWS if conc.get((c, q, d)) is not None]
        pv = papers.get((c, q, 1), (None, None))[0]
        pq[q] = {"pass4": pass_q.get(q), "concept": (sum(cv) / len(cv)) if cv else None, "concept_n": len(cv),
                 "papers": pv, "in_W": q in qw}
    out["per_q"][c] = pq
    pa = {}
    for q in qa:
        for d in M.DRAWS:
            cell = cells[(c, q, d)]
            pa[f"{q}|d{d}"] = {"judge_kind": cell["kind"], "judge_score": cell.get("score"),
                               "concept": conc.get((c, q, d))}
    out["per_answer"][c] = pa
(HERE / "a_data.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
print("reproduced:", *rep, sep="\n  ")
print("qa", len(qa), "W questions", len(qw), "papers answerable rows", len(papers), "all", out["papers_rows_all"])
print("have", fn["have"]); print("all4", fn["all4"], "W", fn["c"].get("W"), "P", fn["c"].get("P"))
for c in C:
    s = out["S473_a"][c]
    print(c, {k: round(v, 3) for k, v in s["pass"]["s"].items()}, s["papers"]["answers"], s["papers"]["null"],
          {k: round(v, 3) for k, v in (s["papers"]["s"] or {}).items()})
