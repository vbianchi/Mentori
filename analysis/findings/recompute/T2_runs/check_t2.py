"""T2's checks (exp_01 with another generator: claude-haiku-4-5, D142; gemini-2.5-pro, D158; gemma3:27b and
qwen3-coder:30b, the local lane, D159 (2)). README.md beside this file.

    python findings/recompute/T2_runs/check_t2.py smoke <config> [--root DIR] [--server URL] [--write]   # a smoke's verdict
    python findings/recompute/T2_runs/check_t2.py progress [--root DIR]                   # answers, calls, tokens
    python findings/recompute/T2_runs/check_t2.py complete --draws 1 [--configs ...]      # gate before later draws
    uv run --frozen python findings/recompute/T2_runs/check_t2.py stores                  # index identity vs G1
    uv run --project experiments/mentori --frozen python findings/recompute/T2_runs/check_t2.py plan [--draws 1 2 3]

plan is exp_01's own dry run (its dry_run function, imported, so no command line names the exp_NN script: K1's guards
on the laptop and the Beelink count any process that does, findings/recompute/K1/run_k1_laptop.sh:18). Every other
mode reads the run folders only (standard library; stores also reads the stores' chroma.sqlite3 read-only, immutable).

The generator is --generator, default T2_GENERATOR (t2_lib.sh exports it), else anthropic::claude-haiku-4-5; every
mode reads that generator's runs (exp_01__<config>__exp_v4_s20_n0+<model>) and nothing else.

D98's subset (S464's 45 questions; subset_draws; run_t2.sh adds exp_01 --question-ids-file), into the runs of all 135:
a Gemini generator's draws 2 and 3 (D159 (2)), and a local generator's rlm_5, rlm_10 and rlm_20 at every draw (D175 Q3
for gemma3:27b, D176 for qwen3-coder:30b).
complete then holds such a config's draw to those 45 keys (answers stored outside them are kept and do not count),
progress counts its 45 beside its stored keys, and plan lists it as a dry run with the filter. Every other config,
draw and generator: all 135, as before.

smoke passes when the smoke run of <config> (exp_01 --max-questions 1 --draws 1, its own .smoke run under
--root, default findings/recompute/T2_runs/smoke_sinks) holds exactly one answer, the first question at draw 1, stored
without an error under the generator; every call of it is a call of the generator's provider at the lock's settings,
role generator, draw 1, the lock's sha256, status ok or length, except verified_pass's verifier calls (Ollama,
gpt-oss:20b-date20261010, status ok); no call of another provider. The settings, by generator (GENERATORS):
  claude-haiku-4-5  model_id claude-haiku-4-5-20251001, options_sent temperature 1.0 and max_tokens 64000 and nothing
                    else (no seed); a request id; the answering model claude-haiku-4-5-20251001
  gemini-2.5-pro    options_sent temperature 1.0, topP 0.95, topK 64, maxOutputTokens 65536 and seed = the draw, and no
                    thinkingConfig (LOCK [thinking] generator "default": Google's default, nothing sent; [gemini]);
                    the posted bytes' sha256; the answering model gemini-2.5-pro
  gemma3:27b,       (the local lane) options_sent = Lock.ollama(<tag>, role generator, draw 1).options (the model's
  qwen3-coder:30b   [sampling.models] row, num_ctx 131072, num_predict -1, num_batch 1024, seed = the draw), fields_sent
                    truncate and shift false, keep_alive 24h, no think (both rows "omit"); the model's digest in
                    [models]; Ollama 0.40.2; the posted bytes' sha256. The verifier calls (verified_pass only) are told
                    apart by their model, gpt-oss:20b-date20261010, and must carry its digest and Ollama 0.40.2 too.
                    With --server (launch_t2_local.sh passes T2_GENERATOR_PORT's URL) every Ollama call of the smoke,
                    the generator's and the verifier's, must name that server (Q-L2: one server for both).
--write writes the verdict (with the generator) to smoke_<config>.verdict.json beside this file, which launch_t2.sh
run requires.
"""

from __future__ import annotations

