#!/usr/bin/env python3
"""key_scope - Q55: is a question in scope for an index of N core papers, under the D5 key.

WHY. The corpus-scaling driver asks every out-of-domain question at every core size and an
answerable question only where min_core <= core size (recovered_harness/tests/experiments_v4/
exp_v4_4_generation.py:227-233). Under D5 (notes/DECISIONS_2026-10-11.md:54-60) the ten false-premise
questions OOD_041 to OOD_050 are answerable, scored on correctness against the refutation their
source paper holds, and the D5 key gives each that paper's core size as min_core
(notes/DECISIONS_2026-10-12.md:21-30). At a size whose index lacks that paper a row on one of the
ten has no correct answer in the key, so Q55 (notes/DECISIONS_2026-10-12.md:5-12, :32-35) leaves it
out of both groups. The driver's filter cannot be reused for this: it tests category
"out_of_domain" first, and the ten keep that category, so it keeps all ten at every size.

THE RULE, as in_scope applies it. Look the question up in the key (a question the key does not
hold raises KeyError; the six dropped under D7 are named as such in the message). If the key marks
it not answerable, it is in scope at every size (refusal is measured on these 39 at every size).
If it is answerable, it is in scope where its min_core <= N. The ten are answerable in the D5 key,
so min_core decides them. in_scope never reads category (Scope reads it once, to name the ten in
Scope.ten for the self-test and for callers).

CORE SIZE. index_core_size reads N from an index name as the harness does (exp_v4_4_generation.py:
71-75): the digits of the first "_s<digits>_" in the name, and 50 when the name has none. That default
is the harness's, and here it would keep every row of a caller that passes something other than an
index name (a strategy, a file name, a ledger's source), so row_in_scope, partition and count_by_core
read the size with strict=True: a name without "_s<digits>_" raises ValueError. in_scope raises
TypeError on a core size that is not an integer (a tidy table's size column is a string).

    from key_scope import Scope
    sc = Scope()                                  # the D5 key, refused unless its sha256 is KEY_SHA256
    sc.in_scope("OOD_043", 5)                     # False: min_core 10
    sc.row_in_scope("OOD_043", "exp_v4_s10_n3")   # True
    rows = [r for r in rows if r["question_id"] not in sc.dropped_d7]          # D7 is the caller's step
    kept, left_out = sc.partition(rows, lambda r: r["question_id"], lambda r: r["index_name"])

A consumer states how many rows it leaves out (notes/DECISIONS_2026-10-12.md:12): len(left_out),
or sc.count_by_core(left_out, index_of) for the split by core size.

SELF-TEST, which reads the key, the v2.4 key, the v1 key, the harness source, the exp05 deposit
and the S314 rerun and writes nothing. It runs every group and exits 1 if any fails; a key whose
sha256 is not KEY_SHA256, or a harness filter whose text is not HARNESS_FILTER, stops it at once:

    uv run python scripts/key_scope.py

  K1  the D5 key's sha256 is KEY_SHA256; its header's source_v24_sha256 is the sha256 of
      data/ground_truth_v2/all_v2_4.json
  K2  for every record, the key's answerable equals v2.4's question_answerable; the not-answerable
      records are exactly v2.4's answer_type not_answerable (40 less the D7 drop OOD_011 = 39) and
      carry no min_core; every answerable record has an integer min_core; the ten (answerable,
      category out_of_domain) are exactly OOD_041 to OOD_050 and exactly v2.4's answer_type
      refutation
  K3  the ten's min_core and source_files are the D5 record (DECISIONS_2026-10-12.md:26-28)
  K4  index_core_size agrees with the harness's own _index_core_size, compiled from its source,
      on every index name in the exp05 deposit and the S314 rerun and on four edge names
  K5  the harness's own question filter, compiled from its source (whose text is pinned), applied
      to the v1 key, gives the deposit's question set at each core size: 72, 94, 138, 250
  K6  on the D5 key, in_scope differs from that filter on exactly the ten with min_core above the
      size: 5 questions at 5 core papers, 3 at 10, none at 20 or 50
  K7  exp05_scaling_latest.json (sha256 DEPOSIT_SHA256): 9,894 rows; 198 on the six D7 questions,
      set aside; of the rest 144 out of scope, 90 at 5 core papers and 54 at 10, all on the ten
  K8  S314_verified_pass_raw.jsonl: 1,680 rows (header lines skipped); 33 on the six D7 questions,
      set aside; of the rest 24 out of scope, 15 at 5 and 9 at 10, all on the ten
  K9  row_in_scope refuses five names without a core size (among them a strategy and a file name),
      and in_scope refuses four core sizes that are not integers ("5", None, 5.0, True)
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable
from numbers import Integral
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from machine import RECOMPUTE, RESULTS, ROOT  # noqa: E402

KEY = ROOT / "data/ground_truth_v2/ground_truth_v2_4_as_v1.json"      # S381 --key 2.4 (D5, Q56)
KEY_SHA256 = "e971de522df6fab54a070e44736b6cb28a5ebd26bab07ca9e1513230bb86f4ef"
KEY_V24 = ROOT / "data/ground_truth_v2/all_v2_4.json"
KEY_V1 = ROOT / "data/replication_inputs/ground_truth.json"           # the key the driver filtered on
HARNESS = ROOT / "recovered_harness/tests/experiments_v4/exp_v4_4_generation.py"
DEPOSIT = RESULTS / "exp05_scaling_latest.json"
DEPOSIT_SHA256 = "58acf1b4a2bfaa908a6790c343c11a7ce745e66493ea62d9b670308015013a8a"
S314 = RECOMPUTE / "S314_verified_pass_raw.jsonl"

_CORE = re.compile(r"_s(\d+)_")


def index_core_size(index_name: str, strict: bool = False) -> int:
    """Core papers of an index, read from its name as the harness reads it (exp_v4_4_generation.py:71-75):
    the digits of the first "_s<digits>_", and 50 when the name has none. With strict=True a name with no
    "_s<digits>_" raises ValueError instead of reading as 50."""
    m = _CORE.search(index_name)
    if m:
        return int(m.group(1))
    if strict:
        raise ValueError(f"no core size in {index_name!r}: an index name holds '_s<digits>_'")
    return 50


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Scope:
    """The D5 key's records, and the Q55 rule over them (module docstring, THE RULE)."""

    def __init__(self, path: Path = KEY, sha256: str = KEY_SHA256):
        raw = Path(path).read_bytes()
        self.sha256 = hashlib.sha256(raw).hexdigest()
        if self.sha256 != sha256:
            raise SystemExit(f"key_scope REFUSED: {path} has sha256 {self.sha256}, expected {sha256}")
        d = json.loads(raw)
        self.records = {q["id"]: q for q in d["questions"]}
        self.dropped_d7 = frozenset(d.get("dropped_d7") or ())
        bad = [q for q, r in self.records.items()
               if not isinstance(r.get("answerable"), bool)
               or (r["answerable"] and not isinstance(r.get("min_core"), int))]
        if bad:
            raise SystemExit(f"key_scope REFUSED: {len(bad)} records with a non-boolean answerable or an answerable "
                             f"record without an integer min_core, e.g. {bad[:3]}")
        self.ten = frozenset(q for q, r in self.records.items()
                             if r["answerable"] and r.get("category") == "out_of_domain")

    def in_scope(self, question_id: str, core_size: int) -> bool:
        rec = self.records.get(question_id)
        if rec is None:
            why = " (dropped under D7)" if question_id in self.dropped_d7 else ""
            raise KeyError(f"{question_id} is not in the key{why}")
        if isinstance(core_size, bool) or not isinstance(core_size, Integral):
            raise TypeError(f"core_size must be an integer, got {core_size!r}")
        if not rec["answerable"]:
            return True
        return rec["min_core"] <= core_size

    def row_in_scope(self, question_id: str, index_name: str) -> bool:
        return self.in_scope(question_id, index_core_size(index_name, strict=True))

    def partition(self, rows: Iterable, qid: Callable, index: Callable) -> tuple[list, list]:
        """(rows kept, rows left out) by row_in_scope(qid(row), index(row)); a row on a question the key does
        not hold raises KeyError, and a row whose index(row) holds no core size raises ValueError."""
        kept, out = [], []
        for r in rows:
            (kept if self.row_in_scope(qid(r), index(r)) else out).append(r)
        return kept, out

    @staticmethod
    def count_by_core(rows: Iterable, index: Callable) -> dict[int, int]:
        c = Counter(index_core_size(index(r), strict=True) for r in rows)
        return dict(sorted(c.items()))


