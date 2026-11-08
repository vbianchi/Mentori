# backend/agents/notebook/import_scan.py
"""
D72 (Valerio, 15 October, Q40): a missing library is the harness's gap, not the model's failure.

Before generated code runs, its imports are scanned (scan) and each top-level module is classified in the
interpreter that runs the code (check):
  - "stdlib": in that interpreter's standard library;
  - "present": importable there (importlib.util.find_spec finds it);
  - "installed": missing and on ALLOW_LIST: installed at its pinned requirement with
    `uv pip install --python <that interpreter> <requirement>`, the requirement, the command and its exit status
    recorded; a failed install is recorded and the code runs anyway (it fails visibly);
  - "not_allowed": missing and not on ALLOW_LIST: nothing is downloaded; the code runs and its ModuleNotFoundError
    is the model's failure.
Nothing outside ALLOW_LIST is ever installed, and nothing at another version than the pin.

The kernel (kernel.py, NotebookKernel.execute) runs this before each execution of generated code while a recorder
is set (SCANS, set per attempt by the coder benchmark's _dispatch); the harness's own setup, extraction and
introspection code is not scanned. Outside such a recorder nothing is scanned or installed.
"""

import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
from contextvars import ContextVar
from typing import Any, Callable, Dict, List, Optional, Tuple

# Top-level module name -> pinned requirement (D72): every library the 20 tasks of coder_ground_truth.json name
# (pandas, numpy, scipy, scikit-learn, lifelines, statsmodels; FREE_FORM_SYSTEM names the same six) and the vetted
# extras (statsmodels 0.14.6 as in the Studio's Mentori-Old environment, pydeseq2, pingouin, matplotlib, seaborn).
# Each pin is the version experiments/mentori/uv.lock holds (check_codegen compares them with the lock).
ALLOW_LIST: Dict[str, str] = {
    "pandas": "pandas==2.3.3",
    "numpy": "numpy==2.4.1",
    "scipy": "scipy==1.17.0",
    "sklearn": "scikit-learn==1.8.0",
    "lifelines": "lifelines==0.30.1",
    "statsmodels": "statsmodels==0.14.6",
    "pydeseq2": "pydeseq2==0.5.4",
    "pingouin": "pingouin==0.7.0",
    "matplotlib": "matplotlib==3.10.8",
    "seaborn": "seaborn==0.13.2",
}

STATUSES = ("stdlib", "present", "installed", "not_allowed")

# The recorder of the current attempt: a list the kernel appends one record to per execution of generated code.
# None (the default) means no scan: the kernel then runs code as before.
SCANS: ContextVar[Optional[List[Dict[str, Any]]]] = ContextVar("import_scan_records", default=None)

# Fallback when the code does not parse (an IPython magic, a syntax error): import statements (each line split on ";",
# a compound header on the same line, "try: import x", "if c: from x import y", stripped first), literal dynamic
# imports, and import statements inside a literal passed to exec, eval or compile
_RE_IMPORT = re.compile(r"^[ \t]*import[ \t]+([A-Za-z_][\w.]*(?:[ \t]+as[ \t]+\w+)?(?:[ \t]*,[ \t]*[A-Za-z_][\w.]*"
                        r"(?:[ \t]+as[ \t]+\w+)?)*)")
_RE_FROM = re.compile(r"^[ \t]*from[ \t]+([A-Za-z_][\w.]*)[ \t]+import\b")
_RE_HEADER = re.compile(r"^[ \t]*(?:(?:try|else|finally)[ \t]*:|(?:if|elif|while|for|with|except|async[ \t]+with|"
                        r"async[ \t]+for)\b[^:\n]*:)[ \t]*(?=\S)")
_RE_DYNAMIC = re.compile(r"\b(?:import_module|__import__)\(\s*(?:name\s*=\s*)?[rbu]?['\"]([A-Za-z_][\w.]*)['\"]")
_RE_EXEC = re.compile(r"\b(?:exec|eval|compile)\(\s*([rbu]?(?:'[^'\n]*'|\"[^\"\n]*\"))")
_RE_NO_MODULE = re.compile(r"No module named '([^']+)'")
_RE_FROM_NAMES = re.compile(r"^[ \t]*from[ \t]+([A-Za-z_][\w.]*)[ \t]+import[ \t]+(.+?)[ \t]*$")
_RE_NAME_ERROR = re.compile(r"name '([^']+)' is not defined")
# A package install the generated code runs itself (!pip install, %pip, uv pip, conda, subprocess with "pip",
# "install", Mentori's install_package tool). Recorded, never run by the harness (D72: nothing outside the allow-list
# is downloaded by the harness; this record shows when the model's code tries to)
_RE_INSTALL = re.compile(r"\b(?:pip3?|uv[ \t]+pip|conda|mamba|micromamba)[ \t]+install\b"
                         r"|['\"](?:pip3?|uv)['\"][ \t]*,[ \t]*(?:['\"]pip['\"][ \t]*,[ \t]*)?['\"]install['\"]"
                         r"|\binstall_package\(")


