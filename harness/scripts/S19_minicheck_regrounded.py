"""S19 - re-score MiniCheck against the SOURCE PAPERS instead of the 2.5-sentence answer key.

Why this exists. The deposited pipeline computes MiniCheck precision as
    "is each generated sentence entailed by gt['expected_answer']?"
(publication/scripts/analysis_minicheck.py:133, :241, :248). The manuscript describes the same
number as claims "grounded in the source text". Those are different quantities, and the
manuscript's description is the false one. This script produces the number the manuscript should
have printed.

Conditions:
  key     document = expected_answer            REPLICATION of the deposited run
  source  document = the question's source paper(s)   THE CORRECTED MEASUREMENT
  decoy   document = a size-matched paper that is NOT a source   CONTROL: rules out the reading
          that precision rises merely because the checker was handed more text to match against

The instrument is unchanged: the same cached MiniCheck-FT5 checkpoint used for the deposited run
(models--lytang--MiniCheck-Flan-T5-Large in <upstream>/data/hf_cache) and the deposited
decompose_to_sentences(), loaded from the deposited source rather than retyped.

Long documents: MiniCheck-FT5 takes about 2k tokens, so a 60k-character paper cannot be one
document. Two modes:
  --retrieval-k N   score each claim against its N most similar chunks (bge-m3) and take the max,
                    which is MiniCheck's own aggregation over sub-documents. Default, affordable.
  --full-doc        hand the whole paper to MiniCheck and let it chunk internally. The reference
                    method, roughly 8.6 s per claim, used on a calibration subsample to measure
                    how much the retrieval mode underestimates.

The current key, --key v22 (item 15, 9 October; ground truth v2.4 since 11 October 09:00 (Q50), v2.3 from 00:00 (Q45)). The key
condition reads the answer key, so it is re-run against the judge's key in the v1 format, S373.AS_V1
(data/ground_truth_v2/ground_truth_v2_4_as_v1.json, S381 --key 2.4), on the same 150 answers
(--sample-answers 150, seed 42) less the answers to the six questions dropped from the key (D7, the same
six in v2.2 and v2.3): 3 of the 150, counted and printed. First it exits unless S373.AS_V1's
source_v<version>_sha256 field (S381's name, from S373.KEY's "version") equals the sha256 of S373.KEY,
as S388 checks. Before any current-key number is written it
rescores the first 20 answers of the v1 key run (S19_minicheck_key_k3.jsonl) with the v1 key on the
chosen device and exits 1 unless n_claims, precision, every claim and every label match exactly and
every probability is within 1e-4 (the file rounds to 4 dp). Output S19_minicheck_key_v22_k3.jsonl (the
name kept from v2.2 so downstream paths hold); the v1 file is never touched. On resume, rows under any
other key sha256 (the v2.2 run's, for one) stop the run until the file is moved aside. Rows carry the key
path and sha256, the source key path, sha256 and version (S373.KEY), the device, the gate result and the sha256 of
nltk's punkt_tab English tables, which MiniCheck's sentence splitter reads (see S384). That data is
not installed by uv; without it the script exits before loading the checker, naming the first
command below.

    uv run python -c "import nltk; nltk.download('punkt_tab')"     # once per machine
    uv run python scripts/S19_minicheck_regrounded.py --condition key --key v22 --sample-answers 150 --device cpu --gate-only
    uv run python scripts/S19_minicheck_regrounded.py --condition key --key v22 --sample-answers 150 --device cpu

--device pins MiniCheck to one device (S384's loader); without it MiniCheck chooses (device_map
"auto"), as the v1 runs did. The checkpoint is found by S384's hf_cache(): $MENTORI_HF_CACHE, else
<upstream>/data/hf_cache, else a sibling checkout's data/hf_cache. S384 scores the 516 exp04 answers
still on the key (528 less 12 on dropped questions) in both directions; these 147 are among them.
For each, S19's key precision comes from the same MiniCheck call, on the same claims and the same
key, as S384's precision (on v1, all 150 precisions in S19_minicheck_key_k3.jsonl equal the
deposited ones).
"""
from __future__ import annotations
import argparse, hashlib, json, math, os, random, re, sys, time, warnings
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent))
from machine import PUB, PUB_SCRIPTS, RECOMPUTE, rel  # noqa: E402
import S373_rejudge_v2 as S373  # noqa: E402  (the judge's key: KEY, AS_V1; imports no model library)

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("TQDM_DISABLE", "1")  # MiniCheck opens a progress bar per score() call, one per answer
                                            # here (inference.py:83); tqdm reads this when first imported
warnings.filterwarnings("ignore")

