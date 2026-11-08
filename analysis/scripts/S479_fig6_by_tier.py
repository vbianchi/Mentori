#!/usr/bin/env python3
"""S479 - Q3 (Valerio, 24 Oct): Figure 6's pass rate by the task's complexity tier. Exploratory, descriptive, no test.

WHY. Valerio, 24 Oct: the coding tasks "were engineered with increased difficulty", so Figure 6 is where a structure
effect that grows with difficulty would show. Tiers are the ground truth's own labels (coder_ground_truth.json v4.0,
`complexity`: simple 6 tasks, medium 8, complex 6); no agent classified them. To be looked at again in the Figure 6 review.

HOW. S447's own loader and design (load_mirror, keep_design; the Q4 lung_9 re-score applied), one draw, 11 variants.
Pass counts by tier for every strategy, each family (free-form, introspection, structured) and all strategies; each
task's pass rate with its tier; and per variant, structured minus free-form by tier, in points.

REPRODUCE FIRST (README.md:75-79): stops unless the design gives Figure 6's 2,420 attempts and 1,660 passes, and every
task in the records has a tier.

Writes findings/recompute/S479_fig6_by_tier.json.

    uv run --project experiments/mentori --frozen python scripts/S479_fig6_by_tier.py
"""
import hashlib
import importlib.util
import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("S447", ROOT / "scripts" / "S447_fig6_panels.py")
S447 = importlib.util.module_from_spec(spec)
sys.modules["S447"] = S447
spec.loader.exec_module(S447)
from S478_fig6_thinking_gap import FAM, GT, MANIFEST, WANT, sha  # noqa: E402  (one family map for both)

OUT = ROOT / "findings/recompute/S479_fig6_by_tier.json"
TIERS = ["simple", "medium", "complex", "all"]


def main():
    tier = {k: o["complexity"] for d in json.loads(GT.read_text())["datasets"].values() for k, o in d["operations"].items()}
    atts, flags, inputs, notes = S447.load_mirror()
    kept, vs, total, left = S447.keep_design(atts)
    got = (len(kept), sum(bool(a["passed"]) for a in kept))
    if got != WANT:
        raise SystemExit(f"design gives {got[0]} attempts and {got[1]} passes, Figure 6 has {WANT}: not reproduced")
    unknown = {a["op_id"] for a in kept} - set(tier)
    if unknown:
        raise SystemExit(f"tasks without a tier: {sorted(unknown)}")
    t = defaultdict(lambda: [0, 0])
    per_var = defaultdict(lambda: [0, 0])
    for a in kept:
        s, k = S447.config_of(a["run_id"]), tier[a["op_id"]]
        for key in ((s, k), (FAM[s], k), ("all", k), (s, "all"), (FAM[s], "all"), ("all", "all")):
            t[key][0] += bool(a["passed"])
            t[key][1] += 1
        per_var[(S447.variant_of(a["run_id"]), FAM[s], k)][0] += bool(a["passed"])
        per_var[(S447.variant_of(a["run_id"]), FAM[s], k)][1] += 1
    pct = lambda c: round(100 * c[0] / c[1], 1)
    groups = ["all", "free-form", "introspection", "structured"] + [s for s, _ in S447.STRATEGIES]
    by_group = {g: {k: {"passes": t[(g, k)], "rate": pct(t[(g, k)])} for k in TIERS} for g in groups}
    po = S447.per_op_counts(kept)
    per_task = [{"task": o, "tier": tier[o], "passes": list(po[o]), "rate": pct(po[o])}
                for o in sorted(po, key=lambda o: (TIERS.index(tier[o]), -po[o][0] / po[o][1]))]
    gap = {v: {k: round(pct(per_var[(v, "structured", k)]) - pct(per_var[(v, "free-form", k)]), 1)
               for k in TIERS[:3]} for v in vs}
    out = {"provenance": {"script": "scripts/S479_fig6_by_tier.py", "script_sha256": sha(Path(__file__)),
                          "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                                                   text=True).stdout.strip(),
                          "manifest": str(MANIFEST.relative_to(ROOT)), "manifest_sha256": sha(MANIFEST),
                          "ground_truth": str(GT.relative_to(ROOT)), "ground_truth_sha256": sha(GT),
                          "q4_lung9_rescore": notes.get("q4_lung9_rescore"),
                          "written_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                          "command": "uv run --project experiments/mentori --frozen python scripts/S479_fig6_by_tier.py"},
           "reproduced": {"attempts": got[0], "passes": got[1]},
           "note": "one draw, descriptive, no test; passes are [passed, attempts]",
           "by_group": by_group, "per_task": per_task, "structured_minus_free_form_per_variant": gap}
    OUT.write_text(json.dumps(out, indent=1, default=str) + "\n")
    print(f"reproduced {got[1]} of {got[0]}; pass rate % ({' / '.join(TIERS)})")
    for g in groups[:4]:
        print(f"  {g:14s}" + "".join(f" {by_group[g][k]['rate']:6.1f}" for k in TIERS))
    print("  structured minus free-form: " + " / ".join(
        f"{by_group['structured'][k]['rate'] - by_group['free-form'][k]['rate']:+.1f}" for k in TIERS[:3]))


if __name__ == "__main__":
    main()
