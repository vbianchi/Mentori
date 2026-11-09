#!/usr/bin/env python3
"""S534: Supplementary Tables of the revised paper, each from the run records: the model table (t7, Supplementary
Table 2 in the manuscript since TABLES and J7 of 6 Nov, findings/audits/audit_2026-11-06/rulings_2026-11-06.json),
the answer counts (t1, unnumbered: the manuscript's Table 1 is S583's judge calibration) and the signals table
(t9, "Table 9" in the plan and the code; Supplementary Table 3 in the manuscript since D276, 6 Nov).

One command, from the repository root, per table:
    uv run --frozen python scripts/S534_si_tables.py t7
    uv run --frozen python scripts/S534_si_tables.py t1
    uv run --frozen python scripts/S534_si_tables.py t9
    uv run --frozen python scripts/S534_si_tables.py selftest
Each table writes one xlsx and one md under findings/figures_provisional/supp_tables/.

TABLE 7, generator and judge pairing (A8, plan.csv:68; spec supp.md section 12). One row per experiment, generator set and
judge, columns as submitted (scripts/S88_ed_table_pairings.py HEAD): Experiment, What it contributes, Generator, Judge,
How the judge is known, Relationship, Files, Records. A second sheet lists every model of experiments/LOCK.toml with its
digest and machines (the full model list, page3 "2 Nov").
  Generator   read from each run's run_identity.json `agent_roles` (the generator or coder role, and the verifier where
              the run has one), the way S88 reads the old files. Other sources, by experiment: G6 from its answers.jsonl
              `model`; G9 from its answers.json `gen_model`; T1 from its results rows' `model`; model selection, the
              number of `model_ids` in each of the deposit's three result files. Added 6 November 2026 (plan.csv A8): T2
              per generator from judge_rows_v25.T2_SOURCES (the rows Table 9 counts, held by t2_source and checked
              against draws.csv's four names); G10 and G11 name gemini-3-flash-preview (D196), counted from S600's
              collects; G17 from its draw-1 run folders plus S573's draw-2 and draw-3 rows of the same runs; G19 from
              S573's arm A, B and C rows; T3 per model from its frozen set's run identities (one component role
              each); S18f from S18f_v25_results.json (answers, judge).
  Judge       the `model` field of the judge's committed judge_passages_headers.jsonl files where a set has them; else
              LOCK.toml [judge] model, and the column says so. No score of any judge is read: this script opens headers,
              run identities and answer-key counts only. qwen3.8:27b ([judge] second_model) is named on the rows of
              SECOND_JUDGE, by name and status only (D198 O4; D195 holds its scores).
  Records     stored answers: S492's registry, the same unit, per experiment. Where an experiment splits over two rows,
              each row's count is the distinct answer keys of its runs, and the rows must sum to the registry's count.
              Model selection's rows are each result file's per_question_results, held to the registry's kept_parts.
  Files       the run folders read.

REPRODUCE FIRST (README.md:75-79; any difference exits 2 and nothing is written): every experiment row of draws.csv is
placed (in the table or in NOT_YET_RUN); each split experiment sums to the registry; the 121 code-generation runs equal
Figure 6's records_manifest.json; every generator named is in the lock; each model-selection file's row count equals the
registry's kept_parts and they sum to its kept count; its judge equals S88_pairings.json's where S88 lists the file; no
form figure_names.py refuses is printed.

TABLE 1, answer counts by experiment (A6, plan.csv:66). Columns as submitted: row, Experiment, Design, Answers (D201 Q6,
2 November 2026: the word replaces "Evaluations"; D139's count stays).
Reads S492's registry (`today.experiments`, `anchor`) and draws.csv's design words. Reproduce first: 37,449 and 50,835,
S492's anchor. A row S492 does not count yet stays blank, and the table is provisional until the runs end. Design prints
draws.csv's words with decision codes dropped (design_words); code generation's reads the manifest's runs and attempts.
TABLE 9, signals recorded per experiment (A8). As S210 on the new records: for each experiment, the share of its records that
hold each key. Each row is parsed and only its key names are kept and counted, so no score reaches an output; the rows
parsed are the main judge's (devstral-small-2:24b), never the second judge's. Provisional: an experiment whose rows are
not in the repository yet is listed as not read. Records is the row count of the file each share is taken over; where that
differs from Table 1's stored answers the table's note says so.
  Rows added 6 November 2026 (plan.csv A8; rulings page 6 Nov, TABLES O2), each read the way its own builder reads it:
  Flat wide call and Short-passage single pass from S600's frozen collects (findings/recompute/g10_g11_v25_inputs);
  Plant-science reuse demonstration from S569's frozen judge rows and signals (findings/recompute/i2_inputs); Strategy
  replication from judge_rows_v25.T2_SOURCES, the v2.5 row of an answer where one exists, else its v2.4 row, each
  generator first passed through judge_rows_v25.t2_source (its checks and its reproduction of S518's earlier copies),
  whose cell count must equal the rows counted here; Component benchmarks and Distiller intervention from T3's frozen
  set (T3_SET, the set S524 figure --t3 reads), every answers.jsonl file held to the set's SHA256SUMS and its row count
  to MANIFEST.json, the two totals to draws.csv's 6,656 and 1,164. A T3 signal is counted where its key holds a value
  (not null), since every T3 row carries every key of its benchmark.
  NLI (MiniCheck) column, filled 6 November 2026 (D280): from the committed MiniCheck rows, NLI_SOURCES. Generation
  strategies: L1's key and papers rows as Figure 5 reads them (findings/recompute/fig5_d200_inputs/l1, S497's D200 set),
  one row per answer_key, every key one of the experiment's records, the counts held to plan.csv L1's (key 2,430, papers
  810, draw 1 only). Plant-science reuse: S569's i2_inputs/signals key and papers rows (90 each, held to each header's
  counts.rows); they were printed under Deterministic before D280, and are MiniCheck's (i2_signals.py key and papers),
  so they move here. A MiniCheck signal is counted where it holds a value (not null), as the T3 rule: every row carries
  every signal key, and MiniCheck stores null where it does not apply (Rule 8's not-answerable questions) or could not
  score (no answer, no claim sentence, over the encoder's limit). Rows with no MiniCheck job print why (NLI_NONE).

Each workbook carries a Provenance sheet: this script's sha256, the command and the sha256 of every file read.
"""
from __future__ import annotations

import csv
import json
import re
import sys
import tempfile
import tomllib
from collections import Counter, OrderedDict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import fig_repro  # noqa: E402
import fig_design  # noqa: E402
import figure_names as FN  # noqa: E402
from machine import RESULTS  # noqa: E402  the deposit's results folder, as every script finds it

import openpyxl  # noqa: E402
from openpyxl.styles import Alignment, Font  # noqa: E402

OUT = REPO / "findings/figures_provisional/supp_tables"
REC = REPO / "findings/recompute"
DRAWS = REPO / "experiments/draws.csv"   # t7 (held in the release, not rerun there)
# t1 (D2, Valerio, 8 Nov: built from data only): fig_design_inputs/draws.csv, S616 extract's copy of every row of
# experiments/draws.csv with the columns t1 reads (experiment, plan_row, design), held to it by S616 check. Its
# provenance keeps the sha256 of the draws.csv the extract was taken from (design_facts.json "sources"), so the table
# records the same source as before.
DRAWS_T1 = fig_design.DRAWS


def draws_source_sha256() -> str:
    hit = [s for s in fig_design.facts()["sources"] if s["path"] == "experiments/draws.csv"]
    if len(hit) != 1:
        die(f"design_facts.json names experiments/draws.csv {len(hit)} times as a source, not once")
    return hit[0]["sha256"]
LOCK = REPO / "experiments/LOCK.toml"
REGISTRY = REC / "S492_answer_registry/registry.json"
T2X_COLLECTS = {"gemma3": "T2X_runs/collect/t2xgemma_collect.jsonl",
                "qwen3-coder": "T2X_runs/collect/t2xqcoder_collect.jsonl"}   # the main judge's T2X rows (S492)
S88 = REC / "S88_pairings.json"
MANIFEST = REPO / "findings/figures_provisional/fig6/records_manifest.json"

HEAD = ["Experiment", "What it contributes", "Generator", "Judge", "How the judge is known", "Relationship", "Files",
        "Records"]

