"""S18b - four-arm grounded re-judge of exp04's 528 answerable answers.

Design and pre-committed interpretations: findings/S18_PREREGISTRATION.md

Arms (only the named variable differs between adjacent arms):
  A   published prompt, answer truncated at 3000 chars, num_ctx 16384, num_predict 8192
      -> REPLICATION GATE: must reproduce the deposited scores
  A2  as A but num_ctx 40960 / num_predict 1024          -> isolates the context setting itself
  B   as A2 but the FULL answer                          -> isolates the 3000-char truncation
  C   as B plus a Source Material section                -> isolates supplying the evidence

Anti-drift measures:
  * the judge prompt template and the score parser are LOADED FROM THE HARNESS SOURCE at runtime,
    never retyped here, so arm A cannot drift from what was published;
  * the harness source file is hashed and the hash is written on every row;
  * Ollama's prompt_eval_count is checked against the truncation ceiling on every call;
  * the raw response text is stored, so a parser change can be re-applied after the fact.

Append-only and resumable. Single model instance, no parallelism.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, sys, time
from pathlib import Path
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parent))
from machine import PUB, RECOMPUTE, ROOT   # noqa: E402

HARNESS = ROOT / "recovered_harness/tests/experiments_v4/exp_common.py"
PAPER = PUB
OUT = RECOMPUTE
OLLAMA = "http://localhost:11434"
MODEL = "qwen3-coder:latest"
EXPECT_DIGEST = "06c1097efce0"
RAW = OUT / "S18_rejudge_raw.jsonl"

ARMS = {
    # name: evidence, truncate_chars, num_ctx, num_predict
    "A":  dict(evidence=None,       truncate=3000, num_ctx=16384, num_predict=8192),
    "A2": dict(evidence=None,       truncate=3000, num_ctx=40960, num_predict=1024),
    "B":  dict(evidence=None,       truncate=None, num_ctx=40960, num_predict=1024),
    "B2": dict(evidence=None,       truncate=None, num_ctx=40960, num_predict=1024),
    "C":  dict(evidence="correct",  truncate=None, num_ctx=40960, num_predict=1024),
    "D":  dict(evidence="mismatch", truncate=None, num_ctx=40960, num_predict=1024),
}
# B2 is a byte-identical repeat of B. It measures the judge's own run-to-run noise floor,
# which GPU reduction-order nondeterminism makes non-zero even at temperature 0. Without it,
# a C-vs-B difference cannot be separated from noise.
# D supplies a DIFFERENT paper's text as evidence, matched on size. It separates "the judge
# reads the evidence" from "the judge behaves differently when the prompt is long".
#   C vs B = effect of adding evidence at all
#   D vs B = effect of adding an equivalent amount of irrelevant text
#   C vs D = effect of the evidence being the RIGHT evidence   <- the quantity of interest
DIMS = ["correctness", "completeness", "faithfulness", "citation_quality"]


# ───────────────────────────────────────────── load prompt + parser from the harness source
def load_harness():
    src = HARNESS.read_text()
    h = hashlib.sha256(src.encode()).hexdigest()
    m = re.search(r'ANSWERABLE_JUDGE_PROMPT\s*=\s*"""(.*?)"""', src, re.S)
    if not m:
        sys.exit("FATAL: could not find ANSWERABLE_JUDGE_PROMPT in the harness source")
    template = m.group(1)
    fn = re.search(r'\ndef parse_judge_scores\(.*?(?=\n\ndef |\n\nasync def |\Z)', src, re.S)
    if not fn:
        sys.exit("FATAL: could not find parse_judge_scores in the harness source")
    ns = {"re": re, "json": json, "Dict": dict, "Any": object}
    exec(fn.group(0), ns)
    return template, ns["parse_judge_scores"], h, len(template)


# ───────────────────────────────────────────────────────────────────────── ollama
def check_digest():
    with urllib.request.urlopen(OLLAMA + "/api/tags", timeout=30) as r:
        tags = json.loads(r.read())
    for m in tags["models"]:
        if m["name"] == MODEL:
            d = m["digest"][:12]
            if d != EXPECT_DIGEST:
                sys.exit(f"FATAL: {MODEL} digest is {d}, expected {EXPECT_DIGEST}. "
                         "The judge model has changed; the replication arm would be meaningless.")
            return d, m.get("details", {})
    sys.exit(f"FATAL: {MODEL} not present in ollama")


def generate(prompt, options, timeout=1800):
    payload = {"model": MODEL, "prompt": prompt, "stream": False,
               "options": options, "keep_alive": "120m", "think": False}
    req = urllib.request.Request(OLLAMA + "/api/generate",
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read())
    d["_wall_s"] = round(time.time() - t0, 2)
    return d


# ───────────────────────────────────────────────────────────────────────── evidence
def mismatch_partner(qid, sizing, order):
    """Deterministic donor for the mismatched-evidence control: the nearest question in the
    size-sorted order whose source files do not overlap this one's. No randomness."""
    mine = set(sizing[qid]["source_files"])
    i = order.index(qid)
    n = len(order)
    for step in range(1, n):
        for j in (i + step, i - step):
            if 0 <= j < n:
                cand = order[j]
                if not (set(sizing[cand]["source_files"]) & mine):
                    return cand
    raise RuntimeError(f"no disjoint donor for {qid}")