def _top(name: str) -> str:
    return name.split(".", 1)[0]


def _literal_arg(node: ast.Call, keyword: Optional[str] = None) -> Optional[str]:
    """The call's first argument, or its keyword argument of that name, when it is a literal string."""
    arg = node.args[0] if node.args else next((k.value for k in node.keywords if keyword and k.arg == keyword), None)
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        return arg.value
    return None


def _call_name(func: ast.expr) -> Optional[str]:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _import_module_aliases(tree: ast.AST) -> set:
    """Names import_module is bound to (from importlib import import_module as im)."""
    names = {"import_module"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module == "importlib":
            names.update(a.asname for a in node.names if a.name == "import_module" and a.asname)
    return names


def _scan_regex(code: str, found: set) -> None:
    for line in code.splitlines():
        for piece in line.split(";"):
            while True:
                stripped = _RE_HEADER.sub("", piece, count=1)
                if stripped == piece:
                    break
                piece = stripped
            m = _RE_IMPORT.match(piece)
            if m:
                for part in m.group(1).split(","):
                    found.add(_top(part.split()[0]))
            m = _RE_FROM.match(piece)
            if m:
                found.add(_top(m.group(1)))
    found.update(_top(m.group(1)) for m in _RE_DYNAMIC.finditer(code))
    for m in _RE_EXEC.finditer(code):
        try:
            inner = ast.literal_eval(m.group(1))
        except (ValueError, SyntaxError):
            continue
        if isinstance(inner, bytes):
            inner = inner.decode("utf-8", "replace")
        found.update(scan_with_method(inner)[0])


def scan_with_method(code: str) -> Tuple[List[str], str]:
    """(the top-level modules code imports, sorted; "ast" or "regex"). ast covers import and from-import at any
    depth (inside functions, classes, try blocks); import_module (also by an alias, also called with name=) and
    __import__ (bare or as an attribute, importlib.__import__) with a literal name; and the code inside a literal
    passed to exec, eval or compile, scanned the same way. A relative import (from . import x,
    import_module(".x")) names no module to install and is left out. When the code does not parse, a regex stands in
    (_scan_regex; it does not follow aliases of import_module)."""
    found: set = set()
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError):
        _scan_regex(code, found)
        return sorted(found), "regex"
    dynamic = _import_module_aliases(tree) | {"__import__"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(_top(a.name) for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                found.add(_top(node.module))
        elif isinstance(node, ast.Call):
            called = _call_name(node.func)
            if called in dynamic:
                name = _literal_arg(node, "name")
                if name and not name.startswith("."):
                    found.add(_top(name))
            elif called in ("exec", "eval", "compile"):
                inner = _literal_arg(node, "source")
                if inner:
                    found.update(scan_with_method(inner)[0])
    return sorted(found), "ast"


def scan(code: str) -> List[str]:
    """The top-level modules code imports (scan_with_method)."""
    return scan_with_method(code)[0]


def import_bindings(code: str) -> Dict[str, List[str]]:
    """D75 Q64: per top-level module the code imports, the names its import statements bind in the namespace:
    "import gseapy as gp" binds gp; "import a.b" binds a; "from gseapy import enrichr, prerank as pr" binds enrichr
    and pr ("*" binds names that cannot be known, and is left out). Any depth, as scan; a regex stands in when the
    code does not parse (import and from-import statements on their own lines)."""
    out: Dict[str, set] = {}
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError):
        tree = None
    if tree is not None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    out.setdefault(_top(a.name), set()).add(a.asname or _top(a.name))
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                for a in node.names:
                    if a.name != "*":
                        out.setdefault(_top(node.module), set()).add(a.asname or a.name)
    else:
        for line in code.splitlines():
            for piece in line.split(";"):
                while True:
                    stripped = _RE_HEADER.sub("", piece, count=1)
                    if stripped == piece:
                        break
                    piece = stripped
                m = _RE_IMPORT.match(piece)
                if m:
                    for part in m.group(1).split(","):
                        words = part.split()
                        name = words[2] if len(words) == 3 and words[1] == "as" else _top(words[0])
                        out.setdefault(_top(words[0]), set()).add(name)
                m = _RE_FROM_NAMES.match(piece)
                if m:
                    for part in m.group(2).strip("() \t").split(","):
                        words = part.split()
                        if not words or words[0] == "*":
                            continue
                        name = words[2] if len(words) == 3 and words[1] == "as" else words[0]
                        out.setdefault(_top(m.group(1)), set()).add(name)
    return {k: sorted(v) for k, v in sorted(out.items())}


def install_lines(code: str) -> List[str]:
    """Each line of code that runs a package install itself (_RE_INSTALL), whole, in order (D72: recorded only)."""
    return [ln for ln in code.splitlines() if _RE_INSTALL.search(ln)]


# Run in the interpreter that runs generated code: per module "stdlib", "present" or "missing". It defines only
# underscore names and deletes them, so a kernel's namespace is left as it was. It writes through sys.stdout and
# builtins.print, never the namespace's print, which generated code may have rebound.
PROBE_TEMPLATE = """
import importlib.util as _mentori_iu, json as _mentori_json, sys as _mentori_sys
def _mentori_probe(_names):
    _out = {}
    for _n in _names:
        if _n in _mentori_sys.stdlib_module_names or _n in _mentori_sys.builtin_module_names:
            _out[_n] = "stdlib"
            continue
        try:
            _out[_n] = "present" if (_n in _mentori_sys.modules or _mentori_iu.find_spec(_n) is not None) else "missing"
        except (ImportError, ValueError):
            _out[_n] = "missing"
    return _out
__import__("builtins").print("__IMPORT_PROBE__" + _mentori_json.dumps({"executable": _mentori_sys.executable,
                                                  "modules": _mentori_probe(%s)}), file=_mentori_sys.stdout,
                              flush=True)
del _mentori_iu, _mentori_json, _mentori_sys, _mentori_probe
"""
PROBE_MARK = "__IMPORT_PROBE__"


def probe_code(modules: List[str]) -> str:
    return PROBE_TEMPLATE % json.dumps(list(modules))


def parse_probe(stdout: str) -> Optional[Dict[str, Any]]:
    for line in stdout.splitlines():
        if line.startswith(PROBE_MARK):
            return json.loads(line[len(PROBE_MARK):])
    return None


def probe_subprocess(modules: List[str], python: str, cwd: Optional[str] = None,
                     run: Callable = subprocess.run) -> Dict[str, str]:
    """The probe run as `python -c` in a fresh process of that interpreter (the kernel itself probes in its own
    process, kernel.py; this is the stand-alone form)."""
    p = run([python, "-c", probe_code(modules)], capture_output=True, text=True, cwd=cwd)
    data = parse_probe(p.stdout or "")
    if data is None:
        raise RuntimeError(f"import probe failed in {python}: exit {p.returncode}: {p.stderr}")
    return data["modules"]


def uv_binary() -> Optional[str]:
    """The uv that runs the harness (uv run sets UV), else the one on PATH."""
    return os.environ.get("UV") or shutil.which("uv")


# One install at a time in this process: attempts that run at once never install into the same interpreter together
_INSTALL_LOCK = threading.Lock()


def install(module: str, python: str, run: Callable = subprocess.run) -> Dict[str, Any]:
    """Install module's pinned requirement into python's environment, every package already there held at its
    version (a constraints file from `uv pip freeze`), so the install adds and never upgrades or downgrades. The
    record: requirement, command, exit_status, stdout and stderr whole; exit_status None when uv was not found or
    the freeze failed (nothing installed). Installs are serialized (_INSTALL_LOCK)."""
    with _INSTALL_LOCK:
        return _install(module, python, run)


def _install(module: str, python: str, run: Callable) -> Dict[str, Any]:
    requirement = ALLOW_LIST[module]
    rec: Dict[str, Any] = {"module": module, "requirement": requirement, "python": python, "command": None,
                           "exit_status": None, "stdout": "", "stderr": "", "held": None}
    uv = uv_binary()
    if uv is None:
        rec["stderr"] = "uv not found (UV unset, none on PATH): nothing installed"
        return rec
    freeze = run([uv, "pip", "freeze", "--python", python], capture_output=True, text=True)
    if freeze.returncode != 0:
        rec["stderr"] = f"uv pip freeze exit {freeze.returncode}: {freeze.stderr}"
        return rec
    # every installed distribution, at its version ("name==v") or its source ("name @ file://..."); an editable
    # line ("-e ...") cannot be a constraint
    held = [ln for ln in (freeze.stdout or "").splitlines()
            if ("==" in ln or " @ " in ln) and not ln.startswith(("#", "-"))]
    rec["held"] = len(held)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", prefix="d72_held_", delete=False) as f:
        f.write("\n".join(held) + "\n")
        constraints = f.name
    try:
        cmd = [uv, "pip", "install", "--python", python, "--constraint", constraints, requirement]
        rec["command"] = cmd
        p = run(cmd, capture_output=True, text=True)
        rec.update(exit_status=p.returncode, stdout=p.stdout or "", stderr=p.stderr or "")
    finally:
        os.unlink(constraints)
    return rec


def check(modules: List[str], python: str, probe: Optional[Callable[[List[str]], Dict[str, str]]] = None,
          run: Callable = subprocess.run) -> Dict[str, Dict[str, Any]]:
    """Per module its status (STATUSES) in the interpreter python, installing each missing allow-listed module
    (install). probe gives "stdlib", "present" or "missing" per module (default: probe_subprocess in python)."""
    modules = list(modules)
    if not modules:
        return {}
    states = (probe or (lambda ms: probe_subprocess(ms, python, run=run)))(modules)
    out: Dict[str, Dict[str, Any]] = {}
    for m in modules:
        state = states.get(m, "missing")
        if state in ("stdlib", "present"):
            out[m] = {"status": state}
        elif m in ALLOW_LIST:
            out[m] = {"status": "installed", "install": install(m, python, run=run)}
        else:
            out[m] = {"status": "not_allowed"}   # nothing downloaded; the code runs and fails as the model's error
    return out


def missing_module(ename: Optional[str], evalue: Optional[str]) -> Optional[str]:
    """The top-level module a ModuleNotFoundError names, else None."""
    if ename != "ModuleNotFoundError":
        return None
    m = _RE_NO_MODULE.search(evalue or "")
    return _top(m.group(1)) if m else None


def final_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The records of the executions that set the attempt's exec_outcome: those of the last kernel run (kernel_run,
    a new number at each kernel start). A script config restarts its kernel before each retry, so this is the final
    script's run; coder_v2 re-runs its notebook in a fresh kernel, so this is that re-run (or, with no re-run, the
    session kernel's cells since its last start). Records without kernel_run count as one run."""
    if not records:
        return []
    last = records[-1].get("kernel_run")
    return [r for r in records if r.get("kernel_run") == last]


