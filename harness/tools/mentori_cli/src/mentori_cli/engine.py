"""The run itself, through the paper's code: the store, the run contexts, the strategy functions, the call records.

Every model call goes through the paper's lock adapter and experiments/runner, as in the paper's runs: each answer runs
inside its own run context (experiments.runner.experiment.context), every call is checked against the lock (the
paper's, or the copy lockfx.py made, installed by inject.py) and written to <sink>/calls.jsonl. The strategies are the
paper's functions: tests/experiments/exp1_rlm_vs_singlepass.py (single pass, multi-hop, RLM, verified pass) and
publication/scripts/exp_03_orchestration_ablation.py _full_orchestrator (the orchestrator, with its tool server).
"""

from __future__ import annotations

import dataclasses
import importlib
import importlib.util
import json
import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace

from mentori_cli import inject, paths, prompts as pr
from mentori_cli.runner import EXPERIMENT, Refused, dispatch

INJECT_FILE = "mentori_cli_inject.json"     # <sink>/: the spec the orchestrator's tool server installs
ANSWERS = "answers.jsonl"                   # <sink>/: one record per answer, appended


def _store_env(store: Path, workdir: Path) -> None:
    """Mentori's settings come from the environment (backend/config.py), read once when backend.config is imported:
    the store's database and Chroma folder, and a workspace folder under the run's out_dir."""
    db, chroma = store / "mentori_app.db", store / "chroma_db"
    if not db.is_file() or not chroma.is_dir():
        raise Refused(f"{store} is not a store (no mentori_app.db and chroma_db); build it with `mentori-cli index`")
    want = {"DATABASE_URL": f"sqlite:///{db}", "CHROMA_PERSIST_DIRECTORY": str(chroma),
            "WORKSPACE_DIR": str(workdir / "workspace")}
    cfg = sys.modules.get("backend.config")
    if cfg is not None and (cfg.settings.DATABASE_URL != want["DATABASE_URL"]
                            or cfg.settings.CHROMA_PERSIST_DIRECTORY != want["CHROMA_PERSIST_DIRECTORY"]):
        raise Refused("Mentori's settings were read before the store was set (backend.config imported too early)")
    os.environ.update(want)


