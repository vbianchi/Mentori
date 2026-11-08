"""Settings and prompts put into the paper's code at run time, in memory; no file of the paper's code is written.

Standard library only: the orchestrator's tool server runs in experiments/mentori's own environment and calls
install_from_env() before it imports the tool server (engine.py prefixes the runner's launcher).

    install({"lock": {"d": <the lock as a dict>, "sha256": "<hex>"} or None,
             "prompts": {"<name>": "<text>", ...},      # only the edited ones (registry.PROMPTS names)
             "verifier": "ollama::<tag>" or None})       # verified pass's verifier, when it is not the paper's

What it does:
  1. Keys: experiments/runner/gemini_client.key() reads an environment variable, else a keys file. The keys file is
     pointed at a path that does not exist, so a key is only ever read from the environment.
  2. The lock: with "lock" given, experiments.runner.lock.load (and every module that imported it by name) returns the
     paper's Lock object with its dict and sha256 replaced by these. With "lock" None nothing is changed: the paper's
     LOCK.toml is read as it is, byte for byte.
  3. Prompts: each edited prompt replaces the constant in its module and in every loaded module that imported the
     same object by the same name; F1 replaces the function that builds it. An unedited prompt is not touched.
  4. Verifier: PipelineConfig.verified() returns its config with verify_model set to the given model.
  5. Offline encoders: with HF_HUB_OFFLINE set, offline_encoders() (below).
"""

from __future__ import annotations

import copy
import importlib
import json
import os
import sys
from pathlib import Path

from mentori_cli import registry

ENV_SPEC = "MENTORI_CLI_INJECT"
PAPER_PREFIX = "_mentori_cli_paper_"
NO_KEYS_FILE = Path("/nonexistent/mentori-cli-reads-keys-from-the-environment-only")
_installed: dict = {}


def _rebind(original, replacement, name: str | None = None) -> int:
    """Every loaded module attribute that is `original` (and named `name`, when given) set to `replacement`; the
    tool's own copies of the paper's values (names starting _mentori_cli_) are kept."""
    n = 0
    for mod in list(sys.modules.values()):
        try:
            d = vars(mod)
        except TypeError:
            continue
        for k, v in list(d.items()):
            if v is original and (name is None or k == name) and not k.startswith("_mentori_cli_"):
                setattr(mod, k, replacement)
                n += 1
    return n


def block_keys_file() -> None:
    from experiments.runner import gemini_client
    gemini_client.KEYS = NO_KEYS_FILE


def install_lock(d: dict, sha256: str) -> None:
    from experiments.runner import lock as L
    paper_load = getattr(L, "_mentori_cli_paper_load", L.load)
    L._mentori_cli_paper_load = paper_load
    frozen = copy.deepcopy(d)

    def load(path=L.LOCK):
        obj = paper_load(path)
        if Path(path).resolve() == L.LOCK.resolve():
            obj.d = copy.deepcopy(frozen)
            obj.sha256 = sha256
        return obj

    load._mentori_cli = True
    current = L.load
    _rebind(current, load)
    if current is not paper_load:
        _rebind(paper_load, load)
    L.load = load


def install_prompts(prompts: dict) -> None:
    for name, body in prompts.items():
        p = registry.BY_NAME[name]
        owner = importlib.import_module(p.module)
        original = getattr(owner, p.attr)
        vars(owner).setdefault(PAPER_PREFIX + p.attr, original)     # prompts.paper_prompts reads the paper's from here
        if p.kind == "f1":
            def built(tool_name, content, _t=body):
                return registry.f1_render(_t, tool_name, content)
            _rebind(original, built, p.attr)
            setattr(owner, p.attr, built)
        else:
            _rebind(original, body, p.attr)
            setattr(owner, p.attr, body)


def install_verifier(ident: str) -> None:
    import dataclasses
    from backend.retrieval import pipeline
    cls = pipeline.PipelineConfig
    paper = getattr(cls, "_mentori_cli_paper_verified", None) or cls.verified.__func__
    cls._mentori_cli_paper_verified = paper

    def verified(c):
        return dataclasses.replace(paper(c), verify_model=ident)
    cls.verified = classmethod(verified)


OFFLINE_VALUES = ("1", "true", "yes", "on")


def offline_encoders(lock_toml: Path | None = None) -> bool:
    """Only when HF_HUB_OFFLINE is set (the user's choice): the paper's environment (transformers 4.57.3,
    tokenization_utils_base._patch_mistral_regex) asks the Hugging Face API for model_info on every tokenizer load,
    local_files_only or not, and fails offline. For the lock's two encoder repos ([retrieval] hf_repo, bge-m3 and
    bge-reranker-v2-m3, neither a Mistral model) model_info returns no tags, which is what the Hub returns for them as
    far as that check reads (no base_model:mistralai tag); every other repo goes to the Hub as before. Returns True
    when installed."""
    if os.environ.get("HF_HUB_OFFLINE", "").strip().lower() not in OFFLINE_VALUES:
        return False
    import tomllib
    import types
    import huggingface_hub
    from mentori_cli import paths
    rows = tomllib.loads(Path(lock_toml or paths.lock_path()).read_text(encoding="utf-8"))["retrieval"]
    repos = {r["hf_repo"] for r in rows.values()}
    paper = getattr(huggingface_hub, PAPER_PREFIX + "model_info", None) or huggingface_hub.model_info
    setattr(huggingface_hub, PAPER_PREFIX + "model_info", paper)

    def model_info(repo_id, *a, **kw):
        if repo_id in repos:
            return types.SimpleNamespace(id=repo_id, tags=None)
        return paper(repo_id, *a, **kw)
    huggingface_hub.model_info = model_info
    return True


def install(spec: dict) -> None:
    block_keys_file()
    offline_encoders()
    if spec.get("lock"):
        install_lock(spec["lock"]["d"], spec["lock"]["sha256"])
    if spec.get("prompts"):
        install_prompts(spec["prompts"])
    if spec.get("verifier"):
        install_verifier(spec["verifier"])
    _installed.clear()
    _installed.update(spec)


def install_from_env() -> None:
    """The tool server's entry: the spec file named by MENTORI_CLI_INJECT, when set."""
    path = os.environ.get(ENV_SPEC)
    if path:
        spec = json.loads(Path(path).read_text(encoding="utf-8"))
        install(spec)
        print(f"mentori-cli: installed in the tool server (pid {os.getpid()}): lock "
              f"{'with departures' if spec.get('lock') else 'as LOCK.toml'}, edited prompts "
              f"{sorted(spec.get('prompts') or {}) or 'none'}, verifier {spec.get('verifier') or 'as the paper'}",
              file=sys.stderr, flush=True)


# The lines put before experiments/runner/experiment.py's _LAUNCHER (it goes through str.format, so no brace here).
# experiments/mentori is put first and the repository last, as the paper's lock adapter orders them.
LAUNCHER_PREFIX = """
import os as _mcli_os, sys as _mcli_sys
if _mcli_os.environ.get("MENTORI_CLI_INJECT"):
    _mcli_sys.path.insert(0, _mcli_os.environ["MENTORI_CLI_MENTORI"])
    _mcli_sys.path.insert(0, _mcli_os.environ["MENTORI_CLI_SRC"])
    _mcli_sys.path.append(_mcli_os.environ["MENTORI_CLI_REPO"])
    import mentori_cli.inject as _mcli_inject
    _mcli_inject.install_from_env()
"""
