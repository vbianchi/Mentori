#!/bin/bash
# I2, the plant-science reuse demonstration (D74, D160 (14)): the one launcher, on the laptop. Nothing here is started
# by hand in another way. GUIDE.md says, for any corpus, what each step does; this file runs those steps for I2.
#
#   bash experiments/reuse_demo/launch_i2.sh check                what is ready; no model call, nothing written
#   bash experiments/reuse_demo/launch_i2.sh index-gate           rebuild the paper's 20-paper index (build_index.py gate)
#   bash experiments/reuse_demo/launch_i2.sh index-build          the plant index i2_plant5 (build_index.py build)
#   bash experiments/reuse_demo/launch_i2.sh stores               one copy of the plant store per config
#   bash experiments/reuse_demo/launch_i2.sh smoke                PB_001, single pass, draw 1: one Gemini answer
#   bash experiments/reuse_demo/launch_i2.sh run [draw ...]       the five configs without a verifier, one at a time
#   bash experiments/reuse_demo/launch_i2.sh resume [draw ...]    the same with --resume --skip-failed
#   I2_VERIFIER_URL=http://127.0.0.1:<port> bash experiments/reuse_demo/launch_i2.sh verified [draw ...]
#                                                                 verified pass, its verifier gpt-oss:20b on that server
# I2_DRY_RUN=1 prints each command instead of running it (and writes nothing).
#
# The rules it holds (D160 (14), Q-I2e O-a: "generate now on the laptop beside K1, one process at a time, only with
# 2 GB free after the smoke"):
#   - one generation process at a time: each config runs after the previous one ended, and i2_generate.py holds a lock
#     (a second process exits 75);
#   - free memory (experiments/reuse_demo/i2_memory.py: vm_stat free+inactive+speculative+purgeable, as G4's launcher)
#     must be at least I2_MIN_FREE_GB (default 2) before each process, and i2_generate.py reads it again before each
#     answer starts and stops the run (exit 4, nothing lost; `resume` goes on) when it is under;
#   - `run` and `resume` refuse unless the last smoke ended with exit 0, its answer stored without an error, and its
#     lowest free memory at or above the floor (i2_generate.jsonl, memory_ok);
#   - K1's busy guard on the laptop (findings/recompute/K1/run_k1_laptop.sh:18) counts any process naming
#     exp_[0-9]+...py or its port; no command here does: the driver loads exp_01 by file, and the five configs name
#     NO_SERVER_URL, where nothing listens (OLLAMA_BASE_URL too). verified_pass calls the laptop's server, so
#     `verified` refuses while a K1 launcher runs here, as the judge (i2_judge.py) does.
#
# The store. build_index.py builds i2_plant5 into $ORIGINAL (a new store; never opened by a run). `stores` makes one
# copy per config, $STORES/<config> (cp -c, APFS clones), each checked file by file against the original and written
# with clone.sha256, as T2's make_store_t2.sh does: opening a store rewrites part of it (B9 F10), so no two runs share
# one and the original stays as built.
#
# Records: one start and one end line per process in $RUNS/i2_records.jsonl (commit, dirty count, lock and key
# sha256, store, command, exit); the driver's own line, with the memory readings, in $RUNS/i2_generate.jsonl; logs
# in $RUNS/logs/. Sinks: $RUNS/sinks/exp_01__<config>__i2_plant5/, the smoke's in $RUNS/smoke_sinks/.
set -u
HERE=$(cd "$(dirname "$0")" && pwd -P)
REPO=${I2_CLONE:-$(cd "$HERE/../.." && pwd -P)}
cd "$REPO" || { echo "refused: no repository at $REPO"; exit 1; }
export PATH=/opt/homebrew/bin:$HOME/.local/bin:$PATH PYTHONDONTWRITEBYTECODE=1
RUNS=${I2_RUNS_DIR:-findings/recompute/I2_runs}
STORES=${I2_STORES:-$HOME/paper_store_i2}
ORIGINAL=${I2_ORIGINAL:-$STORES/original}
GATE_STORE=${I2_GATE_STORE:-$STORES/gate_s20}
PAPERS20=${I2_PAPERS20:-$HOME/projects/Mentori-paper/datasets/v4_papers/core}
CORPUS=experiments/reuse_demo/corpus/core
MANIFEST=experiments/reuse_demo/corpus_papers.csv
INDEX=i2_plant5
PLANT_MANIFEST=2cf6bf6f04f64a4c5bbdd1d4abb5c9dcdb5969b6a3c750e1a305cc9f96449615   # build_index.py PLANT_MANIFEST
MIN_FREE_GB=${I2_MIN_FREE_GB:-2}
NO_SERVER_URL=http://127.0.0.1:11499
NO_SERVER_CONFIGS="single_pass multi_hop rlm_5 rlm_10 rlm_20"
ALL_CONFIGS="$NO_SERVER_CONFIGS verified_pass"
K1_RUNNING=${I2_K1_PATTERN:-'[r]un_k1_laptop\.sh|[k]1_autorestart'}   # t2_lib.sh's laptop pattern; tests name their own
UVM="uv run --project experiments/mentori --frozen python"
UVR="uv run --frozen python"
DRIVER=${I2_DRIVER:-"$UVM experiments/reuse_demo/i2_generate.py"}       # tests name a stub
BUILDER=${I2_BUILDER:-"$UVM experiments/reuse_demo/build_index.py"}
MEMORY=${I2_MEMORY:-"$UVR experiments/reuse_demo/i2_memory.py"}
RECORDS=$RUNS/i2_records.jsonl
GEN_RECORDS=$RUNS/i2_generate.jsonl
LOGS=$RUNS/logs

