#!/bin/bash
# D89 (Q145 O3), D90 (Q1, Q2) and D92 (Q186, Q188, Q199): rerun G1's 15 answers that failed on a Gemini reply D89 or D90 now returns to
# Mentori (lock_adapter._finish, _returned), as the submitted Mentori's Gemini client took it (models/gemini.py:166-176,
# :327-365): a block or an empty reply as empty text (D89), a recitation stop with the text Google streamed before
# stopping (D90 Q1), a malformed_function_call or malformed_response reply with what it held (D90 Q2). The list is
# scripts/S455_d89_affected_answers.py's, run read-only on the Studio's ~/projects/mentori-runs, 18 Oct 00:56
# (findings/recompute/Q145/S455_d92_affected_studio_g1.json, each with action rerun; the D90 list is
# S455_d90_affected_studio_g1.json, the D89 list of 3 S455_d89_affected_studio_g1.json). D92 changes none of the 15: Q185
# and Q187 concern the authors' RLM (G6) only, and no G1 call carries a Q188 reason. S455 --merge
# (findings/recompute/Q145/S455_d92_list.json) lists four of them under K1 too, the draw-1 answers K1 scores: rlm_20
# OOD_043 (beelink, stage 1), rlm_20 OOD_041 (beelink_11435, stage 2), rlm_5 and rlm_20 06_star_aligner_FR1 (laptop,
# stage 2), each to be scored after this rerun (no K1 row for them in the files read on 18 Oct, 00:5x):
#   verified_pass 19_hpai_canada_TE3 d3 (D89): the generation call (pipeline.py:295 _generate, seq 3) ended with no
#     finishReason and nothing in it (gemini_client "error" then, "empty" now); stored with that error and no answer.
#     Now the pass stores "" with no error (pipeline.py returns the reply text as given).
#   rlm_20 OOD_007 d3 and OOD_043 d1 (D89): the first root turn (rlm/orchestrator.py:263 run_stream, seq 1) stopped on
#     RECITATION after 24,719 and 8,281 characters; stored as call_error with no answer. Now the turn returns that text
#     (D90 Q1) and the RLM goes on.
#   12 answers (D90 Q2) whose root turn ended malformed_response or malformed_function_call, each stored as call_error
#     with no answer: rlm_5 06_star_aligner_FR1 d1, 15_rabies_tanzania_TE3 d3, 20_lsd_review_FR1 d3; rlm_10
#     01_sarek_CO2 d2, 07_salmon_FR1 d3, OOD_024 d2, OOD_025 d2, OOD_035 d3; rlm_20 06_star_aligner_FR1 d1, OOD_013 d2,
#     OOD_029 d1, OOD_041 d1. Now the turn returns the text it held (S455's text_chars, text_blank): "" for 4
#     (01_sarek_CO2 d2, 07_salmon_FR1 d3, rlm_20 OOD_013 d2, rlm_5 15_rabies_tanzania_TE3 d3), one blank character for 3
#     (OOD_024 d2, OOD_035 d3, OOD_029 d1), text for the other 5; and goes on.
# Every other G1 answer has no affected call (S455 over the 13 G1 sinks, smokes included).
# G2: the 5 rlm_10 answers are the 5 G2's plan excluded as call errors (G2_runs/g2_targets_check.txt: 400 sources, 5
# excluded, 135 targets; questions 01_sarek_CO2, 07_salmon_FR1, OOD_024, OOD_025 and OOD_035 have a target from 2
# draws). After this rerun each is a source if it stores no error, so those 5 questions' targets (the median of the
# question's own RLM-10 draws, Q79) must be recomputed, and every G2 answer planned from the old targets for them
# rerun; g2_check.py's EXPECT (400 sources, 5 excluded) then no longer holds. That is a G2 step, not done here.
# G2 itself runs on dd3fc37, before D89 (cd49f70): any blocked, recitation, malformed or no-finishReason Gemini reply
# it meets still raises. Once G2 ends, run S455 over exp_01__matched_budget__exp_v4_s20_n0 and rerun what it lists
# under D90, as here; this script does not cover G2's own answers.
# The replaced records are kept in each run's discarded_D89/, as rerun_q151.sh kept its.
#
#   bash findings/recompute/G1_runs/rerun_d89.sh                       dry (the default): checks the 15, writes nothing
#   bash findings/recompute/G1_runs/rerun_d89.sh go <fix commit>       the rerun (Studio, ~/projects/mentori-runs)
#   bash findings/recompute/G1_runs/rerun_d89.sh check <archive>       after the four end records are written again
# The dry form before the pull, from the laptop, writing nothing on the Studio:
#   ssh 10.15.212.253 "S455_SRC=$(base64 < scripts/S455_d89_affected_answers.py | tr -d '\n') bash -c \"\$(cat)\" rerun dry" \
#       < findings/recompute/G1_runs/rerun_d89.sh
# Before "go", in this order:
#  a. laptop: commit the D90 fix and push, so origin/main holds <fix commit>.
#  b. Studio, ~/projects/mentori-runs: G2 has ended (it runs in this clone on dd3fc37 and the clone is never pulled
#     while a job runs) and no other job uses this clone; then git pull --ff-only.
#  c. the code (D92 Q186, Valerio 18 October: the D90 reruns run under today's lock and code, each recording its code
#     version and lock): the 15 reruns run on HEAD (which holds <fix commit>); every other answer of each config on the
#     commit its start record names (verified_pass and rlm_20 11137f9, rlm_5 87ad4a0, rlm_10 4cd0c96). Besides D89, D90
#     and D92 the difference carries the Q141 cite() refusal (rlm/context.py), the Q150 search timers (retriever.py),
#     the Q141 --skip-failed and Q151 changes in exp_01_generation.py, the Q184 final check (str(content), which changes
#     no stored answer), the lock adapter's and gemini_client's other changes, and whatever else <fix commit> holds.
#     "go" writes git diff --stat <their commit> HEAD -- experiments/ into the archive (code_since_g1_<config>.txt), and
#     ran_on.json (archive and each run's discarded_D89/): per config the commit and lock the kept answers ran on
#     (start records) and the commit, dirty state and lock the reruns run on; every rerun call record also carries
#     session_id and code_commit (D92 Q199).
#  d. the lock: G1 ran under 1b89d50c; D92 Q186 accepted d66daa28 (ACCEPTED_LOCK below), whose difference (D85: [judge]
#     second_model and not_sent, the qwen3.8 [models] row; git diff 6457ae6 4fd5b72 -- experiments/LOCK.toml) touches no
#     setting a Gemini call or the gpt-oss:20b verifier sends. "go" refuses any other lock: a later lock needs its own
#     decision.
#
# What "go" does, in order (any refusal stops it before the runs' files are touched):
#  1. refuses if an exp_01 or matched-budget process runs, 11453 has a connection, HEAD lacks <fix commit> or the
#     checkout lacks the D92 rule (D90's, the Q188 statuses, the Q184 final check, the Q199 record fields), tracked
#     files under experiments/ differ from HEAD, today's lock is not ACCEPTED_LOCK, or any config's end record is not
#     rc 0.
#  2. S455 over the four runs must list exactly the 15 keys with action rerun, each stored once with its error and no
#     answer.
#  3. copies aside, into each run's discarded_D89/: answers.jsonl, calls.jsonl and retrievals.jsonl as they stand, the
#     removed answer lines and the answers.jsonl the rerun starts from (kept_answers.jsonl), with sha256s; into
#     findings/recompute/G1_runs/d89_before_rerun_<UTC>/ the log, start and end records of the four configs (run_g1.sh
#     writes them with '>') and the store's hashes with their difference from the launch.
#  4. exp_01's dry run of each config with --resume --skip-failed against copies of kept_answers.jsonl (own
#     --sink-root): in draws 1, 2, 3, verified_pass 0 0 1, rlm_5 1 0 2, rlm_10 0 3 2 and rlm_20 4 1 1 to run (counted
#     from KEYS below), or it refuses.
#  5. fresh-loads the verifier on 11453 as launch_g1.sh did, replaces each answers.jsonl with kept_answers.jsonl (only
#     the 15 lines go; calls.jsonl and retrievals.jsonl are not touched: each record carries its answer's ctx_uid), then
#     starts run_g1.sh for each of the four configs, each --resume --skip-failed, one process per strategy, together,
#     as launch_g1.sh started G1's six.
# --skip-failed keeps every other stored error as it is, so no other key is sent again.
cd ~/projects/mentori-runs || exit 1
export PATH=/opt/homebrew/bin:$HOME/.local/bin:$PATH PYTHONDONTWRITEBYTECODE=1
D=findings/recompute/G1_runs; S=$HOME/paper_store_g1
ACCEPTED_LOCK=d66daa28596bf3b70ff90e0fb89b1353eab023eba699427cb05ebb3376105c12   # D92 Q186 (18 October)
refuse() { echo "refused: $*"; exit 1; }
# run|answer_key|stored generation.stop_reason
KEYS="
exp_01__verified_pass__exp_v4_s20_n0|exp_v4_s20_n0|verified_pass|19_hpai_canada_TE3|d3|error
exp_01__rlm_5__exp_v4_s20_n0|exp_v4_s20_n0|rlm_5|06_star_aligner_FR1|d1|call_error
exp_01__rlm_5__exp_v4_s20_n0|exp_v4_s20_n0|rlm_5|15_rabies_tanzania_TE3|d3|call_error
exp_01__rlm_5__exp_v4_s20_n0|exp_v4_s20_n0|rlm_5|20_lsd_review_FR1|d3|call_error
exp_01__rlm_10__exp_v4_s20_n0|exp_v4_s20_n0|rlm_10|01_sarek_CO2|d2|call_error
exp_01__rlm_10__exp_v4_s20_n0|exp_v4_s20_n0|rlm_10|07_salmon_FR1|d3|call_error
exp_01__rlm_10__exp_v4_s20_n0|exp_v4_s20_n0|rlm_10|OOD_024|d2|call_error
exp_01__rlm_10__exp_v4_s20_n0|exp_v4_s20_n0|rlm_10|OOD_025|d2|call_error
exp_01__rlm_10__exp_v4_s20_n0|exp_v4_s20_n0|rlm_10|OOD_035|d3|call_error
exp_01__rlm_20__exp_v4_s20_n0|exp_v4_s20_n0|rlm_20|06_star_aligner_FR1|d1|call_error
exp_01__rlm_20__exp_v4_s20_n0|exp_v4_s20_n0|rlm_20|OOD_007|d3|call_error
exp_01__rlm_20__exp_v4_s20_n0|exp_v4_s20_n0|rlm_20|OOD_013|d2|call_error
exp_01__rlm_20__exp_v4_s20_n0|exp_v4_s20_n0|rlm_20|OOD_029|d1|call_error
exp_01__rlm_20__exp_v4_s20_n0|exp_v4_s20_n0|rlm_20|OOD_041|d1|call_error
exp_01__rlm_20__exp_v4_s20_n0|exp_v4_s20_n0|rlm_20|OOD_043|d1|call_error
"
N=$(echo "$KEYS" | grep -c '|')
CONFIGS="verified_pass rlm_5 rlm_10 rlm_20"
RUNS=$(for c in $CONFIGS; do printf "exp_01__%s__exp_v4_s20_n0 " $c; done)
# the reruns per draw (1, 2, 3) of a config, counted from KEYS
per_draw() { echo "$KEYS" | awk -F'|' -v c="$1" '$3 == c {n[substr($5, 2)]++} END {print n[1]+0, n[2]+0, n[3]+0}'; }

