"""examples/offline_demo.py runs end to end offline (fake Ollama server, no model) and writes the records the README
describes. It runs in its own process: the demo installs a lock with a departure into the paper's code in memory."""

import json
import subprocess
import sys
from pathlib import Path

from test_record import FIELDS

DEMO = Path(__file__).resolve().parents[1] / "examples" / "offline_demo.py"


def test_offline_demo(tmp_path):
    d = tmp_path / "demo"
    r = subprocess.run([sys.executable, str(DEMO), str(d)], capture_output=True, text=True, cwd=tmp_path,
                       timeout=600)
    assert r.returncode == 0, r.stdout[-3000:] + r.stderr[-3000:]
    s = json.loads((d / "demo_summary.json").read_text())
    r1, r2 = s["records"]
    assert set(r1) == FIELDS and set(r2) == FIELDS
    assert r1["departs_from_lock"] == [] and r1["lock"]["run_sha256"] == r1["lock"]["paper_sha256"]
    assert r2["departs_from_lock"] and "temperature = 0.2" in r2["departs_from_lock"][0]
    assert r2["lock"]["run_sha256"] != r2["lock"]["paper_sha256"]
    o1, o2 = r1["settings_sent"][0]["options_sent"], r2["settings_sent"][0]["options_sent"]
    assert (o1["temperature"], o1["top_k"], o1["seed"], o1["num_ctx"]) == (1.0, 64, 1, 131072)   # LOCK gemma3:27b
    assert o2["temperature"] == 0.2
    assert r1["prompts"]["edited"] == ["single_pass"] and s["edit_reached_the_model"] == [True, True]
    assert r1["sources"][0] == {"id": "demo_p1", "file": "demo_paper.pdf", "page": 1}
    assert s["strict_refused"] and "nothing was sent" in s["strict_refused"] and s["requests"] == 2
    for rec in (r1, r2):
        sink = Path(rec["sink"])
        line = json.loads((sink / "answers.jsonl").read_text().splitlines()[0])
        assert {k: line[k] for k in FIELDS} == rec and "generation" in line
        call = json.loads((sink / "calls.jsonl").read_text().splitlines()[0])
        assert call["status"] == "ok" and call["model_digest"]