say() { echo "$(date +%H:%M:%S) $*"; }
refuse() { echo "refused: $*"; exit 1; }
utc() { date -u +%FT%TZ; }
sha() { shasum -a 256 "$@"; }
hash_tree() { (cd "$1" && find mentori_app.db chroma_db -type f | LC_ALL=C sort | while read -r f; do sha "$f"; done); }
is_config() { case " $ALL_CONFIGS " in *" $1 "*) return 0;; esac; return 1; }
k1_here() { pgrep -f "$K1_RUNNING" > /dev/null 2>&1; }
i2_running() { pgrep -f "${I2_JOB_PATTERN:-[i]2_generate\.py}" > /dev/null 2>&1; }
dry() { [ -n "${I2_DRY_RUN:-}" ]; }
mem_ok() { $MEMORY --floor-gb "$MIN_FREE_GB"; }
check_draws() { for d in "$@"; do case $d in 1|2|3) ;; *) refuse "draw '$d' is not 1, 2 or 3";; esac; done; }

# last_smoke: exit 0 when the last smoke line of i2_generate.jsonl ended with exit 0 and memory_ok true, and the smoke
# sink's answer is stored without an error; prints why not otherwise
last_smoke() {
  $UVR - "$GEN_RECORDS" "$RUNS/smoke_sinks/exp_01__single_pass__$INDEX.smoke/answers.jsonl" <<'PY'
import json, sys
from pathlib import Path
rec, ans = Path(sys.argv[1]), Path(sys.argv[2])
lines = [json.loads(x) for x in rec.read_text().splitlines() if x.strip()] if rec.exists() else []
smokes = [x for x in lines if x.get("smoke")]
if not smokes:
    sys.exit(print(f"no smoke recorded in {rec}") or 1)
s = smokes[-1]
if s.get("exit") != 0 or s.get("memory_ok") is not True:
    sys.exit(print(f"the last smoke ({s.get('start')}) ended with exit {s.get('exit')}, memory_ok {s.get('memory_ok')}, "
                   f"lowest free {(s.get('memory') or {}).get('min_free_gb')} GB") or 1)
last = {}
for x in (ans.read_text().splitlines() if ans.exists() else []):
    if x.strip():
        r = json.loads(x)
        last[r["answer_key"]] = r
if len(last) != 1 or any((r.get("generation") or {}).get("error") for r in last.values()):
    sys.exit(print(f"the smoke sink {ans} holds {len(last)} answers, or its answer stores an error") or 1)
print(f"smoke {s.get('start')}: exit 0, lowest free memory {s['memory']['min_free_gb']} GB, answer stored")
PY
}

