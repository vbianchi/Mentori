#!/usr/bin/env python3
"""The key-based metrics and MiniCheck on the I2 answers, against a curated key, through the paper's own scorer code
(I2, D160 (14) Q-I2d O-a: "the judge, key-based metrics, MiniCheck"; i2_plan.md A5).

    uv run python experiments/reuse_demo/i2_signals.py concepts            # no model: concept recall, D12's matcher
    uv run python experiments/reuse_demo/i2_signals.py numbers             # no model: number overlap
    uv run python experiments/reuse_demo/i2_signals.py key --device cpu    # MiniCheck against the key (loads the model)
    uv run python experiments/reuse_demo/i2_signals.py papers --device cpu # MiniCheck against the papers (loads it)
    (each takes --runs <sink> ... (default: every I2 sink), --out <dir> (default findings/recompute/I2_runs/signals),
     --key/--key-sha256 (default the plant key, pinned), --gate-only; papers also --text-dir)

THE ANSWERS. Each run's answers as experiments/scorers/records.py reads them (the last line of each answer key; status
ok, error or no_answer), with records' Rule 8 groups taken from the curated key (plant_key.py; refutation is
false_premise, not_answerable is not_answerable). The record line each answer came from is read again for
generation.stop_reason and the RLM's turn_limit_note flag. Not-answerable questions get every signal null with the
reason "not applicable" (Rule 8), as in L1 and L3.

THE KEY, in the form the paper's scorers read (S381's v1 form, built here and written beside the outputs as
key_as_v1.json): expected_answer = the short answer, plus a blank line and the synthesis statement where there is one
(S373.key_of, the same rule as S381); expected_concepts = the key-concept phrases in order; answerable =
question_answerable; source_files = the papers its evidence names, as file names, in name order.

THE STAGES. Each is an earlier script's function, called as that script calls it, after that script's own gate
(README.md:75-79): the gate runs first and nothing is written when it fails.
  concepts  S471.score (scripts/S471_l3_concept_recall.py, plan row L3): concept recall on D12's loose matcher
            (scripts/concept_match_loose.py), with the exact substring value beside it, the turn-limit note removed
            where the record flags it; provisional until P2 picks the matcher (D114 Q37), then run again. Gate:
            S471.gate on the paper's D5 key (the matchers' rule cases, then S432's 107 answers reproduced).
  numbers   number overlap as S470's overlap stage computes it: the deposited score_all's number_overlap (lifted by
            scripts/S382_exp04_objective_v22.py deposited_scorer, run through S382.score with the key's answerable
            flag), and the deposited compute_number_overlap on the citation-stripped answer
            (S141_runner.scorers.strip_citations, S141's det_record). Gate: the two number gates of S470's
            gate_overlap, run through this stage's own functions: S382's own gate (the deposit's 828 rows), then
            number_overlap on its 528 answerable v1 rows equal to the deposit; and the stripped number overlap equal
            on every row of S141's deterministic artefact that carries one.
  key       MiniCheck-Flan-T5-Large precision, recall and F1 of each answer against the key's expected answer: S470's
            key_signals after S470's gate_key (S384's G2 and S470's own key gate), on --device.
  papers    MiniCheck precision of each answer's claims against its question's papers, whole: S470's papers_signals
            and S19.check after S470's papers gate (gate_papers_stage, S19's first two full-doc rows on the paper's
            own documents). The plant papers are the text files the key's quotes were checked against
            (--text-dir, default experiments/reuse_demo/text/<file>.pages.json), each paper's pages joined with nothing between (as S18
            joined fitz's pages), the papers of a question joined by a blank line (S470.join_docs).
Not computed: ROUGE-L, METEOR, BERTScore and the bge-m3 similarity (S470's overlap stage computes them for Figure 5;
the reuse claim names "curated ground truth and a NLI model", i2_plan.md Q-I2d).

OUTPUTS, under --out: <stage>.jsonl (one row per answer, in the runs' order, rows as S470 and S471 write them; no
time stamps), <stage>_header.json (the key, each run's answers.jsonl sha256, the code sha256s, the gate's result, the
counts), key_as_v1.json. concepts and numbers are written whole at the end. key and papers append one row per answer
as it is scored and resume after a stop: a row already written under the same header identity (key, answers, code,
device) is not scored again; another identity is refused.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (str(ROOT / "scripts"), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)
from experiments.reuse_demo import i2_memory, plant_key  # noqa: E402

I2_RUNS = ROOT / "findings" / "recompute" / "I2_runs"
SINKS = I2_RUNS / "sinks"
OUT = I2_RUNS / "signals"
TEXT = HERE / "text"
APPLIES = ("answerable", "false_premise")
NA = "not applicable"
STAGES = ("concepts", "numbers", "key", "papers")
NUMBER_SIGNALS = ("number_overlap", "number_overlap_citation_stripped")
CODE = ("experiments/reuse_demo/i2_signals.py", "experiments/reuse_demo/plant_key.py",
        "experiments/scorers/records.py", "scripts/S470_l1_signals.py", "scripts/S471_l3_concept_recall.py",
        "scripts/concept_match_loose.py", "scripts/turn_limit_note.py", "scripts/S382_exp04_objective_v22.py",
        "scripts/S384_exp04_minicheck_key_v22.py", "scripts/S19_minicheck_regrounded.py",
        "scripts/S141_runner/scorers.py", "scripts/S373_rejudge_v2.py")


class Refused(SystemExit):
    def __init__(self, msg: str):
        super().__init__(f"REFUSED: {msg}")


def sha_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def code_shas() -> dict:
    return {f: sha_file(ROOT / f) for f in CODE}


# ---------------------------------------------------------------- the key and the answers

def key_as_v1(key: plant_key.Key) -> dict:
    """The key in S381's v1 form (module docstring, THE KEY)."""
    import S373_rejudge_v2 as S373
    v2 = key.v2()
    qs = []
    for r in key.records:
        ea, ec = S373.key_of(r["id"], v2)
        files = sorted({e["paper"] + ".pdf" for e in r.get("evidence") or [] if e.get("paper")})
        qs.append({"id": r["id"], "question": r["question"], "category": r["category"],
                   "answerable": r["question_answerable"], "answer_type": r["answer_type"], "expected_answer": ea,
                   "expected_concepts": ec, "source_files": files, "min_core": r.get("min_core")})
    return {"version": f"{key.data.get('version')} as v1", "source": {"path": str(key.path), "sha256": key.sha256},
            "questions": qs}


