# Using the method on your own papers

This guide is for a scientist who wants to test a question-answering system on papers from their own field, the way
the paper tests Mentori. You choose a few papers, write the right answers to some questions about them, let several
answering strategies answer, and score every answer three ways. Where the three scores disagree, you read the answer
yourself.

We followed this guide once, on five papers about downy mildew resistance in lettuce (the "I2" run, decisions D74 and
D160 in `experiments/README.md`). Each step ends with what we used for I2, so you can compare.

Everything runs from this repository, with `uv`. Every command below starts in the repository's top folder.

## What you need

- A computer with at least 2 GB of free memory while answers are made, and 4 GB while MiniCheck scores them (the
  tools stop or do not start under these). The search model (bge-m3) and the reranker run on the CPU inside the
  answering process.
- A Gemini API key in `~/.config/mentori-runs/keys.env` (a line `GEMINI_API_KEY=...`). The answers are written by
  `gemini-3-flash-preview`, the model of the paper's Figure 2.
- An Ollama server, version 0.40.2, holding the two models the lock file names (`experiments/LOCK.toml`, section
  `[models]`): `devstral-small-2:24b` (the judge) and `gpt-oss:20b` in its date-fixed copy
  `gpt-oss:20b-date20261010` (the checker inside the "verified pass" strategy). The lock file also fixes every setting
  sent to every model. Do not change it: the scores are only comparable with the paper's under it.
- The paper's own 20 PDFs (`datasets/v4_papers/core/` of the Mentori-paper checkout), for one check in step 3.

## Step 1. Choose your papers and fetch them

Pick a small set of papers that you know well and that you may share (an open licence, such as CC BY). Five is enough
to see the method work; it is not enough to rank strategies.

List them in a table with one row per paper, in the format of `experiments/reuse_demo/corpus_papers.csv`: a number,
the bucket `core`, the file name you want (start it with the number, `01_...pdf`), title, field, DOI, PMCID, a
download link, the licence and whether you may share it. Then fetch them:

    uv run python zenodo/10_data/upstream/publication/data/download_papers.py \
        --csv my_corpus/corpus_papers.csv --output my_corpus

The PDFs land in `my_corpus/core/`. A paper that fails to download is listed with its link; fetch it by hand into the
same folder.

**I2:** five CC BY papers (Parra 2021, Simko 2013, Christopoulou 2015, Giesbers 2017, Pelgrom 2019), fetched from
NLM's PMC open-access bucket (`experiments/reuse_demo/download_log.txt`). The PDFs are not in the repository
(`experiments/reuse_demo/.gitignore`); the table gives their links.

## Step 2. Write the answer key

The answer key holds, for each question, the right answer and the evidence for it. It is the "curated ground truth"
the scores are measured against, so it is the step that takes most of your time.

Write it as a JSON file in the format of the paper's key (answer key v2.4, `data/ground_truth_v2/all_v2_4.json`):
a field `"format": {"version": "2.4"}` and a list `"records"`, one per question, each with:

| Field | What it holds |
|---|---|
| `id` | a short name, no spaces (for example `PB_001`) |
| `question` | the question as the system will see it |
| `category` | a label of your choice (for example `factual_recall`) |
| `answer_type` | `extractive` (the answer is stated in one paper), `synthesis` (it needs several papers), `refutation` (the question states something false, and the answer says why), or `not_answerable` (the papers do not hold the answer) |
| `question_answerable` | `false` for `not_answerable`, `true` for the other three |
| `short_answer` | the right answer, in full sentences |
| `synthesis_statement` | for a synthesis question, how the papers combine (optional otherwise) |
| `key_concepts` | the facts an answer must contain, each `{"phrase": "...", "evidence_index": <n>}`: the phrase copied word for word from evidence sentence number n (counted from 0); an empty list for `not_answerable` |
| `evidence` | the sentences that support the answer, each `{"paper": <file name without .pdf>, "page": <page, from 1>, "sentence": "..."}`, copied exactly from the paper's text |
| `support` | the same sentences in the form the quote check reads, in the same order: `{"paper": <file name with .pdf>, "page": <page>, "quote": "..."}` |
| `min_core` | the number of papers in your corpus for an answerable question, `null` for a not-answerable one |

Mix the four answer types. A not-answerable question and a question with a false premise test whether the system
says "the papers do not say" instead of inventing an answer.

Make a text file per paper, one string per page, put the key file in `my_corpus/` too, and check that every quoted
sentence is on its page and every key concept is inside its sentence:

    uv run --project experiments/mentori --frozen python experiments/reuse_demo/page_text.py \
        --corpus my_corpus/core --out my_corpus/text
    uv run python experiments/reuse_demo/check_quotes.py my_corpus my_key.json

