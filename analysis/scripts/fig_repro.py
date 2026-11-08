#!/usr/bin/env python3
"""fig_repro - D155: the shared module every figure script imports, so every output is deterministic and every
input is checked.

WHY. D155 (Valerio, 26 October): "Whatever you do, it should be all reproducible". One command is to rebuild every
main and Supplementary figure from frozen inputs and check each file byte-equal to the committed plate. Two things
stood in the way, and this module removes both for any script that imports it:
  1. Inputs. The figure scripts read scratch folders (findings/audits/scratch_repro_2026-10-26/INVENTORY.md, F1 to
     F8). Frozen copies are committed under findings/recompute/<set>_inputs/; sets too large for git are tars kept
     outside it, their sha256 committed in findings/recompute/frozen_inputs/SHA256SUMS (INVENTORY.md section 4a).
     frozen() returns a path inside either and refuses a tar that is missing or whose sha256 differs.
  2. Write times. openpyxl stamps the time of saving into docProps/core.xml (dcterms:created, dcterms:modified) and
     into every zip member's date, so the same cells give a different file each run (15 of the 17 committed Source
     Data workbooks on 26 October). deterministic_xlsx() rewrites a workbook exactly as S456_fig1_design.py's
     write_source_data does (the two core times removed, every member dated 1980-01-01 00:00:00, deflated, in the
     order openpyxl wrote them), so Figure 1's committed workbook is a fixed point of it (fig_repro_test.py checks).
     matplotlib's PDF and SVG carry a date unless told not to; pdf_metadata() and svg_metadata() say so, and
     check_pdf_deterministic() / check_svg_deterministic() refuse a file that still carries one. matplotlib also
     salts every SVG clip-path and glyph id with a fresh uuid4 unless rcParams["svg.hashsalt"] is set
     (backend_svg); matplotlib_rc() sets it (S447, S456, S457, S459 and S461 set it in their own rc).

API
  sha256_file(path) -> str                      hex sha256 of a file, read in 1 MiB blocks.
  frozen(set_name, rel, *, root=None) -> Path   path of a frozen input; refuses a missing or altered input.
  check_committed(path, *, root=None) -> Path   every file under a committed set's path against SHA256SUMS.
  frozen_label(path, *, root=None) -> str       "frozen:<set>/<rel>" or "frozen:<name>.tar/<rel>", for provenance.
  recorded_label(key, extra) -> str             a pre-D155 recorded path as its frozen label (MANIFEST.json sources).
  check_recorded(inputs, recorded, translate)   refuse a frozen input whose sha256 differs from the plate's record.
  pin_hash_seed(seed="0") -> None               re-execute the script under PYTHONHASHSEED=0 (PDF font subsets).
  deterministic_xlsx(path) -> None              rewrite an xlsx in place so its bytes depend only on its content.
  check_xlsx_deterministic(path) -> None        raise unless the xlsx carries no write time.
  pdf_metadata(title) / svg_metadata(title)     savefig metadata dicts that write no date, creator or producer.
  matplotlib_rc(salt) -> dict                   rcParams fixing matplotlib's SVG ids (svg.hashsalt), else random.
  check_pdf_deterministic(path) -> None         raise unless the PDF has no CreationDate/ModDate (or the fixed one).
  check_svg_deterministic(path) -> None         raise unless the SVG has no dc:date (or the fixed one).
  FrozenInputError                              the exception every refusal raises.

frozen(set_name, rel). A committed set is findings/recompute/<set_name>_inputs/; a tarred set is the tar
<set_name>.tar named in findings/recompute/frozen_inputs/SHA256SUMS ("<sha256>  <file name>" lines, as sha256sum
writes them), read from the folder in env FROZEN_TARS (default ~/Mentori_scratch_keep/frozen_2026-10-26). The tar
is checked against its committed sha256, extracted once (tarfile's "data" filter: no absolute paths, no "..", no
links leaving the folder) into findings/recompute/frozen_inputs/extracted/<set_name>/ (gitignored), and the
sha256 of every extracted file is recorded there. Each call checks the files it returns against the committed list of
the tar's files, findings/recompute/frozen_inputs/members/<set_name>.sha256 (each sha256 equal, none extra, none
missing), not against that record, so an edited, added or deleted extracted file is refused even when the record
was edited with it. A committed set that holds a SHA256SUMS of its own is checked the same
way. rel is relative to the set's folder (or the tar's top level) and may name a file or a folder.

USAGE
  uv run python scripts/fig_repro.py selftest     the xlsx is written twice, 2.1 s apart, and must be byte-equal
                                                  after deterministic_xlsx (and must differ before it).
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shutil
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RECOMPUTE = REPO / "findings" / "recompute"
DEFAULT_TARS = Path.home() / "Mentori_scratch_keep" / "frozen_2026-10-26"
ZIP_DATE = (1980, 1, 1, 0, 0, 0)          # the zip format's earliest date; S456_fig1_design.py write_source_data
FIXED_DATE = "2026-10-10"                 # LOCK.toml [date] fixed; the only date a PDF or SVG may carry
PDF_FIXED = "D:20261010000000"            # FIXED_DATE as a PDF date string (an optional "Z" or offset follows)
EXTRACT_RECORD = ".fig_repro_extracted.json"


class FrozenInputError(RuntimeError):
    """A frozen input is missing, altered, or unsafe; the message names what to fetch or re-extract."""


def sha256_file(path) -> str:
    """Hex sha256 of a file, read in 1 MiB blocks."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