def build_evidence(qid, sizing, docs, chunks, q_text, budget_chars):
    """Return (evidence_text, mode, n_chars). mode 'full' uses whole papers, no retrieval."""
    info = sizing[qid]
    srcs = info["source_files"]
    if info["mode"] == "full":
        parts = [f"--- SOURCE: {f} ---\n{docs[f]}" for f in srcs]
        return "\n\n".join(parts), "full", sum(len(p) for p in parts)
    # selected: rank this question's chunks by cosine against the question, fill the budget
    import math
    qv = embed_one(q_text)
    cand = [c for c in chunks if c["file"] in srcs]

    def cos(a, b):
        s = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a)) or 1e-9
        nb = math.sqrt(sum(y * y for y in b)) or 1e-9
        return s / (na * nb)

    ranked = sorted(cand, key=lambda c: -cos(qv, c["vector"]))
    picked, tot = [], 0
    for c in ranked:
        if tot + len(c["text"]) > budget_chars:
            continue
        picked.append(c)
        tot += len(c["text"])
        if tot > budget_chars * 0.95:
            break
    picked.sort(key=lambda c: (c["file"], c["idx"]))
    parts = [f"--- SOURCE: {c['file']} (excerpt {c['idx']}) ---\n{c['text']}" for c in picked]
    return "\n\n".join(parts), "selected", tot


_embed_cache = {}


