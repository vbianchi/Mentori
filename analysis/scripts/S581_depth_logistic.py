"""S581: D254, a logistic curve of concept recall against turn cap, one per RLM implementation, on the depth sweep.

One command, from the repository root:
    uv run python scripts/S581_depth_logistic.py            reproduce, then fit, then write
    uv run python scripts/S581_depth_logistic.py --check    reproduce, then fit, then compare with the committed output
    uv run python scripts/S581_depth_logistic_test.py       the test (synthetic curves and mutants)

WHY. D254 (experiments/README.md, Valerio, 5 November, "go ahead with the fit"): beside the plateau rule of S490, a
fitted curve per implementation (Mentori RLM, G5, one draw; the authors' RLM package, G6, three draws) on the 86
depth-sweep questions, with the plateau height and the cap at which the curve reaches 90% of it, each with a 95%
interval from question resamples. The plateau rule stays as S490 states it.

READS (committed files only; the rows Supplementary Figure 8a draws, through S490, which names them):
    S490.L2_ROWS, field S490.A_FIELD   today findings/recompute/L2_d135_d181/concept_recall.jsonl, concept_recall
                                       (D186 (4): the plate's provenance names it under "l2_d181" "drawn")
    S490.L2_D284_ROWS                  joined by S490.l2_rows(): RLM's draws 2 and 3 on all 86 (D284)
    S490's inputs                      S490.build() gates every cell of the plate's data workbook first

REPRODUCE FIRST (README.md:75-79). (1) S490.build() must reproduce the plate's data workbook with 0 mismatches.
(2) S490's plateau numbers must equal the ones the paper prints (PAPER below): Mentori RLM 42.6% at cap 1, 73.0% at
cap 3, between 70.0 and 77.7 from cap 3 to cap 50, plateau cap 3; package 9.9% at cap 1, 62.2% at cap 5, plateau
cap 5 (one decimal). (3) The cap means of this script's question matrix must equal S490's (to 1e-9 after S490's
rounding). Any difference: the script prints it and exits 2 with nothing written.

THE MODEL. Per implementation and cap c, y(c) = P / (1 + exp(-k (ln c - ln m))), which is P / (1 + (m / c)^k):
    P   the plateau, the upper asymptote (a share, 0 to 1);
    m   the midpoint, the cap at which the curve is at P / 2;
    k   the slope in log(cap).
A logistic in log(cap), because the caps are spaced on a log scale (1 to 50). Its lower asymptote is 0, the floor of
concept recall, reached as the cap goes to 0 turns. A free lower asymptote (a fourth parameter) is not identified:
the curve rises between cap 1 and cap 2 and the sweep has no cap below 1, so a lower asymptote anywhere under the
cap-1 value fits as well. The four-parameter fit is run once per implementation on the means as a diagnostic and
recorded (four_parameter), never reported as the result.
c90, the cap at which the curve reaches 0.9 P: (m / c)^k = 1/9, so c90 = m * 9^(1/k).

THE FIT. Least squares on each question's value at each cap (G6: the mean over its three draws, as the plate
draws it), all 86 questions at all caps. With every question present at every cap, this least-squares fit has the
same minimum as the least-squares fit to the ten cap means (the sum of squares splits into a within-cap part that
does not depend on the curve and 86 times the squared distance of each cap mean from the curve); the script checks
the two give the same parameters (EQUAL_TOL) and fits the means. What makes the interval question-level is the
resampling: 10,000 resamples of the 86 questions, each question's whole row of caps kept together, the same
resamples for both implementations (so their difference is paired by question) and for both fits; the resamples are
S463.resample_counts(86), default_rng(20261013).integers(0, 86, size=(10000, 86)), the ones S463.interval uses.
A resample's cap means are its counts times the question matrix over 86, and the curve is fitted to them. 95%
percentile intervals (2.5 and 97.5, linear interpolation). Two fits: all ten caps, and caps 2 to 50 (cap 1 left out,
where the answer is forced after one turn; S485.FIT_FROM).
Starts: the point fit tries every start of STARTS and keeps the least sum of squares; each resample starts from the
point fit's parameters and from STARTS' first two, keeping the least. A resample whose every start fails is counted
(failed) and left out of the intervals; a resample whose best fit sits on a bound of BOUNDS is counted (at_bound,
per parameter). The differences are over the resamples where both implementations' fits succeeded.

WRITES findings/recompute/S581_depth_logistic/ (no time in it, so a rerun is byte-equal):
    fit.json          provenance header, the reproduction, the fits, intervals, differences and the diagnostics
    curves.csv        the fitted curves on a log grid of caps, per implementation and fit
    draft_supp8a_fit.png   a draft (not a plate): cap means with their 95% intervals, each question's value, the
                      fitted curves (solid all caps, dashed caps 2 to 50), P and c90 marked
No model call. No Ollama port contacted.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import curve_fit

REPO = Path(__file__).resolve().parents[1]
HERE = REPO / "scripts"
SCRIPT = "scripts/S581_depth_logistic.py"
OUT = REPO / "findings/recompute/S581_depth_logistic"


def _load(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


S490 = _load("S490", HERE / "S490_fig3_plateau.py")
S463 = _load("S463", HERE / "S463_fig2_ranking.py")

SYSTEMS = ("G5", "G6")
NAME = {"G5": "Mentori RLM", "G6": "package RLM"}
COLOUR = {"G5": "#0072B2", "G6": "#D55E00"}      # Supplementary Figure 8a's colours (FIGURE_LOCK [colour] categorical)
FIT_FROM = 2                                     # the second fit leaves out cap 1 (S485.FIT_FROM)
FRACTION = 0.9                                   # c90: the cap at 90% of the plateau
BOUNDS = ([0.0, 0.01, math.log(0.05)], [1.0, 30.0, math.log(500.0)])   # P, k, ln m
STARTS = [(None, 2.0, math.log(1.5)), (None, 1.0, math.log(3.0)), (None, 4.0, math.log(0.8)),
          (None, 0.5, math.log(10.0))]          # (P from the data, k, ln m)
BOUND_EPS = 1e-6
LSQ = {"ftol": 1e-12, "xtol": 1e-12, "gtol": 1e-12}   # tight, so the two least-squares fits meet
EQUAL_TOL = 1e-6                                 # question points against means: the same parameters
TOL = 1e-9

# The values the paper prints (one decimal), held to S490's numbers before anything is fitted.
# D284: RLM's values are its three draws' means (one draw before: 42.6, 73.0, 70.0 to 77.7).
PAPER = {"G5": {"cap1": 47.5, "cap3": 74.8, "range_cap3_to_50": [72.9, 77.2], "plateau_cap": 3},
         "G6": {"cap1": 9.9, "cap5": 62.2, "plateau_cap": 5}}


class Refused(Exception):
    pass


def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rel(p) -> str:
    return str(Path(p).resolve().relative_to(REPO))


def r1(x: float) -> float:
    return float(f"{x:.1f}")


# ------------------------------------------------------------------------------------------------ the model
def f_curve(c, P, k, t):
    """P / (1 + exp(-k (ln c - t))), t = ln m."""
    return P / (1.0 + np.exp(-k * (np.log(np.asarray(c, float)) - t)))


def f_curve4(c, A, P, k, t):
    return A + (P - A) / (1.0 + np.exp(-k * (np.log(np.asarray(c, float)) - t)))


def c_at(fraction: float, k: float, t: float) -> float:
    """The cap at which the curve reaches fraction * P: (m / c)^k = 1/fraction - 1."""
    return float(math.exp(t) * (1.0 / (1.0 / fraction - 1.0)) ** (1.0 / k))


def _one(x, y, p0):
    p, _ = curve_fit(f_curve, x, y, p0=p0, bounds=BOUNDS, maxfev=20000, **LSQ)
    return p, float(np.sum((y - f_curve(x, *p)) ** 2))


def fit(x, y, starts) -> tuple[np.ndarray | None, float]:
    """Least squares over the starts; the least sum of squares wins. (None, nan) when every start fails."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    best, best_rss = None, math.inf
    for s in starts:
        p0 = [min(max(float(np.max(y)), 1e-3), 1.0) if s[0] is None else s[0], s[1], s[2]]
        p0 = [min(max(v, lo + 1e-9), hi - 1e-9) for v, lo, hi in zip(p0, *BOUNDS)]
        try:
            p, rss = _one(x, y, p0)
        except (RuntimeError, ValueError):
            continue
        if rss < best_rss - 1e-15:
            best, best_rss = p, rss
    return best, (best_rss if best is not None else math.nan)