# ------------------------------------------------------------------------------------------------- frozen inputs
def _read_sums(path: Path) -> dict[str, str]:
    """{file name: sha256} from a sha256sum-style file; a malformed line is an error, not skipped."""
    sums = {}
    for n, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.fullmatch(r"([0-9a-f]{64}) [ *](.+)", line.rstrip())
        if not m:
            raise FrozenInputError(f"{path}:{n}: not a '<sha256>  <name>' line: {line!r}")
        name = m.group(2)
        if name in sums:
            raise FrozenInputError(f"{path}:{n}: {name} listed twice")
        sums[name] = m.group(1)
    return sums


def _files_under(p: Path, skip=()) -> list[Path]:
    """Files under p (or p itself), leaving out the paths in skip (a set's own record of its files)."""
    skip = {Path(q).resolve() for q in skip}
    return [p] if p.is_file() else sorted(q for q in p.rglob("*") if q.is_file() and q.resolve() not in skip)


def _resolve_inside(base: Path, rel: str) -> Path:
    if Path(rel).is_absolute():
        raise FrozenInputError(f"frozen(): rel must be relative to the set, got {rel!r}")
    p = (base / rel).resolve()
    if p != base.resolve() and base.resolve() not in p.parents:
        raise FrozenInputError(f"frozen(): {rel!r} leaves the set folder {base}")
    return p


def _check_against(record: dict[str, str], base: Path, target: Path, what: str, skip=()) -> None:
    """Every file under target (but skip) must be in record (paths relative to base) with that sha256."""
    files = _files_under(target, skip)
    if not files:
        raise FrozenInputError(f"{what}: {target} holds no file")
    for f in files:
        key = f.relative_to(base.resolve()).as_posix()
        if key not in record:
            raise FrozenInputError(f"{what}: {key} is not in the set's recorded file list")
        got = sha256_file(f)
        if got != record[key]:
            raise FrozenInputError(f"{what}: {key} sha256 {got[:12]} differs from the recorded {record[key][:12]}; "
                                   f"delete {base} and run again to re-extract")


