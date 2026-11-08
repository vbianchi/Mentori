"""K1's split of Figure 5's scoring over machines (D83, Q142) and stages (D86), read by both K1 scorers.

    from experiments.scorers import assignment as A
    asg = A.load(Path("findings/recompute/K1/assignment.json"))   # refused unless its sha256 fields recompute
    todo = A.select(items, asg, "beelink", stage=1)               # items: records.read_run() answers of the six runs

WHAT THE FILE IS. scripts/S451_k1_assign.py writes findings/recompute/K1/assignment.json before any scoring: the rule
(its text and sha256), the draws scored, the configs in their order of work inside a question, the machines, and every
question with its machine, in the answer key's order (the order of work on each machine). assignment_sha256 is the
sha256 of the canonical JSON of those signed fields (SIGNED), so a file edited by hand is refused. not_scored lists
the questions of the runs that K1 does not score, each with its reason (Rule 8: not applicable), so they are known and
skipped, never taken for answers of another question set.

STAGES (D86). A staged file also signs "seed" and "stage_sizes" ({"1": {machine: questions}, "2": {...}}), and every
question carries "stage" (1 or 2). Since the D86 review (D1, 17 October) it also signs "stage_2_inputs", what S451's
stage 2 deal read (each machine's start, each question's estimated hours per machine, the answers' sha256), so S451
check recomputes the deal; load() checks it only through assignment_sha256. load() then also refuses a question without a stage of the file, and a file whose
count of questions per (stage, machine) differs from stage_sizes. A file without stage_sizes is the D83 form (no
question has a stage); both forms load.

WHAT select() DOES. Of the answers it is given, it keeps those of the assignment's draws whose question the assignment
gives to `machine` (and, with `stage`, puts in that stage), and returns them question by question: stage 1's questions
first, then stage 2's, each stage in the file's question order, the configs in the file's order inside each question.
In a staged file each answer returned carries "k1_stage", its question's stage (records.item_sha256 does not read
it). Answers to a question in not_scored are skipped. It refuses: a machine the file does not name; a stage the file
does not have (any stage of a D83 file); an answer of a config the file does not name (a wrong run passed); an answer
whose question the file names neither in questions nor in not_scored, in a draw it scores (a run on other questions;
a question of the other stage is known, so it is left out, never refused); and a missing or doubled answer, for any
(question of this machine and stage, config, draw), so a machine never scores fewer than all six strategies' answers
to one of its questions.

WORKERS AND THE AMENDMENT CHAIN (helpers, Valerio, 17 October: "plan it in a way that we can also spawn other runs on
the other machines to help if there is computational availability"). A worker is a name bound to (machine, port,
clone). The base file's three machines are the three first workers, each named as its machine; a helper is named
<machine>_<port>. assignment.json is never edited: findings/recompute/K1/amendments.json holds a genesis record (the
base's assignment_sha256 and file sha256, the lock_sha256, the worker registry and the move rule with its sha256,
signed by genesis_sha256) and a list of records, each signed by amendment_sha256 over its canonical JSON and linked to
the one before by prev (the genesis_sha256 for the first). A record of kind "move" gives questions from one worker to
another (defining the target in to_defined when it is new); a record of kind "abandon" releases a fence no move used.
load_chain() refuses a record changed by hand, records out of order, a broken prev, a chain written for another base,
and a move of a question its source did not hold. effective(base, chain, upto) is the base with the moves up to the
record whose sha256 is upto applied in order: every question keeps its stage (so stage 1 is the base's 25, D86) and
gets "worker" (its owner) and "machine" (the owner's physical machine). select(items, eff, worker, stage) then works by
worker, in the same order as before (stage 1 then stage 2, each in the key's order). With an empty chain the effective
assignment selects exactly what the base does for every machine.

for_worker() is what a scorer calls: the chain verified, the worker's machine checked, its fence none or released
against a head the chain holds (fence_status()), and its question list under the head the launcher pinned equal to its
list under the file now, so an amendment that touches only other workers does not stop it and one that touches it
does. select() by machine on a base file refuses a machine that a move of the chain beside it names
(amended_workers()), so a scorer run without --worker cannot score a question moved away. touched() is what a fence
counts as begun; collect() is how A5 reads every worker's rows.

Standard library only (runs in the scorers' own environments).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

SIGNED = ("rule", "rule_sha256", "draws", "configs", "machines", "questions", "not_scored")
STAGED = ("seed", "stage_sizes", "stage_2_inputs")   # D86: signed too, when the file has them
STAGES = (1, 2)


class AssignmentError(Exception):
    pass


def canonical(asg: dict) -> bytes:
    """The bytes assignment_sha256 is computed over: the SIGNED fields (and the STAGED ones a staged file holds),
    sorted keys, no spaces, UTF-8."""
    keys = SIGNED + tuple(k for k in STAGED if k in asg)
    return json.dumps({k: asg[k] for k in keys}, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def staged(asg: dict) -> bool:
    return "stage_sizes" in asg


def sha256(b: bytes | str) -> str:
    return hashlib.sha256(b.encode("utf-8") if isinstance(b, str) else b).hexdigest()


def load(path: Path) -> dict:
    """The assignment file, checked: its rule_sha256 and assignment_sha256 recompute, every question once with a
    machine the file names, draws and configs non-empty and without repeats. Adds file_sha256 (of the bytes read)."""
    raw = Path(path).read_bytes()
    try:
        asg = json.loads(raw)
    except ValueError as e:
        raise AssignmentError(f"{path} is not JSON ({e})") from None
    missing = [k for k in SIGNED + ("assignment_sha256",) if k not in asg]
    if missing:
        raise AssignmentError(f"{path} lacks {missing}")
    if sha256(asg["rule"]) != asg["rule_sha256"]:
        raise AssignmentError(f"{path}: rule_sha256 is not the sha256 of its rule text")
    if sha256(canonical(asg)) != asg["assignment_sha256"]:
        raise AssignmentError(f"{path}: assignment_sha256 does not recompute; the file was changed after it was written")
    for k in ("draws", "configs", "machines"):
        v = asg[k]
        if not isinstance(v, list) or not v or len(set(v)) != len(v):
            raise AssignmentError(f"{path}: {k} must be a non-empty list without repeats, not {v!r}")
    ids = [q.get("id") for q in asg["questions"]] + [q.get("id") for q in asg["not_scored"]]
    if len(set(ids)) != len(ids) or not all(ids):
        raise AssignmentError(f"{path}: a question is listed twice (in questions or not_scored) or without an id")
    if not all(q.get("reason") for q in asg["not_scored"]):
        raise AssignmentError(f"{path}: a not_scored question has no reason")
    bad = [q["id"] for q in asg["questions"] if q.get("machine") not in asg["machines"]]
    if bad:
        raise AssignmentError(f"{path}: {len(bad)} questions have no machine of {asg['machines']} (first {bad[0]})")
    if staged(asg):
        if "seed" not in asg:
            raise AssignmentError(f"{path}: stage_sizes without the seed of the stage draw")
        sizes = asg["stage_sizes"]
        if sorted(sizes) != [str(k) for k in STAGES] or any(sorted(sizes[k]) != sorted(asg["machines"]) for k in sizes):
            raise AssignmentError(f"{path}: stage_sizes must give every machine a count in stages {list(STAGES)}")
        nostage = [q["id"] for q in asg["questions"] if q.get("stage") not in STAGES]
        if nostage:
            raise AssignmentError(f"{path}: {len(nostage)} questions have no stage of {list(STAGES)} (first {nostage[0]})")
        got = {(str(q["stage"]), q["machine"]): 0 for q in asg["questions"]}
        for q in asg["questions"]:
            got[(str(q["stage"]), q["machine"])] += 1
        off = [f"stage {k} {m}: {got.get((k, m), 0)} questions, stage_sizes {n}" for k in sizes
               for m, n in sizes[k].items() if got.get((k, m), 0) != n]
        if off:
            raise AssignmentError(f"{path}: the questions do not match stage_sizes ({'; '.join(off)})")
    elif any("stage" in q for q in asg["questions"]):
        raise AssignmentError(f"{path}: a question has a stage but the file signs no stage_sizes")
    return {**asg, "file_sha256": sha256(raw), "amended": amended_workers(Path(path).with_name("amendments.json"))}


def amended_workers(chain_path: Path) -> list:
    """The workers a move record of the amendment chain beside the assignment names (as its source or its target),
    read without verifying the chain; ["*"] when the file exists but cannot be read. select() by machine on the base
    refuses a machine named here (K1 helper review F2: a scorer run without --worker would score questions moved away
    and miss questions moved in)."""
    p = Path(chain_path)
    if not p.exists():
        return []
    try:
        recs = json.loads(p.read_bytes())["records"]
        return sorted({w for r in recs if r.get("kind") == "move" for w in (r.get("from"), r.get("to")) if w})
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return ["*"]


def machine_of(asg: dict) -> dict:
    return {q["id"]: q["machine"] for q in asg["questions"]}


def worker_of(asg: dict) -> dict:
    """question id -> its worker: q["worker"] in an effective assignment, the machine in a base file."""
    return {q["id"]: q.get("worker", q["machine"]) for q in asg["questions"]}


def owners(asg: dict) -> list:
    """The names select() accepts: the workers of an effective assignment, the machines of a base file."""
    return list(asg.get("workers") or asg["machines"])


def stage_of(asg: dict) -> dict:
    """question id -> its stage (1 or 2); empty for a D83 file."""
    return {q["id"]: q["stage"] for q in asg["questions"]} if staged(asg) else {}


def select(items: list[dict], asg: dict, machine: str, stage: int | None = None, base_ok: bool = False) -> list[dict]:
    """The answers `machine` scores (in `stage`, when given), in its order of work (the module docstring). In an
    effective assignment (effective()) `machine` is a worker's name: the answers of the questions that worker holds.
    On a base file (load()) a machine that a move of the amendment chain beside it names is refused (amended_workers;
    base_ok: a planning read that scores nothing)."""
    if machine not in owners(asg):
        raise AssignmentError(f"machine {machine!r} is not one of the assignment's {owners(asg)}")
    hit = [w for w in asg.get("amended", ()) if w in (machine, "*")] if "workers" not in asg else []
    if hit and not base_ok:
        raise AssignmentError(f"a move of the amendment chain beside the assignment names {machine!r}"
                              f"{' (the chain is unreadable)' if hit == ['*'] else ''}: its answers are its worker's "
                              f"under the chain, selected with --worker, --amendments and --amendments-head (the K1 "
                              f"launcher passes them)")
    st = stage_of(asg)
    if stage is not None and (not st or stage not in STAGES):
        raise AssignmentError(f"stage {stage!r}: the assignment has "
                              f"{'stages ' + str(list(STAGES)) if st else 'no stages (a D83 file)'}")
    where = {q: m for q, m in worker_of(asg).items() if stage is None or st[q] == stage}
    qpos = {q["id"]: (st.get(q["id"], 0), i) for i, q in enumerate(asg["questions"])}
    cpos = {c: i for i, c in enumerate(asg["configs"])}
    draws = set(asg["draws"])
    other = sorted({x["config"] for x in items} - set(cpos))
    if other:
        raise AssignmentError(f"answers of configs {other} are not in the assignment's {asg['configs']}; "
                              f"pass only the runs it names")
    skipped = {q["id"] for q in asg["not_scored"]}
    known = machine_of(asg)                      # every stage's questions: a question of the other stage is known
    stray = sorted({x["question_id"] for x in items
                    if x["draw"] in draws and x["question_id"] not in known and x["question_id"] not in skipped})
    if stray:
        raise AssignmentError(f"{len(stray)} answered questions are not in the assignment (first {stray[0]}); "
                              f"these runs are not the ones it was written for")
    keep = [x for x in items if x["draw"] in draws and where.get(x["question_id"]) == machine]
    seen: dict = {}
    for x in keep:
        k = (x["question_id"], x["config"], x["draw"])
        seen[k] = seen.get(k, 0) + 1
    want = [(q, c, d) for q in qpos if where.get(q) == machine for c in asg["configs"] for d in sorted(draws)]
    lacking = [k for k in want if seen.get(k, 0) == 0]
    doubled = [k for k, n in seen.items() if n > 1]
    if lacking or doubled:
        raise AssignmentError(f"{machine}: {len(lacking)} (question, config, draw) without an answer"
                              f"{' (first ' + '|'.join(map(str, lacking[0])) + ')' if lacking else ''}, "
                              f"{len(doubled)} with two; every assigned question needs one answer per config and draw")
    keep = sorted(keep, key=lambda x: (qpos[x["question_id"]], cpos[x["config"]], x["draw"]))
    if st:
        keep = [{**x, "k1_stage": st[x["question_id"]]} for x in keep]
    return keep


def stamp(asg: dict, machine: str, path: Path, stage: int | None = None, worker: str | None = None) -> dict:
    """What a scorer's header records about the assignment it ran under (and the stage it scored, D86). With a worker
    (an effective assignment, for_worker()), also the worker, its questions and the chain it ran under."""
    out = {"assignment": str(path), "assignment_file_sha256": asg["file_sha256"],
           "assignment_sha256": asg["assignment_sha256"], "rule_sha256": asg["rule_sha256"], "machine": machine,
           "draws": asg["draws"], "configs": asg["configs"],
           "questions_on_machine": sum(q["machine"] == machine for q in asg["questions"])}
    if staged(asg):
        who = (lambda q: q.get("worker", q["machine"]) == worker) if worker else (lambda q: q["machine"] == machine)
        out.update(seed=asg["seed"], k1_stage=stage, questions_in_stage=None if stage is None else sum(
            who(q) and q["stage"] == stage for q in asg["questions"]))
    if worker:
        ch = asg.get("chain") or {}
        out.update(worker=worker, questions_on_worker=sum(q.get("worker", q["machine"]) == worker
                                                          for q in asg["questions"]),
                   amendments=ch.get("path"), amendments_file_sha256=ch.get("file_sha256"),
                   amendments_head=asg.get("pinned_head"), amendments_file_head=ch.get("head"),
                   moves=asg.get("moves_applied"))
    return out


# ---------------------------------------------------------------- workers and the amendment chain (helpers)

GENESIS_KEYS = ("base_assignment_sha256", "base_file_sha256", "lock_sha256", "workers", "move_rule", "move_rule_sha256")
KINDS = ("move", "abandon")
DONE_RC = frozenset({"ok", "ok_ambiguous_labels", "no_answer", "not_applicable"})   # ragchecker_run.py DONE | n/a
DONE_RAGAS = frozenset({"ok", "ok_with_nulls", "not_applicable", "no_answer", "unscorable"})   # S357 RUN_DONE
SCORERS = ("ragchecker", "ragas")
ROWS = {"ragchecker": "ragchecker/ragchecker.jsonl", "ragas": "ragas/ragas.jsonl"}
CALLS = {"ragchecker": "ragchecker/ragchecker_calls.jsonl", "ragas": "ragas/ragas_calls.jsonl"}


def canon(obj) -> bytes:
    """Canonical JSON: sorted keys, no spaces, UTF-8."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def genesis_sha256(g: dict) -> str:
    return sha256(canon({k: v for k, v in g.items() if k != "genesis_sha256"}))