# the 15 as stored now, against S455 (read only), piped so it reads this clone's findings/runs/
verify() {
  local s455=${S455:-scripts/S455_d89_affected_answers.py}      # S455=<path> or S455_SRC=<base64>: the dry form before the pull
  [ -n "${S455_SRC:-}" ] || [ -f $s455 ] || refuse "$s455 is not in this checkout (pull the commit that adds it, or pass S455= or S455_SRC=)"
  uv run --no-project python - "$KEYS" "${1:-}" "$s455" <<'EOF' || return 1
import base64, json, os, subprocess, sys
from pathlib import Path
want = [l.split("|") for l in sys.argv[1].split("\n") if l.strip()]
out = Path(sys.argv[2]) if sys.argv[2] else None
src = (base64.b64decode(os.environ["S455_SRC"]).decode() if os.environ.get("S455_SRC")
       else Path(sys.argv[3]).read_text())
runs = sorted({w[0] for w in want})
s455 = json.loads(subprocess.run(["uv", "run", "--no-project", "python", "-", "--stdout"]
                                 + [f"findings/runs/{r}" for r in runs], input=src,
                                 capture_output=True, text=True, check=True).stdout)
assert s455["gate"] == "pass", s455["gate"]
assert "D92" in s455["provenance"]["decision"], f"S455 is not the D92 version: {s455['provenance']['decision']}"
listed = sorted((r["run"], r["answer_key"], bool(r.get("failed_at_affected_call")), r.get("action"))
                for r in s455["rows"])
keyed = sorted((w[0], "|".join(w[1:5]), True, "rerun") for w in want)
assert listed == keyed, f"S455 lists {sorted(set(listed) ^ set(keyed))} apart from the {len(want)} here"
for run in runs:
    p = Path("findings/runs") / run / "answers.jsonl"
    lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
    recs = [json.loads(l) for l in lines]
    mine = {"|".join(w[1:5]): w[5] for w in want if w[0] == run}
    gone = [(l, r) for l, r in zip(lines, recs) if r["answer_key"] in mine]
    assert sorted(r["answer_key"] for _, r in gone) == sorted(mine), (run, [r["answer_key"] for _, r in gone])
    for _, r in gone:
        g = r["generation"]
        assert g.get("error") and g.get("stop_reason") == mine[r["answer_key"]] and not g.get("answer"), \
            (r["answer_key"], g.get("stop_reason"), str(g.get("error"))[:80])
        print(f"  {r['answer_key']}: stored {g.get('stop_reason')}, error {str(g['error'])[:90]}")
    kept = [l for l, r in zip(lines, recs) if r["answer_key"] not in mine]
    assert len(kept) == len(lines) - len(mine) == 405 - len(mine), (run, len(lines), len(kept))
    print(f"{run}: {len(lines)} answers, {len(gone)} to rerun, {len(kept)} kept")
    if out is not None:
        x = out / run
        x.mkdir(parents=True)
        (x / "removed_answers.jsonl").write_text("".join(l for l, _ in gone), encoding="utf-8")
        (x / "kept_answers.jsonl").write_text("".join(kept), encoding="utf-8")
print(f"{len(want)} answers to rerun, each stored once with its error and no answer")
EOF
}

