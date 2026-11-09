"""T1 (D97; plan row T1; Figure 3b and 3c): the depth sweep of the local models, exp_06 with --generator
ollama::<tag> on the 15 per-category questions, at assignment.toml's caps, draw 1 (draws 2 and 3 allowed, open
question Q5), under the lock. Since D118 (Valerio, 22 October evening) every model runs on the Studio's port 11454,
one model loaded at a time, interleaved: question by question in assignment.toml's written order, within a question
cap by cap, every model at a cap before the next cap (interleave_t1.py walks it; `order` prints it and `interleaved`
checks it). The checks and records around each start. Reads only, except `smoke` (writes the model's
smoke_check.json), `record` (writes the one --out file) and `faults` (--mark writes the offsets file; a fault found
writes --marker and touches --stop). Each mode ends with one line "COUNTS: ..." (counts only, for the public ntfy
topic) and exits 1 when a check fails (`faults`: 4 on a machine fault). No model call, no server contacted.

    uv run --frozen python findings/recompute/T1_runs/check_t1.py plan [--machine studio|laptop|beelink]
    uv run --frozen python findings/recompute/T1_runs/check_t1.py admit --model <m> --machine <x> --port <p>
    uv run --frozen python findings/recompute/T1_runs/check_t1.py queue --machine <x> [--queue <i>] --draws 1 [2 3]
    uv run --frozen python findings/recompute/T1_runs/check_t1.py progress --model <m> [--smoke]
    uv run --frozen python findings/recompute/T1_runs/check_t1.py complete --model <m> --draws 1 [2 3]
    uv run --frozen python findings/recompute/T1_runs/check_t1.py smoke --model <m> [--launch <rec>] [--out <file>]
    uv run --frozen python findings/recompute/T1_runs/check_t1.py record --out <file> --kind smoke|run --models <m> ...
        --machine <x> --base <url> [--queue <i>] [--draws ...]
    uv run --frozen python findings/recompute/T1_runs/check_t1.py faults --model <m> [--smoke] --mark <offsets.json>
    uv run --frozen python findings/recompute/T1_runs/check_t1.py faults --model <m> [--smoke] --since <offsets.json>
        [--follow --stop <file> --marker <file> [--poll <s>]]
    uv run --frozen python findings/recompute/T1_runs/check_t1.py order [--draw 1] [--first <n>]
    uv run --frozen python findings/recompute/T1_runs/check_t1.py interleaved [--draw 1] [--walk-log <file>]

The models. Figure 3b of the submission (manuscript/manuscript_CAI.md:1106-1111, panel b) drew eight open-weight models:
devstral-small-2:24b, gemma3:27b, glm-4.7-flash, qwen3-coder:30b (run as qwen3-coder:latest, the same model, D83
Q166), qwen3-coder-next:80b (q4_K_M), llama3:8b, gpt-oss:20b and nemotron-3-nano:30b; S426's records hold all eight,
15 questions each (findings/recompute/S426_depth_records_v24.csv). T1 runs seven: nemotron-3-nano:30b left every
experiment of the revision (D116), its April depth curve Figure 3b and 3c as well (D117). Each runs here as the lock
names it: glm at bf16
(D64, every experiment), gpt-oss through its date-fixed copy (D55, [date]), llama3:8b at 8,192 tokens of context
([exceptions], D23: out of the main comparison). assignment.toml puts each on one machine (since D118 all on the Studio, port 11454); plan checks that the lock
lists that machine for the tag that runs and runs the model as a generator (Lock.ollama, the maker's default
thinking, D66). HELD names the models admit refuses until a decided step is done (review F1, F8): glm-4.7-flash until
the lock holds its general-task row and the code sends it (D83 Q181), llama3:8b until its one test call (D83 Q167).
A hold is lifted by a commit that removes its line, with the evidence named in that commit. The interleaved walk skips
a held model's cells and records each skip in its walk log; once the hold is lifted, the next walk runs that model's
cells from the first in the same order (it catches up) before any other model moves past it.

The interleaved order (D118). assignment.toml writes, before any answer, the question order (the 15, alternating the
five categories so every prefix holds each category's count within one of the others'), the caps (ascending) and the
model order. A cell is (question, cap, model) at a draw; cells run question by question, then cap by cap, then model
by model. `interleaved` checks the stored answers against that order: (1) each model's stored cells are a prefix of
its cells (no cell stored after a missing one); (2) below the furthest stored cell, every missing cell has a "held"
record in the walk log (its model was held when the walk passed it), so a model not held is never more than the one
cell in flight behind another; (3) every stored cell has a "begin" record of the walk (nothing stored outside it);
(4) within each pass of the walk, its records go strictly forward in the order; (5) no stored cell is void: its answer
was stored on a fresh load that did not pass both checks (the walk's "void" record, review F2), unless a later "end"
record has the cell answered again (exit 0, stored, its load passed) after the void answer was moved aside.

The questions: exp_06's per_category rule (the first 3 answerable questions of each of the five categories, in the
key's order), which on answer key v2.4 gives exactly the submitted local sweep's 15 (D75 Q50: "T1 keeps the
submitted 15"); questions() refuses any other set. The smoke: exp_06's --smoke pick (the first two answerable of the
135) at the caps assignment.toml names, draw 1.

Names (exp_06 with the D97 change): run exp_06_depth_sweep__rlm_<cap>__percategory15+<slug>, smoke
...__smoke+<slug>; results files results_v4/v4_9_depth_sweep_percategory15+<slug>_<model_short>_<server>_<time>.json
(smoke: v4_9_depth_sweep_smoke+<slug>_...), the slug the tag with ':' and '/' as '-', model_short exp_06's (the tag
with ':' and '/' as '_'). The answers are the union of the files by answer key, as exp_06's resume reads them.

progress: per draw and cap, answers stored and with an error, and the errors by kind: the RLM's own ends
(max_turns_empty: no answer by the cap), a failed root call (call_error) and, among those, the ones whose failed call
never reached the server or timed out on the way (a machine fault, not the model's: counted apart for a decision, as
the Beelink's WSL-to-Windows timeouts of 18 October; exp_06 stores every failed answer and never runs it again, Q29).
smoke: passes when the end record reads exit 0; the smoke files hold exactly the 6 expected keys, not every one with
an error, and every answer without an error has the RLM's record and a stop reason; every call of the three smoke
sinks carries the launch's lock sha256, went to the launch's server, ran the tag the lock names with the lock's
digest, sent the options and fields the lock builds for its draw (seed = the draw) at the generator's thinking rule
(D66: the maker's default, whatever thinking the call's record names; review F7), and no call failed before its
request was posted; every answer has calls of its own; each sink's index_identity.jsonl names exp_v4_s20_n0 with its
778 chunks.
faults (review F6): a call of the model's sinks that never reached the server (NOT_REACHED: status error and the
lock adapter's "before the request was posted", a timeout or a refused or reset connection) is a machine fault, not
the model's. --mark records each sink's calls.jsonl size before exp_06 starts; --since reads only what was written
after; --follow keeps reading (every --poll seconds) until killed, and on the first fault writes --marker (JSON: the
sink, seq and error) and touches --stop, so exp_06 stops before its next answer (run_t1.sh then ends with exit 4 and
the queue stops). The RLM ends an answer on a failed root call and exp_06 stores it and never runs it again (Q29), so
without this stop a dead server would turn every remaining answer of the draw into a stored failure in minutes.
"""

