#!/usr/bin/env python3
"""Step 4.2b — the signals work-plan 1.6 declares, computed over the banked answers.

**Why this exists.** 1.6 specifies five per-row signals: concept recall, complete-answer semantic
similarity, MiniCheck NLI, the citation-format census and number overlap. All five were built, all
passed gate P5/P6/P21/P23, and **none was wired into Phase 4** — `S141_campaign_worker.py` never
imports `S141_runner.scorers`, so every campaign row carries exactly two signal fields, both the
archive's own (`judge_scores`, `citation_metrics`). Filed as D11. Two preregistration sentences
depend on the missing ones: S-c "computable from signals already collected" and S-d "cost no model
compute at all once all three signals exist per arm".

**This is a repair, not a re-run.** Nothing regenerates, no archived file is edited, and the
campaign results are opened read-only. Output goes to its own tree, one JSONL per arm per stage,
resumable by row key.

**The instruments are the deposited ones, loaded from the deposited source rather than retyped**,
so the definitions cannot drift — the same convention `S19_minicheck_regrounded.py` uses for the
decomposer. Their sha256 is recorded in the header.

    concept recall     analysis_deterministic_scorer.compute_concept_recall     verbatim
    number overlap     analysis_deterministic_scorer.compute_number_overlap     on citation-
                       stripped text, which is the one change 1.6 specifies
    MiniCheck          analysis_minicheck.score_faithfulness + decompose_to_sentences, against
                       the expert answer key (CL-73: the deposited run's reference text, which
                       Methods misdescribes as source passages; S19 measured the difference)
    citation census    S141_runner.scorers.census                               new, gated at P6
    similarity         S141_runner.scorers.semantic_similarity                  complete answer (D4)

**One deposited defect is not reproduced.** `score_faithfulness` returns precision 0.0 when the
decomposer yields no sentences (`analysis_minicheck.py:120-129`), which is indistinguishable from an
answer whose every claim was refuted. Row 21 and `minicheck_record()` require the opposite: zero
claims is **unscorable**, never 0.0. Those rows are recorded with `zero_claims_unscorable` set and
no score, which is the same Rule 3 the judge layer applies.

Stages, cheapest first, each independently resumable:

    deterministic   concept recall, number overlap, citation census   seconds for the whole campaign
    minicheck       answerable rows with an answer and a key          ~5 h at the measured 5 claims/s
    similarity      every row with an answer                          encoder-bound

    uv run python scripts/S141_scorers_4_2b.py --stage deterministic
    uv run python scripts/S141_scorers_4_2b.py --stage minicheck
    uv run python scripts/S141_scorers_4_2b.py --stage similarity --device mps

**Item 15 (9 October): the same signals against the current key.** Every printed number that
depends on the answer key is recomputed against the judge's key (S373_rejudge_v2.AS_V1), which S381
writes in the v1 file format: ground truth v2.4 since 11 October 09:00 (Q50;
`data/ground_truth_v2/ground_truth_v2_4_as_v1.json`, `S381 --key 2.4`), v2.3 from 00:00 (Q45,
`ground_truth_v2_3_as_v1.json`), v2.2 before (`ground_truth_v2_2_as_v1.json`). The key is whatever file `--ground-truth` names; this script has no
default for it. v2.3 differs from v2.2 on five questions, each with 97 rows in this campaign:
`expected_answer` on 19_hpai_canada_CO2, CD_001, CD_003 and CD_012, `expected_concepts` on
01_sarek_CO2. Concept recall reads its
`expected_concepts`, number overlap, MiniCheck and similarity read its `expected_answer`. The
citation census reads `source_files`, which that key keeps from v1, as it keeps the `answerable`
flag (Q13), so neither the census fields nor which rows are scored can move. The six questions D7
drops are absent from that key and listed in its
`dropped_d7`: their rows are skipped and counted, never scored against nothing. Three of the six
occur in this campaign (CD_015, OOD_011, SY_010), 291 of its 13,386 rows. v2.4 differs from v2.3 on
25 questions (S398), 14 of them in this campaign (1,358 of its 13,095 scored rows): concept recall can
move on 11 of them, and `expected_answer` changes on 6 (17_brucellosis_ethiopia_FR1, CD_007, SY_007,
SY_009, OOD_002, OOD_005).

`--ground-truth` switches that mode on, and with it three guards:

  - `--outdir` is required. The v1 signals in findings/recompute/S141_scorers are never written to.
  - A reproduction gate runs first and exits 2 on any mismatch, before one row is written: the v1
    key (data/replication_inputs/ground_truth.json, sha256 37d731f9) against the v1 artefact. The
    deterministic stage reproduces every row exactly; each model stage reproduces 20
    fixed rows (evenly spaced over the artefact's sorted keys) to 1e-4, one unit in the fourth
    decimal MiniCheck's artefact keeps. Volatile fields (`at`, cost and wall time) are not compared.
  - Resume is bound to answer length, not to the key, so an output directory whose header records
    another key, or none (every pre-v2.2 header), is refused: its rows would be skipped as done.
    So findings/recompute/S141_scorers_v22, scored against v2.2 (header sha256 42405aff), refuses a
    v2.4 run until it is moved aside; the commands below then write v2.4 under the same name.

    uv run python scripts/S141_scorers_4_2b.py --stage deterministic \\
        --ground-truth data/ground_truth_v2/ground_truth_v2_4_as_v1.json \\
        --outdir findings/recompute/S141_scorers_v22
    uv run python scripts/S141_scorers_4_2b.py --stage similarity --device cpu \\
        --ground-truth data/ground_truth_v2/ground_truth_v2_4_as_v1.json \\
        --outdir findings/recompute/S141_scorers_v22
    uv run python scripts/S141_scorers_4_2b.py --stage minicheck --minicheck-device cpu \\
        --ground-truth data/ground_truth_v2/ground_truth_v2_4_as_v1.json \\
        --outdir findings/recompute/S141_scorers_v22
    # the gate alone, writing nothing (a smoke test for a model stage on a machine)
    uv run python scripts/S141_scorers_4_2b.py --stage minicheck --minicheck-device cpu --reproduce-only

**The minicheck stage in shards (9 October).** MiniCheck checks one claim at a time, so one CPU
process keeps two or three cores busy (S384 measured the same), and v2.2 puts 8,269 rows and
227,821 claims (by the deposited decomposition) in scope. `--shard K/N` scores only the rows whose
key (`arm|config|question_id`) hashes to K: sha256, its first 16 hex digits as an integer, mod N. The split depends on nothing but the key, so it is the same in every
process, on every machine and on every resume. Each shard writes only its own three files under
`<outdir>/minicheck_shards/`: `minicheck.shardKofN.jsonl` (the rows, one record each, exactly as
the unsharded stage writes them), `.json` (one entry per session: platform, threads, the session's own
reproduction gate, counts, wall time) and `.lock`. header.json is read, never written, by a shard.
A shard resumes from its own .jsonl by answer length, as the unsharded stage does; the lock (an
flock, which the kernel drops when the process dies) refuses a second process on the same shard.

Every shard runs the reproduction gate itself, under its own thread count, before its first row:
the gate proves the checker this process loaded, and a separate gate-only call would prove another
process. Run concurrently, the gates cost the wall time of one: 134 s for the 20 rows on this laptop's
CPU on 9 October.

`--merge-shards` loads no model. It refuses unless every shard 0..N-1 exists, has exited (its lock
is free) and was scored against this key; it then reads the current campaign and requires every
row in scope exactly once across the shards, in its own shard, against an answer of the current
length (a record left by an earlier, different answer is dropped and counted). Only then does it
write `<arm>.minicheck.jsonl` per arm, the same lines in the order the unsharded stage writes them,
read them back, add one minicheck entry to header.json (with every shard's sessions and gate), and
remove `minicheck_shards/`. An outdir that already holds an `<arm>.minicheck.jsonl` is refused by
both, as a shard directory is refused by the unsharded stage, so the two modes never mix.

    for k in 0 1 2 3 4 5; do
      TQDM_DISABLE=1 uv run python scripts/S141_scorers_4_2b.py --stage minicheck \\
          --minicheck-device cpu --shard $k/6 --threads 4 \\
          --ground-truth data/ground_truth_v2/ground_truth_v2_4_as_v1.json \\
          --outdir findings/recompute/S141_scorers_v22 > /tmp/S141_mc_shard$k.log 2>&1 &
    done; wait
    uv run python scripts/S141_scorers_4_2b.py --stage minicheck --merge-shards \\
        --ground-truth data/ground_truth_v2/ground_truth_v2_4_as_v1.json \\
        --outdir findings/recompute/S141_scorers_v22

Machine paths, so the same command runs on the Mac Studio, the laptop and the Beelink:

    S141_PAPER                    the deposited scorer source; default the Mac Studio checkout when
                                  it exists, else machine.UPSTREAM (MENTORI_PAPER, data/upstream or
                                  a sibling checkout)
    S141_HF_CACHE, --hf-cache     the MiniCheck-Flan-T5-Large checkpoint cache; default the Mac
                                  Studio path when it exists, else a sibling checkout's data/hf_cache
    S141_BGE_CACHE, --bge-cache   bge-m3; default the HF hub cache (HF_HOME), as the v1 run used
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from functools import cache
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

REANALYSIS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REANALYSIS / "scripts"))

from machine import SIBLINGS, UPSTREAM, rel  # noqa: E402
from S141_runner.scorers import census, minicheck_record, semantic_similarity, strip_citations  # noqa: E402

# S357 runs this on another machine; the three locations can be named there, defaults unchanged.
# Item 15 runs it off the Mac Studio as well, so a default that does not exist here falls back to
# what machine.py resolves; on the Studio the old defaults still win.
_STUDIO_PAPER = Path("/Users/bioinfo-001/projects/Mentori")
_STUDIO_HF_CACHE = Path("/Users/bioinfo-001/projects/Mentori-Old/data/hf_cache")
PAPER = Path(os.environ.get("S141_PAPER") or (_STUDIO_PAPER if _STUDIO_PAPER.exists() else UPSTREAM))
DEPOSITED_DET = PAPER / "publication" / "scripts" / "analysis_deterministic_scorer.py"
DEPOSITED_MC = PAPER / "publication" / "scripts" / "analysis_minicheck.py"
GROUND_TRUTH = Path(os.environ.get("S141_GROUND_TRUTH", PAPER / "datasets" / "ground_truth_v4.json"))
# Both roots are overridable together. The mini arm needs all five signals on its own rows: Delta
# is a difference in differences, and measuring one leg differently from the other is the defect
# rather than the inconvenience. concept_recall settles it alone - the recall argument is made at
# s20 and the arm exists because the inversion is at s50, so without it the one question this arm
# can answer cannot be asked afterwards.
CAMPAIGN = REANALYSIS / "findings" / "recompute" / "S141_campaign"
OUTDIR = REANALYSIS / "findings" / "recompute" / "S141_scorers"
# Item 15: the v1 key and the v1 artefact the reproduction gate holds a keyed (v2.2, v2.3) run to.
V1_KEY = REANALYSIS / "data" / "replication_inputs" / "ground_truth.json"
V1_SIGNALS = OUTDIR


def _hf_cache_default() -> str:
    if _STUDIO_HF_CACHE.exists():
        return str(_STUDIO_HF_CACHE)
    for name in SIBLINGS + ("Mentori-backup",):
        cand = REANALYSIS.parent / name / "data" / "hf_cache"
        if (cand / "models--lytang--MiniCheck-Flan-T5-Large").is_dir():
            return str(cand)
    return str(_STUDIO_HF_CACHE)                    # where it was, so the failure names one place


# The checkpoint the deposited run used, cached locally. HF_HUB_OFFLINE keeps this honest: if the
# cache were missing, the run fails rather than silently fetching a different revision.
HF_CACHE = os.environ.get("S141_HF_CACHE") or _hf_cache_default()
BGE_CACHE = os.environ.get("S141_BGE_CACHE") or None

# Item 15 gate: fields that record when or how fast a row was scored, never what it scored.
VOLATILE = {"deterministic": [("at",)],
            "minicheck": [("at",), ("minicheck", "cost")],
            "similarity": [("at",), ("cost",)]}
MODEL_TOL = 1e-4                                   # one unit in MiniCheck's fourth decimal


def utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_of(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Key:
    """An answer key in the v1 file format: questions by id, the ids it drops, its sha256.

    A v1 key carries no `dropped_d7`; the v2.2 and v2.3 keys (S381) list the six D7 questions there and
    leaves them out of `questions`, so a row on one of them is skipped by name, not by a failed
    lookup that would look the same as a missing key. `version` is the file's "version" for an S381
    conversion and None for any other key; the header records ground_truth_version only when it is
    set, and its "why" names the version, or else the key's path.
    """

    def __init__(self, path: Path):
        self.path = Path(path).resolve()
        raw = self.path.read_bytes()
        self.sha256 = hashlib.sha256(raw).hexdigest()
        data = json.loads(raw)
        self.questions = {q["id"]: q for q in data["questions"]}
        self.dropped_listed = "dropped_d7" in data
        # the key's version, kept only for an S381 conversion (it lists dropped_d7), whose "version" names the
        # ground truth ("v2.3 in the v1 format (S381)"); the v1 key's "version" ("v4" in
        # data/replication_inputs/ground_truth.json) is not a ground-truth version, so for it this is None
        self.version = data.get("version") if self.dropped_listed else None
        self.dropped = frozenset(data.get("dropped_d7") or ())
        both = self.dropped & set(self.questions)
        if both:
            sys.exit(f"FATAL: {rel(self.path)} lists {sorted(both)} as dropped and also scores them")


def lift(path: Path, names: list[str]) -> tuple[dict, str]:
    """Take named functions out of a deposited script without importing it.

    Importing would run its module-level `sys.path` surgery and pull in the whole archive; the
    functions wanted here are self-contained. Their source is hashed so the header records exactly
    which text was executed.
    """
    import numpy as np                                        # score_faithfulness averages with it

    src = path.read_text()
    sha = hashlib.sha256(src.encode()).hexdigest()
    ns: dict = {"re": re, "np": np, "List": list, "Set": set, "Dict": dict, "Any": object,
                "Tuple": tuple, "Optional": object}
    for name in names:
        m = re.search(rf"\ndef {name}\(.*?(?=\ndef |\nclass |\n# ═|\Z)", src, re.S)
        if not m:
            sys.exit(f"FATAL: {name} not found in {path.name}")
        exec(m.group(0), ns)                                   # noqa: S102 - deposited source
    return ns, sha


def arms() -> list[Path]:
    return sorted(p for p in CAMPAIGN.iterdir() if p.is_dir())


def rows_of(arm: Path) -> list[dict]:
    for name in ("results.json", "intermediate.json"):
        f = arm / name
        if not f.exists():
            continue
        try:
            data = json.loads(f.read_text())
        except json.JSONDecodeError:
            continue
        rows = data.get("per_question_results") or data.get("results") or []
        if rows:
            return rows
    return []


def done_keys(path: Path) -> dict[str, int | None]:
    """key -> the answer length that key was scored against, so resume can be content-bound.

    A key of `config|question_id` alone is not enough. When an arm is purged and refilled - which
    is exactly what the provider-failure repair does - the keys are unchanged while the answers
    behind them are new, so a length-blind resume skips every row and silently keeps scores
    computed against answers that no longer exist. Caught by the 2026-08-20 audit on the glm
    think-off arm: 828 records against 819 rows, 9 of them orphans and 2 with a stale length.

    `answer_chars` is already on every record, so the binding costs nothing retrospectively.
    """
    if not path.exists():
        return {}
    keys: dict[str, int | None] = {}
    for line in path.read_text().splitlines():
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        keys[f"{rec['config']}|{rec['question_id']}"] = rec.get("answer_chars")
    return keys


def already_scored(done: dict[str, int | None], cfg: str, qid: str, answer: str) -> bool:
    """Skip only if this key was scored against an answer of the same length."""
    k = f"{cfg}|{qid}"
    if k not in done:
        return False
    was = done[k]
    return was is None or was == len(answer)


def answer_of(row: dict) -> str:
    return ((row.get("generation") or {}).get("answer") or "")


def answerable_of(q: dict) -> bool:
    v = q.get("answerable", True)
    return v is True or str(v).strip().lower() == "true"


def keyed_scope(row: dict, q: dict | None) -> bool:
    """MiniCheck and similarity: answerable questions only, with an answer and a key text.

    There is no expected answer to entail against for the out-of-domain questions, and scoring
    them would invent one.
    """
    return (q is not None and answerable_of(q) and bool(answer_of(row).strip())
            and bool(q.get("expected_answer", "")))


def emit(out: Path, rec: dict) -> None:
    with out.open("a") as f:
        f.write(json.dumps(rec, default=str) + "\n")


# ── instruments, loaded once and shared by the gate and the stage ────────────

@cache
def load_minicheck(device: str | None):
    """MiniCheck-FT5 from the cached checkpoint.

    `device` None is the deposited call, which places the model with device_map="auto" (mps on a
    Mac, cuda where there is one). A named device pins it there instead, so a CPU-only run never
    touches a GPU another job holds; the checkpoint and the scoring code are the same.
    """
    from minicheck.minicheck import MiniCheck
    if device is None:
        return MiniCheck(model_name="flan-t5-large", cache_dir=HF_CACHE)
    import minicheck.inference as mci
    auto = mci.AutoModelForSeq2SeqLM

    class Pinned:
        @staticmethod
        def from_pretrained(*a, **kw):
            return auto.from_pretrained(*a, **{**kw, "device_map": {"": device}})

    mci.AutoModelForSeq2SeqLM = Pinned
    try:
        scorer = MiniCheck(model_name="flan-t5-large", cache_dir=HF_CACHE)
    finally:
        mci.AutoModelForSeq2SeqLM = auto
    placed = str(scorer.model.model.device)
    if not placed.startswith(device):
        sys.exit(f"FATAL: MiniCheck asked for {device}, placed on {placed}")
    return scorer


@cache
def load_encoder(device: str):
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("BAAI/bge-m3", device=device, cache_folder=BGE_CACHE)


def revision_of(get) -> str | None:
    """The hub commit a cached checkpoint resolved to, for the header.

    Asked after a stage has scored every row, so it never raises: a missing attribute costs one
    header field, not the record of a finished run.
    """
    try:
        return getattr(get().config, "_commit_hash", None)
    except Exception:  # noqa: BLE001
        return None


# ── one row each; the stages and the gate share these ────────────────────────

def det_record(arm: str, row: dict, q: dict, det: dict) -> dict:
    qid, cfg = row.get("question_id"), row.get("config")
    ans = answer_of(row)
    answerable = answerable_of(q)
    rec = {"arm": arm, "question_id": qid, "config": cfg,
           "answerable": answerable, "answer_chars": len(ans), "at": utc()}

    if not ans.strip():
        # No answer is not a zero score on every signal; it is an unscorable row.
        rec["unscorable"] = "generation produced no answer"
    else:
        rec.update(census(ans, q.get("source_files")).as_row_fields())
        if answerable:
            rec["concept_recall"] = det["compute_concept_recall"](
                ans, q.get("expected_concepts") or [])
            rec["n_expected_concepts"] = len(q.get("expected_concepts") or [])
            # 1.6: number overlap is computed on citation-stripped text, because a
            # citation like [01_sarek.pdf:12] contributes digits that are not claims.
            rec["number_overlap"] = det["compute_number_overlap"](
                q.get("expected_answer", ""), strip_citations(ans))
            rec["number_overlap_reference_text"] = "citation_stripped_generated"
    return rec


def mc_record(arm: str, row: dict, q: dict, mc_ns: dict, scorer, device: str | None) -> dict:
    qid, cfg = row.get("question_id"), row.get("config")
    ans, expected = answer_of(row), q.get("expected_answer", "")
    t = time.time()
    gen_sents = mc_ns["decompose_to_sentences"](ans)
    exp_sents = mc_ns["decompose_to_sentences"](expected)
    rec = {"arm": arm, "question_id": qid, "config": cfg, "at": utc(),
           "answer_chars": len(ans)}

    if not gen_sents or not exp_sents:
        # The deposited script returns 0.0 here. Row 21 says unscorable, so does
        # minicheck_record(). An answer the decomposer cannot split is not a refuted answer.
        rec.update(minicheck_record("expected_answer", 0,
                                    n_dropped_fragments=0,
                                    wall_s=time.time() - t, device=device,
                                    model="MiniCheck-FT5 flan-t5-large"))
        rec["n_gen_sentences"], rec["n_exp_sentences"] = len(gen_sents), len(exp_sents)
    else:
        res = mc_ns["score_faithfulness"](ans, expected, scorer)
        rec.update(minicheck_record("expected_answer", res["n_gen_sentences"],
                                    n_dropped_fragments=0,
                                    wall_s=time.time() - t, device=device,
                                    model="MiniCheck-FT5 flan-t5-large"))
        rec["minicheck"].update({k: res[k] for k in
                                 ("precision", "recall", "f1",
                                  "n_gen_sentences", "n_exp_sentences")})
        rec["precision_details"] = res["precision_details"]
        rec["recall_details"] = res["recall_details"]
    return rec


def mc_claims(rec: dict) -> int:
    m = rec["minicheck"]
    return 0 if m["zero_claims_unscorable"] else m["n_gen_sentences"] + m["n_exp_sentences"]


def sim_record(arm: str, row: dict, q: dict, enc) -> dict:
    qid, cfg = row.get("question_id"), row.get("config")
    ans, expected = answer_of(row), q.get("expected_answer", "")
    # D4: the complete answer, with the encoder's own limit flagged rather than hidden.
    sim, cost, meta = semantic_similarity(expected, ans, enc, None)
    return {"arm": arm, "question_id": qid, "config": cfg, "at": utc(),
            "answer_chars": len(ans),
            "semantic_similarity": sim, "truncate_chars": None,
            "cost": cost.as_dict(), **meta}


# ── stages ───────────────────────────────────────────────────────────────────

def _dropped_field(key: Key, dropped: int) -> dict:
    # Only a key that lists dropped questions reports the count, so a v1 header keeps its shape.
    return {"skipped_dropped_d7": dropped} if key.dropped_listed else {}


def stage_deterministic(key: Key, args) -> dict:
    det, det_sha = lift(DEPOSITED_DET, ["compute_concept_recall", "extract_numbers",
                                        "compute_number_overlap"])
    n = skipped = dropped = 0
    t0 = time.time()
    for arm in arms():
        out = OUTDIR / f"{arm.name}.deterministic.jsonl"
        already = done_keys(out)
        for row in rows_of(arm):
            qid, cfg = row.get("question_id"), row.get("config")
            if qid in key.dropped:
                dropped += 1
                continue
            ans = answer_of(row)
            if already_scored(already, cfg, qid, ans):
                continue
            q = key.questions.get(qid)
            if q is None:
                skipped += 1
                continue
            emit(out, det_record(arm.name, row, q, det))
            n += 1
    return {"stage": "deterministic", "rows": n, "skipped_no_ground_truth": skipped,
            **_dropped_field(key, dropped),
            "wall_s": round(time.time() - t0, 1), "deposited_sha256": det_sha}


def mc_scope(key: Key, limit: int | None = None) -> tuple[list[tuple[str, dict, dict]], int]:
    """(arm, row, question) for every row the minicheck stage scores, in the order it writes them
    (arms sorted, rows as stored), and the number of rows skipped because D7 dropped the question.

    The unsharded stage, every shard and the merge all select through this, so they cannot
    disagree about which rows exist. `limit` is --limit-rows, for tests only: that many rows evenly
    spaced over the scope, so a small test still crosses several arms.
    """
    scope, dropped = [], 0
    for arm in arms():
        for row in rows_of(arm):
            qid = row.get("question_id")
            if qid in key.dropped:
                dropped += 1
                continue
            q = key.questions.get(qid)
            if keyed_scope(row, q):
                scope.append((arm.name, row, q))
    if limit:
        m = min(limit, len(scope))
        scope = [scope[i] for i in sorted({round(i * (len(scope) - 1) / max(m - 1, 1))
                                           for i in range(m)})]
    return scope, dropped


def stage_minicheck(key: Key, args) -> dict:
    mc_ns, mc_sha = lift(DEPOSITED_MC, ["decompose_to_sentences", "score_faithfulness"])

    t0 = time.time()
    scorer = load_minicheck(args.minicheck_device)
    load_s = time.time() - t0
    print(f"  MiniCheck loaded in {load_s:.1f}s from {HF_CACHE}")

    scope, dropped = mc_scope(key, args.limit_rows)
    n = claims = unscorable = 0
    already: dict[str, dict] = {}
    t0 = time.time()
    for arm, row, q in scope:
        out = OUTDIR / f"{arm}.minicheck.jsonl"
        if arm not in already:
            already[arm] = done_keys(out)
        if already_scored(already[arm], row.get("config"), row.get("question_id"), answer_of(row)):
            continue
        rec = mc_record(arm, row, q, mc_ns, scorer, args.minicheck_device)
        unscorable += rec["minicheck"]["zero_claims_unscorable"]
        claims += mc_claims(rec)
        emit(out, rec)
        n += 1
        if n % 100 == 0:
            el = time.time() - t0
            print(f"  {n} rows, {claims} claims, {claims/el:.1f} claims/s, "
                  f"{el/3600:.2f} h", flush=True)
    return {"stage": "minicheck", "rows": n, "claims": claims, "unscorable_zero_claims": unscorable,
            **_dropped_field(key, dropped),
            "wall_s": round(time.time() - t0, 1), "deposited_sha256": mc_sha,
            "reference_text_kind": "expected_answer", "checkpoint_cache": HF_CACHE,
            **({"limit_rows": args.limit_rows} if args.limit_rows else {})}


# ── the minicheck stage in shards, and the merge (see the module docstring) ──

SHARD_DIR = "minicheck_shards"
ASSIGNMENT = "sha256('arm|config|question_id'), first 16 hex digits as an integer, mod N"


def row_key(arm: str, row: dict) -> str:
    return f"{arm}|{row.get('config')}|{row.get('question_id')}"


def shard_of(rk: str, n: int) -> int:
    """The shard a row belongs to. Not Python's hash(), which is salted per process."""
    return int(hashlib.sha256(rk.encode()).hexdigest()[:16], 16) % n


