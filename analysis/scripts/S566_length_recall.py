#!/usr/bin/env python3
"""S566_length_recall - answer length against concept recall, per question, for Figure 3's six strategies (D220).

WHY. D220 (Valerio, 3 November): does an answer that says more find more of the key's concepts? The method is fixed in
experiments/README.md (D220) before this runs; this script implements that text and nothing more. Descriptive, no test.

THE DATA.
  answers  the generation records Figure 3 reads, through S463's own reader and rerun choice: S463.read_answers() on
           frozen k1_inputs_runs (its committed members list as manifest), then frozen fig2_g1r15_inputs/runs (the 15
           reruns of 18 October replace K1's record of the same key), exactly the call S463.rebuild() makes. Each answers
           file read must carry the sha256 the committed figure3_provenance.json records for it, or the run is refused.
  words    whitespace tokens of the record's answer text (len(answer.split())); an answer whose S463 status is not
           "ok" (a generation error or no text) counts 0 words and is also listed apart with its own token count.
  recall   per question, Source Data Fig. 3, sheet Fig. 3a, rows 'concept recall (not drawn): question (grey dot)',
           column concept_recall_question_pct (each question the mean of its draws, as that sheet gives it), read from
           the workbook as committed at HEAD (git show).
  set      the 86 answerable questions of the D5 key (S463.key_groups()), the six strategies, draws 1 to 3.

WHAT IS COMPUTED. Per strategy and question, words = the mean over draws 1 to 3; per strategy, the median and the mean of
those over the 86 questions. Primary: per question, RLM-10 minus single pass in words and in concept recall
(percentage points); Pearson r between the two differences, with a two-sided 95% percentile interval over 10,000
question resamples (S457.boot_matrix: seed 20261013, Rule 2's matrix). Secondary: the same for RLM-5 and RLM-20.

REPRODUCE FIRST (README.md:75-79). Refused, nothing written, unless
  (1) per strategy, the mean over the 86 questions of the sheet's per-question concept recall equals the sheet's own
      'concept recall (not drawn): strategy' row (concept_recall_pct), within 1e-8 percentage points (the sheet rounds
      each value to 9 decimals);
  (2) RLM-10's draw-1 whitespace token count of every answer equals Figure 4's words sheet (Source Data Fig. 4, sheet
      Fig. 4d, rows 'answer', config rlm_10; an empty cell means no text, 0 tokens) as committed at 698b22c6, read with
      git show (D219 removes that sheet); all 135 questions, exactly.

OUTPUTS, findings/recompute/S566_length_recall/: results.json (provenance first), per_question.csv (a provenance line
first), README.md. No model call, no network.

    uv run python scripts/S566_length_recall.py
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
import S463_fig2_ranking as S463  # noqa: E402  (Figure 3's reader of the answer records; read, never edited here)

S457 = S463.S457
FR = S463.FR
SCRIPT = "scripts/S566_length_recall.py"
OUT = ROOT / "findings" / "recompute" / "S566_length_recall"
CONFIGS = list(S463.CONFIGS)                     # single_pass, multi_hop, verified_pass, rlm_5, rlm_10, rlm_20
LABEL = dict(S463.LABEL)
DRAWS = (1, 2, 3)
BASE = "single_pass"
PRIMARY = "rlm_10"
SECONDARY = ("rlm_5", "rlm_20")
FIG3_DIR = "findings/figures_provisional/fig3_strategies"
FIG3_PROV = ROOT / FIG3_DIR / "figure3_provenance.json"
FIG4_COMMIT = "698b22c6"
FIG4_PATH = "findings/figures_provisional/fig4/Source Data Fig. 4 (provisional, 1485 of 3015).xlsx"
CR_Q_ROW = "concept recall (not drawn): question (grey dot)"
CR_S_ROW = "concept recall (not drawn): strategy"
CR_TOL = 1e-8                                    # percentage points; the sheet rounds each value to 9 decimals


class Refused(SystemExit):
    pass


def git(*a, binary=False):
    r = subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True)
    if r.returncode:
        raise Refused(f"git {' '.join(a)}: {r.stderr.decode().strip()}")
    return r.stdout if binary else r.stdout.decode().strip()


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sheet_rows(xlsx: bytes, sheet: str) -> list[dict]:
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(xlsx), read_only=True)
    if sheet not in wb.sheetnames:
        raise Refused(f"no sheet {sheet!r} in the workbook ({wb.sheetnames})")
    rows = list(wb[sheet].iter_rows(values_only=True))
    head = rows[0]
    return [dict(zip(head, r)) for r in rows[1:]]


# ---------------------------------------------------------------------------------------------------------------
# reading
# ---------------------------------------------------------------------------------------------------------------
def read_records():
    """S463.read_answers on the frozen inputs S463.rebuild() passes it; each file held to Figure 3's provenance."""
    k1 = FR.frozen("k1_inputs_runs", "k1_inputs_runs")
    g1r15 = FR.frozen("fig2_g1r15_inputs", "fig2_g1r15_inputs")
    members = FR.RECOMPUTE / "frozen_inputs" / "members" / "k1_inputs_runs.sha256"
    k1_man = {}
    for ln in members.read_text().splitlines():
        if ln.strip():
            h, n = ln.split(None, 1)
            k1_man["runs/" + n.strip().split("/", 1)[1]] = h
    answers, inputs, _ = S463.read_answers([k1, g1r15 / "runs"], {str(k1): k1_man})
    recorded = json.loads(FIG3_PROV.read_text())["provenance"]["inputs_sha256"]
    labelled = {}
    for p, h in inputs.items():
        lab = FR.frozen_label(p)
        if recorded.get(lab) != h:
            raise Refused(f"{lab}: sha256 {h[:12]} is not the one figure3_provenance.json records "
                          f"({str(recorded.get(lab))[:12]}): not the records Figure 3 reads")
        labelled[lab] = h
    labelled[str(members.relative_to(ROOT))] = FR.sha256_file(members)
    return answers, labelled


