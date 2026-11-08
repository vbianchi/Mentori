#!/usr/bin/env python3
"""Offline checks of the scorers' run reader (experiments/scorers/records.py), the index identity
(experiments/runner/index_identity.py), Rule 8's check, and the --run paths of ragchecker_run.py and judge_passages.py
(audit of 16 October: F5, F39, F55). No model call, no server contact; every fixture is a temporary directory, and the
real G6 sink findings/runs/b4_rlm_ref__cap5__all135 is read only.

    uv run python experiments/scorers/check_records.py
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from experiments.runner import experiment as ex  # noqa: E402
from experiments.runner import index_identity as ii  # noqa: E402
from experiments.scorers import records as R  # noqa: E402

G6 = ROOT / "findings" / "runs" / "b4_rlm_ref__cap5__all135"
INDEX = "exp_v4_s20_n0"
RESULTS = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail else ""))


def raises(fn, exc=Exception) -> Exception | None:
    try:
        fn()
    except exc as e:                                       # noqa: BLE001
        return e
    return None


def make_store(path: Path, collections: dict) -> None:
    """A chroma.sqlite3 with the tables index_identity reads: {collection: {id: (text, file_name, chunk_index)}}."""
    path.mkdir(parents=True, exist_ok=True)
    db = path / "chroma.sqlite3"
    if db.exists():
        db.unlink()
    con = sqlite3.connect(db)
    con.executescript("create table collections (id text, name text);"
                      "create table segments (id text, scope text, collection text);"
                      "create table embeddings (id integer primary key, segment_id text, embedding_id text);"
                      "create table embedding_metadata (id integer, key text, string_value text, int_value integer, "
                      "float_value real, bool_value integer);")
    for ci, (name, chunks) in enumerate(collections.items()):
        con.execute("insert into collections values (?, ?)", (f"c{ci}", name))
        con.execute("insert into segments values (?, 'METADATA', ?)", (f"s{ci}", f"c{ci}"))
        con.execute("insert into segments values (?, 'VECTOR', ?)", (f"v{ci}", f"c{ci}"))
        for eid, (text, fname, idx) in chunks.items():
            rid = con.execute("insert into embeddings (segment_id, embedding_id) values (?, ?)",
                              (f"s{ci}", eid)).lastrowid
            con.execute("insert into embedding_metadata values (?, 'chroma:document', ?, null, null, null)", (rid, text))
            con.execute("insert into embedding_metadata values (?, 'file_name', ?, null, null, null)", (rid, fname))
            con.execute("insert into embedding_metadata values (?, 'chunk_index', null, ?, null, null)", (rid, idx))
            con.execute("insert into embedding_metadata values (?, 'page', null, 1, null, null)", (rid,))
    con.commit()
    con.close()


CHUNKS = {"id-a": ("alpha text", "01_x.pdf", 0), "id-b": ("beta text", "01_x.pdf", 1), "id-c": ("gamma", "02_y.pdf", 0)}


def qids() -> dict:
    qs = ex.questions()
    return {g: next(q["id"] for q in qs if R.group_of(q["id"]) == g)
            for g in ("answerable", "false_premise", "not_answerable")}


def exp01_line(qid: str, draw: int, answer: str, error, passages, config: str = "single_pass") -> dict:
    return {"answer_key": ex.answer_key(config, qid, draw, index=INDEX), "experiment": "exp_01", "config": config,
            "question_id": qid, "draw": draw, "index_name": INDEX, "question": "Q?", "answerable": True,
            "generation": {"answer": answer, "error": error, "passages": passages}}


def write_jsonl(path: Path, rows: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    Q = qids()
    tmp = Path(tempfile.mkdtemp(prefix="check_records_"))
    store = tmp / "chroma"
    make_store(store, {"coll_s20": CHUNKS})

    # ---- Rule 8's groups (LIST.md Rule 8 table: 86 answerable, 10 false premise, 39 not answerable)
    from collections import Counter
    c = Counter(R.group_of(q["id"]) for q in ex.questions())
    check("Rule 8 groups on the 135 from the D5 key: 86 answerable, 10 false_premise, 39 not_answerable",
          c == {"answerable": 86, "false_premise": 10, "not_answerable": 39}, str(dict(c)))
    check("a question outside the D5 key is refused", isinstance(raises(lambda: R.group_of("NOT_A_QID")), R.RecordsError))
    check("RAGAS and RAGChecker apply to answerable and false_premise only",
          [R.applies(s, Q[g]) for s in ("ragas", "ragchecker") for g in ("answerable", "false_premise", "not_answerable")]
          == [True, True, False] * 2)

    # ---- index identity
    sink = tmp / "runs" / f"exp_01__single_pass__{INDEX}"
    line = ii.record(sink, INDEX, "coll_s20", store=store, script="check")
    held = ii.held(sink)
    check("record() writes one identity line; held() returns it", held is not None
          and held["id_text_sha256"] == line["id_text_sha256"] and held["n_chunks"] == 3)
    ii.record(sink, INDEX, "coll_s20", store=store, script="check")
    check("a resumed start with the same content: held() accepts two equal lines",
          ii.held(sink)["id_text_sha256"] == line["id_text_sha256"])
    chunks, where = ii.resolve(held)
    check("resolve() maps every id to its text", {k: v["text"] for k, v in chunks.items()}
          == {k: v[0] for k, v in CHUNKS.items()} and where["collection"] == "coll_s20")
    other = tmp / "chroma_copy"
    make_store(other, {"user_stuff": {"z": ("z", "z.pdf", 0)}, "coll_renamed": CHUNKS})
    check("resolve() finds the collection by content hash under another name in another store",
          ii.resolve(held, store=other)[1]["collection"] == "coll_renamed")
    changed = tmp / "chroma_changed"
    make_store(changed, {"coll_s20": {**CHUNKS, "id-b": ("beta text, edited", "01_x.pdf", 1)}})
    e = raises(lambda: ii.resolve(held, store=changed), ii.IndexIdentityError)
    check("resolve() refuses a store whose text differs from what the run recorded", e is not None, str(e)[:80])
    sink2 = tmp / "runs" / "twice"
    ii.record(sink2, INDEX, "coll_s20", store=store)
    ii.record(sink2, INDEX, "coll_s20", store=changed)
    check("held() refuses a run whose starts recorded two contents",
          isinstance(raises(lambda: ii.held(sink2)), ii.IndexIdentityError))
    check("a chunk's identity is not changed by metadata the hashes do not read (page)",
          ii.hashes(ii.read_chunks(store, "coll_s20")[1])["id_text_sha256"] == line["id_text_sha256"])

    # ---- exp_01 sinks
    write_jsonl(sink / "answers.jsonl", [
        exp01_line(Q["answerable"], 1, "", "boom", None),                 # an attempt with an error ...
        exp01_line(Q["answerable"], 1, "an answer", None, ["id-b", "id-a"]),   # ... then its answer
        exp01_line(Q["not_answerable"], 1, "I cannot tell", None, ["id-c"]),
        exp01_line(Q["false_premise"], 2, "", None, []),
    ])
    xs = R.read_run(sink)
    a = next(x for x in xs if x["question_id"] == Q["answerable"])
    check("exp_01: the last line of a key is its answer (an earlier error line is an attempt)",
          len(xs) == 3 and a["status"] == "ok" and a["answer"] == "an answer")
    check("exp_01: passage ids resolve to text, source and chunk_idx, in the stored order",
          [(p["id"], p["text"], p["source"], p["chunk_idx"]) for p in a["passages"]]
          == [("id-b", "beta text", "01_x.pdf", 1), ("id-a", "alpha text", "01_x.pdf", 0)])
    check("exp_01: config, draw, group and run_id come from the record and its answer key",
          (a["config"], a["draw"], a["group"], a["run_id"]) == ("single_pass", 1, "answerable", sink.name))
    fp = next(x for x in xs if x["question_id"] == Q["false_premise"])
    check("exp_01: an empty answer is no_answer; an empty passage list is kind none",
          fp["status"] == "no_answer" and fp["passages_kind"] == "none" and fp["passages"] == [])
    write_jsonl(tmp / "dup" / "answers.jsonl", [exp01_line(Q["answerable"], 1, "x", None, []),
                                                exp01_line(Q["answerable"], 1, "y", None, [])])
    check("exp_01: a key stored again after its answer is refused",
          isinstance(raises(lambda: R.read_run(tmp / "dup")), R.RecordsError))
    noid = tmp / "runs" / "noident"
    write_jsonl(noid / "answers.jsonl", [exp01_line(Q["answerable"], 1, "x", None, ["id-a"])])
    e = raises(lambda: R.read_run(noid), R.RecordsError)
    check("a run that recorded no index identity is refused when its ids are resolved", e is not None, str(e)[:70])
    check("... and read with resolve=False (counting only), texts None",
          R.read_run(noid, resolve=False)[0]["passages"][0]["text"] is None)
    write_jsonl(noid / "answers.jsonl", [exp01_line(Q["answerable"], 1, "x", None, ["id-zzz"])])
    ii.record(noid, INDEX, "coll_s20", store=store)
    check("an id the recorded collection lacks is refused", isinstance(raises(lambda: R.read_run(noid)), R.RecordsError))
    wrong = tmp / "runs" / "wrongindex"
    write_jsonl(wrong / "answers.jsonl", [exp01_line(Q["answerable"], 1, "x", None, ["id-a"])])
    ii.record(wrong, "exp_v4_s5_n0", "coll_s20", store=store)
    check("a record whose index_name is not the recorded index's is refused",
          isinstance(raises(lambda: R.read_run(wrong)), R.RecordsError))

    # ---- exp_03 answers.json
    s03 = tmp / "runs" / f"exp_03__naive_rag__{INDEX}"
    ii.record(s03, INDEX, "coll_s20", store=store)
    res = []
    for cfg, gen in (("naive_rag", {"answer": "n", "passages": ["id-c"]}), ("raw_gemini", {"answer": "r"}),
                     ("full_orchestrator", {"answer": "f", "steps": []})):
        res.append({"answer_key": ex.answer_key(cfg, Q["answerable"], 1, index=INDEX), "run_id": s03.name,
                    "question_id": Q["answerable"], "config": cfg, "draw": 1, "question": "Q?", "generation": gen,
                    "generated_answer": gen["answer"], "error": None, "index_name": INDEX})
    (s03 / "answers.json").write_text(json.dumps({"results": res, "completed_keys": []}))
    xs = {x["config"]: x for x in R.read_run(s03)}
    check("exp_03: naive_rag ids resolve; raw_gemini none; an orchestrator config not_recorded",
          (xs["naive_rag"]["passages"][0]["text"], xs["raw_gemini"]["passages_kind"],
           xs["full_orchestrator"]["passages_kind"], xs["full_orchestrator"]["passages"])
          == ("gamma", "none", "not_recorded", None))

    # ---- exp_06 and exp_02 results files, each row's run sink under runs_root
    runs = tmp / "runs"
    for rid in ("exp_06_depth_sweep__rlm_5__depthsweep86", f"exp_02_scaling_factorial__single_pass__{INDEX}"):
        ii.record(runs / rid, INDEX, "coll_s20", store=store)
    f06 = tmp / "v4_9_depth_sweep_latest.json"
    f06.write_text(json.dumps({"index": INDEX, "results": [
        {"answer_key": ex.answer_key("rlm_5", Q["answerable"], 1), "run_id": "exp_06_depth_sweep__rlm_5__depthsweep86",
         "question_id": Q["answerable"], "question": "Q?", "depth": 5, "draw": 1, "answer": "r", "error": None,
         "rlm": {"passages_seen": ["id-a", "id-c"]}},
        {"answer_key": ex.answer_key("rlm_5", Q["false_premise"], 1), "run_id": "exp_06_depth_sweep__rlm_5__depthsweep86",
         "question_id": Q["false_premise"], "question": "Q?", "depth": 5, "draw": 1, "answer": "",
         "error": "max_turns_empty: x", "rlm": None}]}))
    xs = R.read_run(f06, runs_root=runs)
    check("exp_06: passages_seen resolve; config rlm_5 from the key; a failed RLM run is error with no passages",
          [p["text"] for p in xs[0]["passages"]] == ["alpha text", "gamma"] and xs[0]["config"] == "rlm_5"
          and xs[1]["status"] == "error" and xs[1]["passages_kind"] == "not_recorded")
    f02 = tmp / "v4_5_scaling_latest.json"
    row02 = {"answer_key": ex.answer_key("single_pass", Q["answerable"], 1, index=INDEX),
             "run_id": f"exp_02_scaling_factorial__single_pass__{INDEX}", "index_name": INDEX,
             "question_id": Q["answerable"], "question": "Q?", "config": "single_pass", "draw": 1,
             "generation": {"answer": "s", "error": None, "passages": ["id-b"]}}
    f02.write_text(json.dumps({"per_question_results": [row02]}))
    check("exp_02: per_question_results rows resolve through their run's sink",
          R.read_run(f02, runs_root=runs)[0]["passages"][0]["text"] == "beta text")
    f02.write_text(json.dumps({"per_question_results": [row02, row02]}))
    check("two answers with the same (run_id, config, question_id, draw) are refused",
          isinstance(raises(lambda: R.read_run(f02, runs_root=runs)), R.RecordsError))

    # ---- G6 (the authors' RLM), the real sink, read only
    if G6.exists():
        xs = R.read_run(G6)
        c = Counter(x["group"] for x in xs)
        ok = (len(xs) == 405 and all(x["passages_kind"] == "whole_corpus" and len(x["passages"]) == 20 for x in xs)
              and c == {"answerable": 258, "false_premise": 30, "not_answerable": 117}
              and sum(len(p["text"]) for p in xs[0]["passages"]) == 1118265)
        check("G6 cap5: 405 answers, each with the 20-paper context (1,118,265 characters) after both sha256 checks",
              ok, f"status {dict(Counter(x['status'] for x in xs))}")
        g6 = tmp / "runs" / "g6_bad"
        rec = json.loads((G6 / "answers.jsonl").read_text().splitlines()[0])
        rec["context"] = {**rec["context"], "file_sha256": "0" * 64}
        write_jsonl(g6 / "answers.jsonl", [rec])
        check("G6: a context file whose sha256 is not the record's is refused",
              isinstance(raises(lambda: R.read_run(g6)), R.RecordsError))
    else:
        check("G6 sink present", False, str(G6))

    # ---- Rule 8's check (LIST.md:337)
    na, fpq = Q["not_answerable"], Q["false_premise"]
    rows = [{"question_id": na, "config": "c", "metrics": {"overall_metrics": {"precision": 50.0}}},   # violation
            {"question_id": na, "config": "c", "metrics": None, "status": "not_applicable"},
            {"question_id": fpq, "config": "c", "metrics": {"overall_metrics": {"precision": 50.0}}},
            {"question_id": na, "config": "c", "scores": {"faithfulness": 0.0}},                        # violation
            {"question_id": na, "config": "c", "scores": {"faithfulness": None}},
            {"question_id": na, "config": "c", "a": {"scores": {"refusal": 5}}, "b": {"status": "not_applicable"},
             "faithfulness_b": None},
            {"question_id": na, "config": "c", "a": {}, "b": {"scores": {"faithfulness": 4}}, "faithfulness_b": 4},  # violation
            {"question_id": "NOT_A_QID", "config": "c", "scores": {"faithfulness": None}}]               # violation
    bad = R.rule8_violations(rows)
    check("Rule 8 check: a number in a not-answerable cell fails (RAGChecker, RAGAS, judge b), null passes, the "
          "false-premise group is scored, a question outside the key fails", [b["row"] for b in bad] == [1, 4, 7, 8],
          str([b["row"] for b in bad]))
    out = tmp / "rule8.jsonl"
    write_jsonl(out, rows[1:3])
    with contextlib.redirect_stdout(io.StringIO()):
        sys.argv = ["records.py", "rule8", str(out)]
        rc_ok = R.main()
        write_jsonl(out, rows)
        rc_bad = R.main()
    check("records.py rule8 exits 0 on a clean output and 1 on a violation", (rc_ok, rc_bad) == (0, 1))

    # ---- resume (F55)
    x = R.read_run(sink)[0]
    k = R.ident(x)
    it = R.item_sha256(x, "ref")
    base = {"run_id": k[0], "config": k[1], "question_id": k[2], "draw": k[3], "item_sha256": it, "lock_sha256": "L1"}
    check("resume: done by (run_id, config, question_id, draw); the latest row counts",
          R.resume([{**base, "status": "ok"}, {**base, "status": "failed"}], "L1", {"ok"}, {k: it}) == set()
          and R.resume([{**base, "status": "failed"}, {**base, "status": "ok"}], "L1", {"ok"}, {k: it}) == {k})
    check("resume: a row under another lock_sha256 is refused",
          isinstance(raises(lambda: R.resume([{**base, "status": "ok"}], "L2", {"ok"}, {k: it})), R.RecordsError))
    check("resume: a row without run_id (an --arm output) is refused",
          isinstance(raises(lambda: R.resume([{**base, "run_id": None}], "L1", {"ok"}, {k: it})), R.RecordsError))
    check("resume: a row of the same answer with another item_sha256 is refused",
          isinstance(raises(lambda: R.resume([{**base, "item_sha256": "x"}], "L1", {"ok"}, {k: it})), R.RecordsError))

    # ---- ragchecker_run.py --run, RAGChecker replaced by a stand-in (no model call)
    check_ragchecker(tmp, sink, Q)
    # ---- judge_passages.py --run (prompt building only)
    check_judge(sink, Q)

    shutil.rmtree(tmp, ignore_errors=True)
    n, ok = len(RESULTS), sum(RESULTS)
    print(f"check_records: {ok}/{n} passed")
    return 0 if ok == n else 1


def check_ragchecker(tmp: Path, sink: Path, Q: dict) -> None:
    evaluated = []

    class Res:
        def __init__(self, d):
            self.results = [types.SimpleNamespace(**d["results"][0])]

        @classmethod
        def from_dict(cls, d):
            return cls(d)

    class Evaluator:
        def evaluate(self, res, metrics):
            y = res.results[0]
            evaluated.append(y)
            y.response_claims, y.gt_answer_claims = [["s", "p", "o"]], [["s", "p", "o"]]
            y.answer2response = y.response2answer = y.retrieved2response = y.retrieved2answer = []
            y.metrics = {"overall_metrics": {"precision": 100.0}}

    fake = types.ModuleType("ragchecker")
    fake.RAGResults = Res
    fake.metrics = types.ModuleType("ragchecker.metrics")
    fake.metrics.all_metrics = ["all"]
    saved = {m: sys.modules.get(m) for m in ("ragchecker", "ragchecker.metrics")}
    sys.modules["ragchecker"], sys.modules["ragchecker.metrics"] = fake, fake.metrics
    try:
        import importlib
        rr = importlib.import_module("experiments.scorers.ragchecker_run")
        gt = tmp / "gt.json"
        gt.write_text(json.dumps({"questions": [{"id": q, "expected_answer": "the reference"} for q in Q.values()]}))
        out = tmp / "rc_out"
        out.mkdir()
        lock = types.SimpleNamespace(sha256="LOCKSHA")
        call = types.SimpleNamespace(digest="d", options={}, fields=[])
        a = types.SimpleNamespace(run=sink, store=None, rows=None, limit=None, gt=gt, out=out, base="none", order="claims")
        current = {"key": None, "n": 0, "checks": 0, "ambiguous": 0}
        refs = {q: "the reference" for q in Q.values()}
        with contextlib.redirect_stdout(io.StringIO()):
            rc = rr.score_run(a, Evaluator(), current, lock, "m", call, False, out / "ragchecker.jsonl", refs)
        rows = {d["question_id"]: d for d in map(json.loads, (out / "ragchecker.jsonl").read_text().splitlines())}
        na, ans, fp = rows[Q["not_answerable"]], rows[Q["answerable"]], rows[Q["false_premise"]]
        check("ragchecker --run: not answerable -> not_applicable, metrics null, reason 'not applicable', no call",
              rc == 0 and na["status"] == "not_applicable" and na["metrics"] is None and na["reason"] == "not applicable"
              and na["calls"] == 0 and len(evaluated) == 1)
        check("ragchecker --run: an answerable answer is scored with its resolved passages as retrieved_context",
              ans["status"] == "ok" and [c["text"] for c in evaluated[0].retrieved_context] == ["beta text", "alpha text"]
              and ans["run_id"] == sink.name and ans["draw"] == 1 and ans["lock_sha256"] == "LOCKSHA")
        check("ragchecker --run: an empty false-premise answer is no_answer", fp["status"] == "no_answer")
        hdr = json.loads((out / "ragchecker_headers.jsonl").read_text().splitlines()[-1])
        check("ragchecker --run: the header records pythonhashseed and hash_randomization as the process has them "
              "(D83, Q144; main() refuses unless they are '0' and 0)",
              hdr.get("pythonhashseed", "absent") == os.environ.get("PYTHONHASHSEED")
              and hdr.get("hash_randomization", "absent") == sys.flags.hash_randomization,
              f"{hdr.get('pythonhashseed', 'absent')!r}, {hdr.get('hash_randomization', 'absent')!r}")
        check("ragchecker --run output passes Rule 8's check",
              R.rule8_violations(list(rows.values())) == [])
        with contextlib.redirect_stdout(io.StringIO()):
            rr.score_run(a, Evaluator(), current, lock, "m", call, False, out / "ragchecker.jsonl", refs)
        check("ragchecker --run: a resume makes no call for done or not_applicable answers", len(evaluated) == 1)
        lock2 = types.SimpleNamespace(sha256="OTHER")
        e = raises(lambda: rr.score_run(a, Evaluator(), current, lock2, "m", call, False, out / "ragchecker.jsonl",
                                        refs), SystemExit)
        check("ragchecker --run: a resume under another lock_sha256 is refused", e is not None and "lock" in str(e))
    finally:
        for m, v in saved.items():
            if v is None:
                sys.modules.pop(m, None)
            else:
                sys.modules[m] = v


def check_judge(sink: Path, Q: dict) -> None:
    import importlib
    jp = importlib.import_module("experiments.scorers.judge_passages")
    items = jp.run_answers(sink, None, None)
    by = {x["question_id"]: x for x in items}
    a, na = by[Q["answerable"]], by[Q["not_answerable"]]
    pa, pb, blk, refusal = jp.safe_prompts(a)
    check("judge --run: an answerable answer gets (b) with its resolved passages, (a) as the --arm path builds it",
          pb is not None and "beta text" in pb and "alpha text" in pb and pb.replace(blk, "", 1) == pa
          and a["answerable"] is True)
    check("judge --run: a not-answerable answer gets the decline prompt and no (b)",
          na["answerable"] is False and jp.safe_prompts(na)[1] is None)
    check("judge --run: rows are identified by (run_id, config, question_id, draw); --arm rows keep (config, "
          "question_id, draw)", jp.ident(a) == (sink.name, "single_pass", Q["answerable"], 1)
          and jp.ident({"config": "c", "question_id": "q", "draw": 1}) == ("c", "q", 1))


if __name__ == "__main__":
    sys.exit(main())
