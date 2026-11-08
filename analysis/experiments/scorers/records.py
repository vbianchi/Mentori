"""One reader of the answers a run stores, for every scorer (F5, F39, F55 of the audit of 16 October).

    from experiments.scorers import records as R
    for x in R.read_run(Path("findings/runs/exp_01__single_pass__exp_v4_s20_n0")):
        x["answer_key"], x["question_id"], x["draw"], x["config"], x["answer"], x["status"], x["passages"]

    uv run python experiments/scorers/records.py summary <run>            # counts per status, group and passage kind
    uv run python experiments/scorers/records.py rule8 <scorer output>...  # LIST.md Rule 8's check; exit 1 on a number

WHAT A RUN IS. <run> is a run's sink (findings/runs/<run_id>/) or a results file that names each answer's run_id:
  exp_01                   <sink>/answers.jsonl, one line per attempt; the last line of an answer_key is its answer,
                           and a key stored again after a line without an error is refused (exp_01 stored_answers)
  exp_03                   <sink>/answers.json {"results": [...]}
  exp_02                   <sink>/answers.jsonl, one line per answer (since D80 V16 the sink is exp_02's record;
                           read as exp_01's)
  exp_06                   its results file (results), each row with run_id; the run's sink is
                           findings/runs/<run_id>/ (runs_root)
  G6 (experiments/rlm_ref) <sink>/answers.jsonl, one line per answer, passages {"whole_corpus": true, ...}
An answer_key twice (after exp_01's last-line rule) is refused, never merged.

WHAT EACH ANSWER GIVES. answer_key, run_id, config (the answer key's part before the question id; G6: its arm, cap<n>),
question_id, draw, question (the record's, else the D5 key's), answer, status (ok; error: the record stores an error;
no_answer: no error and an empty answer), error, record_status (G6's own status), group (Rule 8, below), passages and
passages_kind:
  ids          the record lists the passage ids its generator saw (the generation prompt's passages; an RLM's
               passages_seen; naive RAG's ids), resolved to text through the index the run recorded at its start
               (experiments/runner/index_identity.py, <sink>/index_identity.jsonl): each passage {"id", "source"
               (file_name), "chunk_idx" (chunk_index), "text"}. A run that recorded no index identity, a collection
               whose content hash differs, or an id the collection lacks is refused: no id is matched by guess.
  whole_corpus G6: the 20 papers of the context file the record names, each {"id": file name, "source": file name,
               "chunk_idx": None, "text": the paper as the RLM read it}, after the file's sha256 and the context's
               canonical sha256 (build_context.py context_sha256) are checked against the record. The text is whole:
               about 1.1 million characters, above the lock's num_ctx, so a scorer that sends it fails visibly
               (LOCK.toml [text]: nothing is cut).
  none         the generator saw no passage (exp_03 raw_gemini, whose dispatcher sets an empty passage list)
  not_recorded the record lists no passage ids (an answer that failed before its prompt; exp_03's orchestrator
               configs, whose passages sit inside each step's record)

RULE 8 (LIST.md:326-340). The group comes from the D5 key's answer type as the runner pins it (experiment.py _key()):
extractive and synthesis are answerable, refutation is false_premise, not_answerable is not_answerable. RAGAS,
RAGChecker and the judge with passages (variant b) apply to answerable and false_premise only (APPLIES); on the 39 they
store null with the reason "not applicable" (NOT_APPLICABLE), never a number. rule8_violations() is the check LIST.md
promises: a row of a not-answerable question that holds a number in one of those scorers' cells fails it.

RESUME (F55). resume() is how a scorer reading runs resumes: by (run_id, config, question_id, draw), refusing an
output that holds a row made under another lock_sha256, a row of another kind (no run_id: an --arm row), or a row of
the same answer whose item_sha256 differs (another answer, passage set or reference).

Standard library only (runs in the scorers' own environments; ROOT goes on sys.path for experiments.runner).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.runner import experiment as ex  # noqa: E402
from experiments.runner import index_identity as ii  # noqa: E402

NOT_APPLICABLE = "not applicable"                       # LIST.md:337, the reason stored with the null
GROUP_OF_TYPE = {"extractive": "answerable", "synthesis": "answerable", "refutation": "false_premise",
                 "not_answerable": "not_answerable"}    # LIST.md Rule 8 table, by the key's answer_type
APPLIES = {"ragas": ("answerable", "false_premise"), "ragchecker": ("answerable", "false_premise"),
           "judge_passages_b": ("answerable", "false_premise")}
KINDS = ("ids", "whole_corpus", "none", "not_recorded")
ANSWERS_JSONL, ANSWERS_JSON = "answers.jsonl", "answers.json"


class RecordsError(Exception):
    pass


# ---------------------------------------------------------------- Rule 8

@lru_cache(maxsize=1)
def key_questions() -> dict:
    """question id -> the D5 key's question (experiment.py _key(): the 244, both key files sha256-pinned)."""
    return {q["id"]: q for q in ex._key()}