# ── the harness's own code, compiled from its source for the self-test ────────────────────────────────

HARNESS_FILTER = ("[q for q in questions if q.get('category') == 'out_of_domain' or "
                  "(q.get('min_core') is not None and q['min_core'] <= core_size)]")


def harness_functions() -> tuple[Callable, Callable]:
    """(_index_core_size, filter(q, core_size)) compiled from exp_v4_4_generation.py without importing it
    (it imports the harness backend, exp_v4_4_generation.py:46). The filter is the condition of the list
    comprehension assigned to questions in run_experiment, refused unless that comprehension's source text
    is HARNESS_FILTER."""
    tree = ast.parse(HARNESS.read_text(encoding="utf-8"))
    fn = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_index_core_size"]
    run = [n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "run_experiment"]
    if len(fn) != 1 or len(run) != 1:
        raise SystemExit("key_scope REFUSED: _index_core_size or run_experiment not found once in the harness")
    ns: dict = {}
    exec(compile(ast.Module(body=fn, type_ignores=[]), f"{HARNESS}:_index_core_size", "exec"), ns)
    comps = [n.value for n in ast.walk(run[0]) if isinstance(n, ast.Assign) and isinstance(n.value, ast.ListComp)
             and [ast.unparse(t) for t in n.targets] == ["questions"]]
    if len(comps) != 1 or ast.unparse(comps[0]) != HARNESS_FILTER:
        raise SystemExit("key_scope REFUSED: the harness's question filter is not the pinned text: "
                         + "; ".join(ast.unparse(c) for c in comps))
    cond = comps[0].generators[0].ifs[0]
    lam = ast.Expression(body=ast.Lambda(
        args=ast.arguments(posonlyargs=[], args=[ast.arg("q"), ast.arg("core_size")], kwonlyargs=[],
                           kw_defaults=[], defaults=[]), body=cond))
    ast.fix_missing_locations(lam)
    return ns["_index_core_size"], eval(compile(lam, f"{HARNESS}:filter", "eval"))


