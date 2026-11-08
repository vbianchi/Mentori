#!/usr/bin/env python3
"""S384 - exp04 MiniCheck against the answer key (precision, recall, F1) on the current key
(item 15, 9 October; ground truth v2.4 since 11 October 09:00 (Q50), v2.3 from 00:00 (Q45)).

Why. The deposited exp04 MiniCheck run (<upstream>/publication/results/exp04_minicheck_latest.json,
528 answers: 88 answerable questions x 6 configurations) scores each answer against the key's
expected_answer in both directions (analysis_minicheck.py:131-175): precision is the fraction of the
answer's sentences that the key entails, recall the fraction of the key's sentences that the answer
entails, F1 their harmonic mean. The key is now the judge's (S373.KEY: ground truth v2.2, frozen
9 October, corrected to v2.3 on 11 October, Q45, and v2.4 the same morning, Q50), so all three are recomputed against it. S19 --condition key --key v22 covers 147 answers (its 150-answer sample less 3 on
dropped questions) and precision only; this covers every exp04 row the key selects, and all three:
the 516 answerable rows still on the key and, under D5, the 60 rows on the ten refutation questions.

What is lifted, unchanged. decompose_to_sentences, score_faithfulness and run_minicheck_scoring are
exec'd from the deposited analysis_minicheck.py (sha256 pinned below), and load_ground_truth from
recovered_harness/tests/experiments_v4/exp_common.py, which the deposited script imports. The claim
split, the scoring and the row selection are therefore the deposited code, called one row at a time
so the run can resume. The checker is the cached MiniCheck-Flan-T5-Large checkpoint, loaded offline
(HF_HUB_OFFLINE=1) and pinned to --device; MiniCheck's own loader says device_map="auto", which
would take a GPU.

The key. S373_rejudge_v2.AS_V1, the judge's key in the v1 format (since 11 October
data/ground_truth_v2/ground_truth_v2_4_as_v1.json, S381 --key 2.4): the current expected_answer and
answerable flag, used as given. The report and printed labels name the version read from S373.KEY's
"version" field; each session records S373.KEY's path, sha256 and version beside the v1 format file's.
The outputs keep their _v22 names so that downstream readers (S08 --v22) hold. A .jsonl or shard file
with a session under another key sha256 (the v2.2 run's, for one) stops the run until it is moved
aside. Every run, --report included, first exits unless S373.AS_V1's source_v<version>_sha256 field
(S381's name, from S373.KEY's "version") equals the sha256 of S373.KEY, as S388 checks. Six questions are dropped (D7) and absent from it, so the deposited selection skips their rows (gt_lookup.get(qid) is None, analysis_minicheck.py:226-228).
Two of the six are in exp04, CD_015 and SY_010: 12 rows, counted and listed in the report.

The two groups (D5, 11 October). The deposited run_minicheck_scoring takes each generation row's own
answerable flag before the key's (r.get("answerable", gt.get(...)), analysis_minicheck.py:230), and
every exp04 generation row carries one, so the key's flag would never decide which rows are scored.
The current-key selection therefore runs on a copy of the generation rows whose flag is replaced by the
key's for every question the key keeps (rows_on_key); the v1 selection and G2 run on the rows as
deposited. The rows whose flag this changes must be exactly the rows on S373.KEY's answer_type
"refutation" questions (OOD_041 to OOD_050 in v2.4), each changed to answerable, or the run exits
before G1's current-key check, as it does on a v1-format key that still carries v1's flag for them.
Those rows are scored against the key's expected_answer like any other, and are the refutation group;
every other selected row is the answerable group. Each scored row records its group. The report's
existing tables, v1 columns included, are over the answerable group only; the refutation group has
its own section with the current key's values only, since the deposited run never scored those rows
(their row flag was not answerable) and there is no v1 value for them.

Gates, before any current-key number is written. Any mismatch exits 1 and writes nothing.
  G1  pure Python, all 528 rows. The deposited selection, run with the v1 key and a checker that is
      never consulted, returns the deposited 528 (question, config) rows in the deposited order, with
      the deposited index_name, category, difficulty, n_gen_sentences, n_exp_sentences and every
      claim sentence (sentence[:200]) in both directions. Then the flag check above. The current-key
      selection, on the rows with the key's flag, must then equal, in generation order, the rows in
      the v1 selection or on a refutation question, less the dropped questions' rows. It splits every
      selected row into claim sentences on both sides, so a row with none raises there.
  G2  model, 20 rows (a fixed seed-42 sample of the 528), on --device. The deposited scoring with
      the v1 key reproduces the deposited precision, recall, F1, both sentence counts and every
      per-sentence label exactly, and every per-sentence probability and both mean probabilities
      within 1e-4 (the artefact rounds to 4 dp).

Run from the repo root. Everything is CPU; no Ollama, no GPU. Once per machine, first fetch nltk's
punkt_tab data: MiniCheck splits every document it is given (the key for precision, the answer for
recall) with nltk.sent_tokenize before chunking it (minicheck/inference.py:3, :17-20, :139). nltk
3.10.0 reads punkt_tab from its data path (downloads go to ~/nltk_data), and uv does not install it.
Without it the script exits before loading the checker, naming this command.

    uv run python -c "import nltk; nltk.download('punkt_tab')"     # once per machine
    uv run python scripts/S384_exp04_minicheck_key_v22.py            # G1 + G2 only, writes nothing
    uv run python scripts/S384_exp04_minicheck_key_v22.py --full     # G1 + G2, then the 516 + 60 rows
    uv run python scripts/S384_exp04_minicheck_key_v22.py --report   # merge shards, rebuild the .md

MiniCheck checks one claim at a time (batch 1), so one process keeps only two or three cores busy.
On a many-core machine, run N processes over disjoint rows, then merge:

    for k in 0 1 2 3 4 5; do
      uv run python scripts/S384_exp04_minicheck_key_v22.py --full --shard $k/6 --threads 4 \
          > /tmp/S384_shard$k.log 2>&1 &
    done; wait
    uv run python scripts/S384_exp04_minicheck_key_v22.py --report

The download comes before the loop, so the six processes do not each find the data missing.
Each process holds its own 3 GB float32 copy of the checker and runs G1 and G2 itself before writing.
--full appends to findings/recompute/S384_exp04_minicheck_key_v22.jsonl (or, with --shard K/N and
N > 1, to findings/recompute/S384_shards/), resumes by (question_id, config) across all of them, and
when the last row is in writes the merged .jsonl and S384_exp04_minicheck_key_v22.md. --report
merges, checks the merged file holds every session and row, deletes the shard files and rewrites
the .md. Each session first appends one {"_session": {...}} line (key path and sha256, script,
date, shard, device, threads, checkpoint, library versions, the punkt_tab English tables' sha256,
the G1 and G2 evidence); every other line is one scored row, carrying key_sha256 too, its group
("answerable" or "refutation") and v1_deposited, the deposited values for the row, which is null for
the refutation group. A reader of the .jsonl skips the _session lines.

The checkpoint directory is $MENTORI_HF_CACHE if set, else the first of <upstream>/data/hf_cache and
the sibling checkouts' data/hf_cache (machine.SIBLINGS) that holds
models--lytang--MiniCheck-Flan-T5-Large.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import platform
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("TQDM_DISABLE", "1")  # MiniCheck opens a progress bar per score() call, two per row
                                            # (inference.py:83); tqdm reads this when first imported

sys.path.insert(0, str(Path(__file__).resolve().parent))
from machine import PUB_SCRIPTS, RECOMPUTE, RESULTS, ROOT, SIBLINGS, UPSTREAM, rel  # noqa: E402
import S373_rejudge_v2 as S373  # noqa: E402  (the judge's key: KEY, AS_V1; imports no model library)

import numpy as np  # noqa: E402

SCRIPT = "scripts/S384_exp04_minicheck_key_v22.py"
DEPOSITED = PUB_SCRIPTS / "analysis_minicheck.py"
DEPOSITED_SHA256 = "24f3d8634a1d9ca1d8b88d9dcef77212a0945516236caa17450c9098147a23f4"
HARNESS_COMMON = ROOT / "recovered_harness/tests/experiments_v4/exp_common.py"
ARTEFACT = RESULTS / "exp04_minicheck_latest.json"
GENERATION = RESULTS / "exp04_generation_latest.json"
KEY_V1 = ROOT / "data/replication_inputs/ground_truth.json"
KEY_V22 = S373.AS_V1   # the judge's key in the v1 format: ground truth v2.4 since 11 October 09:00 (Q50), v2.3 from 00:00 (Q45) (S381 --key 2.4)
OUT_JSONL = RECOMPUTE / "S384_exp04_minicheck_key_v22.jsonl"
OUT_MD = RECOMPUTE / "S384_exp04_minicheck_key_v22.md"
SHARD_DIR = RECOMPUTE / "S384_shards"            # --shard K/N writes here; --report merges and clears it
CKPT = "models--lytang--MiniCheck-Flan-T5-Large"
SEED, GATE_N, PROB_TOL = 42, 20, 1e-4
N_DEPOSITED = 528
ANSWERABLE, REFUTATION = "answerable", "refutation"   # the group column (D5); REFUTATION is also the answer_type


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def key_version() -> str:
    """The current key's version as its file states it (S373.KEY "version", "2.4" since 11 October, Q50)."""
    return str(json.loads(S373.KEY.read_text(encoding="utf-8"))["version"])


