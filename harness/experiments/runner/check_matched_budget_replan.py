"""Checks for matched_budget.py replan (PA3, G13). Offline: no store is opened, no token is counted by Gemini, no
model is called. The inputs are the frozen copies the figure scripts read (scripts/fig_repro.py frozen(), each file
checked against its committed member list): G2's plan (s457_mirror_20261022.tar), and G1's RLM-10 answers before
(k1_inputs_runs.tar) and after (fig2_g1r15_inputs.tar) the D89/D90 rerun of 18 Oct. Neither copy holds calls.jsonl,
so each test run folder gets one built from the answers' own per-call records (generation.calls, each with its
prompt_tokens and the answer's ctx_uid), which test 1 shows is the reading the plan was made from.

    uv run --frozen python -m experiments.runner.check_matched_budget_replan

1. Known numbers first: from the pre-rerun answers, answer_inputs() and targets() give the base plan exactly: 400
   sources, 5 excluded (the five call_error answers), and each of the 135 questions' target and sources equal to
   the plan's entry.
2. After the rerun: 405 sources, 0 excluded; replan_targets() for the five gives their targets before (the base
   plan's) and after (EXPECT_TARGETS, as findings/recompute/G13_runs/g13_check.py has them); every other question
   unchanged.
3. Refusals of replan_targets(): one of the five left out (its target moved, unnamed); a sixth question whose target
   did not move named; an unknown id; a base plan at scope all; another question's source changed.
4. plan() over the five with a stand-in count (the base plan's own probes, linear between them) and merge_plan():
   probe_mismatches() finds none; the merged plan equals the base plan on the other 130 entries (as JSON) and on its
   settings; each of the five has a new top_k inside the interval the base plan's probes give, none equal to the
   base's; excluded is empty; floor_bound and the replan record are as stated.
5. A count one token off at top_k 10 is found for all five (probe_mismatches); merge_plan() refuses a plan of
   another collection, and a plan of a question not named.
6. The CLI: replan --dry-run prints the five and writes nothing; an existing --out is refused before anything is
   read; the questions file is the one exp_01's --question-ids-file reads ({"ids": [...]}).
7. After counting (finish_replan) and COUNT DRIFT (D236), on stand-in counts with drift applied: no option, the
   refusal text unchanged and nothing written; --accept-count-drift D236 within 1%, written with count_drift and its
   rows; the ten differences found on ~/paper_store_g13b refused at 1% (two at top_k 10 exceed it) and written at
   1.5%; a mismatch of a question not named refused; a decision not in the README refused; the CLI's refusals before
   anything is read; --dry-run with the option writes nothing.
"""

from __future__ import annotations

import contextlib
import copy
import io
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from experiments.runner import matched_budget as mb   # noqa: E402
import fig_repro as FR                                # noqa: E402

RLM = "exp_01__rlm_10__exp_v4_s20_n0"
IDS_FILE = ROOT / "findings" / "recompute" / "G13_runs" / "pa3_questions.json"
EXPECT_TARGETS = {"01_sarek_CO2": 55258, "07_salmon_FR1": 27261, "OOD_024": 33892, "OOD_025": 50543,
                  "OOD_035": 44589}
results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (f": {detail}" if detail and not ok else ""))


def raises(fn, exc=Exception):
    try:
        fn()
    except exc as e:
        return e
    return None


