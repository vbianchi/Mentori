#!/usr/bin/env python3
"""S524 - Supplementary Figures 10 and 11 (12 and 13 before D257), the component benchmarks and the distiller prompts (T3): frames, and
plates from T3's answers (figure --t3, note of 4 November below).

NOTE, 7 November 2026 (D294, Valerio, "O1" in thread 96158401: "keep c and d; drop a and b. a's fact becomes one
sentence in the text"). Supplementary Figure 10 keeps two panels: a, the supervisor against the judge (c before), and
b, the component scores (d before). The step lengths (old a, old Figure 4b) and the time per item (old b) are dropped
with their sheets, so S524 no longer reads findings/recompute/S472_supp12a_steps.json (S472 still writes it for
Figure 5's folder). The plate is shorter; the legend names only the four components it draws (the synthesizer was in
old b only). Below, notes older than D294 use the letters of their day.

NOTE, 6 November 2026 (audit of 6 Nov, A3). Panel c (S12b, old b) is drawn: `figure --t3 <set>` reads S10's frozen
copy findings/recompute/s12b_inputs (--s12b; 'none' keeps c a frame) through read_s12b (R6): the 194 April supervisor
answers judged once on key v2.5, tied to T3's supervisor items by s12b_item_map.json and each answer's sha256. Per
model, one box per judge score of the supervisor's quality_score (gemini-3-flash-preview: the mean of its three draws)
and Spearman's rho, computed as exp_04 does (rho_of); the reproduction step now also recomputes S285's supervisor
rho_published for devstral-small-2:24b and gemini-3-flash-preview. D213 (1) is applied: the 18 items on D9's six
questions are left out of S12 and S13 (left_out_ids, LEFT_OUT, KEPT), so 814 items count, 6,512 and 1,128 answers.

NOTE, 5 November 2026 (D250, Valerio, 4 November). Figure 4b, the plan step attempts against the distiller threshold,
moved here as Supplementary Figure 10a; the panels below it are relettered: S12 b the time per item (a before), c the
supervisor against the judge (b before; its six small panels now in one row), d the component scores (c before). 12a
reads findings/recompute/S472_supp12a_steps.json (scripts/S472_fig4_panels.py figure --steps-out; read_steps checks it)
and draws it as S472 drew it, the saved PDF's curve read back vertex by vertex (check_curve, S472's check moved with the
panel). On a frame 12a draws its axes only. Below, "S12 a", "S12 b" and "S12 c" name the panels before D250; the
values code (t3_values' "12a" and "12c") keeps those names.

NOTE, 4 November 2026. `figure --t3 <frozen set>` reads T3's sinks (answers.jsonl, calls.jsonl, run_identity.json, copied
by findings/recompute/T3_runs/copy_t3_frozen.sh), the benchmark items in T3_runs/inputs and the deposit's exp07 files
(the reproduction of accuracy_published). Models without answers stay blank rows; panel 12b stays a frame until job
S10's judge scores exist. The text below was written for the frame mode, which is unchanged.

WHY. fig4.md section 6 and build_order.md section 2. T3 has not run, so both plates go out on 9 November as frames and
take their values by 16 November (D198). A frame draws axes, ticks, row and column names, keys, dividers and the two
reference lines (S13 b's line of equal shares, S13 c's zero line). It draws no mark and prints no value, and its data
workbook holds the planned rows with every value cell empty (S448's same_value reads a blank cell as null).

COMMANDS, from the repository root (uv run only; no model call; frame reads no result file, figure does):

  uv run --frozen python scripts/S524_t3_s12_s13.py frame [--out <folder>]
      Writes both plates into <folder>/supp_fig10_components and <folder>/supp_fig11_distiller_prompts (default
      findings/figures_provisional), each with its PDF, SVG, PNG, data workbook, caption, numbers file, provenance file
      and legend draft. The only file it reads is experiments/LOCK.toml ([exceptions], the context of llama3:8b).
      Two runs write the same bytes.
  uv run --frozen python scripts/S524_t3_s12_s13.py selftest
      Row counts and every value cell blank on the sheets of both plates; two builds byte for byte; S448 passes on both
      frames; a value edited into a workbook cell makes S448 R8 fail. Last line "selftest: <k> of <k> checks pass".
  uv run --frozen python scripts/S524_t3_s12_s13.py figure --t3 <frozen set> [--out <folder>]
      Both plates from T3's sinks, named by the lock alone (Q9, 11 Nov); the stamp counts k, the answers stored in the set.
      <frozen set> is a folder findings/recompute/T3_runs/copy_t3_frozen.sh writes (findings/runs/T3_frozen_<stamp>).
      Refuses, exit 2, writing nothing: while findings/recompute/S518_split_confirmation/ does not exist (D195, fig4.md
      Q3); without --t3; on any refusal of read_s12b (R6, NOTE of 6 November); on any refusal of the
      reader (read_t3, R5 of fig4.md section 7: the set's SHA256SUMS, the frozen items, the lock and the digests, keys,
      items and draws, calls, and every stored analyser, planner and distiller score recomputed from its item and text);
      and when the reproduction fails. Reproduce before writing (fig4.md section 6): accuracy_published of the submitted
      run, recomputed from the deposit's exp07 files for devstral-small-2:24b and gemini-3-flash-preview with score_of,
      must equal findings/recompute/S285_component_bench.csv for the analyser, the planner and the distiller.
      Values, all with errors left out and counted (fig4.md section 6): S12 a, the median latency_s of a model's items in
      one draw; S12 c, exp_04's decision_accuracy, tool_accuracy and mean_number_retention, in %; S12 b stays a frame (its
      judge rows, job S10, do not exist). S13 a, number_retention x 100 per item, a box per model and prompt; b, the mean
      source_retention and number_retention per model and prompt, in %; c, F1's mean minus Baseline's, in points. A
      model with no sink in the set keeps its row, empty. The legend is computed: failed calls, length stops, the busy
      record and which models the set holds.

THE DESIGN. S12: gpt-oss:20b, devstral-small-2:24b, gemma3:27b, qwen3-coder:30b and llama3:8b at draw 1 and
gemini-3-flash-preview at draws 1, 2 and 3 (t3.md), 8 draws x 832 items = 6,656 answers planned. S13: those six models,
baseline and F1, draw 1, 97 items (D198, fig4.md Q2), 1,164 answers planned. ITEMS holds the five benchmarks' sizes. The
deposit's dataset files, which are not in the repository, give them; S524_t3_s12_s13_test.py holds ITEMS to those files
where they are present. S12's b has 194 answers because 6 of the deposit's 200 supervisor items are questions outside
the key (facts_behind_notes.txt:356).

ROW KEYS. An item key in sheets 12b and 13a is its position, 1 up to the benchmark's size: the item ids are in the same
files that are not in the repository, and T3's reader replaces them.

Rows and legends: fig4.md section 6, with build_order.md's rulings: "Gemini", not "cloud", on S12's key and in its legend
(A4), and S13 c's printed value as two sheet columns, d_sign and d_size_pp (F6).
"""
import argparse
import hashlib
import json
import platform
import shutil
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import S457_fig2_panels as S457  # noqa: E402  (finish_plate, write_source_data)
import fig_repro as FR  # noqa: E402  (deterministic files)
import figure_names as FN  # noqa: E402  (D283: the pipeline figure's number)
import figure_names as FN  # noqa: E402
import house_style as hs  # noqa: E402
import pdf_font_determinism  # noqa: E402,F401  (D301: the plate prints a Greek rho; the same font subset every run)

SCRIPT = "scripts/S524_t3_s12_s13.py"
LOCK = ROOT / "experiments" / "LOCK.toml"
FIGURE_LOCK = ROOT / "experiments" / "FIGURE_LOCK.toml"
OUT = ROOT / "findings" / "figures_provisional"
S518_OUT = ROOT / "findings" / "recompute" / "S518_split_confirmation"
FOLDER = {10: "supp_fig10_components", 11: "supp_fig11_distiller_prompts"}
TITLE = {10: "Orchestrator component benchmarks", 11: "Distiller prompt variants"}   # D294: no step lengths

GEMINI_MODEL = "gemini-3-flash-preview"
# D291 (Valerio, 7 Nov): plates and legends print the paper's name; data, keys and Source Data keep the API id
GEN_DISPLAY = {GEMINI_MODEL: "gemini-3-flash"}
APART = "llama3:8b"                               # below the line: its context is LOCK [exceptions]
MODELS = ["gpt-oss:20b", "devstral-small-2:24b", "gemma3:27b", "qwen3-coder:30b", GEMINI_MODEL, APART]
N_ABOVE = MODELS.index(APART)
COMPONENTS = ["Analyser", "Planner", "Supervisor", "Distiller", "Synthesizer"]
ITEMS = {"Analyser": 345, "Planner": 90, "Supervisor": 200, "Distiller": 97, "Synthesizer": 100}   # the module docstring
JUDGED = 194                                      # S12 c (b before D250): the supervisor's items inside the key
# D213 (1) (Valerio, 3 November, experiments/README.md "D213"): the 18 items built on the six questions D9 replaced are
# left out of S12 and S13, so 814 of the 832 items count. findings/recompute/T3_runs/README.md "T3-9" names the six and
# counts them by question id: analyser 5, planner 1, supervisor 6, distiller 3, synthesizer 3; the supervisor's 6 are
# the 6 that S12b's copy leaves out as questions no longer in the key. left_out_ids() holds these counts to the items.
D9_QUESTIONS = ("45_kenya_amr_digital_FR1", "46_methylpipe_CO2", "CD_015", "OOD_011", "SY_010", "SY_018")
LEFT_OUT = {"Analyser": 5, "Planner": 1, "Supervisor": 6, "Distiller": 3, "Synthesizer": 3}
KEPT = {c: ITEMS[c] - LEFT_OUT[c] for c in COMPONENTS}
SCORES = [("Analyser", "decisions match"), ("Planner", "tools match"), ("Distiller", "numbers kept")]   # O7a, no synthesizer
DRAWN = ["Analyser", "Planner", "Supervisor", "Distiller"]   # D294: the components Supplementary Figure 10 draws (a, b)
PROMPTS = ["Baseline", "F1"]
SHOWN = {"Baseline": "Mentor::i's prompt", "F1": "Worked-example prompt"}   # the names the plate and legend print (Valerio, 7 Nov: "Baseline" read as the whole pipeline)
S12_DRAWS = [(m, d) for m in MODELS for d in ((1, 2, 3) if m == GEMINI_MODEL else (1,))]
N_PLANNED = {10: len(S12_DRAWS) * sum(KEPT.values()), 11: len(MODELS) * len(PROMPTS) * KEPT["Distiller"]}

W = hs.PAGE_W_MM
RHO_ROOM = 3.4                                    # S10 a: the line "rho x" under each small panel (6 Nov; n off, 11 Nov)
H_S13 = 100.4                                     # S10's height is computed from its layout (draw_12, D294)
H_GUARD = 169.5                                   # S472's guard: past this the plate is refused
ROW_GAP = 1.6                                     # the space above the row that sits apart
ROW_S12, ROW_S13, ROW_S13C = 3.8, 4.2, 5.4        # row pitch, mm
MS_BOX_H = 22.0                                   # S12 c: height of one small panel
MS_GAP = 2.6                                      # S12 c: between two small panels (six in one row since D250)
S10_BOTTOM = 3.0                                  # S10: below b's x label, the plate's last line (D294)


class Refused(SystemExit):
    pass


def kind_of(model: str) -> str:
    return FN.GEMINI if model == GEMINI_MODEL else FN.OPEN_WEIGHT


