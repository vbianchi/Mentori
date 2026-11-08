"""S21 - re-judge every truncated answer in the deposit with the FULL answer.

WHY ONLY THE TRUNCATED ONES. exp_common.judge_answer does `generated[:3000]`. For an answer
shorter than that the slice is a no-op: the prompt is byte-identical with and without it, and
the judge is bit-deterministic at temperature 0 (S18 arms B vs B2, exact agreement 1.000 on all
four dimensions, n=372). So the 10,349 uncut scores carry over unchanged by proof, and only the
2,390 cut answers need a model call.

ARMS
  T   answer[:3000], published judge options (num_ctx 16384 / num_predict 8192)
      -> REPLICATION GATE. Must reproduce the deposited scores. Run on a stratified sample,
         because its purpose is to measure replication drift, not to restate published numbers.
  F   FULL answer, num_ctx 40960 / num_predict 1024
      -> the corrected scores. Run on every cut answer.

The raised context in F is not a free variable: S18 arms A vs A2 changed num_ctx alone and got
exact agreement 1.000 (n=372), so the context setting is inert. It is raised here only because
the published ceiling (num_ctx - num_predict = 8192 tokens) is smaller than some full prompts,
and Ollama truncates silently when a prompt exceeds it.

WHY THE T ARM EXISTS AT ALL. Comparing new full-answer scores against published truncated scores
confounds the truncation effect with run-to-run replication drift, which arm A of S18 measured at
1.5% disagreement on exp04. T measures that drift on each experiment family so the comparison can
be corrected rather than assumed clean.

Anti-drift, inherited from S18b: the prompt templates and the score parser are LOADED FROM THE
HARNESS SOURCE at runtime and never retyped; the harness file is hashed onto every row; the model
digest is checked; and prompt_eval_count is checked against the context ceiling on every call so
a silent truncation cannot pass as a result.

Append-only and resumable. Arm-major so Ollama loads the model once per arm.

  python scripts/S21_full_answer_rejudge.py --pilot            # ~140 calls, checks the gate
  python scripts/S21_full_answer_rejudge.py --arms T,F         # the full job
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, sys, time
from pathlib import Path
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parent))
from machine import PUB, RECOMPUTE, ROOT  # noqa: E402

PAPER = PUB
HARNESS = ROOT / "recovered_harness/tests/experiments_v4/exp_common.py"
OUT = RECOMPUTE
RAW = OUT / "S21_rejudge_raw.jsonl"
OLLAMA = "http://localhost:11434"
MODEL = "qwen3-coder:latest"
EXPECT_DIGEST = "06c1097efce0"
CUT = 3000

ARMS = {
    # published options: JUDGE_OPTIONS = {temperature 0, num_predict NUM_PREDICT=8192,
    #                                     num_ctx JUDGE_NUM_CTX=16384}   (exp_common.py:34-40)
    "T": dict(truncate=CUT,  num_ctx=16384, num_predict=8192),
    "F": dict(truncate=None, num_ctx=40960, num_predict=1024),
    # R: rows the deposit never actually scored. exp_common.judge_answer catches judge
    # exceptions and writes zeros with justification "Judge error: ...", so a deposited
    # 0/0/0/0 carrying that marker is a failed call, not a verdict. Same conditions as F;
    # separate arm because there is no published score to compare against, only to replace.
    "R": dict(truncate=None, num_ctx=40960, num_predict=1024),
}
DIMS = ("correctness", "completeness", "faithfulness", "citation_quality")
UNANS_DIMS = ("refusal_accuracy", "hallucination_avoidance", "explanation_quality")


# ───────────────────────────────────────── load prompts + parser from the harness source
def load_harness():
    src = HARNESS.read_text()
    h = hashlib.sha256(src.encode()).hexdigest()
    out = {}
    for name in ("ANSWERABLE_JUDGE_PROMPT", "UNANSWERABLE_JUDGE_PROMPT"):
        m = re.search(name + r'\s*=\s*"""(.*?)"""', src, re.S)
        if not m:
            sys.exit(f"FATAL: could not find {name} in the harness source")
        out[name] = m.group(1)
    fn = re.search(r'\ndef parse_judge_scores\(.*?(?=\n\ndef |\n\nasync def |\Z)', src, re.S)
    if not fn:
        sys.exit("FATAL: could not find parse_judge_scores in the harness source")
    ns = {"re": re, "json": json, "Dict": dict, "Any": object}
    exec(fn.group(0), ns)
    return out, ns["parse_judge_scores"], h


def check_digest():
    with urllib.request.urlopen(OLLAMA + "/api/tags", timeout=30) as r:
        tags = json.loads(r.read())
    for m in tags["models"]:
        if m["name"] == MODEL:
            d = m["digest"][:12]
            if d != EXPECT_DIGEST:
                sys.exit(f"FATAL: {MODEL} digest is {d}, expected {EXPECT_DIGEST}. "
                         "The judge model changed; the replication arm would be meaningless.")
            return d, m.get("details", {})
    sys.exit(f"FATAL: {MODEL} not present in ollama")


def generate(prompt, options, timeout=1800):
    payload = {"model": MODEL, "prompt": prompt, "stream": False, "options": options,
               "keep_alive": "120m", "think": False}   # JUDGE_THINK = False (exp_common.py:41)
    req = urllib.request.Request(OLLAMA + "/api/generate",
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read())
    d["_wall_s"] = round(time.time() - t0, 2)
    return d


# ───────────────────────────────────────────────────────────────── enumerate the work
def judged_rows(o):
    if isinstance(o, dict):
        if "judge_scores" in o:
            yield o
        for v in o.values():
            yield from judged_rows(v)
    elif isinstance(o, list):
        for v in o:
            yield from judged_rows(v)


def answer_text(r):
    g = r.get("generation")
    if isinstance(g, dict) and g.get("answer"):
        return g["answer"]
    for k in ("answer", "response", "output", "text", "generated_answer"):
        if isinstance(r.get(k), str) and r[k]:
            return r[k]
    return None


def is_answerable(r):
    """Prefer the published score schema, which is what the judge actually produced."""
    js = r.get("judge_scores") or {}
    if any(k in js for k in UNANS_DIMS):
        return False
    if any(k in js for k in DIMS):
        return True
    return bool(r.get("answerable", True))


def is_judge_error(r):
    """A deposited zero written by the harness exception path, not a verdict.
    exp_common.judge_answer:409-421 returns all-zero scores with this justification."""
    js = r.get("judge_scores") or {}
    return "Judge error" in str(js.get("justification", ""))


def collect(gt_questions):
    """Every judged answer with text, tagged cut / judge-error, across the deposit."""
    import glob
    work, gt_miss, inline_mismatch = [], 0, 0
    for f in sorted(glob.glob(str(PAPER / "results" / "*_latest.json"))):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        for i, r in enumerate(judged_rows(d)):
            t = answer_text(r)
            if not t:
                continue
            cut, err = len(t) > CUT, is_judge_error(r)
            if not cut and not err:
                continue                      # nothing to do: prompt identical, score valid
            qid = r.get("question_id")
            q = gt_questions.get(qid)
            # expected_* : prefer the row's own copy, fall back to ground truth
            exp_a = r.get("expected_answer")
            exp_c = r.get("expected_concepts")
            if q is not None:
                if exp_a is not None and (q.get("expected_answer") or "") != exp_a:
                    inline_mismatch += 1
                if exp_a is None:
                    exp_a = q.get("expected_answer") or ""
                if exp_c is None:
                    exp_c = q.get("expected_concepts") or []
            elif exp_a is None:
                gt_miss += 1
                continue
            qtext = r.get("question") or (q or {}).get("question") or ""
            work.append({
                "file": os.path.basename(f), "row_idx": i, "question_id": qid,
                "config": r.get("config") or r.get("model") or "",
                "depth": r.get("depth"), "answerable": is_answerable(r),
                "question": qtext, "expected_answer": exp_a or "",
                "expected_concepts": exp_c or [], "answer": t,
                "published": r.get("judge_scores") or {},
                "is_cut": cut, "published_is_error": err,
            })
    return work, gt_miss, inline_mismatch


def build_prompt(templates, w, truncate):
    """Reproduce exp_common.judge_answer's fill sequence exactly (exp_common.py:380-388)."""
    body = w["answer"] if truncate is None else w["answer"][:truncate]
    if w["answerable"]:
        p = templates["ANSWERABLE_JUDGE_PROMPT"]
        concepts = ", ".join(w["expected_concepts"]) if w["expected_concepts"] else "N/A"
        p = p.replace("{question}", w["question"])
        p = p.replace("{expected_answer}", w["expected_answer"])
        p = p.replace("{expected_concepts}", concepts)
        p = p.replace("{generated_answer}", body)
    else:
        p = templates["UNANSWERABLE_JUDGE_PROMPT"]
        p = p.replace("{question}", w["question"])
        p = p.replace("{generated_answer}", body)
    return p


