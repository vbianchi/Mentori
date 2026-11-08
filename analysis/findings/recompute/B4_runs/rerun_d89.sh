#!/bin/bash
# D89 (Q145 O3), D90 (Q1, Q2) and D92 (Q185, Q186, Q187, Q188): the 131 answers of the authors' RLM (G6) that met a
# Gemini reply D89 or D90 now returns to the package, and what each needs under D92. The list is
# scripts/S455_d89_affected_answers.py's (findings/recompute/Q145/S455_d92_affected.json, laptop, 18 Oct; the D89 list
# of 26 is S455_d89_affected.json, the D90 list S455_d90_affected.json). Each key below carries its action, which
# S455 gives and "dry" checks:
#   rerun, 44: 6 recitation and 33 malformed root failures (root_call_failed) whose reply holds a text part, and the 5
#      answers (answer_ready) whose code met a raised sub-call where D89 and D90 now return text; each is run again.
#      Among the 33: cap2 04_fastp_TE3 d3, cap3 19_hpai_canada_CO2 d1, cap5 OOD_009 d3 and cap5 SY_006 d3, whose
#      malformed root reply holds {"text": ""} beside a thought signature: the package's own client returns "" for that
#      (google-genai 2.30.1 _get_text: "part.text == '' is different from part.text is None"), so the turn goes on.
#   rebuild, 72 (D92 Q187): failed only at a malformed closing call (forced_final_failed: cap 1 62, cap 2 9, cap 3 1).
#      The package returns the closing reply unchanged as the answer (rlm/core/rlm.py:673-695), so the D92 answer is
#      the text the stored call record holds, rebuilt with no model call by experiments/rlm_ref/adapter.py
#      rebuild_from_closing: answer closing_answer(call) (package_text of its parts, "" when it has none; 33 of the 72
#      are blank), status ok, stop_reason turn_cap, error None, forced_final_has_code from the package's own parser;
#      every other field as stored (the one attempt that ran, Q29), plus "rebuilt" with the decision, the call's seq
#      and status, the stored values it replaced, this script, the commit and the adapter's sha256. The line is
#      replaced in place in answers.jsonl; the trace and calls.jsonl are not touched.
#   stays_failed, 15 (D92 Q185): a root reply with no finishReason and no part at all (D89 "empty"). The package's own
#      client returns None for it, and the root turn's code-block search raises TypeError (rlm/core/rlm.py:658,
#      rlm/utils/parsing.py:18), so today's adapter fails the question too: the stored failure stands, untouched. Its
#      stop reason is the old label root_call_failed; today's run would store error with the TypeError (see the
#      return of this build: relabelling the 15 is put to Valerio, not done).
# The rerun and rebuild records replaced are kept in each run's discarded_D89/, as D75 Q48 kept its (d75_q48_rerun.sh).
#
#   bash findings/recompute/B4_runs/rerun_d89.sh                       dry (the default): checks the 131, writes nothing
#   bash findings/recompute/B4_runs/rerun_d89.sh go <fix commit>       rebuild the 72, rerun the 44 (laptop, colima up)
#   bash findings/recompute/B4_runs/rerun_d89.sh check <archive>       after the reruns end
#
# The lock and the code (D92 Q186, Valerio 18 October: the D90 reruns run under today's lock and code, each recording
# its code version and lock). The answers ran under 8fa06e43, 1b89d50c and 668832dc (their answer records; dry prints
# the count per lock); D92 accepted d66daa28 (ACCEPTED_LOCK below), whose difference from 8fa06e43 touches no setting a
# Gemini call reads ([gemini] and [thinking] unchanged; git diff 50af756 4fd5b72 -- experiments/LOCK.toml). "go"
# refuses any other lock: a later lock needs its own decision. The code: the reruns run on HEAD (which holds <fix
# commit>); the removed answers and those kept beside them ran on older adapters. "go" writes ran_on.json into the
# archive and into each run's discarded_D89/: per run, the adapter_sha256 and lock_sha256 of the removed, rebuilt and
# kept answers, and the HEAD commit, dirty state, adapter sha256 and lock the reruns and the rebuild use; every rerun
# call record also carries session_id and code_commit (D92 Q199). Besides D89, D90 and D92 the reruns carry every
# adapter change since the answer was made (D75 round 3 a3f0cf1, Q114 fbbcfb3, Q145 4cd0c96, as applies).
#
# What "go" does, in order (any refusal stops it before a file is touched):
#  1. refusals: a run_rlm_ref process; HEAD lacks <fix commit> or the checkout lacks the D92 rule (Q185 root replies,
#     closing_answer, the Q188 statuses); tracked files under experiments/ differ from HEAD; today's lock is not
#     ACCEPTED_LOCK; Docker not running, the pinned image missing or built from other inputs, or another process on the
#     sandbox's proxy ports (run_rlm_ref.py checks these again, but only after step 4).
#  2. S455 --stdout over the ten runs must list exactly the 131 keys below with the same action (each stored once, with
#     the stop reason given beside it); every rebuild must succeed (rebuild_from_closing refuses anything it cannot
#     rebuild exactly); then run_rlm_ref --dry-run of each cap and draw, against a copy of the answers the rerun starts
#     from (--runs-root in a temporary folder), must list as "todo" exactly that cap and draw's rerun keys. The dry form
#     runs the same checks and prints each rebuilt answer's length and code flag.
#  3. copies aside, into each run's discarded_D89/: answers.jsonl and calls.jsonl as they stand, the removed answer
#     lines (removed_answers.jsonl, the 44), the stored lines of the rebuilt answers (rebuilt_from.jsonl) and the
#     rebuilt lines (rebuilt_answers.jsonl), the answers.jsonl the rerun starts from (kept_answers.jsonl: the stored
#     lines less the 44, the 72 rebuilt in place) and the rerun and rebuilt answers' traces, with sha256s; the archive
#     findings/recompute/B4_runs/d89_before_rerun_<UTC>/ holds rerun.json and ran_on.json.
#  4. replaces each run's answers.jsonl with kept_answers.jsonl (calls.jsonl, traces and blobs untouched: every call
#     record carries its answer's ctx_uid, so the replaced attempts stay apart from the rerun's, as in D75 Q48).
#  5. reruns only the 44, one run_rlm_ref per cap and draw (resume skips every stored answer, the rebuilt included;
#     --questions names the ones to run), serially, as the depth caps ran; each prints to rerun_d89_cap<c>_d<d>.log.
# Each rerun sends the question again with the draw's seed; whatever it ends with is its answer (one attempt, Q29).
cd ~/projects/Mentori-reanalysis || exit 1
export PATH=/opt/homebrew/bin:$HOME/.local/bin:$PATH PYTHONDONTWRITEBYTECODE=1
D=findings/recompute/B4_runs
ACCEPTED_LOCK=d66daa28596bf3b70ff90e0fb89b1353eab023eba699427cb05ebb3376105c12   # D92 Q186 (18 October)
refuse() { echo "refused: $*"; exit 1; }
# run|answer_key|stored stop_reason|action (rerun, rebuild, stays_failed)
KEYS="
b4_rlm_ref__cap5__all135|cap5|18_fmd_review_FR1|d2|root_call_failed|stays_failed
b4_rlm_ref__cap5__all135|cap5|OOD_029|d2|root_call_failed|rerun
b4_rlm_ref__cap5__all135|cap5|19_hpai_canada_TE3|d3|answer_ready|rerun
b4_rlm_ref__cap5__all135|cap5|OOD_009|d3|root_call_failed|rerun
b4_rlm_ref__cap5__all135|cap5|OOD_014|d3|root_call_failed|rerun
b4_rlm_ref__cap5__all135|cap5|SY_006|d3|root_call_failed|rerun
b4_rlm_ref__cap10__all135|cap10|16_ppr_ethiopia_TE3|d2|root_call_failed|rerun
b4_rlm_ref__cap10__all135|cap10|19_hpai_canada_TE3|d2|root_call_failed|stays_failed
b4_rlm_ref__cap10__all135|cap10|OOD_014|d2|root_call_failed|rerun
b4_rlm_ref__cap10__all135|cap10|19_hpai_canada_TE3|d3|root_call_failed|stays_failed
b4_rlm_ref__cap20__all135|cap20|OOD_014|d1|root_call_failed|rerun
b4_rlm_ref__cap20__all135|cap20|OOD_032|d1|root_call_failed|rerun
b4_rlm_ref__cap20__all135|cap20|11_asf_burkina_faso_CO2|d2|root_call_failed|stays_failed
b4_rlm_ref__cap20__all135|cap20|19_hpai_canada_TE3|d2|answer_ready|rerun
b4_rlm_ref__cap20__all135|cap20|OOD_029|d2|root_call_failed|rerun
b4_rlm_ref__cap20__all135|cap20|OOD_030|d2|root_call_failed|rerun
b4_rlm_ref__cap20__all135|cap20|01_sarek_FR1|d3|root_call_failed|rerun
b4_rlm_ref__cap20__all135|cap20|07_salmon_FR1|d3|root_call_failed|rerun
b4_rlm_ref__cap20__all135|cap20|19_hpai_canada_TE3|d3|answer_ready|rerun
b4_rlm_ref__cap20__all135|cap20|OOD_004|d3|root_call_failed|rerun
b4_rlm_ref__cap20__all135|cap20|OOD_031|d3|root_call_failed|rerun
b4_rlm_ref__cap1__depthsweep86|cap1|01_sarek_CO2|d1|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|01_sarek_FR1|d1|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|02_snakemake_CO2|d1|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|02_snakemake_FR1|d1|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|03_nfcore_framework_FR1|d1|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|05_multiqc_CO2|d1|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|11_asf_burkina_faso_FR1|d1|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|11_asf_burkina_faso_TE3|d1|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|14_bovine_tb_cameroon_FR1|d1|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|15_rabies_tanzania_TE3|d1|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|CD_002|d1|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|CD_006|d1|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|CD_012|d1|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|CD_013|d1|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|CD_016|d1|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|CD_017|d1|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|02_snakemake_CO2|d2|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|07_salmon_TE3|d2|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|12_hpai_netherlands_CO2|d2|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|12_hpai_netherlands_FR1|d2|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|12_hpai_netherlands_TE3|d2|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|13_lsd_nepal_FR1|d2|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|15_rabies_tanzania_CO2|d2|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|16_ppr_ethiopia_TE3|d2|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|17_brucellosis_ethiopia_CO2|d2|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|17_brucellosis_ethiopia_FR1|d2|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|19_hpai_canada_TE3|d2|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|20_lsd_review_TE3|d2|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|CD_001|d2|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|CD_009|d2|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|CD_010|d2|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|CD_012|d2|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|CD_013|d2|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|SY_003|d2|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|SY_007|d2|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|SY_008|d2|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|02_snakemake_FR1|d3|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|02_snakemake_TE3|d3|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|04_fastp_CO2|d3|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|04_fastp_FR1|d3|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|05_multiqc_TE3|d3|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|07_salmon_TE3|d3|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|08_deseq2_TE3|d3|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|09_seqkit_FR1|d3|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|10_cutadapt_CO2|d3|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|13_lsd_nepal_FR1|d3|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|13_lsd_nepal_TE3|d3|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|15_rabies_tanzania_CO2|d3|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|15_rabies_tanzania_FR1|d3|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|15_rabies_tanzania_TE3|d3|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|16_ppr_ethiopia_CO2|d3|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|17_brucellosis_ethiopia_TE3|d3|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|18_fmd_review_FR1|d3|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|20_lsd_review_CO2|d3|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|CD_001|d3|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|CD_003|d3|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|CD_009|d3|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|CD_011|d3|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|CD_016|d3|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|SY_001|d3|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|SY_004|d3|forced_final_failed|rebuild
b4_rlm_ref__cap1__depthsweep86|cap1|SY_006|d3|forced_final_failed|rebuild
b4_rlm_ref__cap2__depthsweep86|cap2|05_multiqc_TE3|d1|forced_final_failed|rebuild
b4_rlm_ref__cap2__depthsweep86|cap2|06_star_aligner_CO2|d1|root_call_failed|rerun
b4_rlm_ref__cap2__depthsweep86|cap2|13_lsd_nepal_FR1|d1|forced_final_failed|rebuild
b4_rlm_ref__cap2__depthsweep86|cap2|13_lsd_nepal_TE3|d1|forced_final_failed|rebuild
b4_rlm_ref__cap2__depthsweep86|cap2|19_hpai_canada_CO2|d1|forced_final_failed|rebuild
b4_rlm_ref__cap2__depthsweep86|cap2|06_star_aligner_TE3|d2|forced_final_failed|rebuild
b4_rlm_ref__cap2__depthsweep86|cap2|14_bovine_tb_cameroon_TE3|d2|forced_final_failed|rebuild
b4_rlm_ref__cap2__depthsweep86|cap2|18_fmd_review_TE3|d2|forced_final_failed|rebuild
b4_rlm_ref__cap2__depthsweep86|cap2|02_snakemake_CO2|d3|forced_final_failed|rebuild
b4_rlm_ref__cap2__depthsweep86|cap2|04_fastp_TE3|d3|root_call_failed|rerun
b4_rlm_ref__cap2__depthsweep86|cap2|16_ppr_ethiopia_FR1|d3|forced_final_failed|rebuild
b4_rlm_ref__cap3__depthsweep86|cap3|19_hpai_canada_CO2|d1|root_call_failed|rerun
b4_rlm_ref__cap3__depthsweep86|cap3|11_asf_burkina_faso_FR1|d2|root_call_failed|stays_failed
b4_rlm_ref__cap3__depthsweep86|cap3|13_lsd_nepal_CO2|d3|forced_final_failed|rebuild
b4_rlm_ref__cap7__depthsweep86|cap7|12_hpai_netherlands_CO2|d1|root_call_failed|stays_failed
b4_rlm_ref__cap7__depthsweep86|cap7|19_hpai_canada_TE3|d1|root_call_failed|stays_failed
b4_rlm_ref__cap7__depthsweep86|cap7|19_hpai_canada_TE3|d3|answer_ready|rerun
b4_rlm_ref__cap15__depthsweep86|cap15|18_fmd_review_FR1|d2|root_call_failed|stays_failed
b4_rlm_ref__cap15__depthsweep86|cap15|19_hpai_canada_TE3|d2|answer_ready|rerun
b4_rlm_ref__cap15__depthsweep86|cap15|CD_016|d2|root_call_failed|rerun
b4_rlm_ref__cap15__depthsweep86|cap15|02_snakemake_FR1|d3|root_call_failed|rerun
b4_rlm_ref__cap15__depthsweep86|cap15|12_hpai_netherlands_FR1|d3|root_call_failed|rerun
b4_rlm_ref__cap15__depthsweep86|cap15|19_hpai_canada_TE3|d3|root_call_failed|stays_failed
b4_rlm_ref__cap30__depthsweep86|cap30|01_sarek_FR1|d1|root_call_failed|rerun
b4_rlm_ref__cap30__depthsweep86|cap30|07_salmon_FR1|d1|root_call_failed|rerun
b4_rlm_ref__cap30__depthsweep86|cap30|07_salmon_TE3|d1|root_call_failed|rerun
b4_rlm_ref__cap30__depthsweep86|cap30|16_ppr_ethiopia_TE3|d1|root_call_failed|rerun
b4_rlm_ref__cap30__depthsweep86|cap30|19_hpai_canada_TE3|d1|root_call_failed|stays_failed
b4_rlm_ref__cap30__depthsweep86|cap30|20_lsd_review_TE3|d1|root_call_failed|rerun
b4_rlm_ref__cap30__depthsweep86|cap30|SY_005|d1|root_call_failed|rerun
b4_rlm_ref__cap30__depthsweep86|cap30|11_asf_burkina_faso_CO2|d2|root_call_failed|stays_failed
b4_rlm_ref__cap30__depthsweep86|cap30|14_bovine_tb_cameroon_CO2|d2|root_call_failed|rerun
b4_rlm_ref__cap30__depthsweep86|cap30|CD_007|d2|root_call_failed|rerun
b4_rlm_ref__cap30__depthsweep86|cap30|CD_011|d2|root_call_failed|rerun
b4_rlm_ref__cap30__depthsweep86|cap30|01_sarek_FR1|d3|root_call_failed|rerun
b4_rlm_ref__cap30__depthsweep86|cap30|19_hpai_canada_CO2|d3|root_call_failed|rerun
b4_rlm_ref__cap30__depthsweep86|cap30|CD_011|d3|root_call_failed|rerun
b4_rlm_ref__cap30__depthsweep86|cap30|CD_013|d3|root_call_failed|rerun
b4_rlm_ref__cap50__depthsweep86|cap50|11_asf_burkina_faso_TE3|d1|root_call_failed|stays_failed
b4_rlm_ref__cap50__depthsweep86|cap50|12_hpai_netherlands_FR1|d1|root_call_failed|rerun
b4_rlm_ref__cap50__depthsweep86|cap50|19_hpai_canada_TE3|d1|root_call_failed|stays_failed
b4_rlm_ref__cap50__depthsweep86|cap50|CD_011|d1|root_call_failed|rerun
b4_rlm_ref__cap50__depthsweep86|cap50|01_sarek_FR1|d2|root_call_failed|rerun
b4_rlm_ref__cap50__depthsweep86|cap50|05_multiqc_FR1|d2|root_call_failed|rerun
b4_rlm_ref__cap50__depthsweep86|cap50|11_asf_burkina_faso_TE3|d2|root_call_failed|stays_failed
b4_rlm_ref__cap50__depthsweep86|cap50|19_hpai_canada_FR1|d2|root_call_failed|rerun
b4_rlm_ref__cap50__depthsweep86|cap50|CD_007|d2|root_call_failed|rerun
b4_rlm_ref__cap50__depthsweep86|cap50|11_asf_burkina_faso_TE3|d3|root_call_failed|stays_failed
"
RUNS=$(echo "$KEYS" | awk -F'|' 'NF {print $1}' | sort -u)
N=$(echo "$KEYS" | grep -c '|')
NA() { echo "$KEYS" | awk -F'|' -v a=$1 '$6 == a' | grep -c '|'; }
R="uv run --project experiments/rlm_ref --frozen python -m experiments.rlm_ref.run_rlm_ref"
# one line per run_rlm_ref process (the reruns only): cap draw question-set run qid,qid,...
groups() {
  echo "$KEYS" | awk -F'|' '$6 == "rerun" {split($1, a, "__"); s = (a[3] == "depthsweep86") ? "depth_sweep86" : "all135"; k = substr($2, 4) " " substr($4, 2) " " s " " $1; q[k] = (k in q) ? q[k] "," $3 : $3} END {for (k in q) print k, q[k]}' \
    | sort -k1,1n -k2,2n
}