# draws.csv experiment -> what it contributes, with the figure numbers of the one list (build_order.md section 4)
CONTRIBUTES = {
    "Model selection": "Choice of generator and of the recursive language model (made before the experiments reported here, not run again)",
    "Retrieval optimisation": "Retrieval pipeline selection (Supplementary Figure 2); mean reciprocal rank, no language "
                              "model (made before the experiments reported here, not run again)",
    "Generation strategies": "Strategy comparison (Figure 3)",
    "Matched-budget arm": "Single pass at matched budget (Figure 3)",
    "Package RLM at caps 5 10 20": "Zhang RLM at caps 5, 10 and 20 (Figure 3, Supplementary Figure 17)",
    "Retrieval depth": "Turn caps, RLM (Figure 4a); concept recall",   # N4a Q: Supplementary Figure 8 is corpus size, not depth
    "Retrieval depth, local models": "Turn caps, local generators (Figure 4b); concept recall, no judge",
    "Package RLM depth caps": "Turn caps, Zhang RLM (Figure 4a, Supplementary Figure 7); concept recall, no judge",
    "Corpus scaling": "Corpus size (Figure 3, Supplementary Figure 8)",
    "Flat wide call": "One wide call at a fixed passage count (Discussion)",
    "Short-passage single pass": "Single pass with each passage cut to its first 800 characters (Discussion)",
    "Pipeline ablation": "Pipeline set-ups (Figure 5)",
    "No retrieval and naive RAG": "Baselines (Figure 5)",
    "Distiller on every step (stress)": "Stress set-ups (Figure 5)",
    "Code generation": "Code generation (Figure 7, Supplementary Figures 14 to 16); scored by running the code against "
                       "known outputs, no language-model judge",
    "Strategy replication": "Replication across generators (Figure 3, Supplementary Figure 6)",
    "Plant-science reuse demonstration": "Reuse on five plant-science papers (Supplementary Figure 13)",
    "Component benchmarks": "Each orchestrator component against its benchmark items (Supplementary Figure 10)",
    "Distiller intervention": "The distiller's prompt, Mentor::i's against the worked-example prompt (Supplementary Figure 11)",
    "RLM ablation": "RLM-10 with search off or the gate off, against its control (Figure 5)",
    "RLM ablation, gemma3:27b": "Zhang RLM, search off and gate off with a local generator (Supplementary Note 5)",
    "Judge with evidence": "The judge given the answer's own papers, unrelated papers or none (Results)",
}

# what the table prints for a draws.csv row whose own name a plate may not use (figure_names.py, build_order.md A4), or
# that is not in the paper's spelling
DISPLAY = {"Package RLM at caps 5 10 20": "Zhang RLM at caps 5, 10 and 20", "Package RLM depth caps": "Zhang RLM at the depth caps",
           "Distiller on every step (stress)": "Always distil (stress)", "Retrieval optimisation": "Retrieval optimization"}

# the deposit's three model-selection files, as S13 names them
SELECTION_WORDS = {"exp00_rlm_models": "generator selection", "exp00_phase2": "generator selection, phase 2",
                   "exp00_triage": "model triage"}

# draws.csv rows that have not run. T3's rows joined on 6 November 2026 from its frozen set (plan.csv A8).
NOT_YET_RUN: tuple = ()

# the second judge, by name and status only (D198 O4; GAP3 a; D195: no score is read). Status and source of each row.
SECOND_JUDGE = {
    # sources, kept in the code (N4a): RUNNING.md:1825, :1883 (G1); RUNNING.md:1883, :1919 (haiku);
    # t2_second_inputs, S592 a1dc9398 (gemini-2.5-pro, gemma3:27b, qwen3-coder:30b)
    ("Generation strategies", "gemini-3-flash-preview"): "judged",
    ("Strategy replication", "claude-haiku-4-5"): "judged",
    ("Strategy replication", "gemini-2.5-pro"): "judged",
    ("Strategy replication", "gemma3:27b"): "judged",
    ("Strategy replication", "qwen3-coder:30b"): "judged",
}

# committed judge header folders, per experiment (no T2 or second-judge folder is listed here, and none is read)
JUDGE_HEADERS = {
    "Generation strategies": ["fig2_inputs/out/judge", "fig2_inputs/out_g1r15/judge"],
    "Matched-budget arm": ["fig3_s6_inputs/out_g2/judge"],
    "Package RLM at caps 5 10 20": ["fig3_s6_inputs/out_g6/judge"],
    "Corpus scaling": ["fig3_inputs/s3/out_g4/judge", "fig3_inputs/s3/out_g4r38/judge"],
    "Pipeline ablation": ["fig4_inputs/out_g3/judge"],
    "No retrieval and naive RAG": ["fig4_inputs/out_g3/judge"],
    "Plant-science reuse demonstration": ["I2_runs/judge"],
    "Flat wide call": ["g10_g11_v25_inputs/out_s6_w_g10/judge"],
    "Short-passage single pass": ["g10_g11_v25_inputs/out_s6_w_g11/judge"],
    "RLM ablation": ["G17_runs/out_s6_w_g17/judge"],
}
NO_JUDGE = ("Retrieval optimisation", "Retrieval depth, local models", "Package RLM depth caps", "Code generation",
            "Component benchmarks", "Distiller intervention")
JUDGED_LATER: tuple = ()     # G10 and G11 judged 2 November, frozen by S600 (6 November)


def die(msg: str):
    print(f"REFUSED: {msg}", file=sys.stderr)
    sys.exit(2)


def rel(p: Path) -> str:
    try:
        return str(Path(p).resolve().relative_to(REPO))
    except ValueError:
        return fig_repro.frozen_label(p)


def check_names(text: str) -> None:
    """Refuses a form figure_names.NEVER refuses in plate or legend text: tables print the same names."""
    hit = [n.form for n in FN.NEVER if re.search(n.pattern, text, re.I)]
    if hit:
        die(f"a form figure_names.py refuses would be printed: {hit}")


def provenance(wb, cmd: str, info: dict) -> None:
    ws = wb.create_sheet("Provenance")
    ws.append(["script", "scripts/S534_si_tables.py"])
    ws.append(["script_sha256", fig_repro.sha256_file(Path(__file__))])
    ws.append(["command", cmd])
    for k, v in info.items():
        ws.append([k, json.dumps(v, sort_keys=True) if isinstance(v, (list, dict)) else v])


def design_words(row: dict, man: dict) -> str:
    """Table 1's Design: draws.csv's words, no decision code; code generation's from the manifest, because the plan's
    product is not the design that ran."""
    if row["experiment"] == "Code generation":
        runs = len(man["runs"])
        if man["attempts_total"] % runs:
            die(f"code generation: {man['attempts_total']} attempts do not divide by {runs} runs")
        return f"{runs} model and strategy set-ups x {man['attempts_total'] // runs} operations"
    d = re.sub(r"\s*\((?:D|Q)\d+(?:[^()]|\([^()]*\))*\)", "", row["design"])
    d = d.replace("Figure 2's six strategies", "Figure 3's six strategies").replace(", key PB v1.1", "")
    if re.search(r"\b[DQ]\d+\b", d):
        die(f"{row['experiment']}: a decision code is left in the design: {d}")
    return d


def selection_rows(exp: str, why: str, reg: dict, s88: list) -> list[list]:
    """Model selection, from the deposit's three result files: one row per file. Only names and counts are kept."""
    parts = reg["anchor"]["kept_parts"][exp]
    judges = {t["family"]: t["judge"] for t in s88}
    out = []
    for stem, want in parts.items():
        d = json.loads((RESULTS / f"{stem}_latest.json").read_text())
        n = len(d["per_question_results"])
        if n != want:
            die(f"{stem}: {n} rows, the registry's kept_parts {want}")
        models = [short(m) for m in d["model_ids"]]
        judge = short(d.get("judge_model"))
        if stem in judges and judges[stem] != judge:
            die(f"{stem}: the file's judge is {judge}, S88_pairings.json's {judges[stem]}")
        how = "recorded in the file" if judge else "no judge recorded in the file"
        rel_ = ("no language-model judge recorded" if not judge else
                f"self-judged on 1 of {len(models)} generators" if judge in models else "cross-family")
        out.append([exp, f"{why}: {SELECTION_WORDS[stem]}", f"{len(models)} models", judge or "-", how, rel_, 1, n])
    if sum(r[7] for r in out) != reg["today"]["kept_from_april"][exp]:
        die(f"{exp}: the rows add to {sum(r[7] for r in out)}, the registry keeps {reg['today']['kept_from_april'][exp]}")
    return out