def refutation_ids() -> set[str]:
    """D5: the questions whose answer_type in S373.KEY is "refutation" (OOD_041 to OOD_050 in v2.4)."""
    return {q["id"] for q in json.loads(S373.KEY.read_text(encoding="utf-8"))["records"]
            if q.get("answer_type") == REFUTATION}


def group_of(qid: str, ref_ids: set[str]) -> str:
    return REFUTATION if qid in ref_ids else ANSWERABLE


def require_as_v1_from_key() -> None:
    """S388's check: S373.AS_V1's source_v<version>_sha256 (S381's field for the version in S373.KEY's
    "version") must be the sha256 of S373.KEY. Exits otherwise."""
    kv = key_version()
    src = f"source_v{kv.replace('.', '')}_sha256"
    got = json.loads(S373.AS_V1.read_text(encoding="utf-8")).get(src)
    if got != sha256(S373.KEY):
        sys.exit(f"FATAL: {S373.AS_V1.name} was built from another key ({src} {str(got)[:12]}), "
                 f"not {S373.KEY.name} v{kv}")


def lift(path: Path, names: tuple[str, ...], ns: dict) -> str:
    """exec the named top-level functions from a source file into ns; return the file's sha256.
    The same extraction S19 uses for decompose_to_sentences."""
    src = path.read_text()
    for name in names:
        m = re.search(rf"\ndef {name}\(.*?(?=\ndef |\nclass |\Z)", src, re.S)
        if not m:
            sys.exit(f"FATAL: {name} not found in {rel(path)}")
        exec(m.group(0), ns)
    return hashlib.sha256(src.encode()).hexdigest()