def group_of(qid: str) -> str:
    """Rule 8's group of a question, from the D5 key's answer type; refused for a question outside the key or an
    answer type the rule does not name, or one whose answerable flag disagrees with its group."""
    q = key_questions().get(qid)
    if q is None:
        raise RecordsError(f"{qid} is not in the D5 key ({ex.KEY_D5.name}); Rule 8 cannot place it")
    g = GROUP_OF_TYPE.get(q["answer_type"])
    if g is None or (g != "not_answerable") != q["answerable"]:
        raise RecordsError(f"{qid}: answer_type {q['answer_type']!r}, answerable {q['answerable']!r}: not a Rule 8 group")
    return g


def applies(scorer: str, qid: str) -> bool:
    return group_of(qid) in APPLIES[scorer]


def _numbers(v) -> list:
    if isinstance(v, bool) or v is None:
        return []
    if isinstance(v, (int, float)):
        return [v]
    if isinstance(v, dict):
        return [n for x in v.values() for n in _numbers(x)]
    if isinstance(v, (list, tuple)):
        return [n for x in v for n in _numbers(x)]
    return []


def rule8_cells(row: dict) -> tuple[str, dict]:
    """(scorer, {cell: value}) of one scorer output row: the cells Rule 8 empties on a not-answerable question.
    judge_passages rows (a and b): variant b's scores and faithfulness_b; RAGChecker rows: metrics and
    metrics_as_computed; RAGAS rows (scores): every score."""
    if "a" in row and "b" in row:
        return "judge_passages_b", {"b.scores": (row.get("b") or {}).get("scores"), "faithfulness_b": row.get("faithfulness_b")}
    if "metrics" in row:
        return "ragchecker", {"metrics": row.get("metrics"), "metrics_as_computed": row.get("metrics_as_computed")}
    if "scores" in row:
        return "ragas", {"scores": row.get("scores")}
    raise RecordsError(f"not a judge_passages, RAGChecker or RAGAS row: keys {sorted(row)[:8]}")


def rule8_violations(rows: list[dict]) -> list[dict]:
    """Every row of a not-answerable question that holds a number in a cell Rule 8 empties (LIST.md:337), and every
    row whose question Rule 8 cannot place."""
    bad = []
    for n, row in enumerate(rows, 1):
        try:
            g = group_of(row["question_id"])
        except (RecordsError, KeyError) as e:
            bad.append({"row": n, "question_id": row.get("question_id"), "why": str(e)})
            continue
        scorer, cells = rule8_cells(row)
        if g in APPLIES[scorer]:
            continue
        held = {k: v for k, v in cells.items() if _numbers(v)}
        if held:
            bad.append({"row": n, "question_id": row["question_id"], "config": row.get("config"),
                        "scorer": scorer, "why": f"{g}: a number where Rule 8 stores null ('{NOT_APPLICABLE}')",
                        "cells": held})
    return bad


# ---------------------------------------------------------------- reading a run

def _status(answer, error) -> str:
    if error:
        return "error"
    return "ok" if (answer or "").strip() else "no_answer"


def _config_of(answer_key: str, qid: str) -> str:
    """The config part of an answer key ([index|]config|question_id|d<draw>, experiment.answer_key)."""
    parts = answer_key.split(ex.KEY_SEP)
    if len(parts) < 3 or parts[-2] != qid or not parts[-1].startswith("d"):
        raise RecordsError(f"answer key {answer_key!r} is not [index|]config|{qid}|d<draw>")
    return parts[-3]


def _lines(path: Path) -> list[tuple[int, dict]]:
    out = []
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if raw.strip():
            try:
                out.append((n, json.loads(raw)))
            except ValueError as e:
                raise RecordsError(f"{path}:{n} is not JSON ({e})") from None
    return out