def short(m: str | None) -> str | None:
    return (m or "").split("::", 1)[-1] or None


def relation(gen: str | None, judge: str | None) -> str:
    """S88's relation(), on the first model of a generator set."""
    if not judge:
        return "no language-model judge"
    if not gen:
        return "no generator (judge or scorer only)"
    if gen == judge:
        return "self-judged: generator and judge are the identical model"
    g, j = short(gen).split(":")[0], short(judge).split(":")[0]
    gfam = re.sub(r"[\d.\-].*$", "", g)
    jfam = re.sub(r"[\d.\-].*$", "", j)
    return "same family, different model" if gfam == jfam else "cross-family"


def run_models(rd: Path) -> tuple[str, str | None]:
    """(generator, verifier) of a run folder, from run_identity.json agent_roles."""
    ident = json.loads((rd / "run_identity.json").read_text())
    roles = ident.get("agent_roles") or {}
    gen = short(roles.get("generator") or roles.get("coder") or roles.get("rlm_ref") or roles.get("default"))
    if not gen:
        die(f"{rel(rd)}: no generator role in {sorted(roles)}")
    return gen, short(roles.get("verifier"))


def answer_keys(rd: Path) -> int:
    """Distinct answer keys stored in a run folder; only the keys are kept."""
    jl, js = rd / "answers.jsonl", rd / "answers.json"
    if not jl.is_file() and not js.is_file():
        return 0                  # a sink that keeps its identity only (G5's): the registry's count stands for its row
    if jl.is_file():
        keys = {json.loads(ln)["answer_key"] for ln in jl.read_text().splitlines() if ln.strip()}
        return len(keys)
    data = json.loads(js.read_text())
    rows = data if isinstance(data, list) else data.get("results") or data.get("answers") or data
    if isinstance(rows, dict):
        return len(rows)
    return len({r.get("answer_key") or json.dumps([r.get("question_id"), r.get("draw")]) for r in rows})


def judge_of(exp: str) -> tuple[str | None, str]:
    """(judge, how it is known) of an experiment, from committed headers only; the header's `model` field is the sole
    field read."""
    lock = tomllib.loads(LOCK.read_text())
    if exp in NO_JUDGE:
        return None, "no judge row exists"
    if exp in JUDGED_LATER:
        return lock["judge"]["model"], "the study's settings file, experiments/LOCK.toml ([judge]); answers not judged yet"
    dirs = JUDGE_HEADERS.get(exp)
    if not dirs:
        return lock["judge"]["model"], "the study's settings file, experiments/LOCK.toml ([judge]); this run's judge header files are not in the analysis repository"
    names, n = set(), 0
    for d in dirs:
        for h in sorted((REC / d).rglob("judge_passages_headers.jsonl")):
            for ln in h.read_text().splitlines():
                if ln.strip():
                    names.add(json.loads(ln)["model"])
                    n += 1
    if not n:
        die(f"{exp}: no header line under {dirs}")
    if len(names) != 1:
        die(f"{exp}: headers name {sorted(names)}, one judge expected")
    return names.pop(), f"recorded in the judge's header files ({n} lines)"


