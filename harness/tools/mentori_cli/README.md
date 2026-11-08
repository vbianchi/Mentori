# mentori-cli

Ask questions of your own scientific papers with the Mentori system, the way the paper ran it.

## What it is

Our paper, *Systematic ablation of a multi-agent language model system for life sciences research* (Valerio Bianchi
and Dirkjan Schokker, DOI [PENDING]), tested Mentori, a system that answers questions from a collection of papers,
by switching its parts off one at a time and measuring what each part changes. `mentori-cli` lets you run the same
code on your own PDFs. You put your papers in a folder, build a search index of them, and ask a question. You get an
answer, the papers it was built from, and a record (a JSON file) of exactly what was sent to the language model.
The code that answers is the paper's own code (`experiments/mentori/` and `experiments/runner/` in this repository),
unchanged. You can choose the answering strategy, switch off the same parts the paper switched off, and edit every
prompt as a plain text file.

Version 0.1.0, a first release candidate. See `CHANGELOG.md`.

## What you need

- **macOS or Linux** with a terminal. The offline tests run on macOS (Apple silicon); Linux is not yet tested.
- **uv**, the Python installer: <https://docs.astral.sh/uv/getting-started/installation/>. uv fetches Python 3.12
  itself if you do not have it.
- **git**, to download this repository. The tool runs from inside the repository (it reads the paper's code and its
  settings file from there).
