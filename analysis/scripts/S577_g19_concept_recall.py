#!/usr/bin/env python3
"""S577 (D249 O2, G19): concept recall of G19's four arms R, A, B, C, with the reading S573 used for G17 (D181).

THE READING. D181 (experiments/README.md D181): S505's loose matcher with the question rule, Q-need, reading (b), on key
v2.5, through scripts/d181_concept_recall.py score(answer, concepts, question, flagged), the function S471 --d181
(L3_d181, Figure 3a), S474 --d181 (L2_d181, Supplementary Figure 8) and S573 (G17) call. Per arm:
  - R, B, C (exp_01 records): S573.score_record, unchanged: the stored generation.answer (or ""), with the turn-limit
    note removed where generation.rlm.metadata.turn_limit_note flags it;
  - A (the package's records): the stored answer (or ""), flag None, as S474 read_g6 reads G6's package answers (the
    package appends no note).
A row keeps the matcher's value on the stored text, and says whether the answer failed (exp_01: generation.error;
package: error, or status not "ok", S474.status_of's rule). The header's means apply Rule 10 (a failed answer scores 0),
as S575 and S578 read them.

REPRODUCE FIRST (README.md:75-79), before any G19 row: both paths against the rows Figure 3 draws.
  - exp_01 path: S573.reproduce, G1 RLM-10's draw 1 answers to the 86 (K1) against L3_d181 (86 of 86 at S573's build).
  - package path: G6's cap 10 draw 1 answers to the 86 (frozen g6_d135, its sha256 held to SOURCE_MTIMES.json as S571
    holds it) against L2_d181's cap 10 draw 1 rows, wherever the answer's sha256 is the row's: at least 80 compared and
    every compared concept_recall and found equal.
Neither S518 nor T2X stored a concept recall for R's answers (S518 reads judge rows only; T2X's judge_t2x.sh writes judge
rows only), so R's values are new numbers, made by the exp_01 path reproduced above.

INPUTS (findings/recompute/G19_runs/README.md "Reading").
  --runs-root   a folder holding runs/<run>/answers.jsonl for A, B and C (g19_check.run_id); each holds a line for every
                key of the 46 at draw 1 and no other key, and A one line per key.
  --r-t2, --r-t2x  R's two sinks (T2's gemma3 rlm_10 sink, T2X's); both are exp_01__rlm_10__exp_v4_s20_n0+gemma3-27b.
                R reads the 29 of stored_R.t2_d98 from the first and the 17 of stored_R.t2x from the second, draw 1;
                the sinks may hold other keys (T2's holds draws 2 and 3 and other questions).
  --manifest    g19_stored_R.json (launch_g19.sh manifest, on the Studio): every R line read must have the manifest's
                line_sha256 (g19_check.manifest), so R is the answer the manifest pinned, whichever copy is read.

OUT. --out (default findings/recompute/G19_concept_recall/): concept_recall.jsonl (one row per answer, 184) and
header.json (reading, pins, reproduce, inputs' sha256, means per arm and kind, code sha256). No model call.

    uv run --frozen python scripts/S577_g19_concept_recall.py --reproduce-only
    uv run --frozen python scripts/S577_g19_concept_recall.py --runs-root ~/s3_inputs/g19 \
        --r-t2 <T2 sink> --r-t2x <T2X sink> --manifest <g19_stored_R.json> [--out DIR]
    uv run --frozen python scripts/S578_g19_reading_test.py        (tests S577 and S578 on made-up rows)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
G19 = ROOT / "findings" / "recompute" / "G19_runs"
for p in (str(SCRIPTS), str(ROOT), str(G19)):
    if p not in sys.path:
        sys.path.insert(0, p)

import S470_l1_signals as S470  # noqa: E402
import S573_g17_concept_recall as S573  # noqa: E402
import g19_check as GC  # noqa: E402

SCRIPT = "scripts/S577_g19_concept_recall.py"
OUT = ROOT / "findings" / "recompute" / "G19_concept_recall"
L2_D181 = ROOT / "findings" / "recompute" / "L2_d181" / "concept_recall.jsonl"
QFILE = GC.QUESTIONS
QFILE_SHA256 = "a711e3ee0b63bdf444c33b3cb8b2815a331d40c6c89b84d62d1f187b1d507d10"   # as S579 pins it
ARMS = ("R", "A", "B", "C")
LABEL = {"R": "R Mentori RLM-10 (stored)", "A": "A package RLM", "B": "B search off", "C": "C gate off"}
MIN_REPRODUCED = 80
DECISION = "D249 O2"                               # S594 (G20, D260) sets its own


class Refused(Exception):
    pass


def d181():
    import d181_concept_recall as D
    return D


def line_sha(rec: dict) -> str:
    """g19_check.manifest's line_sha256."""
    return GC.sha256_bytes(json.dumps(rec, sort_keys=True).encode())