def _caused_by_missing_import(errors: List[Dict[str, Any]], codes: Optional[List[str]] = None) -> bool:
    """D75 Q64: every error of the final kernel run is put down to a failed import of a not_allowed module: each is
    that ModuleNotFoundError, or a NameError for a name one of those failed imports would have bound (gp for
    "import gseapy as gp"), raised after it in the run. The names come from each record's import_bindings (recorded
    since D75) and, for records stored before it, from the attempt's code (codes: coder_v2's code_cells; their
    bindings for the failed module, whichever cell holds the import). Any other error leaves the attempt unflagged."""
    if not errors or not any(r.get("error_not_allowed_module") for r in errors):
        return False
    from_codes: Dict[str, set] = {}
    for c in codes or []:
        for m, names in import_bindings(c or "").items():
            from_codes.setdefault(m, set()).update(names)
    bound: set = set()
    for r in errors:
        m = r.get("error_not_allowed_module")
        if m:
            bound.update((r.get("import_bindings") or {}).get(m, []))
            bound.update(from_codes.get(m, set()))
            continue
        err = r.get("error") or {}
        name = _RE_NAME_ERROR.search(err.get("evalue") or "") if err.get("ename") == "NameError" else None
        if not name or name.group(1) not in bound:
            return False
    return True


