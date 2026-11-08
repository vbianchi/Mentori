"""The settings a run sends: the paper's lock, and every departure from it, named.

The defaults are experiments/LOCK.toml's, for every model it names. What a lab's setup needs that the lock does not
hold (another model, another Ollama version, a model build with another digest, a sampling override) is written into
a copy of the lock's dict in memory and listed as a departure ("departs from LOCK: ..."). With no departure the run
reads the paper's LOCK.toml unchanged (inject.py installs nothing). With --strict a departure refuses the run instead.
"""

from __future__ import annotations

import copy
import hashlib
import json
import tomllib
import urllib.request
from pathlib import Path

OLLAMA_SAMPLING = ("temperature", "top_p", "top_k", "min_p", "repeat_penalty", "presence_penalty")


def _lookup(table: dict, tag: str):
    """experiments/runner/lock.py _lookup: by exact tag, else without ':latest', else the family before ':'."""
    for key in (tag, tag.removesuffix(":latest"), tag.split(":")[0]):
        if key in table:
            return key, table[key]
    return None, None


def paper_lock(path: Path) -> tuple[bytes, dict]:
    raw = Path(path).read_bytes()
    return raw, tomllib.loads(raw.decode("utf-8"))


def fetch_server_state(url: str, timeout: float = 10.0) -> dict:
    """An Ollama server's version and its models' digests (two metadata requests; no model is called)."""
    base = url.rstrip("/")
    try:
        with urllib.request.urlopen(f"{base}/api/version", timeout=timeout) as r:
            version = json.loads(r.read())["version"]
        with urllib.request.urlopen(f"{base}/api/tags", timeout=timeout) as r:
            tags = {m["name"]: m["digest"] for m in json.loads(r.read())["models"]}
    except (OSError, ValueError, KeyError) as e:
        raise SystemExit(f"mentori-cli: the Ollama server at {base} could not be read ({type(e).__name__}: {e}); "
                         f"start it (ollama serve) or set [model] server_url") from None
    return {"version": version, "tags": tags}


def ollama_tag(name: str) -> str:
    """Ollama lists a model without a tag as <name>:latest."""
    return name if ":" in name else f"{name}:latest"


def _ollama_model(d: dict, name: str, url: str, state: dict, dep: list, seen_versions: set) -> None:
    if url not in seen_versions:
        seen_versions.add(url)
        if len(seen_versions) > 1 and state["version"] != d["server"]["ollama_version"]:
            raise SystemExit(f"mentori-cli: the Ollama servers run different versions ({d['server']['ollama_version']} "
                             f"and {state['version']} at {url}); the lock holds one version for every server")
        if state["version"] != d["server"]["ollama_version"]:
            dep.append(f"departs from LOCK: Ollama at {url} is version {state['version']}, the lock names "
                       f"{d['server']['ollama_version']} ([server] ollama_version)")
            d["server"]["ollama_version"] = state["version"]   # what ollama_client checks before each call
    copies = d.setdefault("date", {}).setdefault("model_copy", {})
    run = copies.get(name, name)
    if run != name and run not in state["tags"]:
        if name in state["tags"]:
            del copies[name]
            dep.append(f"departs from LOCK: {run} (the lock's copy of {name} with the date fixed, [date] model_copy) "
                       f"is not on {url}; {name} runs with its own template's date")
            run = name
        else:
            raise SystemExit(f"mentori-cli: {url} holds neither {name} nor {run}; pull it first "
                             f"(ollama pull {name})")
    digest = state["tags"].get(run)
    if digest is None:
        raise SystemExit(f"mentori-cli: {url} does not hold {run}; pull it first (ollama pull {run})")
    models = d.setdefault("models", {})
    key, row = _lookup(models, run)
    if row is None:
        models[run] = {"digest": digest, "machines": ["local"]}
        dep.append(f"departs from LOCK: {run} has no row in [models]; it runs the server's build, digest {digest[:12]}")
    elif row.get("digest") != digest:
        dep.append(f"departs from LOCK: {run} on {url} has digest {digest[:12]}, the lock names "
                   f"{str(row.get('digest'))[:12]} ([models])")
        models[key] = {**row, "digest": digest}