def words_of(rec: dict) -> dict:
    """Whitespace tokens of the answer text; a record whose status is not "ok" counts 0 words (D220)."""
    tokens = len((rec.get("answer") or "").split())
    failed = rec["status"] != "ok"
    return {"tokens": tokens, "words": 0 if failed else tokens, "failed": failed, "status": rec["status"]}


def read_concept_recall(rows: list[dict]) -> tuple[dict, dict]:
    """({(strategy, question): pct}, {strategy: sheet mean pct}) from sheet Fig. 3a."""
    per, means = {}, {}
    for r in rows:
        if r["row_kind"] == CR_Q_ROW:
            k = (r["strategy"], r["question_id"])
            if k in per:
                raise Refused(f"sheet Fig. 3a: two '{CR_Q_ROW}' rows for {k}")
            if r["concept_recall_question_pct"] is None:
                raise Refused(f"sheet Fig. 3a: {k} has no concept_recall_question_pct")
            per[k] = float(r["concept_recall_question_pct"])
        elif r["row_kind"] == CR_S_ROW:
            means[r["strategy"]] = float(r["concept_recall_pct"])
    return per, means


# ---------------------------------------------------------------------------------------------------------------
# reproduce first
# ---------------------------------------------------------------------------------------------------------------
def gate_concept_recall(per: dict, means: dict, qa: list[str]) -> dict:
    out = {}
    for c in CONFIGS:
        qs = sorted(q for (s, q) in per if s == c)
        if qs != sorted(qa):
            raise Refused(f"gate (1): sheet Fig. 3a gives {len(qs)} questions for {c}, not the 86 answerable ones")
        if c not in means:
            raise Refused(f"gate (1): sheet Fig. 3a has no '{CR_S_ROW}' row for {c}")
        got = sum(per[(c, q)] for q in qa) / len(qa)
        if abs(got - means[c]) > CR_TOL:
            raise Refused(f"gate (1): {c}: mean of the sheet's per-question concept recall {got!r} is not the sheet's "
                          f"{means[c]!r}; nothing written")
        out[c] = {"computed_pct": got, "sheet_pct": means[c], "abs_diff": abs(got - means[c])}
    if set(s for s, _ in per) != set(CONFIGS):
        raise Refused(f"gate (1): sheet Fig. 3a names strategies {sorted(set(s for s, _ in per))}")
    return out