import argparse
import collections
import hashlib
import json
import os
import re
import socket
import statistics
import subprocess
import sys
import time
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from experiments.runner import experiment as ex                        # noqa: E402
from experiments.runner import lock as lockmod                         # noqa: E402

D = Path(__file__).resolve().parent
ASSIGNMENT = D / "assignment.toml"
RESULTS = ROOT / "experiments" / "mentori" / "publication" / "scripts" / "results_v4"
RUNS = ROOT / "findings" / "runs"
LOCK = ROOT / "experiments" / "LOCK.toml"
EXPERIMENT = "exp_06_depth_sweep"
DEPTHS = (1, 2, 3, 5, 7, 10, 15, 20, 30, 50)            # exp_06 DEFAULT_DEPTHS
DRAWS = ex.draws(3)                                     # (1, 2, 3) allowed: Figure 3 (D78 Q116 names G4, G5 and the
                                                        # authors' caps, not T1; D49 gave Figure 3 one draw): draw 1 is
                                                        # planned, draws 2 and 3 wait for Valerio (README Q5)
SET_TAG = "percategory15"                               # exp_06 set_tag("per_category", 15)
INDEX, INDEX_CHUNKS = "exp_v4_s20_n0", 778
MACHINES = ("studio", "laptop", "beelink")
LOCAL = "ollama::"
# Figure 3b's eight (manuscript_CAI.md:1109-1111 names them; S426 records), as the lock names them now
# D116 (Valerio, 22 October): nemotron-3-nano:30b leaves every experiment of the revision, so T1 runs seven of the eight;
# D117: its April depth curve leaves Figure 3b and 3c as well
T1_MODELS = ("devstral-small-2:24b", "gemma3:27b", "glm-4.7-flash:bf16", "qwen3-coder:30b", "qwen3-coder-next:q4_K_M",
             "llama3:8b", "gpt-oss:20b")
# The submitted local sweep: its 15 questions (findings/recompute/S437_depth_regen_plan.md "Questions"; the same 15 in
# every one of the eight files, S426_depth_records_v24.csv) and each model's caps in S426's records (nemotron's left with
# it, D117)
APRIL_15 = ("01_sarek_FR1", "01_sarek_CO2", "01_sarek_TE3", "02_snakemake_FR1", "02_snakemake_CO2", "02_snakemake_TE3",
            "03_nfcore_framework_FR1", "03_nfcore_framework_CO2", "03_nfcore_framework_TE3", "CD_001", "CD_002",
            "CD_003", "SY_001", "SY_002", "SY_003")
APRIL_CAPS = {"devstral-small-2:24b": (1, 3, 7, 15, 30), "gemma3:27b": (1, 3, 7, 15, 30),
              "glm-4.7-flash:bf16": (1, 3, 7, 15, 30), "llama3:8b": (1, 3, 7, 15, 30),
              "gpt-oss:20b": (2, 3, 5, 7, 10, 15, 20, 30, 50),
              "qwen3-coder-next:q4_K_M": (2, 3, 5, 7, 10, 15, 20, 30, 50),
              "qwen3-coder:30b": (1, 2, 3, 5, 7, 10, 15, 20, 30, 50)}
# Ports a T1 server never is: 11434 on the Studio is the Mentori app's (never touched); 11441 K1's Studio worker;
# 11453 and 11456 Figure 3's verifier ports (G1, G4); 11455 S3's judge. The laptop and the Beelink run one paper
# server each, the app's on 11434, and T1 uses only that one.
# D108 O11, D112 Q10, D116 (22 October): 11451 runs a K1 worker and 11452 S18f, then a K1 worker (D115 PQ2);
# 11460 to 11463 and 11470 are Valerio's own servers (Q19 of 21 October). T1's Studio port is 11454 (D112 Q10 O-b).
STUDIO_RESERVED = (11434, 11441, 11451, 11452, 11453, 11455, 11456, 11460, 11461, 11462, 11463, 11470)
# Held: admit refuses these until the decided step named is done (module docstring; README "Held models")
HELD = {
    "glm-4.7-flash:bf16": "D83 Q181: when glm answers questions it takes a general-task row from Z.ai's page, read on "
                          "the day, before launch; the lock holds only its coding row ([sampling.thinking_on], "
                          "temperature 0.7, top_p 1.0) and no code sends another (README A1)",
    "llama3:8b": "D83 Q167: one llama3:8b test call on a free Studio server first (it never answered under the lock, "
                 "plan.csv C5); kept at 8,192 if it answers, its machine decided then (README A2)",
    "gpt-oss:20b": "D121 (Valerio, 23 Oct, Q2 O-a): out of T1. Its smoke (23 Oct 09:44, 83fe603) stored 6 of 6 answers "
                   "with an error: 4 root calls ended on a tool call Ollama could not parse ('error parsing tool "
                   "call'), 2 reached the one-turn cap with no code block; the paper states it was tested and none "
                   "of its tool calls could be parsed and used automatically",
}
CATEGORIES = ("factual_recall", "conceptual", "technical", "cross_document", "synthesis")   # exp_06's, in its order
WALK_LOG = D / "interleaved_walk.jsonl"                 # interleave_t1.py's records, one JSON line each
NOT_REACHED = re.compile(r"before the request was posted|timed out|Errno 110|Connection refused|Connection reset")


