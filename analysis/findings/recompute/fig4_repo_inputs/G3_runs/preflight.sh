# G3 preflight, sourced by smoke_g3.sh, launch_g3.sh and gate_distiller.sh (not run alone). Defines the set-ups and
# the refusals every start makes before any process starts; each refusal stops the caller with nothing started.
#
# Set-ups (D83): Q148 leaves rlm_10 out of G3 (Figure 4 reuses Figure 2's RLM-10 answers, G1) and makes the distiller
# count a checkpoint before the two distiller set-ups; Q149 runs one process per set-up. WAVE1 starts at the launch,
# the full pipeline among them (Q148's "first" is tied to the count, by the card's own reason: README);
# WAVE2 starts only from gate_distiller.sh, after the full pipeline's 405 answers are
# counted (Q82, D75). raw_gemini and naive_rag are the two descriptive baselines (D79 Q134; LIST.md Rule 12).
WAVE1="raw_gemini naive_rag full_orchestrator orch_no_analyser orch_no_planner orch_no_supervisor orch_no_synthesiser orch_factual_to_documents"
WAVE2="orch_no_distiller orch_distiller_f1"
EXP03=experiments/mentori/publication/scripts/exp_03_orchestration_ablation.py

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

# same_code_as_smoke: refuses unless no file under experiments/ differs between the commit the checked smoke ran on
# (smoke_check.json, launch_record.commit) and HEAD, so a launch runs the code the smoke tested (wave B review F3).
# Called by launch_g3.sh and gate_distiller.sh. Files outside experiments/ (these scripts, findings) may differ.
same_code_as_smoke() {
    local sc
    sc=$(uv run --frozen python -c "import json, sys; print((json.load(open(sys.argv[1])).get('launch_record') or {}).get('commit') or '')" \
        "$D/smoke_check.json") || refuse "cannot read $D/smoke_check.json"
    [ -n "$sc" ] || refuse "smoke_check.json names no smoke commit"
    git cat-file -e "$sc^{commit}" 2>/dev/null || refuse "the smoke's commit $sc is not in this clone"
    git diff --quiet "$sc" HEAD -- experiments \
        || refuse "files under experiments/ differ between the smoke's commit ${sc:0:7} and HEAD $(git rev-parse --short HEAD) (smoke again): $(git diff --name-only "$sc" HEAD -- experiments | head -5 | tr '\n' ' ')"
}
