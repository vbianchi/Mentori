"""S21b - what the 3000-char truncation actually cost, and the corrected numbers.

Reads findings/recompute/S21_rejudge_raw.jsonl (see S21_full_answer_rejudge.py) plus the
deposited results, and reports:

  1. REPLICATION GATE. Arm T re-ran the published conditions. Its disagreement with the
     deposited scores is run-to-run drift, and it bounds how much of any arm-F difference is
     noise rather than truncation. Reported per experiment, because drift was only ever
     measured on exp04 before.

  2. TRUNCATION EFFECT. Arm F (full answer) vs published, on the cut answers only, per
     experiment and per configuration. Cluster bootstrap over question_id, since the same
     question appears under several configurations and depths.

  3. CORRECTED HEADLINES. Each experiment's mean scores recomputed as: arm F where the answer
     was cut, deposited score everywhere else (valid because an uncut answer's prompt is
     byte-identical and the judge is deterministic). This is the number the paper would print
     if the judge had seen whole answers.

  4. DEPTH CONFOUND (exp09). Truncation rate by retrieval depth, and the corrected depth curve.
     If longer answers arrive at greater depth, the truncation biases the curve rather than
     adding noise to it, which would be a live threat to Fig 3a.

Writes findings/recompute/S21_results.json. No model calls.
"""
from __future__ import annotations
import json, glob, os, sys, collections, statistics as st
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from machine import PUB, RECOMPUTE   # noqa: E402

PAPER = PUB
OUT = RECOMPUTE
RAW = OUT / "S21_rejudge_raw.jsonl"
CUT = 3000
DIMS = ("correctness", "completeness", "faithfulness", "citation_quality")
UNANS = ("refusal_accuracy", "hallucination_avoidance", "explanation_quality")
SEED = 42
NBOOT = 10000


def family(fn):
    """Group the 14 exp09 shards into one experiment, keep the rest as-is."""
    b = fn.replace("_latest.json", "")
    if b.startswith("exp09_depth_sweep"):
        return "exp09_depth_sweep"
    return b


# ─────────────────────────────────────────────────────────────────── cluster bootstrap
def cluster_boot(pairs, stat, nboot=NBOOT, seed=SEED):
    """pairs: list of (cluster_id, value). Returns (point, lo, hi) over resampled clusters."""
    import random
    by = collections.defaultdict(list)
    for c, v in pairs:
        by[c].append(v)
    keys = list(by)
    if not keys:
        return None, None, None
    point = stat([v for k in keys for v in by[k]])
    rng = random.Random(seed)
    out = []
    for _ in range(nboot):
        vals = []
        for _ in range(len(keys)):
            vals.extend(by[keys[rng.randrange(len(keys))]])
        out.append(stat(vals))
    out.sort()
    return point, out[int(0.025 * nboot)], out[int(0.975 * nboot)]


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


# ─────────────────────────────────────────────────────────────────── load
def pub_is_error(r):
    """The deposited score is a harness exception artefact, not a verdict, so it can neither
    gate a replication nor serve as the baseline of a contrast."""
    if r.get("published_is_error") is not None:
        return bool(r["published_is_error"])
    return "Judge error" in str((r.get("published") or {}).get("justification", ""))


def load_raw():
    rows = [json.loads(l) for l in open(RAW)]
    ok = [r for r in rows if r.get("parsed") and not r.get("error")]
    return rows, ok


def dims_for(r):
    return DIMS if r.get("answerable", True) else UNANS


def judged_rows(o):
    if isinstance(o, dict):
        if "judge_scores" in o:
            yield o
        for v in o.values():
            yield from judged_rows(v)
    elif isinstance(o, list):
        for v in o:
            yield from judged_rows(v)


def answer_text(r):
    g = r.get("generation")
    if isinstance(g, dict) and g.get("answer"):
        return g["answer"]
    for k in ("answer", "response", "output", "text", "generated_answer"):
        if isinstance(r.get(k), str) and r[k]:
            return r[k]
    return None


def load_deposit():
    """Every judged row, keyed (file, row_idx), with its published scores and answer length."""
    dep = {}
    for f in sorted(glob.glob(str(PAPER / "results" / "*_latest.json"))):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        for i, r in enumerate(judged_rows(d)):
            t = answer_text(r)
            if not t:
                continue
            dep[(os.path.basename(f), i)] = {
                "question_id": r.get("question_id"),
                "config": r.get("config") or r.get("model") or "",
                "depth": r.get("depth"),
                "index_name": r.get("index_name"),
                "chars": len(t),
                "published": r.get("judge_scores") or {},
            }
    return dep