def fail(msg: str) -> None:
    print(f"CHECK FAILED: {msg}")
    sys.exit(1)


def slug(model: str) -> str:
    """exp_06 generator_tag without its '+': the tag with ':' and '/' as '-' (gemma3:27b -> gemma3-27b)."""
    return re.sub(r"[:/]", "-", model)


def model_short(model: str) -> str:
    """exp_06's model_short of ollama::<model>: the tag with ':' and '/' as '_'."""
    return model.replace(":", "_").replace("/", "_")


def tag(model: str, smoke: bool = False) -> str:
    return f"{'smoke' if smoke else SET_TAG}+{slug(model)}"


def run_name(model: str, depth: int, smoke: bool = False) -> str:
    return ex.run_id(EXPERIMENT, f"rlm_{depth}", tag(model, smoke))


def prefix(model: str, smoke: bool = False) -> str:
    return f"v4_9_depth_sweep_{tag(model, smoke)}_{model_short(model)}"


def load_lock(path: Path = LOCK):
    return lockmod.load(path)


def load_assignment(path: Path = ASSIGNMENT, lk=None) -> dict:
    """assignment.toml, checked: every model of T1_MODELS on exactly one machine; each machine one the lock lists for
    the tag that runs ([models] machines); the lock runs each model as a generator; the Studio's queues hold its models
    once each and its port, when named, is not a reserved one; depths (the caps, D118) and smoke_depths are each a
    subset of exp_06's ten, in order (the smoke's caps need not be among the depths: the smoke does not wait for the
    caps to be agreed); depths_status is "proposed" or "agreed"; question_order is the 15 once each, every prefix
    balanced over the five categories (D118). The interleaved walk's model order is the one machine's models list, in
    its order (model_order; None when the models are on more than one machine)."""
    lk = lk or load_lock()
    a = tomllib.loads(Path(path).read_text())
    where = collections.defaultdict(list)
    for m, spec in a.get("machine", {}).items():
        if m not in MACHINES:
            raise SystemExit(f"assignment: machine {m!r} is not one of {MACHINES}")
        for model in spec.get("models", []):
            where[model].append(m)
        if m != "studio" and spec.get("port") != 11434:
            raise SystemExit(f"assignment: {m} runs one paper server, on 11434, not {spec.get('port')!r}")
        if m == "studio" and "port" in spec and (not isinstance(spec["port"], int) or spec["port"] in STUDIO_RESERVED):
            raise SystemExit(f"assignment: the Studio's T1 port {spec['port']!r} is reserved ({STUDIO_RESERVED}) or no port")
        if "queues" in spec:
            flat = [x for q in spec["queues"] for x in q]
            if sorted(flat) != sorted(spec.get("models", [])) or len(set(flat)) != len(flat):
                raise SystemExit(f"assignment: {m}'s queues {spec['queues']} do not hold its models once each")
    missing = [x for x in T1_MODELS if x not in where]
    twice = {x: w for x, w in where.items() if len(w) > 1}
    extra = [x for x in where if x not in T1_MODELS]
    if missing or twice or extra:
        raise SystemExit(f"assignment: models missing {missing}, on two machines {twice}, not Figure 3b's {extra}")
    for model, (m,) in where.items():
        try:
            lk.ollama(model, role="generator", draw=1)
        except lockmod.LockError as e:
            raise SystemExit(f"assignment: the lock does not run {model} as a generator ({e})")
        run, _ = lk._run_tag(model)
        held = lk.d.get("models", {}).get(run, {}).get("machines", [])
        if m not in held:
            raise SystemExit(f"assignment: {model} runs as {run}, which the lock's [models] lists on {held}, not {m}")
    depths = tuple(a.get("depths", ()))
    smoke = tuple(a.get("smoke_depths", ()))
    if not depths or list(depths) != [d for d in DEPTHS if d in depths]:
        raise SystemExit(f"assignment: depths {depths} are not exp_06's caps {DEPTHS} (a subset, in order)")
    if not smoke or list(smoke) != [d for d in DEPTHS if d in smoke]:
        raise SystemExit(f"assignment: smoke_depths {smoke} are not exp_06's caps {DEPTHS} (a subset, in order)")
    if a.get("depths_status") not in ("proposed", "agreed"):
        raise SystemExit(f"assignment: depths_status {a.get('depths_status')!r}, not \"proposed\" or \"agreed\" (D118)")
    if a.get("set") != "per_category":
        raise SystemExit(f"assignment: set {a.get('set')!r}, T1 runs per_category (D75 Q50)")
    order = tuple(a.get("question_order", ()))
    if sorted(order) != sorted(questions()) or len(set(order)) != len(order):
        raise SystemExit(f"assignment: question_order {list(order)} is not T1's 15 questions once each (D118)")
    cat = {q["id"]: q["category"] for q in ex.questions()}
    for n in range(1, len(order) + 1):
        c = collections.Counter(cat[x] for x in order[:n])
        if max(c[k] for k in CATEGORIES) - min(c[k] for k in CATEGORIES) > 1:
            raise SystemExit(f"assignment: question_order's first {n} questions are not balanced over the five "
                             f"categories ({dict(c)}; D118: any prefix balanced)")
    machines = a.get("machine", {})
    model_order = tuple(next(iter(machines.values()))["models"]) if len(machines) == 1 else None
    return {"machine_of": {x: w[0] for x, w in where.items()}, "depths": depths, "smoke_depths": smoke,
            "status": a.get("status"), "depths_status": a.get("depths_status"), "machines": machines,
            "question_order": order, "model_order": model_order,
            "port_of": {m: spec.get("port") for m, spec in machines.items()}}


