#!/usr/bin/env python3
"""S570 - Supplementary Figure 13 (provisional): the pipeline and its evaluation run end to end on a second field (I2).

WHY. The letter tells Reviewer 1 (Comment 1.6, the reuse cost) that "to show what reuse involves, we also ran the whole
pipeline on five questions about five open-access papers from another life-science field" (letter round 2026-10-31,
edits_Reviewer1.json, [PENDING: I2 results]); the story doc of 3 Nov notes that no panel reports I2's result. Valerio,
3 Nov (artifact comment): "freeze them. Let's make a few plots that can become a supplementary figure". S569 froze the
set (ecf1e368).

THE CLAIM the plate carries: with a key written for five plant-science papers, Figure 3's six strategies answered all
90 questions-by-draws; the judge scored all 90 answers; Concepts and Papers scored the 72 answers to questions 1 to 4
(question 5, out of scope, has no concept target), Papers 70 of them (2 over the encoder's input limit). The scores
read there as they read on the main benchmark: per question and draw, where the strategies pass. figure() writes this
sentence from the counts into methods_notes.md, so no count in it is typed here. A signal row with status ok is not a
value: only a float counts as scored.

NOT CLOSED HERE. The letter's bracket is "[PENDING: I2 results and the time its key took]". The plate gives the
results only. The time has one source, experiments/reuse_demo/SIGNOFF.md:205-216 (16 October, about 23 minutes, part
measured from file times, part estimated), and no script regenerates it, so the time half stays open for Valerio.

THE RULES it keeps. I2's own report rule (experiments/reuse_demo/i2_report.py, i2_plan.md Q-I2b): with 5 questions,
counts only, no rate, no interval, no test, no ranking. Scores at judge score 4 and 3 (D153 Q2). The pass rules are
Figure 3's (scripts/S463_fig2_ranking.py METRIC, THRESHOLDS, REFUSAL_T), read through i2_report.build so they are not
typed twice. No rate and no test against the main benchmark: at n = 5 there is none, and the plate shows that the
pipeline transfers to another field once it has a key, not a comparison with the main benchmark (D300, Valerio, 7
November: "Remove the Median from the main benchmark"; it had been drawn from 6 November, tab thread cc041045-ea21).
Panels b and c mark, per strategy, the median of these answers' question means only. D285 (Valerio, tab thread
cc041045-ea21, 6 November 21:12, "O1, go ahead") scores these answers' concept recall with D181's matcher
(scripts/d181_concept_recall.score: the loose matcher with the question rule), the main benchmark's definition
(Figure 6a). Before it draws, the same score() with an empty question must give the frozen signal's
concept_recall_loose on every answer (D181's gate G-B on this set), and the text it scores must hash to the signal's
scored_text_sha256.

WHAT THE CODE DOES.
  1. Reads the frozen set i2 only (fig_repro.frozen: each file against findings/recompute/frozen_inputs/SHA256SUMS) and
     the signed key PB v1.1 (plant_key, pinned by sha256, committed).
  2. Reproduces before it draws: the 90 answers S569 counted (six sinks of 15, no error, no blank), the judge's 90 rows,
     the null counts the signal headers recorded when they were scored (concepts 18, papers 20), and i2_report.build's
     pass counts against a second count made here from the raw judge rows. Any difference refuses the plate.
  3. Draws
       a  tiles, strategy by question, coloured by draws passed of 3 (judge correctness 4 or more; 3 or more), question
          5 by draws refused; right, per strategy, the answers stored, judged and with a Concepts and a Papers value;
       b  concept recall (D181: loose matcher, question rule) per answer, questions 1 to 4, colour and shape by question;
       c  Papers precision per answer, the same.
       b and c also carry, per strategy, one tick: the median of the question means drawn (black, solid). Their one key
       (questions 1 to 4 and the tick) stands on its own line above them, so b and c share the page's width (D300).
     Dots are placed apart by hs.swarm; a dot that cannot be placed apart refuses the plate.
  4. Writes the plate, Source Data workbook, caption, numbers, provenance and legend through S540.write_supp.

    uv run --frozen python scripts/S570_supp_i2_reuse.py figure [--out <folder>]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
SCRIPT = "scripts/S570_supp_i2_reuse.py"
OUT = ROOT / "findings" / "figures_provisional" / "supp_fig13_i2_reuse"
N = 13                                             # D302 (14 before; 25 before D257)
W = 183.0                                         # height: plate_height()
SET = "i2"
INDEX = "i2_plant5"
CONFIGS = ("single_pass", "multi_hop", "verified_pass", "rlm_5", "rlm_10", "rlm_20")   # Figure 3's order
DRAWS = (1, 2, 3)
IMPORTS = ("S497_fig5_d166.py", "S540_fig5_evaluators.py", "house_style.py", "figure_names.py", "S457_fig2_panels.py",
           "fig_repro.py", "d181_concept_recall.py", "S505_question_aware_matcher.py", "concept_match_loose.py",
           "turn_limit_note.py")
S463_RULES = ("METRIC", "THRESHOLDS", "PRIMARY", "REFUSAL_T", "JUDGE_FAILED")   # Figure 3's pass rules, read at HEAD
SIGNAL = {"concept": "concepts.concept_recall_loose", "papers": "papers.precision"}   # the frozen signals read
OTHER_INPUTS = ("experiments/reuse_demo/i2_report.py", "experiments/reuse_demo/plant_key.py",
                "experiments/reuse_demo/key_v1_1.json")
# known numbers this script must reproduce before it draws (S569's checks; the signal headers written at scoring)
KNOWN = {"answers": 90, "judge_rows": 90, "concepts_null": 18, "papers_null": 20}


def _load(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


S497 = _load("S497", ROOT / "scripts" / "S497_fig5_d166.py")
hs, FN, S540, S473 = S497.hs, S497.FN, S497.S540, S497.S473
FR = S473.FR
D181 = _load("d181_concept_recall", ROOT / "scripts" / "d181_concept_recall.py")
LABEL = {"single_pass": FN.SINGLE_PASS, "multi_hop": FN.MULTI_HOP, "verified_pass": FN.VERIFIED_PASS,
         "rlm_5": FN.MENTORI_RLM_N.format(n=5), "rlm_10": FN.MENTORI_RLM_N.format(n=10),
         "rlm_20": FN.MENTORI_RLM_N.format(n=20)}
GROUP = {"extractive": "answerable", "synthesis": "answerable", "refutation": "false_premise",
         "not_answerable": "not_answerable"}
A, B, C = (f"Supplementary Fig. {N}{x}" for x in "abc")
M = f"Supplementary Fig. {N} medians"           # b and c's ticks: per strategy, the median of the question means
QM = f"Supplementary Fig. {N}b,c means"         # b and c's dots: each question's mean over its draws


class Refused(SystemExit):
    pass


def rows(p: Path) -> list:
    return [json.loads(x) for x in Path(p).read_text(encoding="utf-8").splitlines() if x.strip()]


def s463_rules_at_head() -> tuple[dict, str]:
    """Figure 3's pass rules as committed: the constants S463_RULES, read by ast from S463's blob at git HEAD (never its
    working copy, which another job may be editing), and given to i2_report.rules() as module S463_fig2_ranking."""
    import ast
    import subprocess
    import types
    rel = "scripts/S463_fig2_ranking.py"
    blob = subprocess.run(["git", "rev-parse", f"HEAD:{rel}"], cwd=ROOT, capture_output=True, text=True,
                          check=True).stdout.strip()
    src = subprocess.run(["git", "cat-file", "blob", blob], cwd=ROOT, capture_output=True, text=True,
                         check=True).stdout
    got = {}
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign):
            names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            tup = [t for t in node.targets if isinstance(t, ast.Tuple)]
            if names and names[0] in S463_RULES:
                got[names[0]] = ast.literal_eval(node.value)
            elif tup and all(isinstance(e, ast.Name) for e in tup[0].elts):
                ns = [e.id for e in tup[0].elts]
                if set(ns) & set(S463_RULES):
                    got.update(zip(ns, ast.literal_eval(node.value)))
    if set(got) != set(S463_RULES):
        raise Refused(f"S570: {rel} at HEAD lacks {sorted(set(S463_RULES) - set(got))}")
    mod = types.ModuleType("S463_fig2_ranking")
    for k, v in got.items():
        setattr(mod, k, v)
    if "S463_fig2_ranking" in sys.modules and sys.modules["S463_fig2_ranking"] is not mod:
        raise Refused("S570: S463_fig2_ranking was imported from the working tree")
    sys.modules["S463_fig2_ranking"] = mod
    return got, f"git blob {blob}"


def read_inputs() -> dict:
    """Every input file, each through fig_repro.frozen (sha256 against SHA256SUMS) or committed at HEAD."""
    rules, s463 = s463_rules_at_head()
    from experiments.reuse_demo import i2_report, plant_key
    import subprocess
    for rel in OTHER_INPUTS + tuple(f"scripts/{m}" for m in IMPORTS):   # committed at HEAD, unchanged in the tree
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", rel], cwd=ROOT, capture_output=True).returncode
        clean = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", rel], cwd=ROOT).returncode
        if tracked or clean:
            raise Refused(f"S570: {rel} is not committed at HEAD as it stands")
    key = plant_key.load(plant_key.KEY, plant_key.KEY_SHA256)
    f = {"judge": FR.frozen(SET, "judge/judge_passages.jsonl"),
         "concepts": FR.frozen(SET, "signals/concepts.jsonl"), "concepts_header": FR.frozen(SET, "signals/concepts_header.json"),
         "papers": FR.frozen(SET, "signals/papers.jsonl"), "papers_header": FR.frozen(SET, "signals/papers_header.json"),
         "numbers": FR.frozen(SET, "signals/numbers.jsonl"), "key_signal": FR.frozen(SET, "signals/key.jsonl")}
    for c in CONFIGS:
        f[f"answers {c}"] = FR.frozen(SET, f"sinks/exp_01__{c}__{INDEX}/answers.jsonl")
    sig = f["concepts"].parent
    if any(FR.frozen(SET, f"signals/{n}") != sig / n for n in ("concepts.jsonl", "papers.jsonl")):
        raise Refused("the signal files are not in one frozen folder")
    built = i2_report.build(f["judge"], sig, key)
    inputs = {FR.frozen_label(p): FR.sha256_file(p) for p in f.values()}
    inputs |= {rel: FR.sha256_file(ROOT / rel) for rel in OTHER_INPUTS}
    inputs["scripts/S463_fig2_ranking.py at HEAD (" + ", ".join(S463_RULES) + ")"] = s463
    return {"files": f, "key": key, "built": built, "inputs": inputs}


def reproduce(d: dict) -> dict:
    """The known numbers, and i2_report's counts against a second count from the raw judge rows; refuses on any gap."""
    f, key, built = d["files"], d["key"], d["built"]
    qids = list(key.ids)
    types = {r["id"]: r["answer_type"] for r in key.records}
    want = {f"{INDEX}|{c}|{q}|d{k}" for c in CONFIGS for q in qids for k in DRAWS}
    stored = {}
    for c in CONFIGS:
        for r in rows(f[f"answers {c}"]):
            g = r["generation"]
            if g.get("error") is None and isinstance(g.get("answer"), str) and g["answer"].strip():
                stored[r["answer_key"]] = c
    jr = rows(f["judge"])
    got = {"answers": len(stored), "judge_rows": len(jr),
           "concepts_null": sum(1 for r in rows(f["concepts"]) if r.get("concept_recall_loose") is None),
           "papers_null": sum(1 for r in rows(f["papers"]) if (r.get("signals") or {}).get("precision") is None)}
    heads = {"concepts_null": json.loads(f["concepts_header"].read_text())["counts"]["null"]["concept_recall_loose"],
             "papers_null": json.loads(f["papers_header"].read_text())["counts"]["null"]["precision"]}
    if got != KNOWN or any(got[k] != v for k, v in heads.items()) or set(stored) != want:
        raise Refused(f"S570: not reproduced: read {got}, known {KNOWN}, headers {heads}, "
                      f"{len(set(stored) ^ want)} answer keys differ")
    if {r["answer_key"] for r in jr} != want:
        raise Refused("S570: the judge rows are not the 90 answer keys")
    R = built["rules"]
    mine = {c: Counter() for c in CONFIGS}
    for r in jr:
        g = GROUP[types[r["question_id"]]]
        a = r["a"]
        if a.get("status") != "ok":
            raise Refused(f"{r['answer_key']}: judge status {a.get('status')}")
        s = a["scores"][R["metric"][g]]
        if g == "not_answerable":
            mine[r["config"]][("refused", None)] += s >= R["refusal_t"]
        else:
            for t in R["thresholds"]:
                mine[r["config"]][(g, t)] += s >= t
    for c in CONFIGS:
        x = built["counts"][c]
        theirs = {("refused", None): x["not_answerable"]["refused"][0],
                  **{(g, t): x[g][t][0] for g in ("answerable", "false_premise") for t in R["thresholds"]}}
        if {k: v for k, v in mine[c].items() if v} != {k: v for k, v in theirs.items() if v} or x["not_counted"]:
            raise Refused(f"S570: {c}: i2_report counts {theirs} differ from the raw count {dict(mine[c])}")
    return {"known": KNOWN, "reproduced": got, "headers": heads, "pass_counts": "i2_report.build equals the raw count"}


