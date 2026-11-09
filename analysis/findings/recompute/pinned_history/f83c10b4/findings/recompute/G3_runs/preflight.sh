# G3 preflight, sourced by smoke_g3.sh, launch_g3.sh and gate_distiller.sh (not run alone). Defines the set-ups and
# the refusals every start makes before any process starts; each refusal stops the caller with nothing started.
#
# Set-ups (D83): Q148 leaves rlm_10 out of G3 (Figure 4 reuses Figure 2's RLM-10 answers, G1) and makes the distiller
# count a checkpoint before the two distiller set-ups; Q149 runs one process per set-up. WAVE1 starts at the launch,
# the full pipeline among them (Q148's "first" is tied to the count, by the card's own reason: README);
# WAVE2 starts only from gate_distiller.sh, after the full pipeline's 405 answers are
# counted (Q82, D75). raw_gemini and naive_rag are the two descriptive baselines (D79 Q134; LIST.md Rule 12).
# Since D98 wave 1 ended at draw 1 (19 Oct) and the count was 0 (D154 Q1: no wave 2); launch_g3.sh now starts G7 only,
# draws 2 and 3 of D98's subset on the set-ups G3_G7_SETUPS names (g7_setups below; README, G7).
WAVE1="raw_gemini naive_rag full_orchestrator orch_no_analyser orch_no_planner orch_no_supervisor orch_no_synthesiser orch_factual_to_documents"
WAVE2="orch_no_distiller orch_distiller_f1"
# G7 (D98, D112 Q11; F8 of the G7 review): draws 2 and 3 on D98's subset only, set-ups named by G3_G7_SETUPS (g7_setups).
STRESS_SETUPS="orch_distil_every_step orch_distil_every_step_f1"   # stress_g3.sh's STRESS (D75 Q82; A1, 24 Oct)
SUBSET=findings/recompute/D98_subset/d98_subset.json   # D98's 45 questions (scripts/S464_d98_subset.py writes and
                                                      # --check checks this one path, so no override)
EXP03=experiments/mentori/publication/scripts/exp_03_orchestration_ablation.py
DISTILLER=experiments/mentori/orchestrator/distiller_firing.py   # gate_distiller.sh loads it to decide WAVE2 (D112 Q16)

# The clone: G3_CLONE must name G3's own clone (~/projects/mentori-runs-g3, made with uv sync --frozen). It has no
# default: the old default was ~/projects/mentori-runs, G2's clone, which is never pulled while G2 runs, and one
# forgotten export would have run G3 there. Exported, so every process this starts (run_g3.sh) is in the same clone.
[ -n "${G3_CLONE:-}" ] || { echo "refused: G3_CLONE is unset; export G3_CLONE=~/projects/mentori-runs-g3 (G3's own clone)"; exit 1; }
cd "$G3_CLONE" || exit 1
[ "$(pwd -P)" = "$(cd "$HOME/projects/mentori-runs" 2> /dev/null && pwd -P)" ] \
    && { echo "refused: G3_CLONE is ~/projects/mentori-runs, G2's clone; G3 runs from its own"; exit 1; }
export G3_CLONE
export PATH=/opt/homebrew/bin:$HOME/.local/bin:$PATH PYTHONDONTWRITEBYTECODE=1
export G3_STORE=${G3_STORE:-$HOME/paper_store_g3}
export DATABASE_URL=sqlite:///$G3_STORE/mentori_app.db CHROMA_PERSIST_DIRECTORY=$G3_STORE/chroma_db
D=findings/recompute/G3_runs
refuse() { echo "refused: $*"; exit 1; }

# Runs start on committed code: no tracked file under experiments/ differs from HEAD (the RUNNING.md B4 slip, 16 Oct).
git diff --quiet HEAD -- experiments || refuse "tracked files under experiments/ differ from HEAD $(git rev-parse --short HEAD)"
grep -q 'parser.add_argument("--question-ids"' $EXP03 || refuse "exp_03 at $(git rev-parse --short HEAD) has no --question-ids (Q147)"
[ -f findings/recompute/G3_runs/smoke_ids.py ] && [ -f $D/start_record.py ] && [ -f $D/run_g3.sh ] \
    || refuse "$D lacks smoke_ids.py, start_record.py or run_g3.sh at this commit"
[ -f "$G3_STORE/clone.sha256" ] && [ -f "$G3_STORE/mentori_app.db" ] && [ -d "$G3_STORE/chroma_db" ] \
    || refuse "no G3 store at $G3_STORE (run make_store_g3.sh first)"
[ -f "$HOME/.config/mentori-runs/keys.env" ] || refuse "no keys file (its presence is checked, never its content)"

