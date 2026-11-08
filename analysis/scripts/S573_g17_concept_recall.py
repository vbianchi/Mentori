#!/usr/bin/env python3
"""S573 (D240, G17): concept recall of G17's three arms, with the reading Figure 3 and Supplementary Figure 8 draw.

THE READING. D181 (experiments/README.md D181): S505's loose matcher with the question rule, Q-need, reading (b), on key
v2.5, through scripts/d181_concept_recall.py: score(answer, concepts, question, flagged) is the function S471 --d181
called for findings/recompute/L3_d181/ (Figure 3a's concept recall rows, S463 read_concept_recall_d181) and S474 --d181
for L2_d181 (Supplementary Figure 8, S476). The text is the stored answer with the turn-limit note removed where the
record flags it (generation.rlm.metadata.turn_limit_note, as S471's flags()); a failed answer's text is "" and scores 0
(Rule 10, as S470 reads it: answer = generation.answer or ""). Key v2.4 is read through S470.the_key() and v2.5 through
d181_concept_recall.the_key_v25(), with the pins and checks S471 --d181 uses; concepts and question text from v2.5.

REPRODUCE FIRST (README.md:75-79). Before any G17 row: G1 RLM-10's draw 1 answers to the 86 (K1's frozen copy, the
records S470 read for L3) are scored by the same call, and each must give the concept_recall L3_d181 stores for its key
wherever the answer's sha256 equals the row's (G1R15's reruns replaced a few answers after K1; those are skipped and
counted). At least 80 of the 86 must be compared and every compared one equal, or nothing is written.

INPUTS. --runs-root: a folder holding runs/<run>/answers.jsonl for the three G17 runs (the snap in ~/s3_inputs/g17, or
the G17 clone's findings/ folder). Each run must hold a line for every one of the 86 at draw 1 (the last line of a key is
its answer, records.py) and no other key; --partial reads what is there (a progress look; the header says so).

OUT. --out (default findings/recompute/G17_concept_recall/): concept_recall.jsonl, one row per answer (S471 --d181's
columns plus kind one/many), and header.json (the reading, the keys' pins, the reproduce result, the inputs' sha256,
means per arm and kind, code sha256). No model call.

    uv run --frozen python scripts/S573_g17_concept_recall.py --runs-root ~/s3_inputs/g17 [--out DIR] [--partial]
    uv run --frozen python scripts/S573_g17_concept_recall.py --reproduce-only

DRAWS 2 AND 3 (D249 O1): --draws 2 3 reads G17's d23 sinks (runs/<run>/answers.jsonl holding the 86 at draws 2 and 3
and no other key) and writes, by default, findings/recompute/G17_concept_recall_d23/; the reproduce and the scoring are
the same, each row carries its draw, and the header adds "draws". Without --draws (or --draws 1) nothing changes.

    uv run --frozen python scripts/S573_g17_concept_recall.py --runs-root ~/s3_inputs/g17_d23 --draws 2 3
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
for p in (str(SCRIPTS), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

import S470_l1_signals as S470  # noqa: E402

SCRIPT = "scripts/S573_g17_concept_recall.py"
OUT = ROOT / "findings" / "recompute" / "G17_concept_recall"
OUT_D23 = ROOT / "findings" / "recompute" / "G17_concept_recall_d23"                  # D249 O1, --draws 2 3
QFILE = ROOT / "findings" / "recompute" / "G17_runs" / "g17_questions.json"
L3_D181 = ROOT / "findings" / "recompute" / "L3_d181" / "concept_recall.jsonl"
INDEX = "exp_v4_s20_n0"
ARMS = ("rlm_10_ctrl", "rlm_10_nosearch", "rlm_10_nogate")
MIN_REPRODUCED = 80


class Refused(Exception):
    pass


def d181():
    import d181_concept_recall as D
    return D


def questions() -> tuple[list, dict]:
    d = json.loads(QFILE.read_text(encoding="utf-8"))
    kind = {q: "one" for q in d["sets"]["one"]} | {q: "many" for q in d["sets"]["many"]}
    return d["ids"], kind


def keys() -> tuple[dict, dict]:
    key24 = S470.the_key()
    return key24, d181().the_key_v25(key24)


def last_lines(path: Path) -> dict:
    """{answer_key: (line number, record)}: the last line of each key (records.py: a line is an attempt)."""
    out = {}
    with open(path, encoding="utf-8") as f:
        for n, raw in enumerate(f, 1):
            if raw.strip():
                r = json.loads(raw)
                out[r["answer_key"]] = (n, r)
    return out


def score_record(rec: dict, key25: dict) -> dict:
    g = rec.get("generation") or {}
    ans = g.get("answer") or ""
    flag = ((g.get("rlm") or {}).get("metadata") or {}).get("turn_limit_note")
    q = key25["questions"][rec["question_id"]]
    return {"answer_sha256": S470.sha256_text(ans), "turn_limit_note": flag, "error": g.get("error"),
            "stop_reason": g.get("stop_reason"),
            **d181().score(ans, q["expected_concepts"], q["question"], flag)}


def reproduce(key25: dict, ids: list) -> dict:
    """G1 RLM-10 draw 1 (K1's frozen copy) scored here against L3_d181's stored values (module docstring)."""
    import fig_repro as FR
    k1 = FR.frozen("k1_inputs_runs", "k1_inputs_runs") / f"exp_01__rlm_10__{INDEX}" / "answers.jsonl"
    want = {}
    for raw in L3_D181.read_text(encoding="utf-8").splitlines():
        r = json.loads(raw)
        if r["config"] == "rlm_10" and r["draw"] == 1:
            want[r["answer_key"]] = r
    recs = last_lines(k1)
    compared = skipped = 0
    bad = []
    for q in ids:
        k = f"{INDEX}|rlm_10|{q}|d1"
        rec = recs[k][1]
        mine = score_record(rec, key25)
        if mine["answer_sha256"] != want[k]["answer_sha256"]:
            skipped += 1
            continue
        compared += 1
        if mine["concept_recall"] != want[k]["concept_recall"] or mine["found"] != want[k]["found"]:
            bad.append((k, mine["concept_recall"], want[k]["concept_recall"]))
    if bad or compared < MIN_REPRODUCED:
        raise Refused(f"reproduce failed: G1 RLM-10 draw 1, {compared} compared ({skipped} answers differ from L3_d181's, "
                      f"G1R15), {len(bad)} differ from L3_d181, first {bad[:3]}")
    return {"reference": d181().rel(L3_D181),
            "reference_sha256": S470.sha256_file(L3_D181), "answers": FR.frozen_label(k1),
            "compared": compared, "skipped_other_answer": skipped, "equal": compared,
            "what": "d181_concept_recall.score on G1 RLM-10's draw 1 answers to the 86 (K1) = L3_d181's concept_recall "
                    "and found, where the answer's sha256 is the row's"}


def rows_for(root: Path, ids: list, kind: dict, key25: dict, partial: bool, draws=(1,)) -> tuple[list, dict]:
    rows, inputs = [], {}
    tag = "the 86 at draw 1" if tuple(draws) == (1,) else f"the 86 at draws {', '.join(map(str, draws))}"
    for arm in ARMS:
        run = f"exp_01__{arm}__{INDEX}"
        f = root / "runs" / run / "answers.jsonl"
        if not f.exists():
            raise Refused(f"no {f}")
        inputs[str(f)] = S470.sha256_file(f)
        lines = last_lines(f)
        want = {f"{INDEX}|{arm}|{q}|d{d}" for d in draws for q in ids}
        extra = sorted(set(lines) - want)
        missing = sorted(want - set(lines))
        if extra or (missing and not partial):
            raise Refused(f"{f}: {len(extra)} keys outside {tag} {extra[:3]}, {len(missing)} of the 86 "
                          f"missing {missing[:3]}")
        for d in draws:
            for q in ids:
                k = f"{INDEX}|{arm}|{q}|d{d}"
                if k not in lines:
                    continue
                n, rec = lines[k]
                if rec.get("draw") != d or rec.get("question_id") != q:
                    raise Refused(f"{f}:{n}: key {k} holds question {rec.get('question_id')} draw {rec.get('draw')}")
                rows.append({"answer_key": k, "run_id": run, "config": arm, "question_id": q, "draw": d,
                             "kind": kind[q], "source": f"runs/{run}/answers.jsonl:{n}", **score_record(rec, key25)})
    return rows, inputs


def means(rows: list) -> dict:
    by = defaultdict(list)
    for r in rows:
        for k in (r["kind"], "all"):
            by[(r["config"], k)].append(r["concept_recall"] or 0.0)
    return {f"{c}|{k}": {"answers": len(v), "mean_concept_recall": round(sum(v) / len(v), 6)}
            for (c, k), v in sorted(by.items())}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--runs-root", type=Path)
    ap.add_argument("--out", type=Path, default=None, help=f"default {OUT.relative_to(ROOT)} (draw 1), "
                                                             f"{OUT_D23.relative_to(ROOT)} (--draws 2 3)")
    ap.add_argument("--draws", type=int, nargs="+", default=[1], help="1 (D240, the default) or 2 3 (D249 O1)")
    ap.add_argument("--partial", action="store_true")
    ap.add_argument("--reproduce-only", action="store_true")
    a = ap.parse_args(argv)
    draws = tuple(a.draws)
    if draws not in ((1,), (2, 3)):
        print(f"REFUSED: --draws {' '.join(map(str, draws))} is neither 1 (D240) nor 2 3 (D249 O1)", file=sys.stderr)
        return 2
    if a.out is None:
        a.out = OUT if draws == (1,) else OUT_D23
    try:
        ids, kind = questions()
        key24, key25 = keys()
        rep = reproduce(key25, ids)
        print(f"reproduced: {rep['equal']} of {rep['compared']} G1 RLM-10 draw 1 answers equal L3_d181 "
              f"({rep['skipped_other_answer']} other answers skipped)")
        if a.reproduce_only:
            return 0
        if a.runs_root is None:
            raise Refused("--runs-root is required (the folder holding runs/<run>/answers.jsonl)")
        rows, inputs = rows_for(a.runs_root.expanduser(), ids, kind, key25, a.partial, draws)
    except (Refused, d181().Refused, S470.Refused) as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    D = d181()
    header = {"script": SCRIPT, "script_sha256": S470.sha256_file(Path(__file__)),
              "command": "uv run --frozen python " + " ".join([SCRIPT] + list(argv if argv is not None else sys.argv[1:])),
              "written_utc": S470.utc(), "git": S470.git_state(), "decision": "D240", "reading": "D181",
              "matcher": D.MATCHER_TEXT, "columns": D.COLUMNS_TEXT, "partial": a.partial,
              "key": {"path": key25["path"], "sha256": key25["sha256"], "version": key25["version"]},
              "questions": {"file": str(QFILE.relative_to(ROOT)), "sha256": S470.sha256_file(QFILE), "n": len(ids)},
              "code_sha256": {**D.code_sha256(), "scripts/S470_l1_signals.py": S470.sha256_file(SCRIPTS / "S470_l1_signals.py")},
              "reproduce": rep, "inputs_sha256": inputs, "rows": len(rows), "means": means(rows)}
    if draws != (1,):
        header.update(decision="D249", draws=list(draws),
                      means_by_draw={str(d): means([r for r in rows if r["draw"] == d]) for d in draws})
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "concept_recall.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    (a.out / "header.json").write_text(json.dumps(header, indent=1, sort_keys=True) + "\n")
    for k, v in header["means"].items():
        print(f"{k}: {v['answers']} answers, mean concept recall {v['mean_concept_recall']:.4f}")
    print(f"wrote {a.out / 'concept_recall.jsonl'} ({len(rows)} rows) and header.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