def sha256_file(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def context_of_apart() -> int:
    return tomllib.loads(LOCK.read_text())["exceptions"][APART]["num_ctx"]


# ---------------------------------------------------------------------------------------------------------------------
# the planned rows; every value cell is None
# ---------------------------------------------------------------------------------------------------------------------
def sheets_12() -> list:
    """D294: sheet a the supervisor against the judge (sheet c before), sheet b the component scores (d before); the
    step lengths' and the time per item's sheets (a and b before) are dropped with their panels."""
    a = [["model", m, None, None, None, None, None, None, None] for m in MODELS]
    a += [["item", m, None, None, d, i, None, None, None] for m, d in S12_DRAWS for i in range(1, JUDGED + 1)]
    b = [[m, kind_of(m), f"{comp}, {what}", d, KEPT[comp], None] for m, d in S12_DRAWS for comp, what in SCORES]
    return [("Supplementary Fig. 10a", ["row", "model", "n", "rho", "draw", "item", "judge_score", "supervisor_score",
                                        "errors"], a),
            ("Supplementary Fig. 10b", ["model", "kind", "component", "draw", "items_planned", "score"], b)]


def sheets_13() -> list:
    n = KEPT["Distiller"]
    a = [["prompt", m, p, None, None, None, None, None, None, None, None] for m in MODELS for p in PROMPTS]
    a += [["item", m, p, None, None, None, None, None, None, i, None] for m in MODELS for p in PROMPTS
          for i in range(1, n + 1)]
    b = [[m, p, None, None] for m in MODELS for p in PROMPTS]
    c = [[m, None, None, None] for m in MODELS]
    return [("Supplementary Fig. 11a", ["row", "model", "prompt", "n", "minimum", "q1", "median", "q3", "maximum", "item",
                                        "number_retention_pct"], a),
            ("Supplementary Fig. 11b", ["model", "prompt", "mean_source_retention_pct", "mean_number_retention_pct"], b),
            ("Supplementary Fig. 11c", ["model", "change_pp", "d_sign", "d_size_pp"], c)]


VALUE_COLUMNS = {"Supplementary Fig. 10a": {"n", "rho", "judge_score", "supervisor_score", "errors"},
                 "Supplementary Fig. 10b": {"score"},
                 "Supplementary Fig. 11a": {"n", "minimum", "q1", "median", "q3", "maximum", "number_retention_pct"},
                 "Supplementary Fig. 11b": {"mean_source_retention_pct", "mean_number_retention_pct"},
                 "Supplementary Fig. 11c": {"change_pp", "d_sign", "d_size_pp"}}


# ---------------------------------------------------------------------------------------------------------------------
# R5: the reader of T3's sinks (fig4.md section 7), and the values the plates draw
# ---------------------------------------------------------------------------------------------------------------------
INPUTS = ROOT / "findings" / "recompute" / "T3_runs" / "inputs"
S285_CSV = ROOT / "findings" / "recompute" / "S285_component_bench.csv"
BENCH = {"Analyser": "analyzer", "Planner": "planner", "Supervisor": "supervisor", "Distiller": "distiller",
         "Synthesizer": "synthesizer"}                 # exp_04's benchmark names (exp_04:17-19)
VARIANT = {"Baseline": "baseline", "F1": "F1"}         # exp_04b's variant names (exp_04b:21-23)
S13_DRAWS = (1,)
# exp_04_component_bench.py:241-262 and exp_04b_distiller_ablation.py:146-165, the same three patterns in both;
# S524_t3_s12_s13_test.py holds these strings to both files
NUMBER_RE = r"\d+(?:\.\d+)?(?:%|‰)?"
SOURCE_RES = (r"\b\d{2}_\w+\.pdf\b", r"\b[\w-]+\.pdf\b", r"\b[A-Z][a-z]+ et al\.?,? \d{4}\b")
TOO_LONG = "exceeds the available context size"       # llama.cpp's refusal of a prompt longer than num_ctx


def model_key(model: str) -> str:
    """exp_04's model_key and exp_04b's model_short_for with no thinking suffix: the tag with ':' as '-'."""
    return model.replace(":", "-").replace("/", "_")


def item_id_for(item: dict, i: int) -> str:
    """exp_04's item_id_for (exp_04_component_bench.py:311-319): position, then the question id where there is one."""
    qid = item.get("question_id")
    return f"{i:04d}_{qid}" if qid else f"{i:04d}"


def retention(item: dict, text: str):
    """exp_04's (and exp_04b's) number_retention and source_retention of one distillation, rounded to 3 as stored."""
    import re
    nums = set(re.findall(NUMBER_RE, text)) if text else set()
    srcs = set()
    for pat in SOURCE_RES:
        srcs.update(re.findall(pat, text) if text else [])
    raw_n, raw_s = set(item.get("numbers", [])), set(item.get("sources", []))
    n = len(raw_n & nums) / len(raw_n) if raw_n else 1.0
    s = len(raw_s & srcs) / len(raw_s) if raw_s else 1.0
    return round(n, 3), round(s, 3)


def load_inputs(folder: Path = INPUTS) -> dict:
    """T3's frozen items (t3_inputs.py freeze): {benchmark: [items]}, each file held to MANIFEST.json's sha256 and count."""
    man = json.loads((folder / "MANIFEST.json").read_text())
    out = {}
    for b, e in man["files"].items():
        p = folder / e["file"]
        if sha256_file(p) != e["sha256"]:
            raise Refused(f"REFUSED: {p.name} is not the frozen file (sha256 {sha256_file(p)[:12]}, want {e['sha256'][:12]})")
        items = json.loads(p.read_text())
        if len(items) != e["items"]:
            raise Refused(f"REFUSED: {p.name} holds {len(items)} items, MANIFEST.json says {e['items']}")
        out[b] = items
    if {b: len(v) for b, v in out.items()} != {BENCH[c]: ITEMS[c] for c in COMPONENTS}:
        raise Refused(f"REFUSED: the frozen items are not ITEMS: {({b: len(v) for b, v in out.items()})}")
    return out


def verify_set(t3: Path) -> str:
    """The frozen set as copy_t3_frozen.sh wrote it: MANIFEST.json and SHA256SUMS present, every file listed with the
    sha256 it has, no file unlisted. Returns the sha256 of SHA256SUMS."""
    sums = t3 / "SHA256SUMS"
    if not sums.is_file() or not (t3 / "MANIFEST.json").is_file():
        raise Refused(f"REFUSED: {t3} is not a frozen T3 set (no SHA256SUMS or MANIFEST.json)")
    listed = {}
    for ln in sums.read_text().splitlines():
        h, f = ln.split(None, 1)
        listed[f.strip()] = h
    have = {str(p.relative_to(t3)) for p in t3.rglob("*") if p.is_file()} - {"SHA256SUMS", "MANIFEST.json"}
    if have != set(listed):
        raise Refused(f"REFUSED: {t3} holds files SHA256SUMS does not list, or misses listed ones: "
                      f"{sorted(have ^ set(listed))[:4]}")
    bad = [f for f, h in listed.items() if sha256_file(t3 / f) != h]
    if bad:
        raise Refused(f"REFUSED: {len(bad)} file(s) of {t3.name} differ from SHA256SUMS, e.g. {bad[:2]}")
    return sha256_file(sums)


def planned_sinks() -> dict:
    """Every sink the design plans: {run_id: (experiment, component or prompt, model, draws)}."""
    out = {}
    for m in MODELS:
        for c in COMPONENTS:
            out[f"exp_04__{BENCH[c]}__{model_key(m)}"] = ("exp_04", c, m, (1, 2, 3) if m == GEMINI_MODEL else (1,))
        for p in PROMPTS:
            out[f"exp_04b__{VARIANT[p]}__{model_key(m)}"] = ("exp_04b", p, m, S13_DRAWS)
    return out


def read_t3(t3: Path, inputs: dict, lock: dict, equivalent) -> dict:
    """R5. Reads every sink of the frozen set and refuses, writing nothing, on: a sink the design does not plan; a
    run_identity.json or a record of another run; an answer key stored twice; an item outside the frozen dataset or a
    draw outside the plan; an answer with no call or a call with no answer; a call whose lock sha256 is not one
    lock_equiv.py proves equivalent to experiments/LOCK.toml, a local call whose model or digest is not LOCK.toml's
    [models] row (gpt-oss through its [date] copy), a Gemini call of another model; and a stored score that the item
    and the stored text do not give again (analyser decision_correct, planner tool_correct, distiller and exp_04b
    number_retention and source_retention, recomputed with exp_04's own rules). Returns {run_id: {"spec", "answers"
    (sorted by item position and draw), "calls", "length" (answer keys whose call stopped at the context's end)}}."""
    plan = planned_sinks()
    ids = {b: {item_id_for(it, i): (i, it) for i, it in enumerate(items)} for b, items in inputs.items()}
    out = {}
    for d in sorted((t3 / "sinks").iterdir()):
        rid = d.name
        if rid not in plan:
            raise Refused(f"REFUSED: sink {rid} is not one the design plans")
        exp, what, m, draws = plan[rid]
        ident = json.loads((d / "run_identity.json").read_text())
        if ident.get("run_id") != rid:
            raise Refused(f"REFUSED: {rid}/run_identity.json names run {ident.get('run_id')!r}")
        bench = "distiller" if exp == "exp_04b" else BENCH[what]
        mk = model_key(m)
        answers, seen = [], set()
        for n_, ln in enumerate((d / "answers.jsonl").read_text().splitlines(), 1):
            r = json.loads(ln)
            key, iid, dr = r.get("answer_key"), r.get("item_id"), r.get("draw")
            if key in seen:
                raise Refused(f"REFUSED: {rid} stores {key} twice")
            seen.add(key)
            if r.get("run_id") != rid or str(r.get("model_id", "")).split("::")[-1] != m:
                raise Refused(f"REFUSED: {rid}:{n_} is a record of {r.get('run_id')!r}, {r.get('model_id')!r}")
            if iid not in ids[bench]:
                raise Refused(f"REFUSED: {rid}:{n_} item {iid!r} is outside the frozen dataset")
            if dr not in draws or key != f"{mk}|{iid}|d{dr}":
                raise Refused(f"REFUSED: {rid}:{n_} key {key!r}, draw {dr!r}: not in the plan")
            pos, item = ids[bench][iid]
            if not r.get("error"):
                check_score(rid, n_, bench, item, r)
            answers.append((pos, dr, r))
        answers.sort(key=lambda x: (x[0], x[1]))
        calls, by_ctx = 0, {}
        call_model = lock.get("date", {}).get("model_copy", {}).get(m, m)
        want_digest = lock["models"].get(call_model, {}).get("digest")
        for ln in (d / "calls.jsonl").read_text().splitlines():
            c = json.loads(ln)
            calls += 1
            by_ctx.setdefault(c.get("ctx_uid"), []).append(c)
            if c.get("lock_sha256") not in equivalent:
                raise Refused(f"REFUSED: a call of {rid} ran under lock {str(c.get('lock_sha256'))[:12]}, not one "
                              f"equivalent to experiments/LOCK.toml (lock_equiv.py)")
            if m == GEMINI_MODEL:
                if c.get("model") != GEMINI_MODEL:
                    raise Refused(f"REFUSED: a call of {rid} is of model {c.get('model')!r}")
            elif c.get("model") != call_model or c.get("model_digest") != want_digest:
                raise Refused(f"REFUSED: a call of {rid} is {c.get('model')!r} digest {str(c.get('model_digest'))[:12]}, "
                              f"LOCK.toml [models] wants {call_model!r} {str(want_digest)[:12]}")
        ctx = {r["ctx_uid"]: r["answer_key"] for _, _, r in answers}
        if set(ctx) != set(by_ctx):
            raise Refused(f"REFUSED: {rid}: {len(set(ctx) - set(by_ctx))} answer(s) with no call, "
                          f"{len(set(by_ctx) - set(ctx))} call context(s) with no answer")
        length = {ctx[u] for u, cs in by_ctx.items() if any(c.get("stop_reason") == "length" or c.get("status") == "length" for c in cs)}
        out[rid] = {"spec": plan[rid], "answers": [r for _, _, r in answers], "calls": calls, "length": length,
                    "busy": [c.get("busy_servers_on_machine") for cs in by_ctx.values() for c in cs]}
    return out


def check_score(rid, n_, bench, item, r):
    """A stored score the item and the stored text give again, else a refusal."""
    if bench == "analyzer":
        want = r.get("decision") == item["expected_decision"]
        got = r.get("decision_correct")
    elif bench == "planner":
        want = bool(r.get("json_valid")) and any(t in (r.get("actual_tools") or []) for t in item["expected_tools"])
        got = r.get("tool_correct")
    elif bench == "distiller":
        want = retention(item, r.get("distilled") or "")
        got = (r.get("number_retention"), r.get("source_retention"))
    else:
        return
    if got != want:
        raise Refused(f"REFUSED: {rid}:{n_} stores {got!r}; the item and the stored text give {want!r}")


def score_of(component: str, recs) -> float | None:
    """Panel c's score of a model in one draw, exp_04's metrics over the records without an error, in %:
    decision_accuracy (exp_04:1355-1384), tool_accuracy (:1387-1421), mean_number_retention (:1484-1514)."""
    ok = [r for r in recs if not str(r.get("error") or "").strip()]
    if not ok:
        return None
    if component == "Analyser":
        v = sum(1 for r in ok if r.get("decision_correct")) / len(ok)
    elif component == "Planner":
        v = sum(1 for r in ok if r.get("tool_correct")) / len(ok)
    elif component == "Distiller":
        v = sum(r["number_retention"] for r in ok) / len(ok)
    else:
        raise ValueError(component)
    return round(100 * v, 4)


def failure_of(r) -> str | None:
    e = str(r.get("error") or "").strip()
    if not e:
        return None
    return "longer than the context" if TOO_LONG in e else "another failure"


def left_out_ids(inputs: dict) -> dict:
    """D213 (1): {benchmark: the item ids built on one of D9_QUESTIONS}, refused unless their counts are LEFT_OUT's."""
    out = {b: {item_id_for(it, i) for i, it in enumerate(items) if it.get("question_id") in D9_QUESTIONS}
           for b, items in inputs.items()}
    got = {c: len(out[BENCH[c]]) for c in COMPONENTS}
    if got != LEFT_OUT:
        raise Refused(f"REFUSED: the items on D9's six questions are {got}, not D213's {LEFT_OUT}")
    return out


def t3_values(read: dict, inputs: dict) -> dict:
    """The plates' values from the sinks read. Errors are left out of every value and counted (fig4.md section 6).
    D213 (1): the items on D9's six questions are left out first, of every value and count."""
    import statistics
    drop = left_out_ids(inputs)
    by, dropped = {}, {}
    for rid, s in read.items():
        exp, what, m, _ = s["spec"]
        bench = "distiller" if exp == "exp_04b" else BENCH[what]
        for r in s["answers"]:
            if r["item_id"] in drop[bench]:
                dropped[(exp, what)] = dropped.get((exp, what), 0) + 1
                continue
            by.setdefault((exp, what, m, r["draw"]), []).append(r)
    # an answer key (model|item|d<draw>) repeats in every sink of a model, so a length stop is held per sink
    length = {(s["spec"][0], s["spec"][1], s["spec"][2], k) for s in read.values() for k in s["length"]}
    a, c, counts = {}, {}, {}
    for m, d in S12_DRAWS:
        for comp in COMPONENTS:
            recs = by.get(("exp_04", comp, m, d))
            if not recs:
                continue
            ok = [r for r in recs if not failure_of(r)]
            a[(m, d, comp)] = {"items_stored": len(recs), "errors": len(recs) - len(ok),
                               "median_latency_s": round(statistics.median(r["latency_s"] for r in ok), 4) if ok else None}
            counts[("exp_04", m, d, comp)] = {"stored": len(recs), "errors": len(recs) - len(ok),
                                              "too_long": sum(1 for r in recs if failure_of(r) == "longer than the context"),
                                              "length_stops": sum(1 for r in recs if ("exp_04", comp, m, r["answer_key"]) in length)}
            if comp in dict(SCORES):
                c[(m, d, comp)] = score_of(comp, recs)
    ids = [item_id_for(it, i) for i, it in enumerate(inputs["distiller"])
           if item_id_for(it, i) not in drop["distiller"]]
    s13a, s13b, s13c = {}, {}, {}
    for m in MODELS:
        for p in PROMPTS:
            recs = by.get(("exp_04b", p, m, 1))
            if not recs:
                continue
            ok = [r for r in recs if not failure_of(r)]
            pct = {r["item_id"]: round(100 * r["number_retention"], 4) for r in ok}
            st = hs.box_stats(list(pct.values())) if ok else None
            s13a[(m, p)] = {"n": len(ok), "stats": st, "items": [(i, pct.get(i)) for i in ids], "values": list(pct.values())}
            s13b[(m, p)] = (round(100 * statistics.mean(r["source_retention"] for r in ok), 4),
                            round(100 * statistics.mean(r["number_retention"] for r in ok), 4)) if ok else None
            counts[("exp_04b", m, 1, p)] = {"stored": len(recs), "errors": len(recs) - len(ok),
                                            "too_long": sum(1 for r in recs if failure_of(r) == "longer than the context"),
                                            "length_stops": sum(1 for r in recs if ("exp_04b", p, m, r["answer_key"]) in length)}
        if s13b.get((m, "Baseline")) and s13b.get((m, "F1")):
            ch = round(s13b[(m, "F1")][1] - s13b[(m, "Baseline")][1], 4)
            txt = hs.fmt_num(ch, 1, sign=True)
            sign = txt[0] if txt[0] in "+" + hs.MINUS else ""
            s13c[m] = {"change_pp": ch, "d_sign": sign, "d_size_pp": float(txt.lstrip("+" + hs.MINUS)), "text": txt}
    local_busy = [b for s in read.values() if s["spec"][0] == "exp_04" and s["spec"][2] != GEMINI_MODEL for b in s["busy"]]
    stored = {10: sum(len(v) for k, v in by.items() if k[0] == "exp_04"),
              11: sum(len(v) for k, v in by.items() if k[0] == "exp_04b")}
    return {"12a": a, "12c": c, "13a": s13a, "13b": s13b, "13c": s13c, "counts": counts, "stored": stored,
            "item_ids": ids, "dropped": dropped, "by": by, "busy": {"calls": len(local_busy), "busy": sum(1 for b in local_busy if b),
                                      "unread": sum(1 for b in local_busy if b is None)}}


# ---------------------------------------------------------------------------------------------------------------------
# R6: the reader of S12b's judge rows (job S10, plan.csv S10; fig4.md section 6 "12b" and section 7 R6), and panel c
# ---------------------------------------------------------------------------------------------------------------------
S12B = ROOT / "findings" / "recompute" / "s12b_inputs"   # S10's copy, frozen 6 Nov with its SHA256SUMS (FROM.json)
S12B_RUN, S12B_SET, S12B_SCOPE = "s12b_april", "S6WS12B", "whole:s12b"
S12B_MAP = INPUTS / "s12b_item_map.json"


def rho_of(xs, ys) -> float | None:
    """Spearman's rho as exp_04 computes it (exp_04_component_bench.py:1439-1446: scipy.stats.spearmanr, rounded to
    4), on 10 or more pairs; None below 10 or when a side is constant."""
    import math
    from scipy.stats import spearmanr
    if len(xs) < 10 or len(set(xs)) < 2 or len(set(ys)) < 2:
        return None
    r = float(spearmanr(xs, ys)[0])
    return None if math.isnan(r) else round(r, 4)


def read_s12b(folder: Path, inputs: dict, lock: dict, equivalent) -> dict:
    """R6. S10's frozen copy: the 194 April supervisor answers (inputs/) and their judge rows on key v2.5 (out/).
    Refuses, writing nothing, on: a file not as SHA256SUMS lists it, or one unlisted; a copy of another set or of a
    supervisor file other than T3's; an answer key twice, missing or extra against s12b_item_map.json's in-key rows; an
    answer whose text's sha256 is not the map's (the T3 supervisor item's); a judge row twice, missing or extra; a row of
    another run, scope or key version, or whose key_hash or answerable prompt is not key v2.5's (S512); a run_sha256
    not the summary's and the headers'; a lock not equivalent to LOCK.toml; a judge model or digest not LOCK.toml's [judge]
    model; a call not ok; a score outside 0 to 5. The score is correctness, or refusal_accuracy where the prompt is the
    not-answerable one (fig4.md 12b: exp_04:736, S463.METRIC). The run is judge_passages_summary.json's run_sha256,
    whose recheck (calls repeated, scores equal) must have passed. Returns {"score": {item_id: score}, "order": the item
    ids in the map's order, "run_sha256", "sums_sha256"}."""
    import S512_s6_rejudge_v25 as S512
    folder = Path(folder)
    sums = folder / "SHA256SUMS"
    if not sums.is_file():
        raise Refused(f"REFUSED: {folder} is not a frozen S12b copy (no SHA256SUMS)")
    listed = {ln.split(None, 1)[1].strip(): ln.split(None, 1)[0] for ln in sums.read_text().splitlines() if ln.strip()}
    have = {str(p.relative_to(folder)) for p in folder.rglob("*") if p.is_file()} - {"SHA256SUMS"}
    if have != set(listed) or any(sha256_file(folder / f) != h for f, h in listed.items()):
        raise Refused(f"REFUSED: {folder.name}: files and SHA256SUMS disagree: {sorted(have ^ set(listed))[:3]}")
    man = json.loads((INPUTS / "MANIFEST.json").read_text())
    if sha256_file(S12B_MAP) != man["s12b_item_map"]["sha256"]:
        raise Refused("REFUSED: s12b_item_map.json is not the frozen map (T3_runs/inputs/MANIFEST.json)")
    want = {r["answer_key"]: r for r in json.loads(S12B_MAP.read_text()) if r["in_key"]}
    if len(want) != JUDGED:
        raise Refused(f"REFUSED: the map holds {len(want)} in-key supervisor items, not {JUDGED}")
    cp = json.loads((folder / "inputs" / "COPY.json").read_text())
    if cp.get("set") != S12B_SET or cp.get("source_sha256") != man["files"]["supervisor"]["sha256"] \
            or cp.get("answer_lines") != {S12B_RUN: JUDGED}:
        raise Refused(f"REFUSED: inputs/COPY.json is not S12b's copy of T3's supervisor file: {cp.get('set')!r}, "
                      f"{str(cp.get('source_sha256'))[:12]}, {cp.get('answer_lines')}")
    seen = set()
    for ln in (folder / "inputs" / "runs" / S12B_RUN / "answers.jsonl").read_text().splitlines():
        r = json.loads(ln)
        k = r["answer_key"]
        if k in seen or k not in want:
            raise Refused(f"REFUSED: the copy's answer {k} is {'twice' if k in seen else 'not an in-key map row'}")
        seen.add(k)
        if hashlib.sha256(r["generation"]["answer"].encode("utf-8")).hexdigest() != want[k]["answer_sha256"]:
            raise Refused(f"REFUSED: the copy's answer {k} is not the text of T3's supervisor item {want[k]['item_id']}")
    if seen != set(want):
        raise Refused(f"REFUSED: the copy misses {len(set(want) - seen)} in-key answer(s)")
    judge_model = lock["judge"]["model"]
    digest = lock["models"][judge_model]["digest"]
    jdir = folder / "out" / "judge" / S12B_RUN
    summ = json.loads((jdir / "judge_passages_summary.json").read_text())
    run = summ.get("run_sha256")
    rc = summ.get("recheck") or {}
    if not run or summ.get("rows") != JUDGED or summ.get("status_a") != {"ok": JUDGED} or not rc.get("passed") \
            or rc.get("equal") != rc.get("n") or rc.get("run_sha256") != run:
        raise Refused(f"REFUSED: judge_passages_summary.json: rows {summ.get('rows')}, status {summ.get('status_a')}, "
                      f"recheck {rc.get('equal')} of {rc.get('n')} passed {rc.get('passed')}; want {JUDGED} ok and a "
                      f"recheck of the same run passed")
    for ln in (jdir / "judge_passages_headers.jsonl").read_text().splitlines():
        h = json.loads(ln)
        if (h.get("model"), h.get("model_digest"), h.get("run_sha256")) != (judge_model, digest, run) \
                or h.get("lock_sha256") not in equivalent:
            raise Refused(f"REFUSED: a judge header is {h.get('model')!r} {str(h.get('model_digest'))[:12]}, run "
                          f"{str(h.get('run_sha256'))[:12]}, lock {str(h.get('lock_sha256'))[:12]}; want {judge_model} "
                          f"{digest[:12]}, run {str(run)[:12]}, a lock equivalent to LOCK.toml")
    _, k25 = S512.keys()
    v2 = S512.v2_records()
    score, rows = {}, set()
    for n_, ln in enumerate((jdir / "judge_passages.jsonl").read_text().splitlines(), 1):
        r = json.loads(ln)
        k, q = r.get("answer_key"), r.get("question_id")
        where = f"judge_passages.jsonl:{n_} {k}"
        if k in rows or k not in want:
            raise Refused(f"REFUSED: {where} is {'twice' if k in rows else 'not an in-key map row'}")
        rows.add(k)
        if (r.get("run_id"), r.get("run_sha256"), r.get("key_version"), r.get("questions")) != \
                (S12B_RUN, run, S512.KEY_VERSION, S12B_SCOPE) or r.get("lock_sha256") not in equivalent:
            raise Refused(f"REFUSED: {where}: run {r.get('run_id')!r} {str(r.get('run_sha256'))[:12]}, key "
                          f"{r.get('key_version')!r}, scope {r.get('questions')!r}, lock {str(r.get('lock_sha256'))[:12]}")
        if q != want[k]["question_id"] or r.get("key_hash") != S512.key_hash25(q, v2):
            raise Refused(f"REFUSED: {where}: key_hash {r.get('key_hash')} is not key v2.5's for {q}")
        ans = k25[q]["answerable"] in (True, "true", "True")
        if bool(r.get("answerable_prompt")) != ans:
            raise Refused(f"REFUSED: {where}: answerable prompt {r.get('answerable_prompt')}, key v2.5 says {ans}")
        a = r.get("a") or {}
        if a.get("status") != "ok" or a.get("model_digest") != digest:
            raise Refused(f"REFUSED: {where}: call status {a.get('status')!r}, digest {str(a.get('model_digest'))[:12]}")
        v = (a.get("scores") or {}).get("correctness" if ans else "refusal_accuracy")
        if not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= 5:
            raise Refused(f"REFUSED: {where}: score {v!r} is not 0 to 5")
        score[want[k]["item_id"]] = v
    if rows != set(want):
        raise Refused(f"REFUSED: {len(set(want) - rows)} in-key answer(s) have no judge row")
    order = [r["item_id"] for r in json.loads(S12B_MAP.read_text()) if r["in_key"]]
    return {"score": score, "order": order, "run_sha256": run, "sums_sha256": sha256_file(sums), "judge": judge_model}


def s12b_values(V: dict, J: dict) -> dict:
    """Panel c: per model and draw, each judged item's judge score and T3 supervisor score (quality_score, where the
    answer did not fail and gave a valid score); per model the pairs drawn, one per item (gemini-3-flash-preview: the
    mean of its draws' scores), and Spearman's rho over them. Failed answers and answers with no score are left out
    and counted."""
    import statistics
    rows, model = {}, {}
    for m in MODELS:
        draws = [d for mm, d in S12_DRAWS if mm == m]
        per = {}
        failed = no_score = 0
        for d in draws:
            recs = {r["item_id"]: r for r in V["by"].get(("exp_04", "Supervisor", m, d), [])}
            out = []
            for pos, iid in enumerate(J["order"], 1):
                r = recs.get(iid)
                sup = None
                if r is not None and not failure_of(r):
                    q = r.get("quality_score")
                    if r.get("score_valid") and isinstance(q, (int, float)) and not isinstance(q, bool) and 0 <= q <= 100:
                        sup = q
                    else:
                        no_score += 1
                elif r is not None:
                    failed += 1
                if sup is not None:
                    per.setdefault(iid, []).append(sup)
                out.append((pos, iid, J["score"][iid], sup, 0 if sup is not None else (None if r is None else 1)))
            rows[(m, d)] = out
        if not per:
            continue
        pairs = [(J["score"][iid], round(statistics.mean(per[iid]), 4)) for iid in J["order"] if iid in per]
        model[m] = {"n": len(pairs), "rho": rho_of([b for _, b in pairs], [a for a, _ in pairs]), "pairs": pairs,
                    "failed": failed, "no_score": no_score, "draws": len(draws)}
    return {"rows": rows, "model": model}


def sheets_12_t3(V) -> list:
    """D294: sheet 10a the supervisor against the judge (V["s12b"], R6), a frame when no S12b copy is read; sheet 10b
    the component scores (V["12c"]: the values code keeps the letters of before D250)."""
    sh = sheets_12()
    S = V.get("s12b")
    if S is not None:
        a = [["model", m, S["model"].get(m, {}).get("n"), S["model"].get(m, {}).get("rho"), None, None, None, None, None]
             for m in MODELS]
        a += [["item", m, None, None, d, pos, judge, sup, err] for m, d in S12_DRAWS
              for pos, _, judge, sup, err in S["rows"][(m, d)]]
        sh[0] = (sh[0][0], sh[0][1], a)
    b = [[m, k, lab, d, n, V["12c"].get((m, d, lab.split(",")[0]))] for m, k, lab, d, n, _ in sh[1][2]]
    return [sh[0], (sh[1][0], sh[1][1], b)]


def sheets_13_t3(V) -> list:
    sh = sheets_13()
    a = []
    for m in MODELS:
        for p in PROMPTS:
            e = V["13a"].get((m, p))
            st = e["stats"] if e else None
            a.append(["prompt", m, p, e["n"] if e else None,
                      *((round(st[k], 4) for k in ("whisker_low", "q1", "median", "q3", "whisker_high")) if st
                        else (None,) * 5), None, None])
    for m in MODELS:
        for p in PROMPTS:
            e = V["13a"].get((m, p))
            items = e["items"] if e else [(i, None) for i in V["item_ids"]]
            a += [["item", m, p, None, None, None, None, None, None, i, v] for i, v in items]
    b = [[m, p, *(V["13b"].get((m, p)) or (None, None))] for m in MODELS for p in PROMPTS]
    c = [[m, *((V["13c"][m][k] for k in ("change_pp", "d_sign", "d_size_pp")) if m in V["13c"] else (None,) * 3)]
         for m in MODELS]
    return [(sh[0][0], sh[0][1], a), (sh[1][0], sh[1][1], b), (sh[2][0], sh[2][1], c)]


def bench_rows(results, name: str) -> list | None:
    """The rows of the deposit's exp07 file <name>, None when absent. results is a folder (scripts/machine.py RESULTS by
    default) or the committed tar findings/recompute/exp07_bench_20261107/exp07_bench_20261107.tar (D287 O3, --results),
    each of whose members is checked against the SHA256SUMS beside it before it is read."""
    results = Path(results)
    if results.suffix == ".tar":
        import tarfile
        listed = {}
        for ln in (results.parent / "SHA256SUMS").read_text().splitlines():
            if ln.strip():
                h, n = ln.split("  ", 1)
                listed[n] = h
        if listed.get(results.name) != sha256_file(results):
            raise Refused(f"REFUSED, nothing written: {results.name} is not its SHA256SUMS line")
        with tarfile.open(results) as tf:
            ti = next((t for t in tf if t.isfile() and t.name.rsplit("/", 1)[-1] == name), None)
            if ti is None:
                return None
            b = tf.extractfile(ti).read()
        if hashlib.sha256(b).hexdigest() != listed.get(ti.name):
            raise Refused(f"REFUSED, nothing written: {results.name}:{ti.name} differs from SHA256SUMS")
        return json.loads(b.decode()).get("results") or []
    f = results / name
    return (json.loads(f.read_text()).get("results") or []) if f.is_file() else None


def reproduce_published(results: Path | None = None) -> list:
    """Reproduce before writing (fig4.md section 6): accuracy_published of the submitted run for devstral-small-2:24b
    and gemini-3-flash-preview, recomputed from the deposit's exp07_bench_<component>_<model>.json with score_of (the
    function that scores T3), equal to findings/recompute/S285_component_bench.csv, for the three components panel c
    draws, and the supervisor's rho_published (panel c's rho, R6). Rows whose error names a 404 are dropped first, as
    S285 does. Only these two models' files are opened and only their rows are printed. Refuses when a file is missing or a value differs."""
    import csv
    if results is None:
        from machine import RESULTS as results
    want = {(r["component"], r["model_key"]): r for r in csv.DictReader(open(S285_CSV))}
    out = []
    for comp in ("Analyser", "Planner", "Distiller"):
        for mk in ("devstral-small-2-24b", "gemini-3-flash-preview"):
            f = Path(results) / f"exp07_bench_{BENCH[comp]}_{mk}.json"
            raw = bench_rows(results, f.name)
            if raw is None:
                raise Refused(f"REFUSED, nothing written: the reproduction needs {f} (the deposit), not on this machine")
            rows = [r for r in raw if "404" not in str(r.get("error") or "")]
            if any(r.get("model_key") != mk for r in rows):
                raise Refused(f"REFUSED: {f.name} holds rows of another model")
            got = score_of(comp, rows)
            w = float(want[(BENCH[comp], mk)]["accuracy_published"])
            out.append({"component": comp, "model_key": mk, "recomputed": got, "S285": w,
                        "equal": got is not None and abs(got - w) < 1e-9})
    # panel c's rho (R6): rho_published of the submitted supervisor run, recomputed with rho_of on the deposit's own
    # pairs (quality_score against _judge_correctness, exp_04:1434-1446), equal to S285 for the same two models
    for mk in ("devstral-small-2-24b", "gemini-3-flash-preview"):
        f = Path(results) / f"exp07_bench_supervisor_{mk}.json"
        raw = bench_rows(results, f.name)
        if raw is None:
            raise Refused(f"REFUSED, nothing written: the reproduction needs {f} (the deposit), not on this machine")
        rows = [r for r in raw if "404" not in str(r.get("error") or "")]
        ok = [r for r in rows if not r.get("error") and r.get("quality_score") is not None
              and r.get("_judge_correctness") is not None]
        got = rho_of([r["quality_score"] for r in ok], [r["_judge_correctness"] for r in ok])
        w = float(want[("supervisor", mk)]["rho_published"])
        out.append({"component": "Supervisor rho", "model_key": mk, "recomputed": got, "S285": w,
                    "equal": got is not None and abs(got - w) < 1e-9})
    bad = [o for o in out if not o["equal"]]
    for o in out:
        print(f"reproduce {o['component']:9s} {o['model_key']:24s} {o['recomputed']} vs S285 {o['S285']}: "
              f"{'equal' if o['equal'] else 'DIFFERS'}")
    if bad:
        raise Refused(f"REFUSED, nothing written: {len(bad)} of {len(out)} reproduced values differ from S285: {bad}")
    return out


# ---------------------------------------------------------------------------------------------------------------------
# the plates
# ---------------------------------------------------------------------------------------------------------------------
class Plate:
    """One plate on a white page: text in mm from the top left, every digit-bearing text tied through `printed`."""

    def __init__(self, h: float, simplify: bool = True):
        import logging
        logging.getLogger("fontTools").setLevel(logging.ERROR)
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        plt.rcParams.update(hs.rc("S524"))
        plt.rcParams["path.simplify"] = simplify         # D250's step curve needed False; no plate does since D294
        if h > H_GUARD:
            raise Refused(f"a plate {h} mm high is past the guard {H_GUARD} mm")
        self.h, self.fig, self.printed = h, hs.figure(W, h), {}

    def fixed(self, artist, why):
        gid = f"s448num_{len(self.printed)}"
        artist.set_gid(gid)
        self.printed[gid] = {"fixed": artist.get_text(), "why": why}
        return artist

    def tied(self, artist, sheet, row, fmt):
        """A printed value, tied for S448 R8 (6) to its workbook sheet, data row (0-based) and format."""
        gid = f"s448num_{len(self.printed)}"
        artist.set_gid(gid)
        self.printed[gid] = {"sheet": sheet, "row": row, "format": fmt}
        return artist

    def text(self, x, y, s, **kw):
        return hs.text_mm(self.fig, x, y, s, **kw)

    def model(self, x, y, m, **kw):
        return self.fixed(self.text(x, y, GEN_DISPLAY.get(m, m), **kw), "a model's name")

    def key(self, items, centre_x, y):
        before = set(map(id, self.fig.texts))
        hs.key(self.fig, items, centre_x=centre_x, y=y)
        for t in self.fig.texts:
            if id(t) not in before and any(ch.isdigit() for ch in t.get_text()):
                self.fixed(t, "a key's words")

    def letter(self, x, y, ch):
        return hs.panel_letter(self.fig, x, y, ch)

    def rows_axes(self, x, y, w, pitch, xlim, ticks, labels, log=False):
        """A column of the six model rows: bottom axis only, the grey line above the row that sits apart."""
        h = len(MODELS) * pitch + ROW_GAP
        ax = hs.axes_mm(self.fig, x, y, w, h, spines_on=("bottom",))
        if log:
            ax.set_xscale("log")
        ax.set_xlim(*xlim)
        ax.set_ylim(h / pitch, 0)
        ax.set_yticks([])
        ax.set_xticks(ticks, labels)
        ax.minorticks_off()
        yy = N_ABOVE + 0.5 * ROW_GAP / pitch
        ax.plot(list(xlim), [yy, yy], color=hs.GREY["line"], lw=hs.LW["divider"], zorder=0, clip_on=False,
                solid_capstyle="butt")
        return ax

    def row_y(self, top, i, pitch):
        return top + (i + 0.5) * pitch + (ROW_GAP if i >= N_ABOVE else 0.0)


def label_right(models=MODELS) -> float:
    return 2.4 + max(hs._text_width_mm(GEN_DISPLAY.get(m, m)) for m in models) + 0.3


def ypos(i: int, pitch: float) -> float:
    """Row i's centre in a rows_axes column's data units (one unit is one row pitch)."""
    return i + 0.5 + (ROW_GAP / pitch if i >= N_ABOVE else 0.0)


def on_axis(ax, v, what):
    lo, hi = sorted(ax.get_xlim())
    if not lo <= v <= hi:
        raise Refused(f"REFUSED, nothing written: {what} = {v} is off its axis ({lo} to {hi})")


def marks_rows(p, axes, values, pitch):
    """S10 b: one dot per draw on a model's row, filled for Gemini, open for open-weight (DOT_SPARSE_MM), and a
    tick at the median of a model's dots where it has three. values: {(model, draw, column): value}."""
    import statistics
    for k, (col, ax) in enumerate(axes):
        for i, m in enumerate(MODELS):
            vs = [values[(m, d, col)] for mm, d in S12_DRAWS if mm == m and values.get((m, d, col)) is not None]
            if not vs:
                continue
            for v in vs:
                on_axis(ax, v, f"{m} {col}")
            hs.strip(ax, ypos(i, pitch), vs, size_mm=hs.DOT_SPARSE_MM, colour=hs.BLACK,
                     open_=kind_of(m) == FN.OPEN_WEIGHT, edge=hs.BLACK if kind_of(m) == FN.OPEN_WEIGHT else None)
            if len(vs) == 3:
                hs.summary_tick(ax, ypos(i, pitch), statistics.median(vs))


def two_lines(m: str, width: float) -> str:
    """A model's name as one line when it fits width (mm), else broken after its last hyphen that makes it fit."""
    if hs._text_width_mm(m) <= width:
        return m
    for i in range(len(m) - 1, 0, -1):
        if m[i] == "-" and hs._text_width_mm(m[:i + 1]) <= width and hs._text_width_mm(m[i + 1:]) <= width:
            return m[:i + 1] + "\n" + m[i + 1:]
    raise Refused(f"the model name {m!r} does not fit {width:.1f} mm on two lines")


def draw_12(paths, fill=None):
    """D294's layout: a, the supervisor against the judge (c before), the six small panels in one row; b, the
    component scores (d before), with the key of filled and open dots that the time per item (b before) carried."""
    import statistics
    pitch = ROW_S12
    labr = label_right()
    x0 = labr + 1.8
    h = len(MODELS) * pitch + ROW_GAP
    line = hs.PT * hs.MM_PT * 1.2
    x_b = 11.4
    wb = (181.8 - x_b - (len(MODELS) - 1) * MS_GAP) / len(MODELS)
    names = {m: two_lines(GEN_DISPLAY.get(m, m), wb + MS_GAP - 0.6).split("\n") for m in MODELS}
    nl = max(len(v) for v in names.values())
    # a: the letter's baseline at 2.9 mm, the top line of the longest model name on the same baseline
    ly = 2.9
    yt = ly + 1.6 + (nl - 1) * line                    # the panels' top; each model's name ends just above it
    lyb = yt + MS_BOX_H + 13.7 + RHO_ROOM              # a's axis, its tick labels, x label and rho line
    rtb = lyb + 5.4
    last = rtb + h + 7.0
    p = Plate(round(last + S10_BOTTOM, 1))
    first = p.letter(0, ly, "a")
    p.fixed(first, "panel letter")
    S = fill.get("s12b") if fill is not None else None
    for k, m in enumerate(MODELS):
        x = x_b + k * (wb + MS_GAP)
        lines = names[m]                                # one text per line: S448 R10 pairs single lines
        for j, ln in enumerate(lines):
            p.model(x + wb / 2, yt - 1.6 - (len(lines) - 1 - j) * line, ln, ha="center")
        ax = hs.axes_mm(p.fig, x, yt, wb, MS_BOX_H)
        ax.set_xlim(-0.5, 5.5)
        ax.set_ylim(-3, 103)
        ax.set_xticks(range(6))
        ax.set_yticks([0, 50, 100], ["0", "50", "100"] if k == 0 else ["", "", ""])
        ax.set_xlabel("Judge score", labelpad=1.5)
        e = S["model"].get(m) if S else None
        if e:
            for js in range(6):
                vs = [b for a, b in e["pairs"] if a == js]
                if not vs:
                    continue
                if len(vs) >= hs.SMALL_N:
                    hs.boxplot(ax, js, vs, orient="v", dot_mm=hs.DOT_MM)
                else:
                    hs.strip(ax, js, vs, orient="v", size_mm=hs.DOT_MM)
                    hs.summary_tick(ax, js, statistics.median(vs), orient="v")
            row = MODELS.index(m)
            # Valerio, 11 Nov: the plate holds only the figure; each model's n is in the legend ("n = 194 answers
            # per model; 190 for gpt-oss:20b and 191 for llama3:8b"), so the line under a panel prints rho only
            if e["rho"] is not None:
                p.tied(p.text(x + wb / 2, yt + MS_BOX_H + 10.4, f"ρ {e['rho']:.2f}", ha="center",
                              va="center"), "Supplementary Fig. 10a", row, "ρ {rho:.2f}")
    p.text(1.8, yt + MS_BOX_H / 2, "Supervisor score", rotation=90, ha="left", va="center")
    xd = x_b + N_ABOVE * (wb + MS_GAP) - MS_GAP / 2
    pg = p.fig.add_axes((0, 0, 1, 1))
    pg.set_xlim(0, W)
    pg.set_ylim(p.h, 0)
    pg.axis("off")
    pg.plot([xd, xd], [yt - 3.0, yt + MS_BOX_H + 5.0], color=hs.GREY["line"], lw=hs.LW["divider"],
            solid_capstyle="butt", clip_on=False)

    # b: component scores, one row per model, a dot per draw
    p.letter(0, lyb, "b")
    gap = 7.0                                           # "100" and the next "0" must not read as one number
    w = (180.4 - x0 - 2 * gap) / 3                      # room for half of the last "100"
    p.key([("mark", (hs.BLACK, "o"), FN.GEMINI), ("open", (hs.BLACK, "o"), FN.OPEN_WEIGHT)],
          x0 + (3 * w + 2 * gap) / 2, lyb)
    axc = []
    for k, (comp, what) in enumerate(SCORES):
        x = x0 + k * (w + gap)
        p.text(x + w / 2, lyb + 3.7, f"{comp} ({what}, %)", ha="center")
        axc.append((comp, p.rows_axes(x, rtb, w, pitch, (0, 100), [0, 50, 100], ["0", "50", "100"])))
    for i, m in enumerate(MODELS):
        p.model(labr, p.row_y(rtb, i, pitch), m, ha="right", va="center_baseline")
    p.text(x0 + (3 * w + 2 * gap) / 2, last, "Component score (%)", ha="center")
    if last + 2.0 > p.h:
        raise Refused(f"Supplementary Figure 10: its last line at {last:.1f} mm is past the page ({p.h} mm)")
    if fill is not None:                                # a is drawn above, from S12b's judge rows (R6)
        marks_rows(p, axc, fill["12c"], pitch)
    return finish(p, 10, paths)


def draw_13(paths, fill=None):
    p = Plate(H_S13)
    axa = []
    pitch = ROW_S13
    labr = label_right()
    x0, gap = labr + 1.8, 5.0
    h = len(MODELS) * pitch + ROW_GAP

    # a: numbers kept, one column per prompt
    ly = 2.9
    rt = ly + 1.8
    first = p.letter(0, ly, "a")
    p.fixed(first, "panel letter")
    w = (180.2 - x0 - gap) / 2
    for k, pr in enumerate(PROMPTS):
        x = x0 + k * (w + gap)
        t = p.text(x + w / 2, ly, SHOWN[pr], ha="center")
        p.fixed(t, "a prompt's name")
        axa.append((pr, p.rows_axes(x, rt, w, pitch, (0, 100), [0, 50, 100], ["0", "50", "100"])))
    for i, m in enumerate(MODELS):
        p.model(labr, p.row_y(rt, i, pitch), m, ha="right", va="center_baseline")
    p.text(x0 + (2 * w + gap) / 2, rt + h + 7.0, "Numbers kept from the input (%)", ha="center")

    # b: numbers against source names
    ly = rt + h + 7.0 + 3.2 + 2.9
    p.letter(0, ly, "b")
    bx0, bx1, hh = 12.0, 82.0, 42.0
    p.key([("mark", (hs.BLACK, "o"), SHOWN[PROMPTS[0]]), ("mark", (hs.OKABE["orange"], "s"), SHOWN[PROMPTS[1]])],
          (bx0 + bx1) / 2 + 1.0, ly)
    ax = hs.axes_mm(p.fig, bx0, ly + 5.4, bx1 - bx0, hh)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_xlabel("Source names kept (%)", labelpad=1.5)
    p.text(1.8, ly + 5.4 + hh / 2, "Numbers kept (%)", rotation=90, ha="left", va="center")
    ax.plot([0, 100], [0, 100], color=hs.BLACK, lw=hs.LW["reference"], dashes=hs.DASH, zorder=1)
    axb = ax

    # c: change with F1, one dot per model; its value column at the right stays empty on a frame
    xlet = 90.0
    p.letter(xlet, ly, "c")
    labr = xlet + label_right()
    xg, xr = labr + 1.8, 170.0
    top = 56.6
    ax = p.rows_axes(xg, top, xr - xg, ROW_S13C, (-30, 30), [-30, 0, 30],
                     [hs.fmt_num(-30), "0", hs.fmt_num(30, sign=True)])
    hs.reference_line(ax, 0)
    ax.set_xlabel("Change in numbers kept (percentage points)", labelpad=1.5)
    for i, m in enumerate(MODELS):
        p.model(labr, p.row_y(top, i, ROW_S13C), m, ha="right", va="center_baseline")
    if fill is not None:
        marks_13(p, fill, axa, axb, ax, top, xr)
    return finish(p, 13, paths)


def marks_13(p, V, axa, axb, axc, top, xr):
    """S13 a: a house box over one dot per item (DOT_MM); under SMALL_N items, the dots and a tick at the median.
    b: one mark per model and prompt, Baseline a black circle, F1 an orange square. c: F1 minus Baseline, a blue dot
    above zero, a vermilion one below, grey at zero; the value printed at the right, tied to sheet 13c."""
    for pr, ax in axa:
        for i, m in enumerate(MODELS):
            e = V["13a"].get((m, pr))
            if not e or not e["values"]:
                continue
            for v in (e["stats"]["whisker_low"], e["stats"]["whisker_high"]):
                on_axis(ax, v, f"{m} {pr} numbers kept")
            if len(e["values"]) >= hs.SMALL_N:
                hs.boxplot(ax, ypos(i, ROW_S13), e["values"], stats=e["stats"], dot_mm=hs.DOT_MM)
            else:
                hs.strip(ax, ypos(i, ROW_S13), e["values"], size_mm=hs.DOT_MM)
                hs.summary_tick(ax, ypos(i, ROW_S13), e["stats"]["median"])
    look = {PROMPTS[0]: (hs.BLACK, "o"), PROMPTS[1]: (hs.OKABE["orange"], "s")}
    for m in MODELS:
        for pr in PROMPTS:
            xy = V["13b"].get((m, pr))
            if not xy:
                continue
            col, mk = look[pr]
            on_axis(axb, xy[0], f"{m} {pr} source names kept")
            axb.plot([xy[0]], [xy[1]], ls="none", marker=mk, ms=hs.MARK_MM * hs.MARKER_SCALE[mk] / hs.MM_PT, mfc=col,
                     mec=hs.WHITE, mew=0.3, zorder=3, clip_on=False)
    cmp = hs.COLOURS["comparison"]
    for i, m in enumerate(MODELS):
        e = V["13c"].get(m)
        if not e:
            continue
        on_axis(axc, e["change_pp"], f"{m} change with F1")
        col = cmp["better"] if e["d_sign"] == "+" else cmp["worse"] if e["d_sign"] == hs.MINUS else cmp["tie"]
        hs.estimate(axc, ypos(i, ROW_S13C), e["change_pp"], colour=col)
        t = p.text(xr + 2.0, p.row_y(top, i, ROW_S13C), e["text"], ha="left", va="center_baseline")
        p.tied(t, "Supplementary Fig. 11c", i, "{d_sign}{d_size_pp:.1f}")


def finish(p, n, paths):
    hs.check_plate_kinds(("comparison",))              # S13 c's blue and vermilion; no other kind on either plate
    bad = hs.check_figure_colours(p.fig)
    if bad:
        raise Refused(f"Supplementary Figure {n}: colours outside the house palette {bad}")
    S457.finish_plate(p.fig, W, p.h, paths, title=f"Supplementary Figure {n}")
    return p.h, p.printed


# ---------------------------------------------------------------------------------------------------------------------
# legends and captions
# ---------------------------------------------------------------------------------------------------------------------
def legend_12(a_text: str = "", n_text: str = "", n_after: str = "") -> str:
    """D294: a, the supervisor against the judge (c before); b, the component scores (d before). The items named are
    those of the four components the plate draws (DRAWN; the synthesizer was in the dropped time panel only).
    Valerio, 8 Nov, editor row 45: the one n sits in a, the only panel with derived statistics (boxes); b draws one
    dot per draw and carries none; every panel is described in full (no 'in a'). a_text adds a's figure-only
    sentences, n_text qualifies a's n (the models whose n departs from the design); n_after counts, inside a, the
    supervisor answers a leaves out (adversarial check of 8 Nov: they sat after b, so a's n pointed into b); the doc's
    'the final key'."""
    a, b = "**a**", "**b**"
    gem, ctx = GEN_DISPLAY[GEMINI_MODEL], f"{context_of_apart():,}"
    items = _join(f"{KEPT[k]} {k.lower()}" for k in DRAWN) + " items"
    return (f"**Supplementary Figure 10 | {TITLE[10]}.** Each component was tested alone on its own items: {items}, "
            f"the {sum(LEFT_OUT[k] for k in DRAWN)} of these four components' items built on questions later replaced in the answer key left "
            f"out. Five open-weight models answered each item once and {gem} answered it on three draws. "
            f"{a}, Supervisor score against the judge score of the same answer, one panel per model; the judge scores "
            f"an answer on the final key, or gives the refusal score for {FN.OUT_OF_SCOPE_QUESTIONS}. Boxes: median "
            f"and quartiles; whiskers: the range; grey dots: one answer each; a judge score with fewer than "
            f"{hs.SMALL_N} answers shows its dots and a tick at their median. ρ, Spearman's ρ of the two scores. "
            f"{APART} sits right of the grey line because its context is {ctx} tokens.{a_text} "
            f"n = {JUDGED} answers per model{n_text}.{n_after} "
            f"{b}, Component score (%), one row per model and one column per component: analyser, decisions matching "
            f"the label; planner, tools matching the label; distiller, numbers kept. The analyser's label counts "
            f"sending an out-of-scope question to a direct answer as correct. One dot per draw: filled, {FN.GEMINI}; "
            f"open, {FN.OPEN_WEIGHT}; a tick marks the median of {gem}'s three draws. {APART} sits below the grey "
            f"line because its context is {ctx} tokens.")


def legend_13(n_text: str = "") -> str:
    """Valerio, 8 Nov, editor row 45: the one n sits in a, the only panel with derived statistics (boxes); b and c draw
    means with no spread and carry none; every panel is described in full (no 'as in a'). n_text qualifies a's n (the
    figure states each prompt row whose n departs from the design)."""
    a, b, c = "**a**", "**b**", "**c**"
    n = KEPT["Distiller"]
    below = f"{APART} sits below the grey line because its context is {context_of_apart():,} tokens"
    return (f"**Supplementary Figure 11 | {TITLE[11]}.** Six models compressed the same {n} long outputs, once each "
            f"(draw 1), with Mentor::i's prompt and with a worked-example prompt, which adds two worked examples that "
            f"keep every number ({LEFT_OUT['Distiller']} items built on questions later replaced in the answer key are "
            f"left out). The worked-example prompt is not Mentor::i's prompt in the pipeline. {a}, Share of the "
            f"input's numbers kept, one row per model, Mentor::i's prompt on the left and the worked-example prompt on "
            f"the right; boxes: median and quartiles, whiskers the range, grey dots one item each; n = {n} items per "
            f"model and prompt{n_text}; {below}. {b}, Mean share of the input's numbers kept against mean share of the "
            f"input's source names kept, one mark per model and prompt: black circle, Mentor::i's prompt; orange "
            f"square, worked-example prompt; dashed line, equal shares. {c}, Change in the mean share of the input's "
            f"numbers kept with the worked-example prompt against Mentor::i's prompt, in percentage points, one dot per "
            f"model, its value printed at the right; blue, more kept; {FN.VERMILION}, fewer kept; {below}.")


CAPTION = {
    10: ("Sheet a: one 'model' row per model (n, rho; "
         "gemini-3-flash-preview's on the mean of its three draws), then one 'item' row per model, draw and item (judge "
         "score, supervisor score, errors: 1 where the answer failed or gave no score). Sheet b: one row per "
         "model, draw and component score."),
    11: ("Sheet a: one 'prompt' row per model and prompt (n, quartiles, range), then one 'item' row per model, prompt and "
         "item (numbers kept, %). Sheet b: one row per model and prompt (mean share of source names and of numbers kept, "
         "%). Sheet c: one row per model (change with F1, its sign and its size). Prompt Baseline is the plate's "
         "Mentor::i's prompt, F1 its worked-example prompt."),
}


# ---------------------------------------------------------------------------------------------------------------------
# frame
# ---------------------------------------------------------------------------------------------------------------------
def write_frame(n: int, folder: Path) -> Path:
    planned = N_PLANNED[n]
    tag = ""                                  # Q9 (Valerio, 11 Nov): no "(provisional, ...)" in any name
    stamp = (f"0 of {planned:,} planned T3 answers, a frame: T3 has not run, so no value is drawn or held")
    name = f"Supplementary Figure {n}"
    side = f"supplementary_figure{n}"
    folder.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix="S524_", dir=folder.parent))
    try:
        paths = {x: stage / f"{name}{tag}.{x}" for x in ("pdf", "svg", "png")}
        h, printed = (draw_12 if n == 10 else draw_13)(paths)
        sheets = sheets_12() if n == 10 else sheets_13()
        sd = stage / f"{name} data{tag}.xlsx"
        S457.write_source_data(sheets, sd)
        FR.deterministic_xlsx(sd)
        FR.check_pdf_deterministic(paths["pdf"])
        FR.check_svg_deterministic(paths["svg"])
        numbers = stage / f"{side}_numbers.json"
        numbers.write_text(json.dumps({
            "stamp": stamp, "what": f"the planned rows of {name}, sheet by sheet as its data workbook holds them; every "
                                    f"value cell is empty (a frame)",
            "sheets": {nm: {"columns": cols, "rows": rows} for nm, cols, rows in sheets}, "printed": printed,
            "printed_what": "the digit-bearing texts on the plate that are not tick labels, each declared fixed, and "
                            "the first panel letter (build_order.md F7)"}, indent=1) + "\n")
        legend = stage / "legend_draft.md"
        legend.write_text(f"Legend DRAFT for {name} (a frame; written by {SCRIPT}).\n\n"
                          f"{legend_12() if n == 10 else legend_13()}\n")
        cap = stage / f"{name} data caption{tag}.md"
        cap.write_text(f"# {name} data, caption\n\n**{name} data | The planned rows of {name}.** {CAPTION[n]} Every value "
                       f"cell is empty until T3 has run. Generated by `uv run --frozen python {SCRIPT} frame`.\n\n"
                       f"Data stamp: {stamp}.\n")
        out = {"provenance": {"script": SCRIPT, "script_sha256": sha256_file(Path(__file__)),
                              "command": f"uv run --frozen python {SCRIPT} frame", "python": platform.python_version(),
                              "deterministic": "no build time and no repository HEAD are recorded",
                              "inputs_sha256": {"experiments/LOCK.toml": sha256_file(LOCK)}, "model_calls": 0},
               "stamp": stamp, "figure": name, "page_mm": [W, h],
               "figure_lock": {"path": "experiments/FIGURE_LOCK.toml", "sha256": sha256_file(FIGURE_LOCK)},
               "files": {p.name: sha256_file(p) for p in [*paths.values(), sd, cap, numbers, legend]}}
        (stage / f"{side}_provenance.json").write_text(json.dumps(out, indent=1) + "\n")
        if folder.exists():
            other = [p.name for p in folder.glob("*_provenance.json")
                     if json.loads(p.read_text())["provenance"]["script"] != SCRIPT]
            if other:
                raise Refused(f"{folder} holds {other} of another script")
            shutil.rmtree(folder)
        stage.rename(folder)
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    print(f"wrote {name}{tag} ({W:.0f} x {h:.1f} mm) into {folder}")
    return folder


