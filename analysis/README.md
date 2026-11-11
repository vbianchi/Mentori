# Mentori analysis: the scripts that make the paper's figures, tables and numbers

Built by `scripts/S608_release_analysis.py` from Mentori-reanalysis commit `d40237595b`, copied from that commit
(git cat-file), never from a working tree. `RELEASE_PROVENANCE.json` lists every file and where it went.

## What is here

- `reproduce.py`: the one command (below).
- `scripts/`: 123 of the 794 scripts tracked in Mentori-reanalysis, the ones the stages run or
  import (measured by the read audit, `scripts/fig_read_audit.py`).
- `experiments/`: `LOCK.toml` (every model call's settings), `FIGURE_LOCK.toml` (every figure's rules), the runner,
  scorer and Mentori files the scripts import, and `rlm_ref/` (its own `pyproject.toml` and `uv.lock`).
- `findings/figures_provisional/`: every committed plate, Source Data workbook and legend draft, and
  `MANIFEST.sha256`; `findings/recompute/`: the committed outputs the stages are compared with.
- `data/`: the answer keys and prompt files the scripts read.
- `expected/MANIFEST.sha256`: the sha256 of every expected output (393 files), the held ones included.
- `DATA_FILES.tsv`: the files the data root must hold, with size and sha256.
- `pyproject.toml`, `uv.lock`, `.python-version` (Python 3.13.11): the environment, as the analysis ran.

792 files in git (101,712,084 bytes). The inputs the stages read (2198 files) are data and live in the
Zenodo record as `analysis_inputs.tar` (927,846,400 bytes, sha256 `27d93b99b37a1b3332c01bbe55dd3420cc3b426554b7fb49842f28696636e561`), beside the 14 frozen tars of
per-call records.

## The one command

```
uv run --frozen python reproduce.py --data DIR [--work DIR] [--only s494|numbers|held] [--keep]
                                    [--skip-producer NAME ...]
uv run --frozen python reproduce.py --data DIR --download [--zenodo-url https://zenodo.org/records/<id>]
```

`DIR` is one data root: `DIR/frozen/<the 14 tars>`, `DIR/analysis_inputs.tar` and, optionally, `DIR/ratings.tar`
(the anonymised rating rows; ratings.tar pinned (sha256 f0ae63f00c51)). With `--download`, each file
`DATA_FILES.tsv` lists and `DIR` lacks is fetched from `<zenodo-url>/files/<name>?download=1`. The record id in
`ZENODO_URL` is a placeholder until the deposit exists (TO FILL AFTER DEPOSIT); give `--zenodo-url` meanwhile. Every
file is checked by sha256 before anything runs. Then:

1. a work copy (`DIR/work` by default): this folder plus `analysis_inputs.tar`, made a git repository with one commit,
   because S494 compares every output with git HEAD and its read audit refuses files HEAD does not hold;
2. stage `s494`: `scripts/S494_all_figures.py` rebuilds every plate and number step it knows from the frozen tars,
   compares each file byte for byte, runs S448 (the figure rules) on each plate and judges every read;
3. stage `numbers`: 24 further producers (Supplementary Figures 12, 13 and 18, the Supplementary Tables
   that need no model, Supplementary Data 1, the call counts, tokens and cost, the G17, G19 and G20 readings and
   others; `NUMBERS` in reproduce.py), each run by its own command under the
   same read audit and compared with the released copy, nothing masked;
   With `ratings.tar` in the data root, `RATED` then redraws Figure 2 and Supplementary Figure 3: S530 and S531
   `--raters 2` by their committed commands, each plate folder compared file by file with the released copy. S530
   runs with `MENTORI_GENERATED_AT` set to the one line of `ratings.tar`'s
   `findings/recompute/S530_human_signals/generated_at.txt`, the time its released run wrote into `results.json`, so
   that file comes out with the sha256 both plates' provenance files record (D315). A `ratings.tar` without that member
   leaves the variable unset: S530 then stamps the current time, and the two provenance files differ in that one
   sha256 (the row shows them as differing; every plotted number is unchanged);
4. stage `held`: 28 entries that need a model call, a person, the rating rows or data not in this release,
   checked by sha256, each printed with its reason (`HELD` in reproduce.py; Figure 2 and Supplementary Figure 3 only
   when `ratings.tar` is absent);
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

The build measured the stages in a fresh clone of `d40237595b` (S494 exit 1). The producers' results then:
see `RELEASE_PROVENANCE.json` `producers`. Known today:

- Several producers' committed outputs were written before later commits to their scripts and carry the older
  script hashes, commits and dates (and in some, older figure folder names): those rows show "differ" with the json
  keys or lines that differ.

## What this release does not hold

Rater identities and notes (D168; the anonymised rating rows are `ratings.tar` in the data record), the corpus PDFs and their text (publishers' copyright; the corpus
manifest and download script are in `publication/data/`), the chunk store, model weights (identified by digest in
`experiments/LOCK.toml` `[models]`), credentials, and the raw run folders beyond the frozen tars.
