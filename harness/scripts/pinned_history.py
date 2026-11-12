#!/usr/bin/env python3
"""pinned_history - O3 (Valerio, 8 November 2026): the files and facts a shipped script used to read from the git history
of Mentori-reanalysis, read instead from copies committed in the tree, each held to the blob id git gave it.

WHY. The release (Mentori-paper/analysis/) is copied from HEAD without .git, and reproduce.py makes it a repository of
one commit, so `git show <commit>:<path>`, `git cat-file blob <commit>:<path>`, a `git log` walk or `git merge-base` on
an earlier commit cannot run there. O3: a shipped script reads no history. Each such read now reads a pinned copy under
findings/recompute/pinned_history/, written by scripts/S617_pin_history.py from git, and the copy is checked here,
every time it is read, against the blob id git recorded for <commit>:<path>: the git blob id of the bytes
(sha1 of b"blob <size>\\0" + bytes, what `git hash-object` prints) must equal it, and so must the sha256 and the size. So
the copy is byte for byte the blob that commit held; that the commit held it, and that a walk listed every commit, is
what S617 recorded from git and what `S617_pin_history.py verify` checks again in Mentori-reanalysis (the release cannot,
having no history).

WHAT IT GIVES (reads only; no git, no model call):
  show(rev, path)        the bytes of path at rev (rev as the script writes it: short or full), from the pinned copy,
                         held to the recorded blob id, sha256 and size; PinError when not pinned or not equal.
  sha256(rev, path)      the recorded sha256 of path at rev; for an entry pinned by hash only (a document whose bytes
                         no shipped script reads, D2), the recorded value, which the release carries and cannot check.
  commit(rev)            the full commit id rev names (as `git rev-parse rev` gave it).
  subject(rev)           the commit's subject line (`git log -1 --format=%s rev`).
  log(path)              the commits `git log --format=%H -- path` listed at pin time, newest first.
  log_paths(name)        the same for a named walk over several paths (main_identities' walk).
  is_ancestor(a, b)      `git merge-base --is-ancestor a b` as recorded at pin time.
  text(b)                b decoded as subprocess's text=True decodes a child's output (for a script that read git
                         show as text).
  blob_id(b)             git's blob id of bytes b.
"""
from __future__ import annotations

import functools
import hashlib
import json
import locale
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIN = ROOT / "findings" / "recompute" / "pinned_history"
INDEX = PIN / "INDEX.json"


class PinError(Exception):
    pass


def _rel(p: Path) -> str:
    try:
        return str(Path(p).relative_to(ROOT))
    except ValueError:
        return str(p)


def blob_id(b: bytes) -> str:
    """git's blob id of b (`git hash-object`), with no git: sha1 of b"blob <len>\\0" + b."""
    return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()


@functools.lru_cache(maxsize=1)
def index() -> dict:
    try:
        return json.loads(INDEX.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise PinError(f"{_rel(INDEX)}: {e}") from None


def entry(rev: str, path: str) -> dict:
    e = index()["files"].get(f"{rev}:{path}")
    if e is None:
        raise PinError(f"{rev}:{path} is not pinned in {_rel(INDEX)} (scripts/S617_pin_history.py)")
    return e


@functools.lru_cache(maxsize=None)
def show(rev: str, path: str) -> bytes:
    """path's bytes at rev, from its pinned copy, held to the blob id, sha256 and size git gave <rev>:<path>."""
    e = entry(rev, path)
    if not e.get("file"):
        raise PinError(f"{rev}:{path} is pinned by sha256 only (no copy is shipped)")
    f = PIN / e["file"]
    try:
        b = f.read_bytes()
    except OSError as x:
        raise PinError(f"{rev}:{path}: pinned copy {_rel(f)}: {x}") from None
    got = {"blob": blob_id(b), "sha256": hashlib.sha256(b).hexdigest(), "size": len(b)}
    bad = {k: (v, e[k]) for k, v in got.items() if v != e[k]}
    if bad:
        raise PinError(f"{rev}:{path}: pinned copy {_rel(f)} is not the blob git recorded: "
                       + "; ".join(f"{k} {a[:12] if isinstance(a, str) else a} != {w[:12] if isinstance(w, str) else w}"
                                   for k, (a, w) in bad.items()))
    return b


def sha256(rev: str, path: str) -> str:
    """The sha256 of path at rev: of the pinned copy (checked by show) when one is shipped, else as recorded."""
    e = entry(rev, path)
    return hashlib.sha256(show(rev, path)).hexdigest() if e.get("file") else e["sha256"]


def text(b: bytes) -> str:
    """b as subprocess.run(..., text=True) gives a child's output: decoded with the locale's encoding (UTF-8 in UTF-8
    mode) and universal newlines, so a script that read `git show` as text reads its pinned copy the same."""
    enc = "utf-8" if sys.flags.utf8_mode else locale.getencoding()
    return b.decode(enc).replace("\r\n", "\n").replace("\r", "\n")


def has(rev: str, path: str) -> bool:
    return f"{rev}:{path}" in index()["files"]


def commit(rev: str) -> str:
    c = index()["commits"].get(rev)
    if c is None:
        raise PinError(f"commit {rev} is not pinned")
    return c["commit"]


def subject(rev: str) -> str:
    c = index()["commits"].get(rev)
    if c is None or "subject" not in c:
        raise PinError(f"the subject of commit {rev} is not pinned")
    return c["subject"]


def log(path: str) -> list:
    w = index()["logs"].get(path)
    if w is None:
        raise PinError(f"the git log of {path} is not pinned")
    return list(w)


def log_paths(name: str) -> dict:
    w = index()["walks"].get(name)
    if w is None:
        raise PinError(f"the walk {name} is not pinned")
    return w


def is_ancestor(a: str, b: str) -> bool:
    v = index()["ancestry"].get(f"{a}..{b}")
    if v is None:
        raise PinError(f"whether {a} is an ancestor of {b} is not pinned")
    return bool(v)