def record_sha256(r: dict) -> str:
    """amendment_sha256: over every field of the record but amendment_sha256 itself (prev included)."""
    return sha256(canon({k: v for k, v in r.items() if k != "amendment_sha256"}))


def fence_ids(r: dict) -> list:
    """The fence ids a chain record names (a move: its source's and its target's; an abandon: its fence)."""
    return [f["fence_id"] for f in (r.get("fence_from"), r.get("fence_to"), r.get("fence")) if f]


def load_chain(path: Path, base: dict) -> dict:
    """amendments.json, checked against the base it amends (load()'s dict): the genesis signature and base, every
    record's signature, order (seq 1, 2, ...) and prev link, each fence used once, and every move valid when applied
    in order (effective()). Returns {"genesis", "records", "head", "heads", "file_sha256", "path"}; head is the last
    record's amendment_sha256, the genesis_sha256 for an empty chain."""
    raw = Path(path).read_bytes()
    try:
        doc = json.loads(raw)
        g, records = doc["genesis"], doc["records"]
    except (ValueError, KeyError, TypeError) as e:
        raise AssignmentError(f"{path}: not an amendment chain ({type(e).__name__}: {e})") from None
    missing = [k for k in GENESIS_KEYS + ("genesis_sha256",) if k not in g]
    if missing:
        raise AssignmentError(f"{path}: the genesis lacks {missing}")
    if genesis_sha256(g) != g["genesis_sha256"]:
        raise AssignmentError(f"{path}: genesis_sha256 does not recompute; the genesis was changed after it was written")
    if g["base_assignment_sha256"] != base["assignment_sha256"] or g["base_file_sha256"] != base["file_sha256"]:
        raise AssignmentError(f"{path}: a chain for another base (assignment {g['base_assignment_sha256'][:12]}, "
                              f"file {g['base_file_sha256'][:12]}), not {base['assignment_sha256'][:12]} "
                              f"(file {base['file_sha256'][:12]})")
    if sha256(g["move_rule"]) != g["move_rule_sha256"]:
        raise AssignmentError(f"{path}: move_rule_sha256 is not the sha256 of its move rule")
    w = g["workers"]
    if sorted(w) != sorted(base["machines"]) or any(w[m].get("machine") != m for m in w):
        raise AssignmentError(f"{path}: the genesis registry must name each of the base's machines {base['machines']} "
                              f"as a worker on itself")
    prev, heads, used = g["genesis_sha256"], [g["genesis_sha256"]], {}
    for i, r in enumerate(records, 1):
        if r.get("seq") != i:
            raise AssignmentError(f"{path}: record {i} has seq {r.get('seq')}; records are out of order or missing")
        if r.get("prev") != prev:
            raise AssignmentError(f"{path}: record {i}'s prev {str(r.get('prev'))[:12]} is not the record before it "
                                  f"({prev[:12]}); the chain is broken")
        if record_sha256(r) != r.get("amendment_sha256"):
            raise AssignmentError(f"{path}: record {i}'s amendment_sha256 does not recompute; it was changed after it "
                                  f"was written")
        if r.get("kind") not in KINDS:
            raise AssignmentError(f"{path}: record {i} is of kind {r.get('kind')!r}, not one of {KINDS}")
        for f in fence_ids(r):
            if f in used:
                raise AssignmentError(f"{path}: record {i} uses fence {f[:12]}, already used by record {used[f]}")
            used[f] = i
        prev = r["amendment_sha256"]
        heads.append(prev)
    chain = {"genesis": g, "records": records, "head": prev, "heads": heads, "file_sha256": sha256(raw),
             "path": str(path)}
    effective(base, chain)                        # every move valid in order
    return chain


