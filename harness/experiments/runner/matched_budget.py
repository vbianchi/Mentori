"""D51's matched-budget arm (D36): its plan, and after it has run, the input tokens it reached.

    # the plan, from the RLM-10 run's records (needs the Mentori database and index, and the generator's tokenizer)
    uv run --project experiments/mentori --frozen python -m experiments.runner.matched_budget plan \\
        --rlm-run exp_01__rlm_10__exp_v4_s20_n0 --out <plan.json>
    # the arm: exp_01 --configs matched_budget --matched-budget-plan <plan.json>
    # the tokens it reached, from the arm's records (offline)
    uv run --project experiments/mentori --frozen python -m experiments.runner.matched_budget reached \\
        --plan <plan.json> --arm-run exp_01__matched_budget__exp_v4_s20_n0 --out <reached.json>
    # PA3 (G13): a plan again for the named questions only, every other entry copied from the base plan
    uv run --project experiments/mentori --frozen python -m experiments.runner.matched_budget replan \\
        --base-plan <plan.json> --rlm-dir <RLM-10 run folder> --questions-file <ids.json> --out <new plan.json> \\
        [--dry-run] [--accept-count-drift <DECISION> [--max-drift 0.01]]

D51: the matched-budget arm is single pass given more passages until its input tokens per question match RLM-10's
median; one call, same model.

TARGETS. An RLM-10 answer is the last line of its answer key in <run>/answers.jsonl. Its input tokens are the sum of
prompt_tokens over every record in <run>/calls.jsonl with that line's ctx_uid (the root turns and the sub-calls of
that (question, draw)). Q80 (D75): every answer whose token count is complete is a source, including one that ran to
its turn limit with nothing to show (stop_reason max_turns_empty, stored with an error): it spent the tokens, and A5
(D67) records a failure as an outcome. An answer whose count was cut short or is incomplete is not a source: one that
stores any other error (a failed call, call_error, or a setup error), one with no call record, or one with a call that
has no prompt_tokens. It is listed under excluded with the reason. Scope (Q79, D75: per question, the default): a
question's target is the median input tokens of its own RLM-10 answers (its draws), so each question's pair of
answers reads the same amount. --scope all (one target for every question, the median over every source answer of
the run) is kept only as the alternative D75 did not take; the plan records its scope.

TOP_K. For each question, the smallest top_k (from SINGLE_PASS_TOP_K up, since the arm is single pass given more
passages) whose single-pass prompt has at least the target's input tokens: the prompt is exp1's single_pass_prompt
over SimpleRetriever.retrieve(question, top_k), as the arm builds it, and its tokens are counted by the generator's
own tokenizer (Gemini countTokens for a Gemini generator: a count of the request the runner sends, no generation).
The search doubles top_k from SINGLE_PASS_TOP_K, then bisects; every count it made is kept in probes. It assumes the
count grows with top_k (the passages of top_k are mostly those of top_k - 1 plus one). When every passage of the
collection stays below the target, top_k is the collection size and target_reached is false.
FLOOR (Q81, D75). The floor stays at SINGLE_PASS_TOP_K = 10: D51's arm is single pass given more passages, never
fewer. Where RLM-10 spent less than 10 passages' prompt, the arm still gets 10 and reads more than the target. Such
a question has top_k 10 with planned_tokens above target_tokens, and 9 passages would already reach the target
(the floor, not the target, set top_k): its entry has floor_bound true and the plan lists it under floor_bound,
which plan prints when the plan is written. For each question at top_k 10 above its target, plan counts top_k 9
once more (kept in probes): when count(9) is below the target, 10 is the smallest top_k with no floor at all, and
floor_bound is false. (Above the floor, planned_tokens is also at or above the target, by less than one passage,
since top_k is the smallest that reaches it; that is not the floor binding.)

REACHED. For every (question, draw) answer of the arm: its generation call's prompt_tokens, beside the plan's target
and the planned count. A plan entry never changes after the plan is written; reached goes to its own file.

REPLAN (PA3, D112 Q6, D212). When some of the RLM-10 run's answers are rerun after the plan was written (D89, D90:
G1's five call_error answers), the targets of their questions move, and only theirs. replan plans those questions
again and writes a new plan file; the base plan is never changed. Before anything opens the store it refuses unless,
from the run as it now stands, (1) every named question's target differs from the base plan's, and (2) every other
question's target and sources equal the base plan's (the run changed nowhere else). It then opens the store once, as
plan does, refuses unless the collection, its size (k_max) and the embedding model are the base plan's, and plans
the named questions only, by plan() itself. Before writing it reproduces known numbers: each count at a top_k the
base plan also probed for that question must equal the base plan's count, or nothing is written (the store, the
retriever or the tokenizer is not the one the base plan read). The new plan holds the base plan's entries for every
other question unchanged and the new entries for the named ones; its excluded list is the run's as it now stands,
its floor_bound and no_target are those of the merged entries, and "replan" records the base plan's path, sha256 and
time, the named questions, and each one's target and top_k before and after. --dry-run makes checks (1) and (2) and
prints the new targets; it opens no store and counts nothing.

COUNT DRIFT (D236). With --accept-count-drift <DECISION> [--max-drift <r>, default 0.01], a count that differs from
the base plan's at the same top_k no longer refuses by itself. The replan refuses, before anything is read, unless
experiments/README.md holds "**<DECISION>**" and 0 < r < 1. After counting it refuses and writes nothing unless every
differing count is of a named question and |now - base| / base <= r for each, base being the base plan's count. The
written plan then carries "count_drift": the decision, max_drift, the time it was accepted, and one row per differing
count {question_id, top_k, base, now, relative}; the replan prints each row. Without the option every differing
count refuses, as above, with the same message. --max-drift without --accept-count-drift is refused.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "findings" / "runs"
ANSWERS, CALLS = "answers.jsonl", "calls.jsonl"
SINGLE_PASS_TOP_K = 10            # exp1 SINGLE_PASS_TOP_K: the arm never gets fewer passages than single pass
SCOPES = ("question", "all")
DEFAULT_SCOPE = "question"        # Q79 (D75): the median over the question's own RLM-10 draws
COMPLETE_FAILURES = ("max_turns_empty",)   # Q80 (D75): stored with an error, yet the run's token count is complete
COUNT_API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:countTokens"


def last_answers(run_dir: Path) -> dict:
    """answer_key -> the last answers.jsonl line of that key (the key's answer; earlier lines are failed attempts)."""
    out = {}
    with open(run_dir / ANSWERS, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            out[rec["answer_key"]] = rec
    return out


def answer_inputs(run_dir: Path) -> tuple[dict, list]:
    """({question_id: [source answer]}, excluded). A source answer is {answer_key, draw, ctx_uid, input_tokens,
    n_calls, stop_reason}; excluded lists {answer_key, question_id, reason} for answers that are not sources. An
    answer that stores an error is a source only when its stop_reason is in COMPLETE_FAILURES (Q80, D75)."""
    answers = last_answers(run_dir)
    by_uid = {}
    for key, rec in answers.items():
        by_uid[rec["ctx_uid"]] = key
    sums = {uid: {"input_tokens": 0, "n_calls": 0, "missing": 0} for uid in by_uid}
    with open(run_dir / CALLS, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            s = sums.get(rec.get("ctx_uid"))
            if s is None:
                continue
            s["n_calls"] += 1
            if isinstance(rec.get("prompt_tokens"), int):
                s["input_tokens"] += rec["prompt_tokens"]
            else:
                s["missing"] += 1
    sources, excluded = {}, []
    for uid, key in sorted(by_uid.items(), key=lambda kv: kv[1]):
        rec, s = answers[key], sums[uid]
        qid = rec["question_id"]
        gen = rec.get("generation") or {}
        stop = gen.get("stop_reason") or (gen.get("rlm") or {}).get("stop_reason")
        reason = None
        if gen.get("error") and stop not in COMPLETE_FAILURES:
            reason = f"the answer stores an error and its count was cut short (stop_reason {stop})"
        elif s["n_calls"] == 0:
            reason = "no call record carries the answer's ctx_uid"
        elif s["missing"]:
            reason = f"{s['missing']} of its {s['n_calls']} calls have no prompt_tokens"
        if reason:
            excluded.append({"answer_key": key, "question_id": qid, "reason": reason})
            continue
        sources.setdefault(qid, []).append({"answer_key": key, "draw": rec.get("draw"), "ctx_uid": uid,
                                            "input_tokens": s["input_tokens"], "n_calls": s["n_calls"],
                                            "stop_reason": stop})
    return sources, excluded


def targets(sources: dict, scope: str) -> dict:
    """{question_id: {"target_tokens", "scope", "sources"}}: the median input tokens of the question's sources
    (scope question) or of every source of the run (scope all)."""
    if scope not in SCOPES:
        raise ValueError(f"scope {scope!r}: one of {SCOPES}")
    every = [a["input_tokens"] for qs in sources.values() for a in qs]
    if not every:
        raise ValueError("no RLM-10 answer is a source")
    overall = statistics.median(every)
    out = {}
    for qid, qs in sources.items():
        t = statistics.median([a["input_tokens"] for a in qs]) if scope == "question" else overall
        out[qid] = {"target_tokens": t, "scope": scope,
                    "sources": [{k: a.get(k) for k in ("answer_key", "draw", "input_tokens", "n_calls", "stop_reason")}
                                for a in qs]}
    return out


def choose_top_k(count, target: float, k_min: int, k_max: int) -> dict:
    """The smallest k in [k_min, k_max] with count(k) >= target, by doubling from k_min and then bisecting; count(k)
    is called at most once per k. Returns {top_k, planned_tokens, target_reached, probes}."""
    if not 1 <= k_min <= k_max:
        raise ValueError(f"k_min {k_min}, k_max {k_max}")
    probes = {}

    def c(k):
        if k not in probes:
            probes[k] = count(k)
        return probes[k]

    lo, hi = None, k_min
    while c(hi) < target:
        if hi == k_max:
            return {"top_k": k_max, "planned_tokens": c(k_max), "target_reached": False,
                    "probes": {str(k): v for k, v in sorted(probes.items())}}
        lo, hi = hi, min(2 * hi, k_max)
    if lo is not None:
        while hi - lo > 1:               # c(lo) < target <= c(hi)
            mid = (lo + hi) // 2
            if c(mid) >= target:
                hi = mid
            else:
                lo = mid
    return {"top_k": hi, "planned_tokens": c(hi), "target_reached": True,
            "probes": {str(k): v for k, v in sorted(probes.items())}}


def gemini_counter(model: str):
    """count(prompt): Gemini countTokens over the request the runner's generate sends for a prompt (one user turn,
    gemini_client.generate). A count, not a generation; the key is sent in the header and never printed."""
    from experiments.runner import gemini_client as gc

    def count(prompt: str) -> int:
        body = json.dumps({"contents": [{"role": "user", "parts": [{"text": prompt}]}]}).encode()
        req = urllib.request.Request(COUNT_API.format(model=model), data=body,
                                     headers={"Content-Type": "application/json", "x-goog-api-key": gc._key()})
        with gc._open(req, timeout=120) as r:
            return int(json.loads(r.read())["totalTokens"])
    return count


def plan(rlm_run: Path, scope: str, questions: list, retrieve, prompt_for, count_tokens, k_max: int,
         meta: dict) -> dict:
    """The plan document: per question of `questions` with a target, its top_k and how it was found."""
    sources, excluded = answer_inputs(rlm_run)
    tg = targets(sources, scope)
    entries, no_target = {}, []
    for q in questions:
        qid = q["id"]
        if qid not in tg:
            no_target.append(qid)
            continue

        def count(k, q=q):
            return count_tokens(prompt_for(q["question"], retrieve(q["question"], k)))
        e = {**tg[qid], **choose_top_k(count, tg[qid]["target_tokens"], SINGLE_PASS_TOP_K, k_max)}
        e["floor_bound"] = False                 # Q81 (D75): the floor bound only if fewer passages reach the target
        if e["top_k"] == SINGLE_PASS_TOP_K > 1 and e["planned_tokens"] > e["target_tokens"]:
            below = SINGLE_PASS_TOP_K - 1
            e["probes"] = {**e["probes"], str(below): count(below)}
            e["probes"] = dict(sorted(e["probes"].items(), key=lambda kv: int(kv[0])))
            e["floor_bound"] = e["probes"][str(below)] >= e["target_tokens"]
        entries[qid] = e
    return {"kind": "matched_budget_plan", "decision": "D51, D75 (Q79 to Q81)",
            "made": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "rlm_run": str(rlm_run), "scope": scope, "k_min": SINGLE_PASS_TOP_K, "k_max": k_max, **meta,
            "questions": entries, "floor_bound": floor_bound(entries), "no_target": no_target, "excluded": excluded}


def floor_bound(entries: dict) -> list:
    """The plan's floor_bound list (Q81, D75): one row per floor-bound entry, in the entries' order."""
    return [{"question_id": qid, "target_tokens": e["target_tokens"], "planned_tokens": e["planned_tokens"],
             f"tokens_at_{SINGLE_PASS_TOP_K - 1}": e["probes"][str(SINGLE_PASS_TOP_K - 1)]}
            for qid, e in entries.items() if e["floor_bound"]]


SAME_AS_BASE = ("kind", "scope", "k_min", "k_max", "index", "collection", "embedding_model", "count_method")


def read_ids(path: Path) -> list:
    """The question ids a --questions-file names: a JSON list, or an object whose "ids" is one (the form exp_01's
    --question-ids-file reads, so one file serves both)."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    ids = data.get("ids") if isinstance(data, dict) else data
    if not isinstance(ids, list) or not ids or not all(isinstance(i, str) for i in ids) or len(set(ids)) != len(ids):
        raise ValueError(f"{path}: not a list of distinct question ids")
    return ids


def replan_targets(base: dict, tg: dict, qids: list) -> dict:
    """REPLAN checks (1) and (2), before the store is opened: {question_id: {"target_tokens_before",
    "target_tokens"}} for the named questions. Raises ValueError when the base plan is not per question (scope all
    moves every target), a named question is not in the base plan or has no target now, a named question's target
    did not move, or any other question's target or sources differ from the base plan's."""
    if base.get("kind") != "matched_budget_plan" or base.get("scope") != "question":
        raise ValueError(f"the base plan is {base.get('kind')!r} at scope {base.get('scope')!r}: replan needs a "
                         f"matched-budget plan per question (Q79, D75)")
    entries = base["questions"]
    unknown = [q for q in qids if q not in entries]
    if unknown:
        raise ValueError(f"{unknown} are not questions of the base plan")
    missing = [q for q in qids if q not in tg]
    if missing:
        raise ValueError(f"{missing} have no target in the RLM-10 run as it now stands")
    still = [q for q in qids if tg[q]["target_tokens"] == entries[q]["target_tokens"]]
    if still:
        raise ValueError(f"{still}: target unchanged from the base plan, so nothing to replan")
    if set(tg) - set(qids) != set(entries) - set(qids) - set(base.get("no_target") or []):
        raise ValueError(f"the questions with a target differ from the base plan's beyond the named ones: "
                         f"{sorted((set(tg) ^ set(entries)) - set(qids))[:5]}")
    moved = [q for q in tg if q not in qids and (tg[q]["target_tokens"] != entries[q]["target_tokens"]
                                                  or tg[q]["sources"] != entries[q]["sources"])]
    if moved:
        raise ValueError(f"{len(moved)} questions not named have a target or sources other than the base plan's, "
                         f"first {moved[:3]}: the RLM-10 run changed beyond the named questions")
    return {q: {"target_tokens_before": entries[q]["target_tokens"], "target_tokens": tg[q]["target_tokens"]}
            for q in qids}


def probe_mismatches(base: dict, sub: dict) -> list:
    """For each question of sub, each top_k both plans probed whose count differs: [(question_id, top_k, base count,
    new count)]. Empty when the new counts reproduce the base plan's."""
    out = []
    for qid, e in sub["questions"].items():
        old = base["questions"][qid]["probes"]
        out += [(qid, int(k), old[k], v) for k, v in e["probes"].items() if k in old and old[k] != v]
    return sorted(out)


DECISIONS = ROOT / "experiments" / "README.md"
DEFAULT_MAX_DRIFT = 0.01          # D236: "bounded (refused above 1%)"


def check_drift_decision(decision: str, max_drift: float, readme: Path = DECISIONS) -> None:
    """COUNT DRIFT: raises ValueError unless readme holds "**<decision>**" and 0 < max_drift < 1."""
    if not decision or "*" in decision:
        raise ValueError(f"--accept-count-drift {decision!r}: name a decision, for example D236")
    if not readme.is_file() or f"**{decision}**" not in readme.read_text(encoding="utf-8"):
        raise ValueError(f"{readme} holds no \"**{decision}**\": a count drift is accepted only under a recorded decision")
    if not 0 < max_drift < 1:
        raise ValueError(f"--max-drift {max_drift}: a relative bound above 0 and below 1")


def _drift_text(r: dict) -> str:
    rel = "base 0" if r["relative"] is None else f"{r['relative']:.4%}"
    return f"{r['question_id']} top_k {r['top_k']} {r['base']} -> {r['now']} ({rel})"


def accept_drift(bad: list, named, decision: str, max_drift: float) -> dict:
    """COUNT DRIFT: the plan's count_drift record for the mismatches of probe_mismatches(). Raises ValueError when one
    is of a question not named, or differs from the base count by more than max_drift relative to it."""
    rows = [{"question_id": q, "top_k": k, "base": old, "now": new, "relative": abs(new - old) / old if old else None}
            for q, k, old, new in bad]
    other = sorted({r["question_id"] for r in rows if r["question_id"] not in named})
    if other:
        raise ValueError(f"counts of {other} differ, and only a named question's count drift can be accepted")
    over = [r for r in rows if r["relative"] is None or r["relative"] > max_drift]
    if over:
        raise ValueError(f"{len(over)} of {len(rows)} differing counts exceed the bound {max_drift} relative to the "
                         f"base plan's count: " + ", ".join(_drift_text(r) for r in over))
    return {"decision": decision, "max_drift": max_drift, "relative_to": "the base plan's count at the same top_k",
            "accepted": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "differences": [{**r, "relative": round(r["relative"], 6)} for r in rows]}


def merge_plan(base: dict, base_path: str, base_sha256: str, sub: dict, changed: dict) -> dict:
    """The new plan: the base plan's document with sub's entries (plan() over the named questions) in place of the
    base entries of those questions, in the base plan's question order; made, rlm_run and excluded from sub (the run
    as it now stands); floor_bound and no_target of the merged entries; and "replan". Raises ValueError when sub
    differs from the base plan in a setting of SAME_AS_BASE or holds a question that is not named."""
    differ = [k for k in SAME_AS_BASE if sub.get(k) != base.get(k)]
    if differ:
        raise ValueError(f"the new plan's {differ} differ from the base plan's: "
                         f"{[(k, base.get(k), sub.get(k)) for k in differ]}")
    if set(sub["questions"]) != set(changed):
        raise ValueError(f"planned {sorted(sub['questions'])}, named {sorted(changed)}")
    entries = {q: (sub["questions"][q] if q in changed else e) for q, e in base["questions"].items()}
    doc = {**base, "made": sub["made"], "rlm_run": sub["rlm_run"], "questions": entries,
           "floor_bound": floor_bound(entries),
           "no_target": [q for q in base.get("no_target") or [] if q not in changed] + sub["no_target"],
           "excluded": sub["excluded"]}
    doc["replan"] = {"decision": "PA3 (D112 Q6, D212)", "base_plan": base_path, "base_sha256": base_sha256,
                     "base_made": base.get("made"), "base_rlm_run": base.get("rlm_run"), "questions": list(changed),
                     "changed": {q: {**c, "top_k_before": base["questions"][q]["top_k"],
                                     "top_k": sub["questions"][q]["top_k"],
                                     "planned_tokens_before": base["questions"][q]["planned_tokens"],
                                     "planned_tokens": sub["questions"][q]["planned_tokens"]}
                                 for q, c in changed.items()}}
    return doc


def reached(plan_doc: dict, arm_run: Path) -> dict:
    """Per arm answer: the plan's target and planned tokens beside the prompt_tokens its generation call reached."""
    answers = last_answers(arm_run)
    want = {rec["ctx_uid"]: key for key, rec in answers.items()}
    got = {}
    with open(arm_run / CALLS, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            if rec.get("ctx_uid") in want:
                got.setdefault(rec["ctx_uid"], []).append(rec)
    rows = []
    for uid, key in sorted(want.items(), key=lambda kv: kv[1]):
        rec = answers[key]
        entry = plan_doc["questions"].get(rec["question_id"], {})
        calls = got.get(uid, [])
        row = {"answer_key": key, "question_id": rec["question_id"], "draw": rec.get("draw"),
               "top_k": (rec.get("generation") or {}).get("top_k"), "planned_top_k": entry.get("top_k"),
               "target_tokens": entry.get("target_tokens"), "planned_tokens": entry.get("planned_tokens"),
               "reached_tokens": None, "error": (rec.get("generation") or {}).get("error"), "n_calls": len(calls)}
        if len(calls) == 1 and isinstance(calls[0].get("prompt_tokens"), int):
            row["reached_tokens"] = calls[0]["prompt_tokens"]
        rows.append(row)
    return {"kind": "matched_budget_reached", "plan_made": plan_doc.get("made"), "arm_run": str(arm_run),
            "answers": rows}


def _write(doc: dict, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        raise SystemExit(f"{out} exists; a plan is written once")
    out.write_text(json.dumps(doc, indent=1, ensure_ascii=True, allow_nan=False) + "\n", encoding="utf-8")
    print(f"wrote {out} (sha256 {hashlib.sha256(out.read_bytes()).hexdigest()[:12]})")


def replan_main(a) -> None:
    """The replan command (REPLAN in the header): checks, then (without --dry-run) one store open, the named
    questions planned, the base plan's counts reproduced, the merged plan written once."""
    if a.out.exists():
        raise SystemExit(f"{a.out} exists; a plan is written once")
    drift = getattr(a, "accept_count_drift", None)
    max_drift = getattr(a, "max_drift", None)
    if drift is None and max_drift is not None:
        raise SystemExit("replan refused: --max-drift needs --accept-count-drift <decision>; nothing written")
    if drift is not None:
        max_drift = DEFAULT_MAX_DRIFT if max_drift is None else max_drift
        try:
            check_drift_decision(drift, max_drift)
        except ValueError as e:
            raise SystemExit(f"replan refused: {e}; nothing written")
    raw = a.base_plan.read_bytes()
    base, base_sha = json.loads(raw), hashlib.sha256(raw).hexdigest()
    try:
        qids = read_ids(a.questions_file)
        sources, excluded = answer_inputs(a.rlm_dir)
        changed = replan_targets(base, targets(sources, "question"), qids)
    except ValueError as e:
        raise SystemExit(f"replan refused: {e}; nothing written")
    print(f"base plan {a.base_plan} (sha256 {base_sha}), made {base.get('made')}; RLM-10 run {a.rlm_dir}: "
          f"{sum(len(v) for v in sources.values())} sources, {len(excluded)} excluded")
    for q, c in changed.items():
        print(f"  {q}: target {c['target_tokens_before']} -> {c['target_tokens']} (base top_k "
              f"{base['questions'][q]['top_k']})")
    print(f"the other {len(base['questions']) - len(changed)} questions: target and sources as in the base plan")
    if drift is not None:
        print(f"count drift: accepted under {drift} for the named questions, each at most {max_drift} relative to the "
              f"base plan's count at the same top_k, each recorded in the plan's count_drift")
    if a.dry_run:
        print("dry run: no store opened, nothing counted, nothing written")
        return

    prefix = "gemini countTokens, "
    if not str(base.get("count_method", "")).startswith(prefix):
        raise SystemExit(f"replan refused: the base plan's count method {base.get('count_method')!r} is not "
                         f"{prefix}<model>; nothing written")
    model = base["count_method"][len(prefix):]
    sys.path.insert(0, str(ROOT / "experiments" / "mentori"))
    from experiments.runner import experiment as ex
    from tests.experiments_v4.exp_common import find_admin_user_id, setup_retriever
    from tests.experiments.exp1_rlm_vs_singlepass import single_pass_prompt

    user_id = find_admin_user_id()
    retriever, collection, embedding_model = setup_retriever(user_id, base["index"])
    k_max = retriever.vector_store.count(collection)
    meta = {"index": base["index"], "collection": collection, "embedding_model": embedding_model,
            "count_method": f"{prefix}{model}"}
    if (collection, embedding_model, k_max) != (base.get("collection"), base.get("embedding_model"), base.get("k_max")):
        raise SystemExit(f"replan refused: the store gives collection {collection}, {embedding_model}, {k_max} "
                         f"passages; the base plan read {base.get('collection')}, {base.get('embedding_model')}, "
                         f"{base.get('k_max')}; nothing written")

    def retrieve(question, k):
        return retriever.retrieve(query=question, top_k=k, collection_name=collection)

    sub = plan(a.rlm_dir, "question", [q for q in ex.questions() if q["id"] in changed], retrieve,
               single_pass_prompt, gemini_counter(model), k_max, meta)
    finish_replan(base, str(a.base_plan), base_sha, sub, changed, a.out, drift, max_drift)


def finish_replan(base: dict, base_path: str, base_sha: str, sub: dict, changed: dict, out: Path,
                  drift: str | None = None, max_drift: float | None = None) -> None:
    """replan after counting: the base plan's counts reproduced (or, under --accept-count-drift, each difference
    accepted within max_drift and recorded), the merged plan checked and written once, the summary printed."""
    bad = probe_mismatches(base, sub)
    record = None
    if bad:
        for q, k, old, new in bad:
            print(f"  {q} top_k {k}: base plan {old}, now {new}")
        if drift is None:
            raise SystemExit(f"replan refused: {len(bad)} counts differ from the base plan's at the same top_k, so "
                             f"this store, retriever or tokenizer is not the one the base plan read; nothing written")
    if drift is not None:
        try:
            record = accept_drift(bad, changed, drift, max_drift)
        except ValueError as e:
            raise SystemExit(f"replan refused: {e}; nothing written")
    try:
        doc = merge_plan(base, base_path, base_sha, sub, changed)
    except ValueError as e:
        raise SystemExit(f"replan refused: {e}; nothing written")
    kept = [q for q in base["questions"] if q not in changed and doc["questions"][q] != base["questions"][q]]
    if kept:
        raise SystemExit(f"replan refused: {kept[:3]} differ from the base plan's entries; nothing written")
    if record is not None:
        doc["count_drift"] = record
    _write(doc, out)
    shared = sum(len(set(sub["questions"][q]["probes"]) & set(base["questions"][q]["probes"])) for q in changed)
    if record is None:
        print(f"reproduced: {shared} counts at a top_k the base plan also probed, each equal")
    else:
        print(f"reproduced: {shared - len(bad)} of {shared} counts at a top_k the base plan also probed equal; "
              f"{len(bad)} differ, accepted under {drift} (at most {max_drift} relative) and recorded in count_drift:")
        for r in record["differences"]:
            print(f"  {_drift_text(r)}")
    for q, c in doc["replan"]["changed"].items():
        print(f"  {q}: target {c['target_tokens_before']} -> {c['target_tokens']}, top_k {c['top_k_before']} -> "
              f"{c['top_k']}, planned {c['planned_tokens_before']} -> {c['planned_tokens']}")
    print(f"excluded answers (Q80): {len(doc['excluded'])}; floor bound: {len(doc['floor_bound'])}")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--rlm-run", required=True, help="the RLM-10 run_id under findings/runs/")
    p.add_argument("--scope", default=DEFAULT_SCOPE, choices=SCOPES,
                   help="median over the question's own answers (Q79, D75: the default) or over all")
    p.add_argument("--index", default="exp_v4_s20_n0")
    p.add_argument("--model", default="gemini-3-flash-preview", help="the generator whose tokenizer counts")
    p.add_argument("--out", required=True, type=Path)
    r = sub.add_parser("reached")
    r.add_argument("--plan", required=True, type=Path)
    r.add_argument("--arm-run", required=True)
    r.add_argument("--out", required=True, type=Path)
    s = sub.add_parser("replan", help="PA3: plan the named questions again, every other entry from the base plan")
    s.add_argument("--base-plan", required=True, type=Path, help="the plan the arm ran under")
    s.add_argument("--rlm-dir", required=True, type=Path, help="the RLM-10 run folder as it now stands")
    s.add_argument("--questions-file", required=True, type=Path, help="JSON list of ids, or {\"ids\": [...]}")
    s.add_argument("--out", required=True, type=Path)
    s.add_argument("--dry-run", action="store_true", help="checks (1) and (2) only: no store, no count")
    s.add_argument("--accept-count-drift", metavar="DECISION", default=None,
                   help="COUNT DRIFT (D236): accept counts that differ from the base plan's, for the named questions "
                        "only, each within --max-drift; DECISION must appear as **DECISION** in experiments/README.md")
    s.add_argument("--max-drift", type=float, default=None,
                   help=f"relative bound on each accepted difference (default {DEFAULT_MAX_DRIFT})")
    a = ap.parse_args(argv)

    if a.cmd == "reached":
        _write(reached(json.loads(a.plan.read_text()), RUNS / a.arm_run), a.out)
        return
    if a.cmd == "replan":
        replan_main(a)
        return

    sys.path.insert(0, str(ROOT / "experiments" / "mentori"))
    from experiments.runner import experiment as ex
    from tests.experiments_v4.exp_common import find_admin_user_id, setup_retriever
    from tests.experiments.exp1_rlm_vs_singlepass import single_pass_prompt

    user_id = find_admin_user_id()
    retriever, collection, embedding_model = setup_retriever(user_id, a.index)
    k_max = retriever.vector_store.count(collection)

    def retrieve(question, k):
        return retriever.retrieve(query=question, top_k=k, collection_name=collection)

    doc = plan(RUNS / a.rlm_run, a.scope, ex.questions(), retrieve, single_pass_prompt, gemini_counter(a.model),
               k_max, {"index": a.index, "collection": collection, "embedding_model": embedding_model,
                       "count_method": f"gemini countTokens, {a.model}"})
    _write(doc, a.out)
    print(f"floor bound (Q81: top_k {SINGLE_PASS_TOP_K}, and {SINGLE_PASS_TOP_K - 1} passages already reach the target): "
          f"{len(doc['floor_bound'])} of {len(doc['questions'])} questions")
    for f in doc["floor_bound"]:
        print(f"  {f['question_id']}: target {f['target_tokens']}, planned {f['planned_tokens']}, "
              f"at {SINGLE_PASS_TOP_K - 1} passages {f[f'tokens_at_{SINGLE_PASS_TOP_K - 1}']}")
    print(f"excluded answers (Q80): {len(doc['excluded'])}; questions with no target: {len(doc['no_target'])}")


if __name__ == "__main__":
    main()