def embed_one(text):
    if text in _embed_cache:
        return _embed_cache[text]
    payload = {"model": "bge-m3:latest", "input": [text]}
    req = urllib.request.Request(OLLAMA + "/api/embed",
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        v = json.loads(r.read())["embeddings"][0]
    _embed_cache[text] = v
    return v


# ───────────────────────────────────────────────────────────────────────── prompt
def build_prompt(template, q, answer, evidence, truncate):
    """Reproduce exp_common.judge_answer's fill sequence exactly (exp_common.py:381-388),
    optionally inserting a Source Material section before the Generated Answer."""
    concepts = ", ".join(q.get("expected_concepts") or []) or "N/A"
    body = answer if truncate is None else answer[:truncate]
    p = template.replace("{question}", q["question"])
    p = p.replace("{expected_answer}", q.get("expected_answer", "") or "")
    p = p.replace("{expected_concepts}", concepts)
    p = p.replace("{generated_answer}", body)
    if evidence:
        marker = "## Generated Answer"
        assert marker in p, "prompt template shape changed; refusing to guess placement"
        p = p.replace(marker,
                      "## Source Material\n\nThe following is the full text of the source "
                      "document(s) this question was written from. Judge faithfulness against "
                      "this material.\n\n" + evidence + "\n\n" + marker, 1)
    return p


# ───────────────────────────────────────────────────────────────────────── main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", default="A,A2,B,B2,C,D")
    ap.add_argument("--limit", type=int, default=0, help="first N questions only (smoke test)")
    ap.add_argument("--questions", default="", help="comma-separated question ids")
    ap.add_argument("--budget-tokens", type=int, default=28000)
    ap.add_argument("--out", default=str(RAW))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    template, parse_scores, hsha, tlen = load_harness()
    digest, details = check_digest()
    print(f"judge {MODEL} digest={digest} {details.get('quantization_level')} "
          f"{details.get('parameter_size')}")
    print(f"harness {HARNESS.name} sha256={hsha[:16]}... template {tlen} chars")

    gt = json.load(open(PAPER / "data/ground_truth.json"))
    qs = {q["id"]: q for q in (gt["questions"] if isinstance(gt, dict) else gt)}
    gen = json.load(open(PAPER / "results/exp04_generation_latest.json"))
    rows = [r for r in gen["per_question_results"] if r.get("answerable")]
    published = {(r["question_id"], r["config"]): (r["judge_scores"] or {}) for r in rows}
    answers = {(r["question_id"], r["config"]): (r["generation"] or {}).get("answer", "")
               for r in rows}

    origin = json.load(open(OUT / "S18_published_origin.json"))
    with urllib.request.urlopen(OLLAMA + "/api/version", timeout=30) as r:
        ollama_version = json.loads(r.read()).get("version")
    print(f"ollama {ollama_version}; published scores: "
          f"{sum(1 for v in origin.values() if v=='main')} from the main judging pass, "
          f"{sum(1 for v in origin.values() if v=='fixup')} from the fixup pass")

    man = json.load(open(OUT / "S18_evidence_manifest.json"))
    sizing = man["sizing"]
    docs = {json.loads(l)["file"]: json.loads(l)["text"]
            for l in open(OUT / "S18_evidence_docs.jsonl")}
    chunks = [json.loads(l) for l in open(OUT / "S18_evidence_chunks.jsonl")]
    if chunks and "vector" not in chunks[0]:
        print("NOTE: chunks are not embedded; 'selected' mode unavailable "
              "(re-run S18a without --no-embed)")

    qids = sorted({r["question_id"] for r in rows})
    if a.questions:
        qids = [q for q in a.questions.split(",") if q in qids]
    if a.limit:
        qids = qids[:a.limit]
    configs = sorted({r["config"] for r in rows})
    arms = [x for x in a.arms.split(",") if x in ARMS]

    done = set()
    outp = Path(a.out)
    if outp.exists():
        for line in open(outp):
            try:
                d = json.loads(line)
                done.add((d["arm"], d["question_id"], d["config"]))
            except Exception:
                pass
        print(f"resuming: {len(done)} calls already recorded in {outp.name}")

    # Ordering matters twice over.
    #  (1) Within a question, keep the 6 configs of an arm consecutive so the evidence prefix
    #      stays in the KV cache (measured 176x speedup, S18_probe_preflight.py).
    #  (2) B2 must NOT run straight after B: its prompt is byte-identical, so it would replay
    #      B's cache and measure "noise with a warm cache" rather than independent re-run noise.
    #      B2 therefore runs as a separate final pass, after every question's C and D have
    #      flushed the cache with 17k-token evidence prompts.
    #  (3) ARM-MAJOR. num_ctx differs between arm A (16,384) and the rest (40,960); a
    #      question-major loop flips it twice per question and forces Ollama to reload the
    #      model ~176 times. Arm-major holds num_ctx constant for a whole arm: one load each.
    main_arms = [x for x in arms if x != "B2"]
    todo = [(qid, arm, cfg) for arm in main_arms for qid in qids for cfg in configs
            if (arm, qid, cfg) not in done]
    if "B2" in arms:
        todo += [(qid, "B2", cfg) for qid in qids for cfg in configs
                 if ("B2", qid, cfg) not in done]
    print(f"work: {len(qids)} questions x {len(arms)} arms x {len(configs)} configs "
          f"= {len(qids)*len(arms)*len(configs)} calls, {len(todo)} remaining")
    if a.dry_run:
        return

    budget_chars = int(a.budget_tokens * 3.82)
    # deterministic size-sorted order, used only to pick mismatched-evidence donors
    order = sorted(sizing.keys(), key=lambda k: (sizing[k]["est_tokens"], k))
    fh = open(outp, "a")
    t0 = time.time()
    n_done = 0
    ev_cache = {}

    for qid, arm, cfg in todo:
        q = qs[qid]
        spec = ARMS[arm]
        ev, mode, ev_chars, ev_src = "", None, 0, None
        if spec["evidence"]:
            src_qid = qid if spec["evidence"] == "correct" else mismatch_partner(qid, sizing, order)
            key = (src_qid, spec["evidence"])
            if key not in ev_cache:
                ev_cache[key] = build_evidence(src_qid, sizing, docs, chunks,
                                               qs[src_qid]["question"], budget_chars)
            ev, m0, ev_chars = ev_cache[key]
            mode = f"{spec['evidence']}:{m0}"
            ev_src = src_qid
        prompt = build_prompt(template, q, answers[(qid, cfg)], ev, spec["truncate"])
        opts = {"temperature": 0, "num_predict": spec["num_predict"], "num_ctx": spec["num_ctx"]}
        ceiling = spec["num_ctx"] - spec["num_predict"]

        try:
            resp = generate(prompt, opts)
            err = None
        except Exception as e:
            resp, err = {}, f"{type(e).__name__}: {e}"

        pec = resp.get("prompt_eval_count")
        truncated = pec is not None and pec >= ceiling - 8
        text = resp.get("response", "") or ""
        parsed = parse_scores(text, answerable=True) if text else None

        rec = {
            "arm": arm, "question_id": qid, "config": cfg,
            "model": MODEL, "model_digest": digest,
            "harness_sha256": hsha,
            "options": opts, "truncate_chars": spec["truncate"],
            "evidence_mode": mode, "evidence_chars": ev_chars,
            "evidence_source_qid": ev_src,
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "prompt_chars": len(prompt),
            "prompt_eval_count": pec, "eval_count": resp.get("eval_count"),
            "done_reason": resp.get("done_reason"),
            "output_truncated": (resp.get("done_reason") == "length"
                                 or (resp.get("eval_count") or 0) >= spec["num_predict"]),
            "evidence_tokens": int(ev_chars / 3.82) if ev_chars else 0,
            "ollama_version": ollama_version,
            "published_origin": origin.get(f"{qid}|{cfg}"),
            "ceiling_tokens": ceiling, "hit_ceiling": truncated,
            "wall_s": resp.get("_wall_s"),
            "response_raw": text,
            "parsed": parsed,
            "published": published[(qid, cfg)] if arm == "A" else None,
            "error": err,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        fh.write(json.dumps(rec) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
        n_done += 1

        if rec["output_truncated"]:
            fh.close()
            sys.exit(f"\nFATAL: the judge response was cut off at num_predict on arm={arm} "
                     f"{qid}/{cfg} (done_reason={resp.get('done_reason')}, "
                     f"eval_count={resp.get('eval_count')}). parse_judge_scores turns a cut-off "
                     f"response into 0/0/0/0, which cannot be told apart from a real zero score.")
        if truncated:
            fh.close()
            sys.exit(f"\nFATAL guard 8.1: prompt hit the context ceiling "
                     f"({pec} >= {ceiling}) on arm={arm} {qid}/{cfg}. Ollama truncates silently; "
                     f"the run is stopped rather than producing quietly invalid scores.")
        if err:
            print(f"  ERROR arm={arm} {qid}/{cfg}: {err}")

        if n_done % 10 == 0 or n_done == len(todo):
            el = time.time() - t0
            rate = el / n_done
            print(f"  {n_done}/{len(todo)}  {el/60:.1f} min elapsed, "
                  f"{rate:.1f} s/call, ETA {(len(todo)-n_done)*rate/60:.0f} min", flush=True)

    fh.close()
    print(f"\ncomplete: {n_done} calls in {(time.time()-t0)/60:.1f} min -> {outp}")


if __name__ == "__main__":
    main()
