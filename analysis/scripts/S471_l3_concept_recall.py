#!/usr/bin/env python3
"""S471 - plan row L3: concept recall on the Figure 2 answers (G1), per answer, on D12's loose matcher, provisional.

Why. Plan row L3, "Concept matcher (concept recall) on the Figure 2 answers", feeds Figure 5; review A7 split it from
L1 because D17 ties concept recall, and only it, to Valerio's concept labels (plan P2). D114 Q37 O-a (Valerio, 22
October): L3 runs now on D12's loose matcher (scripts/concept_match_loose.py), provisional, and is rerun on the
matcher P2's labels choose (notes/DECISIONS_2026-10-13.md, D12 and D17). D12 makes the loose value the headline and
prints the exact value beside it, so both are written. Nothing here is retyped: the loose value is
concept_recall_loose's, and the exact value counts the concepts that function marks found_by "exact" (its rule 1, the
substring test concept.lower() in answer.lower()), as S432's exact_substring does.

The answers. G1's 2,430 answers as S470 reads them (S470.the_key, verify_inputs, read_answers): <inputs>/runs/
exp_01__<config>__exp_v4_s20_n0/answers.jsonl, each file checked against <inputs>/MANIFEST.sha256, the last line of
each answer_key, cross-checked against records.read_run, the six strategies x 135 questions x 3 draws all present,
the groups from the runner's D5 key (Rule 8). The record line S470 names (source) is read again for its RLM flag,
generation.rlm.metadata.turn_limit_note, and its answer must be the one S470 read.

The value of an answer.
  not_answerable (39 questions)  null, reason "not applicable" (LIST.md Rule 8: concept recall does not score them)
  answerable (86), false_premise (10)
                 the text: the stored answer, with Mentori's fixed turn-limit note removed exactly when the record
                 flags it (D115 L1e O-a; scripts/turn_limit_note.strip: a flagged answer that does not end with the
                 note stops the run, nothing written). The judge keeps the note (D68 Q11); the removal is for concept
                 recall only. The concepts: the key's expected_concepts (S373.AS_V1, the v2.4 key in v1 format).
                 concept_recall_loose = concept_recall_loose(text, concepts); concept_recall_exact = the concepts it
                 marks found_by "exact" / the concepts, rounded to four decimals. An empty text (a blocked or errored
                 answer, max_turns_empty) takes 0 on both: concept recall is defined on an empty text (Rule 10), and
                 an answer that failed stays in as a fail.
Each row keeps found_by per concept ("exact", "loose" or null), so P2's matcher can be compared concept by concept.

Gate (README.md:75-79), before anything is written: concept_match_loose.spec_failures() and
turn_limit_note.spec_failures() are empty; then this script's own score() on S432's 107 completed answers of the
generator selection (the deposit's exp00_phase2_latest.json final_answer, sha256 equal to S432's record of it, on the
same v2.4 key) gives S432's stored loose and exact_substring values and its loose found counts on all 107.
Both files are frozen copies in this repository (D155), read only after their sha256 is checked: S432's output
findings/recompute/fig2_repo_inputs/S432_selection_concept_recall_v24.json (written 13 October; S432 rerun on 27
October gives the same JSON but its written_utc, so the 13 October bytes are frozen) against
frozen_inputs/SHA256SUMS, and the deposit's findings/recompute/upstream_inputs/publication/results/
exp00_phase2_latest.json against S432's record of it. Neither the untracked findings/recompute/S432_*.json nor the
sibling checkout scripts/machine.py finds (RESULTS) is read.

Outputs, under --outdir (default findings/recompute/L3/):
  concept_recall.jsonl   one row per answer, 2,430, in S470's order (draw, the key's question order, strategy)
  header.json            provenance: script, matcher and helper sha256s, the key, the inputs manifest and answers
                         files, the gate's result, the counts, git commit, the command; "provisional": true
Printed: counts only (rows per group, notes removed per strategy, flagged answers, unflagged answers holding the
note's text, empty texts scored (the text score() read, after the note's removal, empty or whitespace only), rows
whose value the removal changed). No mean is printed.

    uv run --no-sync python scripts/S471_l3_concept_recall.py --inputs ~/l1_inputs
    uv run --no-sync python scripts/S471_l3_concept_recall.py --inputs ~/l1_inputs --gate-only
    uv run --no-sync python scripts/check_S471.py                                     # checks and mutants

D181 (--d181; experiments/README.md:1301-1308). The final reading: S505's loose matcher with the question rule, Q-need,
reading (b), on key v2.5, through scripts/d181_concept_recall.py (its docstring gives the rule, the key's checks and
the gates). Without --d181 nothing above changes: the same key, matcher, rows and folder. With it:
  the key      the answers, the groups and the question text as above (S470.the_key, v2.4, whose question texts and
               answerable flags v2.5 must equal); the concepts and the question text scored are key v2.5's
  a row        concept_recall (the D181 value, the headline) with n_counted, found, concept_status and
               concept_removed; the base loose and exact values on the same v2.5 concepts beside it, named *_base;
               no column named concept_recall_loose, so a reader of the provisional folder cannot read this one by
               mistake. A scored answer with no counted concept would have no value: refused (none on v2.5)
  the gates    G-A this script's gate() (S432 107 of 107, v2.4); G-B score() of d181_concept_recall with an empty
               question on the same 107 answers gives S432's loose value; G-C S505's stored M4 reproduced
               (d181_concept_recall.gate_m4); G-D on this run's answers, the D181 score with an empty question on the
               v2.4 concepts gives the committed provisional rows' concept_recall_loose (--held-ref, default
               findings/recompute/L3/concept_recall.jsonl) on every scored answer. Any failure exits 1, nothing written
  the folder   --outdir, default findings/recompute/L3_d181/; L3/ itself is refused (S473 pins its bytes)
  the header   "provisional": false, "reading": "D181", the matcher, the v2.5 key and the v2.4 key the gates read,
               the helper's and S505's sha256s, the four gates' results, the counts (concepts by status)

    uv run --frozen python scripts/S471_l3_concept_recall.py --inputs ~/l1_inputs --d181
    uv run --frozen python scripts/check_d181_L3_L2.py                                # checks and mutants of --d181

FROZEN INPUTS (--frozen, in place of --inputs; audit of 1 November, row 4). The six answers files come from the tar
s457_mirror_20261022 through fig_repro.frozen(), a tar that holds all six at the sha256 L3's header records
(answer_lengths_20261020 holds all six too; k1_inputs_runs holds two, and the four reran strategies differ there). A
temporary folder lays them out as S470
reads them, runs/<run>/answers.jsonl, with a MANIFEST.sha256 of those six lines, so S470.verify_inputs runs unchanged. Each
sha256 must equal the one the committed header of the folder being rebuilt records (L3/header.json, with --d181
L3_d181/header.json), else it refuses. The rows do not change. The header differs from a run on ~/l1_inputs in
inputs.folder, inputs.manifest_sha256 (~/l1_inputs's manifest is not frozen), written_utc and the command.

    uv run --frozen python scripts/S471_l3_concept_recall.py --frozen [--d181] [--outdir DIR]
    uv run --frozen python scripts/S471_frozen_test.py                                # rows, refusals and mutants of --frozen
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
for p in (str(SCRIPTS), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

import concept_match_loose  # noqa: E402
import turn_limit_note  # noqa: E402
import S470_l1_signals as S470  # noqa: E402
import fig_repro as FR  # noqa: E402  (D155: the frozen copies the gate reads, checked against SHA256SUMS)
class _LazyD181:
    """d181_concept_recall, imported on first use: it imports S505, whose import sets two KMP_* variables in os.environ
    (S494's read audit names them, D201 Q9 O1), so a run without --d181 leaves its environment as it found it."""
    def __getattr__(self, name):
        import d181_concept_recall as m
        globals()["D181"] = m
        return getattr(m, name)


D181 = _LazyD181()  # (--d181 only)
from machine import RECOMPUTE, rel  # noqa: E402

SCRIPT = "scripts/S471_l3_concept_recall.py"
OUTDIR = RECOMPUTE / "L3"
APPLIES = ("answerable", "false_premise")
NA = "not applicable"
S432_JSON = RECOMPUTE / "fig2_repo_inputs" / "S432_selection_concept_recall_v24.json"   # frozen (D155), SHA256SUMS
PHASE2 = RECOMPUTE / "upstream_inputs" / "publication" / "results" / "exp00_phase2_latest.json"   # frozen deposit copy
PHASE2_REL = "deposit/publication/results/exp00_phase2_latest.json"     # its name in S432's provenance
GATE_N = 107
OUTDIR_D181 = RECOMPUTE / "L3_d181"                 # --d181: a folder of its own (L3/ stays the reference)
HELD_REF = OUTDIR / "concept_recall.jsonl"         # --d181 G-D: the committed provisional rows
FROZEN_TAR = "s457_mirror_20261022"                # --frozen: holds the six answers files by the sha256 L3 records
_VIEWS = []                                        # --frozen: the temporary folders, alive until the process ends


class Refused(Exception):
    """A refusal before anything is written (exit 2)."""


class GateFail(Exception):
    """The gate did not reproduce (exit 1, nothing written)."""


def score(answer: str, concepts: list, flagged) -> dict:
    """One answer's concept recall on the loose matcher and the exact substring test, after the note's removal."""
    text, removed = turn_limit_note.strip(answer, flagged)
    loose, per = concept_match_loose.concept_recall_loose(text, concepts, detail=True)
    n_exact = sum(1 for x in per if x["found_by"] == "exact")
    return {"note_removed": removed, "scored_text_sha256": S470.sha256_text(text), "n_concepts": len(concepts),
            "found_loose": sum(1 for x in per if x["found_by"] is not None), "found_exact": n_exact,
            "concept_recall_loose": loose, "concept_recall_exact": round(n_exact / len(concepts), 4),
            "found_by": [x["found_by"] for x in per]}


def gate(key: dict) -> dict:
    """The matchers' own rule cases, then score() on S432's 107 completed answers (the module docstring, Gate)."""
    fails = list(concept_match_loose.spec_failures()) + list(turn_limit_note.spec_failures())
    if fails:
        raise GateFail(f"rule cases fail: {fails[:3]}")
    try:
        FR.check_committed(S432_JSON)                    # D155: S432's output as frozen, its sha256 in SHA256SUMS
    except FR.FrozenInputError as e:
        raise GateFail(f"S432's frozen output: {e}") from None
    ref = json.loads(S432_JSON.read_text(encoding="utf-8"))
    want_sha = ref["provenance"]["inputs_sha256"].get(PHASE2_REL)
    got_sha = S470.sha256_file(PHASE2)
    if got_sha != want_sha:
        raise GateFail(f"{PHASE2} sha256 {got_sha[:12]} is not the file S432 read ({str(want_sha)[:12]})")
    by = {(r["model"], r["question_id"]): r for r in json.loads(PHASE2.read_text(encoding="utf-8"))["per_question_results"]}
    n, bad = 0, []
    for a in ref["answers"]:
        if not a["completed"]:
            continue
        n += 1
        got = score(by[(a["model"], a["question_id"])]["final_answer"],
                    key["questions"][a["question_id"]]["expected_concepts"], None)
        if (got["concept_recall_loose"], got["concept_recall_exact"], got["found_loose"]) != \
                (a["value_v24"]["loose"], a["value_v24"]["exact_substring"], a["found_v24"]["loose"]):
            bad.append(f"{a['model']} {a['question_id']}")
    if n != GATE_N or bad:
        raise GateFail(f"S432 reproduced on {n - len(bad)} of {n} completed answers (want {GATE_N} of {GATE_N}); "
                       f"first differing {bad[:3]}")
    return {"reference": rel(S432_JSON), "reference_sha256": S470.sha256_file(S432_JSON), "answers": rel(PHASE2),
            "answers_sha256": got_sha, "reproduced": f"{n} of {GATE_N}",
            "compared": "concept_recall_loose = value_v24.loose, concept_recall_exact = value_v24.exact_substring, "
                        "found_loose = found_v24.loose"}


def flags(inputs: Path, answers: list[dict]) -> dict:
    """answer_key -> generation.rlm.metadata.turn_limit_note, from the record line S470 read (its source)."""
    lines, out = {}, {}
    for a in answers:
        path, n = a["source"].rsplit(":", 1)
        if path not in lines:
            lines[path] = (inputs / path).read_text(encoding="utf-8").splitlines()
        rec = json.loads(lines[path][int(n) - 1])
        gen = rec.get("generation") or {}
        if rec.get("answer_key") != a["answer_key"] or (gen.get("answer") or "") != a["answer"]:
            raise Refused(f"{a['source']} is not the record S470 read for {a['answer_key']}")
        out[a["answer_key"]] = ((gen.get("rlm") or {}).get("metadata") or {}).get("turn_limit_note")
    return out


def rows_for(answers: list[dict], key: dict, flag: dict, d181: bool = False) -> list[dict]:
    """One row per answer. d181: the value is d181_concept_recall.score() with the key's question text."""
    out = []
    for a in answers:
        row = {k: a[k] for k in ("answer_key", "run_id", "config", "question_id", "draw", "group", "status",
                                 "stop_reason", "answer_sha256", "source")}
        row["turn_limit_note"] = flag[a["answer_key"]]
        if a["group"] in APPLIES:
            q = key["questions"][a["question_id"]]
            row.update(D181.score(a["answer"], q["expected_concepts"], q["question"], flag[a["answer_key"]]) if d181
                       else score(a["answer"], q["expected_concepts"], flag[a["answer_key"]]))
            row["reason"] = None
        elif d181:
            row.update(D181.na_fields(), reason=NA)
        else:
            row.update({"note_removed": False, "scored_text_sha256": None, "n_concepts": None, "found_loose": None,
                        "found_exact": None, "concept_recall_loose": None, "concept_recall_exact": None,
                        "found_by": None, "reason": NA})
        out.append(row)
    return out


def counts(rows: list[dict], answers: list[dict], key: dict) -> dict:
    by_key = {a["answer_key"]: a for a in answers}
    note_text = "Analysis reached turn limit"

    def scored_text(r):                                  # the text score() read: the note removed where flagged
        return turn_limit_note.strip(by_key[r["answer_key"]]["answer"], r["turn_limit_note"])[0]

    c = {"rows": len(rows), "by_group": dict(collections.Counter(r["group"] for r in rows)),
         "scored": sum(r["reason"] is None for r in rows), "not_applicable": sum(r["reason"] == NA for r in rows),
         "flagged": sum(r["turn_limit_note"] is True for r in rows),
         "note_removed": sum(r["note_removed"] for r in rows),
         "note_removed_by_strategy": dict(collections.Counter(r["config"] for r in rows if r["note_removed"])),
         "unflagged_holding_note_text": sum(r["turn_limit_note"] is not True
                                            and note_text in by_key[r["answer_key"]]["answer"] for r in rows),
         "empty_text_scored": sum(r["reason"] is None and not scored_text(r).strip() for r in rows),
         "status_scored": dict(collections.Counter(r["status"] for r in rows if r["reason"] is None))}
    changed = collections.Counter()
    for r in rows:
        if r["note_removed"]:
            kept = score(by_key[r["answer_key"]]["answer"], key["questions"][r["question_id"]]["expected_concepts"],
                         None)
            changed["loose"] += kept["concept_recall_loose"] != r["concept_recall_loose"]
            changed["exact"] += kept["concept_recall_exact"] != r["concept_recall_exact"]
    c["removal_changed_value"] = {"loose": changed["loose"], "exact": changed["exact"]}
    return c


# ---------------------------------------------------------------- D181 (--d181)

def gate_d181(key24: dict) -> dict:
    """G-B and G-C (module docstring, D181), after gate() (G-A) passed: d181_concept_recall's rule cases; its score()
    with an empty question on S432's 107 completed answers gives S432's loose value on each; S505's M4 reproduced."""
    try:
        fails = D181.spec_failures()
        if fails:
            raise GateFail(f"D181 rule cases fail: {fails[:3]}")
        ref = json.loads(S432_JSON.read_text(encoding="utf-8"))          # gate() checked its bytes and PHASE2's
        by = {(r["model"], r["question_id"]): r
              for r in json.loads(PHASE2.read_text(encoding="utf-8"))["per_question_results"]}
        count, differ = 0, []
        for a in ref["answers"]:
            if a["completed"]:
                count += 1
                got = D181.score(by[(a["model"], a["question_id"])]["final_answer"],
                                 key24["questions"][a["question_id"]]["expected_concepts"], "", None)
                if got["concept_recall"] != a["value_v24"]["loose"]:
                    differ.append(f"{a['model']} {a['question_id']}")
        if count != GATE_N or differ:
            raise GateFail(f"G-B: the D181 score with an empty question gives S432's loose value on {count - len(differ)}"
                           f" of {count} completed answers (want {GATE_N} of {GATE_N}); first differing {differ[:3]}")
        m4 = D181.gate_m4(key24)
    except D181.GateFail as e:
        raise GateFail(str(e)) from None
    return {"G-B": {"reference": rel(S432_JSON), "reproduced": f"{count} of {GATE_N}",
                    "compared": "d181_concept_recall.score(answer, v2.4 concepts, question '', None).concept_recall "
                                "= value_v24.loose"},
            "G-C": m4}


def held_d181(answers: list[dict], key24: dict, flag: dict, ref_path: Path) -> dict:
    """G-D: on this run's answers, the D181 score with an empty question on the v2.4 concepts equals the committed
    provisional reading's concept_recall_loose on every scored answer, and the reading scores no other answer."""
    ref = {}
    for line in Path(ref_path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            ref[r["answer_key"]] = r
    scored = [a for a in answers if a["group"] in APPLIES]
    differ = [a["answer_key"] for a in scored
              if a["answer_key"] not in ref or D181.score(
                  a["answer"], key24["questions"][a["question_id"]]["expected_concepts"], "",
                  flag[a["answer_key"]])["concept_recall"] != ref[a["answer_key"]]["concept_recall_loose"]]
    n_ref = sum(r.get("concept_recall_loose") is not None for r in ref.values())
    if differ or n_ref != len(scored):
        raise GateFail(f"G-D: the D181 score with an empty question reproduces {rel(ref_path)} on "
                       f"{len(scored) - len(differ)} of {len(scored)} scored answers ({n_ref} scored there); "
                       f"first differing {differ[:3]}")
    return {"reference": rel(ref_path), "reference_sha256": S470.sha256_file(Path(ref_path)),
            "reproduced": f"{len(scored)} of {n_ref}",
            "compared": "d181_concept_recall.score(answer, v2.4 concepts, question '', flag).concept_recall = the "
                        "reference row's concept_recall_loose, every scored answer"}


def write(outdir: Path, rows: list[dict], header: dict) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    for name, text in (("concept_recall.jsonl", "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows)),
                       ("header.json", json.dumps(header, indent=1, sort_keys=True) + "\n")):
        tmp = outdir / f".{name}.tmp"
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, outdir / name)


def frozen_view(header: Path) -> tuple[Path, dict]:
    """(a folder laid out as S470 reads one, its verify_inputs result with the frozen source). The module docstring,
    FROZEN INPUTS. Refused unless every answers file has the sha256 the committed header records."""
    want = json.loads(Path(header).read_text(encoding="utf-8"))["inputs"]["answers_sha256"]
    tmp = tempfile.TemporaryDirectory(prefix="S471_")
    _VIEWS.append(tmp)
    view = Path(tmp.name)
    lines = []
    try:
        for c in S470.CONFIGS:
            run = S470.run_of(c)
            src = FR.frozen(FROZEN_TAR, f"{FROZEN_TAR}/{c}/answers.jsonl")
            (view / "runs" / run).mkdir(parents=True)
            (view / "runs" / run / "answers.jsonl").symlink_to(src)
            lines.append(f"{S470.sha256_file(src)}  runs/{run}/answers.jsonl")
    except FR.FrozenInputError as e:
        raise Refused(str(e)) from None
    (view / "MANIFEST.sha256").write_text("\n".join(lines) + "\n")
    info = S470.verify_inputs(view)
    if info["answers_sha256"] != want:
        raise Refused(f"the frozen answers are not the files {rel(Path(header))} records")
    return view, {"folder": f"frozen:{FROZEN_TAR}.tar/{FROZEN_TAR}/<strategy>/answers.jsonl", **info}


def resolve_inputs(a, header: Path) -> tuple[Path, dict]:
    """(the folder to read, the header's inputs block): --frozen's view, else --inputs after S470's check."""
    if a.frozen:
        return frozen_view(header)
    inputs = a.inputs.expanduser()
    return inputs, {"folder": str(inputs), **S470.verify_inputs(inputs)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    where = ap.add_mutually_exclusive_group(required=True)
    where.add_argument("--inputs", type=Path, help="G1's answers as S470 reads them (~/l1_inputs)")
    where.add_argument("--frozen", action="store_true", help="G1's answers from the frozen tar (module docstring)")
    ap.add_argument("--outdir", type=Path, default=None, help="default findings/recompute/L3/ (with --d181: L3_d181/)")
    ap.add_argument("--gate-only", action="store_true", help="run the gate and stop")
    ap.add_argument("--d181", action="store_true",
                    help="D181's final reading: S505's loose Q-need (b) on key v2.5 (module docstring, D181)")
    ap.add_argument("--held-ref", type=Path, default=HELD_REF,
                    help="--d181 G-D: the committed provisional rows of the same answers (default L3/)")
    a = ap.parse_args(argv)
    try:
        key = S470.the_key()
        g = gate(key)
        print(f"gate: S432 reproduced on {g['reproduced']} completed answers (loose, exact substring, found counts); "
              f"rule cases of the loose matcher and the note's removal hold")
        if a.d181:
            return main_d181(a, argv, key, g)
        if a.outdir is None:
            a.outdir = OUTDIR
        if a.gate_only:
            return 0
        inputs, inputs_block = resolve_inputs(a, OUTDIR / "header.json")
        answers, info = S470.read_answers(inputs, key)
        flag = flags(inputs, answers)
        rows = rows_for(answers, key, flag)
        c = counts(rows, answers, key)
        header = {"script": SCRIPT, "script_sha256": S470.sha256_file(Path(__file__)),
                  "command": "uv run --no-sync python " + " ".join([SCRIPT] + list(argv if argv is not None
                                                                                    else sys.argv[1:])),
                  "written_utc": S470.utc(), "git": S470.git_state(), "plan_row": "L3",
                  "provisional": True,
                  "matcher": "loose (D12, scripts/concept_match_loose.py), provisional until P2's labels choose one "
                             "(D17; D114 Q37 O-a); exact = its rule 1, the substring test, beside it (D12)",
                  "turn_limit_note": "removed exactly before matching where generation.rlm.metadata.turn_limit_note "
                                     "is True (D115 L1e O-a, scripts/turn_limit_note.py); the judge keeps it (D68 Q11)",
                  "code_sha256": {"scripts/concept_match_loose.py": S470.sha256_file(SCRIPTS / "concept_match_loose.py"),
                                  "scripts/turn_limit_note.py": S470.sha256_file(SCRIPTS / "turn_limit_note.py"),
                                  "scripts/S470_l1_signals.py": S470.sha256_file(SCRIPTS / "S470_l1_signals.py"),
                                  "concept_recall_loose (source)":
                                      S470.source_sha(concept_match_loose.concept_recall_loose),
                                  "turn_limit_note.strip (source)": S470.source_sha(turn_limit_note.strip)},
                  "key": {"path": key["path"], "sha256": key["sha256"], "version": key["version"],
                          "source": key["source"]},
                  "inputs": inputs_block, "selection": info, "gate": g, "counts": c}
        write(a.outdir, rows, header)
        print(f"selection: {info['answers']} answers, questions {info['questions']}, status {info['status']}")
        print(f"rows {c['rows']}: scored {c['scored']} (answerable and false premise), not applicable "
              f"{c['not_applicable']}; empty texts scored {c['empty_text_scored']}; status of the scored "
              f"{c['status_scored']}")
        print(f"turn-limit note (D115 L1e): flagged {c['flagged']}, removed {c['note_removed']} "
              f"{c['note_removed_by_strategy']}; unflagged answers holding its text {c['unflagged_holding_note_text']}; "
              f"rows whose value the removal changed: loose {c['removal_changed_value']['loose']}, exact "
              f"{c['removal_changed_value']['exact']}")
        print(f"wrote {rel(a.outdir / 'concept_recall.jsonl')} and {rel(a.outdir / 'header.json')} (provisional)")
        return 0
    except (Refused, S470.Refused, turn_limit_note.NoteMismatch) as e:
        print(f"REFUSED, nothing written: {e}", file=sys.stderr)
        return 2
    except GateFail as e:
        print(f"GATE FAILED, nothing written: {e}", file=sys.stderr)
        return 1
    except D181.Refused as e:
        print(f"REFUSED, nothing written: {e}", file=sys.stderr)
        return 2


def main_d181(a, argv, key24: dict, g: dict) -> int:
    """--d181 (module docstring, D181): the gates G-B, G-C and G-D, then the rows on key v2.5, into a folder of
    their own. Exceptions are main()'s."""
    outdir = (a.outdir or OUTDIR_D181).expanduser()
    if outdir.resolve() == OUTDIR.resolve():
        raise Refused(f"--d181 does not write {rel(OUTDIR)}: it is the provisional reading the gates and S473 pin")
    try:
        key25 = D181.the_key_v25(key24)
    except D181.Refused as e:
        raise Refused(str(e)) from None
    gd = gate_d181(key24)
    print(f"D181 gates: G-B S432 reproduced on {gd['G-B']['reproduced']} with an empty question; G-C S505's M4 "
          f"{D181.M4_COLUMN} reproduced, all {gd['G-C']['reproduced']['all']}")
    if a.gate_only:
        return 0
    inputs, inputs_block = resolve_inputs(a, OUTDIR_D181 / "header.json")
    answers, info = S470.read_answers(inputs, key24)
    flag = flags(inputs, answers)
    held = held_d181(answers, key24, flag, a.held_ref.expanduser())
    print(f"D181 gate G-D: {held['reference']} reproduced on {held['reproduced']} scored answers")
    rows = rows_for(answers, key25, flag, d181=True)
    none = [r["answer_key"] for r in rows if r["reason"] is None and r["concept_recall"] is None]
    if none:
        raise Refused(f"{len(none)} scored answers have no counted concept under D181 (b), first {none[:3]}: "
                      f"this run does not decide their value")
    c = counts([D181.base_view(r) for r in rows], answers, key25)
    c["d181"] = D181.concept_counts([r for r in rows if r["reason"] is None])
    changed = sum(D181.score(r_a["answer"], key25["questions"][r["question_id"]]["expected_concepts"],
                             key25["questions"][r["question_id"]]["question"], None)["concept_recall"]
                  != r["concept_recall"] for r, r_a in zip(rows, answers) if r["note_removed"])
    c["d181"]["removal_changed_value"] = changed
    header = {"script": SCRIPT, "script_sha256": S470.sha256_file(Path(__file__)),
              "command": "uv run --frozen python " + " ".join([SCRIPT] + list(argv if argv is not None
                                                                               else sys.argv[1:])),
              "written_utc": S470.utc(), "git": S470.git_state(), "plan_row": "L3", "provisional": False,
              "reading": "D181", "matcher": D181.MATCHER_TEXT, "columns": D181.COLUMNS_TEXT,
              "turn_limit_note": "removed exactly before matching where generation.rlm.metadata.turn_limit_note "
                                 "is True (D115 L1e O-a, scripts/turn_limit_note.py); the judge keeps it (D68 Q11)",
              "code_sha256": {**D181.code_sha256(),
                              "scripts/S470_l1_signals.py": S470.sha256_file(SCRIPTS / "S470_l1_signals.py")},
              "key": {"path": key25["path"], "sha256": key25["sha256"], "version": key25["version"],
                      "source": key25["source"]},
              "gate_key": {"path": key24["path"], "sha256": key24["sha256"], "version": key24["version"],
                           "read_for": "the gates G-A to G-D, the answers' groups (Rule 8) and S470's reader"},
              "inputs": inputs_block, "selection": info,
              "gate": {"G-A": g, **gd, "G-D": held}, "counts": c}
    write(outdir, rows, header)
    print(f"rows {c['rows']}: scored {c['scored']}, not applicable {c['not_applicable']}; answer-concept pairs by "
          f"status {c['d181']['pairs_by_status']}, of which the concept loses a word to the question "
          f"{c['d181']['pairs_with_a_removed_word']}")
    print(f"wrote {rel(outdir / 'concept_recall.jsonl')} and {rel(outdir / 'header.json')} (D181)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