# start_line / end_line: the launcher's record of one process
start_line() {
  T0=$(utc)
  printf '{"job": "i2_%s", "mode": "%s", "start": "%s", "host": "%s", "commit": "%s", "dirty": %s, "lock_sha256": "%s", "key_sha256": "%s", "store": "%s", "uv_python": "%s", "cmd": "%s"}\n' \
    "$1" "$2" "$T0" "$(hostname -s)" "$(git rev-parse HEAD 2> /dev/null)" \
    "$(git status --porcelain experiments 2> /dev/null | wc -l | tr -d ' ')" "$(sha experiments/LOCK.toml | cut -c1-64)" \
    "$(sha experiments/reuse_demo/key_v1_1.json | cut -c1-64)" "$3" "${UV_PYTHON:-}" "$4" >> "$RECORDS"
}
end_line() { printf '{"job": "i2_%s", "mode": "%s", "start": "%s", "end": "%s", "rc": %s}\n' "$1" "$2" "$T0" "$(utc)" "$3" >> "$RECORDS"; }

# one_process <config> <mode> <driver options...>: one i2_generate.py process on that config's store
one_process() {
  local c=$1 mode=$2 url=$NO_SERVER_URL; shift 2
  local S=$STORES/$c
  [ "$c" = verified_pass ] && url=$I2_VERIFIER_URL
  local sinks=$RUNS/sinks; [ "$mode" = smoke ] && sinks=$RUNS/smoke_sinks
  local CMD="$DRIVER --configs $c --ollama-url $url --min-free-gb $MIN_FREE_GB --sink-root $sinks --record-file $GEN_RECORDS $*"
  if dry; then echo "DATABASE_URL=sqlite:///$S/mentori_app.db CHROMA_PERSIST_DIRECTORY=$S/chroma_db OLLAMA_BASE_URL=$url $CMD"; return 0; fi
  [ -f "$S/clone.sha256" ] || refuse "no checked store for $c at $S (launch_i2.sh stores)"
  i2_running && refuse "an I2 generation process runs already (one at a time, D160 (14))"
  mem_ok || refuse "free memory is under $MIN_FREE_GB GB; nothing started (D160 (14))"
  mkdir -p "$LOGS"
  start_line "$c" "$mode" "$S" "$CMD"
  local LOG=$LOGS/i2_${c}_${mode}_${T0//:/}.log
  DATABASE_URL=sqlite:///$S/mentori_app.db CHROMA_PERSIST_DIRECTORY=$S/chroma_db OLLAMA_BASE_URL=$url \
    $CMD > "$LOG" 2>&1 < /dev/null
  local rc=$?
  end_line "$c" "$mode" "$rc"
  say "$c $mode ended: exit $rc (log $LOG)"
  return $rc
}

# sequence <mode> <driver options...>: the five no-server configs, one after another; stops at the first that fails
sequence() {
  local mode=$1 rc; shift
  for c in $NO_SERVER_CONFIGS; do
    one_process "$c" "$mode" "$@"; rc=$?
    case $rc in
      0) ;;
      4) say "stopped for memory at $c: free memory went under $MIN_FREE_GB GB; nothing lost. Later: launch_i2.sh resume"; exit 4;;
      *) say "stopped: $c ended with exit $rc; the configs after it were not started"; exit "$rc";;
    esac
  done
}

