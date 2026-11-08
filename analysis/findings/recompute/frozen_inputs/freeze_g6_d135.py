#!/usr/bin/env python3
"""freeze_g6_d135 - D160 (7) Q23: freeze G6's records after the D135 reruns, the reading Figure 3a and Supplementary
Figures 11, 12 and 20 draw.

WHY. The authors' RLM package (G6) at ten turn caps on the depth sweep's 86 questions, three draws, had 117 failed
answers among its 2,580 when its records were frozen for D155 (findings/recompute/L2_inputs/g6/, the bytes of 23
October, before the reruns). D89, D90 and D92 listed 131 of G6's answers (findings/recompute/B4_runs/rerun_d89.sh):
44 run again, 72 rebuilt from their stored closing call, 15 left failed. They ran on the laptop on 24 and 25 October
(D135; check PASS, findings/recompute/B4_runs/rerun_d89_check.log) and rewrote the ten run sinks in the gitignored
findings/runs/. Valerio, 27 October (D160 (7), Q23 "Yes, as D156"): the four plates draw the records after the reruns,
and their gates keep checking the reading before them (the frozen L2_inputs/g6/), so every anchor keeps its meaning.

WHAT IT DOES (run on the laptop, which holds findings/runs; refuses, exit 2, nothing written, on any failed check):
  1. reads the ten findings/runs/b4_rlm_ref__cap<c>__{all135,depthsweep86}/answers.jsonl and, for caps 5, 10 and 20
     (Supplementary Figure 11), calls.jsonl; and the rerun's archive record (B4_runs/d89_before_rerun_*/rerun.json,
     ran_on.json);
  2. reproduces rerun_d89.sh check against the frozen reading before the reruns (L2_inputs/g6/<run>/answers.jsonl,
     each against SHA256SUMS): per run the same number of answers, each key once, the same keys; an answer D92 does
     not list, and each of the 15 left failed, equal to its line before; each of the 72 rebuilt equal to its line
     before but for REBUILT_FIELDS (of the adapter at rerun.json's fix_commit) and its "rebuilt" record (decision D92 Q187, status ok); each of the
     44 rerun made by the adapter and under the lock rerun.json names; the 131 keys and their actions those of
     rerun_d89.sh, the action counts those of rerun.json; the calls of caps 5, 10 and 20 before the reruns
     (g6_calls_before_d89.tar) unchanged at the head of the new calls.jsonl (the reruns only append);
  3. counts, on the 86 questions, the answers failed before and after (printed and recorded; the questions page of
     27 October reads 117 and 18), and records whether caps 5, 10 and 20 are the bytes S3 judged for G6 (the snap
     ~/s3_inputs/g6_20261026T170821Z, its MANIFEST.sha256), when that folder is on this machine;
  4. writes the committed set findings/recompute/g6_d135_inputs/ (fig_repro.frozen("g6_d135")): <run>/answers.jsonl
     (ten files, byte for byte), d89_archive/rerun.json and ran_on.json, and SOURCE_MTIMES.json (each source file's
     sha256 and modification time, the plates' "records of" stamps); builds g6_calls_after_d135.tar in the tar folder
     (env FROZEN_TARS, default ~/Mentori_scratch_keep/frozen_2026-10-26; make_frozen_supp.py's deterministic format,
     built twice, the same sha256) with members/g6_calls_after_d135.sha256;
  5. adds the set's files and the tar to SHA256SUMS (committed lines sorted, tar lines sorted after them) and the set
     to MANIFEST.json; reads every written file back.

    uv run --frozen python findings/recompute/frozen_inputs/freeze_g6_d135.py            freeze (once)
    uv run --frozen python findings/recompute/frozen_inputs/freeze_g6_d135.py --dry      steps 1 to 3 only, writes nothing
    uv run --frozen python findings/recompute/frozen_inputs/freeze_g6_d135.py --check    the frozen set and tar against
                                                                                        SHA256SUMS, and steps 2 and 3 on them

After it, S476 rebuild, S485, S459 and S457 rebuild find the set and draw it (each records which reading was gated
and which drawn); without it they draw the reading before the reruns, as before D160, and record that.
"""
from __future__ import annotations

