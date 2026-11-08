#!/usr/bin/env python3
"""g13_merge (D236, D237): the matched-budget arm as it now stands, G2's 390 answers plus G13's 15, and the 15 judge
rows of G13 in place of G2's 15. One place for every reader (S511, Figure 3 through S463, Supplementary Figure 6
through S457).

WHY. G2's plan sized five questions (findings/recompute/G13_runs/pa3_questions.json) to RLM-10 answers that were
stored again on 18 October, so their 15 matched-budget answers were planned from an out-of-date token target. G13
replanned those five and answered them again on gemini-3-flash-preview (G13_runs/README.md, D236 and D237 sections).
The 15 answers went to G13's own sink, with G2's run id and answer keys (README.md D1), and were judged once on key
v2.5 by S512's whole-key scope, plain call only (s3_guard.py SETS["S6WG13"]). This module puts them in place of G2's
15 and refuses anything else.

INPUTS, copied once from the Studio (via the laptop's ~/g13_from_studio/), each checked against
findings/recompute/G13_runs/inputs/SHA256SUMS before it is read:
  runs/exp_01__matched_budget__exp_v4_s20_n0/answers.jsonl   the G13 sink's 15 answer lines (and its calls,
                                                              retrievals and identity files beside it)
  s6wg13_collect.jsonl                                       s3_guard collect of set S6WG13: 15 judge rows, one
                                                              run_sha256 d61f720a01d7
The collect came without its out folder, so its headers (and the run_sha256 recomputed from them) cannot be checked
here as judge_rows_v25.check_v25 checks an S6 out; the rows are checked field by field instead (g13_rows).
The plan the 15 were answered under (sha256 NEW_PLAN_SHA, named by every one of the 15 lines) is on the Studio only;
merged_check uses it when given and says so when not.

    merge_answers(g2_last)   {answer_key: record} of G2 (405, its last line per key) -> the same with the 15 replaced.
                             Refuses unless G13's keys are exactly the five questions at draws 1 to 3, each one of G2's
                             keys, G2's 15 were made under G2's plan (BASE_PLAN_SHA) and G13's under NEW_PLAN_SHA, and
                             every other key is G2's record unchanged.
    g13_rows()               {judge ident: row} for the 15 (judge_passages.ident's (run_id, config, question, draw)).
    replace_rows(choice)     a judge_rows_v25.choose result for G2 -> the same with exactly the 15 entries replaced by
                             G13's rows (status "v2.5", source "S6WG13"); refuses unless the 15 are in it, nothing else
                             changes, and each row agrees with its G13 answer (answer key, passages read).
                             A judge row is bound to its answer by answer key plus passage count only (g13_rows): its
                             item_sha256 is not recomputed, because the G13 store it hashes is on the Studio.
    merged_check(...)        the "merged" check owed by G13_runs/README.md: 405 keys, each top_k equal to its plan entry.

    uv run --frozen python scripts/g13_merge_test.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "scripts"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

G13 = ROOT / "findings" / "recompute" / "G13_runs"
INPUTS = G13 / "inputs"
RUN_ID = "exp_01__matched_budget__exp_v4_s20_n0"
CONFIG = "matched_budget"
INDEX = "exp_v4_s20_n0"
DRAWS = (1, 2, 3)
ANSWERS = INPUTS / "runs" / RUN_ID / "answers.jsonl"
COLLECT = INPUTS / "s6wg13_collect.jsonl"
ANSWERS_SHA = "5cb3ac4eaab59be3e16d27e76f0a983cbcdee997b00e86355951d50ac365e9b7"
COLLECT_SHA = "09d5e5bd359d35c78e2ea0c931d5797de6ca845be342e915fa2da0da579b4336"
RUN_SHA = "d61f720a01d74d3fe012fc8eedef0f461a4a77339affacc0c7ccd01e43c4f2b0"     # the collect's one run_sha256
BASE_PLAN_SHA = "3dc2d9f506dc9376cca4be9bbfaad9380e36181e82d93b858cc9fa79dca9a331"  # G2's plan (g13_check.py)
NEW_PLAN_SHA = "cd8385afae8af982aa9c1ec0c5fae0fd0c263305e8f5f0fab5baf376edccb9dc"   # named by each of G13's 15 lines
SOURCE = "S6WG13"
SCOPE = "whole:g13"


class Refused(Exception):
    def __init__(self, code: str, msg: str):
        super().__init__(f"REFUSED [{code}]: {msg}")
        self.code = code


def sha256_file(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def ids() -> list[str]:
    return list(json.loads((G13 / "pa3_questions.json").read_text())["ids"])


def keys() -> set[str]:
    return {f"{INDEX}|{CONFIG}|{q}|d{d}" for q in ids() for d in DRAWS}


def check_sums() -> dict:
    """Every file SHA256SUMS lists has its sha256; returns {path relative to the repository: sha256}."""
    out = {}
    lines = [x for x in (INPUTS / "SHA256SUMS").read_text().splitlines() if x.strip()]
    for ln in lines:
        h, name = ln.split(None, 1)
        p = INPUTS / name.strip().removeprefix("./")
        if sha256_file(p) != h:
            raise Refused("sums", f"{p.relative_to(ROOT)} is not the file SHA256SUMS records ({h[:12]})")
        out[str(p.relative_to(ROOT))] = h
    out[str((INPUTS / "SHA256SUMS").relative_to(ROOT))] = sha256_file(INPUTS / "SHA256SUMS")
    return out


def _pinned(p: Path, want: str) -> None:
    got = sha256_file(p)
    if got != want:
        raise Refused("pin", f"{p} sha256 {got[:12]}, not {want[:12]}")


def last_lines(p: Path) -> dict:
    out = {}
    for raw in Path(p).read_text().splitlines():
        if raw.strip():
            r = json.loads(raw)
            out[r["answer_key"]] = r
    return out


def g13_answers(path: Path = ANSWERS, want_sha: str | None = ANSWERS_SHA) -> dict:
    """{answer_key: record} of G13's sink: exactly the 15 keys, one line each, G2's run id, under NEW_PLAN_SHA with the
    entry's top_k, no generation error."""
    if want_sha is not None:
        _pinned(Path(path), want_sha)
    lines = [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]
    got = {}
    for r in lines:
        k = r["answer_key"]
        if k in got:
            raise Refused("twice", f"G13 answer {k} found twice (a resume without --skip-failed?)")
        got[k] = r
    want = keys()
    if set(got) != want:
        raise Refused("keys", f"G13's keys are not the five questions at draws 1 to 3: {len(set(got) - want)} extra, "
                              f"{len(want - set(got))} missing")
    for k, r in got.items():
        g, mb = r.get("generation") or {}, (r.get("generation") or {}).get("matched_budget") or {}
        if r.get("run_id") != RUN_ID or r.get("config") != CONFIG:
            raise Refused("run", f"{k}: run {r.get('run_id')!r}, config {r.get('config')!r}")
        if mb.get("plan_sha256") != NEW_PLAN_SHA:
            raise Refused("plan", f"{k}: made under plan {str(mb.get('plan_sha256'))[:12]}, not G13's {NEW_PLAN_SHA[:12]}")
        if g.get("top_k") != mb.get("top_k"):
            raise Refused("top_k", f"{k}: top_k {g.get('top_k')}, its plan entry's {mb.get('top_k')}")
        if g.get("error"):
            raise Refused("error", f"{k}: a generation error ({str(g['error'])[:80]})")
    return got


