#!/usr/bin/env python3
"""prep.py - shared data for Figure 6's panel alternatives (Valerio, 24 Oct: "alternative plates for figure 6 too").

Scratch work, outside the repository. Reads Figure 6's records with S447's own loader and design (load_mirror,
keep_design; S477's lung_9 re-score applied inside load_mirror), labels with S447's functions, families with S478's FAM,
tiers from the ground truth's `complexity` (as S479). Nothing here re-implements those.

REPRODUCE FIRST (README.md:75-79): stops (exit 1) before writing unless
  - the design gives 2,420 attempts and S478 WANT's passes (1,692 after S4),
  - every number S478 and S479 committed (findings/recompute/S478_fig6_thinking_gap.json, S479_fig6_by_tier.json)
    comes out equal when recomputed here from this script's own rows,
  - the manifest and ground truth are the files those two JSONs name (sha256).

Writes, next to this script: attempts.csv, summary.json.

    cd /Users/valeriobianchi/projects/Mentori-reanalysis && uv run --frozen python <this file>
"""
import csv
import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Users/valeriobianchi/projects/Mentori-reanalysis")
HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True           # importing scripts/ must not write __pycache__ into the repository
sys.path.insert(0, str(ROOT / "scripts"))
import S478_fig6_thinking_gap as S478  # noqa: E402  (loads S447 itself; we use that same module object)
import S479_fig6_by_tier as S479  # noqa: E402

S447 = S478.S447
FAM, GT, MANIFEST, WANT = S478.FAM, S478.GT, S478.MANIFEST, S478.WANT
TIERS = S479.TIERS                       # simple, medium, complex, all
FAMILIES = ["structured", "introspection", "free-form"]
DATASET = {"airway": "RNA-seq", "lung_cancer": "survival"}
PAIRS = {"gemini-3-flash": ["gemini-3-flash-preview+off", "gemini-3-flash-preview+default"],
         "gemini-2.5-pro": ["gemini-2.5-pro+off", "gemini-2.5-pro+default"],
         "gpt-oss:20b": ["gpt-oss-20b+low", "gpt-oss-20b+medium", "gpt-oss-20b+high"]}
J478 = ROOT / "findings/recompute/S478_fig6_thinking_gap.json"
J479 = ROOT / "findings/recompute/S479_fig6_by_tier.json"
COST = ["latency_s", "n_calls", "generator_calls", "llm_calls_d115", "prompt_tokens", "output_tokens",
        "thinking_tokens"]


def fail(msg):
    print(f"NOT REPRODUCED: {msg}")
    sys.exit(1)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def tok_sum(calls, key):
    xs = [c.get(key) for c in calls if c.get("role") == "generator"]
    xs = [x for x in xs if isinstance(x, (int, float))]
    return sum(xs) if xs else ""


def count(rows, *keys):
    """{key tuple: [passes, attempts]}."""
    t = defaultdict(lambda: [0, 0])
    for r in rows:
        k = tuple(r[x] for x in keys)
        t[k][0] += r["passed"]
        t[k][1] += 1
    return t


