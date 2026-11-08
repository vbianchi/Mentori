"""Opt-in: the real engine end to end, offline, with a fake Ollama server (tests/fake_ollama.py) and no model.

    MENTORI_CLI_INTEGRATION=1 MENTORI_CLI_TEST_PDF=/path/to/one.pdf uv run pytest tests/test_integration.py

Needs the two encoders in the Hugging Face cache (mentori-cli fetch-encoders) and about 3 GB of free memory: it builds
a one-paper store with bge-m3 on the CPU, then runs `ask` (single pass and multi-hop) through the paper's code, whose
every call goes to the fake server. Skipped otherwise.
"""

import os
import subprocess
import sys
import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(os.environ.get("MENTORI_CLI_INTEGRATION") != "1" or
                                not os.environ.get("MENTORI_CLI_TEST_PDF"),
                                reason="opt-in: MENTORI_CLI_INTEGRATION=1 and MENTORI_CLI_TEST_PDF")

SCRIPT = r'''
import json, os, shutil, sys
from pathlib import Path
sys.path.insert(0, sys.argv[2])
from fake_ollama import FakeOllama
from mentori_cli import config as c, runner, lockfx, paths, indexer
root = Path(sys.argv[1])
pdfs = root / "papers"; pdfs.mkdir()
shutil.copy(os.environ["MENTORI_CLI_TEST_PDF"], pdfs / "01_paper.pdf")
d = lockfx.paper_lock(paths.lock_path())[1]
fake = FakeOllama(d["server"]["ollama_version"], {k: v["digest"] for k, v in d["models"].items()})
rec = indexer.build(pdfs, root / "store", "it_index")
assert rec["ok"], rec
cfg = c.check({"model": {"server_url": fake.url}, "corpus": {"index": "it_index"}, "run": {"prompts_dir": ""}})
cfg["_dir"] = str(root)
out = {}
for strategy in ("single_pass", "multi_hop"):
    recs = runner.ask(cfg, [{"id": "q1", "question": "What does the paper study?"}], strategy=strategy,
                      out=lambda *a: None, environ={})
    out[strategy] = recs[0]
out["requests"] = fake.requests
print("RESULT " + json.dumps(out))
'''


def test_engine_end_to_end_with_a_fake_server(tmp_path):
    tests = Path(__file__).resolve().parent
    r = subprocess.run([sys.executable, "-c", SCRIPT, str(tmp_path), str(tests)], capture_output=True, text=True,
                       cwd=tmp_path, timeout=1800)
    line = next((x for x in r.stdout.splitlines() if x.startswith("RESULT ")), None)
    assert line, r.stdout[-3000:] + r.stderr[-3000:]
    out = json.loads(line[7:])
    for strategy in ("single_pass", "multi_hop"):
        rec = out[strategy]
        assert rec["error"] is None and rec["answer"]
        assert rec["departs_from_lock"] == [] and rec["lock"]["run_sha256"] == rec["lock"]["paper_sha256"]
        s = rec["settings_sent"][0]
        assert s["model"] == "gemma3:27b" and s["options_sent"]["seed"] == 1 and s["status"] == "ok"
        assert rec["sources"] and rec["sources"][0]["file"] == "01_paper.pdf"
    gen = [q for q in out["requests"] if q["path"] == "/api/generate"]
    assert gen and gen[0]["body"]["options"]["top_k"] == 64          # LOCK [sampling.models] gemma3:27b