def merge_answers(g2_last: dict, g13: dict | None = None) -> tuple[dict, dict]:
    """(merged {answer_key: record}, report). g2_last: G2's last line per key (405). Refuses unless G13's 15 keys
    replace exactly 15 of G2's keys made under G2's plan, and every other key is G2's own record."""
    g13 = g13_answers() if g13 is None else g13
    if len(g2_last) != 405:
        raise Refused("g2_keys", f"G2 holds {len(g2_last)} keys, not 405")
    if set(g13) != keys():
        raise Refused("keys", "G13's answers are not the 15 keys")
    missing = sorted(set(g13) - set(g2_last))
    if missing:
        raise Refused("not_g2", f"{len(missing)} G13 keys are not G2 keys, first {missing[0]}")
    stale_plans = {k: ((g2_last[k].get("generation") or {}).get("matched_budget") or {}).get("plan_sha256")
                   for k in g13}
    if set(stale_plans.values()) != {BASE_PLAN_SHA}:
        raise Refused("g2_plan", f"G2's 15 to be replaced are not all under G2's plan: {set(stale_plans.values())}")
    kept_plans = {((r.get("generation") or {}).get("matched_budget") or {}).get("plan_sha256")
                  for k, r in g2_last.items() if k not in g13}
    if kept_plans != {BASE_PLAN_SHA}:
        raise Refused("g2_plan", f"G2's other 390 are not all under G2's plan: {kept_plans}")
    merged = {k: (g13[k] if k in g13 else r) for k, r in g2_last.items()}
    replaced = sorted(k for k in merged if merged[k] is not g2_last[k])
    same = sum(1 for k in merged if merged[k] is g2_last[k])
    if len(replaced) != 15 or same != 390 or set(replaced) != set(g13):
        raise Refused("merge", f"{len(replaced)} replaced, {same} kept; want 15 and 390")
    return merged, {"keys": len(merged), "replaced": len(replaced), "kept": same, "replaced_keys": replaced,
                    "g2_plan_sha256": BASE_PLAN_SHA, "g13_plan_sha256": NEW_PLAN_SHA,
                    "g13_answers": str(ANSWERS.relative_to(ROOT)), "g13_answers_sha256": ANSWERS_SHA}