def _extract(tar: Path, want_sha: str, dest: Path) -> None:
    """Extract tar into dest once, atomically, and record every file's sha256 beside it."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=f".{dest.name}.", dir=dest.parent))
    try:
        with tarfile.open(tar) as tf:
            try:
                tf.extractall(tmp, filter="data")
            except tarfile.FilterError as e:
                raise FrozenInputError(f"{tar.name}: refused an unsafe member ({e})") from e
        if (tmp / EXTRACT_RECORD).exists():
            raise FrozenInputError(f"{tar.name}: holds a top-level {EXTRACT_RECORD}, a name this module reserves")
        files = {f.relative_to(tmp).as_posix(): sha256_file(f) for f in _files_under(tmp)}
        (tmp / EXTRACT_RECORD).write_text(json.dumps({"tar": tar.name, "tar_sha256": want_sha, "files": files},
                                                     indent=1, sort_keys=True) + "\n")
        try:
            tmp.rename(dest)
        except OSError:
            if not (dest / EXTRACT_RECORD).exists():  # another process did not win the race: a real error
                raise
    finally:
        if tmp.exists():
            shutil.rmtree(tmp)


def frozen(set_name: str, rel: str = ".", *, root=None) -> Path:
    """Path of the frozen input rel inside set set_name; raises FrozenInputError when missing or altered.

    A committed set is <root>/<set_name>_inputs/; a tarred set is <set_name>.tar listed in
    <root>/frozen_inputs/SHA256SUMS, extracted (after its sha256 is checked) to <root>/frozen_inputs/extracted/
    <set_name>/. root defaults to findings/recompute; the tar folder is env FROZEN_TARS.
    """
    root = Path(root) if root is not None else RECOMPUTE
    stem = set_name[:-4] if set_name.endswith(".tar") else set_name
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", stem):
        raise FrozenInputError(f"frozen(): set name {set_name!r} is not a plain name")
    sums_file = root / "frozen_inputs" / "SHA256SUMS"
    sums = _read_sums(sums_file) if sums_file.exists() else {}
    tar_name = f"{stem}.tar"
    committed = root / f"{stem}_inputs"

    if tar_name in sums:
        if committed.exists():
            raise FrozenInputError(f"frozen(): {stem} is both a committed folder {committed} and a tar in "
                                   f"{sums_file}; one source per set")
        want = sums[tar_name]
        dest = root / "frozen_inputs" / "extracted" / stem
        rec_file = dest / EXTRACT_RECORD
        if rec_file.exists():
            rec = json.loads(rec_file.read_text())
            if rec.get("tar_sha256") != want:
                raise FrozenInputError(
                    f"{dest} was extracted from {rec.get('tar')} sha256 {str(rec.get('tar_sha256'))[:12]}, but "
                    f"{sums_file} now lists {want[:12]}; delete {dest} and run again")
        else:
            if dest.exists():
                raise FrozenInputError(f"{dest} exists without its {EXTRACT_RECORD} (an interrupted or hand-made "
                                       f"extraction); delete it and run again")
            tars = Path(os.environ.get("FROZEN_TARS", str(DEFAULT_TARS))).expanduser()
            tar = tars / tar_name
            if not tar.is_file():
                raise FrozenInputError(
                    f"frozen input {tar_name} (sha256 {want}) is missing from {tars}. Download {tar_name} from the "
                    f"paper's Zenodo deposit (its data files) into that folder, or set FROZEN_TARS to the folder "
                    f"that holds it")
            got = sha256_file(tar)
            if got != want:
                raise FrozenInputError(
                    f"{tar} has sha256 {got}, but {sums_file} lists {want}: not the frozen copy. Download "
                    f"{tar_name} again from the paper's Zenodo deposit")
            _extract(tar, want, dest)
            rec = json.loads(rec_file.read_text())
        # Audit 27 Oct F9: the record above lives in the gitignored extraction, so the files are checked against the
        # committed list of the tar's members instead: each sha256 equal, none extra, none missing.
        members_file = root / "frozen_inputs" / "members" / f"{stem}.sha256"
        if not members_file.is_file():
            raise FrozenInputError(f"{members_file} is missing: the committed list of {tar_name}'s files, which every "
                                   f"extracted file is checked against")
        members = _read_sums(members_file)
        target = _resolve_inside(dest, rel)
        if not target.exists():
            raise FrozenInputError(f"frozen input {rel!r} is not in {tar_name} (extracted at {dest})")
        _check_against(members, dest, target, f"frozen set {stem}", skip=[rec_file])
        t = target.relative_to(dest.resolve()).as_posix()
        gone = [k for k in sorted(members) if (t == "." or k == t or k.startswith(t + "/"))
                and not (dest / k).is_file()]
        if gone:
            raise FrozenInputError(f"frozen set {stem}: {gone[0]} (of {len(gone)} missing) is listed in {members_file} "
                                   f"but not in {dest}; delete {dest} and run again to re-extract")
        return target

    if not committed.is_dir():
        raise FrozenInputError(
            f"frozen set {stem!r}: neither {committed} (a committed set) nor {tar_name} in {sums_file} (a tarred "
            f"set) exists")
    target = _resolve_inside(committed, rel)
    if not target.exists():
        raise FrozenInputError(f"frozen input {rel!r} is not in {committed}")
    own = committed / "SHA256SUMS"
    if own.exists():
        _check_against(_read_sums(own), committed, target, f"frozen set {stem}", skip=[own])
    return target


def check_committed(path, *, root=None) -> Path:
    """Require every file under path (a file or folder of a committed set, as frozen() returns it) to be listed in
    <root>/frozen_inputs/SHA256SUMS with that sha256; returns path. frozen() checks a tar's files and a committed set
    that carries its own SHA256SUMS, but the committed sets list their files in the shared SHA256SUMS (make_frozen.py),
    so a figure script calls this on every committed input it reads. A file not listed there is refused too."""
    root = Path(root) if root is not None else RECOMPUTE
    base = root.resolve().parents[1]                      # SHA256SUMS lines are repository-relative
    sums = _read_sums(root / "frozen_inputs" / "SHA256SUMS")
    path = Path(path).resolve()
    files = _files_under(path)
    if not files:
        raise FrozenInputError(f"{path} holds no file")
    for f in files:
        key = f.relative_to(base).as_posix()
        if key not in sums:
            raise FrozenInputError(f"{key} is not listed in {root / 'frozen_inputs' / 'SHA256SUMS'}: not a frozen file")
        got = sha256_file(f)
        if got != sums[key]:
            raise FrozenInputError(f"{key}: sha256 {got[:12]} differs from SHA256SUMS {sums[key][:12]}: the frozen "
                                   f"copy was changed; restore it from git")
    return path


def frozen_label(path, *, root=None) -> str:
    """A machine-independent name for a frozen input, for a provenance file: "frozen:<set>/<rel>" for a committed set
    (findings/recompute/<set>_inputs/<rel>), "frozen:<name>.tar/<rel>" for a file extracted from a tar (<rel> inside
    the tar, its top folder included); any other path inside the repository repository-relative."""
    root = (Path(root) if root is not None else RECOMPUTE).resolve()
    p = Path(path).resolve()
    ext = root / "frozen_inputs" / "extracted"
    if ext in p.parents:
        stem, *rest = p.relative_to(ext).parts
        return f"frozen:{stem}.tar/" + "/".join(rest)
    if root in p.parents:
        first, *rest = p.relative_to(root).parts
        if first.endswith("_inputs") and first != "frozen_inputs" and rest:   # frozen_inputs/ holds the records
            return f"frozen:{first[:-len('_inputs')]}/" + "/".join(rest)
    return p.relative_to(root.parents[1]).as_posix()


def recorded_label(key: str, extra: dict | None = None, *, root=None) -> str:
    """The frozen_label() of an input that a provenance file written before D155 names by the folder it was read from
    (a scratch pull, ~/k1_inputs/runs, ...): the longest source folder in <root>/frozen_inputs/MANIFEST.json ("sets"
    and "tars", each with its "source") that holds key is replaced by its frozen set ("frozen:<set>/" for a committed
    set, "frozen:<tar>/<top folder>/" for a tar). extra ({recorded prefix: label prefix}) adds what MANIFEST.json does
    not hold (another step's set). Any other key is returned unchanged."""
    root = Path(root) if root is not None else RECOMPUTE
    pre = dict(extra or {})
    man = json.loads((root / "frozen_inputs" / "MANIFEST.json").read_text())
    for s in (man.get("sets") or {}).values():
        loc = Path(s["location"])
        set_name = loc.name[:-len("_inputs")] if loc.name.endswith("_inputs") else None
        if set_name and s.get("source"):
            pre.setdefault(s["source"].rstrip("/") + "/", f"frozen:{set_name}/")
    for t, s in (man.get("tars") or {}).items():
        if s.get("source"):
            pre.setdefault(s["source"].rstrip("/") + "/", f"frozen:{t}/{s['top_folder']}/")
    for k in sorted(pre, key=len, reverse=True):
        if key.startswith(k):
            return pre[k] + key[len(k):]
    return key


def check_recorded(inputs: dict, recorded: dict, translate=lambda k: k) -> dict:
    """D155: refuse to build when a frozen input differs from the one the committed plate recorded.

    inputs: {label: sha256} this build read; recorded: the committed provenance's {key: sha256}, each key passed
    through translate (recorded_label for a plate written before D155). Every recorded key that translates to a
    frozen label ("frozen:...") must be read now with the same sha256; a frozen input read now that the plate did not
    record is listed, not refused (the record grows by it). Returns {"compared": n, "not_recorded_before": [...]}."""
    rec = {}
    for k, v in recorded.items():
        lab = translate(k)
        if lab in rec and rec[lab] != v:
            raise FrozenInputError(f"the committed plate records {lab} twice with different sha256")
        rec[lab] = v
    bad = []
    for lab, want in sorted(rec.items()):
        if not lab.startswith("frozen:"):
            continue
        if lab not in inputs:
            bad.append(f"{lab}: recorded by the committed plate, not read by this build")
        elif inputs[lab] != want:
            bad.append(f"{lab}: sha256 {inputs[lab][:12]} now, the committed plate recorded {want[:12]}")
    if bad:
        raise FrozenInputError(f"{len(bad)} frozen inputs differ from the committed plate's record, nothing written; "
                               f"first: {bad[0]}")
    return {"compared": sum(1 for lab in rec if lab.startswith("frozen:")),
            "not_recorded_before": sorted(lab for lab in inputs if lab.startswith("frozen:") and lab not in rec)}


def pin_hash_seed(seed: str = "0") -> None:
    """Run the calling script under PYTHONHASHSEED=seed: when the environment holds another value or none, re-execute
    the same command line (sys.orig_argv) with it set, so this call never returns in the first process.

    WHY. Python draws a new string-hash seed per process unless PYTHONHASHSEED is set, and fontTools' subsetter, which
    matplotlib's PDF backend uses to embed a TrueType font (pdf.fonttype 42), builds the subset's AAT 'prop' table
    through a set ordered by those hashes. Supplementary Figure 2's PDF (S461) came out in two versions on 26 October
    (seeds 0, 2, 3, 5 one sha256; 1 and 4 another; same text, PNG and SVG). Call it first thing in a figure script's
    main(), before anything is read or drawn."""
    if os.environ.get("PYTHONHASHSEED") == seed:
        return
    sys.stdout.flush()
    sys.stderr.flush()
    os.execve(sys.executable, [sys.executable, *sys.orig_argv[1:]], {**os.environ, "PYTHONHASHSEED": seed})


# ------------------------------------------------------------------------------------------------------ xlsx
_CORE_TIME = re.compile(rb"<dcterms:(created|modified)\b[^>]*>[^<]*</dcterms:\1>")


def deterministic_xlsx(path) -> None:
    """Rewrite an openpyxl-written xlsx in place so its bytes depend only on its content.

    As S456_fig1_design.py write_source_data: dcterms:created and dcterms:modified removed from docProps/core.xml,
    every member dated 1980-01-01 00:00:00 and deflated at the default level, in the order the file holds them.
    Idempotent: a deterministic workbook is returned byte-equal.
    """
    path = Path(path)
    src = path.read_bytes()
    out = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(src)) as zin, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        names = [i.filename for i in zin.infolist()]
        if len(names) != len(set(names)):
            raise ValueError(f"{path}: a zip member is listed twice")
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename == "docProps/core.xml":
                data = _CORE_TIME.sub(b"", data)
            zi = zipfile.ZipInfo(info.filename, date_time=ZIP_DATE)
            zi.compress_type, zi.external_attr = zipfile.ZIP_DEFLATED, info.external_attr
            zout.writestr(zi, data)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_bytes(out.getvalue())
    os.replace(tmp, path)
    check_xlsx_deterministic(path)