def on_bound(p) -> list[str]:
    return [n for n, v, lo, hi in zip(("P", "k", "m"), p, *BOUNDS) if v <= lo + BOUND_EPS or v >= hi - BOUND_EPS]


def pct(v) -> list[float]:
    return [float(x) for x in np.percentile(np.asarray(v, float), S463.PCT)]


# ------------------------------------------------------------------------------------------------ the data
def matrix(rows: list, system: str, caps: list, field: str) -> tuple[list, np.ndarray]:
    """Questions x caps, each question's mean over its draws (S490.a_tables' per-question value, as a share)."""
    vals: dict = {}
    for r in rows:
        if r["system"] == system:
            vals.setdefault((r["question_id"], r["cap"]), []).append(r[field])
    qs = sorted({q for q, _ in vals})
    missing = [(q, c) for q in qs for c in caps if (q, c) not in vals]
    if missing:
        raise Refused(f"{system}: {len(missing)} question and cap cells without a value, first {missing[0]}")
    return qs, np.array([[float(np.mean(vals[(q, c)])) for c in caps] for q in qs])


# ------------------------------------------------------------------------------------------------ reproduce first
def reproduce(s490_doc: dict, mats: dict, caps: list) -> dict:
    """S490's plateau numbers against the paper's, and this script's cap means against S490's."""
    bad, out = [], {}
    pl = s490_doc["plateau"]
    for s in SYSTEMS:
        R = {int(c): v for c, v in pl[s]["mean_pct_per_cap"].items()}
        got = {"cap1": r1(R[1]), "plateau_cap": pl[s]["interval_rule_cap"]}
        if s == "G5":
            got["cap3"] = r1(R[3])
            got["range_cap3_to_50"] = [r1(min(v for c, v in R.items() if c >= 3)),
                                       r1(max(v for c, v in R.items() if c >= 3))]
        else:
            got["cap5"] = r1(R[5])
        for k, want in PAPER[s].items():
            if got[k] != want:
                bad.append(f"{s} {k}: paper {want!r}, S490 {got[k]!r}")
        mine = 100 * mats[s].mean(axis=0)
        for j, c in enumerate(caps):
            if not math.isclose(100 * round(float(mine[j]) / 100, 4), R[c], abs_tol=TOL, rel_tol=0):
                bad.append(f"{s} cap {c}: S490 mean {R[c]!r}, this script {mine[j]!r}")
        out[s] = {"paper": PAPER[s], "s490": got, "cap_means_equal_s490": len(caps)}
    if bad:
        raise Refused("the paper's plateau numbers are not reproduced: " + "; ".join(bad))
    return out


