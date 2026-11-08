#!/usr/bin/env python3
"""S520 - every language-model call of the revised study, counted from the call logs, for the Plan Dashboard, Figure 1,
Supplementary Figure 1 and Methods (Valerio, 1 November: "all the numbers for all the LLM calls in the study that land of
course in figures and main text too"; block 1.2 option a: the unit is every language-model call).

THE COUNTING RULE, as proposed to Valerio on 1 November. Rule 5 is ruled: D201 Q7 (Valerio, 2 November 2026, yes), replaced
answers stay in their own column. The alternative (kept calls only) needed the answer join on every log, which judge logs
cannot give.
  1. One call is one line in a named call log: a prompt sent to a language model.
  2. Resends inside a line's `attempts` stay one call. Every retry line counts.
  3. Ok means `status` ok. Failed is every other status, named. Unparseable is ok, since the model replied, so
     `judge_status` is not read.
  4. Not calls: `ragas_calls` lines with endpoint embeddings and any bge-m3 line (counted apart as not calls); encoders,
     MiniCheck, fresh loads and Gemini countTokens write no call-log line.
  5. Replaced answers count, in their own column: in a sink, `replaced` is a call whose ctx_uid is not on an answer's last
     line. `no_answer_line` is the part of them whose ctx_uid is on no answer line at all (a rerun that rewrote the file, a
     crashed attempt, a refusal moved out, or, in a live sink, a call in flight). A sink with no answers file, or a line
     with no ctx_uid, cannot be joined and counts in `not_joined`: G5 and T1 always do, as exp_06 keeps its answers in a
     results file outside the sink (experiments/scorers/records.py:15-16). Judge logs carry no ctx_uid, so a main judge's
     key v2.4 call on one of the 132 questions key v2.5 changed is the named group judge_v24_replaced_by_v25, counted in
     `replaced`, once the matching S6 out holds an ok main-judge line for the same unit, question, draw and variant. A
     running S6 set replaces only what it has judged, and S512 can defer (b).
  6. Unit rechecks count, in the run tier, failed ones included. Reference claims count. S508's 59 calls count (49 and
     10 rechecks): they feed Figure 2 (S508_judge_49_v25.py:3-5).
  7. Checks and smokes get their own rows, outside the total. So do nemotron (D116), deepseek-r1:70b and
     glm-4.7-flash:bf16 (D265), with the code judge's calls on their answers (DROPPED_RUNS). The second judge's (b) repeat
     check, out_second_repeat_b/<unit>/ (RUNNING.md:1828), and S440's ledgers are checks.
  8. April and pre-lock work stays out. 37,449 is the April evaluation count (S13), not a call count.

TWO MODES.
  collect --machine <studio|beelink|laptop> --out <json>   (run ON a machine; standard library only)
      Send it by stdin, never with -c, so no clone name reaches a command line:
          ssh <host> 'python3 - collect --machine studio --out ~/s520_studio.json' < scripts/S520_llm_calls.py
      Walks <clone>/findings of each clone named in MACHINES (relative to $HOME). It starts no process and writes only
      --out, through a .tmp beside it. It prunes the protected folders (PRUNE_DIR) without listing them, and opens only files that KIND_RULES names.
      A file with a call-log name that no rule names is listed by path and size and never opened. Each line is read as
      bytes: TOKEN walks the line and skips every string without decoding it, and only the keys in WANT at the top level
      are decoded. A judge line's `answer` field holds the answer key (judge_passages.py:391), of which only the question
      and draw are kept. Answer text and scores are never decoded or kept. Each line's blake2b-64 hash goes into the output
      for the duplicate check. A last line with no newline that does not close is flagged and not counted, so a file being
      appended is safe.
  report --in <json> [<json> ...] --out-dir findings/recompute/S520_llm_calls
      Reproduces first (below), then joins the machines. A line's hash seen in an earlier source is a duplicate and is
      dropped, sources in tier order, so a run log beats a mirror; `copy` sources never count, and lines found only in a
      copy are reported. Writes table.csv, summary.json and summary.md. A machine with no input is named as not read.

REPRODUCE FIRST (README.md:75-79). `report` refuses (exit 2, nothing written) unless, on this laptop:
  K1 rows    the laptop K1 log's lines for the 86 answers of the committed rows
             (findings/recompute/fig5_inputs/k1/laptop/ragchecker/ragchecker.jsonl) equal those rows' `calls` sum, 72,845;
             the whole log equals the sum over the worker's current rows.
  K1 claims  K1/reference_claims/calls.jsonl holds 96 calls, 96 ok (experiments/RUNNING.md:659).
  S440       the laptop ledger B7_judge_passages/check_laptop/check_calls.jsonl holds 107 calls (experiments/README.md:84).
  I2         in each of the six sinks the kept calls equal the sum of `llm_calls` on the answers' last lines, 398 in all.
  G1, G2     on the frozen mirror, `llm_calls` of single_pass and matched_budget equal the committed calls_lines of
             findings/figures_provisional/supp_fig17_outcomes/records_manifest.json (405 each); on the other strategies the sum is
             not above calls_lines, because lines of replaced answers stay in the log.
  Join       over the ten G6 sinks and the six I2 sinks, 59,340 lines, 57,573 kept, 1,767 replaced (an independent
             json.loads join, 1 November).
  G6         calls.jsonl of caps 5, 10, 20 have the sha256 of the committed members/g6_calls_after_d135.sha256; every line
             of discarded_D89/calls.jsonl.before_rerun is in calls.jsonl (freeze_g6_d135.py step 2: the reruns only append);
             kept plus replaced equals lines.
  Scanner    on non-blinded files, the byte scanner's tallies equal json.loads tallies, field by field.
Then, for each machine's input that is given (a difference refuses):
  G2's Studio log has 405 lines; each G1 log has at least its calls_lines; the K1 Studio worker that ended on 26 October
  has 48,560 RAGChecker lines (experiments/RUNNING.md:1377); each K1 worker's log has at least the committed rows' `calls`
  sum.

REPORT FROM TRACKED FILES (tracked-scripts audit, row 5). Collect reads live clones, so a later collect gives other counts,
and the laptop gates read files outside the repository. Two more steps tie the report to tracked files:
  freeze --in <the collects> --summary <its summary.json> --dest <folder>   (once, on the laptop)
      Copies the collects as s520_<machine>.json, writes laptop_gates.json (the results of the gates that need this laptop,
      as the committed summary records them, with that summary's total) and SHA256SUMS over them. Refused unless each
      collect's read times equal the summary's, and the summary's other gates, run again on these collects, give the same
      results. These files hold counts, file paths, sizes and times, and per call file its groups of calls with an 8-byte
      hash per line. A group is the status, the model and the fields SIG names for that log (role, call site, variant,
      stage, and on a judge log the question and the draw). T2's and the second judge's calls are in them too, with these
      fields. Collect decodes no answer text and no score.
  report --frozen [--out-dir DIR]   (on any machine)
      Reads those files, each held to SHA256SUMS, an extra or missing file refused. Takes the laptop gates' results from
      laptop_gates.json and runs the machine gates again. Refuses unless the total equals the frozen total, so a change
      to the join fails here. Writes each input's sha256 into the provenance, and no date or commit, so one set of inputs gives
      one set of bytes (bar this script's own sha256). The counting rule is unchanged, bar DROPPED_RUNS: it first builds
      under FROZEN_RULE_DROPS and refuses unless that equals the frozen total, then builds under every drop (D265).

Offline test (a fake tree): uv run --frozen python scripts/S520_llm_calls_test.py
"""
import argparse
import base64
import csv
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone

SCHEMA = 1
LIVE_WINDOW_S = 1800                      # a log written within 30 minutes of the read counts as running

# ---------------------------------------------------------------------------------------------------------------
# The named roots, relative to $HOME. A clone name that carries a port is built from two strings, as S473:176-178 does,
# so the literal never sits in a text that could reach a command line (the busy guards, RUNNING.md:641, :678).
# ---------------------------------------------------------------------------------------------------------------
P = "projects/"
MACHINES = {
    "studio": [P + "mentori-runs", P + "mentori-runs-g3", P + "mentori-runs-g4", P + "mentori-runs-g5",
               P + "mentori-runs-g10", P + "mentori-runs-t1", P + "mentori-runs-t2", P + "mentori-runs-t2g",
               P + "mentori-runs-t2-gemma3-27b", P + "mentori-runs-t2-qwen3-coder-30b", P + "mentori-runs-s2",
               P + "mentori-runs-s2-d75", P + "mentori-runs-s3", P + "mentori-runs-s3-g4", P + "mentori-runs-s3-g6",
               P + "mentori-runs-s3-t2", P + "mentori-runs-s3-t2g", P + "mentori-runs-s6", P + "mentori-runs-s6g7",
               P + "mentori-runs-s18f", P + "mentori-runs-q152", P + "mentori-runs-k1",
               P + "mentori-runs-k1-1145" + "6", P + "mentori-runs-k1-1145" + "1"],
    "beelink": [P + "mentori-runs", P + "mentori-runs-k1-1143" + "5", P + "mentori-runs-k1-q7",
                P + "mentori-runs-s3-t2-second", P + "mentori-runs-s6-second"],
    "laptop": [P + "Mentori-reanalysis", P + "mentori-runs-k1", P + "mentori-runs-s2-laptop",
               P + "mentori-runs-s2-laptop-d75", P + "mentori-runs-s3-t2g-laptop", P + "mentori-runs-s6",
               P + "mentori-runs-joint-test"],
}
MACHINE_ORDER = ["studio", "beelink", "laptop"]
REPO_CLONE = "Mentori-reanalysis"

# Protected folders: never entered, never listed (the run's hard rules). Bulk folders hold no call log.
PRUNE_DIR = re.compile(r"^(S354|S500|S501|S510|S517)|human_eval|rater_packets|internal_review|concept_match_labels")
BULK_DIR = {"blobs", "traces", "docker_ws", "__pycache__", ".git", ".venv", "node_modules"}

CALL_NAME = re.compile(r"calls[^/]*\.json(l)?(\.[a-z_0-9]+)?$")
OTHER_LOG_NAMES = {"results.jsonl", "S454_resend.jsonl",      # logs of one call a line with another name
                   "S440_judge_lock_check.jsonl", "S440_judge_lock_check_beelink.jsonl",
                   "S440_judge_lock_check_laptop.jsonl"}      # S440's ledgers: 214 + 107 + 107 = 428 lines, one call a line