def check_xlsx_deterministic(path) -> None:
    """Raise ValueError unless every member is dated 1980-01-01 and core.xml carries no created/modified time."""
    with zipfile.ZipFile(path) as z:
        bad = [i.filename for i in z.infolist() if i.date_time != ZIP_DATE]
        if bad:
            raise ValueError(f"{path}: {len(bad)} zip member(s) carry a write date, e.g. {bad[0]}")
        if "docProps/core.xml" in z.namelist():
            core = z.read("docProps/core.xml")
            if b"dcterms:created" in core or b"dcterms:modified" in core:
                raise ValueError(f"{path}: docProps/core.xml carries a creation or modification time")


# ------------------------------------------------------------------------------------------------- PDF, SVG
def pdf_metadata(title: str) -> dict:
    """matplotlib savefig(..., metadata=) for a PDF that writes no date, creator or producer (as S456)."""
    return {"Title": title, "Author": None, "Subject": None, "Keywords": None, "Creator": None,
            "Producer": None, "CreationDate": None, "ModDate": None}


def svg_metadata(title: str) -> dict:
    """matplotlib savefig(..., metadata=) for an SVG that writes no date or creator (as S456)."""
    return {"Title": title, "Date": None, "Creator": None}


def matplotlib_rc(salt: str) -> dict:
    """rcParams to merge into a figure script's rc: a fixed svg.hashsalt, so SVG ids repeat run to run."""
    if not salt:
        raise ValueError("matplotlib_rc(): give a fixed, non-empty salt (the script's S number)")
    return {"svg.hashsalt": salt}


