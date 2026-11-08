#!/usr/bin/env python3
"""Writes the constraint-dependencies block of tools/mentori_cli/pyproject.toml from experiments/mentori/uv.lock.

    python3 tools/mentori_cli/dev/pin_from_paper_lock.py          # rewrite the block
    python3 tools/mentori_cli/dev/pin_from_paper_lock.py --check  # exit 1 when the block differs from the lock

Every package of the paper's lock (except the virtual project itself) is pinned to the version the paper's code runs
with, so the tool's environment resolves to the same versions. Reads the paper's lock only; writes only pyproject.toml.
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1]
PAPER_LOCK = TOOL.parents[1] / "experiments" / "mentori" / "uv.lock"
PYPROJECT = TOOL / "pyproject.toml"
BEGIN = "# BEGIN pins from experiments/mentori/uv.lock (dev/pin_from_paper_lock.py)"
END = "# END pins"


def pins(lock_path: Path = PAPER_LOCK) -> list[str]:
    d = tomllib.loads(lock_path.read_text(encoding="utf-8"))
    out = []
    for p in d["package"]:
        if "virtual" in (p.get("source") or {}):
            continue
        out.append(f"{p['name']}=={p['version']}")
    return sorted(out)


def block(lock_path: Path = PAPER_LOCK) -> str:
    lines = [BEGIN, "constraint-dependencies = ["]
    lines += [f'    "{p}",' for p in pins(lock_path)]
    lines += ["]", END]
    return "\n".join(lines)


def current_block(text: str) -> str:
    a, b = text.index(BEGIN), text.index(END) + len(END)
    return text[a:b]


def main(argv: list[str]) -> int:
    text = PYPROJECT.read_text(encoding="utf-8")
    want = block()
    if "--check" in argv:
        same = current_block(text) == want
        print("pins match experiments/mentori/uv.lock" if same else "pins differ from experiments/mentori/uv.lock")
        return 0 if same else 1
    PYPROJECT.write_text(text.replace(current_block(text), want), encoding="utf-8")
    print(f"wrote {len(pins())} pins into {PYPROJECT}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