import argparse
import collections
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUNS = ROOT / "findings" / "runs"
SMOKES = HERE / "smoke_sinks"
EXP01 = ROOT / "experiments" / "mentori" / "publication" / "scripts" / "exp_01_generation.py"
HAIKU, GEMINI_25_PRO = "anthropic::claude-haiku-4-5", "gemini::gemini-2.5-pro"
GEMMA3, QWEN3_CODER = "ollama::gemma3:27b", "ollama::qwen3-coder:30b"   # the local lane (D159 (2))
OLLAMA_VERSION = "0.40.2"   # LOCK [server] ollama_version
INDEX = "exp_v4_s20_n0"


def _price_anthropic(r: dict) -> float:
    # Anthropic's list prices for claude-haiku-4-5, USD per million tokens (platform.claude.com/docs/en/about-claude/
    # pricing, read 26 Oct 2026): input 1, output 5.
    return (r.get("prompt_tokens") or 0) / 1e6 * 1.0 + (r.get("output_tokens") or 0) / 1e6 * 5.0


def _price_gemini_25_pro(r: dict) -> float:
    # Google's paid-tier Standard prices for gemini-2.5-pro, USD per million tokens (ai.google.dev/gemini-api/docs/
    # pricing, "Last updated 2026-10-26 UTC", read 27 Oct 2026): input 1.25 for prompts <= 200k tokens, 2.50 above;
    # output "including thinking tokens" 10.00 for prompts <= 200k, 15.00 above. Per call, by its own prompt size.
    pt = r.get("prompt_tokens") or 0
    big = pt > 200_000
    out = (r.get("output_tokens") or 0) + (r.get("thinking_tokens") or 0)
    return pt / 1e6 * (2.5 if big else 1.25) + out / 1e6 * (15.0 if big else 10.0)


# Each generator T2 runs: its provider, model, the answering model the API must name, and the settings the lock sends
# at a draw (the expectation a smoke is held to; check_t2_test.py holds each equal to the lock's own reader).
GENERATORS = {
    HAIKU: {"provider": "anthropic", "model": "claude-haiku-4-5", "model_id": "claude-haiku-4-5-20251001",
            "answering": "claude-haiku-4-5-20251001", "id_field": "request_id",
            # LOCK [sampling.models] "claude-haiku-4-5" and [anthropic]; no seed (the Messages API takes none)
            "options": lambda draw: {"temperature": 1.0, "max_tokens": 64000}, "price": _price_anthropic},
    GEMINI_25_PRO: {"provider": "gemini", "model": "gemini-2.5-pro", "model_id": None,
                    "answering": "gemini-2.5-pro", "id_field": "request_sha256",
                    # LOCK [gemini]: temperature 1.0, top_p 0.95, top_k 64, max_output_tokens 65536, seed the draw;
                    # [thinking] generator "default": no thinkingConfig sent (lock.py Lock.gemini)
                    "options": lambda draw: {"temperature": 1.0, "topP": 0.95, "topK": 64, "maxOutputTokens": 65536,
                                             "seed": draw}, "price": _price_gemini_25_pro},
    # The local lane (D159 (2)): LOCK [sampling.models] rows with [generation]'s num_ctx, num_predict, num_batch and the
    # draw as seed (Lock.ollama, role generator); [server] truncate, shift false, keep_alive 24h; both rows think "omit",
    # so no think field. No per-call price (our servers). check_t2_test.py holds each equal to the lock's own reader.
    GEMMA3: {"provider": "ollama", "model": "gemma3:27b", "model_id": None, "local": True,
             "digest": "8dda00f4f636a0ae610bf6eae134d59de477256140276ec847510ce898cf910c", "id_field": "request_sha256",
             "options": lambda draw: {"num_ctx": 131072, "num_predict": -1, "num_batch": 1024, "temperature": 1.0,
                                      "top_p": 0.95, "top_k": 64, "min_p": 0.0, "repeat_penalty": 1.0,
                                      "presence_penalty": 0.0, "seed": draw},
             "fields": {"truncate": False, "shift": False, "keep_alive": "24h"}, "price": lambda r: 0.0},
    QWEN3_CODER: {"provider": "ollama", "model": "qwen3-coder:30b", "model_id": None, "local": True,
                  "digest": "06c1097efce0431c2045fe7b2e5108366e43bee1b4603a7aded8f21689e90bca",
                  "id_field": "request_sha256",
                  "options": lambda draw: {"num_ctx": 131072, "num_predict": -1, "num_batch": 1024, "temperature": 0.7,
                                           "top_p": 0.8, "top_k": 20, "min_p": 0.0, "repeat_penalty": 1.05,
                                           "presence_penalty": 0.0, "seed": draw},
                  "fields": {"truncate": False, "shift": False, "keep_alive": "24h"}, "price": lambda r: 0.0},
}
GENERATOR = os.environ.get("T2_GENERATOR") or HAIKU   # t2_lib.sh exports T2_GENERATOR; a script's own default