# rel path under <clone>/findings, in order: the first match gives the kind. Only these files are opened.
KIND_RULES = [
    (r"^runs/[^/]+/discarded_[^/]+/(calls\.jsonl\.before_rerun|removed_calls\.jsonl)$", "copy"),
    (r"^recompute/frozen_inputs/extracted/(g6_calls_[^/]+|s2_length_retries_\d+)/.*calls\.jsonl$", "copy"),
    (r"^runs/[^/]+/calls\.jsonl$", "sink"),
    (r"^recompute/G4_runs/g4r38_sinks/[^/]+/calls\.jsonl$", "sink"),
    (r"^recompute/I2_runs/(sinks|smoke_sinks)/[^/]+/calls\.jsonl$", "sink"),
    (r"^recompute/S2_launch_laptop/discarded_16oct/[^/]+/calls\.jsonl$", "sink"),
    (r"^recompute/[A-Z][A-Za-z0-9]*_runs/[^/]*smoke[^/]*/([^/]+/)*calls\.jsonl$", "sink"),
    (r"^recompute/S3_runs/out_second_repeat_b/([^/]+/)+[a-z_]*calls\.jsonl$", "judge"),
    (r"^recompute/S3_runs/out[^/]*/judge/[^/]+/judge_[a-z_]*calls\.jsonl$", "judge"),
    (r"^recompute/S3_runs/out[^/]*/check[^/]*/check_calls\.jsonl$", "judge"),
    (r"^recompute/I2_runs/judge(_check)?/[a-z_]*calls\.jsonl$", "judge"),
    (r"^recompute/S18f_runs/out/.*calls\.jsonl$", "judge"),
    (r"^recompute/B7_judge_passages/[^/]+/[a-z_]*calls\.jsonl$", "judge"),
    (r"^recompute/(S508_judge_49_v25|S512_s6_v25)/[a-z_]*calls\.jsonl$", "judge"),
    (r"^recompute/S495_t2_judge_code_proof/[^/]+/calls\.jsonl$", "judge"),
    (r"^recompute/S440_judge_lock_check(_[a-z0-9]+)?\.jsonl$", "ledger"),
    (r"^recompute/S483_d85_check/.*calls\.jsonl$", "judge"),
    (r"^recompute/K1/[^/]+/ragchecker(_archived_q190_[^/]+)?/ragchecker_calls\.jsonl$", "ragchecker"),
    (r"^recompute/K1/[^/]+/ragas(_archived[^/]*)?/ragas_calls\.jsonl$", "ragas"),
    (r"^recompute/K1/reference_claims/calls\.jsonl$", "ragchecker"),
    (r"^recompute/K1/joint_test/[a-z]+_calls\.jsonl$", "ragchecker"),
    (r"^recompute/(K0|R0[^/]*)/.*ragchecker_calls\.jsonl$", "ragchecker"),
    (r"^recompute/(K0|R0[^/]*)/.*ragas_calls\.jsonl$", "ragas"),
    (r"^recompute/S357/arm_[a-z_0-9]+/calls\.jsonl$", "plain"),
    (r"^recompute/Q152_verifier_ports/results\.jsonl$", "plain"),
    (r"^recompute/Q145/S454_resend\.jsonl$", "resend"),
]
KIND_RULES = [(re.compile(rx), k) for rx, k in KIND_RULES]

# Call-log names that stay out on purpose, not opened. (rel regex, reason)
KNOWN_OUT = [
    (r"^recompute/(S141_|S18e|S373|S388|archive_|AUDIT_|round3_evidence|S362_|S404)", "April or pre-lock work (rule 8)"),
    (r"^recompute/(fig[0-9a-z_]*_inputs|frozen_inputs|answer_lengths|g9_inputs|g6_d135_inputs|supp_fig[0-9a-z_]*_inputs"
     r"|L2_inputs|upstream_inputs|fig5_1028_inputs|findings_review)", "a copy of records another source holds"),
    (r"^recompute/B4_runs/d89_before_rerun_", "a copy of G6's records before the D89 reruns"),
    (r"^runs/[^/]+/(discarded_|REMOVED_)", "a copy inside a sink"),
    (r"^recompute/S2_launch(_laptop)?/.*\.guard\.json$", "a guard record, not a call log"),
]
KNOWN_OUT = [(re.compile(rx), why) for rx, why in KNOWN_OUT]

WANT = {"sink": (b"status", b"model", b"role", b"call_site", b"ctx_uid", b"run_draw", b"retry"),
        "judge": (b"status", b"model", b"variant", b"attempt", b"answer"),
        "ragchecker": (b"status", b"model", b"stage"),
        "ragas": (b"status", b"model", b"endpoint"),
        "plain": (b"status", b"model"),
        "ledger": (b"status", b"judge", b"pass"),
        "resend": ()}
NESTED = {"sink": (b"b4",), "resend": (b"resend",)}          # whole-object values, read only for one short key
SIG = {"sink": ("status", "model", "role", "call_site", "run_draw", "retry", "b4_call", "state"),
       "judge": ("status", "model", "variant", "attempt", "question", "draw"),
       "ragchecker": ("status", "model", "stage"),
       "ragas": ("status", "model", "endpoint"),
       "plain": ("status", "model"),
       "ledger": ("status", "model", "variant"),
       "resend": ("status", "model")}

# A JSON string, unrolled so it cannot backtrack badly, with an optional colon: a key. Then brackets.
STRING = re.compile(rb'"[^"\\]*(?:\\.[^"\\]*)*"', re.S)
TOKEN = re.compile(rb'"[^"\\]*(?:\\.[^"\\]*)*"(\s*:)?|[\[{\]}]', re.S)
SCALAR = re.compile(rb"\s*(-?\d+(?:\.\d+)?|true|false|null)")
SAFE = re.compile(r"^[\w.:/+@ ()\-,|]{0,200}$")
KEY_PARTS = re.compile(r"^[^|\s]{1,200}(?:\|[^|\s]{1,200}){1,6}$")
QUESTION = re.compile(r"^[\w.\-]{1,80}$")
LLM_CALLS = re.compile(rb'"llm_calls"\s*:\s*(\d+)')
ANSWER_KEY_ANY = re.compile(rb'"answer_key"\s*:\s*"')
CTX_ANY = re.compile(rb'"ctx_uid"\s*:\s*"([0-9A-Za-z_\-]{1,64})"')


def top_fields(line, wanted, nested=()):
    """The top-level values of `wanted` (bytes keys) in one JSON object line, decoded only for those keys, and the raw
    bytes of each key in `nested`. Every other string is skipped undecoded, so a key's name inside answer text (its
    quotes are escaped) or in a nested object is not read. ValueError when the line does not close."""
    if not line.startswith(b"{"):
        raise ValueError("not an object")
    depth, out, open_key, open_at = 0, {}, None, 0
    for m in TOKEN.finditer(line):
        c = line[m.start()]
        if c == 0x22:
            if depth == 1 and m.group(1):
                t = m.group()
                name = t[1:t.rfind(b'"')]
                if name in wanted:
                    out[name] = value_at(line, m.end())
                elif name in nested and line[m.end():m.end() + 2].lstrip()[:1] == b"{":
                    open_key, open_at = name, m.end()
        elif c == 0x7b or c == 0x5b:
            depth += 1
        else:
            depth -= 1
            if depth == 1 and open_key is not None:
                out[open_key] = line[open_at:m.end()].lstrip()
                open_key = None
    if depth != 0:
        raise ValueError("unbalanced")
    return out


def value_at(line, pos):
    """A scalar value at `pos`: a string, a number, or true, false, null. An object or a list reads as None."""
    while pos < len(line) and line[pos] in b" \t":
        pos += 1
    if pos >= len(line):
        return None
    if line[pos] == 0x22:
        m = STRING.match(line, pos)
        if not m or m.end() - pos > 400:          # a wanted field is short; a long value is not a label
            return None
        return json.loads(m.group().decode("utf-8", "replace"))
    m = SCALAR.match(line, pos)
    if not m:
        return None
    t = m.group(1)
    if t in (b"true", b"false", b"null"):
        return {b"true": True, b"false": False, b"null": None}[t]
    return float(t) if b"." in t else int(t)


def clean(v):
    """A label kept in the output: a short safe string or a number. Anything else reads '?'."""
    if v is None or isinstance(v, (bool, int, float)):
        return v
    return v if isinstance(v, str) and SAFE.match(v) else "?"


def site_of(v):
    """A call_site with its line number and function dropped: 'backend/retrieval/chunk_verifier.py:200 verify' gives the path."""
    return clean(re.split(r":\d", v)[0].strip()) if isinstance(v, str) else None


def question_draw(key):
    """(question, draw) from a judge line's answer key; nothing from a value that is not a key."""
    if not isinstance(key, str) or not KEY_PARTS.match(key):
        return None, None
    parts = key.split("|")
    d = parts[-1]
    if not re.match(r"^d\d{1,3}$", d) or not QUESTION.match(parts[-2]):
        return None, None
    return parts[-2], int(d[1:])


def scan_answers(sink_dir):
    """What calls need from a sink's answers file, keeping no answer text: the ctx_uids on each key's last line, those on
    earlier lines, answers per draw, and the sum of `llm_calls` on last lines. answers.json (exp_03, exp_05) is rewritten
    in place, so it holds last entries only."""
    jl, js = os.path.join(sink_dir, "answers.jsonl"), os.path.join(sink_dir, "answers.json")
    res = {"kept": set(), "earlier": set(), "keys": 0, "by_draw": Counter(), "llm_calls": None, "source": None,
           "lines": 0}
    if os.path.exists(jl):
        res["source"] = "answers.jsonl"
        last = {}
        with open(jl, "rb") as fh:
            for raw in fh:
                if not raw.endswith(b"\n"):
                    continue
                res["lines"] += 1
                try:
                    f = top_fields(raw.rstrip(), (b"answer_key", b"ctx_uid"))
                except ValueError:
                    continue
                k, u = f.get(b"answer_key"), f.get(b"ctx_uid")
                if k is None:
                    continue
                m = LLM_CALLS.search(raw)
                prev = last.get(k)
                if prev is not None and prev[0] is not None and prev[0] != u:
                    res["earlier"].add(prev[0])
                last[k] = (u, int(m.group(1)) if m else None)
        res["keys"] = len(last)
        res["kept"] = {v[0] for v in last.values() if v[0] is not None}
        res["earlier"] -= res["kept"]
        for k in last:
            m = re.search(r"\|d(\d+)$", k)
            res["by_draw"][int(m.group(1)) if m else 0] += 1
        have = [v[1] for v in last.values() if v[1] is not None]
        res["llm_calls"] = sum(have) if have else None
    elif os.path.exists(js):
        res["source"] = "answers.json"
        with open(js, "rb") as fh:
            blob = fh.read()
        res["kept"] = {m.decode() for m in CTX_ANY.findall(blob)}
        res["keys"] = len(ANSWER_KEY_ANY.findall(blob))
    return res