# The run port (D115 PQ9 O-a, D172 G7-Q1). exp_03 needs --base-url (the Ollama server its run contexts name) and sends
# every call to Gemini, so the port is never contacted; but experiments/runner/server_users.py:103-109 counts any
# process whose command line names a port as a user of it, so a G3 process naming 11453 (as wave 1 did) would hold
# T2's judge there. G3_RUN_PORT names an idle port instead, with no default; run_g3.sh refuses while it is unset.
# run_port_free: refuses unless G3_RUN_PORT is a port number, not 11434 (the Mentori web app's) or 11453 (T2's), with
# no process listening on it (lsof). Called by smoke_g3.sh, launch_g3.sh and gate_distiller.sh before anything starts;
# start_record.py writes the port into every launch and job record. stress_g3.sh does not call it: its runner names
# 11499 itself (its header).
RESERVED_PORTS="11434 11453"
run_port_free() {
    [[ "${G3_RUN_PORT:-}" =~ ^[0-9]+$ ]] \
        || refuse "G3_RUN_PORT is unset or not a port number ('${G3_RUN_PORT:-}'): name an idle port for the run contexts (no default since G7; D172 G7-Q1 keeps 11453 for T2)"
    case " $RESERVED_PORTS " in *" $G3_RUN_PORT "*)
        refuse "G3_RUN_PORT=$G3_RUN_PORT is reserved (11434 the Mentori web app's; 11453 T2's judge, D115 PQ9 O-a, D172 G7-Q1): name an idle port";; esac
    local l
    l=$(lsof -nP -iTCP:$G3_RUN_PORT -sTCP:LISTEN 2> /dev/null | awk 'NR > 1 {print $1, $2}' | sort -u | tr '\n' ' ')
    [ -z "$l" ] || refuse "run port $G3_RUN_PORT has a listener ($l): exp_03 names it for its run contexts, so it must be an idle port"
    export G3_RUN_PORT
}

# g7_setups: the set-ups G7 runs, from G3_G7_SETUPS, into CONFIGS. Required, no default: how many G3 set-ups G7 runs
# was G7-Q2, which D173 answered: the six wave-1 ablations and the two stress set-ups (README, G7). Refuses it
# unset, a name given twice, a WAVE2 name (the distiller count was 0, D154 Q1: wave 2 does not exist) and any name not
# in WAVE1 or STRESS_SETUPS.
g7_setups() {
    [ -n "$(echo ${G3_G7_SETUPS:-})" ] || refuse "G3_G7_SETUPS is unset: name the set-ups G7 runs (no default; D173 on G7-Q2: the six wave-1 ablations and the two stress set-ups; README, G7)"
    local c seen=" "
    for c in $G3_G7_SETUPS; do
        case "$seen" in *" $c "*) refuse "G3_G7_SETUPS names $c twice";; esac
        seen="$seen$c "
        case " $WAVE2 " in *" $c "*) refuse "G3_G7_SETUPS names $c, of WAVE2: the distiller count was 0 (D154 Q1), so wave 2 does not exist";; esac
        case " $WAVE1 $STRESS_SETUPS " in *" $c "*) ;; *) refuse "G3_G7_SETUPS names $c, not a set-up of WAVE1 or STRESS_SETUPS";; esac
    done
    CONFIGS=$(echo $G3_G7_SETUPS)
}

# store_hashes <name>: every file of the store, hashed as make_store_g3.sh hashes it; exported for the start records.
store_hashes() {
    (cd "$G3_STORE" && find mentori_app.db chroma_db -type f | sort | xargs shasum -a 256) > "$D/store_at_$1.sha256" \
        || refuse "could not hash the store"
    export G3_STORE_HASHES=$D/store_at_$1.sha256
}

# dry_run <file> <answers per set-up> <exp_03 options...>: exp_03's own work list (no model call, nothing written) of
# every set-up named in $CONFIGS; refuses unless each lists the expected number of answers.
dry_run() {
    local out=$1 want=$2; shift 2
    uv run --project experiments/mentori --frozen python $EXP03 --dry-run --configs $CONFIGS "$@" > "$out" 2>&1 \
        || refuse "exp_03 dry run failed: $(tail -1 "$out")"
    local c n
    for c in $CONFIGS; do
        n=$(grep -E "^run exp_03__${c}__exp_v4_s20_n0 " "$out" | sed -E 's/.* ([0-9]+) answers:.*/\1/')
        [ "$n" = "$want" ] || refuse "dry run lists ${n:-no} answers for $c, not $want ($out)"
    done
}

# same_code_as_smoke: refuses unless the run code of exp_03 and distiller_firing.py (findings/recompute/coordinator/
# run_code.py: the two, their imports, Mentori's backend, the lock, the environment; D112 Q16; gate_distiller.sh:23-24
# loads distiller_firing.py to count whether WAVE2 starts) is the same at the commit the checked smoke ran on
# (smoke_check.json, launch_record.commit) and at HEAD, so a launch runs the code the smoke tested (wave B review F3).
# Called by launch_g3.sh and gate_distiller.sh. Other files (these scripts, findings, documents and status files under
# experiments/) may differ.
same_code_as_smoke() {
    local sc
    sc=$(uv run --frozen python -c "import json, sys; print((json.load(open(sys.argv[1])).get('launch_record') or {}).get('commit') or '')" \
        "$D/smoke_check.json") || refuse "cannot read $D/smoke_check.json"
    [ -n "$sc" ] || refuse "smoke_check.json names no smoke commit"
    git cat-file -e "$sc^{commit}" 2>/dev/null || refuse "the smoke's commit $sc is not in this clone"
    local same rc
    same=$(uv run --frozen python findings/recompute/coordinator/run_code.py same "$sc" HEAD --entry $EXP03 --entry $DISTILLER 2>&1)
    rc=$?
    [ $rc = 1 ] && refuse "$same (HEAD $(git rev-parse --short HEAD); smoke again)"
    [ $rc = 0 ] || refuse "run_code.py could not compare the smoke's commit ${sc:0:7} with HEAD: $same"
}