def stratified_sample(work, frac, floor):
    """Deterministic every-k-th pick within each file. No randomness, so it is reproducible."""
    by = {}
    for w in work:
        by.setdefault(w["file"], []).append(w)
    picked = []
    for f, rows in sorted(by.items()):
        rows = sorted(rows, key=lambda r: (r["question_id"] or "", str(r["config"]), r["row_idx"]))
        n = min(len(rows), max(floor, round(frac * len(rows))))
        if n >= len(rows):
            picked.extend(rows)
            continue
        step = len(rows) / n
        picked.extend(rows[int(i * step)] for i in range(n))
    return picked


def key(w, arm):
    return f"{w['file']}|{w['row_idx']}|{arm}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", default="T,F,R")
    ap.add_argument("--sample-frac", type=float, default=0.15, help="arm T sampling fraction")
    ap.add_argument("--sample-floor", type=int, default=40, help="arm T minimum per file")
    ap.add_argument("--pilot", action="store_true", help="8 per file, arm T only, then report")
    ap.add_argument("--out", default=str(RAW))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    templates, parse_scores, hsha = load_harness()
    digest, details = check_digest()
    gt = json.load(open(PAPER / "data/ground_truth.json"))
    qs = {q["id"]: q for q in (gt["questions"] if isinstance(gt, dict) else gt)}

    work, gt_miss, inline_mismatch = collect(qs)
    cut = [w for w in work if w["is_cut"]]
    cut_valid = [w for w in cut if not w["published_is_error"]]
    err_uncut = [w for w in work if w["published_is_error"] and not w["is_cut"]]
    print(f"judge {MODEL} digest={digest} {details.get('parameter_size')} "
          f"{details.get('quantization_level')}")
    print(f"harness sha256={hsha[:16]}...  ground_truth {len(qs)} questions")
    print(f"cut answers: {len(cut)}  (with a real published score: {len(cut_valid)}, "
          f"published score is a judge error: {len(cut) - len(cut_valid)})")
    print(f"uncut rows whose published score is a judge error: {len(err_uncut)}")
    print(f"unresolvable: {gt_miss}   inline/GT expected_answer mismatches: {inline_mismatch}")
    if gt_miss:
        sys.exit("FATAL: some rows have no expected answer; refusing to guess")

    longest = max(work, key=lambda w: len(w["answer"]))
    print(f"longest answer: {len(longest['answer'])} chars ({longest['file']} "
          f"{longest['question_id']})")

    arms = [x for x in a.arms.split(",") if x in ARMS]
    if a.pilot:
        arms = ["T"]
        plan = {"T": stratified_sample(cut_valid, 0.0, 8)}
    else:
        plan = {}
        if "T" in arms:
            # only rows with a real published score can gate anything
            plan["T"] = stratified_sample(cut_valid, a.sample_frac, a.sample_floor)
        if "F" in arms:
            plan["F"] = cut
        if "R" in arms:
            plan["R"] = err_uncut

    total = sum(len(v) for v in plan.values())
    for arm in arms:
        print(f"  arm {arm}: {len(plan[arm])} calls  {ARMS[arm]}")

    # context-ceiling preflight: refuse to start a run whose prompts cannot fit
    for arm in arms:
        spec = ARMS[arm]
        ceiling = spec["num_ctx"] - spec["num_predict"]
        worst = max(len(build_prompt(templates, w, spec["truncate"])) for w in plan[arm])
        est = worst * 0.239           # tokens/char, measured on S18 arm B
        print(f"  arm {arm}: worst prompt {worst} chars ~= {est:.0f} tokens, "
              f"ceiling {ceiling} tokens {'OK' if est < ceiling * 0.9 else '*** TOO TIGHT ***'}")
        if est >= ceiling * 0.9:
            sys.exit(f"FATAL: arm {arm} prompts do not fit under the context ceiling")

    outp = Path(a.out)
    done = set()
    if outp.exists():
        for line in open(outp):
            try:
                d = json.loads(line)
                done.add(f"{d['file']}|{d['row_idx']}|{d['arm']}")
            except Exception:
                pass
    todo = total - sum(1 for arm in arms for w in plan[arm] if key(w, arm) in done)
    print(f"already done: {len(done)}   to run: {todo}")
    if a.dry_run:
        return

    OUT.mkdir(parents=True, exist_ok=True)
    fh = open(outp, "a")
    n = 0
    t_start = time.time()
    for arm in arms:                      # arm-major: one model load per arm
        spec = ARMS[arm]
        opts = {"temperature": 0, "num_predict": spec["num_predict"], "num_ctx": spec["num_ctx"]}
        ceiling = spec["num_ctx"] - spec["num_predict"]
        for w in plan[arm]:
            if key(w, arm) in done:
                continue
            prompt = build_prompt(templates, w, spec["truncate"])
            rec = {"arm": arm, "file": w["file"], "row_idx": w["row_idx"],
                   "question_id": w["question_id"], "config": w["config"], "depth": w["depth"],
                   "answerable": w["answerable"], "answer_chars": len(w["answer"]),
                   "is_cut": w["is_cut"], "published_is_error": w["published_is_error"],
                   "truncate_chars": spec["truncate"], "options": opts,
                   "prompt_chars": len(prompt),
                   "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                   "harness_sha256": hsha, "model": MODEL, "model_digest": digest,
                   "published": w["published"], "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
            try:
                resp = generate(prompt, opts)
                raw = resp.get("response", "")
                rec.update({
                    "parsed": parse_scores(raw, answerable=w["answerable"]),
                    "response_raw": raw,
                    "prompt_eval_count": resp.get("prompt_eval_count"),
                    "eval_count": resp.get("eval_count"),
                    "done_reason": resp.get("done_reason"),
                    "wall_s": resp["_wall_s"], "error": None,
                })
                pec = resp.get("prompt_eval_count")
                rec["ceiling_tokens"] = ceiling
                rec["hit_ceiling"] = bool(pec and pec >= ceiling - 8)
                rec["output_truncated"] = resp.get("done_reason") == "length"
                if rec["hit_ceiling"]:
                    print(f"\n*** PROMPT HIT THE CONTEXT CEILING ({pec} >= {ceiling}) on "
                          f"{arm} {w['file']} {w['question_id']}; ollama truncates silently ***")
                if rec["output_truncated"]:
                    print(f"\n*** OUTPUT TRUNCATED on {arm} {w['file']} {w['question_id']} ***")
            except Exception as e:
                rec.update({"parsed": None, "response_raw": "", "error": repr(e),
                            "wall_s": None})
                print(f"\nERROR {arm} {w['file']} {w['question_id']}: {e}")
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            n += 1
            if n % 25 == 0:
                el = time.time() - t_start
                print(f"  {n}/{todo}  {el/60:.1f} min elapsed, "
                      f"{(el/n)*(todo-n)/60:.0f} min left", flush=True)
    fh.close()
    print(f"\ndone: {n} calls in {(time.time()-t_start)/60:.1f} min -> {outp}")

    if a.pilot:
        report_gate(outp)


def report_gate(outp):
    """Arm T must reproduce the deposited scores. Report exact agreement per file."""
    import collections
    agree = collections.defaultdict(lambda: collections.Counter())
    for line in open(outp):
        d = json.loads(line)
        if d["arm"] != "T" or not d.get("parsed"):
            continue
        dims = DIMS if d["answerable"] else UNANS_DIMS
        for k in dims:
            if k in (d["published"] or {}) and k in d["parsed"]:
                agree[d["file"]][f"{k}_n"] += 1
                if int(d["published"][k]) == int(d["parsed"][k]):
                    agree[d["file"]][f"{k}_eq"] += 1
    print(f"\n{'REPLICATION GATE (arm T vs published)':60s}")
    for f, c in sorted(agree.items()):
        parts = []
        for k in list(DIMS) + list(UNANS_DIMS):
            if c[f"{k}_n"]:
                parts.append(f"{k[:4]} {c[f'{k}_eq']}/{c[f'{k}_n']}")
        print(f"  {f:52s} {'  '.join(parts)}")


if __name__ == "__main__":
    main()
