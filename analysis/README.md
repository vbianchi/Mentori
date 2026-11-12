# Mentori analysis: the scripts that make the paper's figures, tables and numbers

Built by `scripts/S608_release_analysis.py` from Mentori-reanalysis commit `7c02e422b1`, copied from that commit
(git cat-file), never from a working tree. `RELEASE_PROVENANCE.json` lists every file and where it went.

## What is here

- `reproduce.py`: the one command (below).
- `scripts/`: 123 of the 796 scripts tracked in Mentori-reanalysis, the ones the stages run or
  import (measured by the read audit, `scripts/fig_read_audit.py`).
- `experiments/`: `LOCK.toml` (every model call's settings), `FIGURE_LOCK.toml` (every figure's rules), the runner,
  scorer and Mentori files the scripts import, and `rlm_ref/` (its own `pyproject.toml` and `uv.lock`).
- `findings/figures_provisional/`: every committed plate, Source Data workbook and legend draft, and
  `MANIFEST.sha256`; `findings/recompute/`: the committed outputs the stages are compared with.
- `data/`: the answer keys and prompt files the scripts read.
- `expected/MANIFEST.sha256`: the sha256 of every expected output (393 files), the held ones included.
- `DATA_FILES.tsv`: the files the data root must hold, with size and sha256.
- `pyproject.toml`, `uv.lock`, `.python-version` (Python 3.13.11): the environment, as the analysis ran.

792 files in git (101,734,702 bytes). The inputs the stages read (2198 files) are data and live in the
Zenodo record as `analysis_inputs.tar` (782,397,440 bytes, sha256 `d4407692af27bfa48ffe32795fa2fef60713654f79747370238a749ff62d621c`), beside the
15 frozen tars of per-call records and `stripped_records.tsv` (sha256 `df5c2ab0369ca10befd794926aed8038833ef436eff605d17df4b133a295b260`).

## The papers' text in the data (D316)

The corpus papers are not redistributed. In the frozen tars and in `analysis_inputs.tar`, the text sent to a model
that carried passages of the papers, the retrieved passages, the pipeline steps' tool outputs, the outputs of code a
model ran and the citation quotes are each replaced by
`{"stripped": true, "sha256": <sha256 of the replaced text>, "chars": <its length>, "passage_ids": [<chunk ids>]}`;
model-written text (answers, replies, code, judges' text) stays, as D316 decides, even where it quotes a paper, so
some kept answers still hold passages of the papers (the data record's README gives the count). `analysis_inputs.tar` before stripping had sha256
`27d93b99b37a1b3332c01bbe55dd3420cc3b426554b7fb49842f28696636e561`. `DATA_FILES.tsv` pins the stripped files by their own sha256, and `stripped_records.tsv` gives, per tar
and per member, the original's sha256 and the stripped one's.

The scripts are unchanged and check the originals' sha256 in many places. `reproduce.py` therefore lets a stripped
member stand for its original in every sha256 check, exactly as `stripped_records.tsv` maps it and nothing else (a
module it writes into the work copy's own environment; "THE PAPERS' TEXT" in its docstring). An output computed from
a replaced field cannot come out the same, so it is held, checked by its sha256, with the field it reads; where a
stage rebuilds it, the difference is shown in that stage's row, not hidden. The held outputs:

- `findings/recompute/S472_supp12a_steps.json` (Supplementary Figure 12a step rows; written by S494 step fig4 (scripts/S472_fig4_panels.py); reads answers.json .results[].generation.steps[].raw_content, a pipeline step's tool output, replaced by the stripped object: the script takes its len(), which is 4 (the object's keys), not the text's length): each step row's output length (rows[][5]) and the totals after it are computed from the replaced text; the stripped object's chars field holds that length, which the script does not read
- `findings/figures_provisional/fig4/figure5_provenance.json` (Figure 5 provenance; written by S494 step fig4 (scripts/S472_fig4_panels.py); reads answers.json .results[].generation.steps[].raw_content, a pipeline step's tool output, replaced by the stripped object: the script takes its len(), which is 4 (the object's keys), not the text's length): q82.<setup>.largest_chars and the largest step output it reproduces are computed from the replaced text; the plate and Source Data Fig. 5 rebuild byte-equal
- `findings/recompute/distiller_count_g3_d1/distiller_count_g3_d1.json` (distiller firing count, draw 1; written by S494 step numbers (scripts/distiller_count_g3_d1.py); reads answers.json .results[].generation.steps[].raw_content, a pipeline step's tool output, replaced by the stripped object: the script takes its len(), which is 4 (the object's keys), not the text's length): largest_step_output.chars and the check against RUNNING.md's 26 Oct count are computed from the replaced text

## The one command

```
uv run --frozen python reproduce.py --data DIR [--work DIR] [--only s494|numbers|held] [--keep]
                                    [--skip-producer NAME ...]
uv run --frozen python reproduce.py --data DIR --download [--zenodo-url https://zenodo.org/records/<id>]
```

`DIR` is one data root: `DIR/frozen/<the 15 tars>`, `DIR/analysis_inputs.tar`, `DIR/stripped_records.tsv`
and, optionally, `DIR/ratings.tar`
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

The build measured the stages in a fresh clone of `7c02e422b1` (S494 exit 1). The producers' results then:
see `RELEASE_PROVENANCE.json` `producers`. Known today:

- Several producers' committed outputs were written before later commits to their scripts and carry the older
  script hashes, commits and dates (and in some, older figure folder names): those rows show "differ" with the json
  keys or lines that differ.

## What this release does not hold

Rater identities and notes (D168; the anonymised rating rows are `ratings.tar` in the data record), the corpus PDFs and their text (publishers' copyright; the corpus
manifest and download script are in `publication/data/`), the chunk store, model weights (identified by digest in
`experiments/LOCK.toml` `[models]`), credentials, and the raw run folders beyond the frozen tars.