DEPOSITED = PUB_SCRIPTS / "analysis_minicheck.py"
PAPER = PUB
OUT = RECOMPUTE
KEY_V22 = S373.AS_V1   # the judge's key in the v1 format: ground truth v2.4 since 11 October 09:00 (Q50), v2.3 from 00:00 (Q45) (S381 --key 2.4)
GATE_V1 = OUT / "S19_minicheck_key_k3.jsonl"     # the v1 key run --key v22 must reproduce first
GATE_N, PROB_TOL = 20, 1e-4
OLLAMA = "http://localhost:11434"
SEED = 42


def require_as_v1_from_key() -> None:
    """S388's check: S373.AS_V1's source_v<version>_sha256 (S381's field for the version in S373.KEY's
    "version") must be the sha256 of S373.KEY. Exits otherwise."""
    key_bytes = S373.KEY.read_bytes()
    kv = str(json.loads(key_bytes)["version"])
    src = f"source_v{kv.replace('.', '')}_sha256"
    got = json.loads(S373.AS_V1.read_text(encoding="utf-8")).get(src)
    if got != hashlib.sha256(key_bytes).hexdigest():
        sys.exit(f"FATAL: {S373.AS_V1.name} was built from another key ({src} {str(got)[:12]}), "
                 f"not {S373.KEY.name} v{kv}")


def load_decomposer():
    """Take decompose_to_sentences from the deposited script so the claim set is identical."""
    src = DEPOSITED.read_text()
    h = hashlib.sha256(src.encode()).hexdigest()
    m = re.search(r"\ndef decompose_to_sentences\(.*?(?=\ndef |\nclass |\Z)", src, re.S)
    if not m:
        sys.exit("FATAL: decompose_to_sentences not found in the deposited script")
    ns = {"re": re, "List": list}
    exec(m.group(0), ns)
    return ns["decompose_to_sentences"], h


def embed(texts, batch=16):
    import urllib.request
    out = []
    for i in range(0, len(texts), batch):
        payload = {"model": "bge-m3:latest", "input": texts[i:i + batch]}
        req = urllib.request.Request(OLLAMA + "/api/embed",
                                     data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=600) as r:
            out.extend(json.loads(r.read())["embeddings"])
    return out


def cos(a, b):
    s = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1e-9
    nb = math.sqrt(sum(y * y for y in b)) or 1e-9
    return s / (na * nb)


def check(scorer, claims, docs_for_claims):
    """Score each claim against each of its documents; take the max (MiniCheck's own aggregation
    over sub-documents)."""
    flat_docs, flat_claims, owner = [], [], []
    for i, (cl, dl) in enumerate(zip(claims, docs_for_claims)):
        for d in dl:
            flat_docs.append(d); flat_claims.append(cl); owner.append(i)
    labels, probs, _, _ = scorer.score(docs=flat_docs, claims=flat_claims)
    best = defaultdict(lambda: (0, 0.0))
    for i, l, p in zip(owner, labels, probs):
        if float(p) > best[i][1]:
            best[i] = (int(l), float(p))
    return [{"claim": claims[i][:300], "supported": bool(best[i][0]),
             "probability": round(best[i][1], 4)} for i in range(len(claims))]


