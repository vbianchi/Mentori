"""S619: experiments/draws.csv held to S492's answer registry, every run, before Supplementary Figure 1 is drawn.

WHY. draws.csv is kept by hand. Its design, draws and answers fields feed the Supplementary Figure 1 boxes (S496 reads
the S616 extract findings/recompute/fig_design_inputs/draws.csv, the same rows), and the letter says every number in
the revised paper is printed by a script. Audit 2026-11-09 A28 found four box labels that contradict the counts:
Distiller intervention "7 prompt variants" (2 were run), Component benchmarks and Always distil (stress) "1 draw"
(gemini-3-flash ran three times; the stress set-ups ran draws 2 and 3 on 45 questions). Nothing compared the two.

WHAT IT DOES. For every draws.csv row it reads the row's text the way the plate reads it (S496's own draw_kind,
plain_design and designs(), imported, so the check never drifts from the plate) and compares it with what the artifacts
hold, recomputed on every run:
  rows      draws.csv's experiments are the registry's experiments plus its two kept from April, once each.
  draws     the plate's draw words ("3 draws", "1 + 2 draws", "1 draw") against the registry's per-draw counts:
            3 draws = draws 1, 2, 3, equal; 1 + 2 draws = draws 1, 2, 3, draw 2 equal to draw 3 and below draw 1;
            1 draw = draw 1 only. A registry with no draw field (S2, S12) is reported as not confirmable.
  answers   the first number of the answers field against the registry's stored count (kept rows: submitted
            evaluations against the registry's kept count; S12, which stores no answer of its own, against its
            design product), and the field's own arithmetic, e.g. "1,164 (5 x 2 x 97 + 194)", against that number.
  design.*  each design factor ("7 prompt variants", "models", "832 items") against the count the records name
            where they can confirm it: the sinks and runs the registry lists (prompts, models, components,
            strategies, generators, set-ups, indexes, caps, arms), the T3 MANIFEST's answers per sink (items), S18f's
            analysis set (S12's answers). A factor with no number takes the confirmed count.
  design    the product of the factors against the registry's draw-1 count (or the stored count where the registry
            has no draws, or the "N answers per draw" the design states), so "7 x 6 x 97 = 4,074" fails beside 1,164.
Items for T3 are the STORED items (832, 97): Supplementary Figure 1 counts answers stored (S496 prints the registry's
stored count in the box), so the design line must multiply to that count (832 x 8 = 6,656; 2 x 6 x 97 = 1,164). The
analysed items (814, 94: D213 leaves out the 18 and 3 items built on the six questions D9 replaced) are read from
Supplementary Figures 10 and 11's numbers files and reported beside them, never checked against the box.

A disagreement names the row, the field, what draws.csv says, what the artifacts hold and where that was read. The
check does not edit draws.csv.

REPRODUCE FIRST (README.md:75-79): before any comparison the registry's own sums are reproduced (stored_new_counted,
total_counted, by_experiment) and T3's MANIFEST answers per sink are summed back to the registry's two T3 counts.
A failure there refuses (exit 2) and nothing is judged.

  uv run python scripts/S619_draws_registry_check.py            # both draws.csv files, writes the report
  uv run python scripts/S619_draws_registry_check.py --no-write # S494's supp1 pre-step: prints, writes nothing
  uv run python scripts/S619_draws_registry_check.py --selftest # synthetic draws.csv and registry

Inputs: experiments/draws.csv; findings/recompute/fig_design_inputs/draws.csv (what the plate reads);
findings/recompute/S492_answer_registry/registry.json; T3's MANIFEST.json in the frozen set count_records_20261106
(fig_repro.frozen, sha256 checked); findings/figures_provisional/supp_fig10_components/supplementary_figure10_numbers.json
and supp_fig11_distiller_prompts/supplementary_figure11_numbers.json (analysed items, reported only);
findings/recompute/S18f_v25_results.json (S12's answers); findings/figures_provisional/fig1/figure1_provenance.json
(which boxes take draws.csv's design, through S496.designs()).
Outputs: findings/recompute/S619_draws_registry/report.md and report.json (no timestamp: a rerun on the same inputs
writes the same bytes). Exit 0 when every row agrees, 1 on any disagreement, 2 when refused.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import io
import json
import re
import sys
import tempfile
from collections import Counter
from math import prod
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

SCRIPT = "scripts/S619_draws_registry_check.py"
OUT = ROOT / "findings" / "recompute" / "S619_draws_registry"
DRAWS_FILES = [ROOT / "findings" / "recompute" / "fig_design_inputs" / "draws.csv",   # what S496 reads (fig_design)
               ROOT / "experiments" / "draws.csv"]                                    # the working file it is cut from
REGISTRY = ROOT / "findings" / "recompute" / "S492_answer_registry" / "registry.json"
T3_SET = "count_records_20261106"
T3_MANIFEST_REL = "count_records_20261106/t3/T3_frozen_20261104T131439Z/MANIFEST.json"
SUPP10 = ROOT / "findings/figures_provisional/supp_fig10_components/supplementary_figure10_numbers.json"
SUPP11 = ROOT / "findings/figures_provisional/supp_fig11_distiller_prompts/supplementary_figure11_numbers.json"
S18F = ROOT / "findings" / "recompute" / "S18f_v25_results.json"
GEMINI = "gemini-3-flash-preview"

WORDS = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve".split())}
UNIT = ("questions", "items", "operations", "answers")   # the factor that counts the units one cell is asked


class Refused(Exception):
    pass


def rel(p: Path) -> str:
    try:
        return Path(p).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(p)


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def s496():
    """S496, imported: its draw_kind, plain_design and designs() are the plate's reading of draws.csv."""
    return importlib.import_module("S496_supp_fig1_experiment_graph")