def deposited_code() -> tuple[dict, dict]:
    ns: dict = {"re": re, "np": np, "json": json, "Path": Path, "List": List, "Dict": Dict,
                "Any": Any, "Optional": Optional, "Tuple": Tuple,
                "logger": logging.getLogger("minicheck")}
    shas = {"harness_exp_common_sha256": lift(HARNESS_COMMON, ("load_ground_truth",), ns),
            "deposited_script_sha256": lift(DEPOSITED, ("decompose_to_sentences", "score_faithfulness",
                                                        "run_minicheck_scoring"), ns)}
    if shas["deposited_script_sha256"] != DEPOSITED_SHA256:
        sys.exit(f"FATAL: {rel(DEPOSITED)} sha256 {shas['deposited_script_sha256']} is not the "
                 f"deposited {DEPOSITED_SHA256}")
    return ns, shas


class NoChecker:
    """G1's checker. Selection and claim splitting never depend on a score, so nothing is scored."""

    def score(self, docs, claims):
        return [0] * len(claims), [0.0] * len(claims), None, None


def hf_cache() -> Path:
    env = os.environ.get("MENTORI_HF_CACHE")
    if env:
        p = Path(env).expanduser()
        if not (p / CKPT / "snapshots").is_dir():
            sys.exit(f"MENTORI_HF_CACHE={p} holds no {CKPT}")
        return p
    cands = [UPSTREAM / "data/hf_cache", *(ROOT.parent / s / "data/hf_cache" for s in SIBLINGS)]
    for c in cands:
        if (c / CKPT / "snapshots").is_dir():
            return c
    sys.exit(f"no {CKPT} in any of:\n" + "\n".join(f"    {c}" for c in cands)
             + "\nset MENTORI_HF_CACHE to the hf_cache directory that holds it")


def checkpoint_identity(cache: Path) -> dict:
    """Snapshot the offline loader resolves (refs/main) and the weights blob, whose name is its sha256."""
    root = cache / CKPT
    snap = (root / "refs/main").read_text().strip()
    out = {"hf_cache": rel(cache), "snapshot": snap}
    for f in ("model.safetensors", "pytorch_model.bin"):
        p = root / "snapshots" / snap / f
        if p.exists():
            out["weights"] = f
            out["weights_blob"] = p.resolve().name
            break
    return out


PUNKT_FETCH = "uv run python -c \"import nltk; nltk.download('punkt_tab')\""


def punkt_tab() -> dict:
    """nltk's punkt_tab data, which MiniCheck's sent_tokenize reads for every document
    (minicheck/inference.py:3, :17-20, :139) and uv does not install. Exits naming the download
    command when it is missing, before any model loads. The English tables set the sentence and
    chunk boundaries of every document, so their sha256 is recorded."""
    import nltk
    try:
        ptr = nltk.data.find("tokenizers/punkt_tab/english/")
    except LookupError:
        sys.exit("nltk's punkt_tab data is missing; MiniCheck's sent_tokenize needs it. Run once:\n"
                 f"    {PUNKT_FETCH}")
    d = Path(str(ptr))
    h = None
    if d.is_dir():
        hh = hashlib.sha256()
        for f in sorted(p for p in d.iterdir() if p.is_file()):
            hh.update(f.name.encode() + b"\0" + f.read_bytes())
        h = hh.hexdigest()
    return {"nltk": nltk.__version__, "punkt_tab": rel(d), "punkt_tab_english_sha256": h}


def load_minicheck(device: str):
    """MiniCheck-Flan-T5-Large on one named device. The library hard-codes device_map="auto"
    (minicheck/inference.py:40), so the loader it calls is swapped for one that pins the device,
    for the duration of the load only."""
    punkt = punkt_tab()
    import torch
    import minicheck.inference as mi
    from minicheck.minicheck import MiniCheck

    real = mi.AutoModelForSeq2SeqLM

    class Pinned:
        @staticmethod
        def from_pretrained(*a, **k):
            k["device_map"] = {"": device}
            return real.from_pretrained(*a, **k)

    cache = hf_cache()
    mi.AutoModelForSeq2SeqLM = Pinned
    try:
        scorer = MiniCheck(model_name="flan-t5-large", cache_dir=str(cache))
    finally:
        mi.AutoModelForSeq2SeqLM = real
    model = scorer.model.model
    got = model.device.type
    if got != torch.device(device).type:
        sys.exit(f"FATAL: asked for {device}, MiniCheck loaded on {model.device}")
    dtype = str(next(model.parameters()).dtype)
    if dtype != "torch.float32":
        sys.exit(f"FATAL: MiniCheck loaded as {dtype}; the deposited run was float32")
    import importlib.metadata as md
    import transformers
    dist = md.distribution("minicheck")
    vcs = json.loads(dist.read_text("direct_url.json") or "{}").get("vcs_info", {})
    info = {"device": str(model.device), "dtype": dtype, "torch_threads": torch.get_num_threads(),
            **checkpoint_identity(cache), "torch": torch.__version__,
            "transformers": transformers.__version__,
            "minicheck": f"{dist.version} git {vcs.get('commit_id', '?')}", **punkt,
            "platform": f"{platform.system()} {platform.machine()}, python {sys.version.split()[0]}"}
    return scorer, info


def keys(rows) -> list[tuple[str, str]]:
    return [(r["question_id"], r["config"]) for r in rows]


def sentences(row: dict, side: str) -> list[str]:
    return [d["sentence"] for d in row["minicheck_details"][f"{side}_details"]]