def registry(chain: dict, upto: str | None = None) -> dict:
    """worker -> {"machine", "port", "clone"}: the genesis's, then each move's to_defined in order (up to upto)."""
    reg = {k: dict(v) for k, v in chain["genesis"]["workers"].items()}
    for r in records_upto(chain, upto):
        if r["kind"] == "move" and r.get("to_defined"):
            reg[r["to"]] = dict(r["to_defined"])
    return reg


def records_upto(chain: dict, upto: str | None = None) -> list:
    """The records up to and including the one whose amendment_sha256 is upto (none for the genesis_sha256, all for
    None); refused when upto is in neither."""
    if upto is None:
        return list(chain["records"])
    if upto == chain["genesis"]["genesis_sha256"]:
        return []
    for i, r in enumerate(chain["records"]):
        if r["amendment_sha256"] == upto:
            return chain["records"][: i + 1]
    raise AssignmentError(f"the pinned head {str(upto)[:12]} is not in the chain {chain.get('path')} (head "
                          f"{chain['head'][:12]}); the file is not the one the launcher started on")


def effective(base: dict, chain: dict | None, upto: str | None = None) -> dict:
    """The base with the chain's moves up to upto applied (module docstring). Refuses a move whose target is unknown
    (or a new target that already exists), a question its source does not hold, or a stage that differs from the
    question's."""
    if chain is None:
        return base
    reg = {k: dict(v) for k, v in chain["genesis"]["workers"].items()}
    owner = {q["id"]: q["machine"] for q in base["questions"]}
    stage = {q["id"]: q.get("stage") for q in base["questions"]}
    recs = records_upto(chain, upto)
    for r in recs:
        if r["kind"] != "move":
            continue
        n = r["seq"]
        if r.get("to_defined"):
            if r["to"] in reg:
                raise AssignmentError(f"record {n} defines worker {r['to']!r}, which already exists")
            reg[r["to"]] = dict(r["to_defined"])
        if r.get("from") not in reg or r.get("to") not in reg or r["from"] == r["to"]:
            raise AssignmentError(f"record {n} moves from {r.get('from')!r} to {r.get('to')!r}: both must be workers "
                                  f"of the registry, and two")
        if not r.get("questions"):
            raise AssignmentError(f"record {n} moves no question")
        for q in r["questions"]:
            if owner.get(q["id"]) != r["from"]:
                raise AssignmentError(f"record {n} moves {q['id']} from {r['from']}, which does not hold it "
                                      f"({owner.get(q['id'])})")
            if q.get("stage") != stage[q["id"]]:
                raise AssignmentError(f"record {n} gives {q['id']} stage {q.get('stage')}, its stage is {stage[q['id']]}")
            owner[q["id"]] = r["to"]
    head = recs[-1]["amendment_sha256"] if recs else chain["genesis"]["genesis_sha256"]
    return {**base, "workers": list(reg), "registry": reg,
            "questions": [{**q, "worker": owner[q["id"]], "machine": reg[owner[q["id"]]]["machine"]}
                          for q in base["questions"]],
            "chain": {k: chain[k] for k in ("path", "file_sha256", "head")}, "pinned_head": head,
            "moves_applied": sum(r["kind"] == "move" for r in recs)}