def install_key(key: plant_key.Key):
    """records.py's Rule 8 groups and question texts from the curated key, inside this process only."""
    from experiments.scorers import records as R
    kq = key.key_questions()
    R.key_questions = lambda: kq
    return R


def default_runs() -> list[Path]:
    return sorted(p for p in SINKS.glob("exp_01__*") if (p / "answers.jsonl").exists() and not p.name.endswith(".smoke"))


def read_answers(sinks: list[Path], key: plant_key.Key) -> list[dict]:
    """Every answer of the runs (module docstring, THE ANSWERS), in S470's answer shape plus turn_limit_note."""
    import S470_l1_signals as S470
    R = install_key(key)
    out = []
    for s in sinks:
        lines = (Path(s) / "answers.jsonl").read_text(encoding="utf-8").splitlines()
        try:
            recs = R.read_run(Path(s), resolve=False)
        except R.RecordsError as e:
            raise Refused(str(e)) from None
        for x in recs:
            n = int(x["source"].rsplit(":", 1)[1])
            rec = json.loads(lines[n - 1])
            gen = rec.get("generation") or {}
            if rec.get("answer_key") != x["answer_key"] or (gen.get("answer") or "") != x["answer"]:
                raise Refused(f"{x['source']} is not the record records.py read for {x['answer_key']}")
            a = {k: x[k] for k in ("answer_key", "run_id", "config", "question_id", "draw", "group", "status", "error",
                                   "answer", "source")}
            a["stop_reason"] = gen.get("stop_reason")
            a["answer_sha256"] = S470.sha256_text(a["answer"])
            a["turn_limit_note"] = ((gen.get("rlm") or {}).get("metadata") or {}).get("turn_limit_note")
            out.append(a)
    keys = [a["answer_key"] + "|" + a["run_id"] for a in out]
    if len(set(keys)) != len(keys):
        raise Refused("two answers with the same run and answer key")
    return out


def identity(stage: str, key: plant_key.Key, sinks: list[Path], device: str | None) -> dict:
    return {"stage": stage, "key": key.describe(), "answers": {str(s): sha_file(Path(s) / "answers.jsonl") for s in sinks},
            "code": code_shas(), "device": device}


# ---------------------------------------------------------------- concepts

def concept_rows(answers: list[dict], kv1: dict) -> list[dict]:
    import S471_l3_concept_recall as S471
    key = {"questions": {q["id"]: q for q in kv1["questions"]}}
    return S471.rows_for(answers, key, {a["answer_key"]: a["turn_limit_note"] for a in answers})