# ─────────────────────────────────────────────────────────────────── 1. replication gate
def gate(ok):
    T = [r for r in ok if r["arm"] == "T" and not pub_is_error(r)]
    out = {}
    for fam in sorted({family(r["file"]) for r in T}):
        rs = [r for r in T if family(r["file"]) == fam]
        per = {}
        for k in list(DIMS) + list(UNANS):
            pairs = [(r["question_id"], int(r["published"][k] == r["parsed"][k]))
                     for r in rs if k in (r["published"] or {}) and k in r["parsed"]]
            if not pairs:
                continue
            diffs = [(r["question_id"], int(r["parsed"][k]) - int(r["published"][k]))
                     for r in rs if k in (r["published"] or {}) and k in r["parsed"]]
            pt, lo, hi = cluster_boot(diffs, mean)
            per[k] = {"n": len(pairs),
                      "exact_agreement": round(mean([v for _, v in pairs]), 4),
                      "mean_signed_drift": round(pt, 4),
                      "drift_ci95": [round(lo, 4), round(hi, 4)]}
        out[fam] = {"n_calls": len(rs), "per_dimension": per}
    return out


# ─────────────────────────────────────────────────────────────────── 2. truncation effect
def effect(ok):
    F = [r for r in ok if r["arm"] == "F" and not pub_is_error(r)]
    out = {}
    for fam in sorted({family(r["file"]) for r in F}):
        rs = [r for r in F if family(r["file"]) == fam]
        per = {}
        for k in list(DIMS) + list(UNANS):
            sub = [r for r in rs if k in (r["published"] or {}) and k in r["parsed"]]
            if not sub:
                continue
            diffs = [(r["question_id"], int(r["parsed"][k]) - int(r["published"][k])) for r in sub]
            pt, lo, hi = cluster_boot(diffs, mean)
            s5 = [(r["question_id"], int(int(r["parsed"][k]) == 5) - int(int(r["published"][k]) == 5))
                  for r in sub]
            p5, l5, h5 = cluster_boot(s5, mean)
            per[k] = {
                "n": len(sub),
                "published_mean": round(mean([int(r["published"][k]) for r in sub]), 4),
                "full_answer_mean": round(mean([int(r["parsed"][k]) for r in sub]), 4),
                "mean_diff": round(pt, 4), "mean_diff_ci95": [round(lo, 4), round(hi, 4)],
                "exact_agreement": round(mean([int(int(r["parsed"][k]) == int(r["published"][k]))
                                               for r in sub]), 4),
                "share5_diff_pp": round(p5 * 100, 2),
                "share5_diff_ci95_pp": [round(l5 * 100, 2), round(h5 * 100, 2)],
            }
        # per configuration, primary dimension only
        bycfg = {}
        for cfg in sorted({r["config"] for r in rs}):
            sub = [r for r in rs if r["config"] == cfg and "faithfulness" in (r["published"] or {})
                   and "faithfulness" in r["parsed"]]
            if not sub:
                continue
            bycfg[cfg] = {
                "n": len(sub),
                "published_mean": round(mean([int(r["published"]["faithfulness"]) for r in sub]), 3),
                "full_answer_mean": round(mean([int(r["parsed"]["faithfulness"]) for r in sub]), 3),
            }
        out[fam] = {"n_cut_rejudged": len(rs), "per_dimension": per,
                    "faithfulness_by_config": bycfg}
    return out


# ─────────────────────────────────────────────────────────────────── 3. corrected headlines
def corrected(ok, dep):
    F = {(r["file"], r["row_idx"]): r for r in ok if r["arm"] in ("F", "R")}
    out = {}
    fams = collections.defaultdict(list)
    for (fn, i), d in dep.items():
        fams[family(fn)].append((fn, i, d))
    for fam, items in sorted(fams.items()):
        per = {}
        for k in DIMS:
            pub, cor, n_sub = [], [], 0
            for fn, i, d in items:
                if k not in (d["published"] or {}):
                    continue
                pv = int(d["published"][k])
                pub.append(pv)
                r = F.get((fn, i))
                if r and k in r["parsed"]:
                    cor.append(int(r["parsed"][k]))
                    n_sub += 1
                else:
                    cor.append(pv)
            if not pub:
                continue
            per[k] = {
                "n_answers": len(pub), "n_substituted": n_sub,
                "published_mean": round(mean(pub), 4),
                "corrected_mean": round(mean(cor), 4),
                "delta": round(mean(cor) - mean(pub), 4),
                "published_share5": round(mean([int(x == 5) for x in pub]), 4),
                "corrected_share5": round(mean([int(x == 5) for x in cor]), 4),
            }
        if per:
            out[fam] = per
    return out