def worker_questions(asg: dict, worker: str) -> list[dict]:
    """[{"id", "stage"}] the worker holds, in its order of work (stage 1 then stage 2, each in the key's order)."""
    st = stage_of(asg)
    qs = [(st.get(q["id"], 0), i, q["id"]) for i, q in enumerate(asg["questions"])
          if q.get("worker", q["machine"]) == worker]
    return [{"id": q, "stage": k or None} for k, _, q in sorted(qs)]


def fence_status(k1_dir: Path, worker: str, chain: dict) -> str:
    """The worker's fence (k1_dir/<worker>/fence.json) against the local chain: "none"; "released" only when the
    head it was released against is in the chain (so the record that used the fence is too); "rolled-back:<id12>"
    when that head is not (K1 helper review F1: amendments.json put back to an older chain after a release makes the
    source score its moved questions again); "unreleased:<id12>"; "unreadable"."""
    f = Path(k1_dir) / worker / "fence.json"
    if not f.exists():
        return "none"
    try:
        doc = json.loads(f.read_text())
        fid = str(doc.get("fence_id"))[:12]
    except (OSError, ValueError, AttributeError):
        return "unreadable"
    if not doc.get("released"):
        return f"unreleased:{fid}"
    return "released" if doc.get("released_head") in chain["heads"] else f"rolled-back:{fid}"


