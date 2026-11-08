"""An offline demo of mentori-cli: no model, no network, no PDF. It shows what a run writes.

    uv run python examples/offline_demo.py            # in a new temporary folder
    uv run python examples/offline_demo.py DIR        # in DIR (it must not hold a mentori.toml)

What is real and what is fake:
  real  `mentori-cli init` (mentori.toml and the 23 prompt files), the prompt edit, the config, the lock check and
        its departures, --strict, the paper's prompt (with the edit put in by inject.py), the paper's own Ollama
        client (experiments/runner/ollama_client.py, with the settings LOCK.toml gives), and the record.
  fake  the model: a small HTTP server on 127.0.0.1 (tests/fake_ollama.py) that answers every request with one canned
        sentence. The search: two invented passages stand in for the store, so no index and no encoder are needed.

It answers one question three times:
  1. as the paper ran it: the record's departs_from_lock is empty;
  2. with [sampling] temperature = 0.2: the run goes ahead and the record lists the departure;
  3. the same with --strict: refused before anything is sent.
At the end it prints where the records are: runs/<run id>/answers.jsonl and calls.jsonl.
"""

from __future__ import annotations

import os
import sys
import tempfile
import json
from pathlib import Path
from types import SimpleNamespace

from mentori_cli import paths
from mentori_cli.engine import MentoriEngine   # neither imports the paper's code

HERE = Path(__file__).resolve().parent
QUESTION = "Which gene does the demo paper link to leaf colour?"
PASSAGES = [   # invented for this demo; ABC1 is not a real gene
    {"id": "demo_p1", "file": "demo_paper.pdf", "page": 1,
     "text": "In this invented example, plants lacking the gene ABC1 had pale yellow leaves."},
    {"id": "demo_p2", "file": "demo_paper.pdf", "page": 2,
     "text": "In this invented example, restoring ABC1 gave green leaves again."},
]
REPLY = "(fake server: no model was called) ABC1 [demo_paper.pdf:1]."


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    root = Path(argv[0]).expanduser().resolve() if argv else Path(tempfile.mkdtemp(prefix="mentori_cli_demo_"))
    # Mentori reads its settings from the environment when its code is first imported: point them into the demo
    # folder, so nothing is opened or written in the repository.
    os.environ.setdefault("DATABASE_URL", f"sqlite:///{root / '.unused.db'}")
    os.environ.setdefault("CHROMA_PERSIST_DIRECTORY", str(root / ".unused_chroma"))
    os.environ.setdefault("WORKSPACE_DIR", str(root / ".unused_workspace"))
    os.environ.setdefault("HF_HUB_OFFLINE", "1")

    from mentori_cli import cli, config, lockfx, runner
    sys.path.insert(0, str(HERE.parent / "tests"))
    from fake_ollama import FakeOllama

    print(f"# 1. mentori-cli init {root}")
    cli.main(["init", str(root)])

    edit = "\nAnswer in at most three sentences.\n"
    f = root / "prompts" / "single_pass.txt"
    f.write_text(f.read_text(encoding="utf-8") + edit, encoding="utf-8")
    print(f"# 2. edited {f}: one line added at the end")

    paper = lockfx.paper_lock(paths.lock_path())[1]
    fake = FakeOllama(paper["server"]["ollama_version"], {k: v["digest"] for k, v in paper["models"].items()},
                      reply=REPLY)
    cfg_file = root / "mentori.toml"
    text = cfg_file.read_text(encoding="utf-8").replace('server_url = "http://127.0.0.1:11434"',
                                                        f'server_url = "{fake.url}"', 1)
    cfg_file.write_text(text, encoding="utf-8")
    print(f"# 3. [model] server_url set to the fake server, {fake.url}")

    engine = DemoEngine()
    cwd = os.getcwd()
    try:
        print("\n# 4. ask, as the paper ran it")
        r1 = runner.ask(config.load(cfg_file), [{"id": "demo1", "question": QUESTION}], engine=engine)

        print("\n# 5. ask with [sampling] temperature = 0.2 (a departure from the lock)")
        cfg = config.load(cfg_file)
        cfg["sampling"]["temperature"] = 0.2
        r2 = runner.ask(cfg, [{"id": "demo2", "question": QUESTION}], engine=engine)

        print("\n# 6. the same with --strict")
        try:
            runner.ask(cfg, [{"id": "demo3", "question": QUESTION}], engine=engine, strict=True)
            refused = None
        except SystemExit as e:
            refused = str(e)
            print(refused)
    finally:
        os.chdir(cwd)
        fake.close()

    print("\n# the records")
    for r in r1 + r2:
        print(f"{r['question_id']}: {Path(r['sink']) / 'answers.jsonl'} (and calls.jsonl beside it); "
              f"departs_from_lock = {r['departs_from_lock']}")
    summary = {"dir": str(root), "records": [r1[0], r2[0]], "strict_refused": refused,
               "requests": len(fake.requests),
               "edit_reached_the_model": [edit.strip() in q["body"].get("prompt", "") for q in fake.requests]}
    (root / "demo_summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"summary: {root / 'demo_summary.json'}")
    return 0


class DemoEngine(MentoriEngine):
    """MentoriEngine with the store left out: the passages are PASSAGES, and the strategy is a small single pass
    that fills the paper's single-pass prompt (as installed, so the edit is in it) and sends it through the paper's
    Ollama client. Installing the lock and the prompts, and writing answers.jsonl, are MentoriEngine's own."""

    def prepare(self, st: dict) -> None:
        if st["strategy"] != "single_pass":
            raise SystemExit("the demo runs strategy single_pass only")
        out_dir = Path(st["out_dir"]).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        os.chdir(out_dir)            # Mentori's logging writes backend/logs/ under the working directory
        paths.setup_sys_path()

    async def run(self, questions: list[dict], st: dict, spec: dict) -> list[dict]:
        import tests.experiments.exp1_rlm_vs_singlepass as exp1
        from experiments.runner import lock as L, ollama_client as oc
        from mentori_cli.runner import dispatch
        out = []
        for n, q in enumerate(questions, 1):
            calls = []

            async def single_pass(question, retriever, collection_name, router, gen):
                text = "\n\n".join(f"[{p['file']}:{p['page']}] {p['text']}" for p in PASSAGES)
                prompt = exp1.SINGLE_PASS_PROMPT.replace("{passages}", text).replace("{question}", question)
                rec = oc.generate(st["server_url"], L.load().ollama(st["name"], draw=st["draw"]), prompt,
                                  passages=[p["id"] for p in PASSAGES])
                calls.append(rec)
                return {"answer": rec["text"], "error": rec["error"], "stop_reason": rec["stop_reason"],
                        "passages": [p["id"] for p in PASSAGES]}

            gen = await dispatch(st, q["question"], SimpleNamespace(single_pass=single_pass), None, "demo", None,
                                 "demo_user", None)
            run_id = f"mentori_cli__demo__{q['id']}"
            sink = Path(st["out_dir"]).resolve() / run_id
            sink.mkdir(parents=True, exist_ok=True)
            with open(sink / "calls.jsonl", "a", encoding="utf-8") as fh:
                for c in calls:
                    fh.write(json.dumps(c, ensure_ascii=False, default=repr) + "\n")
            out.append({"gen": gen, "calls": calls, "run_id": run_id, "sink": str(sink),
                        "sources": [{"id": p["id"], "file": p["file"], "page": p["page"]} for p in PASSAGES]})
        return out


if __name__ == "__main__":
    sys.exit(main())