def rows_on_key(results, key22, ref_ids) -> tuple[list[dict], dict]:
    """The generation rows, each row on a question the key keeps replaced by a copy carrying the key's
    answerable flag (True where the key has none, the default analysis_minicheck.py:230 uses); rows on
    questions the key does not hold are passed through unchanged, and the deposited selection skips them.
    Exits unless the rows whose effective flag changes (the row's own, else the key's, as
    analysis_minicheck.py:230 reads it) are exactly the rows on S373.KEY's answer_type "refutation"
    questions that the key keeps, every one of them changed to answerable (D5)."""
    kq = {q["id"]: q for q in key22["questions"]}
    out, changed = [], set()
    for r in results:
        q = kq.get(r["question_id"])
        if q is None:
            out.append(r)
            continue
        flag = bool(q.get("answerable", True))
        if bool(r.get("answerable", flag)) != flag:
            changed.add((r["question_id"], r["config"], flag))
        out.append(dict(r, answerable=flag))
    want = {(r["question_id"], r["config"], True) for r in results
            if r["question_id"] in ref_ids and r["question_id"] in kq}
    refq = sorted({q for q, _, _ in want})
    if changed != want:
        sys.exit(f"FATAL: the key's answerable flag differs from the deposited row flag on {len(changed)} "
                 f"generation rows, not on exactly the {len(want)} rows of the {len(refq)} answer_type "
                 f"{REFUTATION} questions of {S373.KEY.name}, each made answerable (D5); "
                 f"{sorted(changed ^ want)[:5]}. {KEY_V22.name} must carry answerable = "
                 f"question_answerable from {S373.KEY.name} (S381)")
    return out, {"rows_flag_from_key_changed": len(changed), "refutation_questions": refq,
                 "refutation_rows": len(want)}


def gate_g1(ns, results, deposited, key22, ref_ids) -> tuple[dict, list[tuple[str, str]], list[dict]]:
    """Selection and claims for all 528 rows, pure Python; then the flag check (rows_on_key) and the
    current key's selection over the rows with the key's flag, which it returns with them."""
    kv = key_version()
    dropped = set(key22["dropped_d7"])
    v1 = ns["run_minicheck_scoring"](results, KEY_V1, NoChecker())
    if keys(v1) != keys(deposited):
        sys.exit(f"G1 FAIL: the deposited selection with the v1 key gives {len(v1)} rows, not the "
                 f"deposited {len(deposited)} in the deposited order")
    bad = []
    for a, b in zip(v1, deposited):
        same = (all(a[f] == b[f] for f in ("index_name", "category", "difficulty"))
                and all(a["minicheck"][f] == b["minicheck"][f] for f in ("n_gen_sentences", "n_exp_sentences"))
                and sentences(a, "precision") == sentences(b, "precision")
                and sentences(a, "recall") == sentences(b, "recall"))
        if not same:
            bad.append((a["question_id"], a["config"]))
    if bad:
        sys.exit(f"G1 FAIL: {len(bad)} of {len(v1)} rows differ from the deposited claims, first {bad[:5]}")
    results_v22, flag_ev = rows_on_key(results, key22, ref_ids)
    v22 = keys(ns["run_minicheck_scoring"](results_v22, KEY_V22, NoChecker()))
    in_v1 = set(keys(v1))
    expect = [k for k in keys(results) if (k in in_v1 or k[0] in ref_ids) and k[0] not in dropped]
    if v22 != expect:
        sys.exit(f"G1 FAIL: the v{kv} selection ({len(v22)} rows) is not the v1 selection plus the rows on "
                 f"the {REFUTATION} questions, minus the dropped questions ({len(expect)} rows)")
    skipped = [k for k in keys(v1) if k[0] in dropped]
    n_ref = sum(1 for k in v22 if k[0] in ref_ids)
    if n_ref != flag_ev["refutation_rows"] or len(v22) - n_ref != len(v1) - len(skipped):
        sys.exit(f"G1 FAIL: the v{kv} selection's groups ({len(v22) - n_ref} {ANSWERABLE}, {n_ref} "
                 f"{REFUTATION}) are not the v1 selection less the dropped ({len(v1) - len(skipped)}) and "
                 f"the {flag_ev['refutation_rows']} rows whose flag the key changes")
    ev = {"rows_compared": len(v1), "rows_matched": len(v1) - len(bad),
          "claims_compared": sum(a["minicheck"]["n_gen_sentences"] + a["minicheck"]["n_exp_sentences"] for a in v1),
          "v22_rows": len(v22), "v22_rows_answerable": len(v22) - n_ref, "v22_rows_refutation": n_ref,
          "skipped_dropped_rows": len(skipped),
          "skipped_dropped": sorted({q for q, _ in skipped}), "flag_from_key": flag_ev}
    print(f"G1 pass: {ev['rows_matched']}/{ev['rows_compared']} rows, {ev['claims_compared']} claim "
          f"sentences identical to the deposit; the key's flag changes exactly the {n_ref} rows on the "
          f"{len(flag_ev['refutation_questions'])} {REFUTATION} questions; v{kv} selects {len(v22)} "
          f"({len(v22) - n_ref} {ANSWERABLE}, {n_ref} {REFUTATION}), skips {len(skipped)} "
          f"rows on {ev['skipped_dropped']}")
    return ev, v22, results_v22


def gate_rows(deposited) -> list[int]:
    return sorted(random.Random(SEED).sample(range(len(deposited)), GATE_N))