def for_worker(base_path: Path, chain_path: Path, worker: str, machine: str, head: str) -> dict:
    """What a K1 scorer selects from (D7): the base and chain verified, the worker in the registry on this machine, its
    fence none or released against a head the chain holds (fence_status), and its question list under the pinned head
    equal to its list under the file now. Returns the effective assignment."""
    base = load(base_path)
    chain = load_chain(chain_path, base)
    now = effective(base, chain)
    if worker not in now["registry"]:
        raise AssignmentError(f"worker {worker!r} is not in the registry of {chain_path} ({now['workers']})")
    fs = fence_status(Path(chain_path).parent, worker, chain)
    if fs not in ("none", "released"):
        raise AssignmentError(f"worker {worker!r}'s fence is {fs}: "
                              + ("released against a chain head that is not in " + str(chain_path) + "; the file was "
                                 "put back to an older chain after the release (check out the chain it was released "
                                 "against)" if fs.startswith("rolled-back") else "a scorer never runs while its worker "
                                 "is fenced (S451 release first)"))
    if now["registry"][worker]["machine"] != machine:
        raise AssignmentError(f"worker {worker!r} is on {now['registry'][worker]['machine']}, not {machine}")
    pinned = effective(base, chain, upto=head)
    if worker not in pinned["registry"] or worker_questions(pinned, worker) != worker_questions(now, worker):
        raise AssignmentError(f"worker {worker!r}'s questions under {chain_path} now (head {chain['head'][:12]}) differ "
                              f"from those under the head the launcher pinned ({head[:12]}): an amendment moved its "
                              f"questions while it ran; stop it and restart through the launcher")
    return {**now, "pinned_head": head}