def d181_values(d: dict) -> dict:
    """D285: each answer to questions 1 to 4 scored by D181.score (the main benchmark's concept recall), keyed (config,
    question, draw). Gates before any value is kept: the text scored hashes to the frozen signal's scored_text_sha256,
    and score() with an empty question gives the signal's concept_recall_loose (D181 G-B); either failing refuses."""
    recs = {r["id"]: r for r in d["key"].records}
    sig = {}
    for r in rows(d["files"]["concepts"]):
        k = r["answer_key"].split("|")
        sig[(k[1], k[2], int(k[3][1:]))] = r
    out = {}
    for c in CONFIGS:
        for a in rows(d["files"][f"answers {c}"]):
            q, dr = a["question_id"], a["draw"]
            rec = recs[q]
            if GROUP[rec["answer_type"]] == "not_answerable":
                continue
            s_ = sig[(c, q, dr)]
            if not isinstance(s_.get("concept_recall_loose"), float):
                raise Refused(f"S570: {c} {q} d{dr} has no frozen loose value")
            flagged = s_.get("turn_limit_note") is True
            text = a["generation"]["answer"]
            phrases = [kc["phrase"] for kc in rec["key_concepts"]]          # the concept strings the signal scored
            got = D181.score(text, phrases, rec["question"], flagged)
            base = D181.score(text, phrases, "", flagged)
            if got["scored_text_sha256"] != s_["scored_text_sha256"]:
                raise Refused(f"S570: {c} {q} d{dr}: the text scored is not the one the frozen signal scored")
            if base["concept_recall"] != round(s_["concept_recall_loose"], 4):
                raise Refused(f"S570: {c} {q} d{dr}: D181 with no question gives {base['concept_recall']}, the frozen "
                              f"loose value is {s_['concept_recall_loose']} (G-B)")
            out[(c, q, dr)] = (got["concept_recall"], s_["concept_recall_loose"])
    return out


