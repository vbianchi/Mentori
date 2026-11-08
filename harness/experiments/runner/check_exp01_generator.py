"""Checks for exp_01's generator option (D83 Q173, D142; T2's claude-haiku-4-5 arm of Figure 2 panel f).

    uv run --project experiments/mentori --frozen python -m experiments.runner.check_exp01_generator            # checks
    uv run --project experiments/mentori --frozen python -m experiments.runner.check_exp01_generator --mutants  # + mutants

Offline: no model, no index, no database, no server, no key. Every model call that part 3 makes goes through the real
ModelRouter, lock_adapter and experiments/runner/anthropic_client, whose HTTP layer (_open) is replaced by a fake
Anthropic stream and whose key reader (_key) by a constant, so no key is read. gemini_client's calls and HTTP layer are
tripwires; the verifier's Ollama call (ollama_client.generate) returns a fake record. Part 5 runs the real
ollama_client against two fake Ollama servers on 127.0.0.1 (threads of this process, answering as Ollama 0.40.2 with
the lock's digests): no model is called.

No command line this script starts names an exp_NN script (K1's busy guards on the laptop and the Beelink count any
process matching exp_[0-9]+...\\.py, findings/recompute/K1/run_k1_laptop.sh:18): the copy under test is loaded with
importlib from a file named e01_*.py and named to a child process through the environment (CHECK_E01_TARGET).

What it pins:
 1 Default unchanged. With no --generator, the changed exp_01 gives what exp_01 at BASELINE (4cd0c968, the last
   commit before the option) gives: config_run_id and config_models for all 7 configs (paper and smoke), work_list on
   a sink holding stored and failed keys (with and without --skip-failed), the dry run's printed lines (three cases),
   and every answers.jsonl line run_experiment writes on stubs (ctx_uid and pid aside), the strategies receiving
   gemini::gemini-3-flash-preview. The CLI without --generator passes the default.
 2 The option. generator_tag; run ids exp_01__<config>__exp_v4_s20_n0+claude-haiku-4-5[.smoke], all 14 distinct and
   none equal to a G1 or G2 run id; refusals before anything is read (a [think:x] suffix, an unknown provider,
   claude::, a model the lock does not run, an ollama:: tag with no digest in [models], glm-4.7-flash and the qwen3.5
   models for want of a general-task row (D83 Q181), matched_budget with another generator); a gemini:: model the lock
   runs is accepted with its own tag; ollama::gemma3:27b and ollama::qwen3-coder:30b are accepted (D158 (2));
   --generator-url refused with a cloud generator, required (http(s)) with a local one, and the verifier's own tag on
   another server refused in verified_pass; config_models keeps the verifier; a Haiku run beside G1 sinks holding
   stored answers starts, writes only its own sinks and leaves G1's byte for byte; a strategy error and an error
   outside the strategy are stored under Haiku's gen_model; the CLI passes --generator to the run and the dry run.
 3 Every generator call. run_experiment with --generator anthropic::claude-haiku-4-5 on all six configs (2 questions,
   draws 1 and 2, smoke runs) through the real router and lock adapter: every generator call is an Anthropic call
   (single pass, multi-hop's hops, verified pass's answer, the RLM's root turns and its sub-calls, each by its call
   site), every posted body is the lock's (claude-haiku-4-5-20251001, temperature 1.0, max_tokens 64000, stream; no
   seed, no top_p, no top_k, no thinking), every record carries its draw and no seed; the verifier is the one Ollama
   call (gpt-oss:20b-date20261010, chunk_verifier.py); no Gemini call is made; every answer is stored without an
   error, the RLM's with stop_reason final.
 5 A local generator (D158 (2)), through the real router, adapter and ollama_client, against a fake generator server
   and a fake verifier server: run_experiment with --generator ollama::gemma3:27b on all six configs (2 questions,
   draws 1 and 2, smoke runs): every generator call goes to the generator server and only the verifier's to the
   verifier server; every posted body is the lock's (model, the [sampling.models] row, seed the draw, num_ctx,
   num_predict, num_batch, truncate, shift, keep_alive, think as the maker's default); every record carries the
   [record] fields, its server, the lock's digest and Ollama version; no Gemini or Anthropic call; every answer stored
   without an error, the RLM's with stop_reason final. Then single pass with qwen3-coder:30b (its own row),
   llama3:8b (num_ctx 8,192 from [exceptions]) and gpt-oss:20b (the [date] copy, think medium); a generator server
   holding another digest or another Ollama version stops the run with nothing stored.
 6 The question filter (D159 (2), D98; exp_02's and exp_06's option, D112 Q11): read_ids_file reads D98's subset
   (S464, 45 ids, its sha256); the questions kept are the key's own in the key's order whatever the file's order; a
   file that is not JSON, holds no ids, an empty list, a non-string, an unknown or a repeated id is refused, as is the
   option with --max-questions (run_questions, the dry run, run_experiment); gemini-2.5-pro's dry run of draws 2 and 3
   lists 540 answers in its paper runs; on stubs, a filtered start of draws 2 and 3 beside draw 1's 135 stored answers
   starts without --resume, appends the 45 questions' d2 and d3 keys to the runs of draw 1 (draw 1's bytes kept),
   each line holding the filter's record; started again it is refused without --resume and runs nothing with it; an
   unfiltered resume afterwards runs the other 90 into the same run with no question_filter key; the CLI passes the
   option to the run and the dry run.
 4 (--mutants) Code mutants of the option in a copy of exp_01: each must fail part 1, 2, 3, 5 or 6.
"""

from __future__ import annotations

import asyncio
import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
MENTORI = ROOT / "experiments" / "mentori"
SCRIPTS = MENTORI / "publication" / "scripts"
EXP01 = SCRIPTS / "exp_01_generation.py"
BASELINE = "4cd0c968ee107bcda7b1de15b249219e83b9c73a"   # exp_01 at its last commit before the option (17 Oct)
HAIKU = "anthropic::claude-haiku-4-5"
I20 = "exp_v4_s20_n0"
BASE = "http://127.0.0.1:9"        # the run contexts' server: never contacted (the verifier's call is faked)
SUBSET = ROOT / "findings" / "recompute" / "D98_subset" / "d98_subset.json"   # D98's 45 questions (S464)

results: list = []
QUIET = bool(os.environ.get("CHECK_E01_QUIET"))


def check(name, ok, detail=""):
    results.append((name, bool(ok)))
    if not QUIET or not ok:
        print(f"{'PASS' if ok else 'FAIL'} {name}" + (f": {detail}" if detail and not ok else ""))
    return bool(ok)


def raises(fn, kind=BaseException):
    try:
        fn()
    except kind as e:
        return e
    return None


