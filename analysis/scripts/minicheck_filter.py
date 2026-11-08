#!/usr/bin/env python3
"""minicheck_filter - which of MiniCheck's claims count towards Papers precision. One module for Figures 2 and 5.

WHY. D172 A5-Q1 (experiments/README.md): "MiniCheck's claims drop the numbered source list and headings at the
end of RLM answers, stated in Methods." S470 scores every claim its decomposition yields, source-list lines included
(S470_l1_signals.py:599-623), so the stored precision counts them. Build spec: fig5.md section 7, reader R3.

WHAT THE CODE DOES.
  source_list_line(claim)  True when SOURCE_LIST matches the start of the claim's text, case ignored. It reads the text
                           of one claim only: not its place in the answer and not the strategy, so a matching claim
                           counts anywhere in an answer and for every strategy (fig5.md:36).
  kept(claim)              False for a source-list line or for a claim HEADING_RULE calls a heading, else True.
  precision(per_claim)     Supported claims over kept claims, rounded to 4 dp as S470_l1_signals.py:619, or None when
                           no claim is left. per_claim is a row's detail.per_claim; each item's "claim" and "supported"
                           are read. A row with no detail.per_claim (S470 stored a null) is not for this function: the
                           caller keeps that row's null and its stored reason.
  precision_and_reason(per_claim)  The same value, with NO_CLAIM_LEFT as the reason when it is None, else None.

HEADING_RULE IS no_heading (D245, under D207 (2), experiments/README.md). Valerio's ruling of 4 November: S563's 203
rules reversed no pair of strategies, so Papers is reported with no heading filter, and the range across rules goes to
a supplementary table. no_heading calls no claim a heading, so kept() drops only source-list lines. HEADING_RULE is a
callable, claim text to bool, True for a heading. The refusal stays: were HEADING_RULE set back to None, kept(),
precision() and precision_and_reason() would print why and exit 2. A test uses a fixture rule by assigning one to
this module's HEADING_RULE and putting the module's original value back afterwards.

THE GATE. `gate` does not call HEADING_RULE (it runs with the rule unset too), since it needs only the source-list part. It reads the 28 October L1 papers
rows through fig_repro.frozen() and check_committed() (each file's sha256 against frozen_inputs/SHA256SUMS), and uses
the rows with group "answerable" and a stored precision. It refuses, with exit 2 and nothing written, on any of:
  - a row of the folder that is not G1's: index INDEX, run exp_01__<config>__INDEX, one of the six strategies, draw 1;
  - an answer_key in two rows, a used row with no detail.per_claim, a strategy with no used row;
  - a used row whose detail.per_claim does not give its stored precision by S470's ratio (the known number first);
  - a share that differs from SOURCE_SHARE_PIN at 3 dp.
The share of one strategy is the mean over its used answers of (source-list lines / claims in that answer), as
a07/srclist.py computes it. The gate reports shares only: it computes no precision on the filtered claims.

Writes findings/recompute/minicheck_filter_gate.json: the six shares against their pins, the row counts, and
provenance (script, its sha256, time, git head, command, sha256 of each row file). Reads only that folder and
frozen_inputs/SHA256SUMS. No model call.

    uv run --frozen python scripts/minicheck_filter.py gate
"""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

REPO = Path(__file__).resolve().parents[1]
SCRIPT = "scripts/minicheck_filter.py"
GATE_OUT = REPO / "findings" / "recompute" / "minicheck_filter_gate.json"

# fig5.md:217, R3. The same pattern as findings/scratch_archive/2026-10-30/scripts/a07/srclist.py:9.
SOURCE_LIST = re.compile(r"^\s*(\[\d+\]|\d+\.\s+\S+\.pdf|sources?\b|references?\b|##)", re.I)


def no_heading(claim: str) -> bool:
    """no heading filter (D245)"""
    return False


HEADING_RULE = no_heading   # D245 (Valerio, 4 November), D207 (2): no heading filter; the source-list filter is unchanged

NO_CLAIM_LEFT = "no claim left after the source-list and heading filter"
UNSET = ("minicheck_filter: HEADING_RULE is unset. What counts as a heading is Valerio's ruling (Q1, build_order.md "
         "section 9; D245 set it to no_heading), and no filtered Papers value exists without it.")

SET, PAPERS = "fig5_1028", "l1/papers"
INDEX = "exp_v4_s20_n0"
CONFIGS = ("single_pass", "multi_hop", "verified_pass", "rlm_5", "rlm_10", "rlm_20")
# fig5.md:217, the gate on the 28 October rows: the known values this script must reproduce, not results of it.
SOURCE_SHARE_PIN = {"single_pass": 0.000, "multi_hop": 0.001, "verified_pass": 0.001,
                    "rlm_5": 0.338, "rlm_10": 0.338, "rlm_20": 0.350}


class GateFail(Exception):
    """The gate refused: exit 2, nothing written."""