def questions(smoke: bool = False) -> list:
    """exp_06's questions for T1: per_category at 15 (exp_06 select_questions: answerable, by category in the key's
    order, those with min_core <= 20 first, the first 3 of each), refused unless it is the submitted 15; the smoke's
    two, the first two answerable questions of the 135 (exp_06's --smoke pick), refused unless among the 15."""
    ans = [q for q in ex.questions() if q["answerable"]]
    if smoke:
        ids = [q["id"] for q in ans[:2]]
        if not set(ids) <= set(APRIL_15):
            raise SystemExit(f"exp_06's smoke questions {ids} are not among T1's 15: stop and look")
        return ids
    out = []
    for cat in ("factual_recall", "conceptual", "technical", "cross_document", "synthesis"):
        pool = [q for q in ans if q["category"] == cat]
        eligible = [q for q in pool if q.get("min_core", 999) <= 20] or pool
        out += [q["id"] for q in eligible[:3]]
    if sorted(out) != sorted(APRIL_15):
        raise SystemExit(f"per_category gives {out}, not the submitted 15 {list(APRIL_15)} (D75 Q50): stop and look")
    return out


def expected(model: str, smoke: bool, depths, draws=DRAWS) -> dict:
    """answer key -> (depth, question, draw), in exp_06's order (draw, question, depth)."""
    return {ex.answer_key(f"rlm_{d}", q, dr): (d, q, dr) for dr in draws for q in questions(smoke) for d in depths}


def answers(model: str, smoke: bool, results: Path = None) -> tuple:
    """(rows by key, problems): the union of the model's results files, as exp_06's resume reads them."""
    rows, problems = {}, []
    for f in sorted(Path(results or RESULTS).glob(f"{prefix(model, smoke)}*.json")):
        if f.name.endswith("_merged.json"):
            continue
        try:
            data = json.loads(f.read_text())
        except ValueError as e:
            problems.append(f"{f.name} is not JSON ({e})")
            continue
        for r in data.get("results", []):
            k = r.get("answer_key")
            if k is None:
                problems.append(f"{f.name}: a row without an answer_key")
            elif k in rows and rows[k] != r:
                problems.append(f"{k}: two different rows ({f.name})")
            else:
                rows[k] = r
    return rows, problems


def error_kind(r: dict) -> str:
    """'' (no error), 'machine' (a failed root call that never reached the server or timed out on the way),
    'call_error', 'max_turns_empty' or 'other' (exp_06's error string starts with the stop reason)."""
    err = r.get("error") or ""
    if not err:
        return ""
    ce = ((r.get("rlm") or {}).get("call_error") or {})
    if err.startswith("call_error") and NOT_REACHED.search(f"{ce.get('error') or ''} {err}"):
        return "machine"
    for k in ("call_error", "max_turns_empty"):
        if err.startswith(k):
            return k
    return "other"


def read_jsonl(path: Path) -> list:
    return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()] if Path(path).exists() else []


def model_arg(m: str) -> str:
    m = m[len(LOCAL):] if m.startswith(LOCAL) else m
    if m not in T1_MODELS:
        raise SystemExit(f"--model {m!r} is not one of T1's seven {T1_MODELS} (D116: nemotron-3-nano:30b left)")
    return m


# ---- modes

def plan(a) -> None:
    lk = load_lock()
    asg = load_assignment(lk=lk)
    qs = questions()
    n = len(qs) * len(asg["depths"])
    print(f"lock {lk.sha256[:8]}; assignment {asg['status']}; {len(qs)} questions (per_category, D75 Q50) x caps "
          f"{asg['depths']} ({asg['depths_status']}, D118) = {n} answers a model a draw (draw 1 planned; "
          f"{n * len(DRAWS)} with draws 2 and 3, Q5); smoke 2 x {asg['smoke_depths']} x draw 1")
    if asg["model_order"]:
        print(f"interleaved (D118): questions {' '.join(asg['question_order'])}; caps {asg['depths']}; models "
              f"{' '.join(asg['model_order'])}")
    print(f"{'model':<26} {'runs as':<26} {'digest':<13} {'lock machines':<24} {'machine':<8} {'think':<7} "
          f"{'temp':>5} {'num_ctx':>7}  comparison  {'April caps':<26} held")
    total = 0
    for model in T1_MODELS:
        m = asg["machine_of"][model]
        if a.machine and m != a.machine:
            continue
        c = lk.ollama(model, role="generator", draw=1)
        run, dig = lk._run_tag(model)
        _, exc = lockmod._lookup(lk.d.get("exceptions", {}), model)
        held = ",".join(lk.d["models"][run]["machines"])
        print(f"{model:<26} {c.model:<26} {dig[:12]:<13} {held:<24} {m:<8} {str(c.fields.get('think', 'unsent')):<7} "
              f"{c.options['temperature']:>5} {c.options['num_ctx']:>7}  {'out (D23)' if exc else 'main':<10}  "
              f"{','.join(map(str, APRIL_CAPS[model])):<26} {HELD[model].split(':')[0] if model in HELD else '-'}")
        total += 1
    for m, spec in asg["machines"].items():
        if a.machine and m != a.machine:
            continue
        qd = spec.get("queues") or [spec["models"]]
        print(f"{m}" + (f":{spec['port']}" if spec.get("port") else "") + ": "
              + "; ".join(f"queue {i + 1}: " + " ".join(q) for i, q in enumerate(qd))
              + "  (D118: one interleaved walk; draws 2 and 3 only if Valerio gives them, Q5)")
    held = sum(1 for m in HELD if m in asg["machine_of"] and (not a.machine or asg["machine_of"][m] == a.machine))
    print(f"COUNTS: {total} models ({held} held), {len(qs)} questions, {len(asg['depths'])} caps, {n * total} answers "
          f"a draw")