def gate_g2(ns, scorer, by_key, deposited, device) -> dict:
    """20 fixed rows rescored with the v1 key on this device against the deposited values."""
    idx = gate_rows(deposited)
    t0 = time.time()
    n_sent = n_exact = 0
    worst = 0.0
    bad = []
    for i in idx:
        d = deposited[i]
        got = ns["run_minicheck_scoring"]([by_key[(d["question_id"], d["config"])]], KEY_V1, scorer)
        if len(got) != 1:
            bad.append((d["question_id"], d["config"], "not selected"))
            continue
        g, gm, dm = got[0], got[0]["minicheck"], d["minicheck"]
        for f in ("precision", "recall", "f1", "n_gen_sentences", "n_exp_sentences"):
            if gm[f] != dm[f]:
                bad.append((d["question_id"], d["config"], f, dm[f], gm[f]))
        for f in ("mean_precision_prob", "mean_recall_prob"):
            worst = max(worst, abs(gm[f] - dm[f]))
            if abs(gm[f] - dm[f]) > PROB_TOL + 1e-12:
                bad.append((d["question_id"], d["config"], f, dm[f], gm[f]))
        for side, lab in (("precision", "supported"), ("recall", "covered")):
            for x, y in zip(g["minicheck_details"][f"{side}_details"], d["minicheck_details"][f"{side}_details"]):
                n_sent += 1
                diff = abs(x["probability"] - y["probability"])
                worst = max(worst, diff)
                n_exact += diff == 0
                if x[lab] != y[lab] or diff > PROB_TOL + 1e-12 or x["sentence"] != y["sentence"]:
                    bad.append((d["question_id"], d["config"], side, y["sentence"][:40], y["probability"], x["probability"]))
    ev = {"rows": [f"{deposited[i]['question_id']}|{deposited[i]['config']}" for i in idx],
          "rows_compared": len(idx), "rows_matched": len(idx) - len({b[:2] for b in bad}),
          "sentences_compared": n_sent, "probabilities_identical_4dp": n_exact,
          "max_abs_probability_diff": round(worst, 6), "tolerance": PROB_TOL, "device": device,
          "seconds": round(time.time() - t0, 1)}
    if bad:
        for b in bad[:20]:
            print("   ", b)
        sys.exit(f"G2 FAIL on {device}: {len(bad)} mismatches over {len(idx)} rows")
    print(f"G2 pass on {device}: {ev['rows_matched']}/{len(idx)} rows; P, R, F1, counts and labels "
          f"exact; {n_exact}/{n_sent} sentence probabilities identical at 4 dp, max |diff| "
          f"{worst:.4f} (tolerance {PROB_TOL}); {ev['seconds']} s")
    return ev


def shard_files() -> list[Path]:
    return sorted(SHARD_DIR.glob(f"{OUT_JSONL.stem}.shard*.jsonl")) if SHARD_DIR.is_dir() else []


def read_out() -> tuple[list[dict], list[dict]]:
    """Every session line and scored row, from the main .jsonl and any shard files. A merge copies
    shard lines into the main file, so an identical copy is the same line; a row scored twice with
    different content is refused rather than picked from. Sessions are compared as parsed JSON,
    so a copy re-serialised with other escaping is still the same session."""
    sessions, rows, seen = [], {}, set()
    for f in [OUT_JSONL] * OUT_JSONL.exists() + shard_files():
        for line in f.read_text().splitlines():
            if not line.strip():
                continue
            d = json.loads(line)
            if "_session" in d:
                canon = json.dumps(d, sort_keys=True)
                if canon not in seen:
                    seen.add(canon)
                    sessions.append(d)
                continue
            k = (d["question_id"], d["config"])
            if k in rows and rows[k] != d:
                sys.exit(f"FATAL: {k} is scored twice, differently, across {rel(OUT_JSONL)} and {rel(SHARD_DIR)}")
            rows[k] = d
    return sessions, list(rows.values())


def merge(sessions, rows, order) -> None:
    """One .jsonl: every session line, then the rows in the deposited order. Written whole and
    renamed into place, so two shards finishing together cannot leave half a file."""
    pos = {k: i for i, k in enumerate(order)}
    rows = sorted(rows, key=lambda r: pos[(r["question_id"], r["config"])])
    sessions = sorted(sessions, key=lambda s: (s["_session"]["date"], s["_session"].get("shard", "")))
    tmp = OUT_JSONL.with_suffix(f".tmp{os.getpid()}")
    tmp.write_text("".join(json.dumps(d, ensure_ascii=False) + "\n" for d in sessions + rows))
    os.replace(tmp, OUT_JSONL)
    print(f"wrote {rel(OUT_JSONL)}: {len(sessions)} session lines, {len(rows)} rows")


def mean(xs) -> float:
    return float(np.mean(xs)) if xs else float("nan")


def summarise(rows: list[dict], dep_by_key: dict) -> list[str]:
    """Tables for the .md over the answerable group: the current key against v1 on the same rows, by
    configuration and by category."""
    kv = key_version()
    def block(rs):
        v1 = [dep_by_key[(r["question_id"], r["config"])]["minicheck"] for r in rs]
        v2 = [r["minicheck"] for r in rs]
        return (len(rs), *(mean([m[f] for m in v2]) for f in ("precision", "recall", "f1")),
                *(mean([m[f] for m in v1]) for f in ("precision", "recall", "f1")),
                mean([m["n_exp_sentences"] for m in v2]), mean([m["n_exp_sentences"] for m in v1]))

    head = ("| {} | N | " + f"P v{kv} | R v{kv} | F1 v{kv} | P v1 | R v1 | F1 v1 | key sents v{kv} | key sents v1 |\n"
            "|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|")
    fmt = "| {} | {} | {:.3f} | {:.3f} | {:.3f} | {:.3f} | {:.3f} | {:.3f} | {:.1f} | {:.1f} |"
    out = [head.format("Config")]
    for cfg in sorted({r["config"] for r in rows}):
        out.append(fmt.format(cfg, *block([r for r in rows if r["config"] == cfg])))
    out.append(fmt.format("**all**", *block(rows)))
    out += ["", head.format("Category")]
    for cat in sorted({r["category"] for r in rows}):
        out.append(fmt.format(cat, *block([r for r in rows if r["category"] == cat])))
    return out


