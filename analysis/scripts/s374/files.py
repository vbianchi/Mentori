import glob,os
import sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from machine import PUB, RECOMPUTE
R=str(PUB / 'results') + '/'
F=str(RECOMPUTE) + '/'
FILES=[]  # (experiment, path, rowpath-kind)
FILES.append(('Generation strategies (exp04)', R+'exp04_generation_latest.json'))
FILES.append(('Corpus scaling (exp05)', R+'exp05_scaling_latest.json'))
FILES.append(('Orchestration (exp06)', R+'exp06_orchestration_ablation_latest.json'))
FILES.append(('Naive RAG baseline', R+'analysis_naive_baseline_latest.json'))
FILES.append(('Strategy replication (published)', R+'deep_analyses/reviewer_strategy_replication.json'))
FILES.append(('Strategy replication (published)', R+'deep_analyses/reviewer_strategy_replication_122b.json'))
for f in sorted(glob.glob(R+'exp09_depth_sweep_*_merged.json')): FILES.append(('Retrieval depth (exp09)', f))
FILES.append(('Generator selection (exp00 rlm_models)', R+'exp00_rlm_models_latest.json'))
FILES.append(('Generator selection phase 2 (exp00)', R+'exp00_phase2_latest.json'))
FILES.append(('Model triage (exp00)', R+'exp00_triage_latest.json'))
for f in sorted(glob.glob(R+'exp07_bench_synthesizer_*.json')):
    b=os.path.basename(f)
    if 'dataset' in b or 'results' in b: continue
    FILES.append(('Component benchmark: synthesizer (exp07)', f))
for f in sorted(glob.glob(F+'S141_campaign/*/results.json')): FILES.append(('S141 campaign (strategy replication, multi-generator)', f))
for f in sorted(glob.glob(F+'S141_mini/mini__*/results.json')): FILES.append(('S141 mini arm (step 4.3, s50)', f))
for f in sorted(glob.glob(F+'S141_timing/timing__*/results.json')): FILES.append(('S141 timing (step 4.4)', f))
FILES.append(('S357 Gemini paired arm', F+'S357/arm_gemini/results.json'))
FILES.append(('S314 verified_pass rerun (exp05 indexes)', F+'S314_verified_pass_raw.jsonl'))