if [ "${1:-dry}" = dry ]; then
  verify "" || refuse "the stored answers are not the $N above (nothing touched)"
  echo "dry: nothing written. After G2 ends and the clone is pulled: bash $D/rerun_d89.sh go <fix commit> (lock $ACCEPTED_LOCK, D92 Q186)"
  echo "  K1 (S455 --merge): score after this rerun rlm_20 OOD_043 d1 (beelink), rlm_20 OOD_041 d1 (beelink_11435), rlm_5 and rlm_20 06_star_aligner_FR1 d1 (laptop)"
  for c in $CONFIGS; do
    echo "  would run: run_g1.sh $c --resume --skip-failed   (draws 1, 2, 3: $(per_draw $c)): $(echo "$KEYS" | awk -F'|' -v c=$c '$3 == c {printf "%s %s; ", $4, $5}')"
  done
  echo "  then G2: recompute the targets of 01_sarek_CO2, 07_salmon_FR1, OOD_024, OOD_025, OOD_035 from the rerun rlm_10"
  exit 0
fi

if [ "$1" = check ]; then
  # After the reruns: every end record rc 0 and written after the rerun began, every start record naming the commit
  # rerun.json names (so the new answers ran on the D90 code); 405 answers in each run, each key once; the kept lines
  # unchanged at the head; calls.jsonl and retrievals.jsonl as they stood before the rerun unchanged at the head of the
  # new ones (the rerun only appends); every call of a new answer under the lock rerun.json names; the new answers
  # with their stop reason, error and the status of every call they made
  A=${2:-}; [ -n "$A" ] && [ -f "$A/rerun.json" ] || refuse "name the archive the rerun wrote: rerun_d89.sh check <archive>"
  for c in $CONFIGS; do cat $D/g1_$c.end.json; done
  uv run --no-project python - "$KEYS" "$A" "$D" "$CONFIGS" <<'EOF' || exit 1