def summarise_refutation(rows: list[dict]) -> list[str]:
    """Tables for the .md over the refutation group: the current key only (the deposited run never
    scored these rows), by configuration and by question."""
    kv = key_version()
    def block(rs):
        v2 = [r["minicheck"] for r in rs]
        return (len(rs), *(mean([m[f] for m in v2]) for f in ("precision", "recall", "f1", "n_exp_sentences")))

    head = ("| {} | N | " + f"P v{kv} | R v{kv} | F1 v{kv} | key sents v{kv} |\n"
            "|---|--:|--:|--:|--:|--:|")
    fmt = "| {} | {} | {:.3f} | {:.3f} | {:.3f} | {:.1f} |"
    out = [head.format("Config")]
    for cfg in sorted({r["config"] for r in rows}):
        out.append(fmt.format(cfg, *block([r for r in rows if r["config"] == cfg])))
    out.append(fmt.format("**all**", *block(rows)))
    out += ["", head.format("Question")]
    for qid in sorted({r["question_id"] for r in rows}):
        out.append(fmt.format(qid, *block([r for r in rows if r["question_id"] == qid])))
    return out


def claim_weighted(rows, get) -> tuple[float, float, int, int]:
    sup = tot_p = cov = tot_r = 0
    for r in rows:
        det = get(r)
        sup += sum(d["supported"] for d in det["precision_details"])
        tot_p += len(det["precision_details"])
        cov += sum(d["covered"] for d in det["recall_details"])
        tot_r += len(det["recall_details"])
    return sup / tot_p, cov / tot_r, tot_p, tot_r


