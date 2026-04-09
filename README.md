# Mentori

A locally-hosted, agentic AI workspace for scientists.

Mentori orchestrates multiple specialised agents (lead researcher, supervisor, librarian, coder, vision) over a retrieval-augmented document corpus and a Jupyter-based code execution sandbox. The system runs entirely on your own infrastructure and supports both local LLMs (via Ollama) and hosted models (Gemini, OpenAI).

This repository accompanies the paper:

> **Systematic Ablation Reveals Hidden Failures in Multi-Agent AI for Science**
> Valerio Bianchi & Dirkjan Schokker
> Wageningen Bioveterinary Research, Wageningen University & Research
> *Nature Machine Intelligence* (2026, in press)
> [DOI: TBD] · [Data and code archive on Zenodo](https://doi.org/10.5281/zenodo.19476756)

The figure-generation code, experiment scripts, and the manuscript itself are in [`publication/`](publication/). All code needed to reproduce the paper's findings is in this repository; the raw evaluation outputs (~200 MB across 10 experiments) and the 200-paper corpus manifest are deposited at Zenodo: [10.5281/zenodo.19476756](https://doi.org/10.5281/zenodo.19476756).

---

## Quick start

### Prerequisites

- Docker and Docker Compose
- Either:
  - **Ollama** running locally on the host (`http://localhost:11434`), with at least one chat model pulled (e.g. `ollama pull qwen3-coder`), or
  - A **Gemini** API key (free tier works)
- ~10 GB free disk for the embedding model cache and ChromaDB

### Run

```bash
git clone https://github.com/vbianchi/Mentori.git
cd Mentori
cp .env.example .env
# Edit .env: set JWT_SECRET, optionally GEMINI_API_KEY and TAVILY_API_KEY
docker compose up --build
```

Then open <https://localhost:5173> and log in with the default admin account (`admin@mentori` / `admin`). **Change the password immediately**, and override `JWT_SECRET` in `.env` before exposing the service to anything other than localhost.

### Smoke test

```bash
uv run python tests/test_chunking.py     # offline unit test, no backend required
```

For end-to-end tests against a running stack, see [`docs/testing.md`](docs/testing.md).

---

## Architecture

```
Frontend (React/Vite, :5173)
    ↕ HTTP + WebSocket
Backend (FastAPI, :8766)            ← orchestrator, RAG, RLM, auth
    ↕ SSE (MCP)
Tool Server (FastMCP, :8777)        ← sandboxed code execution, web search, file ops
    ↕
Ollama (host :11434) / Gemini API
```

**Backend** (`backend/`)
- `agents/orchestrator/` — multi-phase loop: Analysis → Planning → Execution → Synthesis
- `retrieval/` — hybrid BM25 + semantic search over ChromaDB
- `retrieval/rlm/` — Recursive Language Model for deep, citation-grounded document analysis
- `mcp/` — agent-facing tool wrappers with per-role access control

**Frontend** (`frontend/`)
- React 18 + Vite, with WebSocket streaming of orchestrator events
- Single-page chat + artifact + notebook viewer

**Tool server** (`backend/tool_server.py`)
- Runs as a separate FastMCP process so tool execution is isolated from the chat backend

---

## Reproducing the paper

Figure generation reads raw experiment outputs from `publication/results/`. Those JSONs (~200 MB across 553 files) are **not bundled in this Git repository** — they live at the Zenodo deposit [10.5281/zenodo.19476756](https://doi.org/10.5281/zenodo.19476756). Download them once:

```bash
./publication/data/download_results.sh
```

Then render all figures (~5 min on a modern laptop, requires R):

```bash
Rscript -e "rmarkdown::render('publication/reports/paper_figures.Rmd')"

# Outputs: publication/figures/{fig2..fig6, ed_fig1..ed_fig6}.{tiff,pdf}
# In-browser preview: publication/reports/paper_figures.html
```

The single source of truth for every figure is `publication/reports/paper_figures.Rmd`. The full experiment scripts that produced the input JSONs live in `publication/scripts/`. See [`publication/MANIFEST.md`](publication/MANIFEST.md) for the complete data and script inventory.

---

## Citing

If you use Mentori or the evaluation methodology in your own work, please cite:

```bibtex
@article{bianchi2026mentori,
  title   = {Systematic Ablation Reveals Hidden Failures in Multi-Agent AI for Science},
  author  = {Bianchi, Valerio and Schokker, Dirkjan},
  journal = {Nature Machine Intelligence},
  year    = {2026},
  doi     = {TBD}
}
```

A `CITATION.cff` file is included at the repository root for automatic citation export from GitHub.

---

## License

- **Code** (everything outside `publication/figures/`, `publication/drafts/`): MIT (see [`LICENSE`](LICENSE))
- **Figures, manuscript, and derived data** (`publication/figures/`, `publication/drafts/`, `publication/data/questions/`, `publication/data/ground_truth.json`, etc.): CC-BY 4.0 (see [`LICENSE-CC-BY`](LICENSE-CC-BY))

The 200-paper evaluation corpus is NOT redistributed in this repository; download instructions and DOIs are in `publication/data/download_papers.py` and the Zenodo deposit linked above.

---

## Contact

Questions, bug reports, and reproducibility issues: open a GitHub issue. For correspondence about the paper, contact the corresponding author at the email on the manuscript.
