"""The project's config file, mentori.toml: read, written, checked.

Relative paths in the file are read against the file's own folder. The file names the environment variable that
holds an API key, never the key.
"""

from __future__ import annotations

import copy
import json
import tomllib
from pathlib import Path

PROVIDERS = ("ollama", "gemini", "anthropic")
STRATEGIES = ("single_pass", "multi_hop", "rlm", "verified_pass", "orchestrator")
KEY_ENV = {"gemini": "GEMINI_API_KEY", "anthropic": "ANTHROPIC_API_KEY"}   # what the paper's clients read
ORCH_COMPONENTS = ("analyser", "planner", "supervisor", "synthesiser", "distiller")
RLM_COMPONENTS = ("rlm_gate", "rlm_search")
OFF_NAMES = ORCH_COMPONENTS + RLM_COMPONENTS

DEFAULTS: dict = {
    "model": {
        "provider": "ollama",                 # ollama, gemini or anthropic (OpenAI: a later item)
        "name": "gemma3:27b",                 # a model the paper's lock names (experiments/LOCK.toml [models])
        "server_url": "http://127.0.0.1:11434",   # the Ollama server (also used for Ollama verifiers)
        "api_key_env": "",                    # gemini/anthropic: the NAME of the environment variable with the key;
                                              # empty = GEMINI_API_KEY or ANTHROPIC_API_KEY
    },
    "verifier": {                             # strategy verified_pass only: the model that checks each passage
        "provider": "ollama",
        "name": "gpt-oss:20b",                # the paper's verifier
        "server_url": "",                     # empty = [model] server_url
    },
    "corpus": {
        "papers": "papers",                   # the folder of PDFs `mentori-cli index` reads
        "store": "store",                     # the store `mentori-cli index` builds (database and vectors)
        "index": "my_index",                  # the index name inside the store
    },
    "run": {
        "strategy": "single_pass",
        "rlm_turns": 10,                      # the paper ran 5, 10 and 20
        "draw": 1,                            # the seed is the draw number (LOCK.toml [generation] seed)
        "thinking": "default",                # "default" (the lock's rule for generators) or "off"
        "strict": False,                      # true: refuse any setting that departs from the paper's lock
        "out_dir": "runs",                    # each ask writes its records under out_dir/<run id>/
        "prompts_dir": "prompts",             # the editable prompt files; empty = the paper's prompts
    },
    "components": {                           # "on" is the paper's Mentori as built
        "analyser": "on",                     # on, off, factual_to_documents
        "planner": "on",                      # on, off
        "supervisor": "on",                   # on, off
        "synthesiser": "on",                  # on, off
        "distiller": "on",                    # on, off, F1
        "distiller_trigger": "threshold",     # threshold, every_step
        "rlm_gate": "on",                     # on, off (the RLM's quality gate)
        "rlm_search": "on",                   # on, off (the RLM's search functions)
    },
    "sampling": {},                           # overrides of the lock's settings for the generator, for example
                                              # temperature = 0.2, num_ctx = 32768; each one is a departure
}

COMMENTS = {
    "model": "The answering model. provider: ollama, gemini or anthropic. api_key_env: the NAME of the environment "
             "variable that holds the key (never the key itself).",
    "verifier": "verified_pass only: the model that checks each retrieved passage (the paper used gpt-oss:20b).",
    "corpus": "papers: your PDFs. store and index: what `mentori-cli index` builds and `mentori-cli ask` reads.",
    "run": "strategy: single_pass, multi_hop, rlm, verified_pass or orchestrator. strict = true refuses any setting "
           "that departs from the paper's lock (experiments/LOCK.toml).",
    "components": "on = Mentori as built. analyser, planner, supervisor, synthesiser, distiller: orchestrator only. "
                  "rlm_gate, rlm_search: rlm only.",
    "sampling": "Overrides of the lock's sampling for the generator (temperature, top_p, top_k, min_p, "
                "repeat_penalty, presence_penalty, num_ctx, max_tokens). Empty = the lock's. Each one is recorded "
                "as a departure from the lock.",
}

SAMPLING_KEYS = ("temperature", "top_p", "top_k", "min_p", "repeat_penalty", "presence_penalty", "num_ctx",
                 "max_tokens")


class ConfigError(SystemExit):
    def __init__(self, msg: str):
        super().__init__(f"mentori-cli: {msg}")


def _toml_value(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)      # a TOML basic string (the same escapes)
    raise ConfigError(f"cannot write {v!r} into the config file")