def sheets(d: dict) -> dict:
    key, built = d["key"], d["built"]
    d181 = d181_values(d)
    R = built["rules"]
    qids = list(key.ids)
    types = {r["id"]: r["answer_type"] for r in key.records}
    by = {(a["config"], a["question_id"], a["draw"]): a for a in built["answers"]}
    if len(by) != 90:
        raise Refused(f"S570: {len(by)} judged answers, want 90")
    if tuple(R["thresholds"]) != THRESH:
        raise Refused(f"S570: S463's thresholds are {R['thresholds']}, the plate draws {THRESH}")
    texts = {}
    for c in CONFIGS:
        for r in rows(d["files"][f"answers {c}"]):
            texts.setdefault(r["generation"]["answer"], []).append((c, r["question_id"], r["draw"]))
    same = {k: v for v in texts.values() if len(v) > 1 for k in v}

    a = {"columns": ["row_kind", "strategy", "strategy_label", "question_id", "question_group", "block_threshold",
                     "judge_measure", "pass_mark", "draws_passed", "draws", "answers_stored", "answers_judged", "concepts_values",
                     "papers_values"], "rows": []}
    for c in CONFIGS:
        for t in R["thresholds"]:
            for q in qids:
                g = GROUP[types[q]]
                m = R["metric"][g]
                cut = R["refusal_t"] if g == "not_answerable" else t
                k = sum(1 for dr in DRAWS if by[(c, q, dr)]["judge_score"] >= cut)
                a["rows"].append(["tile", c, LABEL[c], q, g, t, m, cut, k, len(DRAWS), None, None, None, None])
    for c in CONFIGS:
        ans = [x for x in built["answers"] if x["config"] == c]
        a["rows"].append(["coverage", c, LABEL[c], None, None, None, None, None, None, None, len(ans),
                          sum(1 for x in ans if x["judge_status"] == "ok"),
                          sum(1 for x in ans if isinstance(x["signals"].get("concepts.concept_recall_loose"), float)),
                          sum(1 for x in ans if isinstance(x["signals"].get("papers.precision"), float))])

    def per_answer(sig):
        cols = ["strategy", "strategy_label", "question_id", "question_group", "draw", "value", "null_reason",
                "judge_correctness", "same_text_as"] + (["loose_without_question_rule"] if sig == "d181" else [])
        out = []
        for c in CONFIGS:
            for q in qids:
                if GROUP[types[q]] == "not_answerable":
                    continue
                for dr in DRAWS:
                    x = by[(c, q, dr)]
                    sa = "; ".join(f"{o} d{od}" for o, oq, od in same.get((c, q, dr), []) if o != c) or None
                    if sig == "d181":
                        v, loose = d181[(c, q, dr)]
                        out.append([c, LABEL[c], q, GROUP[types[q]], dr, v,
                                    None if v is not None else "no concept left after the question rule",
                                    x["judge_score"], sa, loose])
                        continue
                    v = x["signals"].get(sig)
                    out.append([c, LABEL[c], q, GROUP[types[q]], dr, v if isinstance(v, float) else None,
                                v.get("null") if isinstance(v, dict) else None, x["judge_score"], sa])
        return {"columns": cols, "rows": out}

    b, c_ = per_answer("d181"), per_answer(SIGNAL["papers"])
    qm = question_means({"concept": b, "papers": c_})
    return {A: a, B: b, C: c_, QM: qm, M: medians(qm)}, same