def admit(a) -> None:
    lk = load_lock()
    asg = load_assignment(lk=lk)
    model = model_arg(a.model)
    if a.machine not in MACHINES:
        fail(f"machine {a.machine!r} is not one of {MACHINES}")
    if asg["machine_of"][model] != a.machine:
        fail(f"{model} runs on {asg['machine_of'][model]} (assignment.toml: one model, one machine), not {a.machine}")
    if a.machine == "studio" and a.port in STUDIO_RESERVED:
        fail(f"port {a.port} on the Studio is another job's or the Mentori app's ({STUDIO_RESERVED}), never T1's")
    if a.machine == "studio" and asg["port_of"].get("studio") not in (None, a.port):
        fail(f"T1 on the Studio runs on port {asg['port_of']['studio']} (assignment.toml, D118), not {a.port}")
    if a.machine != "studio" and a.port != 11434:
        fail(f"T1 on the {a.machine} uses its one paper server, the app's port, only")
    if model in HELD:
        fail(f"{model} is held: {HELD[model]}")
    run, dig = lk._run_tag(model)
    print(f"admitted: {model} (runs as {run}, digest {dig[:12]}) on {a.machine}:{a.port}")
    print(f"COUNTS: admitted 1")


def queue(a) -> None:
    """The (draw, model) starts of one queue, draw-major (D78 Q116: draw 1 of every model first), one per line."""
    asg = load_assignment()
    spec = asg["machines"].get(a.machine) or fail(f"no machine {a.machine!r} in assignment.toml")
    qs = spec.get("queues") or [spec["models"]]
    if not 1 <= a.queue <= len(qs):
        fail(f"{a.machine} has {len(qs)} queue(s), not {a.queue}")
    for d in sorted(set(a.draws)):
        for model in qs[a.queue - 1]:
            print(f"{d} {model}")


def progress(a) -> None:
    model = model_arg(a.model)
    asg = load_assignment()
    depths = asg["smoke_depths"] if a.smoke else asg["depths"]
    draws = (1,) if a.smoke else DRAWS
    rows, problems = answers(model, a.smoke, Path(a.results) if a.results else None)
    exp = expected(model, a.smoke, depths, draws)
    by, err, kinds = collections.Counter(), collections.Counter(), collections.Counter()
    for k, (d, q, dr) in exp.items():
        if k in rows:
            by[(dr, d)] += 1
            kind = error_kind(rows[k])
            err[(dr, d)] += bool(kind)
            kinds[kind or "none"] += 1
    print(f"{model}{' smoke' if a.smoke else ''}: stored (errors) per cap")
    print("draw  " + " ".join(f"{'c' + str(d):>9}" for d in depths))
    for dr in draws:
        print(f"{dr:>4}  " + " ".join(f"{by[(dr, d)]:>4} ({err[(dr, d)]:>2})" for d in depths))
    extra = [k for k in rows if k not in exp]
    for p in problems:
        print(f"  PROBLEM {p}")
    if extra:
        print(f"  {len(extra)} stored keys outside the plan (first {extra[0]})")
    print(f"COUNTS: {sum(by.values())} of {len(exp)} stored, {sum(err.values())} with an error "
          f"(max_turns_empty {kinds['max_turns_empty']}, call_error {kinds['call_error']}, machine {kinds['machine']}, "
          f"other {kinds['other']})" + (f", {len(problems)} problems" if problems else ""))
    if problems:
        sys.exit(1)


def complete(a) -> None:
    model = model_arg(a.model)
    asg = load_assignment()
    rows, problems = answers(model, False, Path(a.results) if a.results else None)
    draws = tuple(sorted(set(a.draws)))
    exp = expected(model, False, asg["depths"], draws)
    missing = [k for k in exp if k not in rows]
    print(f"COUNTS: {model} draws {'+'.join(map(str, draws))}: {len(exp) - len(missing)} of {len(exp)} stored")
    if problems or missing:
        fail(f"{len(missing)} keys missing (first {missing[:1]}); problems: {problems[:3]}")
    print(f"complete: every key of draws {draws} stored")