import collections, json, sys
from pathlib import Path
want = [l.split("|") for l in sys.argv[1].split("\n") if l.strip()]
arch, d = Path(sys.argv[2]), Path(sys.argv[3])
rerun = json.loads((arch / "rerun.json").read_text())
good = True
for c in sys.argv[4].split():
    end = json.loads((d / f"g1_{c}.end.json").read_text())
    start = json.loads((d / f"g1_{c}.start.json").read_text())
    ok = (end.get("rc") == 0 and end.get("end", "") > rerun["d89_rerun"] and start.get("start", "") >= rerun["d89_rerun"]
          and start.get("commit") == rerun["head"] and start.get("lock_sha256") == rerun["lock_sha256"])
    good &= ok
    print(f"g1_{c}: rc {end.get('rc')}, started {start.get('start')} on {str(start.get('commit'))[:7]} "
          f"(rerun.json head {rerun['head'][:7]}), lock {str(start.get('lock_sha256'))[:8]}: {'ok' if ok else 'FAIL'}")


def prefix(old: Path, new: Path) -> bool:
    """old's bytes are the first bytes of new (the rerun appended and changed nothing before)."""
    if not old.is_file():
        return not new.exists()
    n = old.stat().st_size
    with open(old, "rb") as a, open(new, "rb") as b:
        return a.read() == b.read(n)