# ------------------------------------------------------------------------------------------------ the fits
def point_fit(M: np.ndarray, caps: list) -> dict:
    """The fit to the cap means, checked against the fit to every question point."""
    x = np.asarray(caps, float)
    ybar = M.mean(axis=0)
    p, rss = fit(x, ybar, STARTS)
    if p is None:
        raise Refused("the point fit failed from every start")
    pq, _ = fit(np.tile(x, M.shape[0]), M.ravel(), [(p[0], p[1], p[2])] + STARTS)
    if pq is None or np.max(np.abs(pq - p)) > EQUAL_TOL:
        raise Refused(f"question points {None if pq is None else list(pq)} and means {list(p)} give different fits")
    yq = f_curve(np.tile(x, M.shape[0]), *p)
    r2_means = 1 - rss / float(np.sum((ybar - ybar.mean()) ** 2))
    r2_q = 1 - float(np.sum((M.ravel() - yq) ** 2)) / float(np.sum((M.ravel() - M.mean()) ** 2))
    return {"P": float(p[0]), "k": float(p[1]), "t": float(p[2]), "m": float(math.exp(p[2])),
            "c90": c_at(FRACTION, p[1], p[2]), "rss_means": rss, "r2_means": float(r2_means),
            "r2_question_points": float(r2_q), "on_bound": on_bound(p),
            "question_point_fit_equal": True,
            "residual_pp_per_cap": {str(c): 100 * float(ybar[j] - f_curve(c, *p)) for j, c in enumerate(caps)},
            "fitted_pct_at_cap": {str(c): 100 * float(f_curve(c, *p)) for c in caps}}