# run_rlm_ref --dry-run of each cap and draw against copies of the kept answers in $1 (verify's output): its "todo"
# list must be exactly that cap and draw's rerun keys (no Docker, no model call, nothing written outside $1)
worklists() {
  local T=$1 bad=0
  for run in $RUNS; do
    mkdir -p "$T/sinks/$run" && cp "$T/$run/kept_answers.jsonl" "$T/sinks/$run/answers.jsonl" || return 1
  done
  while read cap draw set run qs; do
    got=$($R --cap $cap --draw $draw --question-set $set --questions $qs --runs-root "$T/sinks" --dry-run 2>&1 < /dev/null) \
      || { echo "cap $cap draw $draw: run_rlm_ref --dry-run failed: $got"; bad=1; continue; }
    todo=$(echo "$got" | awk '$1 == "todo" {print $2}' | sort)
    want=$(echo "$KEYS" | awk -F'|' -v r=$run -v d=d$draw '$1 == r && $4 == d && $6 == "rerun" {print $2 "|" $3 "|" $4}' | sort)
    if [ "$todo" = "$want" ]; then
      echo "  cap $cap draw $draw ($set): run_rlm_ref --dry-run lists $(echo "$todo" | grep -c .) to run, the keys here"
    else
      echo "  cap $cap draw $draw ($set): run_rlm_ref --dry-run lists other keys: $(diff <(echo "$want") <(echo "$todo") | grep '^[<>]' | tr '\n' ' ')"
      bad=1
    fi
  done < <(groups)
  return $bad
}