def question_means(here: dict) -> dict:
    """What b and c draw: per strategy, signal and question, the mean of the answers' values over the draws that have
    one (Figure 6a's unit for Concepts: a question's mean over its draws)."""
    out = {"columns": ["strategy", "strategy_label", "signal", "question_id", "draws_with_value", "mean"], "rows": []}
    for sig, part in here.items():
        jx = {k: n for n, k in enumerate(part["columns"])}
        qs = list(dict.fromkeys(r[jx["question_id"]] for r in part["rows"]))
        for c in CONFIGS:
            for q in qs:
                v = [r[jx["value"]] for r in part["rows"] if r[jx["strategy"]] == c and r[jx["question_id"]] == q
                     and r[jx["value"]] is not None]
                out["rows"].append([c, LABEL[c], sig, q, len(v), round(sum(v) / len(v), 4) if v else None])
    return out


def medians(qm: dict) -> dict:
    """Per strategy and signal: the median of the question means drawn in b or c (the black tick), and over how many
    questions. A strategy with no question mean refuses. No main-benchmark median (D300)."""
    import statistics
    out = {"columns": ["strategy", "strategy_label", "signal", "median", "questions"], "rows": []}
    jx = {k: n for n, k in enumerate(qm["columns"])}
    for sig in SIGNAL:
        for c in CONFIGS:
            vals = [r[jx["mean"]] for r in qm["rows"] if r[jx["strategy"]] == c and r[jx["signal"]] == sig
                    and r[jx["mean"]] is not None]
            if not vals:
                raise Refused(f"S570: no {sig} question mean for {LABEL[c]}")
            out["rows"].append([c, LABEL[c], sig, round(statistics.median(vals), 4), len(vals)])
    return out