def questions(path: Path = QFILE) -> dict:
    """The 46 under the pin, with each question's kind (one, many) and R's two sources."""
    if GC.sha256_file(path) != QFILE_SHA256:
        raise Refused(f"{Path(path).name} is not the pinned G19 questions file ({QFILE_SHA256[:12]})")
    q = GC.read_ids(path)
    if sorted(q["t2_d98"] + q["t2x"]) != sorted(q["ids"]) or len(q["t2_d98"]) != 29 or len(q["t2x"]) != 17:
        raise Refused("the questions file does not split the 46 into T2's 29 and T2X's 17")
    q["kind"] = {i: "one" for i in q["one_paper"]} | {i: "many" for i in q["many_paper"]}
    return q


def last_lines(path: Path) -> tuple[dict, dict]:
    """({answer_key: (line number, record)} of the last line of each key, {answer_key: lines})."""
    out, n_lines = {}, defaultdict(int)
    with open(path, encoding="utf-8") as f:
        for n, raw in enumerate(f, 1):
            if raw.strip():
                r = json.loads(raw)
                out[r["answer_key"]] = (n, r)
                n_lines[r["answer_key"]] += 1
    return out, n_lines


def failed_of(arm: str, rec: dict) -> bool:
    if arm == "A":
        return bool(rec.get("error")) or rec.get("status") != "ok"
    return bool((rec.get("generation") or {}).get("error"))


def read_arms(runs_root: Path, r_t2: Path, r_t2x: Path, manifest: Path, q: dict) -> tuple[dict, dict]:
    """{arm: {question: {"rec", "source", "run_id", "answer_key", "sink"}}} for R, A, B, C, and {file: sha256} read."""
    out, inputs = {}, {}
    for arm in ("A", "B", "C"):
        sink = Path(runs_root) / "runs" / GC.run_id(arm)
        f = sink / "answers.jsonl"
        if not f.exists():
            raise Refused(f"no {f}")
        inputs[str(f)] = S470.sha256_file(f)
        lines, n_lines = last_lines(f)
        want = {GC.answer_key(arm, i): i for i in q["ids"]}
        extra, missing = sorted(set(lines) - set(want)), sorted(set(want) - set(lines))
        if extra or missing:
            raise Refused(f"{f}: {len(extra)} keys outside the 46 at draw 1 {extra[:2]}, {len(missing)} of the 46 "
                          f"missing {missing[:2]}")
        if arm == "A" and any(v > 1 for v in n_lines.values()):
            raise Refused(f"{f}: a package answer stored more than once (one attempt per answer, Q29)")
        out[arm] = {i: {"rec": lines[k][1], "source": f"runs/{sink.name}/answers.jsonl:{lines[k][0]}",
                        "run_id": GC.run_id(arm), "answer_key": k, "sink": sink} for k, i in want.items()}
    m = json.loads(Path(manifest).read_text(encoding="utf-8"))
    inputs[str(manifest)] = S470.sha256_file(manifest)
    if m.get("questions_sha256") != QFILE_SHA256 or m.get("run_id") != GC.run_id("R") or m.get("draw") != GC.DRAW:
        raise Refused(f"{manifest}: not G19's R manifest (questions {str(m.get('questions_sha256'))[:12]}, run "
                      f"{m.get('run_id')}, draw {m.get('draw')})")
    pinned = {r["answer_key"]: r for r in m.get("rows") or []}
    out["R"] = {}
    for src, sink, qids in (("T2", Path(r_t2), q["t2_d98"]), ("T2X", Path(r_t2x), q["t2x"])):
        if sink.name != GC.run_id("R"):
            raise Refused(f"R ({src}): {sink} is not a sink of {GC.run_id('R')}")
        f = sink / "answers.jsonl"
        if not f.exists():
            raise Refused(f"R ({src}): no {f}")
        inputs[str(f)] = S470.sha256_file(f)
        lines, _ = last_lines(f)
        for i in qids:
            k = GC.answer_key("R", i)
            if k not in lines:
                raise Refused(f"R ({src}): {k} has no line in {f}")
            n, rec = lines[k]
            p = pinned.get(k)
            if p is None or p.get("source") != src or p.get("question_id") != i:
                raise Refused(f"R ({src}): {k} is not in the manifest as a {src} answer")
            if line_sha(rec) != p.get("line_sha256"):
                raise Refused(f"R ({src}): {k}'s line in {f} is not the one the manifest pinned")
            out["R"][i] = {"rec": rec, "source": f"R {src} {f}:{n}", "run_id": GC.run_id("R"), "answer_key": k,
                           "sink": sink}
    if len(pinned) != 46:
        raise Refused(f"{manifest}: {len(pinned)} rows, not 46")
    return out, inputs