def frame(args) -> int:
    S457.figure_lock_agreed()
    out = Path(args.out).expanduser().resolve()
    for n in (10, 11):
        write_frame(n, out / FOLDER[n])
    return 0


# ---------------------------------------------------------------------------------------------------------------------
# figure: both plates from T3's frozen set
# ---------------------------------------------------------------------------------------------------------------------
def _join(xs):
    xs = list(xs)
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


def who_is_in(V, n) -> str:
    """Which models the plate holds, from what is stored, as a sentence led by a space; empty when every model holds
    every planned answer (the final legend states only what departs from the design)."""
    full, part, none = [], [], []
    for m in MODELS:
        if n == 10:
            draws = [d for mm, d in S12_DRAWS if mm == m]
            got = sum(V["counts"].get(("exp_04", m, d, c), {}).get("stored", 0) for d in draws for c in COMPONENTS)
            want = len(draws) * sum(KEPT.values())
        else:
            got = sum(V["counts"].get(("exp_04b", m, 1, pr), {}).get("stored", 0) for pr in PROMPTS)
            want = len(PROMPTS) * KEPT["Distiller"]
        (full if got == want else part if got else none).append((m, got, want))
    if not part and not none:
        return ""
    s = []
    if full:
        s.append(f"{_join(m for m, _, _ in full)} with every planned answer")
    if part:
        s.append(_join(f"{m} with {g:,} of its {w:,} answers" for m, g, w in part))
    out = " This version holds " + "; ".join(s) + "."
    if none:
        out += f" {_join(m for m, _, _ in none)} {'has' if len(none) == 1 else 'have'} no answer in the frozen set yet, " \
               f"so {'its row is' if len(none) == 1 else 'their rows are'} empty."
    return out


