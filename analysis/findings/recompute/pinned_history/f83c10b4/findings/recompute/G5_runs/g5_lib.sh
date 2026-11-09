# G5 (plan row G5; Figure 3, depth sweep: exp_06, Mentori's RLM at 10 turn caps on depth_sweep86, gemini, three
# draws), sourced by launch_g5.sh, run_g5.sh and make_store_g5.sh (never run alone). It moves to the G5 clone.
#
# The clone. G5 runs from its own clone, ~/projects/mentori-runs-g5 (G5_CLONE), never from ~/projects/mentori-runs
# (G2's) or G4's. Made once on the Studio:
#   git clone https://github.com/vbianchi/Mentori-reanalysis.git ~/projects/mentori-runs-g5
#   cd ~/projects/mentori-runs-g5 && uv sync --frozen && uv sync --frozen --project experiments/mentori
# exp_06 writes its answers into the clone: experiments/mentori/publication/scripts/results_v4/
# v4_9_depth_sweep_depthsweep86_gemini-3-flash-preview_127.0.0.1-<run port>_<UTC>.json (and _latest.json; draw 1's
# files name 11453), the whole list rewritten after every answer, and every call into
# findings/runs/exp_06_depth_sweep__rlm_<depth>__depthsweep86/. exp_06's resume and check_g5.py read the files
# whatever port they name.
#
# The store. One APFS clone of Mentori's database and vector store, ~/paper_store_g5 (make_store_g5.sh): exp_06 loads
# the index for every answer (RLMContext.from_index), and an open rewrites part of the store (B9 F10).
#
# Shares (D95 Q213). G5 runs as PARTS processes at once (g5_queue.sh), process k running share k of PARTS of the
# questions (exp_06 --part k/PARTS: the questions at positions k, k+PARTS, ... of depth_sweep86, experiment.share), one
# answer at a time in exp_06's order (question, then depth), one draw per phase: every share ends draw d and the gate
# (check_g5.py complete --draws 1 .. d) passes before any share starts draw d+1 (D78 Q116 across the processes). Each
# answer is exactly the answer one process would run (same run context, settings and seed). Each share opens its own
# store clone, $STORES/p<k> (make_store_g5.sh shares <PARTS>), as G4 gives each process its own (B9 F10, B9 D3).
# The run port (D115 PQ9 O-a, D172 G7-Q1). --base-url names a port for the run contexts only; every call goes to Gemini
# and nothing contacts it. But experiments/runner/server_users.py:103-109 counts any process whose command line names a
# port as a user of it, so a G5 process naming 11453 (as draw 1 did, after B9's exp_06 smoke and G1) would hold T2's
# judge there. G5_RUN_PORT names an idle port instead, with no default: run_g5.sh, g5_queue.sh and launch_g5.sh refuse
# it unset, not a number, 11434 or 11453 (RESERVED_PORTS; run_port_why, so a start that skips the launcher refuses the
# reserved ports too, D1 of the G7 verifier), launch_g5.sh also a port with a listener, and the launch record keeps it.
cd "${G5_CLONE:-$HOME/projects/mentori-runs-g5}" 2> /dev/null \
    || { echo "refused: no G5 clone at ${G5_CLONE:-$HOME/projects/mentori-runs-g5} (g5_lib.sh header)"; exit 1; }
export PATH=/opt/homebrew/bin:$HOME/.local/bin:$PATH PYTHONDONTWRITEBYTECODE=1
D=findings/recompute/G5_runs
EXP06=experiments/mentori/publication/scripts/exp_06_depth_sweep.py
RESULTS=experiments/mentori/publication/scripts/results_v4
S=${G5_STORE:-$HOME/paper_store_g5}
ORIG=${G5_ORIGINAL_STORE:-$HOME/projects/Mentori}
LOCK_WANT=d66daa28596bf3b70ff90e0fb89b1353eab023eba699427cb05ebb3376105c12   # LOCK.toml since 17 Oct 16:30 (D85)
RUN_PORT=${G5_RUN_PORT:-}         # named for the run contexts only (exp_06: a Gemini run never contacts it); no default
BASE_URL=http://127.0.0.1:$RUN_PORT
RESERVED_PORTS="11434 11453"      # the Mentori web app's; T2's judge (D115 PQ9 O-a, D172 G7-Q1)
NO_RUN_PORT="G5_RUN_PORT is unset or not a port number ('$RUN_PORT'): name an idle port for the run contexts (no default since G7; D172 G7-Q1 keeps 11453 for T2)"
NTFY=https://ntfy.sh/mentori_alert_system   # public: counts only
export DATABASE_URL=sqlite:///$S/mentori_app.db CHROMA_PERSIST_DIRECTORY=$S/chroma_db
# The smoke: exp_06's --smoke (its 2 questions, which are depth_sweep86's first two; its own runs and files) at every
# depth the run reaches, so the deep caps (B9 F2 runaway replies, F3 Gemini's input limit) run before the run does
SMOKE_OPTS="--smoke --depths 1 2 3 5 7 10 15 20 30 50"
PARTS=${G5_PARTS:-4}              # D95 Q213: processes at once for the run (README "Several processes": the advice)
SMOKE_PARTS=${G5_SMOKE_PARTS:-2}  # the smoke's 2 questions as 2 shares, so the smoke runs the queue the run uses
STORES=${G5_STORES:-$HOME/paper_store_g5_shares}   # share k's store clone: $STORES/p<k>
START_GAP_S=${G5_START_GAP_S:-30} # between two share starts: the encoder and reranker loads do not coincide
POLL_S=${G5_POLL_S:-60}           # the queue looks at its processes this often
STOP=$D/STOP                      # present: no share starts and every running share stops before its next answer
# D284 (Valerio, 6 Nov 20:31, tab thread 80d30fe8-c1a2: "Go ahead. Can't we actually parallelize the call?"): with
# G5_D284=1 the run's draws 2 and 3 run on all 86 questions, as draw 1 does: no D98 subset file and no --subset, so
# every share's --resume skips the 29 subset questions G7 stored and runs the other 57 (1,140 answers); the plan and
# the gates count the full 2,580. Unset: D98 as before.
D284=${G5_D284:-}

say() { echo "$(date +%H:%M:%S) $*"; }
post() { [ -n "${G5_DRY_RUN:-}" ] || curl -s -m 20 -d "G5 $*" $NTFY > /dev/null; }
hash_tree() { (cd "$1" && find mentori_app.db chroma_db -type f | sort | xargs shasum -a 256); }
# run_port_why: why G5_RUN_PORT may not be the run port (nothing when it may): unset or not a number, or reserved
run_port_why() {
  [[ "$RUN_PORT" =~ ^[0-9]+$ ]] || { echo "$NO_RUN_PORT"; return; }
  case " $RESERVED_PORTS " in *" $RUN_PORT "*)
    echo "G5_RUN_PORT=$RUN_PORT is reserved (11434 the Mentori web app's; 11453 T2's judge, D115 PQ9 O-a, D172 G7-Q1): name an idle port";; esac
}
# port_listener <port>: the processes listening on it (command, pid), nothing when none
port_listener() { lsof -nP -iTCP:$1 -sTCP:LISTEN 2> /dev/null | awk 'NR > 1 {print $1, $2}' | sort -u | tr '\n' ' '; }