def dumps(cfg: dict) -> str:
    out = ["# mentori-cli project file. Relative paths are read against this file's folder.", ""]
    for section in DEFAULTS:
        out.append(f"# {COMMENTS[section]}")
        out.append(f"[{section}]")
        for k, v in cfg.get(section, {}).items():
            out.append(f"{k} = {_toml_value(v)}")
        out.append("")
    return "\n".join(out)


def check(cfg: dict) -> dict:
    """Every section and key known, every value of the right type; missing keys take DEFAULTS. Returns a new dict."""
    out = copy.deepcopy(DEFAULTS)
    for section, values in cfg.items():
        if section not in DEFAULTS:
            raise ConfigError(f"unknown section [{section}] (known: {', '.join(DEFAULTS)})")
        if not isinstance(values, dict):
            raise ConfigError(f"[{section}] is not a table")
        for k, v in values.items():
            if section == "sampling":
                if k not in SAMPLING_KEYS:
                    raise ConfigError(f"[sampling] {k}: not a setting this tool sends (known: {', '.join(SAMPLING_KEYS)})")
                if isinstance(v, bool) or not isinstance(v, (int, float)):
                    raise ConfigError(f"[sampling] {k} = {v!r}: a number")
            elif k not in DEFAULTS[section]:
                raise ConfigError(f"[{section}] {k}: unknown key (known: {', '.join(DEFAULTS[section])})")
            elif type(v) is not type(DEFAULTS[section][k]):
                raise ConfigError(f"[{section}] {k} = {v!r}: a {type(DEFAULTS[section][k]).__name__}")
            out[section][k] = v
    for sec in ("model", "verifier"):
        if out[sec]["provider"] not in PROVIDERS:
            raise ConfigError(f"[{sec}] provider {out[sec]['provider']!r}: one of {', '.join(PROVIDERS)} "
                              f"(OpenAI is a later item)")
    if out["run"]["strategy"] not in STRATEGIES:
        raise ConfigError(f"[run] strategy {out['run']['strategy']!r}: one of {', '.join(STRATEGIES)}")
    if out["run"]["thinking"] not in ("default", "off"):
        raise ConfigError(f"[run] thinking {out['run']['thinking']!r}: default or off")
    if not 1 <= out["run"]["rlm_turns"] <= 100:
        raise ConfigError("[run] rlm_turns: from 1 to 100")
    if not 1 <= out["run"]["draw"] <= 999:
        raise ConfigError("[run] draw: from 1 to 999 (the lock's draw numbers)")
    comp = {"analyser": ("on", "off", "factual_to_documents"), "planner": ("on", "off"),
            "supervisor": ("on", "off"), "synthesiser": ("on", "off"), "distiller": ("on", "off", "F1"),
            "distiller_trigger": ("threshold", "every_step"), "rlm_gate": ("on", "off"), "rlm_search": ("on", "off")}
    for k, allowed in comp.items():
        if out["components"][k] not in allowed:
            raise ConfigError(f"[components] {k} = {out['components'][k]!r}: one of {', '.join(allowed)}")
    return out


def loads(text: str) -> dict:
    try:
        return check(tomllib.loads(text))
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"the config file is not TOML: {e}") from None


def load(path: Path) -> dict:
    path = Path(path)
    if not path.is_file():
        raise ConfigError(f"no config file at {path}; make one with `mentori-cli init DIR`")
    cfg = loads(path.read_text(encoding="utf-8"))
    cfg["_dir"] = str(path.resolve().parent)
    return cfg


def resolve_path(cfg: dict, value: str) -> Path | None:
    """A path of the config file, read against the file's folder; None for an empty value."""
    if not value:
        return None
    p = Path(value).expanduser()
    return p if p.is_absolute() else Path(cfg.get("_dir", ".")) / p


def parse_model(spec: str) -> tuple[str, str]:
    """provider:name or provider::name (the name may hold ':', as Ollama tags do: ollama:gemma3:27b)."""
    if "::" in spec:
        provider, _, name = spec.partition("::")
    else:
        provider, _, name = spec.partition(":")
    provider, name = provider.strip(), name.strip()
    if provider not in PROVIDERS or not name:
        raise ConfigError(f"--model {spec!r}: write provider:name, provider one of {', '.join(PROVIDERS)} "
                          f"(for example ollama:gemma3:27b or gemini:gemini-3-flash-preview)")
    return provider, name