def failures_text(V, exp, only=None) -> str:
    """Failed calls (left out and counted) and length stops (kept), from the counts, as one sentence or none; with
    only, of those components alone (D294: Supplementary Figure 10 counts the components it draws)."""
    parts, stops = [], []
    for (e, m, d, what), c in sorted(V["counts"].items(), key=lambda kv: (MODELS.index(kv[0][1]), kv[0][2])):
        if e != exp or (only is not None and what not in only):
            continue
        name = what.lower() if exp == "exp_04" else SHOWN[what].replace("Worked", "worked")
        dr = f" in draw {d}" if m == GEMINI_MODEL and exp == "exp_04" else ""
        if c["errors"]:
            why = []
            if c["too_long"]:
                why.append(f"{c['too_long']} with a prompt longer than its context")
            if c["errors"] - c["too_long"]:
                why.append(f"{c['errors'] - c['too_long']} for another reason")
            parts.append(f"{m}, {c['errors']} {name} item{'s' if c['errors'] != 1 else ''}{dr} ({'; '.join(why)})")
        if c["length_stops"]:
            stops.append(f"{c['length_stops']} {m} answer{'s' if c['length_stops'] != 1 else ''} with the {name}{dr}")
    out = ""
    if parts:
        out += f" Failed calls are left out and counted: {'; '.join(parts)}."
    else:
        out += " No call failed."
    if stops:
        out += f" Stopped at the end of the context and kept as scored: {'; '.join(stops)}."
    return out