def check_pdf_deterministic(path) -> None:
    """Raise ValueError if the PDF carries a CreationDate or ModDate other than the fixed date, in its Info
    dictionary or its XMP metadata."""
    import fitz  # PyMuPDF; reads Info dictionaries inside compressed object streams too

    path = Path(path)
    with fitz.open(path) as doc:
        meta = doc.metadata or {}
        xmp = doc.get_xml_metadata() or ""
    for key in ("creationDate", "modDate"):
        v = (meta.get(key) or "").strip()
        if v and not v.startswith(PDF_FIXED):
            raise ValueError(f"{path}: Info {key} is {v!r} (only none or {PDF_FIXED} is reproducible); save with "
                             f"metadata=fig_repro.pdf_metadata(title)")
    for m in re.finditer(r"<xmp:(CreateDate|ModifyDate|MetadataDate)>([^<]*)<", xmp):
        if not m.group(2).startswith(FIXED_DATE):
            raise ValueError(f"{path}: XMP {m.group(1)} is {m.group(2)!r}")
    raw = path.read_bytes()  # an uncompressed Info dictionary fitz might not surface
    for m in re.finditer(rb"/(CreationDate|ModDate)\s*\(([^)]*)\)", raw):
        if not m.group(2).decode("latin-1").startswith(PDF_FIXED):
            raise ValueError(f"{path}: /{m.group(1).decode()} ({m.group(2).decode('latin-1')})")