def _load_fig_repro():
    spec = importlib.util.spec_from_file_location("fig_repro", REPO / "scripts" / "fig_repro.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


FR = _load_fig_repro()


def _need_rule():
    if HEADING_RULE is None:
        print(UNSET, file=sys.stderr)
        sys.exit(2)


def source_list_line(claim: str) -> bool:
    return SOURCE_LIST.match(claim) is not None


def kept(claim: str) -> bool:
    _need_rule()
    return not (source_list_line(claim) or HEADING_RULE(claim))


def _supported_share(per_claim: list) -> float:
    """S470_l1_signals.py:619."""
    return round(sum(1 for c in per_claim if c["supported"]) / len(per_claim), 4)


def precision_and_reason(per_claim: list) -> tuple:
    _need_rule()
    left = [c for c in per_claim if kept(c["claim"])]
    if not left:
        return None, NO_CLAIM_LEFT
    return _supported_share(left), None


def precision(per_claim: list):
    return precision_and_reason(per_claim)[0]


def frozen_papers() -> Path:
    return FR.check_committed(FR.frozen(SET, PAPERS))


def read_rows() -> list:
    rows = []
    for f in sorted(frozen_papers().glob("*.jsonl")):
        with f.open() as fh:
            rows += [json.loads(line) for line in fh if line.strip()]
    return rows


def used(row: dict) -> bool:
    return row["group"] == "answerable" and row["signals"].get("precision") is not None


def gate(rows: list, pin: dict = SOURCE_SHARE_PIN) -> dict:
    """The result of the module docstring's gate, or GateFail."""
    seen = Counter(r["answer_key"] for r in rows)
    twice = [k for k, n in seen.items() if n > 1]
    if twice:
        raise GateFail(f"{len(twice)} answer_keys in two rows, first {twice[0]}")
    foreign = [r["answer_key"] for r in rows
               if r["config"] not in CONFIGS or r["draw"] != 1 or r["answer_key"].split("|")[0] != INDEX
               or r["run_id"] != f"exp_01__{r['config']}__{INDEX}"]
    if foreign:
        raise GateFail(f"{len(foreign)} rows are not one of the rows of this gate, first {foreign[0]}")
    use = [r for r in rows if used(r)]
    empty = [r["answer_key"] for r in use if not (r.get("detail") or {}).get("per_claim")]
    if empty:
        raise GateFail(f"{len(empty)} rows hold a value with no detail.per_claim, first {empty[0]}")
    wrong = [r["answer_key"] for r in use if _supported_share(r["detail"]["per_claim"]) != r["signals"]["precision"]]
    if wrong:
        raise GateFail(f"{len(wrong)} rows' per_claim does not give the stored precision, first {wrong[0]}")
    shares, off = {}, []
    for c in CONFIGS:
        per = [[source_list_line(x["claim"]) for x in r["detail"]["per_claim"]] for r in use if r["config"] == c]
        if not per:
            raise GateFail(f"no used row for {c}")
        share = mean(sum(p) / len(p) for p in per)
        shares[c] = {"answers": len(per), "claims": sum(map(len, per)), "source_list_lines": sum(map(sum, per)),
                     "share": share, "share_3dp": round(share, 3), "fig5_217": pin[c]}
        if round(share, 3) != pin[c]:
            off.append(f"{c} {round(share, 3)}, pinned {pin[c]}")
    if off:
        raise GateFail("share of claims dropped differs from fig5.md:217: " + "; ".join(off))
    return {"passed": True, "rows": {"read": len(rows), "used": len(use)},
            "stored_precision_reproduced": {"equal": len(use), "of": len(use)}, "source_list_share": shares}


def run_gate(rows: list, out: Path) -> int:
    try:
        res = gate(rows)
    except GateFail as e:
        print(f"minicheck_filter gate REFUSED: {e}; nothing written", file=sys.stderr)
        return 2
    d = frozen_papers()
    inputs = {f.relative_to(REPO).as_posix(): FR.sha256_file(f) for f in sorted(d.glob("*.jsonl"))}
    head = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    rec = {"_provenance": {"script": SCRIPT, "script_sha256": FR.sha256_file(REPO / SCRIPT),
                           "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "git_head": head,
                           "command": f"uv run --frozen python {SCRIPT} gate", "inputs_sha256": inputs},
           **res}
    Path(out).write_text(json.dumps(rec, indent=1) + "\n")
    print(f"gate passed: {res['rows']['used']} of {res['rows']['read']} rows used, stored precision reproduced on "
          f"{res['stored_precision_reproduced']['equal']}")
    for c, x in res["source_list_share"].items():
        print(f"  {c:14} answers {x['answers']:3}  share dropped {x['share_3dp']:.3f}  fig5:217 {x['fig5_217']:.3f}")
    print(f"wrote {Path(out).relative_to(REPO) if Path(out).is_relative_to(REPO) else out}")
    return 0


def main(argv: list) -> int:
    if argv != ["gate"]:
        print("usage: uv run --frozen python scripts/minicheck_filter.py gate", file=sys.stderr)
        return 2
    return run_gate(read_rows(), GATE_OUT)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
