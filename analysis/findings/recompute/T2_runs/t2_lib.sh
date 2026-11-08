# T2, the other generators of Figure 2 panel f (D77, D83 Q173 to Q182, D142, D158): exp_01 with --generator
# T2_GENERATOR, the six configs, the 135 questions, index exp_v4_s20_n0, as G1 ran gemini-3-flash-preview. Sourced by
# launch_t2.sh, run_t2.sh, make_store_t2.sh and preflight.sh (never run alone). README.md beside this file says why it
# runs on the Studio and what each step does.
#
# The generator (T2_GENERATOR, D158 (1)): anthropic::claude-haiku-4-5 (the default, D142) or gemini::gemini-2.5-pro
# (D83 Q175, D158). Each has its own clone, its own stores and its own key name, so no generator's process reads,
# writes or stops another's (t2_pids names the generator).
#
# The clone. Each generator runs from its own clone on the Studio (T2_CLONE; default ~/projects/mentori-runs-t2 for
# claude-haiku-4-5, ~/projects/mentori-runs-t2g for gemini-2.5-pro), made once at a commit that holds this folder
# (README "Before the first start"). exp_01 writes every answer and call into
# findings/runs/exp_01__<config>__exp_v4_s20_n0+<model>/ in that clone (the smokes under $D/smoke_sinks).
#
# The stores. One APFS clone per config of the Studio's originals (~/projects/Mentori: mentori_app.db and chroma_db,
# the store G1 to G5 cloned, so T2 reads G1's collection and its passage ids pair with G1's), $STORES/<config>, made
# by make_store_t2.sh and checked file by file against the originals: a store open rewrites part of a store (B9 F10),
# so no two processes share one: each generator has its own ($STORES, default
# ~/paper_store_t2 for claude-haiku-4-5, ~/paper_store_t2g for gemini-2.5-pro).
#
# The server. Five configs make no Ollama call (the generator is a cloud model, the encoders run in-process on CPU,
# LOCK [retrieval] device cpu), so they name 11499, where nothing listens on the Studio (G9 named it the same way,
# G3_runs/stress_g3.sh:20; preflight checks that nothing listens). verified_pass calls its verifier,
# gpt-oss:20b-date20261010, on T2_VERIFIER_PORT, which Valerio assigns (README Q-V): launch_t2.sh verified refuses a
# port on RESERVED, the guarded and other jobs' ports of experiments/NOW.md's standing rules, unless
# T2_VERIFIER_DECISION names the decision that frees it.
#
# The local lane (D158 (2), D159 (2)): ollama::gemma3:27b or ollama::qwen3-coder:30b, run by launch_t2_local.sh only
# (launch_t2.sh refuses them). Each has its own clone (~/projects/mentori-runs-t2-<model>) and stores
# (~/paper_store_t2-<model>), no key, and one Studio Ollama server, T2_GENERATOR_PORT, that answers the generator and
# verified_pass's verifier both (Q-L2's advice, D159 (2)). A port on RESERVED needs T2_GENERATOR_DECISION=D<n>, the
# decision that frees it (D159 (3): the ports D157's T2 judging frees).
T2_GENERATOR=${T2_GENERATOR:-anthropic::claude-haiku-4-5}
LOCAL=""
case $T2_GENERATOR in
  anthropic::claude-haiku-4-5)
    CLONE_DEFAULT=$HOME/projects/mentori-runs-t2;  STORES_DEFAULT=$HOME/paper_store_t2;  KEY_NAME=ANTHROPIC_API_KEY;;
  gemini::gemini-2.5-pro)
    CLONE_DEFAULT=$HOME/projects/mentori-runs-t2g; STORES_DEFAULT=$HOME/paper_store_t2g; KEY_NAME=GEMINI_API_KEY;;
  ollama::gemma3:27b|ollama::qwen3-coder:30b)
    LOCAL=1; slug=$(printf '%s' "${T2_GENERATOR#*::}" | tr ':/' '--')
    CLONE_DEFAULT=$HOME/projects/mentori-runs-t2-$slug; STORES_DEFAULT=$HOME/paper_store_t2-$slug; KEY_NAME="";;
  *) echo "refused: T2_GENERATOR is '$T2_GENERATOR', not anthropic::claude-haiku-4-5, gemini::gemini-2.5-pro," \
          "ollama::gemma3:27b or ollama::qwen3-coder:30b"; exit 1;;