# ---- drawing ----------------------------------------------------------------------------------------------------------
# Layout (Valerio, tab thread 89258810-4838, 6 Nov 21:22): a spans the whole width with no count table (the counts stay
# in sheet a's coverage rows); b and c share the bottom row. D300 (7 Nov): b and c take the whole width, and their one
# key stands on its own line under their letters, centred as a's key is.
LAB_R = 23.5                          # row labels end here (mm)
GAP_BLOCK = 4.0
TILE_H, ROW_A = 4.0, 4.6
ROW_B = 5.6
R_PAD = 2.0                           # right of c's axis: half its "1" tick label and a dot at 1 stay on the page
KEY_ROW = 4.2                         # b and c's shared key line, between their letters and their axes (D300)
THRESH = (4, 3)                       # the two blocks of a, left to right (S463 THRESHOLDS; checked in sheets())
H_BOTTOM_PAD = 10.0                   # under b and c's axes: tick labels and axis titles


def q_style(qids):
    return {q: hs.SERIES_ORDER[i] for i, q in enumerate(qids)}


def plate_height(n_rows_a: int) -> tuple:
    ybot = 9.6 + n_rows_a * ROW_A
    y0 = ybot + 9.0
    rt = y0 + 4.5 + KEY_ROW
    return ybot, y0, rt, rt + len(CONFIGS) * ROW_B + H_BOTTOM_PAD