mode=${1:-check}; shift 2> /dev/null || true
case $mode in
  check)
    echo "repository $REPO at $(git rev-parse --short HEAD 2> /dev/null); lock $(sha experiments/LOCK.toml | cut -c1-12)"
    echo "key: $($UVR experiments/reuse_demo/plant_key.py | grep -E '"(sha256|n_questions)"' | tr -s ' \n' ' ')"
    [ -f "$HOME/.config/mentori-runs/keys.env" ] && echo "ok: Gemini key file present (not read)" || echo "MISSING: ~/.config/mentori-runs/keys.env"
    [ -f "$RUNS/index_gate.json" ] && echo "index gate: $(grep -o '"passed": [a-z]*' "$RUNS/index_gate.json" | head -1)" || echo "index gate: not run (index-gate)"
    [ -f "$RUNS/index_$INDEX.json" ] && echo "index $INDEX: $(grep -o '"ok": [a-z]*' "$RUNS/index_$INDEX.json" | head -1), store $ORIGINAL" || echo "index $INDEX: not built (index-build)"
    for c in $ALL_CONFIGS; do [ -f "$STORES/$c/clone.sha256" ] && echo "ok: store $STORES/$c" || echo "no store $STORES/$c (stores)"; done
    mem_ok; k1_here && echo "K1 runs on this machine: verified pass and the judge wait" || echo "no K1 launcher here"
    i2_running && echo "an I2 generation process runs now" || echo "no I2 generation process runs"
    last_smoke || true
    exit 0;;
  index-gate)
    CMD="$BUILDER gate --papers-dir $PAPERS20 --store $GATE_STORE --min-free-gb $MIN_FREE_GB"
    dry && { echo "$CMD"; exit 0; }
    mkdir -p "$RUNS"; start_line index_gate gate "$GATE_STORE" "$CMD"; $CMD; rc=$?; end_line index_gate gate $rc; exit $rc;;
  index-build)
    CMD="$BUILDER build --corpus $CORPUS --manifest $MANIFEST --index $INDEX --store $ORIGINAL --min-free-gb $MIN_FREE_GB --expect-manifest $PLANT_MANIFEST"
    dry && { echo "$CMD"; exit 0; }
    mkdir -p "$RUNS"; start_line index_build build "$ORIGINAL" "$CMD"; $CMD; rc=$?; end_line index_build build $rc; exit $rc;;
  stores)
    [ -f "$ORIGINAL/mentori_app.db" ] && [ -d "$ORIGINAL/chroma_db" ] || refuse "$ORIGINAL has no mentori_app.db and chroma_db (index-build)"
    i2_running && refuse "an I2 generation process runs: a store is never made under a running job"
    for c in $ALL_CONFIGS; do
      S=$STORES/$c
      if [ -f "$S/clone.sha256" ]; then say "$c: made already"; continue; fi
      [ -e "$S" ] && refuse "$S exists without clone.sha256 (a failed copy, left for inspection)"
      if dry; then echo "cp -c $ORIGINAL/{mentori_app.db,chroma_db} $S/"; continue; fi
      mkdir -p "$S"
      hash_tree "$ORIGINAL" > "$S/originals_before.sha256" || refuse "could not hash $ORIGINAL"
      cp -c "$ORIGINAL/mentori_app.db" "$S/" && cp -c -R "$ORIGINAL/chroma_db" "$S/" || refuse "cp -c failed for $c"
      hash_tree "$ORIGINAL" > "$S/originals_after.sha256"
      hash_tree "$S" > "$S/copy.sha256"
      cmp -s "$S/originals_before.sha256" "$S/originals_after.sha256" || refuse "$c: the original changed during the copy"
      cmp -s "$S/originals_before.sha256" "$S/copy.sha256" || refuse "$c: the copy differs from the original"
      mv "$S/copy.sha256" "$S/clone.sha256"
      say "$c: $S, $(wc -l < "$S/clone.sha256" | tr -d ' ') files equal to the original"
    done
    exit 0;;
  smoke)
    # exp_01 refuses a second start over a stored answer; say so here rather than in the log (move the sink aside to
    # smoke again, e.g. after K1 ends when the first smoke's memory_ok was false)
    SMOKE_ANSWERS=$RUNS/smoke_sinks/exp_01__single_pass__$INDEX.smoke/answers.jsonl
    dry || { [ -s "$SMOKE_ANSWERS" ] && refuse "a smoke answer is stored already ($SMOKE_ANSWERS); move that sink aside to smoke again"; }
    one_process single_pass smoke --smoke; exit $?;;
  run|resume)
    draws=${*:-1 2 3}; check_draws $draws
    dry || last_smoke || refuse "no passed smoke (Q-I2e: generate only with 2 GB free after the smoke)"
    opts="--draws $draws"; [ "$mode" = resume ] && opts="$opts --resume --skip-failed"
    sequence "$mode" $opts;;
  verified)
    draws=${*:-1 2 3}; check_draws $draws
    [[ ${I2_VERIFIER_URL:-} =~ ^http://127\.0\.0\.1:[0-9]+$ ]] || refuse "verified needs I2_VERIFIER_URL=http://127.0.0.1:<port>"
    k1_here && refuse "a K1 launcher runs on this machine: verified pass calls the laptop's Ollama server; wait for K1's share to end"
    dry || last_smoke || refuse "no passed smoke"
    opts="--draws $draws"; [ -n "${I2_RESUME:-}" ] && opts="$opts --resume --skip-failed"
    one_process verified_pass verified $opts; exit $?;;
  *) echo "usage: launch_i2.sh check|index-gate|index-build|stores|smoke|run|resume|verified [draw ...]"; exit 2;;
esac