def concepts_gate() -> dict:
    import S470_l1_signals as S470
    import S471_l3_concept_recall as S471
    try:
        return S471.gate(S470.the_key())
    except S471.GateFail as e:
        raise Refused(f"the concept recall gate (S471.gate) did not reproduce: {e}") from None


# ---------------------------------------------------------------- numbers

class NumberFns:
    """S470 OverlapFns' number calls (number_overlap, number_overlap_stripped, key_numbers) without its encoders."""

    def __init__(self, key_path: Path):
        import S382_exp04_objective_v22 as S382
        import S470_l1_signals as S470
        from S141_runner import scorers as sc
        self.S382, self.S470, self.sc, self.key_path = S382, S470, sc, key_path
        self.ns, self.sources, self.sink = S382.deposited_scorer()
        self.flags = S470.key_flags(key_path)

    def number_overlap(self, batch, key_path: Path | None = None):
        kp, flags = (self.key_path, self.flags) if key_path is None else (key_path, self.S470.key_flags(key_path))
        rows = [{"question_id": a["question_id"], "config": a["answer_key"], "answerable": flags[a["question_id"]],
                 "generation": {"answer": a["answer"], "error": a["error"]}} for a in batch]
        scored, skipped = self.S382.score(self.ns, rows, kp, None, self.sink)
        by = {r["config"]: r["objective_metrics"].get("number_overlap") for r in scored}
        if skipped or len(by) != len(batch) or any(v is None for v in by.values()):
            raise Refused(f"score_all skipped {skipped} of {len(batch)} rows, or scored one as unanswerable")
        return [by[a["answer_key"]] for a in batch]

    def number_overlap_stripped(self, expected, answer):
        return self.ns["compute_number_overlap"](expected, self.sc.strip_citations(answer))

    def key_numbers(self, expected):
        return len(self.ns["extract_numbers"](expected))


def numbers_gate(fns: NumberFns) -> list[dict]:
    """S470 gate_overlap's two number gates, through fns (module docstring, numbers)."""
    import S141_scorers_4_2b as S141
    from machine import require
    S382, out = fns.S382, []
    require(S382.GEN, S382.DET, S382.KEY_V1, S141.V1_KEY)
    gen = json.loads(S382.GEN.read_text())["per_question_results"]
    det = json.loads(S382.DET.read_text())
    g382 = S382.gate(fns.ns, gen, det, fns.sink)
    dep = {(r["question_id"], r["config"]): r for r in det["per_result"] if r["answerable"]}
    gen_by = {(r["question_id"], r["config"]): r for r in gen}
    batch = [{"question_id": q, "answer_key": f"{q}|{c}",
              "answer": ((gen_by[(q, c)].get("generation") or {}).get("answer") or ""),
              "error": (gen_by[(q, c)].get("generation") or {}).get("error")} for q, c in sorted(dep)]
    mine = fns.number_overlap(batch, key_path=S382.KEY_V1)
    n_eq = sum(float(v) == float(dep[(a["question_id"], a["answer_key"].split("|", 1)[1])]["objective_metrics"]
                                 ["number_overlap"]) for a, v in zip(batch, mine))
    if n_eq != len(batch) or len(batch) != 528:
        raise Refused(f"numbers gate: number_overlap equal to the deposit on {n_eq} of {len(batch)} v1 rows (want 528)")
    out.append({"gate": "S382 gate, then number_overlap on its 528 answerable v1 rows",
                "evidence": {**{k: v for k, v in g382.items() if not isinstance(v, (list, dict))}, "equal": n_eq}})
    campaign = {(arm.name, row.get("config"), row.get("question_id")): row
                for arm in S141.arms() for row in S141.rows_of(arm)}
    key1 = S141.Key(S141.V1_KEY)
    n = n_eq = 0
    bad = []
    for f in sorted(Path(S141.V1_SIGNALS).glob("*.deterministic.jsonl")):
        for line in f.read_text().splitlines():
            r = json.loads(line)
            if "number_overlap" not in r:
                continue
            row = campaign.get((r["arm"], r["config"], r["question_id"]))
            if row is None or r["question_id"] not in key1.questions:
                bad.append((r["arm"], r["config"], r["question_id"]))
                continue
            got = fns.number_overlap_stripped(key1.questions[r["question_id"]].get("expected_answer", ""),
                                              S141.answer_of(row))
            n += 1
            n_eq += got == r["number_overlap"]
            if got != r["number_overlap"]:
                bad.append((r["arm"], r["config"], r["question_id"], r["number_overlap"], got))
    if bad or not n:
        raise Refused(f"numbers gate: stripped number overlap equal on {n_eq} of {n} S141 rows; first {bad[:3]}")
    out.append({"gate": "S141 deterministic number overlap, citation-stripped", "rows": n, "equal": n_eq})
    return out


