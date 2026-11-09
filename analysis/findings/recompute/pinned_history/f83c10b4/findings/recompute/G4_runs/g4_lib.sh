# G4 (plan row G4; Figure 3, corpus scaling: exp_02 on the 12 indexes, three draws), sourced by launch_g4.sh,
# g4_queue.sh, run_g4.sh and make_stores_g4.sh (never run alone). It moves to the G4 clone and holds what they share.
#
# The clone. G4 runs from its own clone, ~/projects/mentori-runs-g4 (G4_CLONE), never from ~/projects/mentori-runs,
# where G2 runs (a clone running a job is never pulled; RUNNING.md). Made once on the Studio:
#   git clone https://github.com/vbianchi/Mentori-reanalysis.git ~/projects/mentori-runs-g4
#   cd ~/projects/mentori-runs-g4 && uv sync --frozen && uv sync --frozen --project experiments/mentori
# then moved only by `git pull --ff-only` while no G4 process runs (launch_g4.sh refuses a clone another job uses).
#
# The stores. One APFS clone of Mentori's database and vector store per index process, ~/paper_store_g4/<index>/
# (make_stores_g4.sh), so no two G4 processes open one store: an open rewrites chroma.sqlite3 and the segment (B9 F10),
# and twelve processes on one store were never tested (B9 D3). The originals, ~/projects/Mentori/mentori_app.db and
# chroma_db (plan row I1: all 12 indexes READY with S66's chunk counts; read again 17 Oct, 21:50 CEST), are only read.
#
# Order (D78 Q116): draw 1 on every index first, then draws 2 and 3, the 50-core indexes first. The queue runs three
# phases, draw 1, draw 2, draw 3, each complete on all 12 indexes before the next starts, so a progress look (D79)
# finds whole draws. ORDER is the order the queue starts the index processes in each phase: the three 50-core indexes, then 20, 10 and 5 core papers, the
# noisiest first within a size (the largest index first: the longest process starts first).
cd "${G4_CLONE:-$HOME/projects/mentori-runs-g4}" 2> /dev/null \
    || { echo "refused: no G4 clone at ${G4_CLONE:-$HOME/projects/mentori-runs-g4} (g4_lib.sh header)"; exit 1; }
export PATH=/opt/homebrew/bin:$HOME/.local/bin:$PATH PYTHONDONTWRITEBYTECODE=1
D=findings/recompute/G4_runs
EXP02=experiments/mentori/publication/scripts/exp_02_scaling_factorial.py
STORES=${G4_STORES:-$HOME/paper_store_g4}
ORIG=${G4_ORIGINAL_STORE:-$HOME/projects/Mentori}
LOCK_WANT=d66daa28596bf3b70ff90e0fb89b1353eab023eba699427cb05ebb3376105c12   # LOCK.toml since 17 Oct 16:30 (D85)
ORDER="exp_v4_s50_n3 exp_v4_s50_n1 exp_v4_s50_n0 exp_v4_s20_n3 exp_v4_s20_n1 exp_v4_s20_n0 exp_v4_s10_n3 exp_v4_s10_n1 exp_v4_s10_n0 exp_v4_s5_n3 exp_v4_s5_n1 exp_v4_s5_n0"
PORTS=${G4_PORTS:-}               # the verifier ports, no default (D172 G7-Q1, port plan PA4: 11453 is T2's since D115
                                  # PQ9 O-a; G7 runs on 11441 and 11456, PORT_PLAN.md:35,41). launch_g4.sh, g4_queue.sh
                                  # and run_g4.sh refuse while it is unset (need_ports); check_g4.py record too. A
                                  # second port only if Q152's timing test says so (D83 Q152; run and resume refuse
                                  # unless G4_Q152 names that test's report or a decision)
SUBSET=findings/recompute/D98_subset/d98_subset.json   # D98 (D112 Q11, G7): draws 2 and 3 on these 45 questions only
                                  # (scripts/S464_d98_subset.py writes and --check checks this one path, so no override)