def run_groups(reg: dict) -> "OrderedDict[str, list[dict]]":
    """Per experiment, its rows {gen, verifier, files, records}, one per generator set, from run folders."""
    def groups(folders) -> list[dict]:
        out: "OrderedDict[tuple, dict]" = OrderedDict()
        for rd in sorted(folders):
            g, v = run_models(rd)
            row = out.setdefault((g, v), {"gen": g, "verifier": v, "files": 0, "records": 0})
            row["files"] += 1
            row["records"] += answer_keys(rd)
        return list(out.values())

    def g6_group(tail: str) -> list[dict]:
        """G6: its committed copy keeps answers.jsonl only, so the generator is each row's `model`."""
        names, files, keys = set(), 0, set()
        for rd in sorted((REC / "L2_inputs/g6").iterdir()):
            if not rd.name.endswith(tail):
                continue
            files += 1
            for ln in (rd / "answers.jsonl").read_text().splitlines():
                if ln.strip():
                    row = json.loads(ln)
                    names.add(short(row["model"]))
                    keys.add((rd.name, row["answer_key"]))
        if len(names) != 1:
            die(f"G6 {tail}: rows name {sorted(names)}, one generator expected")
        return [{"gen": names.pop(), "verifier": None, "files": files, "records": len(keys)}]

    def frozen_runs(stem: str, sub: str, pick=lambda p: True) -> list[Path]:
        base = fig_repro.frozen(stem, sub)
        return [p for p in sorted(base.iterdir()) if (p / "run_identity.json").is_file() and pick(p)]

    r: "OrderedDict[str, list[dict]]" = OrderedDict()
    r["Generation strategies"] = groups(frozen_runs("s457_mirror_20261022", "s457_mirror_20261022",
                                                    lambda p: p.name != "matched_budget"))
    r["Matched-budget arm"] = groups(frozen_runs("s457_mirror_20261022", "s457_mirror_20261022",
                                                 lambda p: p.name == "matched_budget"))
    r["Package RLM at caps 5 10 20"] = g6_group("__all135")
    r["Package RLM depth caps"] = g6_group("__depthsweep86")
    r["Retrieval depth"] = groups(frozen_runs("answer_lengths_20261020", "answer_lengths_20261020/G5/sinks"))
    r["Corpus scaling"] = groups(frozen_runs("g4_draws_20261101", "g4_draws_20261101/runs"))     # every draw (D287 (1)), as S492
    # G3 and G9: every draw, from count_records_20261108.tar's g3/runs, as S492 since 8 Nov (Valerio: these draws are in
    # Source Data Fig. 5); fig4_records_1023.tar and g9_inputs held draw 1 only
    cr8 = "count_records_20261108"
    base = f"{cr8}/g3/runs"
    baselines = ("exp_03__naive_rag__exp_v4_s20_n0", "exp_03__raw_gemini__exp_v4_s20_n0")
    distil = ("exp_03__orch_distil_every_step__exp_v4_s20_n0", "exp_03__orch_distil_every_step_f1__exp_v4_s20_n0")
    r["Pipeline ablation"] = groups(frozen_runs(cr8, base, lambda p: p.name not in baselines + distil))
    r["No retrieval and naive RAG"] = groups(frozen_runs(cr8, base, lambda p: p.name in baselines))
    g9 = frozen_runs(cr8, base, lambda p: p.name in distil)
    names = {short(x["gen_model"]) for p in g9 for x in json.loads((p / "answers.json").read_text())["results"]}
    if len(names) != 1:
        die(f"G9: rows name {sorted(names)}, one generator expected")
    r["Distiller on every step (stress)"] = [{"gen": names.pop(), "verifier": None, "files": len(g9),
                                              "records": sum(answer_keys(p) for p in g9)}]
    r["Plant-science reuse demonstration"] = groups(p for p in sorted((REC / "I2_runs/sinks").iterdir()) if p.is_dir())

    # G17: draw 1's run folders (run identity), and draws 2 and 3 counted from S573's concept-recall rows of those runs
    g17 = groups(p for p in sorted((REC / "G17_runs/inputs/runs").iterdir()) if p.is_dir())
    g17_runs = {p.name for p in (REC / "G17_runs/inputs/runs").iterdir() if p.is_dir()}
    d23 = {}
    for ln in (REC / "G17_concept_recall_d23/concept_recall.jsonl").read_text().splitlines():
        if ln.strip():
            x = json.loads(ln)
            if x["run_id"] not in g17_runs or x["draw"] not in (2, 3):
                die(f"G17 draws 2 and 3: row {x['answer_key']} of run {x['run_id']} draw {x['draw']}")
            d23[(x["run_id"], x["answer_key"])] = 1
    if len(g17) != 1:
        die(f"G17: {len(g17)} generator sets, one expected")
    g17[0]["records"] += len(d23)
    r["RLM ablation"] = g17
    # G19: arms A, B and C of S573's concept-recall rows (R is T2's stored RLM-10, counted there); B and C name their
    # generator in the run id; A, the package's RLM, runs the same model (G19_runs/README.md) and names none
    g19 = [json.loads(ln) for ln in (REC / "G19_concept_recall/concept_recall.jsonl").read_text().splitlines() if ln.strip()]
    g19 = [x for x in g19 if x["arm"] in ("A", "B", "C")]
    tails = {x["run_id"].split("+")[1] for x in g19 if "+" in x["run_id"]}
    if tails != {"gemma3-27b"}:
        die(f"G19: run ids name {sorted(tails)}, gemma3-27b expected")
    r["RLM ablation, gemma3:27b"] = [{"gen": "gemma3:27b", "verifier": None, "files": len({x["run_id"] for x in g19}),
                                      "records": len({(x["run_id"], x["answer_key"]) for x in g19})}]
    # G10 and G11: their judge rows name the run (S600's collects); the generator is D196's
    for exp, f in (("Flat wide call", "g10_collect.jsonl"), ("Short-passage single pass", "g11_collect.jsonl")):
        xs = [json.loads(ln) for ln in (REC / "g10_g11_v25_inputs" / f).read_text().splitlines() if ln.strip()]
        r[exp] = [{"gen": "gemini-3-flash-preview", "verifier": None, "files": len({x["run_id"] for x in xs}),
                   "records": len(xs)}]
    # T2: judge_rows_v25's sources, the rows Table 9 counts
    import judge_rows_v25 as JR
    r["Strategy replication"] = []
    for g, name in (("claude-haiku-4-5", "claude-haiku-4-5"), ("gemini-2.5-pro", "gemini-2.5-pro"),
                    ("gemma3", "gemma3:27b"), ("qwen3-coder", "qwen3-coder:30b")):
        sp, merged = JR.T2_SOURCES[g], {}
        cells = JR.t2_source(g)["counts"]["cells"]          # refuses as its checks refuse
        for key in ("base", "v25"):
            if sp.get(key):
                for d in JR.read_jsonl(Path(sp[key])):
                    merged[JR.JP.ident(d)] = d
        if len(merged) != cells:
            die(f"T2 {g}: {len(merged)} rows, judge_rows_v25.t2_source gives {cells} cells")
        if g in T2X_COLLECTS:                      # T2X (D241), counted in T2's row by S492 since 8 Nov
            x = {JR.JP.ident(d): d for d in JR.read_jsonl(REC / T2X_COLLECTS[g])}
            if len(x) != 17 or set(x) & set(merged):
                die(f"T2X {g}: {len(x)} rows, {len(set(x) & set(merged))} shared with T2's; 17 and none expected")
            merged.update(x)
        r["Strategy replication"].append({"gen": name, "verifier": None, "files": len({d["run_id"] for d in merged.values()}),
                                          "records": len(merged)})
    # T3: one row per model, from the frozen set's sinks (MANIFEST.json answers_per_sink, held in t3_rows)
    man3 = json.loads((T3_SET / "MANIFEST.json").read_text())
    for exp, pre in (("Component benchmarks", "exp_04__"), ("Distiller intervention", "exp_04b__")):
        per3: "OrderedDict[str, dict]" = OrderedDict()
        for sink, n in sorted(man3["answers_per_sink"].items()):
            if sink.startswith(pre):
                roles = json.loads((T3_SET / "sinks" / sink / "run_identity.json").read_text()).get("agent_roles") or {}
                if len(roles) != 1:
                    die(f"T3 {sink}: agent_roles {sorted(roles)}, one component role expected")
                g = short(next(iter(roles.values())))
                row = per3.setdefault(g, {"gen": g, "verifier": None, "files": 0, "records": 0})
                row["files"] += 1
                row["records"] += n
        r[exp] = [per3[k] for k in sorted(per3)]
    # S18f: G1's draw-1 answers, judged again with evidence; the answers and the judge from its results file
    s18 = json.loads((REC / "S18f_v25_results.json").read_text())
    r["Judge with evidence"] = [{"gen": "gemini-3-flash-preview", "verifier": None, "files": 1,
                                 "records": s18["analysis_set"]["answers"]}]

    # T1: its results rows, the registry's per_model
    t1 = next(e for e in reg["today"]["experiments"] if e["experiment"] == "Retrieval depth, local models")
    t1_files = Counter()
    for f in sorted(fig_repro.frozen("fig3_t1", "fig3_t1/results_v4").glob("*.json")):
        for m in {x["model"] for x in json.loads(f.read_text())["results"]}:
            t1_files[m] += 1
    r["Retrieval depth, local models"] = [{"gen": short(m), "verifier": None, "files": t1_files[m], "records": n}
                                          for m, n in sorted(t1["note"]["per_model"].items())]
    # S2: the 121 runs Figure 6's manifest names, each model from its run identity
    man = json.loads(MANIFEST.read_text())
    base2 = fig_repro.frozen("s2_length_retries_20261021", "s2_length_retries_20261021")
    idx = {}
    for p in sorted(base2.rglob("run_identity.json")):
        idx.setdefault(p.parent.name, []).append(p.parent)
    per: "OrderedDict[str, dict]" = OrderedDict()
    for run, m in sorted(man["runs"].items()):
        hit = [p for p in idx.get(run, []) if fig_repro.sha256_file(p / "run_identity.json") ==
               m["files"]["run_identity.json"]["sha256"]]
        if not hit:
            die(f"code generation run {run}: no frozen run_identity.json with the manifest's sha256")
        g, _ = run_models(hit[0])
        row = per.setdefault(g, {"gen": g, "verifier": None, "files": 0, "records": 0})
        row["files"] += 1
        row["records"] += m["attempts"]
    r["Code generation"] = [per[k] for k in sorted(per)]
    return r


def parse_replication(row: dict) -> list[str]:
    """T2's generators, from draws.csv's design words in parentheses."""
    m = re.search(r"\(D160 \(2\): ([^;)]+)", row["design"])
    if not m:
        die("draws.csv Strategy replication: its design no longer names the four generators in D160 (2)'s words")
    return [g.strip() for g in m.group(1).split(",")]


