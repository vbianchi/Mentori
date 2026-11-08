#!/usr/bin/env python3
"""S595 (D260, G20): the reading of G20's four arms on qwen3-coder:30b, by S578 as it stands.

Imports S594 (G20's names on g19_check and S577) and then S578, and sets S578's G20 values: R's S518 source
qwen3-coder (S518_split_confirmation/qwen3-coder.json, S518_inputs/qwen3-coder/collect.jsonl), the judge set
whole:g20 (S593's rows in out_s6_w_g20), the out findings/recompute/G20_reading/, decision D260, the title and the code
note. The reproduce-first steps (S518's stored reading of R's T2 and T2X rows, judged = read, S577's two reproduces),
the table, the contrasts and D249's five hypotheses read descriptively are S578's code.

    uv run --frozen python scripts/S595_g20_reading.py --reproduce-only --r-collect-t2x findings/recompute/S518_inputs/qwen3-coder/t2x_collect.jsonl
    uv run --frozen python scripts/S595_g20_reading.py --runs-root ~/s3_inputs/g20 --r-t2 <sink> --r-t2x <sink> \
        --manifest <g20_stored_R.json> --judge <out_s6_w_g20> --r-collect-t2x <t2xqcoder_collect.jsonl>
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import S594_g20_concept_recall  # noqa: E402,F401  (G20's names on g19_check and S577)
import S578_g19_reading as RD  # noqa: E402

SCRIPT = "scripts/S595_g20_reading.py"


def setup() -> None:
    RD.SCRIPT = SCRIPT
    RD.OUT = ROOT / "findings" / "recompute" / "G20_reading"
    RD.S518_GEMMA3 = ROOT / "findings" / "recompute" / "S518_split_confirmation" / "qwen3-coder.json"
    RD.T2_COLLECT = ROOT / "findings" / "recompute" / "S518_inputs" / "qwen3-coder" / "collect.jsonl"
    RD.SET = "whole:g20"
    RD.S518_SOURCE = "qwen3-coder"
    RD.DECISION = "D260"
    RD.LABEL = RD.CR.LABEL
    RD.TITLE = "G20 reading (D260): qwen3-coder:30b, draw 1, the 46 questions of D239 amended (G19's design)"
    RD.CODE_NOTE = ("R ran at T2's code (the T2 qwen3-coder clone, 73c326a6) and T2X's PIN, A, B and C at G20's PIN, so "
                    "B and C differ from R in code as well as in their switch (G20_runs/README.md).")
    RD.CODE_DEPS = tuple(RD.CODE_DEPS) + ("scripts/S595_g20_reading.py", "scripts/S594_g20_concept_recall.py",
                                          "scripts/S593_g20_judge.py", "findings/recompute/G20_runs/g20_check.py")


setup()


def main(argv=None) -> int:
    return RD.main(argv)


if __name__ == "__main__":
    sys.exit(main())