def shard_paths(k: int, n: int) -> dict[str, Path]:
    d = OUTDIR / SHARD_DIR
    stem = f"minicheck.shard{k}of{n}"
    return {"dir": d, "rows": d / f"{stem}.jsonl", "meta": d / f"{stem}.json", "lock": d / f"{stem}.lock"}


def shard_files(d: Path) -> dict[tuple[int, int], list[Path]]:
    """(k, n) -> the shard files present for it."""
    out: dict[tuple[int, int], list[Path]] = {}
    for f in sorted(d.iterdir()) if d.is_dir() else []:
        m = re.fullmatch(r"minicheck\.shard(\d+)of(\d+)\.(jsonl|json|lock)", f.name)
        if m:
            out.setdefault((int(m[1]), int(m[2])), []).append(f)
    return out


def take_lock(path: Path):
    """An exclusive flock, held while the returned handle is open; None if another process holds
    it. The kernel drops it when the process dies, so a killed shard leaves no stale lock."""
    import fcntl
    fh = path.open("a")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        fh.close()
        return None
    return fh


def write_json(path: Path, obj: dict) -> None:
    tmp = path.with_name(f"{path.name}.tmp{os.getpid()}")
    tmp.write_text(json.dumps(obj, indent=2, default=str) + "\n")
    os.replace(tmp, path)