- **Disk space**: about 1.3 GB for the Python packages and about 6.4 GB for the two search models (bge-m3, 4.3 GB,
  and its reranker, 2.1 GB, as measured on the paper's machine). Building an index needs about 3 GB of free memory.
- **A language model**, one of:
  - **Ollama** on your own computer (<https://ollama.com>), with the model pulled, for example `ollama pull gemma3:27b`.
    Your papers then never leave your computer. The paper used Ollama 0.40.2; another version works, and is marked in
    the record (see "Settings" below).
  - **Gemini** (Google) or **Claude** (Anthropic) through their APIs. You need an API key, which you put in an
    environment variable: `GEMINI_API_KEY` or `ANTHROPIC_API_KEY`. Your question and the passages found in your
    papers are then sent to that company.

## Install

    git clone https://github.com/vbianchi/Mentori-reanalysis.git   # public when the paper is published
    cd Mentori-reanalysis/tools/mentori_cli
    uv sync --frozen                        # the Python packages, at the exact versions the paper used
    uv run mentori-cli --help               # check: prints the commands
    uv run mentori-cli fetch-encoders       # once: downloads the two search models (about 6.4 GB)

Every command below is run from `Mentori-reanalysis/tools/mentori_cli/` and starts with `uv run`.

`uv tool install` and `pip install` do not work in this version: the tool needs the repository around it (see
"Limits").

## A first look without a model (one minute)

    uv run python examples/offline_demo.py

This runs one question end to end with no model and no PDF: a small fake server stands in for the model, and two
invented passages stand in for your papers. It writes a project folder (in a temporary folder; it prints where), so
you can see the files and the record before you set anything up. Real: `mentori-cli init`, the project file, the
prompt files and the prompt edit, the settings check, the paper's Ollama client and the record. Not real: the model,
the passages, and the answering step itself, which is the demo's own short single pass (`DemoEngine` in the script:
it fills the paper's single-pass prompt and sends it once) and not the paper's strategy function, since that needs a
store and the search models.

## Five minutes on your own PDFs

**1. Make a project folder.**

    uv run mentori-cli init ~/mentori_lab

This writes `~/mentori_lab/mentori.toml` (the settings of your project), `~/mentori_lab/prompts/` (one text file per
prompt, 23 files, holding the paper's prompts exactly) and an empty `~/mentori_lab/papers/`.

**2. Choose your model** in `~/mentori_lab/mentori.toml`, under `[model]`:

    [model]
    provider = "ollama"                     # or "gemini" or "anthropic"
    name = "gemma3:27b"                     # for example gemini-3-flash-preview, or claude-haiku-4-5
    server_url = "http://127.0.0.1:11434"   # where Ollama runs (Ollama only)
    api_key_env = ""                        # Gemini or Claude: the NAME of the variable holding your key

For Gemini, run `export GEMINI_API_KEY=your-key` in the same terminal before step 4. The tool reads the key only from
that environment variable; it never reads a file of keys, and never prints or records the key. To keep the key under
another name, write that name (only the name) as `api_key_env = "MY_LAB_GEMINI_KEY"`.

To save typing, tell the tool where the project is:

    export MENTORI_CLI_CONFIG=~/mentori_lab/mentori.toml

**3. Add your papers and build the index.** Copy your PDFs into `~/mentori_lab/papers/`, then:

    uv run mentori-cli index

Each paper is cut into passages of 512 tokens (50 overlapping) and stored with their bge-m3 vectors in
`~/mentori_lab/store/`, as the paper's indexes were built. No language model is called in this step. It prints how
many passages it stored and how many files failed.

**4. Ask.**

    uv run mentori-cli ask "Which genes confer resistance to downy mildew?"

It prints the answer, then its record as JSON. The exit status is 0 when every answer came back, and 1 when any
answer ended in an error (the record's `error` field says why), so a script can tell. `--draw N` (1 to 999) sets the
draw, which is the seed; another number is refused before anything runs. Many questions at once: write a file with one question per line,
`{"id": "q1", "question": "..."}` (the `id` is optional), and run `uv run mentori-cli ask --questions questions.jsonl`.

**5. Read the record.** Each answer is also kept in `~/mentori_lab/runs/<run id>/answers.jsonl`, one line per answer.
The fields you will look at first:

| Field | What it holds |
|---|---|
| `answer`, `error` | the answer, or why there is none |
| `sources` | each passage the answer was built from: its id, the paper's file name, and `page` as the index stores it, which is 0 for every passage (see "Limits") |
| `strategy`, `components` | how it was answered, and which parts were on or off |
| `models`, `draw` | the model of each role, and the draw number (the random seed) |
| `departs_from_lock` | every setting that differs from the paper's (empty: run as the paper ran) |
| `settings_sent` | for each model call: the settings sent, the model build (digest), the server, how the call ended, tokens |
| `prompts` | the prompts you edited, and a fingerprint (sha256) of every prompt used |
| `lock` | the fingerprint of the paper's settings file and of the settings used in this run |

`runs/<run id>/calls.jsonl`, beside it, holds every model call in full, the prompt sent included.

## Choosing the strategy

    uv run mentori-cli ask --strategy single_pass   "..."    # one search, one answer (the default)
    uv run mentori-cli ask --strategy multi_hop     "..."    # up to 5 searches; the model chooses each query
    uv run mentori-cli ask --strategy rlm --rlm-turns 10 "..."   # the model writes code to search the papers
    uv run mentori-cli ask --strategy verified_pass "..."    # a second model (gpt-oss:20b) keeps only relevant passages
    uv run mentori-cli ask --strategy orchestrator  "..."    # the full multi-agent system: analyser, planner,
                                                             # supervisor, synthesiser, tools

To make one the default for the project, set `strategy` under `[run]` in `mentori.toml`. `verified_pass` needs
`gpt-oss:20b` in Ollama as well (`ollama pull gpt-oss:20b`), or another checker set under `[verifier]`.

## Switching parts off (the paper's ablations)

    uv run mentori-cli ask --strategy orchestrator --off planner,supervisor "..."
    uv run mentori-cli ask --strategy rlm --off rlm_gate "..."       # the RLM's quality gate off
    uv run mentori-cli ask --strategy rlm --off rlm_search "..."     # the RLM's search functions removed

`analyser`, `planner`, `supervisor`, `synthesiser` and `distiller` are parts of the orchestrator; `rlm_gate` and
`rlm_search` are parts of the RLM. Switching off a part the chosen strategy does not have is refused. The paper's
other variants are set in `mentori.toml` under `[components]`: `distiller = "F1"` (the distiller's alternative
prompt), `analyser = "factual_to_documents"`, `distiller_trigger = "every_step"`. Each switch reaches the paper's
code under the paper's own name and value. The reranker always stays on, as in the paper.

## Editing the prompts

Each file in `prompts/` holds one of the paper's prompts, byte for byte. It starts with a few lines marked
`##mentori-cli##`: which part uses the prompt, where it lives in the paper's code, how its placeholders (such as
`{question}` and `{passages}`) are filled, and its fingerprint. Those lines are never sent. Edit the text below the
line `---- the prompt starts on the next line ...`, and keep the placeholders the header names. An edited prompt
must hold exactly the placeholders of the paper's prompt, no fewer and no more: a prompt without `{question}` would
run without the question, so `ask` refuses it and names what is missing, before anything is sent. Delete a file to go
back to the paper's prompt. `--prompts OTHER_FOLDER` uses another folder of prompts for one run, so you can compare.

Two files are derived from another one when the paper's code loads (`analyser_factual_to_documents` from `analyser`,
`rlm_system_nosearch` from `rlm_system`), so an edit of the first does not reach the second: edit both. Every record
names the prompts you edited.

All 23 files: `analyser`, `analyser_factual_to_documents`, `planner_system`, `planner`, `step_evaluator`,
`supervisor_evaluation`, `supervisor_micro_adjustment`, `synthesiser_system`, `synthesiser`, `direct_answer`,
`librarian_memory`, `distiller`, `distiller_f1`, `rlm_system`, `rlm_system_nosearch`, `rlm_cut_reply_note`,
`single_pass`, `multi_hop_system`, `multi_hop_user`, `multi_hop_closing_user`, `multi_hop_cut_note`,
`verified_pass_generation`, `verified_pass_verifier`.

## Settings: the paper's lock, and --strict

Every model call takes its settings from the paper's settings file, `experiments/LOCK.toml` (the "lock"): each
model's sampling values, the seed (the draw number, `--draw`), a context of 131,072 tokens (less for the few models that cannot hold that many), and nothing cut (a text
too long for the model fails visibly instead of being shortened). You do not set these yourself.

When your setup differs from the lock, for example another Ollama version than 0.40.2, a model the lock does not
name, a build of a model with another digest, or a sampling value you set under `[sampling]` in `mentori.toml`, the
run goes ahead, prints each difference, and writes it into every record under `departs_from_lock`, for example:

    "departs_from_lock": ["departs from LOCK: gemma3:27b temperature = 0.2 (the lock's [sampling.models] row gives 1.0)"]

Answers with departures are not comparable with the paper's numbers. `--strict` (or `strict = true` under `[run]`)
refuses such a run before anything is sent. With an Ollama version other than 0.40.2 every Ollama run departs from
the lock, so `--strict` then refuses every Ollama run.

## Limits

- **It runs inside this repository only.** It reads the paper's code and `experiments/LOCK.toml` from the checkout;
  `uv tool install`, `pip install` and a Docker image are later items.
- **It answers; it does not grade.** The paper's judge and scores (concept recall, MiniCheck) are run from the
  repository, not from this tool.
- **Models**: Ollama, Gemini and Anthropic only. OpenAI and OpenAI-compatible servers are a later item.
- **The orchestrator runs every role on one model**, as the paper's Figure 4 runs did.
- **Not every prompt is a file.** The RLM's turn messages and sub-call prompts, and the orchestrator's tool and step
  prompts, are written inside the paper's functions and cannot be changed from outside.
- **The reranker cannot be switched off**, as in the paper.
- **No sandbox.** The RLM runs the code the model writes, inside the answering process, on your machine; its
  restricted namespace is not a security boundary. The orchestrator runs a tool server on 127.0.0.1 that executes
  the tools the model asks for. Run it in a container or a virtual machine with access only to what it needs.
- **Privacy**: with Gemini or Claude, your question and the passages from your papers go to that company.
- **No page numbers.** The paper's index builder stores every passage's page as 0
  (`experiments/mentori/backend/retrieval/smart_ingestor.py:489` reads the page from the wrong place in the
  chunker's output), so the record's `page` is 0 and the passages the model reads are labelled `Page 0`. The answer
  names the paper (its file name), not the page. The tool does not correct it: the PDFs are read by the paper's own
  code, and the stored page is part of what the strategies receive (the passage label in the single-pass,
  multi-hop and orchestrator prompts, the RLM's page lookups), so a corrected page would change the method
  from the one the paper measured.
- **Asking changes the store slightly**: opening a store rewrites a few bytes in it. Keep a copy if you need the
  store unchanged.

## Citation

If you use mentori-cli, please cite the paper:

> Valerio Bianchi and Dirkjan Schokker. Systematic ablation of a multi-agent language model system for life sciences
> research. DOI [PENDING].

## Licence

MIT, as the rest of the repository's code (`LICENSE` at the repository's root). The repository's data are under
CC BY 4.0 (`LICENSE-DATA`).

## For developers

### Tests

    uv run --frozen pytest

Offline, with fake model clients: no model is called and nothing goes over the network beyond 127.0.0.1. They check
that the config file reads back what was written, that the exported prompt files are byte-equal to the paper's
constants, that each switch reaches the paper's strategy function, the record's fields, the `--strict` refusal, the
keys, the offline demo (`examples/offline_demo.py`), and that `git diff --quiet HEAD -- experiments/mentori
experiments/runner` holds and the environment resolves to the paper's package versions.

`tests/test_integration.py` is opt-in: it builds a one-paper store with bge-m3 and runs `ask` through the paper's code
against a fake Ollama server (no model behind it):
`MENTORI_CLI_INTEGRATION=1 MENTORI_CLI_TEST_PDF=/path/to/one.pdf HF_HUB_OFFLINE=1 uv run pytest tests/test_integration.py`.

### How it works

- `pyproject.toml` takes `experiments/mentori` as a path dependency for its dependencies only (it is not a package),
  every version pinned to `experiments/mentori/uv.lock` (`dev/pin_from_paper_lock.py --check`). At run time the tool
  puts `experiments/mentori` and the repository on `sys.path`, as the paper's scripts do. `MENTORI_REPO` points it at
  another checkout.
- `index` is `experiments/reuse_demo/build_index.py`'s ingest (`experiments/reuse_demo/GUIDE.md`, step 3), without its
  gate (the rebuild of the paper's 20-paper index).
- `ask` runs each answer in its own run context of `experiments/runner` and calls the paper's strategy functions:
  `tests/experiments/exp1_rlm_vs_singlepass.py` (single pass, multi-hop, RLM, verified pass) and
  `publication/scripts/exp_03_orchestration_ablation.py` `_full_orchestrator`, every orchestrator role on the one model.
- `src/mentori_cli/inject.py` installs, in memory, the lock with its departures, the edited prompts and another
  verifier; no file of the paper's code is written. The orchestrator's tool server, a second process in
  `experiments/mentori`'s own environment (`uv run --project experiments/mentori`, which makes
  `experiments/mentori/.venv` on first use; git ignores it), installs the same before it starts.
- With `HF_HUB_OFFLINE=1` set, the tool answers one Hugging Face lookup itself: the paper's environment (transformers
  4.57.3) asks the Hub for `model_info` at every tokenizer load, even from local files, and fails offline. For the lock's
  two encoders only, the tool returns no tags (neither is a Mistral model, which is all that check reads). Without
  `HF_HUB_OFFLINE` that lookup goes to the Hub as in the paper's runs.

### Later items

| Item | Why not now | Hours (estimate) |
|---|---|---|
| OpenAI, and any OpenAI-compatible server | the paper's lock adapter routes only ollama, gemini and anthropic (`backend/agents/lock_adapter.py` _route); a route of its own is an edit of the paper's code | 10 |
| A reranker switch | the paper keeps the reranker on (`backend/retrieval/retriever.py` refuses `use_reranker=False`); a change of the method | 3 |
| The RLM's turn messages and sub-call prompts, the orchestrator's tool and step prompts | written inline inside functions of the paper's code (for example the nudges in `backend/retrieval/rlm/orchestrator.py`), so they cannot be replaced from outside without editing it | 4 |
| `index --check-against-paper`: the paper's gate before a build | needs the paper's 20 PDFs; `build_index.py gate` runs it today | 2 |
| One model per orchestrator role | every role runs the one generator, as Figure 4's runs did | 3 |
| A fresh copy of the store per run | opening a store changes a few bytes in it (GUIDE.md step 4) | 1 |
| Judging and scoring (the judge, concept recall, MiniCheck) | GUIDE.md step 5 runs them from the repository | 6 |
| A package that works outside this checkout (`uv tool install`, PyPI), and a Docker image | the tool reads `experiments/LOCK.toml`, `experiments/runner` and `experiments/mentori` from the checkout, and `uv tool install` fails building `experiments/mentori` (setuptools: "Multiple top-level packages discovered in a flat-layout") | 14 |
