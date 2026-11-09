"""B4 run: the authors' RLM (rlms 0.1.3) at one turn cap and one draw, every answer into the runner's sink.

    # Figure 2's reference bars (D73 Q45): caps 5, 10 and 20, all 135 questions, draws 1, 2 and 3
    uv run --project experiments/rlm_ref --frozen python -m experiments.rlm_ref.run_rlm_ref --cap 5 --draw 1

    # the depth sweep's other caps (1, 2, 3, 7, 15, 30, 50) on the depth sweep's 86 questions, draws 1, 2 and 3
    # (D75 Q50, D78 Q116)
    uv run --project experiments/rlm_ref --frozen python -m experiments.rlm_ref.run_rlm_ref --cap 7 --draw 1 \
        --question-set depth_sweep86

    # smoke: its own run (b4_rlm_ref__cap<cap>__smoke), any cap, never read by a paper run
    uv run --project experiments/rlm_ref --frozen python -m experiments.rlm_ref.run_rlm_ref --smoke --cap 1 --draw 1 --limit 1

    --questions ID,ID   only these questions of the set (in the key's order); --limit N   the first N of the selection
    --dry-run           print the work list and stop (no Docker, no model call, nothing written)
    --build-image       build the sandbox image from sandbox/ and print its id (a run never builds; it uses
                        adapter.IMAGE_ID, which is changed by hand)

Run from the repository root. Each cap is its own run (the cap is written into every turn's prompt, "Turn i/N"), so a
cap-5 answer is never read off a longer run: run_id b4_rlm_ref__cap<cap>__<set>, sink findings/runs/<run_id>/, which
holds calls.jsonl (one record per model call), answers.jsonl (one record per answer, keyed by
experiment.answer_key("cap<cap>", question_id, draw)), traces/, blobs/ and the run's identity. One attempt per answer
(Q29): an answer whose record is in answers.jsonl, failed or not, is done and is not run again; a fatal or setup error
(a key in a record, a lock refusal, Docker not starting) stops the run with nothing stored for that answer.

BEFORE THE FIRST QUESTION (adapter.py patches 6 and 7): the image must be adapter.IMAGE_ID (never built here); a
killed run's containers and workspaces are removed; no other process may listen on the proxy ports; the b4-sandbox
network and its firewall are set in colima's VM; and a probe from a sandbox container must find no laptop port, VM
service or private address reachable (a canary first). Any failure stops the run before a model call.

QUESTION SETS. all135: experiment.questions(), the 135 of answer key v2.4 (D48). depth_sweep86 (D75 Q50): the
submitted Gemini depth sweep's 88 questions less CD_015 and SY_010, which D48 dropped, in the key's order: DEPTH_SWEEP86
below, read from the deposit's DEPTH_SWEEP_DEPOSIT (sha256 DEPTH_SWEEP_DEPOSIT_SHA256; zenodo/ is not in git, so the
ids are written here and check_rlm_ref.py derives them again from the deposit when it is present). It is a named set,
not exp_06_depth_sweep.py's per-category rule (which gives 77 at n = 88), and the same set as Mentori's RLM depth
sweep (G5). Every id must be an answerable question of v2.4 in the five categories, 86 in all, or the run is refused;
--n-questions, if given, must be 86.

Guards (not with --smoke): all135 runs only caps 5, 10, 20 and Figure 2's draws (1, 2, 3); depth_sweep86 runs only the
caps 1, 2, 3, 7, 15, 30, 50 and Figure 3's draws (1, 2, 3), experiment.draws(3) (D49, D60, D73 Q45, D75 Q50, D78
Q116).

D239 ARM A (--generator gemma3:27b): the same package run with gemma3:27b as root and sub-call model through Ollama
(adapter.LockedOllama). Its own experiment, b4_rlm_ref_gemma3: run_id b4_rlm_ref_gemma3__cap<cap>__<name> (name from
the ids file; smoke: b4_rlm_ref_gemma3__cap<cap>__smoke), answer keys cap<cap>|<question>|d<draw> in that sink. It
needs --question-ids-file (JSON {"name": <run_id part>, "ids": [...]}, every id an answerable question of v2.4 in the
five categories, no repeat) and, unless --dry-run, the Ollama server in RLM_REF_OLLAMA_URL (environment only, so the
port is never on this command line); before the first question the server must run the lock's Ollama version and hold
gemma3:27b with the lock's digest. Guard (not with --smoke): cap 10 and draw 1 only (D239: turn cap 10, one draw;
D249 O2 revives it, G19, on the 46 questions of D239 amended). A Gemini run prints and does exactly what it did
before this option existed (findings/recompute/G19_runs/g19_gemini_identity.py holds it equal to the file before).

D260 (G20, --generator qwen3-coder:30b): the same arm with qwen3-coder:30b, its own experiment b4_rlm_ref_qwen3coder
(run_id b4_rlm_ref_qwen3coder__cap<cap>__<name>), the same guards, server check and digest check at that model's lock
row (findings/recompute/G20_runs/).

    RLM_REF_OLLAMA_URL=... uv run --project experiments/rlm_ref --frozen python -m experiments.rlm_ref.run_rlm_ref \\
        --generator gemma3:27b --cap 10 --draw 1 --question-ids-file findings/recompute/G19_runs/g19_questions.json
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.runner import experiment as ex  # noqa: E402
from experiments.runner import run_context as rc  # noqa: E402

EXPERIMENT = "b4_rlm_ref"
FIGURE2_CAPS = (5, 10, 20)                          # D73 Q45: all 135 questions, three draws
DEPTH_SWEEP_CAPS = (1, 2, 3, 7, 15, 30, 50)         # exp_06_depth_sweep.py:73 DEFAULT_DEPTHS less 5, 10, 20
CATEGORIES = ("factual_recall", "conceptual", "technical", "cross_document", "synthesis")   # exp_06:93-99
BASE_URL = "https://generativelanguage.googleapis.com"   # a run context names a server; Gemini calls never use it
GENERATOR_IDENTS = {"gemini-3-flash-preview": "gemini::gemini-3-flash-preview", "gemma3:27b": "ollama::gemma3:27b",
                    "qwen3-coder:30b": "ollama::qwen3-coder:30b"}
OLLAMA_EXPERIMENT = "b4_rlm_ref_gemma3"             # D239 arm A
OLLAMA_EXPERIMENTS = {"gemma3:27b": OLLAMA_EXPERIMENT,             # G19 (D249 O2)
                      "qwen3-coder:30b": "b4_rlm_ref_qwen3coder"}  # G20 (D260): the same arm on qwen3-coder:30b
D239_CAPS, D239_DRAWS = (10,), (1,)                 # D239: turn cap 10, draw 1 ("a proof of concept")
OLLAMA_URL_ENV = "RLM_REF_OLLAMA_URL"


# D75 Q50: the submitted Gemini depth sweep's question ids (DEPTH_SWEEP_DEPOSIT, results[].question_id, 88 ids) less
# DEPTH_SWEEP_DROPPED, which answer key v2.4 no longer holds (D48); in the key's order, which is also the deposit's
DEPTH_SWEEP_DEPOSIT = "zenodo/10_data/upstream/publication/results/exp09_depth_sweep_gemini-3-flash-preview_merged.json"
DEPTH_SWEEP_DEPOSIT_SHA256 = "e63242b7943c0121fde86e5af86c8bf36656ce474e1f70150ba555d6df07ae91"
DEPTH_SWEEP_DROPPED = ("CD_015", "SY_010")
DEPTH_SWEEP_SIZE = 86
DEPTH_SWEEP86 = (
    *(f"{p}_{t}" for p in ("01_sarek", "02_snakemake", "03_nfcore_framework", "04_fastp", "05_multiqc",
                           "06_star_aligner", "07_salmon", "08_deseq2", "09_seqkit", "10_cutadapt",
                           "11_asf_burkina_faso", "12_hpai_netherlands", "13_lsd_nepal", "14_bovine_tb_cameroon",
                           "15_rabies_tanzania", "16_ppr_ethiopia", "17_brucellosis_ethiopia", "18_fmd_review",
                           "19_hpai_canada", "20_lsd_review") for t in ("CO2", "FR1", "TE3")),
    *(f"CD_{i:03d}" for i in range(1, 19) if i != 15),
    *(f"SY_{i:03d}" for i in range(1, 10)),
)


def depth_sweep86_questions() -> list[dict]:
    """The questions of DEPTH_SWEEP86 from experiment.questions(), in the key's order; refused unless all 86 are
    answerable questions of v2.4 in the five categories."""
    want = set(DEPTH_SWEEP86)
    qs = [q for q in ex.questions() if q["id"] in want]
    found = {q["id"] for q in qs}
    bad = ([f"{i}: not in answer key v2.4" for i in DEPTH_SWEEP86 if i not in found]
           + [f"{q['id']}: not answerable" for q in qs if not q["answerable"]]
           + [f"{q['id']}: category {q.get('category')}" for q in qs if q.get("category") not in CATEGORIES])
    if len(DEPTH_SWEEP86) != len(want) or len(qs) != DEPTH_SWEEP_SIZE or bad:
        raise SystemExit(f"depth_sweep86 is {len(qs)} questions ({len(DEPTH_SWEEP86)} ids, {len(want)} distinct), "
                         f"not {DEPTH_SWEEP_SIZE} answerable questions of v2.4 in {CATEGORIES} (D75 Q50): {bad}")
    return qs


def ids_file_questions(path: Path) -> tuple[str, list[dict]]:
    """(name, questions) of a question-ids file (D239 arm A), in the key's order; refused unless the name is a run_id
    part and every id is a distinct answerable question of v2.4 in the five categories."""
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise SystemExit(f"--question-ids-file {path}: {e}") from None
    name, ids = (doc.get("name"), doc.get("ids")) if isinstance(doc, dict) else (None, None)
    if not isinstance(name, str) or not name:          # run_id() leaves a None extra out: the run would lose its name
        raise SystemExit(f"--question-ids-file {path}: no name (the run_id's last part)")
    try:
        ex.run_id(OLLAMA_EXPERIMENT, "cap10", name)
    except ex.ExperimentError as e:
        raise SystemExit(f"--question-ids-file {path}: name: {e}") from None
    if not isinstance(ids, list) or not ids or not all(isinstance(i, str) for i in ids) or len(set(ids)) != len(ids):
        raise SystemExit(f"--question-ids-file {path}: ids is not a non-empty list of distinct question ids")
    by = {q["id"]: q for q in ex.questions()}
    bad = ([f"{i}: not in answer key v2.4" for i in ids if i not in by]
           + [f"{i}: not answerable" for i in ids if i in by and not by[i]["answerable"]]
           + [f"{i}: category {by[i].get('category')}" for i in ids if i in by and by[i].get("category") not in CATEGORIES])
    if bad:
        raise SystemExit(f"--question-ids-file {path}: {bad}")
    want = set(ids)
    return name, [q for q in ex.questions() if q["id"] in want]


def select(args) -> tuple[str, list[dict]]:
    if args.question_ids_file is not None:
        if args.n_questions is not None or args.question_set != "all135":
            raise SystemExit("--question-ids-file names the set; --question-set and --n-questions do not apply")
        name, qs = ids_file_questions(args.question_ids_file)
    elif args.question_set == "all135":
        if args.n_questions is not None:
            raise SystemExit("--n-questions applies only to --question-set depth_sweep86")
        name, qs = "all135", ex.questions()
    else:
        if args.n_questions is not None and args.n_questions != DEPTH_SWEEP_SIZE:
            raise SystemExit(f"--n-questions {args.n_questions}: the depth sweep is the named set of "
                             f"{DEPTH_SWEEP_SIZE} questions (D75 Q50); no other count runs at the depth caps")
        name, qs = f"depthsweep{DEPTH_SWEEP_SIZE}", depth_sweep86_questions()
    if args.questions:
        want = [w.strip() for w in args.questions.split(",") if w.strip()]
        missing = [w for w in want if w not in {q["id"] for q in qs}]
        if missing:
            raise SystemExit(f"not in the {name} set: {missing}")
        qs = [q for q in qs if q["id"] in want]
    if args.limit is not None:
        if args.limit < 1:
            raise SystemExit(f"--limit {args.limit}: a limit is a number of questions from 1")
        qs = qs[:args.limit]
    return name, qs


def guard(args, set_name: str) -> None:
    if args.generator in OLLAMA_EXPERIMENTS:
        if args.question_ids_file is None:
            raise SystemExit(f"--generator {args.generator} runs the questions of --question-ids-file only (D239)")
        if not args.smoke and (args.cap not in D239_CAPS or args.draw not in D239_DRAWS):
            raise SystemExit(f"D239 arm A runs cap {D239_CAPS[0]} and draw {D239_DRAWS[0]} only (one draw, a proof of "
                             f"concept); use --smoke for anything else")
        return
    if args.question_ids_file is not None:
        raise SystemExit("--question-ids-file is D239 arm A's (--generator gemma3:27b); Figure 2 and 3's runs use "
                         "their named sets")
    if args.smoke:
        return
    if args.question_set == "all135":
        if args.cap not in FIGURE2_CAPS or args.draw not in ex.draws(2):
            raise SystemExit(f"all135 runs caps {FIGURE2_CAPS} with Figure 2's draws {ex.draws(2)} (D73 Q45, D49); "
                             f"use --question-set depth_sweep86 or --smoke")
    elif args.cap not in DEPTH_SWEEP_CAPS or args.draw not in ex.draws(3):
        raise SystemExit(f"{set_name} runs caps {DEPTH_SWEEP_CAPS} with Figure 3's draws {ex.draws(3)} (D78 Q116); "
                         f"caps 5, 10 and 20 come from the all135 runs (D73 Q45)")


def done_keys(sink: Path) -> set:
    path = sink / "answers.jsonl"
    if not path.exists():
        return set()
    return {json.loads(line)["answer_key"] for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="B4: the authors' RLM at one turn cap and one draw")
    ap.add_argument("--cap", type=int, help="max_iterations, the turn cap")
    ap.add_argument("--draw", type=int, help="the draw (the seed), 1 to 3")
    ap.add_argument("--question-set", choices=("all135", "depth_sweep86"), default="all135")
    ap.add_argument("--n-questions", type=int, default=None,
                    help=f"optional; with depth_sweep86 it must be {DEPTH_SWEEP_SIZE} (D75 Q50)")
    ap.add_argument("--questions", default=None, help="comma-separated question ids, a subset of the set")
    ap.add_argument("--generator", choices=tuple(GENERATOR_IDENTS), default="gemini-3-flash-preview",
                    help="the root and sub-call model; gemma3:27b is D239 arm A (Ollama, RLM_REF_OLLAMA_URL)")
    ap.add_argument("--question-ids-file", type=Path, default=None,
                    help='D239 arm A: JSON {"name": ..., "ids": [...]}, the set the run answers')
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--build-image", action="store_true",
                    help="build the sandbox image from sandbox/, print its id and stop (a run never builds one)")
    ap.add_argument("--runs-root", type=Path, default=ex.RUNS, help=argparse.SUPPRESS)   # check_rlm_ref only
    args = ap.parse_args(argv)
    if args.build_image:
        from experiments.rlm_ref import adapter as ad
        new = ad.build_image()
        print(f"built {ad.IMAGE_TAG} = {new}" + ("" if new == ad.IMAGE_ID else
                                                 "; this is not adapter.IMAGE_ID: a run uses IMAGE_ID until it is "
                                                 "changed by hand"))
        return 0
    if args.cap is None or args.draw is None:
        ap.error("--cap and --draw are required")
    set_name, qs = select(args)
    guard(args, set_name)
    ollama = args.generator in OLLAMA_EXPERIMENTS
    generator = GENERATOR_IDENTS[args.generator]
    experiment = OLLAMA_EXPERIMENTS[args.generator] if ollama else EXPERIMENT
    arm = f"cap{args.cap}"
    rid = ex.run_id(experiment, arm, "smoke" if args.smoke else set_name)
    path = (args.runs_root / rid).resolve()
    done = done_keys(path)
    work = [(q, ex.answer_key(arm, q["id"], args.draw)) for q in qs]
    todo = [(q, k) for q, k in work if k not in done]
    # a Gemini run prints the line it printed before the Ollama path existed (G19: Gemini behaviour unchanged)
    print(f"{rid}: {len(work)} answers at cap {args.cap}, draw {args.draw}"
          + (f", generator {generator}" if ollama else "")
          + f"; {len(work) - len(todo)} done, {len(todo)} to run")
    if args.dry_run:
        for _q, k in work:
            print(f"  {'done' if k in done else 'todo'}  {k}")
        if ollama:
            from experiments.runner.lock import MAX_RETRIES, load
            lk = load()
            c = lk.ollama(args.generator, draw=args.draw)
            print(f"  every call sends {c.model} (digest {c.digest[:12]}), options {c.options}, fields {c.fields}; "
                  f"retries {', '.join(str(lk.ollama(args.generator, draw=args.draw, retry=r).options['seed']) for r in range(1, MAX_RETRIES + 1))}"
                  f" (lock {lk.sha256[:8]})")
        return 0
    if not todo:
        return 0
    base_url = BASE_URL
    if ollama:
        base_url = os.environ.get(OLLAMA_URL_ENV, "").rstrip("/")
        if not base_url.startswith(("http://", "https://")):
            raise SystemExit(f"{OLLAMA_URL_ENV} names no Ollama server (an http URL); the port is set there, never "
                             f"on this command line")
    from experiments.rlm_ref import adapter as ad          # imports the package and applies the patches
    if ollama:
        from experiments.runner import ollama_client
        from experiments.runner.lock import load
        lk = load()
        version, digest = ollama_client.server_state(base_url, lk.ollama(args.generator, draw=args.draw).model)
        if version != lk.d["server"]["ollama_version"]:
            raise SystemExit(f"the server runs Ollama {version}, the lock names {lk.d['server']['ollama_version']}")
        lk.check_digest(args.generator, digest or "")
    if subprocess.run(["docker", "info"], capture_output=True).returncode != 0:
        raise SystemExit("Docker is not running (on the laptop: colima start)")
    sink = ex.sink(rid, root=args.runs_root)
    bundle = ad.load_context()
    image = ad.ensure_image()                               # IMAGE_ID or a refusal; never builds
    stale = ad.clean_stale(sink)
    ad.check_proxy_ports()
    image["network"] = ad.ensure_network(image["image_id"])
    probe = ad.probe_network(image["image_id"])
    if probe["open"]:
        raise SystemExit(f"the sandbox reaches {probe['open']}; patch 6's firewall is not holding, nothing was run")
    new = ad.add_sandbox_forms(bundle, image)
    print(f"context {bundle['context_sha256'][:12]} ({bundle['file']}); image {image['image_id'][:19]}; "
          f"{new} sandbox repr forms differ from the host's; network {ad.NETWORK}: {probe['targets']} host and "
          f"private targets refused; stale removed: {len(stale['containers_removed'])} containers, "
          f"{len(stale['workspaces_removed'])} workspaces")
    for i, (q, key) in enumerate(todo, 1):
        ctx = ex.context(experiment, arm, q["id"], args.draw, {"rlm_ref": generator}, base_url=base_url, run=rid,
                         sink=sink, judge=False)
        with rc.run(ctx):
            rec = ad.run_question(ctx, q, args.cap, bundle, image, set_name if not args.smoke else "smoke", arm, key,
                                  generator=generator)
        t = rec["tokens"]["total"]
        print(f"[{i}/{len(todo)}] {key}: {rec['stop_reason']}, {rec['turns_used']} turns, {rec['calls']['sub']} "
              f"sub-calls ({rec['calls']['sub_failed']} failed), {t['prompt_tokens']:,} in / {t['output_tokens']:,} "
              f"out / {t['thinking_tokens']:,} thinking tokens, {rec['wall_s']:.0f} s"
              + (f"; error: {rec['error'][:200]}" if rec["error"] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