def read_jsonl_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [x for x in path.read_text().split("\n") if x.strip()]


def unsharded_minicheck_files() -> list[Path]:
    return sorted(OUTDIR.glob("*.minicheck.jsonl"))


def shard_preflight(key: Key, args):
    """Before the gate: this outdir can take this shard, and no other process is running it."""
    k, n = args.shard_k, args.shard_n
    p = shard_paths(k, n)
    if unsharded_minicheck_files():
        sys.exit(f"REFUSED: {rel(OUTDIR)} already holds unsharded minicheck rows "
                 f"({unsharded_minicheck_files()[0].name}, ...); a shard would score them again")
    other = sorted({nn for (_, nn) in shard_files(p["dir"]) if nn != n})
    if other:
        sys.exit(f"REFUSED: {rel(p['dir'])} holds shards of N={other}; a {n}-way split would overlap them")
    p["dir"].mkdir(parents=True, exist_ok=True)
    lock = take_lock(p["lock"])
    if lock is None:
        sys.exit(f"REFUSED: shard {k}/{n} is already running (its lock {rel(p['lock'])} is held)")
    if p["meta"].exists():
        meta = json.loads(p["meta"].read_text())
        for field, now in (("ground_truth_sha256", key.sha256), ("campaign", rel(CAMPAIGN)),
                           ("limit_rows", args.limit_rows)):
            if meta.get(field) != now:
                sys.exit(f"REFUSED: {rel(p['meta'])} records {field} {meta.get(field)!r}, "
                         f"this run has {now!r}")
    return lock


