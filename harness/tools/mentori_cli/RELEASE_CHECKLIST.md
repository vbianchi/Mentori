# Release checklist, mentori-cli

For Valerio. Each step names what it needs; nothing here has been done.

## Before the tag

1. Decide the open questions below (Q1 to Q3).
2. Fill the DOI in `README.md` (Citation, and "What it is") once the paper has one.
3. Confirm the repository URL in `README.md` (`https://github.com/vbianchi/Mentori-reanalysis.git`) is the public one.
4. In `tools/mentori_cli/`: `uv run --frozen pytest` passes, and `uv run --frozen python examples/offline_demo.py`
   exits 0.
5. From a fresh clone: `cd tools/mentori_cli && uv sync --frozen && uv run mentori-cli --help && uv run mentori-cli init
   /tmp/lab` all exit 0.
6. Optional, with one PDF: the opt-in integration test (`README.md`, "Tests").
7. Version: `version` in `pyproject.toml` and `__version__` in `src/mentori_cli/__init__.py` agree; `CHANGELOG.md`
   has the release date.

## Tag

    git tag -a mentori-cli-v0.1.0 -m "mentori-cli 0.1.0"
    git push origin mentori-cli-v0.1.0

## Zenodo

The repository goes to Zenodo with the paper (editorial items 12 and 29). If the GitHub to Zenodo link is on, a
GitHub release from the tag makes the deposit; otherwise upload the tagged archive. Put the DOI it gives in the paper's
Code Availability and in `README.md`.

## PyPI (optional, not possible in 0.1.0)

The tool runs only inside the repository, and `uv tool install` fails building `experiments/mentori` (README,
"Later items"). PyPI waits for a package that works outside the checkout.

## Open questions

- **Q1. Departures by default.** Today a run that departs from the lock goes ahead and is marked; `--strict` refuses
  it. The default was chosen so a lab can try its own model and Ollama version. To refuse by default instead, set
  `"strict": True` in `src/mentori_cli/config.py` DEFAULTS (one line). Advice: keep the default; every record
  carries its departures.
- **Q2. Command name.** The command is `mentori-cli`. A shorter `mentori` would be easy to confuse with the Mentori
  application's own `mentori` command (for example `mentori ollama ensure`). Advice: keep `mentori-cli`.
- **Q3. Licence of this folder.** It falls under the repository's MIT `LICENSE`; the README says so. A licence file
  inside `tools/mentori_cli/` is needed only if the folder is ever published on its own (PyPI).
