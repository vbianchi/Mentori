#!/usr/bin/env python3
"""S478 - O1 (Valerio, 24 Oct): does more thinking narrow Figure 6's structured gap? Exploratory, descriptive, no test.

WHY. Sinha et al. (ICLR 2026, reference 28) find per-step accuracy falls over many steps as models condition on their own
errors, and that thinking removes the effect. Their prediction for Figure 6: a structured variant (coder_v2_*, the work
split over notebook cells) trails free-form less with more thinking. Valerio, 24 Oct: "Yes go ahead"; to be looked at
again in the Figure 6 review.

HOW. S447's own loader and design (load_mirror, keep_design; the Q4 lung_9 re-score applied), one draw. The design holds
no local model with thinking off; its thinking pairs are gemini-3-flash-preview and gemini-2.5-pro off against default,
and gpt-oss-20b low, medium, high. Per variant and complexity tier (coder_ground_truth.json): passes of the structured,
introspection and free-form families, structured minus free-form and introspection minus free-form in points, and the
structured failures by S447's fail_kind (with S447's end flags).

REPRODUCE FIRST (README.md:75-79): stops unless the design gives Figure 6's 2,420 attempts and 1,660 passes.

Writes findings/recompute/S478_fig6_thinking_gap.json.

    uv run --project experiments/mentori --frozen python scripts/S478_fig6_thinking_gap.py
"""
import hashlib
import importlib.util
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("S447", ROOT / "scripts" / "S447_fig6_panels.py")
S447 = importlib.util.module_from_spec(spec)
sys.modules["S447"] = S447
spec.loader.exec_module(S447)

GT = ROOT / "experiments/mentori/tests/experiments_v2/datasets/coder_ground_truth.json"
MANIFEST = ROOT / "findings/figures_provisional/fig6/records_manifest.json"
OUT = ROOT / "findings/recompute/S478_fig6_thinking_gap.json"
WANT = (2420, 1692)                      # Figure 6 after S4's 165 reruns (D201 Q2): S525_fig6_s4_check.json's new
#                                          totals, the 2,255 attempts off the list equal to the copy before S4, which
#                                          gave (2420, 1660) after Q4 (254ded7); S525 holds that number on the old tar
FAM = {"free_form": "free-form", "free_form_n3_best": "free-form", "free_form_n3_combined": "free-form",
       "error_recovery_introspect": "introspection", "introspect_then_code": "introspection",
       "introspect_with_recovery": "introspection", "thinker_coder_split": "introspection",
       "coder_v2_n1": "structured", "coder_v2_n1_cell3_best": "structured",
       "coder_v2_n1_cell3_combined": "structured", "coder_v2_n3": "structured"}
PAIRS = ["gemini-3-flash-preview+off", "gemini-3-flash-preview+default", "gemini-2.5-pro+off", "gemini-2.5-pro+default",
         "gpt-oss-20b+low", "gpt-oss-20b+medium", "gpt-oss-20b+high"]
TIERS = ["simple", "medium", "complex", "all"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    tier = {k: o["complexity"] for d in json.loads(GT.read_text())["datasets"].values() for k, o in d["operations"].items()}
    atts, flags, inputs, notes = S447.load_mirror()
    kept, vs, total, left = S447.keep_design(atts)
    got = (len(kept), sum(bool(a["passed"]) for a in kept))
    if got != WANT:
        raise SystemExit(f"design gives {got[0]} attempts and {got[1]} passes, Figure 6 has {WANT}: not reproduced")
    missing = [v for v in PAIRS if v not in vs]
    if missing:
        raise SystemExit(f"variants not in the design: {missing}")
    t = defaultdict(lambda: [0, 0])
    kinds = defaultdict(Counter)
    for a in kept:
        v, f = S447.variant_of(a["run_id"]), FAM[S447.config_of(a["run_id"])]
        for k in (tier[a["op_id"]], "all"):
            t[(v, f, k)][0] += bool(a["passed"])
            t[(v, f, k)][1] += 1
        if f == "structured" and not a["passed"]:
            kinds[v][S447.fail_kind(a, flags.get(a.get("ctx_uid"), set()))] += 1
    rate = lambda v, f, k: 100 * t[(v, f, k)][0] / t[(v, f, k)][1]
    rows = {}
    for v in PAIRS:
        rows[v] = {k: {"passes": {f: t[(v, f, k)] for f in ("structured", "introspection", "free-form")},
                       "structured_minus_free_form": round(rate(v, "structured", k) - rate(v, "free-form", k), 1),
                       "introspection_minus_free_form": round(rate(v, "introspection", k) - rate(v, "free-form", k), 1)}
                   for k in TIERS}
        rows[v]["structured_fail_kinds"] = dict(kinds[v].most_common())
    out = {"provenance": {"script": "scripts/S478_fig6_thinking_gap.py", "script_sha256": sha(Path(__file__)),
                          "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                                                   text=True).stdout.strip(),
                          "manifest": str(MANIFEST.relative_to(ROOT)), "manifest_sha256": sha(MANIFEST),
                          "ground_truth": str(GT.relative_to(ROOT)), "ground_truth_sha256": sha(GT),
                          "q4_lung9_rescore": notes.get("q4_lung9_rescore"),
                          "written_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                          "command": "uv run --project experiments/mentori --frozen python scripts/S478_fig6_thinking_gap.py"},
           "reproduced": {"attempts": got[0], "passes": got[1]},
           "note": "one draw, descriptive, no test; passes are [passed, attempts]",
           "variants": rows}
    OUT.write_text(json.dumps(out, indent=1, default=str) + "\n")
    print(f"reproduced {got[1]} of {got[0]}; structured minus free-form, points ({' / '.join(TIERS)})")
    for v in PAIRS:
        print(f"  {v:32s}" + "".join(f" {rows[v][k]['structured_minus_free_form']:+7.1f}" for k in TIERS)
              + "   fails: " + ", ".join(f"{k} {n}" for k, n in kinds[v].most_common()))


if __name__ == "__main__":
    main()