def smoke(a) -> None:
    model = model_arg(a.model)
    md = D / slug(model)
    launch_path = Path(a.launch) if a.launch else md / "smoke_launch.json"
    if not launch_path.exists():
        fail(f"no launch record {launch_path}")
    launch = json.loads(launch_path.read_text())
    lock_sha, base = launch.get("lock_sha256"), launch.get("base")
    lk = load_lock()
    asg = load_assignment(lk=lk)
    p = []
    end = Path(a.end) if a.end else md / "smoke.end.json"
    if not end.exists() or json.loads(end.read_text()).get("rc") != 0:
        p.append(f"{end.name} missing or not exit 0")
    rows, problems = answers(model, True, Path(a.results) if a.results else None)
    p += problems
    exp = expected(model, True, asg["smoke_depths"], (1,))
    if set(rows) != set(exp):
        p.append(f"the smoke files hold {len(rows)} keys, not the {len(exp)} expected (missing "
                 f"{sorted(set(exp) - set(rows))[:2]}, extra {sorted(set(rows) - set(exp))[:2]})")
    errs = [k for k, r in rows.items() if r.get("error")]
    if rows and len(errs) == len(rows):
        p.append("every smoke answer stored with an error")
    for k, r in rows.items():
        if not r.get("error") and (r.get("rlm") is None or not r.get("stop_reason")):
            p.append(f"{k}: no RLM record or stop reason")
        if r.get("model") != LOCAL + model:
            p.append(f"{k}: stored for model {r.get('model')!r}, not {LOCAL + model}")
    runs = Path(a.runs) if a.runs else RUNS
    run_tag, digest = lk._run_tag(model)
    statuses = collections.Counter()
    for d in asg["smoke_depths"]:
        sink = runs / run_name(model, d, smoke=True)
        calls = read_jsonl(sink / "calls.jsonl")
        if not calls:
            p.append(f"rlm_{d}: no calls.jsonl lines")
            continue
        for c in calls:
            statuses[c.get("status")] += 1
            where = f"rlm_{d} seq {c.get('seq')}"
            if c.get("lock_sha256") != lock_sha:
                p.append(f"{where}: lock {str(c.get('lock_sha256'))[:8]}, not the launch's {str(lock_sha)[:8]}")
                break
            if c.get("provider", "ollama") != "ollama" or c.get("model") != run_tag:
                p.append(f"{where}: a call to {c.get('provider')}:{c.get('model')}, not ollama:{run_tag}")
                break
            if c.get("server") != base:
                p.append(f"{where}: sent to {c.get('server')}, not the launch's server {base}")
                break
            if c.get("status") == "error" and NOT_REACHED.search(c.get("error") or ""):
                p.append(f"{where}: failed before its request reached the server ({str(c.get('error'))[:80]})")
                break
            if c.get("options_sent") is None:
                continue                                    # a failed call with nothing sent (counted in statuses)
            try:
                want = lk.ollama(model, role="generator", draw=c.get("draw"), thinking=None,   # D66, never the record's
                                 candidate=c.get("candidate"), retry=c.get("retry"))
            except Exception as e:                          # noqa: BLE001  (a LockError, a missing field)
                p.append(f"{where}: the lock builds no call for it ({e!r})")
                break
            if c.get("draw") != c.get("run_draw", c.get("draw")) or c.get("options_sent") != want.options \
                    or c.get("fields_sent") != want.fields:
                p.append(f"{where}: draw {c.get('draw')} (run draw {c.get('run_draw')}) sent {c.get('options_sent')} "
                         f"and {c.get('fields_sent')}, not the lock's {want.options} and {want.fields}")
                break
            if c.get("model_digest") != digest:
                p.append(f"{where}: digest {str(c.get('model_digest'))[:12]}, not the lock's {digest[:12]}")
                break
        have = {(c.get("item_id"), c.get("run_draw", c.get("draw"))) for c in calls}
        for k, (dd, q, dr) in exp.items():
            if dd == d and k in rows and (q, dr) not in have:
                p.append(f"{k}: no call of its own in rlm_{d}'s sink")
        ident = read_jsonl(sink / "index_identity.jsonl")
        if not ident or any(i.get("index_name") != INDEX or i.get("n_chunks") != INDEX_CHUNKS for i in ident):
            p.append(f"rlm_{d}: index_identity.jsonl missing or not {INDEX} with {INDEX_CHUNKS} chunks")
    lat = collections.defaultdict(list)
    for r in rows.values():
        lat[r["depth"]].append(r.get("latency_s") or 0)
    timing = {d: {"n": len(v), "latency_mean_s": round(statistics.mean(v), 1)} for d, v in sorted(lat.items())}
    kinds = collections.Counter(error_kind(r) or "none" for r in rows.values())
    out = {"smoke_passed": not p, "model": model, "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "launch_record": launch, "answers": len(rows), "errors": len(errs), "error_kinds": dict(kinds),
           "call_statuses": dict(statuses), "problems": p, "timing_by_depth": timing}
    outp = Path(a.out) if a.out else md / "smoke_check.json"
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(out, indent=1) + "\n")
    for x in p:
        print(f"  PROBLEM {x}")
    print(f"timing by cap: {timing}; call statuses {dict(statuses)}; error kinds {dict(kinds)}")
    print(f"wrote {outp}: smoke_passed {out['smoke_passed']}")
    print(f"COUNTS: smoke {len(rows)} answers, {len(errs)} with an error, {len(p)} problems")
    if p:
        sys.exit(1)


def record(a) -> None:
    if a.out.exists():
        raise SystemExit(f"refused: {a.out} exists")
    models = [model_arg(m) for m in a.models]
    git = lambda *x: subprocess.run(["git", "-C", str(ROOT), *x], capture_output=True, text=True,  # noqa: E731
                                    check=True).stdout.strip()
    out = subprocess.run(["ps", "-eo", "pid=,etime=,args="], capture_output=True, text=True, check=True).stdout
    procs = []
    for line in out.splitlines():
        parts = line.strip().split(None, 2)
        if len(parts) == 3 and re.search(r"exp_0[0-9]_|ragchecker|S357_ragas|judge|experiments\.runner", parts[2]):
            procs.append({"pid": int(parts[0]), "etime": parts[1], "command": parts[2][:300]})
    lk = load_lock()
    rec = {"kind": a.kind, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "host": socket.gethostname(),
           "machine": a.machine, "base": a.base, "queue": a.queue, "models": models,
           "runs_as": {m: lk._run_tag(m)[0] for m in models},
           "clone": str(ROOT), "commit": git("rev-parse", "HEAD"),
           "tracked_changes_under_experiments": git("status", "--porcelain", "--untracked-files=no", "--",
                                                    "experiments").splitlines(),
           "lock_sha256": hashlib.sha256(LOCK.read_bytes()).hexdigest(),
           "assignment_sha256": hashlib.sha256(ASSIGNMENT.read_bytes()).hexdigest(),
           "draws": a.draws or [1], "statements": {k: os.environ.get(k) for k in ("T1_LOCK_OK", "T1_NOTE")},
           "jobs_running_on_this_machine": procs}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    tmp = a.out.with_name(f".{a.out.name}.{os.getpid()}")
    tmp.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
    os.link(tmp, a.out)
    tmp.unlink()
    print(f"{a.out}: {a.kind} launch record written")
    print(f"COUNTS: launch record {a.kind}")


def cells(asg: dict, draw: int = 1) -> list:
    """D118: the interleaved order, one (question, cap, model, draw) per cell: question by question in question_order,
    within a question cap by cap (ascending), within a cap model by model in model_order. A cell's place in this list
    is its index g; its slot (question, cap) is g // len(model_order)."""
    if not asg.get("model_order"):
        raise SystemExit("assignment: the models are on more than one machine; the interleaved order needs one (D118)")
    return [(q, c, m, draw) for q in asg["question_order"] for c in asg["depths"] for m in asg["model_order"]]


def stored_cells(asg: dict, draw: int = 1, results: Path = None) -> tuple:
    """(the cells whose answer is stored, the keys stored outside the order's cells, problems): each model's results
    files as exp_06's resume reads them (answers())."""
    have, extra, problems = set(), 0, []
    for m in asg["model_order"]:
        rows, pr = answers(m, False, results)
        problems += [f"{m}: {x}" for x in pr]
        key = {ex.answer_key(f"rlm_{c}", q, draw): (q, c, m, draw) for q in asg["question_order"] for c in asg["depths"]}
        have |= {key[k] for k in rows if k in key}
        extra += sum(1 for k in rows if k not in key)
    return have, extra, problems