def done_rowkeys(path: Path) -> tuple[dict[str, int | None], int]:
    """row key -> answer length scored against, from one shard file; and its unreadable lines."""
    done: dict[str, int | None] = {}
    bad = 0
    for line in read_jsonl_lines(path):
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            bad += 1
            continue
        done[f"{rec['arm']}|{rec['config']}|{rec['question_id']}"] = rec.get("answer_chars")
    return done, bad


def row_done(done: dict[str, int | None], rk: str, answer: str) -> bool:
    """already_scored(), keyed by the full row key: skip only a row scored against an answer of
    the same length."""
    return rk in done and (done[rk] is None or done[rk] == len(answer))


def stage_minicheck_shard(key: Key, args, gates: list[dict], lock) -> dict:
    import platform
    import torch
    k, n = args.shard_k, args.shard_n
    p = shard_paths(k, n)
    mc_ns, mc_sha = lift(DEPOSITED_MC, ["decompose_to_sentences", "score_faithfulness"])
    scorer = load_minicheck(args.minicheck_device)        # the gate loaded it; cached
    scope, dropped = mc_scope(key, args.limit_rows)
    mine = [t for t in scope if shard_of(row_key(t[0], t[1]), n) == k]
    done, bad = done_rowkeys(p["rows"])
    todo = [t for t in mine if not row_done(done, row_key(t[0], t[1]), answer_of(t[1]))]

    meta = (json.loads(p["meta"].read_text()) if p["meta"].exists() else
            {"step": "4.2b minicheck shard", "shard": f"{k}/{n}", "assignment": ASSIGNMENT,
             "ground_truth": rel(key.path), "ground_truth_sha256": key.sha256,
             "campaign": rel(CAMPAIGN), "limit_rows": args.limit_rows, "sessions": []})
    meta["rows_in_shard"] = len(mine)
    # The platform, not the hostname: this header ships with the deposit.
    session = {"started": utc(),
               "platform": f"{platform.system()} {platform.machine()}, python {sys.version.split()[0]}, "
                           f"torch {torch.__version__}",
               "device": args.minicheck_device, "torch_threads": torch.get_num_threads(),
               "script_sha256": sha256_of(Path(__file__)),
               "scorers_module_sha256": sha256_of(REANALYSIS / "scripts" / "S141_runner" / "scorers.py"),
               "deposited_sha256": mc_sha, "checkpoint_cache": HF_CACHE,
               "reproduction_gate": gates[0], "rows_in_shard": len(mine),
               "rows_already_in": len(mine) - len(todo), "unreadable_lines_before": bad,
               "finished": None}
    meta["sessions"].append(session)
    write_json(p["meta"], meta)                     # a killed session still shows it started
    print(f"  shard {k}/{n}: {len(mine)} of {len(scope)} rows are this shard's, "
          f"{len(mine) - len(todo)} already in, {len(todo)} to score -> {rel(p['rows'])}", flush=True)

    # A process killed mid-write leaves a last line with no newline; the next record would be
    # glued to it and both lost. End it first, so the torn line stays one unreadable line.
    if p["rows"].exists() and p["rows"].stat().st_size:
        with p["rows"].open("rb") as f:
            f.seek(-1, os.SEEK_END)
            torn = f.read(1) != b"\n"
        if torn:
            with p["rows"].open("a") as f:
                f.write("\n")

    rows = claims = unscorable = 0
    t0 = time.time()
    for arm, row, q in todo:
        rec = mc_record(arm, row, q, mc_ns, scorer, args.minicheck_device)
        unscorable += rec["minicheck"]["zero_claims_unscorable"]
        claims += mc_claims(rec)
        emit(p["rows"], rec)
        rows += 1
        if rows % 50 == 0:
            el = time.time() - t0
            print(f"  shard {k}/{n}: {rows}/{len(todo)} rows, {claims} claims, "
                  f"{claims/el:.2f} claims/s, {el/3600:.2f} h, "
                  f"ETA {(len(todo) - rows) * el / rows / 3600:.1f} h", flush=True)
    session.update({"rows": rows, "claims": claims, "unscorable_zero_claims": unscorable,
                    "wall_s": round(time.time() - t0, 1), "finished": utc(),
                    "checkpoint_revision": revision_of(
                        lambda: load_minicheck(args.minicheck_device).model.model),
                    "complete": rows == len(todo)})
    write_json(p["meta"], meta)
    lock.close()
    return {"stage": "minicheck", "shard": f"{k}/{n}", "rows_in_shard": len(mine),
            "rows": rows, "claims": claims, "unscorable_zero_claims": unscorable,
            **_dropped_field(key, dropped), "wall_s": session["wall_s"]}