import argparse
import ast
import collections
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
REC = REPO / "findings" / "recompute"
RUNS = REPO / "findings" / "runs"
PRE = REC / "L2_inputs" / "g6"
SET = REC / "g6_d135_inputs"
RERUN_SH = REC / "B4_runs" / "rerun_d89.sh"
ARCHIVES = sorted(REC.glob("B4_runs/d89_before_rerun_*"))
ADAPTER = REPO / "experiments" / "rlm_ref" / "adapter.py"
S3_SNAP = Path.home() / "s3_inputs" / "g6_20261026T170821Z"
TAR_DIR = Path(os.environ.get("FROZEN_TARS", str(Path.home() / "Mentori_scratch_keep" / "frozen_2026-10-26")))
TOP = "g6_calls_after_d135"
TAR = f"{TOP}.tar"
ALL135 = [f"b4_rlm_ref__cap{c}__all135" for c in (5, 10, 20)]
RUN_NAMES = ALL135 + [f"b4_rlm_ref__cap{c}__depthsweep86" for c in (1, 2, 3, 7, 15, 30, 50)]
ACTIONS = {"rerun": 44, "rebuild": 72, "stays_failed": 15}


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


RF = _load("refreeze_fig3", HERE / "refreeze_fig3.py")              # sha, rel, files_under, read_sums, write_sums
MFS = _load("make_frozen_supp", HERE / "make_frozen_supp.py")        # build_tar, HashSink (TOP set below)
Refused = RF.Refused


def rebuilt_fields(rer: dict) -> tuple:
    """REBUILT_FIELDS of the adapter the reruns ran: experiments/rlm_ref/adapter.py at rerun.json's fix_commit, held to
    rerun.json's adapter_sha256 (so a later edit of the working-tree adapter cannot change this check), read with ast
    (the adapter is never imported here)."""
    rel_a = RF.rel(ADAPTER)
    r = subprocess.run(["git", "-C", str(REPO), "show", f"{rer.get('fix_commit')}:{rel_a}"], capture_output=True)
    if r.returncode:
        raise Refused(f"git show {rer.get('fix_commit')}:{rel_a} failed")
    if hashlib.sha256(r.stdout).hexdigest() != rer.get("adapter_sha256"):
        raise Refused(f"{rel_a} at {rer.get('fix_commit')} is not the adapter rerun.json names")
    for node in ast.parse(r.stdout.decode("utf-8")).body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "REBUILT_FIELDS" for t in node.targets):
            return tuple(ast.literal_eval(node.value))
    raise Refused(f"{rel_a} at {rer.get('fix_commit')} holds no REBUILT_FIELDS")


def keys_listed() -> dict:
    """{(run, answer_key): action} from rerun_d89.sh's KEYS block (run|answer_key|stored stop|action)."""
    out = {}
    for line in RERUN_SH.read_text().splitlines():
        m = re.fullmatch(r"(b4_rlm_ref__cap\d+__\w+)\|(cap\d+\|[^|]+\|d\d)\|(\w+)\|(rerun|rebuild|stays_failed)",
                         line.strip())
        if m:
            out[(m.group(1), m.group(2))] = m.group(4)
    got = collections.Counter(out.values())
    if dict(got) != ACTIONS:
        raise Refused(f"{RF.rel(RERUN_SH)} lists {dict(got)}, not {ACTIONS}")
    return out


def archive() -> Path:
    if len(ARCHIVES) != 1:
        raise Refused(f"want one B4_runs/d89_before_rerun_* archive, found {len(ARCHIVES)}")
    return ARCHIVES[0]


def depth_ids() -> list:
    """The 86 questions: run_rlm_ref.py's DEPTH_SWEEP86, as S459.design_constants reads it (ast, never imported)."""
    sys.path.insert(0, str(REPO / "scripts"))
    s459 = _load("S459", REPO / "scripts" / "S459_fig3_rlm_ref_caps.py")
    return list(s459.design_constants()[0])


