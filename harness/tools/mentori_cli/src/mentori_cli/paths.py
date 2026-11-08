"""Where the paper's code is, and how it is put on sys.path (standard library only)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1]          # tools/mentori_cli/src


def repo() -> Path:
    """The Mentori-reanalysis checkout: MENTORI_REPO when set, else the checkout that holds this file
    (tools/mentori_cli/src/mentori_cli/paths.py, installed editable by uv)."""
    env = os.environ.get("MENTORI_REPO")
    root = Path(env).expanduser().resolve() if env else Path(__file__).resolve().parents[4]
    if not (root / "experiments" / "mentori" / "backend").is_dir() or not (root / "experiments" / "LOCK.toml").is_file():
        raise SystemExit(f"mentori-cli: {root} is not a Mentori-reanalysis checkout (no experiments/mentori or "
                         f"experiments/LOCK.toml); set MENTORI_REPO to the checkout")
    return root


def mentori() -> Path:
    return repo() / "experiments" / "mentori"


def lock_path() -> Path:
    return repo() / "experiments" / "LOCK.toml"


def setup_sys_path() -> None:
    """experiments/mentori first (its packages backend and tests), the repository last (experiments.runner), as the
    paper's own lock adapter orders them (backend/agents/lock_adapter.py appends the repository)."""
    m, r = str(mentori()), str(repo())
    if m not in sys.path:
        sys.path.insert(0, m)
    if r not in sys.path:
        sys.path.append(r)