for run in sorted({w[0] for w in want}):
    p = Path("findings/runs") / run
    lines = (p / "answers.jsonl").read_text(encoding="utf-8").splitlines(keepends=True)
    kept = (p / "discarded_D89" / "kept_answers.jsonl").read_text(encoding="utf-8").splitlines(keepends=True)
    recs = [json.loads(l) for l in lines]
    n = collections.Counter(r["answer_key"] for r in recs)
    mine = {"|".join(w[1:5]) for w in want if w[0] == run}
    new = recs[len(kept):]
    x = p / "discarded_D89"
    heads = {f: prefix(x / f"{f}.before_rerun", p / f) for f in ("calls.jsonl", "retrievals.jsonl")}
    uids = {r["ctx_uid"] for r in new}
    locks = collections.Counter()
    with open(p / "calls.jsonl", encoding="utf-8") as f:
        for line in f:
            if any(u in line for u in uids):
                c = json.loads(line)
                if c.get("ctx_uid") in uids:
                    locks[c.get("lock_sha256")] += 1
    ok = (len(recs) == 405 and max(n.values()) == 1 and lines[:len(kept)] == kept
          and {r["answer_key"] for r in new} == mine and len(new) == len(mine) and all(heads.values())
          and set(locks) == {rerun["lock_sha256"]})
    good &= ok
    print(f"{run}: {len(recs)} answers, {'each key once' if max(n.values()) == 1 else 'DUPLICATE KEYS'}, the "
          f"{len(kept)} kept lines {'unchanged' if lines[:len(kept)] == kept else 'CHANGED'}, "
          + ", ".join(f"{k} before the rerun {'unchanged at the head' if v else 'CHANGED'}" for k, v in heads.items())
          + f", the new answers' {sum(locks.values())} calls under lock {sorted(str(k)[:8] for k in locks)}, "
          f"{len(new)} new: {'ok' if ok else 'FAIL'}")
    for r in new:
        g = r["generation"]
        st = collections.Counter(c.get("status") for c in g.get("calls") or [])
        print(f"  {r['answer_key']}: {g.get('stop_reason')}, answer {len(g.get('answer') or '')} chars, call statuses "
              f"{dict(st)}" + (f", error {str(g['error'])[:90]}" if g.get("error") else ""))