def interleave_problems(order: list, have: set, log: list, held_now=()) -> tuple:
    """D118's check of the stored cells against the written order (module docstring, rules 1 to 4). Returns (problems,
    a summary dict). order: cells(); have: the stored cells; log: the walk log's records; held_now: the models held
    now (reported, not needed by the rules: a hold is proved by the walk's records)."""
    index = {cell: g for g, cell in enumerate(order)}
    models = list(dict.fromkeys(c[2] for c in order))
    p = []
    held_rec = {tuple(r["cell"]) for r in log if r.get("action") == "held"}
    begun = {tuple(r["cell"]) for r in log if r.get("action") == "begin"}
    for r in log:                                           # a record names a cell of the order at its index
        if r.get("action") in ("held", "begin") and index.get(tuple(r.get("cell") or ())) != r.get("g"):
            p.append(f"walk log: a {r.get('action')} record at g {r.get('g')} names {r.get('cell')}, not that cell")
    # (1) each model's stored cells are a prefix of its cells
    k = {}
    for m in models:
        mine = [c for c in order if c[2] == m]
        stored = [c in have for c in mine]
        k[m] = stored.index(False) if False in stored else len(stored)
        if any(stored[k[m]:]):
            late = next(c for c in mine[k[m]:] if c in have)
            p.append(f"{m}: {late[0]} cap {late[1]} stored after its missing {mine[k[m]][0]} cap {mine[k[m]][1]} "
                     f"(not a prefix)")
    # (2) below the furthest stored cell, a missing cell was passed while its model was held
    front = max((index[c] for c in have), default=-1)
    unheld = [c for c in order[:max(front, 0)] if c not in have and c not in held_rec]
    if unheld:
        c = unheld[0]
        p.append(f"{len(unheld)} cells missing below the furthest stored cell without a hold record (first {c[2]} at "
                 f"{c[0]} cap {c[1]}): a model ahead of another by more than the cell in flight")
    # (3) nothing stored outside the walk
    outside = sorted((c for c in have if c not in begun), key=index.get)
    if outside:
        p.append(f"{len(outside)} stored cells with no begin record in the walk log (first {outside[0]}): stored "
                 f"outside the interleaved walk")
    # (4) each pass goes strictly forward
    last = {}
    for r in log:
        if r.get("action") not in ("held", "begin"):
            continue
        pid, g = r.get("pass"), r.get("g")
        if pid in last and not (isinstance(g, int) and g > last[pid]):
            p.append(f"walk log: pass {pid} went from g {last[pid]} back to g {g}")
            break
        last[pid] = g
    # (5) no stored answer from a load that did not pass both checks: a cell whose latest "void" or successful "end"
    # record (exit 0, stored, its load passed) is a void is still the void answer, until moved aside and answered again
    latest = {}
    for r in log:
        if r.get("action") == "void" or (r.get("action") == "end" and r.get("rc") == 0 and r.get("stored") is True
                                         and r.get("load_ok") is not False):
            latest[tuple(r.get("cell") or ())] = r["action"]
    void = sorted((c for c in have if latest.get(c) == "void"), key=index.get)
    if void:
        p.append(f"{len(void)} stored cells answered on a load that did not pass its checks (void record; first "
                 f"{void[0][2]} at {void[0][0]} cap {void[0][1]}): move the answer aside (README Service steps)")
    nm = len(models)
    slots = len(order) // nm if nm else 0
    lead = max(k.values(), default=0)
    behind = sorted(m for m in models if k[m] < lead - 1)   # catching up (or held): rule (2) proves each was held
    complete_q = [q for q in dict.fromkeys(c[0] for c in order)
                  if all(c in have for c in order if c[0] == q and c[2] not in held_now)]
    return p, {"stored": len(have), "cells": len(order), "front_g": front, "slots": slots, "k": k,
               "behind": behind, "held_now": sorted(held_now), "complete_questions": complete_q}


def order_mode(a) -> None:
    """The written order (D118), each cell with its state: stored, held (its model is held now) or pending."""
    asg = load_assignment()
    order = cells(asg, a.draw)
    have, extra, problems = stored_cells(asg, a.draw, Path(a.results) if a.results else None)
    n = 0
    for g, c in enumerate(order):
        state = "stored" if c in have else "held" if c[2] in HELD else "pending"
        if a.first is None or n < a.first:
            print(f"{g:>4} {c[0]:<26} cap {c[1]:>2} {c[2]:<26} {state}")
        n += 1
    pend = sum(1 for c in order if c not in have and c[2] not in HELD)
    print(f"COUNTS: order d{a.draw}: {len(order)} cells ({len(asg['question_order'])} questions x "
          f"{len(asg['depths'])} caps x {len(asg['model_order'])} models), {len(have)} stored, {pend} pending, "
          f"{sum(1 for c in order if c not in have and c[2] in HELD)} held" + (f", {extra} keys outside" if extra else ""))
    if problems:
        fail(f"results files: {problems[:3]}")


def interleaved(a) -> None:
    """D118: the stored answers follow the written order (interleave_problems); exit 1 on any problem."""
    asg = load_assignment()
    order = cells(asg, a.draw)
    have, extra, problems = stored_cells(asg, a.draw, Path(a.results) if a.results else None)
    log = [r for r in read_jsonl(Path(a.walk_log) if a.walk_log else WALK_LOG) if r.get("draw", a.draw) == a.draw]
    held_now = [m for m in asg["model_order"] if m in HELD]
    p, s = interleave_problems(order, have, log, held_now)
    p = [f"results files: {x}" for x in problems] + p
    nm = len(asg["model_order"])
    f = s["front_g"]
    where = f"{order[f][0]} cap {order[f][1]} {order[f][2]}" if f >= 0 else "nothing stored"
    print(f"interleaved d{a.draw}: caps {asg['depths']} ({asg['depths_status']}); furthest stored cell {f} of "
          f"{len(order)} ({where}); per model stored: " + ", ".join(f"{m} {s['k'][m]}" for m in asg["model_order"]))
    print(f"questions complete for every model not held: {len(s['complete_questions'])} "
          f"({' '.join(s['complete_questions'])})")
    if s["behind"]:
        print(f"behind the others by more than the cell in flight (held, or catching up after a hold): "
              f"{' '.join(s['behind'])}")
    for x in p:
        print(f"  PROBLEM {x}")
    print(f"COUNTS: interleaved d{a.draw}: {s['stored']} of {s['cells']} cells stored, front slot "
          f"{(f // nm) + 1 if f >= 0 else 0} of {s['slots']}, {len(s['complete_questions'])} questions complete, "
          f"{len(held_now)} models held, {len(p)} problems" + (f", {extra} keys outside the order" if extra else ""))
    if p:
        sys.exit(1)


