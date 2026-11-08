#!/usr/bin/env python3
"""refreeze_fig3 - D156: refreeze the S3 part of Figure 3's frozen inputs with G4's final judging.

WHY. D155 froze Figure 3's inputs as the pull of 26 October 18:30 (findings/recompute/fig3_inputs: g4_collect.jsonl
5ca931f4, its sidecar, s3/ with 68 judge folders of G4 and 2 units still claimed). G4's judging then ended: the S3
collect of 27 October (~/s3_collect/g4_final_20261027 on the Studio, `s3_guard.py collect --replace out_g4r38`) has
11,620 rows (sha256 8f10e30a), the 10,705 rows of 26 October unchanged, 877 verified pass rows and the 38 G4R38
reruns added. D156 (Valerio, 27 October, Q14 O1: "that is a real figure, so I should see that"): Figure 3 and
Supplementary Figure 4 are drawn from that final judging. make_frozen.py refuses an existing set, so this script does
the refreeze, once, and keeps the record consistent.

WHAT IT DOES (nothing is read from the Studio; the pull is a folder already on this machine):
  1. checks the pull: every file listed in its SUMS.json (sha256 taken on the Studio from the bytes sent) has that
     sha256 and no file is unlisted; studio_collect/g4_collect.jsonl is 8f10e30a and its sidecar 45be4ec5; its
     g4_inputs_check/COPY.json and MANIFEST.sha256 equal those inside fig3_g4_inputs.tar (members/fig3_g4_inputs.sha256),
     so the G4 inputs, and the tar, are unchanged; s3/HEAD.txt equals the frozen one (the S3 clone e1ad90d);
  2. checks the current fig3_inputs: every file equal to its SHA256SUMS line, g4_collect.jsonl 5ca931f4;
  3. copies the current fig3_inputs (280 files) byte for byte to findings/recompute/fig3_1026_inputs: the pull the
     scratch S-2 read, on which S484's gate (2) reproduces it (D156);
  4. writes into fig3_inputs the pull's g4_collect.jsonl and sidecar (from studio_collect/), its s3/ (replacing the
     old s3/ whole) and its SUMS.json as SUMS_20261027.json; PULL_SUMMARY.json stays (it describes t1/ and g4_inputs/,
     which are unchanged);
  5. rewrites SHA256SUMS (the fig3_inputs lines replaced, the fig3_1026_inputs lines added, committed lines sorted,
     the tar lines unchanged after them) and MANIFEST.json (the fig3_inputs set, the new fig3_1026_inputs set, the
     totals, and a "refrozen" record with the old and new sha256);
  6. reads everything back: every written file equal to its source and to its SHA256SUMS line.

    uv run python findings/recompute/frozen_inputs/refreeze_fig3.py --pull <the 27 October pull folder>
    uv run python findings/recompute/frozen_inputs/refreeze_fig3.py --check [--pull <folder>]

It refuses (exit 2, nothing written) when fig3_1026_inputs already exists or any check fails. --check writes nothing:
every fig3_inputs and fig3_1026_inputs file against SHA256SUMS, the collect sha256 old and new, and with --pull every
refrozen file against the pull.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
REC = REPO / "findings" / "recompute"
NEW = REC / "fig3_inputs"
OLD = REC / "fig3_1026_inputs"
SUMS = HERE / "SHA256SUMS"
MANIFEST = HERE / "MANIFEST.json"
MEMBERS_G4 = HERE / "members" / "fig3_g4_inputs.sha256"
OLD_COLLECT = "5ca931f4ee7bc358bfa26b12e79750c4e19d64b5bd3d643dea43008ac4640808"
NEW_COLLECT = "8f10e30af2f33f8899198762e85298646f86ebe920b9e2ac86d9bc2f1cc65bd0"
NEW_SIDECAR = "45be4ec5949a454a75c96dd85e06cfd3dcfd446fd6ff71376a1d87f9e52eedc5"
STUDIO_COLLECT = "~/s3_collect/g4_final_20261027 on the Studio (10.15.212.253)"
SUMS_NAME = "SUMS_20261027.json"


class Refused(SystemExit):
    def __init__(self, msg):
        super().__init__(f"REFUSED, nothing written: {msg}")


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def rel(p: Path) -> str:
    return p.resolve().relative_to(REPO).as_posix()


def files_under(d: Path) -> list[Path]:
    return sorted(p for p in d.rglob("*") if p.is_file() and "__pycache__" not in p.parts)


def read_sums() -> tuple[dict, list]:
    committed, tars = {}, []
    for line in SUMS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        h, name = line.split("  ", 1)
        if name.endswith(".tar") and "/" not in name:
            tars.append((name, h))
        else:
            committed[name] = h
    return committed, tars


def write_sums(committed: dict, tars: list) -> None:
    SUMS.write_text("".join(f"{h}  {n}\n" for n, h in sorted(committed.items()))
                    + "".join(f"{h}  {n}\n" for n, h in tars), encoding="utf-8")


def check_pull(pull: Path) -> dict:
    sums = json.loads((pull / "SUMS.json").read_text())
    bad = [k for k, v in sums.items() if not (pull / k).is_file() or sha(pull / k) != v]
    extra = sorted({p.relative_to(pull).as_posix() for p in files_under(pull)} - set(sums) - {"SUMS.json"})
    if bad or extra:
        raise Refused(f"the pull's files are not its SUMS.json: {len(bad)} differ {bad[:3]}, {len(extra)} unlisted "
                      f"{extra[:3]}")
    if sums.get("studio_collect/g4_collect.jsonl") != NEW_COLLECT or \
            sums.get("studio_collect/g4_collect.jsonl.json") != NEW_SIDECAR:
        raise Refused("the pull's collect is not 8f10e30a with sidecar 45be4ec5")
    mem = {}
    for line in MEMBERS_G4.read_text().splitlines():
        if line.strip():
            h, name = line.split("  ", 1)
            mem[name] = h
    for n in ("COPY.json", "MANIFEST.sha256"):
        want = mem.get(f"fig3_g4_inputs/{n}")
        if want is None or sums.get(f"g4_inputs_check/{n}") != want:
            raise Refused(f"the Studio's G4 inputs {n} is not the one in fig3_g4_inputs.tar")
    if (pull / "s3" / "HEAD.txt").read_bytes() != (OLD / "s3" / "HEAD.txt" if OLD.exists() else
                                                   NEW / "s3" / "HEAD.txt").read_bytes():
        raise Refused("the pull's S3 clone head is not the frozen one")
    s3 = [k for k in sums if k.startswith("s3/")]
    return {"files": len(sums), "s3_files": len(s3),
            "judge_folders": {o: len({k.split("/")[3] for k in s3 if k.startswith(f"s3/{o}/judge/")})
                              for o in ("out_g4", "out_g4r38")},
            "claims": {o: len([x for x in (pull / "s3" / o / "claims.txt").read_text().splitlines() if x.strip()])
                       for o in ("out_g4", "out_g4r38")},
            "collect_rows": sum(1 for x in (pull / "studio_collect" / "g4_collect.jsonl").read_bytes().splitlines()
                                if x.strip())}


def plan(pull: Path) -> dict:
    """{repository path under fig3_inputs: source file} of the refrozen set."""
    out = {f"{rel(NEW)}/PULL_SUMMARY.json": (OLD if OLD.exists() else NEW) / "PULL_SUMMARY.json",
           f"{rel(NEW)}/g4_collect.jsonl": pull / "studio_collect" / "g4_collect.jsonl",
           f"{rel(NEW)}/g4_collect.jsonl.json": pull / "studio_collect" / "g4_collect.jsonl.json",
           f"{rel(NEW)}/{SUMS_NAME}": pull / "SUMS.json"}
    for p in files_under(pull / "s3"):
        out[f"{rel(NEW)}/s3/{p.relative_to(pull / 's3').as_posix()}"] = p
    return out


def check(pull: Path | None) -> int:
    committed, _ = read_sums()
    n = 0
    for d in (NEW, OLD):
        for p in files_under(d):
            k = rel(p)
            if committed.get(k) != sha(p):
                raise Refused(f"{k} is not its SHA256SUMS line")
            n += 1
        listed = {k for k in committed if k.startswith(rel(d) + "/")}
        if listed != {rel(p) for p in files_under(d)}:
            raise Refused(f"{rel(d)}: SHA256SUMS lists other files than the folder holds")
    if sha(OLD / "g4_collect.jsonl") != OLD_COLLECT or sha(NEW / "g4_collect.jsonl") != NEW_COLLECT:
        raise Refused("the collects are not 5ca931f4 (fig3_1026_inputs) and 8f10e30a (fig3_inputs)")
    if pull is not None:
        check_pull(pull)
        for k, src in plan(pull).items():
            if sha(REPO / k) != sha(src):
                raise Refused(f"{k} is not its source {src}")
        if {rel(p) for p in files_under(NEW)} != set(plan(pull)):
            raise Refused("fig3_inputs holds other files than the refreeze writes")
    print(f"PASS: {n} files of fig3_inputs and fig3_1026_inputs equal to SHA256SUMS; collects 5ca931f4 (26 October) "
          f"and 8f10e30a (27 October)" + ("; every refrozen file equal to the pull" if pull else ""))
    return 0


def refreeze(pull: Path) -> int:
    if OLD.exists():
        raise Refused(f"{rel(OLD)} exists: the refreeze was made (use --check)")
    info = check_pull(pull)
    committed, tars = read_sums()
    old_files = files_under(NEW)
    for p in old_files:
        if committed.get(rel(p)) != sha(p):
            raise Refused(f"{rel(p)} is not its SHA256SUMS line")
    if {k for k in committed if k.startswith(rel(NEW) + "/")} != {rel(p) for p in old_files}:
        raise Refused(f"{rel(NEW)}: SHA256SUMS lists other files than the folder holds")
    if sha(NEW / "g4_collect.jsonl") != OLD_COLLECT:
        raise Refused(f"{rel(NEW)}/g4_collect.jsonl is not 5ca931f4")
    old_bytes = sum(p.stat().st_size for p in old_files)
    # 3. the 26 October set, byte for byte
    for p in old_files:
        dst = OLD / p.relative_to(NEW)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, dst)
        if sha(dst) != committed[rel(p)]:
            raise Refused(f"copy of {rel(p)} differs")
    # 4. the refrozen set
    src = plan(pull)
    shutil.rmtree(NEW / "s3")
    for k, s in src.items():
        dst = REPO / k
        if s.resolve() == dst.resolve():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(s, dst)
    stray = {rel(p) for p in files_under(NEW)} - set(src)
    if stray:
        raise Refused(f"fig3_inputs holds files the refreeze does not write: {sorted(stray)[:3]}")
    # 5. SHA256SUMS and MANIFEST.json
    for k in [k for k in committed if k.startswith(rel(NEW) + "/")]:
        del committed[k]
    for p in files_under(NEW) + files_under(OLD):
        committed[rel(p)] = sha(p)
    write_sums(committed, tars)
    new_files = files_under(NEW)
    new_bytes = sum(p.stat().st_size for p in new_files)
    m = json.loads(MANIFEST.read_text())
    a5 = m["sets"]["fig3_inputs"]
    m["sets"]["fig3_1026_inputs"] = {
        **a5, "location": rel(OLD), "inventory": "A5 (F1), the S3 part as frozen on 26 October",
        "source": f"{rel(NEW)} as committed before the refreeze of 27 October (the pull of 26 October 18:30)",
        "read_by": "S484 gate (2) only (D156): the scratch S-2's numbers (supp_fig4_inputs/s2_samepull.json) were "
                   "computed on this pull; S476 frozen_copy('fig3_1026')",
        "copy_equals_source": f"{len(old_files)} of {len(old_files)}"}
    m["sets"]["fig3_inputs"] = {
        **a5, "inventory": "A5 (F1), S3 part refrozen 27 October (D156)",
        "source": (f"PULL_SUMMARY.json as frozen on 26 October; the rest the pull of 27 October (folder {pull}): "
                   f"studio_collect/ (the collect made at {STUDIO_COLLECT}), s3/ (out_g4 and out_g4r38 of the clone "
                   f"~/projects/mentori-runs-s3-g4 at e1ad90d) and SUMS.json as {SUMS_NAME}"),
        "taken": ["PULL_SUMMARY.json", "g4_collect.jsonl", "g4_collect.jsonl.json", "s3/", SUMS_NAME],
        "files": len(new_files), "files_copied": len(new_files), "bytes": new_bytes,
        "read_by": "S476 g4c and t1 (Figure 3 panels b and c; findings/recompute/G4_fig3c, T1_L2) and S484 "
                   "(Supplementary Figure 4)",
        "must_match": {"g4_collect.jsonl": NEW_COLLECT, "g4_collect.jsonl.json": NEW_SIDECAR},
        "copy_equals_source": f"{len(new_files)} of {len(new_files)}",
        "must_match_check": {"g4_collect.jsonl": {"want": NEW_COLLECT, "frozen_at": f"{rel(NEW)}/g4_collect.jsonl",
                                                  "frozen": sha(NEW / "g4_collect.jsonl"),
                                                  "equal": sha(NEW / "g4_collect.jsonl") == NEW_COLLECT}},
        "recorded_hash_check": "every file equal to the sha256 the Studio took of the bytes sent (SUMS_20261027.json)",
        "refrozen": {"when": "27 October 2026", "decision": "D156 (Valerio, Q14 O1)",
                     "by": "findings/recompute/frozen_inputs/refreeze_fig3.py",
                     "g4_collect_old": OLD_COLLECT, "g4_collect_new": NEW_COLLECT, "sidecar_new": NEW_SIDECAR,
                     "old_kept_in": rel(OLD), "old_files": len(old_files), "old_bytes": old_bytes,
                     "pull": info, "g4_inputs": "unchanged: the Studio's COPY.json and MANIFEST.sha256 equal "
                                                "those in fig3_g4_inputs.tar, so no tar is rebuilt"}}
    tot = m["sha256sums"]
    tot["committed_files"] = len(committed)
    tot["committed_bytes"] = sum((REPO / k).stat().st_size for k in committed)
    m.setdefault("refrozen_by", []).append({"script": rel(Path(__file__)), "script_sha256": sha(Path(__file__)),
                                            "python": sys.version.split()[0], "sets": ["fig3_inputs",
                                                                                       "fig3_1026_inputs"]})
    MANIFEST.write_text(json.dumps(m, indent=1) + "\n")
    # 6. read back
    check(pull)
    print(f"refrozen {rel(NEW)}: {len(new_files)} files, {new_bytes:,} bytes, collect {OLD_COLLECT[:8]} -> "
          f"{NEW_COLLECT[:8]} ({info['collect_rows']:,} rows; judge folders {info['judge_folders']}, claims "
          f"{info['claims']}); kept {rel(OLD)}: {len(old_files)} files, {old_bytes:,} bytes; SHA256SUMS "
          f"{len(committed)} committed lines and {len(tars)} tars")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pull", type=Path, default=None)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    pull = a.pull.expanduser().resolve() if a.pull else None
    if a.check:
        return check(pull)
    if pull is None:
        ap.error("--pull is required to refreeze")
    return refreeze(pull)


if __name__ == "__main__":
    raise SystemExit(main())