def gate_v1_key(scorer, decompose, answers, device):
    """--key v22 only: the first GATE_N answers of the v1 key run, rescored with the v1 key here."""
    v1 = {q["id"]: q for q in json.load(open(PAPER / "data/ground_truth.json"))["questions"]}
    ref = [json.loads(l) for l in open(GATE_V1)][:GATE_N]
    bad, n, exact, worst = [], 0, 0, 0.0
    t0 = time.time()
    for r in ref:
        claims = decompose(answers.get((r["question_id"], r["config"]), ""))
        doc = v1[r["question_id"]].get("expected_answer", "") or ""
        per = check(scorer, claims, [[doc]] * len(claims))
        prec = round(sum(1 for x in per if x["supported"]) / len(per), 4) if per else None
        if len(per) != r["n_claims"] or prec != r["precision"]:
            bad.append((r["question_id"], r["config"], "n_claims/precision",
                        (r["n_claims"], r["precision"]), (len(per), prec)))
        for x, y in zip(per, r["per_claim"]):
            n += 1
            diff = abs(x["probability"] - y["probability"])
            worst = max(worst, diff)
            exact += diff == 0
            if x["claim"] != y["claim"] or x["supported"] != y["supported"] or diff > PROB_TOL + 1e-12:
                bad.append((r["question_id"], r["config"], y["claim"][:40], y["probability"], x["probability"]))
    if bad:
        for b in bad[:20]:
            print("   ", b)
        sys.exit(f"GATE FAIL on {device}: {len(bad)} mismatches against {GATE_V1.name}; nothing written")
    msg = (f"{len(ref)}/{GATE_N} answers of {GATE_V1.name} reproduced with the v1 key on {device}: "
           f"n_claims, precision, claims and labels exact, {exact}/{n} claim probabilities identical "
           f"at 4 dp, max |diff| {worst:.4f}")
    print(f"gate pass ({time.time()-t0:.0f} s): {msg}")
    return msg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--condition", required=True, choices=["key", "source", "decoy"])
    ap.add_argument("--retrieval-k", type=int, default=3)
    ap.add_argument("--full-doc", action="store_true")
    ap.add_argument("--sample-claims", type=int, default=0, help="0 = all")
    ap.add_argument("--sample-answers", type=int, default=0, help="0 = all")
    ap.add_argument("--primary-set-only", action="store_true")
    ap.add_argument("--out", default="")
    ap.add_argument("--key", default="v1", choices=["v1", "v22"],
                    help="v22: the key condition against the judge's current key (S373.AS_V1, ground truth "
                         "v2.4 since 11 October 09:00 (Q50), v2.3 from 00:00 (Q45)), after the 20-answer gate")
    ap.add_argument("--device", default=None, choices=["cpu", "mps", "cuda"],
                    help="pin MiniCheck to one device (default: MiniCheck's own device_map='auto')")
    ap.add_argument("--gate-only", action="store_true", help="--key v22: run the gate, write nothing")
    a = ap.parse_args()
    if a.key == "v22" and a.condition != "key":
        sys.exit("--key v22 applies to --condition key only: source and decoy never read the key")
    if a.gate_only and a.key != "v22":
        sys.exit("--gate-only belongs to --key v22")
    if a.key == "v22":
        require_as_v1_from_key()

    v22 = "_v22" if a.key == "v22" else ""
    tag = f"{a.condition}{v22}{'_fulldoc' if a.full_doc else f'_k{a.retrieval_k}'}"
    outp = Path(a.out) if a.out else OUT / f"S19_minicheck_{tag}.jsonl"
    decompose, dep_sha = load_decomposer()

    key_path = KEY_V22 if a.key == "v22" else PAPER / "data/ground_truth.json"
    gt = json.load(open(key_path))
    qs = {q["id"]: q for q in (gt["questions"] if isinstance(gt, dict) else gt)}
    dropped = set(gt.get("dropped_d7", [])) if isinstance(gt, dict) else set()
    mc = json.load(open(PAPER / "results/exp04_minicheck_latest.json"))
    gen = json.load(open(PAPER / "results/exp04_generation_latest.json"))
    answers = {(r["question_id"], r["config"]): (r["generation"] or {}).get("answer", "")
               for r in gen["per_question_results"] if r.get("answerable")}
    judge = {(r["question_id"], r["config"]): (r["judge_scores"] or {})
             for r in gen["per_question_results"] if r.get("answerable")}

    docs = {json.loads(l)["file"]: json.loads(l)["text"]
            for l in open(OUT / "S18_evidence_docs.jsonl")}
    chunks = [json.loads(l) for l in open(OUT / "S18_evidence_chunks.jsonl")]
    by_file = defaultdict(list)
    for c in chunks:
        by_file[c["file"]].append(c)
    sizing = json.load(open(OUT / "S18_evidence_manifest.json"))["sizing"]
    frozen = json.load(open(OUT / "S18_frozen_analysis_set.json"))["primary_set_full"]

    # decoy donor: nearest by evidence size with no shared source file (deterministic)
    order = sorted(sizing, key=lambda k: (sizing[k]["est_tokens"], k))

    def donor(qid):
        mine = set(sizing[qid]["source_files"])
        i = order.index(qid)
        for step in range(1, len(order)):
            for j in (i + step, i - step):
                if 0 <= j < len(order) and not (set(sizing[order[j]]["source_files"]) & mine):
                    return order[j]
        raise RuntimeError(qid)

    units = [r for r in mc["per_result"]]
    if a.primary_set_only:
        units = [r for r in units if r["question_id"] in frozen]
    rng = random.Random(SEED)
    if a.sample_answers:
        units = rng.sample(units, min(a.sample_answers, len(units)))
    if dropped:             # after the sample, so the current-key answers are the v1 answers less these
        n0 = len(units)
        gone = sorted({u["question_id"] for u in units if u["question_id"] in dropped})
        units = [u for u in units if u["question_id"] not in dropped]
        print(f"skipped {n0 - len(units)} answers on questions dropped from the key (D7): {gone}")

    done = set()
    if outp.exists():
        for line in open(outp):
            try:
                d = json.loads(line)
                done.add((d["question_id"], d["config"]))
            except Exception:
                pass
        print(f"resuming: {len(done)} answers already scored")
        if a.key == "v22":
            key_sha = hashlib.sha256(KEY_V22.read_bytes()).hexdigest()
            stale = {json.loads(l).get("key_sha256") for l in open(outp) if l.strip()} - {key_sha}
            if stale:
                sys.exit(f"{outp.name} holds rows scored against key sha256 {sorted(stale)}, not the "
                         f"current {key_sha}; move it aside")
    units = [u for u in units if (u["question_id"], u["config"]) not in done]

    total_claims = sum(u["minicheck"]["n_gen_sentences"] for u in units)
    print(f"condition={a.condition}  mode={'full-doc' if a.full_doc else f'top-{a.retrieval_k}'}"
          f"  answers={len(units)}  claims~{total_claims}")
    print(f"deposited script sha256={dep_sha[:16]}...")

    from S384_exp04_minicheck_key_v22 import hf_cache, load_minicheck, punkt_tab
    punkt = punkt_tab()            # exits naming the download command if nltk's punkt_tab is missing
    t0 = time.time()
    if a.device:
        scorer, info = load_minicheck(a.device)
        device = info["device"]
    else:
        from minicheck.minicheck import MiniCheck
        scorer = MiniCheck(model_name="flan-t5-large", cache_dir=str(hf_cache()))
        device = str(scorer.model.model.device)
    print(f"MiniCheck loaded in {time.time()-t0:.1f}s on {device}")

    extra = {}
    if a.key == "v22":
        gate = gate_v1_key(scorer, decompose, answers, device)
        if a.gate_only:
            print("gate only: nothing written")
            return
        extra = {"key": rel(KEY_V22), "key_sha256": hashlib.sha256(KEY_V22.read_bytes()).hexdigest(),
                 "key_source": rel(S373.KEY), "key_source_sha256": hashlib.sha256(S373.KEY.read_bytes()).hexdigest(),
                 "key_version": str(json.loads(S373.KEY.read_text(encoding="utf-8"))["version"]),
                 "device": device, "script": "scripts/S19_minicheck_regrounded.py", "gate": gate,
                 "punkt_tab_english_sha256": punkt["punkt_tab_english_sha256"]}

    fh = open(outp, "a")
    n_claims = 0
    t0 = time.time()
    for ui, u in enumerate(units):
        qid, cfg = u["question_id"], u["config"]
        q = qs[qid]
        claims = decompose(answers.get((qid, cfg), ""))
        if not claims:
            continue

        if a.condition == "key":
            doc_src, doc_files = q.get("expected_answer", "") or "", ["<expected_answer>"]
            docs_for_claims = [[doc_src]] * len(claims)
        else:
            src_qid = qid if a.condition == "source" else donor(qid)
            doc_files = sizing[src_qid]["source_files"]
            if a.full_doc:
                whole = "\n\n".join(docs[f] for f in doc_files)
                docs_for_claims = [[whole]] * len(claims)
            else:
                pool = [c for f in doc_files for c in by_file[f]]
                cvs = embed(claims)
                docs_for_claims = []
                for cv in cvs:
                    top = sorted(pool, key=lambda ch: -cos(cv, ch["vector"]))[:a.retrieval_k]
                    docs_for_claims.append([t["text"] for t in top])

        per = check(scorer, claims, docs_for_claims)
        prec = sum(1 for x in per if x["supported"]) / len(per)

        pub = u["minicheck"]
        fh.write(json.dumps({
            "question_id": qid, "config": cfg, "condition": a.condition,
            "mode": "full-doc" if a.full_doc else f"top-{a.retrieval_k}",
            "doc_files": doc_files, "n_claims": len(claims),
            "precision": round(prec, 4),
            "published_precision": pub["precision"],
            "published_n_gen_sentences": pub["n_gen_sentences"],
            "judge_faithfulness": judge.get((qid, cfg), {}).get("faithfulness"),
            "judge_correctness": judge.get((qid, cfg), {}).get("correctness"),
            "deposited_script_sha256": dep_sha,
            "per_claim": per,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            **extra,
        }) + "\n")
        fh.flush(); os.fsync(fh.fileno())
        n_claims += len(claims)

        if (ui + 1) % 10 == 0 or ui + 1 == len(units):
            el = time.time() - t0
            print(f"  {ui+1}/{len(units)} answers, {n_claims} claims, {el/60:.1f} min, "
                  f"{el/max(n_claims,1):.2f} s/claim, "
                  f"ETA {(total_claims-n_claims)*el/max(n_claims,1)/60:.0f} min", flush=True)
    fh.close()
    print(f"\ndone: {n_claims} claims in {(time.time()-t0)/60:.1f} min -> {outp}")


if __name__ == "__main__":
    main()
