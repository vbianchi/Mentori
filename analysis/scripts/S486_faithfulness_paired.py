#!/usr/bin/env python3
"""S486 - the judge's faithfulness score under the plain call and under the call with passages, paired per answer.

WHY. AUDIT_2026-10-25 told Valerio that faithfulness 5/5 rises from 941 of 1,545 answers under the plain call to
1,130 of 1,539 with the retrieved passages, 223 answers up to 5 and 33 down, and that answers the plain call scored
correctness 0 get 5/5 faithfulness in 2 of 41 (plain) against 7 of 41 (with passages). Those numbers came from
scratch code (audit_1025/synthesis/faith86.py, inventory findings/audits/scratch_repro_2026-10-26/INVENTORY.md F9,
action A10) and are meant to replace the abstract's "81.7% versus 82.5%". Figure 5 reads only the call with passages
(S473's compute() d, drawn by S497 as panel f); nothing committed paired the two calls. This script ports
faith86.py's logic unchanged.

WHAT IT COUNTS. Input: S3's G1 collect of 23 October (g1_collect.jsonl, sha256 f5ff75bc, the file Figure 5 read),
frozen in findings/recompute/fig2_inputs/ and read through scripts/fig_repro.frozen(). One row per answer
(6 strategies x 135 questions x 3 draws = 2,430). Each row holds two judge calls by devstral-small-2:24b:
  a  the plain call (question, key and answer);
  b  the call with passages (the same, plus the passages the strategy retrieved).
Only the 86 answerable questions of the D5 key count (S463.key_groups(), Rule 8; S473 uses the same set). Of a call,
a faithfulness score counts only when the call's status is "ok"; a call that errored, had no answer or was not
applicable is left out of that call's count (so the two calls' n differ: 1,545 against 1,539); the JSON gives the
answers each call leaves out, by status (counts.*.plain_not_ok_by_status and passages_not_ok_by_status).
  plain 5/5          answers whose plain call scored faithfulness 5, of the answers with a plain score.
  with passages 5/5  the same for call b. This is Figure 5's total (S473's compute() d_all, fig5_data_state.json),
                     the anchor.
  paired             answers with both scores: up = 5 with passages and below 5 plain; down = 5 plain and below 5
                     with passages.
  correctness 0      answers whose plain call scored correctness 0 (the plain call's own score; an answer with no
                     text has no plain score and is not among them), and of those, how many each call scored
                     faithfulness 5. Each call's denominator is the correctness-0 answers that call scored.
Every count is also given per strategy.

REPRODUCE BEFORE WRITING (README.md:75-79). Before writing any number the script recomputes Figure 5's faithfulness
counts (S473's compute() d, S497's panel f) from the same rows: the with-passages score counts 0 to 5 over all
strategies (fig5_data_state.json "d_all": n 1,539, at 5 1,130) and per strategy (figure5_numbers.json sheet "Fig. 5f",
written by S497, its judge pass and fail rows summed), and checks the collect's sha256 against the one
figure5_provenance.json recorded. Any mismatch stops the run and nothing is written.

KEY v2.5 (D188, Valerio, 31 October: "every figure using v2.4 needs to move to v2.5"). After the reproduction above
has passed on the frozen v2.4 collect, the answers are read again through S463.judge_rows (scripts/judge_rows_v25.py,
as Figures 2 and 5 read G1 since D186 (3)): S463.read_collect on the frozen collect, its outs read from the frozen
fig2 set (relocate, as S463 rebuild), then per answer its key v2.5 row (S512, out_s6_g1 with out_s6_g1r15 as
--replace, under --s6, default the frozen fig2 folder) where one exists, else its key v2.4 row. A v2.5 row chosen
replaces the collect's row of that answer, both calls (a and b) with it, and every count above is made on the rows
chosen ("counts" and "summary"). While out_s6_g1 is absent every answer is the collect's v2.4 row, the counts equal
the v2.4 ones, and "judge_rows" records "awaiting S6" with the number of answers of the changed questions read from
key v2.4 and provisional true. "counts_v24" keeps the all-strategy counts of the frozen v2.4 collect, the anchor.

D201 Q2 (Valerio, 2 November 2026): S486 stays pinned to the v2.4 anchor until Figure 5 moves to v2.5. The committed plate
decides. A plate with no judge_key in fig5_data_state.json, the D166 plate of tonight, runs as before: the --s6 default is
the frozen fig2 folder, the counts and the summary stay on the v2.4 rows, and every output value stays as it was.
Figure 5's D200 plate draws key v2.5 rows, where the with-passages 5/5 is 1,133 of 1,539 against the D166 plate's 1,130.
Build order Q2's O1 for that plate is proposed, not ruled, so the following branch runs only once a plate carrying
judge_key "v2.5" (S497's D200 path writes it) is committed in fig5: --s6 then defaults to the frozen fig3_s6 set (S6_SET),
"counts" and "summary" are on key v2.5, the run must reach KNOWN_D_ALL_V25, and the plate is held on those counts to
d_all, sheet Fig. 5f and KNOWN_D_ALL_V25, with the collect's sha256 read from the plate's inputs_sha256. KNOWN_D_ALL stays
the v2.4 anchor, held on the frozen collect in both cases, and "counts_v24" keeps the letter's figures.

COMMAND, from the repository root (no model call, no network):
  uv run python scripts/S486_faithfulness_paired.py            writes findings/recompute/S486_faithfulness_paired/
  uv run python scripts/S486_faithfulness_paired.py --check    recomputes and requires the committed json byte-equal
  --s6 <folder>                                                where out_s6_g1 and out_s6_g1r15 are (D186 (3));
                                                               default the frozen fig2 folder, or the frozen fig3_s6
                                                               set once the committed plate is on key v2.5
The output carries no time: input paths with sha256, the script's sha256 and the command.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import fig_repro  # noqa: E402


def _load(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


S457 = _load("S457", ROOT / "scripts" / "S457_fig2_panels.py")
S463 = _load("S463", ROOT / "scripts" / "S463_fig2_ranking.py")

SCRIPT = "scripts/S486_faithfulness_paired.py"
OUT = ROOT / "findings" / "recompute" / "S486_faithfulness_paired"
OUT_JSON = "S486_faithfulness_paired.json"
FROZEN_SET, FROZEN_REL = "fig2", "g1_collect.jsonl"
S6_SET = "fig3_s6"                                    # the S6 rows Figures 3 and 5 read (S528); a v2.5 plate only
FIG5 = ROOT / "findings" / "figures_provisional" / "fig5"
ANCHOR_STATE = FIG5 / "fig5_data_state.json"          # S473 compute()'s d_all, written by S497
ANCHOR_SHEETS = FIG5 / "figure6_numbers.json"         # S497's sheet Fig. 6d (D283: Figure 6, 5 until 6 Nov; f until D295) (judge pass and fail rows summed)
ANCHOR_PROV = FIG5 / "figure6_provenance.json"        # the collect's sha256 Figure 5 read
KNOWN_D_ALL = {"n": 1539, "at5": 1130}                # INVENTORY.md F9, AUDIT_2026-10-25.md:241-246
KNOWN_D_ALL_V25 = {"n": 1539, "at5": 1133}            # the same count on the rows of S6_SET, for a v2.5 plate (Q2's O1)
CONFIGS = list(S463.CONFIGS)
LABEL = dict(S463.LABEL)
DRAWS = (1, 2, 3)


class Refused(RuntimeError):
    pass


def rel(p: Path) -> str:
    return str(Path(p).resolve().relative_to(ROOT))


def faith(call: dict | None, field: str = "faithfulness"):
    """A call's score for field when the call's status is ok, else None (faith86.py's sc())."""
    x = call or {}
    return (x.get("scores") or {}).get(field) if x.get("status") == "ok" else None


def tally(rows: list[dict], groups: dict) -> dict:
    """faith86.py's counts over the answerable rows, all strategies ("all") and per strategy."""
    keys = Counter((r["config"], r["question_id"], r["draw"]) for r in rows)
    dup = [k for k, n in keys.items() if n > 1]
    if dup:
        raise Refused(f"{len(dup)} answers appear twice in the collect, first {dup[0]}")
    by = {g: Counter() for g in ["all"] + CONFIGS}
    b_counts = {g: Counter() for g in ["all"] + CONFIGS}
    not_ok = {(g, side): Counter() for g in ["all"] + CONFIGS for side in ("plain", "passages")}
    for r in rows:
        if groups.get(r["question_id"]) != "answerable":
            continue
        if r["config"] not in CONFIGS:
            raise Refused(f"strategy {r['config']!r} is not one of G1's six")
        a, b, c = faith(r.get("a")), faith(r.get("b")), faith(r.get("a"), "correctness")
        for side, call, v in (("a", r.get("a"), a), ("b", r.get("b"), b)):
            if (call or {}).get("status") == "ok" and v is None:
                raise Refused(f"{r['answer_key']}: call {side} is ok but has no faithfulness score")
        for g in ("all", r["config"]):
            C = by[g]
            for side, call in (("plain", r.get("a")), ("passages", r.get("b"))):
                st = (call or {}).get("status") if call else "absent"
                if st != "ok":                         # audit 27 Oct F13: the answers each call leaves out, by status
                    not_ok[(g, side)][str(st)] += 1
            if a is not None:
                C["plain_n"] += 1
                C["plain_at5"] += a == 5
            if b is not None:
                C["passages_n"] += 1
                C["passages_at5"] += b == 5
                b_counts[g][b] += 1
            if a is not None and b is not None:
                C["paired_n"] += 1
                C["paired_both5"] += a == 5 and b == 5
                C["paired_up_to5"] += b == 5 and a != 5
                C["paired_down_from5"] += a == 5 and b != 5
            if c == 0 and a is not None:
                C["c0_plain_n"] += 1
                C["c0_plain_at5"] += a == 5
            if c == 0 and b is not None:
                C["c0_passages_n"] += 1
                C["c0_passages_at5"] += b == 5
    order = ("plain_n", "plain_at5", "passages_n", "passages_at5", "paired_n", "paired_both5", "paired_up_to5",
             "paired_down_from5", "c0_plain_n", "c0_plain_at5", "c0_passages_n", "c0_passages_at5")
    out = {}
    for g in ["all"] + CONFIGS:
        C = by[g]
        d = {k: int(C[k]) for k in order}
        d["plain_share_at5_pct"] = round(100 * C["plain_at5"] / C["plain_n"], 6) if C["plain_n"] else None
        d["passages_share_at5_pct"] = round(100 * C["passages_at5"] / C["passages_n"], 6) if C["passages_n"] else None
        d["passages_score_counts"] = {str(k): int(b_counts[g][k]) for k in range(6)}
        for side in ("plain", "passages"):
            d[f"{side}_not_ok_by_status"] = dict(sorted((k, int(v)) for k, v in not_ok[(g, side)].items()))
        out[g] = d
    return out


def plate_on_v25() -> bool:
    """D201 Q2: the committed Figure 5 was drawn on key v2.5 rows (S497's D200 path writes judge_key "v2.5")."""
    return json.loads(ANCHOR_STATE.read_text()).get("judge_key") == "v2.5"


def reproduce(counts: dict, collect_sha: str, known: dict = None) -> list[str]:
    """Figure 5's faithfulness counts (S473's compute() d, S497's panel f) from the same rows, before any number is
    written. known: the value those rows must give, KNOWN_D_ALL (the D166 plate's) unless named (D201 Q2). The collect's
    sha256 is read from {path, sha256} entries (the D166 plate) or from inputs_sha256 (S497's D200 path)."""
    known = KNOWN_D_ALL if known is None else known
    rep = []
    prov = json.loads(ANCHOR_PROV.read_text())
    recorded = [v.get("sha256") for v in _walk(prov) if isinstance(v, dict) and
                str(v.get("path", "")).endswith("g1_collect.jsonl")]
    recorded += [h for k, h in prov.get("inputs_sha256", {}).items() if k.endswith("g1_collect.jsonl")]
    if collect_sha not in recorded:
        raise Refused(f"the frozen collect has sha256 {collect_sha[:12]}, {rel(ANCHOR_PROV)} records {recorded}")
    rep.append(f"collect sha256 {collect_sha[:12]} equals the one {rel(ANCHOR_PROV)} records")
    d_all = json.loads(ANCHOR_STATE.read_text())["d_all"]
    got = {"n": counts["all"]["passages_n"], "at5": counts["all"]["passages_at5"]}
    if got != known or {k: d_all[k] for k in known} != known:
        raise Refused(f"with passages 5/5: got {got}, Figure 6 committed {d_all}, known {known}")
    if counts["all"]["passages_score_counts"] != {str(k): v for k, v in d_all["counts"].items()}:
        raise Refused(f"with-passages score counts {counts['all']['passages_score_counts']} differ from Figure 6's "
                      f"{d_all['counts']}")
    rep.append(f"with passages 5/5 {got['at5']:,} of {got['n']:,} and the counts at scores 0 to 5 equal "
               f"{rel(ANCHOR_STATE)} d_all")
    sh = json.loads(ANCHOR_SHEETS.read_text())["sheets"]["Fig. 6d"]
    cols = sh["columns"]
    want = {}
    for row in sh["rows"]:                      # one row per strategy and judge verdict (pass, fail): summed
        x = dict(zip(cols, row))
        w = want.setdefault(x["strategy"], {str(k): 0 for k in range(6)})
        for k in range(6):
            w[str(k)] += x[f"faithfulness_{k}"]
    for c in CONFIGS:
        if counts[c]["passages_score_counts"] != want.get(LABEL[c]):
            raise Refused(f"{c}: with-passages counts {counts[c]['passages_score_counts']}, S497's sheet Fig. 6d "
                          f"(judge pass and fail rows summed) {want.get(LABEL[c])}")
    rep.append(f"per strategy, the with-passages counts at scores 0 to 5 equal {rel(ANCHOR_SHEETS)} sheet Fig. 6d "
               f"(judge pass and fail rows summed; 6 of 6 strategies)")
    return rep


def _walk(x):
    yield x
    if isinstance(x, dict):
        for v in x.values():
            yield from _walk(v)
    elif isinstance(x, list):
        for v in x:
            yield from _walk(v)


def rows_v25(collect: Path, rows: list[dict], groups: dict, s6: Path | None = None) -> tuple[list[dict], dict]:
    """D188: the collect's rows with each answer's key v2.5 row in place of its v2.4 row where S6 has judged one
    (S463.judge_rows on S463.read_collect of the frozen collect, its outs relocated to the frozen fig2 folder as S463
    rebuild reads them). Returns the rows chosen, in the collect's order, and judge_rows' record."""
    fig2 = collect.parent
    side = json.loads(collect.with_name(collect.name + ".json").read_text())
    outs = (side.get("_provenance") or {}).get("inputs") or []
    if sorted(Path(o).name for o in outs) != ["out", "out_g1r15"] or len({str(Path(o).parent) for o in outs}) != 1:
        raise Refused(f"the frozen sidecar records the outs {outs}, not one pull's out/ and out_g1r15/")
    reruns = S463.rerun_keys()
    try:
        read = S463.read_collect(collect, list(DRAWS), groups, reruns, None, None, {str(Path(outs[0]).parent): str(fig2)})
        jr = S463.judge_rows(read, collect, groups, reruns, list(DRAWS), s6, None)
    except S463.Refused as e:
        raise Refused(f"judge rows (D188): {e}") from None
    v25 = {(k[1], k[2], k[3]): v["row"] for k, v in jr["choice"].items() if k != "_sources" and v["status"] == "v2.5"}
    out = [v25.get((r["config"], r["question_id"], r["draw"]), r) for r in rows]
    if sum(1 for r in rows if (r["config"], r["question_id"], r["draw"]) in v25) != len(v25):
        raise Refused(f"judge rows (D188): {len(v25)} key v2.5 rows chosen, not all of them answers of the collect")
    rec = S463.judge_rows_record(jr)
    return out, {k: rec[k] for k in ("reader", "status", "provisional", "answers_read", "cells_from_v25",
                                     "awaiting_s6_read", "sources")}


def check_known(counts: dict, known: dict, what: str) -> str:
    """The all-strategy with-passages count on these rows equals known. Returns the line for the record."""
    got = {"n": counts["all"]["passages_n"], "at5": counts["all"]["passages_at5"]}
    if got != known:
        raise Refused(f"with passages 5/5 on {what}: got {got}, known {known}")
    return f"with passages 5/5 on {what}: {got['at5']:,} of {got['n']:,}, the known value"


def build(s6: Path | None = None) -> bytes:
    from experiments.runner import experiment
    collect = fig_repro.frozen(FROZEN_SET, FROZEN_REL)
    collect_sha = fig_repro.sha256_file(collect)
    groups = S463.key_groups()
    rows24 = [json.loads(ln) for ln in collect.read_text().splitlines() if ln.strip()]
    if len(rows24) != len(CONFIGS) * S463.N_Q * len(DRAWS):
        raise Refused(f"{len(rows24)} rows in the collect, want {len(CONFIGS) * S463.N_Q * len(DRAWS)}")
    counts24 = tally(rows24, groups)
    s6_named = s6 is not None
    on25 = plate_on_v25()                            # D201 Q2: the committed plate decides
    if on25 and not s6_named:
        s6 = fig_repro.frozen(S6_SET, ".")
    # the v2.4 anchor first (README.md:75-79): held to the plate while the plate is on v2.4, to its own value after
    rep = [check_known(counts24, KNOWN_D_ALL, "the frozen v2.4 collect")] if on25 else reproduce(counts24, collect_sha)
    rows, jrec = rows_v25(collect, rows24, groups, s6)
    counts = tally(rows, groups)
    if on25 and not s6_named:                        # a named folder is a look at other rows, with no known value
        rep.append(check_known(counts, KNOWN_D_ALL_V25, f"key v2.5, the frozen {S6_SET} set"))
    if on25:
        rep += reproduce(counts, collect_sha, KNOWN_D_ALL_V25)
    rep.append(f"judge rows (D188, judge_rows_v25 through S463.judge_rows): {jrec['status']}")
    inputs = [(collect, "S3's G1 collect of 23 Oct, frozen set fig2 (fig_repro.frozen)"),
              (experiment.KEY_V24, "answer key v2.4 (question types)"),
              (experiment.KEY_D5, "the D5 key (answerable or not)"),
              (ANCHOR_STATE, "anchor: Figure 6's d_all (S473 compute(), written by S497)"),
              (ANCHOR_SHEETS, "anchor: S497 sheet Fig. 6d (judge pass and fail rows summed)"),
              (ANCHOR_PROV, "anchor: the collect sha256 Figure 6 read")]
    if jrec["cells_from_v25"]:
        # review of build 2, F4: what was read on key v2.5 is listed with the rest (the S6 rows' run_sha256 sit in
        # judge_rows.sources; the folder they were read from is recorded under provenance.s6_folder)
        inputs.append((ROOT / "data" / "ground_truth_v2" / "ground_truth_v2_5_as_v1.json",
                       "answer key v2.5: the key of the S6 rows chosen (judge_rows_v25)"))
        if on25 and not s6_named:
            inputs.append((s6 / "SHA256SUMS", "the frozen fig3_s6 set's list of files (S528)"))
    a = counts["all"]
    doc = {
        "provenance": {
            "script": SCRIPT, "script_sha256": fig_repro.sha256_file(ROOT / SCRIPT),
            "command": f"uv run python {SCRIPT}",
            "inputs": [{"path": rel(p), "sha256": fig_repro.sha256_file(p), "role": why} for p, why in inputs],
            "ported_from": "scratch audit_1025/synthesis/faith86.py (INVENTORY.md F9, A10)",
            "reproduced": rep,
            **({"s6_folder": str(s6) if s6_named else rel(s6) if on25 else
                "the folder holding the v2.4 outs (S463.judge_rows default)"} if jrec["cells_from_v25"] else {}),
            "plate_held_on": "key v2.5" if on25 else "key v2.4",
            "code_sha256": {f"scripts/{n}": fig_repro.sha256_file(ROOT / "scripts" / n)
                            for n in ("S463_fig2_ranking.py", "judge_rows_v25.py")},
        },
        "judge_rows": jrec,
        "definitions": {
            "questions": "the 86 answerable questions of the D5 key (S463.key_groups), all three draws",
            "rows": "per answer the key v2.5 judge row where S6 has judged one, else the frozen v2.4 collect's row "
                    "(judge_rows_v25 through S463.judge_rows; both calls a and b come from the row chosen); "
                    "counts_v24 is the v2.4 collect alone, the anchor",
            "plain": "call a, the judge without passages; a score counts when the call's status is ok",
            "passages": "call b, the judge with the retrieved passages; a score counts when the call's status is ok",
            "paired_up_to5": "both scored; 5 with passages, below 5 plain",
            "paired_down_from5": "both scored; 5 plain, below 5 with passages",
            "c0": "the plain call's correctness score is 0; each call's n is the c0 answers that call scored",
            "not_ok_by_status": "answerable answers whose call (plain or passages) has a status other than ok, by "
                                "that status ('absent' when the row holds no such call); they are left out of that "
                                "call's n, so each call's n plus its not-ok answers is the answerable answers",
        },
        "summary": {
            "plain_5of5": f"{a['plain_at5']} of {a['plain_n']}",
            "passages_5of5": f"{a['passages_at5']} of {a['passages_n']}",
            "paired_up_to5": a["paired_up_to5"], "paired_down_from5": a["paired_down_from5"],
            "paired_n": a["paired_n"],
            "c0_plain_5of5": f"{a['c0_plain_at5']} of {a['c0_plain_n']}",
            "c0_passages_5of5": f"{a['c0_passages_at5']} of {a['c0_passages_n']}",
            "plain_not_ok": f"{sum(a['plain_not_ok_by_status'].values())} ("
                            + ", ".join(f"{k} {v}" for k, v in a["plain_not_ok_by_status"].items()) + ")",
            "passages_not_ok": f"{sum(a['passages_not_ok_by_status'].values())} ("
                               + ", ".join(f"{k} {v}" for k, v in a["passages_not_ok_by_status"].items()) + ")",
        },
        "counts": counts,
        "counts_v24": counts24["all"],
    }
    return (json.dumps(doc, indent=1, ensure_ascii=False) + "\n").encode()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="recompute and require the committed json byte-equal")
    ap.add_argument("--out", default=str(OUT), help=argparse.SUPPRESS)
    ap.add_argument("--s6", default=None, help="the folder holding out_s6_g1 and out_s6_g1r15 (S6G1, key v2.5); "
                                               "default the frozen fig2 folder, or the frozen fig3_s6 set once the "
                                               "committed plate is on key v2.5 (D201 Q2)")
    args = ap.parse_args(argv)
    try:
        data = build(Path(args.s6) if args.s6 else None)
    except (Refused, fig_repro.FrozenInputError) as e:
        print(f"S486 REFUSED, nothing written: {e}", file=sys.stderr)
        return 2
    target = Path(args.out) / OUT_JSON
    if args.check:
        same = target.is_file() and target.read_bytes() == data
        print(f"S486 check: {rel(target) if target.is_relative_to(ROOT) else target} "
              f"{'byte-equal' if same else 'DIFFERS'} (sha256 {hashlib.sha256(data).hexdigest()[:12]})")
        return 0 if same else 1
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    doc = json.loads(data)
    for line in doc["provenance"]["reproduced"]:
        print("reproduced:", line)
    for k, v in doc["summary"].items():
        print(f"{k}: {v}")
    print(f"wrote {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