esac
# launch_t2.sh has no survey, two-model load or generator server: a local generator through it would start exp_01
# without its server checked, so it refuses (the cloud lane is unchanged)
[ -n "$LOCAL" ] && [ "${0##*/}" = launch_t2.sh ] \
  && { echo "refused: $T2_GENERATOR is a local generator: launch_t2_local.sh runs it (launch_t2.sh is the cloud lane)"; exit 1; }
# D160 (3) replaced Q-L1's option T2_RESUME_RERUN_FAILED, which reran every failed key (a turn cap's and a prompt over
# the context's included): the local lane's resume now always reruns our own server's failures and nothing else
# (run_t2.sh). A script that still sets it is refused, so nobody believes it does something.
[ -z "${T2_RESUME_RERUN_FAILED:-}" ] \
  || { echo "refused: T2_RESUME_RERUN_FAILED is gone (D160 (3)): launch_t2_local.sh resume reruns only a failure of our own Ollama server, with no option; unset it"; exit 1; }
GPORT=${T2_GENERATOR_PORT:-}           # the local lane's server (launch_t2_local.sh checks it); unset on the cloud lane
GURL=${GPORT:+http://127.0.0.1:$GPORT}
export T2_GENERATOR                   # check_t2.py reads it (its --generator default)
cd "${T2_CLONE:-$CLONE_DEFAULT}" 2> /dev/null \
    || { echo "refused: no T2 clone at ${T2_CLONE:-$CLONE_DEFAULT} (t2_lib.sh header)"; exit 1; }
export PATH=/opt/homebrew/bin:$HOME/.local/bin:$PATH PYTHONDONTWRITEBYTECODE=1
D=findings/recompute/T2_runs
EXP01=experiments/mentori/publication/scripts/exp_01_generation.py
GENERATOR=$T2_GENERATOR
TAG=+$(printf '%s' "${GENERATOR#*::}" | tr ':/' '--')   # exp_01's generator_tag: every T2 run_id is exp_01__<config>__$INDEX$TAG
INDEX=exp_v4_s20_n0
LOCK_WANT=d66daa28596bf3b70ff90e0fb89b1353eab023eba699427cb05ebb3376105c12   # LOCK.toml since 17 Oct 16:30 (D85)
NO_SERVER_CONFIGS="single_pass multi_hop rlm_5 rlm_10 rlm_20"
ALL_CONFIGS="$NO_SERVER_CONFIGS verified_pass"
NO_SERVER_URL=http://127.0.0.1:11499  # nothing listens there (preflight); no call goes there
VERIFY_MODEL=gpt-oss:20b              # exp_01 VERIFY_MODEL; the lock sends the date-fixed copy ([date])
# D98's subset (S464's 45 questions), through exp_01 --question-ids-file, into the runs and answer keys of all 135:
# a Gemini generator's draws 2 and 3 (D98, D159 (2): the Gemini cost; its draw 1 runs all 135), and a local generator's
# RLM set-ups rlm_5, rlm_10 and rlm_20 at every draw (D175 Q3, Valerio 30 Oct: gemma3:27b's RLM set-ups, 21 of 405
# draw-1 answers in about 31 h, end in time on the 45; the paper says so; D176, Valerio 30 Oct: qwen3-coder:30b's too,
# the rule is the local lane's; answers stored outside the 45 stay on disk). Every other config, draw and generator
# (claude-haiku-4-5; a local generator's single_pass, multi_hop and verified_pass) runs all 135. One process never mixes
# draw 1 with draws 2 or 3 of a Gemini generator (launch_t2.sh and run_t2.sh refuse it). check_t2.py subset_draws holds
# the same rule for the draw gate, progress and the plan, and check_t2_subset_test.py holds the two equal.
D98_SUBSET=findings/recompute/D98_subset/d98_subset.json
SUBSET_LOCAL_CONFIGS="rlm_5 rlm_10 rlm_20"   # D175 Q3, D176: the local lane's RLM set-ups (check_t2.py)
subset_gen() { case $GENERATOR in gemini::*) return 0;; esac; return 1; }
# subset_mix <draws...>: true when a Gemini generator's draws name draw 1 together with draw 2 or 3
subset_mix() { subset_gen && printf '%s\n' "$@" | grep -qx 1 && printf '%s\n' "$@" | grep -qx '[23]'; }
# subset_for <config> <draws...>: true when this process runs D98's subset (run_t2.sh adds --question-ids-file):
# a local generator's RLM set-up at any draw (D175 Q3, D176: gemma3:27b and qwen3-coder:30b), or a Gemini generator's
# draws without draw 1 (D98, D159 (2))
subset_for() {
  local c=$1; shift
  [ -n "$LOCAL" ] && case " $SUBSET_LOCAL_CONFIGS " in *" $c "*) return 0;; esac
  subset_gen && ! printf '%s\n' "$@" | grep -qx 1
}
# experiments/NOW.md standing rules, 26 Oct: Studio 11434 (never), K1 11441 11451 11456, S3 11453 11455, S18f 11452
# (ended; idle by D120; since D143 the verifier of claude-haiku-4-5's verified_pass), T1 11454, Valerio's 11460 to 11463 and 11470
RESERVED="11434 11441 11451 11452 11453 11454 11455 11456 11460 11461 11462 11463 11470"
# The machine (T2_MACHINE, default studio; README "Where it runs"). Off the Studio the store is the laptop's own copy of
# the index (~/projects/Mentori-paper/data: G1's chunk texts, other chroma ids), on the Beelink pushed from the laptop
# (make_store_t2.sh push-beelink), and no T2 process may run while a K1 launcher runs there: K1's busy guard counts
# any exp_NN process as a user of its server and stops K1 at its next fresh load (K1/run_k1_laptop.sh:18-19,
# K1/run_k1_beelink.sh:37-38).
T2_MACHINE=${T2_MACHINE:-studio}
case $T2_MACHINE in
  studio)  ORIG_DEFAULT=$HOME/projects/Mentori;            CP="cp -c"; K1_RUNNING='[r]un_k1_studio\.sh';;
  laptop)  ORIG_DEFAULT=$HOME/projects/Mentori-paper/data; CP="cp -c"; K1_RUNNING='[r]un_k1_laptop\.sh|[k]1_autorestart';;
  beelink) ORIG_DEFAULT=$HOME/paper_store_t2_orig;         CP="cp";    K1_RUNNING='[r]un_k1_beelink\.sh';;
  *) echo "refused: T2_MACHINE is '$T2_MACHINE', not studio, laptop or beelink"; exit 1;;
