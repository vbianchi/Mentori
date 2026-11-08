#!/usr/bin/env python3
"""lock_equiv: is experiments/LOCK.toml D88's lock d66daa28 in every setting a call sends? (D204)

D204 (Valerio, 2 November: "If you need to change the lock or add options to the lock, do it") added the laptop and the
Studio to the second judge's [models] machines ("qwen3.8:27b"). That changes the file's sha256, so every check that
pinned the file at d66daa28 would refuse. Such a check now calls accepts(): the file passes when its parsed TOML equals
the frozen copy experiments/lock_history/LOCK_d66daa28.toml in every key, except [models] "qwen3.8:27b" machines,
which must hold "beelink" and only names from MACHINES. Comments are not settings and are not compared. Any other
difference (a value, a key added or removed, another model's machines, a status) is refused.

Judged rows still carry the sha256 of the lock they were judged under; this module does not change what a row check
accepts. EQUIVALENT lists the sha256 of each lock file proven equivalent here (selftest), for a row check that adopts it.

    uv run python scripts/lock_equiv.py            prints the verdict for experiments/LOCK.toml, exit 1 if refused
    uv run python scripts/lock_equiv.py selftest   mutants: each other change is refused
"""

from __future__ import annotations

import copy
import hashlib
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK_TOML = ROOT / "experiments" / "LOCK.toml"
D88_COPY = ROOT / "experiments" / "lock_history" / "LOCK_d66daa28.toml"
D88_SHA = "d66daa28596bf3b70ff90e0fb89b1353eab023eba699427cb05ebb3376105c12"
SECOND = "qwen3.8:27b"
MACHINES = {"beelink", "laptop", "studio"}
EQUIVALENT = frozenset({D88_SHA, "8730d401a5d7b6baa1780e656f844261eaead60e45b5199afa29d57f989ad495"})


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _d88() -> dict:
    if sha256_file(D88_COPY) != D88_SHA:
        raise SystemExit(f"REFUSED: {D88_COPY.relative_to(ROOT)} is not d66daa28")
    return tomllib.loads(D88_COPY.read_text())


def why_not(text: str) -> str | None:
    """None when text is D88's lock but for the second judge's machines; else the first difference found."""
    try:
        now = tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        return f"not TOML: {e}"
    want = _d88()
    try:
        m = now["models"][SECOND]["machines"]
    except (KeyError, TypeError):
        return f'[models] "{SECOND}" machines missing'
    if not isinstance(m, list) or "beelink" not in m or set(m) - MACHINES or len(set(m)) != len(m):
        return f'[models] "{SECOND}" machines {m!r}: must hold "beelink" and only {sorted(MACHINES)}, once each'
    a, b = copy.deepcopy(now), copy.deepcopy(want)
    a["models"][SECOND]["machines"] = b["models"][SECOND]["machines"] = None
    if a == b:
        return None
    for k in sorted(set(a) | set(b)):
        if a.get(k) != b.get(k):
            if isinstance(a.get(k), dict) and isinstance(b.get(k), dict):
                for j in sorted(set(a[k]) | set(b[k])):
                    if a[k].get(j) != b[k].get(j):
                        return f"[{k}] {j} differs from d66daa28"
            return f"[{k}] differs from d66daa28"
    return "differs from d66daa28"


def accepts(path: Path = LOCK_TOML) -> bool:
    return sha256_file(path) == D88_SHA or why_not(path.read_text()) is None


def selftest() -> int:
    base = D88_COPY.read_text()
    line = f'machines = ["beelink"] }}'
    assert base.count(line) >= 1
    i = base.index(f'\n"{SECOND}"')
    j = base.index(line, i)
    def swap(new: str) -> str:
        return base[:j] + new + base[j + len(line):]
    ok = [swap('machines = ["beelink", "laptop", "studio"] }'), swap('machines = ["beelink", "laptop"] }'), base,
          base.replace("# D85: the second judge", "# D85, a comment changed: the second judge")]
    bad = {"a value": base.replace("num_ctx = 131072", "num_ctx = 65536", 1),
           "the status": base.replace('status = "agreed"', 'status = "draft"', 1),
           "beelink dropped": swap('machines = ["laptop"] }'),
           "an unknown machine": swap('machines = ["beelink", "cloud"] }'),
           "a machine twice": swap('machines = ["beelink", "laptop", "laptop"] }'),
           "another model's machines": base.replace('machines = ["studio"] }', 'machines = ["studio", "laptop"] }', 1),
           "a key added": base.replace("[server]\n", "[server]\nextra = 1\n", 1),
           "the second judge's digest": base.replace("aaee06c39dcf", "aaee06c39dce", 1)}
    n = 0
    for t in ok:
        assert why_not(t) is None, why_not(t)
        n += 1
    for name, t in bad.items():
        assert t != base, name
        assert why_not(t) is not None, f"mutant not refused: {name}"
        n += 1
    cur = LOCK_TOML.read_text()
    assert why_not(cur) is None, f"experiments/LOCK.toml refused: {why_not(cur)}"
    assert sha256_file(LOCK_TOML) in EQUIVALENT, "experiments/LOCK.toml's sha256 is not in EQUIVALENT"
    print(f"lock_equiv selftest: {n} of {n} ({len(ok)} accepted, {len(bad)} mutants refused); LOCK.toml "
          f"{sha256_file(LOCK_TOML)[:8]} accepted")
    return 0


if __name__ == "__main__":
    if sys.argv[1:] == ["selftest"]:
        sys.exit(selftest())
    w = why_not(LOCK_TOML.read_text())
    print(f"LOCK.toml {sha256_file(LOCK_TOML)[:8]}: " + ("same as d66daa28 but for the second judge's machines"
                                                        if w is None else f"REFUSED: {w}"))
    sys.exit(0 if w is None else 1)