def build_t7() -> tuple[list[list], list[list], dict]:
    reg = json.loads(REGISTRY.read_text())
    by_exp = {}
    for e in reg["today"]["experiments"]:
        by_exp.setdefault(e["experiment"], e)
    with DRAWS.open(newline="") as f:
        draws = list(csv.DictReader(f))
    lock = tomllib.loads(LOCK.read_text())
    groups = run_groups(reg)
    gemini = "gemini-3-flash-preview"
    table: list[list] = []
    placed = []

    s88 = [t for t in json.loads(S88.read_text())["pairings"] if t["family"].startswith("exp00")]

    for row in draws:
        exp = row["experiment"]
        placed.append(exp)
        if exp in NOT_YET_RUN:
            continue
        if exp not in CONTRIBUTES:
            die(f"draws.csv row {exp!r} has no place in Table 7: add it")
        why = CONTRIBUTES[exp]
        if exp == "Model selection":
            table += selection_rows(exp, why, reg, s88)
            continue
        if exp == "Retrieval optimisation":
            parts = reg["anchor"]["kept_parts"][exp]
            table.append([exp, why, "-", "-", "no judge row exists", "no language-model judge", len(parts),
                          sum(parts.values())])
            continue
        judge, how = judge_of(exp)
        if exp == "Strategy replication":
            gens = parse_replication(row)
            if sorted(gens) != sorted(g["gen"] for g in groups[exp]):
                die(f"Strategy replication: draws.csv names {gens}, the records {[g['gen'] for g in groups[exp]]}")
            # held by judge_rows_v25.t2_source: one run_sha256 per key version, gemma3 and qwen3-coder also to headers
            how = ("the study's settings file, experiments/LOCK.toml ([judge]); every judged answer is tied to its judge "
                   "run by a sha256 checksum, and for gemma3:27b and qwen3-coder:30b also to the judge's header files")
        if exp == "Judge with evidence":
            judge, how = json.loads((REC / "S18f_v25_results.json").read_text())["judge"].split(" (")[0], \
                "named in the experiment's results file"
        if exp in JUDGED_LATER:
            table.append([exp, why, gemini, judge, how, relation(gemini, judge), None, None])
        else:
            if exp not in groups:
                die(f"{exp}: no run folders are read for it")
            rows = groups[exp]
            if exp == "Strategy replication":
                # T2's rows are judge rows; a stored answer with no text has none (the judge reads no empty answer).
                # S492 lists each such answer, so it is added back to its generator and Records counts stored answers.
                note = by_exp[exp].get("note") or {}
                for key in note.get("stored_with_no_text_not_judged", []):
                    gen = key.split("|")[0].rsplit("+", 1)[-1]
                    hit = [g for g in rows if g["gen"] == gen]
                    if len(hit) != 1:
                        die(f"Strategy replication: S492's no-text answer {key} names no generator of the records")
                    hit[0]["records"] += 1
                for g in rows:
                    want_g = (note.get("per_generator") or {}).get(g["gen"].replace(":", "-"))
                    if want_g is not None and g["records"] != want_g:
                        die(f"Strategy replication {g['gen']}: runs hold {g['records']}, S492's registry {want_g}")
            for g in rows:
                name = g["gen"] + (f"; verifier {g['verifier']}" if g["verifier"] else "")
                table.append([exp, why, name, judge or "-", how, relation(g["gen"], judge), g["files"], g["records"]])
            want = by_exp.get(exp, {}).get("stored")
            got = sum(g["records"] for g in rows)
            if got == 0 and len(rows) == 1 and want is not None:     # G5: the registry counts its results file
                table[-1][7] = want
            elif want == 0 and by_exp[exp].get("special_case") and len(rows) == 1:
                # S12 (D281): judge calls on G1's answers, which G1 counts; no stored answer of its own
                sc = by_exp[exp]["special_case"]          # S492's words carry G1, S18f and D281; the reader's do not
                if "4 arms" not in sc or "366 of G1's draw-1 answers" not in sc:
                    die(f"{exp}: S492's special_case changed: {sc!r}")
                table[-1][4] += ("; it stores no answer of its own: its judge calls (4 arms) are on 366 first-draw "
                                 "answers of the generation strategies, which that experiment's row counts")
                table[-1][7] = 0
            elif want is not None and got != want:
                die(f"{exp}: runs hold {got}, S492's registry {want}")
    # the second judge's rows, placed under their experiment
    out: list[list] = []
    for t in table:
        out.append(t)
        k = (t[0], t[2].split(";")[0])
        if k in SECOND_JUDGE:
            j2 = lock["judge"]["second_model"]
            out.append([t[0], t[1], t[2], j2, f"the study's settings file, experiments/LOCK.toml ([judge] second_model); {SECOND_JUDGE[k]}",
                        relation(t[2].split(";")[0], j2), None, None])
    table = out

    # gates
    missing = [k for k in SECOND_JUDGE if not any(t[0] == k[0] and t[2].split(";")[0] == k[1] for t in table)]
    if missing:
        die(f"second-judge rows with no generator row: {missing}")
    if len(placed) != len(draws):
        die("draws.csv rows not all placed")
    man = json.loads(MANIFEST.read_text())
    s2 = [t for t in table if t[0] == "Code generation"]
    if sum(t[6] for t in s2) != len(man["runs"]) or sum(t[7] for t in s2) != man["attempts_total"]:
        die(f"code generation: {sum(t[6] for t in s2)} runs and {sum(t[7] for t in s2)} attempts, manifest "
            f"{len(man['runs'])} and {man['attempts_total']}")

    # the model list: every model the lock names, then what the table uses it for
    used: dict[str, set] = {}
    role_of: dict[str, set] = {}
    def note(name, exp, role):
        used.setdefault(name, set()).add(exp)
        role_of.setdefault(name, set()).add(role)
    for t in table:
        parts = [p.strip() for p in str(t[2]).split(";")]
        if parts[0] != "-" and t[0] != "Model selection":      # its files hold several generators each, named there
            note(parts[0], t[0], "generator")
        for p in parts[1:]:
            note(p.replace("verifier ", ""), t[0], "verifier")
        if t[3] != "-":
            note(t[3], t[0], "second judge" if t[3] == lock["judge"].get("second_model") else "judge")
    models = []
    pool = {}
    for tag, m in lock["models"].items():
        pool[tag] = {"digest": m["digest"], "machines": ", ".join(m["machines"]), "where": "Ollama"}
    for tag in lock["gemini"]["thinking_off"]:
        pool[tag] = {"digest": "-", "machines": "Google API", "where": "Google"}
    pool[lock["anthropic"]["model_id"]] = {"digest": "-", "machines": "Anthropic API", "where": "Anthropic"}
    alias = {tag: tag.replace("-date20261010", "") for tag in pool}
    alias_back = {v: k for k, v in alias.items()}
    alias_back["claude-haiku-4-5"] = lock["anthropic"]["model_id"]
    for stem in reg["anchor"]["kept_parts"]["Model selection"]:      # a lock model tested in April is in that experiment
        for m in json.loads((RESULTS / f"{stem}_latest.json").read_text())["model_ids"]:
            if short(m) in alias_back:
                note(short(m), "Model selection", "generator")
    for name in used:
        if name not in alias_back and not name.startswith("qwen3-coder:latest"):
            die(f"model {name!r} is in the table and not in LOCK.toml")
    for tag in pool:
        name = next((n for n in used if alias_back.get(n) == tag), None)
        roles = sorted(role_of.get(name, [])) if name else []
        if tag == lock["scorers"]["embedding"]:
            roles = ["encoder for answer relevancy (RAGAS)"]
        models.append([tag, pool[tag]["where"], pool[tag]["digest"], pool[tag]["machines"],
                       ", ".join(roles) if roles else "in the lock, in no experiment of this table",
                       ", ".join(sorted(DISPLAY.get(e, e) for e in used.get(name, []))) if name else "-"])
    prov = {"not_yet_run": list(NOT_YET_RUN),
            "registry_sha256": fig_repro.sha256_file(REGISTRY), "lock_sha256": fig_repro.sha256_file(LOCK),
            "draws_sha256": fig_repro.sha256_file(DRAWS), "s88_sha256": fig_repro.sha256_file(S88),
            "manifest_sha256": fig_repro.sha256_file(MANIFEST),
            "selection_sha256": {k: fig_repro.sha256_file(RESULTS / f"{k}_latest.json") for k in SELECTION_WORDS},
            "rows": len(table), "models": len(models)}
    return table, models, prov


T7_NOTE = ("Generator and judge for every experiment of this study. Generator names come from the run records in the "
           "analysis repository: each run's identity file, or the model field of its answer rows or result rows for Zhang "
           "RLM, the stress set-ups and the local-model depth sweep. Model selection reads the three result files of the "
           "earlier selection runs, each with several generators, so the row gives their number. The flat wide call and the "
           "short-passage single pass name gemini-3-flash-preview from their design, since only their judge rows are in "
           "the analysis repository; the component benchmarks and the distiller intervention name the model of each run's "
           "single component role. Judge names come from the judge's header files where they are in the analysis "
           "repository, otherwise from the study's settings file, experiments/LOCK.toml. devstral-small-2:24b is the main "
           "judge. qwen3.8:27b is the second judge and appears only on the rows it judged; its scores are not read here. "
           "Records counts stored answers. Files and Records are blank on the second judge's rows: their answers are "
           "counted once, on the main judge's row.")