MAX_PROCS=${G4_MAX_PROCS:-12}     # index processes at once (D80 V16: one per index)
MIN_FREE_GB=${G4_MIN_FREE_GB:-48} # memory a process may take before the next starts (vm_stat free+inactive+spec+purg)
START_GAP_S=${G4_START_GAP_S:-120}  # between two starts: the encoder and reranker loads do not coincide
POLL_S=${G4_POLL_S:-60}        # the queue looks at its processes this often
NICE=${G4_NICE:-10}               # D92 Q197: G4 gives way on the CPU (nice 10) so S2's 120 s notebook cells do not
export G4_NICE=$NICE              # time out under its load; exported so the launch record holds the value used.
                                  # G4_NICE=0 runs as G1 ran (not niced); search times are measured niced (Methods)
THREADS=${G4_THREADS:-}           # unset (D92 Q197: no cap): torch's own thread count, as G1 ran; a number caps each process's CPU threads
                                  # (OMP_NUM_THREADS, MKL_NUM_THREADS; README option, Valerio's call)
VERIFIER_MODEL=gpt-oss:20b        # the lock's verifier; [date] runs it as gpt-oss:20b-date20261010
VERIFIER_TAG=gpt-oss:20b-date20261010
OLLAMA_BIN=/opt/homebrew/opt/ollama/bin/ollama
NTFY=https://ntfy.sh/mentori_alert_system   # public: counts only
FORBIDDEN_PORTS="11434"           # the Mentori web app's server (RUNNING.md)

say() { echo "$(date +%H:%M:%S) $*"; }
post() { [ -n "${G4_DRY_RUN:-}" ] || curl -s -m 20 -d "G4 $*" $NTFY > /dev/null; }

# need_ports: refuses (exit 1) while G4_PORTS names no port (no default since G7; D172 G7-Q1)
need_ports() {
  [ -n "$(echo $PORTS)" ] || { echo "refused: G4_PORTS is unset: name the verifier ports (no default since G7; D172 G7-Q1 keeps 11453 for T2; G7's are 11441 and 11456, PORT_PLAN.md:35,41)"; exit 1; }
}

# port_of <index>: the verifier port the index's process names, the ports dealt in ORDER, round robin (none: exit 1)
port_of() {
  local idx=$1 i=0 n x
  n=$(echo $PORTS | wc -w | tr -d ' ')
  [ "$n" -gt 0 ] || return 1
  for x in $ORDER; do
    if [ "$x" = "$idx" ]; then echo $PORTS | tr -s ' ' '\n' | sed -n "$(( i % n + 1 ))p"; return 0; fi
    i=$((i + 1))
  done
  return 1
}

# avail_gb: what vm_stat reports free, inactive, speculative and purgeable, in GB (a new process can take it unpaged)
avail_gb() {
  vm_stat | awk '/page size of/ {ps = $8} /^Pages free/ {f = $3} /^Pages inactive/ {i = $3}
                 /^Pages speculative/ {s = $3} /^Pages purgeable/ {p = $3}
                 END {printf "%d\n", (f + i + s + p) * ps / 1073741824}'
}

# hash_tree <dir>: every file of a store, as make_store_g3.sh hashes it
hash_tree() { (cd "$1" && find mentori_app.db chroma_db -type f | sort | xargs shasum -a 256); }

# port_users <port>: prints why the port is not free for G4 (nothing when free): an established connection, or a model
# in /api/ps other than the verifier. Processes that only name the port are not counted: they name it for their run
# contexts and never contact it (G2 named 11453; since G7, G3 and G5 name their own idle ports, G3_RUN_PORT and
# G5_RUN_PORT; exp_01 matched_budget, exp_03, exp_06 send every call to Gemini).
port_users() {
  local p=$1 c ps
  c=$(lsof -nP -iTCP:$p -sTCP:ESTABLISHED 2> /dev/null | awk 'NR > 1' | wc -l | tr -d ' ')
  [ "$c" = 0 ] || echo "$c established connections on $p"
  ps=$(curl -s -m 10 http://127.0.0.1:$p/api/ps) || { echo "$p does not answer /api/ps"; return; }
  echo "$ps" | uv run --frozen python -c "import json, sys; d = json.load(sys.stdin); o = [m['name'] for m in d.get('models', []) if m['name'] != sys.argv[1]]; print('models loaded on $p besides the verifier: ' + ', '.join(o)) if o else None" "$VERIFIER_TAG" \
      || echo "$p's /api/ps unreadable"
}
