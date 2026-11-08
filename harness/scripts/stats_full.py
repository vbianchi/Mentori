"""The full report of each test the paper uses, in one place so every script reports it the same way.

The journal's statistics guidelines ask for the test, the statistic with its degrees of freedom,
n, the exact P, an effect size and its confidence interval. Each function takes the inputs the
analysis already has and returns a flat dict with all of them. No function decides what the paper
reports; S318 compares each result with the number printed and writes the rest beside it.

Conventions: two-sided unless the name says otherwise; 95% intervals; P is exact where the test
allows it, and the dict says which method produced it.
"""
from __future__ import annotations

import itertools
import math
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction

import numpy as np
from scipy import stats

Z = stats.norm.ppf(0.975)


def p_number_format(p: float) -> str:
    """An Excel number format that shows P in the paper's notation: exact to two significant
    figures, or "< 0.001" (the journal's Statistical Guidelines). The cell keeps the exact value."""
    if p < 0.001:
        return '"< 0.001"'
    return "0." + "0" * (1 - math.floor(math.log10(p)))       # P = 1 shows 1.0, two figures


def half_up(x: float, places: int, sep: bool = False) -> str:
    """x printed to `places` decimals, an exact half rounded up on the decimal it holds (the
    paper's decimals policy), never Python's binary rounding. sep adds the thousands separator."""
    d = Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
    return f"{d:{',' if sep else ''}.{places}f}"


def _half_up_frac(x: Fraction, places: int) -> Fraction:
    q = Fraction(10) ** places
    return Fraction(math.floor(x * q + Fraction(1, 2))) / q


def mean_of_counts(v: float, n: int, stored: int, target: int) -> float:
    """The mean behind v, a mean of whole-number counts over n that an upstream artifact stored
    rounded to `stored` decimals, fit to print once at `target` decimals.

    Every k with k/n inside v's rounding interval (ends included, so any upstream rounding mode is
    covered) is a candidate. All candidates must print the same at `target`, half up, or the value
    cannot be printed without the raw data and ValueError is raised. Returns k/n when one k fits,
    otherwise the value every candidate prints as."""
    s, h = Fraction(repr(float(v))), Fraction(1, 2 * 10 ** stored)
    ks = range(math.ceil((s - h) * n), math.floor((s + h) * n) + 1)
    shown = {_half_up_frac(Fraction(k, n), target) for k in ks}
    if len(shown) != 1:
        raise ValueError(f"{v} over n = {n} prints as {sorted(float(x) for x in shown)} at "
                         f"{target} decimals depending on the unrounded mean")
    return float(f"{ks[0] / n:.12g}") if len(ks) == 1 else float(shown.pop())


def on_a_half(v: float, target: int) -> bool:
    """True when a stored value sits exactly on a half at `target` decimals. Only then can
    rounding the stored value again differ from rounding the unrounded value once."""
    d = Decimal(repr(float(v))).normalize()
    return -d.as_tuple().exponent == target + 1 and d.as_tuple().digits[-1] == 5


def wilson(k: int, n: int) -> dict:
    lo, hi = stats.binomtest(k, n).proportion_ci(0.95, method="wilson")
    return {"test": "Wilson score interval", "k": k, "n": n, "rate": k / n, "ci_low": lo, "ci_high": hi}


def mcnemar_paired(a_only: int, b_only: int, both: int, neither: int, labels=("A", "B")) -> dict:
    """Exact McNemar on a 2x2 paired table. a_only: A passed, B failed; b_only: the reverse.

    Effect sizes: the paired difference in pass rate with a Wald interval for paired proportions
    (the interval Methods names), Cohen's h on the two marginal pass rates, and the conditional
    odds ratio a_only/b_only with an exact interval from the Clopper-Pearson interval of the
    discordant split.
    """
    n = a_only + b_only + both + neither
    d = a_only + b_only
    p = stats.binomtest(a_only, d, 0.5).pvalue if d else 1.0
    pa, pb = (a_only + both) / n, (b_only + both) / n
    diff = pa - pb
    se = math.sqrt(max(a_only + b_only - (a_only - b_only) ** 2 / n, 0)) / n
    h = 2 * math.asin(math.sqrt(pa)) - 2 * math.asin(math.sqrt(pb))
    out = {"test": "exact McNemar (two-sided binomial on discordant pairs)", "n_pairs": n,
           "discordant": d, f"{labels[0]}_only": a_only, f"{labels[1]}_only": b_only,
           "rate_" + labels[0]: pa, "rate_" + labels[1]: pb, "diff": diff,
           "diff_ci_low": diff - Z * se, "diff_ci_high": diff + Z * se, "cohens_h": h, "P": p}
    if a_only and b_only:
        ci = stats.binomtest(a_only, d).proportion_ci(0.95, method="exact")
        out.update(odds_ratio=a_only / b_only, or_ci_low=ci.low / (1 - ci.low), or_ci_high=ci.high / (1 - ci.high))
    return out


def mcnemar_from_vectors(a, b, labels=("A", "B")) -> dict:
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    return mcnemar_paired(int((a & ~b).sum()), int((~a & b).sum()), int((a & b).sum()), int((~a & ~b).sum()), labels)