S455_SCAN = G13 / "S455_g13_scan.json"   # uv run --frozen python scripts/S455_d89_affected_answers.py --stdout <the run>


def s455_clean() -> dict:
    """The S455 scan of G13's sink for the D89, D90 and D92 Gemini cases (S457's "checked by S455" for these 15): it read
    the calls.jsonl SHA256SUMS records and lists no affected answer, none D90 leaves raising and no still-raising call."""
    j = json.loads(S455_SCAN.read_text())
    calls = str((ANSWERS.parent / "calls.jsonl").relative_to(ROOT))
    want = check_sums()[calls]
    read = {i["path"]: i["sha256"] for i in j["provenance"]["inputs"]}
    if read != {calls: want}:
        raise Refused("s455", f"{S455_SCAN.name} read {read}, not G13's calls.jsonl {want[:12]}")
    if j.get("gate") != "pass" or j.get("rows") or j["not_d90"]["answers"] or j["still_raising"]["calls"]:
        raise Refused("s455", f"{S455_SCAN.name}: gate {j.get('gate')}, {len(j.get('rows') or [])} affected answers")
    return {"scan": str(S455_SCAN.relative_to(ROOT)), "scan_sha256": sha256_file(S455_SCAN), "calls_sha256": want,
            "affected": 0}


def g13_reached(answers: dict | None = None) -> list[dict]:
    """matched_budget.reached's rows for the 15 (the prompt tokens their one generation call reached, from the sink's
    calls.jsonl), against the entry each line records (the new plan itself is not here; merged_check)."""
    from experiments.runner import matched_budget as mbm
    answers = g13_answers() if answers is None else answers
    entries = {}
    for r in answers.values():
        mb = r["generation"]["matched_budget"]
        e = {"top_k": mb["top_k"], "target_tokens": mb["target_tokens"], "planned_tokens": mb["planned_tokens"]}
        if entries.setdefault(r["question_id"], e) != e:
            raise Refused("entry", f"{r['question_id']}: its draws record different plan entries")
    rows = mbm.reached({"questions": entries, "made": None}, ANSWERS.parent)["answers"]
    if sorted(x["answer_key"] for x in rows) != sorted(keys()):
        raise Refused("reached", "reached rows are not the 15 keys")
    return rows