# ─────────────────────────────────────────────────────────────────── 4. depth confound
def depth_confound(ok, dep):
    F = {(r["file"], r["row_idx"]): r for r in ok if r["arm"] in ("F", "R")}
    bydepth = collections.defaultdict(lambda: {"n": 0, "cut": 0, "chars": [],
                                               "pub": [], "cor": []})
    for (fn, i), d in dep.items():
        if family(fn) != "exp09_depth_sweep" or d["depth"] is None:
            continue
        if "faithfulness" not in (d["published"] or {}):
            continue
        b = bydepth[d["depth"]]
        b["n"] += 1
        b["chars"].append(d["chars"])
        pv = int(d["published"]["faithfulness"])
        b["pub"].append(pv)
        if d["chars"] > CUT:
            b["cut"] += 1
            r = F.get((fn, i))
            b["cor"].append(int(r["parsed"]["faithfulness"])
                            if r and "faithfulness" in r["parsed"] else pv)
        else:
            b["cor"].append(pv)
    out = {}
    for depth in sorted(bydepth):
        b = bydepth[depth]
        out[str(depth)] = {
            "n": b["n"], "n_truncated": b["cut"],
            "pct_truncated": round(b["cut"] / b["n"] * 100, 1),
            "median_answer_chars": round(st.median(b["chars"])),
            "published_faithfulness": round(mean(b["pub"]), 4),
            "corrected_faithfulness": round(mean(b["cor"]), 4),
            "delta": round(mean(b["cor"]) - mean(b["pub"]), 4),
        }
    # does truncation rate track depth?
    xs = [float(d) for d in sorted(bydepth)]
    ys = [bydepth[d]["cut"] / bydepth[d]["n"] for d in sorted(bydepth)]
    if len(xs) > 2:
        rx = sorted(range(len(xs)), key=lambda i: xs[i])
        ry = sorted(range(len(ys)), key=lambda i: ys[i])
        n = len(xs)
        rank_x = [0] * n
        rank_y = [0] * n
        for pos, i in enumerate(rx):
            rank_x[i] = pos
        for pos, i in enumerate(ry):
            rank_y[i] = pos
        dsum = sum((rank_x[i] - rank_y[i]) ** 2 for i in range(n))
        out["_spearman_depth_vs_cutrate"] = round(1 - 6 * dsum / (n * (n * n - 1)), 4)
    return out


def main():
    rows, ok = load_raw()
    dep = load_deposit()
    arms = collections.Counter(r["arm"] for r in rows)
    print(f"raw rows {len(rows)}  usable {len(ok)}  errors {sum(1 for r in rows if r.get('error'))}"
          f"  arms {dict(arms)}")
    hit = sum(1 for r in rows if r.get("hit_ceiling"))
    trunc = sum(1 for r in rows if r.get("output_truncated"))
    print(f"prompts that hit the context ceiling: {hit}   outputs truncated: {trunc}")

    g = gate(ok)
    print("\n── REPLICATION GATE (arm T vs published, faithfulness)")
    for fam, d in g.items():
        f = d["per_dimension"].get("faithfulness")
        if f:
            print(f"  {fam:34s} n={f['n']:>4}  exact {f['exact_agreement']*100:5.1f}%  "
                  f"drift {f['mean_signed_drift']:+.3f} CI{f['drift_ci95']}")

    e = effect(ok)
    print("\n── TRUNCATION EFFECT (arm F vs published, cut answers only, faithfulness)")
    for fam, d in e.items():
        f = d["per_dimension"].get("faithfulness")
        if f:
            print(f"  {fam:34s} n={f['n']:>4}  {f['published_mean']:.3f} -> "
                  f"{f['full_answer_mean']:.3f}  diff {f['mean_diff']:+.3f} "
                  f"CI{f['mean_diff_ci95']}  share5 {f['share5_diff_pp']:+.1f}pp")

    c = corrected(ok, dep)
    print("\n── CORRECTED HEADLINES (all answers; arm F substituted where cut)")
    for fam, d in c.items():
        f = d.get("faithfulness")
        if f:
            print(f"  {fam:34s} n={f['n_answers']:>5} (sub {f['n_substituted']:>4})  "
                  f"{f['published_mean']:.3f} -> {f['corrected_mean']:.3f}  "
                  f"delta {f['delta']:+.4f}")

    dc = depth_confound(ok, dep)
    if len(dc) > 1:
        print("\n── exp09 DEPTH CONFOUND")
        print(f"  {'depth':>6} {'n':>5} {'cut%':>6} {'med chars':>10} {'published':>10} "
              f"{'corrected':>10} {'delta':>8}")
        for k, v in dc.items():
            if k.startswith("_"):
                continue
            print(f"  {k:>6} {v['n']:>5} {v['pct_truncated']:>5.1f}% {v['median_answer_chars']:>10} "
                  f"{v['published_faithfulness']:>10.3f} {v['corrected_faithfulness']:>10.3f} "
                  f"{v['delta']:>+8.4f}")
        print(f"  spearman(depth, truncation rate) = {dc.get('_spearman_depth_vs_cutrate')}")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "S21_results.json").write_text(json.dumps({
        "_provenance": {"script": "scripts/S21b_analyze.py", "raw": RAW.name,
                        "seed": SEED, "n_boot": NBOOT, "cut_chars": CUT},
        "run_health": {"raw_rows": len(rows), "usable": len(ok),
                       "errors": sum(1 for r in rows if r.get("error")),
                       "hit_ceiling": hit, "output_truncated": trunc,
                       "arms": dict(arms)},
        "replication_gate": g,
        "truncation_effect": e,
        "corrected_headlines": c,
        "depth_confound": dc,
    }, indent=2))
    print(f"\nwrote {OUT / 'S21_results.json'}")


if __name__ == "__main__":
    main()