def score(arm: str, rec: dict, key25: dict) -> dict:
    """The matcher's value on the stored text (module docstring)."""
    if arm == "A":
        ans = rec.get("answer") or ""
        qk = key25["questions"][rec["question_id"]]
        return {"answer_sha256": S470.sha256_text(ans), "turn_limit_note": None, "error": rec.get("error"),
                "stop_reason": rec.get("stop_reason"),
                **d181().score(ans, qk["expected_concepts"], qk["question"], None)}
    return S573.score_record(rec, key25)


def reproduce_package(key25: dict, ids: list) -> dict:
    """G6 cap 10 draw 1 (frozen g6_d135) scored here against L2_d181's cap 10 draw 1 rows (module docstring)."""
    import fig_repro as FR
    import S463_fig2_ranking as S463
    g6 = FR.check_committed(FR.frozen(S463.G6_SET)) / S463.G6_RUN10 / "answers.jsonl"
    want_sha = json.loads((FR.frozen(S463.G6_SET) / "SOURCE_MTIMES.json").read_text())["files"][
        f"findings/runs/{S463.G6_RUN10}/answers.jsonl"]["sha256"]
    if S470.sha256_file(g6) != want_sha:
        raise Refused(f"{g6} is not the file SOURCE_MTIMES.json records")
    recs, _ = last_lines(g6)
    ref = {}
    for raw in L2_D181.read_text(encoding="utf-8").splitlines():
        r = json.loads(raw)
        if r.get("cap") == 10 and r["draw"] == 1:
            ref[r["question_id"]] = r
    compared = skipped = 0
    bad = []
    for i in ids:
        rec = recs[f"cap10|{i}|d1"][1]
        mine = score("A", rec, key25)
        if i not in ref or mine["answer_sha256"] != ref[i]["answer_sha256"]:
            skipped += 1
            continue
        compared += 1
        if mine["concept_recall"] != ref[i]["concept_recall"] or mine["found"] != ref[i]["found"]:
            bad.append((i, mine["concept_recall"], ref[i]["concept_recall"]))
    if bad or compared < MIN_REPRODUCED:
        raise Refused(f"reproduce failed: G6 cap 10 draw 1, {compared} compared ({skipped} skipped), {len(bad)} differ "
                      f"from L2_d181, first {bad[:3]}")
    return {"reference": d181().rel(L2_D181), "reference_sha256": S470.sha256_file(L2_D181),
            "answers": FR.frozen_label(g6), "compared": compared, "skipped_other_answer": skipped, "equal": compared,
            "what": "the package path (stored answer, flag None, d181_concept_recall.score) on G6's cap 10 draw 1 "
                    "answers to the 86 = L2_d181's concept_recall and found, where the answer's sha256 is the row's"}


def reproduce(key25: dict) -> dict:
    ids86, _ = S573.questions()
    return {"exp_01": S573.reproduce(key25, ids86), "package": reproduce_package(key25, ids86)}