def gen_spec(generator: str) -> dict:
    if generator not in GENERATORS:
        raise SystemExit(f"generator {generator!r} is not one T2 runs: {', '.join(GENERATORS)}")
    return GENERATORS[generator]


def tag(generator: str) -> str:
    """exp_01's generator_tag: "+" and the model with ':' and '/' written '-'."""
    return "+" + generator.split("::", 1)[1].replace(":", "-").replace("/", "-")


# Haiku's names, as before D158 (check_t2_test.py's fixtures use them)
TAG = tag(HAIKU)
MODEL, MODEL_ID = GENERATORS[HAIKU]["model"], GENERATORS[HAIKU]["model_id"]
OPTIONS = GENERATORS[HAIKU]["options"](1)
VERIFIER = "gpt-oss:20b-date20261010"
VERIFIER_DIGEST = "41bf45e8998c34516dd702276336c7bb22a17278e53806194046bbc0afef8323"   # LOCK [models]
LOCK_WANT = "d66daa28596bf3b70ff90e0fb89b1353eab023eba699427cb05ebb3376105c12"
# G1's index as G1's single_pass sink recorded it (Studio, findings/runs/exp_01__single_pass__exp_v4_s20_n0/
# index_identity.jsonl, read 26 Oct 2026 00:41): the identity a store off the Studio is held to, on its content
G1_INDEX = {"index_name": INDEX, "collection": "collection_ee5fcaee-b9ad-41ce-8c24-a1d387230382", "n_chunks": 778,
            "id_text_sha256": "16444935ec7c02671f76f5f215de73950e1dde5c1a52dead87d05c8638ef9a1a",
            "chunk_manifest_sha256": "b9affe3fecad2245d24c8ed2379dd700d6d1041473595d1c7e738bccad9d51e2"}
CONTENT = ("index_name", "n_chunks", "chunk_manifest_sha256")   # the same chunk texts, whatever the chroma ids
CONFIGS = ["single_pass", "multi_hop", "rlm_5", "rlm_10", "rlm_20", "verified_pass"]
N_QUESTIONS = 135
D98_SUBSET = ROOT / "findings" / "recompute" / "D98_subset" / "d98_subset.json"   # S464's 45 questions (D98)
SUBSET_DRAWS = (2, 3)   # D98, D159 (2): a Gemini generator's draws on D98_SUBSET only (subset_draws)
# D175 Q3, D176: a local generator's RLM set-ups, on D98_SUBSET at every draw (subset_draws)
SUBSET_LOCAL_CONFIGS = ("rlm_5", "rlm_10", "rlm_20")
# The prices (GENERATORS' price) are for the progress line only; nothing is decided on them.


def is_gen(r: dict, g: dict) -> bool:
    """A call of the generator: its provider, and on the local lane its model (the verifier is an Ollama call too)."""
    return r.get("provider") == g["provider"] and (not g.get("local") or r.get("model") == g["model"])


def run_id(config: str, smoke: bool = False, generator: str | None = None) -> str:
    return f"exp_01__{config}__{INDEX}{tag(generator or GENERATOR)}" + (".smoke" if smoke else "")


def read_jsonl(path: Path) -> list:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def first_question() -> str:
    """The first question of key v2.4 in exp_01's order (experiment.questions()), which --max-questions 1 runs."""
    sys.path.insert(0, str(ROOT))
    from experiments.runner import experiment as ex
    return ex.questions()[0]["id"]