def lines_of(p: Path) -> list:
    return [x for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def compare(post_dir: Path, calls_dir: Path | None) -> dict:
    """Step 2 and 3 on a folder <run>/answers.jsonl (and calls_dir/<run>/calls.jsonl for caps 5, 10, 20)."""
    listed = keys_listed()
    rer = json.loads((archive() / "rerun.json").read_text())
    got = {"rerun": rer.get("rerun"), "rebuild": rer.get("rebuilt"), "stays_failed": rer.get("stays_failed")}
    if got != ACTIONS or rer.get("answers") != sum(ACTIONS.values()):
        raise Refused(f"rerun.json counts {got}, not {ACTIONS}")
    sums = RF.read_sums()[0]
    fields = rebuilt_fields(rer)
    ids = set(depth_ids())
    if len(ids) != 86:
        raise Refused(f"DEPTH_SWEEP86 holds {len(ids)} questions")
    probs, per_run = [], {}
    failed_before, failed_after = [], []
    seen_listed = set()
    for run in RUN_NAMES:
        pre_f = PRE / run / "answers.jsonl"
        if sums.get(RF.rel(pre_f)) != RF.sha(pre_f):
            raise Refused(f"{RF.rel(pre_f)} is not its SHA256SUMS line")
        pre_l, post_l = lines_of(pre_f), lines_of(post_dir / run / "answers.jsonl")
        pre = {json.loads(x)["answer_key"]: x for x in pre_l}
        post = {}
        for x in post_l:
            k = json.loads(x)["answer_key"]
            if k in post:
                probs.append(f"{run}: {k} twice")
            post[k] = x
        if len(pre_l) != len(post_l) or set(pre) != set(post):
            probs.append(f"{run}: {len(post_l)} answers ({len(set(post))} keys), {len(pre_l)} before")
            continue
        act = {k: a for (r, k), a in listed.items() if r == run}
        seen_listed |= {(run, k) for k in act}
        if set(act) - set(pre):
            probs.append(f"{run}: listed keys not in its records: {sorted(set(act) - set(pre))[:2]}")
        n = collections.Counter()
        for k in pre:
            a, b = json.loads(pre[k]), json.loads(post[k])
            how = act.get(k)
            if how is None or how == "stays_failed":
                if pre[k] != post[k]:
                    probs.append(f"{run} {k}: {how or 'not listed'}, changed")
            elif how == "rebuild":
                if (b.get("rebuilt") or {}).get("decision") != "D92 Q187" or b.get("status") != "ok" or \
                        {f: v for f, v in b.items() if f not in fields + ("rebuilt",)} != \
                        {f: v for f, v in a.items() if f not in fields}:
                    probs.append(f"{run} {k}: rebuild is not its stored line but for the rebuilt fields")
            elif how == "rerun":
                if b.get("adapter_sha256") != rer["adapter_sha256"] or b.get("lock_sha256") != rer["lock_sha256"]:
                    probs.append(f"{run} {k}: rerun not under rerun.json's adapter and lock")
            n[how or "unchanged"] += 1
            if a.get("question_id") in ids:
                if a.get("status") != "ok":
                    failed_before.append(f"{run}|{k}")
                if b.get("status") != "ok":
                    failed_after.append(f"{run}|{k}")
        per_run[run] = {"answers": len(post_l), **dict(sorted(n.items())),
                        "sha256_before": RF.sha(pre_f), "sha256_after": RF.sha(post_dir / run / "answers.jsonl")}
        if calls_dir is not None and run in ALL135:
            old = MFS_frozen_calls(run)
            new = calls_dir / run / "calls.jsonl"
            k_ = old.stat().st_size
            with open(old, "rb") as f1, open(new, "rb") as f2:
                if f1.read() != f2.read(k_):
                    probs.append(f"{run}: calls.jsonl before the reruns is not the head of the new one")
            per_run[run]["calls_sha256_after"] = RF.sha(new)
    if seen_listed != set(listed):
        probs.append(f"{len(set(listed) - seen_listed)} listed keys in no run read")
    if probs:
        raise Refused(f"G6 after D135 against the reading before ({len(probs)}): " + "; ".join(probs[:4]))
    snap = None
    if (S3_SNAP / "MANIFEST.sha256").is_file():
        man = {n_: h for h, n_ in (ln.split("  ", 1) for ln in (S3_SNAP / "MANIFEST.sha256").read_text().splitlines()
                                   if ln.strip())}
        snap = {run: man.get(f"runs/{run}/answers.jsonl") == per_run[run]["sha256_after"] for run in ALL135}
    return {"runs": per_run, "failed_on_86_before": len(failed_before), "failed_on_86_after": len(failed_after),
            "failed_on_86_after_keys": sorted(failed_after),
            "caps_5_10_20_equal_to_s3_g6_snap": snap, "listed": dict(collections.Counter(listed.values())),
            "rebuilt_fields": list(fields), "rerun_adapter_sha256": rer["adapter_sha256"],
            "rerun_lock_sha256": rer["lock_sha256"]}


def MFS_frozen_calls(run: str) -> Path:
    """The calls.jsonl of caps 5, 10, 20 before the reruns, from g6_calls_before_d89.tar (fig_repro.frozen)."""
    sys.path.insert(0, str(REPO / "scripts"))
    import fig_repro
    try:
        return fig_repro.frozen("g6_calls_before_d89", f"g6_calls_before_d89/{run}/calls.jsonl")
    except fig_repro.FrozenInputError as e:
        raise Refused(str(e)) from e


def mtimes_body(post_dir: Path, calls_dir: Path) -> dict:
    rec = {}
    for run in RUN_NAMES:
        for p in [post_dir / run / "answers.jsonl"] + ([calls_dir / run / "calls.jsonl"] if run in ALL135 else []):
            rec[f"findings/runs/{run}/{p.name}"] = {"sha256": RF.sha(p), "mtime": int(p.stat().st_mtime),
                                                    "source": RF.rel(p)}
    return {"what": "the modification time (seconds since 1970, UTC) of each G6 record after the D135 reruns, when "
                    "freeze_g6_d135.py froze it; the plates' stamps print the newest. Keyed by the path the plates' "
                    "provenance names.",
            "frozen_at": {"answers": "findings/recompute/g6_d135_inputs/<run>/answers.jsonl",
                          "calls": f"{TAR}: {TOP}/<run>/calls.jsonl"},
            "files": rec}


def build_tar(calls_dir: Path, fobj) -> dict:
    MFS.TOP = TOP
    return MFS.build_tar([(f"{run}/calls.jsonl", calls_dir / run / "calls.jsonl") for run in ALL135], fobj)


def freeze(dry: bool) -> int:
    if SET.exists():
        raise Refused(f"{RF.rel(SET)} exists: the freeze was made (use --check)")
    info = compare(RUNS, RUNS)
    print(json.dumps({k: v for k, v in info.items() if k != "failed_on_86_after_keys"}, indent=1))
    print(f"failed on the 86 questions: {info['failed_on_86_before']} before the reruns, "
          f"{info['failed_on_86_after']} after: {info['failed_on_86_after_keys']}")
    if dry:
        print("dry: nothing written")
        return 0
    tar = TAR_DIR / TAR
    if tar.exists():
        raise Refused(f"{tar} exists")
    arch = archive()
    for run in RUN_NAMES:
        (SET / run).mkdir(parents=True, exist_ok=True)
        shutil.copyfile(RUNS / run / "answers.jsonl", SET / run / "answers.jsonl")
    (SET / "d89_archive").mkdir(parents=True, exist_ok=True)
    for n in ("rerun.json", "ran_on.json"):
        shutil.copyfile(arch / n, SET / "d89_archive" / n)
    (SET / "SOURCE_MTIMES.json").write_text(json.dumps(mtimes_body(RUNS, RUNS), indent=1, sort_keys=True) + "\n")
    with open(tar, "xb") as f:
        sink = MFS.HashSink(f)
        written = build_tar(RUNS, sink)
    again = MFS.HashSink()
    build_tar(RUNS, again)
    if again.h.hexdigest() != sink.h.hexdigest():
        raise Refused(f"{TAR}: a second build gives another sha256")
    want = {f"{run}/calls.jsonl": RF.sha(RUNS / run / "calls.jsonl") for run in ALL135}
    if written != want:
        raise Refused(f"{TAR}: member bytes differ from their sources")
    (HERE / "members" / f"{TOP}.sha256").write_text("".join(f"{want[m]}  {TOP}/{m}\n" for m in sorted(want)))
    committed, tars = RF.read_sums()
    for p in RF.files_under(SET):
        committed[RF.rel(p)] = RF.sha(p)
    tars = sorted([t for t in tars if t[0] != TAR] + [(TAR, RF.sha(tar))])
    RF.write_sums(committed, tars)
    m = json.loads(RF.MANIFEST.read_text())
    files = RF.files_under(SET)
    m["sets"]["g6_d135_inputs"] = {
        "location": RF.rel(SET), "inventory": "D160 (7) Q23: G6 after the D135 reruns, the reading Figure 3a and "
                                              "Supplementary Figures 11, 12 and 20 draw",
        "source": "findings/runs/<run>/answers.jsonl (laptop), the rerun archive's rerun.json and ran_on.json",
        "files": len(files), "files_copied": len(files), "bytes": sum(p.stat().st_size for p in files),
        "check": {k: v for k, v in info.items()},
        "read_by": "S476 rebuild (L2_d135), S485, S459, S457 rebuild",
        "copy_equals_source": f"{len(files)} of {len(files)}"}
    m.setdefault("tars", {})
    if isinstance(m["tars"], dict):
        # kind, location and top_folder as make_frozen.py's tar entries: fig_repro.py reads top_folder of every tar
        m["tars"][TAR] = {"kind": "tar", "source": "findings/runs/b4_rlm_ref__cap{5,10,20}__all135/calls.jsonl after "
                                    "the D135 reruns", "top_folder": TOP, "location": str(tar), "files": len(want),
                          "bytes": tar.stat().st_size, "sha256": RF.sha(tar)}
    tot = m["sha256sums"]
    tot["committed_files"] = len(committed)
    tot["committed_bytes"] = sum((REPO / k).stat().st_size for k in committed)
    tot["tars"] = len(tars)
    m.setdefault("refrozen_by", []).append({"script": RF.rel(Path(__file__)), "script_sha256": RF.sha(Path(__file__)),
                                            "python": sys.version.split()[0], "sets": ["g6_d135_inputs", TAR]})
    RF.MANIFEST.write_text(json.dumps(m, indent=1) + "\n")
    check()
    print(f"froze {RF.rel(SET)} ({len(files)} files) and {tar} (sha256 {RF.sha(tar)})")
    return 0


def check() -> int:
    if not SET.exists():
        raise Refused(f"{RF.rel(SET)} does not exist: nothing frozen yet")
    committed, tars = RF.read_sums()
    for p in RF.files_under(SET):
        if committed.get(RF.rel(p)) != RF.sha(p):
            raise Refused(f"{RF.rel(p)} is not its SHA256SUMS line")
    if {k for k in committed if k.startswith(RF.rel(SET) + "/")} != {RF.rel(p) for p in RF.files_under(SET)}:
        raise Refused(f"{RF.rel(SET)}: SHA256SUMS lists other files than the folder holds")
    sys.path.insert(0, str(REPO / "scripts"))
    import fig_repro
    try:
        calls = fig_repro.frozen(TOP, TOP)
    except fig_repro.FrozenInputError as e:
        raise Refused(str(e)) from e
    info = compare(SET, calls)
    mt = json.loads((SET / "SOURCE_MTIMES.json").read_text())["files"]
    for run in RUN_NAMES:
        if mt[f"findings/runs/{run}/answers.jsonl"]["sha256"] != RF.sha(SET / run / "answers.jsonl"):
            raise Refused(f"SOURCE_MTIMES.json: {run} answers sha256 differs from the frozen file")
    print(f"PASS: {RF.rel(SET)} and {TAR} equal to SHA256SUMS; against the reading before the reruns: listed "
          f"{info['listed']}; failed on the 86 questions {info['failed_on_86_before']} before, "
          f"{info['failed_on_86_after']} after")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dry", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    try:
        return check() if a.check else freeze(a.dry)
    except Refused as e:
        print(e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
