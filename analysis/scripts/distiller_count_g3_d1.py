#!/usr/bin/env python3
"""distiller_count_g3_d1 - the distiller count of D154 (O3) on the full pipeline's draw 1 (G3), re-run on the frozen records.

WHY. D154 (amended) keeps Figure 1 at 6 set-ups + 2 stress set-ups because the distiller never fired on the full
pipeline's draw 1 (G3's exp_03__full_orchestrator): 0 step outputs over 209,712 characters, largest 62,712
(experiments/RUNNING.md, 26 Oct 21:20). This script counts that one set-up, as that count did, not G3's other
set-ups; the audit of 27 October counted the eight set-ups by hand, with none over the threshold and the longest step
67,570 characters (analyser off; findings/audits/audit_2026-10-27_scripts/infra_numbers_k1_verified.md F14, and
fig4_6_verified.md A2). That count was run on the Studio's live answers.json with scratch dcount.sh, and its
input's sha256 was recorded nowhere; G3 draws 2 and 3 rewrite that file (INVENTORY.md F19, action A19).
This script runs the same committed function, experiments/mentori/orchestrator/distiller_firing.count, on the
frozen copy of that file in fig4_records_1023.tar (the copy Figure 4 read: figure4_provenance.json records its
sha256), and records the input's sha256.

WHAT distiller_firing.count DOES (read from the code): for each answer in answers.json "results", for each step
attempt in generation.steps, it counts the step as over the threshold from the record's over_distill_threshold when
present, else from len(raw_content) > int(0.40 x LOCK num_ctx) x 4 characters (209,712; 0.40 x 131,072 x 4 without
the int() would be 209,715.2); it tallies distill.status ("not_asked" when absent) and keeps the longest raw_content.
It reads only.

REPRODUCE BEFORE WRITING. The input's sha256 must equal figure4_provenance.json's record of it, the threshold from
the lock must be 209,712 and the file must hold G3's 135 draw-1 answers (RUNNING.md 26 Oct 21:20). Otherwise nothing
is written.

COMMAND, from the repository root: uv run python scripts/distiller_count_g3_d1.py [--check]
Writes findings/recompute/distiller_count_g3_d1/distiller_count_g3_d1.json (no time in it); --check requires the
committed file byte-equal instead.

DRAWS 2 AND 3 (fig4.md R7, owed by experiments/NOW.md:37): uv run python scripts/distiller_count_g3_d1.py --sink <file>
<file> is a read-only copy of the full pipeline's answers.json after G7 gave it draws 2 and 3 on D98's 45 questions. The
same function counts the file's draw-1 rows, its draw-2 rows, its draw-3 rows and all of them, each from a temporary
file holding only those rows. Reproduces first: the draw-1 rows must give the frozen draw 1's count above (answers, step
attempts, steps over the threshold, statuses, longest output), and the file must hold 135 answers at draw 1 and 45 at
each of draws 2 and 3, the later ones on D98's 45 questions, once each. Otherwise nothing is written. It covers 225
answers, not the 405 of Rule 12 (LIST.md), because D98 stopped draws 2 and 3 at 45 questions, and the output says so.
Writes findings/recompute/distiller_count_g3_d2d3/distiller_count_g3_d2d3.json (no time in it); --check as above.
Tested by scripts/distiller_count_g3_d1_test.py on a built copy. Not run on the real sink when written (2 November): that
file is on the Studio.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "experiments" / "mentori" / "orchestrator")]

import fig_repro  # noqa: E402
import distiller_firing  # noqa: E402

SCRIPT = "scripts/distiller_count_g3_d1.py"
COUNTER = ROOT / "experiments" / "mentori" / "orchestrator" / "distiller_firing.py"
LOCK = ROOT / "experiments" / "LOCK.toml"
OUT = ROOT / "findings" / "recompute" / "distiller_count_g3_d1"
OUT_JSON = "distiller_count_g3_d1.json"
TAR_SET = "fig4_records_1023"
MEMBER = "fig4_records_1023/findings/runs/exp_03__full_orchestrator__exp_v4_s20_n0/answers.json"
PROV = ROOT / "findings" / "figures_provisional" / "fig4" / "figure5_provenance.json"   # D283: Figure 5 (4 until 6 Nov)
PROV_KEY = "findings/runs/exp_03__full_orchestrator__exp_v4_s20_n0/answers.json"
KNOWN = {"threshold_chars": 209712, "answers": 135}       # RUNNING.md 26 Oct 21:20
D98_SUBSET = ROOT / "findings" / "recompute" / "D98_subset" / "d98_subset.json"
OUT_SINK = ROOT / "findings" / "recompute" / "distiller_count_g3_d2d3"
OUT_SINK_JSON = "distiller_count_g3_d2d3.json"
SINK_DRAWS = {1: 135, 2: 45, 3: 45}                       # D98: 135 once, then D98's 45 at draws 2 and 3 (fig4.md C4)
COMPARED = ("answers", "step_attempts", "steps_over_threshold", "distill_status", "largest_step_output")
RUNNING_SAID = {"answers": 135, "step_attempts": 146, "steps_over_threshold": 0, "distill_status": {"not_asked": 146},
                "largest_chars": 62712, "largest_answer_key": "exp_v4_s20_n0|full_orchestrator|OOD_048|d1",
                "largest_step_id": "step_1"}       # experiments/RUNNING.md, 26 Oct 21:20 (live file, sha unrecorded)


class Refused(RuntimeError):
    pass


def _find(x, key):
    if isinstance(x, dict):
        if key in x:
            yield x[key]
        for v in x.values():
            yield from _find(v, key)
    elif isinstance(x, list):
        for v in x:
            yield from _find(v, key)


def build() -> bytes:
    path = fig_repro.frozen(TAR_SET, MEMBER)
    sha = fig_repro.sha256_file(path)
    rec = list(_find(json.loads(PROV.read_text()), PROV_KEY))
    if sha not in rec:
        raise Refused(f"frozen answers.json sha256 {sha[:12]}; {PROV.relative_to(ROOT)} records {rec}")
    rep = [f"answers.json sha256 {sha[:12]} equals {PROV.name}'s record"]
    thr = distiller_firing.threshold_chars()
    data = json.loads(path.read_text())
    n_d1 = sum(1 for r in data.get("results", []) if str(r.get("answer_key", "")).endswith("|d1"))
    if thr != KNOWN["threshold_chars"] or n_d1 != KNOWN["answers"] or len(data.get("results", [])) != n_d1:
        raise Refused(f"threshold {thr}, draw-1 answers {n_d1} of {len(data.get('results', []))}; want {KNOWN}")
    rep.append(f"threshold {thr:,} characters (LOCK num_ctx) and {n_d1} draw-1 answers, as RUNNING.md 26 Oct 21:20")
    out = distiller_firing.count(path)
    out["answers_path"] = f"{TAR_SET}.tar:{MEMBER}"            # not the local extraction folder
    lg = out["largest_step_output"]
    got = {"answers": out["answers"], "step_attempts": out["step_attempts"],
           "steps_over_threshold": out["steps_over_threshold"], "distill_status": out["distill_status"],
           "largest_chars": lg["chars"], "largest_answer_key": lg["answer_key"], "largest_step_id": lg["step_id"]}
    tars = fig_repro._read_sums(ROOT / "findings" / "recompute" / "frozen_inputs" / "SHA256SUMS")
    doc = {
        "provenance": {
            "script": SCRIPT, "script_sha256": fig_repro.sha256_file(ROOT / SCRIPT),
            "command": f"uv run python {SCRIPT}",
            "inputs": [{"path": f"{TAR_SET}.tar", "sha256": tars[f"{TAR_SET}.tar"],
                        "role": "frozen tar (findings/recompute/frozen_inputs/SHA256SUMS)"},
                       {"path": f"{TAR_SET}.tar:{MEMBER}", "sha256": sha, "role": "G3 full_orchestrator answers"},
                       {"path": str(COUNTER.relative_to(ROOT)), "sha256": fig_repro.sha256_file(COUNTER),
                        "role": "the counting function"},
                       {"path": str(LOCK.relative_to(ROOT)), "sha256": fig_repro.sha256_file(LOCK),
                        "role": "num_ctx for the threshold"},
                       {"path": str(PROV.relative_to(ROOT)), "sha256": fig_repro.sha256_file(PROV),
                        "role": "anchor: the answers file's recorded sha256"}],
            "reproduced": rep,
        },
        "result": out,
        "against_running_md_26oct_2120": {"running_md": RUNNING_SAID, "this_run": got, "equal": got == RUNNING_SAID},
    }
    return (json.dumps(doc, indent=1, ensure_ascii=False) + "\n").encode()


def draw_of(row: dict) -> int:
    """The draw of a result, from the last field of its answer key."""
    return int(str(row.get("answer_key", "")).rsplit("|d", 1)[-1])


def count_rows(rows: list) -> dict:
    """distiller_firing.count on these rows alone, through a temporary answers.json; the path is left out."""
    with tempfile.TemporaryDirectory(prefix="distiller_count_") as t:
        p = Path(t) / "answers.json"
        p.write_text(json.dumps({"results": rows}))
        out = distiller_firing.count(p)
    out.pop("answers_path")
    return out


def build_sink(answers: Path) -> bytes:
    """R7: the count on a read-only copy of the sink after G7, per draw and together, the draw-1 rows held to the
    frozen count first."""
    answers = Path(answers)
    if not answers.is_file():
        raise Refused(f"{answers}: no such file")
    sha = fig_repro.sha256_file(answers)
    rows = json.loads(answers.read_text()).get("results", [])
    per = Counter(draw_of(r) for r in rows)
    if dict(per) != SINK_DRAWS:
        raise Refused(f"answers per draw {dict(sorted(per.items()))}, want {SINK_DRAWS} (D98)")
    subset = json.loads(D98_SUBSET.read_text())["ids"]
    for d in (2, 3):
        got = sorted(r.get("question_id") for r in rows if draw_of(r) == d)
        if got != sorted(subset):
            raise Refused(f"draw {d} is not D98's {len(subset)} questions, once each")
    frozen = json.loads(build())["result"]
    d1 = count_rows([r for r in rows if draw_of(r) == 1])
    moved = [k for k in COMPARED if d1[k] != frozen[k]]
    if moved:
        raise Refused(f"the draw-1 rows differ from the frozen draw 1's count in {moved}: {[(d1[k], frozen[k]) for k in moved]}")
    result = {"all_draws": count_rows(rows), **{f"draw_{d}": count_rows([r for r in rows if draw_of(r) == d])
                                                for d in (1, 2, 3)}}
    doc = {"provenance": {"script": SCRIPT, "script_sha256": fig_repro.sha256_file(ROOT / SCRIPT),
                          "command": f"uv run python {SCRIPT} --sink <read-only copy of answers.json>",
                          "inputs": [{"path": "the full pipeline's answers.json, a read-only copy", "sha256": sha,
                                      "role": "G3 full_orchestrator answers after G7"},
                                     {"path": str(D98_SUBSET.relative_to(ROOT)), "sha256":
                                      fig_repro.sha256_file(D98_SUBSET), "role": "D98's 45 questions"},
                                     {"path": str(COUNTER.relative_to(ROOT)), "sha256": fig_repro.sha256_file(COUNTER),
                                      "role": "the counting function"}],
                          "reproduced": [f"the draw-1 rows give the frozen draw 1's count on {list(COMPARED)}"]},
           "scope": "225 answers: 135 at draw 1, 45 at each of draws 2 and 3; not Rule 12's 405, since D98 stopped draws "
                    "2 and 3 at 45 questions",
           "result": result}
    return (json.dumps(doc, indent=1, ensure_ascii=False) + "\n").encode()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--sink", help="a read-only copy of the full pipeline's answers.json after G7 (fig4.md R7)")
    ap.add_argument("--out", help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    try:
        data = build_sink(args.sink) if args.sink else build()
    except (Refused, fig_repro.FrozenInputError) as e:
        print(f"distiller_count_g3_d1 REFUSED, nothing written: {e}", file=sys.stderr)
        return 2
    out = Path(args.out) if args.out else (OUT_SINK if args.sink else OUT)
    target = out / (OUT_SINK_JSON if args.sink else OUT_JSON)
    if args.check:
        same = target.is_file() and target.read_bytes() == data
        print(f"distiller_count_g3_d1 check: {'byte-equal' if same else 'DIFFERS'}")
        return 0 if same else 1
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    doc = json.loads(data)
    for line in doc["provenance"]["reproduced"]:
        print("reproduced:", line)
    if args.sink:
        print(json.dumps({k: {x: v[x] for x in ("answers", "step_attempts", "steps_over_threshold")}
                          for k, v in doc["result"].items()}))
        print(f"wrote {target}")
        return 0
    print(json.dumps(doc["against_running_md_26oct_2120"]["this_run"]))
    print("equal to RUNNING.md 26 Oct 21:20:", doc["against_running_md_26oct_2120"]["equal"])
    print(f"wrote {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
