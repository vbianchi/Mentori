#!/usr/bin/env python3
"""S525 - the known number S4's rerun copy must reproduce before Figure 6 moves onto it (D201 Q2; fig6 spec section 5, A8).

One command, from the repository root, once S4's copy is frozen and named in S447.FROZEN_S2:
    uv run --frozen python scripts/S525_fig6_s4_check.py            compare, then write
    uv run --frozen python scripts/S525_fig6_s4_check.py selftest   the gates and their mutants on built rows, then the
                                                                    old copy against itself; nothing written

WHY. S481 stops on any copy that does not give S478.WANT, 2,420 attempts and 1,660 passes. S4 reruns 165 attempts
(findings/recompute/S502_fig6_s4_reruns/S502_rerun_list.json), so its copy will move the 1,660 and WANT and the anchors
have to follow it (fig6 spec Q1). Valerio ruled yes on 2 November 2026 (D201 Q2). Moving WANT alone would leave S481
with no known number on the new copy; this script supplies one: the 2,255 attempts S4 did not rerun must come out equal.

D201 Q2, what is built and what waits (2 November 2026). This script is built. WANT is not moved: it stays (2420, 1660)
in S478 until S4's copy exists, and S4's last variant had not ended when this was written (plan.csv row S4). The order
when it ends is the spec's A4 to A9: S447 mirror --from-copy --complete-only, the tar, FROZEN_S2; S477 again (S447 stops
on another manifest); this script, which must pass; then WANT, S447 draw, S478, S479, inputs/prep.py and the _X anchors,
draw_B.py, draw_G4.py, draw_C.py and _C_DRAFT_SHA256, and the literal 1,660 in S481; stamp_of and the caption; S491, S488.

WHAT IT READS, through S447's own loader (load_mirror, keep_design, fail_kind), so every file is checked against its
manifest, the length rule and S477's flips apply, and nothing is re-implemented here:
    old  frozen copy OLD_SET, with records_manifest.json and S477_lung9_rescore.json as they stood at commit OLD_AT
         (pinned in the tree, O3: findings/recompute/pinned_history/, each copy held to its git blob id; the working
         copies will have moved by then)
    new  S447.FROZEN_S2 with the working records_manifest.json and S477_lung9_rescore.json
    findings/recompute/S502_fig6_s4_reruns/S502_rerun_list.json   the 165 keys, held to its keys_sha256 and n_keys

GATES. Any failure exits 2 and writes nothing:
  (0) the known number: the old copy gives OLD_WANT, 2,420 attempts and 1,660 passes;
  (1) the list holds OLD_LISTED keys (165), all of them among the old copy's;
  (2) the old and the new copy hold the same keys;
  (3) every key outside the list is equal in FIELDS (passed, fail_kind, exec_outcome, actual_results), read after S447's
      length rule and S477's flips, and keeps its ctx_uid, so it did not run again: the 2,255;
  (4) every listed key has a ctx_uid in the new copy, and another one than in the old: it ran again and was not carried
      over.
A failed comparison of (3) is a finding about the copy, never a reason to edit this list.

OUTPUT. findings/recompute/S525_fig6_s4_check.json: provenance, the counts, and passes per variant old and new.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import pinned_history as PH  # noqa: E402
SCRIPT = "scripts/S525_fig6_s4_check.py"
OUT = ROOT / "findings/recompute/S525_fig6_s4_check.json"
LIST = ROOT / "findings/recompute/S502_fig6_s4_reruns/S502_rerun_list.json"
MANIFEST_REL = "findings/figures_provisional/fig6/records_manifest.json"
Q4_REL = "findings/recompute/S477_lung9_rescore.json"
OLD_SET = "s2_length_retries_20261021"         # the copy Figure 6 stands on before S4 (S447.FROZEN_S2 on 2 November)
OLD_AT = "94262a0e"                            # a commit holding that copy's manifest and S477's file
OLD_WANT = (2420, 1660)                        # S478.WANT before S4; kept here so it survives WANT's move
OLD_LISTED = 165                               # S502: 162 structured and 3 Q60
FIELDS = ("passed", "fail_kind", "exec_outcome", "actual_results")


class Refused(Exception):
    pass


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load_S447():
    spec = importlib.util.spec_from_file_location("S447", ROOT / "scripts" / "S447_fig6_panels.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["S447"] = m
    spec.loader.exec_module(m)
    return m


def listed_keys() -> set:
    """{(run id, answer key)} of S502's list, held to its own keys_sha256 and n_keys (as S502.load_list holds them)."""
    lst = json.loads(LIST.read_text())
    flat = sorted(f"{rid}\t{k}" for vv in lst["variants"].values() for rid, r in vv["runs"].items() for k in r["keys"])
    if sha256_bytes(json.dumps(flat).encode()) != lst["keys_sha256"] or len(flat) != lst["n_keys"]:
        raise Refused(f"{LIST.relative_to(ROOT)}: its keys do not give its keys_sha256 or n_keys")
    return {tuple(x.split("\t", 1)) for x in flat}