def line_hash(line):
    return hashlib.blake2b(line, digest_size=8).digest()


def scan_calls(path, kind, ans=None):
    """Streams one call log, whole lines only. Returns the file's counts and {signature: bytearray of 8-byte hashes}. A
    line that does not close is counted as bad, and a last line with no newline that does not close only sets the flag."""
    want, nested = WANT[kind], NESTED.get(kind, ())
    keys = SIG[kind]
    groups, lines, bad, partial = {}, 0, 0, False
    with open(path, "rb") as fh:
        for raw in fh:
            line = raw.rstrip(b"\r\n")
            if not line:
                continue
            try:
                f = top_fields(line, want, nested)
                if not line.endswith(b"}"):
                    raise ValueError("no close")
            except ValueError:
                if raw.endswith(b"\n"):
                    bad += 1
                else:
                    partial = True
                continue
            v = {"status": clean(f.get(b"status")), "model": clean(f.get(b"model"))}
            if kind == "sink":
                b4 = f.get(b"b4")
                call = None
                if b4:
                    try:
                        call = clean(top_fields(b4, (b"call",)).get(b"call"))
                    except ValueError:
                        call = "?"
                u = f.get(b"ctx_uid")
                state = "noctx" if u is None else ("noanswers" if ans is None or ans["source"] is None else
                                                   "kept" if u in ans["kept"] else
                                                   "replaced" if u in ans["earlier"] else "none")
                r = f.get(b"retry")
                v.update(role=clean(f.get(b"role")), call_site=site_of(f.get(b"call_site")),
                         run_draw=clean(f.get(b"run_draw")), retry=bool(r), b4_call=call, state=state)
            elif kind == "judge":
                q, d = question_draw(f.get(b"answer"))
                v.update(variant=clean(f.get(b"variant")), attempt=clean(f.get(b"attempt")), question=q, draw=d)
            elif kind == "ragchecker":
                v["stage"] = clean(f.get(b"stage"))
            elif kind == "ragas":
                v["endpoint"] = clean(f.get(b"endpoint"))
            elif kind == "ledger":                     # S440: the model is `judge`, the pass is its only variant
                v.update(model=clean(f.get(b"judge")), variant=clean(f.get(b"pass")))
            elif kind == "resend":
                inner = {}
                try:
                    inner = top_fields(f.get(b"resend") or b"{}", (b"status", b"model"))
                except ValueError:
                    pass
                v = {"status": clean(inner.get(b"status")), "model": clean(inner.get(b"model"))}
            sig = tuple(v.get(k) for k in keys)
            groups.setdefault(sig, bytearray()).extend(line_hash(line))
            lines += 1
    return {"lines": lines, "bad_lines": bad, "bad_last_line": partial}, groups


def rule_of(rel):
    """(kind, None) for a file to open; (None, reason) for a known file left out; (None, None) for an unmapped one."""
    for rx, kind in KIND_RULES:
        if rx.search(rel):
            return kind, None
    for rx, why in KNOWN_OUT:
        if rx.search(rel):
            return None, why
    return None, None


def table_sha():
    """Ties an input to the tables that collected it, so report refuses an input from another version of them."""
    blob = repr((SCHEMA, sorted(MACHINES.items()), [(r.pattern, k) for r, k in KIND_RULES],
                 sorted((k, v) for k, v in WANT.items()), sorted((k, v) for k, v in SIG.items())))
    return hashlib.sha256(blob.encode()).hexdigest()


def sink_key(clone, rel):
    return clone + "/" + rel.rsplit("/", 1)[0]


def collect_clone(home, clone_rel, now, out):
    """One clone's records into `out`. Reads only what rule_of names."""
    root = os.path.join(home, clone_rel, "findings")
    clone = os.path.basename(clone_rel)
    if not os.path.isdir(root):
        out["missing_roots"].append(clone_rel)
        return
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in BULK_DIR and not PRUNE_DIR.search(d))
        rel_dir = os.path.relpath(dirpath, root).replace(os.sep, "/")
        for name in sorted(filenames):
            if PRUNE_DIR.search(name) or not (CALL_NAME.search(name) or name in OTHER_LOG_NAMES):
                continue
            rel = name if rel_dir == "." else rel_dir + "/" + name
            kind, why = rule_of(rel)
            if kind is None and why is None and name in OTHER_LOG_NAMES:
                continue
            path = os.path.join(dirpath, name)
            try:
                st = os.stat(path)
            except OSError:
                continue
            if why is not None:
                out["known_out"][why] += 1
                continue
            if kind is None:
                out["unmapped"].append({"clone": clone, "path": rel, "size": st.st_size})
                continue
            scan_kind = kind
            ans = None
            if kind == "copy":
                scan_kind = "plain"
            if kind == "sink":
                try:
                    ans = scan_answers(dirpath)
                except OSError:
                    ans = None
                if ans is not None:
                    out["sinks"][sink_key(clone, rel)] = {"keys": ans["keys"], "lines": ans["lines"],
                                                          "by_draw": {str(k): v for k, v in ans["by_draw"].items()},
                                                          "llm_calls": ans["llm_calls"], "source": ans["source"]}
            try:
                info, groups = scan_calls(path, scan_kind, ans)
            except OSError as e:
                out["unreadable"].append({"clone": clone, "path": rel, "error": type(e).__name__})
                continue
            entry = {"clone": clone, "path": rel, "kind": kind, "scan_kind": scan_kind, "size": st.st_size,
                     "mtime": int(st.st_mtime), "age_s": int(now - st.st_mtime), "groups": []}
            entry.update(info)
            if kind == "ragchecker" and name == "ragchecker_calls.jsonl":
                entry["rows"] = k1_rows(os.path.join(dirpath, "ragchecker.jsonl"))
            for sig, hashes in groups.items():
                entry["groups"].append({"k": list(sig), "n": len(hashes) // 8,
                                        "h": base64.b64encode(bytes(hashes)).decode("ascii")})
            out["files"].append(entry)


def k1_rows(path):
    """A K1 worker's rows: how many, and the sum of each row's top-level `calls` (an integer). Nothing else is decoded."""
    if not os.path.exists(path):
        return None
    n, s = 0, 0
    with open(path, "rb") as fh:
        for raw in fh:
            if not raw.endswith(b"\n"):
                continue
            try:
                f = top_fields(raw.rstrip(), (b"calls",))
            except ValueError:
                continue
            n += 1
            c = f.get(b"calls")
            s += c if isinstance(c, int) and not isinstance(c, bool) else 0
    return {"rows": n, "calls_sum": s}