def draw(sh: dict, qids: list):
    hs.apply_rc("S570")
    ybot, y0, rt, h = plate_height(len(CONFIGS))
    pl = S497.Page(W, h)
    tw = hs._text_width_mm
    rows_a = sh[A]["rows"]
    cols = sh[A]["columns"]
    ix = {c: i for i, c in enumerate(cols)}
    lev = {k: v.upper() for k, v in enumerate(hs.cividis_levels(len(DRAWS) + 1))}

    # a: tiles, the whole width -----------------------------------------------------------------------------------------
    ly = 3.0
    pl.letter(0, ly, "a")
    x1 = LAB_R + 1.0
    tile_w = (W - x1 - GAP_BLOCK) / (2 * len(qids))
    bw = len(qids) * tile_w
    x2 = x1 + bw + GAP_BLOCK
    top = 9.6
    items = [(lev[k], f"{k}" + (f" of {len(DRAWS)}" if k == 0 else "")) for k in range(len(DRAWS), -1, -1)]
    title = "Draws passed (refused):"
    sw, sh_ = hs.SWATCH_MM
    total = tw(title) + 1.5 + sum(sw + 0.8 + tw(t) + 2.4 for _, t in items) - 2.4
    kx = x1 + (2 * bw + GAP_BLOCK) / 2 - total / 2
    pl.t(kx, ly, title)
    kx += tw(title) + 1.5
    for fc, text in items:
        pl.rect(kx, ly - sh_ + 0.25, sw, sh_, fc, ec=hs.GREY["line"] if fc == lev[len(DRAWS)] else "none",
                lw=hs.LW["divider"] if fc == lev[len(DRAWS)] else 0.0)
        pl.t(kx + sw + 0.8, ly, text, why="a key entry, draws of 3")
        kx += sw + 0.8 + tw(text) + 2.4
    for xb, t in zip((x1, x2), THRESH):
        pl.t(xb + bw / 2, top - 1.6, f"Judge score {t} or more", ha="center", why="the judge threshold of the block")
    for r_i, r in enumerate(rows_a):
        if r[ix["row_kind"]] != "tile":
            continue
        c, q, k = r[ix["strategy"]], r[ix["question_id"]], r[ix["draws_passed"]]
        xb = (x1, x2)[THRESH.index(r[ix["block_threshold"]])]
        x = xb + qids.index(q) * tile_w
        y = top + CONFIGS.index(c) * ROW_A + (ROW_A - TILE_H) / 2
        fc = lev[k]
        pl.rect(x + 0.2, y, tile_w - 0.4, TILE_H, fc, ec=hs.GREY["line"] if k == len(DRAWS) else "none",
                lw=hs.LW["divider"] if k == len(DRAWS) else 0.0)
        pl.t(x + tile_w / 2, y + TILE_H / 2, str(k), ha="center", va="center_baseline", color=hs.ink_on(fc),
             printed={"sheet": A, "row": r_i, "format": "{draws_passed}"})
    for i, c in enumerate(CONFIGS):
        pl.t(LAB_R, top + i * ROW_A + ROW_A / 2, LABEL[c], ha="right", va="center_baseline", why="strategy name")
    for xb in (x1, x2):
        for j, q in enumerate(qids):
            pl.t(xb + (j + 0.5) * tile_w, ybot + 3.2, str(j + 1), ha="center", why="question number (PB_00n)")
    pl.t(x1 + (2 * bw + GAP_BLOCK) / 2, ybot + 6.9, "Question (4, false premise; 5, out of scope: draws refused)",
         ha="center", why="question numbers on the axis title")

    # b and c: per answer, the whole width of the bottom row --------------------------------------------------------------
    st = q_style(qids)
    ly = y0 + 2.5
    gap = 7.0
    xa_b = LAB_R + 1.5
    wa = (W - R_PAD - xa_b - gap) / 2
    xa_c = xa_b + wa + gap
    pl.letter(0, ly, "b")
    pl.letter(xa_c - 5.0, ly, "c")
    hb = len(CONFIGS) * ROW_B
    for i, c in enumerate(CONFIGS):
        pl.t(LAB_R, rt + i * ROW_B + ROW_B / 2, LABEL[c], ha="right", va="center_baseline", why="strategy name")
    # one key for b and c, on its own line under their letters, centred over both as a's key is over a (D300)
    kq = [q for q in qids if any(r[2] == q for r in sh[B]["rows"])]
    size = hs.KEY_MARK_MM
    ky = ly + KEY_ROW
    tl = 4.0
    title = "Question (b, c):"
    tick_text = "Median here"
    q_items = [str(qids.index(q) + 1) for q in kq]
    gap_k = 3.2                       # between key entries: the diamond is drawn larger than the other marks
    total = (tw(title) + 1.5 + sum(size + 0.8 + tw(t) + gap_k for t in q_items) + 2.4
             + tl + 1.2 + tw(tick_text))
    kx = xa_b + (W - R_PAD - xa_b) / 2 - total / 2
    if kx < 0 or kx + total > W:
        raise Refused("S570: the shared key runs past the plate")
    pl.t(kx, ky, title, why="the shared key's title")
    kx += tw(title) + 1.5
    for q, text in zip(kq, q_items):
        colr, mk = st[q]
        pl.pg.plot([kx + size / 2], [ky - 1.0], ls="none", marker=mk,
                   ms=size * hs.MARKER_SCALE.get(mk, 1.0) / hs.MM_PT, mfc=colr, mec=hs.WHITE, mew=0.3, clip_on=False)
        pl.t(kx + size + 0.8, ky, text, why="question id in the key")
        kx += size + 0.8 + tw(text) + gap_k
    kx += 2.4
    pl.pg.plot([kx, kx + tl], [ky - 1.0, ky - 1.0], solid_capstyle="butt", clip_on=False, color=hs.BLACK,
               lw=hs.LW["median"])
    pl.t(kx + tl + 1.2, ky, tick_text, why="a key entry, median tick")
    over_all = 0
    mcols = sh[M]["columns"]
    med = {(r[0], r[2]): dict(zip(mcols, r)) for r in sh[M]["rows"]}
    for xa, name, label, sig in ((xa_b, B, "Concept recall (Concepts)", "concept"),
                                 (xa_c, C, FN.PAPERS_PRECISION, "papers")):
        ax = pl.ax(xa, rt, wa, hb, (0, 1), (len(CONFIGS), 0))
        ax.set_xticks([0, 0.5, 1], ["0", "0.5", "1"])
        mx, my = hs.mm_per_unit(ax)
        for i in range(1, len(CONFIGS)):
            ax.plot([0, 1], [i, i], color=hs.GREY["line"], lw=hs.LW["divider"], zorder=1, clip_on=False)
        cl = sh[name]["columns"]
        jx = {k: n for n, k in enumerate(cl)}
        for i, c in enumerate(CONFIGS):
            m = med[(c, sig)]
            half_band = hs.BAND_FRAC / 2
            ax.plot([m["median"]] * 2, [i + 0.5 - half_band, i + 0.5 + half_band], color=hs.BLACK,
                    lw=hs.LW["median"], solid_capstyle="butt", zorder=4, clip_on=False)
            qc = sh[QM]["columns"]
            qx = {k: n for n, k in enumerate(qc)}
            pts = [{"value": r[qx["mean"]], "question_id": r[qx["question_id"]]} for r in sh[QM]["rows"]
                   if r[qx["strategy"]] == c and r[qx["signal"]] == sig and r[qx["mean"]] is not None]
            dot = hs.DOT_SPARSE_MM
            half = hs.BAND_FRAC * ROW_B / 2 - dot / 2
            off, over = hs.swarm([r["value"] * mx for r in pts], half=half, pitch=dot + 0.05, dot=dot)
            over_all += over
            for r, o in zip(pts, off):
                colr, mk = st[r["question_id"]]
                ax.plot([r["value"]], [i + 0.5 + o / my], ls="none", marker=mk,
                        ms=dot * hs.MARKER_SCALE.get(mk, 1.0) / hs.MM_PT, mfc=colr, mec=hs.WHITE, mew=0.3,
                        zorder=3, clip_on=False)
        pl.t(xa + wa / 2, rt + hb + 7.0, label, ha="center")
    if over_all:
        raise Refused(f"S570: {over_all} dot(s) could not be placed apart; raise ROW_B")
    bad = hs.check_figure_colours(pl.fig)
    if bad:
        raise Refused(f"Supplementary Figure {N}: colours outside the house palette: {bad}")
    return pl