def g13_rows(path: Path = COLLECT, want_sha: str | None = COLLECT_SHA, answers: dict | None = None) -> dict:
    """{judge ident: row} of the S6WG13 collect, each row checked: one run_sha256 (RUN_SHA), key v2.5 with S512's
    key_hash, the whole:g13 scope, a lock equal to D88's, the main judge, the prompt key v2.5's answerable flag gives,
    plain call (a) ok or a recorded judge failure, and the answer key and passages of its G13 answer. A row is bound to
    its answer by answer key plus passage count only: its item_sha256 is not recomputed, because the G13 store it
    hashes is on the Studio."""
    import S512_s6_rejudge_v25 as S512
    from experiments.scorers import judge_passages as JP
    LOCKS_OK = __import__("lock_equiv").EQUIVALENT
    if want_sha is not None:
        _pinned(Path(path), want_sha)
    answers = g13_answers() if answers is None else answers
    rows = {}
    for raw in Path(path).read_text().splitlines():
        if not raw.strip():
            continue
        d = json.loads(raw)
        k = JP.ident(d)
        if k in rows:
            raise Refused("collect_dup", f"row {k} twice")
        rows[k] = d
    if len(rows) != 15:
        raise Refused("rows", f"{len(rows)} rows, not 15")
    _, k25 = S512.keys()
    v2 = S512.v2_records()
    for k, d in rows.items():
        a = answers.get(d.get("answer_key"))
        if a is None or (a["run_id"], a["config"], a["question_id"], a["draw"]) != k:
            raise Refused("row_answer", f"{k}: no G13 answer with answer key {d.get('answer_key')!r}")
        if d.get("run_sha256") != RUN_SHA:
            raise Refused("run_sha", f"{k}: run_sha256 {str(d.get('run_sha256'))[:12]}, not {RUN_SHA[:12]}")
        if d.get("key_version") != S512.KEY_VERSION or d.get("questions") != SCOPE:
            raise Refused("scope", f"{k}: key_version {d.get('key_version')!r}, questions {d.get('questions')!r}")
        if d.get("key_hash") != S512.key_hash25(k[2], v2):
            raise Refused("key_hash", f"{k}: key_hash {d.get('key_hash')}, not S512.key_hash25")
        if bool(d.get("answerable_prompt")) != (k25[k[2]]["answerable"] in (True, "true", "True")):
            raise Refused("prompt", f"{k}: answerable_prompt {d.get('answerable_prompt')}, key v2.5 says otherwise")
        if d.get("lock_sha256") not in LOCKS_OK:
            raise Refused("lock", f"{k}: lock {str(d.get('lock_sha256'))[:8]}")
        if d.get("judge") is not None:
            raise Refused("second_judge", f"{k}: a second-judge row")
        # the row is bound to its answer by answer key (above) plus passage count (here) only; item_sha256 is not
        # recomputed, because the G13 store it hashes is on the Studio
        if d.get("n_passages") != len((a.get("generation") or {}).get("passages") or []):
            raise Refused("passages", f"{k}: the row read {d.get('n_passages')} passages, the answer "
                                      f"{len(a['generation'].get('passages') or [])}")
        if (d.get("a") or {}).get("status") is None:
            raise Refused("status", f"{k}: plain call (a) has no status")
    return rows