def four_parameter(M: np.ndarray, caps: list) -> dict:
    """The diagnostic: a free lower asymptote A in [0, 1], fitted to the means."""
    x, y = np.asarray(caps, float), M.mean(axis=0)
    lo, hi = [0.0] + BOUNDS[0], [1.0] + BOUNDS[1]
    best, best_rss = None, math.inf
    for s in STARTS:
        p0 = [0.0 + 1e-6, float(np.max(y)), s[1], s[2]]
        try:
            p, _ = curve_fit(f_curve4, x, y, p0=p0, bounds=(lo, hi), maxfev=20000, **LSQ)
        except (RuntimeError, ValueError):
            continue
        rss = float(np.sum((y - f_curve4(x, *p)) ** 2))
        if rss < best_rss:
            best, best_rss = p, rss
    if best is None:
        return {"fitted": False}
    names = ("A", "P", "k", "m")
    return {"fitted": True, "A": float(best[0]), "P": float(best[1]), "k": float(best[2]), "m": float(math.exp(best[3])),
            "rss_means": best_rss,
            "on_bound": [n for n, v, l_, h_ in zip(names, best, lo, hi) if v <= l_ + BOUND_EPS or v >= h_ - BOUND_EPS]}


def resampled(M: np.ndarray, caps: list, W: np.ndarray, start: dict) -> dict:
    """The fit on each resample's cap means. Returns arrays of P and c90 (nan where failed) and the counts."""
    x = np.asarray(caps, float)
    Y = (W @ M) / M.shape[0]
    starts = [(start["P"], start["k"], start["t"])] + STARTS[:2]
    P, C, K, T = (np.full(len(W), np.nan) for _ in range(4))
    bound = {"P": 0, "k": 0, "m": 0}
    any_bound = 0
    for i, y in enumerate(Y):
        p, _ = fit(x, y, starts)
        if p is None:
            continue
        P[i], K[i], T[i] = p
        C[i] = c_at(FRACTION, p[1], p[2])
        ob = on_bound(p)
        any_bound += bool(ob)
        for n in ob:
            bound[n] += 1
    return {"P": P, "c90": C, "k": K, "t": T, "failed": int(np.isnan(P).sum()), "at_bound": bound,
            "at_any_bound": any_bound}


def summarise(point: dict, bs: dict) -> dict:
    ok = ~np.isnan(bs["P"])
    return {"P_pct": 100 * point["P"], "P_pct_ci95": [100 * v for v in pct(bs["P"][ok])],
            "c90": point["c90"], "c90_ci95": pct(bs["c90"][ok]),
            "m": point["m"], "m_ci95": pct(np.exp(bs["t"][ok])),
            "k": point["k"], "k_ci95": pct(bs["k"][ok]),
            "resamples": int(len(bs["P"])), "failed": bs["failed"], "at_bound": bs["at_bound"],
            "at_any_bound": bs["at_any_bound"],
            "c90_below_lowest_cap_fitted_share": float(np.mean(bs["c90"][ok] < point["lowest_cap"]))}