# the 131 as they are stored now, against S455 (read only), with each rebuild made in $1 (never in findings/runs);
# prints each with the lock and adapter it ran under
verify() {
  uv run --project experiments/rlm_ref --frozen python - "$KEYS" "$1" <<'PY' || return 1
import collections, hashlib, json, subprocess, sys, time
from pathlib import Path
from experiments.rlm_ref import adapter as ad
want = [l.split("|") for l in sys.argv[1].split("\n") if l.strip()]
out = Path(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] else None
runs = sorted({w[0] for w in want})
s455 = json.loads(subprocess.run(["uv", "run", "--no-sync", "python", "scripts/S455_d89_affected_answers.py",
                                  "--stdout"] + [f"findings/runs/{r}" for r in runs],
                                 capture_output=True, text=True, check=True).stdout)
assert s455["gate"] == "pass", s455["gate"]
assert "D92" in s455["provenance"]["decision"], f"S455 is not the D92 version: {s455['provenance']['decision']}"
listed = sorted((r["run"], r["answer_key"], r["action"]) for r in s455["rows"])
keyed = sorted((w[0], "|".join(w[1:4]), w[5]) for w in want)
assert listed == keyed, f"S455 lists {len(listed)} answers, not the {len(want)} here: {sorted(set(listed) ^ set(keyed))}"
git = lambda *a: subprocess.run(["git", *a], capture_output=True, text=True).stdout.strip()   # noqa: E731
prov = {"script": "findings/recompute/B4_runs/rerun_d89.sh", "commit": git("rev-parse", "HEAD"),
        "dirty": bool(git("status", "--porcelain", "--untracked-files=no", "--", "experiments", "scripts")),
        "adapter_sha256": ad.adapter_sha256(), "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
locks, ran_on = collections.Counter(), {}
for run in runs:
    p = Path("findings/runs") / run
    lines = (p / "answers.jsonl").read_text(encoding="utf-8").splitlines(keepends=True)
    recs = [json.loads(l) for l in lines]
    mine = {"|".join(w[1:4]): (w[4], w[5]) for w in want if w[0] == run}
    hit = [r for r in recs if r["answer_key"] in mine]
    assert sorted(r["answer_key"] for r in hit) == sorted(mine), (run, [r["answer_key"] for r in hit])
    for r in hit:
        assert r["stop_reason"] == mine[r["answer_key"]][0], (run, r["answer_key"], r["stop_reason"])
        locks[r["lock_sha256"][:8]] += 1
    act = lambda r: mine.get(r["answer_key"], (None, "keep"))[1]   # noqa: E731
    uids = {r["ctx_uid"] for r in recs if act(r) == "rebuild"}
    calls = collections.defaultdict(list)
    if uids:
        with open(p / "calls.jsonl", "rb") as f:
            for raw in f:
                if b'"ctx_uid"' in raw and any(u.encode() in raw for u in uids):
                    c = json.loads(raw)
                    if c.get("ctx_uid") in uids:
                        calls[c["ctx_uid"]].append(c)
    kept, removed, rebuilt, rebuilt_from = [], [], [], []
    for l, r in zip(lines, recs):
        a = act(r)
        if a == "rerun":
            removed.append(l)
        elif a == "rebuild":
            new = ad.rebuild_from_closing(r, calls[r["ctx_uid"]], prov)      # ValueError: refused, nothing written
            nl = json.dumps(new, ensure_ascii=False) + "\n"
            kept.append(nl), rebuilt.append(nl), rebuilt_from.append(l)
            print(f"  rebuild {r['answer_key']}: seq {new['rebuilt']['from_call_seq']} {new['rebuilt']['call_status']}, "
                  f"answer {len(new['answer'])} chars{' (blank)' if not new['answer'].strip() else ''}"
                  f"{', holds a repl block' if new['forced_final_has_code'] else ''}")
        else:
            kept.append(l)
    by = lambda a: dict(collections.Counter(f"{r.get('adapter_sha256', '')[:8]} lock {r['lock_sha256'][:8]}"  # noqa: E731
                                            for r in recs if act(r) == a))
    ran_on[run] = {"removed_for_rerun": by("rerun"), "rebuilt": by("rebuild"), "stays_failed": by("stays_failed"),
                   "kept": by("keep")}
    n = collections.Counter(act(r) for r in recs)
    print(f"{run}: {len(lines)} answers: {n['rerun']} to rerun, {n['rebuild']} rebuilt, {n['stays_failed']} stay failed, "
          f"{n['keep']} kept; adapter and lock of each: {ran_on[run]}")
    if out is not None:
        x = out / run
        x.mkdir(parents=True)
        for name, ls in (("removed_answers.jsonl", removed), ("kept_answers.jsonl", kept),
                         ("rebuilt_answers.jsonl", rebuilt), ("rebuilt_from.jsonl", rebuilt_from)):
            (x / name).write_text("".join(ls), encoding="utf-8")
lock_now = hashlib.sha256(Path("experiments/LOCK.toml").read_bytes()).hexdigest()
if out is not None:
    (out / "ran_on.json").write_text(json.dumps({
        "decision": "D92 Q186: the D90 reruns run under today's lock and code, each recording its code version and lock",
        "locks_of_listed": dict(locks), "runs": ran_on,
        "reruns_and_rebuild_run_on": {**prov, "lock_sha256": lock_now}}, indent=1) + "\n")
print(f"{len(want)} answers listed ({sum(w[5] == 'rerun' for w in want)} rerun, {sum(w[5] == 'rebuild' for w in want)} "
      f"rebuilt, {sum(w[5] == 'stays_failed' for w in want)} stay failed), each stored once with the stop reason above; "
      f"locks they ran under: {dict(locks)}; the rerun and rebuild run on {prov['commit'][:12]}"
      f"{' (dirty)' if prov['dirty'] else ''}, adapter {prov['adapter_sha256'][:12]}, lock {lock_now[:8]}")
PY
}

if [ "${1:-dry}" = dry ]; then
  T=$(mktemp -d) || refuse "no temporary folder"
  verify "$T" || refuse "the stored answers are not the $N above, or a rebuild was refused (nothing touched)"
  worklists "$T" || refuse "run_rlm_ref would not run exactly the $(NA rerun) reruns above (nothing touched; see $T)"
  rm -rf "$T"
  echo "dry: nothing written. Then: bash $D/rerun_d89.sh go <fix commit> (lock $ACCEPTED_LOCK, D92 Q186)"
  groups | while read cap draw set run qs; do echo "  would run: run_rlm_ref --cap $cap --draw $draw --question-set $set --questions $qs"; done
  exit 0
fi

if [ "$1" = check ]; then
  # After the reruns: each run holds its old count, each key once; kept_answers.jsonl (the rebuilt lines included)
  # unchanged at the head; calls.jsonl as it stood before the rerun unchanged at the head of the new one (the rerun only
  # appends); each rebuilt line equal to its stored line but for the rebuilt fields; the 15 that stay failed unchanged;
  # the 44 new records made by the adapter rerun.json names under its lock, every call of theirs carrying a session_id
  # and code_commit (D92 Q199), with their stop reason and their calls' statuses
  A=${2:-}; [ -n "$A" ] && [ -f "$A/rerun.json" ] || refuse "name the archive the rerun wrote: rerun_d89.sh check <archive>"
  uv run --project experiments/rlm_ref --frozen python - "$KEYS" "$A" <<'PY' || exit 1
import collections, json, sys
from pathlib import Path
from experiments.rlm_ref import adapter as ad
want = [l.split("|") for l in sys.argv[1].split("\n") if l.strip()]
arch = Path(sys.argv[2])
rerun = json.loads((arch / "rerun.json").read_text())
good = True


def prefix(old: Path, new: Path) -> bool:
    """old's bytes are the first bytes of new (the rerun appended and changed nothing before)."""
    n = old.stat().st_size
    with open(old, "rb") as a, open(new, "rb") as b:
        return a.read() == b.read(n)
for run in sorted({w[0] for w in want}):
    p = Path("findings/runs") / run
    x = p / "discarded_D89"
    lines = (p / "answers.jsonl").read_text(encoding="utf-8").splitlines(keepends=True)
    kept = (x / "kept_answers.jsonl").read_text(encoding="utf-8").splitlines(keepends=True)
    before = [json.loads(l) for l in (x / "answers.jsonl.before_rerun").read_text(encoding="utf-8").splitlines()]
    recs = [json.loads(l) for l in lines]
    n = collections.Counter(r["answer_key"] for r in recs)
    act = {"|".join(w[1:4]): w[5] for w in want if w[0] == run}
    new = recs[len(kept):]
    head = prefix(x / "calls.jsonl.before_rerun", p / "calls.jsonl")
    old = {r["answer_key"]: r for r in before}
    now = {r["answer_key"]: r for r in recs}
    rebuilt_ok = all(now[k].get("rebuilt", {}).get("decision") == "D92 Q187" and now[k]["status"] == "ok"
                     and {f: v for f, v in now[k].items() if f not in ad.REBUILT_FIELDS + ("rebuilt",)}
                     == {f: v for f, v in old[k].items() if f not in ad.REBUILT_FIELDS}
                     for k, a in act.items() if a == "rebuild")
    stays_ok = all(now[k] == old[k] for k, a in act.items() if a == "stays_failed")
    want_new = {k for k, a in act.items() if a == "rerun"}
    calls = [json.loads(l) for l in (p / "calls.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    uids = {r["ctx_uid"] for r in new}
    new_calls = [c for c in calls if c.get("ctx_uid") in uids]
    q199 = all(c.get("session_id") and c.get("code_commit") for c in new_calls)
    ok = (len(recs) == len(before) and max(n.values()) == 1 and lines[:len(kept)] == kept
          and {r["answer_key"] for r in new} == want_new and len(new) == len(want_new) and head and rebuilt_ok
          and stays_ok and q199
          and all(r.get("adapter_sha256") == rerun["adapter_sha256"] and r.get("lock_sha256") == rerun["lock_sha256"]
                  for r in new))
    good &= ok
    print(f"{run}: {len(recs)} answers (was {len(before)}), {'each key once' if max(n.values()) == 1 else 'DUPLICATE'}, "
          f"the {len(kept)} kept lines {'unchanged' if lines[:len(kept)] == kept else 'CHANGED'}, rebuilt "
          f"{'as stored but the rebuilt fields' if rebuilt_ok else 'WRONG'}, stays_failed "
          f"{'unchanged' if stays_ok else 'CHANGED'}, calls.jsonl before the rerun "
          f"{'unchanged at the head' if head else 'CHANGED'}, {len(new)} new, their {len(new_calls)} calls "
          f"{'each with session_id and code_commit' if q199 else 'MISSING session_id or code_commit'}: "
          f"{'ok' if ok else 'FAIL'}")
    for r in new:
        st = collections.Counter(c["status"] for c in new_calls if c.get("ctx_uid") == r["ctx_uid"])
        print(f"  {r['answer_key']}: {r['status']} {r['stop_reason']}, {r['turns_used']} turns, sub_failed "
              f"{r['calls']['sub_failed']}, call statuses {dict(st)}"
              + (f", error {str(r['error'])[:80]}" if r.get("error") else ""))
print("check:", "PASS" if good else "FAIL")
sys.exit(0 if good else 1)
PY
  exit 0
fi

[ "$1" = go ] || refuse "rerun_d89.sh [dry | go <fix commit> | check <archive>]"
# 1. refusals
FIX=${2:-}
[ -n "$FIX" ] || refuse "name the commit that holds the D92 fix: rerun_d89.sh go <commit>"
pgrep -f "[r]un_rlm_ref" > /dev/null && refuse "a run_rlm_ref process runs"
git cat-file -e "$FIX^{commit}" 2>/dev/null || refuse "commit $FIX is not in this clone (pull first)"
git merge-base --is-ancestor "$FIX" HEAD || refuse "HEAD $(git rev-parse --short HEAD) does not contain $FIX (pull first)"
grep -q 'if root and status in gemini_client.RETURNED_STATUSES:' experiments/rlm_ref/adapter.py \
    && grep -q 'def rebuild_from_closing(answer: dict' experiments/rlm_ref/adapter.py \
    && grep -q 'EMPTY_TEXT_STATUSES = ("empty", "blocked")' experiments/runner/gemini_client.py \
    && grep -q '"language", "other", "unexpected_tool_call", "too_many_tool_calls")' experiments/runner/gemini_client.py \
    && grep -q 'def raised_before_d89(rec: dict)' experiments/runner/gemini_client.py \
    && grep -q 'def provenance() -> dict' experiments/runner/ollama_client.py \
    || refuse "the checkout lacks the D92 rule (adapter.py, gemini_client.py, ollama_client.py)"
git diff --quiet HEAD -- experiments/ || refuse "tracked files under experiments/ differ from HEAD"
LOCK_NOW=$(shasum -a 256 experiments/LOCK.toml | cut -c1-64)
[ "$LOCK_NOW" = "$ACCEPTED_LOCK" ] || refuse "today's lock is $LOCK_NOW; D92 Q186 accepted $ACCEPTED_LOCK; another lock needs its own decision"
for r in $RUNS; do [ -e findings/runs/$r/discarded_D89 ] && refuse "findings/runs/$r/discarded_D89 exists (a rerun was prepared before)"; done
docker info > /dev/null 2>&1 || refuse "Docker is not running (colima start); nothing touched"
uv run --project experiments/rlm_ref --frozen python -c "from experiments.rlm_ref import adapter as ad; ad.ensure_image(); ad.check_proxy_ports()" \
  || refuse "the sandbox image or the proxy ports would stop run_rlm_ref (above); nothing touched"

# 2 and 3. the 131 checked against S455 and rebuilt in a temporary folder, then copied aside with the runs' files
A=$D/d89_before_rerun_$(date -u +%Y%m%dT%H%M%SZ)
[ -e "$A" ] && refuse "$A exists"
T=$(mktemp -d) || refuse "no temporary folder"
verify "$T" || refuse "the stored answers are not the $N above, or a rebuild was refused (nothing touched; see $T)"
worklists "$T" || refuse "run_rlm_ref would not run exactly the $(NA rerun) reruns above (nothing touched; see $T)"
mkdir -p "$A" || refuse "cannot make $A"
cp -p $T/ran_on.json "$A/ran_on.json" || refuse "copy of ran_on.json failed"
for r in $RUNS; do
  X=findings/runs/$r/discarded_D89
  mkdir -p $X/traces || refuse "cannot make $X"
  cp -p findings/runs/$r/answers.jsonl $X/answers.jsonl.before_rerun && cp -p findings/runs/$r/calls.jsonl $X/calls.jsonl.before_rerun \
    && cp -p $T/$r/removed_answers.jsonl $T/$r/kept_answers.jsonl $T/$r/rebuilt_answers.jsonl $T/$r/rebuilt_from.jsonl $T/ran_on.json $X/ \
    || refuse "copy to $X failed"
  for k in $(echo "$KEYS" | awk -F'|' -v r=$r '$1 == r && $6 != "stays_failed" {print $2 "__" $3 "__" $4}'); do
    [ -f findings/runs/$r/traces/$k.json ] && cp -p findings/runs/$r/traces/$k.json $X/traces/
  done
  (cd $X && shasum -a 256 *.before_rerun *.jsonl ran_on.json traces/*.json 2>/dev/null) > $X/SHA256SUMS
  cmp -s findings/runs/$r/answers.jsonl $X/answers.jsonl.before_rerun || refuse "$r: answers.jsonl copy differs"
done
echo "{\"d89_rerun\": \"$(date -u +%FT%TZ)\", \"fix_commit\": \"$(git rev-parse "$FIX")\", \"head\": \"$(git rev-parse HEAD)\", \"lock_sha256\": \"$LOCK_NOW\", \"adapter_sha256\": \"$(shasum -a 256 experiments/rlm_ref/adapter.py | cut -c1-64)\", \"runs\": \"$(echo $RUNS)\", \"decisions\": \"D89, D90, D92 (Q185, Q186, Q187, Q188)\", \"answers\": $N, \"rerun\": $(NA rerun), \"rebuilt\": $(NA rebuild), \"stays_failed\": $(NA stays_failed)}" > "$A/rerun.json"
for r in $RUNS; do cp -p "$A/rerun.json" findings/runs/$r/discarded_D89/rerun.json; done

# 4. the 44 answer lines go and the 72 are rebuilt in place (answers.jsonl becomes kept_answers.jsonl)
for r in $RUNS; do
  X=findings/runs/$r/discarded_D89
  cp -p $X/kept_answers.jsonl findings/runs/$r/answers.jsonl.d89_tmp && mv findings/runs/$r/answers.jsonl.d89_tmp findings/runs/$r/answers.jsonl \
    || refuse "$r: could not replace answers.jsonl (the copy before the rerun is $X/answers.jsonl.before_rerun)"
  cmp -s findings/runs/$r/answers.jsonl $X/kept_answers.jsonl || refuse "$r: answers.jsonl is not kept_answers.jsonl"
done

# 5. only the 44, one process per cap and draw, serially
groups | while read cap draw set run qs; do
    echo "$(date +%H:%M) cap $cap draw $draw ($set): $qs"
    $R --cap $cap --draw $draw --question-set $set --questions $qs > $D/rerun_d89_cap${cap}_d${draw}.log 2>&1 < /dev/null \
      || echo "  cap $cap draw $draw ended with exit $? (see $D/rerun_d89_cap${cap}_d${draw}.log)"
  done
echo "reruns ended at $(date +%H:%M); records before them in each run's discarded_D89/ and $A"
echo "next: bash $D/rerun_d89.sh check $A"
curl -s -d "G6 D92 rerun of $(NA rerun) answers ended ($(NA rebuild) rebuilt)" https://ntfy.sh/mentori_alert_system > /dev/null