def attempt_fields(records: List[Dict[str, Any]], passed: Optional[bool] = None,
                   exec_outcome: Optional[str] = None, codes: Optional[List[str]] = None) -> Dict[str, Any]:
    """The attempt's D72 fields from its per-execution records: imports (every module scanned), missing_installed
    (each install: module, requirement, exit_status), missing_not_allowed, install_lines (lines where the generated
    code runs a package install itself), and missing_library_not_allowed: True when the attempt failed (passed
    False, exec_outcome "error" or "step_failed") and every error raised by the executions that set exec_outcome
    (final_records) is a ModuleNotFoundError for a module that execution classified not_allowed (the model's
    failure, D72; exec_outcome stays as computed), or a NameError for a name such a failed import would have bound,
    raised after it (D75 Q64, _caused_by_missing_import; codes: the attempt's code, for records stored without
    import_bindings). An error fixed by a later run of the attempt does not count."""
    imports, not_allowed, installed, lines = set(), set(), [], []
    for r in records:
        imports.update(r.get("modules") or [])
        lines.extend(ln for ln in (r.get("install_lines") or []) if ln not in lines)
        for m, c in (r.get("classification") or {}).items():
            if c["status"] == "not_allowed":
                not_allowed.add(m)
            elif c["status"] == "installed":
                i = c["install"]
                installed.append({"module": m, "requirement": i["requirement"], "exit_status": i["exit_status"]})
    errors = [r for r in final_records(records) if r.get("error")]
    failed = passed is False and exec_outcome in ("error", "step_failed")
    return {
        "imports": sorted(imports),
        "missing_installed": installed,
        "missing_not_allowed": sorted(not_allowed),
        "install_lines": lines,
        "missing_library_not_allowed": failed and _caused_by_missing_import(errors, codes),
        "import_scans": records,
    }