# ---------------------------------------------------------------------------------------------------------------
# Reading draws.csv's text
# ---------------------------------------------------------------------------------------------------------------
def num(tok: str) -> int | None:
    tok = tok.strip().lower()
    if re.fullmatch(r"\d[\d,]*", tok):
        return int(tok.replace(",", ""))
    return WORDS.get(tok)


def strip_parens(text: str) -> str:
    prev = None
    while prev != text:
        prev, text = text, re.sub(r"\([^()]*\)", "", text)
    return re.sub(r"\s+", " ", text).strip()


def factors(design: str) -> list[dict]:
    """draws.csv's design as factors [{n, label}], parentheticals removed: "7 prompt variants x models x 97 items" ->
    (7, prompt variants), (None, models), (97, items). A bare number is the questions factor ("x 135")."""
    out = []
    for part in strip_parens(design).split(" x "):
        part = re.sub(r"^Figure \d+'s\s+", "", part.strip())
        m = re.match(r"^(\d[\d,]*|[a-z]+)\b\s*(.*)$", part)
        n = num(m.group(1)) if m else None
        label = (m.group(2) if n is not None else part).strip()
        label = re.split(r"\s+(?:on|at|with|given)\s+|\s+per\s+(?=size)", label)[0] if n is not None else label
        out.append({"n": n, "label": label or "questions", "text": part})
    return out


def is_unit(label: str) -> bool:
    return label.startswith(UNIT)


def answers_first(text: str) -> int | None:
    m = re.match(r"\s*(\d[\d,]*)", text or "")
    return int(m.group(1).replace(",", "")) if m else None


def answers_arith(text: str) -> tuple[str, int] | None:
    """The answers field's arithmetic, "(5 x 2 x 97 + 194)" or "(860 x 3; ...)": (expression, value), else None."""
    m = re.search(r"\(([^;)]*)", text or "")
    if not m:
        return None
    expr = re.sub(r"(\d)\s+(?!x\b)[A-Za-z][\w-]*", r"\1", m.group(1)).strip()
    if not re.fullmatch(r"\d[\d,]*(\s*[x+]\s*\d[\d,]*)+", expr):
        return None
    return expr, sum(prod(int(t.replace(",", "")) for t in term.split("x")) for term in expr.split("+"))


def per_draw_stated(design: str) -> int | None:
    m = re.search(r"(\d[\d,]*) answers per draw", design or "")
    return int(m.group(1).replace(",", "")) if m else None


def questions_in_draws(draws: str) -> int | None:
    m = re.match(r"\s*1 on (\d+) questions", draws or "")
    return int(m.group(1)) if m else None


# ---------------------------------------------------------------------------------------------------------------
# What the records confirm, per experiment
# ---------------------------------------------------------------------------------------------------------------
def files(e: dict) -> list[str]:
    return list((e.get("files_sha256") or {}).keys())


def distinct(e: dict, pattern: str, group: int = 1, only: str | None = None) -> set:
    got = set()
    for f in files(e):
        if only and only not in f:
            continue
        m = re.search(pattern, f)
        if m:
            got.add(m.group(group) if isinstance(group, int) else tuple(m.group(g) for g in group))
    return got


def t3_items(manifest: dict, prefix: str) -> dict:
    """{part: items} for T3's sinks under prefix ("exp_04", "exp_04b"), and {model: draws}: each part's items are its
    rows in a single-draw model's sink; a model's draws are its rows over the items. Refused when they do not divide."""
    per = {k: v for k, v in manifest["answers_per_sink"].items() if k.split("__")[0] == prefix}
    parts = sorted({k.split("__")[1] for k in per})
    models = sorted({k.split("__")[2] for k in per})
    items = {p: min(per[f"{prefix}__{p}__{m}"] for m in models) for p in parts}
    draws = {}
    for m in models:
        ratios = {per[f"{prefix}__{p}__{m}"] / items[p] for p in parts}
        if len(ratios) != 1 or not float(next(iter(ratios))).is_integer():
            raise Refused(f"T3 {prefix} {m}: rows per sink {[per[f'{prefix}__{p}__{m}'] for p in parts]} are not one "
                          f"whole number of draws of the items {items}")
        draws[m] = int(next(iter(ratios)))
    # exp_04's components each ask their own items, so the experiment's items are their sum; exp_04b's prompts ask the
    # same distiller items, so its items are the one count every prompt holds
    if prefix == "exp_04b":
        if len(set(items.values())) != 1:
            raise Refused(f"T3 {prefix}: the prompts hold different item counts {items}")
        n_items = next(iter(items.values()))
    else:
        n_items = sum(items.values())
    return {"parts": parts, "models": models, "items": items, "n_items": n_items, "draws": draws,
            "rows": sum(per.values())}