def check_svg_deterministic(path) -> None:
    """Raise ValueError if the SVG carries a dc:date other than the fixed date."""
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r"<dc:date>([^<]*)</dc:date>", text):
        if not m.group(1).strip().startswith(FIXED_DATE):
            raise ValueError(f"{path}: dc:date {m.group(1)!r}; save with metadata=fig_repro.svg_metadata(title)")


# ------------------------------------------------------------------------------------------------- selftest
def _write_sample_xlsx(path: Path) -> None:
    from openpyxl import Workbook
    from openpyxl.styles import Font

    wb = Workbook()
    ws = wb.active
    ws.title = "Fig. 1a"
    ws.append(["model", "pass_rate_4"])
    for c in ws[1]:
        c.font = Font(bold=True)
    ws.append(["a", 0.5])
    ws.append(["b", 0.25])
    wb.save(path)


def selftest(fix=None, gap_s: float = 2.1, log=print) -> bool:
    """Write the same workbook twice gap_s apart (2.1 s: a zip date counts in 2-second steps), run fix on both and
    require byte-equal files; also require that the raw files differ, so the check can see a write time at all."""
    import time

    fix = deterministic_xlsx if fix is None else fix
    with tempfile.TemporaryDirectory() as d:
        a, b = Path(d) / "a.xlsx", Path(d) / "b.xlsx"
        _write_sample_xlsx(a)
        time.sleep(gap_s)
        _write_sample_xlsx(b)
        raw_differ = a.read_bytes() != b.read_bytes()
        log(f"raw workbooks {gap_s:g} s apart differ: {raw_differ} ({sha256_file(a)[:12]} vs {sha256_file(b)[:12]})")
        fix(a)
        fix(b)
        equal = a.read_bytes() == b.read_bytes()
        log(f"after the fix byte-equal: {equal} ({sha256_file(a)[:12]} vs {sha256_file(b)[:12]})")
        return raw_differ and equal


def main(argv):
    if argv[1:2] == ["selftest"]:
        ok = selftest()
        print("selftest PASS" if ok else "selftest FAIL")
        return 0 if ok else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