# ── part 4 (parent): mutants of a copy, each run in a child process named by the environment ──
MUTANTS = [
    ("the strategy gets the default generator", "                gen_model=generator,\n",
     "                gen_model=GEN_MODEL,\n"),
    ("config_models ignores the generator", '    models = {"generator": generator}\n',
     '    models = {"generator": GEN_MODEL}\n'),
    ("the verifier follows the generator", '        models["verifier"] = VERIFY_MODEL\n',
     '        models["verifier"] = generator\n'),
    ("run ids without the tag", "    extra = index_name + generator_tag(generator)\n", "    extra = index_name\n"),
    ("the default generator tagged", '    if generator == GEN_MODEL:\n        return ""\n',
     '    if False:\n        return ""\n'),
    ("the answer record names the default", '        "gen_model": generator,\n', '        "gen_model": GEN_MODEL,\n'),
    ("the contexts allow the default", "draw, config_models(config, generator),\n", "draw, config_models(config),\n"),
    ("the lock not asked", "no seed is sent (B11)\n                anthropic_client.settings(lock, name)\n",
     "no seed is sent (B11)\n                pass\n"),
    ("an ollama generator refused", 'CLOUD_GENERATORS + (LOCAL_GENERATOR,)', 'CLOUD_GENERATORS'),
    ("glm and qwen3.5 accepted (D83 Q181)", "        if row in NO_GENERAL_TASK_ROW:\n", "        if False:\n"),
    ("the ollama generator not checked against the lock",
     "                lock.ollama(name, role=\"generator\", draw=d)   # D158 (2)", "                pass   # D158 (2)"),
    ("the contexts get no servers map", "                                     judge=False, servers=servers)",
     "                                     judge=False)"),
    ("the generator sent to the verifier's server", "    return {tag: generator_url}\n",
     "    return {tag: base_url or generator_url}\n"),
    ("a local generator without --generator-url accepted",
     "    if not isinstance(generator_url, str) or not generator_url.startswith((\"http://\", \"https://\")):\n",
     "    if False:\n"),
    ("--generator-url accepted with a cloud generator",
     "        if generator_url is not None:\n            raise SystemExit(f\"--generator-url is for",
     "        if False:\n            raise SystemExit(f\"--generator-url is for"),
    ("the verifier's tag on two servers accepted", "            and generator_url.rstrip(\"/\") != base_url.rstrip(\"/\")):\n",
     "            and False):\n"),
    ("the run does not build the servers map", "    servers = generator_servers(configs, generator, generator_url, base_url)\n",
     "    servers = None\n"),
    ("the CLI run without --generator-url",
     "        generator_url=args.generator_url,\n        question_ids_file=args.question_ids_file,\n    ))",
     "        question_ids_file=args.question_ids_file,\n    ))"),
    ("matched_budget allowed", "    if generator != GEN_MODEL and MATCHED_BUDGET in configs:\n", "    if False:\n"),
    ("the run's work list without the generator",
     "    items = work_list(configs, questions, draws, index_name, smoke, root, skip_failed, generator)\n",
     "    items = work_list(configs, questions, draws, index_name, smoke, root, skip_failed)\n"),
    ("the dry run's work list without the generator",
     "    items = work_list(configs, questions, draws, index_name, smoke, sink_root, skip_failed, generator)\n",
     "    items = work_list(configs, questions, draws, index_name, smoke, sink_root, skip_failed)\n"),
    ("a strategy error stored under the default", "            gen = failed_answer(config, generator, e, log, time.time() - t0)\n",
     "            gen = failed_answer(config, GEN_MODEL, e, log, time.time() - t0)\n"),
    ("an outside error stored under the default", "                    result = failed_answer(config, generator, result, None, None)\n",
     "                    result = failed_answer(config, GEN_MODEL, result, None, None)\n"),
    ("the CLI run without the generator", "        generator=args.generator,\n        generator_url", "        generator_url"),
    ("the CLI dry run without the generator", "                args.skip_failed, args.generator, generator_url",
     "                args.skip_failed, generator_url"),
    # D159 (2): the question filter
    ("the filter keeps every question", '    kept = [q for q in questions if q["id"] in named]\n',
     "    kept = list(questions)\n"),
    ("the filter keeps the file's order", '    kept = [q for q in questions if q["id"] in named]\n',
     '    kept = [q for i in keep for q in questions if q["id"] == i]\n'),
    ("the answer line without the filter's record",
     '        **({"question_filter": question_filter} if question_filter is not None else {}),\n', ""),
    ("every answer line with a question_filter key", "question_filter} if question_filter is not None else {}),",
     "question_filter} if True else {}),"),
    ("an unknown id accepted", "    if unknown or repeated:\n", "    if repeated:\n"),
    ("a repeated id accepted", "    if unknown or repeated:\n", "    if unknown:\n"),
    ("the filter with --max-questions accepted",
     '    if max_questions is not None:\n        raise SystemExit("--question-ids-file with --max-questions',
     '    if False:\n        raise SystemExit("--question-ids-file with --max-questions'),
    ("a filtered start run as a smoke", "    smoke = max_questions is not None\n    root = runs_root(sink_root)\n",
     "    smoke = max_questions is not None or question_filter is not None\n    root = runs_root(sink_root)\n"),
    ("the run ignores the file",
     "run_questions(max_questions, question_ids_file, draws)\n    smoke = max_questions is not None\n    root =",
     "run_questions(max_questions, None, draws)\n    smoke = max_questions is not None\n    root ="),
    ("the dry run ignores the file",
     "run_questions(max_questions, question_ids_file, draws)\n    smoke = max_questions is not None\n    load_budget",
     "run_questions(max_questions, None, draws)\n    smoke = max_questions is not None\n    load_budget"),
    ("the CLI run without the file", "        question_ids_file=args.question_ids_file,\n    ))", "    ))"),
    ("the CLI dry run without the file",
     "generator_url=args.generator_url,\n                question_ids_file=args.question_ids_file)",
     "generator_url=args.generator_url)"),
    ("the run does not check the generator",
     "    check_generator(generator, draws)\n    _check_generator_configs(configs, generator)\n    servers = generator_servers(",
     "    servers = generator_servers("),
]


def child(target: Path, quiet: bool) -> subprocess.CompletedProcess:
    env = {**os.environ, "CHECK_E01_TARGET": str(target)}
    if quiet:
        env["CHECK_E01_QUIET"] = "1"
    return subprocess.run([sys.executable, "-m", "experiments.runner.check_exp01_generator"], cwd=ROOT, env=env,
                          capture_output=True, text=True, timeout=900)


def parent(mutants: bool) -> int:
    tmp = Path(tempfile.mkdtemp(prefix="check_e01gen_"))
    real = tmp / "e01_real.py"
    real.write_text(EXP01.read_text(encoding="utf-8"), encoding="utf-8")
    p = child(real, quiet=False)
    print(p.stdout, end="")
    if p.returncode != 0:
        print(p.stderr[-4000:])
        print("FAIL the checks on exp_01 as it is (the mutants are not run)")
        return 1
    if not mutants:
        return 0
    src = EXP01.read_text(encoding="utf-8")
    killed, bad = 0, 0
    for name, old, new in MUTANTS:
        n = src.count(old)
        if n != 1:
            print(f"FAIL mutant '{name}' applies once: {n} matches")
            bad += 1
            continue
        m = tmp / "e01_mutant.py"
        m.write_text(src.replace(old, new), encoding="utf-8")
        q = child(m, quiet=True)
        caught = q.returncode != 0
        by = [ln[5:].split(":")[0] for ln in q.stdout.splitlines() if ln.startswith("FAIL ")][:2]
        if not caught:
            bad += 1
        killed += caught
        print(f"{'PASS' if caught else 'FAIL'} mutant killed: {name}" + (f" (by: {'; '.join(by)})" if caught else ""))
    print(f"mutants killed: {killed} of {len(MUTANTS)}")
    return 1 if bad else 0