def smoke_verdict(config: str, root: Path = SMOKES, question: str | None = None,
                  generator: str | None = None, server: str | None = None) -> tuple[bool, list, dict]:
    """(passed, problems, facts) for the smoke run of config under root, by generator (default GENERATOR). server
    (the local lane): every Ollama call must name it."""
    generator = generator or GENERATOR
    g = gen_spec(generator)
    prov = g["provider"]
    question = question or first_question()
    sink = Path(root) / run_id(config, smoke=True, generator=generator)
    problems, facts = [], {"sink": str(sink), "generator": generator}
    answers, calls = read_jsonl(sink / "answers.jsonl"), read_jsonl(sink / "calls.jsonl")
    want_key = f"{INDEX}|{config}|{question}|d1"
    if len(answers) != 1:
        problems.append(f"{len(answers)} answer lines, not 1")
    for a in answers:
        if a.get("answer_key") != want_key:
            problems.append(f"answer key {a.get('answer_key')!r}, not {want_key!r}")
        if a.get("gen_model") != generator or (a.get("generation") or {}).get("gen_model") != generator:
            problems.append(f"gen_model {a.get('gen_model')!r}")
        if (a.get("generation") or {}).get("error"):
            problems.append(f"stored with an error: {a['generation']['error'][:200]}")
        facts["stop_reason"] = (a.get("generation") or {}).get("stop_reason")
        facts["answer_chars"] = len((a.get("generation") or {}).get("answer") or "")
    if not calls:
        problems.append("no call records")
    local = bool(g.get("local"))
    gen = [c for c in calls if is_gen(c, g)]
    ver = [c for c in calls if c.get("provider") == "ollama" and not is_gen(c, g)
           and (not local or c.get("model") == VERIFIER)]
    other = [c for c in calls if c not in gen and c not in ver]
    if other:
        problems.append(f"{len(other)} calls of another provider or model: "
                        f"{sorted({(str(c.get('provider')), str(c.get('model'))) for c in other})}")
    if ver and config != "verified_pass":
        problems.append(f"{len(ver)} Ollama calls in {config}, which has no verifier")
    if config == "verified_pass" and not ver:
        problems.append("verified_pass made no verifier call")
    for c in ver:
        if c.get("model") != VERIFIER or c.get("status") != "ok":
            problems.append(f"verifier call seq {c.get('seq')}: model {c.get('model')!r}, status {c.get('status')!r}")
        if local and (c.get("model_digest") != VERIFIER_DIGEST or c.get("ollama_version") != OLLAMA_VERSION):
            problems.append(f"verifier call seq {c.get('seq')}: digest {str(c.get('model_digest'))[:12]}, Ollama "
                            f"{c.get('ollama_version')!r}")
    if server is not None:
        for c in gen + ver:
            if str(c.get("server") or "").rstrip("/") != server.rstrip("/"):
                problems.append(f"call seq {c.get('seq')} ({c.get('model')}) on server {c.get('server')!r}, not {server}")
    if not gen:
        problems.append(f"no {prov} call")
    for c in gen:
        bad = []
        if c.get("model") != g["model"] or c.get("model_id") != g["model_id"]:
            bad.append(f"model {c.get('model')!r} {c.get('model_id')!r}")
        if local:
            if c.get("model_digest") != g["digest"] or c.get("ollama_version") != OLLAMA_VERSION:
                bad.append(f"digest {str(c.get('model_digest'))[:12]}, Ollama {c.get('ollama_version')!r}")
            if c.get("fields_sent") != g["fields"]:
                bad.append(f"fields_sent {c.get('fields_sent')!r}")
        elif not str(c.get("model_version") or "").startswith(g["answering"]):
            bad.append(f"answering model {c.get('model_version')!r}")
        if c.get("options_sent") != g["options"](1):
            bad.append(f"options_sent {c.get('options_sent')!r}")
        if c.get("draw") != 1 or c.get("run_draw") != 1:
            bad.append(f"draw {c.get('draw')!r}")
        if c.get("lock_sha256") != LOCK_WANT:
            bad.append(f"lock {str(c.get('lock_sha256'))[:12]}")
        if c.get("status") not in ("ok", "length"):
            bad.append(f"status {c.get('status')!r}: {str(c.get('error'))[:160]}")
        if not c.get(g["id_field"]):
            bad.append(f"no {g['id_field']}")
        if c.get("role") != "generator":
            bad.append(f"role {c.get('role')!r}")
        if bad:
            problems.append(f"call seq {c.get('seq')}: " + "; ".join(bad))
    facts.update(calls=len(calls), **{f"{prov}_calls": len(gen)}, verifier_calls=len(ver),
                 prompt_tokens=sum(c.get("prompt_tokens") or 0 for c in gen),
                 output_tokens=sum(c.get("output_tokens") or 0 for c in gen),
                 **({"thinking_tokens": sum(c.get("thinking_tokens") or 0 for c in gen),
                     "answering_models": sorted({str(c.get("model_version")) for c in gen}),
                     "usd_at_list_price": round(sum(g["price"](c) for c in gen), 4)} if prov == "gemini" else {}),
                 **({"servers": sorted({str(c.get("server")) for c in gen + ver}),
                     "stop_reasons": dict(collections.Counter(str(c.get("stop_reason")) for c in gen))}
                    if local else {}),
                 call_wall_s=round(sum(c.get("wall_s") or 0 for c in gen), 1),
                 statuses=dict(collections.Counter(c.get("status") for c in calls)),
                 attempts_resent=sum(max(len(c.get("attempts") or []) - 1, 0) for c in gen))
    return not problems, problems, facts


