#!/usr/bin/env python3
"""
Post-hoc Analysis: V2-1 (Embedding), V2-2 (Search), V2-3 (Chunking + Scalability)

Reads existing V1 experiment results and reformats them into the V2 narrative.
No experiments are re-run — this is purely reformatting.

Outputs:
  results_v2/v2_1_embedding.md
  results_v2/v2_2_search.md
  results_v2/v2_3_chunking_scale.md

Usage:
    uv run python tests/experiments_v2/analyze_retrieval.py
    uv run python tests/experiments_v2/analyze_retrieval.py --only v2_1
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.experiments_v2.exp_v2_common import (
    V1_RESULTS,
    V2_RESULTS_DIR,
    format_v2_table,
    save_v2_markdown,
)

# ─────────────────────────────────────────────────────────────
# V2-1: Embedding Model Selection
# ─────────────────────────────────────────────────────────────

EXP2_FILE = "exp2_results_20260211_174232.json"

def analyze_v2_1() -> str:
    """Reformat exp2 (embedding comparison) into V2-1 narrative."""
    data = _load(EXP2_FILE)
    config = data["config"]
    results = data["results"]

    lines = [
        "# V2-1: Embedding Model Selection",
        "",
        "**Question**: Which embedding model retrieves the most relevant scientific chunks?",
        "",
        f"**Design**: {len(config['models'])} models x {len(config['corpus_sizes'])} corpus sizes x {config['n_queries']} queries. Dense-only retrieval.",
        "",
        "**Models**: " + ", ".join(config["models"]),
        "",
        "**Corpus sizes**: " + ", ".join(str(s) for s in config["corpus_sizes"]),
        "",
    ]

    # Summary table: MRR by model × corpus size
    headers = ["Model"] + [f"s{s}" for s in config["corpus_sizes"]]
    rows = []

    models = config["models"]
    for model in models:
        row = [model]
        for cs in config["corpus_sizes"]:
            # Find matching result
            match = [r for r in results if r["model"] == model and r["corpus_size"] == cs]
            if match:
                mrr = match[0]["overall"]["MRR"]
                row.append(f"{mrr:.3f}")
            else:
                row.append("-")
        rows.append(row)

    lines.append("## MRR by Model and Corpus Size")
    lines.append("")
    lines.append(format_v2_table(headers, rows, ["l"] + ["r"] * len(config["corpus_sizes"])))
    lines.append("")

    # Detailed table at largest corpus size
    max_cs = max(config["corpus_sizes"])
    lines.append(f"## Detailed Metrics at {max_cs} Papers")
    lines.append("")

    detail_headers = ["Model", "MRR", "P@5", "P@10", "nDCG@10", "R@10"]
    detail_rows = []
    for model in models:
        match = [r for r in results if r["model"] == model and r["corpus_size"] == max_cs]
        if match:
            o = match[0]["overall"]
            detail_rows.append([
                model,
                f"{o['MRR']:.3f}",
                f"{o['P@5']:.3f}",
                f"{o['P@10']:.3f}",
                f"{o['nDCG@10']:.3f}",
                f"{o['R@10']:.3f}",
            ])

    lines.append(format_v2_table(detail_headers, detail_rows, ["l"] + ["r"] * 5))
    lines.append("")

    # Category breakdown at max corpus size for best model
    best_model = max(
        models,
        key=lambda m: next(
            (r["overall"]["MRR"] for r in results if r["model"] == m and r["corpus_size"] == max_cs),
            0
        )
    )
    best_result = [r for r in results if r["model"] == best_model and r["corpus_size"] == max_cs][0]

    lines.append(f"## Category Breakdown ({best_model} at {max_cs} papers)")
    lines.append("")

    cat_headers = ["Category", "MRR", "P@5", "P@10", "nDCG@10"]
    cat_rows = []
    for cat, metrics in sorted(best_result.get("by_category", {}).items()):
        cat_rows.append([
            cat,
            f"{metrics.get('MRR', 0):.3f}",
            f"{metrics.get('P@5', 0):.3f}",
            f"{metrics.get('P@10', 0):.3f}",
            f"{metrics.get('nDCG@10', 0):.3f}",
        ])

    lines.append(format_v2_table(cat_headers, cat_rows, ["l"] + ["r"] * 4))
    lines.append("")

    # Conclusion
    lines.append("## Conclusion")
    lines.append("")
    lines.append(f"**{best_model}** wins decisively with MRR={best_result['overall']['MRR']:.3f} at {max_cs} papers.")
    lines.append("")
    lines.append(f"**Data source**: `results/{EXP2_FILE}`")
    lines.append("")
    lines.append("**Bridge**: BGE-M3 is our embedding model. Next: does adding BM25 help?")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# V2-2: Search Strategy Ablation
# ─────────────────────────────────────────────────────────────

EXP3_FILE = "exp3_results_20260211_180248.json"

def analyze_v2_2() -> str:
    """Reformat exp3 (hybrid search ablation) into V2-2 narrative."""
    data = _load(EXP3_FILE)
    config = data["config"]
    results = data["results"]

    lines = [
        "# V2-2: Search Strategy Ablation",
        "",
        "**Question**: Does hybrid search outperform dense-only or BM25-only?",
        "",
        f"**Design**: {len(config['configs_tested'])} search configs x {len(config['corpus_sizes'])} corpus sizes x {config['n_queries']} queries. Fixed embedding: {config['embedding_model']}.",
        "",
        "**Configs**: " + ", ".join(config["configs_tested"]),
        "",
    ]

    # Summary table: MRR by config × corpus size
    headers = ["Config"] + [f"s{s}" for s in config["corpus_sizes"]]
    rows = []

    for cfg in config["configs_tested"]:
        row = [cfg]
        for cs in config["corpus_sizes"]:
            match = [r for r in results if r["config"] == cfg and r["corpus_size"] == cs]
            if match:
                mrr = match[0]["overall"]["MRR"]
                row.append(f"{mrr:.3f}")
            else:
                row.append("-")
        rows.append(row)

    lines.append("## MRR by Search Config and Corpus Size")
    lines.append("")
    lines.append(format_v2_table(headers, rows, ["l"] + ["r"] * len(config["corpus_sizes"])))
    lines.append("")

    # Detailed table at largest corpus size
    max_cs = max(config["corpus_sizes"])
    lines.append(f"## Detailed Metrics at {max_cs} Papers")
    lines.append("")

    detail_headers = ["Config", "MRR", "P@5", "P@10", "nDCG@10", "R@10", "R@20"]
    detail_rows = []
    for cfg in config["configs_tested"]:
        match = [r for r in results if r["config"] == cfg and r["corpus_size"] == max_cs]
        if match:
            o = match[0]["overall"]
            detail_rows.append([
                cfg,
                f"{o['MRR']:.3f}",
                f"{o.get('P@5', 0):.3f}",
                f"{o.get('P@10', 0):.3f}",
                f"{o.get('nDCG@10', 0):.3f}",
                f"{o.get('R@10', 0):.3f}",
                f"{o.get('R@20', 0):.3f}",
            ])

    lines.append(format_v2_table(detail_headers, detail_rows, ["l"] + ["r"] * 6))
    lines.append("")

    # Find winner
    best_cfg = max(
        config["configs_tested"],
        key=lambda c: next(
            (r["overall"]["MRR"] for r in results if r["config"] == c and r["corpus_size"] == max_cs),
            0
        )
    )
    best_mrr = next(
        r["overall"]["MRR"] for r in results if r["config"] == best_cfg and r["corpus_size"] == max_cs
    )

    lines.append("## Conclusion")
    lines.append("")
    lines.append(f"**{best_cfg}** achieves MRR={best_mrr:.3f} at {max_cs} papers.")
    lines.append("Scientific tokenizer helps for technical terms (CRISPR-Cas9, H2O2).")
    lines.append("")
    lines.append(f"**Data source**: `results/{EXP3_FILE}`")
    lines.append("")
    lines.append("**Bridge**: RRF + scientific tokenizer wins. What about chunk size?")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# V2-3: Chunking Strategy + Retrieval Scalability
# ─────────────────────────────────────────────────────────────

EXP3B_FILE = "exp3b_chunking_20260213_142928.json"
EXP3C_FILE = "exp3c_results_20260216_090601.json"

def analyze_v2_3() -> str:
    """Reformat exp3b (chunking) + exp3c (scalability) into V2-3 narrative."""
    data_3b = _load(EXP3B_FILE)
    data_3c = _load(EXP3C_FILE)

    lines = [
        "# V2-3: Chunking Strategy + Retrieval Scalability",
        "",
        "## Part A: Chunking Strategy Comparison",
        "",
        "**Question**: What chunk size works best for scientific document retrieval?",
        "",
    ]

    config_3b = data_3b["config"]
    results_3b = data_3b["results"]
    chunk_stats = data_3b.get("chunk_stats", [])

    lines.append(f"**Design**: {len(config_3b['configs_tested'])} chunking configs x {len(config_3b['runs'])} runs x queries at {config_3b['corpus_size']} papers.")
    lines.append(f"**Fixed**: embedding={config_3b['model']}, search={config_3b['search']}")
    lines.append("")

    # Chunk statistics table
    if chunk_stats:
        lines.append("### Chunk Statistics")
        lines.append("")
        cs_headers = ["Config", "Total Chunks", "Avg Tokens", "Min", "Max", "Std"]
        cs_rows = []
        # chunk_stats can be a dict {config_name: stats_dict} or a list
        if isinstance(chunk_stats, dict):
            items = [(k, v) for k, v in chunk_stats.items()]
        else:
            items = [(cs.get("config", "?"), cs) for cs in chunk_stats]
        for cfg_name, cs in items:
            cs_rows.append([
                cfg_name,
                str(cs.get("total_chunks", 0)),
                f"{cs.get('avg_tokens_per_chunk', 0):.0f}",
                str(cs.get("min_tokens", 0)),
                str(cs.get("max_tokens", 0)),
                f"{cs.get('std_tokens', 0):.0f}",
            ])
        lines.append(format_v2_table(cs_headers, cs_rows, ["l"] + ["r"] * 5))
        lines.append("")

    # Average MRR across runs for each chunking config
    from collections import defaultdict
    import statistics

    config_mrrs = defaultdict(list)
    config_metrics = defaultdict(lambda: defaultdict(list))

    for r in results_3b:
        cfg = r["config"]
        overall = r["overall"]
        config_mrrs[cfg].append(overall["MRR"])
        for metric_key in ["P@5", "P@10", "nDCG@10", "R@10"]:
            if metric_key in overall:
                config_metrics[cfg][metric_key].append(overall[metric_key])

    lines.append("### Retrieval Quality (averaged across runs)")
    lines.append("")

    mrr_headers = ["Config", "MRR (mean)", "MRR (std)", "P@5", "P@10", "nDCG@10"]
    mrr_rows = []
    for cfg in config_3b["configs_tested"]:
        if cfg not in config_mrrs:
            continue
        vals = config_mrrs[cfg]
        mrr_mean = statistics.mean(vals)
        mrr_std = statistics.stdev(vals) if len(vals) > 1 else 0

        row = [
            cfg,
            f"{mrr_mean:.3f}",
            f"{mrr_std:.3f}",
        ]
        for mk in ["P@5", "P@10", "nDCG@10"]:
            mv = config_metrics[cfg].get(mk, [])
            row.append(f"{statistics.mean(mv):.3f}" if mv else "-")
        mrr_rows.append(row)

    # Sort by MRR descending
    mrr_rows.sort(key=lambda r: float(r[1]), reverse=True)
    lines.append(format_v2_table(mrr_headers, mrr_rows, ["l"] + ["r"] * 5))
    lines.append("")

    # Part B: Scalability
    lines.append("## Part B: Retrieval Scalability")
    lines.append("")
    lines.append("**Question**: Does retrieval hold as corpus grows to 100 papers?")
    lines.append("")

    config_3c = data_3c["config"]
    results_3c = data_3c["results"]

    lines.append(f"**Design**: BGE-M3 + RRF + Simple(512,50) across {', '.join(str(s) for s in config_3c['corpus_sizes'])} papers.")
    lines.append("")

    # Scale table
    scale_headers = ["Corpus Size", "Index", "MRR", "P@5", "P@10", "nDCG@10", "R@10"]
    scale_rows = []
    for r in results_3c:
        o = r["overall"]
        scale_rows.append([
            str(r["corpus_size"]),
            r["index_name"],
            f"{o['MRR']:.3f}",
            f"{o.get('P@5', 0):.3f}",
            f"{o.get('P@10', 0):.3f}",
            f"{o.get('nDCG@10', 0):.3f}",
            f"{o.get('R@10', 0):.3f}",
        ])

    lines.append(format_v2_table(scale_headers, scale_rows, ["l", "l"] + ["r"] * 5))
    lines.append("")

    # Latency table
    has_timing = any("timing" in r for r in results_3c)
    if has_timing:
        lines.append("### Query Latency by Corpus Size")
        lines.append("")
        lat_headers = ["Corpus Size", "Median (ms)", "Mean (ms)", "P95 (ms)"]
        lat_rows = []
        for r in results_3c:
            t = r.get("timing", {})
            lat_rows.append([
                str(r["corpus_size"]),
                f"{t.get('median_query_latency_ms', 0):.0f}",
                f"{t.get('mean_query_latency_ms', 0):.0f}",
                f"{t.get('p95_query_latency_ms', 0):.0f}",
            ])
        lines.append(format_v2_table(lat_headers, lat_rows, ["l"] + ["r"] * 3))
        lines.append("")

    # Conclusion
    best_chunking = mrr_rows[0][0] if mrr_rows else "simple_512"
    lines.append("## Conclusion")
    lines.append("")
    lines.append(f"**Chunking**: {best_chunking} wins. Semantic chunking creates too many tiny fragments.")
    lines.append("**Scalability**: MRR stays high through ~50 papers, slight drop at 100. Retrieval is not the bottleneck.")
    lines.append("")
    lines.append(f"**Data sources**: `results/{EXP3B_FILE}`, `results/{EXP3C_FILE}`")
    lines.append("")
    lines.append("**Bridge**: Our retrieval pipeline (BGE-M3 + RRF + 512-token chunks) is solid through 100 papers. Now: how well do different generation strategies USE these retrieved passages?")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _load(filename: str) -> dict:
    """Load a V1 result file."""
    path = V1_RESULTS / filename
    if not path.exists():
        print(f"ERROR: Result file not found: {path}")
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Post-hoc analysis of retrieval experiments (V2-1/2/3)")
    parser.add_argument(
        "--only",
        choices=["v2_1", "v2_2", "v2_3"],
        help="Only run one analysis",
    )
    args = parser.parse_args()

    V2_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    analyses = {
        "v2_1": ("V2-1: Embedding Model Selection", analyze_v2_1, "v2_1_embedding"),
        "v2_2": ("V2-2: Search Strategy Ablation", analyze_v2_2, "v2_2_search"),
        "v2_3": ("V2-3: Chunking + Scalability", analyze_v2_3, "v2_3_chunking_scale"),
    }

    targets = [args.only] if args.only else list(analyses.keys())

    for key in targets:
        title, func, prefix = analyses[key]
        print(f"\nAnalyzing {title}...")
        try:
            content = func()
            md_path = save_v2_markdown(content, prefix)
            print(f"  Saved: {md_path}")
        except FileNotFoundError as e:
            print(f"  SKIPPED: {e}")
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()

    print("\nDone.")


if __name__ == "__main__":
    main()