def number_rows(answers: list[dict], kv1: dict, fns: NumberFns) -> list[dict]:
    import S470_l1_signals as S470
    exp = {q["id"]: q["expected_answer"] for q in kv1["questions"]}
    todo = [a for a in answers if a["group"] in APPLIES]
    numov = dict(zip((a["answer_key"] + "|" + a["run_id"] for a in todo), fns.number_overlap(todo))) if todo else {}
    rows = []
    for a in answers:
        row = S470.base_row(a, "numbers")
        if a["group"] not in APPLIES:
            row.update(signals={s: None for s in NUMBER_SIGNALS}, null_reasons={s: NA for s in NUMBER_SIGNALS},
                       detail={})
        else:
            e = exp[a["question_id"]]
            detail = {"key_numbers": fns.key_numbers(e)}
            if not a["answer"].strip() or a["error"]:
                detail["number_overlap_branch"] = S470.ERROR_BRANCH
            row.update(signals={"number_overlap": float(numov[a["answer_key"] + "|" + a["run_id"]]),
                                "number_overlap_citation_stripped": float(fns.number_overlap_stripped(e, a["answer"]))},
                       null_reasons={}, detail=detail)
        rows.append(row)
    return rows


# ---------------------------------------------------------------- MiniCheck

def plant_docs(kv1: dict, answers: list[dict], text_dir: Path = TEXT) -> dict:
    """question -> {"files", "text", "sha256"}: each paper's pages joined with nothing between, the papers joined by
    S470.join_docs (module docstring, papers)."""
    import S470_l1_signals as S470
    qs = {q["id"]: q for q in kv1["questions"]}
    out = {}
    for qid in sorted({a["question_id"] for a in answers if a["group"] in APPLIES}):
        files = qs[qid]["source_files"]
        docs = {}
        for f in files:
            p = Path(text_dir) / f"{f}.pages.json"
            if not p.exists():
                raise Refused(f"{qid}: no page text {p} for its paper {f}")
            docs[f] = "".join(json.loads(p.read_text(encoding="utf-8")))
        if not files:
            raise Refused(f"{qid}: the key names no paper in its evidence")
        text = S470.join_docs(docs, files)
        out[qid] = {"files": files, "text": text, "sha256": sha_text(text)}
    return out


def gate_docs() -> dict:
    """The paper's own documents for the questions of S470's papers gate (S470.papers_docs on the D5 key)."""
    import S470_l1_signals as S470
    fake = [{"question_id": q, "group": "answerable"} for q, _ in S470.PAPERS_GATE_ROWS]
    return S470.papers_docs(S470.the_key(), fake)[0]


def done_rows(path: Path) -> dict:
    out = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                out[r["answer_key"] + "|" + r["run_id"]] = r
    return out


# ---------------------------------------------------------------- the stages