def progress(root: Path = RUNS, configs=CONFIGS, smoke: bool = False, generator: str | None = None) -> dict:
    """Per config: answer keys stored per draw, with an error, and the generator calls' tokens and statuses. At the
    draws the config runs on D98's subset (subset_draws), subset_stored counts the subset's 45 keys stored, out of
    subset_n (keys outside the subset, stored before D175 Q3 and D176, count in stored only)."""
    generator = generator or GENERATOR
    g = gen_spec(generator)
    prov = g["provider"]
    ids = subset_ids() if any(subset_draws(c, generator) for c in configs) else []
    out = {}
    for c in configs:
        sink = Path(root) / run_id(c, smoke, generator)
        last = {}
        for a in read_jsonl(sink / "answers.jsonl"):
            last[a["answer_key"]] = a
        per_draw = collections.Counter(int(k.rsplit("|d", 1)[1]) for k in last)
        sub = subset_draws(c, generator)
        want = {f"{INDEX}|{c}|{q}|d{d}" for q in ids for d in sub}
        in_sub = collections.Counter(int(k.rsplit("|d", 1)[1]) for k in last if k in want)
        err = collections.Counter(int(k.rsplit("|d", 1)[1]) for k, a in last.items()
                                  if (a.get("generation") or {}).get("error"))
        gen = [r for r in read_jsonl(sink / "calls.jsonl") if is_gen(r, g)]
        pt = sum(r.get("prompt_tokens") or 0 for r in gen)
        ot = sum(r.get("output_tokens") or 0 for r in gen)
        out[c] = {"stored": dict(sorted(per_draw.items())), "with_error": dict(sorted(err.items())),
                  f"{prov}_calls": len(gen), "calls": len(gen), "prompt_tokens": pt, "output_tokens": ot,
                  **({"thinking_tokens": sum(r.get("thinking_tokens") or 0 for r in gen)} if prov == "gemini"
                     else {}),
                  "usd_at_list_price": round(sum(g["price"](r) for r in gen), 2),
                  "statuses": dict(collections.Counter(r.get("status") for r in gen)),
                  **({"subset_n": len(ids), "subset_stored": {d: in_sub.get(d, 0) for d in sub}} if sub else {})}
    return out


def subset_draws(config: str, generator: str | None = None) -> tuple:
    """The draws at which a generator runs config on D98's subset only (exp_01 --question-ids-file D98_SUBSET):
    a local generator's rlm_5, rlm_10 and rlm_20 at every draw (D175 Q3 for gemma3:27b, D176 for qwen3-coder:30b: the
    local lane's rule; their other three configs run all 135); a Gemini generator's draws 2 and 3 of every config (D98,
    D159 (2), the Gemini cost); none for any other. t2_lib.sh subset_for holds the same rule for run_t2.sh, and
    check_t2_subset_test.py holds the two equal."""
    generator = generator or GENERATOR
    if config in SUBSET_LOCAL_CONFIGS and generator.startswith("ollama::"):   # the local lane (t2_lib.sh LOCAL)
        return (1, 2, 3)
    return SUBSET_DRAWS if generator.startswith("gemini::") else ()