def analysed(path: Path, by_prompt: bool) -> dict | None:
    """Supplementary Figure 10 or 11's analysed answers per (model, draw), and the items that gives (reported only)."""
    if not path.exists():
        return None
    c = Counter()
    for r in json.loads(path.read_text())["counts"]:
        c[(r["model"], r["draw"])] += r["stored"]
    vals = set(c.values())
    if len(vals) != 1:
        return {"source": rel(path), "per_model_draw": sorted(vals), "items": None}
    v = vals.pop()
    parts = {r["part"] for r in json.loads(path.read_text())["counts"]}
    return {"source": rel(path), "answers": sum(c.values()), "items": v // len(parts) if by_prompt else v,
            "parts": sorted(parts)}


def confirmers(e: dict, ctx: dict) -> dict:
    """{factor label: (count, where read)} the records confirm for experiment e (its plan row and name)."""
    row, name = e["plan_row"], e["experiment"]
    src = "registry files_sha256 of " + name
    c = {}

    def put(label, values, where=src):
        if values:
            c[label] = (len(values), where, sorted(map(str, values)))

    if row == "T3":
        t = ctx["t3"]["exp_04b" if name == "Distiller intervention" else "exp_04"]
        where = f"{ctx['t3_source']} answers_per_sink"
        c["prompt variants" if name == "Distiller intervention" else "components"] = (len(t["parts"]), where, t["parts"])
        c["models"] = (len(t["models"]), where, t["models"])
        c["items"] = (t["n_items"], where + " (stored items: rows of a one-draw model's sink)",
                      [f"{k} {v}" for k, v in t["items"].items()])
    elif row == "T2":
        put("generators", distinct(e, r"/t2x?/([^/]+)/runs/"))
        put("strategies", distinct(e, r"/runs/exp_01__([a-z0-9_]+?)__exp"))
    elif row == "S2":
        put("model variants", distinct(e, r"/runs/exp_05__.+?__([^/]+)/"))
        put("strategies", distinct(e, r"/runs/exp_05__(.+?)__[^/]+/"))
        runs = distinct(e, r"/runs/([^/]+)/answers")
        if runs and e["stored"] % len(runs) == 0:
            c["operations"] = (e["stored"] // len(runs), src + f" (stored {e['stored']:,} / {len(runs)} runs)", [])
    elif row == "G1" or (row == "I2"):
        put("strategies", distinct(e, r"(?:s457_mirror_\d+|exp_01__)/?([a-z0-9_]+?)(?:/answers|__i2)"))
    elif row == "G6":
        put("caps", distinct(e, r"__cap(\d+)__"))
    elif row in ("G3", "G9"):
        key = "baselines" if name == "No retrieval and naive RAG" else "set-ups"
        vals = distinct(e, r"/runs/exp_03__([a-z0-9_]+?)__exp", only="count_records_")
        if name == "Pipeline ablation" and vals and "G9" in ctx.get("by_row", {}):
            # Valerio, 11 Nov (Q1): the pipeline ablation has 8 set-ups, as the manuscript says: its 6 runs and the 2
            # distiller set-ups of G9 (always distil, always distil Ex), which the registry files under their own row
            g9 = distinct(ctx["by_row"]["G9"], r"/runs/exp_03__([a-z0-9_]+?)__exp", only="count_records_")
            vals = sorted(set(vals) | set(g9))
            src = src + " and Distiller on every step (stress)"
        put(key, vals, src)
    elif row == "G4":
        put("indexes", distinct(e, r"__exp_v4_(s\d+_n\d+)/"))
        put("strategies", distinct(e, r"exp_02_scaling_factorial__([a-z0-9_]+?)__exp"))
    elif row == "G10":
        put("indexes", distinct(e, r"__exp_v4_(s\d+_n\d+)/answers"))
    elif row in ("G17", "G19"):
        put("arms", distinct(e, r"/runs/([^/]+)/answers"))
    elif row == "S12" and ctx.get("s18f"):
        c["answers"] = (ctx["s18f"]["answers"], ctx["s18f"]["source"] + " analysis_set.answers", [])
    return c


def match_label(label: str, conf: dict) -> str | None:
    for k in conf:
        if label == k or label.endswith(" " + k) or label.endswith(k):
            return k
    return None


# ---------------------------------------------------------------------------------------------------------------
# The check
# ---------------------------------------------------------------------------------------------------------------
def reproduce(reg: dict, ctx: dict) -> list[str]:
    """Known numbers first: the registry's own sums, and T3's MANIFEST summed back to the registry's T3 counts."""
    t = reg["today"]
    counted = sum(e["stored"] for e in t["experiments"] if e["counted"])
    by = {f"{e['experiment']} ({e['plan_row']})": e["stored"] for e in t["experiments"]}
    checks = [("stored_new_counted", counted, t["stored_new_counted"]),
              ("total_counted", counted + sum(t["kept_from_april"].values()), t["total_counted"]),
              ("by_experiment", by, t["by_experiment"])]
    for e in t["experiments"]:
        if e.get("draws"):
            checks.append((f"{e['experiment']} draws sum", sum(e["draws"].values()), e["stored"]))
    if ctx.get("t3"):
        reg_t3 = {e["experiment"]: e["stored"] for e in t["experiments"] if e["plan_row"] == "T3"}
        checks += [("T3 MANIFEST exp_04 rows = registry Component benchmarks", ctx["t3"]["exp_04"]["rows"],
                    reg_t3.get("Component benchmarks")),
                   ("T3 MANIFEST exp_04b rows = registry Distiller intervention", ctx["t3"]["exp_04b"]["rows"],
                    reg_t3.get("Distiller intervention"))]
    bad = [f"{w}: {g!r} against {k!r}" for w, g, k in checks if g != k]
    if bad:
        raise Refused("reproduce-first failed, nothing judged: " + "; ".join(bad))
    return [f"{w}: reproduced" for w, _, _ in checks]


def check_rows(rows: list[dict], reg: dict, ctx: dict, mod, plate_csv: set) -> tuple[list, list]:
    """(disagreements, notes) for one draws.csv. Each disagreement: experiment, plan_row, field, draws_csv, artifacts,
    source, plate_reads."""
    t = reg["today"]
    reg_by = {(e["plan_row"], e["experiment"]): e for e in t["experiments"]}
    ctx = {**ctx, "by_row": {e["plan_row"]: e for e in t["experiments"]}}
    kept = t["kept_from_april"]
    bad, notes = [], []

    def fail(r, field, said, holds, source, plate):
        bad.append({"experiment": r["experiment"], "plan_row": r["plan_row"], "field": field, "draws_csv": said,
                    "artifacts": holds, "source": source, "plate_reads": plate})

    csv_keys = [(r["plan_row"], r["experiment"]) for r in rows]
    want = sorted(list(reg_by) + [("", k) for k in kept])
    dup = [k for k, n in Counter(csv_keys).items() if n > 1]
    for k in sorted(set(want) - set(csv_keys)):
        bad.append({"experiment": k[1], "plan_row": k[0], "field": "row", "draws_csv": "(no row)",
                    "artifacts": "an experiment in the registry", "source": rel(REGISTRY), "plate_reads": "yes"})
    for k in sorted(set(csv_keys) - set(want)) + dup:
        bad.append({"experiment": k[1], "plan_row": k[0], "field": "row", "draws_csv": "a row" + (" twice" if k in dup
                    else ""), "artifacts": "no such experiment in the registry (once)", "source": rel(REGISTRY),
                    "plate_reads": "yes"})

    for r in rows:
        key = (r["plan_row"], r["experiment"])
        e = reg_by.get(key)
        design_on_plate = "yes" if key in plate_csv else "no (the plate takes Figure 1's design)"
        if e is None:
            if r["experiment"] in kept:
                se = r.get("submitted_evaluations")
                if se not in (None, "") and int(se.replace(",", "")) != kept[r["experiment"]]:
                    fail(r, "submitted_evaluations", se, kept[r["experiment"]], rel(REGISTRY) + " today.kept_from_april",
                         "no")
                if (r["draws"] or "").strip() not in ("", "0"):
                    fail(r, "draws", r["draws"], "no draws: kept from April, not re-run", rel(REGISTRY), "yes")
            continue
        src = f"{rel(REGISTRY)} {r['experiment']} ({r['plan_row']})"
        d = {int(k): v for k, v in (e.get("draws") or {}).items()}

        # draws, as the plate words them
        try:
            kind = mod.draw_kind(r["draws"])
        except Exception:                                       # S496 refuses the text: the plate does not read it
            kind = None
            notes.append(f"{r['experiment']} ({r['plan_row']}): draws {r['draws'][:60]!r} is not a plate form "
                         f"(S496 takes this box's draws from Figure 1's facts); draws not compared")
        if kind and not d:
            notes.append(f"{r['experiment']} ({r['plan_row']}): draws.csv '{kind}', the registry holds no draw field "
                         f"({(e.get('special_case') or e['basis'])[:90]}); not confirmable")
        elif kind:
            holds = ", ".join(f"draw {k} {v:,}" for k, v in sorted(d.items()))
            # 11 Nov: '1 (<model> 3)' is one draw with one model drawn three times (N-5, Valerio 10 Nov: the plate prints
            # '1 draw; gemini-3-flash 3'); draws 2 and 3 then hold that model's answers only. Draw 2 may exceed draw 3 by
            # answers the sheet states itself (Pipeline ablation: '+ 23' draw-2 answers without the supervisor).
            one_model_three = kind == "1 draw" and re.search(r"\(\S+ 3\)", r["draws"] or "") is not None
            extra = re.search(r"\+ (\d+)\s*[;)]", r["answers"] or "")   # the last term of '1,373 (6 x 135 + ... + 23; ...)'
            extra = int(extra.group(1)) if extra else 0
            ok = {"3 draws": sorted(d) == [1, 2, 3] and len(set(d.values())) == 1,
                  "1 + 2 draws": sorted(d) == [1, 2, 3] and d[2] - d[3] in (0, extra) and d[3] < d[1],
                  "1 draw": sorted(d) == [1] or (one_model_three and sorted(d) == [1, 2, 3] and d[2] == d[3] < d[1])}[kind]
            if not ok:
                fail(r, "draws", f"{r['draws']} (plate: '{kind}')", holds, src + " draws", "yes")

        # answers
        first = answers_first(r["answers"])
        if e.get("special_case") and e["stored"] == 0:
            notes.append(f"{r['experiment']} ({r['plan_row']}): stores no answer of its own (registry special_case); "
                         f"answers {r['answers']!r} checked against its design below")
        elif first != e["stored"]:
            fail(r, "answers", r["answers"], f"{e['stored']:,} stored", src + " stored", "no (the box prints the "
                 "registry's count)")
        ar = answers_arith(r["answers"])
        if ar and ar[1] != first:
            fail(r, "answers arithmetic", f"{r['answers']} ({ar[0]} = {ar[1]:,})", f"{first:,} stated",
                 "draws.csv answers field itself", "no")

        # design factors
        conf = confirmers(e, ctx)
        fs = factors(r["design"])
        used = set()
        resolved = []
        for f in fs:
            k = match_label(f["label"], conf)
            if k:
                used.add(k)
                n_conf, where, members = conf[k]
                if f["n"] is not None and f["n"] != n_conf:
                    fail(r, f"design.{k}", f["text"], f"{n_conf:,}" + (f" ({', '.join(members)})" if members else ""),
                         where, design_on_plate)
                resolved.append(f["n"] if f["n"] is not None else n_conf)
            else:
                resolved.append(f["n"] if f["n"] is not None else (1 if len(fs) == 1 else None))
        if not any(is_unit(f["label"]) for f in fs) and questions_in_draws(r["draws"]):
            resolved.append(questions_in_draws(r["draws"]))
        stated_pd = per_draw_stated(r["design"])
        if None in resolved and stated_pd is None:
            notes.append(f"{r['experiment']} ({r['plan_row']}): design {strip_parens(r['design'])!r} has a factor the "
                         f"records here cannot count; its product not compared")
            continue
        p = stated_pd if None in resolved else prod(resolved)
        expr = (f"{stated_pd:,} answers per draw (stated)" if None in resolved else
                " x ".join(f"{x:,}" for x in resolved) + f" = {p:,}")
        if e.get("special_case") and e["stored"] == 0:
            target, what = first, "answers stated"
        elif d and kind is not None:
            target, what = d.get(1), "draw 1"
            if r["experiment"] == "Pipeline ablation" and "G9" in ctx.get("by_row", {}):
                # Valerio, 11 Nov (Q1): 8 set-ups, the 2 distiller set-ups' answers filed under G9
                g9 = {int(k): v for k, v in (ctx["by_row"]["G9"].get("draws") or {}).items()}
                target, what = target + g9.get(1, 0), "draw 1, with Distiller on every step (stress)"
        elif d:                                                 # T2: mixed draws, no plate form
            continue
        else:
            target, what = e["stored"], "stored (no draw field)"
        if target is not None and p != target:
            fail(r, "design", f"{r['design']} ({expr})", f"{target:,} ({what})", src, design_on_plate)
    return bad, notes


def items_decision(ctx: dict) -> list[dict]:
    """T3's stored and analysed items, side by side, with the reading the check applies."""
    out = []
    for name, prefix, an in (("Component benchmarks", "exp_04", ctx.get("supp10")),
                             ("Distiller intervention", "exp_04b", ctx.get("supp11"))):
        t = ctx["t3"][prefix]
        out.append({"experiment": name, "stored_items": t["n_items"], "stored_items_by_part": t["items"],
                    "draws_by_model": t["draws"], "analysed_items": an and an.get("items"),
                    "analysed_source": an and an["source"], "analysed_answers": an and an.get("answers")})
    return out


def load_ctx(manifest_path: Path | None, supp10: Path, supp11: Path, s18f: Path) -> dict:
    import fig_repro
    if manifest_path is None:
        try:
            manifest_path = fig_repro.frozen(T3_SET, T3_MANIFEST_REL)
        except fig_repro.FrozenInputError as e:
            raise Refused(f"T3 MANIFEST: {e}")
        t3_source = f"frozen:{T3_SET}.tar/{T3_MANIFEST_REL}"
    else:
        t3_source = rel(manifest_path)
    man = json.loads(Path(manifest_path).read_text())
    ctx = {"t3": {p: t3_items(man, p) for p in ("exp_04", "exp_04b")}, "t3_source": t3_source,
           "t3_manifest_sha256": sha(manifest_path), "supp10": analysed(supp10, False),
           "supp11": analysed(supp11, True), "inputs": {t3_source: sha(manifest_path)}}
    for p in (supp10, supp11, s18f):
        if Path(p).exists():
            ctx["inputs"][rel(p)] = sha(p)
    if Path(s18f).exists():
        a = json.loads(Path(s18f).read_text()).get("analysis_set") or {}
        if "answers" in a:
            ctx["s18f"] = {"answers": a["answers"], "source": rel(s18f)}
    return ctx


def plate_csv_rows(mod, rows) -> set:
    """(plan_row, experiment) of the boxes whose design line S496 takes from draws.csv (designs() returns none)."""
    try:
        prov = json.loads(mod.FIG1_PROV.read_text())
        des = mod.designs(prov, rows)
    except Exception as e:                                       # noqa: BLE001
        print(f"note: S496.designs() could not be read ({type(e).__name__}: {e}); every design marked as read", flush=True)
        return {(b[1], b[2]) for b in mod.BOXES if b[1] is not None}
    return {(b[1], b[2]) for b in mod.BOXES if b[1] is not None and not des.get(b[0])}


def run(draws_files: list[Path], registry: Path, ctx: dict, mod) -> dict:
    reg = json.loads(Path(registry).read_text())
    repro = reproduce(reg, ctx)
    result = {"files": {}, "reproduced": repro}
    for f in draws_files:
        rows = list(csv.DictReader(io.StringIO(Path(f).read_text(), newline="")))
        bad, notes = check_rows(rows, reg, ctx, mod, plate_csv_rows(mod, rows))
        result["files"][rel(f)] = {"sha256": sha(f), "rows": len(rows), "disagreements": bad, "notes": notes}
    result["t3_items"] = items_decision(ctx)
    return result


def render_md(res: dict, header: dict) -> str:
    L = ["# S619: draws.csv against the answer registry", "",
         f"Script `{header['script']}` (sha256 `{header['script_sha256'][:12]}`), command `{header['command']}`.", "",
         "Inputs (sha256):", ""]
    L += [f"- `{k}` `{v[:12]}`" for k, v in header["inputs"].items()]
    L += ["", "Reproduced first: " + "; ".join(res["reproduced"]) + ".", ""]
    groups = {}
    for f, v in res["files"].items():
        groups.setdefault(json.dumps(v["disagreements"], sort_keys=True), []).append(f)
    for blob, fs in groups.items():
        bad = json.loads(blob)
        L += [f"## {len(bad)} disagreements in " + " and ".join(f"`{f}`" for f in fs), ""]
        if bad:
            L += ["| Experiment (plan row) | Field | draws.csv says | The artifacts hold | Read from | The plate reads it |",
                  "|---|---|---|---|---|---|"]
            for b in bad:
                cells = [f"{b['experiment']} ({b['plan_row']})", b["field"], str(b["draws_csv"]), str(b["artifacts"]),
                         b["source"], b["plate_reads"]]
                L.append("| " + " | ".join(c.replace("|", "/").replace("\n", " ") for c in cells) + " |")
            L.append("")
    notes = res["files"][next(iter(res["files"]))]["notes"]
    if notes:
        L += ["## Not compared", ""] + [f"- {n}" for n in notes] + [""]
    L += ["## T3 items: stored or analysed", "",
          "The Supplementary Figure 1 box prints the registry's stored count, so its design line must multiply to the "
          "stored items. The analysed items are Supplementary Figures 10 and 11's and Methods' (D213 leaves out the "
          "items built on the six questions D9 replaced). This check holds draws.csv to the stored items.", "",
          "| Experiment | Stored items | Draws per model | Analysed items | Analysed read from |", "|---|---|---|---|---|"]
    for t in res["t3_items"]:
        dm = Counter(t["draws_by_model"].values())
        dtxt = ", ".join(f"{n} model{'s' if n > 1 else ''} x {k}" for k, n in sorted(dm.items()))
        L.append(f"| {t['experiment']} | {t['stored_items']:,} ({', '.join(f'{k} {v}' for k, v in t['stored_items_by_part'].items())}) "
                 f"| {dtxt} | {t['analysed_items'] if t['analysed_items'] is not None else 'not read'} | "
                 f"{t['analysed_source'] or ''} |")
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--draws", action="append", type=Path, help="a draws.csv to check (repeatable; default both)")
    ap.add_argument("--registry", type=Path, default=REGISTRY)
    ap.add_argument("--t3-manifest", type=Path, default=None, help="T3 MANIFEST.json (default: the frozen set's)")
    ap.add_argument("--supp10", type=Path, default=SUPP10)
    ap.add_argument("--supp11", type=Path, default=SUPP11)
    ap.add_argument("--s18f", type=Path, default=S18F)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--no-write", action="store_true", help="print the verdict only (S494's supp1 pre-step)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    draws_files = a.draws or DRAWS_FILES
    try:
        mod = s496()
        ctx = load_ctx(a.t3_manifest, a.supp10, a.supp11, a.s18f)
        res = run(draws_files, a.registry, ctx, mod)
    except (Refused, FileNotFoundError, KeyError) as e:
        print(f"S619 REFUSED: {e}", file=sys.stderr)
        return 2
    inputs = {rel(f): sha(f) for f in draws_files}
    inputs[rel(a.registry)] = sha(a.registry)
    inputs.update(ctx["inputs"])
    inputs["scripts/S496_supp_fig1_experiment_graph.py"] = sha(ROOT / "scripts/S496_supp_fig1_experiment_graph.py")
    header = {"script": SCRIPT, "script_sha256": sha(Path(__file__)), "command": "uv run python " + SCRIPT,
              "inputs": inputs}
    n_bad = sum(len(v["disagreements"]) for v in res["files"].values())
    for f, v in res["files"].items():
        print(f"{f}: {v['rows']} rows, {len(v['disagreements'])} disagreements")
        for b in v["disagreements"]:
            print(f"  FAIL {b['experiment']} ({b['plan_row']}) {b['field']}: draws.csv {b['draws_csv']!r}; "
                  f"artifacts {b['artifacts']!r} [{b['source']}]")
    if not a.no_write:
        a.out.mkdir(parents=True, exist_ok=True)
        (a.out / "report.json").write_text(json.dumps({"header": header, **res}, indent=1, ensure_ascii=False) + "\n")
        (a.out / "report.md").write_text(render_md(res, header))
        print(f"wrote {rel(a.out / 'report.md')} and report.json")
    print("S619: " + ("PASS, draws.csv agrees with the registry" if n_bad == 0 else f"FAIL, {n_bad} disagreements"))
    return 1 if n_bad else 0


# ---------------------------------------------------------------------------------------------------------------
# Self-test: a synthetic registry, MANIFEST and draws.csv
# ---------------------------------------------------------------------------------------------------------------
def selftest() -> int:
    mod = s496()
    models = ["m-a", "m-b", GEMINI]
    manifest = {"answers_per_sink": {}}
    for m in models:
        for p, n in (("analyzer", 10), ("planner", 4)):
            manifest["answers_per_sink"][f"exp_04__{p}__{m}"] = n * (3 if m == GEMINI else 1)
        for p in ("baseline", "F1"):
            manifest["answers_per_sink"][f"exp_04b__{p}__{m}"] = 5

    def ent(name, row, draws, fs, **kw):
        return {"experiment": name, "plan_row": row, "counted": True, "stored": sum(draws.values()) if draws else
                kw.pop("stored"), "draws": {str(k): v for k, v in draws.items()} if draws else None, "basis": "synthetic",
                "files_sha256": {f: "0" * 64 for f in fs}, **kw}

    exps = [ent("Generation strategies", "G1", {1: 12, 2: 12, 3: 12},
                [f"s457_mirror_1.tar:s457_mirror_1/{s}/answers.jsonl" for s in ("single_pass", "rlm_10")]),
            ent("Distiller on every step (stress)", "G9", {1: 12, 2: 4, 3: 4},
                [f"x.tar:x/g3/runs/exp_03__{s}__exp_v4_s20_n0/answers.json" for s in ("d1", "d2")]
                + ["count_records_9.tar:count_records_9/g3/runs/exp_03__d1__exp_v4_s20_n0/answers.json",
                   "count_records_9.tar:count_records_9/g3/runs/exp_03__d2__exp_v4_s20_n0/answers.json"]),
            ent("Component benchmarks", "T3", {1: 42, 2: 14, 3: 14}, ["t3/sinks/exp_04__analyzer__m-a/answers.jsonl"]),
            ent("Distiller intervention", "T3", {1: 30}, ["t3/sinks/exp_04b__F1__m-a/answers.jsonl"])]
    kept = {"Model selection": 7}
    total = sum(e["stored"] for e in exps)
    reg = {"today": {"experiments": exps, "kept_from_april": kept, "stored_new_counted": total,
                     "total_counted": total + 7, "not_counted": [],
                     "by_experiment": {f"{e['experiment']} ({e['plan_row']})": e["stored"] for e in exps}}}
    cols = ["experiment", "submitted_id", "submitted_evaluations", "figure", "plan_row", "design", "draws", "answers",
            "status", "basis"]
    good = [["Model selection", "exp00", "7", "Supp", "", "not re-run", "0", "0", "not re-run", "kept"],
            ["Generation strategies", "exp04", "0", "Fig 3", "G1", "2 strategies x 6 questions", "3", "36 (12 x 3)",
             "done", "s"],
            ["Distiller on every step (stress)", "new", "0", "Fig 4", "G9", "2 set-ups x 6 questions",
             "1, and 2 and 3 on a fixed third (D98)", "20 (12 + 2 x 4)", "done", "s"],
            ["Component benchmarks", "exp07", "0", "Supp", "T3", "models x 14 items (over 2 components)",
             "1, and 2 and 3 on a fixed third (D98)", "70", "done", "s"],
            ["Distiller intervention", "exp07b", "0", "Supp", "T3", "2 prompt variants x models x 5 items", "1",
             "30 (2 x 3 x 5)", "done", "s"]]
    # The synthetic T3C row takes the "1 + 2" draws form (draws 2 and 3 equal, below draw 1) so the good file passes;
    # the real row's "1 (Gemini 3)", which the plate prints as "1 draw", is the case a28_one_draw must catch.
    cases = {
        # the real T3C shape: the items already sum over the components, so components x models x items overcounts
        "components_double_count": ([r if r[0] != "Component benchmarks" else
                                     r[:5] + ["orchestrator components x models x 14 items"] + r[6:] for r in good],
                                    {("Component benchmarks", "design")}),
        "good": (good, set()),
        "a28_prompts": ([r if r[0] != "Distiller intervention" else r[:5] + ["7 prompt variants x models x 5 items"]
                         + r[6:] for r in good], {("Distiller intervention", "design.prompt variants"),
                                                  ("Distiller intervention", "design")}),
        "a28_one_draw": ([r if r[0] not in ("Component benchmarks", "Distiller on every step (stress)")
                          else r[:6] + ["1" if r[4] == "T3" else "1 (D98)"] + r[7:] for r in good],
                         {("Component benchmarks", "draws"), ("Distiller on every step (stress)", "draws")}),
        "items": ([r if r[0] != "Component benchmarks" else r[:5] + ["orchestrator components x models x 13 items"]
                   + r[6:] for r in good], {("Component benchmarks", "design.items"), ("Component benchmarks", "design")}),
        "answers": ([r if r[0] != "Generation strategies" else r[:7] + ["35 (12 x 3)"] + r[8:] for r in good],
                    {("Generation strategies", "answers"), ("Generation strategies", "answers arithmetic")}),
        "kept": ([r if r[0] != "Model selection" else r[:2] + ["8"] + r[3:] for r in good],
                 {("Model selection", "submitted_evaluations")}),
        "missing_row": (good[:-1], {("Distiller intervention", "row")}),
        "strategies": ([r if r[0] != "Generation strategies" else r[:5] + ["3 strategies x 4 questions"] + r[6:]
                        for r in good], {("Generation strategies", "design.strategies")}),
    }
    fails = 0
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "registry.json").write_text(json.dumps(reg))
        (td / "MANIFEST.json").write_text(json.dumps(manifest))
        ctx = load_ctx(td / "MANIFEST.json", td / "none10.json", td / "none11.json", td / "none18f.json")
        for name, (rows, want) in cases.items():
            p = td / f"{name}.csv"
            buf = io.StringIO()
            w = csv.writer(buf, lineterminator="\n")
            w.writerow(cols)
            w.writerows(rows)
            p.write_text(buf.getvalue())
            res = run([p], td / "registry.json", ctx, mod)
            got = {(b["experiment"], b["field"]) for b in res["files"][rel(p)]["disagreements"]}
            ok = got == want
            fails += not ok
            print(f"{'ok  ' if ok else 'FAIL'} {name}: {sorted(got)}" + ("" if ok else f" (expected {sorted(want)})"))
        # reproduce-first: a registry whose sums do not add up is refused
        bad_reg = json.loads(json.dumps(reg))
        bad_reg["today"]["stored_new_counted"] += 1
        (td / "bad_registry.json").write_text(json.dumps(bad_reg))
        try:
            run([td / "good.csv"], td / "bad_registry.json", ctx, mod)
            print("FAIL refused: a registry with a wrong sum was judged")
            fails += 1
        except Refused:
            print("ok   refused: a registry with a wrong sum is refused before any comparison")
        # T3 MANIFEST that does not add up to the registry is refused
        m2 = json.loads(json.dumps(manifest))
        m2["answers_per_sink"]["exp_04b__F1__m-a"] = 10
        (td / "M2.json").write_text(json.dumps(m2))
        try:
            run([td / "good.csv"], td / "registry.json", load_ctx(td / "M2.json", td / "n", td / "n", td / "n"), mod)
            print("FAIL refused: a MANIFEST off the registry was judged")
            fails += 1
        except Refused:
            print("ok   refused: a MANIFEST whose rows differ from the registry is refused")
    # the arithmetic and the factor reader on the real rows' text
    unit = [(answers_arith("1,164 (5 x 2 x 97 + 194)"), ("5 x 2 x 97 + 194", 1164)),
            (answers_arith("774 (3 arms x 86 x 3 draws; draw 1 258)"), ("3 x 86 x 3", 774)),
            (answers_arith("0 (its 270 are inside Pipeline ablation's 1,800)"), None),
            ([(f["n"], f["label"]) for f in factors("Figure 2's six strategies x 5 questions on 5 papers, key PB v1.1")],
             [(6, "strategies"), (5, "questions")]),
            ([(f["n"], f["label"]) for f in factors("1 arm (single pass given more passages) x 135")],
             [(1, "arm"), (135, "questions")]),
            ([(f["n"], f["label"]) for f in factors("7 prompt variants x models x 97 items")],
             [(7, "prompt variants"), (None, "models"), (97, "items")])]
    for got, want in unit:
        ok = got == want
        fails += not ok
        print(f"{'ok  ' if ok else 'FAIL'} parse: {got}" + ("" if ok else f" (expected {want})"))
    print(f"S619 selftest: {'PASS' if not fails else f'FAIL ({fails})'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