def replace_rows(choice: dict, rows: dict | None = None) -> tuple[dict, dict]:
    """(choice with the 15 replaced, report). choice: judge_rows_v25.choose's result over G2's 405 answers (its
    "_sources" entry kept). Refuses unless every one of the 15 idents is in choice and is the only thing changed."""
    rows = g13_rows() if rows is None else rows
    items = {k: v for k, v in choice.items() if k != "_sources"}
    if len(items) != 405:
        raise Refused("choice", f"the choice holds {len(items)} answers, not 405")
    missing = [k for k in rows if k not in items]
    if missing:
        raise Refused("choice", f"{len(missing)} G13 rows are not answers of the choice, first {missing[0]}")
    out = dict(choice)
    before = {}
    for k, d in rows.items():
        old = items[k]
        before[k] = {"status": old["status"], "source": old["source"]}
        out[k] = {**old, "status": "v2.5", "source": SOURCE, "row": d}
    changed = [k for k in out if k != "_sources" and out[k] is not choice.get(k)]
    if sorted(changed) != sorted(rows) or len(changed) != 15:
        raise Refused("replace", f"{len(changed)} entries changed, not the 15")
    out["_sources"] = {**choice.get("_sources", {}),
                       SOURCE: {"kind": "v2.5 whole", "run_sha256": RUN_SHA, "rows": len(rows)}}
    sources_before = {}
    for v in before.values():
        sources_before[f"{v['source']} ({v['status']})"] = sources_before.get(f"{v['source']} ({v['status']})", 0) + 1
    return out, {"replaced": len(rows), "source": SOURCE, "run_sha256": RUN_SHA,
                 "collect": str(COLLECT.relative_to(ROOT)), "collect_sha256": COLLECT_SHA,
                 "replaced_rows_were": sources_before}


def merged_check(g2_answers: Path, g2_plan: Path, new_plan: Path | None = None) -> dict:
    """G13_runs/README.md's owed "merged" check: G2's 390 plus the 15 give 405 keys, each answer's top_k equal to its
    plan entry. With new_plan (sha256 NEW_PLAN_SHA): every key's top_k equals the new plan's entry, and the new plan's
    entries outside the five equal G2's plan's. Without it: the 390 against G2's plan and the 15 against the entry each
    line records (top_k, target and planned tokens), all 15 naming NEW_PLAN_SHA; "new_plan": "not available"."""
    _pinned(Path(g2_plan), BASE_PLAN_SHA)
    base = json.loads(Path(g2_plan).read_text())["questions"]
    merged, rep = merge_answers(last_lines(g2_answers))
    g13 = set(rep["replaced_keys"])
    bad = []
    for k, r in merged.items():
        g = r.get("generation") or {}
        q = r["question_id"]
        if k not in g13 and g.get("top_k") != base[q]["top_k"]:
            bad.append(f"{k}: top_k {g.get('top_k')}, G2's plan {base[q]['top_k']}")
    for k in g13:
        mb = merged[k]["generation"]["matched_budget"]
        if base[merged[k]["question_id"]]["top_k"] == mb["top_k"]:
            bad.append(f"{k}: top_k {mb['top_k']} as in G2's plan, though its target moved")
    out = {"keys": len(merged), "replaced": len(g13), "kept": rep["kept"]}
    if new_plan is not None:
        _pinned(Path(new_plan), NEW_PLAN_SHA)
        new = json.loads(Path(new_plan).read_text())["questions"]
        for k, r in merged.items():
            q = r["question_id"]
            if r["generation"].get("top_k") != new[q]["top_k"]:
                bad.append(f"{k}: top_k {r['generation'].get('top_k')}, the new plan {new[q]['top_k']}")
        other = [q for q in base if q not in ids() and new.get(q) != base[q]]
        if other or set(new) != set(base):
            bad.append(f"{len(other)} entries of the new plan outside the five differ from G2's")
        out["new_plan"] = str(new_plan)
    else:
        for k in g13:
            mb = merged[k]["generation"]["matched_budget"]
            if not (isinstance(mb.get("planned_tokens"), int) and isinstance(mb.get("target_tokens"), int)):
                bad.append(f"{k}: no planned or target tokens in its matched_budget record")
        per_q = {}
        for k in g13:
            r = merged[k]
            per_q.setdefault(r["question_id"], set()).add(r["generation"]["top_k"])
        bad += [f"{q}: its three draws used top_k {sorted(v)}" for q, v in per_q.items() if len(v) != 1]
        out["new_plan"] = (f"not available locally (sha256 {NEW_PLAN_SHA[:12]}, on the Studio): the 15 were checked "
                           f"against the entry each line records, and each question's three draws share one top_k")
        out["g13_top_k"] = {q: sorted(v)[0] for q, v in sorted(per_q.items())}
    if bad:
        raise Refused("merged", f"{len(bad)} problems, first {bad[:3]}")
    return out