# D75 Q63: the environment the generated code runs in must not change during an attempt. The coder benchmark takes a
# fingerprint of the installed packages (`uv pip freeze` of the kernel's interpreter) before and after every attempt
# and stops the run as a setup error when it changed (EnvironmentChanged), or when it cannot be taken
# (EnvironmentCheckError). It tests the property itself, so it also catches an install by a route nobody listed.
# Since every allow-listed library is installed (D72, settled import-scan D1), an install by the harness (check above)
# cannot happen in a fixed environment; if one did, the fingerprint changes and the run stops here as well.
class EnvironmentCheckError(RuntimeError):
    """The package fingerprint could not be taken (no uv, or `uv pip freeze` failed): a setup error."""


class EnvironmentChanged(EnvironmentCheckError):
    """The installed packages differ after an attempt from before it: a setup error that stops the run."""


def fingerprint(python: str, run: Callable = subprocess.run) -> List[str]:
    """The installed packages of python's environment, one `uv pip freeze` line each, sorted (D75 Q63)."""
    uv = uv_binary()
    if uv is None:
        raise EnvironmentCheckError("D75 Q63: uv not found (UV unset, none on PATH): no package fingerprint")
    p = run([uv, "pip", "freeze", "--python", python], capture_output=True, text=True)
    if p.returncode != 0:
        raise EnvironmentCheckError(f"D75 Q63: uv pip freeze --python {python} exit {p.returncode}: {p.stderr}")
    return sorted(ln for ln in (p.stdout or "").splitlines() if ln.strip())


def fingerprint_sha256(lines: List[str]) -> str:
    """The recorded form of a fingerprint (D75 Q63): sha256 of its sorted freeze lines, one per line."""
    return hashlib.sha256("\n".join(sorted(lines)).encode()).hexdigest()


def check_unchanged(before: List[str], after: List[str], where: str = "") -> None:
    """Raise EnvironmentChanged naming every line added and removed when after differs from before."""
    if before == after:
        return
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    raise EnvironmentChanged(f"D75 Q63: the installed packages changed during {where or 'the attempt'}: "
                             f"added {added}, removed {removed}")


# D78 Q112: the fingerprint must watch the interpreter that runs the generated code. The kernel's spec is resolved by
# jupyter_client, so a user-level 'python3' kernelspec could start another Python than the harness's; the benchmark
# therefore asks a kernel which interpreter it runs (the probe's "executable", its own sys.executable), fingerprints
# that one, and stops the run as a setup error when it differs from the harness's (KernelInterpreterMismatch). Every
# kernel the attempt probed (each scan's "python") is held to the same interpreter.
class KernelInterpreterMismatch(EnvironmentCheckError):
    """A notebook kernel runs another interpreter than the harness: a setup error that stops the run."""


def check_kernel_python(kernel_python: Optional[str], harness_python: str, where: str = "") -> None:
    """Raise KernelInterpreterMismatch unless the kernel reported exactly the harness's interpreter (D78 Q112)."""
    if kernel_python != harness_python:
        raise KernelInterpreterMismatch(f"D78 Q112: the kernel of {where or 'the benchmark'} runs {kernel_python!r}, "
                                        f"the harness {harness_python!r}")


def check_scans_python(scans: List[Dict[str, Any]], python: str, where: str = "") -> None:
    """Raise KernelInterpreterMismatch naming every other interpreter a scan's kernel reported (a scan with no probe
    answer, python None, names none) (D78 Q112)."""
    other = sorted({s["python"] for s in scans if s.get("python") not in (None, python)})
    if other:
        raise KernelInterpreterMismatch(f"D78 Q112: a kernel of {where or 'the attempt'} ran {other}, the "
                                        f"fingerprinted interpreter is {python!r}")
