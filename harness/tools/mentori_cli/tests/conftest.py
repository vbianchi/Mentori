"""Offline tests: no model call, no network. Mentori's settings point into a scratch folder before anything imports
the paper's code, so no test opens or creates a database inside the repository."""

import os
import tempfile
from pathlib import Path

import pytest

_SCRATCH = Path(tempfile.mkdtemp(prefix="mentori_cli_tests_"))
os.environ["DATABASE_URL"] = f"sqlite:///{_SCRATCH / 'unused.db'}"
os.environ["CHROMA_PERSIST_DIRECTORY"] = str(_SCRATCH / "unused_chroma")
os.environ["WORKSPACE_DIR"] = str(_SCRATCH / "unused_workspace")
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ.pop("GEMINI_API_KEY", None)
os.environ.pop("ANTHROPIC_API_KEY", None)

from mentori_cli import lockfx, paths, registry  # noqa: E402

paths.setup_sys_path()


def paper_lock_d() -> dict:
    return lockfx.paper_lock(paths.lock_path())[1]


def fake_state(version=None, tags=None):
    """A fake Ollama server holding the lock's own builds of every model in [models], at the lock's version."""
    d = paper_lock_d()
    st = {"version": version or d["server"]["ollama_version"],
          "tags": {k: v["digest"] for k, v in d["models"].items()}}
    if tags:
        st["tags"].update(tags)
    return st


class Recorder:
    """A fake of the paper's strategy functions: records what each received, returns a GenerationResult-shaped dict."""

    def __init__(self):
        self.calls = []

    def _ret(self, name, **kw):
        self.calls.append((name, kw))
        return {"answer": f"answer by {name}", "error": None, "stop_reason": "ok", "passages": ["p1", "p2"]}

    async def single_pass(self, question, retriever, collection_name, router, gen):
        return self._ret("single_pass", question=question, gen=gen)

    async def multi_hop(self, question, retriever, collection_name, router, gen):
        return self._ret("multi_hop", question=question, gen=gen)

    async def rlm(self, question, router, gen, user_id, **kw):
        return self._ret("rlm", question=question, gen=gen, **kw)

    async def verified_pass(self, question, retriever, collection_name, router, gen):
        return self._ret("verified_pass", question=question, gen=gen)

    async def orchestrator(self, question, user_id, index_name, task_id, switches, collection_name=None):
        return self._ret("orchestrator", question=question, switches=switches, index_name=index_name,
                         task_id=task_id)


FAKE_CALL = {"provider": "ollama", "model": "gemma3:27b", "role": "generator", "status": "ok", "stop_reason": "stop",
             "options_sent": {"temperature": 1.0, "seed": 1, "num_ctx": 131072}, "fields_sent": {"truncate": False},
             "prompt_sent": "THE WHOLE PROMPT", "prompt_tokens": 10, "output_tokens": 5, "lock_sha256": "x",
             "passages": ["p1", "p2"]}


class FakeEngine:
    """MentoriEngine's interface, with the strategy functions faked and no store, server or model."""

    def __init__(self, sink: Path):
        self.sink = Path(sink)
        self.mods = Recorder()
        self.prepared = False
        self.spec = None
        self.stored = []

    def prepare(self, st):
        self.prepared = True

    def paper_prompts(self):
        return {p.name: f"paper prompt {p.name} {{question}}" for p in registry.PROMPTS}

    def install(self, spec):
        self.spec = spec

    async def run(self, questions, st, spec):
        from mentori_cli.runner import dispatch
        out = []
        for q in questions:
            gen = await dispatch(st, q["question"], self.mods, "retriever", "coll", "router", "uid",
                                 "task" if st["strategy"] == "orchestrator" else None)
            out.append({"gen": gen, "calls": [dict(FAKE_CALL)],
                        "sources": [{"id": "p1", "file": "01_a.pdf", "page": 2}], "run_id": "mentori_cli__x__1",
                        "sink": str(self.sink)})
        return out

    def store_record(self, result, record):
        self.stored.append(record)


@pytest.fixture(autouse=True, scope="session")
def _scratch_cwd():
    """Mentori's logging writes under the working directory: the tests run in a scratch folder."""
    old = os.getcwd()
    os.chdir(_SCRATCH)
    yield
    os.chdir(old)


@pytest.fixture
def cfg(tmp_path):
    from mentori_cli import config as c
    d = c.check({})
    d["_dir"] = str(tmp_path)
    (tmp_path / "prompts").mkdir()          # [run] prompts_dir, empty: the paper's prompts
    return d


@pytest.fixture
def engine(tmp_path):
    return FakeEngine(tmp_path / "sink")

