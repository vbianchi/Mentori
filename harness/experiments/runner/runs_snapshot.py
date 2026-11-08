"""The findings/runs gate of the offline checks (Q108, D78): did this check write there?

    from experiments.runner import runs_snapshot
    before = runs_snapshot.take()          # at the check's start: every path under findings/runs, with its sha256
    ...                                    # the check, its own sinks in a temporary folder
    runs_snapshot.diff(before, runs_snapshot.take())   # [] when nothing was added, removed or changed

A snapshot maps each path under the folder (relative, '/'-separated) to the sha256 of its bytes, "dir" for a
directory and "link -> <target>" for a symbolic link (never followed); a folder that does not exist is the empty
snapshot. diff names each path added, removed or changed, one line each, sorted. The gate compares the folder
with itself at the check's start, so whatever other jobs left there before the check does not trip it; a job that
writes there while the check runs (G6's sinks, RUNNING.md) does, with the file named.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "findings" / "runs"


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def take(root: Optional[Path] = None) -> Dict[str, str]:
    """Every path under root (default findings/runs) with its sha256, "dir" or "link -> <target>"."""
    root = Path(root) if root is not None else RUNS
    out: Dict[str, str] = {}
    if not root.exists():
        return out
    for dirpath, dirnames, filenames in os.walk(root):
        d = Path(dirpath)
        for name in dirnames + filenames:
            p = d / name
            rel = p.relative_to(root).as_posix()
            if p.is_symlink():
                out[rel] = f"link -> {os.readlink(p)}"
            elif p.is_dir():
                out[rel] = "dir"
            else:
                try:
                    out[rel] = _sha256(p)
                except FileNotFoundError:   # removed between the listing and the read: absent, so diff names it
                    continue
    return out


def diff(before: Dict[str, str], after: Dict[str, str]) -> List[str]:
    """One line per path added, removed or changed between two snapshots, sorted by path; [] when equal."""
    lines = []
    for rel in sorted(set(before) | set(after)):
        if rel not in before:
            lines.append(f"added {rel}")
        elif rel not in after:
            lines.append(f"removed {rel}")
        elif before[rel] != after[rel]:
            lines.append(f"changed {rel}")
    return lines
