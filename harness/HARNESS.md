# The harness: the code that ran the paper's experiments

This folder holds the code that made the revised paper's answers and judge rows: our copy of Mentori
(`experiments/mentori/`), the runner every model call goes through (`experiments/runner/`), the one settings file
(`experiments/LOCK.toml`), the judge and scorers (`experiments/scorers/`), the authors' RLM package
(`experiments/rlm_ref/`), the run on a new corpus (`experiments/reuse_demo/`) and a command line tool
(`tools/mentori_cli/`). Use it to run prompts on any corpus of PDFs, to switch each component off, and to change the
prompts.

It is copied from the Mentori-reanalysis repository by `scripts/S609_release_harness.py`; `PROVENANCE.json` names
the commit, and `MANIFEST.tsv` lists every file with its size and sha256. The folders keep the layout they have
there, because the code finds its files by repository paths (for example `experiments/runner/experiment.py:101`
`KEY_V24`). Every command below starts in this folder (`harness/`).

## Approximate, not exact

Running this code again gives new answers, not the paper's answers. The paper's numbers are rebuilt from the frozen
records of the runs (the Zenodo record) by `../analysis/`, not by running this harness.

| what | re-runs exactly? | why |
|---|---|---|
| the work list: which answers, their keys, seeds and the settings each call sends | yes | the dry runs below print it from the answer key and the lock alone |
| the index: which passages exist | yes, checked | `build_index.py gate` rebuilds the paper's 20-paper index and requires its 778 chunks and chunk manifest (`experiments/reuse_demo/build_index.py:86` `GATE_CHUNKS`); Chroma's ids differ on every build (`experiments/runner/index_identity.py`) |
| a generator's answer | no | generators sample at their makers' temperatures, with the draw as seed (LOCK `[generation]`, `[sampling.models]`); an Anthropic call sends no seed (`experiments/runner/anthropic_client.py`); preview cloud models change or retire (`gemini-3-flash-preview`; LOCK `[anthropic]` gives Haiku's retirement as "not sooner than October 15, 2026") |
| a local judge's score | on the same hardware | the judge runs at temperature 0, but another machine can score differently: the Beelink (AMD) gave the Studio's devstral scores on 95 of 107 calibration answers (`findings/recompute/S440_judge_lock_check_beelink.md`) |
| the code | no, by default | this folder is the code at one commit; the runs used earlier commits (`PINS.md`) |

What is fixed is the method: the lock's settings, each model's digest, Ollama 0.40.2 and its binary's sha256
(LOCK `[server]`, `[models]`).

## Install

You need uv, git, and for local models Ollama 0.40.2 with the models the lock names, each pulled at the digest in
LOCK `[models]`. The code was tested here on macOS (Apple silicon) only. Cloud models need a key in an environment
variable, `GEMINI_API_KEY` or `ANTHROPIC_API_KEY`; without one, the clients look in `~/.config/mentori-runs/keys.env`
(`experiments/runner/gemini_client.py:82` `KEYS`). The authors' RLM package runs the model's code in a Docker
sandbox (`experiments/rlm_ref/sandbox/Dockerfile`).

    uv sync --frozen --project experiments/mentori    # the experiments: Mentori's own pyproject.toml and uv.lock
    uv sync --frozen                                  # the judge and scorers: pyproject.toml, uv.lock, Python 3.13.11
    uv sync --frozen --project experiments/rlm_ref    # the authors' RLM package (rlms 0.1.3)

Python is pinned by `.python-version` (3.13.11). The tests below run with no model, no server and no key; each
passed when this folder was built (`PROVENANCE.json`, field `checks`):

    uv run --frozen --project experiments/mentori python -m experiments.runner.check_lock   # offline
    uv run --frozen --project experiments/mentori python -m experiments.runner.check_experiment   # offline
    uv run --frozen --project experiments/mentori python -m experiments.runner.check_adapter --offline   # offline
    uv run --frozen --project experiments/mentori python -m experiments.runner.check_retrieval   # offline
    uv run --frozen --project experiments/mentori python -m experiments.runner.check_rolling_pool   # offline
    uv run --frozen --project experiments/mentori python -m experiments.runner.check_tool_server   # offline
    uv run --frozen --project experiments/mentori python -m experiments.runner.check_anthropic   # offline
    uv run --frozen --project experiments/mentori python -m experiments.runner.check_gemini --offline   # offline
    uv run --frozen --project experiments/mentori python -m experiments.runner.check_codegen   # offline

Some checks do not run here. Four of `experiments/runner/` (`check_orchestrator.py`, `check_rlm.py`,
`check_search_timers.py`, `check_exp01_generator.py`) compare today's code with an earlier commit, read with
`git show`, so they need Mentori-reanalysis's history. `experiments/rlm_ref/check_rlm_ref.py` needs Docker running
(its sandbox) and stops before its checks without it. `experiments/rlm_ref/check_rlm_ref_ollama.py` and
`check_component_bench.py` load lane scripts of Mentori-reanalysis that are not here (the G19 lane's check, and
`findings/recompute/T3_runs/t3_guard.py`). Each of these exits 1 in this folder.

## Your corpus and your answer key

1. Fetch the PDFs. `../publication/data/download_papers.py` reads a table of papers (the paper's own is
   `../publication/data/corpus_papers.csv`) and downloads each one. The paper's PDFs are mostly not ours to share,
   so the table holds links, not files.
2. Write an answer key in the format of `data/ground_truth_v2/all_v2_4.json` (key v2.4).
   `experiments/reuse_demo/GUIDE.md` step 2 lists the fields.
3. Build the index. First prove the build matches the paper's (`build_index.py gate`, on the paper's own 20 core
   PDFs), then build yours (`build_index.py build`), as `experiments/reuse_demo/GUIDE.md` step 3 shows. A run finds
   its store through the environment variables `DATABASE_URL` and `CHROMA_PERSIST_DIRECTORY`
   (`experiments/mentori/backend/config.py:10` `DATABASE_URL`, `experiments/mentori/backend/config.py:22`
   `CHROMA_PERSIST_DIRECTORY`).