def build() -> tuple[dict, dict]:
    doc490, bad, compared = S490.build()
    if bad:
        raise Refused(f"S490 does not reproduce the plate's workbook ({len(bad)} differences): {bad[:3]}")
    rows = S490.l2_rows()
    caps = sorted({r["cap"] for r in rows})
    mats, qsets = {}, {}
    for s in SYSTEMS:
        qsets[s], mats[s] = matrix(rows, s, caps, S490.A_FIELD)
    if qsets["G5"] != qsets["G6"]:
        raise Refused("the two implementations do not answer the same questions")
    n = len(qsets["G5"])
    rep = reproduce(doc490, mats, caps)
    W = S463.resample_counts(n)
    if W.shape != (S463.N_BOOT, n) or not np.all(W.sum(axis=1) == n):
        raise Refused("the resample counts are not 10,000 resamples of the questions")
    fits, curves, draws = {}, [], {}
    for label, cut in (("all caps", 0), (f"caps {FIT_FROM} to {caps[-1]}", caps.index(FIT_FROM))):
        cc = caps[cut:]
        block, bsd = {}, {}
        for s in SYSTEMS:
            Ms = mats[s][:, cut:]
            pt = point_fit(Ms, cc)
            pt["lowest_cap"] = cc[0]
            bs = resampled(Ms, cc, W, pt)
            bsd[s] = bs
            block[s] = {"name": NAME[s], "point": pt, "summary": summarise(pt, bs),
                        "four_parameter": four_parameter(Ms, cc)}
            grid = np.exp(np.linspace(math.log(0.5), math.log(cc[-1]), 121))
            curves += [{"system": s, "fit": label, "cap": float(g), "fitted_pct": 100 * float(f_curve(g, pt["P"],
                        pt["k"], pt["t"]))} for g in grid]
        both = ~np.isnan(bsd["G5"]["P"]) & ~np.isnan(bsd["G6"]["P"])
        dP = 100 * (bsd["G5"]["P"][both] - bsd["G6"]["P"][both])
        dC = bsd["G5"]["c90"][both] - bsd["G6"]["c90"][both]
        block["difference_G5_minus_G6"] = {
            "P_pp": block["G5"]["point"]["P"] * 100 - block["G6"]["point"]["P"] * 100, "P_pp_ci95": pct(dP),
            "c90_caps": block["G5"]["point"]["c90"] - block["G6"]["point"]["c90"], "c90_caps_ci95": pct(dC),
            "resamples_both_fitted": int(both.sum())}
        fits[label] = block
        draws[label] = {s: bsd[s] for s in SYSTEMS}
    cap_ci = {s: {str(c): [100 * v for v in pct((W @ mats[s][:, j]) / n)] for j, c in enumerate(caps)}
              for s in SYSTEMS}
    head = {"script": SCRIPT, "script_sha256": sha256_file(Path(__file__)),
            "command": "uv run python scripts/S581_depth_logistic.py", "decision": "D254 (experiments/README.md)",
            "inputs": {rel(S490.L2_ROWS): sha256_file(S490.L2_ROWS),
                       **{k: v for k, v in doc490["header"]["inputs"].items()}},
            "value_field": S490.A_FIELD,
            "reproduced": {"s490_workbook_values_equal": sum(compared.values()), "s490_mismatches": 0, **rep},
            "model": "y(c) = P / (1 + exp(-k (ln c - ln m))), lower asymptote 0; c90 = m * 9^(1/k)",
            "fitted_to": "least squares to the cap means of each question's value (G6: mean of 3 draws), which "
                         "equals least squares to all question points (checked); questions resampled as whole rows",
            "resamples": {"n": int(S463.N_BOOT), "seed": int(S463.SEED), "source": "S463.resample_counts",
                          "percentiles": list(S463.PCT)},
            "bounds": {"P": [BOUNDS[0][0], BOUNDS[1][0]], "k": [BOUNDS[0][1], BOUNDS[1][1]],
                       "m": [math.exp(BOUNDS[0][2]), math.exp(BOUNDS[1][2])]},
            "questions": n, "caps": caps, "model_calls": 0}
    doc = {"header": head, "fits": fits, "cap_mean_pct": {s: {str(c): 100 * float(mats[s][:, j].mean())
                                                              for j, c in enumerate(caps)} for s in SYSTEMS},
           "cap_mean_pct_ci95": cap_ci}
    return doc, {"mats": mats, "caps": caps, "curves": curves}


# ------------------------------------------------------------------------------------------------ outputs
def curves_csv(curves: list) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=["system", "fit", "cap", "fitted_pct"], lineterminator="\n")
    w.writeheader()
    for r in curves:
        w.writerow({**r, "cap": f"{r['cap']:.6g}", "fitted_pct": f"{r['fitted_pct']:.6f}"})
    return buf.getvalue()