def _answer(rec: dict, *, run_id, answer, error, passages, source, config=None, record_status=None) -> dict:
    qid, key = rec["question_id"], rec["answer_key"]
    cfg = _config_of(key, qid)
    if config is not None and config != cfg:
        raise RecordsError(f"{source}: config {config!r} is not its answer key's {key!r}")
    draw = rec["draw"]
    if f"d{draw}" != key.split(ex.KEY_SEP)[-1]:
        raise RecordsError(f"{source}: draw {draw!r} is not its answer key's {key!r}")
    kq = key_questions().get(qid) or {}
    return {"answer_key": key, "run_id": run_id, "config": cfg, "question_id": qid, "draw": draw,
            "question": rec.get("question") or kq.get("question"), "answer": answer or "",
            "status": _status(answer, error), "error": error, "record_status": record_status,
            "group": group_of(qid), "passages": passages, "source": source}


def _ids(v) -> list | None:
    if v is None:
        return None
    if not isinstance(v, list) or not all(isinstance(i, str) for i in v):
        raise RecordsError(f"passages {str(v)[:80]!r}: not a list of ids")
    return v


class _Resolver:
    """Turns a run's passage ids into text through the index identity its sink recorded (index_identity.held)."""

    def __init__(self, store: Path | None, resolve: bool, immutable: bool):
        self.store, self.resolve, self.immutable = store, resolve, immutable
        self.maps: dict = {}
        self.where: dict = {}

    def identity(self, sink: Path) -> dict | None:
        try:
            return ii.held(sink)
        except ii.IndexIdentityError as e:
            raise RecordsError(str(e)) from None

    def passages(self, ids: list | None, sink: Path, run_id: str, kind_if_none: str = "not_recorded"):
        if ids is None:
            return None, kind_if_none, None
        ident = self.identity(sink)
        if not ids:                                     # the generator saw no passage: nothing to resolve
            return [], "none", ident
        if not self.resolve:
            return [{"id": i, "source": None, "chunk_idx": None, "text": None} for i in ids], "ids", ident
        if ident is None:
            raise RecordsError(f"run {run_id} recorded no index identity ({sink / ii.FILE}); its passage ids cannot "
                               f"be turned into the text its generator saw (F5)")
        h = ident["id_text_sha256"]
        if h not in self.maps:
            try:
                self.maps[h], self.where[h] = ii.resolve(ident, self.store, self.immutable)
            except ii.IndexIdentityError as e:
                raise RecordsError(f"run {run_id}: {e}") from None
        m = self.maps[h]
        missing = [i for i in ids if i not in m]
        if missing:
            raise RecordsError(f"run {run_id}: {len(missing)} passage ids not in index {ident['index_name']} "
                               f"(first {missing[0]!r})")
        return [{"id": i, "source": m[i]["file_name"], "chunk_idx": m[i]["chunk_index"], "text": m[i]["text"]}
                for i in ids], "ids", ident


def _exp01(sink: Path, rv: _Resolver) -> list[dict]:
    last: dict = {}
    for n, rec in _lines(sink / ANSWERS_JSONL):
        key = rec["answer_key"]
        if key in last and not last[key][1]["generation"].get("error"):
            raise RecordsError(f"{sink / ANSWERS_JSONL}:{n} stores {key} again after its answer at line "
                               f"{last[key][0]}")
        last[key] = (n, rec)
    out = []
    for n, rec in last.values():
        gen = rec.get("generation") or {}
        run_id = rec.get("run_id") or sink.name
        p, kind, ident = rv.passages(_ids(gen.get("passages")), sink, run_id)
        x = _answer(rec, run_id=run_id, answer=gen.get("answer"), error=gen.get("error"), passages=p,
                    source=f"{sink / ANSWERS_JSONL}:{n}", config=rec.get("config"))
        _check_index(x, ident, rec.get("index_name"))
        out.append({**x, "passages_kind": kind, "index": _short(ident)})
    return out