def merge_shards(key: Key, args):
    """Check the shards against the current campaign and write the per-arm files.

    Returns the header.json stage entry, the shards' gates, and a cleanup that removes the shard
    directory (called once header.json is written). Exits 2, having written nothing, on any problem.
    """
    d = OUTDIR / SHARD_DIR
    present = shard_files(d)
    ns = sorted({n for (_, n) in present})
    if not ns:
        sys.exit(f"--merge-shards: no shard files in {rel(d)}")
    if len(ns) > 1:
        sys.exit(f"--merge-shards: {rel(d)} mixes shard counts {ns}")
    n = ns[0]
    if unsharded_minicheck_files():
        sys.exit(f"REFUSED: {rel(OUTDIR)} already holds {unsharded_minicheck_files()[0].name}; "
                 "a merge would overwrite it (an earlier merge that stopped part-way? compare, "
                 "then move the per-arm minicheck files aside)")
    problems: list[str] = []
    paths = {k: shard_paths(k, n) for k in range(n)}
    metas: dict[int, dict] = {}
    for k in range(n):
        if not paths[k]["meta"].exists():
            problems.append(f"shard {k}/{n}: no {paths[k]['meta'].name}; was it ever started?")
        else:
            metas[k] = json.loads(paths[k]["meta"].read_text())
    locks = []
    for k in range(n):
        if not paths[k]["lock"].exists():
            continue                                # never started: the meta check reports it
        lk = take_lock(paths[k]["lock"])
        if lk is None:
            problems.append(f"shard {k}/{n} is still running (its lock is held)")
        else:
            locks.append(lk)                        # held to the end, so no shard starts mid-merge
    for k, m in metas.items():
        if m.get("ground_truth_sha256") != key.sha256:
            problems.append(f"shard {k}/{n} was scored against key {str(m.get('ground_truth_sha256'))[:12]}")
        if m.get("campaign") != rel(CAMPAIGN):
            problems.append(f"shard {k}/{n} read campaign {m.get('campaign')}, not {rel(CAMPAIGN)}")
        if not m.get("sessions") or not m["sessions"][-1].get("finished"):
            problems.append(f"shard {k}/{n}: its last session never finished (killed?); run it again")
        for s in m.get("sessions", []):
            if not (s.get("reproduction_gate") or {}).get("passed"):
                problems.append(f"shard {k}/{n}: a session at {s.get('started')} has no passed gate")
    limits = {m.get("limit_rows") for m in metas.values()}
    if len(limits) > 1:
        problems.append(f"the shards were run with different --limit-rows {sorted(map(str, limits))}")
    limit = next(iter(limits)) if len(limits) == 1 else None
    if args.limit_rows is not None and args.limit_rows != limit:
        problems.append(f"--limit-rows {args.limit_rows} here, {limit} in the shards")
    sessions = [s for m in metas.values() for s in m.get("sessions", [])]
    for field in ("deposited_sha256", "scorers_module_sha256"):
        seen = {s.get(field) for s in sessions}
        if len(seen) > 1:
            problems.append(f"the shard sessions ran different {field}: {sorted(map(str, seen))}")
    if problems:
        print("  STOP: nothing merged")
        for x in problems:
            print(f"    {x}")
        sys.exit(2)

    scope, dropped = mc_scope(key, limit)
    expected = {row_key(arm, row): row for arm, row, _ in scope}
    chosen: dict[str, tuple[str, dict]] = {}
    stale = unreadable = 0
    per_shard = []
    for k in range(n):
        lines = read_jsonl_lines(paths[k]["rows"])
        mine = [rk for rk in expected if shard_of(rk, n) == k]
        for line in lines:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                unreadable += 1
                continue
            rk = f"{rec['arm']}|{rec['config']}|{rec['question_id']}"
            if rk not in expected:
                problems.append(f"shard {k}/{n}: {rk} is not in the current scope (campaign or key changed?)")
            elif shard_of(rk, n) != k:
                problems.append(f"shard {k}/{n}: {rk} belongs to shard {shard_of(rk, n)}")
            elif rec.get("answer_chars") != len(answer_of(expected[rk])):
                stale += 1                          # scored against an answer since replaced
            elif rk in chosen:
                problems.append(f"shard {k}/{n}: {rk} scored twice against the current answer")
            else:
                chosen[rk] = (line, rec)
        missing = [rk for rk in mine if rk not in chosen]
        if missing:
            problems.append(f"shard {k}/{n} incomplete: {len(mine) - len(missing)} of {len(mine)} "
                            f"rows, first missing {missing[:3]}")
        raw = paths[k]["rows"].read_bytes() if paths[k]["rows"].exists() else b""
        per_shard.append({"shard": f"{k}/{n}", "rows": len(mine), "file_lines": len(lines),
                          "file_sha256": hashlib.sha256(raw).hexdigest(),
                          "sessions": [{x: v for x, v in s.items() if x != "reproduction_gate"}
                                       | {"gate_at": (s.get("reproduction_gate") or {}).get("at")}
                                       for s in metas[k]["sessions"]]})
    if problems or len(chosen) != len(expected):
        print(f"  STOP: nothing merged ({len(chosen)} of {len(expected)} rows accounted for)")
        for x in problems[:30]:
            print(f"    {x}")
        sys.exit(2)

    per_arm: dict[str, list[str]] = {}
    for arm, row, _ in scope:
        per_arm.setdefault(arm, []).append(chosen[row_key(arm, row)][0])
    for arm, lines in per_arm.items():
        target = OUTDIR / f"{arm}.minicheck.jsonl"
        write_text = "".join(x + "\n" for x in lines)
        tmp = target.with_name(f"{target.name}.tmp{os.getpid()}")
        tmp.write_text(write_text)
        os.replace(tmp, target)
    for arm, lines in per_arm.items():               # read back before header.json says so
        if (OUTDIR / f"{arm}.minicheck.jsonl").read_text() != "".join(x + "\n" for x in lines):
            sys.exit(f"FATAL: {arm}.minicheck.jsonl does not read back as written; shards kept")
    recs = [chosen[row_key(arm, row)][1] for arm, row, _ in scope]
    print(f"  merged {len(recs)} rows from {n} shards into {len(per_arm)} per-arm files "
          f"({stale} stale records dropped, {unreadable} unreadable lines)")

    def one(field):
        """The value every session agrees on, else all of them (null stays null)."""
        vals = sorted({json.dumps(s.get(field), default=str) for s in sessions})
        return json.loads(vals[0]) if len(vals) == 1 else [json.loads(v) for v in vals]

    gates = [{**s["reproduction_gate"], "shard": m["shard"], "session_started": s["started"]}
             for m in metas.values() for s in m["sessions"]]
    walls = [sum(s.get("wall_s") or 0 for s in metas[k]["sessions"]) for k in range(n)]
    summary = {"stage": "minicheck", "rows": len(recs), "claims": sum(mc_claims(r) for r in recs),
               "unscorable_zero_claims": sum(r["minicheck"]["zero_claims_unscorable"] for r in recs),
               **_dropped_field(key, dropped),
               "wall_s": round(max(walls), 1), "deposited_sha256": one("deposited_sha256"),
               "reference_text_kind": "expected_answer", "checkpoint_cache": one("checkpoint_cache"),
               **({"limit_rows": limit} if limit else {}),
               "finished": utc(), "ground_truth_sha256": key.sha256,
               "checkpoint_revision": one("checkpoint_revision"), "device": one("device"),
               "sharded": {"shards": n, "assignment": ASSIGNMENT,
                           "wall_s_note": "wall_s is the slowest shard's scoring time summed over "
                                          "its sessions; the shards ran concurrently",
                           "stale_records_dropped": stale, "unreadable_lines": unreadable,
                           "per_shard": per_shard}}

    def cleanup() -> None:
        for k in range(n):
            for f in shard_files(d).get((k, n), []):
                f.unlink()
        for lk in locks:
            lk.close()
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()
        print(f"  removed {rel(d)}")

    return summary, gates, cleanup