def legend(sh: dict, same: dict) -> str:
    """Editor row 45 round (Valerio, 8 Nov): no panel draws derived statistics (no box, interval or test; the black
    line is a median of question means), so the legend carries no "n = " tag, and each panel is described in full,
    with no reference to another panel or figure. Counts are read from the sheets."""
    nt = len(sh[B]["rows"])
    nb = sum(1 for r in sh[B]["rows"] if r[5] is not None)
    nc = sum(1 for r in sh[C]["rows"] if r[5] is not None)
    nc_null = len(sh[C]["rows"]) - nc
    if nb != nt or len(sh[C]["rows"]) != nt:
        raise Refused(f"S570: concepts {nb} of {nt}, Papers rows {len(sh[C]['rows'])}; the legend states every one")
    mc = sh[M]["columns"]
    nq = sorted({dict(zip(mc, r))["questions"] for r in sh[M]["rows"]})
    if nq != [4]:
        raise Refused(f"S570: the medians are over {nq} question means; the legend states 4")
    n_ans = len(CONFIGS) * len(DRAWS) * 5
    return (f"**Supplementary Figure {N} | The pipeline and its evaluation on five plant-science papers.** The key "
            "covers five open-access papers on lettuce resistance to downy mildew. Questions 1 and 2 are extractive, 3 "
            "is a synthesis, 4 has a false premise and 5 is out of scope. Six strategies (single pass, multi-hop, "
            "verified pass and our RLM stopped at 5, 10 and 20 turns: RLM-5, RLM-10 and RLM-20) answered each "
            f"question with gemini-3-flash in {len(DRAWS)} draws, {n_ans} answers in all. The judge (devstral-small-2:24b, "
            "plain call) scored every answer. Question 5 has no concept target. In three question-draws the RLMs returned the same text: questions 1 and 4 "
            "(all three RLMs, one draw each) and question 3 (RLM-5 and RLM-20, one draw). **a**, One tile per "
            "strategy (rows) and question (columns): the draws passed of 3, printed in the tile and coloured from 0 "
            "(dark blue) to 3 (yellow). Left block, judge correctness 4 or more; right block, 3 or more. For question "
            "5 a tile counts the draws refused instead (refusal score 3 or more, the same in both blocks). **b**, "
            f"Concept recall (loose matcher with the question rule) of the {nt} answers to the first four questions, "
            "one row per strategy: one dot per question, the mean over its "
            f"{len(DRAWS)} draws; colour and shape, question; black line, the strategy's median of its 4 question means. "
            "**c**, Papers precision (MiniCheck against each question's source papers) of the "
            f"{nt} answers to the first four questions, one row per strategy: one dot per question, the mean over its draws "
            f"with a value ({nc} answers have one; the other {nc_null} are longer than the encoder's 2,048-token input); "
            "colour and shape, question; black line, the strategy's median of its 4 question means.")