# ── the child: every check against the copy named by CHECK_E01_TARGET ──
def child_main(target: Path) -> int:
    tmp = Path(tempfile.mkdtemp(prefix="check_e01gen_child_")).resolve()
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/check.db"
    os.environ["WORKSPACE_DIR"] = str(tmp / "ws")
    os.environ["CHROMA_PERSIST_DIRECTORY"] = str(tmp / "chroma")
    os.environ["BACKEND_INTERNAL_URL"] = BASE
    os.environ["TOOL_SERVER_URL"] = BASE
    os.environ.pop("ANTHROPIC_API_KEY", None)        # no key is read: anthropic_client._key is replaced below
    sys.path.insert(0, str(MENTORI))
    sys.path.insert(0, str(SCRIPTS))

    def load(name: str, path: Path):
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod

    base_src = subprocess.run(["git", "show", f"{BASELINE}:experiments/mentori/publication/scripts/exp_01_generation.py"],
                              cwd=ROOT, capture_output=True, text=True, check=True).stdout
    (tmp / "e01_base.py").write_text(base_src, encoding="utf-8")
    eb = load("e01_base", tmp / "e01_base.py")
    en = load("e01_new", target)
    real_dispatch = en._run_config          # part 3 runs the module's own dispatch; parts 1 and 2 stub it

    from experiments.runner import experiment as ex
    from experiments.runner import run_context as rc
    from experiments.runner import anthropic_client as ac
    from experiments.runner import gemini_client as gc
    from experiments.runner import ollama_client as oc
    from backend.agents import lock_adapter as la
    from backend.retrieval.rlm.context import RLMContext, DocumentInfo
    from backend.retrieval.reranker import CrossEncoderReranker

    qs = ex.questions()
    G = en.GEN_MODEL

    # ═════════════════════════ 1. default unchanged ═════════════════════════
    check("1 the default generator is the module's GEN_MODEL, gemini::gemini-3-flash-preview",
          G == eb.GEN_MODEL == "gemini::gemini-3-flash-preview")
    same = all(en.config_run_id(c, i, s) == eb.config_run_id(c, i, s) and en.config_models(c) == eb.config_models(c)
               for c in eb.ALL_CONFIGS for i in (I20, "exp_v4_s5_n0") for s in (False, True))
    check("1 config_run_id and config_models for all 7 configs, paper and smoke: as at BASELINE", same)

    root1 = tmp / "runs1"
    sp = root1 / eb.config_run_id("single_pass", I20)
    sp.mkdir(parents=True)
    (sp / eb.ANSWERS).write_text(
        json.dumps({"answer_key": ex.answer_key("single_pass", qs[0]["id"], 1, index=I20), "generation": {"error": None}})
        + "\n" + json.dumps({"answer_key": ex.answer_key("single_pass", qs[1]["id"], 1, index=I20),
                             "generation": {"error": "boom"}}) + "\n")
    wl_same = all(en.work_list(eb.CONFIG_NAMES, qs[:5], (1, 2, 3), I20, s, root1, f)
                  == eb.work_list(eb.CONFIG_NAMES, qs[:5], (1, 2, 3), I20, s, root1, f)
                  for s in (False, True) for f in (False, True))
    check("1 work_list on a sink with a stored and a failed key, smoke or not, --skip-failed or not: as at BASELINE",
          wl_same)

    def printed(fn):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            e = raises(fn, SystemExit)
        return buf.getvalue(), e

    cases = {"all six, draws 1-3": dict(configs=eb.CONFIG_NAMES, max_questions=None, index_name=I20, draws=(1, 2, 3),
                                         sink_root=root1),
             "smoke, 3 questions": dict(configs=eb.CONFIG_NAMES, max_questions=3, index_name=I20, draws=(1,),
                                         sink_root=root1),
             "--skip-failed": dict(configs=["single_pass"], max_questions=None, index_name=I20, draws=(1,),
                                   sink_root=root1, skip_failed=True)}
    for name, kw in cases.items():
        a, ea = printed(lambda: eb.dry_run(**kw))
        b, eb_ = printed(lambda: en.dry_run(**kw))
        check(f"1 the dry run ({name}) prints exactly what it printed at BASELINE", a == b and ea is None and eb_ is None
              and a.count("\n") > 3, f"{len(a)} against {len(b)} characters")

    # run_experiment on stubs, the baseline and the new code with the default generator
    seen: dict = {}

    def stub(mod, root, tag):
        seen[tag] = []

        async def fake_config(config_name, question, retriever, collection_name, router, gen_model, user_id,
                              index_name, budget=None):
            seen[tag].append(gen_model)
            return mod.GenerationResult(answer="a", latency_s=0.0, llm_calls=0, tokens_used=0, retrieved_passages=0,
                                        config=config_name, gen_model=gen_model)
        for n, v in {"_run_config": fake_config, "find_admin_user_id": lambda: "u",
                     "check_index_exists": lambda u, i: True, "setup_retriever": lambda u, i: (None, "coll", "emb"),
                     "ModelRouter": lambda: None,
                     "index_identity": SimpleNamespace(record=lambda sink, *a, **k: None), "RUNS_ROOT": root}.items():
            setattr(mod, n, v)

    def run_on(mod, **kw):
        with contextlib.redirect_stdout(io.StringIO()):
            return raises(lambda: asyncio.run(mod.run_experiment(base_url=BASE, index_name=I20, **kw)), SystemExit)

    def lines(root):
        out = {}
        for f in sorted(Path(root).rglob("answers.jsonl")):
            out[str(f.relative_to(root))] = [{k: v for k, v in json.loads(x).items() if k not in ("ctx_uid", "pid")}
                                             for x in f.read_text().splitlines()]
        return out

    rb, rn = tmp / "runs_base", tmp / "runs_new"
    stub(eb, rb, "base")
    stub(en, rn, "new")
    e1 = run_on(eb, configs=eb.CONFIG_NAMES, max_questions=2, draws=(1, 2))
    e2 = run_on(en, configs=eb.CONFIG_NAMES, max_questions=2, draws=(1, 2))
    lb, ln_ = lines(rb), lines(rn)
    check("1 run_experiment on stubs with the default generator writes the answers.jsonl lines it wrote at BASELINE "
          "(same run ids, sinks, keys and fields; ctx_uid and pid aside)",
          e1 is None and e2 is None and lb == ln_ and sum(len(v) for v in lb.values()) == 24,
          f"{e1!r} {e2!r} {sorted(lb)} {sorted(ln_)}")
    check("1 every strategy got gemini::gemini-3-flash-preview, as at BASELINE",
          seen["base"] == seen["new"] == [G] * 24)

    def cli(mod, argv):
        got = {}

        async def fake_run(**kw):
            got["run"] = kw

        def fake_dry(*a, **kw):
            got["dry"] = a
            got["dry_kw"] = kw
        saved = mod.run_experiment, mod.dry_run, sys.argv
        mod.run_experiment, mod.dry_run, sys.argv = fake_run, fake_dry, ["e01", *argv]
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                e = raises(mod.main, SystemExit)
        finally:
            mod.run_experiment, mod.dry_run, sys.argv = saved
        return got, e
    got, e = cli(en, ["--ollama-url", BASE])
    check("1 the CLI without --generator runs the default generator", e is None
          and got.get("run", {}).get("generator") == G, repr(got))

    # ═════════════════════════ 2. the option ═════════════════════════
    check("2 generator_tag: '' for the default, +claude-haiku-4-5, +gemini-2.5-pro",
          en.generator_tag(G) == "" and en.generator_tag(HAIKU) == "+claude-haiku-4-5"
          and en.generator_tag("gemini::gemini-2.5-pro") == "+gemini-2.5-pro")
    h_ids = [en.config_run_id(c, I20, s, HAIKU) for c in en.CONFIG_NAMES for s in (False, True)]
    g_ids = {en.config_run_id(c, I20, s) for c in en.ALL_CONFIGS for s in (False, True)}
    check("2 Haiku's run ids are exp_01__<config>__exp_v4_s20_n0+claude-haiku-4-5[.smoke]",
          h_ids == [f"exp_01__{c}__{I20}+claude-haiku-4-5" + (".smoke" if s else "")
                    for c in en.CONFIG_NAMES for s in (False, True)], str(h_ids[:2]))
    check("2 the 12 Haiku run ids are distinct, none is a G1 or G2 run id, and each is a valid sink name",
          len(set(h_ids)) == 12 and not set(h_ids) & g_ids
          and all(ex.run_id(*r.split("__", 2)) == r for r in h_ids))
    for bad in ("anthropic::claude-haiku-4-5[think:high]", "ollama::gemma3:27b[think:high]",
                "claude::claude-haiku-4-5", "openai::gpt-5", "anthropic::", "ollama::", "anthropic::claude-sonnet-4-5",
                "gemini::gemini-9-nonexistent", " anthropic::claude-haiku-4-5", "ollama::llama3.3:70b",
                "ollama::olmo-3:32b", "ollama::qwen3.8:27b-mlx"):
        e = raises(lambda: en.check_generator(bad, (1, 2, 3)), SystemExit)
        check(f"2 --generator {bad!r} is refused before anything is read", e is not None)
    for bad in ("ollama::glm-4.7-flash:bf16", "ollama::glm-4.7-flash", "ollama::qwen3.5:122b", "ollama::qwen3.5:35b"):
        e = raises(lambda: en.check_generator(bad, (1,)), SystemExit)
        check(f"2 --generator {bad!r} is refused for want of a general-task row (D83 Q181)",
              e is not None and "D83 Q181" in str(e), repr(e))
    check("2 ollama::gemma3:27b and ollama::qwen3-coder:30b are accepted at draws 1 to 3 (D158 (2)), tagged "
          "+gemma3-27b and +qwen3-coder-30b",
          en.check_generator("ollama::gemma3:27b", (1, 2, 3)) == "ollama::gemma3:27b"
          and en.check_generator("ollama::qwen3-coder:30b", (1, 2, 3)) == "ollama::qwen3-coder:30b"
          and en.generator_tag("ollama::gemma3:27b") == "+gemma3-27b"
          and en.generator_tag("ollama::qwen3-coder:30b") == "+qwen3-coder-30b")
    GEM3 = "ollama::gemma3:27b"
    for name, fn in {
            "--generator-url with a cloud generator": lambda: en.generator_servers(["single_pass"], HAIKU, "http://x:1"),
            "a local generator without --generator-url": lambda: en.generator_servers(["single_pass"], GEM3, None),
            "a local generator with a --generator-url that is not http(s)":
                lambda: en.generator_servers(["single_pass"], GEM3, "127.0.0.1:11460"),
            "gpt-oss:20b as the generator on another server than the verifier's, in verified_pass":
                lambda: en.generator_servers(["verified_pass"], "ollama::gpt-oss:20b", "http://h:2", "http://h:3")}.items():
        check(f"2 {name} is refused", raises(fn, SystemExit) is not None)
    check("2 generator_servers: None for the default and Haiku; {tag: url} for a local generator; gpt-oss:20b on the "
          "verifier's own server, or in a config without the verifier, is accepted",
          en.generator_servers(en.CONFIG_NAMES, G, None) is None and en.generator_servers(en.CONFIG_NAMES, HAIKU, None)
          is None and en.generator_servers(["single_pass"], GEM3, "http://h:2", "http://h:3") == {"gemma3:27b": "http://h:2"}
          and en.generator_servers(["verified_pass"], "ollama::gpt-oss:20b", "http://h:3/", "http://h:3")
          == {"gpt-oss:20b": "http://h:3/"}
          and en.generator_servers(["single_pass"], "ollama::gpt-oss:20b", "http://h:2", "http://h:3")
          == {"gpt-oss:20b": "http://h:2"})
    check("2 Haiku and gemini-2.5-pro are accepted at draws 1 to 3",
          en.check_generator(HAIKU, (1, 2, 3)) == HAIKU
          and en.check_generator("gemini::gemini-2.5-pro", (1, 2, 3)) == "gemini::gemini-2.5-pro")
    check("2 config_models: the generator in every config, the verifier stays ollama::gpt-oss:20b",
          all(en.config_models(c, HAIKU)["generator"] == HAIKU for c in en.CONFIG_NAMES)
          and en.config_models("verified_pass", HAIKU) == {"generator": HAIKU, "verifier": "ollama::gpt-oss:20b"}
          and en.config_models("rlm_10", HAIKU) == {"generator": HAIKU})
    plan = tmp / "plan.json"          # a plan valid for every question, so only the generator rule can refuse
    plan.write_text(json.dumps({"kind": "matched_budget_plan", "questions": {q["id"]: {"top_k": 5} for q in qs}}))
    out, e = printed(lambda: en.dry_run(["matched_budget"], None, I20, (1,), plan, root1, False, G))
    check("2 matched_budget with the default generator and a valid plan: the dry run runs (control)", e is None
          and "= 135 answers" in out, repr(e))
    out, e = printed(lambda: en.dry_run(["matched_budget"], None, I20, (1,), plan, root1, False, HAIKU))
    check("2 matched_budget with another generator is refused (D51, D83 Q177), even with a valid plan",
          e is not None and "D51" in str(e), repr(e))
    e = raises(lambda: asyncio.run(en.run_experiment(["single_pass"], BASE, index_name=I20, draws=(1,),
                                                     generator="ollama::gemma3:27b")), SystemExit)
    check("2 run_experiment refuses a local generator without --generator-url before anything is read", e is not None
          and "--generator-url" in str(e) and not (en.RUNS_ROOT / f"exp_01__single_pass__{I20}+gemma3-27b").exists(),
          repr(e))
    e = raises(lambda: asyncio.run(en.run_experiment(["single_pass"], BASE, index_name=I20, draws=(1,),
                                                     generator="ollama::qwen3.5:122b", generator_url=BASE)), SystemExit)
    check("2 run_experiment refuses qwen3.5:122b (D83 Q181) before anything is read", e is not None
          and "D83 Q181" in str(e), repr(e))
    e = raises(lambda: asyncio.run(en.run_experiment(["single_pass"], BASE, index_name=I20, draws=(1,),
                                                     generator=HAIKU, generator_url=BASE)), SystemExit)
    check("2 run_experiment refuses --generator-url with Haiku", e is not None, repr(e))
    out, e = printed(lambda: en.dry_run(en.CONFIG_NAMES, None, I20, (1, 2, 3), None, root1, False,
                                        GEM3, generator_url="http://127.0.0.1:2"))
    check("2 the dry run of gemma3:27b lists 2,430 answers in its own +gemma3-27b runs and names its server",
          e is None and "= 2430 answers" in out and out.count(f"{I20}+gemma3-27b ") == 18
          and "generator server http://127.0.0.1:2" in out, out[-500:] + repr(e))

    # G1's single_pass sink (1 stored, 1 failed key at draw 1) beside a Haiku rlm_10 sink with 2 stored keys
    root2 = tmp / "runs2"
    (root2 / en.config_run_id("single_pass", I20)).mkdir(parents=True)
    (root2 / en.config_run_id("single_pass", I20) / en.ANSWERS).write_bytes((sp / eb.ANSWERS).read_bytes())
    hk = root2 / en.config_run_id("rlm_10", I20, False, HAIKU)
    hk.mkdir(parents=True)
    (hk / en.ANSWERS).write_text("".join(json.dumps({"answer_key": ex.answer_key("rlm_10", q["id"], 1, index=I20),
                                                     "generation": {"error": None}}) + "\n" for q in qs[:2]))
    out, e = printed(lambda: en.dry_run(en.CONFIG_NAMES, None, I20, (1, 2, 3), None, root2, False, HAIKU))
    check("2 Haiku's dry run lists 6 configs x 3 draws of 135 = 2,430 answers in its own runs, counts only its own "
          "stored answers (2, none of G1's), the verifier kept",
          e is None and "= 2430 answers, 2 stored, 2428 pending (0 of them stored with an error" in out
          and out.count(f"{I20}+claude-haiku-4-5 ") == 18
          and "generator anthropic::claude-haiku-4-5" in out and "'verifier': 'ollama::gpt-oss:20b'" in out,
          out[-600:])

    # a Haiku run beside G1 sinks that hold stored answers
    rh = tmp / "runs_haiku"
    stub(en, rh, "haiku")
    for c in en.CONFIG_NAMES:
        g1 = rh / en.config_run_id(c, I20, True)
        g1.mkdir(parents=True)
        (g1 / en.ANSWERS).write_text(json.dumps({"answer_key": ex.answer_key(c, qs[0]["id"], 1, index=I20),
                                                 "generation": {"error": None}}) + "\n")
    g1_before = {str(f.relative_to(rh)): f.read_bytes() for f in rh.rglob("*") if f.is_file()}
    e = run_on(en, configs=en.CONFIG_NAMES, max_questions=2, draws=(1, 2), generator=HAIKU)
    after = {str(f.relative_to(rh)): f.read_bytes() for f in rh.rglob("*") if f.is_file()}
    hl = lines(rh)
    mine = {k: v for k, v in hl.items() if "+claude-haiku-4-5" in k}
    check("2 a Haiku run beside G1 sinks holding stored answers starts and stores its 24 answers in its own .smoke "
          "sinks", e is None and sorted(mine) == sorted(f"exp_01__{c}__{I20}+claude-haiku-4-5.smoke/answers.jsonl"
                                                        for c in en.CONFIG_NAMES)
          and sum(len(v) for v in mine.values()) == 24, repr(e))
    check("2 G1's sinks are byte for byte as before the Haiku run",
          all(after[k] == v for k, v in g1_before.items()) and all("+claude-haiku-4-5" in k for k in after
                                                                   if k not in g1_before))
    check("2 each Haiku answer line names Haiku (gen_model, models, generation.gen_model) and its own run",
          all(r["gen_model"] == HAIKU and r["models"]["generator"] == HAIKU and r["generation"]["gen_model"] == HAIKU
              and r["run_id"] == k.split("/")[0] for k, v in mine.items() for r in v)
          and seen["haiku"] == [HAIKU] * 24)
    ident = {json.loads((rh / k.split("/")[0] / "run_identity.json").read_text())["agent_roles"]["generator"]
             for k in mine}
    check("2 each Haiku sink's run identity names Haiku as the generator", ident == {HAIKU}, str(ident))

    # errors stored under Haiku: a strategy that raises, and an error outside the strategy
    re_root = tmp / "runs_err"
    stub(en, re_root, "err")

    async def boom(*a, **k):
        raise RuntimeError("strategy failed")
    en._run_config = boom
    e = run_on(en, configs=["single_pass"], max_questions=1, draws=(1,), generator=HAIKU)
    r = lines(re_root).get(f"exp_01__single_pass__{I20}+claude-haiku-4-5.smoke/answers.jsonl", [{}])[0]
    check("2 a strategy error is stored under Haiku's gen_model", e is None and r.get("generation", {}).get("error")
          and r["generation"]["gen_model"] == HAIKU and r["gen_model"] == HAIKU, json.dumps(r)[:300])
    saved_p1 = en._process_one

    async def outside(*a, **k):
        raise ValueError("outside the strategy")
    en._process_one = outside
    e = run_on(en, configs=["multi_hop"], max_questions=1, draws=(1,), generator=HAIKU)
    en._process_one = saved_p1
    r = lines(re_root).get(f"exp_01__multi_hop__{I20}+claude-haiku-4-5.smoke/answers.jsonl", [{}])[0]
    check("2 an error outside the strategy is stored under Haiku's gen_model", e is None
          and r.get("generation", {}).get("gen_model") == HAIKU and r.get("gen_model") == HAIKU, json.dumps(r)[:300])

    got, e = cli(en, ["--ollama-url", BASE, "--generator", HAIKU, "--configs", "rlm_10", "--draws", "2"])
    check("2 the CLI passes --generator to the run", e is None and got.get("run", {}).get("generator") == HAIKU,
          repr(got))
    got, e = cli(en, ["--dry-run", "--generator", HAIKU])
    check("2 the CLI passes --generator to the dry run", e is None and got.get("dry", (None,))[-1] == HAIKU, repr(got))
    got, e = cli(en, ["--ollama-url", BASE, "--generator", GEM3, "--generator-url", "http://127.0.0.1:2"])
    check("2 the CLI passes --generator-url to the run", e is None and got.get("run", {}).get("generator") == GEM3
          and got["run"].get("generator_url") == "http://127.0.0.1:2", repr(got))
    got, e = cli(en, ["--dry-run", "--generator", GEM3, "--generator-url", "http://127.0.0.1:2"])
    check("2 the CLI passes --generator-url to the dry run", e is None
          and got.get("dry_kw", {}).get("generator_url") == "http://127.0.0.1:2", repr(got))

    # ═════════════════════════ 6. the question filter (D159 (2), D98) ═════════════════════════
    import hashlib
    G25 = "gemini::gemini-2.5-pro"
    sub_raw = SUBSET.read_bytes()
    sub_ids = json.loads(sub_raw)["ids"]
    ids6, rec6 = en.read_ids_file(SUBSET)
    check("6 read_ids_file reads D98's subset (S464): 45 ids in the file's order, the file's sha256",
          ids6 == sub_ids and len(ids6) == 45 and rec6 == {"option": "--question-ids-file", "file": str(SUBSET),
                                                          "file_sha256": hashlib.sha256(sub_raw).hexdigest(),
                                                          "n_named": 45}, json.dumps(rec6))
    in_key = [q for q in qs if q["id"] in set(sub_ids)]
    rev = tmp / "subset_reversed.json"            # a plain list, in the reverse order: the key's order still rules
    rev.write_text(json.dumps(list(reversed(sub_ids))))
    kept6, frec6 = en.run_questions(None, rev, (2, 3))
    check("6 run_questions: a plain list is read; the 45 kept are the key's own questions in the key's order, whatever "
          "the file's order; the record counts 45 of 135 and names the draws",
          [q["id"] for q in kept6] == [q["id"] for q in in_key] and len(kept6) == 45
          and [q["id"] for q in in_key] != list(reversed(sub_ids))
          and frec6["n_kept"] == 45 and frec6["n_set"] == 135 and frec6["draws"] == [2, 3], json.dumps(frec6))
    check("6 run_questions without the file: every question (or the first n of a smoke) and no record",
          en.run_questions(None, None, (1,)) == (qs, None) and en.run_questions(3, None, (1,)) == (qs[:3], None))
    bad_files = {"not JSON": "{", "an object without ids": json.dumps({"rule": "x"}), "an empty list": "[]",
                 "a list holding a number": json.dumps([sub_ids[0], 7]),
                 "an id not among the 135": json.dumps([sub_ids[0], "NO_SUCH_Q"]),
                 "an id named twice": json.dumps([sub_ids[0], sub_ids[1], sub_ids[0]])}
    for name, text in bad_files.items():
        f = tmp / f"bad_{len(name)}_{abs(hash(name)) % 10**6}.json"
        f.write_text(text)
        e = raises(lambda: en.run_questions(None, f, (2,)), SystemExit)
        check(f"6 a question-ids file holding {name} is refused", e is not None and "--question-ids-file" in str(e),
              repr(e))
    e = raises(lambda: en.read_ids_file(tmp / "no_such_file.json"), SystemExit)
    check("6 a question-ids file that does not exist is refused", e is not None, repr(e))
    e = raises(lambda: en.run_questions(3, SUBSET, (2,)), SystemExit)
    check("6 --question-ids-file with --max-questions is refused (one way of naming the questions, as exp_02)",
          e is not None and "--max-questions" in str(e), repr(e))

    root6 = tmp / "runs6"
    out, e = printed(lambda: en.dry_run(en.CONFIG_NAMES, None, I20, (2, 3), None, root6, False, G25,
                                        question_ids_file=SUBSET))
    first_d2 = ex.answer_key("single_pass", in_key[0]["id"], 2, index=I20)
    check("6 the dry run of gemini-2.5-pro's draws 2 and 3 on the subset: 6 configs x 2 draws x 45 = 540 answers, in "
          "its paper runs (no .smoke), the filter named, first key the first subset question at draw 2",
          e is None and "= 540 answers" in out and "45 questions (" in out and out.count(f"{I20}+gemini-2.5-pro ") == 12
          and ".smoke" not in out and "question filter (--question-ids-file" in out and "45 of the 135" in out
          and f"first key {first_d2};" in out, out[-700:] + repr(e))
    out, e = printed(lambda: en.dry_run(en.CONFIG_NAMES, None, I20, (1, 2, 3), None, root6, False, G25))
    check("6 the dry run of gemini-2.5-pro without the filter: 2,430 answers, no filter line (control)",
          e is None and "= 2430 answers" in out and "question filter" not in out, out[-300:])
    e = raises(lambda: en.dry_run(["single_pass"], 2, I20, (2,), None, root6, False, G25,
                                  question_ids_file=SUBSET), SystemExit)
    check("6 the dry run refuses the filter with --max-questions", e is not None, repr(e))

    # gemini-2.5-pro's paper runs holding draw 1 of all 135 (rlm_10's draw-1 line of one subset question an error)
    stub(en, root6, "g25")
    six = ["single_pass", "rlm_10"]
    for c in six:
        s6 = root6 / en.config_run_id(c, I20, False, G25)
        s6.mkdir(parents=True)
        (s6 / en.ANSWERS).write_text("".join(json.dumps(
            {"answer_key": ex.answer_key(c, q["id"], 1, index=I20),
             "generation": {"error": "boom" if (c == "rlm_10" and q["id"] == in_key[0]["id"]) else None}}) + "\n"
            for q in qs))
    d1_before = {c: (root6 / en.config_run_id(c, I20, False, G25) / en.ANSWERS).read_bytes() for c in six}
    e = run_on(en, configs=six, draws=(2, 3), generator=G25, question_ids_file=SUBSET)
    l6 = lines(root6)
    want_runs = sorted(f"{en.config_run_id(c, I20, False, G25)}/answers.jsonl" for c in six)
    new6 = {k: v[135:] for k, v in l6.items()}
    check("6 a filtered start of draws 2 and 3 beside draw 1's stored answers starts without --resume and appends to "
          "the paper runs of draw 1 (the run ids an unfiltered start uses, no .smoke, no other sink)",
          e is None and sorted(l6) == want_runs and all(len(v) == 135 + 90 for v in l6.values()), repr(e)
          + str({k: len(v) for k, v in l6.items()}))
    check("6 draw 1's 135 lines of each run are byte for byte as before",
          all((root6 / en.config_run_id(c, I20, False, G25) / en.ANSWERS).read_bytes().startswith(d1_before[c])
              for c in six))
    check("6 the new lines are the 45 subset questions at draws 2 and 3, in the key's order, each key once, keys "
          "distinct from draw 1's",
          all([r["answer_key"] for r in v] == [ex.answer_key(k.split("__")[1], q["id"], d, index=I20)
                                               for d in (2, 3) for q in in_key] for k, v in new6.items()),
          str([r["answer_key"] for r in list(new6.values())[0][:2]]))
    check("6 every new line stores the filter's record (file, its sha256, 45 of 135, draws [2, 3]) and gemini-2.5-pro",
          all(r.get("question_filter") == {**rec6, "n_kept": 45, "n_set": 135, "draws": [2, 3]}
              and r["gen_model"] == G25 for v in new6.values() for r in v),
          json.dumps(list(new6.values())[0][0].get("question_filter")))
    check("6 the strategy ran 180 answers, all gemini-2.5-pro", seen["g25"] == [G25] * 180, str(len(seen["g25"])))
    e = run_on(en, configs=six, draws=(2, 3), generator=G25, question_ids_file=SUBSET)
    check("6 the same filtered start again without --resume is refused (its answers are stored)", e is not None
          and sum(len(v) for v in lines(root6).values()) == 2 * 225, repr(e))
    e = run_on(en, configs=six, draws=(2, 3), generator=G25, question_ids_file=SUBSET, resume=True)
    check("6 with --resume it runs nothing more", e is None and sum(len(v) for v in lines(root6).values()) == 2 * 225
          and len(seen["g25"]) == 180, repr(e))
    e = run_on(en, configs=["single_pass"], draws=(2,), generator=G25, resume=True)
    l6b = lines(root6)[f"{en.config_run_id('single_pass', I20, False, G25)}/answers.jsonl"]
    check("6 an unfiltered resume of draw 2 afterwards runs the other 90 questions into the same run and stores no "
          "question_filter key",
          e is None and len(l6b) == 225 + 90 and all("question_filter" not in r for r in l6b[225:])
          and {r["question_id"] for r in l6b[225:]} == {q["id"] for q in qs} - set(sub_ids), repr(e))
    e = run_on(en, configs=["single_pass"], max_questions=2, draws=(2,), generator=G25, question_ids_file=SUBSET)
    check("6 run_experiment refuses the filter with --max-questions, nothing stored",
          e is not None and not (root6 / en.config_run_id("single_pass", I20, True, G25)).exists(), repr(e))
    got, e = cli(en, ["--ollama-url", BASE, "--generator", G25, "--draws", "2", "3", "--question-ids-file",
                      str(SUBSET)])
    check("6 the CLI passes --question-ids-file to the run", e is None
          and got.get("run", {}).get("question_ids_file") == SUBSET, repr(got))
    got, e = cli(en, ["--dry-run", "--generator", G25, "--question-ids-file", str(SUBSET)])
    check("6 the CLI passes --question-ids-file to the dry run", e is None
          and got.get("dry_kw", {}).get("question_ids_file") == SUBSET, repr(got))
    got, e = cli(en, ["--ollama-url", BASE])
    check("6 the CLI without --question-ids-file passes none", e is None
          and got.get("run", {}).get("question_ids_file") is None, repr(got))

    # ═════════════════════════ 3. every generator call, through the real adapter ═════════════════════════
    import backend.agents.model_router as mr
    en._run_config = real_dispatch
    en._process_one = saved_p1
    en.ModelRouter = mr.ModelRouter

    TEXT = {"a0": "Sample size was 24 patients.\nThe methods used fastp for trimming of reads before alignment.",
            "a1": "Results show 12 differentially expressed genes. methods appear twice: methods.",
            "a2": "A third chunk on page two with the word methods in it.",
            "b0": "Another paper about salmon quantification methods."}

    class FakeRetriever:
        def retrieve(self, query, collection_name=None, top_k=10, where=None, trace=None, **kw):
            if trace is not None:
                trace.append({"query": query, "reranked": True, "rerank_skipped": None, **kw})
            return [{"id": "a1", "text": TEXT["a1"], "score": 0.9, "rerank_score": 0.8,
                     "metadata": {"file_name": "a.pdf", "chunk_index": 1, "page": 1}},
                    {"id": "b0", "text": TEXT["b0"], "score": 0.1, "rerank_score": 0.2,
                     "metadata": {"file_name": "b.pdf", "chunk_index": 0, "page": 1}}]

    class FakeCE:
        max_length = 10 ** 6

        def tokenizer(self, *t, truncation=False):
            return {"input_ids": " ".join(t).split()}

        def predict(self, pairs):
            return [x.lower().count(q.lower()) for q, x in pairs]

    def make_context():
        c = RLMContext(index_name="check", user_id="u")
        for doc, rows in {"a.pdf": [("a0", 0, 1), ("a1", 1, 1), ("a2", 2, 2)], "b.pdf": [("b0", 0, 1)]}.items():
            c._chunks_by_doc[doc] = [{"id": i, "text": TEXT[i], "chunk_idx": k, "page": p,
                                      "metadata": {"file_name": doc}} for i, k, p in rows]
            c._documents[doc] = DocumentInfo(name=doc, file_path=doc, total_chunks=len(rows),
                                             total_pages=max(p for _, _, p in rows), title=doc)
        c.n_chunks_loaded = 4
        c._retriever = FakeRetriever()
        r = object.__new__(CrossEncoderReranker)
        r.model, r.model_name, r.is_available = FakeCE(), "fake", True
        c._reranker = r
        return c

    async def from_index(index_name, user_id, max_tokens=1_000_000):
        return make_context()

    WORK = ('ch = search_keyword("methods", doc_name="a.pdf")\n'
            'r1 = llm_summarize(ch, task="t")\nr2 = llm_summarize(ch, task="t")\nr3 = llm_summarize(ch, task="t")\n'
            'add_to_report("Methods", r1["summary"], r1["citations"])\nFINAL("Short: 24 patients [a.pdf:p1].")')
    SUMMARY = ("SUMMARY:\nThe sample size was 24 [1]. Methods used fastp [1, 2].\nCITATIONS_USED:\n1, 2\n")
    posted, gemini_calls, ollama_calls = [], [], []

    def reply_for(body):
        system = body.get("system") or ""
        text = "\n".join(m["content"] for m in body["messages"])
        if "repl" in system:
            return f"```repl\n{WORK}\n```"
        if "iterative document analysis" in system:
            return "FINAL ANSWER: 24 patients [a.pdf:1]."
        if "CITATIONS_USED" in text:
            return SUMMARY
        return "24 patients [a.pdf:1]."

    class Resp:
        def __init__(self, data_lines):
            self.lines, self.headers = data_lines, {"request-id": "req_offline"}

            class _Raw:
                class _sock:
                    @staticmethod
                    def settimeout(t):
                        pass
            self.fp = SimpleNamespace(raw=_Raw)

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def __iter__(self):
            return iter(self.lines)

    def sse(*events):
        return [x for e in events for x in (f"event: {e['type']}\n".encode(), f"data: {json.dumps(e)}\n".encode(),
                                            b"\n")]

    def fake_open(req, timeout=None):
        body = json.loads(req.data)
        posted.append(body)
        text = reply_for(body)
        return Resp(sse({"type": "message_start", "message": {"id": "msg_x", "model": "claude-haiku-4-5-20251001",
                                                             "usage": {"input_tokens": 50, "output_tokens": 1}}},
                        {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}},
                        {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": text}},
                        {"type": "content_block_stop", "index": 0},
                        {"type": "message_delta", "delta": {"stop_reason": "end_turn"}, "usage": {"output_tokens": 9}},
                        {"type": "message_stop"}))

    def tripwire(*a, **k):
        gemini_calls.append(a[:2])
        raise RuntimeError("a Gemini call was made")

    def fake_ollama_generate(base_url, call, prompt, passages=None, images=None, **kw):
        ollama_calls.append(call.model)
        return {"model": call.model, "role": call.role, "draw": call.draw, "candidate": call.candidate,
                "thinking": call.thinking, "options_sent": dict(call.options), "model_digest": call.digest,
                "server": base_url, "ollama_version": "offline", "lock_sha256": call.lock_sha256,
                "passages": passages, "status": "ok", "stop_reason": "stop", "error": None,
                "text": "[1] RELEVANT: states the sample size\n[2] NOT_RELEVANT: another paper",
                "thinking_text": "", "prompt_tokens": 40, "output_tokens": 12, "wall_s": 0.0}

    saved3 = (ac._open, ac._key, gc.generate, gc.chat, gc._open, oc.generate, oc.chat, RLMContext.__dict__["from_index"])
    ac._open, ac._key = fake_open, (lambda: "offline-key")
    gc.generate = gc.chat = gc._open = tripwire
    oc.generate, oc.chat = fake_ollama_generate, tripwire
    RLMContext.from_index = staticmethod(from_index)
    r3 = tmp / "runs3"
    for n, v in {"find_admin_user_id": lambda: "u", "check_index_exists": lambda u, i: True,
                 "setup_retriever": lambda u, i: (FakeRetriever(), "coll", "emb"),
                 "index_identity": SimpleNamespace(record=lambda sink, *a, **k: None), "RUNS_ROOT": r3}.items():
        setattr(en, n, v)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            e = raises(lambda: asyncio.run(en.run_experiment(configs=en.CONFIG_NAMES, base_url=BASE, index_name=I20,
                                                             max_questions=2, draws=(1, 2), generator=HAIKU)),
                       BaseException)
    finally:
        (ac._open, ac._key, gc.generate, gc.chat, gc._open, oc.generate, oc.chat) = saved3[:7]
        RLMContext.from_index = saved3[7]
    check("3 the Haiku run on all six configs ends without an exception", e is None, repr(e))
    ans = {c: [json.loads(x) for x in (r3 / f"exp_01__{c}__{I20}+claude-haiku-4-5.smoke" / en.ANSWERS)
                                       .read_text().splitlines()]
           for c in en.CONFIG_NAMES if (r3 / f"exp_01__{c}__{I20}+claude-haiku-4-5.smoke" / en.ANSWERS).exists()}
    calls = {c: [json.loads(x) for x in (r3 / f"exp_01__{c}__{I20}+claude-haiku-4-5.smoke" / "calls.jsonl")
                                         .read_text().splitlines()]
             for c in en.CONFIG_NAMES if (r3 / f"exp_01__{c}__{I20}+claude-haiku-4-5.smoke" / "calls.jsonl").exists()}
    check("3 every config stored its 4 answers (2 questions x draws 1, 2) without an error, under Haiku",
          sorted(ans) == sorted(en.CONFIG_NAMES) and all(len(v) == 4 for v in ans.values())
          and all(not r["generation"]["error"] and r["gen_model"] == HAIKU for v in ans.values() for r in v),
          {c: [r["generation"]["error"] for r in v] for c, v in ans.items()})
    check("3 the RLM answers end with stop_reason final",
          all(r["generation"]["stop_reason"] == "final" for c in ("rlm_5", "rlm_10", "rlm_20") for r in ans.get(c, [])),
          {c: [r["generation"]["stop_reason"] for r in ans.get(c, [])] for c in ("rlm_5", "rlm_10", "rlm_20")})
    check("3 no Gemini call was made (tripwire) and no record names Gemini",
          not gemini_calls and not any(r.get("provider") == "gemini" for v in calls.values() for r in v),
          str(gemini_calls[:2]))
    gen_recs = [r for v in calls.values() for r in v if r.get("provider") == "anthropic"]
    other = [(c, r.get("provider"), r.get("model"), r.get("call_site")) for c, v in calls.items() for r in v
             if r.get("provider") != "anthropic"]
    check("3 every call but the verifier's is an Anthropic call; the verifier's are Ollama gpt-oss:20b-date20261010 "
          "from chunk_verifier.py, in verified_pass only",
          other and all(c == "verified_pass" and p == "ollama" and m == "gpt-oss:20b-date20261010"
                        and "chunk_verifier.py" in (s or "") for c, p, m, s in other)
          and len(other) == len(ollama_calls) == 4, str(other[:3]))
    sites = {c: {(r.get("call_site") or "").split(":")[0] for r in v if r.get("provider") == "anthropic"}
             for c, v in calls.items()}
    want = {"single_pass": {"tests/experiments/exp1_rlm_vs_singlepass.py"},
            "multi_hop": {"tests/experiments/exp1_rlm_vs_singlepass.py"},
            "verified_pass": {"backend/retrieval/pipeline.py"},
            **{c: {"backend/retrieval/rlm/orchestrator.py", "backend/retrieval/rlm/executor.py"}
               for c in ("rlm_5", "rlm_10", "rlm_20")}}
    check("3 the Anthropic calls come from each strategy's own call sites (single pass, multi-hop, verified pass's "
          "answer, the RLM's root turns and sub-calls)", sites == want, json.dumps({k: sorted(v) for k, v in sites.items()}))
    check("3 every RLM answer made 1 root turn and 3 sub-calls through Anthropic",
          all(sum(1 for r in calls[c] if r.get("provider") == "anthropic" and r.get("item_id") == a["question_id"]
                  and r.get("run_draw") == a["draw"]) == 4 for c in ("rlm_5", "rlm_10", "rlm_20") for a in ans[c]))
    check("3 every posted body is the lock's: claude-haiku-4-5-20251001, temperature 1.0, max_tokens 64000, stream; "
          "no seed, top_p, top_k or thinking",
          posted and len(posted) == len(gen_recs)
          and all({k: b[k] for k in ("model", "temperature", "max_tokens", "stream")}
                  == {"model": "claude-haiku-4-5-20251001", "temperature": 1.0, "max_tokens": 64000, "stream": True}
                  and not {"seed", "top_p", "top_k", "thinking"} & set(b) for b in posted),
          f"{len(posted)} bodies, {len(gen_recs)} records")
    check("3 every Anthropic record carries the run's draw, role generator, options_sent without a seed, the lock's "
          "sha256", all(r["draw"] == r["run_draw"] and r["role"] == "generator" and r["model"] == "claude-haiku-4-5"
                        and r["options_sent"] == {"temperature": 1.0, "max_tokens": 64000}
                        and r["lock_sha256"] for r in gen_recs) and {r["draw"] for r in gen_recs} == {1, 2})
    check("3 the run contexts allowed Haiku and, in verified_pass only, the verifier",
          all(json.loads((r3 / f"exp_01__{c}__{I20}+claude-haiku-4-5.smoke" / "run_identity.json").read_text())
              ["agent_roles"] == en.config_models(c, HAIKU) for c in en.CONFIG_NAMES))

    # ═════════════════════════ 5. a local generator, through the real ollama_client ═════════════════════════
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from experiments.runner.lock import load as load_lock, LockError
    lock = load_lock()
    VER = lock.d["server"]["ollama_version"]

    def ollama_reply(body):
        """The fake model's text, from what the strategy sent (as reply_for in part 3, in Ollama's request shape)."""
        msgs = body.get("messages") or []
        system = " ".join(m.get("content") or "" for m in msgs if m.get("role") == "system")
        text = body.get("prompt") or "\n".join(m.get("content") or "" for m in msgs)
        if "repl" in system:
            return f"```repl\n{WORK}\n```"
        if "iterative document analysis" in system:
            return "FINAL ANSWER: 24 patients [a.pdf:1]."
        if "CITATIONS_USED" in text:
            return SUMMARY
        return "24 patients [a.pdf:1]."

    def fake_ollama(name, verifier=False):
        state = {"bodies": [], "paths": [], "digest": None, "version": VER}

        class H(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/api/version":
                    self._lines([{"version": state["version"]}])
                else:
                    self._lines([{"models": [{"name": t, "digest": state["digest"] or r["digest"]}
                                             for t, r in lock.d["models"].items()]}])

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                state["bodies"].append(body)
                state["paths"].append(self.path)
                text = ("[1] RELEVANT: states the sample size\n[2] NOT_RELEVANT: another paper" if verifier
                        else ollama_reply(body))
                done = {"done": True, "done_reason": "stop", "prompt_eval_count": 40, "eval_count": 12,
                        "load_duration": 1000, "prompt_eval_duration": 2000, "eval_duration": 3000,
                        "total_duration": 7000}
                if self.path == "/api/chat":
                    self._lines([{"message": {"role": "assistant", "content": text}, "done": False},
                                 {"message": {"role": "assistant", "content": ""}, **done}])
                else:
                    self._lines([{"response": text, "done": False}, {"response": "", **done}])

            def _lines(self, objs):
                self.send_response(200)
                self.send_header("Content-Type", "application/x-ndjson")
                self.end_headers()
                for o in objs:
                    self.wfile.write((json.dumps(o) + "\n").encode())

            def log_message(self, *a):
                pass
        srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        state["url"] = f"http://127.0.0.1:{srv.server_address[1]}"
        state["srv"] = srv
        return state

    gsrv, vsrv = fake_ollama("generator"), fake_ollama("verifier", verifier=True)
    r5 = tmp / "runs5"
    saved5 = (gc.generate, gc.chat, gc._open, ac._open, RLMContext.__dict__["from_index"])
    gc.generate = gc.chat = gc._open = tripwire
    ac._open = tripwire
    RLMContext.from_index = staticmethod(from_index)
    gemini_calls.clear()
    for n, v in {"find_admin_user_id": lambda: "u", "check_index_exists": lambda u, i: True,
                 "setup_retriever": lambda u, i: (FakeRetriever(), "coll", "emb"),
                 "index_identity": SimpleNamespace(record=lambda sink, *a, **k: None), "RUNS_ROOT": r5}.items():
        setattr(en, n, v)

    def local_run(gen, configs, draws, url=None):
        with contextlib.redirect_stdout(io.StringIO()):
            return raises(lambda: asyncio.run(en.run_experiment(configs=configs, base_url=vsrv["url"], index_name=I20,
                                                                max_questions=2, draws=draws, generator=gen,
                                                                generator_url=url or gsrv["url"])), BaseException)

    def sink_lines(gen, config, name):
        f = r5 / f"exp_01__{config}__{I20}{en.generator_tag(gen)}.smoke" / name
        return [json.loads(x) for x in f.read_text().splitlines()] if f.exists() else []

    def want_body(tag, draw):
        c = lock.ollama(tag, role="generator", draw=draw)
        return c.model, c.options, c.fields

    try:
        e = local_run(GEM3, en.CONFIG_NAMES, (1, 2))
        check("5 the gemma3:27b run on all six configs ends without an exception", e is None, repr(e))
        ans5 = {c: sink_lines(GEM3, c, en.ANSWERS) for c in en.CONFIG_NAMES}
        calls5 = {c: sink_lines(GEM3, c, "calls.jsonl") for c in en.CONFIG_NAMES}
        check("5 every config stored its 4 answers (2 questions x draws 1, 2) without an error, under gemma3:27b, in its "
              "own +gemma3-27b.smoke run",
              all(len(v) == 4 for v in ans5.values())
              and all(not r["generation"]["error"] and r["gen_model"] == GEM3 and r["generation"]["gen_model"] == GEM3
                      and r["models"] == en.config_models(c, GEM3) for c, v in ans5.items() for r in v),
              {c: [r["generation"]["error"] for r in v] for c, v in ans5.items()})
        check("5 the RLM answers end with stop_reason final",
              all(r["generation"]["stop_reason"] == "final" for c in ("rlm_5", "rlm_10", "rlm_20") for r in ans5[c]),
              {c: [r["generation"]["stop_reason"] for r in ans5[c]] for c in ("rlm_5", "rlm_10", "rlm_20")})
        recs = [r for v in calls5.values() for r in v]
        gen_recs5 = [r for r in recs if r.get("model") == "gemma3:27b"]
        ver_recs5 = [(c, r) for c, v in calls5.items() for r in v if r.get("model") != "gemma3:27b"]
        check("5 every call record is an Ollama call; no Gemini or Anthropic call was made",
              recs and all(r.get("provider") == "ollama" for r in recs) and not gemini_calls, str(gemini_calls[:2]))
        check("5 every generator call went to the generator server, and only the verifier's (gpt-oss:20b-date20261010 "
              "from chunk_verifier.py, verified_pass only) to the verifier server",
              all(r["server"] == gsrv["url"] for r in gen_recs5)
              and ver_recs5 and all(c == "verified_pass" and r["model"] == "gpt-oss:20b-date20261010"
                                    and r["server"] == vsrv["url"] and "chunk_verifier.py" in (r.get("call_site") or "")
                                    for c, r in ver_recs5)
              and len(ver_recs5) == 4 and len(vsrv["bodies"]) == 4
              and len(gsrv["bodies"]) == len(gen_recs5)
              and all(b["model"] == "gemma3:27b" for b in gsrv["bodies"])
              and all(b["model"] == "gpt-oss:20b-date20261010" for b in vsrv["bodies"]),
              f"{len(gen_recs5)} generator records, {len(gsrv['bodies'])} bodies; {len(ver_recs5)} verifier records")
        sites5 = {c: {(r.get("call_site") or "").split(":")[0] for r in v if r.get("model") == "gemma3:27b"}
                  for c, v in calls5.items()}
        check("5 the generator calls come from each strategy's own call sites (single pass, multi-hop, verified pass's "
              "answer, the RLM's root turns and sub-calls), as Haiku's in part 3", sites5 == want,
              json.dumps({k: sorted(v) for k, v in sites5.items()}))
        check("5 every RLM answer made 1 root turn and 3 sub-calls through gemma3:27b",
              all(sum(1 for r in calls5[c] if r.get("model") == "gemma3:27b" and r.get("item_id") == a["question_id"]
                      and r.get("run_draw") == a["draw"]) == 4 for c in ("rlm_5", "rlm_10", "rlm_20") for a in ans5[c]))
        ok_body = all((b["model"], b["options"], {k: b[k] for k in ("truncate", "shift", "keep_alive") if k in b},
                       "think" in b, b["stream"]) == (*want_body("gemma3:27b", b["options"]["seed"])[:2],
                                                      {"truncate": False, "shift": False, "keep_alive": "24h"},
                                                      False, True)
                      for b in gsrv["bodies"])
        g_row = lock.d["sampling"]["models"]["gemma3:27b"]
        check("5 every generator body is the lock's: gemma3:27b, its [sampling.models] row (temperature 1.0, top_p "
              "0.95, top_k 64, min_p 0, repeat_penalty 1, presence_penalty 0), num_ctx 131072, num_predict -1, "
              "num_batch 1024, seed the draw, truncate and shift false, keep_alive 24h, no think (the row's omit)",
              ok_body and {b["options"]["seed"] for b in gsrv["bodies"]} == {1, 2}
              and all(b["options"]["num_ctx"] == 131072 and b["options"]["num_predict"] == -1
                      and b["options"]["num_batch"] == 1024 and b["options"]["temperature"] == g_row["temperature"]
                      and b["options"]["top_k"] == 64 for b in gsrv["bodies"]),
              json.dumps(gsrv["bodies"][0]["options"]) if gsrv["bodies"] else "no body")
        check("5 each generator call's seed is its record's draw and run draw (no candidate, no retry)",
              all(r["options_sent"]["seed"] == r["draw"] == r["run_draw"] and r.get("candidate") is None
                  and r.get("retry") is None for r in gen_recs5))
        vb = lock.ollama("gpt-oss:20b", role="generator", draw=1)
        check("5 the verifier's bodies are the lock's gpt-oss:20b (date-fixed copy, think medium, its row), seed the draw",
              all(b["options"] == lock.ollama("gpt-oss:20b", role="generator", draw=b["options"]["seed"]).options
                  and b.get("think") == "medium" and b["model"] == vb.model for b in vsrv["bodies"]),
              json.dumps(vsrv["bodies"][0].get("options")) if vsrv["bodies"] else "no body")
        fields = lock.d["record"]["fields"]
        check("5 every call record carries every [record] field, the lock's sha256, the lock's digest and Ollama "
              "version, and status ok",
              all(all(f in r for f in fields) and r["lock_sha256"] == lock.sha256 and r["status"] == "ok"
                  and r["ollama_version"] == VER
                  and r["model_digest"] == lock.d["models"][r["model"]]["digest"] for r in recs),
              str([f for f in fields if recs and f not in recs[0]]))
        check("5 the run contexts allowed gemma3:27b and, in verified_pass only, the verifier",
              all(json.loads((r5 / f"exp_01__{c}__{I20}+gemma3-27b.smoke" / "run_identity.json").read_text())
                  ["agent_roles"] == en.config_models(c, GEM3) for c in en.CONFIG_NAMES))

        # other rows of the lock: qwen3-coder:30b, llama3:8b ([exceptions]) and gpt-oss:20b ([date] copy)
        for tag, why in (("qwen3-coder:30b", "its own row (temperature 0.7, top_p 0.8, top_k 20, repeat_penalty 1.05)"),
                         ("llama3:8b", "num_ctx 8192 from [exceptions]"),
                         ("gpt-oss:20b", "the [date] copy gpt-oss:20b-date20261010, think medium")):
            gsrv["bodies"].clear()
            e = local_run(f"ollama::{tag}", ["single_pass"], (1,))
            a = sink_lines(f"ollama::{tag}", "single_pass", en.ANSWERS)
            m, o, f = want_body(tag, 1)
            check(f"5 ollama::{tag} on single pass: answers stored, every body the lock's, {why}",
                  e is None and len(a) == 2 and not any(r["generation"]["error"] for r in a)
                  and len(gsrv["bodies"]) == 2
                  and all(b["model"] == m and b["options"] == o and {k: b.get(k) for k in f} == f
                          for b in gsrv["bodies"])
                  and (tag != "llama3:8b" or all(b["options"]["num_ctx"] == 8192 for b in gsrv["bodies"]))
                  and (tag != "gpt-oss:20b" or all(b["model"] == "gpt-oss:20b-date20261010" and b["think"] == "medium"
                                                   for b in gsrv["bodies"]))
                  and (tag != "qwen3-coder:30b" or all(b["options"]["repeat_penalty"] == 1.05 for b in gsrv["bodies"])),
                  f"{e!r} {len(a)} answers {json.dumps(gsrv['bodies'][:1])[:300]}")

        # a generator server holding another build, or another Ollama version, stops the run with nothing stored
        for what, key, value in (("another digest", "digest", "0" * 64), ("another Ollama version", "version", "0.1.0")):
            gsrv[key] = value
            gsrv["bodies"].clear()
            e = local_run(GEM3, ["multi_hop"], (3,))
            gsrv["digest"], gsrv["version"] = None, VER
            a = [r for r in sink_lines(GEM3, "multi_hop", en.ANSWERS) if r["draw"] == 3]
            check(f"5 a generator server with {what} stops the run (a lock refusal, Q38): nothing posted, nothing stored "
                  f"for draw 3", isinstance(e, LockError) and not gsrv["bodies"] and not a, repr(e))
    finally:
        (gc.generate, gc.chat, gc._open, ac._open) = saved5[:4]
        RLMContext.from_index = saved5[4]
        gsrv["srv"].shutdown()
        vsrv["srv"].shutdown()

    n_fail = sum(1 for _, ok in results if not ok)
    print(f"{len(results) - n_fail} of {len(results)} checks pass")
    return 1 if n_fail else 0


if __name__ == "__main__":
    target = os.environ.get("CHECK_E01_TARGET")
    if target:
        sys.exit(child_main(Path(target)))
    sys.exit(parent("--mutants" in sys.argv[1:]))