def stage_similarity(key: Key, args) -> dict:
    enc = load_encoder(args.device)
    n = truncated = dropped = 0
    t0 = time.time()
    for arm in arms():
        out = OUTDIR / f"{arm.name}.similarity.jsonl"
        already = done_keys(out)
        for row in rows_of(arm):
            qid, cfg = row.get("question_id"), row.get("config")
            if qid in key.dropped:
                dropped += 1
                continue
            if already_scored(already, cfg, qid, answer_of(row)):
                continue
            q = key.questions.get(qid)
            if not keyed_scope(row, q):
                continue
            rec = sim_record(arm.name, row, q, enc)
            truncated += bool(rec.get("encoder_truncated"))
            emit(out, rec)
            n += 1
            if n % 200 == 0:
                print(f"  {n} rows, {(time.time()-t0)/3600:.2f} h", flush=True)
    return {"stage": "similarity", "rows": n, "encoder_truncated_rows": truncated,
            **_dropped_field(key, dropped),
            "device": args.device, "wall_s": round(time.time() - t0, 1)}


STAGES = {"deterministic": stage_deterministic, "minicheck": stage_minicheck,
          "similarity": stage_similarity}


# ── item 15: reproduce v1 before writing a keyed run ────────────────────────────────

def comparable(rec: dict, stage: str) -> dict:
    rec = json.loads(json.dumps(rec, default=str))
    for path in VOLATILE[stage]:
        d = rec
        for k in path[:-1]:
            d = d.get(k) or {}
        d.pop(path[-1], None)
    return rec


def compare(ref, got, tol: float, tally: dict, at: str = "") -> tuple[list[str], float]:
    """Differences between an artefact record and its recomputation, and the largest float gap.

    `tally` counts the floats compared and those not bit-identical, so a pass within tolerance
    still says how many values moved.
    """
    if isinstance(ref, dict) and isinstance(got, dict):
        out, worst = [], 0.0
        for k in sorted(set(ref) | set(got)):
            if k not in ref or k not in got:
                out.append(f"{at}.{k} only in {'artefact' if k in ref else 'recomputed'}")
                continue
            d, w = compare(ref[k], got[k], tol, tally, f"{at}.{k}")
            out += d
            worst = max(worst, w)
        return out, worst
    if isinstance(ref, list) and isinstance(got, list):
        if len(ref) != len(got):
            return [f"{at} length {len(ref)} vs {len(got)}"], 0.0
        out, worst = [], 0.0
        for i, (a, b) in enumerate(zip(ref, got)):
            d, w = compare(a, b, tol, tally, f"{at}[{i}]")
            out += d
            worst = max(worst, w)
        return out, worst
    num = (int, float)
    if (isinstance(ref, float) or isinstance(got, float)) and isinstance(ref, num) \
            and isinstance(got, num) and not isinstance(ref, bool) and not isinstance(got, bool):
        gap = abs(ref - got)
        tally["floats"] = tally.get("floats", 0) + 1
        tally["floats_not_identical"] = tally.get("floats_not_identical", 0) + (ref != got)
        ok = ref == got if tol == 0 else gap <= tol + 1e-12   # 1e-12: 0.7149 - 0.7148 > 1e-4
        return ([] if ok else [f"{at} {ref!r} vs {got!r}"]), gap
    return ([] if ref == got else [f"{at} {ref!r} vs {got!r}"]), 0.0


def reference_shas(ref_dir: Path, stage: str) -> set[str]:
    hdr = ref_dir / "header.json"
    if not hdr.exists():
        return set()
    return {s["deposited_sha256"] for s in json.loads(hdr.read_text()).get("stages", [])
            if s.get("stage") == stage and s.get("deposited_sha256")}


