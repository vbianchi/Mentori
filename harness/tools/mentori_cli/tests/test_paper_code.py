"""The paper's code is not changed by a byte, and the tool's environment pins the paper's package versions."""

import subprocess
import sys
import tomllib
from pathlib import Path

from mentori_cli import inject, paths

TOOL = Path(__file__).resolve().parents[1]
PAPER = ("experiments/mentori", "experiments/runner")


def git(*args):
    return subprocess.run(["git", "--no-optional-locks", *args], cwd=paths.repo(), capture_output=True, text=True)


def test_paper_code_unchanged():
    r = git("diff", "--quiet", "HEAD", "--", *PAPER)
    assert r.returncode == 0, git("diff", "--stat", "HEAD", "--", *PAPER).stdout
    status = git("status", "--porcelain", "--untracked-files=all", "--", *PAPER).stdout
    assert status == "", status                     # no new file either (ignored files such as .venv aside)


def test_pins_are_the_paper_lock():
    sys.path.insert(0, str(TOOL / "dev"))
    import pin_from_paper_lock as pins
    text = (TOOL / "pyproject.toml").read_text(encoding="utf-8")
    assert pins.current_block(text) == pins.block()


def test_resolved_versions_are_the_papers():
    paper = tomllib.loads((paths.mentori() / "uv.lock").read_text(encoding="utf-8"))
    tool = tomllib.loads((TOOL / "uv.lock").read_text(encoding="utf-8"))
    pv = {p["name"]: p["version"] for p in paper["package"] if "virtual" not in p.get("source", {})}
    tv = {p["name"]: p.get("version") for p in tool["package"]}
    differ = {k: (pv[k], tv[k]) for k in pv if k in tv and tv[k] != pv[k]}
    assert differ == {}
    extra = sorted(k for k in tv if k not in pv and k not in ("mentori", "mentori-cli"))
    assert all(k.startswith(("cuda-", "nvidia-")) for k in extra), extra   # platform wheels only


def test_launcher_prefix_keeps_the_runner_launcher():
    from experiments.runner import experiment as ex
    assert "{" not in inject.LAUNCHER_PREFIX and "}" not in inject.LAUNCHER_PREFIX
    paper = ex._LAUNCHER.format(mentori="/m")
    assert (inject.LAUNCHER_PREFIX + ex._LAUNCHER).format(mentori="/m") == inject.LAUNCHER_PREFIX + paper
    compile(inject.LAUNCHER_PREFIX + paper, "<launcher>", "exec")


def test_no_em_dash_in_the_tool():
    bad = [str(f) for f in TOOL.rglob("*") if f.is_file() and ".venv" not in f.parts and "__pycache__" not in f.parts
           and f.suffix in (".py", ".md", ".toml", ".txt") and chr(0x2014) in f.read_text(encoding="utf-8")]
    assert bad == []