def rows_of(S447, attempts, flags) -> dict:
    """{(run id, answer key): {FIELDS, ctx_uid}} of the design's attempts, as S447 gives them."""
    out = {}
    for a in attempts:
        k = (a["run_id"], a["answer_key"])
        if k in out:
            raise Refused(f"{k}: two attempts with one key")
        fl = flags.get(a.get("ctx_uid"), set())
        out[k] = {"passed": bool(a["passed"]), "fail_kind": None if a["passed"] else S447.fail_kind(a, fl),
                  "exec_outcome": a.get("exec_outcome"), "actual_results": a.get("actual_results"),
                  "ctx_uid": a.get("ctx_uid")}
    return out


def load_copy(S447, set_name: str, manifest: bytes | None = None, q4: bytes | None = None) -> tuple[dict, dict]:
    """The rows of one frozen copy through S447's loader. manifest and q4 are the bytes to read in place of the working
    records_manifest.json and S477 file (the old copy's); None reads the working files."""
    saved = {k: getattr(S447, k) for k in ("ROOT", "RUNS", "MANIFEST", "Q4_RESCORE", "FROZEN_S2")}
    with tempfile.TemporaryDirectory(prefix="S525_") as td:
        try:
            S447.FROZEN_S2 = set_name
            if manifest is not None:
                tmp = Path(td)
                S447.ROOT, S447.RUNS = tmp, tmp / "findings" / "runs"
                S447.MANIFEST, S447.Q4_RESCORE = tmp / MANIFEST_REL, tmp / Q4_REL
                for p, b in ((S447.MANIFEST, manifest), (S447.Q4_RESCORE, q4)):
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_bytes(b)
            atts, flags, inputs, notes = S447.load_mirror()
            kept = S447.keep_design(atts)[0]
        finally:
            for k, v in saved.items():
                setattr(S447, k, v)
    if notes["duplicates_dropped"]:
        raise Refused(f"{set_name}: duplicates dropped in {sorted(notes['duplicates_dropped'])[:3]}")
    return rows_of(S447, kept, flags), {"frozen_set": set_name, "manifest_sha256": inputs[MANIFEST_REL],
                                        "tar_sha256": inputs[f"frozen {set_name}.tar"]}


def git_show(rev: str, path: str) -> bytes:
    """path as committed at rev (O3, 8 Nov: no git; its copy pinned in the tree, held to the blob id git gave
    <rev>:<path>, scripts/pinned_history.py)."""
    try:
        return PH.show(rev, path)
    except PH.PinError as e:
        raise Refused(f"git show {rev}:{path}: {e}") from None