`GUIDE.md` is the record of the one run on a new corpus (five lettuce papers, I2) as it was written in
Mentori-reanalysis. Two of its paths differ here: its `zenodo/10_data/upstream/publication/data/download_papers.py`
is `../publication/data/download_papers.py`, and the paper's 20 core PDFs are in `../datasets/v4_papers/core/` once
`download_papers.py` has fetched them.

## Run prompts, the short way

`tools/mentori_cli/` runs the same code on a folder of PDFs: `init`, `index`, `ask --strategy`, `--off`, and a
folder of 23 editable prompts (`tools/mentori_cli/README.md`). It finds the paper's code through
`tools/mentori_cli/src/mentori_cli/paths.py`, four folders up, which is this folder. Its README's install lines
name the Mentori-reanalysis repository; here, start in `tools/mentori_cli/`:

    cd tools/mentori_cli && uv sync --frozen && uv run --frozen mentori-cli --help   # offline
    cd tools/mentori_cli && uv run --frozen pytest -q   # offline

## Ablate each component

Each line below is a dry run: it prints the work list and the settings, calls no model and writes nothing. Remove
`--dry-run` and add the server flag the script asks for (`--ollama-url`, `--base-url`) to run it. Every flag and
value here is checked against the script's own argument parser when this folder is built.

