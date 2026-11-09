#!/usr/bin/env python3
"""S575 (D240, G17): paired contrasts of G17's arms against the control and against the package RLM.

S571 --g17 tabulates each arm (medians and pass shares); it tests nothing. This reads S571's per-answer rows
(findings/recompute/S571_rlm_reading/g17/g17_reading.json, which already carries S572's judge score and S573's concept
recall for every answer) and, for each pair of arms, takes the per-question difference on the same question (draw 1,
one answer per arm and question) of pass at 4 and of concept recall, then reports their mean with the 95% percentile
interval from 10,000 question resamples and the exact two-sided sign-flip test, as Figure 3's contrasts do (S463
interval and signflip_p, Rules 2 and 3: default_rng(20261013)). Questions: all 86, and the 60 one-paper and 26
many-paper apart. A failed answer passes nothing and scores concept recall 0 (Rule 10, as S571 and S573 read it).

REPRODUCE FIRST (README.md:75-79): every arm's pass share at 4 and mean concept recall from these rows must equal what
S571's table and S573's header.json state, or nothing is written.

    uv run --frozen python scripts/S575_g17_contrasts.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from fractions import Fraction
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))
import S463_fig2_ranking as S463  # noqa: E402

IN = ROOT / "findings/recompute/S571_rlm_reading/g17/g17_reading.json"
CR_HEADER = ROOT / "findings/recompute/G17_concept_recall/header.json"
OUT = ROOT / "findings/recompute/S575_g17_contrasts"
ARMS = {"ctrl": "rlm_10_ctrl", "search_off": "rlm_10_nosearch", "gate_off": "rlm_10_nogate",
        "package": "cap10", "g1": "rlm_10"}
PAIRS = [("search_off", "ctrl"), ("gate_off", "ctrl"), ("package", "ctrl"), ("g1", "ctrl"),
         ("search_off", "package"), ("gate_off", "package")]
GROUPS = ("all", "one", "many")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def values(rows: list, arm: str) -> dict:
    out = {}
    for r in rows:
        if r["strategy"] != ARMS[arm] or r["draw"] != 1:
            continue
        if r["question_id"] in out:
            raise SystemExit(f"REFUSED: two draw-1 answers of {arm} to {r['question_id']}")
        cr = r.get("concept_recall")
        out[r["question_id"]] = {"group": r["group"], "pass4": 0 if r.get("failed") else int(r.get("pass4") or 0),
                                 "cr": 0.0 if r.get("failed") else float(cr if cr is not None else 0.0)}
    return out


def reproduce(d: dict, v: dict) -> list[str]:
    bad = []
    hdr = json.loads(CR_HEADER.read_text())["means"]
    for arm, s in ARMS.items():
        for g in GROUPS:
            qs = [q for q, x in v[arm].items() if g == "all" or x["group"] == g]
            p4 = 100 * sum(v[arm][q]["pass4"] for q in qs) / len(qs)
            row = next(t for t in d["table"] if t["strategy"] == s and t["group"] == g)
            if abs(p4 - row["pass4_pct"]) > 1e-9:
                bad.append(f"{arm} {g} pass4 {p4:.4f} vs S571 {row['pass4_pct']}")
            key = f"{s}|{g}"
            if key in hdr and abs(sum(v[arm][q]["cr"] for q in qs) / len(qs) - hdr[key]["mean_concept_recall"]) > 1e-6:
                bad.append(f"{arm} {g} concept recall vs S573")
    return bad


def contrast(a: dict, b: dict, g: str, metric: str) -> dict:
    qs = sorted(q for q in a if q in b and (g == "all" or a[q]["group"] == g))
    diffs = [a[q][metric] - b[q][metric] for q in qs]
    n = len(qs)
    lo, hi = S463.interval(diffs, [1.0] * n)
    p = S463.signflip_p([Fraction(x).limit_denominator(100000) for x in diffs])
    scale = 100 if metric == "pass4" else 1
    return {"n_questions": n, "mean_a": scale * sum(a[q][metric] for q in qs) / n,
            "mean_b": scale * sum(b[q][metric] for q in qs) / n, "diff": scale * sum(diffs) / n,
            "ci95": [scale * lo, scale * hi], "p_two_sided": p,
            "a_higher": sum(x > 0 for x in diffs), "b_higher": sum(x < 0 for x in diffs)}


def main() -> int:
    d = json.loads(IN.read_text())
    if not (d.get("judged") and d.get("concept_recall_given")):
        raise SystemExit("REFUSED: S571's G17 reading lacks the judge or concept recall")
    v = {arm: values(d["answers"], arm) for arm in ARMS}
    for arm, x in v.items():
        if len(x) != 86:
            raise SystemExit(f"REFUSED: {arm} has {len(x)} draw-1 answers, not 86")
    bad = reproduce(d, v)
    print(f"  {'ok  ' if not bad else 'FAIL'}  REPRODUCE pass at 4 and mean concept recall per arm and group equal "
          f"S571 and S573{'' if not bad else ': ' + '; '.join(bad)}")
    if bad:
        print("NOTHING WRITTEN")
        return 1
    res = {"_provenance": {"script": "scripts/S575_g17_contrasts.py",  # no run time or git head (S608, 9 Nov): a rerun of the same code on the same inputs is byte-equal
                           "inputs_sha256": {str(IN.relative_to(ROOT)): sha(IN),
                                             str(CR_HEADER.relative_to(ROOT)): sha(CR_HEADER)},
                           "code_sha256": sha(Path(__file__)), "boot": S463.N_BOOT, "seed": S463.SEED,
                           "decision": "D240"},
           "contrasts": []}
    for a, b in PAIRS:
        for g in GROUPS:
            for m in ("pass4", "cr"):
                res["contrasts"].append({"a": a, "b": b, "group": g, "metric": m, **contrast(v[a], v[b], g, m)})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "contrasts.json").write_text(json.dumps(res, indent=1) + "\n")
    L = ["# S575: G17's paired contrasts (D240), draw 1, a minus b per question", "",
         f"Generated by `uv run --frozen python scripts/S575_g17_contrasts.py` (code sha256 "
         f"{res['_provenance']['code_sha256'][:12]}). Pass at 4 in percentage points, concept recall as a share; "
         "95% percentile interval over 10,000 question resamples (seed 20261013); exact two-sided sign-flip P.", "",
         "| a | b | questions | metric | n | mean a | mean b | a - b | 95% interval | P | a higher | b higher |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in res["contrasts"]:
        f = "{:.1f}" if c["metric"] == "pass4" else "{:.3f}"
        L.append(f"| {c['a']} | {c['b']} | {c['group']} | {c['metric']} | {c['n_questions']} | {f.format(c['mean_a'])} | "
                 f"{f.format(c['mean_b'])} | {f.format(c['diff'])} | {f.format(c['ci95'][0])} to "
                 f"{f.format(c['ci95'][1])} | {c['p_two_sided']:.3g} | {c['a_higher']} | {c['b_higher']} |")
    (OUT / "contrasts.md").write_text("\n".join(L) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}/contrasts.{{json,md}} ({len(res['contrasts'])} contrasts)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