def compare(old: dict, new: dict, listed: set, want: tuple = OLD_WANT, n_listed: int = OLD_LISTED) -> tuple[list, dict]:
    """The gates (0) to (4) on two row maps. Returns (problems, counts)."""
    bad = []
    got = (len(old), sum(r["passed"] for r in old.values()))
    if got != tuple(want):
        bad.append(f"(0) the old copy gives {got}, not {tuple(want)}")
    if len(listed) != n_listed or listed - set(old):
        bad.append(f"(1) the list holds {len(listed)} keys, {len(listed - set(old))} of them not in the old copy, "
                   f"not {n_listed} old keys")
    if set(old) != set(new):
        bad.append(f"(2) keys: {len(set(old) - set(new))} old keys not in the new copy, {len(set(new) - set(old))} new "
                   f"keys not in the old")
    both = set(old) & set(new)
    outside = both - listed
    moved = Counter()
    for k in sorted(outside):
        for f in FIELDS:
            if old[k][f] != new[k][f]:
                moved[f] += 1
                if moved[f] == 1:
                    bad.append(f"(3) {k}: {f} changed outside the list, the first of the changes counted below")
    if moved:
        bad.append(f"(3) changes outside the list per field: {dict(moved)}")
    off_list = sorted(k for k in outside if old[k]["ctx_uid"] != new[k]["ctx_uid"])
    if off_list:
        bad.append(f"(3) {len(off_list)} keys outside the list changed ctx_uid, first {off_list[0]}: run again off the list")
    no_uid = sorted(k for k in listed & both if not new[k]["ctx_uid"])
    if no_uid:
        bad.append(f"(4) {len(no_uid)} listed keys have no ctx_uid in the new copy, first {no_uid[0]}")
    same_uid = sorted(k for k in listed & both if old[k]["ctx_uid"] == new[k]["ctx_uid"])
    if same_uid:
        bad.append(f"(4) {len(same_uid)} listed keys keep their ctx_uid, first {same_uid[0]}: not run again")
    return bad, {"keys": len(both), "outside_the_list_equal": len(outside) - len(
        {k for k in outside for f in FIELDS if old[k][f] != new[k][f]} | set(off_list)), "listed": len(listed & both),
        "listed_rerun": len(listed & both) - len(same_uid)}


def per_variant(rows: dict) -> dict:
    out = {}
    for (rid, _), r in rows.items():
        v = rid.split("__", 2)[2]
        e = out.setdefault(v, {"attempts": 0, "passed": 0})
        e["attempts"] += 1
        e["passed"] += r["passed"]
    return dict(sorted(out.items()))


def built_rows() -> tuple[dict, dict, set]:
    """Made-up rows for the mutants: 6 attempts, 2 of them on the list, the new copy a correct rerun."""
    old = {("r__c__v", f"k{i}"): {"passed": i % 2 == 0, "fail_kind": None if i % 2 == 0 else "no code",
                                  "exec_outcome": "ok", "actual_results": {"x": i}, "ctx_uid": f"u{i}"}
           for i in range(6)}
    listed = {("r__c__v", "k0"), ("r__c__v", "k1")}
    new = {k: dict(r) for k, r in old.items()}
    for k in listed:
        new[k]["ctx_uid"] += "b"
        new[k]["passed"] = True                # a rerun may change anything
        new[k]["fail_kind"] = None
    return old, new, listed


def mutants() -> list:
    """Each (name, mutate) changes a correct built new copy, or the arguments, so that one gate must fire."""
    def drop(o, n, ls):
        del n[("r__c__v", "k3")]

    def extra(o, n, ls):
        n[("r__c__v", "k9")] = dict(n[("r__c__v", "k3")])

    def field(f, v):
        def m(o, n, ls):
            n[("r__c__v", "k3")][f] = v
        return m

    def carried(o, n, ls):
        n[("r__c__v", "k0")]["ctx_uid"] = o[("r__c__v", "k0")]["ctx_uid"]

    def rerun_off_list(o, n, ls):
        n[("r__c__v", "k3")]["ctx_uid"] = "new"

    def no_uid(o, n, ls):
        n[("r__c__v", "k0")]["ctx_uid"] = None

    def short_list(o, n, ls):
        ls.discard(("r__c__v", "k1"))

    def stranger(o, n, ls):
        ls.discard(("r__c__v", "k1"))
        ls.add(("r__c__v", "zz"))

    def old_pass(o, n, ls):
        o[("r__c__v", "k5")]["passed"] = True
    return [("a key missing from the new copy", drop), ("a key added to the new copy", extra),
            ("passed changed outside the list", field("passed", True)),
            ("fail_kind changed outside the list", field("fail_kind", "other")),
            ("exec_outcome changed outside the list", field("exec_outcome", "length")),
            ("actual_results changed outside the list", field("actual_results", {"x": 0})),
            ("an attempt off the list ran again with equal fields", rerun_off_list),
            ("a listed attempt carried over, not rerun", carried), ("a listed attempt with no ctx_uid", no_uid),
            ("a key off the list", short_list),
            ("a listed key the old copy lacks", stranger), ("the old copy one pass off the known number", old_pass)]