def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp{os.getpid()}")
    tmp.write_text(json.dumps(obj, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def write_rows(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp{os.getpid()}")
    tmp.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    tmp.replace(path)


def counts(rows: list[dict], signals) -> dict:
    import collections
    return {"rows": len(rows), "by_group": dict(collections.Counter(r["group"] for r in rows)),
            "by_config": dict(collections.Counter(r["config"] for r in rows)),
            "null": {s: sum((r.get("signals") or {}).get(s) is None for r in rows) for s in signals}}


def run(a) -> int:
    pin = a.key_sha256 or (plant_key.KEY_SHA256 if Path(a.key).resolve() == plant_key.KEY.resolve() else None)
    if pin is None:
        raise Refused("--key names another key: give its --key-sha256")
    try:
        key = plant_key.load(a.key, pin)
    except plant_key.KeyProblem as e:
        raise Refused(str(e)) from None
    sinks = [Path(s) for s in (a.runs or default_runs())]
    if not sinks:
        raise Refused(f"no run sinks given and none under {SINKS}")
    answers = read_answers(sinks, key)
    kv1 = key_as_v1(key)
    out = Path(a.out)
    ident = identity(a.stage, key, sinks, a.device if a.stage in ("key", "papers") else None)
    hdr_path = out / f"{a.stage}_header.json"
    rows_path = out / f"{a.stage}.jsonl"
    if a.stage in ("key", "papers") and hdr_path.exists():
        old = json.loads(hdr_path.read_text())
        if old.get("identity") != ident:
            raise Refused(f"{rows_path} was written under another key, answers, code or device; use a new --out")
    print(f"{a.stage}: {len(answers)} answers from {len(sinks)} runs; key {key.path.name} {key.sha256[:12]}", flush=True)
    header = {"_provenance": {"script": "experiments/reuse_demo/i2_signals.py " + a.stage, "argv": sys.argv[1:],
                              "at": time.strftime("%Y-%m-%dT%H:%M:%S"), "host": os.uname().nodename},
              "identity": ident, "provisional": a.stage == "concepts"}
    if a.stage == "concepts":
        gate = concepts_gate()
        print(f"concepts gate passed: {gate['reproduced']}", flush=True)
        if a.gate_only:
            return 0
        rows = concept_rows(answers, kv1)
        signals = ("concept_recall_loose", "concept_recall_exact")
        c = counts([{**r, "signals": {s: r[s] for s in signals}} for r in rows], signals)
    elif a.stage == "numbers":
        write_json(out / "key_as_v1.json", kv1)
        fns = NumberFns(out / "key_as_v1.json")
        gate = numbers_gate(fns)
        print("numbers gate passed: " + "; ".join(g["gate"] for g in gate), flush=True)
        if a.gate_only:
            return 0
        rows = number_rows(answers, kv1, fns)
        c = counts(rows, NUMBER_SIGNALS)
    else:
        import S470_l1_signals as S470
        low, r = i2_memory.under(a.min_free_gb)
        if low:
            raise Refused(f"free memory {r} GB is under {a.min_free_gb} GB; MiniCheck is not loaded")
        docs = plant_docs(kv1, answers, a.text_dir) if a.stage == "papers" else None
        if a.stage == "key":
            ns, scorer, info, gate = S470.gate_key(a.device)
        else:
            ns, scorer, info, gate = S470.gate_papers_stage(a.device, gate_docs())
        print(f"{a.stage} gate passed (MiniCheck loaded)", flush=True)
        if a.gate_only:
            return 0
        header["model"] = info
        done = done_rows(rows_path)
        if done and not hdr_path.exists():
            raise Refused(f"{rows_path} holds rows and no header: their identity is unknown; use a new --out")
        write_json(hdr_path, {**header, "gate": gate, "counts": None})   # the identity, before the first row
        exp = {q["id"]: q["expected_answer"] for q in kv1["questions"]}
        rows_path.parent.mkdir(parents=True, exist_ok=True)
        with open(rows_path, "a", encoding="utf-8") as fh:
            for x in answers:
                k = x["answer_key"] + "|" + x["run_id"]
                if k in done:
                    continue
                if a.stage == "key":
                    row = S470.key_signals(x, exp[x["question_id"]], ns, scorer)
                else:
                    import S19_minicheck_regrounded as S19
                    row = (S470.papers_signals(x, docs[x["question_id"]], ns["decompose_to_sentences"], S19.check,
                                               scorer) if x["group"] in APPLIES else S470.not_applicable(x, "papers"))
                fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
                fh.flush()
                done[k] = row
                print(f"  {x['answer_key']} {x['run_id']}: {row['signals']}", flush=True)
        rows = [done[x["answer_key"] + "|" + x["run_id"]] for x in answers]
        c = counts(rows, S470.SIGNALS[a.stage])
    header.update(gate=gate, counts=c)
    if a.stage in ("concepts", "numbers"):
        write_rows(rows_path, rows)
    write_json(hdr_path, header)
    print(f"{a.stage}: wrote {len(rows)} rows to {rows_path}; {json.dumps(c['null'])} null", flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="I2 key-based metrics and MiniCheck (module docstring).")
    ap.add_argument("stage", choices=STAGES)
    ap.add_argument("--runs", nargs="+", type=Path, help="run sinks (default: every I2 sink)")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--key", type=Path, default=plant_key.KEY)
    ap.add_argument("--key-sha256", default=None)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--min-free-gb", type=float, default=4.0, help="key and papers: MiniCheck needs about 3 GB "
                    "(UNVERIFIED); refused under this")
    ap.add_argument("--text-dir", type=Path, default=TEXT, help="papers: the page texts (<file>.pages.json); default "
                    "experiments/reuse_demo/text, the files the plant key's quotes were checked against")
    ap.add_argument("--gate-only", action="store_true")
    return ap.parse_args(argv)


def main(argv=None) -> int:
    return run(parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
