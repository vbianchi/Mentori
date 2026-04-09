# Mentori

A locally-hosted, agentic AI workspace for scientists.

Mentori orchestrates multiple specialised agents (lead researcher, supervisor, librarian, coder, vision) over a retrieval-augmented document corpus and a Jupyter-based code execution sandbox. The system runs entirely on your own infrastructure and supports both local LLMs (via Ollama) and hosted models (Gemini, OpenAI, Anthropic).

This repository accompanies the paper:

> **Systematic Ablation Reveals Hidden Failures in Multi-Agent AI for Science**
> Valerio Bianchi & Dirkjan Schokker
> Wageningen Bioveterinary Research, Wageningen University & Research
> *Nature Machine Intelligence* (2026, in press)
> DOI: TBD · Data and code archive: [10.5281/zenodo.19476756](https://doi.org/10.5281/zenodo.19476756)

The figure-generation code, experiment scripts, and the manuscript itself are in [`publication/`](publication/). The raw experiment outputs (~200 MB across 10 experiments) and the 200-paper evaluation corpus manifest are deposited at Zenodo: [10.5281/zenodo.19476756](https://doi.org/10.5281/zenodo.19476756).

---

## Contents

1. [Installation](#1-installation)
2. [First run](#2-first-run)
3. [Architecture](#3-architecture)
4. [Where to find things (reviewer guide)](#4-where-to-find-things-reviewer-guide)
5. [Reproducing the paper figures](#5-reproducing-the-paper-figures)
6. [Re-running the experiments](#6-re-running-the-experiments)
7. [Citing](#7-citing)
8. [License](#8-license)
9. [Contact](#9-contact)

---

## 1. Installation

Mentori runs as three containerised services (backend, tool server, frontend) plus a local Ollama process on the host for language models. You do **not** need to install Node.js, npm, or Python manually for running Mentori — all three are built inside Docker from the images in this repository.

### 1.1. Host prerequisites (everyone)

You need:

| Tool | Why | Version |
|---|---|---|
| **Git** | To clone this repository | any recent |
| **Docker** + **Docker Compose** | Runs the backend / tool-server / frontend | Docker Engine ≥ 24, Compose V2 |
| **Ollama** | Serves local LLMs to the backend | ≥ 0.5 |
| **At least one Ollama model** | Provides the generator + reasoning LLM | e.g. `qwen3-coder:30b` (recommended) or `gpt-oss:20b` |
| **~20 GB free disk** | ~5 GB for the BGE-M3 embedding cache, ~10 GB for one mid-sized Ollama model, ~5 GB for ChromaDB + workspace | — |
| **R ≥ 4.3** *(optional, only for re-rendering figures)* | `paper_figures.Rmd` is written in R Markdown | — |
| **Python ≥ 3.11 + [uv](https://docs.astral.sh/uv/)** *(optional, only for re-running experiments or unit tests)* | Experiment scripts and tests use `uv run python ...` | Python ≥ 3.11, uv ≥ 0.4 |

### 1.2. macOS installation path

On macOS, Docker Desktop is not free for commercial use. The recommended open-source alternative is [Colima](https://github.com/abiosoft/colima), a lightweight Docker runtime. The full install using [Homebrew](https://brew.sh):

```bash
# 1. Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Install Docker CLI + Compose + Colima
brew install docker docker-compose colima

# 3. Start Colima with enough RAM and CPU for the stack
colima start --cpu 6 --memory 12 --disk 60

# 4. Verify Docker works
docker ps

# 5. Install Ollama (runs on the host, not inside Colima)
brew install ollama
brew services start ollama

# 6. Pull a capable model (choose one; qwen3-coder:30b is what we use in the paper)
ollama pull qwen3-coder:30b
# or, lighter alternative:
# ollama pull gpt-oss:20b

# 7. Optional: install R + uv for paper reproduction
brew install r
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 1.3. Linux installation path

Docker is straightforward on Linux — no Colima needed.

```bash
# 1. Install Docker Engine + Compose V2 (Ubuntu/Debian example)
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# Log out and back in so the group membership takes effect

# 2. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 3. Pull a capable model
ollama pull qwen3-coder:30b
# or the lighter alternative:
# ollama pull gpt-oss:20b

# 4. Optional: install R + uv for paper reproduction
sudo apt install -y r-base                 # Debian/Ubuntu
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 1.4. Windows installation path

Use Docker Desktop with WSL2 backend, install Ollama for Windows, and run the `docker compose` commands from a WSL2 Ubuntu shell. Details:

- Docker Desktop + WSL2: <https://docs.docker.com/desktop/wsl/>
- Ollama for Windows: <https://ollama.com/download/windows>
- R for Windows: <https://cran.r-project.org/bin/windows/base/>
- uv for Windows: <https://docs.astral.sh/uv/getting-started/installation/>

### 1.5. Which Ollama model should I use?

The experiments in the paper used several models; `qwen3-coder:30b` was the most capable open-weights model in our V4-8 code benchmark, followed by `gpt-oss:20b`. For a first run:

| Model | Size on disk | RAM / VRAM | Good for |
|---|---|---|---|
| `qwen3-coder:30b` | ~17 GB | 24 GB+ (or GPU with ≥24 GB VRAM) | Best overall; what the paper benchmarks |
| `gpt-oss:20b` | ~12 GB | 16 GB+ | Lighter, still very capable |
| `gemma3:27b` | ~15 GB | 24 GB+ | Strong alternative |
| `nemotron-3-nano:30b` | ~18 GB | 24 GB+ | NVIDIA's tuned model |

You only need one. Pull more if you want to run the experiments comparing multiple models.

---

## 2. First run

After the prerequisites above are installed:

```bash
# Clone the repository
git clone https://github.com/vbianchi/Mentori.git
cd Mentori

# Copy and edit the environment file
cp .env.example .env
# Edit .env: set MENTORI_ADMIN_PASSWORD and JWT_SECRET to strong values.
# The defaults are deliberately invalid placeholders — do not leave them.
# GEMINI_API_KEY / TAVILY_API_KEY are optional (can be set later in the UI).

# Start the three services
docker compose up --build
```

First build takes a few minutes (the backend image downloads the BGE-M3 embedding model, ~5 GB). Subsequent starts are fast.

When the stack is up:

- Open <http://localhost:5173> in a browser
- Log in with the email and password you set in `.env`
- Go to **Settings → API Keys** if you want to add Gemini, OpenAI, Anthropic, or Tavily keys for your user (per-user, stored in the database)
- Ask your first question; Mentori will route through the orchestrator (analysis → plan → execution → synthesis)

---

## 3. Architecture

```
Browser (http://localhost:5173)
    ↕ HTTP + WebSocket
Frontend (React/Vite, :5173)
    ↕ HTTP + WebSocket
Backend  (FastAPI, :8766)        ← orchestrator, RAG, RLM, auth
    ↕ SSE (MCP)
Tool Server (FastMCP, :8777)     ← sandboxed code exec, web search, file ops, RAG tools
    ↕
Ollama (host :11434)  /  Gemini / OpenAI / Anthropic APIs (optional)
```

**Backend** (`backend/`)

- `agents/orchestrator/` — multi-phase loop: **Analysis → Planning → Execution (with Supervisor evaluation) → Synthesis**
- `agents/session_context.py` — per-request context carrying user, task, workspace, API keys through async code
- `agents/model_router.py` — abstracts Ollama / Gemini / OpenAI / Anthropic under a common interface
- `retrieval/` — hybrid BM25 + semantic search over ChromaDB (BGE-M3 embeddings)
- `retrieval/rlm/` — Recursive Language Model for deep, citation-grounded document analysis
- `mcp/` — agent-facing tool wrappers with per-role access control

**Frontend** (`frontend/`)

- React 18 + Vite, with WebSocket streaming of orchestrator events
- Single-page chat + artifact + notebook viewer

**Tool server** (`backend/tool_server.py`)

- Runs as a separate FastMCP process so tool execution is isolated from the chat backend

---

## 4. Where to find things (reviewer guide)

If you are reviewing the paper and want to inspect specific components:

### 4.1. Prompts

The paper describes five orchestrator components (Analyzer, Planner, Supervisor, Distiller, Synthesizer) plus the Lead Researcher loop and the Recursive Language Model (RLM). Their prompts live in:

| File | What's in it |
|---|---|
| [`backend/agents/prompts.py`](backend/agents/prompts.py) | Lead researcher system prompt, general agent framing, tool-use prompts |
| [`backend/agents/orchestrator/prompts.py`](backend/agents/orchestrator/prompts.py) | Analyzer, Planner, Supervisor, Synthesizer prompts (the multi-phase loop) |
| [`backend/agents/orchestrator/planner.py`](backend/agents/orchestrator/planner.py) | Plan-generation templates and query-analysis prompts |
| [`backend/agents/orchestrator/observation_distiller.py`](backend/agents/orchestrator/observation_distiller.py) | Observation Distiller prompts — the component the paper identifies as the primary orchestration bottleneck |
| [`backend/agents/notebook/prompts.py`](backend/agents/notebook/prompts.py) and [`prompts_v2.py`](backend/agents/notebook/prompts_v2.py) | Coder-mode prompts used for the V4-8 code generation benchmark |
| [`backend/retrieval/rlm/`](backend/retrieval/rlm/) | Recursive Language Model orchestrator and executor prompts (deep document analysis) |

For the **distiller prompt ablation** (ED Fig. 5 in the paper), the seven prompt variants (baseline, F1, F2, F3, F1+F2, F1+F3, F2+F3) are defined in:

- [`publication/scripts/exp_04b_distiller_ablation.py`](publication/scripts/exp_04b_distiller_ablation.py)

### 4.2. Evaluation components

The paper's triple-triangulation evaluation (deterministic ground truth, calibrated LLM judge, MiniCheck NLI) is implemented across:

| File | Role |
|---|---|
| [`publication/scripts/analysis_deterministic_scorer.py`](publication/scripts/analysis_deterministic_scorer.py) | Concept recall + semantic similarity against expert ground truth |
| [`publication/scripts/analysis_minicheck.py`](publication/scripts/analysis_minicheck.py) | MiniCheck natural-language-inference claim grounding |
| [`publication/scripts/analysis_paper_validation.py`](publication/scripts/analysis_paper_validation.py) | Kendall's W triangulation analysis |
| [`publication/scripts/analysis_statistical_tests.py`](publication/scripts/analysis_statistical_tests.py) | McNemar tests, Spearman / Pearson correlations |
| [`publication/scripts/analysis_fliprate.py`](publication/scripts/analysis_fliprate.py) | Self-correction harm analysis (the 79% statistic) |
| [`publication/scripts/analysis_perturn.py`](publication/scripts/analysis_perturn.py) | Per-turn RLM progression (the logistic saturation fits) |

### 4.3. Questions, ground truth, and validation data

- [`publication/data/ground_truth.json`](publication/data/ground_truth.json) — 250 expert-curated questions with expected answers and concepts
- [`publication/data/questions/`](publication/data/questions/) — question source files grouped by category (factual recall, conceptual, technical, cross-document, synthesis, out-of-domain)
- [`publication/data/validation_main.json`](publication/data/validation_main.json) — main validation results
- [`publication/data/validation_cross_document.json`](publication/data/validation_cross_document.json), `validation_synthesis.json`, `validation_ood.json` — category-specific validation

The 200-paper corpus itself is not redistributed in this repository (publisher copyright); download it via the Zenodo deposit and its `download_corpus.py` script. See [`publication/data/download_papers.py`](publication/data/download_papers.py) for the core-paper download plan.

### 4.4. Experiment scripts

All ten experiments (V4-0 through V4-9) live in [`publication/scripts/`](publication/scripts/):

| Script | What it runs |
|---|---|
| `exp_00_*` | Model selection and judge calibration |
| `exp_01_generation.py` | Generation strategy comparison (Fig. 2) |
| `exp_02_scaling_*.py` | Corpus scaling factorial (Fig. 3d–f) |
| `exp_03_citations.py`, `exp_03_orchestration_ablation.py` | Citation analysis + pipeline ablation (Fig. 4a–c) |
| `exp_04_component_bench.py` | Component benchmarks (Fig. 4d, ED Fig. 4) |
| `exp_04b_distiller_ablation.py` | Distiller prompt ablation (ED Fig. 5) |
| `exp_05_coder_benchmark.py` | Code generation benchmark (Fig. 6) |
| `exp_06_depth_sweep.py` | Retrieval depth saturation (Fig. 3a–c) |

### 4.5. Figures

- [`publication/reports/paper_figures.Rmd`](publication/reports/paper_figures.Rmd) — **single source of truth** for all 6 main and 6 Extended Data figures
- [`publication/figures/`](publication/figures/) — pre-rendered TIFF + PDF of every figure (the versions submitted to NMI)
- Fig. 1 (system architecture) is authored separately in PowerPoint, exported to PDF and TIFF

---

## 5. Reproducing the paper figures

The quickest path from a clean clone to re-rendered figures:

```bash
# 1. Clone and enter the repo (if you haven't already)
git clone https://github.com/vbianchi/Mentori.git
cd Mentori

# 2. Download the raw experiment results from Zenodo (~47 MB, auto-extracts to publication/results/)
./publication/data/download_results.sh

# 3. Install R dependencies (one-time)
Rscript -e 'install.packages(c("tidyverse","jsonlite","scales","patchwork","ggrepel","here","ragg","kableExtra","minpack.lm","rmarkdown"))'

# 4. Render all figures
Rscript -e "rmarkdown::render('publication/reports/paper_figures.Rmd')"
```

The render writes 12 TIFF + 12 PDF files into `publication/figures/` and an in-browser preview at `publication/reports/paper_figures.html`. Takes ~5 min on a modern laptop. No GPU required.

---

## 6. Re-running the experiments

Re-running the experiments from scratch is **not necessary** for reviewing the paper — the results in the Zenodo deposit already contain every evaluation reported. But if you want to re-run a subset:

```bash
# Install Python dependencies via uv (one-time)
uv sync

# Start Mentori stack (the experiments call the running backend)
docker compose up -d

# Optional: run the smallest experiment (generation strategy comparison, ~30 min)
uv run python publication/scripts/exp_01_generation.py --configs rlm_10 --max-questions 10

# Or the distiller prompt ablation (~20 min for one model)
uv run python publication/scripts/exp_04b_distiller_ablation.py --models qwen3-coder --variants baseline F1 F2
```

The full experiment suite takes **several days of compute** across a multi-GPU machine with all the models pulled locally. Individual experiments have `--help` flags that show smoke-test options.

---

## 7. Citing

If you use Mentori or the evaluation methodology in your own work, please cite:

```bibtex
@article{bianchi2026mentori,
  title   = {Systematic Ablation Reveals Hidden Failures in Multi-Agent AI for Science},
  author  = {Bianchi, Valerio and Schokker, Dirkjan},
  journal = {Nature Machine Intelligence},
  year    = {2026},
  doi     = {TBD}
}

@dataset{bianchi2026mentori_zenodo,
  title     = {Mentori — code, data, and supplementary materials for ``Systematic Ablation Reveals Hidden Failures in Multi-Agent AI for Science''},
  author    = {Bianchi, Valerio and Schokker, Dirkjan},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.19476756}
}
```

A [`CITATION.cff`](CITATION.cff) file at the repository root enables automatic citation export from GitHub (the "Cite this repository" button).

---

## 8. License

- **Code** (`backend/`, `frontend/`, `scripts/`, `tests/`, `publication/scripts/`, `publication/data/download_*.{sh,py}`, etc.): MIT — see [`LICENSE`](LICENSE)
- **Figures, manuscript, and derived data** (`publication/figures/`, `publication/drafts/`, `publication/data/ground_truth.json`, `publication/data/questions/`, `publication/data/validation_*.json`, `publication/reports/`): CC-BY 4.0 — see [`LICENSE-CC-BY`](LICENSE-CC-BY)

The 200-paper evaluation corpus is **not** redistributed in this repository; third-party papers remain under their original publisher licenses. Download instructions are in [`publication/data/download_papers.py`](publication/data/download_papers.py) and the Zenodo deposit.

---

## 9. Contact

Bug reports, reproducibility issues, and code questions: **open a GitHub issue** at <https://github.com/vbianchi/Mentori/issues>.

For correspondence about the paper itself, contact the corresponding author at the email listed on the manuscript.