def reproduce(stage: str, ref_dir: Path, ref_key: Key, args) -> dict:
    """Recompute the v1 artefact from the v1 key with this code, on this machine, and compare.

    deterministic: every row, exactly. minicheck and similarity: `--reproduce-n` rows evenly spaced
    over the artefact's sorted (arm, config, question) keys, to MODEL_TOL. A row whose answer
    length no longer matches the artefact's is a mismatch: the artefact would then describe
    answers that are not in the campaign.
    """
    t0 = time.time()
    campaign = {(arm.name, row.get("config"), row.get("question_id")): row
                for arm in arms() for row in rows_of(arm)}
    ref: dict[tuple, dict] = {}
    missing_files = []
    for arm in arms():
        f = ref_dir / f"{arm.name}.{stage}.jsonl"
        if not f.exists():
            missing_files.append(f.name)
            continue
        for line in f.read_text().splitlines():
            r = json.loads(line)
            ref[(r["arm"], r["config"], r["question_id"])] = r

    sha, dev = None, None
    if stage == "deterministic":
        det, sha = lift(DEPOSITED_DET, ["compute_concept_recall", "extract_numbers",
                                        "compute_number_overlap"])
        tol = 0.0
        keys = sorted(k for k in campaign if k[2] in ref_key.questions)
        selection = "every campaign row the v1 key scores"
        build = lambda k: det_record(k[0], campaign[k], ref_key.questions[k[2]], det)
    else:
        tol = MODEL_TOL
        ordered = sorted(ref)
        n = min(args.reproduce_n, len(ordered))
        idx = sorted({round(i * (len(ordered) - 1) / max(n - 1, 1)) for i in range(n)})
        keys = [ordered[i] for i in idx]
        selection = f"{len(keys)} rows evenly spaced over the artefact's {len(ordered)} sorted keys"
        if stage == "minicheck":
            mc_ns, sha = lift(DEPOSITED_MC, ["decompose_to_sentences", "score_faithfulness"])
            dev = args.minicheck_device
            scorer = load_minicheck(dev)
            build = lambda k: mc_record(k[0], campaign[k], ref_key.questions[k[2]],
                                        mc_ns, scorer, dev)
        else:
            dev = args.device
            enc = load_encoder(dev)
            build = lambda k: sim_record(k[0], campaign[k], ref_key.questions[k[2]], enc)

    problems: list[str] = [f"artefact file missing: {m}" for m in missing_files]
    if stage == "deterministic":
        extra = sorted(set(ref) - set(keys))
        absent = sorted(set(keys) - set(ref))
        problems += [f"{k}: in the artefact, not recomputed" for k in extra[:10]]
        problems += [f"{k}: recomputed, not in the artefact" for k in absent[:10]]
        if len(extra) + len(absent) > 20:
            problems.append(f"... {len(extra)} artefact-only and {len(absent)} recompute-only keys")
    matched = compared = claims = 0
    worst = 0.0
    tally: dict = {}
    row_s: list[float] = []
    for k in keys:
        if k not in ref:
            continue
        if k not in campaign or k[2] not in ref_key.questions:
            problems.append(f"{k}: in the artefact, not in the campaign or the key")
            continue
        compared += 1
        t = time.time()
        got = build(k)
        row_s.append(time.time() - t)
        if stage == "minicheck":
            claims += mc_claims(got)
        if stage == "similarity" and "answer_chars" not in ref[k]:
            # 7,852 of the 8,463 v1 similarity rows predate `answer_chars` (2064b99, the 20 August
            # resume fix). Their `generated_chars` is the same length, so the binding is held there.
            got = dict(got)
            if got.pop("answer_chars") != ref[k].get("generated_chars"):
                problems.append(f"{k}: answer length {len(answer_of(campaign[k]))} vs the "
                                f"artefact's generated_chars {ref[k].get('generated_chars')}")
                continue
        diffs, w = compare(comparable(ref[k], stage), comparable(got, stage), tol, tally)
        worst = max(worst, w)
        if diffs:
            problems.append(f"{k}: " + "; ".join(diffs[:4]))
        else:
            matched += 1

    known = reference_shas(ref_dir, stage)
    sha_ok = sha is None or not known or sha in known
    if not sha_ok:
        problems.append(f"deposited source {sha[:12]} is not the one the artefact recorded "
                        f"({', '.join(s[:12] for s in sorted(known))})")
    passed = not problems and compared == len(keys) and compared > 0
    res = {"stage": stage, "at": utc(), "passed": passed,
           "reference": rel(ref_dir), "reference_key": rel(ref_key.path),
           "reference_key_sha256": ref_key.sha256, "selection": selection,
           "rows_compared": compared, "rows_matched": matched, "artefact_rows": len(ref),
           "tolerance": tol, "max_abs_float_gap": worst,
           "floats_compared": tally.get("floats", 0),
           "floats_not_identical": tally.get("floats_not_identical", 0),
           "deposited_sha256": sha, "deposited_matches_artefact": sha_ok if sha else None,
           "device": dev, "mean_row_s": round(sum(row_s) / len(row_s), 3) if row_s else None,
           "wall_s": round(time.time() - t0, 1), "mismatches": problems[:25]}
    if stage != "deterministic":
        res["keys"] = ["|".join(k) for k in keys]
    if stage == "minicheck":
        res["claims"] = claims
    return res


def guard_outdir(outdir: Path, key: Key, keyed_mode: bool, ref_dir: Path | None) -> None:
    """Refuse an output directory whose rows were scored against a different key.

    Resume skips a row whose (config, question) was scored against an answer of the same length.
    Pointed at a directory scored against another key, every row is skipped and the old key's
    numbers come back under the new key's name.
    """
    if ref_dir is not None and outdir.resolve() == ref_dir.resolve():
        sys.exit(f"REFUSED: {rel(outdir)} is the artefact the gate reproduces; name another --outdir")
    hdr = outdir / "header.json"
    if hdr.exists():
        recorded = json.loads(hdr.read_text()).get("ground_truth_sha256")
        if recorded is None and keyed_mode:
            sys.exit(f"REFUSED: {rel(outdir)} holds signals from a run that records no key "
                     "(every pre-v2.2 run); its rows would be skipped as already scored")
        if recorded is not None and recorded != key.sha256:
            sys.exit(f"REFUSED: {rel(outdir)} was scored against key {recorded[:12]}, "
                     f"this run uses {key.sha256[:12]} ({rel(key.path)})")
    elif keyed_mode and outdir.exists() and any(outdir.glob("*.jsonl")):
        sys.exit(f"REFUSED: {rel(outdir)} holds signal files and no header to say which key")