def legend_12_t3(V) -> str:
    """D294: the busy-machine sentence went with the time per item it qualified; a is the supervisor panel."""
    S = V.get("s12b")
    if S is None:
        return legend_12() + " Panel **a** is empty until the judge scores of the supervisor answers exist." \
            + failures_text(V, "exp_04", only=DRAWN) + who_is_in(V, 12)
    # rulings page 6 Nov, SUPP10C-DEVSTRAL: O1. The judge of a is also one of a's supervisor models; the legend
    # names the pairing. No second-judge (qwen3.8:27b) row of S12b exists, so a keeps the main judge.
    pair = (f" {V['s12b_judge']} is both one of the supervisor models and the judge."
            if V.get("s12b_judge") in S["model"] else "")
    a_text = (f" For {GEN_DISPLAY[GEMINI_MODEL]}, each answer's supervisor score is the mean of its three draws."
              f"{pair}")
    odd = [f"{e['n']} for {m}" for m in MODELS if (e := S["model"].get(m)) and e.get("n", JUDGED) != JUDGED]
    n_text = f"; {_join(odd)}, whose missing answers are counted below" if odd else ""   # audit 9 Nov, X087 (A101)
    miss = [f"{m}, {e['no_score']}" for m, e in S["model"].items() if e["no_score"]]
    c_text = (f" Answers that gave no supervisor score are left out and counted: {'; '.join(miss)}."
              if miss else "")
    # a's left-out answers are counted inside a, b's failed calls inside b (no "counted below" across panels)
    a_fail = failures_text(V, "exp_04", only=["Supervisor"])
    b_fail = failures_text(V, "exp_04", only=[c for c in DRAWN if c != "Supervisor"])
    b_fail = "" if b_fail == " No call failed." else b_fail
    return legend_12(a_text, n_text, c_text + a_fail) + b_fail + who_is_in(V, 12)


