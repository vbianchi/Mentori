# Changelog

## 0.1.1 (unreleased)

Defects found in a walkthrough of 0.1.0. No change to what the paper's code runs.

- An edited prompt file must hold exactly the placeholders of the paper's prompt (`{question}`, `{passages}` and so
  on, as `str.format` or the code's replacements read them); `ask` refuses one that drops or adds a placeholder, or
  that `str.format` cannot read, and names what differs, before anything is sent. Before, a prompt with its
  placeholders removed ran and sent no question.
- `--draw` outside 1 to 999 is refused before anything runs. Before, `--draw 0` ended in a traceback and left an
  empty run folder.
- The paper's `Warning: No Gemini API Key provided.` line is no longer printed for runs that use no Gemini model; for
  a Gemini run it goes to stderr.
- `ask` exits with status 1 when any answer ended in an error (0 when every answer came back).
- `init`'s next-step hint says `uv run mentori-cli index`, as the README does.
- README: the claim "citations to paper and page" is removed. The paper's index builder stores every page as 0
  (`smart_ingestor.py:489`), and the tool keeps the paper's index as it is; written under "Limits".
- README: the offline demo's answering step is its own single pass (`DemoEngine`), not the paper's strategy
  function; the README said "everything else in it is the real tool". The clone URL notes that the repository becomes
  public with the paper.

## 0.1.0 (release candidate, 8 November 2026)

The first version shared with the paper.

- `init DIR`: writes `mentori.toml` (model provider and name, server URL, the API key variable's name only, corpus,
  strategy, component switches) and `prompts/`, 23 files each holding one of the paper's prompts byte for byte, under
  a header naming its component and its source `path:line`.
- `index`: builds a store from a folder of PDFs with the paper's index builder (`experiments/reuse_demo/build_index.py`).
- `ask`: answers one question, or a JSONL file of questions, with `single_pass`, `multi_hop`, `rlm` (`--rlm-turns`),
  `verified_pass` or `orchestrator`, through the paper's strategy functions, unchanged. `--off` switches off the
  paper's components (`analyser`, `planner`, `supervisor`, `synthesiser`, `distiller`, `rlm_gate`, `rlm_search`);
  `--prompts` uses another prompts folder; `--model provider:name` (ollama, gemini, anthropic).
- Settings come from `experiments/LOCK.toml`. A setting the lock does not hold runs and is recorded as
  `departs from LOCK: ...`; `--strict` refuses it before anything is sent.
- Each answer prints its record as JSON and appends it to `runs/<run id>/answers.jsonl`; `calls.jsonl` keeps every
  call in full.
- `fetch-encoders`: downloads bge-m3 and its reranker at the lock's revisions.
- `examples/offline_demo.py`: one question end to end with a fake Ollama server and no model, to show the record.
- Offline tests with fake clients (`uv run --frozen pytest`); an opt-in integration test with one PDF.