def run_folder(answers: Path, dest: Path) -> Path:
    """dest/<RLM>/ with answers.jsonl as frozen and calls.jsonl rebuilt from each answer's generation.calls."""
    d = dest / RLM
    d.mkdir(parents=True)
    lines = answers.read_text(encoding="utf-8").splitlines()
    (d / "answers.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    with open(d / "calls.jsonl", "w", encoding="utf-8") as f:
        for raw in lines:
            r = json.loads(raw)
            for c in (r.get("generation") or {}).get("calls") or []:
                f.write(json.dumps({"ctx_uid": r["ctx_uid"], "prompt_tokens": c.get("prompt_tokens")}) + "\n")
    return d


base_path = FR.frozen("s457_mirror_20261022", "s457_mirror_20261022/matched_budget/g2_runs/g2_matched_budget_plan.json")
base = json.loads(base_path.read_text(encoding="utf-8"))
tmp = Path(tempfile.mkdtemp(prefix="check_mb_replan_"))
before = run_folder(FR.frozen("k1_inputs_runs", f"k1_inputs_runs/{RLM}/answers.jsonl"), tmp / "before")
after = run_folder(FR.frozen("fig2_g1r15_inputs", f"fig2_g1r15_inputs/runs/{RLM}/answers.jsonl"), tmp / "after")
IDS = mb.read_ids(IDS_FILE)

# 1. known numbers
src0, ex0 = mb.answer_inputs(before)
tg0 = mb.targets(src0, "question")
check("1 pre-rerun: 400 sources, 5 excluded, as the base plan", sum(len(v) for v in src0.values()) == 400
      and len(ex0) == 5 and sorted(x["question_id"] for x in ex0) == sorted(IDS)
      and all("call_error" in x["reason"] for x in ex0), [x["answer_key"] for x in ex0])
same = [q for q, e in base["questions"].items()
        if tg0[q]["target_tokens"] == e["target_tokens"] and tg0[q]["sources"] == e["sources"]]
check("1 pre-rerun: all 135 targets and sources equal the base plan's", len(same) == 135 == len(base["questions"]),
      len(same))
check("1 the base plan's excluded list is the same five keys",
      sorted(x["answer_key"] for x in base["excluded"]) == sorted(x["answer_key"] for x in ex0))

# 2. after the rerun
src1, ex1 = mb.answer_inputs(after)
tg1 = mb.targets(src1, "question")
changed = mb.replan_targets(base, tg1, IDS)
check("2 post-rerun: 405 sources, 0 excluded", sum(len(v) for v in src1.values()) == 405 and not ex1, ex1)
check("2 the five targets after the rerun", {q: c["target_tokens"] for q, c in changed.items()} == EXPECT_TARGETS,
      changed)
check("2 the five targets before are the base plan's",
      all(c["target_tokens_before"] == base["questions"][q]["target_tokens"] for q, c in changed.items()))
check("2 the questions file names the five, in the form exp_01 reads",
      sorted(IDS) == sorted(EXPECT_TARGETS) and isinstance(json.loads(IDS_FILE.read_text())["ids"], list))
g13 = (ROOT / "findings" / "recompute" / "G13_runs" / "g13_check.py").read_text(encoding="utf-8")
check("2 g13_check.py carries the same EXPECT_TARGETS",
      all(f'"{q}": {v}' in g13 for q, v in EXPECT_TARGETS.items()))

# 3. refusals
check("3 a moved question left out is refused", raises(lambda: mb.replan_targets(base, tg1, IDS[:-1]), ValueError))
check("3 a question whose target did not move is refused",
      raises(lambda: mb.replan_targets(base, tg1, IDS + ["01_sarek_FR1"]), ValueError))
check("3 an unknown id is refused", raises(lambda: mb.replan_targets(base, tg1, IDS + ["NOPE"]), ValueError))
b_all = {**base, "scope": "all"}
check("3 a base plan at scope all is refused", raises(lambda: mb.replan_targets(b_all, tg1, IDS), ValueError))
tg_bad = copy.deepcopy(tg1)
tg_bad["01_sarek_FR1"]["sources"][0]["input_tokens"] += 1
check("3 another question's source changed is refused",
      raises(lambda: mb.replan_targets(base, tg_bad, IDS), ValueError))


# 4. plan() over the five and merge_plan()
def stand_in(entries, shift=0):
    """count(question, k): the base plan's probe where it has one, linear between probes, the last slope beyond."""
    def count(prompt):
        q, k = prompt
        pr = sorted((int(x), v) for x, v in entries[q]["probes"].items())
        if k in dict(pr):
            return dict(pr)[k] + (shift if k == 10 else 0)
        lo = max((p for p in pr if p[0] < k), default=pr[0])
        hi = min((p for p in pr if p[0] > k), default=None)
        if hi is None:
            lo, hi = pr[-2], pr[-1]
        return round(lo[1] + (hi[1] - lo[1]) * (k - lo[0]) / (hi[0] - lo[0]))
    return count


qs = [{"id": q, "question": q} for q in IDS]
meta = {k: base[k] for k in ("index", "collection", "embedding_model", "count_method")}
sub = mb.plan(after, "question", qs, lambda q, k: k, lambda q, k: (q, k), stand_in(base["questions"]),
              base["k_max"], meta)
check("4 the stand-in count reproduces the base plan's probes", mb.probe_mismatches(base, sub) == [])
doc = mb.merge_plan(base, str(base_path), "x" * 64, sub, changed)
kept = [q for q in base["questions"] if q not in IDS and json.dumps(doc["questions"][q]) == json.dumps(base["questions"][q])]
check("4 the other 130 entries are the base plan's, as JSON", len(kept) == 130, len(kept))
check("4 question order and settings as the base plan",
      list(doc["questions"]) == list(base["questions"])
      and all(doc[k] == base[k] for k in mb.SAME_AS_BASE + ("decision",)))
ok = []
for q in IDS:
    pr = sorted((int(k), v) for k, v in base["questions"][q]["probes"].items())
    t = EXPECT_TARGETS[q]
    lo = max((k for k, v in pr if v < t), default=None)
    hi = min((k for k, v in pr if v >= t), default=None)
    e = doc["questions"][q]
    ok.append(e["top_k"] != base["questions"][q]["top_k"] and (lo is None or e["top_k"] > lo)
              and (hi is None or e["top_k"] <= hi) and e["planned_tokens"] >= t and e["target_tokens"] == t)
check("4 each of the five crosses a top_k, inside the base probes' interval", all(ok),
      {q: (base["questions"][q]["top_k"], doc["questions"][q]["top_k"]) for q in IDS})
check("4 excluded empty, floor_bound recomputed, no_target empty",
      doc["excluded"] == [] and doc["floor_bound"] == mb.floor_bound(doc["questions"]) and doc["no_target"] == [])
check("4 the replan record", doc["replan"]["base_sha256"] == "x" * 64 and doc["replan"]["questions"] == IDS
      and doc["replan"]["base_made"] == base["made"] and set(doc["replan"]["changed"]) == set(IDS)
      and all(doc["replan"]["changed"][q]["top_k_before"] == base["questions"][q]["top_k"] for q in IDS))
check("4 the base plan document is not changed by the merge",
      json.loads(base_path.read_text(encoding="utf-8")) == base)
check("4 every question has an integer top_k (exp_01 load_budget_plan's rule)",
      all(isinstance(e.get("top_k"), int) and e["top_k"] >= 1 for e in doc["questions"].values()))

# 5. refusals after counting
sub_off = mb.plan(after, "question", qs, lambda q, k: k, lambda q, k: (q, k), stand_in(base["questions"], 1),
                  base["k_max"], meta)
bad = mb.probe_mismatches(base, sub_off)
check("5 a count one token off at top_k 10 is found for all five",
      sorted(q for q, k, _, _ in bad) == sorted(IDS) and all(k == 10 for _, k, _, _ in bad), bad)
check("5 merge_plan refuses a plan of another collection",
      raises(lambda: mb.merge_plan(base, "b", "s", {**sub, "collection": "other"}, changed), ValueError))
ch6 = {**changed, "01_sarek_FR1": {"target_tokens_before": 1, "target_tokens": 2}}
check("5 merge_plan refuses when the planned and named questions differ",
      raises(lambda: mb.merge_plan(base, "b", "s", sub, ch6), ValueError))

# 6. the CLI
out = tmp / "new_plan.json"
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    mb.main(["replan", "--base-plan", str(base_path), "--rlm-dir", str(after), "--questions-file", str(IDS_FILE),
             "--out", str(out), "--dry-run"])
text = buf.getvalue()
check("6 --dry-run prints the five and writes nothing", not out.exists() and "dry run" in text
      and all(f"-> {v}" in text for v in EXPECT_TARGETS.values()), text[-400:])
out.write_text("{}")
e = raises(lambda: mb.main(["replan", "--base-plan", str(base_path), "--rlm-dir", str(tmp / "none"),
                            "--questions-file", str(IDS_FILE), "--out", str(out), "--dry-run"]), SystemExit)
check("6 an existing --out is refused before anything is read", e is not None and "written once" in str(e), e)
e = raises(lambda: mb.main(["replan", "--base-plan", str(base_path), "--rlm-dir", str(before),
                            "--questions-file", str(IDS_FILE), "--out", str(tmp / "n2.json"), "--dry-run"]),
           SystemExit)
check("6 the pre-rerun run is refused (the five targets have not moved)", e is not None and "unchanged" in str(e), e)


# 7. after counting (finish_replan) and COUNT DRIFT (D236), on the stand-in counts of section 4
def run_finish(sub_, out_, drift=None, max_drift=None):
    """(SystemExit or None, printed text) of finish_replan on sub_."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        e = raises(lambda: mb.finish_replan(base, str(base_path), "x" * 64, sub_, changed, out_, drift, max_drift),
                   SystemExit)
    return e, buf.getvalue()


def drifted(entries, drift):
    """The base plan's entries with drift {(question, top_k): new count} applied to the probes."""
    out = copy.deepcopy(entries)
    for (q, k), v in drift.items():
        out[q]["probes"][str(k)] = v
    return out


# the ten differences the replan found on ~/paper_store_g13b (G13_runs/README.md, D225 Q1 O1 F4), all 0.8% or less
# except two at top_k 10, and two made-up rows inside 1%
G13B = {("OOD_024", 10): 5651, ("OOD_024", 20): 11332, ("OOD_024", 40): 23017, ("OOD_024", 50): 28735,
        ("OOD_024", 60): 34534, ("OOD_024", 80): 46294, ("OOD_025", 10): 5255, ("OOD_035", 40): 22996,
        ("OOD_035", 75): 43523, ("OOD_035", 80): 46310}
WITHIN = {("OOD_024", 20): 11332, ("OOD_035", 75): 43523}          # 0.80% and 0.31%
sub_in = mb.plan(after, "question", qs, lambda q, k: k, lambda q, k: (q, k),
                 stand_in(drifted(base["questions"], WITHIN)), base["k_max"], meta)
sub_g13b = mb.plan(after, "question", qs, lambda q, k: k, lambda q, k: (q, k),
                   stand_in(drifted(base["questions"], G13B)), base["k_max"], meta)
check("7 the stand-in drift is found by probe_mismatches",
      [(q, k) for q, k, _, _ in mb.probe_mismatches(base, sub_in)] == sorted(WITHIN)
      and len(mb.probe_mismatches(base, sub_g13b)) == len(G13B), mb.probe_mismatches(base, sub_g13b))

o = tmp / "f_equal.json"
e, text = run_finish(sub, o)
check("7 no drift, no option: written, 'each equal', no count_drift", e is None and o.exists()
      and "each equal" in text and "count_drift" not in json.loads(o.read_text()), (e, text[-300:]))
OLD_REFUSAL = ("replan refused: 2 counts differ from the base plan's at the same top_k, so this store, retriever or "
               "tokenizer is not the one the base plan read; nothing written")
o = tmp / "f_refused.json"
e, text = run_finish(sub_in, o)
check("7 drift without the option: the refusal unchanged, byte for byte, and nothing written",
      e is not None and str(e) == OLD_REFUSAL and not o.exists()
      and "  OOD_024 top_k 20: base plan 11423, now 11332\n  OOD_035 top_k 75: base plan 43387, now 43523\n" == text,
      (str(e), text))
o = tmp / "f_drift.json"
e, text = run_finish(sub_in, o, "D236", 0.01)
d = json.loads(o.read_text()) if o.exists() else {}
cd = d.get("count_drift") or {}
check("7 drift within 1% under D236: written with count_drift, the rows and the decision",
      e is None and cd.get("decision") == "D236" and cd.get("max_drift") == 0.01 and cd.get("accepted")
      and [(r["question_id"], r["top_k"], r["base"], r["now"]) for r in cd.get("differences", [])]
      == [("OOD_024", 20, 11423, 11332), ("OOD_035", 75, 43387, 43523)]
      and abs(cd["differences"][0]["relative"] - 91 / 11423) < 1e-6, (e, cd))
check("7 drift within 1%: the summary lists each difference and the 130 other entries stay the base plan's",
      "2 differ, accepted under D236" in text and "OOD_024 top_k 20 11423 -> 11332 (0.7966%)" in text
      and sum(json.dumps(d["questions"][q]) == json.dumps(base["questions"][q]) for q in base["questions"]
              if q not in IDS) == 130, text[-500:])
o = tmp / "f_over.json"
e, text = run_finish(sub_g13b, o, "D236", 0.01)
check("7 G13b's ten differences at max 1%: refused (OOD_024 and OOD_025 at top_k 10 exceed it), nothing written",
      e is not None and "2 of 10 differing counts exceed the bound 0.01" in str(e) and "OOD_024 top_k 10" in str(e)
      and "OOD_025 top_k 10" in str(e) and not o.exists(), e)
o = tmp / "f_over2.json"
e, _ = run_finish(sub_g13b, o, "D236", 0.015)
check("7 the same ten at max 1.5%: written, ten rows", e is None and o.exists()
      and len(json.loads(o.read_text())["count_drift"]["differences"]) == 10, e)
o = tmp / "f_none.json"
e, text = run_finish(sub, o, "D236", 0.01)
check("7 the option and no drift: written, count_drift with no rows",
      e is None and json.loads(o.read_text())["count_drift"]["differences"] == [] and "0 differ" in text, (e, text))
check("7 a mismatch of a question not named cannot be accepted",
      raises(lambda: mb.accept_drift([("01_sarek_FR1", 10, 5000, 5001)], changed, "D236", 0.01), ValueError))
check("7 a mismatch on a base count of 0 cannot be accepted",
      raises(lambda: mb.accept_drift([("OOD_024", 10, 0, 1)], changed, "D236", 0.01), ValueError))

readme = tmp / "README.md"
readme.write_text("- **D236** (test)\n- D237 without stars\n")
check("7 a decision in the README passes", raises(lambda: mb.check_drift_decision("D236", 0.01, readme)) is None)
check("7 a decision missing from the README is refused",
      raises(lambda: mb.check_drift_decision("D237", 0.01, readme), ValueError))
check("7 a prefix of a decision is refused (**D23** is not in **D236**)",
      raises(lambda: mb.check_drift_decision("D23", 0.01, readme), ValueError))
check("7 max drift 0 or 1 is refused", raises(lambda: mb.check_drift_decision("D236", 0, readme), ValueError)
      and raises(lambda: mb.check_drift_decision("D236", 1.0, readme), ValueError))
check("7 the repository's README holds **D236**", raises(lambda: mb.check_drift_decision("D236", 0.01)) is None)
for args, word, name in ((["--accept-count-drift", "D99999"], "holds no", "a decision missing from the README"),
                         (["--max-drift", "0.02"], "needs --accept-count-drift", "--max-drift alone")):
    o = tmp / f"cli_{len(results)}.json"
    e = raises(lambda: mb.main(["replan", "--base-plan", str(base_path), "--rlm-dir", str(tmp / "none"),
                                "--questions-file", str(IDS_FILE), "--out", str(o), *args]), SystemExit)
    check(f"7 the CLI refuses {name} before anything is read, nothing written",
          e is not None and word in str(e) and "nothing written" in str(e) and not o.exists(), e)
buf = io.StringIO()
o = tmp / "cli_dry.json"
with contextlib.redirect_stdout(buf):
    mb.main(["replan", "--base-plan", str(base_path), "--rlm-dir", str(after), "--questions-file", str(IDS_FILE),
             "--out", str(o), "--dry-run", "--accept-count-drift", "D236"])
check("7 --dry-run with D236 prints the drift rule and writes nothing",
      not o.exists() and "count drift: accepted under D236" in buf.getvalue() and "0.01 relative" in buf.getvalue(),
      buf.getvalue()[-300:])

# g13_check.py reads the rows replan writes: relative rounded to 6 decimals (the G13 chain of 4 Nov 10:40 stopped on
# 10 rows within D237's 1.5% because the check compared that rounded value with the exact one at 1e-9)
_spec = importlib.util.spec_from_file_location("g13_check", ROOT / "findings" / "recompute" / "G13_runs" / "g13_check.py")
g13c = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(g13c)
written = [{**r, "relative": round(r["relative"], 6)} for r in
           [{"question_id": "OOD_024", "top_k": 10, "base": 5722, "now": 5651, "relative": 71 / 5722},
            {"question_id": "OOD_025", "top_k": 10, "base": 5183, "now": 5255, "relative": 72 / 5183}]]
check("8 g13_check accepts replan's rounded rows within max_drift (OOD_024 1.24%, OOD_025 1.39% under 1.5%)",
      not any(g13c.drift_off(r, 0.015) for r in written), written)
check("8 g13_check refuses the same rows above max_drift (1%)", all(g13c.drift_off(r, 0.01) for r in written))
check("8 g13_check refuses a stored relative that is not the recomputed drift",
      g13c.drift_off({**written[0], "relative": 0.001}, 0.015))

print(f"{sum(results)} of {len(results)} checks passed")
sys.exit(0 if all(results) else 1)
