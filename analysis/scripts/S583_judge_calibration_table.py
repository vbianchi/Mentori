"""S583 - Supplementary Table (judge calibration): how the judge was chosen, in two rounds.

Round 1: 22 candidate judges each scored the same 107 answers (findings/recompute/S376_calibration_analysis.json,
all_answers). Round 2: four of them each scored the same 1,500 answers (findings/recompute/S404/S404_analysis.json,
table_A). For each judge: answers scored, the composite (the mean of three Pearson correlations, each between a judge
score and a measure that needs no judge: correctness with semantic similarity to the expected answer, completeness
with concept recall, citation quality with a citation score) with its 95% bootstrap interval, and the three
correlations. Writes findings/figures_provisional/supp_tables/Supplementary Table 1.{xlsx,md} (J7: O1, 6 Nov).

Reproduces before writing: round 2's composites must give devstral-small-2:24b 0.576 and qwen3.8:27b-mlx 0.628, the
values D8 recorded (notes/DECISIONS_2026-10-13.md:11), or the script stops.

    uv run python scripts/S583_judge_calibration_table.py
"""

import hashlib
import json
import sys
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
R1 = ROOT / "findings/recompute/S376_calibration_analysis.json"
R2 = ROOT / "findings/recompute/S404/S404_analysis.json"
OUT = ROOT / "findings/figures_provisional/supp_tables/Supplementary Table 1"   # the manuscript's number (J7: O1, 6 Nov)
HEAD = ["Round", "Judge", "Answers scored", "Composite", "95% interval", "Correctness against semantic similarity (r)",
        "Completeness against concept recall (r)", "Citation against citation score (r)"]
TITLE = "Supplementary Table 1 | Choosing the judge"
# N4a (proposal): the reader's note; every count in it is read from the two analysis files in main()
NOTE = ("How the judge was chosen, in two rounds (Supplementary Note 2). In round 1, {n1} candidate judges each scored "
        "the same {a1} answers; in round 2, {n2} of them each scored the same {a2:,} answers. Composite: the mean of "
        "three Pearson correlations, each between a judge score and a measure that needs no judge (correctness with "
        "semantic similarity to the expected answer, completeness with concept recall, citation quality with an "
        "automatic citation score). 95% interval: percentile interval over 2,000 bootstrap resamples of the answers. "
        "Judges are named by their Ollama tag; qwen3.8:27b-mlx is the MLX build of qwen3.8:27b (Methods). "
        "Answers scored: answers that received a score, of those sent.")


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rows():
    r1 = json.loads(R1.read_text())["all_answers"]
    r2 = json.loads(R2.read_text())["table_A"]
    if round(r2["devstral-small-2:24b"]["composite"], 3) != 0.576 or round(r2["qwen3.8:27b-mlx"]["composite"], 3) != 0.628:
        sys.exit("S583: round 2 composites do not reproduce D8's 0.576 and 0.628")
    out = []
    for j, v in sorted(r1.items(), key=lambda kv: -kv[1]["composite"]):
        out.append(["1 (107 answers)", j, f"{v['n_scored']} of {v['n_calls']}", round(v["composite"], 3),
                    f"{v['ci95'][0]:.3f} to {v['ci95'][1]:.3f}", round(v["correctness~similarity"], 3),
                    round(v["completeness~concept_recall"], 3), round(v["citation~citation_composite"], 3)])
    for j, v in sorted(r2.items(), key=lambda kv: -kv[1]["composite"]):
        out.append(["2 (1,500 answers)", j, f"{v['n']:,}", round(v["composite"], 3),
                    f"{v['ci95'][0]:.3f} to {v['ci95'][1]:.3f}", round(v["correctness~semantic_similarity"], 3),
                    round(v["completeness~concept_recall"], 3), round(v["citation_quality~cite_composite"], 3)])
    return out


def main():
    body = rows()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Judge calibration"
    ws.append(HEAD)
    for r in body:
        ws.append(r)
    r1 = json.loads(R1.read_text())["all_answers"]
    r2 = json.loads(R2.read_text())["table_A"]
    a1 = {v["n_calls"] for v in r1.values()}
    a2 = {v["n"] for v in r2.values()}
    if len(a1) != 1 or len(a2) != 1:
        sys.exit(f"S583: answers per round {sorted(a1)}, {sorted(a2)}: one count per round expected")
    note = NOTE.format(n1=len(r1), a1=a1.pop(), n2=len(r2), a2=a2.pop())
    pv = wb.create_sheet("Provenance")     # the hashes leave the reader's sheet
    pv.append(["input", "sha256"])
    pv.append([str(R1.relative_to(ROOT)), sha(R1)])
    pv.append([str(R2.relative_to(ROOT)), sha(R2)])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT.with_suffix(".xlsx"))
    md = [f"# {TITLE}", "", note, "", "| " + " | ".join(HEAD) + " |", "|" + "---|" * len(HEAD)]
    md += ["| " + " | ".join(str(c) for c in r) + " |" for r in body]
    OUT.with_suffix(".md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