def subset_ids() -> list:
    """D98's 45 question ids, as S464 wrote them (findings/recompute/D98_subset/d98_subset.json)."""
    return json.loads(D98_SUBSET.read_text(encoding="utf-8"))["ids"]


def complete(draws, root: Path = RUNS, configs=CONFIGS, generator: str | None = None) -> list:
    """The configs whose run lacks a stored line (error or not) for any of the 135 questions at a draw; [] = complete.
    At a draw the generator runs the config on D98's subset (subset_draws), each of the subset's 45 questions must have
    its line at that draw instead (progress's subset_stored, its keys read one by one); a key outside the 45 neither
    counts nor fails it (D175 Q3, D176: a local generator's RLM answers stored before the subset stay on disk)."""
    generator = generator or GENERATOR
    missing = []
    for c, p in progress(root, configs, generator=generator).items():
        sub = subset_draws(c, generator)
        for d in draws:
            if d in sub:
                have = p["subset_stored"][d]
                if have != p["subset_n"]:
                    missing.append(f"{c} draw {d}: {have} of D98's {p['subset_n']}")
            elif p["stored"].get(d, 0) != N_QUESTIONS:
                missing.append(f"{c} draw {d}: {p['stored'].get(d, 0)} of {N_QUESTIONS}")
    return missing


def stores(stores_root: Path, g1_sinks: Path, configs=CONFIGS, machine: str = "studio") -> list:
    """Problems with T2's stores: each must be made (clone.sha256) and hold exp_v4_s20_n0 READY. On the Studio it must
    be G1's own collection (collection, n_chunks, id_text_sha256, chunk_manifest_sha256 as G1's single_pass sink
    recorded them, read there); elsewhere G1's content (index_name, n_chunks, chunk_manifest_sha256 equal to G1_INDEX),
    its chroma ids being the copy's own."""
    import sqlite3
    sys.path.insert(0, str(ROOT))
    from experiments.runner import index_identity as ii
    if machine == "studio":
        held, keys = ii.held(Path(g1_sinks) / f"exp_01__single_pass__{INDEX}"), ii.SAME
        if held is None:
            return [f"G1's index identity not found under {g1_sinks}"]
    else:
        held, keys = G1_INDEX, CONTENT
    problems = []
    for c in configs:
        s = Path(stores_root) / c
        if not (s / "clone.sha256").exists():
            problems.append(f"{c}: {s} not made (no clone.sha256)")
            continue
        db = sqlite3.connect(f"file:{s / 'mentori_app.db'}?mode=ro&immutable=1", uri=True)
        row = db.execute("select vector_db_collection_name, status from user_collections where name=?",
                         (INDEX,)).fetchone()
        db.close()
        if row is None or row[1] != "READY":
            problems.append(f"{c}: {INDEX} not READY in {s}/mentori_app.db ({row!r})")
            continue
        got = ii.identity(s / "chroma_db", row[0], INDEX, immutable=True)
        diff = [k for k in keys if got.get(k) != held.get(k)]
        if diff:
            problems.append(f"{c}: differs from G1's index in {diff}")
    return problems