def claim(sh: dict) -> str:
    """The claim sentence, every count read from the sheets. The legend says the judge scored every answer and that
    the Papers nulls are over the encoder's limit; either not holding refuses the plate."""
    ca = sh[A]["columns"]
    cov = [dict(zip(ca, r)) for r in sh[A]["rows"] if r[0] == "coverage"]
    tiles = [dict(zip(ca, r)) for r in sh[A]["rows"] if r[0] == "tile"]
    stored = sum(r["answers_stored"] for r in cov)
    judged = sum(r["answers_judged"] for r in cov)
    if judged != stored:
        raise Refused(f"S570: the judge scored {judged} of {stored} answers; the legend says every answer")
    n_target = len(sh[B]["rows"])
    nb = sum(1 for r in sh[B]["rows"] if r[5] is not None)
    nc = sum(1 for r in sh[C]["rows"] if r[5] is not None)
    reasons = Counter(r[6] for r in sh[C]["rows"] if r[5] is None)
    if nb != n_target or set(reasons) - {"over the encoder's 2048-token limit"}:
        raise Refused(f"S570: concepts {nb} of {n_target}; Papers null reasons {dict(reasons)}; the legend states otherwise")
    answ = {c: sum(t["draws_passed"] for t in tiles if t["strategy"] == c and t["block_threshold"] == 4
                   and t["question_group"] != "not_answerable") for c in CONFIGS}
    n_answ = sum(t["draws"] for t in tiles if t["strategy"] == CONFIGS[0] and t["block_threshold"] == 4
                 and t["question_group"] != "not_answerable")
    refused = {c: sum(t["draws_passed"] for t in tiles if t["strategy"] == c and t["block_threshold"] == 4
                      and t["question_group"] == "not_answerable") for c in CONFIGS}
    n_ref = sum(t["draws"] for t in tiles if t["strategy"] == CONFIGS[0] and t["block_threshold"] == 4
                and t["question_group"] == "not_answerable")
    per = "; ".join(f"{LABEL[c]} {answ[c]} of {n_answ} and {refused[c]} of {n_ref}" for c in CONFIGS)
    return (f"With a key written for five open-access papers on lettuce resistance to downy mildew, Figure 3's six "
            f"strategies answered the five questions in {len(DRAWS)} draws. The judge scored all {judged} answers. "
            f"Concepts and Papers scored the {n_target} answers to questions 1 to 4, Papers {nc} of them "
            f"({n_target - nc} over the encoder's input limit). Passed at judge score 4 of the answerable and "
            f"false-premise answers, and refused of the out-of-scope ones: {per}.")


def figure(out) -> None:
    d = read_inputs()
    rep = reproduce(d)
    sh, same = sheets(d)
    qids = list(d["key"].ids)
    k = sum(r[sh[A]["columns"].index("answers_stored")] for r in sh[A]["rows"] if r[0] == "coverage")
    tag = f"provisional, {k} of 90"
    run_sha = {json.loads(x)["run_sha256"] for x in d["files"]["judge"].read_text().splitlines() if x.strip()}
    stamp = (f"PROVISIONAL: {k} of 90 answers drawn (I2, draws 1, 2, 3 of 3), frozen set i2 (S569, ecf1e368); judge "
             f"devstral-small-2:24b plain call, run_sha256 {sorted(run_sha)[0][:12]}; key PB v1.1 sha256 "
             f"{d['key'].sha256[:12]}; concept recall D181 (loose matcher, question rule; D285)")
    caption = (f"# Supplementary Figure {N} data, caption\n\n**Supplementary Figure {N} data.** Provisional. Data stamp: "
               f"{stamp}. Sheet {A}: one row per tile (strategy, question, judge threshold; draws passed or refused "
               f"of 3) and one coverage row per strategy. Sheets {B} and {C}: one row per answer to questions 1 to 4 "
               "(strategy, question, draw), with its value or the reason it has none, its judge correctness and any "
               "other strategy that returned the same text. "
               f"Sheet {QM}: per strategy, signal and question, the mean over the draws with a value (the dots of b "
               f"and c). Sheet {M}: per strategy and signal, the median of those question means (the black line). "
               "Generated by "
               f"`uv run --frozen python {SCRIPT} figure` from the frozen set findings/recompute/i2_inputs.\n")
    notes = ("Reproduced before drawing: " + json.dumps(rep, sort_keys=True) + "\n\nNo rate or test against the main "
             "benchmark: I2's report rule (experiments/reuse_demo/i2_report.py, i2_plan.md Q-I2b) gives counts only at "
             "five questions. Panels b and c mark each strategy's median of its question means (sheet "
             f"{M}); the main benchmark's median is not drawn (D300, Valerio, 7 November: the plate shows the "
             "transfer to another field, not a comparison with the main benchmark).\n\nClaim, written from the counts: "
             + claim(sh) + "\n\nNot closed by this plate: the letter's bracket \"[PENDING: I2 results and the time "
             "its key took]\" asks for the time as well. Its one source is experiments/reuse_demo/SIGNOFF.md:205-216 "
             "(16 October, part measured from file times, part estimated) and no script regenerates it, so the time "
             "half stays open.")
    S540.write_supp(out, N, tag, stamp, draw(sh, qids), sh, legend(sh, same), caption, script=SCRIPT, imports=IMPORTS,
                    inputs=d["inputs"], notes=notes)
    print(f"Supplementary Figure {N}: {k} of 90 answers; {Path(out)}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("figure")
    f.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    FR.pin_hash_seed()
    figure(a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