| what is varied | script | switch | values |
|---|---|---|---|
| generation strategy | `experiments/mentori/publication/scripts/exp_01_generation.py` | `--configs` | `single_pass` `multi_hop` `rlm_5` `rlm_10` `rlm_20` `verified_pass` (`exp_01_generation.py:323` `CONFIG_NAMES`) |
| one strategy part, run only when named | the same | `--configs` | `matched_budget` (with `--matched-budget-plan`), `single_pass_cut800`, `rlm_10_nogate` (the RLM's quality gate off), `rlm_10_nosearch` (its search functions removed), `rlm_10_ctrl` (the control) |
| the generator model | the same | `--generator` | `gemini::<model>`, `anthropic::<model>`, or `ollama::<tag>` with `--generator-url` |
| corpus size and noise | `experiments/mentori/publication/scripts/exp_02_scaling_factorial.py` | `--indexes`, `--configs` | 12 indexes `exp_v4_s{5,10,20,50}_n{0,1,3}` (`exp_02_scaling_factorial.py:187` `ALL_INDEXES`) |
| the orchestrator's parts | `experiments/mentori/publication/scripts/exp_03_orchestration_ablation.py` | `--configs` | `raw_gemini` `naive_rag` `rlm_10` `full_orchestrator` `orch_no_distiller` `orch_distiller_f1` `orch_no_analyser` `orch_no_planner` `orch_no_supervisor` `orch_no_synthesiser` `orch_factual_to_documents`; stress: `orch_distil_every_step` `orch_distil_every_step_f1` (`exp_03_orchestration_ablation.py:147` `ORCHESTRATOR_CONFIGS`) |
| each component alone, per model | `experiments/mentori/publication/scripts/exp_04_component_bench.py` | `--benchmark`, `--models`, `--datasets` | `analyzer` `planner` `supervisor` `distiller` `synthesizer` (`exp_04_component_bench.py:160` `BENCHMARK_NAMES`) |
| the distiller's prompt | `experiments/mentori/publication/scripts/exp_04b_distiller_ablation.py` | `--variants`, `--datasets` | `baseline` `F1` `F2` `F3` `F1_F3` `F2_F3` `F1_F2_F3` (`exp_04b_distiller_ablation.py:344` `ALL_VARIANTS`) |
| code generation | `experiments/mentori/publication/scripts/exp_05_coder_benchmark.py` | `--model`, `--configs`, `--thinking`, `--length-stop` | models: `exp_05_coder_benchmark.py:126` `FIG6_MODELS`; configs: `experiments/mentori/tests/experiments_v2/exp_v2_8_coder_benchmark.py:90` `CONFIG_NAMES` |
| the RLM's turn limit (depth) | `experiments/mentori/publication/scripts/exp_06_depth_sweep.py` | `--depths`, `--question-set`, `--generator` | depths `1 2 3 5 7 10 15 20 30 50` (`exp_06_depth_sweep.py:145` `DEFAULT_DEPTHS`) |
| the authors' RLM package | `experiments/rlm_ref/run_rlm_ref.py` | `--cap`, `--draw`, `--question-set`, `--generator` | caps 5, 10, 20 on `all135`; 1, 2, 3, 7, 15, 30, 50 on `depth_sweep86` |

    uv run --frozen --project experiments/mentori python experiments/mentori/publication/scripts/exp_01_generation.py --dry-run
    uv run --frozen --project experiments/mentori python experiments/mentori/publication/scripts/exp_01_generation.py --dry-run --configs single_pass_cut800 rlm_10_nogate rlm_10_nosearch rlm_10_ctrl --max-questions 3
    uv run --frozen --project experiments/mentori python experiments/mentori/publication/scripts/exp_01_generation.py --dry-run --generator anthropic::claude-haiku-4-5
    uv run --frozen --project experiments/mentori python experiments/mentori/publication/scripts/exp_01_generation.py --dry-run --generator ollama::gemma3:27b --generator-url http://127.0.0.1:11434
    uv run --frozen --project experiments/mentori python experiments/mentori/publication/scripts/exp_02_scaling_factorial.py --dry-run --indexes exp_v4_s5_n0 exp_v4_s50_n3 --configs single_pass rlm_10
    uv run --frozen --project experiments/mentori python experiments/mentori/publication/scripts/exp_03_orchestration_ablation.py --dry-run --configs full_orchestrator orch_no_distiller orch_no_planner
    uv run --frozen --project experiments/mentori python experiments/mentori/publication/scripts/exp_03_orchestration_ablation.py --dry-run --configs orch_distil_every_step orch_distil_every_step_f1
    uv run --frozen --project experiments/mentori python experiments/mentori/publication/scripts/exp_04_component_bench.py --dry-run --benchmark all --datasets findings/recompute/T3_runs/inputs
    uv run --frozen --project experiments/mentori python experiments/mentori/publication/scripts/exp_04b_distiller_ablation.py --dry-run --variants baseline F1 F2 F3 --datasets findings/recompute/T3_runs/inputs
    uv run --frozen --project experiments/mentori python experiments/mentori/publication/scripts/exp_05_coder_benchmark.py --dry-run
    uv run --frozen --project experiments/mentori python experiments/mentori/publication/scripts/exp_06_depth_sweep.py --dry-run --depths 1 5 10
    uv run --frozen --project experiments/rlm_ref python -m experiments.rlm_ref.run_rlm_ref --dry-run --cap 10 --draw 1

`--datasets findings/recompute/T3_runs/inputs` is the frozen set of component inputs the paper's component runs read
(its `MANIFEST.json` holds each file's sha256). Without `--datasets`, `exp_04_component_bench.py` and
`exp_04b_distiller_ablation.py` look for the submission's results files, which are not here, and say so.

The same switches in the short tool: `mentori-cli ask --strategy single_pass|multi_hop|rlm|verified_pass|orchestrator`
and `--off analyser,planner,supervisor,synthesiser,distiller,rlm_gate,rlm_search`
(`tools/mentori_cli/src/mentori_cli/config.py:15` `STRATEGIES`, `tools/mentori_cli/src/mentori_cli/config.py:19`
`OFF_NAMES`).

The answering strategy's search index: the dry runs read no store. A run reads the index its `--index` names from
the store in `CHROMA_PERSIST_DIRECTORY`.

## Change the prompts

With the short tool, edit the 23 files `mentori-cli init` writes into the project's prompts folder
(`tools/mentori_cli/src/mentori_cli/registry.py` names where each one lives in the code). In the code itself:

| prompt | where |
|---|---|
| single pass and the verified pass's answer | `experiments/mentori/backend/retrieval/pipeline.py:46` `GENERATION_PROMPT` |
| the verified pass's checker | `experiments/mentori/backend/retrieval/chunk_verifier.py:122` `VERIFICATION_PROMPT` |
| the RLM's system prompt | `experiments/mentori/backend/agents/prompts.py:441` `RLM_ORCHESTRATOR_PROMPT` |
| the orchestrator's analyser | `experiments/mentori/backend/agents/orchestrator/prompts.py:20` `ORCHESTRATOR_ANALYZER_PROMPT` |
| the orchestrator's planner | `experiments/mentori/backend/agents/orchestrator/prompts.py:124` `PLANNER_SYSTEM_PROMPT` |
| the distiller | `experiments/mentori/backend/agents/orchestrator/observation_distiller.py:59` `_DISTILL_PROMPT` |

A changed prompt is a change of method: its answers are not comparable with the paper's. `mentori-cli` writes the
sha256 of every prompt it sent into each record.

## Score the answers

- The judge: `experiments/scorers/judge_passages.py`. Its `check` first re-scores the 107 calibration answers and
  compares every score with the stored pass (`findings/recompute/S440_judge_lock_check.jsonl`); `run` refuses to
  start without a passed check on the same machine and server. The 107 answers are read from
  `data/upstream/publication/results/exp00_phase2_latest.json`, which is not in this folder: it is in the
  submission's Zenodo deposit (10.5281/zenodo.19476756), which `../publication/data/download_results.sh` fetches
  into `../publication/results/`. Copy it to that path; its sha256 is in `data/upstream/MANIFEST.sha256`.
- Concept recall, the number check and MiniCheck on a new corpus: `experiments/reuse_demo/i2_signals.py`, as
  `experiments/reuse_demo/GUIDE.md` step 5 shows.

## What every call records

Every model call writes the fields of LOCK `[record]` into its run's `calls.jsonl`, under `findings/runs/<run_id>/`
(empty here). Each Ollama call record also names the code: `code_commit` is `git rev-parse HEAD` of the checkout
that holds the runner, `code_dirty` whether tracked files under `experiments/` or `scripts/` differ from it
(`experiments/runner/ollama_client.py:95` `code_version`). Inside a Mentori-paper checkout that is Mentori-paper's
commit; from an unpacked archive with no `.git`, both are null and `code_error` says why.

## Not in this folder, and why

- The corpus PDFs and their text, and every store (copyright). `experiments/rlm_ref/adapter.py:223`
  `CONTEXT_FILE` reads the RLM package's context, which `experiments/rlm_ref/build_context.py` builds from a store;
  build it from yours.
- The paper's runs and their records: in the Zenodo record, read by `../analysis/`.
- The decision log of Mentori-reanalysis (`experiments/README.md` there). `experiments/runner/matched_budget.py:293`
  `DECISIONS` reads it only for `replan --accept-count-drift`, which therefore refuses here.
- The machine launchers (`findings/recompute/*_runs/*.sh` in Mentori-reanalysis): they name the paper's machines
  and ports. `PINS.md` lists the commits they pinned.
