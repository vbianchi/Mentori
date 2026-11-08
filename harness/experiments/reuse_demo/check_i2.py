#!/usr/bin/env python3
"""Offline checks for the I2 tools: plant_key.py, i2_memory.py, build_index.py, i2_generate.py, i2_judge.py, launch_i2.sh.

    uv run python experiments/reuse_demo/check_i2.py            # every part; part D runs in Mentori's environment
    uv run python experiments/reuse_demo/check_i2.py --part A   # one part (A to F)

No model, no server, no key, no index, no network. Nothing is written outside a temporary folder; the repository's
findings/ is not touched. Part D runs as a child process under experiments/mentori's environment (uv run --project
experiments/mentori), as exp_01 needs it; no command line here names an exp_NN script (K1's guard, i2_generate.py).

  A plant_key      the signed-off key loads under its pin; a changed byte is refused; each content rule refuses its
                   own mutation; the runner, records and S373 forms are right (PB_004 a refutation, answerable;
                   PB_005 not answerable, no concepts, min_core None).
  B i2_memory      vm_stat and /proc/meminfo readings; the floor (under, unknown counts as under); the sampler keeps
                   the lowest reading.
  C build_index    Mentori's own store set-up in a fresh folder (one admin, the index row); ingest on the paper's
                   20 PDFs with the encoder stood in gives the paper's 778 chunks and chunk manifest (the gate passes);
                   the gate's 20 files in create_indexes.py's order; a missing id, a manifest that names other files
                   and an existing store are refused; the gate verdict on the recorded identity and on each kind of
                   difference; gate and build with a stand-in ingestion: records written, build refused without a
                   passed gate, with a gate made by other code, with an existing record, and under the memory floor.
  D i2_generate    (Mentori's environment) exp_01 loaded by file; the dry run lists 5 questions x 5 configs x 3 draws;
                   on stubbed strategies (as experiments/runner/check_exp01_generator.py stubs them) the smoke stores
                   PB_001 single pass d1 in exp_01__single_pass__i2_plant5.smoke and a record line with memory_ok; a
                   run stores the key's questions under i2_plant5 keys; the memory rule stops a run before the answers
                   it would start under the floor (exit 4, those keys not stored, the others stored) and a resume
                   finishes them; a second process is refused (exit 75); --question-ids-file is refused; a key other
                   than the pinned one needs its own sha256; page_text.py refuses to overwrite the I2 texts and writes
                   one string per page with the pypdf version.
  E i2_judge       the key reading reproduces judge_passages.run_answers on the paper's own key (same fields and
                   item_sha256 on paper questions of each prompt rule); on the plant key the prompt rule, expected
                   answer and key_hash are S373's; selftest runs through judge_passages; status reports a check that
                   does not cover; run is refused while a K1 launcher runs, with --judge, and without --run/--out;
                   judge_passages.py and records.py are unchanged on disk and judge_passages' own functions are its
                   own in a process that does not install the key.
  G i2_signals     answers read with the plant key's groups; the key's v1 form; concepts after S471's gate (S432's
                   107 reproduced), its values S471.score's, rows the same bytes when run again; numbers after S382's
                   and S141's number gates, its values the deposited functions'; the papers' texts as the key's text
                   files; the MiniCheck stages' loop (S470's gate and scorer stood in): rows appended, a stopped run
                   resumes with the rest, another identity and the memory floor refused.
  H i2_report      Figure 2's rules read from S463 (correctness at 4 and 3, refusal at 3); the latest judge row per
                   answer; no_answer not passed; a judge failure listed, not counted; each answer's signals beside its
                   score; the same bytes when built again.
  F launch_i2.sh   with stand-ins for the driver and the memory reading: run refused without a passed smoke and with
                   a smoke whose memory was under the floor; smoke and run start one process at a time in the order of
                   the five configs on each config's store; a memory stop (exit 4) ends the sequence; under the floor
                   nothing starts; verified refused without a URL and while K1 runs; stores makes checked copies; no
                   command it starts matches K1's busy-guard pattern (run_k1_laptop.sh STRANGER).
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import copy
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (str(ROOT / "scripts"), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

FAILS: list = []
N = [0]


def check(name: str, ok: bool, detail: str = "") -> None:
    N[0] += 1
    if not ok:
        FAILS.append(name)
    print(f"{'PASS' if ok else 'FAIL'} {name}" + ("" if ok or not detail else f"  [{detail}]"), flush=True)


def raises(fn, exc=BaseException):
    try:
        fn()
    except exc as e:
        return e
    return None


def tmpdir(prefix: str) -> Path:
    return Path(tempfile.mkdtemp(prefix=prefix)).resolve()


# ───────────────────────────── A. plant_key ─────────────────────────────
def part_a():
    from experiments.reuse_demo import plant_key as PK
    k = PK.load()
    check("A the signed-off key loads under its pin", k.sha256 == PK.KEY_SHA256 and k.ids == [
        "PB_001", "PB_002", "PB_003", "PB_004", "PB_005"], str(k.ids))
    data = json.loads(PK.KEY.read_text())
    check("A its status says it is signed off (A9)", data["status"].startswith("signed off by Valerio Bianchi"))
    t = tmpdir("i2_key_")
    raw = PK.KEY.read_bytes()
    (t / "k.json").write_bytes(raw + b" ")
    check("A one byte more is refused under the pin", isinstance(raises(lambda: PK.load(t / "k.json")), PK.KeyProblem))
    check("A the same file without a pin is read (a reader's key)", PK.load(t / "k.json", None).ids == k.ids)

    def mutated(fn):
        d = copy.deepcopy(data)
        fn(d)
        return PK.check(d)
    muts = {
        "format not v2.4": lambda d: d["format"].update(version="2.3"),
        "no records": lambda d: d.update(records=[]),
        "a repeated id": lambda d: d["records"][1].update(id="PB_001"),
        "an id with '|'": lambda d: d["records"][0].update(id="PB|1"),
        "an empty question": lambda d: d["records"][0].update(question=" "),
        "question_answerable not a bool": lambda d: d["records"][0].update(question_answerable="true"),
        "an unknown answer type": lambda d: d["records"][0].update(answer_type="factoid"),
        "a concept without a phrase": lambda d: d["records"][0]["key_concepts"].append({"evidence_index": 0}),
        "not answerable but question_answerable true": lambda d: d["records"][4].update(question_answerable=True),
        "a refutation marked not answerable": lambda d: d["records"][3].update(question_answerable=False),
        "a not-answerable record with concepts": lambda d: d["records"][4].update(key_concepts=[{"phrase": "x"}]),
        "a not-answerable record with min_core": lambda d: d["records"][4].update(min_core=5),
        "an answerable record without min_core": lambda d: d["records"][0].update(min_core=None),
        "min_core a bool": lambda d: d["records"][0].update(min_core=True),
        "a synthesis statement that is not text": lambda d: d["records"][2].update(synthesis_statement=[1]),
    }
    check("A the key as signed off has no problem", PK.check(data) == [], str(PK.check(data)))
    for name, fn in muts.items():
        check(f"A refused: {name}", bool(mutated(fn)))
    qs = k.questions()
    check("A questions() gives the runner's FIELDS, in the key's order", all(tuple(q) == PK.FIELDS for q in qs)
          and [q["id"] for q in qs] == k.ids)
    by = {q["id"]: q for q in qs}
    check("A PB_004 is a refutation and answerable; PB_005 not answerable with no concepts and min_core None",
          by["PB_004"]["answer_type"] == "refutation" and by["PB_004"]["answerable"] is True
          and by["PB_005"]["answerable"] is False and by["PB_005"]["key_concepts"] == [] and by["PB_005"]["min_core"] is None)
    qs[0]["key_concepts"].append({"phrase": "changed"})
    check("A questions() returns fresh copies", k.questions()[0]["key_concepts"] != qs[0]["key_concepts"])
    check("A v1 and v2 forms", k.v1()["PB_005"] == {"id": "PB_005", "answerable": False}
          and k.v2()["PB_003"]["synthesis_statement"] == data["records"][2]["synthesis_statement"]
          and set(k.key_questions()) == set(k.ids))
    check("A describe() counts the answer types", k.describe()["answer_types"] == {
        "extractive": 2, "synthesis": 1, "refutation": 1, "not_answerable": 1})


# ───────────────────────────── B. i2_memory ─────────────────────────────
VM = """Mach Virtual Memory Statistics: (page size of 16384 bytes)
Pages free:                                    74164.
Pages active:                                 240273.
Pages inactive:                               238065.
Pages speculative:                              2366.
Pages throttled:                                   0.
Pages wired down:                            1869508.
Pages purgeable:                                2090.
"""


def part_b():
    from experiments.reuse_demo import i2_memory as M
    want = (74164 + 238065 + 2366 + 2090) * 16384 / 1024 ** 3
    check("B vm_stat: free+inactive+speculative+purgeable pages x page size", abs(M.parse_vm_stat(VM) - want) < 1e-9,
          f"{M.parse_vm_stat(VM)} {want}")
    check("B vm_stat without the purgeable line reads None", M.parse_vm_stat(VM.replace("Pages purgeable", "X")) is None)
    check("B vm_stat without a page size reads None", M.parse_vm_stat(VM.replace("page size of", "pg")) is None)
    check("B /proc/meminfo MemAvailable", abs(M.parse_meminfo("MemTotal: 1 kB\nMemAvailable:  2097152 kB\n") - 2.0) < 1e-9)
    check("B under: 1.99 is under 2, 2.0 is not, unknown is under",
          M.under(2, 1.99)[0] and not M.under(2, 2.0)[0] and M.under(2, None)[0])
    seq = iter([5.0, 3.0, None, 4.0, 2.5])
    s = M.Sampler(0.01, read=lambda: next(seq))
    for _ in range(4):
        s.sample()
    r = s.stop()
    check("B the sampler keeps the lowest reading and counts unknown ones",
          r["min_free_gb"] == 2.5 and r["samples"] == 5 and r["unknown_samples"] == 1, str(r))
    real = M.free_gb()
    check("B a real reading on this machine is a number", isinstance(real, float) and real > 0, str(real))


# ───────────────────────────── C. build_index ─────────────────────────────
def part_c():
    from experiments.reuse_demo import build_index as B
    from experiments.reuse_demo import i2_memory as M
    t = tmpdir("i2_build_")
    papers = t / "papers"
    papers.mkdir()
    for i in range(25, 0, -1):
        (papers / f"{i:02d}_p{i}.pdf").write_bytes(f"pdf {i}".encode())
    (papers / "notes.pdf").write_bytes(b"x")
    files = B.gate_files(papers)
    check("C the gate's files are ids 1 to 20 in order", [f.name for f in files] == [f"{i:02d}_p{i}.pdf" for i in
                                                                                       range(1, 21)])
    (papers / "07_p7.pdf").unlink()
    check("C a missing core id is refused", isinstance(raises(lambda: B.gate_files(papers)), SystemExit))
    (papers / "07_p7.pdf").write_bytes(b"pdf 7")
    corpus = t / "corpus"
    corpus.mkdir()
    for n in ("02_b.pdf", "01_a.pdf"):
        (corpus / n).write_bytes(n.encode())
    man = t / "m.csv"
    man.write_text("paper_id,bucket,filename\n1,core,01_a.pdf\n2,core,02_b.pdf\n3,noise,03_c.pdf\n")
    check("C corpus files sorted by name and matched by the manifest's core rows",
          [p.name for p in B.corpus_files(corpus, man)] == ["01_a.pdf", "02_b.pdf"])
    man.write_text("paper_id,bucket,filename\n1,core,01_a.pdf\n")
    check("C a manifest naming other files is refused", isinstance(raises(lambda: B.corpus_files(corpus, man)), SystemExit))
    man.write_text("paper_id,bucket,filename\n1,core,01_a.pdf\n2,core,02_b.pdf\n")
    (t / "exists").mkdir()
    check("C an existing store folder is refused", isinstance(raises(lambda: B.fresh_store(t / "exists")), SystemExit))
    real = {"status": "READY", "file_errors": [], "documents_registered": 20, "total_chunks": 778,
            "identity": {"n_chunks": 778, "chunk_manifest_sha256": B.GATE_MANIFEST}}
    check("C the gate verdict passes the recorded identity", B.gate_verdict(real, 20) == (True, []))
    for name, change in {"another manifest": {"identity": {"n_chunks": 778, "chunk_manifest_sha256": "0" * 64}},
                         "777 chunks": {"total_chunks": 777, "identity": {"n_chunks": 777,
                                                                          "chunk_manifest_sha256": B.GATE_MANIFEST}},
                         "a file error": {"file_errors": [{"file": "x"}]}, "19 documents": {"documents_registered": 19},
                         "not READY": {"status": "FAILED"}}.items():
        check(f"C the gate verdict fails on {name}", B.gate_verdict({**real, **change}, 20)[0] is False)

    # Mentori's own store set-up (init_db, the admin user, the UserCollection row) in a fresh folder, in its environment
    code = ("import json, sys; from pathlib import Path; from experiments.reuse_demo import build_index as B\n"
            "st = B.fresh_store(Path(sys.argv[1])); files = [Path(sys.argv[2])]\n"
            "cid, uid = B.prepare(st, 'i2_check', files, 'check')\n"
            "from backend.database import engine\nfrom backend.retrieval.models import UserCollection\n"
            "from backend.models.user import User\nfrom sqlmodel import Session, select\n"
            "import backend.retrieval.jobs as J\n"
            "with Session(engine) as s:\n"
            "    c = s.exec(select(UserCollection)).all(); u = s.exec(select(User)).all()\n"
            "    print(json.dumps({'collections': [(x.name, x.chunk_size, x.chunk_overlap, x.embedding_model, x.status.value,"
            " x.id == cid) for x in c], 'users': [(x.email, x.role, x.settings, x.id == uid) for x in u],"
            " 'registry_dir': J.REGISTRY_DIR, 'cwd': str(Path.cwd())}))\n")
    out = subprocess.run(["uv", "run", "--project", str(ROOT / "experiments" / "mentori"), "--frozen", "python", "-c",
                          code, str(t / "mstore"), str(corpus / "01_a.pdf")], cwd=ROOT, capture_output=True,
                         text=True, env={k: v for k, v in os.environ.items() if k not in ("DATABASE_URL",
                                                                                          "CHROMA_PERSIST_DIRECTORY")})
    try:
        got = json.loads(out.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        got = None
    check("C prepare in Mentori's environment: a fresh store with one admin (empty settings) and the index row at "
          "512/50 bge-m3, PENDING; the registry inside the store's chroma_db; the store as working directory",
          got is not None and got["collections"] == [["i2_check", 512, 50, "BAAI/bge-m3", "PENDING", True]]
          and got["users"] == [["admin@mentori", "admin", {}, True]]
          and got["registry_dir"] == str(t / "mstore" / "chroma_db" / "registries") and got["cwd"] == str(t / "mstore"),
          (out.stdout + out.stderr)[-800:])

    # build_index.ingest end to end on the paper's 20 PDFs, with the encoder stood in (vectors of ones): the chunk texts,
    # which are all the gate compares, must be the paper's 778 (chunk_manifest_sha256 b9affe3f...)
    papers20 = Path.home() / "projects/Mentori-paper/datasets/v4_papers/core"
    stub = ("import sys, json; from pathlib import Path; import numpy as np\n"
            "from experiments.reuse_demo import build_index as B\n"
            "orig = B.prepare\n"
            "def prepare(*a, **k):\n"
            "    r = orig(*a, **k)\n"
            "    import backend.retrieval.embeddings as E\n"
            "    E.EmbeddingEngine._ensure_model = lambda self: setattr(self, 'dimension', 1024)\n"
            "    E.EmbeddingEngine.embed_documents = lambda self, t, batch_size=32, show_progress=False: "
            "np.ones((len(t), 1024), dtype=np.float32)\n"
            "    return r\n"
            "B.prepare = prepare\n"
            "gate = sys.argv[2] == 'gate'\n"
            "files = B.gate_files(Path(sys.argv[3])) if gate else B.corpus_files(Path(sys.argv[3]), Path(sys.argv[4]))\n"
            "res = B.ingest(B.fresh_store(Path(sys.argv[1])), B.GATE_INDEX if gate else 'i2_plant5', files, 'stub')\n"
            "print(json.dumps({'verdict': B.gate_verdict(res, len(files)), 'cwd': str(Path.cwd()), 'ident': "
            "[res['identity']['n_chunks'], res['identity']['chunk_manifest_sha256'], res['file_errors']]}))\n")

    def stub_build(store, *args):              # one store per process: Mentori reads its settings once
        out = subprocess.run(["uv", "run", "--project", str(ROOT / "experiments" / "mentori"), "--frozen", "python",
                              "-c", stub, str(store), *map(str, args)], cwd=ROOT, capture_output=True, text=True,
                             env={k: v for k, v in os.environ.items() if k not in ("DATABASE_URL",
                                                                                   "CHROMA_PERSIST_DIRECTORY")})
        try:
            return json.loads(out.stdout.strip().splitlines()[-1]), ""
        except (ValueError, IndexError):
            return None, (out.stdout + out.stderr)[-800:]
    if not papers20.exists():
        check("C (skipped: the paper's 20 PDFs are not on this machine) the gate's chunking on a stand-in encoder", True)
    else:
        got, err = stub_build(t / "stubgate", "gate", papers20)
        check("C ingest on the paper's 20 PDFs with the encoder stood in: the gate passes (778 chunks, the paper's "
              "chunk manifest), and the caller's working directory is put back",
              got is not None and got["verdict"] == [True, []] and got["cwd"] == str(ROOT), err)
    got, err = stub_build(t / "stubplant", "plant", HERE / "corpus" / "core", HERE / "corpus_papers.csv")
    check("C the plant corpus with the encoder stood in: 222 chunks, chunk manifest build_index.PLANT_MANIFEST",
          got is not None and got["ident"] == [222, B.PLANT_MANIFEST, []], err or str(got))

    calls = []

    def fake_ingest(result):
        def ingest(store, index_name, fl, desc):
            calls.append((store, index_name, [p.name for p in fl], desc))
            return copy.deepcopy(result)
        return ingest
    saved = M.under
    M.under = lambda floor, reading=None: (False, 9.0)
    try:
        rec = t / "gate.json"
        a = B.parse_args(["gate", "--papers-dir", str(papers), "--store", str(t / "g1"), "--record", str(rec)])
        rc = B.cmd_gate(a, fake_ingest(real))
        g = json.loads(rec.read_text())
        check("C gate with the recorded identity: exit 0, record passed, its code identity and 20 files",
              rc == 0 and g["passed"] is True and g["code"] == B.code_identity() and len(g["files"]) == 20
              and calls[-1][1] == "exp_v4_s20_n0" and calls[-1][3].startswith("V4 experiment index: 20 core"), str(g)[:300])
        bad_rec = t / "gate_bad.json"
        a = B.parse_args(["gate", "--papers-dir", str(papers), "--store", str(t / "g2"), "--record", str(bad_rec)])
        rc = B.cmd_gate(a, fake_ingest({**real, "total_chunks": 700}))
        check("C gate with another chunk count: exit 1, record not passed",
              rc == 1 and json.loads(bad_rec.read_text())["passed"] is False)
        plant = {"status": "READY", "file_errors": [], "documents_registered": 2, "total_chunks": 40,
                 "identity": {"n_chunks": 40, "chunk_manifest_sha256": "a" * 64}}

        def build(store, record, gate_record, result=plant):
            a = B.parse_args(["build", "--corpus", str(corpus), "--manifest", str(man), "--index", "i2_test",
                              "--store", str(store), "--record", str(record), "--gate-record", str(gate_record)])
            return raises(lambda: B.cmd_build(a, fake_ingest(result)), SystemExit), a
        e, _ = build(t / "b0", t / "b0.json", t / "none.json")
        check("C build refused without a gate record", e is not None and "gate" in str(e) and not (t / "b0").exists())
        e, _ = build(t / "b1", t / "b1.json", bad_rec)
        check("C build refused with a gate that did not pass", e is not None and not (t / "b1").exists())
        other = json.loads(rec.read_text())
        other["code"]["experiments/mentori/backend/retrieval/chunking.py"] = "0" * 64
        (t / "gate_other.json").write_text(json.dumps(other))
        e, _ = build(t / "b2", t / "b2.json", t / "gate_other.json")
        check("C build refused with a gate made by other code", e is not None and "chunking.py" in str(e))
        a = B.parse_args(["build", "--corpus", str(corpus), "--manifest", str(man), "--index", "i2_test",
                          "--store", str(t / "b3"), "--record", str(t / "b3.json"), "--gate-record", str(rec)])
        rc = B.cmd_build(a, fake_ingest(plant))
        r = json.loads((t / "b3.json").read_text())
        check("C build after a passed gate: exit 0, record ok with files, manifest sha256 and gate record sha256",
              rc == 0 and r["ok"] is True and [f["file"] for f in r["files"]] == ["01_a.pdf", "02_b.pdf"]
              and r["gate_record_sha256"] == B.sha256_file(rec) and calls[-1][1] == "i2_test", str(r)[:300])
        a = B.parse_args(["build", "--corpus", str(corpus), "--manifest", str(man), "--index", "i2_test",
                          "--store", str(t / "b7"), "--record", str(t / "b7.json"), "--gate-record", str(rec),
                          "--expect-manifest", "b" * 64])
        rc = B.cmd_build(a, fake_ingest(plant))
        r7 = json.loads((t / "b7.json").read_text())
        check("C a build whose chunk manifest is not the expected one exits 1 and is recorded not ok",
              rc == 1 and r7["ok"] is False and r7["expected"]["equal"] is False)
        sh = (HERE / "launch_i2.sh").read_text()
        check("C launch_i2.sh index-build expects build_index.PLANT_MANIFEST",
              f"PLANT_MANIFEST={B.PLANT_MANIFEST}" in sh and "--expect-manifest $PLANT_MANIFEST" in sh)
        e, _ = build(t / "b4", t / "b3.json", rec)
        check("C build refused when its record exists", e is not None and "never overwritten" in str(e))
        a = B.parse_args(["build", "--corpus", str(corpus), "--manifest", str(man), "--index", "i2_test",
                          "--store", str(t / "b5"), "--record", str(t / "b5.json"), "--gate-record", str(rec)])
        rc = B.cmd_build(a, fake_ingest({**plant, "file_errors": [{"file": "02_b.pdf", "error": "x"}]}))
        check("C a build with a file error exits 1 and is recorded not ok",
              rc == 1 and json.loads((t / "b5.json").read_text())["ok"] is False)
        M.under = lambda floor, reading=None: (True, 1.2)
        e, _ = build(t / "b6", t / "b6.json", rec)
        check("C build refused under the memory floor, before the store is made",
              e is not None and "floor" in str(e) and not (t / "b6").exists())
    finally:
        M.under = saved


# ───────────────────────────── D. i2_generate (Mentori's environment) ─────────────────────────────
def part_d_parent():
    env = {**os.environ, "CHECK_I2_CHILD": "D"}
    out = subprocess.run(["uv", "run", "--project", str(ROOT / "experiments" / "mentori"), "--frozen", "python",
                          str(Path(__file__)), "--part", "D"], cwd=ROOT, env=env, capture_output=True, text=True)
    for line in out.stdout.splitlines():
        if line.startswith(("PASS ", "FAIL ")):
            N[0] += 1
            if line.startswith("FAIL"):
                FAILS.append(line[5:])
            print(line, flush=True)
    if out.returncode not in (0, 1) or "PART D DONE" not in out.stdout:
        FAILS.append("D the child did not finish")
        print("FAIL D the child did not finish:\n" + out.stdout[-3000:] + out.stderr[-3000:], flush=True)


def part_d_child():
    t = tmpdir("i2_gen_")
    os.environ.update(DATABASE_URL=f"sqlite:///{t}/check.db", WORKSPACE_DIR=str(t / "ws"),
                      CHROMA_PERSIST_DIRECTORY=str(t / "chroma"), TOOL_SERVER_URL="http://127.0.0.1:9",
                      BACKEND_INTERNAL_URL="http://127.0.0.1:9")
    from experiments.reuse_demo import i2_generate as G
    from experiments.reuse_demo import i2_memory as M
    from experiments.reuse_demo import plant_key as PK
    G.LOCK_FILE = t / ".lock"
    mod = G.load_exp01()
    check("D exp_01 loads from its file as i2_exp01 (no command line names it)", mod.__name__ == "i2_exp01"
          and Path(mod.__file__).name == "exp_01_generation.py")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = G.main(["--dry-run", "--sink-root", str(t / "dry")], load=lambda: mod)
    out = buf.getvalue()
    check("D the dry run: 5 questions x 5 configs x 3 draws = 75 answers on i2_plant5",
          rc == 0 and "5 questions x 5 configs x 3 draws = 75 answers" in out and "index i2_plant5" in out
          and "first key i2_plant5|single_pass|PB_001|d1" in out, out[-400:])
    check("D the dry run wrote nothing", not (t / "dry").exists())

    seen = []

    async def fake_config(config_name, question, retriever, collection_name, router, gen_model, user_id, index_name,
                          budget=None):
        seen.append((config_name, question, gen_model, index_name))
        await asyncio.sleep(0.01)
        return mod.GenerationResult(answer=f"answer to {question[:20]}", latency_s=0.0, llm_calls=0, tokens_used=0,
                                    retrieved_passages=0, config=config_name, gen_model=gen_model)
    for n, v in {"_run_config": fake_config, "find_admin_user_id": lambda: "u",
                 "check_index_exists": lambda u, i: i == "i2_plant5",
                 "setup_retriever": lambda u, i: (None, "coll", "emb"), "ModelRouter": lambda: None,
                 "index_identity": SimpleNamespace(record=lambda sink, *a, **k: None)}.items():
        setattr(mod, n, v)

    readings = {"v": 10.0}
    M.under = lambda floor, reading=None: (readings["v"] < floor, readings["v"])
    M.free_gb = lambda: readings["v"]
    rec = t / "rec.jsonl"
    base = ["--ollama-url", G.NO_SERVER_URL, "--record-file", str(rec), "--sample-s", "0.05"]

    def run(args):
        b = io.StringIO()
        with contextlib.redirect_stdout(b), contextlib.redirect_stderr(io.StringIO()):
            e = raises(lambda: G.main(args + base, load=lambda: mod), SystemExit)
            code = None
        return b.getvalue(), e

    def answers(root, rid):
        f = Path(root) / rid / "answers.jsonl"
        return [json.loads(x) for x in f.read_text().splitlines()] if f.exists() else []

    b = io.StringIO()
    with contextlib.redirect_stdout(b), contextlib.redirect_stderr(io.StringIO()):
        rc = G.main(["--configs", "single_pass", "--smoke", "--sink-root", str(t / "smoke")] + base, load=lambda: mod)
    sm = answers(t / "smoke", "exp_01__single_pass__i2_plant5.smoke")
    line = json.loads(rec.read_text().splitlines()[-1])
    check("D the smoke stores PB_001, single pass, draw 1, in its own .smoke run, with Gemini as the generator",
          rc == 0 and [a["answer_key"] for a in sm] == ["i2_plant5|single_pass|PB_001|d1"]
          and sm[0]["gen_model"] == "gemini::gemini-3-flash-preview" and sm[0]["question"] == PK.load().records[0]["question"],
          f"{rc} {[a['answer_key'] for a in sm]}")
    check("D the smoke's record line: smoke, exit 0, memory_ok, the key's sha256, one memory check",
          line["smoke"] is True and line["exit"] == 0 and line["memory_ok"] is True and line["memory_checks"] == 1
          and line["key"]["sha256"] == PK.KEY_SHA256 and line["memory"]["min_free_gb"] == 10.0, str(line)[:400])

    seen.clear()
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        rc = G.main(["--configs", "single_pass", "multi_hop", "--draws", "1", "2", "--sink-root", str(t / "runs")] + base,
                    load=lambda: mod)
    sp = answers(t / "runs", "exp_01__single_pass__i2_plant5")
    mh = answers(t / "runs", "exp_01__multi_hop__i2_plant5")
    check("D a run stores the 5 questions x 2 draws per config under i2_plant5 keys",
          rc == 0 and len(sp) == 10 and len(mh) == 10
          and {a["answer_key"] for a in sp} == {f"i2_plant5|single_pass|PB_00{i}|d{d}" for i in range(1, 6) for d in (1, 2)}
          and all(s[3] == "i2_plant5" for s in seen), f"{rc} {len(sp)} {len(mh)}")
    check("D the not-answerable question is stored as not answerable",
          {a["question_id"]: a["answerable"] for a in sp}["PB_005"] is False)

    # the memory rule: the floor is crossed after three answers have started
    calls = {"n": 0}

    def under(floor, reading=None):
        calls["n"] += 1
        low = calls["n"] > 4          # the first call is main's start check; then three answers start
        return low, (1.0 if low else 10.0)
    M.under = under
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        rc = G.main(["--configs", "rlm_10", "--draws", "1", "--sink-root", str(t / "mem")] + base, load=lambda: mod)
    got = answers(t / "mem", "exp_01__rlm_10__i2_plant5")
    line = json.loads(rec.read_text().splitlines()[-1])
    check("D under the floor the run stops: exit 4, the answers that started stored, none of the others",
          rc == G.EXIT_MEMORY and len(got) == 3 and all(not (a["generation"] or {}).get("error") for a in got)
          and line["exit"] == G.EXIT_MEMORY and line["memory_ok"] is False and "under the floor" in (line["stopped"] or ""),
          f"rc {rc}, {len(got)} stored, {line.get('stopped')}")
    n_before = len(got)
    M.under = lambda floor, reading=None: (False, 10.0)
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        rc = G.main(["--configs", "rlm_10", "--draws", "1", "--resume", "--sink-root", str(t / "mem")] + base,
                    load=lambda: mod)
    got = answers(t / "mem", "exp_01__rlm_10__i2_plant5")
    check("D a resume after the memory stop stores the rest, each key once",
          rc == 0 and len(got) == 5 and len({a["answer_key"] for a in got}) == 5 and n_before < 5, f"{rc} {len(got)}")

    import fcntl
    fh = open(G.LOCK_FILE, "a")
    fcntl.flock(fh, fcntl.LOCK_EX)
    child = subprocess.run([sys.executable, "-c",
                            "import sys; sys.path.insert(0, %r); from experiments.reuse_demo import i2_generate as G;"
                            "G.hold_lock(%r)" % (str(ROOT), str(G.LOCK_FILE))], capture_output=True, text=True)
    fh.close()
    check("D a second process is refused while one holds the lock (exit 75)", child.returncode == G.EXIT_BUSY,
          child.stdout + child.stderr)
    e = raises(lambda: G.plant_questions(PK.load())(None, Path("x.json"), (1,)), SystemExit)
    check("D --question-ids-file is refused", e is not None)
    e = raises(lambda: G.main(["--key", str(ROOT / "data/ground_truth_v2/all_v2_4.json"), "--dry-run"],
                              load=lambda: mod), SystemExit)
    check("D another key without its own sha256 is refused", e is not None and "key-sha256" in str(e))
    e = raises(lambda: G.main(["--configs", "single_pass", "--ollama-url", "http://127.0.0.1:11434", "--record-file",
                               str(rec)], load=lambda: mod), SystemExit)
    check("D a no-server config naming a real server is refused", e is not None and "11499" in str(e))
    from experiments.reuse_demo import page_text as PT
    e = raises(lambda: PT.main(["--corpus", str(HERE / "corpus" / "core"), "--out", str(HERE / "text")]), SystemExit)
    check("D page_text refuses to write over the I2 texts the key's quotes were checked against",
          e is not None and "never overwritten" in str(e))
    small = t / "pdfs"
    small.mkdir()
    import shutil
    shutil.copy(HERE / "corpus" / "core" / "05_pelgrom2019_blr38.pdf", small)
    with contextlib.redirect_stdout(io.StringIO()):
        PT.main(["--corpus", str(small), "--out", str(t / "text")])
    pages = json.loads((t / "text" / "05_pelgrom2019_blr38.pdf.pages.json").read_text())
    check("D page_text writes one string per page and records the pypdf version",
          len(pages) == 14 and (t / "text" / "pages.txt").read_text().startswith("pypdf "))
    print("PART D DONE", flush=True)


# ───────────────────────────── E. i2_judge ─────────────────────────────
def write_sink(root: Path, run_id: str, rows: list[dict]) -> Path:
    s = root / run_id
    s.mkdir(parents=True)
    (s / "answers.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    return s


def row(index, config, qid, draw, question, answer, error=None):
    return {"answer_key": f"{index}|{config}|{qid}|d{draw}", "run_id": f"exp_01__{config}__{index}",
            "question_id": qid, "draw": draw, "config": config, "index_name": index, "question": question,
            "generation": {"answer": answer, "error": error, "passages": None}}


def part_e():
    import importlib
    t = tmpdir("i2_judge_")
    jp_file, rec_file = ROOT / "experiments/scorers/judge_passages.py", ROOT / "experiments/scorers/records.py"
    before = {f: hashlib.sha256(f.read_bytes()).hexdigest() for f in (jp_file, rec_file)}
    from experiments.scorers import judge_passages as JP
    from experiments.scorers import records as R
    from experiments.reuse_demo import i2_judge as IJ
    from experiments.reuse_demo import plant_key as PK
    original_run_answers, original_kq = JP.run_answers, R.key_questions
    saved = (JP.run_answers, JP.STORED, JP.S373.KEY, R.key_questions)
    try:
        _part_e(t, JP, R, IJ, PK, original_run_answers, jp_file, rec_file, before)
    finally:                                   # the key is installed for this process only: put it back for parts G, H
        JP.run_answers, JP.STORED, JP.S373.KEY, R.key_questions = saved


def _part_e(t, JP, R, IJ, PK, original_run_answers, jp_file, rec_file, before):

    # the paper's own key, read both ways: judge_passages' own run_answers and the wrapper's
    v24 = json.loads((ROOT / "data/ground_truth_v2/all_v2_4.json").read_text())
    d5 = R.key_questions()
    pick = {}
    for q in d5.values():
        g = R.GROUP_OF_TYPE[q["answer_type"]]
        pick.setdefault(g, q["id"])
    ids = sorted(pick.values())
    recs = {r["id"]: r for r in v24["records"]}
    paper_rows = [row("exp_v4_s20_n0", "single_pass", q, 1, recs[q]["question"], f"an answer to {q}") for q in ids]
    paper_rows.append(row("exp_v4_s20_n0", "single_pass", ids[0], 2, recs[ids[0]]["question"], "", error="boom"))
    sink = write_sink(t / "paper", "exp_01__single_pass__exp_v4_s20_n0", paper_rows)
    want = original_run_answers(sink, None, None)
    paper_key = PK.Key(ROOT / "data/ground_truth_v2/all_v2_4.json", "paper",
                       {"records": [{**recs[q], "min_core": d5[q]["min_core"]} for q in ids]})
    IJ.install(paper_key)
    got = JP.run_answers(sink, None, None)
    check("E on the paper's key the wrapper's reading equals judge_passages.run_answers (fields, prompt rule, key_hash, "
          f"item_sha256) for {', '.join(f'{g} {q}' for g, q in sorted(pick.items()))} and an errored answer",
          got == want and len(got) == 4, f"{len(got)} {len(want)}")

    key = PK.load()
    IJ.install(key)
    pr = [row("i2_plant5", "single_pass", r["id"], 1, r["question"], f"plant answer {r['id']}") for r in key.records]
    psink = write_sink(t / "plant", "exp_01__single_pass__i2_plant5", pr)
    xs = {x["question_id"]: x for x in JP.run_answers(psink, None, None)}
    S373 = JP.S373
    v1, v2 = key.v1(), key.v2()
    check("E plant: PB_001 to PB_004 get the answerable prompt (PB_004 a refutation, Q51), PB_005 the decline prompt",
          [xs[q]["answerable"] for q in key.ids] == [True, True, True, True, False])
    check("E plant: PB_003's expected answer is the short answer, a blank line and the synthesis statement",
          xs["PB_003"]["expected"] == v2["PB_003"]["short_answer"] + "\n\n" + v2["PB_003"]["synthesis_statement"])
    check("E plant: concepts are the key's phrases; key_hash is S373.key_hash on the plant key",
          all(xs[q]["concepts"] == [k["phrase"] for k in v2[q]["key_concepts"]]
              and xs[q]["key_hash"] == S373.key_hash(q, v2) for q in key.ids))
    check("E plant: S373.KEY names the plant key and judge_passages has no stored scores to compare",
          Path(S373.KEY) == key.path and JP.STORED == [])
    b = io.StringIO()
    argv0 = sys.argv
    try:
        with contextlib.redirect_stdout(b):
            rc = IJ.main(["selftest", "--run", str(psink)])
    finally:
        sys.argv = argv0
    check("E selftest runs through judge_passages' own selftest on the 5 plant answers",
          rc == 0 and "SELFTEST: 5 answers" in b.getvalue(), b.getvalue()[-300:])
    cd = t / "check"
    cd.mkdir()
    (cd / "repro_check.json").write_text(json.dumps({"passed": True, "full_sample": True, "code": {"x": "y"},
                                                     "lock_sha256": "0"}))
    b = io.StringIO()
    with contextlib.redirect_stdout(b):
        rc = IJ.status(cd)
    check("E status reports a check made with other code and another lock as not covering", rc == 1
          and "DOES NOT COVER" in b.getvalue())
    sleeper = subprocess.Popen(["sleep", "30"])
    try:
        os.environ[IJ.K1_PATTERN_VAR] = r"^sleep 30$"
        e = raises(lambda: IJ.main(["run", "--run", str(psink), "--out", str(t / "o"), "--base", "x", "--log", "x",
                                    "--binary", "x", "--machine", "macos", "--check-dir", str(cd)]), SystemExit)
        check("E run is refused while a K1 launcher runs here, before anything is read or loaded",
              e is not None and "K1" in str(e) and not (t / "o").exists())
    finally:
        sleeper.kill()
        os.environ[IJ.K1_PATTERN_VAR] = r"^no such process pattern i2 check$"
    e = raises(lambda: IJ.main(["run", "--run", str(psink), "--out", str(t / "o2"), "--judge", "second"]), SystemExit)
    check("E run with --judge is refused (the main judge only)", e is not None and "--judge" in str(e))
    forms = [["--judge=second"], ["--jud", "second"], ["--j=second"]]
    errs = [raises(lambda f=f: IJ.main(["run", "--run", str(psink), "--out", str(t / "o3"), *f]), SystemExit)
            for f in forms]
    check("E run with --judge=second or an abbreviation is refused too", all(e is not None and "--judge" in str(e)
                                                                           for e in errs), str(errs))
    e = raises(lambda: IJ.main(["run", "--run", str(psink)]), SystemExit)
    check("E run without --out is refused", e is not None and "--out" in str(e))
    forms = [["--variants", "ab"], ["--variants=ab"], ["--var", "ab"], ["--v=ab"]]
    errs = [raises(lambda f=f: IJ.main(["run", "--run", str(psink), "--out", str(t / "o4"), *f]), SystemExit)
            for f in forms]
    check("E run with --variants ab, in any form argparse takes, is refused (D161 (7): the plain call only)",
          all(e is not None and "--variants a" in str(e) for e in errs), str(errs))
    seen, jp_main = [], JP.main
    JP.main = lambda: seen.append(list(sys.argv)) or 0
    argv0 = sys.argv
    try:
        rcs = [IJ.main(["run", "--run", str(psink), "--out", str(t / "o5"), *f]) for f in ([], ["--variants", "a"])]
    finally:
        JP.main, sys.argv = jp_main, argv0
    check("E run sends --variants a to judge_passages when none is given, and passes an explicit a once",
          rcs == [0, 0] and [x[x.index("--variants") + 1] for x in seen] == ["a", "a"]
          and [x.count("--variants") for x in seen] == [1, 1], str(seen))
    os.environ.pop(IJ.K1_PATTERN_VAR, None)
    after = {f: hashlib.sha256(f.read_bytes()).hexdigest() for f in (jp_file, rec_file)}
    check("E judge_passages.py and records.py are unchanged on disk", before == after)
    child = subprocess.run(["uv", "run", "--frozen", "python", "-c",
                            "import sys; sys.path[:0] = ['scripts', '.']\n"
                            "from experiments.scorers import judge_passages as JP, records as R\n"
                            "print(JP.run_answers.__module__, JP.run_answers.__qualname__, R.key_questions.__qualname__,"
                            " str(JP.S373.KEY).endswith('all_v2_4.json'), len(JP.STORED))"],
                           cwd=ROOT, capture_output=True, text=True)
    check("E in a process that does not install the key, judge_passages reads key v2.4 with its own functions",
          child.stdout.split() == ["experiments.scorers.judge_passages", "run_answers", "key_questions", "True", "1"],
          child.stdout + child.stderr[-300:])


# ───────────────────────────── F. launch_i2.sh ─────────────────────────────
def part_f():
    t = tmpdir("i2_launch_")
    runs, stores = t / "runs", t / "stores"
    runs.mkdir()
    log = t / "driver.log"
    (t / "driver.sh").write_text(f"""#!/bin/bash