def gate_words(fig4: list[dict], answers: dict, n_q: int) -> dict:
    rows = [r for r in fig4 if r["row"] == "answer" and r["config"] == PRIMARY]
    if len(rows) != n_q:
        raise Refused(f"gate (2): Figure 4's words sheet has {len(rows)} RLM-10 answers, want {n_q}")
    bad = []
    for r in rows:
        k = r["answer_key"]
        if not k.endswith("|d1") or k not in answers:
            bad.append(f"{k}: not a draw-1 key read here")
            continue
        want = 0 if r["value"] is None else int(r["value"])
        got = words_of(answers[k])["tokens"]
        if got != want:
            bad.append(f"{k}: {got} tokens here, {want} in Figure 4's sheet")
    if bad:
        raise Refused(f"gate (2): {len(bad)} of {len(rows)} RLM-10 draw-1 answers differ; first: {bad[0]}; nothing "
                      f"written")
    return {"answers_compared": len(rows), "equal": len(rows),
            "empty_cells_as_0": sum(1 for r in rows if r["value"] is None)}


# ---------------------------------------------------------------------------------------------------------------
# computing
# ---------------------------------------------------------------------------------------------------------------
def pearson(x, y) -> float:
    x, y = np.asarray(x, float), np.asarray(y, float)
    dx, dy = x - x.mean(), y - y.mean()
    den = math.sqrt(float((dx * dx).sum()) * float((dy * dy).sum()))
    return float("nan") if den == 0 else float((dx * dy).sum()) / den


def r_with_interval(x, y, boot) -> dict:
    x, y = np.asarray(x, float), np.asarray(y, float)
    X, Y = x[boot], y[boot]
    dx, dy = X - X.mean(axis=1, keepdims=True), Y - Y.mean(axis=1, keepdims=True)
    flat = (X.max(axis=1) == X.min(axis=1)) | (Y.max(axis=1) == Y.min(axis=1))
    if flat.any():
        raise Refused(f"{int(flat.sum())} resamples have no spread: r undefined there")
    den = np.sqrt((dx * dx).sum(axis=1) * (dy * dy).sum(axis=1))
    rs = (dx * dy).sum(axis=1) / den
    return {"r": pearson(x, y), "ci95_lo": float(np.percentile(rs, 2.5)), "ci95_hi": float(np.percentile(rs, 97.5)),
            "resamples": int(boot.shape[0]), "questions": int(len(x))}


def compute(answers: dict, per_cr: dict, qa: list[str]) -> dict:
    words, failed = {}, {c: [] for c in CONFIGS}
    for c in CONFIGS:
        for q in qa:
            ws = []
            for d in DRAWS:
                k = f"{S463.INDEX}|{c}|{q}|d{d}"
                if k not in answers:
                    raise Refused(f"{k}: no record")
                w = words_of(answers[k])
                ws.append(w["words"])
                if w["failed"]:
                    failed[c].append({"answer_key": k, "status": w["status"], "tokens_in_text": w["tokens"]})
            words[(c, q)] = sum(ws) / len(ws)
    per_strategy = {}
    for c in CONFIGS:
        v = np.array([words[(c, q)] for q in qa])
        per_strategy[c] = {"label": LABEL[c], "questions": len(qa), "median_words": float(np.median(v)),
                           "mean_words": float(v.mean()), "failed_answers_counted_0": len(failed[c]),
                           "failed_answers": failed[c]}
    boot = S457.boot_matrix(len(qa))
    pairs = {}
    for c in (PRIMARY, *SECONDARY):
        dw = [words[(c, q)] - words[(BASE, q)] for q in qa]
        dc = [per_cr[(c, q)] - per_cr[(BASE, q)] for q in qa]
        pairs[c] = {"role": "primary" if c == PRIMARY else "secondary",
                    "contrast": f"{LABEL[c]} minus {LABEL[BASE]}", **r_with_interval(dw, dc, boot),
                    "mean_words_difference": float(np.mean(dw)), "mean_recall_difference_pp": float(np.mean(dc))}
    return {"words": words, "per_strategy": per_strategy, "pearson": pairs}