def legend_13_t3(V) -> str:
    n = KEPT["Distiller"]
    odd = [f"{e['n']} for {m} with the {SHOWN[pr].lower()}" for m in MODELS for pr in PROMPTS
           if (e := V["13a"].get((m, pr))) and e["n"] != n]
    base = legend_13(f" ({_join(odd)}; failed calls are left out)" if odd else "")
    who = who_is_in(V, 13)
    old = f"Six models compressed the same {n} long outputs"
    if old not in base:
        raise Refused(f"legend_13 lost {old!r}; legend_13_t3 cannot qualify it")
    base = base.replace(old, f"{'The' if who else 'Six'} models compressed the same {n} long outputs")
    return base + failures_text(V, "exp_04b") + who


def write_figure(n: int, folder: Path, V: dict, prov: dict) -> Path:
    """One plate from T3's values: its PDF, SVG, PNG, data workbook, caption, numbers, provenance and legend draft,
    staged and moved into place as write_frame does."""
    planned, k = N_PLANNED[n], V["stored"][n]
    tag = ""                                  # Q9 (Valerio, 11 Nov): no "(provisional, ...)" in any name
    models_in = [m for m in MODELS if any(c["stored"] for (e, mm, _, _), c in V["counts"].items()
                                          if mm == m and e == ("exp_04" if n == 10 else "exp_04b"))]
    stamp = (f"{k:,} of {planned:,} planned T3 answers, from frozen set {prov['frozen_set']} (SHA256SUMS "
             f"{prov['frozen_set_sha256'][:12]}); models in: {', '.join(models_in) or 'none'}"
             + ("; panel a a frame: no S12b copy read" if n == 10 and V.get("s12b") is None else "")
             + (f"; panel a from S12b's {JUDGED} judge rows on key v2.5 (run_sha256 {V['s12b_run'][:12]}, "
                f"{prov['s12b']}/SHA256SUMS {V['s12b_sums'][:12]})" if n == 10 and V.get("s12b") is not None else "")
             + f"; D213: the {sum(LEFT_OUT.values()) if n == 10 else LEFT_OUT['Distiller']} items on D9's six questions "
               f"left out")
    name = f"Supplementary Figure {n}"
    side = f"supplementary_figure{n}"
    folder.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix="S524_", dir=folder.parent))
    try:
        paths = {x: stage / f"{name}{tag}.{x}" for x in ("pdf", "svg", "png")}
        h, printed = (draw_12 if n == 10 else draw_13)(paths, fill=V)
        sheets = sheets_12_t3(V) if n == 10 else sheets_13_t3(V)
        sd = stage / f"{name} data{tag}.xlsx"
        S457.write_source_data(sheets, sd)
        FR.deterministic_xlsx(sd)
        FR.check_pdf_deterministic(paths["pdf"])
        FR.check_svg_deterministic(paths["svg"])
        exp = "exp_04" if n == 10 else "exp_04b"
        counts = [{"model": m, "draw": d, "part": w, **c} for (e, m, d, w), c in V["counts"].items() if e == exp]
        numbers = stage / f"{side}_numbers.json"
        numbers.write_text(json.dumps({
            "stamp": stamp, "what": f"the rows of {name}, sheet by sheet as its data workbook holds them, from T3's "
                                    f"frozen set; a cell is empty where its model has no answer in the set"
                                    + (("; sheet a is empty (no S12b copy read)" if V.get("s12b") is None else
                                        "; sheet a from S12b's judge rows") if n == 10 else ""),
            "sheets": {nm: {"columns": cols, "rows": rows} for nm, cols, rows in sheets}, "printed": printed,
            "printed_what": "the digit-bearing texts on the plate that are not tick labels: fixed ones declared, "
                            "printed values tied to their sheet row and format",
            "counts": counts}, indent=1) + "\n")
        legend = stage / "legend_draft.md"
        legend.write_text(f"Legend DRAFT for {name} (written by {SCRIPT} figure).\n\n"
                          f"{legend_12_t3(V) if n == 10 else legend_13_t3(V)}\n")
        cap = stage / f"{name} data caption{tag}.md"
        cap.write_text(f"# {name} data, caption\n\n**{name} data | The values of {name}.** {CAPTION[n]} A value cell "
                       f"is empty where its model has no answer in the frozen set, or where that answer failed"
                       + (", and every value cell of sheet a is empty until the judge scores of the submitted "
                          "supervisor answers exist" if n == 10 and V.get("s12b") is None else "")
                       + f". Generated by `uv run --frozen python {SCRIPT} {prov['args']}`.\n\n"
                         f"Data stamp: {stamp}.\n")
        out = {"provenance": {"script": SCRIPT, "script_sha256": sha256_file(Path(__file__)),
                              "command": f"uv run --frozen python {SCRIPT} {prov['args']}",
                              "python": platform.python_version(),
                              "deterministic": "no build time and no repository HEAD are recorded",
                              "inputs_sha256": prov["inputs_sha256"], "frozen_set": prov["frozen_set"],
                              "frozen_set_sha256sums": prov["frozen_set_sha256"],
                              "reproduced": prov["reproduced"], "refusals_checked": prov["refusals"],
                              "model_calls": 0},
               "stamp": stamp, "figure": name, "page_mm": [W, h],
               "figure_lock": {"path": "experiments/FIGURE_LOCK.toml", "sha256": sha256_file(FIGURE_LOCK)},
               "files": {p.name: sha256_file(p) for p in [*paths.values(), sd, cap, numbers, legend]}}
        (stage / f"{side}_provenance.json").write_text(json.dumps(out, indent=1) + "\n")
        if folder.exists():
            other = [p.name for p in folder.glob("*_provenance.json")
                     if json.loads(p.read_text())["provenance"]["script"] != SCRIPT]
            if other:
                raise Refused(f"{folder} holds {other} of another script")
            shutil.rmtree(folder)
        stage.rename(folder)
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    print(f"wrote {name}{tag} ({W:.0f} x {h:.1f} mm) into {folder}")
    return folder


