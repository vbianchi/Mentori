#!/usr/bin/env python3
"""S594 (D260, G20): concept recall of G20's four arms R, A, B, C on qwen3-coder:30b, by S577 as it stands.

Imports findings/recompute/G20_runs/g20_check.py (which gives g19_check G20's model and run names) and then S577, and
sets S577's script name, out (findings/recompute/G20_concept_recall/) and decision (D260). The reading, the reproduce-
first steps (exp_01 path = L3_d181, package path = L2_d181) and every refusal are S577's. R is read from qwen3-coder's T2
and T2X sinks, each line held to g20_stored_R.json. header.json gains this file's and g20_check.py's sha256.

    uv run --frozen python scripts/S594_g20_concept_recall.py --reproduce-only
    uv run --frozen python scripts/S594_g20_concept_recall.py --runs-root ~/s3_inputs/g20 --r-t2 <T2 sink> \
        --r-t2x <T2X sink> --manifest <g20_stored_R.json>
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
G20 = ROOT / "findings" / "recompute" / "G20_runs"
for p in (str(SCRIPTS), str(ROOT), str(G20)):
    if p not in sys.path:
        sys.path.insert(0, p)

import g20_check  # noqa: E402,F401  (installs G20's names on g19_check before S577 reads them)
import S577_g19_concept_recall as CR  # noqa: E402

SCRIPT = "scripts/S594_g20_concept_recall.py"


def setup() -> None:
    CR.SCRIPT = SCRIPT
    CR.OUT = ROOT / "findings" / "recompute" / "G20_concept_recall"
    CR.DECISION = "D260"
    CR.LABEL = {**CR.LABEL, "R": "R Mentori RLM-10 (stored, qwen3-coder:30b)"}


setup()


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    rc = CR.main(argv)
    out = Path(argv[argv.index("--out") + 1]) if "--out" in argv else CR.OUT
    h = out / "header.json"
    if rc == 0 and "--reproduce-only" not in argv and h.exists():
        d = json.loads(h.read_text())
        d["wrapper"] = {"script": SCRIPT, "sha256": sha(Path(__file__)), "wraps": "scripts/S577_g19_concept_recall.py",
                        "findings/recompute/G20_runs/g20_check.py": sha(G20 / "g20_check.py")}
        h.write_text(json.dumps(d, indent=1, sort_keys=True) + "\n")
    return rc


if __name__ == "__main__":
    sys.exit(main())