def main() -> int:
    global CAMPAIGN, OUTDIR, HF_CACHE, BGE_CACHE
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=[*STAGES, "all"], default="all")
    ap.add_argument("--campaign", default=None,
                    help="arm root; default S141_campaign. Use S141_mini for the 4.3 arm.")
    ap.add_argument("--outdir", default=None,
                    help="signal output root; defaults beside the campaign root")
    ap.add_argument("--device", default="cpu", help="similarity encoder device (cpu|mps)")
    ap.add_argument("--minicheck-device", default=None,
                    help="cpu|mps|cuda; default the deposited device_map='auto'")
    ap.add_argument("--hf-cache", default=None, help="MiniCheck checkpoint cache (S141_HF_CACHE)")
    ap.add_argument("--bge-cache", default=None, help="bge-m3 cache (S141_BGE_CACHE)")
    ap.add_argument("--ground-truth", default=None,
                    help="item 15: an answer key in the v1 format (the current one: "
                         "data/ground_truth_v2/ground_truth_v2_4_as_v1.json, S381 --key 2.4); requires "
                         "--outdir and runs the reproduction gate first")
    ap.add_argument("--reproduce", default=None,
                    help="v1 artefact the gate reproduces; default S141_scorers, or <campaign>/scorers")
    ap.add_argument("--reproduce-key", default=str(V1_KEY), help="the key that artefact was scored against")
    ap.add_argument("--reproduce-n", type=int, default=20, help="rows per model stage in the gate")
    ap.add_argument("--reproduce-only", action="store_true",
                    help="run the gate for the chosen stages, write nothing")
    ap.add_argument("--shard", default=None,
                    help="minicheck only, K/N (0-based): score the rows whose key hashes to K, into "
                         "<outdir>/minicheck_shards; then --merge-shards")
    ap.add_argument("--merge-shards", action="store_true",
                    help="minicheck only: check that every shard is complete, write the per-arm "
                         "files, update header.json once; loads no model")
    ap.add_argument("--threads", type=int, default=0,
                    help="torch threads in this process (0 = torch's default)")
    ap.add_argument("--limit-rows", type=int, default=None, help=argparse.SUPPRESS)  # tests only
    a = ap.parse_args()

    if a.shard is not None or a.merge_shards:
        if a.stage != "minicheck":
            sys.exit("--shard and --merge-shards are for --stage minicheck")
        if a.ground_truth is None or not a.outdir:
            sys.exit("--shard and --merge-shards need --ground-truth and --outdir: the shards and "
                     "the merge are checked against one key")
        if a.shard is not None and a.merge_shards:
            sys.exit("--shard scores, --merge-shards merges: one or the other")
        if a.reproduce_only:
            sys.exit("--reproduce-only writes nothing; drop --shard / --merge-shards")
    if a.shard is not None:
        try:
            a.shard_k, a.shard_n = (int(x) for x in a.shard.split("/"))
            assert 0 <= a.shard_k < a.shard_n
        except (ValueError, AssertionError):
            sys.exit(f"--shard {a.shard}: expected K/N with 0 <= K < N")
    if a.threads:
        import torch
        torch.set_num_threads(a.threads)            # before the gate loads the checker

    if a.hf_cache:
        HF_CACHE = a.hf_cache
    if a.bge_cache:
        BGE_CACHE = a.bge_cache
    keyed_mode = a.ground_truth is not None
    if keyed_mode and not a.outdir and not a.reproduce_only:
        sys.exit("--ground-truth needs --outdir: the v1 signals are never written to")
    if a.campaign:
        CAMPAIGN = Path(a.campaign).resolve()
        # Signals live beside the arm they describe unless told otherwise, so a mini-arm signal can
        # never be mistaken for a campaign one by a later reader.
        OUTDIR = (Path(a.outdir).resolve() if a.outdir else CAMPAIGN / "scorers")
        print(f"  campaign root: {CAMPAIGN}\n  signal output: {OUTDIR}")
    elif a.outdir:
        OUTDIR = Path(a.outdir).resolve()
    chosen = list(STAGES) if a.stage == "all" else [a.stage]

    # The merge scores nothing, so it has no gate of its own: it requires every shard's.
    gating = not a.merge_shards and (keyed_mode or a.reproduce_only or a.reproduce is not None)
    ref_dir = (Path(a.reproduce).resolve() if a.reproduce
               else (CAMPAIGN / "scorers" if a.campaign else V1_SIGNALS)) if gating else None
    key = None
    if not a.reproduce_only:
        key = Key(Path(a.ground_truth) if keyed_mode else GROUND_TRUTH)
        guard_outdir(OUTDIR, key, keyed_mode, ref_dir)
    if keyed_mode and key is not None:
        print(f"  key: {rel(key.path)} sha256 {key.sha256[:12]}, {len(key.questions)} questions, "
              f"dropped {sorted(key.dropped)}")
    lock = None
    if a.shard is not None:
        lock = shard_preflight(key, a)              # before the gate, so a duplicate stops at once
    elif "minicheck" in chosen and not a.reproduce_only and not a.merge_shards \
            and shard_files(OUTDIR / SHARD_DIR):
        sys.exit(f"REFUSED: {rel(OUTDIR / SHARD_DIR)} holds minicheck shards; finish them and "
                 "--merge-shards, or move them aside, before an unsharded minicheck run")

    gates = []
    if gating:
        ref_key = Key(Path(a.reproduce_key))
        print(f"  reproduction gate: {rel(ref_key.path)} ({ref_key.sha256[:12]}) "
              f"against {rel(ref_dir)}")
        for name in chosen:
            g = reproduce(name, ref_dir, ref_key, a)
            gates.append(g)
            print(f"  gate {name}: {'PASS' if g['passed'] else 'FAIL'}, "
                  f"{g['rows_matched']} of {g['rows_compared']} rows match "
                  f"({g['selection']}), max float gap {g['max_abs_float_gap']:.3g}, "
                  f"{g['wall_s']}s", flush=True)
            for m in g["mismatches"][:10]:
                print(f"    {m[:300]}")
        if not all(g["passed"] for g in gates):
            print("  STOP: the code does not reproduce the v1 artefact; nothing written")
            return 2
        if a.reproduce_only:
            print(json.dumps(gates, indent=1))
            return 0

    if a.shard is not None:                         # header.json is the merge's to write
        print(f"\n  === minicheck, shard {a.shard} ===")
        s = stage_minicheck_shard(key, a, gates, lock)
        print(f"  {json.dumps(s)}")
        return 0

    OUTDIR.mkdir(parents=True, exist_ok=True)
    hdr = OUTDIR / "header.json"
    old = json.loads(hdr.read_text()) if hdr.exists() else {}
    prior = old.get("stages", [])
    summaries: list[dict] = []

    def write_header() -> None:
        # After every stage, so a run that dies in a later stage still records the earlier ones.
        if not keyed_mode:
            hdr.write_text(json.dumps({
                "step": "4.2b", "updated": utc(),
                "why": "work-plan 1.6 signals; never wired into Phase 4 (D11)",
                "campaign_files_read_only": True,
                "stages": prior + summaries,
            }, indent=2) + "\n")
            return
        hdr.write_text(json.dumps({
            "step": "4.2b", "updated": utc(),
            "why": f"item 15 (9 October): the 1.6 signals recomputed against ground truth "
                   f"{key.version or rel(key.path)}; rows on the six D7 questions skipped and counted",
            "campaign_files_read_only": True,
            "ground_truth": rel(key.path), "ground_truth_sha256": key.sha256,
            **({"ground_truth_version": key.version} if key.version else {}),
            "dropped_d7": sorted(key.dropped),
            "campaign": rel(CAMPAIGN),
            "script": rel(Path(__file__)), "script_sha256": sha256_of(Path(__file__)),
            "scorers_module_sha256": sha256_of(REANALYSIS / "scripts" / "S141_runner" / "scorers.py"),
            "reproduction_gates": old.get("reproduction_gates", []) + gates,
            "stages": prior + summaries,
        }, indent=2) + "\n")

    if a.merge_shards:
        print("\n  === minicheck, merging shards ===")
        summary, gates, cleanup = merge_shards(key, a)
        summaries.append(summary)
        print(f"  {json.dumps({x: v for x, v in summary.items() if x != 'sharded'})[:300]}")
        write_header()
        print(f"  wrote {rel(hdr)}")
        cleanup()
        return 0

    for name in chosen:
        print(f"\n  === {name} ===")
        summaries.append(STAGES[name](key, a))
        if keyed_mode:
            summaries[-1].update({"finished": utc(), "ground_truth_sha256": key.sha256})
            if name == "minicheck":
                summaries[-1]["checkpoint_revision"] = revision_of(
                    lambda: load_minicheck(a.minicheck_device).model.model)
                summaries[-1]["device"] = a.minicheck_device
            if name == "similarity":
                summaries[-1]["checkpoint_revision"] = revision_of(
                    lambda: load_encoder(a.device)[0].auto_model)
        print(f"  {json.dumps(summaries[-1])[:300]}")
        write_header()
        print(f"  wrote {rel(hdr)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