c=""; prev=""
for x in "$@"; do [ "$prev" = --configs ] && c=$x; prev=$x; done
echo "$c|$DATABASE_URL|$OLLAMA_BASE_URL|$*" >> {log}
code=$(cat {t}/code_$c 2> /dev/null || echo 0)
exit $code
""")
    (t / "mem.sh").write_text(f"#!/bin/bash\nexit $(cat {t}/mem_code 2> /dev/null || echo 0)\n")
    env = {**os.environ, "I2_RUNS_DIR": str(runs), "I2_STORES": str(stores), "I2_DRIVER": f"bash {t}/driver.sh",
           "I2_MEMORY": f"bash {t}/mem.sh", "I2_K1_PATTERN": "^no such k1 pattern i2 check$",
           "I2_JOB_PATTERN": "^no such i2 job pattern$"}
    sh = str(HERE / "launch_i2.sh")

    def launch(*args, extra=None):
        return subprocess.run(["bash", sh, *args], cwd=ROOT, env={**env, **(extra or {})}, capture_output=True, text=True)

    def started():
        return [x.split("|") for x in log.read_text().splitlines()] if log.exists() else []

    configs = ["single_pass", "multi_hop", "rlm_5", "rlm_10", "rlm_20", "verified_pass"]
    for c in configs:
        (stores / c).mkdir(parents=True)
        (stores / c / "clone.sha256").write_text("x\n")
    r = launch("run", "1")
    check("F run is refused without a passed smoke, and starts nothing", r.returncode != 0
          and "no passed smoke" in r.stdout and not started(), r.stdout[-300:])
    r = launch("smoke")
    st = started()
    check("F smoke starts one process: single pass on its own store, --smoke, the no-server URL",
          r.returncode == 0 and len(st) == 1 and st[0][0] == "single_pass" and st[0][1].endswith("/single_pass/mentori_app.db")
          and st[0][2] == "http://127.0.0.1:11499" and "--smoke" in st[0][3], r.stdout + str(st))
    smoke_sink = runs / "smoke_sinks" / "exp_01__single_pass__i2_plant5.smoke"
    smoke_sink.mkdir(parents=True)
    (smoke_sink / "answers.jsonl").write_text(json.dumps({"answer_key": "i2_plant5|single_pass|PB_001|d1",
                                                          "generation": {"error": None}}) + "\n")
    (runs / "i2_generate.jsonl").write_text(json.dumps({"smoke": True, "exit": 0, "memory_ok": False, "start": "s",
                                                        "memory": {"min_free_gb": 1.5}}) + "\n")
    log.unlink()
    r = launch("smoke")
    check("F a second smoke over a stored smoke answer is refused, and starts nothing",
          r.returncode != 0 and "move that sink aside" in r.stdout and not started(), r.stdout[-300:])
    r = launch("run", "1")
    check("F run is refused when the smoke's lowest free memory was under the floor", r.returncode != 0
          and "memory_ok False" in r.stdout and not started(), r.stdout[-300:])
    with open(runs / "i2_generate.jsonl", "a") as f:
        f.write(json.dumps({"smoke": True, "exit": 0, "memory_ok": True, "start": "s2",
                            "memory": {"min_free_gb": 3.1}}) + "\n")
    r = launch("run", "1", "2")
    st = started()
    check("F run starts the five no-server configs one after another, each on its own store, draws 1 2",
          r.returncode == 0 and [s[0] for s in st] == configs[:5]
          and all(s[1].endswith(f"/{s[0]}/mentori_app.db") and "--draws 1 2" in s[3] for s in st), r.stdout + str(st))
    recs = [json.loads(x) for x in (runs / "i2_records.jsonl").read_text().splitlines()]
    check("F each process has a start and an end line in i2_records.jsonl",
          sum("end" in x for x in recs) == sum("end" not in x for x in recs) == 6, str(len(recs)))
    log.unlink()
    (t / "code_rlm_5").write_text("4")
    r = launch("resume")
    st = started()
    check("F a memory stop (exit 4) ends the sequence; resume passes --resume --skip-failed",
          r.returncode == 4 and [s[0] for s in st] == configs[:3] and all("--resume --skip-failed" in s[3] for s in st)
          and "stopped for memory" in r.stdout, r.stdout + str(st))
    (t / "code_rlm_5").unlink()
    log.unlink()
    (t / "mem_code").write_text("3")
    r = launch("run", "1")
    check("F under the memory floor nothing starts", r.returncode != 0 and not started() and "under" in r.stdout,
          r.stdout[-300:])
    (t / "mem_code").unlink()
    r = launch("verified", "1")
    check("F verified is refused without I2_VERIFIER_URL", r.returncode != 0 and "I2_VERIFIER_URL" in r.stdout)
    sleeper = subprocess.Popen(["sleep", "30"])
    try:
        r = launch("verified", "1", extra={"I2_VERIFIER_URL": "http://127.0.0.1:11470", "I2_K1_PATTERN": "^sleep 30$"})
        check("F verified is refused while a K1 launcher runs here", r.returncode != 0 and "K1" in r.stdout
              and not started())
    finally:
        sleeper.kill()
    r = launch("verified", "1", extra={"I2_VERIFIER_URL": "http://127.0.0.1:11470"})
    st = started()
    check("F verified runs verified_pass alone on its own store against the verifier URL",
          r.returncode == 0 and [s[0] for s in st] == ["verified_pass"] and st[0][2] == "http://127.0.0.1:11470",
          r.stdout + str(st))
    r = launch("run", "4")
    check("F a draw other than 1, 2, 3 is refused", r.returncode != 0 and "draw '4'" in r.stdout)

    orig = t / "orig"
    (orig / "chroma_db" / "sub").mkdir(parents=True)
    (orig / "mentori_app.db").write_bytes(b"db")
    (orig / "chroma_db" / "sub" / "x.bin").write_bytes(b"x" * 100)
    st2 = t / "stores2"
    r = launch("stores", extra={"I2_STORES": str(st2), "I2_ORIGINAL": str(orig)})
    made = sorted(p.parent.name for p in st2.glob("*/clone.sha256"))
    check("F stores makes one checked copy per config of the original",
          r.returncode == 0 and made == sorted(configs) and (st2 / "rlm_5/chroma_db/sub/x.bin").read_bytes() == b"x" * 100,
          r.stdout[-300:])
    r = launch("stores", extra={"I2_STORES": str(st2), "I2_ORIGINAL": str(orig)})
    check("F stores again leaves the copies (made already)", r.returncode == 0 and r.stdout.count("made already") == 6)

    k1 = (ROOT / "findings/recompute/K1/run_k1_laptop.sh").read_text()
    stranger = re.search(r"^STRANGER='(.*)'$", k1, re.M).group(1)
    dry = "\n".join(launch(m, "1", extra={"I2_DRY_RUN": "1", "I2_DRIVER": "", "I2_VERIFIER_URL": "http://127.0.0.1:11470"}
                           ).stdout for m in ("smoke", "run", "index-gate", "index-build", "verified"))
    dry_lines = [x for x in dry.splitlines() if "python" in x]
    hits = [x for x in dry_lines if re.search(stranger, x) or re.search(r"\b11434\b", x)]
    check("F no command the launcher starts matches K1's busy-guard pattern or names K1's port (smoke, run, index "
          "builds, verified)", len(dry_lines) >= 9 and not hits, f"{len(dry_lines)} lines; {hits[:2]}")
    check("F the dry run wrote no record", not (runs / "i2_records.jsonl").exists()
          or all("index_" not in x for x in (runs / "i2_records.jsonl").read_text().splitlines()))


# ───────────────────────────── G. i2_signals ─────────────────────────────
def part_g():
    from experiments.reuse_demo import i2_signals as SG
    from experiments.reuse_demo import i2_memory as M
    from experiments.reuse_demo import plant_key as PK
    from experiments.scorers import records as R
    import S470_l1_signals as S470
    saved_kq = R.key_questions
    try:
        _part_g(SG, M, PK, S470)
    finally:
        R.key_questions = saved_kq


def _part_g(SG, M, PK, S470):
    t = tmpdir("i2_signals_")
    key = PK.load()
    answers = {"PB_001": "Three QTLs: qDM2.1 on LG 2b and qDM5.1 on LG 5a from Iceberg; qDM9.1 from Grand Rapids, "
                         "60% to 75% of their effect [02_simko2013_qtl.pdf:p4].",
               "PB_002": "", "PB_003": "BLN08 maps to chromosome 8.",
               "PB_004": "No. Eight F2 populations segregated 3:1; UC07108 and UC12101 9:7.", "PB_005": "Not answerable."}
    rows = [row("i2_plant5", "rlm_10", r["id"], 1, r["question"], answers[r["id"]],
                error=None if answers[r["id"]] else "boom") for r in key.records]
    rows[0]["generation"].update(stop_reason="final", rlm={"metadata": {"turn_limit_note": False}})
    sink = write_sink(t, "exp_01__rlm_10__i2_plant5", rows)
    xs = SG.read_answers([sink], key)
    check("G answers read through records.py with the plant key's groups, stop reason and turn-limit flag",
          [x["group"] for x in xs] == ["answerable", "answerable", "answerable", "false_premise", "not_answerable"]
          and [x["status"] for x in xs] == ["ok", "error", "ok", "ok", "ok"] and xs[0]["stop_reason"] == "final"
          and xs[0]["turn_limit_note"] is False and xs[0]["answer_sha256"] == S470.sha256_text(answers["PB_001"]))
    kv1 = SG.key_as_v1(key)
    q = {x["id"]: x for x in kv1["questions"]}
    check("G the key's v1 form: expected answer as S373.key_of, concepts, answerable, the evidence's papers",
          q["PB_003"]["expected_answer"].endswith(key.v2()["PB_003"]["synthesis_statement"])
          and q["PB_003"]["source_files"] == ["04_giesbers2017_blr31.pdf", "05_pelgrom2019_blr38.pdf"]
          and q["PB_001"]["source_files"] == ["02_simko2013_qtl.pdf"] and q["PB_005"]["answerable"] is False
          and q["PB_002"]["expected_concepts"] == [k["phrase"] for k in key.v2()["PB_002"]["key_concepts"]])
    out = t / "out"
    rc = SG.main(["concepts", "--runs", str(sink), "--out", str(out)])
    cr = [json.loads(x) for x in (out / "concepts.jsonl").read_text().splitlines()]
    hdr = json.loads((out / "concepts_header.json").read_text())
    check("G concepts: gate (S432's 107) passed, a row per answer, the not-answerable one not applicable, the errored "
          "one 0, provisional", rc == 0 and len(cr) == 5 and cr[4]["reason"] == "not applicable"
          and cr[1]["concept_recall_loose"] == 0.0 and hdr["gate"]["reproduced"] == "107 of 107"
          and hdr["provisional"] is True, str(cr[:2])[:300])
    import S471_l3_concept_recall as S471
    want = S471.score(answers["PB_001"], q["PB_001"]["expected_concepts"], False)["concept_recall_loose"]
    check("G concepts: the value is S471.score's on the key's concepts", cr[0]["concept_recall_loose"] == want)
    first = (out / "concepts.jsonl").read_bytes()
    SG.main(["concepts", "--runs", str(sink), "--out", str(out)])
    check("G concepts: a second run writes the same bytes (no time stamp in the rows)",
          (out / "concepts.jsonl").read_bytes() == first)
    rc = SG.main(["numbers", "--runs", str(sink), "--out", str(out)])
    nr = [json.loads(x) for x in (out / "numbers.jsonl").read_text().splitlines()]
    fns = SG.NumberFns(out / "key_as_v1.json")
    check("G numbers: gates passed; number overlap as the deposited score_all and compute_number_overlap give it",
          rc == 0 and nr[0]["signals"]["number_overlap_citation_stripped"]
          == fns.number_overlap_stripped(q["PB_001"]["expected_answer"], answers["PB_001"])
          and nr[1]["detail"]["number_overlap_branch"] == S470.ERROR_BRANCH and nr[1]["signals"]["number_overlap"] == 0.0
          and nr[4]["null_reasons"] == {s: "not applicable" for s in SG.NUMBER_SIGNALS}, str(nr[0])[:300])
    docs = SG.plant_docs(kv1, xs)
    pages = json.loads((SG.TEXT / "02_simko2013_qtl.pdf.pages.json").read_text())
    check("G papers: each question's papers from the key's text files, pages joined with nothing between",
          docs["PB_001"]["text"] == "".join(pages) and docs["PB_003"]["files"] == q["PB_003"]["source_files"]
          and "PB_005" not in docs)
    gd = SG.gate_docs()
    check("G papers: the gate reads the paper's own documents for S19's two gate questions",
          sorted(gd) == sorted({qq for qq, _ in S470.PAPERS_GATE_ROWS}))

    # the MiniCheck stages' loop, with S470's gate and scorers stood in (S470's own checks test those functions)
    saved = (S470.gate_key, S470.key_signals, M.under)
    scored = []

    def fake_signals(x, expected, ns, scorer):
        scored.append(x["question_id"])
        if len(scored) == 3 and "stop" in os.environ.get("CHECK_I2_G", ""):
            raise KeyboardInterrupt
        return {**S470.base_row(x, "key"), "signals": {"precision": 0.5, "recall": 0.5, "f1": 0.5}, "null_reasons": {},
                "detail": {"expected_chars": len(expected)}}
    S470.gate_key = lambda device: ({}, None, {"stub": True}, [{"gate": "stub"}])
    S470.key_signals = fake_signals
    M.under = lambda floor, reading=None: (False, 9.0)
    try:
        os.environ["CHECK_I2_G"] = "stop"
        e = raises(lambda: SG.main(["key", "--runs", str(sink), "--out", str(t / "mc")]), KeyboardInterrupt)
        n1 = len((t / "mc" / "key.jsonl").read_text().splitlines())
        hdr_after_stop = (t / "mc" / "key_header.json").exists()
        os.environ["CHECK_I2_G"] = ""
        rc = SG.main(["key", "--runs", str(sink), "--out", str(t / "mc")])
        kr = [json.loads(x) for x in (t / "mc" / "key.jsonl").read_text().splitlines()]
        check("G key: rows are appended as scored; after a stop the run resumes and scores only the rest",
              e is not None and n1 == 2 and rc == 0 and hdr_after_stop and len(kr) == 5 and scored == [
                  "PB_001", "PB_002", "PB_003", "PB_003", "PB_004", "PB_005"], f"{n1} {len(kr)} {scored}")
        hdr = json.loads((t / "mc" / "key_header.json").read_text())
        hdr["identity"]["device"] = "mps"
        (t / "mc" / "key_header.json").write_text(json.dumps(hdr))
        e = raises(lambda: SG.main(["key", "--runs", str(sink), "--out", str(t / "mc")]), SystemExit)
        check("G key: rows written under another identity (device) are refused", e is not None
              and "another key" in str(e))
        M.under = lambda floor, reading=None: (True, 1.0)
        e = raises(lambda: SG.main(["key", "--runs", str(sink), "--out", str(t / "mc2")]), SystemExit)
        check("G key: refused under the memory floor before MiniCheck loads", e is not None and "memory" in str(e)
              and not (t / "mc2").exists())
    finally:
        S470.gate_key, S470.key_signals, M.under = saved
        os.environ.pop("CHECK_I2_G", None)
    e = raises(lambda: SG.main(["concepts", "--runs", str(sink), "--out", str(t / "o3"), "--key",
                                str(ROOT / "data/ground_truth_v2/all_v2_4.json")]), SystemExit)
    check("G another key without its sha256 is refused", e is not None and "key-sha256" in str(e))


# ───────────────────────────── H. i2_report ─────────────────────────────
def part_h():
    from experiments.reuse_demo import i2_report as IR
    import S463_fig2_ranking as S463
    t = tmpdir("i2_report_")
    rid = "exp_01__rlm_10__i2_plant5"

    def jr(q, d, st, scores=None):
        return {"run_id": rid, "config": "rlm_10", "question_id": q, "draw": d, "a": {"status": st, "scores": scores},
                "b": {"status": "deferred"}}
    rows = [jr("PB_001", 1, "ok", {"correctness": 4}), jr("PB_002", 1, "ok", {"correctness": 3}),
            jr("PB_003", 1, "no_answer"), jr("PB_004", 1, "ok", {"correctness": 4}),
            jr("PB_005", 1, "ok", {"refusal_accuracy": 3}), jr("PB_001", 2, "unparseable"),
            jr("PB_001", 2, "ok", {"correctness": 2}), jr("PB_004", 2, "error")]
    (t / "judge.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    sig = t / "signals"
    sig.mkdir()
    (sig / "concepts.jsonl").write_text(json.dumps({"run_id": rid, "config": "rlm_10", "question_id": "PB_001",
                                                    "draw": 1, "concept_recall_loose": 0.5, "reason": None}) + "\n"
                                        + json.dumps({"run_id": rid, "config": "rlm_10", "question_id": "PB_005",
                                                      "draw": 1, "concept_recall_loose": None,
                                                      "reason": "not applicable"}) + "\n")
    rc = IR.main(["--judge", str(t / "judge.jsonl"), "--signals", str(sig), "--out", str(t / "out")])
    s = json.loads((t / "out" / "i2_summary.json").read_text())
    c = s["counts"]["rlm_10"]
    check("H the rules are Figure 2's, read from S463 (correctness at 4 and 3; refusal_accuracy at 3)",
          s["rules"]["thresholds"] == list(S463.THRESHOLDS) == [4, 3] and s["rules"]["refusal_t"] == S463.REFUSAL_T == 3)
    check("H answerable: the latest row per answer; at 4 one of 4 (PB_001 d1), at 3 two of 4; no_answer counts as not "
          "passed", rc == 0 and c["answerable"]["4"] == [1, 4] and c["answerable"]["3"] == [2, 4], str(c))
    check("H false premise PB_004: 1 of 1 at 4 and 3; its d2 judge error is listed, not counted",
          c["false_premise"]["4"] == [1, 1] and c["false_premise"]["3"] == [1, 1]
          and c["not_counted"] == ["PB_004 d2: error"], str(c))
    check("H not answerable: refused 1 of 1 (refusal_accuracy 3)", c["not_answerable"]["refused"] == [1, 1])
    a = {(x["question_id"], x["draw"]): x for x in s["answers"]}
    check("H each answer's line holds its signals, a null with its reason",
          a[("PB_001", 1)]["signals"] == {"concepts.concept_recall_loose": 0.5}
          and a[("PB_005", 1)]["signals"] == {"concepts.concept_recall_loose": {"null": "not applicable"}})
    first = (t / "out" / "i2_summary.json").read_bytes() + (t / "out" / "i2_report.md").read_bytes()
    IR.main(["--judge", str(t / "judge.jsonl"), "--signals", str(sig), "--out", str(t / "out")])
    check("H the report is the same bytes when built again",
          (t / "out" / "i2_summary.json").read_bytes() + (t / "out" / "i2_report.md").read_bytes() == first)
    md = (t / "out" / "i2_report.md").read_text()
    check("H the markdown has the counts table and no em dash", "| rlm_10 | 1 of 4 | 2 of 4 |" in md and "\u2014" not in md,
          md[:500])


PARTS = {"A": part_a, "B": part_b, "C": part_c, "D": part_d_parent, "E": part_e, "F": part_f, "G": part_g,
         "H": part_h}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", choices=sorted(PARTS))
    a = ap.parse_args()
    if os.environ.get("CHECK_I2_CHILD") == "D":
        part_d_child()
        return 1 if FAILS else 0
    for name in ([a.part] if a.part else sorted(PARTS)):
        PARTS[name]()
    print(f"{N[0] - len(FAILS)} of {N[0]} checks passed" + (f"; FAILED: {FAILS}" if FAILS else ""), flush=True)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