# ---------------------------------------------------------------- what a worker has begun, and what A5 reads

def question_of_call(rec: dict, scorer: str) -> str | None:
    """The question a call record names (F6): RAGChecker's answer is "<run_id>|<answer key>", the key ending
    "|<question>|d<draw>"; RAGAS's is "<config>|<question>". None when the record has no answer."""
    a = rec.get("answer")
    if not isinstance(a, str) or "|" not in a:
        return None
    parts = a.split("|")
    return parts[-2] if scorer == "ragchecker" else parts[-1]


def touched(order: list[str], rows: dict, calls: dict) -> dict:
    """The questions a worker has begun, from its rows and call records ({scorer: [dict, ...]}; a call record that is
    None stands for a line that could not be read). A question is touched by any row, by any call record naming it,
    and, when a scorer has a call record that names no question, the scorer's next question (the first of `order`
    with no row of that scorer) is touched too. Returns {"rows": set, "calls": set}."""
    by_rows = {r.get("question_id") for s in SCORERS for r in rows.get(s, ())}
    by_calls = set()
    for s in SCORERS:
        untagged = False
        for rec in calls.get(s, ()):
            q = question_of_call(rec, s) if isinstance(rec, dict) else None
            if q is None:
                untagged = True
            else:
                by_calls.add(q)
        if untagged:
            have = {r.get("question_id") for r in rows.get(s, ())}
            nxt = next((q for q in order if q not in have), None)
            if nxt is not None:
                by_calls.add(nxt)
    return {"rows": by_rows - {None}, "calls": by_calls}