esac
K1_RUNNING=${T2_K1_PATTERN:-$K1_RUNNING}   # tests name a pattern of their own; never set it for a run
STORES=${T2_STORES:-$STORES_DEFAULT}
ORIG=${T2_ORIGINAL_STORE:-$ORIG_DEFAULT}
G1_SINKS=${T2_G1_SINKS:-$HOME/projects/mentori-runs/findings/runs}   # G1's runs, read only (index identity)
RECORDS=$D/t2_records.jsonl           # one start and one end line per process, appended, never rewritten
LOGS=$D/logs
NTFY=https://ntfy.sh/mentori_alert_system   # public: counts only
[ "$GENERATOR" = anthropic::claude-haiku-4-5 ] && POST_TAG="" || POST_TAG=" $TAG"   # Haiku's messages as before
SERVE_LOG_DIR=${T2_SERVE_LOG_DIR:-$HOME/ollama_logs}   # serve_<port>.log, each Studio server's log (tests name their own)
OLLAMA_BIN=/opt/homebrew/opt/ollama/bin/ollama        # the Studio's binary, checked against LOCK [server] binary_sha256

say() { echo "$(date +%H:%M:%S) $*"; }
refuse() { echo "refused: $*"; exit 1; }
# The message goes on curl's stdin, never its command line (T1's 22 Oct lesson: a message on argv is seen by guards)
post() { [ -n "${T2_DRY_RUN:-}" ] || printf '%s' "T2$POST_TAG $*" | curl -s -m 20 --data-binary @- $NTFY > /dev/null; }
sha() { if command -v shasum > /dev/null; then shasum -a 256 "$@"; else sha256sum "$@"; fi; }
hash_tree() { (cd "$1" && find mentori_app.db chroma_db -type f | LC_ALL=C sort | while read -r f; do sha "$f"; done); }
is_config() { case " $ALL_CONFIGS " in *" $1 "*) return 0;; esac; return 1; }
# A running T2 exp_01 (the bracket keeps this pgrep's own command line from matching itself or any guard's pattern)
# T2_JOB_PATTERN: tests name a pattern of their own, so a live T2 run on the machine does not answer their guards
# (check_t2_test.py on the Studio, 27 Oct, while Haiku ran); never set it for a run
t2_pids() { pgrep -f "${T2_JOB_PATTERN:-[e]xp_01_generation\.py --generator $GENERATOR${1:+ .*--configs $1( |$)}}" 2> /dev/null; }
utc() { date -u +%FT%TZ; }
# Off the Studio: a K1 launcher on this machine (its guard would stop K1 at its next fresh load while T2 runs)
k1_here() { [ "$T2_MACHINE" = studio ] && return 1; pgrep -f "$K1_RUNNING" > /dev/null 2>&1; }