# ── self-test ─────────────────────────────────────────────────────────────────────────────────────────

D5_TEN = {"OOD_041": ("01_sarek.pdf", 5), "OOD_042": ("04_fastp.pdf", 5), "OOD_043": ("08_deseq2.pdf", 10),
          "OOD_044": ("02_snakemake.pdf", 5), "OOD_045": ("03_nfcore_framework.pdf", 5),
          "OOD_046": ("07_salmon.pdf", 10), "OOD_047": ("13_lsd_nepal.pdf", 20),
          "OOD_048": ("12_hpai_netherlands.pdf", 20), "OOD_049": ("05_multiqc.pdf", 5),
          "OOD_050": ("15_rabies_tanzania.pdf", 20)}          # notes/DECISIONS_2026-10-12.md:26-28
SIZES = (5, 10, 20, 50)


def _gate(fails: list, name: str, ok: bool, msg: str) -> None:
    print(f"  {'ok  ' if ok else 'FAIL'} {name} {msg}")
    if not ok:
        fails.append(name)


def self_test() -> int:
    fails: list = []
    print(f"key_scope self-test: key {KEY.relative_to(ROOT)}")
    sc = Scope()
    head = json.loads(KEY.read_text(encoding="utf-8"))
    v24 = {r["id"]: r for r in json.loads(KEY_V24.read_text(encoding="utf-8"))["records"]}
    _gate(fails, "K1", head.get("source_v24_sha256") == _sha256(KEY_V24),
          f"key sha256 {sc.sha256[:8]}; header source_v24_sha256 {str(head.get('source_v24_sha256'))[:8]}, "
          f"all_v2_4.json {_sha256(KEY_V24)[:8]}")

    recs = sc.records
    mism = [q for q, r in recs.items() if q not in v24 or r["answerable"] != v24[q]["question_answerable"]]
    na = {q for q, r in recs.items() if not r["answerable"]}
    na24 = {q for q, r in v24.items() if r["answer_type"] == "not_answerable"} - sc.dropped_d7
    na_core = [q for q in na if recs[q].get("min_core") is not None]
    ref24 = {q for q, r in v24.items() if r["answer_type"] == "refutation"}
    _gate(fails, "K2", not mism and na == na24 and len(na) == 39 and not na_core
          and sc.ten == set(D5_TEN) == ref24,
          f"answerable = v2.4 question_answerable on all {len(recs)} records ({len(mism)} differ); "
          f"{len(na)} not answerable = v2.4 not_answerable less D7 ({na == na24}), {len(na_core)} with a min_core; "
          f"the ten = OOD_041..OOD_050 = v2.4 refutation ({sc.ten == set(D5_TEN) == ref24})")

    got = {q: (tuple(recs[q].get("source_files") or ()), recs[q].get("min_core")) for q in sorted(sc.ten)}
    want = {q: ((f,), c) for q, (f, c) in D5_TEN.items()}
    _gate(fails, "K3", got == want,
          "the ten's source_files and min_core: " + ", ".join(f"{q[-3:]} {c}" for q, (_, c) in got.items()))

    h_core, h_filter = harness_functions()
    dep_raw = DEPOSIT.read_bytes()
    dep_sha = hashlib.sha256(dep_raw).hexdigest()
    dep = json.loads(dep_raw)["per_question_results"]
    s314 = [d for d in (json.loads(l) for l in S314.read_text(encoding="utf-8").splitlines() if l.strip())
            if "_header" not in d]
    names = ({r["index_name"] for r in dep} | {d["index"] for d in s314}
             | {"exp_v4_s20_n0", "no_size_here", "exp_v4_s20", "x_s7_y_s9_"})
    bad = sorted(n for n in names if index_core_size(n) != h_core(n))
    _gate(fails, "K4", not bad, f"index_core_size = harness _index_core_size on {len(names)} names; differ: {bad}")

    v1 = json.loads(KEY_V1.read_text(encoding="utf-8"))["questions"]
    asked = defaultdict(set)
    for r in dep:
        asked[index_core_size(r["index_name"])].add(r["question_id"])
    sets = {n: {q["id"] for q in v1 if h_filter(q, n)} for n in SIZES}
    _gate(fails, "K5", all(sets[n] == asked[n] for n in SIZES) and [len(sets[n]) for n in SIZES] == [72, 94, 138, 250],
          "harness filter on the v1 key = deposit question set at 5/10/20/50: "
          + "/".join(f"{len(sets[n])}" + ("" if sets[n] == asked[n] else "(differs)") for n in SIZES))

    diff = {n: sorted(q for q, r in recs.items() if h_filter(r, n) != sc.in_scope(q, n)) for n in SIZES}
    expect = {n: sorted(q for q in sc.ten if recs[q]["min_core"] > n) for n in SIZES}
    _gate(fails, "K6", diff == expect and [len(diff[n]) for n in SIZES] == [5, 3, 0, 0],
          "in_scope differs from the harness filter on the D5 key at 5/10/20/50: "
          + "; ".join(f"{n}: {len(diff[n])} {' '.join(q[-3:] for q in diff[n])}".rstrip() for n in SIZES))

    def check(name, rows, qid, index, n_rows, n_d7, want_out):
        d7 = [r for r in rows if qid(r) in sc.dropped_d7]
        rest = [r for r in rows if qid(r) not in sc.dropped_d7]
        kept, out = sc.partition(rest, qid, index)
        by_core = sc.count_by_core(out, index)
        on_ten = all(qid(r) in sc.ten for r in out)
        ok = len(rows) == n_rows and len(d7) == n_d7 and by_core == want_out and on_ten
        _gate(fails, name, ok, f"{len(rows)} rows, {len(d7)} on D7 questions set aside, {len(kept)} kept, "
                               f"{len(out)} left out {by_core}, all on the ten: {on_ten}")

    if dep_sha != DEPOSIT_SHA256:
        _gate(fails, "K7", False, f"deposit sha256 {dep_sha[:8]}, expected {DEPOSIT_SHA256[:8]}")
    else:
        check("K7", dep, lambda r: r["question_id"], lambda r: r["index_name"], 9894, 198, {5: 90, 10: 54})
    check("K8", s314, lambda d: d["question_id"], lambda d: d["index"], 1680, 33, {5: 15, 10: 9})

    loose = []
    for n in ("no_size_here", "exp_v4_s20", "", "single_pass", "exp05_scaling_latest.json"):
        try:
            sc.row_in_scope("OOD_043", n)
            loose.append(n)
        except ValueError:
            pass
    typed = []
    for n in ("5", None, 5.0, True):
        try:
            sc.in_scope("OOD_001", n)
            typed.append(n)
        except TypeError:
            pass
    _gate(fails, "K9", not loose and not typed,
          f"row_in_scope refuses a name without a core size ({len(loose)} accepted: {loose}); in_scope refuses a core "
          f"size that is not an integer ({len(typed)} accepted: {typed})")

    print(f"\n{'PASSED' if not fails else 'FAILED ' + ' '.join(fails)}; nothing written")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(self_test())