def _ollama_sampling(d: dict, name: str, overrides: dict, dep: list, generator: bool) -> None:
    rows = d["sampling"]["models"]
    key, row = _lookup(rows, name)
    if row is None:
        rows[name] = {"think": "omit"}
        key = name
        dep.append(f"departs from LOCK: {name} has no row in [sampling.models]; no sampling option is sent (the "
                   f"model's own defaults apply) and no think field is sent")
    if not generator:
        return
    for k, v in overrides.items():
        if k in OLLAMA_SAMPLING:
            old = rows[key].get(k)
            if old != v:
                rows[key] = {**rows[key], k: v}
                on_key, on = _lookup(d["sampling"].get("thinking_on", {}), name)
                if on is not None and k in on:   # the maker's thinking-on row would set it back
                    d["sampling"]["thinking_on"][on_key] = {**on, k: v}
                dep.append(f"departs from LOCK: {name} {k} = {v} (the lock's [sampling.models] row gives {old})")
        elif k == "num_ctx":
            exc = d.setdefault("exceptions", {})
            ek, erow = _lookup(exc, name)
            old = (erow or {}).get("num_ctx", d["generation"]["num_ctx"])
            if old != v:
                exc[ek or name] = {**(erow or {}), "num_ctx": v}
                dep.append(f"departs from LOCK: {name} num_ctx = {v} (the lock gives {old})")
        elif k == "max_tokens":
            raise SystemExit("mentori-cli: [sampling] max_tokens is for Gemini and Anthropic; Ollama answers until "
                             "the context is full (LOCK [generation] num_predict -1)")


def _gemini(d: dict, name: str, overrides: dict, dep: list) -> None:
    g = d["gemini"]
    if name not in g["thinking_off"]:
        g["thinking_off"][name] = "minimal"
        dep.append(f"departs from LOCK: {name} has no row in [gemini] thinking_off; 'minimal' is used when thinking "
                   f"is off")
    names = {"temperature": "temperature", "top_p": "top_p", "top_k": "top_k", "max_tokens": "max_output_tokens"}
    for k, v in overrides.items():
        if k not in names:
            raise SystemExit(f"mentori-cli: [sampling] {k} is not sent to Gemini (it takes {', '.join(names)})")
        if g[names[k]] != v:
            dep.append(f"departs from LOCK: gemini {names[k]} = {v} (the lock's [gemini] gives {g[names[k]]})")
            g[names[k]] = v


def _anthropic(d: dict, name: str, overrides: dict, dep: list) -> None:
    a = d["anthropic"]
    if not (a["model_id"] == name or a["model_id"].startswith(name + "-")):
        dep.append(f"departs from LOCK: Anthropic model {name} (the lock's [anthropic] model_id is {a['model_id']})")
        a["model_id"] = name
    rows = d["sampling"]["models"]
    key, row = _lookup(rows, name)
    if row is None:
        rows[name] = {"temperature": 1.0, "think": "omit"}
        key = name
        dep.append(f"departs from LOCK: {name} has no row in [sampling.models]; temperature 1.0 (Anthropic's "
                   f"default) is sent")
    for k, v in overrides.items():
        if k == "temperature":
            if rows[key].get("temperature") != v:
                dep.append(f"departs from LOCK: {name} temperature = {v} (the lock gives "
                           f"{rows[key].get('temperature')})")
                rows[key] = {**rows[key], "temperature": v}
        elif k == "max_tokens":
            if a["max_tokens"] != v:
                dep.append(f"departs from LOCK: Anthropic max_tokens = {v} (the lock gives {a['max_tokens']})")
                a["max_tokens"] = v
        else:
            raise SystemExit(f"mentori-cli: [sampling] {k} is not sent to Anthropic (it takes temperature, max_tokens)")


def effective(paper_d: dict, models: list[dict], overrides: dict, thinking: str,
              server_states: dict) -> tuple[dict, list[str]]:
    """(the lock's dict as the run sends it, the departures). models: [{"role", "provider", "name", "url"}], the
    generator first. overrides apply to the generator. server_states: {url: fetch_server_state(url)}."""
    d = copy.deepcopy(paper_d)
    dep: list[str] = []
    versions: set = set()
    for m in models:
        gen = m["role"] == "generator"
        if m["provider"] == "ollama":
            _ollama_model(d, m["name"], m["url"], server_states[m["url"]], dep, versions)
            _ollama_sampling(d, m["name"], overrides if gen else {}, dep, gen)
        elif m["provider"] == "gemini":
            _gemini(d, m["name"], overrides if gen else {}, dep)
        else:
            _anthropic(d, m["name"], overrides if gen else {}, dep)
    if thinking == "off":
        dep.append("departs from LOCK: thinking off for the generator (the lock's [thinking] generator rule is "
                   "'default', the maker's default)")
    return d, dep


def run_sha256(paper_raw: bytes, d: dict) -> str:
    """The lock_sha256 a departing run's call records carry: never the paper's, the same for the same settings."""
    canon = json.dumps(d, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(paper_raw + b"\n# mentori-cli departures\n" + canon.encode("utf-8")).hexdigest()


def models_of(cfgd: dict, provider: str, name: str, strategy: str) -> list[dict]:
    """The models a run calls: the generator, and verified pass's verifier."""
    url = cfgd["model"]["server_url"]
    out = [{"role": "generator", "provider": provider, "name": ollama_tag(name) if provider == "ollama" else name,
            "url": url}]
    if strategy == "verified_pass":
        v = cfgd["verifier"]
        out.append({"role": "verifier", "provider": v["provider"],
                    "name": ollama_tag(v["name"]) if v["provider"] == "ollama" else v["name"],
                    "url": v["server_url"] or url})
    return out