print("check:", "PASS" if good else "FAIL")
print("next (G2): recompute the targets of 01_sarek_CO2, 07_salmon_FR1, OOD_024, OOD_025, OOD_035 from the rerun rlm_10")
sys.exit(0 if good else 1)
EOF
  exit 0
fi

[ "$1" = go ] || refuse "rerun_d89.sh [dry | go <fix commit> | check <archive>]"
# 1. refusals
FIX=${2:-}
[ -n "$FIX" ] || refuse "name the commit that holds the D92 fix: rerun_d89.sh go <commit>"
pgrep -f "[e]xp_01_generation.py" > /dev/null && refuse "an exp_01 process runs"
pgrep -f "[m]atched_budget" > /dev/null && refuse "a matched-budget (G2) process runs"
[ "$(lsof -nP -iTCP:11453 -sTCP:ESTABLISHED | wc -l)" -gt 0 ] && refuse "11453 in use"
git cat-file -e "$FIX^{commit}" 2>/dev/null || refuse "commit $FIX is not in this clone (pull first)"
git merge-base --is-ancestor "$FIX" HEAD || refuse "HEAD $(git rev-parse --short HEAD) does not contain $FIX (pull first)"
grep -q 'PASSED_ON_STATUSES = ("recitation", "malformed_function_call", "malformed_response",' experiments/runner/gemini_client.py \
    && grep -q 'EMPTY_TEXT_STATUSES = ("empty", "blocked")' experiments/runner/gemini_client.py \
    && grep -q 'def _gemini_returns(record: dict)' experiments/mentori/backend/agents/lock_adapter.py \
    && grep -q 'def raised_before_d89(rec: dict)' experiments/runner/gemini_client.py \
    && grep -q '"language", "other", "unexpected_tool_call", "too_many_tool_calls")' experiments/runner/gemini_client.py \
    && grep -q 'any(str(s.content).strip() for s in context.report_sections)' experiments/mentori/backend/retrieval/rlm/orchestrator.py \
    && grep -q 'def provenance() -> dict' experiments/runner/ollama_client.py \
    || refuse "the checkout lacks the D92 rule (gemini_client.py, lock_adapter.py, orchestrator.py, ollama_client.py)"
git diff --quiet HEAD -- experiments/ || refuse "tracked files under experiments/ differ from HEAD"
LOCK_NOW=$(shasum -a 256 experiments/LOCK.toml | cut -c1-64)
[ "$LOCK_NOW" = "$ACCEPTED_LOCK" ] || refuse "today's lock is $LOCK_NOW; D92 Q186 accepted $ACCEPTED_LOCK (G1 ran under $(grep -o '"lock_sha256": "[0-9a-f]*"' $D/g1_rlm_20.start.json | cut -d'"' -f4)); another lock needs its own decision"
for c in $CONFIGS; do
  [ -f $D/g1_$c.start.json ] && [ -f $D/g1_$c.end.json ] && [ -f $D/g1_$c.log ] || refuse "g1_$c records missing"
  grep -q '"rc": 0}' $D/g1_$c.end.json || refuse "g1_$c.end.json is not rc 0: $(cat $D/g1_$c.end.json)"
  OLD=$(grep -o '"commit": "[0-9a-f]*"' $D/g1_$c.start.json | cut -d'"' -f4)
  [ -n "$OLD" ] && git cat-file -e "$OLD^{commit}" 2>/dev/null || refuse "g1_$c.start.json names no commit this clone holds"
done
for r in $RUNS; do [ -e findings/runs/$r/discarded_D89 ] && refuse "findings/runs/$r/discarded_D89 exists (a rerun was prepared before)"; done