def fault_of(line: bytes):
    """The machine fault one calls.jsonl line records (its seq and error), or None: status error with NOT_REACHED in
    its error (the lock adapter's "before the request was posted", a timeout, a refused or reset connection)."""
    try:
        c = json.loads(line)
    except ValueError:
        return None
    if isinstance(c, dict) and c.get("status") == "error" and NOT_REACHED.search(str(c.get("error") or "")):
        return {"seq": c.get("seq"), "item_id": c.get("item_id"), "error": str(c.get("error"))[:300]}
    return None


def faults(a) -> None:
    """--mark: each sink's calls.jsonl size now. --since: the faults written after those sizes (once, or --follow)."""
    model = model_arg(a.model)
    asg = load_assignment()
    runs = Path(a.runs) if a.runs else RUNS
    files = {str(runs / run_name(model, d, a.smoke) / "calls.jsonl")
             for d in (asg["smoke_depths"] if a.smoke else asg["depths"])}
    if a.mark:
        sizes = {f: (Path(f).stat().st_size if Path(f).exists() else 0) for f in sorted(files)}
        Path(a.mark).write_text(json.dumps(sizes, indent=1) + "\n")
        print(f"COUNTS: faults mark, {len(sizes)} sinks")
        return
    pos = json.loads(Path(a.since).read_text())
    if set(pos) != files:
        fail(f"{a.since} names other sinks than {model}'s{' smoke' if a.smoke else ''}")
    buf = {f: b"" for f in files}
    while True:
        for f in sorted(files):
            fp = Path(f)
            if not fp.exists():
                continue
            size = fp.stat().st_size
            if size < pos[f]:
                fail(f"{f} shrank from {pos[f]} to {size} bytes: a sink is never rewritten")
            if size == pos[f]:
                continue
            with fp.open("rb") as fh:
                fh.seek(pos[f])
                data = buf[f] + fh.read(size - pos[f])
            pos[f] = size
            *lines, buf[f] = data.split(b"\n")
            for ln in lines:
                hit = fault_of(ln)
                if hit:
                    hit.update({"sink": Path(f).parent.name, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
                    if a.marker:
                        Path(a.marker).write_text(json.dumps(hit, indent=1) + "\n")
                    if a.stop:
                        Path(a.stop).touch()
                    print(f"MACHINE FAULT in {hit['sink']} seq {hit['seq']}: {hit['error'][:200]}")
                    print("COUNTS: faults 1 (machine)")
                    sys.exit(4)
        if not a.follow:
            print("COUNTS: faults 0")
            return
        time.sleep(a.poll)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--machine", choices=MACHINES)
    p = sub.add_parser("admit")
    p.add_argument("--model", required=True)
    p.add_argument("--machine", required=True)
    p.add_argument("--port", type=int, required=True)
    p = sub.add_parser("queue")
    p.add_argument("--machine", required=True, choices=MACHINES)
    p.add_argument("--queue", type=int, default=1)
    p.add_argument("--draws", nargs="+", type=int, required=True, choices=list(DRAWS))
    p = sub.add_parser("progress")
    p.add_argument("--model", required=True)
    p.add_argument("--smoke", action="store_true")
    p.add_argument("--results", default=None, help="the results_v4 folder (tests)")
    p = sub.add_parser("complete")
    p.add_argument("--model", required=True)
    p.add_argument("--draws", nargs="+", type=int, required=True, choices=list(DRAWS))
    p.add_argument("--results", default=None)
    p = sub.add_parser("smoke")
    p.add_argument("--model", required=True)
    p.add_argument("--launch", default=None)
    p.add_argument("--end", default=None)
    p.add_argument("--out", default=None)
    p.add_argument("--results", default=None, help="the results_v4 folder (tests)")
    p.add_argument("--runs", default=None, help="the findings/runs folder (tests)")
    p = sub.add_parser("record")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--kind", choices=("smoke", "run", "interleaved"), required=True)
    p.add_argument("--models", nargs="+", required=True)
    p.add_argument("--machine", required=True, choices=MACHINES)
    p.add_argument("--base", required=True)
    p.add_argument("--queue", type=int, default=None)
    p.add_argument("--draws", nargs="*", type=int, choices=list(DRAWS))
    p = sub.add_parser("faults")
    p.add_argument("--model", required=True)
    p.add_argument("--smoke", action="store_true")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--mark", default=None, help="write each sink's calls.jsonl size to this file")
    g.add_argument("--since", default=None, help="read only what the sinks gained after these sizes")
    p.add_argument("--follow", action="store_true")
    p.add_argument("--poll", type=float, default=2.0)
    p.add_argument("--stop", default=None, help="touched on a fault (exp_06's --stop-file)")
    p.add_argument("--marker", default=None, help="written on a fault")
    p.add_argument("--runs", default=None, help="the findings/runs folder (tests)")
    p = sub.add_parser("order")
    p.add_argument("--draw", type=int, default=1, choices=list(DRAWS))
    p.add_argument("--first", type=int, default=None, help="print only the first n cells")
    p.add_argument("--results", default=None, help="the results_v4 folder (tests)")
    p = sub.add_parser("interleaved")
    p.add_argument("--draw", type=int, default=1, choices=list(DRAWS))
    p.add_argument("--walk-log", default=None, help="interleave_t1.py's records (default interleaved_walk.jsonl here)")
    p.add_argument("--results", default=None, help="the results_v4 folder (tests)")
    a = ap.parse_args(argv)
    if a.mode == "faults" and a.follow and not (a.since and a.stop and a.marker):
        ap.error("faults --follow needs --since, --stop and --marker")
    {"plan": plan, "admit": admit, "queue": queue, "progress": progress, "complete": complete, "smoke": smoke,
     "record": record, "faults": faults, "order": order_mode, "interleaved": interleaved}[a.mode](a)


if __name__ == "__main__":
    main(sys.argv[1:])