def write_report(sessions, rows, deposited, g1_now, ref_ids) -> None:
    """The .md. The existing tables (answer means and claim-weighted, v1 columns on the same rows) are
    over the answerable group; the refutation group, rows on ref_ids, has its own section after them."""
    dep_by_key = {(d["question_id"], d["config"]): d for d in deposited}
    s0 = sessions[-1]["_session"]
    rows_ref = [r for r in rows if group_of(r["question_id"], ref_ids) == REFUTATION]
    rows = [r for r in rows if group_of(r["question_id"], ref_ids) == ANSWERABLE]
    p22, r22, np22, nr22 = claim_weighted(rows, lambda r: r["minicheck_details"])
    same = [dep_by_key[(r["question_id"], r["config"])] for r in rows]
    p1, r1, np1, nr1 = claim_weighted(same, lambda r: r["minicheck_details"])
    allp, allr, allf = (mean([d["minicheck"][f] for d in deposited]) for f in ("precision", "recall", "f1"))
    kv = key_version()
    lines = [
        f"# S384: exp04 MiniCheck against the answer key, ground truth v{kv}",
        "",
        f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} by `{SCRIPT}` "
        f"from `{rel(OUT_JSONL)}`.",
        "",
        "## Provenance",
        "",
        f"- key: `{s0['key']}`, sha256 `{s0['key_sha256']}`"
        + (f" (v{s0['key_version']}, from `{s0['key_source']}` sha256 `{s0['key_source_sha256']}`)"
           if s0.get("key_version") else ""),
        f"- v1 key (gates): `{s0['key_v1']}`, sha256 `{s0['key_v1_sha256']}`",
        f"- deposited code: `{s0['deposited_script']}` sha256 `{s0['deposited_script_sha256']}`; "
        f"load_ground_truth from `{rel(HARNESS_COMMON)}` sha256 `{s0['harness_exp_common_sha256']}`",
        f"- deposited artefact: `{s0['artefact']}` sha256 `{s0['artefact_sha256']}`; answers from "
        f"`{s0['generation']}` sha256 `{s0['generation_sha256']}`",
        f"- sessions: {len(sessions)}; " + "; ".join(
            f"{s['_session']['date']} shard {s['_session'].get('shard', '0/1')} on {s['_session']['model']['device']} "
            f"({s['_session']['model']['platform']}, {s['_session']['model']['torch_threads']} threads)"
            for s in sessions),
        f"- checker: MiniCheck-Flan-T5-Large, snapshot `{s0['model']['snapshot']}`, weights blob "
        f"`{s0['model'].get('weights_blob')}`, {s0['model']['dtype']}, torch {s0['model']['torch']}, "
        f"transformers {s0['model']['transformers']}",
        f"- sentence splitter: nltk {s0['model']['nltk']}, punkt_tab English tables sha256 "
        f"`{s0['model']['punkt_tab_english_sha256']}`" + (
            "" if len({s['_session']['model']['punkt_tab_english_sha256'] for s in sessions}) == 1
            else " (NOT the same in every session; see the _session lines)"),
        "",
        "## Gates (every session passed both before writing)",
        "",
    ]
    for s in sessions:
        g1, g2 = s["_session"]["gate_g1"], s["_session"]["gate_g2"]
        fk = g1["flag_from_key"]
        lines.append(f"- {s['_session']['date']}: G1 {g1['rows_matched']}/{g1['rows_compared']} rows and "
                     f"{g1['claims_compared']} claim sentences identical to the deposit"
                     + (f", the key's flag changes exactly the {fk['refutation_rows']} rows on the "
                        f"{len(fk['refutation_questions'])} {REFUTATION} questions" if fk else "") + "; G2 "
                     f"{g2['rows_matched']}/{g2['rows_compared']} rows exact on {g2['device']}, "
                     f"{g2['probabilities_identical_4dp']}/{g2['sentences_compared']} sentence probabilities "
                     f"identical at 4 dp, max |diff| {g2['max_abs_probability_diff']}")
    refq = g1_now["flag_from_key"]["refutation_questions"]
    lines += [f"- this report: G1 re-run now, {g1_now['rows_matched']}/{g1_now['rows_compared']} rows",
              "",
              "## Rows",
              "",
              f"- scored against v{kv}: {len(rows) + len(rows_ref)} of {g1_now['v22_rows']}: {len(rows)} in the "
              f"{ANSWERABLE} group (the deposited 528 minus "
              f"{g1_now['skipped_dropped_rows']} rows on the dropped questions {', '.join(g1_now['skipped_dropped'])}) "
              f"and {len(rows_ref)} in the {REFUTATION} group (the rows on the {len(refq)} questions whose "
              f"answer_type in `{S373.KEY.name}` is {REFUTATION}; the deposited run did not score them, "
              f"since their generation rows carry answerable false and its selection reads that first)",
              f"- rows with no claim sentence in the answer or in the key: "
              f"{sum(1 for r in rows + rows_ref if not r['minicheck']['n_gen_sentences'] or not r['minicheck']['n_exp_sentences'])} "
              f"(the deposited run_minicheck_scoring raises KeyError on such a row: score_faithfulness "
              f"returns early without mean_precision_prob, analysis_minicheck.py:120-129, which :262 "
              f"reads; G1 ran it on every v{kv} row)",
              "",
              "## Answer means (the deposited report's statistic: mean over answers of the per-answer value)",
              "",
              f"The {len(rows)} rows of the {ANSWERABLE} group; the {REFUTATION} group is in its own section "
              "below. v1 columns are the deposited values for the same rows.",
              "",
              *summarise(rows, dep_by_key),
              "",
              f"Deposited v1 over all 528 rows: P {allp:.3f}, R {allr:.3f}, F1 {allf:.3f}.",
              "",
              "## Claim-weighted (pooled over sentences, as S19b reports precision)",
              "",
              f"The {ANSWERABLE} group.",
              "",
              "| | precision | answer sentences | recall | key sentences |",
              "|---|--:|--:|--:|--:|",
              f"| v{kv} | {p22:.4f} | {np22} | {r22:.4f} | {nr22} |",
              f"| v1, same rows | {p1:.4f} | {np1} | {r1:.4f} | {nr1} |",
              "",
              f"## {REFUTATION.capitalize()} group (D5): {len(rows_ref)} rows on {len(refq)} questions",
              ""]
    if rows_ref:
        pr, rr, npr, nrr = claim_weighted(rows_ref, lambda r: r["minicheck_details"])
        lines += [f"The rows on {', '.join(refq)}, whose answer_type in `{S373.KEY.name}` is {REFUTATION}, "
                  f"scored against the key's expected_answer like every other row. They are in no table above. "
                  f"The deposited run never scored them, so there is no v1 column.",
                  "",
                  "Answer means:",
                  "",
                  *summarise_refutation(rows_ref),
                  "",
                  "Claim-weighted:",
                  "",
                  "| | precision | answer sentences | recall | key sentences |",
                  "|---|--:|--:|--:|--:|",
                  f"| v{kv} | {pr:.4f} | {npr} | {rr:.4f} | {nrr} |",
                  ""]
    else:
        lines += [f"None: no question the key keeps has answer_type {REFUTATION} in `{S373.KEY.name}`.", ""]
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"wrote {rel(OUT_MD)}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--full", action="store_true",
                    help="after the gates, score the current key's rows (516 answerable, 60 refutation) "
                         "against it (S373.AS_V1)")
    ap.add_argument("--report", action="store_true",
                    help="merge the shards into the .jsonl, rebuild the .md, clear the shards; no model")
    ap.add_argument("--device", default="cpu", choices=["cpu", "mps", "cuda"])
    ap.add_argument("--shard", default="0/1", help="K/N: score every N-th row from the K-th (0-based)")
    ap.add_argument("--threads", type=int, default=0, help="torch threads per process (0 = torch's default)")
    a = ap.parse_args()
    try:
        shard_k, shard_n = (int(x) for x in a.shard.split("/"))
        assert 0 <= shard_k < shard_n
    except (ValueError, AssertionError):
        sys.exit(f"--shard {a.shard}: expected K/N with 0 <= K < N")
    require_as_v1_from_key()

    ns, shas = deposited_code()
    dep = json.loads(ARTEFACT.read_text())["per_result"]
    if len(dep) != N_DEPOSITED:
        sys.exit(f"FATAL: {rel(ARTEFACT)} has {len(dep)} rows, not {N_DEPOSITED}")
    results = json.loads(GENERATION.read_text())["per_question_results"]
    by_key = {(r["question_id"], r.get("config", "unknown")): r for r in results}
    if len(by_key) != len(results):
        sys.exit("FATAL: (question_id, config) is not unique in the generation file")
    key22 = json.loads(KEY_V22.read_text())
    key_sha = sha256(KEY_V22)
    ref_ids = refutation_ids()

    g1, v22_keys, results_v22 = gate_g1(ns, results, dep, key22, ref_ids)
    by_key_v22 = {(r["question_id"], r.get("config", "unknown")): r for r in results_v22}
    sessions, rows = read_out()
    for s in sessions:
        if s["_session"]["key_sha256"] != key_sha:
            sys.exit(f"FATAL: {rel(OUT_JSONL)} was written against key sha256 "
                     f"{s['_session']['key_sha256']}, not the current {key_sha}; move it aside")
        if "flag_from_key" not in s["_session"]["gate_g1"]:
            sys.exit(f"FATAL: {rel(OUT_JSONL)} holds a session written by S384 before D5 (its G1 records no "
                     "flag_from_key); move it aside")
    if any("group" not in r for r in rows):
        sys.exit(f"FATAL: {rel(OUT_JSONL)} holds rows written by S384 before D5 (no group field); move it aside")

    if a.report:
        if not sessions or len(rows) != len(v22_keys):
            sys.exit(f"--report: {len(rows)} of {len(v22_keys)} rows scored so far; finish --full first")
        merge(sessions, rows, v22_keys)
        back = [json.loads(x) for x in OUT_JSONL.read_text().splitlines() if x.strip()]
        s2 = sum("_session" in d for d in back)
        r2 = [(d["question_id"], d["config"]) for d in back if "_session" not in d]
        if s2 != len(sessions) or r2 != v22_keys:
            sys.exit(f"FATAL: the merged {rel(OUT_JSONL)} does not hold every session and row; shards kept")
        for f in shard_files():
            f.unlink()
        if SHARD_DIR.is_dir() and not any(SHARD_DIR.iterdir()):
            SHARD_DIR.rmdir()
        write_report(sessions, rows, dep, g1, ref_ids)
        return 0

    done = {(r["question_id"], r["config"]) for r in rows}
    todo = [k for i, k in enumerate(v22_keys) if i % shard_n == shard_k and k not in done]
    if a.full and not todo:
        print(f"shard {a.shard}: nothing left to score ({len(rows)} of {len(v22_keys)} rows in); "
              f"no model loaded, nothing written. --report merges and rebuilds the .md")
        return 0

    if a.threads:
        import torch
        torch.set_num_threads(a.threads)
    scorer, info = load_minicheck(a.device)
    print(f"MiniCheck on {info['device']} ({info['dtype']}, {info['torch_threads']} threads), "
          f"snapshot {info['snapshot'][:12]}, weights {info.get('weights_blob', '?')[:12]}")
    g2 = gate_g2(ns, scorer, by_key, dep, a.device)
    if not a.full:
        print(f"gates only: nothing written (pass --full to score against v{key_version()})")
        return 0

    out = OUT_JSONL
    if shard_n > 1:
        SHARD_DIR.mkdir(exist_ok=True)
        out = SHARD_DIR / f"{OUT_JSONL.stem}.shard{shard_k}of{shard_n}.jsonl"
    dep_by_key = {(d["question_id"], d["config"]): d for d in dep}
    # for the ETA only: the deposited count where the row was deposited, else the deposited split of the answer
    total = sum(dep_by_key[k]["minicheck"]["n_gen_sentences"] if k in dep_by_key else
                len(ns["decompose_to_sentences"](by_key_v22[k]["generation"]["answer"])) for k in todo)
    print(f"v{key_version()} shard {a.shard}: {len(done)} rows already scored overall, {len(todo)} to go here "
          f"(~{total} answer sentences plus the key's sentences) -> {rel(out)}")
    session = {"_session": {
        "script": SCRIPT, "date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "shard": a.shard,
        "key": rel(KEY_V22), "key_sha256": key_sha, "key_v1": rel(KEY_V1), "key_v1_sha256": sha256(KEY_V1),
        "key_source": rel(S373.KEY), "key_source_sha256": sha256(S373.KEY), "key_version": key_version(),
        "deposited_script": rel(DEPOSITED), **shas,
        "artefact": rel(ARTEFACT), "artefact_sha256": sha256(ARTEFACT),
        "generation": rel(GENERATION), "generation_sha256": sha256(GENERATION),
        "model": info, "gate_g1": g1, "gate_g2": g2}}
    fh = open(out, "a")
    fh.write(json.dumps(session, ensure_ascii=False) + "\n")
    fh.flush()
    t0 = time.time()
    n_claims = 0
    for i, k in enumerate(todo):
        got = ns["run_minicheck_scoring"]([by_key_v22[k]], KEY_V22, scorer)
        if len(got) != 1:
            sys.exit(f"FATAL: {k} passed G1's current-key selection but was not scored")
        g, d, grp = got[0], dep_by_key.get(k), group_of(k[0], ref_ids)
        if (d is None) != (grp == REFUTATION):
            sys.exit(f"FATAL: {k} is in the {grp} group but {'absent from' if d is None else 'in'} "
                     f"{rel(ARTEFACT)}; only the {REFUTATION} group's rows are absent from it")
        fh.write(json.dumps({
            "question_id": g["question_id"], "config": g["config"], "index_name": g["index_name"],
            "category": g["category"], "difficulty": g["difficulty"], "group": grp,
            "minicheck": g["minicheck"], "minicheck_details": g["minicheck_details"],
            "v1_deposited": None if d is None else {f: d["minicheck"][f] for f in (
                "precision", "recall", "f1", "n_gen_sentences", "n_exp_sentences")},
            "key_sha256": key_sha, "device": info["device"],
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
        n_claims += g["minicheck"]["n_gen_sentences"]
        if (i + 1) % 10 == 0 or i + 1 == len(todo):
            el = time.time() - t0
            print(f"  {i+1}/{len(todo)} rows, {el/60:.1f} min, "
                  f"ETA {(total-n_claims)*el/max(n_claims, 1)/60:.0f} min", flush=True)
    fh.close()
    sessions, rows = read_out()
    if len(rows) == len(v22_keys):
        if shard_files():
            merge(sessions, rows, v22_keys)
        write_report(sessions, rows, dep, g1, ref_ids)
        if shard_files():
            print(f"all rows in; run --report once every shard has exited, to clear {rel(SHARD_DIR)}")
    else:
        print(f"{len(rows)} of {len(v22_keys)} rows scored overall; the .md is written when all are in")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