def load_exp03():
    """publication/scripts/exp_03_orchestration_ablation.py, loaded from its file (it is a script, not a package)."""
    name = "mentori_cli_exp03"
    if name in sys.modules:
        return sys.modules[name]
    scripts = paths.mentori() / "publication" / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    spec = importlib.util.spec_from_file_location(name, scripts / "exp_03_orchestration_ablation.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    for attr in ("_full_orchestrator", "_discover_tools", "AGENT_ROLES", "GEN_MODEL"):
        if not hasattr(mod, attr):
            raise Refused(f"exp_03 has no {attr}; this tool was written against the exp_03 that has it")
    return mod


class MentoriEngine:
    def prepare(self, st: dict) -> None:
        out_dir = Path(st["out_dir"]).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        _store_env(Path(st["store"]).resolve(), out_dir)
        os.chdir(out_dir)              # Mentori's logging writes backend/logs/app.log under the working directory
        paths.setup_sys_path()
        import backend.agents.lock_adapter  # noqa: F401  (the lock adapter; puts the repository on sys.path)
        import tests.experiments.exp1_rlm_vs_singlepass  # noqa: F401
        # Mentori's log handler writes each task's log lines to the table task_logs (backend/logging_config.py
        # DatabaseHandler); a store made by build_index.py's init_db has no such table, so it is added to the store
        from sqlmodel import SQLModel
        from backend.database import engine as db_engine
        from backend.models.log import TaskLog
        SQLModel.metadata.create_all(db_engine, tables=[TaskLog.__table__])
        for p in pr.registry.PROMPTS:
            importlib.import_module(p.module)

    def paper_prompts(self) -> dict:
        return pr.paper_prompts()

    def install(self, spec: dict) -> None:
        inject.install(spec)

    def _sources(self, ids: list, collection_name: str) -> list[dict]:
        """Each passage id with its paper (file name) and page, read from the index."""
        if not ids:
            return []
        try:
            from backend.retrieval.vector_store import VectorStore
            col = VectorStore(collection_name=collection_name).get_collection(collection_name)
            got = col.get(ids=list(ids), include=["metadatas"])
            meta = dict(zip(got["ids"], got["metadatas"]))
        except Exception as e:                     # the record keeps the ids whatever the lookup does
            return [{"id": i, "file": None, "page": None, "lookup_error": f"{type(e).__name__}: {e}"} for i in ids]
        return [{"id": i, "file": (meta.get(i) or {}).get("file_name"), "page": (meta.get(i) or {}).get("page")}
                for i in ids]

    async def run(self, questions: list[dict], st: dict, spec: dict) -> list[dict]:
        from backend.agents.model_router import ModelRouter
        from backend.agents.orchestrator import run_records as rr
        from experiments.runner import experiment as ex, index_identity, run_context as rc
        import tests.experiments.exp1_rlm_vs_singlepass as exp1
        from tests.experiments_v4.exp_common import check_index_exists, find_admin_user_id, setup_retriever

        user_id = find_admin_user_id()
        if not check_index_exists(user_id, st["index"]):
            raise Refused(f"index {st['index']!r} is not in {st['store']} or not ready ([corpus] index)")
        retriever, collection_name, _ = setup_retriever(user_id, st["index"])
        router = ModelRouter()
        run = ex.run_id(EXPERIMENT, st["arm"], time.strftime("%Y%m%dT%H%M%S") + f"-{os.getpid()}")
        sink = ex.sink(run, Path(st["out_dir"]).resolve())
        index_identity.record(sink, st["index"], collection_name, script="mentori-cli")
        (sink / INJECT_FILE).write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        thinking = None if st["thinking"] == "default" else "off"
        mods = SimpleNamespace(single_pass=exp1._single_pass_rag, multi_hop=exp1._multi_hop_rag, rlm=exp1._run_rlm,
                               verified_pass=exp1._verified_pass_rag, orchestrator=None)
        models = dict(st["models"])
        stops = exp1.STOPS + (rr.SetupError,)

        async def one(q: dict) -> dict:
            ctx = ex.context(EXPERIMENT, st["arm"], q["id"], st["draw"], models, thinking,
                             base_url=st["server_url"], run=run, sink=sink, judge=False, servers=st["servers"])
            task_id = f"mentori_cli_{q['id']}_d{st['draw']}" if st["strategy"] == "orchestrator" else None
            calls_file = sink / "calls.jsonl"
            start = calls_file.stat().st_size if calls_file.exists() else 0
            t0 = time.time()
            with rc.run(ctx):
                if task_id:
                    rc.dump(task_id)
                try:
                    gen = await dispatch(st, q["question"], mods, retriever, collection_name, router, user_id, task_id)
                except stops as e:        # a lock refusal or a setup error: the run stops, as in the paper's runs
                    raise Refused(f"{q['id']}: {type(e).__name__}: {e}") from e
                except Exception as e:    # the strategy failed: recorded with an empty answer (A5)
                    gen = exp1.failed_answer(st["arm"], st["ident"], e, None, round(time.time() - t0, 3))
            calls = []
            if calls_file.exists():
                with open(calls_file, "rb") as f:
                    f.seek(start)
                    for line in f.read().decode("utf-8").splitlines():
                        c = json.loads(line)
                        if c.get("run_id") == run and c.get("item_id") == q["id"]:
                            calls.append(c)
            ids = getattr(gen, "passages", None) if not isinstance(gen, dict) else None
            if ids is None:               # the orchestrator: every passage its calls carried
                ids = list(dict.fromkeys(p for c in calls for p in (c.get("passages") or [])))
            return {"gen": gen, "calls": calls, "sources": self._sources(ids, collection_name), "run_id": run,
                    "sink": str(sink)}

        if st["strategy"] != "orchestrator":
            return [await one(q) for q in questions]
        exp03 = load_exp03()
        exp03.GEN_MODEL = st["ident"]                     # every role on the one generator, as Figure 4's runs
        models = {role: st["ident"] for role in exp03.AGENT_ROLES}
        st["models"] = dict(models)                       # the record names every role
        mods.orchestrator = exp03._full_orchestrator
        exp03._discover_tools()
        run_ctx = ex.context(EXPERIMENT, st["arm"], None, st["draw"], models, thinking, base_url=st["server_url"],
                             run=run, sink=sink, judge=False)
        if not getattr(ex, "_mentori_cli_launcher", False):
            ex._LAUNCHER = inject.LAUNCHER_PREFIX + ex._LAUNCHER   # the tool server installs the same spec
            ex._mentori_cli_launcher = True
        os.environ.update({inject.ENV_SPEC: str(sink / INJECT_FILE), "MENTORI_CLI_SRC": str(paths.SRC),
                           "MENTORI_CLI_MENTORI": str(paths.mentori()), "MENTORI_CLI_REPO": str(paths.repo())})
        with ex.tool_server(run_ctx):
            return [await one(q) for q in questions]

    def store_record(self, result: dict, record: dict) -> None:
        """<sink>/answers.jsonl: the record, and the strategy's whole result under "generation"."""
        gen = result["gen"] if isinstance(result["gen"], dict) else dataclasses.asdict(result["gen"])
        line = {**record, "generation": json.loads(json.dumps(gen, default=repr))}
        with open(Path(result["sink"]) / ANSWERS, "a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