# 2 and 3. the 15 checked against S455, then copied aside with the runs' files, logs and the store's hashes
A=$D/d89_before_rerun_$(date -u +%Y%m%dT%H%M%SZ)
[ -e "$A" ] && refuse "$A exists"
T=$(mktemp -d) || refuse "no temporary folder"
verify "$T" || refuse "the stored answers are not the $N above (nothing touched; see $T)"
mkdir -p "$A" || refuse "cannot make $A"
for r in $RUNS; do
  X=findings/runs/$r/discarded_D89
  mkdir -p $X || refuse "cannot make $X"
  cp -p findings/runs/$r/answers.jsonl $X/answers.jsonl.before_rerun && cp -p findings/runs/$r/calls.jsonl $X/calls.jsonl.before_rerun \
    && cp -p findings/runs/$r/retrievals.jsonl $X/retrievals.jsonl.before_rerun \
    && cp -p $T/$r/removed_answers.jsonl $T/$r/kept_answers.jsonl $X/ || refuse "copy to $X failed"
  (cd $X && shasum -a 256 *.before_rerun removed_answers.jsonl kept_answers.jsonl) > $X/SHA256SUMS
  cmp -s findings/runs/$r/answers.jsonl $X/answers.jsonl.before_rerun || refuse "$r: answers.jsonl copy differs"
done
for c in $CONFIGS; do
  cp -p $D/g1_$c.log $D/g1_$c.start.json $D/g1_$c.end.json "$A/" || refuse "copy to $A failed"
done
(cd "$A" && shasum -a 256 g1_*) > "$A/SHA256SUMS"
# the code the kept answers ran on, and its difference from the code the reruns run on (F4/F5 of the D89 reviews)
for c in $CONFIGS; do
  OLD=$(grep -o '"commit": "[0-9a-f]*"' $D/g1_$c.start.json | cut -d'"' -f4)
  echo "$OLD" > "$A/g1_${c}_commit_before.txt"
  { echo "kept $c answers ran on $OLD; the reruns on $(git rev-parse HEAD)"; git diff --stat "$OLD" HEAD -- experiments/; } \
    > "$A/code_since_g1_$c.txt"
done
# D92 Q186: the code version and lock of the kept answers (their start records) and of the reruns, on file
uv run --no-project python - "$CONFIGS" "$D" "$A" "$LOCK_NOW" <<'EOF' || refuse "ran_on.json not written (answers untouched)"
import json, subprocess, sys
from pathlib import Path
d, a = Path(sys.argv[2]), Path(sys.argv[3])
git = lambda *x: subprocess.run(["git", *x], capture_output=True, text=True).stdout.strip()   # noqa: E731
kept = {}
for c in sys.argv[1].split():
    st = json.loads((d / f"g1_{c}.start.json").read_text())
    kept[c] = {"commit": st.get("commit"), "lock_sha256": st.get("lock_sha256"), "start": st.get("start")}
out = {"decision": "D92 Q186: the D90 reruns run under today's lock and code, each recording its code version and lock",
       "kept_answers_ran_on": kept,
       "reruns_run_on": {"commit": git("rev-parse", "HEAD"),
                         "dirty": bool(git("--no-optional-locks", "status", "--porcelain", "--untracked-files=no", "--",
                                           "experiments", "scripts")),
                         "lock_sha256": sys.argv[4]},
       "per_call": "every rerun call record carries session_id and code_commit (D92 Q199)"}
(a / "ran_on.json").write_text(json.dumps(out, indent=1) + "\n")
print("ran_on.json:", json.dumps(out)[:300])
EOF
for r in $RUNS; do cp -p "$A/ran_on.json" findings/runs/$r/discarded_D89/ran_on.json || refuse "copy of ran_on.json failed"; done
(cd $S && find . -type f ! -name '*.sha256' ! -name '*.txt' | sort | xargs shasum -a 256) > "$A/store_at_rerun.sha256"
diff $D/store_at_launch.sha256 "$A/store_at_rerun.sha256" > "$A/store_launch_vs_rerun.diff"
echo "store files differing from store_at_launch.sha256: $(grep -c '^>' "$A/store_launch_vs_rerun.diff")"