def write_t7() -> int:
    table, models, prov = build_t7()
    check_names(json.dumps([[DISPLAY.get(t[0], t[0])] + t[1:] for t in table] + models) + T7_NOTE)
    OUT.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Generator and judge pairing"
    ws.append(HEAD)
    for t in table:
        ws.append([DISPLAY.get(t[0], t[0])] + t[1:])
    for c in ws[1]:
        c.font = Font(bold=True)
        c.alignment = Alignment(wrap_text=True, vertical="top")
    for i, w in enumerate([32, 46, 40, 24, 44, 28, 7, 9], 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w
    ws.freeze_panes = "A2"
    ws2 = wb.create_sheet("Models")
    mh = ["Model", "Served by", "Digest", "Machines", "Role", "Experiments"]
    ws2.append(mh)
    for m in models:
        ws2.append(m)
    for c in ws2[1]:
        c.font = Font(bold=True)
    provenance(wb, "uv run --frozen python scripts/S534_si_tables.py t7", prov)
    x = OUT / "Supplementary Table 2.xlsx"
    wb.save(x)
    fig_repro.deterministic_xlsx(x)
    md = ["# Supplementary Table 2 | Generator and judge pairing", "", T7_NOTE, "",
          "| " + " | ".join(HEAD) + " |", "|" + "---|" * len(HEAD)]
    for t in table:
        md.append("| " + " | ".join("" if v is None else str(v) for v in [DISPLAY.get(t[0], t[0])] + t[1:]) + " |")
    md += ["", "## Models", "", "| " + " | ".join(mh) + " |", "|" + "---|" * len(mh)]
    md += ["| " + " | ".join(str(v) for v in m) + " |" for m in models]
    (OUT / "Supplementary Table 2.md").write_text("\n".join(md) + "\n")
    print(f"wrote {rel(x)}: {len(table)} rows, {len(models)} models; self-judged: "
          f"{sum(1 for t in table if str(t[5]).startswith('self'))}")
    return 0


# ---------------------------------------------------------------------------------------------------------------
# Table 1
# ---------------------------------------------------------------------------------------------------------------
T1_HEAD = ["Row", "Experiment", "Design", "Answers"]
ANCHOR_WANT = {"S13_total": 37449, "S187_total": 50835}


def build_t1() -> tuple[list[list], dict]:
    reg = json.loads(REGISTRY.read_text())
    anc = reg["anchor"]
    got = {k: anc[k] for k in ANCHOR_WANT}
    if got != ANCHOR_WANT:
        die(f"S492's anchor is {got}, the gate holds {ANCHOR_WANT}")
    by = {}
    for e in reg["today"]["experiments"]:
        by.setdefault(e["experiment"], []).append(e)
    kept = reg["today"]["kept_from_april"]
    with DRAWS_T1.open(newline="") as f:
        draws = list(csv.DictReader(f))
    man = json.loads(MANIFEST.read_text())
    rows = []
    for i, row in enumerate(draws, 1):
        exp = row["experiment"]
        if exp in kept:
            n = kept[exp]
        else:
            hit = [e for e in by.get(exp, []) if e["plan_row"] == row["plan_row"]]
            if not hit:
                die(f"draws.csv row {exp!r} ({row['plan_row']}) is not in S492's registry")
            n = hit[0]["stored"] if hit[0]["counted"] else None
        rows.append([i, DISPLAY.get(exp, exp), design_words(row, man), n])
    total = sum(r[3] for r in rows if r[3] is not None)
    if total != reg["today"]["total_counted"]:
        die(f"the rows add to {total}, S492's total is {reg['today']['total_counted']}")
    return rows, {"anchor": got, "total_counted": total, "not_counted": reg["today"]["not_counted"],
                  "registry_sha256": fig_repro.sha256_file(REGISTRY), "draws_sha256": draws_source_sha256(),
                  "manifest_sha256": fig_repro.sha256_file(MANIFEST)}


def write_t1() -> int:
    rows, info = build_t1()
    check_names(json.dumps(rows))
    OUT.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Answer counts"
    ws.append(T1_HEAD)
    for r in rows:
        ws.append(r)
    ws.append([None, "Total counted", None, info["total_counted"]])
    for c in ws[1]:
        c.font = Font(bold=True)
    provenance(wb, "uv run --frozen python scripts/S534_si_tables.py t1", info)
    x = OUT / "Supplementary Table answer counts.xlsx"
    wb.save(x)
    fig_repro.deterministic_xlsx(x)
    note = (f"Stored answers per experiment, counted from the run records (S492's unit: one generation row, whether or not a "
            f"judge scored it). Provisional: a blank row is not counted yet ({', '.join(info['not_counted']) or 'none'}), and "
            f"counts rise as frozen copies land.")
    md = ["# Supplementary Table answer counts | Answer counts by experiment", "", note, "", "| " + " | ".join(T1_HEAD) + " |",
          "|" + "---|" * len(T1_HEAD)]
    md += ["| " + " | ".join("" if v is None else str(v) for v in r) + " |" for r in rows]
    md += [f"| | Total counted | | {info['total_counted']} |"]
    (OUT / "Supplementary Table answer counts.md").write_text("\n".join(md) + "\n")
    print(f"wrote {rel(x)}: {len(rows)} rows, {info['total_counted']} counted; anchors {info['anchor']}; not counted: "
          f"{', '.join(info['not_counted']) or 'none'}")
    return 0


# ---------------------------------------------------------------------------------------------------------------
# Table 9
# ---------------------------------------------------------------------------------------------------------------
T9_HEAD = ["Experiment", "Records", "Deterministic", "LLM judge", "NLI (MiniCheck)", "Execution", "Retrieval ranking"]
JUDGED = (("Generation strategies", REC / "fig2_inputs/g1_collect.jsonl"),
          ("Matched-budget arm", REC / "fig3_s6_inputs/g2_collect.jsonl"),
          ("Package RLM at caps 5, 10 and 20", REC / "fig3_s6_inputs/g6_collect.jsonl"),
          ("Corpus scaling", REC / "fig3_inputs/g4_collect.jsonl"),
          ("Pipeline ablation and baselines", REC / "fig4_inputs/g3_collect.jsonl"))
CONCEPTS = {"Generation strategies": REC / "L3_d181/concept_recall.jsonl"}
DEPTH = (("Retrieval depth, Mentori RLM and package RLM", REC / "L2_d135_d181/concept_recall.jsonl"),
         ("Retrieval depth, local models", REC / "T1_L2_d181/concept_recall.jsonl"))
JUDGED += (("Flat wide call", REC / "g10_g11_v25_inputs/g10_collect.jsonl"),
           ("Short-passage single pass", REC / "g10_g11_v25_inputs/g11_collect.jsonl"),
           ("Plant-science reuse demonstration", REC / "i2_inputs/judge/judge_passages.jsonl"))
I2_SIGNALS = REC / "i2_inputs/signals"
CONCEPTS["Plant-science reuse demonstration"] = I2_SIGNALS / "concepts.jsonl"
OTHER_SIGNALS = {"Plant-science reuse demonstration": [("numbers", I2_SIGNALS / "numbers.jsonl")]}
# D280: the NLI (MiniCheck) column. Per experiment, (label, files, rows the plan says were written, draws noted or None).
L1_FROZEN = REC / "fig5_d200_inputs/l1"
NLI_SOURCES = {
    "Generation strategies": [("against the answer key", sorted((L1_FROZEN / "key").glob("*.jsonl")), 2430, None),
                              ("against the source papers", sorted((L1_FROZEN / "papers").glob("*.jsonl")), 810,
                               "draw 1 only")],
    "Plant-science reuse demonstration": [("against the answer key", [I2_SIGNALS / "key.jsonl"],
                                           I2_SIGNALS / "key_header.json", None),
                                          ("against the source papers", [I2_SIGNALS / "papers.jsonl"],
                                           I2_SIGNALS / "papers_header.json", None)]}
# rows with no MiniCheck job: plan.csv runs MiniCheck under rows L1 (Figure 2's answers) and I2 only
NLI_NOT_IN_PLAN = "not run: the NLI check was run on the generation-strategy and plant-science answers only"
NLI_NONE = {"Matched-budget arm": NLI_NOT_IN_PLAN, "Package RLM at caps 5, 10 and 20": NLI_NOT_IN_PLAN,
            "Corpus scaling": NLI_NOT_IN_PLAN, "Pipeline ablation and baselines": NLI_NOT_IN_PLAN,
            "Flat wide call": NLI_NOT_IN_PLAN, "Short-passage single pass": NLI_NOT_IN_PLAN,
            "Strategy replication": NLI_NOT_IN_PLAN}   # planned under D83 (Q179), never run
# the paper's names for Table 3's rows (Zhang RLM, RLM: Figure 4's legend); lookups keep the names above
T9_DISPLAY = {"Package RLM at caps 5, 10 and 20": "Zhang RLM at caps 5, 10 and 20",
              "Retrieval depth, Mentori RLM and package RLM": "Retrieval depth, RLM and Zhang RLM"}
T2_GENERATORS = ("claude-haiku-4-5", "gemini-2.5-pro", "gemma3", "qwen3-coder")
T3_SET = REPO / "findings/runs/T3_frozen_20261104T131439Z"
T3_PLANNED = {"Component benchmarks": 6656, "Distiller intervention": 1164}      # draws.csv, design words; S524 THE DESIGN
# each T3 benchmark's signals: (key, column); the rest of a row is the model's own output
T3_SIGNALS = {"analyzer": [("decision_correct", "det"), ("complexity_correct", "det")],
              "planner": [("tool_correct", "det"), ("agent_correct", "det"), ("step_efficiency", "det")],
              "distiller": [("number_retention", "det"), ("source_retention", "det")],
              "supervisor": [("score_valid", "det"), ("_judge_correctness", "judge")],
              "synthesizer": [("judge_scores", "judge")]}
T3_WORDS = {"analyzer": "analyser", "planner": "planner", "distiller": "distiller", "supervisor": "supervisor",
            "synthesizer": "synthesizer", "_judge_correctness": "the judge's score of the reviewed answer"}
T3_UNJUDGED = {"judge_scores": "not judged, by design"}   # T3_runs/README.md, T3-17   # printed when no row holds the key
NOT_READ: tuple = ()


def key_shares(path: Path) -> tuple[int, dict]:
    """(rows, {key: rows holding it}), for each row's judge call a's and b's score keys. Key names only: the row is read as
    a whole by json, and no value of a score is kept or returned."""
    n, have = 0, Counter()
    for ln in path.read_text().splitlines():
        if not ln.strip():
            continue
        n += 1
        r = json.loads(ln)
        for call, label in (("a", "plain call"), ("b", "call with passages")):
            for k in ((r.get(call) or {}).get("scores") or {}):
                have[f"{label}: {k}"] += 1
    return n, have


def share_cell(have: dict, n: int) -> str:
    return "; ".join(f"{k} {100 * v / n:.1f}%" for k, v in sorted(have.items())) or "-"


# Table 9's rows that Table 1 counts under other names
T1_NAMES = {"Generation strategies": ["Generation strategies"], "Matched-budget arm": ["Matched-budget arm"],
            "Plant-science reuse demonstration": ["Plant-science reuse demonstration"],
            "Package RLM at caps 5, 10 and 20": ["Package RLM at caps 5 10 20"], "Corpus scaling": ["Corpus scaling"],
            "Pipeline ablation and baselines": ["Pipeline ablation", "No retrieval and naive RAG"]}


def rows_shares(rows: list[dict]) -> tuple[int, dict]:
    """key_shares on rows already parsed (the same rule: the a and b calls' score key names)."""
    have = Counter()
    for r in rows:
        for call, label in (("a", "plain call"), ("b", "call with passages")):
            for k in ((r.get(call) or {}).get("scores") or {}):
                have[f"{label}: {k}"] += 1
    return len(rows), have


def t2_rows() -> tuple[list[dict], list[Path], dict]:
    """Strategy replication's main-judge rows: per generator of T2_GENERATORS, judge_rows_v25.t2_source first (it
    refuses as its checks refuse), then its v2.5 rows over its v2.4 rows by answer (JP.ident); the rows counted must
    equal t2_source's cells."""
    import judge_rows_v25 as JR
    out, read, per = [], [], {}
    for g in T2_GENERATORS:
        src = JR.t2_source(g)
        sp = JR.T2_SOURCES[g]
        merged = {}
        for key in ("base", "v25"):
            if sp.get(key):
                read.append(Path(sp[key]))
                for d in JR.read_jsonl(Path(sp[key])):
                    merged[JR.JP.ident(d)] = d          # v25 read second, so its row stands
        if len(merged) != src["counts"]["cells"]:
            die(f"T2 {g}: {len(merged)} rows counted, judge_rows_v25.t2_source gives {src['counts']['cells']} cells")
        per[g] = {"rows": len(merged), "reproduced": src["reproduced"]}
        out += list(merged.values())
    return out, read, per


def t3_rows() -> tuple[list[list], list[Path], dict]:
    """Component benchmarks' and Distiller intervention's rows from T3_SET: answers.jsonl held to SHA256SUMS and to
    MANIFEST.json's answers_per_sink, totals to T3_PLANNED. Per signal, the rows whose key holds a value (not null)."""
    sums = {}
    for ln in (T3_SET / "SHA256SUMS").read_text().splitlines():
        h, f = ln.split(None, 1)
        sums[f.strip().lstrip("*")] = h
    man = json.loads((T3_SET / "MANIFEST.json").read_text())
    tot = {"Component benchmarks": Counter(), "Distiller intervention": Counter()}
    have = {"Component benchmarks": Counter(), "Distiller intervention": Counter()}
    read = []
    for sink, n_man in sorted(man["answers_per_sink"].items()):
        f = T3_SET / "sinks" / sink / "answers.jsonl"
        relf = str(f.relative_to(T3_SET))
        if sums.get(relf) != fig_repro.sha256_file(f):
            die(f"T3: {relf} is not the file its SHA256SUMS records")
        read.append(f)
        exp, part = sink.split("__")[:2]
        name = "Component benchmarks" if exp == "exp_04" else "Distiller intervention"
        bench = part if exp == "exp_04" else "distiller"
        n = 0
        for ln in f.read_text().splitlines():
            if not ln.strip():
                continue
            n += 1
            r = json.loads(ln)
            tot[name][bench] += 1
            for k, _ in T3_SIGNALS[bench]:
                if r.get(k) not in (None, "", {}, []):
                    have[name][(bench, k)] += 1
        if n != n_man:
            die(f"T3: {sink} holds {n} rows, MANIFEST.json says {n_man}")
    rows = []
    for name in ("Component benchmarks", "Distiller intervention"):
        n = sum(tot[name].values())
        if n != T3_PLANNED[name]:
            die(f"T3: {name} {n} rows, draws.csv plans {T3_PLANNED[name]}")
        cells = {"det": [], "judge": []}
        for bench in T3_SIGNALS:
            if not tot[name][bench]:
                continue
            for col in cells:
                ks = [(f"{T3_WORDS.get(k, k)} {100 * have[name][(bench, k)] / tot[name][bench]:.1f}%"
                       if have[name][(bench, k)] or k not in T3_UNJUDGED else T3_UNJUDGED[k])
                      for k, c in T3_SIGNALS[bench] if c == col]
                if ks:
                    cells[col].append(f"{T3_WORDS[bench]} ({tot[name][bench]:,}): {', '.join(ks)}")
        rows.append([name, n, "; ".join(cells["det"]) or "-", "; ".join(cells["judge"]) or "-", "-", "-", "-"])
    return rows, read, {k: dict(v) for k, v in tot.items()}


def nli_cell(name: str, records: Path, n: int, read: list) -> str:
    """D280: the NLI (MiniCheck) cell of one experiment. Reproduce first: each source's rows, one per answer_key,
    number what the plan or the source's header says was written, and every answer_key is one of the experiment's
    records (the file its other shares are taken over). Then, per MiniCheck signal, the share of the n records whose
    signal holds a value; key names and nulls only, no score is kept."""
    if name not in NLI_SOURCES:
        return NLI_NONE.get(name, "-")
    keys = {json.loads(ln)["answer_key"] for ln in records.read_text().splitlines() if ln.strip()}
    if len(keys) != n:
        die(f"NLI {name}: {len(keys)} distinct answer keys in {records.name}, {n} records")
    parts = []
    for label, files, want, note in NLI_SOURCES[name]:
        if isinstance(want, Path):
            read.append(want)
            want = json.loads(want.read_text())["counts"]["rows"]
        rows, have = {}, Counter()
        for f in files:
            read.append(f)
            for ln in f.read_text().splitlines():
                if not ln.strip():
                    continue
                r = json.loads(ln)
                k = r["answer_key"]
                if k in rows:
                    die(f"NLI {name} {label}: {k} in two rows ({f.name})")
                if k not in keys:
                    die(f"NLI {name} {label}: {k} is not one of the {n} records of {records.name}")
                rows[k] = 1
                for s, v in (r.get("signals") or {}).items():
                    if v is not None:
                        have[s] += 1
        if len(rows) != want:
            die(f"NLI {name} {label}: {len(rows)} rows, {want} written by its job")
        cell = ", ".join(f"{s} {100 * have[s] / n:.1f}%" for s in sorted(have))
        parts.append(f"{label}{' (' + note + ')' if note else ''}: {cell}")
    return "; ".join(parts)


def build_t9() -> tuple[list[list], dict]:
    rows = []
    read = [REGISTRY, MANIFEST]
    for name, path in JUDGED:
        n, have = key_shares(path)
        read.append(path)
        det = "-"
        if name in CONCEPTS:
            lines = [ln for ln in CONCEPTS[name].read_text().splitlines() if ln.strip()]
            read.append(CONCEPTS[name])
            det = f"concept recall {100 * len(lines) / n:.1f}%"
            for label, sp in OTHER_SIGNALS.get(name, []):
                k = sum(1 for ln in sp.read_text().splitlines() if ln.strip())
                read.append(sp)
                det += f"; {label} {100 * k / n:.1f}%"
        rows.append([name, n, det, share_cell(have, n), nli_cell(name, path, n, read), "-", "-"])
    t2, t2_read, t2_info = t2_rows()
    read += t2_read
    n, have = rows_shares(t2)
    rows.append(["Strategy replication", n, "-", share_cell(have, n), NLI_NONE["Strategy replication"], "-", "-"])
    t3, t3_read, t3_info = t3_rows()
    read += t3_read
    rows += t3
    for name, path in DEPTH:
        lines = [ln for ln in path.read_text().splitlines() if ln.strip()]
        read.append(path)
        n = len(lines)
        c = sum('"concept_recall":' in ln for ln in lines)
        rows.append([name, n, f"concept recall {100 * c / n:.1f}%", "-", "-", "-", "-"])
    man = json.loads(MANIFEST.read_text())
    rows.append(["Code generation", man["attempts_total"], "-", "-", "-", "objective execution of every attempt", "-"])
    reg = json.loads(REGISTRY.read_text())
    rows.append(["Retrieval optimization", sum(reg["anchor"]["kept_parts"]["Retrieval optimisation"].values()), "-", "-", "-", "-",
                 "mean reciprocal rank on every query"])
    rows += [[name, None, "not read", "not read", "not read", "not read", "not read"] for name in NOT_READ]
    stored = {}
    for e in reg["today"]["experiments"]:
        stored.setdefault(e["experiment"], e.get("stored"))
    differ = [(r[0], r[1], sum(stored[x] for x in T1_NAMES[r[0]])) for r in rows if r[0] in T1_NAMES]
    info = {"inputs_sha256": {rel(p): fig_repro.sha256_file(p) for p in read},
            "differ_from_table_1": [d for d in differ if d[1] != d[2]],
            "strategy_replication": t2_info, "t3_rows_by_benchmark": t3_info}
    return rows, info


def write_t9() -> int:
    rows, info = build_t9()
    check_names(json.dumps(rows))
    OUT.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Signals recorded"
    ws.append(T9_HEAD)
    rows = [[T9_DISPLAY.get(r[0], r[0])] + r[1:] for r in rows]   # the paper's names, after every lookup by name
    check_names(json.dumps(rows))
    for r in rows:
        ws.append(r)
    for c in ws[1]:
        c.font = Font(bold=True)
    provenance(wb, "uv run --frozen python scripts/S534_si_tables.py t9", info)
    x = OUT / "Supplementary Table 3.xlsx"      # D276: the manuscript's number
    wb.save(x)
    fig_repro.deterministic_xlsx(x)
    # the stored answers come from S492's registry, as Supplementary Table 2's Records column does (its gate: got == want)
    differ = "; ".join(f"{T9_DISPLAY.get(a, a)}, {b:,} here and {c:,} in Supplementary Table 2"
                       for a, b, c in info["differ_from_table_1"])
    note = ("Share of each experiment's records that hold each signal's key, on the records in the analysis repository. Only key "
            "names are counted, never a value; in the NLI (MiniCheck) column and the component benchmarks a record counts where "
            "the signal holds a value, since MiniCheck stores no value where it does not apply (questions with no answer "
            "in the papers) or could not score the answer. Records is the row count of the file each share is taken over, which can "
            f"differ from the stored answers of Supplementary Table 2{': ' + differ if differ else ''}."
            + (" Provisional: rows marked not read wait for their records." if NOT_READ else ""))
    md = ["# Supplementary Table 3 | Signals recorded per experiment", "", note, "", "| " + " | ".join(T9_HEAD) + " |",
          "|" + "---|" * len(T9_HEAD)]
    md += ["| " + " | ".join("" if v is None else str(v) for v in r) + " |" for r in rows]
    (OUT / "Supplementary Table 3.md").write_text("\n".join(md) + "\n")
    print(f"wrote {rel(x)}: {len(rows)} rows, {sum(r[1] is None for r in rows)} not read yet")
    return 0


def selftest() -> int:
    checks = []

    def ok(name, cond):
        checks.append(bool(cond))
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")
    ok("relation: the identical model is self-judged", relation("qwen3-coder:30b", "qwen3-coder:30b").startswith("self-judged"))
    ok("relation: two qwen models are the same family", relation("qwen3-coder:30b", "qwen3.8:27b") == "same family, different model")
    ok("relation: gemini under devstral is cross-family", relation("gemini-3-flash-preview", "devstral-small-2:24b") == "cross-family")
    ok("relation: no judge", relation("gemma3:27b", None) == "no language-model judge")
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "c.jsonl"
        f.write_text(json.dumps({"a": {"scores": {"correctness": 5}}}) + "\n" + json.dumps({"a": {"scores": {}}}) + "\n")
        n, have = key_shares(f)
        ok("key_shares counts a key's presence, and its row count", n == 2 and have == {"plain call: correctness": 1})
        ok("the share cell prints no value of a score", "5" not in share_cell({"plain call: correctness": 1}, 2).replace("50.0", ""))
        # D280: nli_cell counts a non-null signal, prints no value, and refuses a row that is not one of the records
        rec_f, mc = Path(td) / "r.jsonl", Path(td) / "mc.jsonl"
        rec_f.write_text("".join(json.dumps({"answer_key": k}) + "\n" for k in ("k1", "k2")))
        mc.write_text(json.dumps({"answer_key": "k1", "signals": {"precision": 0.9}}) + "\n"
                      + json.dumps({"answer_key": "k2", "signals": {"precision": None}}) + "\n")
        saved = dict(NLI_SOURCES)
        try:
            NLI_SOURCES["x"] = [("against the answer key", [mc], 2, None)]
            cell = nli_cell("x", rec_f, 2, [])
            ok("nli_cell counts a non-null signal and prints no value", cell == "against the answer key: precision 50.0%")
            mc.write_text(json.dumps({"answer_key": "k9", "signals": {"precision": 0.9}}) + "\n")
            NLI_SOURCES["x"] = [("against the answer key", [mc], 1, None)]
            try:
                nli_cell("x", rec_f, 2, [])
                ok("nli_cell refuses a row that is not one of the records", False)
            except SystemExit:
                ok("nli_cell refuses a row that is not one of the records", True)
        finally:
            NLI_SOURCES.clear()
            NLI_SOURCES.update(saved)
    ok("design_words drops decision codes, nested brackets too",
       design_words({"experiment": "x", "design": "4 generators x 135 (D160 (2): a, b; c out)"}, {}) == "4 generators x 135"
       and design_words({"experiment": "x", "design": "8 set-ups (D52) x 135"}, {}) == "8 set-ups x 135")
    ok("design_words reads code generation from the manifest",
       design_words({"experiment": "Code generation", "design": "16 x 11 x 20"},
                    {"runs": dict.fromkeys(range(121)), "attempts_total": 2420}).startswith("121 "))
    try:
        check_names("Authors' RLM depth caps")
        ok("check_names refuses a form figure_names.py refuses", False)
    except SystemExit:
        ok("check_names refuses a form figure_names.py refuses", True)
    check_names("package RLM; the method's authors")
    print(f"selftest: {sum(checks)} of {len(checks)} checks pass")
    return 0 if all(checks) else 1


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else ""
    if cmd == "t7":
        return write_t7()
    if cmd == "t1":
        return write_t1()
    if cmd == "t9":
        return write_t9()
    if cmd == "selftest":
        return selftest()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