def selftest() -> bool:
    res = []

    def check(name, ok, detail=""):
        res.append(bool(ok))
        print(f"  {'PASS' if ok else 'FAIL'}  {name}{'' if ok else ': ' + str(detail)}")

    old, new, listed = built_rows()
    want = (6, 3)
    bad, n = compare(old, new, listed, want, 2)
    check("a correct rerun passes, 4 outside the list equal, 2 listed rerun",
          not bad and (n["outside_the_list_equal"], n["listed_rerun"]) == (4, 2), bad)
    for name, m in mutants():
        o, nw, ls = built_rows()
        m(o, nw, ls)
        bad, _ = compare(o, nw, ls, want, 2)
        check(f"mutant refused: {name}", bool(bad), "survived")
    S447 = load_S447()
    if S447.FROZEN_S2 != OLD_SET:
        print(f"  note: S447.FROZEN_S2 is {S447.FROZEN_S2}; the old copy {OLD_SET} is still read below")
    man, q4 = git_show(OLD_AT, MANIFEST_REL), git_show(OLD_AT, Q4_REL)
    rows, prov = load_copy(S447, OLD_SET, man, q4)
    ls = listed_keys()
    bad, n = compare(rows, rows, ls)
    only4 = [b for b in bad if not b.startswith("(4)")]
    check(f"the old copy gives the known number {OLD_WANT}, holds the {OLD_LISTED} listed keys and equals itself outside "
          f"the list", not only4 and n["outside_the_list_equal"] == OLD_WANT[0] - OLD_LISTED, only4)
    check(f"the old copy against itself is refused by (4): {n['listed'] - n['listed_rerun']} listed keys not rerun",
          any(b.startswith(f"(4) {OLD_LISTED} ") for b in bad), bad)
    check("the old manifest at OLD_AT is the one S502 listed from",
          prov["manifest_sha256"] == json.loads(LIST.read_text())["provenance"]["inputs"][MANIFEST_REL], prov)
    print(f"selftest: {sum(res)} of {len(res)} checks pass")
    return all(res)


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["selftest"]:
        return 0 if selftest() else 1
    if argv:
        print(f"usage: {SCRIPT} [selftest]", file=sys.stderr)
        return 2
    try:
        if not selftest():
            raise Refused("the selftest fails")
        S447 = load_S447()
        if S447.FROZEN_S2 == OLD_SET:
            raise Refused(f"S4's copy is not frozen: S447.FROZEN_S2 is still {OLD_SET}. Nothing to compare yet")
        old, oprov = load_copy(S447, OLD_SET, git_show(OLD_AT, MANIFEST_REL), git_show(OLD_AT, Q4_REL))
        new, nprov = load_copy(S447, S447.FROZEN_S2)
        bad, counts = compare(old, new, listed_keys())
    except Refused as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    if bad:
        print(f"REFUSED: {len(bad)} gates failed, nothing written:", file=sys.stderr)
        for b in bad:
            print("  " + b, file=sys.stderr)
        return 2
    pv = {"old": per_variant(old), "new": per_variant(new)}
    doc = {"provenance": {"script": SCRIPT, "script_sha256": sha256_bytes(Path(__file__).read_bytes()),
                          "command": f"uv run --frozen python {SCRIPT}", "decision": "D201 Q2", "old": oprov, "new": nprov,
                          "list": {"path": str(LIST.relative_to(ROOT)), "sha256": sha256_bytes(LIST.read_bytes())},
                          "model_calls": 0},
           "fields_compared": list(FIELDS), "counts": counts,
           "totals": {k: {"attempts": sum(x["attempts"] for x in v.values()),
                          "passed": sum(x["passed"] for x in v.values())} for k, v in pv.items()},
           "per_variant": pv}
    OUT.write_text(json.dumps(doc, indent=1) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