The check prints, for every quote, whether it is on its page (also when only spacing or a word broken by a hyphen at a
line end differs), and ends with the number of defects. Fix the key until
there are none. Then check that the programs can read it, and note its fingerprint (sha256), which every later step
asks for:

    uv run python experiments/reuse_demo/plant_key.py my_corpus/my_key.json
    shasum -a 256 my_corpus/my_key.json

**I2:** five questions (two extractive, one synthesis, one refutation, one not answerable) in
`experiments/reuse_demo/key_v1_1.json`, sha256 `eb58a724...`, 89 evidence quotes, 0 defects. Valerio, who worked in
plant science, read and signed it off (16 October, D75; version 1.1 on 26 October, D153).

## Step 3. Build the search index

The index cuts each paper into passages of 512 tokens (50 overlapping) and stores them with their bge-m3 vectors, as
the paper's indexes were built. `build_index.py` does this with the paper's own steps
(`experiments/reuse_demo/build_index.py`, its first lines explain each one).

First it proves it builds indexes the way the paper did. It rebuilds the paper's 20-paper index in a scratch folder
and compares the result with the index every Figure 2 answer was made on: 778 passages, with the same text. Only if
that passes does it build yours:

    uv run --project experiments/mentori --frozen python experiments/reuse_demo/build_index.py gate \
        --papers-dir ~/projects/Mentori-paper/datasets/v4_papers/core --store ~/my_store/gate_s20
    uv run --project experiments/mentori --frozen python experiments/reuse_demo/build_index.py build \
        --corpus my_corpus/core --manifest my_corpus/corpus_papers.csv --index my_index --store ~/my_store/original

Each command makes a store folder that must not exist yet, and writes a record (`index_gate.json`,
`index_<name>.json` under `findings/recompute/I2_runs/`, or where `--record` says). The build is refused if the gate
did not pass, or passed with other code. Only the bge-m3 model runs; no language model is called.

**I2:** index `i2_plant5` in `~/paper_store_i2/original`, built by `launch_i2.sh index-gate` and
`launch_i2.sh index-build`.

## Step 4. Let the strategies answer

`i2_generate.py` runs the paper's own answering script (`exp_01_generation.py`, Figure 2) on your questions and your
index. Six strategies answer every question: single pass, multi-hop, verified pass, and the recursive agent (RLM) with
5, 10 and 20 turns. Each question is answered three times (three "draws"), so you see how much the answers vary.

Each run works on its own copy of the store, because opening a store changes a few bytes in it. Copy the store once
per strategy (on a Mac, `cp -c` makes the copy instantly; `launch_i2.sh stores` shows how, with a check that each copy
equals the original). Then, for each strategy, point the run at its copy:

    export DATABASE_URL=sqlite:///$HOME/my_store/single_pass/mentori_app.db
    export CHROMA_PERSIST_DIRECTORY=$HOME/my_store/single_pass/chroma_db
    export OLLAMA_BASE_URL=http://127.0.0.1:11499
    uv run --project experiments/mentori --frozen python experiments/reuse_demo/i2_generate.py \
        --key my_corpus/my_key.json --key-sha256 <its sha256> --index my_index --configs single_pass --smoke \
        --ollama-url http://127.0.0.1:11499

`--smoke` answers the first question once, in a run of its own, and writes a line with the lowest free memory seen
(`findings/recompute/I2_runs/i2_generate.jsonl`). If that went well, run each strategy for the three draws
(`--draws 1 2 3` without `--smoke`), one process at a time. Five strategies call only Gemini, so their
`--ollama-url` names a port where nothing listens. Verified pass also calls its checker model: give it your Ollama
server (`--configs verified_pass --ollama-url http://127.0.0.1:<port>`).

The run checks the free memory before every answer. Under 2 GB (`--min-free-gb`) it starts no more answers, keeps the
ones already made and stops; run the same command with `--resume` later to go on.

**I2:** `launch_i2.sh smoke`, then `launch_i2.sh run 1 2 3` (the five Gemini-only strategies) on the laptop beside
another job (K1), then `launch_i2.sh verified 1 2 3` once the laptop's Ollama server is free. 5 questions x 6
strategies x 3 draws = 90 answers, under `findings/recompute/I2_runs/sinks/`.

## Step 5. Score every answer three ways