def plan(draws, configs, generator: str | None = None) -> int:
    """exp_01's dry run for the generator, imported (no command line names exp_01). The configs' subset draws
    (subset_draws: a Gemini generator's 2 and 3, a local generator's RLM configs at every draw, D175 Q3, D176) are a
    dry run of their own with --question-ids-file D98_SUBSET, as run_t2.sh starts them, so the plan lists what the
    launcher runs: one dry run per set of configs that share their draws and filter, the unfiltered first."""
    tmp = Path(tempfile.mkdtemp(prefix="t2_plan_"))
    for k, v in {"DATABASE_URL": f"sqlite:///{tmp}/plan.db", "WORKSPACE_DIR": str(tmp / "ws"),
                 "CHROMA_PERSIST_DIRECTORY": str(tmp / "chroma")}.items():
        os.environ.setdefault(k, v)
    sys.path.insert(0, str(EXP01.parents[2]))
    sys.path.insert(0, str(EXP01.parent))
    spec = importlib.util.spec_from_file_location("e01_t2_plan", EXP01)
    e01 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(e01)
    generator = generator or GENERATOR
    runs = {}   # (draws, filtered) -> the configs run so, in CONFIGS' order
    for c in configs:
        sub = subset_draws(c, generator)
        for filtered in (False, True):
            ds = tuple(d for d in sorted(set(draws)) if (d in sub) == filtered)
            if ds:
                runs.setdefault((ds, filtered), []).append(c)
    for (ds, filtered), cs in sorted(runs.items(), key=lambda kv: kv[0][1]):
        e01.dry_run(cs, None, INDEX, ds, None, None, False, generator,
                    **({"question_ids_file": D98_SUBSET} if filtered else {}))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--generator", default=GENERATOR, choices=sorted(GENERATORS),
                    help="the generator whose runs are read (default T2_GENERATOR, else claude-haiku-4-5)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("smoke")
    s.add_argument("config", choices=CONFIGS)
    s.add_argument("--root", type=Path, default=SMOKES)
    s.add_argument("--server", help="the local lane: the server every Ollama call of the smoke must name")
    s.add_argument("--write", action="store_true")
    p = sub.add_parser("progress")
    p.add_argument("--root", type=Path, default=RUNS)
    c = sub.add_parser("complete")
    c.add_argument("--draws", nargs="+", type=int, required=True)
    c.add_argument("--configs", nargs="+", default=CONFIGS, choices=CONFIGS)
    c.add_argument("--root", type=Path, default=RUNS)
    st = sub.add_parser("stores")
    st.add_argument("--stores", type=Path, default=Path.home() / "paper_store_t2")
    st.add_argument("--g1-sinks", type=Path, default=Path.home() / "projects" / "mentori-runs" / "findings" / "runs")
    st.add_argument("--configs", nargs="+", default=CONFIGS, choices=CONFIGS)
    st.add_argument("--machine", choices=["studio", "laptop", "beelink"], default="studio")
    pl = sub.add_parser("plan")
    pl.add_argument("--draws", nargs="+", type=int, default=[1, 2, 3], choices=[1, 2, 3])
    pl.add_argument("--configs", nargs="+", default=CONFIGS, choices=CONFIGS)
    a = ap.parse_args(argv)
    if a.cmd == "smoke":
        ok, problems, facts = smoke_verdict(a.config, a.root, generator=a.generator, server=a.server)
        print(f"T2 smoke {a.config}: {'PASS' if ok else 'FAIL'} {json.dumps(facts)}")
        for p_ in problems:
            print(f"  problem: {p_}")
        if a.write:
            commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
            (HERE / f"smoke_{a.config}.verdict.json").write_text(json.dumps(
                {"config": a.config, "generator": a.generator, "pass": ok, "problems": problems, "facts": facts,
                 "commit": commit,
                 "lock_sha256": LOCK_WANT}, indent=1) + "\n")
        return 0 if ok else 1
    if a.cmd == "progress":
        out = progress(a.root, generator=a.generator)
        for k, v in out.items():
            think = f", {v['thinking_tokens']:,} thinking" if "thinking_tokens" in v else ""
            sub = (f" (D98's subset: {v['subset_stored']} of {v['subset_n']})" if "subset_stored" in v else "")
            print(f"{run_id(k, generator=a.generator):<52} stored {v['stored']}{sub} with error {v['with_error']} calls "
                  f"{v['calls']} tokens {v['prompt_tokens']:,} in, {v['output_tokens']:,} out{think} "
                  f"(${v['usd_at_list_price']}) statuses {v['statuses']}")
        tot = sum(v["usd_at_list_price"] for v in out.values())
        print(f"total at list price: ${tot:.2f}")
        return 0
    if a.cmd == "complete":
        missing = complete(a.draws, a.root, a.configs, a.generator)
        print("complete" if not missing else "incomplete: " + "; ".join(missing))
        return 0 if not missing else 1
    if a.cmd == "stores":
        problems = stores(a.stores, a.g1_sinks, a.configs, a.machine)
        what = "G1's index" if a.machine == "studio" else "G1's chunk texts (its own chroma ids)"
        print(f"stores: every store holds {what}" if not problems else "stores: " + "; ".join(problems))
        return 0 if not problems else 1
    return plan(a.draws, a.configs, a.generator)


if __name__ == "__main__":
    sys.exit(main())
