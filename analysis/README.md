# Mentori analysis: the scripts that make the paper's figures, tables and numbers

Built by `scripts/S608_release_analysis.py` from Mentori-reanalysis commit `e058482faa`, copied from that commit
(git cat-file), never from a working tree. `RELEASE_PROVENANCE.json` lists every file and where it went.

## What is here

- `reproduce.py`: the one command (below).
- `scripts/`: 115 of the 783 scripts tracked in Mentori-reanalysis, the ones the stages run or
  import (measured by the read audit, `scripts/fig_read_audit.py`).
- `experiments/`: `LOCK.toml` (every model call's settings), `FIGURE_LOCK.toml` (every figure's rules), the runner,
  scorer and Mentori files the scripts import, and `rlm_ref/` (its own `pyproject.toml` and `uv.lock`).
- `findings/figures_provisional/`: every committed plate, Source Data workbook and legend draft, and
  `MANIFEST.sha256`; `findings/recompute/`: the committed outputs the stages are compared with.
- `data/`: the answer keys and prompt files the scripts read.
- `expected/MANIFEST.sha256`: the sha256 of every expected output (392 files), the held ones included.
- `DATA_FILES.tsv`: the files the data root must hold, with size and sha256.
- `pyproject.toml`, `uv.lock`, `.python-version` (Python 3.13.11): the environment, as the analysis ran.

645 files in git (101,217,501 bytes). The inputs the stages read (2176 files) are data and live in the
Zenodo record as `analysis_inputs.tar` (912,896,000 bytes, sha256 `405062de2b3443f193e25d16d7b5b161f12098d518eb2149a19d19e333cc7046`), beside the 14 frozen tars of
per-call records.

## The one command

```
uv run --frozen python reproduce.py --data DIR [--work DIR] [--only s494|numbers|held] [--keep]
                                    [--skip-producer NAME ...]
uv run --frozen python reproduce.py --data DIR --download [--zenodo-url https://zenodo.org/records/<id>]
```

`DIR` is one data root: `DIR/frozen/<the 14 tars>` and `DIR/analysis_inputs.tar`. With `--download`, each file
`DATA_FILES.tsv` lists and `DIR` lacks is fetched from `<zenodo-url>/files/<name>?download=1`. The record id in
`ZENODO_URL` is a placeholder until the deposit exists (TO FILL AFTER DEPOSIT); give `--zenodo-url` meanwhile. Every
file is checked by sha256 before anything runs. Then:

1. a work copy (`DIR/work` by default): this folder plus `analysis_inputs.tar`, made a git repository with one commit,
   because S494 compares every output with git HEAD and its read audit refuses files HEAD does not hold;
2. stage `s494`: `scripts/S494_all_figures.py` rebuilds every plate and number step it knows from the frozen tars,
   compares each file byte for byte, runs S448 (the figure rules) on each plate and judges every read;
3. stage `numbers`: 22 further producers (Supplementary Figures 12, 13 and 18, the Supplementary Tables
   that need no model, Supplementary Data 1, the call counts, tokens and cost, the G17, G19 and G20 readings and
   others; `NUMBERS` in reproduce.py), each run by its own command under the
   same read audit and compared with the released copy, nothing masked;
4. stage `held`: 30 entries that need a model call, a person, the rating rows or data not in this release,
   checked by sha256, each printed with its reason (`HELD` in reproduce.py);
5. one pass table. Exit 0 only when every row passes.

Free space: about 7.3 GB for the tars, 6.8 GB when S494 extracts them inside the work copy, and 3 GB for the work
copy and its environments. S494 takes about 6 minutes on an M-series Mac once the tars are extracted. In the numbers
stage S581 takes about 4 minutes, and S565 about 12.5 hours: its 20 fits of 10,000 bootstrap refits each took 45,000 s
in all on 8 cores (`boot_seconds` in `findings/recompute/S565_corpus_interaction/model.json`).
`--skip-producer S565` leaves it out, and its row then reads FAIL "not run", so such a run never ends REPRODUCED.

## What "100%" means

1. Numbers, tables and Source Data (`.json`, `.md`, `.csv`, `.jsonl`, `.xlsx`): byte-equal with the released copy.
2. Plates (PDF, SVG, PNG): byte-equal on macOS with the font they were drawn with,
   `/System/Library/Fonts/Helvetica.ttc`, sha256 `25eceb458d4baf628ee0b6a135a9f8ac5ec7b2826646720834bd2bf00dfc825a`. reproduce.py records the font it finds; with any
   other font, or none, a plate that differs is reported "font differs", never as reproduced, and is to be checked by
   eye. Helvetica is Apple's and is not redistributed.
3. Held values: equal sha256, each with its reason.
4. The environment is part of the claim: `uv run --frozen` installs exactly `uv.lock` (one package, `minicheck`,
   comes from a git source, `pyproject.toml` `[tool.uv.sources]`), so every locked package must still be downloadable.
   One producer is outside `uv.lock`: S565 fits its model in R (`scripts/S565_corpus_interaction.R`, through
   `Rscript`); its committed outputs were made with R 4.5.2 and lme4 2.0.1
   (`findings/recompute/S565_corpus_interaction/header.json`), which a reader installs.

## What did not pass when this tree was built

The build measured the stages in a fresh clone of `e058482faa` (S494 exit 1). The producers' results then:
see `RELEASE_PROVENANCE.json` `producers`. Known today:

- Several producers' committed outputs were written before later commits to their scripts and carry the older
  script hashes, commits and dates (and in some, older figure folder names): those rows show "differ" with the json
  keys or lines that differ.

## What this release does not hold

The rating rows and rater identities (D168), the corpus PDFs and their text (publishers' copyright; the corpus
manifest and download script are in `publication/data/`), the chunk store, model weights (identified by digest in
`experiments/LOCK.toml` `[models]`), credentials, and the raw run folders beyond the frozen tars.