1. **The judge.** A language model (devstral-small-2:24b) reads the question, the key's answer and key concepts, and
   the system's answer, and scores correctness from 0 to 5 with the paper's own prompt. A not-answerable question is
   scored on whether the answer declines (refusal accuracy, 0 to 5). First prove that your server and the judge give
   the paper's scores: the check re-judges 107 answers whose scores are stored and requires every score to be equal
   (107 judge calls, about 1.3 hours at 45 s a call; an estimate from one call timed on the paper's Mac Studio):

       uv run python experiments/scorers/judge_passages.py check --base http://127.0.0.1:<port> \
           --log <your Ollama server's log> --binary <your ollama binary> --machine macos --out ~/my_judge_check

   Then judge each strategy's answers against your key:

       uv run python experiments/reuse_demo/i2_judge.py run --key my_corpus/my_key.json --key-sha256 <its sha256> \
           --run findings/recompute/I2_runs/sinks/exp_01__single_pass__my_index --check-dir ~/my_judge_check \
           --base http://127.0.0.1:<port> --log <server log> --binary <ollama binary> --machine macos \
           --out findings/recompute/I2_runs/judge

2. **The key-based metrics.** No model. Concept recall: the share of the key concepts the paper's word matcher finds
   in the answer. Number overlap: the share of the numbers written in the key's answer that the answer also writes
   (the paper's function counts a number with and without the word after it, so units count, and gives 1 when the
   key holds no number):

       uv run python experiments/reuse_demo/i2_signals.py concepts --key my_corpus/my_key.json --key-sha256 <sha256>
       uv run python experiments/reuse_demo/i2_signals.py numbers --key my_corpus/my_key.json --key-sha256 <sha256>

3. **MiniCheck**, a small model that tests whether a sentence is supported by a text. Against the key: the share of
   the answer's sentences the key's answer supports (precision), the share of the key's sentences the answer supports
   (recall), and their F1. Against the papers: the share of the answer's sentences the question's papers support (the
   page text of step 2):

       uv run python experiments/reuse_demo/i2_signals.py key --device cpu \
           --key my_corpus/my_key.json --key-sha256 <sha256>
       uv run python experiments/reuse_demo/i2_signals.py papers --device cpu \
           --key my_corpus/my_key.json --key-sha256 <sha256> --text-dir my_corpus/text

Each scorer first repeats a piece of the paper's own scoring and stops, writing nothing, if it does not get the same
numbers. `--text-dir` points `papers` at your page texts from step 2. The two MiniCheck commands do not start with
less than 4 GB free (`--min-free-gb`). Each command also takes `--runs` (the run folders to score) and `--out` (where
the rows go).

**I2:** the judge runs after K1 has finished on the laptop, because loading the judge unloads K1's model.

## Step 6. Read where the scores disagree

    uv run python experiments/reuse_demo/i2_report.py --key my_corpus/my_key.json --key-sha256 <sha256>

The report (`findings/recompute/I2_runs/report/i2_report.md`) gives, per strategy, how many answers the judge passed
at score 4 (the pass rate) and at score 3 (the relaxed reading), how many not-answerable questions were declined, and
then every answer on one line with its judge score and its three signals. Look first at the lines where they point
different ways: the judge passes an answer that finds few key concepts, or fails one that MiniCheck finds fully
supported by the papers. Read those answers yourself, against the papers. That reading, by someone who knows the
field, is the last check of the method.

With five questions, the counts show that the procedure runs and how the signals behave. They do not show which
strategy is best.

## What the I2 run used

| What | I2 |
|---|---|
| Papers | 5, `experiments/reuse_demo/corpus_papers.csv` |
| Key | `experiments/reuse_demo/key_v1_1.json`, sha256 `eb58a724f10382f478a25c68ec3b52260c398ce912e071ff8ba5a7647d9e5487` |
| Index | `i2_plant5`, bge-m3 at the lock's revision, 512-token passages with 50 overlap |
| Strategies | the six of Figure 2 (D160 Q-I2b) |
| Draws | 3 (D160 Q-I2c) |
| Answering model | `gemini-3-flash-preview`; verified pass's checker `gpt-oss:20b` |
| Scores | the judge (devstral-small-2:24b), concept recall and number overlap, MiniCheck; pass at score 4 and 3 (D160 Q-I2d) |
| Where | the laptop, one process at a time, only with 2 GB free (D160 Q-I2e) |
| Launcher | `bash experiments/reuse_demo/launch_i2.sh check` lists what is ready |

## Limits to know

- Concept recall uses a provisional word matcher (D12). The paper may change it after Valerio's hand labels (plan row
  P2); the concept recall is then computed again.
- The code needed here is in this repository. The data deposit on Zenodo does not hold it yet; it will once the
  deposit's experiments folder is assembled.
- The checks in steps 3 and 5 repeat the paper's numbers on the paper's machines. On another machine they may fail;
  if one does, the scores of that machine are not comparable with the paper's, and the tools stop there.
