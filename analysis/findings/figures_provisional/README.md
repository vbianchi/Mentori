# findings/figures_provisional

This folder holds the final figures of the revised paper; it keeps its working name (D315 Q3).

One folder per plate: main Figures 1 to 7 (`fig1/`, `fig2_human/`, `fig3_strategies/`, `fig4_depth/`, `fig4/`, `fig5/`,
`fig6/`; D283's folder names) and Supplementary Figures 1 to 18 (`supp_fig<N>*/`): 25 plates, 20 of them in steps of S494.
The other five are built outside it: Figure 2 and Supplementary Figure 3 by `scripts/S531_fig2_s3_plates.py` (`--raters 0`
gives the frames), Supplementary Figures 12, 13 and 18 by S543, S570 and S542 (`figure`). Supplementary Figures 10 and 11
are a step, but it draws their frames: the committed plates are `scripts/S524_t3_s12_s13.py figure --t3 <T3 frozen set>`.
`supp_tables/` holds the Tables; `supp_data1_answer_key/` holds the answer key, Supplementary Data 1.

**Numbering (D302, Valerio, 7 November 2026: "Q1: drop them"; the manuscript tab's order of first citation).** Every
Supplementary figure is cited, 1 to 18. D257's number to D302's: 1 to 4 and 9 to 11 keep theirs; 6 to 5
(`supp_fig5_false_premise`), 5 to 6 (`supp_fig6_replication`), 8 to 7 (`supp_fig7_package_caps`), 7 to 8
(`supp_fig8_depth`), 19 to 12 (`supp_fig12_signal_pairs`), 14 to 13 (`supp_fig13_i2_reuse`), 12 to 14
(`supp_fig14_fig6_failures`), 23 to 15 (`supp_fig15_fig6_pairs`), 13 to 16 (`supp_fig16_fig6_models`), 15 to 17
(`supp_fig17_outcomes`); 18 keeps its number (`supp_fig18_evaluators`). The answer key is Supplementary Data 1 (7
before). Dropped, not cited: D257's 16 (score 3, S463 no longer writes it), 17 (corpus, S484, no step), 20 (examples,
S544), 21, 22 and 24 (code-generation difficulty, operations and cost, S481). Under D257 (5 November) the order was:
1, 2, 3 kept; 14 to 4, 7 to 5, 4 to 6, 8 to 7, 10 to 8, the pipeline schematic 9, 12 to 10, 13 to 11, 20 to 12, 19 to 13,
25 to 14, 6 to 15, and the uncited held as 16 to 24. The depth fit (S485, Supplementary Figure 11 until 2 November)
stays removed. The dated state notes below keep the numbers they were written under. Every figure is drawn in
Python (matplotlib) by one script in `scripts/`. No build calls R: the R scripts of the earlier round (Figures 2 to 5,
`resubmission/09_code/scripts/S282_figure2.R` to `S288_figure5.R`) are not used.

## Reproduce every figure

One command, from the root of a clone of this repository (D155):

    uv run python scripts/S494_all_figures.py

**What it needs, and nothing else.**
- A full `git clone` of this repository, on branch `main`, with its `.git` folder and history: not a source
  archive (a Zenodo zip or a GitHub "Download ZIP") and not a shallow clone. S494 reads the committed files with
  `git ls-tree`, `git cat-file` and `git diff`, and figure scripts read earlier versions of files with
  `git show <commit>:<path>` (S459, among others), so without the history the build stops.
- Python 3.13.11, which `.python-version` pins (uv installs it when it is missing). The provenance files record the
  interpreter's version, so under another release those files differ even where every plotted number is equal.
- `uv` (https://docs.astral.sh/uv/). `uv run` installs the locked Python packages of `uv.lock`; for Supplementary
  Figure 8, S494 itself runs `uv sync --frozen` in `experiments/rlm_ref` (its own `uv.lock`), because the legend
  cites the installed `rlms` package's metadata. On the first run uv downloads those packages.
- The folder of the ten frozen tars (about 5.2 GB, 4.8 GiB, in all; each listed with its sha256 in
  `findings/recompute/frozen_inputs/SHA256SUMS`). Default `~/Mentori_scratch_keep/frozen_2026-10-26`; any other
  folder with `--tars DIR` or the `FROZEN_TARS` variable. After the Zenodo deposit, the folder its tars were
  downloaded to.

**What it does.**
1. Checks every frozen input against `findings/recompute/frozen_inputs/SHA256SUMS`: the committed sets under
   `findings/recompute/<set>_inputs/` file by file, and the tars by sha256. Each tar is extracted once (into the
   gitignored `findings/recompute/frozen_inputs/extracted/`) and every extracted file is checked against the
   committed list of the tar's files, `findings/recompute/frozen_inputs/members/<tar>.sha256`, none missing.
2. Runs each figure's own build command into a fresh temporary folder, never into this one, in dependency order. In
   a check run (not under `--write`) step `d181` comes first: S471, S474 and S514 rebuild the concept-recall and
   panel c folders. Then Figure 3 with Supplementary Figure 6 (S522, S463, S523), Supplementary Figure 5 (S532),
   8 (S476: S474's L2 rows, T1 and G4 first), Figure 4 (S480's recount, then
   S472), 5 (S497, the plate D166 locked), 6 (draw_B.py's anchor, then S481), Supplementary Figure 2 (S461), then
   Figure 1 (S456), which reads
   the legend drafts of all of these (at git HEAD in a check run, so it is blocked when one of them fails; from the
   working tree under `--write`, where they were just rewritten, so one `--write` pass suffices; audit 27 Oct F1b),
   then Supplementary Figures 17 (S457), 7 (S459, after
   `experiments/rlm_ref/.venv` is checked against its lock, made when the check fails, and the step refused with
   the reason when it cannot be made), 14 to 16 (S481), 10 and 11 (S524's frames), 4 (S541) and 9 (S590).
   Figure 3 reads Supplementary Figure 17, so a `--write` pass that renumbers or rebuilds it runs that first (D302 did:
   `--only supp8 --only supp17 --only supp7 --only supp14_16`, then the rest). The number scripts
   S486 to S492 and `distiller_count_g3_d1.py` run next, each judged on its own, then step `need_map` (S526, S527 and
   S519 `--check`); then Supplementary Figure 1 (S496, the experiment
   graph, D160 (9)), which reads S492's registry, `experiments/draws.csv` and Figure 1's provenance.
3. **The read audit**, on by default. Every Python process of every build step runs under an audit hook
   (`scripts/fig_read_audit.py`, loaded through `scripts/fig_read_audit_site/` on `PYTHONPATH`) that logs every file
   it opens, lists or globs, and every child process it starts. A step fails when it reads a file outside the
   repository and outside the allowed folders, or a repository file that git HEAD does not hold (untracked or
   gitignored) or that differs from HEAD in the working tree (measured again before each step); when it writes into
   the repository during an `--out` run; or when it starts a child process that is not on the audit's allow list
   (audit 27 Oct F3, `fig_read_audit` section 3). A child is accepted only in the environment its parent process
   started with (no variable added, removed or changed, except four that change no read: `PYTHONHASHSEED`, which
   five builds set to 0 when they start themselves again, and `HF_HUB_OFFLINE`, `TOKENIZERS_PARALLELISM` and
   `TQDM_DISABLE`, which the scorer modules set on import), and only as one of three kinds: a Python of the repository's
   venvs (or `uv run --frozen python`, inside the repository) without `-I`, `-E` or `-S`, which loads the hook and has
   its own reads judged; git with a read-only subcommand and option from `GIT_READ` (`cat-file`, `show`, `log`,
   `ls-files`, `status`, `rev-parse`, `merge-base`, `hash-object`), or `init`, `add` and `commit` in a folder the step
   made; or a shell string pinned by sha256 in `fig_read_audit.REVIEWED_SHELL` (one: S472's selftest of its `.git`
   reader), run in a folder the step made. Any other program (`cat`, `tar`), any wrapper word (`env`, `nice`,
   `time`), any shell string not pinned (`os.system` and `shell=True` included, whatever it holds), any other git
   subcommand or option and any changed environment fail the step as unaudited, whatever the arguments. The lists
   are what the plates' builds start (18 then; 19 with Supplementary Figure 1): 175 child processes on a fresh clone (27 October). An accepted child's path
   arguments are judged as reads, and `git show` or `git cat-file <rev>:<path>` counts as a read of `<path>`, so a step
   reading a committed output that way is blocked when its owner fails (F1b). Such a read is accepted only when
   `<rev>` resolves to HEAD's commit or an ancestor of it (`git rev-parse --verify`, `git merge-base --is-ancestor`);
   the index (`:<path>`), a stash, a commit HEAD does not reach and a revision that does not resolve fail the step,
   as content not committed on main (audit 27 Oct R4, R5). Allowed: the ten tars `SHA256SUMS` names (not
   anything else kept in their folder), the extracted folder, the interpreter and its standard library,
   site-packages and the venvs, the uv cache, matplotlib's font cache,
   `/dev`, temporary folders and files the step itself makes, and this run's output folder (the list is
   `fig_read_audit.Context` and `PLATFORM`). Operating-system files a build reads (the system Helvetica, which
   `experiments/FIGURE_LOCK.toml` `[type] font_families` names, the time zone database, the MIME table, the macOS
   version file) are allowed and printed under the table. The audit is a check against accidental reads of
   uncommitted or outside files, not a sandbox against code written to evade it. What it cannot see: a file opened
   by C or Rust code inside a Python process (no figure script uses such a reader), a child started without an
   audit event (from C code), and what an allowed git or the reviewed shell string reads beyond its path arguments
   (git's object store and its own configuration); a repository folder given to a child is judged as a listing, not
   file by file. Known evasions it does not try to catch, since each needs code written to evade it: an environment
   changed below `os.environ` (`os.unsetenv`, `os.putenv`, a `preexec_fn`); git run in a folder the step made whose
   `.git` points or links to another repository; a git hook planted in a repository the step made; and files opened
   through `ctypes` or other C code (`fig_read_audit` LIMITS).
4. Compares every file written with the committed file at git HEAD, and a plate's files also with
   `MANIFEST.sha256` in this folder (the sha256 of every committed plate file).
5. Runs S448, the figure-rules check (`experiments/FIGURE_LOCK.toml`), on every rebuilt plate, under the step's
   read audit. A plate passes only when every rule `FIGURE_LOCK.toml` tags for S448 (R1 to R12) reports PASS or
   WARN and none FAILs.
6. **Blocked steps.** A step that reads (by the audit) a committed output of a step that failed, or was itself
   blocked, is reported "blocked by <step>" and its outputs are not compared: its build used an output nobody
   proved. When the frozen inputs fail, every step is blocked.
7. Prints one table: figure, files, byte-equal (or "blocked by"), S448, audit (the number of reads judged
   violations), seconds; then every difference, violation and block. Exit status 0 means every frozen input
   checks, every step exits 0 with no audit violation, every file is byte-equal and every plate passes S448.

Options: `--out DIR` to keep the rebuild in a folder of your choice, `--only fig3` (or `d181`, `fig1`, `fig4`, `fig5`, `fig6`, `supp2`,
`supp4`, `supp6`, `supp7`, `supp8`, `supp9`, `supp10_11`, `supp12_24`, `supp15`, `supp17`, `supp1`, `numbers`, `need_map`, `frozen`) to run one step (a read of a step not run
is then noted as held to git HEAD only; without `frozen` the frozen inputs are not checked, and a run whose steps all
pass ends "PARTIAL" and exits 1), `--tars DIR` for the tar folder, `--keep` to keep the temporary folder,
`--no-audit` to run without the read audit (the run then ends "NOT VERIFIED" and exits 1).
`uv run python scripts/S494_all_figures.py manifest --check` checks `MANIFEST.sha256` against git HEAD; `manifest`
rewrites it after a plate is recommitted. Tests: `uv run python scripts/S494_all_figures_test.py`.

**The formats.** Each plate folder holds, for Figure N:

| File | What it is |
|---|---|
| `Figure N (...).pdf` | the file uploaded to the journal (`FIGURE_LOCK.toml` `[files] upload_format = "pdf"`): vector, fonts embedded (Helvetica, TrueType), no date in it |
| `Figure N (...).svg` | the same drawing as SVG; S448 R10 checks its text and shapes against the PDF |
| `Figure N (...).png` | a preview: the PDF rasterised at 600 dpi (4,323 pixels across, 183 mm), held equal to the PDF pixel for pixel by S448 R7 |
| `Source Data Fig. N (...).xlsx` | the numbers behind every panel, one sheet per panel (editor's row 20); no write time inside |
| `Source Data Fig. N caption (...).md` | the Source Data caption |
| `legend_draft.md` | the figure legend draft |
| `figure<N>_numbers.json`, `figure<N>_provenance.json` | the plotted numbers, and the sha256 of every input, script and output |

Supplementary figures use the same files under "Supplementary Figure N" and "Supplementary Figure N data"
(`supplementary_figure<N>_numbers.json`, `supplementary_figure<N>_provenance.json`). No TIFF is made: the journal
accepts PDF ("Preferred figure formats are: PDF, EPS, AI, or PS"), and `FIGURE_LOCK.toml` `[files] upload_format` is
`pdf`. A TIFF would be a raster held to the journal's 1,200 dpi for line art, which the vector PDF does not need.

**Figure 6's `records_manifest.json`.** Its provenance names `scripts/S447_fig6_panels.py` sha256 4fc9bdfb, flagged dirty, which is in no commit: the mirror ran from an uncommitted working copy at 14:02 CEST on 22 October. The nearest commit is 49e55fe0, 14:22 the same day, which committed this manifest. The manifest's contents are checked against the frozen tar and S494 holds it as an input, so only the code that wrote it is unrecorded. Do not mirror again to fix this: a new manifest sha256 makes S447 refuse S477's file.

**Inputs kept in a plate folder.** Six committed files in these folders are read by a build and are not written by
it, so S494 checks them against git HEAD as inputs and does not rebuild them: Figure 6's `claims.md`,
`fig6_cells.csv`, `fig6_numbers.json` and `records_manifest.json` (S447's draw and its mirror of the records),
Supplementary Figure 6's `records_manifest.json` (S457's mirror) and `findings/recompute/G4_fig3c/
anchor_d149_rlm10.json` (S476's D149 anchor). Figure 6's four are an exception to D155's "every output is
deterministic" (audit of 27 October, F11): `scripts/S447_fig6_panels.py draw` writes its write time into
`fig6_numbers.json` (`written_utc`, 2026-10-24T09:05:42Z) and the scratch `--view-dir` path of the machine that drew
them into `fig6_cells.csv`'s header, and sets `clone_commits_have_d80` with `git merge-base --is-ancestor`, which
reads False wherever git cannot answer (a source archive, a clone without that history). Run again, the draw would
not give the same bytes, so the one command does not run it; it reads the committed files as inputs, checked against
git HEAD, and S481 and S447 reproduce every number from the frozen S2 records before drawing. S447's draw is not
changed.

**State, 2 November 2026 (the current one).** Checked at 72dc453f, after the figure build (3086d753 onward) and Figure
1's rebuild, in the working copy and not on a fresh clone, so the fresh-clone runs below have not been repeated.
`uv run --frozen python scripts/S494_all_figures.py`, no `--only`, read audit on: exit 0, "ALL EQUAL AND PASSING", 958
of 958 committed frozen files equal `SHA256SUMS`, 25 plates, 257 of 257 compared files byte-equal, S448 12 rules PASS on
every plate (1 warning each: the provisional file name), audit 0 on every step, 466 s. `S494 manifest --check`: exit 0,
240 files. `figure_names_test.py --all`: 27 of 27 folders clean.

- **Left out of S494.** Figure 2 and Supplementary Figure 3. `S531 --raters 0` rewrote both folders with no change in
  git, and S448 passes on both. S494 prints no line saying they are left out.
- **Built without Papers.** The D200 Figure 5 (fc3493ae, review fixes f4041e75), "0 of 516": 5c and 5e on the
  re-run answers (`findings/recompute/fig5_d200_inputs`); panels b and g and every Papers part of a, c, d and e are
  empty, their Source Data cells blank, until S564's selection (D208) is frozen and read. 5d keeps its old three-part
  bars (Valerio's note of 2 November, experiments/README.md:1225-1229, reversing FF18 a). The Judge and Concepts counts of 5d are on W (86 questions while Papers
  waits) and can change when Papers is read.
- **Not built.** Supplementary Figures 15 to 17: code and tests only, no plate. They wait for the frozen Papers set.
- **Frames, no value drawn.** Figure 2, Supplementary Figures 3, 7, 12, 13 and 14, and Figure 3e (3f before D218). Supplementary
  Figures 7 and 14 and Figure 3e hold until S518 runs on Valerio's word (D195); 12 and 13 wait for T3; 2 and 3 for the ratings.
- **Provisional counts.** Figures 3 and 4 and Supplementary Figures 4 and 8 still hold answers on key v2.4 while S6 runs;
  each stamp gives its count. `findings/recompute/S512_s6_v25/` and `findings/recompute/S520_inputs/` are not committed,
  so Figure 1's total of LLM calls comes from S520's committed summary and cannot be rerun from the repository until
  those inputs are frozen. Then `S494 --write` for `fig1` and `supp1`.
- **Tracked scripts.** All 80 script names in the 27 provenance files are in `git ls-files`. `git grep` over `scripts/`
  for `scratch_archive`, `mock_scripts`, `Mentori_scratch_keep` and `/private/tmp` gives 45 lines and no import: 26
  docstring or comment notes, 14 test strings and 5 code lines. Of the 5: `fig_repro.py:69` is the default folder of the
  frozen tars (each tar checked against `SHA256SUMS`; `FROZEN_TARS` or `--tars` replaces it); `S465_r_views_adapter.py`
  lines 116, 118 and 120 are three default read paths of a script that is in no provenance file and no S494 step;
  `S521_valerio_reading_pack.py:66` is a default output folder. Until 72dc453f S521 loaded `marks.py` from the archive;
  it now loads `scripts/minicheck_marks.py`, the same bytes.
- **Language.** S172 reads no legend file. A person read all 27 legends on 2 November and found no word of the editor's
  list. S172 itself exits 1 on the manuscript's sentence counts against its baseline; no manuscript or letter commit
  falls in this round.

**State, 27 October.** Verified 27 October 2026 on two fresh clones of `main` at d2b91721, each made with `git clone` and
`uv sync`, nothing copied in and no environment variable set: the bare command exited 0 with "ALL EQUAL AND PASSING"
(five runs, 108 to 139 s). 18 of 18 plates byte-equal (152 plate files, 72 of them PDF, SVG, PNG and xlsx), the
derived steps and the eight number outputs byte-equal (174 of 174 compared files), S448 12 rules PASS on every plate
(1 warning each: the provisional file name), audit 0 on every step; two runs into two folders gave identical sha256
for all 185 files written. An audit hook of each verifier's own, independent of this one, saw no read of the sibling
checkout `~/projects/Mentori-paper`, no read of an untracked or modified file and no network connection. Outside the
clone a run reads only the ten tars, uv's interpreter and cache, matplotlib's font cache and the operating-system
files printed under the table (`/System/Library/Fonts/Helvetica.ttc`, the MIME table, the Europe/Amsterdam zone
file, the macOS version file). Byte equality therefore holds on macOS with that Helvetica and under Python 3.13.11
(`.python-version`); another system draws the same figures with different font bytes, and another Python release
writes another version into the provenance files. Since then the audit judges a `.pyc` read as its source `.py` (a fresh
`.pyc` used to hide an uncommitted edit to an imported module). After any commit to a script or input a plate
records, run `S494 --write`, then `S494 manifest`, so the recorded sha256 stay current.

Re-verified 27 October 2026 after D156 (Figure 3 and Supplementary Figure 4 on G4's final judging, Figure 3's S3
inputs refrozen: `g4_collect.jsonl` 8f10e30a) on a fresh clone of `main` at 766f6821, made the same way: exit 0, "ALL
EQUAL AND PASSING", 18 of 18 plates and 174 of 174 compared files byte-equal, S448 12 rules PASS on every plate (1
warning each), audit 0 on every step, 854 of 854 committed frozen files equal `SHA256SUMS`, 139 s.

Not equal since then (audit of 27 October, F1): Figures 1 and 4 hashed live design files (plan.csv, draws.csv,
`experiments/README.md`, `LIST.md`, the run code, the letter), so the dashboard commit fc3b67d5 and the decision and
D158 commits after it made their provenance (and Figure 1's stamp, legend, caption and numbers) differ, with every
plotted number equal. S456 and S472 now record those files' sha256 as they stood at a pinned commit, `DESIGN_AT`
(7e4a13f9 for Figure 1, 96936742 for Figure 4, the commits whose files give every sha256 the committed plates
recorded), so a later commit to them no longer moves a plate; a design change reaches a plate when its `DESIGN_AT`
is moved. Every check, claim lookup and tripwire reads the documents as they stand (corrected in part 4, below: for
a day the pin had moved the checks onto `DESIGN_AT` too), and a value a plate draws from them must be the same at
`DESIGN_AT` as today, or the build stops.

Re-verified 27 October 2026 after the audit's fixes (parts 1 and 2): `S494 --write` and `S494 manifest` rewrote the
committed legends, captions, Source Data and provenance (a16b2460, 1c61f708; no PDF, SVG or PNG changed), and Figure 1
was rebuilt once more (e3f7d01d, de61e138) because S456 hashes the Figure 2 to 6 and Supplementary Figure 2 legends
from git HEAD and runs first, so one `--write` pass leaves it a round behind. A fresh clone of `main` at de61e138, made
the same way: exit 0, "ALL EQUAL AND PASSING", 18 of 18 plates and 174 of 174 compared files byte-equal, S448 12 rules
PASS on every plate (1 warning each), audit 0 on every step, 854 of 854 committed frozen files equal `SHA256SUMS`,
139 s. In that clone a local commit appending a line to `experiments/README.md` and `experiments/plan.csv` left
Figures 1 and 4 byte-equal (`--only frozen --only fig1 --only fig4`: exit 0, 8 of 8 and 10 of 10).

Re-verified 27 October 2026 after part 4 of the audit's fixes (its verifier's F1, F1b, F3: 10e8510a, 4845e835). F1:
the checks read the live documents again. S456 runs every check and tripwire on its files at git HEAD (draws.csv's
T2 "design to come", G3 "wave 2 not run", G9 "done", the design and draws columns, the reproduce-first numbers) and
computes what the plate draws a second time from the design files at `DESIGN_AT`, stopping when the two differ;
S472's claims list and its plan.csv check read the working tree, and exp_03's stress set-ups must equal
`DESIGN_AT`'s. Only `inputs_sha256` records `DESIGN_AT`. F1b: Figure 1 runs after the figures whose legends it reads,
reads them from the working tree under `--write`, and is blocked by a failed one (the audit counts `git cat-file`
or `git show <rev>:<path>` as a read of `<path>`). F3: `os.system`, `shell=True` and `env -u` children are judged.
One `S494 --write` pass (43f6376f) changed 3 files (Figure 1's and Figure 4's provenance, `distiller_count_g3_d1.json`;
no PDF, SVG, PNG, legend, caption or Source Data), then `S494 manifest` (747976f4). That `--write` run's own audit
showed one read, Figure 5's staging PNG (`fig5.staging/`), which S473 writes from C code inside the repository only
under `--write`; the audit module before part 4 gives the same verdict on the same logs. A fresh clone of `main` at
747976f4, made the same way: exit 0, "ALL EQUAL AND PASSING", 18 of 18 plates and 174 of 174 compared files
byte-equal, S448 12 rules PASS on every plate (1 warning each), audit 0 on every step, 854 of 854 committed frozen
files equal `SHA256SUMS`, 142 s. In that clone, each probe a local commit: plan.csv and draws.csv rewritten by
`csv.writer` with T2's status changed, and a line appended to `experiments/README.md`, left Figures 1 and 4
byte-equal (exit 0, 8 of 8 and 10 of 10); a reworded `LIST.md` claim made Figure 4's `claims.md` read "NOT FOUND"
(exit 1, `claims.md` differs); draws.csv's T2 design without "design to come" made S456 refuse (exit 1, "draws.csv T2
no longer says 'design to come'"), where S456 before part 4 wrote the plate; and a stale line committed to Figure 2's
legend, then one `--write --only fig2 --only fig1` pass and a commit, gave `--only frozen --only fig2 --only fig1`
exit 0, 11 of 11 and 8 of 8 (Figure 1 recorded the rebuilt legend, 8cc0c46c, not HEAD's stale 8b11767c).

Re-verified 27 October 2026 after the audit's child processes moved from a block list to an allow list (F3, second
pass: d9c07acb). The verifier had found children that passed the block list: `nice` or `time` before `env -u
FIG_READ_AUDIT_DIR`, an `env=` mapping that redirected or dropped `FIG_READ_AUDIT_DIR`, and `~` or brace expansion
in an `os.system` string. A census of every child the builds start, on two fresh clones, gave 175: git 157
(`/usr/bin/git`), Python 13 (5 venv `python3`, 8 `uv run --frozen python`), S472's reviewed bash string 5; 160 in
their parent's environment unchanged, 5 with `PYTHONHASHSEED` and 10 with the three Hugging Face and tqdm switches.
Those are the allow list (item 3). No committed output records the audit module or S494, so no `--write` pass was
needed, and `S494 manifest` left `MANIFEST.sha256` unchanged (157 plate files). A fresh clone of `main` at d9c07acb,
made the same way: exit 0, "ALL EQUAL AND PASSING", 18 of 18 plates and 174 of 174 compared files byte-equal, S448
12 rules PASS on every plate (1 warning each), audit 0 on every step, 854 of 854 committed frozen files equal
`SHA256SUMS`, 141 s. In that clone the verifier's 15 probes each give a violation. Three of them fail only on
`<string>`: the probe's own `-c` code is a syntax error, so no child starts; its corrected twin in the second probe
file fails as an unaudited child. `S494_all_figures_test.py` has 106 of 106 PASS. On the module before this pass, 15
of its 18 probe tests give no violation at all.