def binomial_split(k: int, d: int) -> dict:
    """k of d changed outcomes in one direction, against an even split (the flip-rate test)."""
    ci = stats.binomtest(k, d).proportion_ci(0.95, method="exact")
    return {"test": "exact binomial against 0.5 (McNemar on discordant pairs)", "k": k, "discordant": d,
            "share": k / d, "share_ci_low": ci.low, "share_ci_high": ci.high,
            "P": stats.binomtest(k, d, 0.5).pvalue}


def _exact_rank_p(x, y) -> float | None:
    n = len(x)
    if n > 9:
        return None
    rx, ry = stats.rankdata(x), stats.rankdata(y)
    obs = abs(stats.spearmanr(rx, ry)[0])
    perms = list(itertools.permutations(ry))
    return sum(abs(stats.spearmanr(rx, q)[0]) >= obs - 1e-12 for q in perms) / len(perms)


def spearman(x, y) -> dict:
    """rho with average ranks for ties; exact permutation P for n <= 9, else the t approximation.
    CI by Fisher z with the Bonett-Wright standard error."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    n = len(x)
    r, p_asym = stats.spearmanr(x, y)
    p_exact = _exact_rank_p(x, y)
    out = {"test": "Spearman rank correlation", "n": n, "rho": r,
           "P": p_exact if p_exact is not None else p_asym,
           "P_method": "exact permutation" if p_exact is not None else "t approximation", "df": n - 2}
    if n > 3 and abs(r) < 1:
        se = math.sqrt((1 + r * r / 2) / (n - 3))
        out.update(ci_low=math.tanh(math.atanh(r) - Z * se), ci_high=math.tanh(math.atanh(r) + Z * se))
    return out


def pearson(x, y) -> dict:
    x, y = np.asarray(x, float), np.asarray(y, float)
    res = stats.pearsonr(x, y)
    ci = res.confidence_interval(0.95)
    return {"test": "Pearson correlation", "n": len(x), "r": res.statistic, "df": len(x) - 2,
            "P": res.pvalue, "ci_low": ci.low, "ci_high": ci.high}


def cohens_kappa(a, b) -> dict:
    """Unweighted kappa for two raters on the same items, with the large-sample standard error
    of Fleiss, Cohen and Everitt (1969) for the interval and a z test against 0."""
    a, b = np.asarray(a), np.asarray(b)
    cats = sorted(set(a) | set(b))
    n = len(a)
    t = np.array([[np.sum((a == i) & (b == j)) for j in cats] for i in cats], float) / n
    r, c = t.sum(1), t.sum(0)
    po, pe = np.trace(t), float(r @ c)
    k = (po - pe) / (1 - pe)
    s = sum(t[i, i] * (1 - (r[i] + c[i]) * (1 - k)) ** 2 for i in range(len(cats)))
    s += (1 - k) ** 2 * sum(t[i, j] * (c[i] + r[j]) ** 2 for i in range(len(cats)) for j in range(len(cats)) if i != j)
    s -= (k - pe * (1 - k)) ** 2
    se = math.sqrt(max(s, 0) / n) / (1 - pe)
    se0 = math.sqrt((pe + pe * pe - float(np.sum(r * c * (r + c)))) / n) / (1 - pe)
    return {"test": "Cohen's kappa", "n": n, "agreement": po, "kappa": k,
            "ci_low": k - Z * se, "ci_high": k + Z * se, "P": 2 * stats.norm.sf(abs(k / se0))}


def chi2_independence(table) -> dict:
    t = np.asarray(table, float)
    chi2, p, df, _ = stats.chi2_contingency(t, correction=False)
    n = t.sum()
    v = math.sqrt(chi2 / (n * (min(t.shape) - 1)))
    return {"test": "Pearson chi-square test of independence (upper tail)", "chi2": chi2, "df": int(df),
            "n": int(n), "P": p, "cramers_v": v}


def kendall_w(ranks) -> dict:
    """ranks: k raters by n objects. W without tie correction, the Friedman chi-square it implies,
    and the exact upper-tail P by enumerating every ordering of each rater after the first."""
    R = np.asarray(ranks, float)
    k, n = R.shape

    def w(M):
        s = M.sum(0)
        return 12 * float(((s - s.mean()) ** 2).sum()) / (k * k * (n ** 3 - n))
    obs = w(R)
    perms = [np.array(p) for p in itertools.permutations(range(n))]
    ge = tot = 0
    for combo in itertools.product(perms, repeat=k - 1):
        M = np.vstack([R[0]] + [R[i + 1][list(c)] for i, c in enumerate(combo)])
        ge += w(M) >= obs - 1e-12
        tot += 1
    return {"test": "Kendall's W, exact permutation (upper tail)", "k": k, "n": n, "W": obs,
            "chi2_r": k * (n - 1) * obs, "df": n - 1, "P": ge / tot}


def bootstrap_mean_diff_ci(x, y, n_boot=2000, seed=42) -> dict:
    """Paired difference of means with a percentile bootstrap over the paired units."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), (n_boot, len(x)))
    d = (x[idx] - y[idx]).mean(1)
    return {"test": "paired difference, percentile bootstrap", "n": len(x), "diff": float((x - y).mean()),
            "ci_low": float(np.percentile(d, 2.5)), "ci_high": float(np.percentile(d, 97.5)), "n_boot": n_boot}