def read_jsonl(path: Path, lenient: bool = False) -> list:
    """The lines of a jsonl file as dicts; a line that is not JSON raises, or is None with lenient."""
    out = []
    if not Path(path).exists():
        return out
    for n, ln in enumerate(Path(path).read_text(errors="replace").splitlines(), 1):
        if not ln.strip():
            continue
        try:
            out.append(json.loads(ln))
        except ValueError:
            if not lenient:
                raise AssignmentError(f"{path}: line {n} is not JSON (a write cut short?)") from None
            out.append(None)
    return out


def row_worker(row: dict) -> str | None:
    """The worker that wrote a row: its "worker", or its "machine" for a row written before workers existed."""
    return row.get("worker") or row.get("machine")


def collect(k1_dir: Path, base: dict, chain: dict, done: dict | None = None) -> dict:
    """A5's reading of K1 (D9): every worker's two row files under k1_dir/<worker>/, the latest row per (run_id,
    config, question_id, draw) kept. Refused: a question with rows in two workers' files, a row whose worker is not
    its question's owner in the final chain, a row in a worker's file written by another worker. Returns {"rows":
    {scorer: [rows]}, "missing": {scorer: [question ids without a done row for every config and draw]}}."""
    done = done or {"ragchecker": DONE_RC, "ragas": DONE_RAGAS}
    eff = effective(base, chain)
    owner = worker_of(eff)
    where: dict = {}
    out, missing = {}, {}
    for s in SCORERS:
        latest: dict = {}
        for w in eff["workers"]:
            for r in read_jsonl(Path(k1_dir) / w / ROWS[s]):
                q = r.get("question_id")
                if row_worker(r) != w:
                    raise AssignmentError(f"{w}/{ROWS[s]}: a row of {q} written by {row_worker(r)!r}")
                where.setdefault(q, set()).add(w)
                if len(where[q]) > 1:
                    raise AssignmentError(f"{q} has rows in the files of {sorted(where[q])}; a question is scored on one "
                                          f"worker (Q142)")
                if owner.get(q) != w:
                    raise AssignmentError(f"{w}/{ROWS[s]}: a row of {q}, which the final chain gives to {owner.get(q)}")
                latest[(r["run_id"], r["config"], q, r["draw"])] = r
        out[s] = list(latest.values())
        ok = {(k[1], k[2], k[3]) for k, r in latest.items() if r.get("status") in done[s]}
        missing[s] = [q["id"] for q in eff["questions"]
                      if not all((c, q["id"], d) in ok for c in eff["configs"] for d in eff["draws"])]
    return {"rows": out, "missing": missing, "head": chain["head"]}