def rows_for(arms: dict, q: dict, key25: dict) -> list:
    rows = []
    for arm in ARMS:
        for i in q["ids"]:
            x = arms[arm][i]
            rows.append({"arm": arm, "answer_key": x["answer_key"], "run_id": x["run_id"], "question_id": i, "draw": 1,
                         "kind": q["kind"][i], "source": x["source"], "failed": failed_of(arm, x["rec"]),
                         **score(arm, x["rec"], key25)})
    return rows


def means(rows: list) -> dict:
    """Per arm and kind: the mean with Rule 10 (a failed answer scores 0), and the matcher's raw mean beside it."""
    by = defaultdict(list)
    for r in rows:
        for k in (r["kind"], "all"):
            by[(r["arm"], k)].append(r)
    return {f"{a}|{k}": {"answers": len(v), "failed": sum(r["failed"] for r in v),
                         "mean_concept_recall": round(sum(0.0 if r["failed"] else (r["concept_recall"] or 0.0)
                                                          for r in v) / len(v), 6),
                         "mean_concept_recall_stored_text": round(sum(r["concept_recall"] or 0.0 for r in v) / len(v), 6)}
            for (a, k), v in sorted(by.items())}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--runs-root", type=Path)
    ap.add_argument("--r-t2", type=Path)
    ap.add_argument("--r-t2x", type=Path)
    ap.add_argument("--manifest", type=Path, default=GC.MANIFEST)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--reproduce-only", action="store_true")
    a = ap.parse_args(argv)
    try:
        q = questions()
        _, key25 = S573.keys()
        rep = reproduce(key25)
        for k, v in rep.items():
            print(f"reproduced ({k} path): {v['equal']} of {v['compared']} equal {Path(v['reference']).parent.name} "
                  f"({v['skipped_other_answer']} other answers skipped)")
        if a.reproduce_only:
            return 0
        if a.runs_root is None or a.r_t2 is None or a.r_t2x is None:
            raise Refused("--runs-root, --r-t2 and --r-t2x are required")
        arms, inputs = read_arms(a.runs_root.expanduser(), a.r_t2.expanduser(), a.r_t2x.expanduser(),
                                 a.manifest.expanduser(), q)
        rows = rows_for(arms, q, key25)
    except (Refused, GC.Refused, S573.Refused, d181().Refused, S470.Refused) as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    D = d181()
    header = {"script": SCRIPT, "script_sha256": S470.sha256_file(Path(__file__)),
              "command": "uv run --frozen python " + " ".join([SCRIPT] + list(argv if argv is not None else sys.argv[1:])),
              "written_utc": S470.utc(), "git": S470.git_state(), "decision": DECISION, "reading": "D181",
              "matcher": D.MATCHER_TEXT, "columns": D.COLUMNS_TEXT, "arms": LABEL,
              "key": {"path": key25["path"], "sha256": key25["sha256"], "version": key25["version"]},
              "questions": {"file": str(QFILE.relative_to(ROOT)), "sha256": QFILE_SHA256, "n": len(q["ids"])},
              "code_sha256": {**D.code_sha256(),
                              "scripts/S470_l1_signals.py": S470.sha256_file(SCRIPTS / "S470_l1_signals.py"),
                              "scripts/S573_g17_concept_recall.py": S470.sha256_file(SCRIPTS / "S573_g17_concept_recall.py"),
                              "findings/recompute/G19_runs/g19_check.py": S470.sha256_file(G19 / "g19_check.py")},
              "reproduce": rep, "inputs_sha256": inputs, "rows": len(rows), "means": means(rows),
              "means_rule": "mean_concept_recall: Rule 10, a failed answer scores 0; mean_concept_recall_stored_text: "
                            "the matcher on the stored text of every answer"}
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "concept_recall.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    (a.out / "header.json").write_text(json.dumps(header, indent=1, sort_keys=True) + "\n")
    for k, v in header["means"].items():
        print(f"{k}: {v['answers']} answers, {v['failed']} failed, mean concept recall {v['mean_concept_recall']:.4f}")
    print(f"wrote {a.out / 'concept_recall.jsonl'} ({len(rows)} rows) and header.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