# ---------------------------------------------------------------------------------------------------------------
# writing
# ---------------------------------------------------------------------------------------------------------------
def fmt(x, nd=1):
    return f"{x:.{nd}f}"


def write(out: Path, prov: dict, gates: dict, res: dict, per_cr: dict, qa: list[str]):
    out.mkdir(parents=True, exist_ok=True)
    body = {"_provenance": prov, "gates": gates, "per_strategy": res["per_strategy"], "pearson": res["pearson"]}
    (out / "results.json").write_text(json.dumps(body, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    buf = io.StringIO()
    buf.write(f"# provenance: {SCRIPT} sha256 {prov['script_sha256'][:12]}, git head {prov['git_head'][:10]}, "
              f"{prov['written_utc']}; see results.json\n")
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["question_id", *[f"words_{c}" for c in CONFIGS], *[f"concept_recall_pct_{c}" for c in CONFIGS]])
    for q in qa:
        w.writerow([q, *[repr(res["words"][(c, q)]) for c in CONFIGS], *[repr(per_cr[(c, q)]) for c in CONFIGS]])
    (out / "per_question.csv").write_text(buf.getvalue(), encoding="utf-8")
    ps, pr = res["per_strategy"], res["pearson"]
    L = ["# S566: answer length against concept recall (D220)", "",
         f"Generated by `{prov['command']}` at {prov['written_utc']}, git head {prov['git_head'][:10]}, script sha256 "
         f"{prov['script_sha256'][:12]}.", "",
         "## What it measures", "",
         "For each of Figure 3's six strategies, on the 86 answerable questions and draws 1 to 3, the script counts the "
         "words of each answer (whitespace tokens of the answer text) in the generation records Figure 3 reads (S463's "
         "reader, with the 15 reruns of 18 October in place of the first records). An answer that failed (a generation "
         "error or no text) counts 0 words and is listed apart in results.json. Each question's words are the mean over "
         "its three draws. Each question's concept recall is copied from Source Data Fig. 3, sheet Fig. 3a, rows "
         f"'{CR_Q_ROW}'.", "",
         "Per question it takes RLM-10 minus single pass in words and in concept recall, and gives Pearson r between "
         "the two differences with a two-sided 95% percentile interval over 10,000 resamples of the questions (seed "
         "20261013). RLM-5 and RLM-20 against single pass are the secondary rows. It runs no test.", "",
         "## Words per answer", "", "| strategy | median words | mean words | failed answers (counted 0) |",
         "|---|---:|---:|---:|"]
    for c in CONFIGS:
        L.append(f"| {LABEL[c]} | {fmt(ps[c]['median_words'])} | {fmt(ps[c]['mean_words'])} | "
                 f"{ps[c]['failed_answers_counted_0']} |")
    L += ["", "## Words difference against concept recall difference", "",
          "| contrast | role | r | 95% interval | questions |", "|---|---|---:|---|---:|"]
    for c, v in pr.items():
        L.append(f"| {v['contrast']} | {v['role']} | {fmt(v['r'], 3)} | {fmt(v['ci95_lo'], 3)} to {fmt(v['ci95_hi'], 3)} "
                 f"| {v['questions']} |")
    g1, g2 = gates["concept_recall_means"], gates["rlm10_draw1_words"]
    L += ["", "## Reproduced before writing", "",
          f"1. The mean over the 86 questions of the sheet's per-question concept recall equals the sheet's own strategy "
          f"row for all six strategies (largest difference {max(v['abs_diff'] for v in g1.values()):.1e} percentage "
          f"points, tolerance {CR_TOL:g}).",
          f"2. RLM-10's draw-1 word count equals Figure 4's words sheet (Fig. 4d) at {FIG4_COMMIT} for "
          f"{g2['equal']} of {g2['answers_compared']} answers.",
          f"3. Every answers file read has the sha256 Figure 3's provenance file records.", ""]
    (out / "README.md").write_text("\n".join(L), encoding="utf-8")


def main() -> int:
    groups = S463.key_groups()
    qa = sorted(q for q, g in groups.items() if g == "answerable")
    if len(qa) != 86:
        raise Refused(f"{len(qa)} answerable questions, want 86")
    answers, inputs = read_records()
    fig3_rel = [p for p in git("ls-files", FIG3_DIR).splitlines() if Path(p).name.startswith("Source Data Fig. 3 (")
                and p.endswith(".xlsx")]
    if len(fig3_rel) != 1:
        raise Refused(f"{len(fig3_rel)} committed Source Data Fig. 3 workbooks, want 1")
    fig3_b = git("show", f"HEAD:{fig3_rel[0]}", binary=True)
    fig3_commit = git("log", "-1", "--format=%H", "--", fig3_rel[0])
    fig4_b = git("show", f"{FIG4_COMMIT}:{FIG4_PATH}", binary=True)
    per_cr, cr_means = read_concept_recall(sheet_rows(fig3_b, "Fig. 3a"))
    gates = {"concept_recall_means": gate_concept_recall(per_cr, cr_means, qa),
             "rlm10_draw1_words": gate_words(sheet_rows(fig4_b, "Fig. 4d"), answers, len(groups)),
             "answers_files_equal_figure3_provenance": len([k for k in inputs if k.endswith("answers.jsonl")])}
    res = compute(answers, per_cr, qa)
    me = ROOT / SCRIPT
    prov = {"script": SCRIPT, "script_sha256": sha(me.read_bytes()), "command": f"uv run python {SCRIPT}",
            "git_head": git("rev-parse", "HEAD"), "written_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "method": "experiments/README.md D220",
            "reader": {"function": "S463_fig2_ranking.read_answers", "sha256": sha((ROOT / "scripts" / "S463_fig2_ranking.py").read_bytes()),
                       "S457_sha256": sha((ROOT / "scripts" / "S457_fig2_panels.py").read_bytes()),
                       "S463_differs_from_head": bool(git("status", "--porcelain", "scripts/S463_fig2_ranking.py"))},
            "inputs_sha256": inputs,
            "concept_recall": {"workbook": fig3_rel[0], "read_at": "HEAD", "last_commit": fig3_commit,
                               "sha256": sha(fig3_b), "sheet": "Fig. 3a", "rows": CR_Q_ROW,
                               "column": "concept_recall_question_pct"},
            "figure4_words": {"workbook": FIG4_PATH, "commit": git("rev-parse", FIG4_COMMIT), "sha256": sha(fig4_b),
                              "sheet": "Fig. 4d", "rows": "answer, config rlm_10", "read_with": "git show"},
            "words": "len(generation.answer.split()); 0 where S463 status is not ok", "draws": list(DRAWS),
            "resamples": int(S457.N_BOOT), "seed": int(S457.BOOT_SEED), "interval": "two-sided 95% percentile"}
    write(OUT, prov, gates, res, per_cr, qa)
    ps, pr = res["per_strategy"], res["pearson"]
    for c in CONFIGS:
        print(f"{LABEL[c]:14s} median {ps[c]['median_words']:8.1f}  mean {ps[c]['mean_words']:8.1f}  failed "
              f"{ps[c]['failed_answers_counted_0']}")
    for c, v in pr.items():
        print(f"{v['contrast']:28s} r {v['r']:.3f} [{v['ci95_lo']:.3f}, {v['ci95_hi']:.3f}] ({v['role']})")
    print(f"gates: (1) concept recall means 6/6 equal; (2) RLM-10 d1 words {gates['rlm10_draw1_words']['equal']}/"
          f"{gates['rlm10_draw1_words']['answers_compared']} equal; answers files = Figure 3 provenance "
          f"({gates['answers_files_equal_figure3_provenance']})")
    print(f"wrote {OUT.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
