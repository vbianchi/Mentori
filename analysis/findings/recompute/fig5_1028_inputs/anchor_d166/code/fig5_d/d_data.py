"""Figure 5 panel d, options (scratch, not a plate). Computes panel d's numbers on the 28 October pull with S473's
own functions (import of scripts/S473_fig5_panels.py: pull_sources, reproduce, read_l3, read_l1, compute), then the
per-answer rows the alternatives need, taken from the same collect rows S473 reads (faithfulness from the call with
passages, "b"; correctness from S463's checked cells, Rule 10 as in S473.compute).

Writes only into this folder: d_data.json (panel d's numbers and the per-answer rows) and d_inputs.json (path and
sha256 of every file read). Run from the repository root:
  uv run --frozen python <this folder>/d_data.py
"""
import hashlib
import importlib.util
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path("/Users/valeriobianchi/projects/Mentori-reanalysis")
HERE = Path(__file__).resolve().parent
PULL = HERE.parents[1] / "fig5_pull_1028"
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]


def mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


S473 = mod("S473", ROOT / "scripts/S473_fig5_panels.py")
S463, S457 = S473.S463, S473.S457


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


with tempfile.TemporaryDirectory(dir=HERE, prefix="tmp_") as tmp:
    srcs = S473.pull_sources(PULL, Path(tmp))
    rep = S473.reproduce()
    groups = S463.key_groups()
    answers, ans_inputs, _ = S463.read_answers(srcs["ans_dirs"])
    read = S463.read_collect(srcs["collect"], list(S473.DRAWS), groups, S463.rerun_keys(), None, answers)
    l3 = S473.read_l3(groups)
    l1 = S473.read_l1(srcs["l1"], l3["header"], groups)
    S473.check_same_answers(l1, l3)
    faith_rows = {}
    for x in S473.read_jsonl(srcs["collect"]):
        b = x.get("b") or {}
        v = (b.get("scores") or {}).get("faithfulness") if b.get("status") == "ok" else None
        faith_rows[(x["config"], x["question_id"], x["draw"])] = (b.get("status"), v, b.get("error"))
    fn = S473.compute(read, l3, l1, faith_rows, groups)
    sheets = S473.build_sheets(fn, "options, 28 Oct pull")
    inputs = {k: v for k, v in srcs["sha"].items()}

qa = fn["qa"]
CONFIGS = S473.CONFIGS
# per answer: faithfulness (with passages, status) and judge correctness (plain call; Rule 10 as S473.compute)
rows = []
for c in CONFIGS:
    for q in qa:
        for d in S473.DRAWS:
            st, v, why = faith_rows.get((c, q, d), (None, None, None))
            cell = read["cells"][(c, q, d)]
            corr = cell["score"] if cell["kind"] == "scored" else 0 if cell["kind"] == "failed" else None
            rows.append({"strategy": c, "question_id": q, "draw": d, "faith_status": st, "faithfulness": v,
                         "judge_kind": cell["kind"], "correctness": corr})

# reproduce: the per-answer rows give S473's panel d counts exactly
for c in CONFIGS:
    sc = [r["faithfulness"] for r in rows if r["strategy"] == c and r["faith_status"] == "ok"]
    if {k: sc.count(k) for k in range(6)} != fn["d"][c]["counts"] or len(sc) != fn["d"][c]["n"]:
        raise SystemExit(f"{c}: per-answer rows differ from S473's panel d counts")
rep.append("per-answer faithfulness rows give S473.compute's panel d counts for all six strategies")

out = {
    "what": "Figure 5 panel d on the 28 October pull, through S473's functions; per-answer rows for the options",
    "pull": str(PULL), "pull_ended_utc": json.loads((PULL / "PULL.json").read_text())["ended_utc"],
    "collect_run_sha256": read["run_sha256"], "collect_at": (read["side"].get("_provenance") or {}).get("at"),
    "reproduced": rep,
    "configs": CONFIGS, "labels": {c: S473.LABEL[c] for c in CONFIGS}, "questions": qa,
    "d": {c: {"counts": {str(k): v for k, v in fn["d"][c]["counts"].items()}, "n": fn["d"][c]["n"],
              "status": fn["d"][c]["status"]} for c in CONFIGS},
    "d_all": {"n": fn["d_all"]["n"], "at5": fn["d_all"]["at5"],
              "counts": {str(k): v for k, v in fn["d_all"]["counts"].items()}},
    "sheet_d": sheets["Fig. 5d"],
    "have": {k: v for k, v in fn["have"].items() if k.startswith("faith") or k.startswith("judge")},
    "rows": rows,
}
(HERE / "d_data.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
files = {}
for k, v in inputs.items():
    if k.startswith("pull:"):
        files[str(PULL / k[5:])] = v
    else:
        files[k] = v
for p in (ROOT / "scripts/S473_fig5_panels.py", ROOT / "scripts/S463_fig2_ranking.py",
          ROOT / "scripts/S457_fig2_panels.py", ROOT / "experiments/FIGURE_LOCK.toml"):
    files[str(p)] = sha(p)
(HERE / "d_inputs.json").write_text(json.dumps(files, indent=1, sort_keys=True) + "\n")
print("\n".join(rep))
print("d_all", out["d_all"], "run", out["collect_run_sha256"])
print(Counter((r["faith_status"]) for r in rows))