def draw(doc: dict, extra: dict) -> bytes:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "Arial", "font.size": 8, "axes.linewidth": 0.6, "svg.hashsalt": "S581",
                         "pdf.fonttype": 42})
    caps, mats = extra["caps"], extra["mats"]
    fig, axes = plt.subplots(1, 2, figsize=(183 / 25.4, 72 / 25.4), sharey=True)
    off = {"G5": 0.94, "G6": 1.06}
    rng = np.random.default_rng(0)
    for ax, s in zip(axes, SYSTEMS):
        col = COLOUR[s]
        for j, c in enumerate(caps):
            jit = np.exp(rng.uniform(-0.05, 0.05, mats[s].shape[0]))
            ax.scatter(c * jit, 100 * mats[s][:, j], s=3, facecolors="none", edgecolors=col, linewidths=0.3,
                       alpha=0.45, zorder=1)
        mu = [doc["cap_mean_pct"][s][str(c)] for c in caps]
        ci = np.array([doc["cap_mean_pct_ci95"][s][str(c)] for c in caps])
        ax.errorbar(caps, mu, yerr=[np.array(mu) - ci[:, 0], ci[:, 1] - np.array(mu)], fmt="o", ms=3.5, color="black",
                    mfc=col, mec="black", mew=0.4, elinewidth=0.6, capsize=0, zorder=4)
        for label, ls in (("all caps", "-"), (f"caps {FIT_FROM} to {caps[-1]}", "--")):
            pt = doc["fits"][label][s]["point"]
            g = np.exp(np.linspace(math.log(0.8 if label == "all caps" else 1.6), math.log(caps[-1] * 1.1), 200))
            ax.plot(g, 100 * f_curve(g, pt["P"], pt["k"], pt["t"]), ls, color=col, lw=1.0, zorder=3,
                    label=f"fit, {label}: plateau {100 * pt['P']:.1f}%, 90% at cap {pt['c90']:.2f}")
        pt = doc["fits"]["all caps"][s]["point"]
        ax.axvline(pt["c90"], color="0.35", lw=0.4, ls=":", zorder=2)
        ax.set_xscale("log")
        ax.set_xticks(caps)
        ax.set_xticklabels([str(c) for c in caps])
        ax.minorticks_off()
        ax.set_xlim(0.8, 60)
        ax.set_ylim(0, 100)
        ax.set_xlabel("turn cap (log scale)")
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_title(f"{NAME[s]} ({'one draw' if s == 'G5' else 'mean of three draws'}), n = {mats[s].shape[0]} "
                     f"questions", fontsize=8)
        ax.legend(loc="lower right", frameon=False, fontsize=7, handlelength=2.2)
    axes[0].set_ylabel("concept recall (%)")
    fig.text(0.5, 0.005, "DRAFT for D254, not a plate: dots each question; filled dots the cap mean with its 95% "
             "interval (10,000 question resamples); dotted line c90 of the all-caps fit", ha="center", fontsize=6.5)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300, metadata={"Software": None})
    plt.close(fig)
    return buf.getvalue()


def outputs(doc: dict, extra: dict) -> dict:
    return {"fit.json": (json.dumps(doc, indent=1) + "\n").encode(), "curves.csv": curves_csv(extra["curves"]).encode(),
            "draft_supp8a_fit.png": draw(doc, extra)}


def report(doc: dict) -> None:
    for label, b in doc["fits"].items():
        print(f"-- {label}")
        for s in SYSTEMS:
            m = b[s]["summary"]
            print(f"  {NAME[s]}: plateau {m['P_pct']:.1f}% [{m['P_pct_ci95'][0]:.1f}, {m['P_pct_ci95'][1]:.1f}]; "
                  f"c90 {m['c90']:.2f} [{m['c90_ci95'][0]:.2f}, {m['c90_ci95'][1]:.2f}]; m {m['m']:.2f}; "
                  f"k {m['k']:.2f}; failed {m['failed']}; at a bound {m['at_any_bound']} {m['at_bound']}; "
                  f"point on bound {b[s]['point']['on_bound']}; R2 means {b[s]['point']['r2_means']:.3f}")
        d = b["difference_G5_minus_G6"]
        print(f"  difference: plateau {d['P_pp']:.1f} pp [{d['P_pp_ci95'][0]:.1f}, {d['P_pp_ci95'][1]:.1f}]; "
              f"c90 {d['c90_caps']:.2f} [{d['c90_caps_ci95'][0]:.2f}, {d['c90_caps_ci95'][1]:.2f}] "
              f"({d['resamples_both_fitted']} resamples)")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="compare with the committed output, write nothing")
    a = ap.parse_args(argv)
    try:
        doc, extra = build()
    except Refused as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    r = doc["header"]["reproduced"]
    print(f"reproduced: S490 {r['s490_workbook_values_equal']} workbook values, 0 mismatches; paper numbers "
          + "; ".join(f"{s} {r[s]['s490']}" for s in SYSTEMS))
    report(doc)
    files = outputs(doc, extra)
    if a.check:
        diff = [k for k, v in files.items() if not (OUT / k).exists() or (OUT / k).read_bytes() != v]
        print("byte-equal" if not diff else f"DIFFERS: {diff}")
        return 0 if not diff else 1
    OUT.mkdir(parents=True, exist_ok=True)
    for k, v in files.items():
        (OUT / k).write_bytes(v)
        print(f"wrote {rel(OUT / k)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