def main():
    gt = json.loads(GT.read_text())["datasets"]
    tier = {k: o["complexity"] for d in gt.values() for k, o in d["operations"].items()}
    dset = {k: DATASET[dn] for dn, d in gt.items() for k in d["operations"]}

    atts, flags, inputs, notes = S447.load_mirror()
    kept, vs, total, left = S447.keep_design(atts)
    got = (len(kept), sum(bool(a["passed"]) for a in kept))
    if got != WANT or total != WANT[0]:
        fail(f"design gives {got} (total {total}), Figure 6 has {WANT}")
    if set(a["op_id"] for a in kept) - set(tier):
        fail("tasks without a tier")

    rows = []
    for a in kept:
        rid = a["run_id"]
        v, s = S447.variant_of(rid), S447.config_of(rid)
        if a["dataset"] not in DATASET or dset[a["op_id"]] != DATASET[a["dataset"]]:
            fail(f"dataset of {a['answer_key']} disagrees with the ground truth")
        calls = a.get("calls") or []
        multi = sum(1 for _, m, _ in S447.VARIANTS if m == S447.VMODEL[v]) > 1
        r = {"variant_id": v, "variant": S447.short_variant(v), "model": S447.VMODEL[v],
             "setting": S447.VTHINK[v] if multi else "", "thinking": S447.VTHINK[v],
             "strategy": s, "strategy_label": S447.SLAB[s], "family": FAM[s],
             "op_id": a["op_id"], "dataset": dset[a["op_id"]], "tier": tier[a["op_id"]],
             "passed": int(bool(a["passed"])),
             "fail_kind": "" if a["passed"] else S447.fail_kind(a, flags.get(a.get("ctx_uid"), set())),
             "latency_s": a.get("latency_s") if a.get("latency_s") is not None else "",
             "n_calls": a.get("n_calls") if a.get("n_calls") is not None else "",
             "generator_calls": sum(1 for c in calls if c.get("role") == "generator"),
             "llm_calls_d115": S447.llm_calls(a) if S447.llm_calls(a) is not None else "",
             "prompt_tokens": tok_sum(calls, "prompt_tokens"), "output_tokens": tok_sum(calls, "output_tokens"),
             "thinking_tokens": tok_sum(calls, "thinking_tokens")}
        rows.append(r)

    # ---- reproduce S478 from these rows -------------------------------------------------------------------------
    j478, j479 = json.loads(J478.read_text()), json.loads(J479.read_text())
    for j, name in ((j478, "S478"), (j479, "S479")):
        if j["provenance"]["manifest_sha256"] != sha(MANIFEST):
            fail(f"{name}'s JSON was written on another manifest")
        if j["provenance"]["ground_truth_sha256"] != sha(GT):
            fail(f"{name}'s JSON was written on another ground truth")
        if j["provenance"]["q4_lung9_rescore"] != notes.get("q4_lung9_rescore"):
            fail(f"{name}'s JSON had another lung_9 re-score")
        if j["reproduced"] != {"attempts": got[0], "passes": got[1]}:
            fail(f"{name}'s JSON reproduced another total")
    vft = count(rows, "variant_id", "family", "tier")
    vfa = count(rows, "variant_id", "family")
    cell = lambda v, f, k: list(vft[(v, f, k)]) if k != "all" else list(vfa[(v, f)])
    rate = lambda c: 100 * c[0] / c[1]
    s478 = {}
    for v in S478.PAIRS:
        s478[v] = {k: {"passes": {f: cell(v, f, k) for f in FAMILIES},
                       "structured_minus_free_form": round(rate(cell(v, "structured", k)) - rate(cell(v, "free-form", k)), 1),
                       "introspection_minus_free_form": round(rate(cell(v, "introspection", k)) - rate(cell(v, "free-form", k)), 1)}
                   for k in TIERS}
        s478[v]["structured_fail_kinds"] = dict(Counter(r["fail_kind"] for r in rows if r["variant_id"] == v
                                                        and r["family"] == "structured" and not r["passed"]).most_common())
    if s478 != j478["variants"]:
        bad = [v for v in s478 if s478[v] != j478["variants"].get(v)]
        fail(f"S478 table differs for {bad}")

    # ---- reproduce S479 from these rows -------------------------------------------------------------------------
    pct = lambda c: round(100 * c[0] / c[1], 1)
    st, ft, at = count(rows, "strategy", "tier"), count(rows, "family", "tier"), count(rows, "tier")
    sa, fa = count(rows, "strategy"), count(rows, "family")

    def g(group, k):
        if group == "all":
            c = [len([r for r in rows if r["passed"]]), len(rows)] if k == "all" else list(at[(k,)])
        elif group in FAMILIES:
            c = list(fa[(group,)]) if k == "all" else list(ft[(group, k)])
        else:
            c = list(sa[(group,)]) if k == "all" else list(st[(group, k)])
        return {"passes": c, "rate": pct(c)}
    groups = ["all", "free-form", "introspection", "structured"] + [s for s, _ in S447.STRATEGIES]
    by_group = {grp: {k: g(grp, k) for k in TIERS} for grp in groups}
    po = count(rows, "op_id")
    order = list(dict.fromkeys(r["op_id"] for r in rows))     # first appearance, as per_op_counts' dict order
    per_task = [{"task": o, "tier": tier[o], "passes": list(po[(o,)]), "rate": pct(po[(o,)])}
                for o in sorted(order, key=lambda o: (TIERS.index(tier[o]), -po[(o,)][0] / po[(o,)][1]))]
    gap = {v: {k: round(pct(vft[(v, "structured", k)]) - pct(vft[(v, "free-form", k)]), 1) for k in TIERS[:3]}
           for v in vs}
    for name, mine in (("by_group", by_group), ("per_task", per_task),
                       ("structured_minus_free_form_per_variant", gap)):
        if mine != j479[name]:
            fail(f"S479 {name} differs")
    print(f"reproduced: {got[0]} attempts, {got[1]} passes; S478 table ({len(s478)} variants) and S479 tables "
          f"(by_group {len(by_group)} groups, per_task {len(per_task)} tasks, gap {len(gap)} variants) equal")

    # ---- write attempts.csv -------------------------------------------------------------------------------------
    cols = ["variant_id", "variant", "model", "setting", "thinking", "strategy", "strategy_label", "family", "op_id",
            "dataset", "tier", "passed", "fail_kind"] + COST
    with open(HERE / "attempts.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    # ---- summary.json -------------------------------------------------------------------------------------------
    vs_ = count(rows, "variant_id", "strategy")
    va = count(rows, "variant_id")
    vtier = count(rows, "variant_id", "tier")
    per_variant = {}
    for v in vs:
        per_variant[v] = {
            "label": S447.short_variant(v), "model": S447.VMODEL[v], "thinking": S447.VTHINK[v],
            "overall": list(va[(v,)]),
            "by_strategy": {s: list(vs_[(v, s)]) for s, _ in S447.STRATEGIES},
            "by_family": {f: list(vfa[(v, f)]) for f in FAMILIES},
            "by_tier": {k: list(vtier[(v, k)]) for k in TIERS[:3]},
            "by_tier_family": {k: {f: list(vft[(v, f, k)]) for f in FAMILIES} for k in TIERS[:3]}}
    if any(vs_[(v, s)][1] != 20 for v in vs for s, _ in S447.STRATEGIES):
        fail("a variant x strategy cell does not hold 20 attempts")
    thinking_pairs = {m: {v: {"setting": S447.VTHINK[v], "overall": per_variant[v]["overall"],
                              "by_family": per_variant[v]["by_family"],
                              "by_tier_family": per_variant[v]["by_tier_family"],
                              "structured_minus_free_form": {k: s478[v][k]["structured_minus_free_form"] for k in TIERS}}
                          for v in vv} for m, vv in PAIRS.items()}
    cost_fields = {c: sum(1 for r in rows if r[c] != "") for c in COST}
    out = {"provenance": {"script": str(Path(__file__)), "script_sha256": sha(__file__),
                          "repo_commit": subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                                                        capture_output=True, text=True).stdout.strip(),
                          "manifest_sha256": sha(MANIFEST), "ground_truth_sha256": sha(GT),
                          "S478_json_sha256": sha(J478), "S479_json_sha256": sha(J479),
                          "q4_lung9_rescore": notes.get("q4_lung9_rescore"),
                          "written_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                          "command": "cd /Users/valeriobianchi/projects/Mentori-reanalysis && uv run --frozen python "
                                     + str(Path(__file__))},
           "note": "one draw, descriptive, no test; every count is [passes, attempts]",
           "reproduced": {"attempts": got[0], "passes": got[1], "S478_equal": True, "S479_equal": True},
           "variants_in_order": vs, "strategies_in_order": [s for s, _ in S447.STRATEGIES],
           "strategy_labels": dict(S447.STRATEGIES), "family_of_strategy": FAM,
           "cost_fields": {"rows_with_value": cost_fields,
                           "meaning": {"latency_s": "attempt's stored latency_s (wall seconds)",
                                       "n_calls": "attempt's stored n_calls (all calls, judge included)",
                                       "generator_calls": "generator-role entries in the attempt's calls list",
                                       "llm_calls_d115": "S447.llm_calls(a): stored n_llm_calls, or calls to the first "
                                                         "length stop for a length-cut attempt (D115 LS1)",
                                       "prompt_tokens": "sum over generator calls with a value",
                                       "output_tokens": "sum over generator calls with a value",
                                       "thinking_tokens": "sum over generator calls with a value"}},
           "per_variant": per_variant,
           "by_family_tier_all_variants": {f: {k: by_group[f][k]["passes"] for k in TIERS} for f in FAMILIES},
           "thinking_pairs": thinking_pairs,
           "S478_structured_minus_free_form": s478,
           "S479": {"by_group": by_group, "per_task": per_task, "structured_minus_free_form_per_variant": gap}}
    (HERE / "summary.json").write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {HERE / 'attempts.csv'} ({len(rows)} rows, {len(cols)} columns)")
    print(f"wrote {HERE / 'summary.json'}")
    print("cost fields, rows with a value of " + str(len(rows)) + ": "
          + ", ".join(f"{c} {n}" for c, n in cost_fields.items()))
    print("structured minus free-form, points (simple / medium / complex / all):")
    for v in S478.PAIRS:
        print(f"  {v:32s}" + "".join(f" {s478[v][k]['structured_minus_free_form']:+6.1f}" for k in TIERS))
    print("all variants, pass % (simple / medium / complex / all):")
    for grp in ["free-form", "introspection", "structured"]:
        print(f"  {grp:14s}" + "".join(f" {by_group[grp][k]['rate']:6.1f}" for k in TIERS))


if __name__ == "__main__":
    main()
