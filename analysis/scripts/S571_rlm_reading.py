"""S571: how Mentori RLM-10 and package RLM-10 read, from their stored runs (association only, no model call).

Question (Valerio, 4 November, story doc): why does Mentori's RLM-10 gain on many-paper questions while package RLM-10
(rlms 0.1.3, run G6, D73) does not? One candidate explanation, not tested here (D238 tests it): Mentori's quality
gate. Line numbers below are at commit 6318e8e8 (orchestrator.py and exp1_rlm_vs_singlepass.py have uncommitted
edits in the working tree since). The gate rejects FINAL when `sub_calls_ok < MIN_LLM_CALLS or not has_substance`
(experiments/mentori/backend/retrieval/rlm/orchestrator.py:440 at 6318e8e8; MIN_LLM_CALLS = 3 at :39; has_substance at :437, false only when the answer has no text and no get_report()
section holds text either), at most 3 times (:445); then it accepts (final_after_max_rejections,
:461-495). sub_calls_ok counts every successful llm_summarize/llm_query/llm_extract call except one handed an empty
list, including llm_query(prompt) with no passages (executor.py:207-215, 268-271 at 6318e8e8). metadata.rejections
counts both kinds of rejection and the record does not say which; S571 tells them apart where the call records allow
(rejection_kinds). This script measures, per answer, how much each implementation read and whether the gate fired,
and sets it beside the answer's pass at score 4. It changes nothing and measures association only.

Inputs (each read through the code Figure 3 uses, scripts/S463_fig2_ranking.py, as its `rebuild` reads them):
  - the judge cells: S463.read_answers + read_collect + judge_rows (G1, key v2.5 through judge_rows_v25) for Mentori
    RLM-10, S463.read_extra (G6 cap 10, key v2.5) for package RLM-10; the one-paper / many-paper split from
    S511.questions() (D5 key, Rule 8), as Figure 3 uses it;
  - Mentori RLM-10's generation records: the exact line S463.read_answers took for each answer (K1's frozen copy with
    G1R15's over it), generation.rlm written by exp1_rlm_vs_singlepass.py:627 at 6318e8e8 from
    RLMOrchestrator._metadata, and generation.calls, one summary per call record (exp1:248 at 6318e8e8; n_passages =
    the number of chunk ids set for the call, pipeline.py:42);
  - package RLM-10's generation records: frozen g6_d135 b4_rlm_ref__cap10__all135/answers.jsonl (the file S463's
    read_g6_clock reads), and its call records: frozen g6_calls_after_d135 calls.jsonl, every answer's calls.seqs
    found there with its ctx_uid;
  - passage id to paper: S511.paper_map (the paper store's chroma.sqlite3, sha256 pinned in S511);
  - paper text for the package: findings/recompute/B4_rlm_ref_context.json (the context the package was given; its
    sha256 must be the one every G6 record carries).

Reproduce first (README.md:75-79): both strategies' pass rates at score 4 on the one-paper and many-paper questions
must equal Figure 3a's committed Source Data (sheet Fig. 3a, rows 'strategy, question group', threshold 4), and
Mentori RLM-10's every-key-paper counts must equal S511's results.json; otherwise nothing is written.

G17 (D240, --g17; nothing above changes with it or without it). With --g17 <folder holding runs/exp_01__<arm>__
exp_v4_s20_n0/answers.jsonl> the same definitions are read on G17's three arms (rlm_10_ctrl, rlm_10_nosearch,
rlm_10_nogate; draw 1, the 86 answerable) beside G1's RLM-10 and G6's cap 10 at draw 1 (g17_reading): mentori_trace per
answer, every key paper, model calls and tokens over the answer's call records, wall time, failures and stop reasons,
B's refused search attempts, pass at 4 and at 3 from S572's judge rows (--g17-judge <out_s6_w_g17>, S463.cell_of) and
concept recall from S573's rows (--g17-concept-recall); G1's and G6's pass from Figure 3's cells, their concept recall
from L3_d181 and L2_d181 (cap 10) where the answer's sha256 matches. Written to <out>/g17/ only. Test:
scripts/S571_g17_test.py (R' holding G1's answers gives G1's measures in every column).

G17 draws 2 and 3 (D249 O1, --g17-d23; with --g17). --g17-d23 <folder holding the d23 sinks as runs/<run>/answers.jsonl,
the 86 at draws 2 and 3 and no other key>, --g17-d23-judge <out_s6_w_g17_d23> and --g17-d23-concept-recall <S573
--draws 2 3 rows> add <out>/g17_d123/: the same reading on draws 1, 2 and 3, the five strategies (G1 RLM-10 and G6 cap 10
at draws 1 to 3 from the records and cells build() read, concept recall from L3_d181 and, for G6, L2_d135_d181's G6
rows: S474's reading of the g6_d135 records read here, where L2_d181 holds a pre-D135 answer at one draw-2 question),
the table pooled over the three draws and one table per draw. <out>/g17/ is written as without it.

Usage: uv run --frozen python scripts/S571_rlm_reading.py [--out DIR] [--g17 DIR [--g17-judge DIR]
       [--g17-concept-recall FILE] [--g17-d23 DIR [--g17-d23-judge DIR] [--g17-d23-concept-recall FILE]]]
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

SCRIPT = "scripts/S571_rlm_reading.py"
OUT = ROOT / "findings" / "recompute" / "S571_rlm_reading"
FIG3_DIR = ROOT / "findings" / "figures_provisional" / "fig3_strategies"
FIG3_SD_GLOB = "Source Data Fig. 3.xlsx"              # Q9 (11 Nov): the lock's name, no suffix
S511_RESULTS = ROOT / "findings" / "recompute" / "S511_g2_budget" / "results.json"
CONTEXT = ROOT / "findings" / "recompute" / "B4_rlm_ref_context.json"
INDEX = "exp_v4_s20_n0"
MENTORI, PACKAGE = "rlm_10", "cap10"
LABEL = {MENTORI: "Mentori RLM-10", PACKAGE: "package RLM-10"}
DRAWS = (1, 2, 3)
PASS_T = 4
TOL = 1e-6
N_BOOT, SEED = 10000, 20261013          # S463's resamples and seed (Rule 2)
K, STRIDE, MIN_HITS = 64, 32, 2          # package paper matching (PaperIndex)
DEEP_CHARS = 2000                         # package: a paper 'read in depth' when at least this many DISTINCT
                                          # characters of it reached the answer's successful sub-calls (each sampled
                                          # run found covers its first STRIDE characters; text sent twice counts once)
MIN_LLM_CALLS = 3                         # orchestrator.py:39 at 6318e8e8 (the gate's count)
PLACEMENT_CAP = 1000                      # root-call placements enumerated per answer before giving up
GATE_COUNT, GATE_SUBSTANCE, GATE_UNKNOWN = "under_3_sub_calls", "3_or_more_sub_calls", "cannot_tell"
CODE_DEPS = ("scripts/S571_rlm_reading.py", "scripts/S571_rlm_reading_test.py", "scripts/S463_fig2_ranking.py",
             "scripts/S511_g2_matched_budget.py", "scripts/fig_repro.py", "experiments/runner/gemini_client.py")
GROUP_ORDER = ("one", "many", "false_premise", "not_answerable")
GROUP_LABEL = {"one": "one-paper", "many": "many-paper", "false_premise": "false premise",
               "not_answerable": "not answerable"}


class Refused(Exception):
    pass


def sha256_file(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def rel(p) -> str:
    try:
        return str(Path(p).resolve().relative_to(ROOT))
    except ValueError:
        return str(p)


# ---------------------------------------------------------------------------------------------------------------
# trace parsing, one function per implementation (fixtures in S571_rlm_reading_test.py)
# ---------------------------------------------------------------------------------------------------------------
def words(text) -> int:
    return len((text or "").split())


def root_placements(calls: list[dict], turns: int, cap: int = PLACEMENT_CAP):
    """(calls sorted by seq, every placement of the run's `turns` root calls among them), a placement being the
    indices of the root calls in turn order. The record does not label root calls; a placement is any choice that
    meets three facts of the code at 6318e8e8: the first call is root turn 1; a root call carries no passage ids
    (rc.set_passages([]) before it, orchestrator.py:262, so n_passages 0); the root prompt holds the whole history,
    which only grows (no compaction, orchestrator.py:532), so root prompt_tokens rise strictly turn by turn. Returns
    None for the placements when more than `cap` fit."""
    c = sorted(calls, key=lambda z: z["seq"])
    if turns < 1 or not c or c[0].get("n_passages"):
        return c, []
    cand = [i for i, x in enumerate(c) if not x.get("n_passages") and isinstance(x.get("prompt_tokens"), int)]
    out, stack = [], [[0]]
    while stack:
        path = stack.pop()
        if len(path) == turns:
            out.append(tuple(path))
            if len(out) > cap:
                return c, None
            continue
        last = path[-1]
        for i in reversed(cand):
            if i > last and c[i]["prompt_tokens"] > c[last]["prompt_tokens"]:
                stack.append(path + [i])
    return c, sorted(out)


def rejection_kinds(md: dict, calls: list[dict]) -> list[str]:
    """For each gate rejection (metadata.nudges kind 'rejection', one per rejection, at its turn t), whether the
    successful sub-calls counted by then were under MIN_LLM_CALLS (GATE_COUNT: the count alone rejects; the answer may
    also have lacked substance), or MIN_LLM_CALLS or more (GATE_SUBSTANCE: the count was met, so the answer lacked
    substance), or GATE_UNKNOWN. The sub-calls counted by turn t are the calls before root call t+1 (or all calls
    after the last root call) that are not root calls and not in metadata.sub_call_failures; a call handed an empty
    list (sub_calls_empty) is not counted by the gate and cannot be told from llm_query(prompt) in the record (both
    n_passages 0), so the count is a range [hi - min(sub_calls_empty, such calls), hi]. A kind is given only when
    every root placement (root_placements) gives the same one."""
    rej = [n.get("turn") for n in (md.get("nudges") or []) if n.get("kind") == "rejection"]
    if len(rej) != (md.get("rejections") or 0):
        raise Refused(f"metadata.nudges holds {len(rej)} rejections, metadata.rejections {md.get('rejections')}")
    if not rej:
        return []
    c, placements = root_placements(calls, md.get("turns") or 0)
    if not placements:
        return [GATE_UNKNOWN] * len(rej)
    failed = {f.get("seq") for f in (md.get("sub_call_failures") or [])}
    n_empty = md.get("sub_calls_empty") or 0
    out = []
    for t in rej:
        kinds = set()
        for pl in placements:
            roots = set(pl)
            end = pl[t] if t < len(pl) else len(c)
            before = [c[i] for i in range(end) if i not in roots and c[i]["seq"] not in failed]
            no_ids = sum(1 for x in before if not x.get("n_passages"))
            hi = len(before)
            lo = hi - min(n_empty, no_ids)
            kinds.add(GATE_COUNT if hi < MIN_LLM_CALLS else GATE_SUBSTANCE if lo >= MIN_LLM_CALLS else GATE_UNKNOWN)
        out.append(kinds.pop() if len(kinds) == 1 else GATE_UNKNOWN)
    return out


def mentori_trace(rec: dict, paper_of: dict) -> dict:
    """One Mentori RLM-10 answer record (exp1_rlm_vs_singlepass.py:627 at 6318e8e8: generation.rlm = RLM_FIELDS of the
    orchestrator's _metadata, plus metadata = the whole _metadata, orchestrator.py:157-189 at 6318e8e8).
      sub_calls_ok   metadata.sub_calls_ok, the count the gate reads: every successful llm_summarize/llm_query/
                     llm_extract call except one handed an empty list (executor.py:268-271 at 6318e8e8), so it
                     includes llm_query(prompt) with no passages and calls handed passages as strings
      sub_calls_with_paper_text
                     successful sub-calls handed chunk ids: generation.calls with n_passages > 0 (the chunk ids set
                     for that call, executor.py:235-242, pipeline.py:42) and not in metadata.sub_call_failures (root
                     calls carry 0). Passages handed as strings carry no id, so this is a lower bound on the sub-calls
                     that carried paper text
      root_turns     metadata.turns (orchestrator.py:257 at 6318e8e8, root calls made)
      papers         distinct papers (paper_of) among metadata.passages_seen, the ids of every chunk a search or a navigation
                     read returned to the code (context.py:399-413). PROXY: the record holds how many chunks each sub-call was
                     handed (n_passages) but not their ids, so this is what the code was given, an upper bound on the
                     papers its sub-calls were handed
      papers_cited   distinct doc_name of metadata.citations (context.py:478-482), second proxy, labelled
      rejections     metadata.rejections (orchestrator.py:445 at 6318e8e8), the gate's rejections of FINAL, both kinds
      rejection_kinds  rejection_kinds(): per rejection, under_3_sub_calls, 3_or_more_sub_calls or cannot_tell
      after_max      stop_reason final_after_max_rejections or accepted_after_max_rejections (orchestrator.py:461-495)
      words          generation.answer split on whitespace"""
    g = rec.get("generation") or {}
    rlm = g.get("rlm") or {}
    md = rlm.get("metadata") or {}
    calls = g.get("calls") or []
    failed = {f.get("seq") for f in (md.get("sub_call_failures") or [])}
    with_text = sum(1 for x in calls if (x.get("n_passages") or 0) > 0 and x.get("seq") not in failed)
    n_ok = md.get("sub_calls_ok", rlm.get("sub_calls_ok"))
    if n_ok is not None and with_text > n_ok:
        raise Refused(f"{rec.get('answer_key')}: {with_text} calls carry chunk ids, more than sub_calls_ok {n_ok}")
    seen = md.get("passages_seen")
    if seen is None:
        seen = rlm.get("passages_seen") or []
    unmapped = sorted({i for i in seen if not paper_of.get(i)})
    papers = sorted({paper_of[i] for i in seen if paper_of.get(i)})
    cited = sorted({c.get("doc_name") for c in (md.get("citations") or []) if isinstance(c, dict) and c.get("doc_name")})
    stop = md.get("stop_reason") or rlm.get("stop_reason") or g.get("stop_reason")
    return {"sub_calls_ok": n_ok, "sub_calls_with_paper_text": with_text,
            "rejection_kinds": rejection_kinds(md, calls),
            "sub_calls_empty": md.get("sub_calls_empty", rlm.get("sub_calls_empty")),
            "sub_calls_failed": md.get("sub_calls_failed", rlm.get("sub_calls_failed")),
            "root_turns": md.get("turns", rlm.get("turns")),
            "papers": papers, "n_papers": len(papers), "papers_cited": cited, "n_papers_cited": len(cited),
            "unmapped_ids": len(unmapped),
            "rejections": md.get("rejections", rlm.get("rejections")) or 0,
            "after_max": stop == "final_after_max_rejections" or bool(md.get("accepted_after_max_rejections")),
            "stop_reason": stop, "words": words(g.get("answer"))}


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


class PaperIndex:
    """Every K-character run of each paper's text in the package's context (whitespace collapsed), keyed by its
    text, with the paper and the run's first position in it; a run found in two papers is dropped. hits() samples a
    prompt at every STRIDE-th position (0, 32, 64, ...) and looks each sampled K-character window up: a paper counts
    as read by that prompt when at least MIN_HITS windows are its runs. Any whole copy of K + STRIDE - 1 = 95
    characters holds one sampled window and any of 127 holds two, so a copy of 127 characters or more of text
    found in only one paper is always found; shorter copies, and text shared with another paper (its runs are
    dropped), may be missed."""

    def __init__(self, papers: dict):
        self.names = sorted(papers)
        idx = {}
        for i, name in enumerate(self.names):
            t = norm(papers[name])
            for j in range(0, max(0, len(t) - K + 1)):
                h = t[j:j + K]
                prev = idx.get(h)
                if prev is None:
                    idx[h] = (i << 32) | j
                elif prev != -1 and (prev >> 32) != i:
                    idx[h] = -1
        self.idx = idx

    def positions(self, prompt: str) -> dict:
        """{paper: [positions in the paper of the sampled windows found]} for the papers with at least MIN_HITS."""
        t = norm(prompt)
        found = {}
        for j in range(0, max(0, len(t) - K + 1), STRIDE):
            v = self.idx.get(t[j:j + K])
            if v is not None and v >= 0:
                found.setdefault(v >> 32, []).append(v & 0xFFFFFFFF)
        return {self.names[i]: ps for i, ps in found.items() if len(ps) >= MIN_HITS}

    def hits(self, prompt: str) -> dict:
        """{paper: sampled windows found} for the papers with at least MIN_HITS windows in prompt."""
        return {n: len(ps) for n, ps in self.positions(prompt).items()}

    def match(self, prompt: str) -> list[str]:
        return sorted(self.positions(prompt))


def covered(positions) -> int:
    """Distinct characters of a paper covered by sampled windows found at these positions, each window counting its
    first STRIDE characters (consecutive samples of one copy tile the copy; the same text sent twice counts once)."""
    n, end = 0, -1
    for p in sorted(set(positions)):
        lo = max(p, end)
        if p + STRIDE > lo:
            n += p + STRIDE - lo
        end = max(end, p + STRIDE)
    return n


def package_sub_ok(call: dict, raised_before_d89) -> bool:
    """A successful sub-call by the adapter's own rule (experiments/rlm_ref/adapter.py:565-570, sub_failed): status
    ok or empty and not one gemini_client.raised_before_d89 counts as failed."""
    return not (call.get("status") not in ("ok", "empty") or raised_before_d89(call))


def package_trace(ans: dict, calls: list[dict], pindex: PaperIndex, raised_before_d89) -> dict:
    """One package RLM-10 answer (adapter.py:1185-1200) with its call records (calls.jsonl, adapter.py:747-776).
      sub_calls_ok   calls.sub - calls.sub_failed (adapter.py:1195, sub_failed :565-570), checked against the call
                     records with b4.call 'sub' and package_sub_ok
      root_turns     turns_used (adapter.py:1190, root calls; the closing forced_final call is not counted)
      papers         distinct papers whose text appears in the prompt_sent (adapter.py:749) of a successful sub-call,
                     by PaperIndex.match (text copied from the context; a sub-call given only text the model wrote
                     itself reads no paper)
      papers_deep    of those, the papers with at least DEEP_CHARS distinct characters covered (covered()) over the
                     answer's successful sub-calls: text sent to two sub-calls counts once. A sub-call given each
                     paper's first 1,000 characters reads all 20 papers, none in depth
      sub_calls_with_paper_text  successful sub-calls whose prompt_sent matched at least one paper
      words          answer split on whitespace"""
    seqs = sorted(ans["calls"]["seqs"])
    got = sorted(c["seq"] for c in calls)
    if got != seqs or any(c.get("ctx_uid") != ans.get("ctx_uid") for c in calls):
        raise Refused(f"{ans['answer_key']}: its call records are not the seqs it lists ({len(got)} found, "
                      f"{len(seqs)} listed)")
    subs = [c for c in calls if (c.get("b4") or {}).get("call") == "sub"]
    ok = [c for c in subs if package_sub_ok(c, raised_before_d89)]
    n_ok = ans["calls"]["sub"] - ans["calls"]["sub_failed"]
    if len(subs) != ans["calls"]["sub"] or len(ok) != n_ok:
        raise Refused(f"{ans['answer_key']}: calls.sub {ans['calls']['sub']} / sub_failed {ans['calls']['sub_failed']}"
                      f" disagree with its call records ({len(subs)} sub, {len(ok)} successful)")
    pos, summed, per_call = {}, {}, []
    for c in ok:
        h = pindex.positions(c.get("prompt_sent") or "")
        per_call.append(len(h))
        for name, ps in h.items():
            pos.setdefault(name, []).extend(ps)
            summed[name] = summed.get(name, 0) + len(ps) * STRIDE
    papers = set(pos)
    distinct = {n: covered(ps) for n, ps in pos.items()}
    deep = sorted(n for n, v in distinct.items() if v >= DEEP_CHARS)
    # the earlier rule (windows found x STRIDE summed over sub-calls, repeats counted again), kept for the record only
    by_sum_only = sorted(n for n in papers if summed[n] >= DEEP_CHARS and distinct[n] < DEEP_CHARS)
    return {"sub_calls_ok": n_ok, "sub_calls_failed": ans["calls"]["sub_failed"], "root_turns": ans.get("turns_used"),
            "papers": sorted(papers), "n_papers": len(papers), "papers_deep": deep, "n_papers_deep": len(deep),
            "papers_deep_by_repeats_only": by_sum_only,
            "sub_calls_with_paper_text": sum(1 for n in per_call if n),
            "rejections": None, "after_max": None, "stop_reason": ans.get("stop_reason"),
            "forced_final": ans.get("forced_final"), "words": words(ans.get("answer"))}


# ---------------------------------------------------------------------------------------------------------------
# pass rates, reproduce
# ---------------------------------------------------------------------------------------------------------------
def pass_of(cell: dict, t: int = PASS_T):
    """1, 0 or None (Figure 3's rule, S463.shares: a failed answer counts as a fail, an unscored one is left out)."""
    if cell["kind"] == "scored":
        return int(cell["score"] >= t)
    if cell["kind"] == "failed":
        return 0
    return None


def question_rate(cells: dict, c: str, qids, draws=DRAWS):
    """Figure 3's pass rate: the mean over questions of each question's share of passing draws, in percent."""
    sh = []
    for q in qids:
        v = [pass_of(cells[(c, q, d)]) for d in draws]
        v = [x for x in v if x is not None]
        if v:
            sh.append(sum(v) / len(v))
    return 100 * sum(sh) / len(sh) if sh else None


def committed_rates(xlsx: Path) -> dict:
    """{(strategy, group): pass_rate_pct} from Source Data Fig. 3a, rows 'strategy, question group', threshold 4."""
    import openpyxl
    wb = openpyxl.load_workbook(xlsx, read_only=True)
    rows = list(wb["Fig. 3a"].iter_rows(values_only=True))
    head = list(rows[0])
    ix = {k: head.index(k) for k in ("row_kind", "strategy", "threshold", "question_group", "pass_rate_pct")}
    out = {}
    for r in rows[1:]:
        if r[ix["row_kind"]] == "strategy, question group" and r[ix["threshold"]] == PASS_T:
            out[(r[ix["strategy"]], r[ix["question_group"]])] = r[ix["pass_rate_pct"]]
    return out


def reproduce(got: dict, want: dict) -> list[str]:
    """Each (strategy, group) of got must equal want within TOL; raises Refused naming every difference."""
    lines, bad = [], []
    for k, v in sorted(got.items()):
        w = want.get(k)
        if w is None or v is None or abs(v - w) > TOL:
            bad.append(f"{LABEL.get(k[0], k[0])} {k[1]}-paper: recomputed {v}, committed {w}")
        else:
            lines.append(f"{LABEL.get(k[0], k[0])} {k[1]}-paper: {v:.6f} = committed {w:.6f}")
    if bad:
        raise Refused("reproduce failed: " + "; ".join(bad))
    return lines


# ---------------------------------------------------------------------------------------------------------------
# summaries
# ---------------------------------------------------------------------------------------------------------------
def quart(v):
    """(median, Q1, Q3) by numpy's default linear percentile; Nones dropped."""
    import numpy as np
    v = [x for x in v if x is not None]
    if not v:
        return (None, None, None)
    a = np.asarray(v, float)
    return (float(np.median(a)), float(np.percentile(a, 25)), float(np.percentile(a, 75)))


def pearson(x, y):
    n = len(x)
    if n < 2:
        return None
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx == 0 or syy == 0:
        return None
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / math.sqrt(sxx * syy)


def boot_r(x, y, n_boot=N_BOOT, seed=SEED):
    """Two-sided 95% percentile interval of Pearson r over question resamples (numpy default_rng(seed)); resamples
    with no spread in x or y are skipped and counted."""
    import numpy as np
    rng = np.random.default_rng(seed)
    x, y = np.asarray(x, float), np.asarray(y, float)
    rs, skipped = [], 0
    for _ in range(n_boot):
        i = rng.integers(0, len(x), len(x))
        a, b = x[i], y[i]
        if a.std() == 0 or b.std() == 0:
            skipped += 1
            continue
        rs.append(float(np.corrcoef(a, b)[0, 1]))
    if not rs:
        return None, None, skipped
    return float(np.percentile(rs, 2.5)), float(np.percentile(rs, 97.5)), skipped


def concordant(rows: dict, qids, win: str, lose: str) -> list[str]:
    """Questions where every draw of `win` passes at 4 and every draw of `lose` fails (each of the 3 draws measured,
    a failed answer counted as a fail): rows[(strategy, q, d)]["pass4"]."""
    out = []
    for q in qids:
        w = [rows[(win, q, d)]["pass4"] for d in DRAWS]
        l_ = [rows[(lose, q, d)]["pass4"] for d in DRAWS]
        if all(v == 1 for v in w) and all(v == 0 for v in l_):
            out.append(q)
    return out


# ---------------------------------------------------------------------------------------------------------------
# reading the inputs: each refusal is a small function (tested in S571_rlm_reading_test.py)
# ---------------------------------------------------------------------------------------------------------------
def check_sha(path: Path, want: str, what: str) -> str:
    """path's sha256, refused unless it is want."""
    got = sha256_file(path)
    if got != want:
        raise Refused(f"{rel(path)} is not the file {what} records ({got[:12]}, want {str(want)[:12]})")
    return got


def one_workbook(folder: Path, pattern: str = FIG3_SD_GLOB) -> Path:
    sds = sorted(Path(folder).glob(pattern))
    if len(sds) != 1:
        raise Refused(f"want one committed Source Data Fig. 3 workbook in {rel(folder)}, found {len(sds)}")
    return sds[0]


def check_record(k: str, r: dict, answer_sha256: str) -> dict:
    """The record line S463 read must be answer k with the answer text S463 hashed."""
    ans = (r.get("generation") or {}).get("answer") or ""
    if r.get("answer_key") != k or hashlib.sha256(ans.encode()).hexdigest() != answer_sha256:
        raise Refused(f"{k}: the record line is not the answer S463 read")
    return r


def context_texts(ctx: dict) -> dict:
    """{file name: paper text} from the package's context; each text starts 'File: <name>' and the names are the
    context's papers."""
    texts = {}
    for t in ctx["context"]:
        m = re.match(r"File: (\S+)\n", t)
        if not m:
            raise Refused("a context paper does not start with 'File: <name>'")
        texts[m.group(1)] = t
    if sorted(texts) != sorted(p["file_name"] for p in ctx["papers"]):
        raise Refused("the context's papers and its 'File:' headers differ")
    return texts


def package_records(p_ans: dict, qids, file_sha: str) -> dict:
    """{ctx_uid: answer record} for every question and draw; refused when a record is missing or was given another
    context file."""
    need = {}
    for q in qids:
        for d in DRAWS:
            a = p_ans.get(f"{PACKAGE}|{q}|d{d}")
            if a is None:
                raise Refused(f"{PACKAGE}|{q}|d{d}: no package record")
            if (a.get("context") or {}).get("file_sha256") != file_sha:
                raise Refused(f"{a['answer_key']}: its context file sha256 is not {rel(CONTEXT)}'s")
            need[a["ctx_uid"]] = a
    return need


def calls_by_ctx(lines, need: dict) -> dict:
    """{ctx_uid: call records} from calls.jsonl lines: a record is taken when its ctx_uid is an answer's and its seq
    is one that answer lists. A record of another ctx_uid is never taken, so an answer missing one shows up in
    package_trace as a missing seq."""
    by_ctx = {u: [] for u in need}
    seqs = {u: set(a["calls"]["seqs"]) for u, a in need.items()}
    for raw in lines:
        if not raw.strip():
            continue
        c = json.loads(raw)
        u = c.get("ctx_uid")
        if u in by_ctx and c.get("seq") in seqs[u]:
            by_ctx[u].append(c)
    return by_ctx


def reproduce_s511(rows: dict, one, many, s511_by_set: dict) -> list[str]:
    """Mentori RLM-10's every-key-paper counts must equal S511's results.json (reading.by_set)."""
    out = []
    for sub, name in ((one, "one-paper"), (many, "many-paper")):
        n = sum(rows[(MENTORI, q, d)]["every_key_paper"] for q in sub for d in DRAWS)
        w = s511_by_set[name]["rlm_10"]["every_key_paper_read"]
        if n != w:
            raise Refused(f"reproduce failed: Mentori RLM-10 every key paper read on {name}: {n}, S511 {w}")
        out.append(f"Mentori RLM-10 {name} answers with every key paper among the passages: {n} = S511 {w}")
    return out


def read_inputs():
    import S463_fig2_ranking as S463
    import S511_g2_matched_budget as S511
    import fig_repro as FR
    shas = {}
    groups = S463.key_groups()
    reruns = S463.rerun_keys()
    fig2 = FR.check_committed(FR.frozen("fig2"))
    collect = fig2 / "g1_collect.jsonl"
    side = json.loads(collect.with_name(collect.name + ".json").read_text())
    outs = (side.get("_provenance") or {}).get("inputs") or []
    relocate = {str(Path(outs[0]).parent): str(fig2)}
    k1 = FR.frozen("k1_inputs_runs", "k1_inputs_runs")
    g1r15 = FR.frozen("fig2_g1r15_inputs", "fig2_g1r15_inputs")
    members = FR.RECOMPUTE / "frozen_inputs" / "members" / "k1_inputs_runs.sha256"
    k1_man = {}
    for ln in members.read_text().splitlines():
        if ln.strip():
            h, n = ln.split(None, 1)
            k1_man["runs/" + n.strip().split("/", 1)[1]] = h
    answers, a_in, _ = S463.read_answers([k1, g1r15 / "runs"], manifests={str(k1): k1_man})
    read = S463.read_collect(collect, list(DRAWS), groups, reruns, answers=answers, relocate=relocate)
    s6 = FR.frozen("fig3_s6")
    jr = S463.judge_rows(read, collect, groups, reruns, list(DRAWS), s6_root=s6, answers=answers)
    g6_answers = FR.check_committed(FR.frozen(S463.G6_SET)) / S463.G6_RUN10 / "answers.jsonl"
    want = json.loads((FR.frozen(S463.G6_SET) / "SOURCE_MTIMES.json").read_text())["files"][
        f"findings/runs/{S463.G6_RUN10}/answers.jsonl"]["sha256"]
    check_sha(g6_answers, want, "its SOURCE_MTIMES.json")
    extra = S463.read_extra(s6, groups, list(DRAWS), g6_answers=g6_answers)
    cells = {k: v for k, v in read["cells"].items() if k[0] == MENTORI}
    cells.update({k: v for k, v in extra["cells"].items() if k[0] == PACKAGE})
    qs = S511.questions()
    for p in a_in:
        if "rlm_10" in p:
            shas[rel(p)] = a_in[p]
    shas[rel(collect)] = sha256_file(collect)
    shas[rel(g6_answers)] = sha256_file(g6_answers)
    for f in sorted(s6.glob("*g6*")) + sorted(s6.glob("*g1*collect*")):
        if f.is_file():
            shas[rel(f)] = sha256_file(f)
    calls_p = FR.frozen("g6_calls_after_d135", "g6_calls_after_d135") / S463.G6_RUN10 / "calls.jsonl"
    shas[rel(calls_p)] = sha256_file(calls_p)
    shas[rel(CONTEXT)] = sha256_file(CONTEXT)
    shas[rel(S511_RESULTS)] = sha256_file(S511_RESULTS)
    shas["~/l1_inputs/store/chroma.sqlite3 (S511.STORE_SHA, pinned in S511; S511.paper_map checks it before reading)"] = \
        S511.STORE_SHA
    return {"S463": S463, "S511": S511, "groups": groups, "qs": qs, "answers": answers, "cells": cells, "jr": jr,
            "g6_answers": g6_answers, "calls": calls_p, "shas": shas}


def full_record(source: str) -> dict:
    """The record line S463.read_answers took ('<path>:<line>')."""
    path, n = source.rsplit(":", 1)
    with open(path) as f:
        for i, raw in enumerate(f, 1):
            if i == int(n):
                return json.loads(raw)
    raise Refused(f"{source}: no such line")


def kind_of(qs: dict, q: str) -> str:
    v = qs[q]
    return v["kind"] if v["group"] == "answerable" else v["group"]


def build(inp: dict) -> dict:
    from experiments.runner.gemini_client import raised_before_d89
    qs, cells, S511 = inp["qs"], inp["cells"], inp["S511"]
    qids = sorted(qs)
    one = [q for q in qids if kind_of(qs, q) == "one"]
    many = [q for q in qids if kind_of(qs, q) == "many"]

    # reproduce 1: Figure 3a's committed pass rates
    sd = one_workbook(FIG3_DIR)
    want = committed_rates(sd)
    got = {(c, g): question_rate(cells, c, sub) for c in (MENTORI, PACKAGE) for g, sub in (("one", one), ("many", many))}
    rep_lines = reproduce(got, want)
    inp["shas"][rel(sd)] = sha256_file(sd)

    # Mentori traces
    m_recs = {}
    for q in qids:
        for d in DRAWS:
            k = f"{INDEX}|{MENTORI}|{q}|d{d}"
            a = inp["answers"][k]
            m_recs[(q, d)] = check_record(k, full_record(a["source"]), a["answer_sha256"])
    ids = {i for r in m_recs.values() for i in
           (((r["generation"].get("rlm") or {}).get("metadata") or {}).get("passages_seen") or [])}
    paper_of = S511.paper_map(ids)

    # package traces
    pindex = PaperIndex(context_texts(json.loads(CONTEXT.read_text())))
    p_ans = {}
    for raw in inp["g6_answers"].read_text().splitlines():
        if raw.strip():
            r = json.loads(raw)
            p_ans[r["answer_key"]] = r
    need = package_records(p_ans, qids, sha256_file(CONTEXT))
    with open(inp["calls"]) as f:
        by_ctx = calls_by_ctx(f, need)
    inp["g6_records"] = (p_ans, by_ctx)    # G17's part (--g17) reads them; nothing written depends on this line

    rows = {}
    for q in qids:
        for d in DRAWS:
            mt = mentori_trace(m_recs[(q, d)], paper_of)
            a = p_ans[f"{PACKAGE}|{q}|d{d}"]
            pt = package_trace(a, by_ctx[a["ctx_uid"]], pindex, raised_before_d89)
            for c, t in ((MENTORI, mt), (PACKAGE, pt)):
                cell = cells[(c, q, d)]
                key_papers = set(qs[q]["papers"])
                t.update(question_id=q, draw=d, group=kind_of(qs, q), cell=cell["kind"],
                         score=cell.get("score"), pass4=pass_of(cell),
                         every_key_paper=(key_papers <= set(t["papers"])) if qs[q]["group"] == "answerable" else None,
                         key_papers=sorted(key_papers))
                if c == PACKAGE:
                    t["every_key_paper_deep"] = (key_papers <= set(t["papers_deep"])) \
                        if qs[q]["group"] == "answerable" else None
                rows[(c, q, d)] = t

    # reproduce 2: S511's every-key-paper counts for Mentori RLM-10 (the same definition, the same records)
    rep2 = reproduce_s511(rows, one, many, json.loads(S511_RESULTS.read_text())["reading"]["by_set"])

    # table by strategy x group
    table = []
    for c in (MENTORI, PACKAGE):
        for g in GROUP_ORDER:
            rs = [rows[(c, q, d)] for q in qids if kind_of(qs, q) == g for d in DRAWS]
            qg = sorted({r["question_id"] for r in rs})
            row = {"strategy": c, "label": LABEL[c], "group": g, "questions": len(qg), "answers": len(rs),
                   "sub_calls_ok": quart([r["sub_calls_ok"] for r in rs]),
                   "sub_calls_with_paper_text": quart([r["sub_calls_with_paper_text"] for r in rs]),
                   "sub_calls_with_paper_text_under_3": sum(1 for r in rs if r["sub_calls_with_paper_text"] < 3),
                   "root_turns": quart([r["root_turns"] for r in rs]),
                   "papers": quart([r["n_papers"] for r in rs]),
                   "words": quart([r["words"] for r in rs]),
                   "pass4_rate_pct": question_rate(cells, c, qg),
                   "sub_calls_under_3": sum(1 for r in rs if (r["sub_calls_ok"] or 0) < 3)}
            if c == MENTORI:
                row.update(papers_cited=quart([r["n_papers_cited"] for r in rs]),
                           gate_rejected_once=sum(1 for r in rs if r["rejections"] >= 1),
                           gate_rejections_total=sum(r["rejections"] for r in rs),
                           gate_rejections_dist={str(k): sum(1 for r in rs if r["rejections"] == k)
                                                 for k in sorted({r["rejections"] for r in rs})},
                           gate_rejections_by_kind={kd: sum(r["rejection_kinds"].count(kd) for r in rs)
                                                    for kd in (GATE_COUNT, GATE_SUBSTANCE, GATE_UNKNOWN)},
                           gate_answers_by_kind={kd: sum(1 for r in rs if kd in r["rejection_kinds"])
                                                 for kd in (GATE_COUNT, GATE_SUBSTANCE, GATE_UNKNOWN)},
                           final_after_max_rejections=sum(1 for r in rs if r["after_max"]),
                           unmapped_ids=sum(r["unmapped_ids"] for r in rs))
            else:
                row.update(papers_deep=quart([r["n_papers_deep"] for r in rs]),
                           answer_papers_deep_by_repeats_only=sum(len(r["papers_deep_by_repeats_only"]) for r in rs),
                           forced_final=sum(1 for r in rs if r["forced_final"]))
                if g in ("one", "many"):
                    for full in (True, False):
                        v = [r["pass4"] for r in rs if r["every_key_paper_deep"] is full and r["pass4"] is not None]
                        row[f"pass4_every_key_paper_deep_{str(full).lower()}"] = [sum(v), len(v)]
            if g in ("one", "many"):
                for full in (True, False):
                    v = [r["pass4"] for r in rs if r["every_key_paper"] is full and r["pass4"] is not None]
                    row[f"pass4_every_key_paper_{str(full).lower()}"] = [sum(v), len(v)]
                if c == MENTORI:
                    for rej in (True, False):
                        v = [r["pass4"] for r in rs if (r["rejections"] >= 1) is rej and r["pass4"] is not None]
                        row[f"pass4_gate_rejected_{str(rej).lower()}"] = [sum(v), len(v)]
                        v = [r["pass4"] for r in rs if (GATE_COUNT in r["rejection_kinds"]) is rej
                             and r["pass4"] is not None]
                        row[f"pass4_gate_rejected_under_3_{str(rej).lower()}"] = [sum(v), len(v)]
            table.append(row)

    # paired view on many-paper questions
    paired = []
    for q in many:
        mp = [rows[(MENTORI, q, d)]["n_papers"] for d in DRAWS]
        pp = [rows[(PACKAGE, q, d)]["n_papers"] for d in DRAWS]
        pd = [rows[(PACKAGE, q, d)]["n_papers_deep"] for d in DRAWS]
        mr = [rows[(MENTORI, q, d)]["pass4"] for d in DRAWS if rows[(MENTORI, q, d)]["pass4"] is not None]
        pr = [rows[(PACKAGE, q, d)]["pass4"] for d in DRAWS if rows[(PACKAGE, q, d)]["pass4"] is not None]
        if not mr or not pr:
            continue
        paired.append({"question_id": q, "key_papers": len(qs[q]["papers"]),
                       "d_papers": sum(mp) / 3 - sum(pp) / 3, "d_papers_deep": sum(mp) / 3 - sum(pd) / 3,
                       "package_papers_deep": pd, "d_pass_pct": 100 * (sum(mr) / len(mr) - sum(pr) / len(pr)),
                       "mentori_papers": mp, "package_papers": pp, "mentori_pass": mr, "package_pass": pr})
    x = [p["d_papers"] for p in paired]
    y = [p["d_pass_pct"] for p in paired]
    r = pearson(x, y)
    lo, hi, skipped = boot_r(x, y)
    xd = [p["d_papers_deep"] for p in paired]
    r_deep = pearson(xd, y)
    lo_d, hi_d, skipped_d = boot_r(xd, y)

    # concordant candidates
    def detail(q):
        return {"question_id": q, "group": kind_of(qs, q), "key_papers": qs[q]["papers"],
                "draws": {LABEL[c]: [{"draw": d, "score": rows[(c, q, d)]["score"], "cell": rows[(c, q, d)]["cell"],
                                      "sub_calls_ok": rows[(c, q, d)]["sub_calls_ok"],
                                      "sub_calls_with_paper_text": rows[(c, q, d)]["sub_calls_with_paper_text"],
                                      "papers": rows[(c, q, d)]["n_papers"],
                                      "every_key_paper": rows[(c, q, d)]["every_key_paper"],
                                      **({"papers_deep": rows[(c, q, d)]["n_papers_deep"]} if c == PACKAGE else {}),
                                      **({"gate_rejections": rows[(c, q, d)]["rejections"],
                                          "gate_rejection_kinds": rows[(c, q, d)]["rejection_kinds"]}
                                         if c == MENTORI else {})}
                                     for d in DRAWS] for c in (MENTORI, PACKAGE)}}
    conc = {}
    for g, sub in (("many", many), ("one", one)):
        conc[f"mentori_3of3_package_0of3_{g}"] = [detail(q) for q in concordant(rows, sub, MENTORI, PACKAGE)]
        conc[f"package_3of3_mentori_0of3_{g}"] = [detail(q) for q in concordant(rows, sub, PACKAGE, MENTORI)]

    return {"reproduce": rep_lines + rep2, "table": table,
            "paired": {"questions": len(paired), "r": r, "ci95": [lo, hi], "resamples": N_BOOT, "seed": SEED,
                       "resamples_skipped": skipped,
                       "sensitivity_package_papers_deep": {"r": r_deep, "ci95": [lo_d, hi_d],
                                                           "resamples_skipped": skipped_d},
                       "rows": paired},
            "concordant": conc,
            "answers": [{"strategy": c, **{k: v for k, v in rows[(c, q, d)].items() if k not in ("papers",)},
                         "papers": rows[(c, q, d)]["papers"]}
                        for c in (MENTORI, PACKAGE) for q in qids for d in DRAWS],
            "judge_rows": inp["jr"].get("status"),
            "matching": {"K": K, "stride": STRIDE, "min_hits": MIN_HITS, "deep_distinct_chars": DEEP_CHARS,
                         "answer_paper_pairs_deep_by_repeats_only": sum(
                             len(rows[(PACKAGE, q, d)]["papers_deep_by_repeats_only"]) for q in qids for d in DRAWS),
                         "ambiguous_runs_dropped": sum(1 for v in pindex.idx.values() if v < 0)}}


# ---------------------------------------------------------------------------------------------------------------
# G17 (D240, --g17): the same definitions on G17's three arms beside G1's and G6's draw 1
# ---------------------------------------------------------------------------------------------------------------
G17_ARMS = ("rlm_10_ctrl", "rlm_10_nosearch", "rlm_10_nogate")
G17_LABEL = {"rlm_10_ctrl": "R' Mentori RLM-10, today's code", "rlm_10_nosearch": "B search off",
             "rlm_10_nogate": "C gate off"}
G17_ORDER = (MENTORI, *G17_ARMS, PACKAGE)
G17_LABEL_ALL = {MENTORI: "G1 Mentori RLM-10 (Figure 3)", PACKAGE: "G6 package RLM-10", **G17_LABEL}
L2_D181 = ROOT / "findings" / "recompute" / "L2_d181" / "concept_recall.jsonl"
L3_D181 = ROOT / "findings" / "recompute" / "L3_d181" / "concept_recall.jsonl"
L2_D135_D181 = ROOT / "findings" / "recompute" / "L2_d135_d181" / "concept_recall.jsonl"   # G6 after D135 (Figure 3a)
G17_MEASURES = ("sub_calls_ok", "sub_calls_with_paper_text", "root_turns", "n_papers", "words", "model_calls", "tokens",
                "wall_s", "concept_recall")


def calls_cost(calls: list[dict]) -> dict:
    """Model calls and tokens (prompt + output + thinking) over an answer's call records or summaries."""
    t = sum((c.get("prompt_tokens") or 0) + (c.get("output_tokens") or 0) + (c.get("thinking_tokens") or 0)
            for c in calls)
    return {"model_calls": len(calls), "tokens": t}


def g17_last(path: Path) -> dict:
    out = {}
    with open(path) as f:
        for raw in f:
            if raw.strip():
                r = json.loads(raw)
                out[r["answer_key"]] = r
    return out


def g17_cells(judge: Path | None, qs: dict) -> dict:
    """{answer_key: cell} from S572's judge rows under <judge>/judge/*/ (S463.latest_by_ident and cell_of, Figure 3's
    Rule 10), or {} without a judge folder."""
    if judge is None:
        return {}
    import S463_fig2_ranking as S463
    out = {}
    for d in S463.latest_by_ident(judge).values():
        q = d["answer_key"].split("|")[2]
        cell, why = S463.cell_of(d, qs[q]["group"])
        if cell is None:
            raise Refused(f"{d['answer_key']}: {why}")
        out[d["answer_key"]] = cell
    return out


def g17_reading(R: dict, inp: dict, runs_root: Path, judge: Path | None, cr: Path | None,
                extra: list | None = None) -> dict:
    """Per answer at draw 1 on the 86, for G1 RLM-10, G6 cap 10 and G17's three arms, the S571 measures (mentori_trace
    and package_trace, as for G1 and G6 above), plus model calls, tokens and wall time from the records, pass at 4 and
    at 3 (S463.cell_of on the judge rows; G1 and G6 from Figure 3's cells), concept recall (D181: L3_d181 for G1,
    L2_d181 cap 10 for G6 where the answer's sha256 matches, S573's rows for G17), stop reason and failure; B's
    refused search attempts; C's answers under 3 sub-calls. Then the table: strategy x kind x measure.

    extra (D249 O1, --g17-d23): more sources, each (draws, runs_root, judge, cr), e.g. [((2, 3), d23 root, d23 judge,
    d23 rows)]: every strategy is then read at draw 1 and those draws, the table pools them and table_by_draw is added.
    Without extra the result is draw 1's, as before."""
    import S470_l1_signals as S470
    qs, S511 = inp["qs"], inp["S511"]
    ids = sorted(q for q in qs if qs[q]["group"] == "answerable")
    sources = [((1,), runs_root, judge, cr)] + list(extra or [])
    draws = tuple(d for src in sources for d in src[0])
    if len(set(draws)) != len(draws) or 1 not in draws:
        raise Refused(f"--g17: draws {draws} read twice or without draw 1")
    base = {(a["strategy"], a["question_id"], a["draw"]): a for a in R["answers"] if a["draw"] in draws}
    rows = []
    # G1 and G6 at draw 1: the rows build() made, with calls, tokens and time from their records
    l3 = {r["answer_key"]: r for r in map(json.loads, L3_D181.read_text().splitlines()) if r["draw"] in draws}
    # G6's concept recall: L2_d181 at draw 1 alone (as D240's reading); with draws 2 and 3 L2_d135_d181, S474's reading
    # of G6 after the D135 reruns (Figure 3a's), whose answers are the g6_d135 records read here (L2_d181 holds a
    # pre-D135 failed answer at 16_ppr_ethiopia_TE3 draw 2); both hold G5's rlm_10 rows at draw 1 and cap 10 beside
    # G6's, so G6's rows only (the answer's sha256 decides)
    l2_file = L2_D181 if draws == (1,) else L2_D135_D181
    l2 = {(r["question_id"], r["draw"]): r for r in map(json.loads, l2_file.read_text().splitlines())
          if r.get("cap") == 10 and r["draw"] in draws and r.get("system", "G6") == "G6"}
    p_ans, by_ctx = inp["g6_records"]
    cr_unmatched = {MENTORI: 0, PACKAGE: 0}
    for d in draws:
        for q in ids:
            k = f"{INDEX}|{MENTORI}|{q}|d{d}"
            rec = full_record(inp["answers"][k]["source"])
            g = rec.get("generation") or {}
            a_sha = S470.sha256_text(g.get("answer") or "")
            crv = l3[k]["concept_recall"] if l3.get(k, {}).get("answer_sha256") == a_sha else None
            cr_unmatched[MENTORI] += crv is None
            rows.append({**base[(MENTORI, q, d)], **calls_cost(g.get("calls") or []), "wall_s": g.get("latency_s"),
                         "failed": bool(g.get("error")), "concept_recall": crv,
                         "pass3": pass_of(inp["cells"][(MENTORI, q, d)], 3)})
            pa = p_ans[f"{PACKAGE}|{q}|d{d}"]
            p_sha = S470.sha256_text(pa.get("answer") or "")
            crv = l2[(q, d)]["concept_recall"] if l2.get((q, d), {}).get("answer_sha256") == p_sha else None
            cr_unmatched[PACKAGE] += crv is None
            rows.append({**base[(PACKAGE, q, d)], **calls_cost(by_ctx[pa["ctx_uid"]]), "wall_s": pa.get("wall_s"),
                         "failed": bool(pa.get("error")), "concept_recall": crv,
                         "pass3": pass_of(inp["cells"][(PACKAGE, q, d)], 3)})
    # G17's sinks: one folder per source, each holding the 86 at that source's draws and no other key
    recs, inputs = {arm: {} for arm in G17_ARMS}, {}
    if draws != (1,):
        inputs.update({str(f): sha256_file(f) for f in (L3_D181, l2_file)})
    for s_draws, s_root, _, _ in sources:
        what = "at draw 1" if s_draws == (1,) else f"at draws {', '.join(map(str, s_draws))}"
        flag = "--g17" if s_draws == (1,) else "--g17-d23"
        for arm in G17_ARMS:
            f = Path(s_root) / "runs" / f"exp_01__{arm}__{INDEX}" / "answers.jsonl"
            if not f.exists():
                raise Refused(f"{flag}: no {f}")
            inputs[str(f)] = sha256_file(f)
            last = g17_last(f)
            want = {f"{INDEX}|{arm}|{q}|d{d}" for d in s_draws for q in ids}
            if set(last) != want:
                raise Refused(f"{flag}: {f} holds {len(set(last) - want)} keys outside the 86 {what} and misses "
                              f"{len(want - set(last))}")
            recs[arm].update(last)
    ids_seen = {i for last in recs.values() for r in last.values()
                for i in ((((r.get("generation") or {}).get("rlm") or {}).get("metadata") or {}).get("passages_seen") or [])}
    paper_of = S511.paper_map(ids_seen)
    cells, crs = {}, {}
    for s_draws, _, s_judge, s_cr in sources:
        got = g17_cells(s_judge, qs)
        bad = [k for k in got if int(k.rsplit("|d", 1)[1]) not in s_draws]
        if bad:
            raise Refused(f"judge rows of {s_judge} hold {len(bad)} answers outside draws {s_draws} (first {bad[0]})")
        cells.update(got)
        if s_cr is not None:
            got = {r["answer_key"]: r for r in map(json.loads, Path(s_cr).read_text().splitlines())}
            bad = [k for k, r in got.items() if r.get("draw") not in s_draws]
            if bad:
                raise Refused(f"concept recall rows of {s_cr} hold {len(bad)} answers outside draws {s_draws}")
            crs.update(got)
            inputs[str(s_cr)] = sha256_file(s_cr)
    for arm in G17_ARMS:
        for d, q in ((d, q) for d in draws for q in ids):
            k = f"{INDEX}|{arm}|{q}|d{d}"
            rec = recs[arm][k]
            g = rec.get("generation") or {}
            md = (g.get("rlm") or {}).get("metadata") or {}
            t = mentori_trace(rec, paper_of)
            key_papers = set(qs[q]["papers"])
            cell = cells.get(k)
            c_row = crs.get(k)
            if c_row is not None and c_row.get("answer_sha256") != S470.sha256_text(g.get("answer") or ""):
                raise Refused(f"--g17-concept-recall: {k} was scored on another answer")
            t.update(strategy=arm, question_id=q, draw=d, group=kind_of(qs, q), cell=cell["kind"] if cell else None,
                     score=cell.get("score") if cell else None, pass4=pass_of(cell) if cell else None,
                     pass3=pass_of(cell, 3) if cell else None, every_key_paper=key_papers <= set(t["papers"]),
                     key_papers=sorted(key_papers), **calls_cost(g.get("calls") or []), wall_s=g.get("latency_s"),
                     failed=bool(g.get("error")), concept_recall=c_row["concept_recall"] if c_row else None,
                     search_attempts=(md.get("search_tools") or {}).get("n_attempts"))
            rows.append(t)
    table = g17_table(rows)
    head = {"decision": "D240", "draw": 1} if draws == (1,) else {"decision": "D249", "draws": list(draws)}
    out = {**head, "questions": len(ids), "strategies": list(G17_ORDER),
           "labels": G17_LABEL_ALL, "judged": all(s[2] is not None for s in sources),
           "concept_recall_given": all(s[3] is not None for s in sources),
           "concept_recall_unmatched_answers": cr_unmatched, "inputs_sha256": inputs,
           "definitions": "S571's (mentori_trace, package_trace, pass_of, every key paper); model_calls and tokens "
                          "over the answer's call records; wall_s: generation.latency_s (Mentori), wall_s (package); "
                          "concept recall D181 (L3_d181, L2_d181 cap 10, S573)",
           "table": table}
    if draws != (1,):
        out["definitions"] = out["definitions"].replace("L2_d181 cap 10", "L2_d135_d181 cap 10")
    if draws != (1,):
        out["table_by_draw"] = {str(d): g17_table([r for r in rows if r["draw"] == d]) for d in draws}
    out["answers"] = [{k: v for k, v in r.items() if k != "papers"} | {"papers": r.get("papers")} for r in rows]
    return out


def g17_table(rows: list) -> list:
    """Strategy x kind x measure over the rows given (g17_reading)."""
    from collections import Counter
    table = []
    for c in G17_ORDER:
        for grp in ("one", "many", "all"):
            rs = [r for r in rows if r["strategy"] == c and (grp == "all" or r["group"] == grp)]
            row = {"strategy": c, "label": G17_LABEL_ALL[c], "group": grp, "answers": len(rs)}
            for t_, f_ in (("pass4", "pass4"), ("pass3", "pass3")):
                v = [r[f_] for r in rs if r.get(f_) is not None]
                row[f"{t_}_pct"] = 100 * sum(v) / len(v) if v else None
                row[f"{t_}_answers_read"] = len(v)
            for m in G17_MEASURES:
                row[m] = quart([r.get(m) for r in rs if r.get(m) is not None])
            row["every_key_paper"] = [sum(1 for r in rs if r["every_key_paper"]), len(rs)]
            row["failed"] = sum(1 for r in rs if r["failed"])
            row["stop_reasons"] = dict(sorted(Counter(str(r["stop_reason"]) for r in rs).items()))
            row["sub_calls_under_3"] = sum(1 for r in rs if (r.get("sub_calls_ok") or 0) < MIN_LLM_CALLS)
            if c != PACKAGE:
                row["gate_rejected_once"] = sum(1 for r in rs if (r.get("rejections") or 0) >= 1)
            if c == "rlm_10_nosearch":
                row["search_attempts_total"] = sum(r.get("search_attempts") or 0 for r in rs)
                row["answers_with_search_attempt"] = sum(1 for r in rs if r.get("search_attempts"))
            table.append(row)
    return table


def write_g17_md(G: dict, path: Path) -> None:
    if "draws" not in G:
        L = ["# S571 --g17: how the three G17 arms read, beside G1 and G6 at draw 1 (D240, association)", "",
             f"Draw 1, the {G['questions']} answerable questions of Figure 3a. Judged: {G['judged']}; concept recall "
             f"given: {G['concept_recall_given']}. Each cell: median [quartile 25, quartile 75] over answers.", ""]
        tables = [(None, G["table"])]
    else:
        ds = ", ".join(map(str, G["draws"]))
        L = [f"# S571 --g17 --g17-d23: the three G17 arms beside G1 and G6 at draws {ds} (D249 O1, association)", "",
             f"Draws {ds}, the {G['questions']} answerable questions of Figure 3a. Judged: {G['judged']}; concept "
             f"recall given: {G['concept_recall_given']}. Each cell: median [quartile 25, quartile 75] over answers; "
             "the first table pools the draws, one table per draw follows.", ""]
        tables = [(f"Draws {ds} pooled", G["table"])] + [(f"Draw {d}", t) for d, t in G["table_by_draw"].items()]
    for title, rows in tables:
        if title is not None:
            L += [f"## {title}", ""]
        L += _g17_md_rows(rows)
        if title is not None:
            L.append("")
    path.write_text("\n".join(L).rstrip("\n") + "\n")


def _g17_md_rows(table: list) -> list:
    def pct(v):
        return "n/a" if v is None else f"{v:.1f}%"
    L = ["| Strategy | Questions | Answers | Pass at 4 | Pass at 3 | Sub-calls | With paper text | Papers | Every key "
         "paper | Root turns | Words | Model calls | Tokens | Wall s | Concept recall | Failed |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in table:
        L.append(f"| {r['label']} | {r['group']} | {r['answers']} | {pct(r['pass4_pct'])} | {pct(r['pass3_pct'])} | "
                 f"{fq(r['sub_calls_ok'], 0)} | {fq(r['sub_calls_with_paper_text'], 0)} | {fq(r['n_papers'], 0)} | "
                 f"{r['every_key_paper'][0]}/{r['every_key_paper'][1]} | {fq(r['root_turns'], 0)} | "
                 f"{fq(r['words'], 0)} | {fq(r['model_calls'], 0)} | {fq(r['tokens'], 0)} | {fq(r['wall_s'], 0)} | "
                 f"{fq(r['concept_recall'], 3)} | {r['failed']} |")
    return L


# ---------------------------------------------------------------------------------------------------------------
# output
# ---------------------------------------------------------------------------------------------------------------
def fq(t, nd=1):
    m, a, b = t
    if m is None:
        return "n/a"
    f = (lambda v: f"{v:.{nd}f}".rstrip("0").rstrip(".")) if nd else (lambda v: f"{v:.0f}")
    return f"{f(m)} [{f(a)}, {f(b)}]"


def frac(v):
    k, n = v
    return f"{k}/{n} ({100 * k / n:.1f}%)" if n else "0/0"


KIND_LABEL = {GATE_COUNT: "under 3 sub-calls counted", GATE_SUBSTANCE: "3 or more counted (so no substance)",
              GATE_UNKNOWN: "cannot tell"}


def write_md(R: dict, path: Path) -> None:
    pv = R["_provenance"]
    L = ["# S571: how Mentori RLM-10 and package RLM-10 read (association, stored runs)", "",
         f"Generated by `uv run --frozen python {SCRIPT}` at {pv['at']} (HEAD {pv['git_head'][:8]}, tracked files "
         f"changed: {'yes' if pv['worktree_dirty'] else 'no'}; S571's code dependencies changed from HEAD: "
         f"{', '.join(pv['dependencies_changed_from_head']) or 'none'}). Descriptive only: no model call, no causal "
         f"claim. Code line numbers are at commit 6318e8e8.", "",
         "## Reproduce", ""] + [f"- {x}" for x in R["reproduce"]] + ["", f"Judge rows: {R['judge_rows']}.", "",
         "## By strategy and question type", "",
         "Medians with [Q1, Q3] (numpy linear percentiles) over answers (3 draws per question).", "",
         "- All sub-calls: every successful sub-call. Mentori = `sub_calls_ok`, the count the gate reads: it includes "
         "llm_query(prompt) with no passages and calls handed passages as strings, and leaves out calls handed an "
         "empty list. Package = `calls.sub - calls.sub_failed`.",
         "- With paper text: Mentori = successful sub-calls handed chunk ids (`generation.calls[].n_passages` > 0; "
         "passages handed as strings carry no id, so a lower bound); package = successful sub-calls whose "
         "`prompt_sent` matched a paper (2 or more sampled 64-character windows).",
         "- Papers: Mentori = distinct papers among the chunks returned to its code (PROXY, an upper bound on what "
         "its sub-calls were handed; the record holds each sub-call's passage count, not its ids); package = distinct "
         "papers matched in a successful sub-call's prompt.",
         f"- In depth (package): papers with at least {DEEP_CHARS:,} distinct characters covered across the answer's "
         "successful sub-calls; text sent to two sub-calls counts once.",
         "- Gate rejected: Mentori's metadata.rejections at least once, either kind (fewer than 3 counted sub-calls, "
         "or an answer without substance; the record does not say which, see the next table).",
         "- Pass rate = Figure 3's (mean over questions of the share of draws scoring 4 or more; failed answers count "
         "as fails).", "",
         "| Strategy | Type | Questions | Answers | All sub-calls | With paper text | Root turns | Papers | Papers "
         "cited (Mentori) / in depth (package) | Words | All sub-calls under 3 | With paper text under 3 | Gate "
         "rejected at least once | final_after_max_rejections | Pass rate at 4 |",
         "|---|---|---:|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|"]
    for r in R["table"]:
        L.append(f"| {r['label']} | {GROUP_LABEL[r['group']]} | {r['questions']} | {r['answers']} | "
                 f"{fq(r['sub_calls_ok'])} | {fq(r['sub_calls_with_paper_text'])} | {fq(r['root_turns'])} | "
                 f"{fq(r['papers'])} | "
                 f"{fq(r['papers_cited']) if 'papers_cited' in r else fq(r['papers_deep'])} | {fq(r['words'], 0)} | "
                 f"{r['sub_calls_under_3']} | {r['sub_calls_with_paper_text_under_3']} | "
                 f"{frac([r['gate_rejected_once'], r['answers']]) if 'gate_rejected_once' in r else 'no gate'} | "
                 f"{r.get('final_after_max_rejections', 'n/a')} | {r['pass4_rate_pct']:.1f}% |")
    L += ["", "Mentori gate rejections per answer (count of answers with 0, 1, 2, 3 rejections):", ""]
    for r in R["table"]:
        if "gate_rejections_dist" in r:
            L.append(f"- {GROUP_LABEL[r['group']]}: " + ", ".join(f"{k}: {v}" for k, v in r["gate_rejections_dist"].items()))
    L += ["", "## Mentori gate rejections by kind", "",
          "The gate rejects FINAL when `sub_calls_ok < 3 or not has_substance` (orchestrator.py:440 at 6318e8e8). "
          "The record does not label root calls, so S571 places them (`root_placements`: the first call is root, a "
          "root call carries no chunk ids, root prompt_tokens rise strictly because the history only grows) and "
          "counts the successful sub-calls made before each rejection. Under 3 counted: the count alone rejects (the "
          "answer may also have lacked substance). 3 or more counted: the count was met, so the answer lacked "
          "substance. Cannot tell: the placement is not unique and the placements disagree, or calls handed an empty "
          "list (not counted by the gate) cannot be told from llm_query calls (both carry no ids).", "",
          "| Type | Rejections | Under 3 sub-calls counted | 3 or more counted (no substance) | Cannot tell | "
          "Answers with an under-3 rejection |", "|---|---:|---:|---:|---:|---:|"]
    for r in R["table"]:
        if "gate_rejections_by_kind" in r:
            k = r["gate_rejections_by_kind"]
            L.append(f"| {GROUP_LABEL[r['group']]} | {r['gate_rejections_total']} | {k[GATE_COUNT]} | "
                     f"{k[GATE_SUBSTANCE]} | {k[GATE_UNKNOWN]} | {r['gate_answers_by_kind'][GATE_COUNT]} |")
    L += ["", "## Pass at 4 by whether the answer read every paper the key names", "",
          "Every key paper = all of the key's source_files among the papers above (S511's definition, "
          "S511_g2_matched_budget.py:762-787; for Mentori the same records and count as S511). Answer-level counts, "
          "unscored answers left out.", "",
          "| Strategy | Type | Every key paper read: pass | Not every key paper: pass |", "|---|---|---|---|"]
    for r in R["table"]:
        if r["group"] in ("one", "many"):
            L.append(f"| {r['label']} | {GROUP_LABEL[r['group']]} | {frac(r['pass4_every_key_paper_true'])} | "
                     f"{frac(r['pass4_every_key_paper_false'])} |")
    for r in R["table"]:
        if r["group"] in ("one", "many") and "pass4_every_key_paper_deep_true" in r:
            L.append(f"| {r['label']}, in depth ({DEEP_CHARS:,} or more distinct characters of each key paper) | "
                     f"{GROUP_LABEL[r['group']]} | {frac(r['pass4_every_key_paper_deep_true'])} | "
                     f"{frac(r['pass4_every_key_paper_deep_false'])} |")
    L += ["", "Mentori RLM-10, pass at 4 by whether the gate rejected FINAL:", ""]
    for r in R["table"]:
        if r["strategy"] == MENTORI and r["group"] in ("one", "many"):
            L.append(f"- {GROUP_LABEL[r['group']]}: rejected at least once (either kind) "
                     f"{frac(r['pass4_gate_rejected_true'])}, never rejected {frac(r['pass4_gate_rejected_false'])}; "
                     f"rejected at least once with under 3 sub-calls counted "
                     f"{frac(r['pass4_gate_rejected_under_3_true'])}, not so rejected "
                     f"{frac(r['pass4_gate_rejected_under_3_false'])}")
    P = R["paired"]
    L += ["", "## Paired view, many-paper questions", "",
          f"Per question: Mentori minus package in mean distinct papers read (over 3 draws) against Mentori minus "
          f"package in pass rate at 4 (points). n = {P['questions']} questions. Pearson r = "
          f"{P['r']:.3f}, two-sided 95% percentile bootstrap over questions [{P['ci95'][0]:.3f}, {P['ci95'][1]:.3f}] "
          f"({P['resamples']:,} resamples, seed {P['seed']}, {P['resamples_skipped']} skipped for no spread). "
          f"Descriptive only; the two paper measures are not the same instrument (see above). Sensitivity, the "
          f"package's papers read in depth in place of its papers: r = {P['sensitivity_package_papers_deep']['r']:.3f} "
          f"[{P['sensitivity_package_papers_deep']['ci95'][0]:.3f}, "
          f"{P['sensitivity_package_papers_deep']['ci95'][1]:.3f}].", "",
          "| Question | Key papers | Mentori papers d1-d3 | Package papers d1-d3 | Package in depth d1-d3 | "
          "Mentori pass d1-d3 | Package pass d1-d3 | d papers | d papers (depth) | d pass (pts) |",
          "|---|---:|---|---|---|---|---|---:|---:|---:|"]
    for p in sorted(P["rows"], key=lambda z: z["question_id"]):
        L.append(f"| {p['question_id']} | {p['key_papers']} | {p['mentori_papers']} | {p['package_papers']} | "
                 f"{p['package_papers_deep']} | {p['mentori_pass']} | {p['package_pass']} | {p['d_papers']:+.2f} | "
                 f"{p['d_papers_deep']:+.2f} | {p['d_pass_pct']:+.1f} |")
    L += ["", "## Concordant questions for a follow-up ablation (all listed, none selected)", "",
          "3 of 3 draws pass at 4 for one strategy and 0 of 3 for the other (a failed answer counts as a fail). Per "
          "draw: score, all successful sub-calls, sub-calls with paper text, papers read, every key paper read, and "
          "for Mentori the gate's rejections with their kinds (u = under 3 counted, s = 3 or more counted, ? = cannot "
          "tell).", ""]
    short = {GATE_COUNT: "u", GATE_SUBSTANCE: "s", GATE_UNKNOWN: "?"}
    for k, v in R["concordant"].items():
        L.append(f"### {k.replace('_', ' ')}: {len(v)}")
        L.append("")
        for x in v:
            L.append(f"- {x['question_id']} ({GROUP_LABEL[x['group']]}, key papers {', '.join(x['key_papers'])})")
            for lab, ds in x["draws"].items():
                L.append(f"  - {lab}: " + "; ".join(
                    f"d{e['draw']} score {e['score']} sub {e['sub_calls_ok']} with text {e['sub_calls_with_paper_text']}"
                    f" papers {e['papers']} all-key {'yes' if e['every_key_paper'] else 'no'}"
                    + (f" rej {e['gate_rejections']}"
                       + (f" ({''.join(short[z] for z in e['gate_rejection_kinds'])})" if e["gate_rejections"] else "")
                       if "gate_rejections" in e else "")
                    + (f" in-depth {e['papers_deep']}" if "papers_deep" in e else "") for e in ds))
        L.append("")
    m = R["matching"]
    L += ["## What the record does not hold", "",
          "- Mentori: the passage ids each sub-call was handed. The frozen record holds how many chunks each call was "
          "handed (`generation.calls[].n_passages`, used above for sub-calls with paper text) but not their ids, so "
          "its papers are those returned to the code, an upper bound. Passages handed to a sub-call as strings carry "
          "no id and are not counted as paper text.",
          "- Mentori: which kind each gate rejection was is not recorded; the kinds above are inferred from the call "
          "order and are given only where every root placement agrees.",
          "- Package: it has no gate, so no rejection count. A sub-call given only text the model wrote (a summary of "
          "earlier sub-calls) reads no paper by this measure, even when that text came from one. A copy shorter than "
          "127 characters, or text shared with another paper, may be missed (sampled windows).",
          f"- Package in depth: {m['answer_paper_pairs_deep_by_repeats_only']} (answer, paper) pairs would reach "
          f"{DEEP_CHARS:,} characters only by counting text sent to several sub-calls again (the earlier summed rule); "
          f"they are not in depth here.", ""]
    path.write_text("\n".join(L))


README = """# S571_rlm_reading

Written by `uv run --frozen python scripts/S571_rlm_reading.py` (test: `scripts/S571_rlm_reading_test.py`). Code line
numbers are at commit 6318e8e8 (orchestrator.py and exp1_rlm_vs_singlepass.py have uncommitted edits since).

What the code does:

1. Reads Figure 3a's judge cells for Mentori RLM-10 (G1 `rlm_10`) and package RLM-10 (G6 `cap10`) with the functions
   Figure 3 itself uses (`S463.read_answers`, `read_collect`, `judge_rows` through `judge_rows_v25`, `read_extra`), on
   the same frozen inputs `S463 rebuild` reads. Question types from `S511.questions()` (60 one-paper, 26 many-paper,
   10 false premise, 39 not answerable).
2. Reproduces Figure 3a's committed pass rates at score 4 (Source Data Fig. 3, sheet Fig. 3a, rows 'strategy,
   question group') for both strategies on one-paper and many-paper questions, and Mentori RLM-10's every-key-paper
   counts in S511's results.json; refuses on any difference.
3. Per answer: all successful sub-calls, successful sub-calls that carried paper text, root turns, distinct papers
   read, gate rejections and their kinds (Mentori), answer words, pass at 4.
   - Mentori (record line S463 read; `generation.rlm.metadata`, written by exp1_rlm_vs_singlepass.py:627 from
     orchestrator.py:157-189; `generation.calls`, one summary per call, n_passages from pipeline.py:42):
     all sub-calls = `sub_calls_ok` (executor.py:268-271), what the gate counts: every successful
     llm_summarize/llm_query/llm_extract call except one handed an empty list, so it includes llm_query(prompt) with
     no passages. With paper text = calls with `n_passages` > 0 not listed in `sub_call_failures` (passages handed
     as strings carry no id, so a lower bound). Papers = distinct `file_name` (paper store, `S511.paper_map`) of
     `passages_seen`, every chunk a search or a navigation read returned to the code: a proxy and an upper bound, because the record
     holds each sub-call's passage count but not its ids.
   - Mentori gate: FINAL is rejected when `sub_calls_ok < 3 or not has_substance` (orchestrator.py:440), at most 3
     times; `rejections` counts both kinds and the record does not say which. S571 places the root calls in the
     call list (first call root; a root call carries no ids; root prompt_tokens rise strictly) and counts the
     successful sub-calls before each rejection: under 3 means the count alone rejected; 3 or more means the answer
     lacked substance; otherwise, or when the possible placements disagree, the kind is "cannot tell".
   - Package (g6_d135 answers.jsonl, adapter.py:1185-1200; frozen g6_calls_after_d135 calls.jsonl, adapter.py:747-776):
     all sub-calls = `calls.sub - calls.sub_failed`, checked against the call records; root turns = `turns_used`;
     papers = papers whose text appears in a successful sub-call's `prompt_sent`: every 64-character run of each
     paper's text in B4_rlm_ref_context.json (whitespace collapsed, runs shared by two papers dropped) is indexed,
     the prompt is sampled at every 32nd position, and a paper with 2 or more sampled windows found counts as read
     (a copy of 127 characters or more of text found in only one paper is always found). With paper text = successful sub-calls with at least one
     paper read. A paper is read in depth when the distinct characters of it covered by the windows found (each
     window counting its first 32), across the answer's successful sub-calls, reach 2,000: text sent to two
     sub-calls counts once.
4. Tables by strategy and type; gate rejections by kind; pass at 4 by whether every key paper was read (S511's
   definition) and by whether the gate rejected; a per-question paired view on many-paper questions with Pearson r
   and a 10,000-resample percentile bootstrap (seed 20261013); all questions where one strategy passes 3 of 3 draws
   and the other 0 of 3. Association only.

Files: results.json (every number and every answer's row, with `_provenance`), results.md (the tables), header.json
(the same provenance: script and code sha256, git HEAD, whether tracked files differ from HEAD, UTC time, input
sha256).
"""


def git(*args) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=True).stdout


def provenance(shas: dict) -> dict:
    """S511's _provenance block, plus whether tracked files differ from HEAD and the sha256 of S571's code
    dependencies (the numbers depend on S463, S511, fig_repro and gemini_client)."""
    changed = [ln[3:] for ln in git("status", "--porcelain", "--untracked-files=no").splitlines() if ln.strip()]
    deps_status = git("status", "--porcelain", "--", *CODE_DEPS).splitlines()
    return {"script": SCRIPT, "script_sha256": sha256_file(Path(__file__)),
            "at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "git_head": git("rev-parse", "HEAD").strip(),
            "worktree_dirty": bool(changed), "tracked_files_changed": len(changed),
            "dependencies_changed_from_head": sorted(ln[3:] for ln in deps_status if ln.strip()),
            "code_sha256": {d: sha256_file(ROOT / d) for d in CODE_DEPS if (ROOT / d).exists()},
            "command": f"uv run --frozen python {SCRIPT}", "inputs_sha256": shas,
            "python": sys.version.split()[0]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--g17", type=Path, default=None,
                    help="D240: a folder holding runs/exp_01__<arm>__exp_v4_s20_n0/answers.jsonl for G17's three arms; "
                         "writes <out>/g17/ beside the outputs above, which do not change")
    ap.add_argument("--g17-judge", type=Path, default=None, help="with --g17: S572's out_s6_w_g17 folder (pass at 4, 3)")
    ap.add_argument("--g17-concept-recall", type=Path, default=None,
                    help="with --g17: S573's concept_recall.jsonl")
    ap.add_argument("--g17-d23", type=Path, default=None,
                    help="D249 O1, with --g17: a folder holding runs/exp_01__<arm>__exp_v4_s20_n0/answers.jsonl of G17's "
                         "draws 2 and 3; adds <out>/g17_d123/ (draws 1 to 3); <out>/g17/ is written as without it")
    ap.add_argument("--g17-d23-judge", type=Path, default=None, help="with --g17-d23: S572's out_s6_w_g17_d23 folder")
    ap.add_argument("--g17-d23-concept-recall", type=Path, default=None,
                    help="with --g17-d23: S573 --draws 2 3's concept_recall.jsonl")
    a = ap.parse_args(argv)
    if (a.g17_judge or a.g17_concept_recall or a.g17_d23) and a.g17 is None:
        ap.error("--g17-judge, --g17-concept-recall and --g17-d23 go with --g17")
    if (a.g17_d23_judge or a.g17_d23_concept_recall) and a.g17_d23 is None:
        ap.error("--g17-d23-judge and --g17-d23-concept-recall go with --g17-d23")
    try:
        inp = read_inputs()
        R = build(inp)
    except Refused as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    pv = provenance(inp["shas"])
    R = {"_provenance": pv, **R}
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps(R, indent=1, default=list) + "\n")
    write_md(R, out / "results.md")
    (out / "README.md").write_text(README)
    (out / "header.json").write_text(json.dumps(pv, indent=1) + "\n")
    for x in R["reproduce"]:
        print("reproduced:", x)
    print(f"wrote {rel(out)}")
    if a.g17 is not None:
        try:
            G = g17_reading(R, inp, a.g17.expanduser(), a.g17_judge, a.g17_concept_recall)
        except Refused as e:
            print(f"REFUSED (--g17; the outputs above are written): {e}", file=sys.stderr)
            return 2
        gdir = out / "g17"
        gdir.mkdir(parents=True, exist_ok=True)
        gp = provenance({**inp["shas"], **G["inputs_sha256"]})
        gp["command"] = " ".join([f"uv run --frozen python {SCRIPT}"] + list(argv if argv is not None else sys.argv[1:]))
        (gdir / "g17_reading.json").write_text(json.dumps({"_provenance": gp, **G}, indent=1, default=list) + "\n")
        write_g17_md(G, gdir / "g17_reading.md")
        print(f"wrote {rel(gdir)} (G17: {len(G['answers'])} answers, judged {G['judged']})")
    if a.g17_d23 is not None:
        try:
            G = g17_reading(R, inp, a.g17.expanduser(), a.g17_judge, a.g17_concept_recall,
                            extra=[((2, 3), a.g17_d23.expanduser(), a.g17_d23_judge, a.g17_d23_concept_recall)])
        except Refused as e:
            print(f"REFUSED (--g17-d23; the outputs above are written): {e}", file=sys.stderr)
            return 2
        gdir = out / "g17_d123"
        gdir.mkdir(parents=True, exist_ok=True)
        gp = provenance({**inp["shas"], **G["inputs_sha256"]})
        gp["command"] = " ".join([f"uv run --frozen python {SCRIPT}"] + list(argv if argv is not None else sys.argv[1:]))
        (gdir / "g17_reading.json").write_text(json.dumps({"_provenance": gp, **G}, indent=1, default=list) + "\n")
        write_g17_md(G, gdir / "g17_reading.md")
        print(f"wrote {rel(gdir)} (G17 draws 1 to 3: {len(G['answers'])} answers, judged {G['judged']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
