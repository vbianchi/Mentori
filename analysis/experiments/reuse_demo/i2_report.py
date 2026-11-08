#!/usr/bin/env python3
"""The I2 report: per strategy, the judge's pass counts at score 4 and score 3, and every answer's three signals side by
side, so a reader sees where they disagree (I2, D160 (14); i2_plan.md A8; GUIDE.md step 6).

    uv run python experiments/reuse_demo/i2_report.py \
        [--judge findings/recompute/I2_runs/judge/judge_passages.jsonl] [--signals findings/recompute/I2_runs/signals] \
        [--out findings/recompute/I2_runs/report]

WHAT IT COUNTS. The judge's rows (judge_passages.jsonl, written through i2_judge.py; the latest row of each answer), its
(a) call (the archived prompt, as Figure 2 reads it). The rules are Figure 2's, read from scripts/S463_fig2_ranking.py
so they are not typed twice: an answerable or false-premise answer passes at score t when the judge's correctness is t
or more (METRIC, THRESHOLDS: t = 4, the pass rate, and t = 3, the relaxed reading; D154, D160 (11)); a not-answerable
answer is refused when its refusal_accuracy is REFUSAL_T (3) or more (Rule 9, one level); an answer with no text or a
generation error (judge status no_answer) counts as not passed (Rule 10); a judge call that gave no score (JUDGE_FAILED)
is not counted and is listed. With 5 questions it gives counts only: no rate, interval, test or ranking (i2_plan.md
Q-I2b: the demonstration shows that the procedure runs and how the signals behave, not which strategy is best).

THE SIGNALS (i2_signals.py's rows, each where it exists): concept recall (loose, D12; provisional), number overlap,
MiniCheck against the key (F1) and against the papers (precision). Each answer's line holds its judge scores and these
values, nulls written with their reason. No threshold is applied to a signal (D136: Figure 5's signals have none).

OUTPUT, under --out: i2_summary.json (the counts and the per-answer table), i2_report.md (the same as tables). Both are
deterministic for the same inputs (no time stamp); the inputs' sha256 are recorded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (str(ROOT / "scripts"), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

I2_RUNS = ROOT / "findings" / "recompute" / "I2_runs"
CONFIGS = ("single_pass", "multi_hop", "verified_pass", "rlm_5", "rlm_10", "rlm_20")   # Figure 2's order (S470 CONFIGS)
SIGNAL_FILES = {"concepts": ("concepts.jsonl", ("concept_recall_loose",)),
                "numbers": ("numbers.jsonl", ("number_overlap",)),
                "key": ("key.jsonl", ("f1",)),
                "papers": ("papers.jsonl", ("precision",))}


def sha_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rules():
    import S463_fig2_ranking as S463
    return {"metric": dict(S463.METRIC), "thresholds": tuple(S463.THRESHOLDS), "primary": S463.PRIMARY,
            "refusal_t": S463.REFUSAL_T, "judge_failed": set(S463.JUDGE_FAILED)}


def latest_judge_rows(path: Path) -> dict:
    """(run_id, config, question_id, draw) -> the latest row (judge_passages' reading order)."""
    out = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            out[(r.get("run_id"), r["config"], r["question_id"], r["draw"])] = r
    return out


def outcome(r: dict, group: str, R: dict) -> dict:
    """One judged answer: its score on the group's metric, passed at each threshold (or refused), or why not counted."""
    a = r.get("a") or {}
    st = a.get("status")
    metric = R["metric"][group]
    if st == "no_answer":
        return {"status": "no_answer", "score": None, "counted": True, "pass": {t: False for t in R["thresholds"]},
                "refused": False}
    if st in R["judge_failed"] or st != "ok":
        return {"status": st, "score": None, "counted": False, "pass": None, "refused": None}
    s = (a.get("scores") or {}).get(metric)
    if s is None:
        return {"status": "no score for " + metric, "score": None, "counted": False, "pass": None, "refused": None}
    return {"status": "ok", "score": s, "counted": True, "pass": {t: s >= t for t in R["thresholds"]},
            "refused": s >= R["refusal_t"]}


def build(judge: Path, signals_dir: Path, key) -> dict:
    R = rules()
    types = {r["id"]: r["answer_type"] for r in key.records}
    grp = {"extractive": "answerable", "synthesis": "answerable", "refutation": "false_premise",
           "not_answerable": "not_answerable"}
    rows = latest_judge_rows(judge)
    sig = {}
    inputs = {"judge": {"path": str(judge), "sha256": sha_file(judge)}, "key": key.describe()}
    for name, (fname, cols) in SIGNAL_FILES.items():
        f = Path(signals_dir) / fname
        if not f.exists():
            continue
        inputs[name] = {"path": str(f), "sha256": sha_file(f)}
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                x = json.loads(line)
                vals = x.get("signals") or {c: x.get(c) for c in cols}
                reasons = x.get("null_reasons") or ({c: x.get("reason") for c in cols} if x.get("reason") else {})
                for c in cols:
                    sig.setdefault((x["run_id"], x["config"], x["question_id"], x["draw"]), {})[f"{name}.{c}"] = \
                        vals.get(c) if vals.get(c) is not None else {"null": reasons.get(c)}
    def empty():
        return {"answerable": {t: [0, 0] for t in R["thresholds"]}, "false_premise": {t: [0, 0] for t in R["thresholds"]},
                "not_answerable": {"refused": [0, 0]}, "not_counted": []}
    counts = {c: empty() for c in CONFIGS}
    table = []
    for ident in sorted(rows, key=lambda k: (CONFIGS.index(k[1]) if k[1] in CONFIGS else 99, k[3], k[2])):
        r = rows[ident]
        run_id, config, qid, draw = ident
        if qid not in types:
            raise SystemExit(f"REFUSED: judge row {ident} names a question outside the key")
        g = grp[types[qid]]
        o = outcome(r, g, R)
        c = counts.setdefault(config, empty())
        if not o["counted"]:
            c["not_counted"].append(f"{qid} d{draw}: {o['status']}")
        elif g == "not_answerable":
            c[g]["refused"][0] += bool(o["refused"])
            c[g]["refused"][1] += 1
        else:
            for t in R["thresholds"]:
                c[g][t][0] += bool(o["pass"][t])
                c[g][t][1] += 1
        table.append({"config": config, "question_id": qid, "draw": draw, "group": g, "judge_status": o["status"],
                      "judge_metric": R["metric"][g], "judge_score": o["score"],
                      **{f"pass_{t}": (None if o["pass"] is None else o["pass"][t]) for t in R["thresholds"]},
                      "refused": o["refused"] if g == "not_answerable" else None,
                      "signals": sig.get(ident, {})})
    return {"rules": {"metric": R["metric"], "thresholds": list(R["thresholds"]), "primary": R["primary"],
                      "refusal_t": R["refusal_t"], "source": "scripts/S463_fig2_ranking.py"},
            "inputs": inputs, "counts": counts, "answers": table}


def fmt(v) -> str:
    if v is None:
        return "-"
    if isinstance(v, dict):
        return "null (" + str(v.get("null")) + ")"
    if isinstance(v, float):
        return f"{v:.3f}"
    return str(v)


def markdown(s: dict) -> str:
    th = s["rules"]["thresholds"]
    out = ["# I2: judge pass counts and the three signals, per answer", "",
           f"Pass at score t: correctness t or more ({', '.join(map(str, th))}; {s['rules']['primary']} is the pass "
           f"rate, 3 the relaxed reading). Refused: refusal_accuracy {s['rules']['refusal_t']} or more. Counts are "
           "k of n answers (questions x draws). No rate, interval or ranking: 5 questions.", "",
           "| Strategy | " + " | ".join(f"Answerable, score {t}" for t in th) + " | "
           + " | ".join(f"False premise, score {t}" for t in th) + " | Not answerable, refused | Not counted |",
           "|---|" + "---|" * (2 * len(th) + 2)]
    for c, x in s["counts"].items():
        cells = [f"{x['answerable'][t][0]} of {x['answerable'][t][1]}" for t in th] + \
                [f"{x['false_premise'][t][0]} of {x['false_premise'][t][1]}" for t in th] + \
                [f"{x['not_answerable']['refused'][0]} of {x['not_answerable']['refused'][1]}",
                 "; ".join(x["not_counted"]) or "none"]
        out.append(f"| {c} | " + " | ".join(cells) + " |")
    names = sorted({k for a in s["answers"] for k in a["signals"]})
    out += ["", "## Every answer", "", "| Strategy | Question | Draw | Judge | " + " | ".join(names) + " |",
            "|---|---|---|---|" + "---|" * len(names)]
    for a in s["answers"]:
        j = f"{a['judge_metric']} {fmt(a['judge_score'])}" if a["judge_status"] == "ok" else a["judge_status"]
        out.append(f"| {a['config']} | {a['question_id']} | {a['draw']} | {j} | "
                   + " | ".join(fmt(a["signals"].get(n)) for n in names) + " |")
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    from experiments.reuse_demo import plant_key
    ap = argparse.ArgumentParser(description="I2 report (module docstring).")
    ap.add_argument("--judge", type=Path, default=I2_RUNS / "judge" / "judge_passages.jsonl")
    ap.add_argument("--signals", type=Path, default=I2_RUNS / "signals")
    ap.add_argument("--out", type=Path, default=I2_RUNS / "report")
    ap.add_argument("--key", type=Path, default=plant_key.KEY)
    ap.add_argument("--key-sha256", default=None)
    a = ap.parse_args(argv)
    pin = a.key_sha256 or (plant_key.KEY_SHA256 if Path(a.key).resolve() == plant_key.KEY.resolve() else None)
    if pin is None:
        raise SystemExit("--key names another key: give its --key-sha256")
    if not a.judge.exists():
        raise SystemExit(f"REFUSED: no judge rows at {a.judge} (i2_judge.py run)")
    s = build(a.judge, a.signals, plant_key.load(a.key, pin))
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "i2_summary.json").write_text(json.dumps(s, indent=1, ensure_ascii=False, sort_keys=True,
                                                      default=str) + "\n", encoding="utf-8")
    (a.out / "i2_report.md").write_text(markdown(s), encoding="utf-8")
    print(f"I2 report: {len(s['answers'])} answers judged; {a.out / 'i2_report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
