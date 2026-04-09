# publication/results/

This directory holds the **raw evaluation outputs** from all ten experiments (V4-0 through V4-9) — the JSON inputs that `publication/reports/paper_figures.Rmd` reads to regenerate every figure in the paper.

The actual files are **not bundled in the Git repository** because they total ~200 MB uncompressed (47 MB as a gzipped tarball, across 553 files). They are deposited at Zenodo:

> **Bianchi, V. & Schokker, D.** *Mentori — code, data, and supplementary materials for "Systematic Ablation Reveals Hidden Failures in Multi-Agent AI for Science"*. Zenodo (2026).
> DOI: [10.5281/zenodo.19476756](https://doi.org/10.5281/zenodo.19476756)

## How to populate this directory

### Option 1 — convenience script (recommended)

From the repository root:

```bash
./publication/data/download_results.sh
```

This downloads `mentori_results.tar.gz` from the Zenodo record and extracts it here. After it finishes, you should see several hundred files named `exp00_*`, `exp04_*`, `exp05_*`, etc.

### Option 2 — manual

1. Open [https://doi.org/10.5281/zenodo.19476756](https://doi.org/10.5281/zenodo.19476756) in a browser.
2. Download `mentori_results.tar.gz`.
3. Extract it into this directory:
   ```bash
   tar -xzf mentori_results.tar.gz -C publication/
   ```
   (The tarball is rooted at `results/`, so it unpacks into `publication/results/`.)
4. Delete the tarball if you want.

## Verifying the results are in place

After populating, you can verify with:

```bash
ls publication/results/ | head
ls publication/results/exp*.json | wc -l    # should be ~500+
```

Then regenerate all figures with:

```bash
Rscript -e "rmarkdown::render('publication/reports/paper_figures.Rmd')"
```

which writes the 11 main and Extended Data figure TIFF + PDF files into `publication/figures/`.

## What's in the results

| Prefix | Experiment | Figure(s) it feeds |
|---|---|---|
| `exp00_*` | Model selection and judge calibration | ED Fig 2 |
| `exp01_embedding_*` | Embedding model comparison | ED Fig 1 |
| `exp02_search_*` | Search strategy ablation | ED Fig 1 |
| `exp03a_chunking_*` | Chunk size comparison | ED Fig 1 |
| `exp03b_scalability_*` | Retrieval scalability | ED Fig 1 |
| `exp04_generation_*` | Generation strategy comparison | Fig 2 |
| `exp05_scaling_*` | Corpus scaling factorial | Fig 3d–f |
| `exp06_orchestration_ablation_*` | Pipeline ablation | Fig 4a–c |
| `exp07_bench_*` | Component benchmarks | Fig 4d, ED Fig 4 |
| `exp07b_distiller_ablation_*` | Distiller prompt ablation | ED Fig 5 |
| `exp08_coder_benchmark_*` | Code generation benchmark | Fig 6 |
| `exp09_depth_sweep_*` | Retrieval depth saturation | Fig 3a–c |

The results for V4-5 include a reference copy of the pre-bug-fix data used for transparency about the async bug discovered and corrected during development. That archive is NOT bundled in the default download; see the Zenodo deposit page if you need it.