def collect(machine, out_path, home=None):
    home = home or os.path.expanduser("~")
    try:
        os.nice(10)                       # the machines are running jobs; this read yields to them
    except OSError:
        pass
    now = time.time()
    out = {"schema": SCHEMA, "table_sha256": table_sha(), "machine": machine, "host": socket.gethostname(),
           "started_utc": datetime.fromtimestamp(now, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "files": [],
           "sinks": {}, "unmapped": [], "unreadable": [], "missing_roots": [], "known_out": Counter(),
           "clones_not_in_table": []}
    for clone_rel in MACHINES[machine]:
        collect_clone(home, clone_rel, now, out)
    known = {os.path.basename(c) for c in MACHINES[machine]}
    try:
        names = os.listdir(os.path.join(home, "projects"))
    except OSError:
        names = []
    out["clones_not_in_table"] = sorted(n for n in names if n.startswith("mentori-runs") and n not in known)
    out["known_out"] = dict(out["known_out"])
    out["ended_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    tmp = out_path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(out, fh)
    os.replace(tmp, out_path)
    print("collected %s: %d files, %d lines, %d unmapped, %d bad last lines" % (
        machine, len(out["files"]), sum(f["lines"] for f in out["files"]), len(out["unmapped"]),
        sum(1 for f in out["files"] if f["bad_last_line"])))


# ---------------------------------------------------------------------------------------------------------------
# Report: what each source is.
# ---------------------------------------------------------------------------------------------------------------
NO_BOX = "not in a box"
EXPERIMENTS = {  # id: (draws.csv name, S1 box in S496:107-115; G10, G11 and S508's 49 answers have none)
    "G1": ("Generation strategies", "G1"), "G2": ("Matched-budget arm", "G2"),
    "G3A": ("Pipeline ablation", "G3A"), "G3B": ("No retrieval and naive RAG", "G3B"),
    "G9": ("Distiller on every step (stress)", "G9"), "G4": ("Corpus scaling", "G4"),
    "G5": ("Retrieval depth", "G5"), "G6C": ("Package RLM at caps 5 10 20", "G6C"),
    "G6D": ("Package RLM depth caps", "G6D"), "T1": ("Retrieval depth, local models", "T1"),
    "T2": ("Strategy replication", "T2"), "S2": ("Code generation", "S2"),
    "I2": ("Plant-science reuse demonstration", "I2"), "G10": ("Flat wide call", NO_BOX),
    "G11": ("Short-passage single pass", NO_BOX), "R49": ("Judge on the 49 rated answers", NO_BOX),
    "CHECK": ("Checks and calibrations", ""), "UNMAPPED": ("Not mapped to an experiment", "")}
S1_READS = {"RO": "kept from April", "MS": "kept from April", "T3C": 0, "T3D": 0}   # block 1.2: T3 has not started
OUT_SET = {"out": "G1", "out_g1r15": "G1", "out_g2": "G2", "out_g6": "G6", "out_g3": "G3", "out_g4": "G4",
           "out_g4r38": "G4", "out_g5": "G5", "out_g9": "G9", "out_t2": "T2", "out_t2g": "T2",
           "out_t2lgemma": "T2", "out_t2lqcoder": "T2"}   # S482_progress_counts.py:101-103
S6_OF = {"out": ("out_s6_g1", "out_s6_g1r15"), "out_g1r15": ("out_s6_g1", "out_s6_g1r15"), "out_g2": ("out_s6_g2",),
         "out_g3": ("out_s6_g3",), "out_g4": ("out_s6_g4", "out_s6_g4r38"), "out_g4r38": ("out_s6_g4", "out_s6_g4r38"),
         "out_g5": ("out_s6_g5",), "out_g6": ("out_s6_g6",), "out_t2": ("out_s6_t2",), "out_t2g": ("out_s6_t2g",)}
# S482:108-109, S6_OUT: a v2.4 out and the S6 outs of its set; T2LGEMMA and T2LQCODER have no S6 set (S482:33)
REPEAT_B_OUT = "out_second_repeat_b"      # the second judge's (b) repeat check, RUNNING.md:1828
NEW_SET_OUT = re.compile(r"(?:^|_)(g1[01])(?:_|$)")   # G10's and G11's judge outs: their folders are not built yet (D196)
EXP06 = ("G5", "T1")                      # their answers sit outside the sink
EXP06_NOTE = "exp_06 keeps answers in a results file outside the sink (records.py:15-16)"
# The S2 runs dropped by decision, by the model tag in the sink's name, each with its decision: their calls (the code
# judge's on their answers included) leave the total, by_model and the boxes for the dropped tier (rule 7).
DROPPED_RUNS = {"nemotron": "D116", "deepseek-r1-70b": "D265", "glm-4.7-flash": "D265"}
# D265 (rulings page 6 Nov, I19: O1): deepseek-r1:70b and glm-4.7-flash:bf16 appear in no reported experiment.
FROZEN_RULE_DROPS = ("nemotron", "deepseek-r1-70b", "glm-4.7-flash")   # the drops in force when the inputs were frozen
# (laptop_gates.json's total): 7 Nov, after G5 D284, with D265's two drops in force; ("nemotron",) for the 6 Nov inputs
_drops = tuple(DROPPED_RUNS)        # the drops classify applies; report --frozen narrows it once, to reproduce first
TIER_RANK = {"run": 0, "dropped": 1, "check": 2, "smoke": 3, "unmapped": 4, "copy": 5}
GENERATION = ("generator", "RLM root", "RLM sub-call", "verifier", "orchestrator component", "code generation")
SCORER_ROLES = ("RAGAS", "RAGChecker extract", "RAGChecker check")
SECOND_JUDGE_MODEL = "qwen3.8:27b"        # LOCK.toml [judge] second_model
PLANNED = [
    {"job": "G10 flat wide call", "experiment": "G10", "due": 585, "unit": "answers",
     "source": "experiments/draws.csv row Flat wide call"},
    {"job": "G11 short-passage single pass", "experiment": "G11", "due": 225, "unit": "answers",
     "source": "experiments/draws.csv row Short-passage single pass"},
    {"job": "T2 four generators", "experiment": "T2", "due": 7020, "unit": "answers",
     "source": "experiments/draws.csv row Strategy replication (D178); D197 paused the local multi_hop, rlm_5 and rlm_20, "
               "and whether they resume is open, so this due can fall"},
    {"job": "G7 judging on G4 and G3", "outs": ("out_s6_g7_g4", "out_s6_g7_g3"), "due": 7153, "unit": "judged answers",
     "source": "experiments/RUNNING.md:146 (dry runs: S6G7G4 6,433, S6G7G3 720); D198 O2 and D199 keep phase 2 on these "
               "two sets, so S6G7G5 is left out"},
    {"job": "S6 on G4", "outs": ("out_s6_g4",), "due": 5574, "unit": "judged answers",
     "source": "experiments/RUNNING.md:137"},
]
NOT_PLANNED = [("T3 component benchmarks and distiller prompts",
                "not started; draws.csv holds no call or answer count for it (D198 O7: the 59-hour core)"),
               ("Second judge outside 3f, 5e and S14", "held by D198 O4 (2,025 calls)"),
               ("S4 gpt-oss-20b high", "its end is UNVERIFIED; its calls fall in S2's sinks")]


def exp_of_run(run):
    """The experiment of a run or judge-unit folder name; None when the name is not one of the study's."""
    if run.startswith("exp_01__"):
        if "+" in run:
            return "T2"
        if "single_pass_cut800" in run:
            return "G11"
        return "G2" if "matched_budget" in run else "G1"
    if run.startswith("exp_02_scaling_factorial__"):
        return "G4"
    if run.startswith("exp_03__"):
        if "__naive_rag__" in run or "__raw_gemini__" in run:
            return "G3B"
        return "G9" if "distil_every_step" in run else "G3A"
    if run.startswith("exp_06_depth_sweep__"):
        return "T1" if "percategory15" in run else "G5"
    if run.startswith("b4_rlm_ref__"):
        return "G6C" if "__all135" in run else "G6D"
    if run.startswith("exp_05__"):
        return "S2"
    return None


def exp_in_clone(clone, run):
    """exp_of_run, with G10's own clone: G10 is exp_01's matched_budget arm, so a sink's name alone reads G2."""
    e = exp_of_run(run)
    return "G10" if e == "G2" and clone.startswith("mentori-runs-g10") else e


def classify(clone, rel, kind):
    """{experiment, plan_row, tier, moved, out} of a source, by its clone and path."""
    parts = rel.split("/")
    run = parts[-2] if len(parts) > 1 else ""
    r = {"experiment": "UNMAPPED", "plan_row": "", "tier": "unmapped", "moved": False, "out": None}
    smoke = "smoke" in rel.lower()

    def done(exp, plan, tier="run", **kw):
        r.update(experiment=exp, plan_row=plan, tier=tier, **kw)
        return r

    if kind == "copy":
        for p in parts:
            e = exp_in_clone(clone, p)
            if e:
                return done(e, plan_of(e), "copy")
        return done("UNMAPPED", "", "copy")
    if rel.startswith("recompute/K1/joint_test/") or re.match(r"recompute/(K0|R0)", rel) \
            or rel.startswith("recompute/S357/"):
        return done("CHECK", "K0" if "/K0/" in "/" + rel else "K1" if "joint_test" in rel else "R0", "check")
    if rel.startswith("recompute/K1/"):
        return done("G1", "K1", moved="_archived_" in rel)
    if rel.startswith("recompute/S3_runs/"):
        out = parts[2]
        base = out[:-7] if out.endswith("_second") else out
        if out == REPEAT_B_OUT:
            return done("CHECK", "S3", "check", out=out)
        if parts[3].startswith("check"):
            return done("CHECK", "S6" if "s6" in out else "S3", "check", out=out)
        unit = exp_of_run(parts[4])
        named = NEW_SET_OUT.search(base)
        if named and unit in (None, "G2"):             # a G10 unit is exp_01__matched_budget__*, which alone reads G2
            unit = named.group(1).upper()
        tier = "smoke" if smoke else "run"
        if base.startswith("out_s6_g7_"):
            return done(unit or "UNMAPPED", "G7", tier, out=out)
        if base.startswith("out_s6_"):
            return done("T2" if base.startswith("out_s6_t2") else unit or "UNMAPPED", "S6", tier, out=out)
        if base in OUT_SET or named:
            return done("T2" if OUT_SET.get(base) == "T2" else unit or "UNMAPPED", "S3", tier, out=out)
        return r
    if rel.startswith("recompute/S18f_runs/"):
        return done("CHECK", "S5", "check") if parts[3].startswith("check") else done("G1", "S5")
    if rel.startswith("recompute/I2_runs/"):
        if "judge_check" in rel:
            return done("CHECK", "I2", "check")
        return done("I2", "I2", "smoke" if smoke else "run")
    if rel.startswith("recompute/G4_runs/g4r38_sinks/"):
        return done("G4", "G8", "smoke" if smoke else "run")
    if rel.startswith("recompute/S2_launch_laptop/discarded_16oct/"):
        return done("S2", "S2", moved=True)
    if rel.startswith("recompute/S508_"):
        return done("R49", "S6")
    for prefix, row in (("recompute/B7_judge_passages/", "S3"), ("recompute/S512_", "S6"), ("recompute/S440_", "S3"),
                        ("recompute/S495_", "T2"), ("recompute/S483_", "S3"), ("recompute/Q152_", "G1"),
                        ("recompute/Q145/", "G1")):
        if rel.startswith(prefix):
            return done("CHECK", row, "check")
    if rel.startswith("recompute/") and smoke:
        e = exp_in_clone(clone, run) or "CHECK"
        return done(e, plan_of(e), "smoke")
    if rel.startswith("runs/"):
        e = exp_in_clone(clone, run)
        if e is None:
            return r
        if clone == REPO_CLONE and e == "S2":          # the 143 sinks here: a copy, unless a line is found nowhere else
            return done(e, "S2", "copy")
        tier = "smoke" if smoke else "dropped" if e == "S2" and any(t in run for t in _drops) else "run"
        return done(e, plan_of(e), tier)
    return r


def plan_of(e):
    return {"G3A": "G3", "G3B": "G3", "G6C": "G6", "G6D": "G6"}.get(e, e)


def role_of(kind, rel, v, plan_row):
    """The table's role, from a line's fields."""
    model = v.get("model") or ""
    if kind == "ragas":
        return "RAGAS"
    if kind == "ragchecker":
        if rel.endswith("reference_claims/calls.jsonl"):
            return "RAGChecker extract"
        return "RAGChecker extract" if v.get("stage") == "extract" else "RAGChecker check"
    if kind == "ledger":
        return "judge (a)"                         # S440's calls are the plain call
    if kind == "judge":
        if model == SECOND_JUDGE_MODEL:
            return "second judge"
        if "judge_evidence" in rel:
            return "judge (evidence)"
        va = str(v.get("variant") or "")
        return "judge (%s)" % ("a" if va.startswith("a") else "b" if va.startswith("b") else va or "?")
    if kind == "plain":
        return "verifier" if "Q152" in rel else "generator"
    if kind == "resend":
        return "generator"
    b4 = v.get("b4_call")
    if b4:
        return "RLM sub-call" if b4 == "sub" else "RLM root"
    site, role = v.get("call_site") or "", v.get("role")
    if role == "judge":
        return "code judge" if plan_row == "S2" else "judge (a)"
    if "chunk_verifier" in site:
        return "verifier"
    if "rlm/executor.py" in site:
        return "RLM sub-call"
    if "rlm/orchestrator.py" in site:
        return "RLM root"
    if "agents/orchestrator/" in site:
        return "orchestrator component"
    if "agents/notebook/" in site or plan_row == "S2":
        return "code generation"
    return "generator"


def role_group(role):
    if role in GENERATION:
        return "generation"
    return "RAGAS and RAGChecker" if role in SCORER_ROLES else "judges"


class Book:
    """The join: one pass over the sources in tier order."""

    def __init__(self, changed, rejudged=()):
        self.changed = set(changed)
        self.rejudged = set(rejudged)          # s6_rejudged(): what key v2.5 has judged again
        self.seen = set()
        self.rows = defaultdict(lambda: {"status": Counter(), "replaced": 0, "no_answer_line": 0, "not_joined": 0})
        self.not_calls = Counter()
        self.dups = Counter()
        self.only_copy = Counter()
        self.dup_in_file = 0
        self.v24_group = 0
        self.judged = defaultdict(set)         # (plan row, out): distinct (unit, question, draw), main judge only
        self.out_calls = Counter()             # main judge's calls per out
        self.sites = Counter()

    def add(self, machine, f):
        meta = classify(f["clone"], f["path"], f["kind"])
        kind = f["scan_kind"]
        keys = SIG[kind]
        tier = meta["tier"]
        for g in f["groups"]:
            v = dict(zip(keys, g["k"]))
            raw = base64.b64decode(g["h"])
            new = 0
            in_file = set()
            for i in range(0, len(raw), 8):
                h = raw[i:i + 8]
                if h in self.seen:
                    if h in in_file:
                        self.dup_in_file += 1
                    else:
                        self.dups[(f["clone"], tier)] += 1
                    continue
                self.seen.add(h)
                in_file.add(h)
                new += 1
            if tier == "copy":
                self.only_copy[f["clone"]] += new
                continue
            if not new:
                continue
            if (v.get("endpoint") == "embeddings") or str(v.get("model") or "").startswith("bge-m3"):
                self.not_calls["embeddings lines (bge-m3)"] += new
                continue
            plan_row = meta["plan_row"]
            e = meta["experiment"]
            if kind == "sink" and plan_row in ("G3", "G4", "G5") and e != "G3B" and (v.get("run_draw") or 1) >= 2:
                plan_row = "G7"
            role = role_of(kind, f["path"], v, plan_row)
            if role == "generator" and kind == "sink":
                self.sites[v.get("call_site")] += new
            box = EXPERIMENTS.get(e, ("", ""))[1] if tier == "run" else ""
            key = (e, plan_row, role, v.get("model") or "?", machine, tier, box)
            row = self.rows[key]
            row["status"][v.get("status") or "none"] += new
            state = v.get("state")
            if meta["moved"] or state in ("replaced", "none"):
                row["replaced"] += new
            if state == "none":
                row["no_answer_line"] += new
            elif state in ("noanswers", "noctx"):
                row["not_joined"] += new
            if kind == "judge" and meta["out"] and tier == "run":
                unit = f["path"].split("/")[-2]
                if role != "second judge" and plan_row == "S3" and v.get("question") in self.changed \
                        and any(rejudged_key(o, unit, v) in self.rejudged for o in S6_OF.get(meta["out"], ())):
                    row["replaced"] += new
                    self.v24_group += new
                if role.startswith("judge") and v.get("question"):
                    self.judged[(plan_row, meta["out"])].add((unit, v.get("question"), v.get("draw")))
                    self.out_calls[meta["out"]] += new

    def table(self):
        out = []
        for (e, plan, role, model, machine, tier, box), r in sorted(self.rows.items()):
            ok = r["status"].get("ok", 0)
            failed = {k: v for k, v in r["status"].items() if k != "ok"}
            out.append({"experiment": EXPERIMENTS.get(e, (e, ""))[0], "exp_id": e, "plan_row": plan, "role": role,
                        "model": model, "machine": machine, "calls_ok": ok, "calls_failed": sum(failed.values()),
                        "failed_by_status": ";".join("%s=%d" % kv for kv in sorted(failed.items())),
                        "replaced": r["replaced"], "no_answer_line": r["no_answer_line"],
                        "not_joined": r["not_joined"], "tier": tier, "s1_box": box,
                        "note": EXP06_NOTE if e in EXP06 and r["not_joined"] else ""})
        return out


def sum_by(rows, key):
    out = defaultdict(lambda: {"calls": 0, "ok": 0, "failed": 0, "replaced": 0, "no_answer_line": 0, "not_joined": 0})
    for r in rows:
        k = key(r)
        s = out[k]
        s["calls"] += r["calls_ok"] + r["calls_failed"]
        s["ok"] += r["calls_ok"]
        s["failed"] += r["calls_failed"]
        s["replaced"] += r["replaced"]
        s["no_answer_line"] += r["no_answer_line"]
        s["not_joined"] += r["not_joined"]
    return {k: out[k] for k in sorted(out, key=lambda x: -out[x]["calls"])}


def rejudged_key(out, unit, v):
    """One judge line's answer and call, `a` or `b`, in an S6 out."""
    return out, unit, v.get("question"), v.get("draw"), str(v.get("variant") or "")[:1]


def s6_rejudged(inputs):
    """The answers and calls an S6 out has judged on key v2.5: its ok main-judge lines, in the run tier."""
    outs = {o for group in S6_OF.values() for o in group}
    keys = SIG["judge"]
    found = set()
    for inp in inputs:
        for f in inp["files"]:
            if f["scan_kind"] != "judge":
                continue
            m = classify(f["clone"], f["path"], f["kind"])
            if m["out"] not in outs or m["tier"] != "run":
                continue
            unit = f["path"].split("/")[-2]
            for g in f["groups"]:
                v = dict(zip(keys, g["k"]))
                if v["status"] == "ok" and v["model"] != SECOND_JUDGE_MODEL and v["question"]:
                    found.add(rejudged_key(m["out"], unit, v))
    return found


def planned_left(book, rows, sinks_done):
    """Calls left, about: (due less done) x the calls per done answer so far. No done answers: not known."""
    res = []
    for p in PLANNED:
        if "experiment" in p:
            done = sinks_done.get(p["experiment"], 0)
            sel = [r for r in rows if r["exp_id"] == p["experiment"] and r["tier"] == "run"
                   and role_group(r["role"]) == "generation"]
            calls = sum(r["calls_ok"] + r["calls_failed"] for r in sel)
        else:
            done = sum(len(v) for (_, o), v in book.judged.items() if o in p["outs"])
            calls = sum(book.out_calls[o] for o in p["outs"])
        per = calls / done if done and calls else None
        left = max(p["due"] - done, 0)
        res.append({"job": p["job"], "unit": p["unit"], "due": p["due"], "done": done, "left": left,
                    "calls_per_answer_so_far": round(per, 3) if per else None,
                    "calls_left_about": int(round(left * per)) if per else None, "source": p["source"]})
    return res


def reconcile(inputs):
    """Sinks whose kept call lines differ from the answers' llm_calls sum, and K1 workers whose lines differ from rows."""
    out = {"sinks_checked": 0, "sinks_differ": [], "k1_workers": []}
    for inp in inputs:
        for f in inp["files"]:
            if f["kind"] == "ragchecker" and f.get("rows"):
                out["k1_workers"].append({"machine": inp["machine"], "worker": f["path"].split("/")[2],
                                          "lines": f["lines"], "rows": f["rows"]["rows"],
                                          "rows_calls_sum": f["rows"]["calls_sum"]})
            if f["kind"] != "sink":
                continue
            s = inp["sinks"].get(sink_key(f["clone"], f["path"]))
            if not s or s.get("llm_calls") is None:
                continue
            idx = SIG["sink"].index("state")
            kept = sum(g["n"] for g in f["groups"] if g["k"][idx] == "kept")
            out["sinks_checked"] += 1
            if kept != s["llm_calls"]:
                out["sinks_differ"].append({"machine": inp["machine"], "sink": sink_key(f["clone"], f["path"]),
                                            "kept_lines": kept, "llm_calls": s["llm_calls"]})
    return out


def live_jobs(inputs):
    out = defaultdict(lambda: {"logs": 0, "newest_age_s": None})
    for inp in inputs:
        for f in inp["files"]:
            if f["age_s"] <= LIVE_WINDOW_S:
                m = classify(f["clone"], f["path"], f["kind"])
                if m["tier"] == "copy":
                    continue
                k = (inp["machine"], m["plan_row"] or "?", m["experiment"], m["tier"])
                s = out[k]
                s["logs"] += 1
                s["newest_age_s"] = f["age_s"] if s["newest_age_s"] is None else min(s["newest_age_s"], f["age_s"])
    return [{"machine": k[0], "plan_row": k[1], "experiment": k[2], "tier": k[3], **v} for k, v in sorted(out.items())]


def build(inputs, changed):
    """The join and every grouped number, pure: no file is read or written here."""
    order = []
    for inp in inputs:
        rank_machine = MACHINE_ORDER.index(inp["machine"])
        for f in inp["files"]:
            tier = classify(f["clone"], f["path"], f["kind"])["tier"]
            order.append((TIER_RANK[tier], rank_machine, f["clone"], f["path"], inp["machine"], f))
    order.sort(key=lambda t: t[:4])
    book = Book(changed, s6_rejudged(inputs))
    for *_, machine, f in order:
        book.add(machine, f)
    rows = book.table()
    run = [r for r in rows if r["tier"] == "run"]
    sinks_done = Counter()
    for inp in inputs:
        for key, s in inp["sinks"].items():
            clone, rel = key.split("/", 1)
            m = classify(clone, rel + "/calls.jsonl", "sink")
            if m["tier"] == "run":
                sinks_done[m["experiment"]] += s["keys"]
    total = sum_by(run, lambda r: "all").get("all", {"calls": 0, "ok": 0, "failed": 0, "replaced": 0, "no_answer_line": 0,
                                                     "not_joined": 0})
    fail = Counter()
    for r in run:
        for part in filter(None, r["failed_by_status"].split(";")):
            k, v = part.split("=")
            fail[k] += int(v)
    boxes = {k: v["calls"] for k, v in sum_by([r for r in run if r["s1_box"]], lambda r: r["s1_box"]).items()}
    boxes.update(S1_READS)
    tiers = {t: sum(r["calls_ok"] + r["calls_failed"] for r in rows if r["tier"] == t)
             for t in ("run", "check", "smoke", "dropped", "unmapped")}
    return {
        "rows": rows,
        "summary": {
            "total": dict(total, failed_by_status=dict(sorted(fail.items()))),
            "figure1_legend_total": total["calls"], "tiers": tiers,
            "by_role": sum_by(run, lambda r: r["role"]), "by_model": sum_by(run, lambda r: r["model"]),
            "by_experiment": sum_by(run, lambda r: r["exp_id"]), "by_plan_row": sum_by(run, lambda r: r["plan_row"]),
            "by_machine": sum_by(run, lambda r: r["machine"]), "s1_boxes": boxes,
            "methods_groups": sum_by(run, lambda r: role_group(r["role"])),
            "not_joined_exp06": sum(r["not_joined"] for r in run if r["exp_id"] in EXP06),
            "judge_v24_replaced_by_v25": book.v24_group,
            "not_calls": dict(book.not_calls), "duplicates_removed": sum(book.dups.values()),
            "duplicates_by_clone": {"%s (%s)" % k: v for k, v in sorted(book.dups.items())},
            "duplicate_lines_within_a_file": book.dup_in_file, "lines_found_only_in_copies": dict(book.only_copy),
            "generator_call_sites": {str(k): v for k, v in book.sites.most_common(40)},
            "live": live_jobs(inputs), "planned_left": planned_left(book, rows, sinks_done),
            "not_planned": [{"job": a, "why": b} for a, b in NOT_PLANNED], "reconcile": reconcile(inputs),
            "files": len(order), "lines_read": sum(t[-1]["lines"] for t in order),
            "bad_last_lines": [t[-1]["clone"] + "/" + t[-1]["path"] for t in order if t[-1]["bad_last_line"]],
            "bad_lines": sum(t[-1]["bad_lines"] for t in order),
            "unmapped": [dict(u, machine=i["machine"]) for i in inputs for u in i["unmapped"]],
            "unmapped_opened": ["%s:%s/%s" % (t[4], t[2], t[3]) for t in order if t[0] == TIER_RANK["unmapped"]],
            "clones_not_in_table": {i["machine"]: i["clones_not_in_table"] for i in inputs},
            "missing_roots": {i["machine"]: i["missing_roots"] for i in inputs},
            "known_out": {i["machine"]: i["known_out"] for i in inputs}}}


# ---------------------------------------------------------------------------------------------------------------
# Reproduce first.
# ---------------------------------------------------------------------------------------------------------------
class Gates:
    def __init__(self):
        self.results = []

    def equal(self, name, got, want, source):
        self.results.append({"gate": name, "got": got, "want": want, "source": source, "pass": got == want})

    def at_least(self, name, got, floor, source):
        self.results.append({"gate": name, "got": got, "want": ">= %s" % floor, "source": source, "pass": got >= floor})

    def refuse_on_failure(self):
        bad = [r for r in self.results if not r["pass"]]
        for r in self.results:
            print("  %s %s: %s (want %s) [%s]" % ("PASS" if r["pass"] else "FAIL", r["gate"], r["got"], r["want"],
                                                  r["source"]))
        if bad:
            print("REFUSED: %d of %d gates differ; nothing written" % (len(bad), len(self.results)))
            sys.exit(2)


def _counts(groups, keys, field):
    i = keys.index(field)
    c = Counter()
    for sig, h in groups.items():
        c[sig[i]] += len(h) // 8
    return c


def _lines(groups):
    return sum(len(h) // 8 for h in groups.values())


def reproduce(repo, home):
    """The laptop's gates; the numbers come from the same scan_calls and scan_answers that collect runs."""
    g = Gates()
    F = os.path.join(repo, "findings")
    k1 = os.path.join(home, "projects/mentori-runs-k1/findings/recompute/K1/laptop/ragchecker")
    log = os.path.join(k1, "ragchecker_calls.jsonl")
    committed = os.path.join(F, "recompute/fig5_inputs/k1/laptop/ragchecker/ragchecker.jsonl")
    keys, want = set(), 0
    with open(committed, "rb") as fh:
        for raw in fh:
            f = top_fields(raw.rstrip(), (b"run_id", b"answer_key", b"calls"))
            keys.add("%s|%s" % (f[b"run_id"], f[b"answer_key"]))
            want += f.get(b"calls") or 0
    got = 0
    with open(log, "rb") as fh:
        for raw in fh:
            if top_fields(raw.rstrip(), (b"answer",)).get(b"answer") in keys:
                got += 1
    g.equal("K1 laptop log, the 86 committed answers", got, want, "fig5_inputs/k1/laptop rows, sum of calls")
    g.equal("K1 committed sum", want, 72845, "same file")
    _, groups = scan_calls(log, "ragchecker")
    rows = k1_rows(os.path.join(k1, "ragchecker.jsonl"))
    g.equal("K1 laptop log, whole file", _lines(groups), rows["calls_sum"], "worker's current rows, sum of calls")

    info, groups = scan_calls(os.path.join(F, "recompute/K1/reference_claims/calls.jsonl"), "ragchecker")
    g.equal("K1 reference claims calls", info["lines"], 96, "RUNNING.md:659")
    g.equal("K1 reference claims ok", _counts(groups, SIG["ragchecker"], "status")["ok"], 96, "RUNNING.md:659")
    info, _ = scan_calls(os.path.join(F, "recompute/B7_judge_passages/check_laptop/check_calls.jsonl"), "judge")
    g.equal("S440 laptop ledger", info["lines"], 107, "experiments/README.md:84")

    total = 0
    for sink in sorted(os.listdir(os.path.join(F, "recompute/I2_runs/sinks"))):
        d = os.path.join(F, "recompute/I2_runs/sinks", sink)
        ans = scan_answers(d)
        _, groups = scan_calls(os.path.join(d, "calls.jsonl"), "sink", ans)
        kept = _counts(groups, SIG["sink"], "state")["kept"]
        g.equal("I2 " + sink.split("__")[1], kept, ans["llm_calls"], "answers' llm_calls, last lines")
        total += kept
    g.equal("I2 total", total, 398, "the six sinks, 1 November")

    manifest = json.load(open(os.path.join(F, "figures_provisional/supp_fig17_outcomes/records_manifest.json")))["exp01"]
    mirror = os.path.join(F, "recompute/frozen_inputs/extracted/s457_mirror_20261022/s457_mirror_20261022")
    for s, e in sorted(manifest.items()):
        ans = scan_answers(os.path.join(mirror, s))
        if s in ("single_pass", "matched_budget"):
            g.equal("G1/G2 frozen " + s, ans["llm_calls"], e["calls_lines"], "supp_fig17_outcomes records_manifest calls_lines")
        else:
            g.at_least("G1 calls_lines above kept " + s, e["calls_lines"], ans["llm_calls"],
                       "supp_fig17_outcomes records_manifest calls_lines")

    sums = Counter()
    sinks = [os.path.join(F, "runs", d) for d in sorted(os.listdir(os.path.join(F, "runs")))
             if d.startswith("b4_rlm_ref__") and "smoke" not in d]
    sinks += [os.path.join(F, "recompute/I2_runs/sinks", d) for d in sorted(os.listdir(os.path.join(F, "recompute/I2_runs/sinks")))]
    for d in sinks:
        _, groups = scan_calls(os.path.join(d, "calls.jsonl"), "sink", scan_answers(d))
        sums.update(_counts(groups, SIG["sink"], "state"))
    g.equal("Join, lines", sum(sums.values()), 59340, "independent json.loads join, 1 November")
    g.equal("Join, kept", sums["kept"], 57573, "independent json.loads join, 1 November")
    g.equal("Join, replaced", sums["replaced"] + sums["none"], 1767, "independent json.loads join, 1 November")

    members = {}
    with open(os.path.join(F, "recompute/frozen_inputs/members/g6_calls_after_d135.sha256")) as fh:
        for ln in fh:
            sha, name = ln.split()
            members[name.split("/")[1]] = sha
    for run, sha in sorted(members.items()):
        d = os.path.join(F, "runs", run)
        h = hashlib.sha256()
        with open(os.path.join(d, "calls.jsonl"), "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        g.equal("G6 sha256 " + run, h.hexdigest(), sha, "members/g6_calls_after_d135.sha256")
        ans = scan_answers(d)
        info, groups = scan_calls(os.path.join(d, "calls.jsonl"), "sink", ans)
        st = _counts(groups, SIG["sink"], "state")
        g.equal("G6 kept plus replaced " + run, st["kept"] + st["replaced"] + st["none"], info["lines"], "the same log")
        cur = set()
        for hh in groups.values():
            cur.update(bytes(hh[i:i + 8]) for i in range(0, len(hh), 8))
        _, old = scan_calls(os.path.join(d, "discarded_D89/calls.jsonl.before_rerun"), "plain")
        outside = sum(1 for hh in old.values() for i in range(0, len(hh), 8) if bytes(hh[i:i + 8]) not in cur)
        g.equal("G6 before-rerun lines outside calls.jsonl " + run, outside, 0, "freeze_g6_d135.py step 2")

    d = os.path.join(F, "runs/b4_rlm_ref__cap5__all135")
    for path, kind, ans in ((os.path.join(d, "calls.jsonl"), "sink", scan_answers(d)),
                            (os.path.join(F, "recompute/K1/reference_claims/calls.jsonl"), "ragchecker", None),
                            (os.path.join(F, "recompute/B7_judge_passages/check_laptop/check_calls.jsonl"), "judge", None)):
        _, groups = scan_calls(path, kind, ans)
        fields = ("status", "model") + (("role", "run_draw") if kind == "sink" else ())
        truth = Counter()
        with open(path, errors="replace") as fh:
            for ln in fh:
                x = json.loads(ln)
                truth[tuple(x.get(k) for k in fields)] += 1
        idx = [SIG[kind].index(k) for k in fields]
        mine = Counter()
        for sig, h in groups.items():
            mine[tuple(sig[i] for i in idx)] += len(h) // 8
        g.equal("scanner equals json.loads " + kind, mine == truth, True, os.path.basename(os.path.dirname(path)))
    return g


def machine_gates(g, inputs, repo):
    """Gates that need another machine's records; each runs only when that machine's input is given."""
    by = {i["machine"]: i for i in inputs}
    F = os.path.join(repo, "findings")
    manifest = json.load(open(os.path.join(F, "figures_provisional/supp_fig17_outcomes/records_manifest.json")))["exp01"]
    if "studio" in by:
        lines = {f["path"]: f["lines"] for f in by["studio"]["files"] if f["clone"] == "mentori-runs"}
        for s, e in sorted(manifest.items()):
            got = lines.get("runs/%s/calls.jsonl" % e["run"], 0)
            if s == "matched_budget":
                g.equal("G2 Studio log", got, e["calls_lines"], "supp_fig17_outcomes records_manifest calls_lines")
            else:
                g.at_least("G1 Studio log " + s, got, e["calls_lines"], "append-only; records_manifest calls_lines")
        w = {f["path"]: f["lines"] for f in by["studio"]["files"]}
        g.equal("K1 studio worker ended 26 Oct", w.get("recompute/K1/studio_1145" + "1/ragchecker/ragchecker_calls.jsonl", 0),
                48560, "RUNNING.md:1377")
    for inp in inputs:
        w = {f["path"]: f["lines"] for f in inp["files"]}
        for worker in sorted(os.listdir(os.path.join(F, "recompute/fig5_inputs/k1"))):
            if inp["machine"] != ("studio" if worker.startswith("studio") else "beelink" if worker.startswith("beelink")
                                  else "laptop"):
                continue
            rows = k1_rows(os.path.join(F, "recompute/fig5_inputs/k1", worker, "ragchecker/ragchecker.jsonl"))
            if rows:
                g.at_least("K1 %s log" % worker, w.get("recompute/K1/%s/ragchecker/ragchecker_calls.jsonl" % worker, 0),
                           rows["calls_sum"], "fig5_inputs/k1 rows, sum of calls")


# ---------------------------------------------------------------------------------------------------------------
# Writing.
# ---------------------------------------------------------------------------------------------------------------
TABLE_COLUMNS = ["experiment", "plan_row", "role", "model", "machine", "calls_ok", "calls_failed", "failed_by_status",
                 "replaced", "no_answer_line", "not_joined", "tier", "s1_box", "note"]


def provenance(repo, inputs, command, inputs_sha256, frozen=False):
    me = os.path.abspath(__file__)
    with open(me, "rb") as fh:
        sha = hashlib.sha256(fh.read()).hexdigest()
    head = NOT_STAMPED
    if not frozen:
        try:
            head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                  universal_newlines=True).stdout.strip()
        except OSError:
            head = None
    return {"script": "scripts/S520_llm_calls.py", "script_sha256": sha, "command": command, "repository_head": head,
            "written_utc": NOT_STAMPED if frozen else datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "inputs_sha256": inputs_sha256,
            "read": {i["machine"]: {"started_utc": i["started_utc"], "ended_utc": i["ended_utc"], "host": i["host"]}
                     for i in inputs}}


NOT_STAMPED = "not stamped (report --frozen)"
FROZEN_DIR = "findings/recompute/S520_inputs"       # S496 reads this prefix (S520_INPUTS) in the shared SHA256SUMS
DEFAULT_OUT = "findings/recompute/S520_llm_calls"
LAPTOP_GATES = "laptop_gates.json"
SUMS = "SHA256SUMS"


def sha256_path(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_frozen(folder):
    """({file name: path} of a frozen inputs folder, {file name: sha256}), every file held to its SHA256SUMS; a file
    missing, altered or not listed refuses (exit 2)."""
    with open(os.path.join(folder, SUMS)) as fh:
        listed = dict(reversed(ln.split(None, 1)) for ln in fh.read().splitlines() if ln.strip())
    listed = {k.strip(): v for k, v in listed.items()}
    present = sorted(f for f in os.listdir(folder) if f != SUMS)
    if present != sorted(listed):
        print("REFUSED: %s holds %s; %s lists %s" % (folder, present, SUMS, sorted(listed)))
        sys.exit(2)
    for name, want in sorted(listed.items()):
        got = sha256_path(os.path.join(folder, name))
        if got != want:
            print("REFUSED: %s sha256 %s, %s lists %s" % (name, got[:12], SUMS, want[:12]))
            sys.exit(2)
    return {k: os.path.join(folder, k) for k in listed}, listed


def mask_sha(text):
    """text with the script's own sha256 hidden: the one value of a frozen report that a change to this script moves."""
    return re.sub(r'("script_sha256": ")[0-9a-f]{64}|(sha256 )[0-9a-f]{16}', lambda m: (m.group(1) or m.group(2)) + "*", text)


def laptop_only(gates, machine_results):
    """The gates of a report that machine_gates does not give: the ones that need this laptop. Refused unless each machine
    gate's stored got, want and pass are the ones machine_gates gives now (its source is a label, which a folder's new
    name changes)."""
    now = {r["gate"]: r for r in machine_results}
    stored = {r["gate"]: r for r in gates if r["gate"] in now}
    same = lambda x, y: x is not None and all(x[k] == y[k] for k in ("got", "want", "pass"))   # noqa: E731
    bad = sorted(k for k, r in now.items() if not same(stored.get(k), r))
    if bad:
        print("REFUSED: machine gates differ from the summary: %s" % ", ".join(bad[:5]))
        sys.exit(2)
    return [r for r in gates if r["gate"] not in now]


def freeze(in_paths, summary_path, dest):
    """The module docstring, REPORT FROM TRACKED FILES. Copies the collects, writes laptop_gates.json and SHA256SUMS."""
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(summary_path) as fh:
        summary = json.load(fh)
    prov = summary["provenance"]
    inputs = [json.load(open(p)) for p in in_paths]
    for inp in inputs:
        read = prov["read"].get(inp["machine"])
        if read != {k: inp[k] for k in ("started_utc", "ended_utc", "host")}:
            print("REFUSED: %s's collect is not the one the summary read (%s)" % (inp["machine"], read))
            sys.exit(2)
        if inp.get("table_sha256") != table_sha():
            print("REFUSED: %s was collected with other tables" % inp["machine"])
            sys.exit(2)
    if os.path.exists(dest):
        print("REFUSED: %s exists: the collects are frozen once" % dest)
        sys.exit(2)
    g = Gates()
    machine_gates(g, inputs, repo)
    laptop = laptop_only(summary["gates"], g.results)
    os.makedirs(dest)
    names = {}
    for p, inp in zip(in_paths, inputs):
        names[inp["machine"]] = "s520_%s.json" % inp["machine"]
        with open(p, "rb") as src, open(os.path.join(dest, names[inp["machine"]]), "wb") as out:
            out.write(src.read())
    doc = {"what": "The results of the gates that need the laptop, from the report of 1 November, which ran them there",
           "summary_sha256": sha256_path(summary_path), "report": {k: prov[k] for k in prov if k != "read"},
           "total_calls": summary["total"]["calls"], "figure1_legend_total": summary["figure1_legend_total"],
           "collect_order": [names[i["machine"]] for i in inputs], "gates": laptop}
    with open(os.path.join(dest, LAPTOP_GATES), "w") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)
        fh.write("\n")
    with open(os.path.join(dest, SUMS), "w") as fh:
        for name in sorted(list(names.values()) + [LAPTOP_GATES]):
            fh.write("%s  %s\n" % (sha256_path(os.path.join(dest, name)), name))
    print("froze %d collects and %d laptop gates in %s" % (len(names), len(laptop), dest))


def n(v):
    return "{:,}".format(v) if isinstance(v, int) else str(v)


def md_table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(n(c) for c in r) + " |" for r in rows]
    return out


def first_few(items, cap=20):
    """A list for a banner: the first `cap`, then how many more, all of them in summary.json."""
    more = len(items) - cap
    return ", ".join(items[:cap]) + (" and %d more (summary.json)" % more if more > 0 else "")


def write_report(built, gates, prov, out_dir, missing):
    os.makedirs(out_dir, exist_ok=True)
    s = built["summary"]
    s = dict(s, provenance=prov, machines_read=sorted(prov["read"]), machines_not_read=missing, gates=gates)
    with open(os.path.join(out_dir, "summary.json"), "w") as fh:
        json.dump(s, fh, indent=1, sort_keys=True, default=str)
    with open(os.path.join(out_dir, "table.csv"), "w", newline="") as fh:
        fh.write("# provenance: %s sha256 %s, HEAD %s, written %s\n# command: %s\n# read: %s\n" % (
            prov["script"], prov["script_sha256"][:16], prov["repository_head"], prov["written_utc"], prov["command"],
            json.dumps(prov["read"])))
        w = csv.DictWriter(fh, TABLE_COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(built["rows"])
    t = s["total"]
    L = ["<!-- provenance: %s sha256 %s, HEAD %s, written %s -->" % (prov["script"], prov["script_sha256"][:16],
                                                                      prov["repository_head"], prov["written_utc"]),
         "# Language-model calls of the study", ""]
    if missing:
        L += ["**Partial: machines not read: %s. Every total below covers only %s.**" % (
            ", ".join(missing), ", ".join(s["machines_read"])), ""]
    if s["unmapped"]:
        L += ["**Unmapped: %d call-log files no rule names, not opened and not counted: %s.**" % (
            len(s["unmapped"]), first_few(["%s:%s/%s (%s bytes)" % (u["machine"], u["clone"], u["path"], n(u["size"]))
                                       for u in s["unmapped"]])), ""]
    if s["unmapped_opened"]:
        L += ["**Unmapped: %d logs read but tied to no experiment, %s calls outside the total: %s.**" % (
            len(s["unmapped_opened"]), n(s["tiers"]["unmapped"]), first_few(s["unmapped_opened"])), ""]
    L += ["Read at: " + "; ".join("%s %s to %s" % (m, v["started_utc"], v["ended_utc"])
                                  for m, v in sorted(prov["read"].items())), "",
          "One call is one line in a named call log (rule in scripts/S520_llm_calls.py; rule 5 ruled by D201 Q7: replaced "
          "answers in their own column). The total counts run tier only.", "",
          "## Total", ""]
    L += md_table(["Calls", "Ok", "Failed", "Replaced", "Of those, on no answer line", "Could not be joined"],
                  [[t["calls"], t["ok"], t["failed"], t["replaced"], t["no_answer_line"], t["not_joined"]]])
    L += ["", "Failed by status: " + (", ".join("%s %s" % (k, n(v)) for k, v in t["failed_by_status"].items()) or "none"),
          "", "Figure 1 legend total: %s." % n(s["figure1_legend_total"]), "",
          "Of the replaced calls, %s are the main judge's key v2.4 calls on the 132 questions key v2.5 changed, each "
          "judged again in the matching S6 out." % n(s["judge_v24_replaced_by_v25"]), "", "## Methods groups", ""]
    L += md_table(["Group", "Calls", "Ok", "Failed"], [[k, v["calls"], v["ok"], v["failed"]]
                                                        for k, v in s["methods_groups"].items()])
    L += ["", "G5 and T1 cannot join ctx_uid: exp_06 keeps their answers in a results file outside the sink "
          "(experiments/scorers/records.py:15-16), so their %s calls read not_joined." % n(s["not_joined_exp06"])]
    L += ["", "Outside the total: checks %s, smokes %s, dropped by decision (%s) %s, not mapped %s." % (
        n(s["tiers"]["check"]), n(s["tiers"]["smoke"]), "; ".join("%s, %s" % (", ".join(sorted(
            t for t in DROPPED_RUNS if DROPPED_RUNS[t] == d)), d) for d in sorted(set(DROPPED_RUNS.values()))),
        n(s["tiers"]["dropped"]), n(s["tiers"]["unmapped"])), "",
        "Scorers with no language-model call: MiniCheck, text overlap, concept recall, bge-m3 and the other encoders.",
        "", "## By role", ""]
    L += md_table(["Role", "Calls", "Ok", "Failed", "Replaced"],
                  [[k, v["calls"], v["ok"], v["failed"], v["replaced"]] for k, v in s["by_role"].items()])
    L += ["", "## By model", ""]
    L += md_table(["Model", "Calls", "Ok", "Failed"], [[k, v["calls"], v["ok"], v["failed"]]
                                                        for k, v in s["by_model"].items()])
    L += ["", "## By experiment", ""]
    L += md_table(["Experiment", "Calls", "Ok", "Failed", "Replaced"],
                  [[EXPERIMENTS.get(k, (k, ""))[0], v["calls"], v["ok"], v["failed"], v["replaced"]]
                   for k, v in s["by_experiment"].items()])
    L += ["", "## Supplementary Figure 1 boxes", ""]
    L += md_table(["Box", "Calls"], [[k, v] for k, v in s["s1_boxes"].items()])
    L += ["", "G7 and G8 sit in G3, G4 and G5; K1 and S18f sit in G1. G10, G11 and S508's 49 answers are not in a box.",
          "",
          "## Still running at read time", ""]
    L += md_table(["Machine", "Plan row", "Experiment", "Tier", "Logs written in the last 30 min", "Newest (s ago)"],
                  [[x["machine"], x["plan_row"], x["experiment"], x["tier"], x["logs"], x["newest_age_s"]]
                   for x in s["live"]]) if s["live"] else ["No log written in the last 30 minutes on the machines read."]
    L += ["", "## Planned calls left (about)", ""]
    L += md_table(["Job", "Unit", "Due", "Done", "Calls per answer so far", "Calls left, about", "Source"],
                  [[x["job"], x["unit"], x["due"], x["done"], x["calls_per_answer_so_far"] or "not known",
                    x["calls_left_about"] if x["calls_left_about"] is not None else "not known", x["source"]]
                   for x in s["planned_left"]])
    L += ["", "No planned count: " + "; ".join("%s (%s)" % (x["job"], x["why"]) for x in s["not_planned"]) + ".", "",
          "## Not counted, and why", "",
          "- Embeddings lines: %s (a call to an encoder, rule 4)." % n(s["not_calls"].get("embeddings lines (bge-m3)", 0)),
          "- April: 37,449 is the evaluation count (S13), and April's records hold only `llm_calls` per answer.",
          "- Pre-lock work (S141_campaign, S373, S18e), by name, unopened: "
          + json.dumps(s["known_out"], sort_keys=True) + ".",
          "- Duplicates removed: %s lines (the same bytes in another source)." % n(s["duplicates_removed"]),
          "- Lines found only in a copy, not counted: %s." % (json.dumps(s["lines_found_only_in_copies"]) if
                                                               s["lines_found_only_in_copies"] else "none"),
          "- Call-log names no rule covers, unopened: %d." % len(s["unmapped"]),
          "- Clones not in the table: %s." % json.dumps(s["clones_not_in_table"]), "",
          "## Checks on these numbers", "",
          "Gates passed: %d of %d. Sinks whose kept lines differ from the answers' llm_calls: %d of %d." % (
              sum(1 for g in gates if g["pass"]), len(gates), len(s["reconcile"]["sinks_differ"]),
              s["reconcile"]["sinks_checked"]),
          "Files read %s, lines %s, bad lines %s, unfinished last lines %d." % (
              n(s["files"]), n(s["lines_read"]), n(s["bad_lines"]), len(s["bad_last_lines"]))]
    with open(os.path.join(out_dir, "summary.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")


def report(in_paths, out_dir, frozen_dir=None):
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    home = os.path.expanduser("~")
    frozen_doc = None
    if frozen_dir:
        files, sums = read_frozen(frozen_dir)
        with open(files.pop(LAPTOP_GATES)) as fh:
            frozen_doc = json.load(fh)
        in_paths = [files[k] for k in frozen_doc["collect_order"]]      # a duplicate line goes to the earlier source
    else:
        sums = {os.path.basename(p): sha256_path(p) for p in in_paths}
    inputs = []
    for p in in_paths:
        with open(p) as fh:
            inp = json.load(fh)
        if inp.get("table_sha256") != table_sha():
            print("REFUSED: %s was collected with other tables; collect again" % p)
            sys.exit(2)
        inputs.append(inp)
    if len({i["machine"] for i in inputs}) != len(inputs):
        print("REFUSED: two inputs from one machine")
        sys.exit(2)
    print("Reproducing first")
    if frozen_doc:
        g = Gates()
        g.results = list(frozen_doc["gates"])
    else:
        g = reproduce(repo, home)
    machine_gates(g, inputs, repo)
    g.refuse_on_failure()
    sys.path.insert(0, os.path.join(repo, "scripts"))
    import S512_s6_rejudge_v25 as S512   # the 132 questions, under S512's sha256 pin
    built = build(inputs, S512.changed_ids())
    missing = [m for m in MACHINE_ORDER if m not in {i["machine"] for i in inputs}]
    if frozen_doc:
        global _drops
        kept, _drops = _drops, FROZEN_RULE_DROPS     # reproduce first: the frozen total under the frozen rule
        try:
            old = build(inputs, S512.changed_ids())["summary"]
        finally:
            _drops = kept
        got = (old["total"]["calls"], old["figure1_legend_total"])
        want = (frozen_doc["total_calls"], frozen_doc["figure1_legend_total"])
        if got != want:
            print("REFUSED: under the frozen rule (drops %s) total %s and legend total %s, the frozen report gave %s and %s;"
                  " nothing written" % ((FROZEN_RULE_DROPS,) + got + want))
            sys.exit(2)
        moved = old["total"]["calls"] - built["summary"]["total"]["calls"]
        built["summary"]["dropped_after_freeze"] = {
            "runs": sorted(t for t in DROPPED_RUNS if t not in FROZEN_RULE_DROPS),
            "decisions": sorted({DROPPED_RUNS[t] for t in DROPPED_RUNS if t not in FROZEN_RULE_DROPS}),
            "frozen_total": old["total"]["calls"], "calls_moved": moved}
        print("Reproduced: %d calls under the frozen rule; the later drops move %d to the dropped tier" % (
            old["total"]["calls"], moved))
        command = "uv run --frozen python scripts/S520_llm_calls.py report --frozen"
    else:
        command = "uv run --frozen python scripts/S520_llm_calls.py report --in %s --out-dir %s" % (
            " ".join(os.path.basename(p) for p in in_paths), out_dir)
    prov = provenance(repo, inputs, command, sums, frozen=bool(frozen_doc))
    write_report(built, g.results, prov, out_dir, missing)
    t = built["summary"]["total"]
    print("%d calls, %d ok, %d failed, %d replaced; machines not read: %s" % (
        t["calls"], t["ok"], t["failed"], t["replaced"], ", ".join(missing) or "none"))


def main():
    ap = argparse.ArgumentParser(description="Every language-model call of the study, from the call logs.")
    sub = ap.add_subparsers(dest="mode")
    c = sub.add_parser("collect")
    c.add_argument("--machine", required=True, choices=sorted(MACHINES))
    c.add_argument("--out", required=True)
    r = sub.add_parser("report")
    r.add_argument("--in", dest="inputs", nargs="+")
    r.add_argument("--out-dir")
    r.add_argument("--frozen", action="store_true", help="read %s; no --in" % FROZEN_DIR)
    z = sub.add_parser("freeze")
    z.add_argument("--in", dest="inputs", nargs="+", required=True)
    z.add_argument("--summary", required=True)
    z.add_argument("--dest", default=FROZEN_DIR)
    a = ap.parse_args()
    if a.mode == "collect":
        collect(a.machine, os.path.expanduser(a.out))
    elif a.mode == "freeze":
        freeze(a.inputs, a.summary, a.dest)
    elif a.mode == "report":
        repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if a.frozen == bool(a.inputs):
            ap.error("report takes --in or --frozen, one of them")
        if not a.frozen and not a.out_dir:
            ap.error("report --in needs --out-dir")
        report(a.inputs, a.out_dir or os.path.join(repo, DEFAULT_OUT), os.path.join(repo, FROZEN_DIR) if a.frozen else None)
    else:
        ap.error("collect or report")


if __name__ == "__main__":
    main()
