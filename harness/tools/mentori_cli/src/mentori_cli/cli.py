"""mentori-cli: init, index, ask, fetch-encoders (README.md)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from mentori_cli import __version__, config as cfgmod

CONFIG_NAME = "mentori.toml"


def _config_path(a) -> Path:
    return Path(a.config or os.environ.get("MENTORI_CLI_CONFIG") or CONFIG_NAME).expanduser().resolve()


def cmd_init(a) -> int:
    from mentori_cli import paths, prompts as pr
    root = Path(a.dir).expanduser().resolve()
    cfg_file = root / CONFIG_NAME
    if cfg_file.exists() and not a.force:
        raise SystemExit(f"mentori-cli: {cfg_file} exists; nothing written (pass --force to write it again)")
    root.mkdir(parents=True, exist_ok=True)
    cfg = cfgmod.check({})
    if a.model:
        cfg["model"]["provider"], cfg["model"]["name"] = cfgmod.parse_model(a.model)
    cfg_file.write_text(cfgmod.dumps(cfg), encoding="utf-8")
    (root / cfg["corpus"]["papers"]).mkdir(exist_ok=True)
    paths.setup_sys_path()
    os.environ.setdefault("DATABASE_URL", f"sqlite:///{root / '.mentori_cli_unused.db'}")   # nothing is opened
    os.environ.setdefault("CHROMA_PERSIST_DIRECTORY", str(root / ".mentori_cli_unused_chroma"))
    os.environ.setdefault("WORKSPACE_DIR", str(root / ".mentori_cli_unused_workspace"))
    cwd = os.getcwd()
    os.chdir(root)                 # Mentori's logging writes backend/logs/ under the working directory
    try:
        written = pr.export(root / cfg["run"]["prompts_dir"], pr.paper_prompts(), overwrite=a.force)
    finally:
        os.chdir(cwd)
    print(f"wrote {cfg_file}")
    print(f"wrote {len(written)} prompt files in {root / cfg['run']['prompts_dir']} (the paper's prompts, editable)")
    print(f"put your PDFs in {root / cfg['corpus']['papers']}, then: uv run mentori-cli index --config {cfg_file}")
    return 0


def cmd_index(a) -> int:
    from mentori_cli import indexer
    cfg = cfgmod.load(_config_path(a))
    corpus = Path(a.corpus) if a.corpus else cfgmod.resolve_path(cfg, cfg["corpus"]["papers"])
    store = Path(a.store) if a.store else cfgmod.resolve_path(cfg, cfg["corpus"]["store"])
    rec = indexer.build(corpus, store, a.name or cfg["corpus"]["index"])
    r = rec["result"]
    print(f"index {rec['index']} in {rec['store']}: {r.get('status')}, {r.get('total_chunks')} passages from "
          f"{r.get('documents_registered')} of {len(rec['files'])} files, {len(r.get('file_errors') or [])} file errors "
          f"({rec['wall_s']} s); record {rec['store']}/index_record.json")
    if a.store or a.name:
        print("note: ask reads [corpus] store and index from the config file; set them there to use this store")
    return 0 if rec["ok"] else 1


def cmd_ask(a) -> int:
    from mentori_cli import runner
    cfg = cfgmod.load(_config_path(a))
    questions = runner.read_questions(a.question, Path(a.questions) if a.questions else None)
    off = [x.strip() for x in (a.off or "").split(",") if x.strip()]
    records = runner.ask(cfg, questions, strategy=a.strategy, off=off, rlm_turns=a.rlm_turns,
                         prompts_dir=Path(a.prompts).expanduser().resolve() if a.prompts else None,
                         model=cfgmod.parse_model(a.model) if a.model else None, strict=True if a.strict else None,
                         draw=a.draw)
    failed = [r["question_id"] for r in records if r.get("error")]
    if failed:
        print(f"mentori-cli: {len(failed)} of {len(records)} answers ended in an error ({', '.join(failed)}); "
              "exit status 1 (each record's error field says why)", file=sys.stderr)
        return 1
    return 0


def cmd_fetch(a) -> int:
    from mentori_cli import indexer
    for p in indexer.fetch_encoders():
        print(f"in the Hugging Face cache: {p}")
    return 0


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="mentori-cli", description="The Mentori method on your own papers "
                                 "(the paper's code, unchanged). See tools/mentori_cli/README.md.")
    ap.add_argument("--version", action="version", version=f"mentori-cli {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init", help="write mentori.toml, prompts/ (the paper's prompts) and papers/ in DIR")
    p.add_argument("dir")
    p.add_argument("--model", help="provider:name, for example ollama:gemma3:27b or gemini:gemini-3-flash-preview")
    p.add_argument("--force", action="store_true", help="write over an existing mentori.toml and prompt files")
    p.set_defaults(fn=cmd_init)
    p = sub.add_parser("index", help="build the store from a folder of PDFs (the paper's index builder)")
    p.add_argument("corpus", nargs="?", help="a folder of PDFs (default: [corpus] papers)")
    p.add_argument("--config", help=f"the project file (default ./{CONFIG_NAME} or $MENTORI_CLI_CONFIG)")
    p.add_argument("--store", help="a new folder for the store (default: [corpus] store)")
    p.add_argument("--name", help="the index name (default: [corpus] index)")
    p.set_defaults(fn=cmd_index)
    p = sub.add_parser("ask", help="answer a question over the indexed papers; prints the answer and its record")
    p.add_argument("question", nargs="?")
    p.add_argument("--questions", help="a JSONL file, one {\"question\": ..., \"id\": ...} per line")
    p.add_argument("--config", help=f"the project file (default ./{CONFIG_NAME} or $MENTORI_CLI_CONFIG)")
    p.add_argument("--strategy", choices=cfgmod.STRATEGIES)
    p.add_argument("--off", help="components to switch off, comma separated: " + ",".join(cfgmod.OFF_NAMES))
    p.add_argument("--rlm-turns", type=int, help="the RLM's turn limit (strategy rlm)")
    p.add_argument("--prompts", help="a prompts folder (default: [run] prompts_dir)")
    p.add_argument("--model", help="provider:name, for example ollama:gemma3:27b, gemini:gemini-3-flash-preview, "
                                   "anthropic:claude-haiku-4-5")
    p.add_argument("--draw", type=int, help="the draw number, which is the seed (default [run] draw)")
    p.add_argument("--strict", action="store_true", help="refuse any setting that departs from the paper's lock")
    p.set_defaults(fn=cmd_ask)
    p = sub.add_parser("fetch-encoders", help="download bge-m3 and the reranker at the lock's revisions (once)")
    p.set_defaults(fn=cmd_fetch)
    return ap


def main(argv=None) -> int:
    a = parser().parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