@lru_cache(maxsize=4)
def _corpus(file: str, file_sha256: str, context_sha256: str) -> tuple:
    path = ROOT / file
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != file_sha256:
        raise RecordsError(f"{file}: sha256 is not the {file_sha256[:12]} the run's records name")
    doc = json.loads(raw)
    ctx = doc["context"]
    canon = hashlib.sha256(json.dumps(ctx, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
    if canon != context_sha256 or doc.get("context_sha256") != context_sha256:
        raise RecordsError(f"{file}: its context's sha256 {canon[:12]} is not the records' {context_sha256[:12]}")
    names = [p["file_name"] for p in doc["papers"]]
    if len(names) != len(ctx):
        raise RecordsError(f"{file}: {len(names)} papers named, {len(ctx)} texts")
    return tuple(names), tuple({"id": f, "source": f, "chunk_idx": None, "text": t} for f, t in zip(names, ctx))


def _rlm_ref(sink: Path, rv: _Resolver) -> list[dict]:
    out, seen = [], {}
    for n, rec in _lines(sink / ANSWERS_JSONL):
        key = rec["answer_key"]
        if key in seen:
            raise RecordsError(f"{sink / ANSWERS_JSONL}:{n} stores {key} again (line {seen[key]})")
        seen[key] = n
        pas, c = rec.get("passages") or {}, rec.get("context") or {}
        if not pas.get("whole_corpus") or pas.get("context_sha256") != c.get("context_sha256"):
            raise RecordsError(f"{sink / ANSWERS_JSONL}:{n}: passages {str(pas)[:80]} name no whole-corpus context")
        names, papers = _corpus(c["file"], c["file_sha256"], c["context_sha256"])
        if list(pas.get("papers") or []) != list(names):
            raise RecordsError(f"{sink / ANSWERS_JSONL}:{n}: the record's papers are not the context file's")
        error = rec.get("error") or (None if rec.get("status") == "ok"
                                     else f"status {rec.get('status')} ({rec.get('stop_reason')})")
        x = _answer(rec, run_id=rec.get("run_id") or sink.name, answer=rec.get("answer"), error=error,
                    passages=list(papers), source=f"{sink / ANSWERS_JSONL}:{n}", config=rec.get("arm"),
                    record_status=rec.get("status"))
        out.append({**x, "passages_kind": "whole_corpus",
                    "index": {"whole_corpus_context": c["file"], "context_sha256": c["context_sha256"]}})
    return out


def _exp03(sink: Path, rv: _Resolver) -> list[dict]:
    data = json.loads((sink / ANSWERS_JSON).read_text(encoding="utf-8"))
    out = []
    for n, rec in enumerate(data.get("results") or [], 1):
        gen = rec.get("generation") or {}
        run_id = rec.get("run_id") or sink.name
        cfg = rec.get("config")
        if "passages" in gen:
            ids, none_kind = _ids(gen["passages"]), "not_recorded"
        elif cfg == "raw_gemini":                       # exp_03 _raw_gemini: rc.set_passages([]), no retrieval
            ids, none_kind = [], "none"
        else:
            ids, none_kind = None, "not_recorded"
        p, kind, ident = rv.passages(ids, sink, run_id, none_kind)
        x = _answer(rec, run_id=run_id, answer=gen.get("answer", rec.get("generated_answer")),
                    error=rec.get("error", gen.get("error")), passages=p, source=f"{sink / ANSWERS_JSON} results[{n}]",
                    config=cfg)
        _check_index(x, ident, rec.get("index_name"))
        out.append({**x, "passages_kind": kind, "index": _short(ident)})
    return out


def _results_file(path: Path, rv: _Resolver, runs_root: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("per_question_results") if "per_question_results" in data else data.get("results")
    if not isinstance(rows, list):
        raise RecordsError(f"{path}: neither per_question_results nor results")
    out = []
    for n, rec in enumerate(rows, 1):
        run_id = rec.get("run_id")
        if not run_id or "answer_key" not in rec:
            raise RecordsError(f"{path} row {n}: no run_id or answer_key; not a run's results file")
        sink = Path(runs_root) / run_id
        if "generation" in rec:                          # exp_02: the strategy's GenerationResult
            gen = rec["generation"] or {}
            answer, error, ids = gen.get("answer"), gen.get("error"), _ids(gen.get("passages"))
        elif "rlm" in rec:                               # exp_06: the RLM's metadata, passages_seen
            answer, error = rec.get("answer"), rec.get("error")
            ids = _ids((rec.get("rlm") or {}).get("passages_seen")) if rec.get("rlm") else None
        else:
            raise RecordsError(f"{path} row {n}: neither generation nor rlm")
        p, kind, ident = rv.passages(ids, sink, run_id)
        x = _answer(rec, run_id=run_id, answer=answer, error=error, passages=p, source=f"{path} row {n}",
                    config=rec.get("config"))
        _check_index(x, ident, rec.get("index_name") or data.get("index"))
        out.append({**x, "passages_kind": kind, "index": _short(ident)})
    return out


def _check_index(x: dict, ident: dict | None, index_name: str | None) -> None:
    if ident is not None and index_name is not None and ident["index_name"] != index_name:
        raise RecordsError(f"{x['source']}: index {index_name!r}, and run {x['run_id']} recorded "
                           f"{ident['index_name']!r}")


def _short(ident: dict | None) -> dict | None:
    return None if ident is None else {k: ident.get(k) for k in ("index_name", "collection", "n_chunks",
                                                                 "id_text_sha256", "chunk_manifest_sha256")}


def read_run(path: Path, *, store: Path | None = None, resolve: bool = True, immutable: bool = False,
             runs_root: Path = ex.RUNS) -> list[dict]:
    """Every answer of a run (the module docstring), in the order stored. store: the Chroma directory to resolve ids
    against (default: the one the run recorded); resolve False leaves passage texts None (counting only)."""
    path = Path(path)
    rv = _Resolver(store, resolve, immutable)
    if path.is_dir():
        if (path / ANSWERS_JSONL).exists():
            first = next((rec for _, rec in _lines(path / ANSWERS_JSONL)), None)
            if first is None:
                out = []
            elif "generation" in first:
                out = _exp01(path, rv)
            elif isinstance(first.get("passages"), dict):
                out = _rlm_ref(path, rv)
            else:
                raise RecordsError(f"{path / ANSWERS_JSONL}: neither exp_01's nor the authors' RLM's records")
        elif (path / ANSWERS_JSON).exists():
            out = _exp03(path, rv)
        else:
            raise RecordsError(f"{path} holds no {ANSWERS_JSONL} or {ANSWERS_JSON}")
    elif path.is_file():
        out = _results_file(path, rv, runs_root)
    else:
        raise RecordsError(f"{path} does not exist")
    idents = [(x["run_id"], x["config"], x["question_id"], x["draw"]) for x in out]
    if len(set(idents)) != len(idents):
        raise RecordsError(f"{path}: two answers with the same (run_id, config, question_id, draw)")
    return out


def ident(x: dict) -> tuple:
    """What a scorer reading runs resumes on (F55)."""
    return x["run_id"], x["config"], x["question_id"], x["draw"]


def item_sha256(x: dict, reference: str | None = None) -> str:
    """sha256 of what enters a scorer's calls for one answer: question, reference, answer, status, passages."""
    pas = [[p["id"], p["source"], p["chunk_idx"], hashlib.sha256((p["text"] or "").encode("utf-8")).hexdigest()]
           for p in x["passages"] or []]
    return hashlib.sha256(json.dumps([x["question"], reference, x["answer"], x["status"], x["passages_kind"], pas],
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


def resume(rows: list[dict], lock_sha256: str, done: set, items: dict) -> set:
    """The idents (ident()) of rows already done, from a scorer output's rows (the latest row of an answer counts).
    Refused: a row without run_id (another mode's output), a row under another lock_sha256, a row of one of this
    run's answers whose item_sha256 differs. items: ident -> item_sha256 of the answers being scored."""
    latest = {}
    for n, d in enumerate(rows, 1):
        if not d.get("run_id"):
            raise RecordsError(f"row {n} has no run_id (an --arm output); a run's scores go to their own --out")
        if d.get("lock_sha256") != lock_sha256:
            raise RecordsError(f"row {n} ({d.get('run_id')}, {d.get('question_id')}) was scored under lock "
                               f"{str(d.get('lock_sha256'))[:12]}, this run is under {lock_sha256[:12]}; use a new --out")
        k = (d["run_id"], d["config"], d["question_id"], d["draw"])
        if k in items and d.get("item_sha256") != items[k]:
            raise RecordsError(f"row {n} scored {k} on another answer, passage set or reference "
                               f"(item {str(d.get('item_sha256'))[:12]}, now {items[k][:12]}); use a new --out")
        latest[k] = d.get("status")
    return {k for k, s in latest.items() if s in done}


# ---------------------------------------------------------------- command line

def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("summary", help="counts of one run's answers (reads the index only with --resolve)")
    s.add_argument("run", type=Path)
    s.add_argument("--resolve", action="store_true")
    s.add_argument("--store", type=Path)
    r = sub.add_parser("rule8", help="LIST.md Rule 8's check over scorer outputs (jsonl); exit 1 on a violation")
    r.add_argument("outputs", nargs="+", type=Path)
    a = ap.parse_args()
    if a.cmd == "summary":
        from collections import Counter
        xs = read_run(a.run, store=a.store, resolve=a.resolve)
        print(json.dumps({"answers": len(xs), "status": Counter(x["status"] for x in xs),
                          "group": Counter(x["group"] for x in xs),
                          "passages_kind": Counter(x["passages_kind"] for x in xs),
                          "runs": sorted({x["run_id"] for x in xs})}, indent=1))
        return 0
    failed = 0
    for f in a.outputs:
        rows = [d for _, d in _lines(f)]
        bad = rule8_violations(rows)
        failed += bool(bad)
        print(f"{f}: {len(rows)} rows, {len(bad)} violate Rule 8" + "".join(f"\n  {json.dumps(b)}" for b in bad[:20]))
    print("RULE 8 CHECK " + ("FAILED" if failed else "PASSED"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
