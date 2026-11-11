#!/usr/bin/env python3
"""S590 - Supplementary Figure 9: Mentor::i's question-answering pipeline, drawn from the code (D257).

S590, not S586: S586 is scripts/S586_false_premise_classes.py, written beside this one on 5 November.

WHY. D257 (Valerio, 5 November 2026, "Q6: go ahead", then "Q1: O1"): the manuscript tab cites Supplementary Figure 9 as
Mentor::i's question-answering pipeline, so the schematic drawn from the code on 4 November
(findings/recompute/pipeline_schematic/, commit 7c3ee10d, the draft for the first author) becomes a plate under the
figure lock's names. Every box, arrow and label cites the code it draws in ELEMENTS below (the table of that draft's
pipeline_schematic.md, moved here); its draft legend is the legend, with the system's printed name
(figure_names.MENTORI). No data and no model call: the plate draws the code at experiments/mentori/.

ONE COMMAND (D155), from the repository root:

    uv run --frozen python scripts/S590_supp_fig9_pipeline.py [--out DIR]
    uv run --frozen python scripts/S448_figure_rules_check.py --figure 9 --supplementary \
        --dir findings/figures_provisional/supp_fig9_pipeline
    uv run --frozen python scripts/S590_supp_fig9_pipeline_test.py

writes into findings/figures_provisional/supp_fig9_pipeline/ (or --out; earlier "Supplementary Figure 9*" files deleted
first): Supplementary Figure 9.{pdf,svg,png} (183 x 100 mm, every text at [type] font_min_pt in [type] font_families[0],
lines at 0.8 pt; S457.finish_plate refuses a text off the page or on another and writes the PNG as MuPDF's rendering of
the PDF at 600 dpi, S448 R7), "Supplementary Figure 9 data.xlsx" (sheets "Supp. Fig. 9 lines", one row per printed
line; "Supp. Fig. 9 elements", each box, arrow and label with what the code does and where; "Supp. Fig. 9 set-ups",
each set-up of the orchestration ablation and the label that draws it), its caption, legend_draft.md,
supplementary_figure9_numbers.json (every sheet, and every printed line tied to its sheet row, S448 R8 (6)) and
supplementary_figure9_provenance.json (each input's sha256, the figure lock's, every output's). No file carries a
suffix (Q9, 11 Nov); its stamp says what it is drawn from.

INPUTS, both committed: experiments/mentori/publication/scripts/exp_03_orchestration_ablation.py (its
ORCHESTRATOR_CONFIGS and MAX_STEPS, read with ast, nothing imported) and experiments/FIGURE_LOCK.toml.
REPRODUCE FIRST (README.md:75-79): nothing is written unless exp_03's ORCHESTRATOR_CONFIGS, the full pipeline left
out, are exactly the set-ups the dashed labels draw (SETUPS), and its MAX_STEPS is the "at most 10" the plate prints.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import platform
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import fig_repro as FR  # noqa: E402
import figure_names as fn  # noqa: E402

SCRIPT = "scripts/S590_supp_fig9_pipeline.py"
N = 9
OUT = ROOT / "findings" / "figures_provisional" / "supp_fig9_pipeline"
FIGURE_LOCK = ROOT / "experiments" / "FIGURE_LOCK.toml"
EXP03 = ROOT / "experiments" / "mentori" / "publication" / "scripts" / "exp_03_orchestration_ablation.py"
FLOCK = tomllib.loads(FIGURE_LOCK.read_text())
SI_LABEL = FLOCK["files"]["supplementary_name"].format(n=N)    # "Supplementary Figure 9" (D92 Q194)
SIDE = f"supplementary_figure{N}"
SHEETS = {"lines": f"Supp. Fig. {N} lines", "elements": f"Supp. Fig. {N} elements", "setups": f"Supp. Fig. {N} set-ups"}
TITLE = f"{fn.MENTORI}'s question-answering pipeline"
PT = float(FLOCK["type"]["font_min_pt"])
FONT = FLOCK["type"]["font_families"][0]
W_MM, H_MM = float(FLOCK["page"]["width_double_mm"]), 100.0
LW = 0.8                                            # above [lines] line_min_pt
PAL = FLOCK["colour"]["categorical"]                # Okabe and Ito's eight
BLACK, BLUE, VERMILION = PAL[0], PAL[5], PAL[6]
GREY = "#595959"                                    # a grey (R5), 7.0:1 on white (R11)
LH = PT * 25.4 / 72 * 1.22                          # line pitch, mm
DASH = (0, (3, 1.5))
MAX_STEPS_PRINTED = 10                              # "at most 10" on the plate

# The set-ups of the orchestration ablation (exp_03 ORCHESTRATOR_CONFIGS, the full pipeline left out) and the dashed
# label that draws each; reproduce() holds the keys to exp_03. None: in exp_03 but not one of Figure 5's 11 set-ups
# (findings/figures_provisional/fig4/figure5_numbers.json holds neither), so not drawn (D292)
SETUPS = {"orch_no_analyser": "no analyser", "orch_factual_to_documents": "routing fix",
          "orch_no_planner": "no planner", "orch_no_synthesiser": "no synthesizer",
          "orch_no_distiller": None,
          "orch_distiller_f1": None,
          "orch_distil_every_step": "every step distilled, with either prompt",
          "orch_distil_every_step_f1": "every step distilled, with either prompt",
          "orch_no_supervisor": "no supervisor"}
DRAWN = {k: v for k, v in SETUPS.items() if v}

# What each box, arrow and label draws, and where in the code (paths under experiments/mentori/ unless they start with
# publication/; exp_03 is publication/scripts/exp_03_orchestration_ablation.py). From pipeline_schematic.md, 4 Nov.
ELEMENTS = [
    ('Question -> Analyser',
     'One model call returns `decision` "direct_answer" or "needs_plan" (with reasoning, complexity)',
     'prompts.py:46-52; schemas.py:229-238; engine.py:433-452'),
    ('Analyser -> Direct answer',
     '`decision == "direct_answer"`: one call, `tools=None`',
     'engine.py:483-545; synthesizer.py:165-222 (tools=None at :220)'),
    ('Direct answer -> Answer',
     'the streamed text is the answer',
     'engine.py:520-531'),
    ('Analyser -> Planner ("needs_plan")',
     'one model call writes goal, reasoning and steps, each with one `tool_name` and its args',
     'engine.py:550-567; prompts.py:168-182'),
    ('"at most 10 steps"',
     'the engine cuts a longer plan to `max_steps` (10)',
     'engine.py:235, 619-621; publication/scripts/exp_03_orchestration_ablation.py:163'),
    ('Each step in plan order',
     '`while not plan.is_complete()`, `plan.current_step()`, `plan.advance()`',
     'engine.py:681-689, 1130'),
    ('Tool call, one per step',
     'one `mcp_session.call_tool` per attempt',
     'executor.py:371-374; engine.py:854-861'),
    ('Tool call: smart query router, no model call',
     'keyword rules in order: metadata words -> `inspect_document_index`; triage -> `paper_triage`; corpus analysis -> `analyze_corpus`; cross-document -> `cross_document_analysis`; verify words -> RLM with `verify`; complex or deep words -> RLM; index > 500 passages -> RLM; else `query_documents`, 5 passages',
     'context_engine.py:1-14, 157-225; rag_tools.py:1105-1193'),
    ('Tool -> Distiller',
     'only when the output is longer than 0.40 x num_ctx 131,072 x 4 = 209,712 characters (`should_distill`)',
     'executor.py:410-437; observation_distiller.py:42-54, 267-269'),
    ('"asked for at most 600 words"',
     'the prompt asks for at most 600 words; no output cap is set',
     'observation_distiller.py:46-47, 67'),
    ('Distiller -> Supervisor',
     'text pre-check (empty or failed result, no model call), else one call scoring relevance, completeness, accuracy, progress, 0 to 100',
     'supervisor.py:156-186, 263-285, 367-372'),
    ('">= 70: next step"',
     '`is_good_quality()` at 70 resets the failure count; the plan advances',
     'schemas.py:526-532; engine.py:1126-1130'),
    ('Retry loop ("retry"; < 70, < 3 retries)',
     'one micro-adjustment call rewrites `tool_args`, `retry_count += 1`, the same step reruns; no replanning',
     'supervisor.py:383-385, 410; engine.py:1030-1072; schemas.py:21'),
    ('"< 70 after 3 retries: an escalation"; "3 escalations in a row end the steps"',
     '`should_escalate` -> `consecutive_failures += 1`; at `max_failures` (3) the plan is marked failed and the loop breaks; synthesis still runs',
     'supervisor.py:386-388; engine.py:1074-1123; schemas.py:17-22, 445'),
    ('Execution -> Synthesizer',
     "one call reads question, goal and `format_steps_with_results` (each step's last attempt)",
     'synthesizer.py:73-88; engine.py:1164-1180'),
    ('Synthesizer -> Answer',
     'the synthesis text; thinking used only when content is empty and no error',
     'engine.py:1182-1197'),
    ('no analyser',
     '`{"analyser": "off"}`: no call, every question to the planner',
     'exp_03:151; engine.py:433-436'),
    ('routing fix',
     '`{"analyser": "factual_to_documents"}`: the analyser prompt\'s direct-answer list keeps only greetings, meta questions and the like, so factual questions are planned',
     'exp_03:155; prompts.py:85-114; engine.py:447'),
    ('no planner',
     '`{"planner": "off"}`: one fixed step, `smart_query` (the smart query router) with the question, mode auto',
     'exp_03:152; engine.py:188-209, 555-556'),
    ('every step distilled, with either prompt',
     '`{"distiller_trigger": "every_step"}`, alone or with `{"distiller": "F1"}` (the worked-example prompt, exp_04b\'s F1; D290)',
     'exp_03:149-150, 156-157; executor.py:412-430'),
    ('no supervisor',
     '`{"supervisor": "off"}`: each step once, no evaluation, no retry',
     'exp_03:153; engine.py:946-962'),
    ('no synthesizer',
     '`{"synthesiser": "off"}`: the answer is the steps\' text as synthesis would read it',
     'exp_03:154; engine.py:1151-1162'),
]


class Refused(Exception):
    pass


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rel(p: Path) -> str:
    try:
        return str(Path(p).resolve().relative_to(ROOT))
    except ValueError:
        return str(p)


# ---------------------------------------------------------------------------------------------------------------
# Reproduce first: the set-ups and the step cap the plate draws are exp_03's
# ---------------------------------------------------------------------------------------------------------------
def exp03_facts(src: str) -> dict:
    """ORCHESTRATOR_CONFIGS' keys and MAX_STEPS, read from exp_03's source with ast (nothing imported)."""
    facts = {}
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name == "ORCHESTRATOR_CONFIGS" and isinstance(node.value, ast.Dict):
                facts["configs"] = [ast.literal_eval(k) for k in node.value.keys]
            elif name == "MAX_STEPS":
                facts["max_steps"] = ast.literal_eval(node.value)
    return facts


def reproduce(src: str) -> list:
    f = exp03_facts(src)
    if "configs" not in f or "max_steps" not in f:
        raise Refused(f"{rel(EXP03)}: ORCHESTRATOR_CONFIGS or MAX_STEPS not found")
    ablated = [k for k in f["configs"] if k != "full_orchestrator"]
    if "full_orchestrator" not in f["configs"] or sorted(ablated) != sorted(SETUPS):
        raise Refused(f"exp_03's set-ups {sorted(ablated)} are not the ones the plate draws {sorted(SETUPS)}")
    if f["max_steps"] != MAX_STEPS_PRINTED:
        raise Refused(f"exp_03 MAX_STEPS {f['max_steps']}, the plate prints at most {MAX_STEPS_PRINTED}")
    return [f"exp_03 ORCHESTRATOR_CONFIGS: full_orchestrator and {len(ablated)} set-ups = the {len(SETUPS)} the "
            f"dashed labels draw", f"exp_03 MAX_STEPS {f['max_steps']} = the plate's 'at most {MAX_STEPS_PRINTED}'"]


# ---------------------------------------------------------------------------------------------------------------
# Drawing: the 4 November schematic, every text one line, each tied to a row of the lines sheet
# ---------------------------------------------------------------------------------------------------------------
def draw(files: dict) -> tuple[list, dict]:
    import logging
    logging.getLogger("fontTools").setLevel(logging.ERROR)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
    import house_style as hs
    import S457_fig2_panels as S457
    plt.rcParams.update({"font.family": FONT, "font.size": PT, "svg.fonttype": "none", "pdf.fonttype": 42,
                         "lines.linewidth": LW, "patch.linewidth": LW, "text.color": BLACK,
                         **FR.matplotlib_rc("S590")})
    fig = plt.figure(figsize=(W_MM / 25.4, H_MM / 25.4), facecolor="#FFFFFF")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W_MM)
    ax.set_ylim(0, H_MM)
    ax.set_aspect("equal")
    ax.axis("off")
    rows, printed = [], {}

    def T(x, y, s, element, kind, ha="center", bold=False, color=BLACK, rot=0, bbox=None):
        a = ax.text(x, y, s, ha=ha, va="center", fontweight="bold" if bold else "normal", color=color, zorder=3,
                    rotation=rot, bbox=bbox)
        gid = f"s448num_{len(rows)}"
        a.set_gid(gid)
        printed[gid] = {"sheet": SHEETS["lines"], "row": len(rows), "format": "{text}"}
        rows.append([element, kind, sum(1 for r in rows if r[0] == element) + 1, s])

    def stack(cx, cy, lines, element, kind, ha="center", first_bold=True, color=BLACK):
        top = cy + (len(lines) - 1) * LH / 2
        for i, (ind, ln) in enumerate(lines):
            T(cx + ind, top - i * LH, ln, element, kind, ha=ha, bold=first_bold and i == 0, color=color)

    def box(x0, y0, x1, y1, lines, element, edge=BLACK, ls="-", color=BLACK, align="center"):
        ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle="round,pad=0,rounding_size=1.2",
                                    fc="white", ec=edge, lw=LW, ls=ls, zorder=2))
        lines = [(0.0, ln) if isinstance(ln, str) else ln for ln in lines]
        cx = (x0 + x1) / 2 if align == "center" else x0 + 1.6
        stack(cx, (y0 + y1) / 2, lines, element, "box", ha="center" if align == "center" else "left", color=color)

    def tag(x0, y0, x1, y1, lines, element):
        ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle="round,pad=0,rounding_size=0.8",
                                    fc="white", ec=VERMILION, lw=LW, ls=DASH, zorder=2))
        stack((x0 + x1) / 2, (y0 + y1) / 2, [(0.0, ln) for ln in lines], element, "ablation set-up",
              first_bold=False)

    def arrow(points, color=BLACK, ls="-"):
        for (xa, ya), (xb, yb) in zip(points[:-2], points[1:-1]):
            ax.plot([xa, xb], [ya, yb], color=color, lw=LW, ls=ls, solid_capstyle="butt", zorder=1)
        ax.add_patch(FancyArrowPatch(points[-2], points[-1], arrowstyle="-|>", mutation_scale=7, color=color, lw=LW,
                                     ls=ls, shrinkA=0, shrinkB=0, zorder=1))

    white = dict(fc="white", ec="none", pad=0.6)
    # D292: one plain line per box, no thresholds or rule lists (Methods and the legend give them), no code names,
    # no memory consolidation, every ablation set-up beside or under the box it changes with no connecting line
    Y = 57.0
    T(0.8, Y + 2.6, "Question", "Question -> Analyser", "label", ha="left")
    arrow([(0.8, Y), (13.0, Y)])
    box(13, 49, 39, 65, ["Analyser", "answer directly", "or plan"], "Question -> Analyser", edge=BLUE)
    arrow([(39, Y), (43, Y)])
    box(43, 49, 69, 65, ["Planner", "writes the steps,", "one tool each"], 'Analyser -> Planner ("needs_plan")',
        edge=BLUE)
    arrow([(69, Y), (74, Y)])
    # the direct path, over the top
    box(13, 76, 39, 88, ["Direct answer", "one model call,", "no tools"], "Analyser -> Direct answer", edge=BLUE)
    arrow([(26, 65), (26, 76)])
    arrow([(26, 88), (26, 94), (169, 94), (169, 88)])
    # the execution frame
    ax.add_patch(FancyBboxPatch((74, 4), 78, 72, boxstyle="round,pad=0,rounding_size=1.5", fc="none", ec=GREY,
                                lw=LW, ls=(0, (4, 2)), zorder=0))
    T(113, 72.2, f"at most {MAX_STEPS_PRINTED} steps", '"at most 10 steps"', "label")
    box(84, 48, 120, 66, ["Tool call", "smart query router picks", "the retrieval strategy", "(no model call)"],
        "Tool call: smart query router, no model call")
    arrow([(102, 48), (102, 43)])
    box(84, 30, 120, 43, ["Distiller", "condenses a very long", "step output"], "Tool -> Distiller", edge=BLUE)
    arrow([(102, 30), (102, 25)])
    box(84, 8, 120, 25, ["Supervisor", "scores each step;", "below 70, reruns it", "(up to 3 times)"],
        "Distiller -> Supervisor", edge=BLUE)
    # the retry loop on the left
    arrow([(84, 16.5), (79, 16.5), (79, 53), (84, 53)])
    T(79, 35, "retry", 'Retry loop ("retry"; < 70, < 3 retries)', "label", rot=90, bbox=white)
    # the exit to synthesis
    arrow([(152, Y), (156, Y)])
    box(156, 49, 182, 65, ["Synthesizer", "writes the answer", "from the steps"], "Execution -> Synthesizer", edge=BLUE)
    arrow([(169, 65), (169, 76)])
    box(156, 76, 182, 88, ["Answer"], "Synthesizer -> Answer")
    # the set-ups of the orchestration ablation (exp_03 ORCHESTRATOR_CONFIGS), each under or beside its box
    tag(13, 34.5, 39, 46, ["no analyser:", "every question", "planned"], "no analyser")
    tag(13, 21.5, 39, 33, ["routing fix:", "factual", "questions planned"], "routing fix")
    tag(43, 34.5, 69, 46, ["no planner:", "one fixed step", "to the router"], "no planner")
    tag(156, 34.5, 182, 46, ["no synthesizer:", "the steps' text", "is the answer"], "no synthesizer")
    tag(123, 30.5, 149, 42.5, ["every step", "distilled, with", "either prompt"],
        "every step distilled, with either prompt")
    tag(123, 10.5, 149, 22.5, ["no supervisor:", "each step once,", "no retry"], "no supervisor")
    # the keys, in the figure ([colour] colour_keys)
    kx, ky = 1.5, 13.0
    for dy, edge, ls, word in ((0, BLUE, "-", "model call"), (-5.5, BLACK, "-", "no model call"),
                               (-11, VERMILION, DASH, "ablation set-up")):
        ax.add_patch(FancyBboxPatch((kx, ky + dy), 6, 3.2, boxstyle="round,pad=0,rounding_size=0.6", fc="white",
                                    ec=edge, lw=LW, ls=ls))
        T(kx + 7.5, ky + dy + 1.6, word, "key", "key", ha="left")
    bad = hs.check_figure_colours(fig)
    if bad:
        plt.close(fig)
        raise Refused(f"colours outside the house palette: {bad}")
    try:                                            # build order F4: ligatures off, no text off the page or on another
        S457.finish_plate(fig, W_MM, H_MM, files, title=SI_LABEL)
    except SystemExit as e:
        raise Refused(str(e)) from None
    return rows, printed


# ---------------------------------------------------------------------------------------------------------------
# Legend, caption, workbook
# ---------------------------------------------------------------------------------------------------------------
def legend_text(stamp: str) -> str:
    # 7 Nov: the manuscript's accepted wording (goal and ordered steps, keyword rules and index size, rewritten
    # arguments then the rerun), carried back here so the draft equals the document
    body = (f"The analyser decides, in one model call, whether a question is answered directly, in one further "
            f"call without tools, or planned. The planner writes a goal and ordered steps, one tool each; at most "
            f"{MAX_STEPS_PRINTED} run. Document steps go to the smart query router, which picks a retrieval strategy by "
            f"keyword rules and index size, without a model call. The distiller condenses a step output longer than "
            f"209,712 characters. The supervisor scores each step from 0 to 100; below 70, the step's arguments are "
            f"rewritten and the step reruns, up to 3 times. The synthesizer writes the answer from the question, the "
            f"goal and each step's last output. "
            f"Blue box, a model call; black box, no model call; grey dashed frame, what runs for each plan step; dashed "
            f"{fn.VERMILION} box, an ablation set-up, drawn under or beside the step it changes. The {len(DRAWN)} "
            f"ablation set-ups are no analyser, the routing fix (factual questions "
            f"planned), no planner, no supervisor, no synthesizer and every step distilled with {fn.MENTORI}'s "
            f"prompt or with the worked-example prompt, which adds two worked examples that keep every number.")
    return (f"Legend DRAFT for {SI_LABEL} (written by {SCRIPT}).\n\n"
            f"**{SI_LABEL} | {TITLE}.**\n\n{body}\n")


def write_workbook(sheets: dict, path: Path):
    from openpyxl import Workbook
    from openpyxl.styles import Font
    wb = Workbook()
    wb.remove(wb.active)
    for name, (cols, rows_) in sheets.items():
        ws = wb.create_sheet(name)
        ws.append(cols)
        for c in ws[1]:
            c.font = Font(bold=True)
        for r in rows_:
            ws.append(r)
    wb.save(path)
    FR.deterministic_xlsx(path)


def build(out: Path) -> dict:
    if FLOCK.get("status") != "agreed":
        raise Refused(f"{rel(FIGURE_LOCK)} status {FLOCK.get('status')!r}, not 'agreed' (D87)")
    reproduced = reproduce(EXP03.read_text())
    stamp = (f"drawn from the code at experiments/mentori/, no data: the {len(DRAWN)} orchestration ablation "
             f"set-ups of Figure 5 and at most {MAX_STEPS_PRINTED} plan steps")
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob(f"{SI_LABEL}*"):
        old.unlink()
    files = {x: out / f"{SI_LABEL}.{x}" for x in ("pdf", "svg", "png")}
    lines, printed = draw(files)
    FR.check_pdf_deterministic(files["pdf"])
    FR.check_svg_deterministic(files["svg"])
    sheets = {SHEETS["lines"]: (["element", "kind", "line", "text"], lines),
              SHEETS["elements"]: (["element", "what_the_code_does", "source"], [list(e) for e in ELEMENTS]),
              SHEETS["setups"]: (["exp_03_config", "label"], [[k, v or "not drawn: not one of Figure 5's set-ups"] for k, v in SETUPS.items()])}
    sd = out / f"{SI_LABEL} data.xlsx"
    write_workbook(sheets, sd)
    numbers = out / f"{SIDE}_numbers.json"
    numbers.write_text(json.dumps({
        "stamp": stamp, "what": f"every text {SI_LABEL} prints and every element it draws, as the data workbook holds them",
        "sheets": {k: {"columns": c, "rows": r} for k, (c, r) in sheets.items()}, "printed": printed,
        "printed_what": "every text on the plate: the SVG group id of its text, the lines sheet's 0-based data row "
                        "and format it is written from (S448 R8 (6))"}, indent=1, ensure_ascii=False) + "\n")
    (out / "legend_draft.md").write_text(legend_text(stamp))
    capf = out / f"{SI_LABEL} data caption.md"
    capf.write_text(
        f"**{SI_LABEL} data |** The texts and elements drawn in {SI_LABEL}. Sheet {SHEETS['lines']}: one row per "
        f"printed line (the element it belongs to, its kind, its line number within the element and its text). Sheet "
        f"{SHEETS['elements']}: one row per box, arrow and label, with what the code does and the file and lines it "
        f"is read from (paths under experiments/mentori/; exp_03 is "
        f"publication/scripts/exp_03_orchestration_ablation.py). Sheet {SHEETS['setups']}: one row per set-up of the "
        f"orchestration ablation (exp_03 ORCHESTRATOR_CONFIGS, the full pipeline left out) and the dashed label that "
        f"draws it. Generated by `uv run --frozen python {SCRIPT}`.\n\n{stamp}.\n")
    prov = {
        "provenance": {"script": SCRIPT, "script_sha256": sha256_file(Path(__file__)),
                       "command": f"uv run --frozen python {SCRIPT}", "python": platform.python_version(),
                       "deterministic": "D155: no build time and no repository HEAD are recorded",
                       "inputs_sha256": {rel(EXP03): sha256_file(EXP03)}, "model_calls": 0},
        "reproduced": reproduced, "stamp": stamp, "figure": SI_LABEL,
        "named": f"{SI_LABEL}: FIGURE_LOCK [files] supplementary_name (D92 Q194); D257",
        "page_mm": [W_MM, H_MM],
        "figure_lock": {"path": rel(FIGURE_LOCK), "sha256": sha256_file(FIGURE_LOCK), "status": FLOCK.get("status")},
        "type_pt": {"all text": PT}, "font": FONT, "line_pt": LW,
        "colours": {"model call": BLUE, "no model call, text": BLACK, "ablation set-up": VERMILION,
                    "execution frame": GREY},
        "files": {p.name: sha256_file(p) for p in [*files.values(), sd, capf, numbers, out / "legend_draft.md"]}}
    (out / f"{SIDE}_provenance.json").write_text(json.dumps(prov, indent=1, ensure_ascii=False) + "\n")
    return {"stamp": stamp, "files": files, "reproduced": reproduced, "lines": len(lines)}


def main(argv=None):
    global OUT
    FR.pin_hash_seed()                     # D155: the PDF's font subsets depend on the string-hash seed
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", help="default findings/figures_provisional/supp_fig9_pipeline")
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    if a.out:
        OUT = Path(a.out).resolve()
    try:
        res = build(OUT)
    except Refused as e:
        print(f"S590 REFUSED: {e}", file=sys.stderr)
        sys.exit(2)
    print("reproduced: " + "; ".join(res["reproduced"]))
    print(f"wrote {', '.join(p.name for p in res['files'].values())} ({W_MM:g} x {H_MM:g} mm, {res['lines']} printed "
          f"lines), data workbook, caption, numbers, legend_draft.md, provenance into {rel(OUT)}")


if __name__ == "__main__":
    main()