REFUSALS = ["S518_split_confirmation exists (D195)",
            "frozen set: every file as SHA256SUMS lists it, none unlisted",
            "frozen items: five files as T3_runs/inputs/MANIFEST.json", "LOCK.toml equivalent to d66daa28 (lock_equiv)",
            "every sink planned; run_identity and every record of its run and model",
            "no answer key twice; every item in the frozen dataset; every draw in the plan",
            "one or more calls per answer, no call without an answer",
            "every call's lock sha256 equivalent; local digests as LOCK.toml [models]; Gemini calls of Gemini",
            "stored analyser, planner and distiller scores recomputed from the item and the stored text",
            "D213: the items on D9's six questions counted as LEFT_OUT and left out (left_out_ids)"]
S12B_REFUSALS = ["S12b copy: every file as SHA256SUMS lists it, none unlisted; COPY.json of T3's supervisor file",
                 "S12b answers: the map's 194 in-key rows once each, every text's sha256 the T3 supervisor item's",
                 "S12b judge rows: once each, run, scope and key v2.5 (key_hash, answerable prompt, S512); run_sha256 the "
                 "summary's (its recheck passed) and the headers'; lock equivalent; judge model and digest LOCK.toml's; status ok; score 0 to 5"]


def rel_or_name(p: Path) -> str:
    try:
        return str(Path(p).resolve().relative_to(ROOT))
    except ValueError:
        return Path(p).name


def build_t3(t3: Path, out: Path, reproduce=True, results=None, s12b: Path | None = None) -> dict:
    """Read, check and write both plates; with s12b, Supplementary Figure 10a from S12b's frozen judge rows (R6). Refusals raise
    Refused before anything is written."""
    import lock_equiv as LE
    t3 = Path(t3).resolve()
    sums = verify_set(t3)
    if not LE.accepts():
        raise Refused("REFUSED, nothing written: experiments/LOCK.toml is not equivalent to d66daa28 (lock_equiv.py)")
    lock = tomllib.loads(LOCK.read_text())
    inputs = load_inputs()
    read = read_t3(t3, inputs, lock, LE.EQUIVALENT)
    V = t3_values(read, inputs)
    J = read_s12b(Path(s12b), inputs, lock, LE.EQUIVALENT) if s12b is not None else None
    if J is not None:
        V["s12b"] = s12b_values(V, J)
        V["s12b_run"], V["s12b_sums"], V["s12b_judge"] = J["run_sha256"], J["sums_sha256"], J["judge"]
    rep = reproduce_published(results) if reproduce else "not run (selftest fixture)"
    try:
        shown = str(t3.relative_to(ROOT))
    except ValueError:
        shown = t3.name
    s12b_shown = rel_or_name(s12b) if s12b is not None else None
    prov = {"frozen_set": shown, "frozen_set_sha256": sums, "reproduced": rep, "refusals": REFUSALS + (S12B_REFUSALS if J else []),
            "s12b": s12b_shown,
            "args": f"figure --t3 {shown}" + (f" --s12b {s12b_shown}" if s12b is not None else " --s12b none")
            + (f" --results {rel_or_name(results)}" if results is not None else ""),
            "inputs_sha256": {"experiments/LOCK.toml": sha256_file(LOCK),
                              "findings/recompute/T3_runs/inputs/MANIFEST.json": sha256_file(INPUTS / "MANIFEST.json"),
                              "findings/recompute/S285_component_bench.csv": sha256_file(S285_CSV),
                              f"{shown}/SHA256SUMS": sums,
                              **({rel_or_name(results): sha256_file(Path(results))}
                                 if results is not None and Path(results).is_file() else {}),
                              **({f"{s12b_shown}/SHA256SUMS": J["sums_sha256"],
                                  rel_or_name(S12B_MAP): sha256_file(S12B_MAP)} if J else {})}}
    for n in (10, 11):
        write_figure(n, out / FOLDER[n], V, prov)
    return V


def figure(args) -> int:
    if not S518_OUT.exists():
        print(f"REFUSED, nothing written: {S518_OUT.relative_to(ROOT)} does not exist (D195; fig4.md Q3)", file=sys.stderr)
        return 2
    if not getattr(args, "t3", None):
        print("REFUSED, nothing written: --t3 <frozen set> is required (copy_t3_frozen.sh writes one)", file=sys.stderr)
        return 2
    S457.figure_lock_agreed()
    try:
        sb = getattr(args, "s12b", None) or str(S12B)
        res = getattr(args, "results", None)
        V = build_t3(Path(args.t3), Path(args.out).expanduser().resolve(), results=Path(res) if res else None,
                     s12b=None if sb == "none" else Path(sb))
    except Refused as e:
        print(str(e), file=sys.stderr)
        return 2
    for n in (10, 11):
        print(f"S{n}: {V['stored'][n]:,} of {N_PLANNED[n]:,} planned answers")
    return 0


# ---------------------------------------------------------------------------------------------------------------------
# selftest
# ---------------------------------------------------------------------------------------------------------------------
def s448(n: int, folder: Path):
    import subprocess
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "S448_figure_rules_check.py"), "--figure", str(n),
                        "--supplementary", "--dir", str(folder)], cwd=ROOT, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


MUTANT_SHEET = {10: "Supplementary Fig. 10a", 11: "Supplementary Fig. 11c"}   # D294: 10's supervisor sheet (c before)
FIX_MODELS = ("gpt-oss:20b", APART)                  # the made-up set: two local models, every planned answer
FIX_NO_SCORE = "0000_04_fastp_FR1"                     # the fixture's gpt-oss:20b supervisor item with no valid score


def _edit_judge_rows(folder: Path, fn):
    p = folder / "out" / "judge" / S12B_RUN / "judge_passages.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in fn([json.loads(x) for x in p.read_text().splitlines()])))


def _edit_copy_answers(folder: Path, fn):
    p = folder / "inputs" / "runs" / S12B_RUN / "answers.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in fn([json.loads(x) for x in p.read_text().splitlines()])))


def _edit_headers(folder: Path, fn):
    p = folder / "out" / "judge" / S12B_RUN / "judge_passages_headers.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in fn([json.loads(x) for x in p.read_text().splitlines()])))


def resum_s12b(folder: Path):
    files = sorted(str(p.relative_to(folder)) for p in folder.rglob("*") if p.is_file() and p.name != "SHA256SUMS")
    (folder / "SHA256SUMS").write_text("".join(f"{sha256_file(folder / f)}  {f}\n" for f in files))


S12B_MUTANTS = {
    # name: an edit of a copy of the frozen S12b folder; each must be refused by build_t3, writing nothing
    "a judge row twice": lambda f: _edit_judge_rows(f, lambda rs: rs + rs[:1]),
    "a judge row missing": lambda f: _edit_judge_rows(f, lambda rs: rs[1:]),
    "a judge row of another run": lambda f: _edit_judge_rows(f, lambda rs: [dict(rs[0], run_sha256="0" * 64), *rs[1:]]),
    "a judge row on key v2.4": lambda f: _edit_judge_rows(f, lambda rs: [dict(rs[0], key_version="v2.4"), *rs[1:]]),
    "a key_hash not key v2.5's": lambda f: _edit_judge_rows(f, lambda rs: [dict(rs[0], key_hash="0" * 16), *rs[1:]]),
    "an answerable prompt flipped": lambda f: _edit_judge_rows(
        f, lambda rs: [dict(rs[0], answerable_prompt=not rs[0]["answerable_prompt"]), *rs[1:]]),
    "a score of 6": lambda f: _edit_judge_rows(
        f, lambda rs: [dict(rs[0], a=dict(rs[0]["a"], scores={**rs[0]["a"]["scores"], "correctness": 6,
                                                              "refusal_accuracy": 6})), *rs[1:]]),
    "a call not ok": lambda f: _edit_judge_rows(f, lambda rs: [dict(rs[0], a=dict(rs[0]["a"], status="error")), *rs[1:]]),
    "an answer text that is not T3's item": lambda f: _edit_copy_answers(
        f, lambda rs: [dict(rs[0], generation=dict(rs[0]["generation"], answer=rs[0]["generation"]["answer"] + " ")),
                       *rs[1:]]),
    "a header of another judge digest": lambda f: _edit_headers(f, lambda hs_: [dict(hs_[0], model_digest="0" * 64),
                                                                               *hs_[1:]]),
}


def resum(t3: Path):
    """SHA256SUMS and MANIFEST.json of a made-up set, as copy_t3_frozen.sh writes them."""
    files = sorted(str(p.relative_to(t3)) for p in t3.rglob("*") if p.is_file()
                   and p.name not in ("SHA256SUMS", "MANIFEST.json"))
    (t3 / "SHA256SUMS").write_text("".join(f"{sha256_file(t3 / f)}  {f}\n" for f in files))
    (t3 / "MANIFEST.json").write_text(json.dumps({"what": "made-up T3 set (S524 selftest)"}) + "\n")


def make_fixture(t3: Path, inputs: dict, judge: dict | None = None) -> dict:
    """Made-up sinks for FIX_MODELS under the design's names, every planned answer, scores consistent with exp_04's
    rules; llama3:8b's F1 prompt: item 0 refused as longer than the context, item 1 stopped at the context's end.
    Supervisor (with judge, {item_id: judge score}): gpt-oss:20b scores 20 x the judge score (rho 1) except one judged
    item with no valid score; llama3:8b 100 - 20 x the judge score (rho -1). Returns the expected counts (D213's
    items left out)."""
    lock = tomllib.loads(LOCK.read_text())
    lsha = sha256_file(LOCK)
    plan = planned_sinks()
    for rid, (exp, what, m, draws) in plan.items():
        if m not in FIX_MODELS:
            continue
        d = t3 / "sinks" / rid
        d.mkdir(parents=True)
        (d / "run_identity.json").write_text(json.dumps({"run_id": rid}) + "\n")
        bench = "distiller" if exp == "exp_04b" else BENCH[what]
        cm = lock["date"]["model_copy"].get(m, m)
        ans, calls = [], []
        for i, it in enumerate(inputs[bench]):
            iid, u = item_id_for(it, i), f"{rid}-{i}"
            r = {"answer_key": f"{model_key(m)}|{iid}|d1", "item_id": iid, "draw": 1, "run_id": rid,
                 "model_id": f"ollama::{m}", "ctx_uid": u, "error": None, "latency_s": 1.0 + i % 5}
            if bench == "analyzer":
                r["decision"] = it["expected_decision"] if i % 3 else "neither"
                r["decision_correct"] = r["decision"] == it["expected_decision"]
            elif bench == "planner":
                r["json_valid"], r["actual_tools"] = True, (it["expected_tools"][:1] if i % 2 else ["none"])
                r["tool_correct"] = any(t in r["actual_tools"] for t in it["expected_tools"])
            elif bench == "supervisor" and judge is not None:
                js = judge.get(iid, 0)
                r["score_valid"], r["quality_score"] = True, 20 * js if m != APART else 100 - 20 * js
                if m != APART and iid == FIX_NO_SCORE:
                    r["score_valid"], r["quality_score"] = None, None
            elif bench == "distiller":
                nums = list(it.get("numbers", []))
                r["distilled"] = " ".join(nums[: len(nums) // 2] + list(it.get("sources", []))[:1])
                r["number_retention"], r["source_retention"] = retention(it, r["distilled"])
            stop = "stop"
            if m == APART and what == "F1" and i == 0:
                r.update(error=f"{m}: status error: HTTP 400: request (9000 tokens) {TOO_LONG} (8192 tokens)",
                         number_retention=0, source_retention=0, distilled="")
            if m == APART and what == "F1" and i == 1:
                stop = "length"
            ans.append(r)
            calls.append({"ctx_uid": u, "model": cm, "model_digest": lock["models"][cm]["digest"], "lock_sha256": lsha,
                          "status": "ok" if stop == "stop" else "length", "stop_reason": stop,
                          "busy_servers_on_machine": 0})
        (d / "answers.jsonl").write_text("".join(json.dumps(r) + "\n" for r in ans))
        (d / "calls.jsonl").write_text("".join(json.dumps(c) + "\n" for c in calls))
    resum(t3)
    return {10: len(FIX_MODELS) * sum(KEPT.values()), 11: len(FIX_MODELS) * len(PROMPTS) * KEPT["Distiller"]}


def _edit_jsonl(p: Path, fn):
    rows = [json.loads(x) for x in p.read_text().splitlines()]
    rows = fn(rows)
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))


