#!/usr/bin/env python3
"""S519 - D196: the flat wide call's plans, one fixed passage count per index, from token counts only.

WHY. G2's matched budget copied each question's own RLM-10 median (experiments/runner/matched_budget.py), which shows how
hard RLM found that question; no user knows that in advance. D196 fixes one count per index before any answer exists:
    k = round(median RLM-10 input tokens / (median single-pass input tokens / 10))
on G4's draw 1, the 86 answerable questions, at that index. Only `prompt_tokens` is read: no score, no answer text.

Reads the frozen G4 runs (fig3_g4_inputs.tar) through scripts/fig_repro.frozen(), which checks the tar and its files
against findings/recompute/frozen_inputs/SHA256SUMS and members/. Before anything is written, each k must equal D196's
(WANT_K, experiments/README.md, D196). Writes findings/recompute/G10_runs/plans/<index>.json in the form exp_01's
load_budget_plan takes (a top_k for each of the 135) and, beside that folder, S519_plans_provenance.json: this script's
and the tar's sha256, each answers file's sha256 and each plan's. The plans hold no provenance, so their bytes stay the
bytes G10 ran on, and the sidecar sits outside plans/ because run_g10.sh reads that folder.

    uv run --frozen python scripts/S519_flat_wide_plan.py [--out DIR]
    uv run --frozen python scripts/S519_flat_wide_plan.py --check      rebuilds, compares with the committed plans, writes nothing
    uv run --frozen python scripts/S519_flat_wide_plan_test.py
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import fig_repro as FR  # noqa: E402
from experiments.runner import experiment as ex  # noqa: E402

SET = "fig3_g4_inputs"
OUT = ROOT / "findings" / "recompute" / "G10_runs" / "plans"
SIDECAR = "S519_plans_provenance.json"
INDEXES = ("exp_v4_s20_n3", "exp_v4_s50_n3", "exp_v4_s20_n0")
ANSWERABLE = ("factual_recall", "technical", "conceptual", "cross_document", "synthesis")
WANT_K = {"exp_v4_s20_n3": 58, "exp_v4_s50_n3": 92, "exp_v4_s20_n0": 49}     # D196
RULE = "round(median RLM-10 prompt_tokens / (median single-pass prompt_tokens / 10)), G4 draw 1, 86 answerable"


class Refused(Exception):
    """A count differs from D196's, or a plan differs from the committed one."""


def k_of(rlm, sp) -> int:
    return int(rlm / (sp / 10) + 0.5)


def answers_path(cfg: str, idx: str) -> Path:
    return FR.frozen(SET, f"{SET}/runs/exp_02_scaling_factorial__{cfg}__{idx}/answers.jsonl")


def med(path: Path, ans: set) -> tuple:
    """(median prompt_tokens, how many) on draw 1 of the answerable questions, the last line of each answer key."""
    last = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            last[r["answer_key"]] = r
    v = [r["generation"]["prompt_tokens"] for r in last.values() if r["draw"] == 1 and r["question_id"] in ans
         and isinstance((r.get("generation") or {}).get("prompt_tokens"), (int, float))]
    return statistics.median(v), len(v)


def plan_of(idx: str, rlm, sp, n1: int, n2: int, qs: list) -> dict:
    k = k_of(rlm, sp)
    return {"kind": "matched_budget_plan", "flat": True, "decision": "D196", "index": idx, "top_k": k, "rule": RULE,
            "rlm_10_median_prompt_tokens": rlm, "single_pass_median_prompt_tokens": sp, "answers": [n1, n2],
            "questions": {q["id"]: {"top_k": k} for q in qs}}


def plan_text(plan: dict) -> str:
    return json.dumps(plan, indent=1) + "\n"


def build() -> tuple:
    """({index: plan}, {answers file label: sha256}), refused unless every k is D196's."""
    qs = ex.questions()
    if len(qs) != 135:
        raise Refused(f"{len(qs)} questions, not 135")
    ans = {q["id"] for q in qs if q["category"] in ANSWERABLE}
    if len(ans) != 86:
        raise Refused(f"{len(ans)} answerable questions, not 86")
    plans, read = {}, {}
    for idx in INDEXES:
        pr, ps = answers_path("rlm_10", idx), answers_path("single_pass", idx)
        read.update({FR.frozen_label(p): FR.sha256_file(p) for p in (pr, ps)})
        (rlm, n1), (sp, n2) = med(pr, ans), med(ps, ans)
        plans[idx] = plan_of(idx, rlm, sp, n1, n2, qs)
    check_k(plans)
    return plans, read


def check_k(plans: dict, want: dict = WANT_K) -> None:
    got = {i: p["top_k"] for i, p in plans.items()}
    if got != want:
        raise Refused(f"counts {got} are not D196's {want}: nothing written")


def differing(plans: dict, folder: Path) -> list:
    return [i for i, p in plans.items() if not (folder / f"{i}.json").is_file()
            or (folder / f"{i}.json").read_text() != plan_text(p)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, default=OUT, help="the plans' folder; the sidecar goes beside it")
    ap.add_argument("--check", action="store_true", help="compare with the plans in --out; write nothing")
    a = ap.parse_args(argv)
    try:
        plans, read = build()
        if a.check:
            bad = differing(plans, a.out)
            if bad:
                raise Refused(f"plans differ from {a.out}: {bad}")
            print(f"{len(plans)} plans equal {a.out}; counts {[p['top_k'] for p in plans.values()]} are D196's")
            return 0
    except (Refused, FR.FrozenInputError) as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    a.out.mkdir(parents=True, exist_ok=True)
    for idx, p in plans.items():
        (a.out / f"{idx}.json").write_text(plan_text(p))
        print(idx, "k", p["top_k"], "rlm", p["rlm_10_median_prompt_tokens"], "single pass",
              p["single_pass_median_prompt_tokens"], "n", *p["answers"])
    tar = f"{SET}.tar"
    side = {"script": "scripts/S519_flat_wide_plan.py", "script_sha256": FR.sha256_file(Path(__file__)),
            "command": "uv run --frozen python scripts/S519_flat_wide_plan.py", "tar": tar,
            "tar_sha256": FR._read_sums(FR.RECOMPUTE / "frozen_inputs" / "SHA256SUMS")[tar], "answers_sha256": read,
            "rule": RULE, "plans_sha256": {i: FR.sha256_file(a.out / f"{i}.json") for i in plans}}
    (a.out.parent / SIDECAR).write_text(json.dumps(side, indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