# 4. the work lists the reruns will run, against copies of the kept answers (no model call, nothing written by exp_01)
RESUME="--resume --skip-failed"
for r in $RUNS; do mkdir -p $T/sinks/$r && cp -p findings/runs/$r/discarded_D89/kept_answers.jsonl $T/sinks/$r/answers.jsonl; done
for c in $CONFIGS; do
  DATABASE_URL=sqlite:///$S/mentori_app.db CHROMA_PERSIST_DIRECTORY=$S/chroma_db uv run --project experiments/mentori --frozen python experiments/mentori/publication/scripts/exp_01_generation.py \
      --configs $c --draws 1 2 3 $RESUME --sink-root $T/sinks --dry-run > "$A/dry_run_$c.txt" 2>&1 \
      || refuse "dry run of $c failed: see $A/dry_run_$c.txt (the runs' answers.jsonl are untouched)"
  GOT=$(awk -v r="exp_01__${c}__exp_v4_s20_n0" '$1 == r {n[$2] = $5} END {print n[1]+0, n[2]+0, n[3]+0}' "$A/dry_run_$c.txt")
  [ "$GOT" = "$(per_draw $c)" ] || refuse "$c: the dry run gives $GOT to run in draws 1, 2, 3, not $(per_draw $c) (answers untouched)"
  echo "to run: $c draws 1, 2, 3: $GOT"
done

# 5. the verifier fresh-loaded as at the launch, the 15 answer lines go, the four strategies resume
uv run --frozen python -m experiments.runner.job fresh-load --base http://127.0.0.1:11453 --model gpt-oss:20b \
    --log ~/ollama_logs/serve_11453.log --binary /opt/homebrew/opt/ollama/bin/ollama --machine macos \
    --record "$A/fresh_load_11453.json" || refuse "fresh load failed (answers untouched)"
for r in $RUNS; do
  X=findings/runs/$r/discarded_D89
  cp -p $X/kept_answers.jsonl findings/runs/$r/answers.jsonl.d89_tmp && mv findings/runs/$r/answers.jsonl.d89_tmp findings/runs/$r/answers.jsonl \
    || refuse "$r: could not replace answers.jsonl (the copy before the rerun is $X/answers.jsonl.before_rerun)"
  cmp -s findings/runs/$r/answers.jsonl $X/kept_answers.jsonl || refuse "$r: answers.jsonl is not kept_answers.jsonl"
done
BEFORE=$(for c in $CONFIGS; do printf '"%s": "%s", ' $c "$(cat "$A/g1_${c}_commit_before.txt")"; done | sed 's/, $//')
TORUN=$(for c in $CONFIGS; do set -- $(per_draw $c); printf '"%s": {"d1": %s, "d2": %s, "d3": %s}, ' $c $1 $2 $3; done | sed 's/, $//')
echo "{\"d89_rerun\": \"$(date -u +%FT%TZ)\", \"decisions\": \"D89, D90, D92 (Q186)\", \"fix_commit\": \"$(git rev-parse "$FIX")\", \"head\": \"$(git rev-parse HEAD)\", \"lock_sha256\": \"$LOCK_NOW\", \"kept_answers_commit\": {$BEFORE}, \"archive\": \"$A\", \"store_hashes\": \"$A/store_at_rerun.sha256\", \"exp_01_options\": \"$RESUME\", \"answers\": $N, \"to_run\": {$TORUN}}" > "$A/rerun.json"
uv run --no-project python -c "import json, sys; json.load(open(sys.argv[1]))" "$A/rerun.json" || refuse "rerun.json is not JSON (answers already replaced: restore from each discarded_D89/answers.jsonl.before_rerun)"
for r in $RUNS; do cp -p "$A/rerun.json" findings/runs/$r/discarded_D89/rerun.json; done
for c in $CONFIGS; do
  G1_STORE_HASHES="$A/store_at_rerun.sha256" nohup bash $D/run_g1.sh $c $RESUME > /dev/null 2>&1 < /dev/null &
done
echo "rerun of $N answers ($(for c in $CONFIGS; do printf '%s %s, ' $c "$(per_draw $c)"; done | sed 's/, $//')) started at $(date +%H:%M) on $(git rev-parse --short HEAD); records before it in each run's discarded_D89/ and $A"
echo "when the four end records are written again: bash $D/rerun_d89.sh check $A"