READER_MUTANTS = {
    # name: (sink, file, edit of the rows) or a callable on the set; each must be refused by build_t3
    "an answer key stored twice": ("exp_04__planner__gpt-oss-20b", "answers.jsonl", lambda rs: rs + rs[:1]),
    "an item outside the frozen dataset": ("exp_04__analyzer__gpt-oss-20b", "answers.jsonl",
                                           lambda rs: [dict(rs[0], item_id="9999_X", answer_key="gpt-oss-20b|9999_X|d1"),
                                                       *rs[1:]]),
    "a draw outside the plan": ("exp_04__analyzer__llama3-8b", "answers.jsonl",
                                lambda rs: [dict(rs[0], draw=2, answer_key=rs[0]["answer_key"][:-1] + "2"), *rs[1:]]),
    "a stored score the text does not give": ("exp_04b__baseline__gpt-oss-20b", "answers.jsonl",
                                              lambda rs: [dict(rs[3], number_retention=rs[3]["number_retention"] + 0.1)
                                                          if k == 3 else r for k, r in enumerate(rs)]),
    "an analyser decision_correct flipped": ("exp_04__analyzer__llama3-8b", "answers.jsonl",
                                             lambda rs: [dict(rs[1], decision_correct=not rs[1]["decision_correct"]),
                                                         *rs[2:], rs[0]]),
    "a local digest not as LOCK.toml": ("exp_04__supervisor__llama3-8b", "calls.jsonl",
                                        lambda rs: [dict(rs[0], model_digest="0" * 64), *rs[1:]]),
    "a lock not equivalent": ("exp_04__synthesizer__gpt-oss-20b", "calls.jsonl",
                              lambda rs: [dict(rs[0], lock_sha256="f" * 64), *rs[1:]]),
    "an answer with no call": ("exp_04__distiller__gpt-oss-20b", "calls.jsonl", lambda rs: rs[1:]),
    "a record of another model": ("exp_04b__F1__gpt-oss-20b", "answers.jsonl",
                                  lambda rs: [dict(rs[0], model_id="ollama::gemma3:27b"), *rs[1:]]),
}


def selftest() -> bool:
    res = []

    def check(name, ok, detail=""):
        res.append(bool(ok))
        print(f"{'PASS' if ok else 'FAIL'} {name}{': ' + str(detail)[:400] if detail and not ok else ''}")

    s12, s13 = {x[0]: x for x in sheets_12()}, {x[0]: x for x in sheets_13()}
    n12 = [len(x[2]) for x in s12.values()]
    # D294: two sheets, the supervisor's (c before) and the component scores' (d before); a and b went with their panels
    check("S12's sheets: 6 + 8 x 194, 24 rows (D294: a and b dropped)", n12 == [6 + 8 * JUDGED, 24], n12)
    check("S12's sheets named a and b (D294)", list(s12) == ["Supplementary Fig. 10a", "Supplementary Fig. 10b"], list(s12))
    n13 = [len(x[2]) for x in s13.values()]
    check("S13's sheets: 12 + 1,128, 12, 6 rows (D213: 94 distiller items)", n13 == [12 + 1128, 12, 6], n13)
    check("planned answers: 6,512 and 1,128 (D213: 814 of 832 items)", N_PLANNED == {10: 6512, 11: 1128}, N_PLANNED)
    check("every row as long as its header",
          all(len(r) == len(c) for _, c, rows in [*s12.values(), *s13.values()] for r in rows))
    blank = all(r[c.index(v)] is None for nm, c, rows in [*s12.values(), *s13.values()] for r in rows
                for v in VALUE_COLUMNS[nm])
    check("every value cell is blank", blank)
    check("the legends: under 350 words, 'n =' present, one word for the 39",
          all(len(x.split()) < 350 and "n = " in x for x in (legend_12(), legend_13()))
          and "not-answerable" not in legend_12())
    with tempfile.TemporaryDirectory(prefix="S524_selftest_") as td:
        t = Path(td)
        for n in (10, 11):
            a = write_frame(n, t / "one" / FOLDER[n])
            b = write_frame(n, t / "two" / FOLDER[n])
            fa = {p.name: sha256_file(p) for p in a.iterdir()}
            check(f"S{n}: two builds byte for byte", fa == {p.name: sha256_file(p) for p in b.iterdir()})
            rc, log = s448(n, a)
            check(f"S{n}: S448 passes on the frame", rc == 0, log[-500:])
            from openpyxl import load_workbook
            xs = next(a.glob("*.xlsx"))
            wb = load_workbook(xs)
            ws = wb[MUTANT_SHEET[n]]
            ws.cell(row=2, column=ws.max_column, value=5)
            wb.save(xs)
            rc, log = s448(n, a)
            check(f"S{n}: mutant, a value edited into the workbook fails R8",
                  rc == 1 and any("R8" in ln and "FAIL" in ln for ln in log.splitlines()), log[-500:])
    # the reader (R5) and the figure on made-up sinks
    inputs = load_inputs()
    import lock_equiv as LE
    lock0 = tomllib.loads(LOCK.read_text())
    J0 = read_s12b(S12B, inputs, lock0, LE.EQUIVALENT)
    check("the frozen S12b copy reads: 194 judge scores, one per in-key supervisor item",
          len(J0["score"]) == JUDGED and set(J0["score"]) == set(J0["order"]))
    drop = left_out_ids(inputs)
    with tempfile.TemporaryDirectory(prefix="S524_t3fix_") as td:
        t = Path(td)
        want = make_fixture(t / "set", inputs, J0["score"])
        V = build_t3(t / "set", t / "one", reproduce=False, s12b=S12B)
        check("fixture: stored answers counted per plate, D213's 18 items left out", V["stored"] == want
              and V["dropped"].get(("exp_04", "Analyser")) == len(FIX_MODELS) * LEFT_OUT["Analyser"], (V["stored"], want))
        c12 = V["s12b"]["model"]
        check("fixture c: rho 1 for gpt-oss:20b on 193 items (one gave no score, counted), -1 for llama3:8b on 194",
              c12["gpt-oss:20b"]["rho"] == 1.0 and c12["gpt-oss:20b"]["n"] == JUDGED - 1
              and c12["gpt-oss:20b"]["no_score"] == 1 and c12[APART]["rho"] == -1.0 and c12[APART]["n"] == JUDGED,
              {m: (e["rho"], e["n"], e["no_score"]) for m, e in c12.items()})
        check("fixture c: a model with no supervisor answer has no rho and blank rows",
              "gemma3:27b" not in c12 and all(x[3] is None for x in V["s12b"]["rows"][("gemma3:27b", 1)]))
        kept_a = [i for i, it in enumerate(inputs["analyzer"]) if item_id_for(it, i) not in drop["analyzer"]]
        exp_a = round(100 * sum(1 for i in kept_a if i % 3) / KEPT["Analyser"], 4)
        check("fixture: analyser score = decisions matching / items, in %",
              V["12c"].get(("gpt-oss:20b", 1, "Analyser")) == exp_a, (V["12c"].get(("gpt-oss:20b", 1, "Analyser")), exp_a))
        f1 = V["counts"][("exp_04b", APART, 1, "F1")]
        check("fixture: the refused prompt is left out and counted, the length stop counted and kept",
              f1 == {"stored": 94, "errors": 1, "too_long": 1, "length_stops": 1} and V["13a"][(APART, "F1")]["n"] == 93,
              f1)
        check("fixture: a length stop counts in its own sink only (keys repeat across a model's sinks)",
              V["counts"][("exp_04b", APART, 1, "Baseline")]["length_stops"] == 0
              and V["counts"][("exp_04", APART, 1, "Distiller")]["length_stops"] == 0
              and sum(c["length_stops"] for c in V["counts"].values()) == 1)
        check("fixture: absent models keep blank rows",
              not any(m not in FIX_MODELS for m, *_ in V["12a"]) and "gemma3:27b" not in V["13c"])
        leg12, leg13 = legend_12_t3(V), legend_13_t3(V)
        check("fixture: legends name the failure, the length stop and the absent models; no busy sentence when none was busy",
              "1 with a prompt longer than its context" in leg13 and "Stopped at the end of the context" in leg13
              and "GPU" not in leg12 and "model server" not in leg12 and "have no answer" in leg12, leg13)
        check("fixture: legend 12 fills a (no 'empty'), counts the answer with no score and names the 15 left out of the "
          "four components drawn (D294)",
              "is empty until" not in leg12 and "gpt-oss:20b, 1." in leg12 and "the 15 items built on questions" in leg12
              and "synthesizer" not in leg12 and "step" not in leg12
              and (("devstral-small-2:24b is both one of the supervisor models and the judge." in leg12)
                   == ("devstral-small-2:24b" in V["s12b"]["model"]))
              and "(3 items built on questions" in leg13, leg12[-600:])
        check("fixture: legend 12 names devstral as supervisor and judge only when c draws its row (SUPP10C-DEVSTRAL)",
              "is both one of the supervisor models and the judge" in legend_12_t3(
                  {**V, "s12b": {**V["s12b"], "model": {**V["s12b"]["model"], "devstral-small-2:24b": {"no_score": 0}}}})
              and "is both one of the supervisor models" not in legend_12_t3({**V, "s12b_judge": "x"}))
        V2 = build_t3(t / "set", t / "two", reproduce=False, s12b=S12B)
        for n in (10, 11):
            a, b = t / "one" / FOLDER[n], t / "two" / FOLDER[n]
            check(f"fixture S{n}: two builds byte for byte",
                  {p.name: sha256_file(p) for p in a.iterdir()} == {p.name: sha256_file(p) for p in b.iterdir()})
            rc, log = s448(n, a)
            check(f"fixture S{n}: S448 passes on the provisional plate", rc == 0, log[-500:])
            from openpyxl import load_workbook
            xs = next(b.glob("*.xlsx"))
            wb = load_workbook(xs)
            ws = wb[MUTANT_SHEET[n]]
            ws.cell(row=2, column=ws.max_column, value=12345)
            wb.save(xs)
            rc, log = s448(n, b)
            check(f"fixture S{n}: mutant, a value edited into the workbook fails R8",
                  rc == 1 and any("R8" in ln and "FAIL" in ln for ln in log.splitlines()), log[-500:])
        del V2
        for name, (sink, fname, fn) in READER_MUTANTS.items():
            mt = t / f"mut_{len(res)}"
            shutil.copytree(t / "set", mt)
            _edit_jsonl(mt / "sinks" / sink / fname, fn)
            resum(mt)
            try:
                build_t3(mt, t / "never", reproduce=False)
                ok = False
            except Refused:
                ok = not (t / "never").exists()
            check(f"reader refuses, writing nothing: {name}", ok)
        for name, act in {"a sink the design does not plan": lambda s: shutil.copytree(
                              s / "sinks" / "exp_04__planner__llama3-8b", s / "sinks" / "exp_04__router__llama3-8b"),
                          "a file changed after SHA256SUMS": None}.items():
            mt = t / f"mut_{len(res)}"
            shutil.copytree(t / "set", mt)
            if act:
                act(mt)
                resum(mt)
            else:
                p = mt / "sinks" / "exp_04__analyzer__gpt-oss-20b" / "answers.jsonl"
                p.write_text(p.read_text().replace('"latency_s": 1.0', '"latency_s": 1.5', 1))
            try:
                build_t3(mt, t / "never", reproduce=False)
                ok = False
            except Refused:
                ok = not (t / "never").exists()
            check(f"reader refuses, writing nothing: {name}", ok)
        for name, act in S12B_MUTANTS.items():
            mt = t / f"s12b_mut_{len(res)}"
            shutil.copytree(S12B, mt)
            act(mt)
            resum_s12b(mt)
            try:
                build_t3(t / "set", t / "never", reproduce=False, s12b=mt)
                ok = False
            except Refused:
                ok = not (t / "never").exists()
            check(f"S12b reader refuses, writing nothing: {name}", ok)
        mt = t / "s12b_unlisted"
        shutil.copytree(S12B, mt)
        (mt / "extra.txt").write_text("x\n")
        try:
            build_t3(t / "set", t / "never", reproduce=False, s12b=mt)
            ok = False
        except Refused:
            ok = not (t / "never").exists()
        check("S12b reader refuses, writing nothing: a file SHA256SUMS does not list", ok)
    k = sum(res)
    print(f"selftest: {k} of {len(res)} checks pass")
    return k == len(res)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("frame")
    f.add_argument("--out", default=str(OUT), help="the folder that holds both plate folders")
    g = sub.add_parser("figure")
    g.add_argument("--t3", help="a frozen set written by findings/recompute/T3_runs/copy_t3_frozen.sh")
    g.add_argument("--s12b", default=str(S12B), help="S12b's frozen copy (R6; default findings/recompute/s12b_inputs); "
                                                       "'none' leaves Supplementary Figure 10a a frame")
    g.add_argument("--out", default=str(OUT), help="the folder that holds both plate folders")
    g.add_argument("--results", help="the deposit's exp07 files for the reproduction: a folder, or the committed tar "
                                     "findings/recompute/exp07_bench_20261107/exp07_bench_20261107.tar (D287 O3); "
                                     "default scripts/machine.py RESULTS")
    sub.add_parser("selftest")
    args = ap.parse_args(argv)
    if args.cmd == "frame":
        return frame(args)
    if args.cmd == "figure":
        return figure(args)
    return 0 if selftest() else 1


if __name__ == "__main__":
    sys.exit(main())
