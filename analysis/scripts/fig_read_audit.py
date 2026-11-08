#!/usr/bin/env python3
"""fig_read_audit - D155: record every file a figure build reads, and judge each read.

WHY. A clean clone of the repository rebuilt only 14 of the 18 plates (27 October): builds read the sibling checkout
~/projects/Mentori-paper, an untracked file and working-tree versions of committed files, and S494 compared outputs
only, so the working tree satisfied what a clean clone could not. This module makes the reads visible.

WHAT IT IS. A check against accidental reads: a figure build that reads an uncommitted file, a file outside the
repository, or a file through a program the audit cannot follow, fails, so a fresh clone rebuilds what the working
tree did. It is not a sandbox. Code written to evade it can (a C extension opening files itself, a process started
without an audit event); the audit makes such code visible only where it starts a child process, which must be on
the allow list (section 3 below).

TWO HALVES.
  1. The hook (install()). A Python audit hook (sys.addaudithook, PEP 578) that writes one line per event to
     $FIG_READ_AUDIT_DIR/<pid>.log: every file opened for reading (READ); every file opened for writing, as WRITE
     when the open creates or truncates it (all its content is then the step's own) and as UPDATE when it keeps
     content already there (r+, a, a+, os.open O_RDWR or O_WRONLY without O_TRUNC on an existing file); every
     directory listed or globbed; every temporary file or folder created through tempfile; sqlite3.connect; and every
     child process (CHILD: whether its environment keeps the hook's two variables exactly as the process started with
     them, its argv, its working folder, the program the operating system runs, and the names of the environment
     variables that differ from the process's own at its start), started through subprocess (shell=True included:
     its argv is then /bin/sh -c and the string; executable= is the program logged), os.posix_spawn, os.system
     (logged as /bin/sh -c and the string), os.exec* or os.spawn*. It changes nothing a build does. It is loaded in
     every Python process of a step through scripts/fig_read_audit_site/sitecustomize.py, which S494 puts first on
     PYTHONPATH; a child Python inherits it.
  2. The judge (judge()). S494 reads a step's logs and classifies each read path:
       allowed   the frozen tars folder (FROZEN_TARS); fig_repro's extracted folder; the interpreter's own files
                 (sys.prefix, sys.base_prefix, sys.exec_prefix and sysconfig's stdlib and site-packages, recorded by
                 each process: the standard library, site-packages, the venvs); the uv cache and uv's Python
                 installs; the repository's venvs (.venv, experiments/rlm_ref/.venv); compiled bytecode in
                 __pycache__; matplotlib's font cache (fontlist-v*.json) and the listing of its config folder; /dev;
                 a temporary file or folder the step itself made (tempfile, any process of the step), a file the step
                 itself created or truncated (WRITE, not UPDATE: an r+ or O_RDWR open reads what was there before),
                 outside the repository or, in a --write run, inside it; and the run's --out and log folders. In the
                 frozen tars folder only the tars SHA256SUMS names are allowed (and the listing of the folder), not
                 anything else kept beside them (an extracted copy, say).
       platform  files of the operating system a build reads and the repository cannot hold (PLATFORM below: the
                 system Helvetica, which FIGURE_LOCK [type] font_families names, the time zone database, the MIME
                 table, the macOS version file). Allowed, and listed by S494 so the dependence stays visible.
       violation anything else outside the repository (the sibling checkout, a home folder file, a scratch folder),
                 and inside the repository a file that git HEAD does not hold (untracked or gitignored) or that
                 differs from HEAD in the working tree (git diff --name-only HEAD, computed by S494 before each step,
                 so a file changed during the run fails every later read of it). Also a violation: a write (WRITE or
                 UPDATE) into the repository during an --out run, outside __pycache__, the venvs and fig_repro's
                 extracted folder; and every child process not on the allow list (judge_child(), section 3 below;
                 audit 27 Oct F3): a child is accepted only when it runs in the environment its parent process
                 started with (no variable added, removed or changed but the six of CHILD_ENV_MAY_CHANGE, which
                 change no read: PYTHONHASHSEED, three Hugging Face and tqdm switches and two OpenMP
                 switches) and is a Python of the repository's venvs (or
                 uv run --frozen python, inside the repository) without -I, -E or -S, so it loads the hook and its
                 own reads are judged; git with a read-only subcommand and option from GIT_READ (or one of
                 GIT_IN_MADE_FOLDER, which writes, in a folder the step made); or a shell string pinned by sha256 in
                 REVIEWED_SHELL, run in a folder the step made. Any other program (cat, tar, env, nice, time), any
                 wrapper word in front of an allowed one, any shell string not pinned (os.system and shell=True
                 included, whatever it holds), any other git subcommand or option, and any changed environment fail
                 the step as unaudited, whatever the arguments. An accepted child's path arguments are judged as
                 reads (an absolute one, or a relative one from its working folder or git's -C folder, that names an
                 existing file or folder; a repository folder as a listing). git show or git cat-file
                 <rev>:<path> run inside the repository is a read of <path> (audit 27 Oct F1b): a repository read,
                 so the step is blocked when the step that owns <path> fails, and a violation when the revision is
                 HEAD and an earlier step of this run rewrote <path> (the step then read the version before the
                 rewrite). It is accepted only when rev resolves (git rev-parse --verify <rev>^{commit}) to HEAD's
                 commit or an ancestor of it (git merge-base --is-ancestor; audit 27 Oct R4, R5): an empty rev (the
                 index, ':<path>' or ':<n>:<path>'), a stash, a commit HEAD does not reach and a rev that does not
                 resolve are violations, content not committed on main. In a --write run, a read of a repository file that an earlier step of the same run
                 rewrote (Context.changed) is that step's output and a repository read, not a violation.
     A directory listing (os.listdir, os.scandir, glob) is judged the same way outside the repository; inside it a
     listing is not a violation, since every file it leads to is judged when opened.

LIMITS. Only Python reads raise audit events. A reader in C or Rust that opens files itself (none of the figure
scripts uses one: no polars, pyarrow or duckdb reader, 27 October) is not seen; nor is a child started by C code
without an audit event (os.fork followed by a C exec, multiprocessing's spawn, whose Python children inherit the
hook's variables and so are audited themselves). What an allowed non-Python child reads is not seen: for git only
its path arguments and <rev>:<path> are judged, not its object store or its own configuration (~/.gitconfig, the
repository's .git/config); for a reviewed shell string, what it was read to do. uv run reads the repository's
pyproject.toml and uv.lock itself. A repository folder given to a child is judged as a listing, not file by file. A
Python child's interpreter prefix is allowed as the interpreter's own files, which is why only the repository's
venvs (and the judging interpreter's folder) are accepted. git show or cat-file given a bare object name (a blob's
hash, no <rev>:<path>) is not judged as a read of any file.
Known evasions, not caught: the audit guards against accidental reads, not code written to evade it, and these need
such code: an environment changed below os.environ (os.unsetenv, os.putenv, or a subprocess preexec_fn), which the
hook does not see, so a child may run without the hook's variables and be logged as audited; git run in a folder the
step made whose .git file or link points to another repository (git then reads that repository, judged as the
step's own folder); a git hook planted in a repository the step made, which git init, add or commit then runs
without an audit event; and files opened through ctypes or other C code.
"""
from __future__ import annotations

import ast
import hashlib
import os
import re
import shutil
import sys

ENV = "FIG_READ_AUDIT_DIR"
SITE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fig_read_audit_site")

# Operating-system files a build may read that no repository can hold. Each is allowed and listed (S494 prints them).
PLATFORM = {
    "/System/Library/Fonts/": "macOS system fonts: Helvetica.ttc, the face FIGURE_LOCK [type] font_families names",
    "/Library/Fonts/": "macOS fonts installed for all users (matplotlib's font search)",
    "/usr/share/fonts/": "Linux system fonts (matplotlib's font search)",
    "/usr/share/zoneinfo/": "the time zone database (zoneinfo, Europe/Amsterdam stamps)",
    "/private/var/db/timezone/": "macOS time zone database (zoneinfo through /etc/localtime)",
    "/etc/localtime": "the machine's time zone",
    "/System/Library/CoreServices/SystemVersion.plist": "macOS version (platform.mac_ver)",
    "/etc/mime.types": "MIME table read by mimetypes.init()",
    "/etc/apache2/mime.types": "MIME table read by mimetypes.init() (macOS)",
    "/etc/httpd/mime.types": "MIME table read by mimetypes.init()",
    "/etc/httpd/conf/mime.types": "MIME table read by mimetypes.init()",
    "/etc/apache/mime.types": "MIME table read by mimetypes.init()",
    "/etc/apache2/conf/mime.types": "MIME table read by mimetypes.init()",
    "/usr/local/etc/httpd/conf/mime.types": "MIME table read by mimetypes.init()",
    "/usr/local/lib/netscape/mime.types": "MIME table read by mimetypes.init()",
    "/usr/local/etc/mime.types": "MIME table read by mimetypes.init()",
}


# ---------------------------------------------------------------------------------------------------------------
# 1. The hook
# ---------------------------------------------------------------------------------------------------------------
def install() -> bool:
    """Add the audit hook when FIG_READ_AUDIT_DIR is set. Returns whether it was added."""
    d = os.environ.get(ENV)
    if not d or getattr(sys, "_fig_read_audit_on", False):
        return False
    sys._fig_read_audit_on = True
    import shutil
    env0 = dict(os.environ)                            # this process's environment at its start
    state = {"fd": None, "busy": False, "seen": set()}

    def w(line: str) -> None:
        if line in state["seen"]:
            return
        state["seen"].add(line)
        if state["fd"] is None:
            os.makedirs(d, exist_ok=True)
            state["fd"] = os.open(os.path.join(d, f"{os.getpid()}.log"), os.O_WRONLY | os.O_CREAT | os.O_APPEND,
                                  0o644)
            import sysconfig
            paths = sysconfig.get_paths()
            pre = [sys.prefix, sys.base_prefix, sys.exec_prefix, sys.base_exec_prefix,
                   *(paths.get(k, "") for k in ("stdlib", "platstdlib", "purelib", "platlib"))]
            head = "ARGV\t" + repr(sys.argv) + "\n" + "".join(f"PREFIX\t{p}\n" for p in dict.fromkeys(pre) if p)
            os.write(state["fd"], head.encode("utf-8", "replace"))
        os.write(state["fd"], (line + "\n").encode("utf-8", "replace"))

    def path_of(p):
        if p is None or isinstance(p, int):
            return None
        return os.path.abspath(os.fsdecode(p))

    def hook(ev, args):
        if state["busy"]:
            return
        state["busy"] = True
        try:
            if ev == "open":
                p = path_of(args[0])
                if p is None:
                    return
                mode, flags = args[1], args[2] if len(args) > 2 else 0
                existed = os.path.exists(p)            # the event is raised before the open
                if isinstance(mode, str):
                    reads = "r" in mode or ("+" in mode and "w" not in mode and "x" not in mode)
                    writes = any(c in mode for c in "wax+")
                    fresh = "w" in mode or "x" in mode or not existed      # all the content is the step's own
                else:                                  # os.open: flags only
                    # The event carries no dir_fd: shutil.rmtree opens each entry relative to its parent's fd, which
                    # abspath would place under the cwd. A directory open reads no file content, and a relative name
                    # that does not exist at the cwd was opened relative to a dir_fd; neither is logged.
                    if os.path.isdir(p) or (not os.path.isabs(os.fsdecode(args[0])) and not os.path.exists(p)):
                        return
                    acc = (flags or 0) & os.O_ACCMODE
                    reads = acc in (os.O_RDONLY, os.O_RDWR) and not ((flags or 0) & os.O_TRUNC)
                    writes = acc in (os.O_WRONLY, os.O_RDWR) or bool((flags or 0) & os.O_CREAT)
                    fresh = bool((flags or 0) & os.O_TRUNC) or not existed
                if writes:
                    w(f"{'WRITE' if fresh else 'UPDATE'}\t{p}")
                if reads:
                    w(f"READ\t{p}")
            elif ev in ("os.listdir", "os.scandir"):
                p = path_of(args[0]) if args[0] is not None else os.getcwd()
                if p is not None:
                    w(f"LIST\t{p}")
            elif ev == "glob.glob":
                w(f"LIST\t{os.path.abspath(os.fsdecode(args[0]))}")
            elif ev in ("tempfile.mkdtemp", "tempfile.mkstemp"):
                w(f"TEMP\t{os.path.abspath(os.fsdecode(args[0]))}")
            elif ev == "sqlite3.connect":
                p = path_of(args[0])
                if p and not str(args[0]).startswith(":memory:"):
                    w(f"READ\t{p}")
            elif ev in ("subprocess.Popen", "os.posix_spawn", "os.system", "os.exec", "os.spawn"):
                if ev == "subprocess.Popen":           # (executable, args, cwd, env); shell=True arrives as
                    prog, argv, cwd, env = args       # [/bin/sh, -c, the string], executable= as executable
                elif ev == "os.system":                # the C library runs the string with /bin/sh -c
                    prog, argv, cwd, env = "/bin/sh", ["/bin/sh", "-c", os.fsdecode(args[0])], None, None
                elif ev == "os.spawn":                 # (mode, path, args, env)
                    prog, argv, cwd, env = args[1], args[2], None, args[3]
                else:                                  # os.posix_spawn and os.exec: (path, args, env)
                    prog, argv, cwd, env = args[0], args[1], None, args[2]
                e = {os.fsdecode(k): os.fsdecode(v) for k, v in (env.items() if env is not None
                                                                 else os.environ.items())}
                # audited: the child keeps the hook's two variables exactly as this process started with them
                kept = e.get(ENV) == d and e.get("PYTHONPATH") == env0.get("PYTHONPATH")
                # every variable whose value differs from this process's environment at its start (added, removed,
                # changed), whether by an env= mapping or by this process editing os.environ before the start
                changed = sorted(k for k in set(e) | set(env0) if e.get(k) != env0.get(k))
                if isinstance(argv, (list, tuple)):        # plain strings, so the judge can parse the line back
                    argv = [os.fsdecode(a) if isinstance(a, (str, bytes, os.PathLike)) else str(a) for a in argv]
                cwd = os.path.abspath(os.fsdecode(cwd)) if cwd is not None else os.getcwd()
                # the program the operating system runs: a name with a folder is taken from the child's working
                # folder, a bare name is found on the child's PATH, as subprocess and os.exec*p find it
                prog = os.fsdecode(prog) if prog is not None else (argv[0] if argv else "")
                if os.sep in prog:
                    prog = os.path.abspath(os.path.join(cwd, prog))
                else:
                    prog = shutil.which(prog, path=e.get("PATH", os.defpath)) or prog
                w(f"CHILD\t{'audited' if kept else 'unaudited'}\t{argv!r}\t{cwd}\t{prog}\t{','.join(changed)}")
        except Exception:                              # an observer: never break the build
            pass
        finally:
            state["busy"] = False

    sys.addaudithook(hook)
    return True


def env_for(base_env: dict, audit_dir) -> dict:
    """base_env with the hook switched on for every Python process started from it."""
    e = dict(base_env)
    e[ENV] = str(audit_dir)
    e["PYTHONPATH"] = SITE_DIR + (os.pathsep + e["PYTHONPATH"] if e.get("PYTHONPATH") else "")
    return e


# ---------------------------------------------------------------------------------------------------------------
# 2. The judge
# ---------------------------------------------------------------------------------------------------------------
def _real(p: str) -> str:
    return os.path.realpath(p)


def _under(p: str, prefix: str) -> bool:
    prefix = prefix.rstrip("/")
    return p == prefix or p.startswith(prefix + "/")


def new_events() -> dict:
    """An empty event record: argv list, prefixes, reads, writes (created or truncated), updates (written, earlier
    content kept), lists, temps, children."""
    return {"argv": [], "prefix": set(), "read": set(), "write": set(), "update": set(), "list": set(), "temp": set(),
            "child": []}


def read_logs(audit_dir) -> dict:
    """Every event of every process logged in audit_dir: argv list, prefixes, reads, writes, lists, temps, children."""
    ev = new_events()
    if not audit_dir or not os.path.isdir(audit_dir):
        return ev
    for name in sorted(os.listdir(audit_dir)):
        if not name.endswith(".log"):
            continue
        with open(os.path.join(audit_dir, name), encoding="utf-8", errors="replace") as fh:
            for line in fh:
                kind, _, rest = line.rstrip("\n").partition("\t")
                if kind == "ARGV":
                    ev["argv"].append(rest)
                elif kind == "PREFIX":
                    ev["prefix"].add(rest)
                elif kind == "READ":
                    ev["read"].add(rest)
                elif kind == "WRITE":
                    ev["write"].add(rest)
                elif kind == "UPDATE":
                    ev["update"].add(rest)
                elif kind == "LIST":
                    ev["list"].add(rest)
                elif kind == "TEMP":
                    ev["temp"].add(rest)
                elif kind == "CHILD":
                    ev["child"].append(rest)
    return ev


class Context:
    """What a run allows: computed once per S494 run (git state, the tars folder, uv's folders)."""

    def __init__(self, root, tars, head_files: set[str], dirty: set[str], extra_allowed=(), uv_dirs=(),
                 tar_names=None, write_run: bool = False, changed=()):
        self.root = _real(str(root))
        self.head_files = set(head_files)
        self.dirty = set(dirty)
        # the repository files that came to differ from HEAD during this run, before the step (an earlier step's
        # output in a --write run): a read of one at HEAD (git show HEAD:<path>) is a read of the version before
        # the rewrite; in a --write run a read of the working tree's is a read of the earlier step's output
        self.changed = set(changed)
        self.tars = _real(str(tars))
        if tar_names is None:                          # the tars SHA256SUMS names (frozen_inputs/SHA256SUMS)
            sums = os.path.join(str(root), "findings", "recompute", "frozen_inputs", "SHA256SUMS")
            tar_names = []
            if os.path.isfile(sums):
                with open(sums, encoding="utf-8") as fh:
                    tar_names = [ln.split("  ", 1)[1].strip() for ln in fh if ln.strip().endswith(".tar")]
        self.tar_files = sorted({_real(os.path.join(str(tars), n)) for n in tar_names})
        self.write_run = bool(write_run)               # --write: a step writes its outputs into the repository
        self.extracted = _real(os.path.join(str(root), "findings", "recompute", "frozen_inputs", "extracted"))
        self.venvs = [_real(os.path.join(str(root), v)) for v in (".venv", "experiments/rlm_ref/.venv")]
        home = os.path.expanduser("~")
        mpl = [os.environ.get("MPLCONFIGDIR") or "", os.path.join(home, ".matplotlib"),
               os.path.join(home, ".config", "matplotlib"), os.path.join(home, ".cache", "matplotlib")]
        self.mpl = [_real(m) for m in mpl if m]
        uv = [os.environ.get("UV_CACHE_DIR") or "", os.environ.get("UV_PYTHON_INSTALL_DIR") or "",
              os.path.join(home, ".cache", "uv"), os.path.join(home, ".local", "share", "uv"), *uv_dirs]
        self.uv = [_real(u) for u in uv if u]
        self.extra = [_real(str(x)) for x in extra_allowed if x]
        self._revs: dict[str, tuple[str | None, str]] = {}   # committed(): rev -> (commit or None, why)
        self._head: str | None = None

    def _git(self, *args: str):
        """git in the repository judged, with no GIT_* variable of this process (none may point it elsewhere)."""
        import subprocess                              # here, not at the top: the hook loads this module everywhere
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        return subprocess.run(["git", "-C", self.root, *args], capture_output=True, text=True, env=env)

    def committed(self, rev: str) -> tuple[str | None, str]:
        """(commit, "") when rev names HEAD's commit or an ancestor of it, so <rev>:<path> reads committed content on
        the branch the run judges; (None, why) otherwise: an empty rev (the index, the staged copy: ':a.txt',
        ':0:a.txt'), a rev that does not resolve to a commit, or a commit HEAD does not reach (a stash, another
        branch). HEAD is resolved once, at the first call, and every answer is kept for the run."""
        if rev in self._revs:
            return self._revs[rev]
        if not rev:
            res = (None, "an empty revision names the index (the staged copy)")
        else:
            if self._head is None:
                r = self._git("rev-parse", "--verify", "--quiet", "HEAD^{commit}")
                self._head = r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else ""
            r = self._git("rev-parse", "--verify", "--quiet", rev + "^{commit}")
            c = r.stdout.strip() if r.returncode == 0 else ""
            if not self._head:
                res = (None, "the repository has no HEAD commit")
            elif not c:
                res = (None, f"{rev} does not resolve to a commit")
            elif c == self._head or self._git("merge-base", "--is-ancestor", c, self._head).returncode == 0:
                res = (c, "")
            else:
                res = (None, f"{rev} ({c[:8]}) is neither HEAD nor an ancestor of it")
        self._revs[rev] = res
        return res

    def is_head(self, rev: str) -> bool:
        """rev resolves to HEAD's commit (committed() called first)."""
        c, _ = self.committed(rev)
        return c is not None and c == self._head

    def allowed_prefixes(self) -> list[tuple[str, str]]:
        """The fixed allowed prefixes, named (the run's own and each process's interpreter prefixes come on top)."""
        rows = [*((t, "a frozen tar named in SHA256SUMS (FROZEN_TARS)") for t in self.tar_files),
                (self.extracted, "fig_repro's extracted folder"),
                *((v, "a repository venv") for v in self.venvs),
                *((u, "uv's cache or Python installs") for u in self.uv),
                ("/dev", "devices"),
                *((x, "this run's --out or log folder") for x in self.extra)]
        return rows


def judge(ev: dict, ctx: Context) -> dict:
    """Classify a step's reads. Returns {"violations": [(path, why)], "platform": [path], "repo_reads": [rel]}."""
    interp = [_real(p) for p in ev["prefix"]]
    made = [_real(t) for t in ev["temp"]]
    wrote = {_real(p) for p in ev["write"]}            # created or truncated by the step: its own content
    fixed = [p for p, _ in ctx.allowed_prefixes()]
    out = {"violations": [], "platform": [], "repo_reads": []}

    def outside_ok(p: str, listing: bool) -> str | None:
        """'ok', 'platform' or None (a violation) for a path outside the repository (or a repo venv/extracted)."""
        if any(_under(p, a) for a in fixed) or any(_under(p, a) for a in interp):
            return "ok"
        if listing and p == ctx.tars:                  # the tars folder itself may be listed, not what is in it
            return "ok"
        if any(_under(p, t) for t in made):
            return "ok"
        if p in wrote and (ctx.write_run or not _under(p, ctx.root)):
            return "ok"
        for m in ctx.mpl:
            if listing and _under(p, m):
                return "ok"
            if _under(p, m) and os.path.dirname(p) == m and os.path.basename(p).startswith("fontlist-v") \
                    and p.endswith(".json"):
                return "ok"
        for k in PLATFORM:
            if (k.endswith("/") and _under(p, k)) or p == k:
                return "platform"
            rk = _real(k.rstrip("/"))
            if (k.endswith("/") and _under(p, rk)) or p == rk:
                return "platform"
        return None

    def read(p: str, via: str = "") -> None:
        """Judge one read of p (a real path); via names the child process it was given to, if any."""
        verdict = outside_ok(p, False)
        if verdict == "ok":
            return
        if verdict == "platform":
            out["platform"].append(p)
            return
        if _under(p, ctx.root):
            rel = os.path.relpath(p, ctx.root)
            parts = rel.split(os.sep)
            if "__pycache__" in parts and rel.endswith(".pyc"):
                # a fresh .pyc is read instead of its .py: judge the source it was compiled from
                rel = os.sep.join(parts[:parts.index("__pycache__")] + [parts[-1].split(".")[0] + ".py"])
                if rel in out["repo_reads"] or any(v[0] == rel for v in out["violations"]):
                    return
            if rel not in ctx.head_files:
                out["violations"].append((rel, via + "not in git HEAD (untracked or gitignored)"))
            elif rel in ctx.dirty and not (ctx.write_run and rel in ctx.changed):
                out["violations"].append((rel, via + "differs from git HEAD in the working tree"))
            elif rel not in out["repo_reads"]:
                out["repo_reads"].append(rel)
            return
        out["violations"].append((p, via + "outside the repository and the allowed folders"))

    def step_folder(p: str) -> bool:
        """p is in a folder the step itself made (tempfile) or in this run's --out or log folder."""
        return any(_under(p, t) for t in made) or any(_under(p, x) for x in ctx.extra)

    for raw in sorted(ev["read"]):
        read(_real(raw))
    if not ctx.write_run:                              # an --out run writes nothing into the repository
        for raw in sorted(ev["write"] | ev.get("update", set())):
            p = _real(raw)
            if not _under(p, ctx.root) or "__pycache__" in p.split(os.sep) \
                    or any(_under(p, a) for a in [ctx.extracted, *ctx.venvs]):
                continue
            out["violations"].append((os.path.relpath(p, ctx.root), "written into the repository during an --out "
                                                                     "run (only --write writes there)"))
    for raw in sorted(ev["list"]):
        p = _real(raw.split("*")[0].split("?")[0].split("[")[0].rstrip("/") or "/")
        if _under(p, ctx.root):
            continue
        verdict = outside_ok(p, True)
        if verdict is None:
            out["violations"].append((raw, "listed or globbed outside the repository and the allowed folders"))
    for c in ev["child"]:
        # state, argv, cwd, program, changed variables; a hand-made line may stop after argv or cwd
        state, argv, cwd, prog, changed = (c.split("\t") + ["", "", "", "", ""])[:5]
        try:
            args = ast.literal_eval(argv)
        except (ValueError, SyntaxError):
            args = None
        args = [os.fsdecode(x) if isinstance(x, (bytes, os.PathLike)) else x
                for x in (args if isinstance(args, (list, tuple)) else [])]
        envdiff = [n for n in changed.split(",") if n] if c.count("\t") >= 4 else None
        judge_child(args, state == "unaudited", cwd or None, argv, ctx, read, outside_ok, out,
                    program=prog or None, envdiff=envdiff, step_folder=step_folder)
    out["violations"] = list(dict.fromkeys(out["violations"]))   # the same event from two processes is one line
    return out


# ---------------------------------------------------------------------------------------------------------------
# 3. Child processes: an allow list (audit 27 Oct F3, second pass)
# ---------------------------------------------------------------------------------------------------------------
# A child process is accepted only when it is one of the three kinds below, and only in the environment its parent
# process started with: no variable added, removed or changed, except the six of CHILD_ENV_MAY_CHANGE. Every other child fails the step as unaudited, whatever its arguments:
# another program (cat, tar, env, nice, time, a shell), a wrapper word in front of an allowed program, a shell string
# not pinned in REVIEWED_SHELL, a git subcommand or option not listed here. The program judged is the one the
# operating system runs (the hook logs it: subprocess's executable=, os.exec*'s path, a bare name found on PATH), not
# the first word of argv.
#   a. Python: python, python3 or python3.N from a repository venv (.venv, experiments/rlm_ref/.venv) or from the
#      folder of the interpreter that judges (S494's), or "uv run [--frozen] python ..." started inside the
#      repository; never with -I, -E or -S. It loads the hook itself, so its own reads are judged.
#   b. git, the system's: global options --no-optional-locks, -C <folder> and -c user.name=... or -c user.email=...
#      only, then a subcommand of GIT_READ with only the options listed for it, run in the repository or in a folder
#      the step made (or this run's --out); or a subcommand of GIT_IN_MADE_FOLDER, which writes, only in a folder the
#      step made. Every other word is judged as a path read from git's folder, and <rev>:<path> of show or cat-file
#      as a read of <path>.
#   c. a shell (sh or bash, the system's) given exactly -c and a string whose sha256 is in REVIEWED_SHELL, run in a
#      folder the step made or this run's --out.
# The lists below are what the 18 plates' builds start: a census of every CHILD line of S494 on fresh clones of main
# (27 October; 39218050, then fc200091 with the program and changed variables logged), 175 child processes: Python 13
# (5 .venv/bin/python3, 8 uv run --frozen python), git 157 (/usr/bin/git), bash -c with S472's HEAD_SH 5 (/bin/bash).
# The variables a build changes for a child, none of which changes which files a process reads or whether the hook
# loads: PYTHONHASHSEED, set to 0 when S457, S459, S461, S463 and draw_B.py start themselves again (5 children), and
# HF_HUB_OFFLINE, TOKENIZERS_PARALLELISM and TQDM_DISABLE, set with os.environ.setdefault when S463, S476, S484 and
# S485 import the scorer modules (S19, S141), so the git children they start afterwards inherit them (10 children).
# D201 Q9 O1 (Valerio, 2 November 2026): KMP_DUPLICATE_LIB_OK and KMP_INIT_AT_FORK. A diff of os.environ around
# `import S505_question_aware_matcher` names exactly these two; they appear at `import nltk` (concept_match_stem.py:116),
# which imports scikit-learn, whose __init__.py sets both with os.environ.setdefault (sklearn/__init__.py:56, :60). They
# are read by the OpenMP runtime of a process that loads it, to allow a second copy of the library and to skip its
# at-fork handler; neither changes which files a process reads or whether the hook loads, and the git children that
# inherit them load no OpenMP at all. S471 and S474 keep importing d181_concept_recall lazily; that repair stays.
CHILD_ENV_MAY_CHANGE: frozenset[str] = frozenset({"PYTHONHASHSEED", "HF_HUB_OFFLINE", "TOKENIZERS_PARALLELISM",
                                                  "TQDM_DISABLE", "KMP_DUPLICATE_LIB_OK", "KMP_INIT_AT_FORK"})
SHELLS = {"sh", "bash"}
PYTHON_NAME = re.compile(r"python(?:3(?:\.\d+)?)?")
SYSTEM_BIN = ("/bin", "/usr/bin", "/usr/local/bin", "/opt/homebrew/bin", "/Library/Developer/CommandLineTools/usr/bin")
UV_RUN_FLAGS = {"--frozen"}
GIT_GLOBAL_FLAGS = {"--no-optional-locks"}
GIT_CONFIG_OK = ("user.name=", "user.email=")
# git subcommands that only read, each with the options it may carry: "--x=" any value, "-<n>" a count, "--" always.
GIT_READ = {
    "cat-file": set(),                             # cat-file blob <rev>:<path>
    "show": set(),                                 # show <rev>:<path>
    "log": {"-<n>", "--format="},                  # log -1 --format=%s <rev>; log --format=%H -- <path>
    "ls-files": {"-s"},                            # ls-files [-s] -- <path>
    "status": {"--porcelain", "--untracked-files=no"},
    "rev-parse": {"--is-inside-work-tree"},        # rev-parse HEAD
    "merge-base": {"--is-ancestor"},
    "hash-object": set(),                          # hash-object -- <path> (no -w, so nothing is written)
}
# git subcommands that write, accepted only in a folder the step itself made: S472's selftest of its git readers
# builds a repository there (git init -q; git add plan.csv; git -c user.name=t -c user.email=t@t commit -qm c1).
GIT_IN_MADE_FOLDER = {
    "init": {"-q"},
    "add": set(),
    "commit": {"-q", "-a", "-m", "-qm", "-am", "-qam"},
}
# Shell strings that cannot be judged word by word but were read and found to read nothing outside their working
# folder, each pinned by the sha256 of its exact text (a change to the text fails the step again until re-read). Each
# is accepted only when it runs in a folder the step itself made (tempfile) or this run's --out, never in the
# repository or elsewhere.
REVIEWED_SHELL = {
    "99bcdc7e5f6475fa88d3ef557aa48d25ea4d072134d4ee280ce3f4179f31cd8b":
        "S472 selftest_d155: HEAD_SH + 'head_of' on .git layouts it built in its own temporary folder; reads .git, "
        ".git/HEAD, a ref, commondir and packed-refs under its working folder only (27 Oct, audit F3)",
}


def _program(program: str | None, args: list) -> str:
    """The program a child runs: the hook's logged path, or (a hand-made line) argv[0] found on this process's PATH."""
    p = program or (args[0] if args else "")
    if p and os.sep not in p:
        p = shutil.which(p) or p
    return p


def _folder_real(p: str) -> str:
    """p with its folders resolved and its own name kept (a venv's python is a link to uv's interpreter)."""
    return os.path.join(_real(os.path.dirname(p)), os.path.basename(p))


def system_program(p: str, name: str) -> bool:
    """p is the system's program called name: in a system folder (SYSTEM_BIN), or the one PATH gives this process."""
    if os.path.basename(p) != name or os.sep not in p:
        return False
    found = shutil.which(name)
    return os.path.dirname(_folder_real(p)) in SYSTEM_BIN or bool(found and _real(found) == _real(p))


def python_program(p: str, ctx: "Context") -> bool:
    """p is a python of a repository venv or of the judging interpreter's own folder (S494's venv)."""
    if os.sep not in p or not PYTHON_NAME.fullmatch(os.path.basename(p)):
        return False
    bins = [os.path.join(v, "bin") for v in ctx.venvs] + [_real(os.path.dirname(os.path.abspath(sys.executable)))]
    return os.path.dirname(_folder_real(p)) in bins


def _git_option_ok(a: str, allowed: set) -> bool:
    return a in allowed or ("-<n>" in allowed and re.fullmatch(r"-\d+", a) is not None) \
        or any(x.endswith("=") and a.startswith(x) for x in allowed)


def git_rev_paths(args: list, base: str | None, root: str) -> list[tuple[str, str]]:
    """(revision, repository-relative path) for every <rev>:<path> argument of git show or git cat-file (git's
    object syntax: the path from the repository's top, or from the working folder when it starts ./ or ../). Only
    when the command runs inside the repository judged (its working folder, or git -C, under root). An empty
    revision (':a.txt', ':0:a.txt', the index) is returned as "", so the caller can refuse it."""
    if not args or not isinstance(args[0], str) or os.path.basename(args[0]) != "git":
        return []
    i = 1
    while i < len(args) and isinstance(args[i], str) and args[i].startswith("-"):
        i += 2 if args[i] in ("-C", "-c", "--git-dir", "--work-tree", "--namespace") else 1
    if i >= len(args) or args[i] not in ("show", "cat-file"):
        return []
    if base is None or not _under(_real(base), root):
        return []
    out = []
    for x in args[i + 1:]:
        if not isinstance(x, str) or x.startswith("-") or ":" not in x:
            continue
        rev, path = x.split(":", 1)
        if not path:                                   # <rev>: is the top tree, a listing; an empty rev is kept
            continue                                   # (the index), for judge_child to refuse
        if not rev and re.fullmatch(r"[0-3]:.+", path):
            path = path[2:]                            # :<n>:<path>, the index at merge stage n
        full = os.path.join(base, path) if path.startswith(("./", "../")) else os.path.join(root, path)
        rel = os.path.relpath(os.path.normpath(full), root)
        if not rel.startswith(".."):
            out.append((rev, rel))
    return out


def judge_child(args: list, unaudited: bool, cwd: str | None, raw: str, ctx: "Context", read, outside_ok,
                out: dict, program: str | None = None, envdiff: list | None = None, step_folder=None) -> None:
    """Judge one child process against the allow list (section 3 above; audit 27 Oct F2, F3, F1b): its argv, working
    folder, program and changed environment variables as the hook logged them. A child that is not on the list fails
    the step as unaudited. An accepted child's path arguments are judged as reads; git show / cat-file <rev>:<path>
    as a read of <path> at that revision (a repository read, for the blocked rule)."""
    def refuse(why: str) -> None:
        out["violations"].append((raw[:160], "unaudited child process: " + why))

    if step_folder is None:                            # a folder the step made, or this run's --out or logs
        def step_folder(p: str) -> bool:
            return not _under(p, ctx.root) and outside_ok(p, True) == "ok"
    if not args or not all(isinstance(a, str) for a in args):
        refuse("a command line the audit cannot read")
        return
    bad_env = sorted(set(envdiff or ()) - CHILD_ENV_MAY_CHANGE)
    if bad_env:
        refuse(f"its environment differs from the one its parent process started with ({', '.join(bad_env)}); "
               f"only {', '.join(sorted(CHILD_ENV_MAY_CHANGE))} may change")
        return
    if unaudited:
        refuse("its environment drops or changes FIG_READ_AUDIT_DIR or PYTHONPATH, the hook's variables")
        return
    prog = _program(program, args)
    name = os.path.basename(prog)
    here = _real(cwd) if cwd else None
    via = f"given to a child process ({raw[:80]}): "

    def paths(words: list, base: str | None) -> None:
        """Every word that names an existing file or folder (absolute, or relative to base) is judged as a read."""
        for x in words:
            if not x or x.startswith("-") and not x.startswith("/"):
                continue
            if not x.startswith("/") and base is None:
                continue
            p = _real(x if x.startswith("/") else os.path.join(base, x))
            if not os.path.exists(p):
                continue                               # not a path (a git revision, a script text, a flag value)
            if os.path.isdir(p):
                if not _under(p, ctx.root) and outside_ok(p, True) is None:
                    out["violations"].append((x, via + "outside the repository and the allowed folders"))
            else:
                read(p, via)

    if PYTHON_NAME.fullmatch(name):                    # a. Python
        if not python_program(prog, ctx):
            refuse(f"a Python interpreter outside the repository's venvs ({prog})")
            return
        flags = python_isolating_flags([name, *args[1:]])
        if flags:
            refuse(f"a Python child started with {' '.join(flags)}, which ignores PYTHONPATH or sitecustomize")
            return
        paths(args[1:], here)
        return
    if name == "uv":                                   # a. uv run [--frozen] python ...
        if not system_program(prog, "uv"):
            refuse(f"a uv that is not the one on PATH ({prog})")
            return
        if len(args) < 2 or args[1] != "run":
            refuse(f"uv {args[1] if len(args) > 1 else ''} (only 'uv run' is on the allow list)")
            return
        i = 2
        while i < len(args) and args[i].startswith("-"):
            if args[i] not in UV_RUN_FLAGS:
                refuse(f"uv run option {args[i]} is not on the allow list ({', '.join(sorted(UV_RUN_FLAGS))})")
                return
            i += 1
        if i >= len(args) or not PYTHON_NAME.fullmatch(args[i]):
            refuse("uv run of a program other than python")
            return
        if here is None or not _under(here, ctx.root):
            refuse("uv run started outside the repository (uv takes its project from the working folder)")
            return
        flags = python_isolating_flags(args[i:])
        if flags:
            refuse(f"a Python child started with {' '.join(flags)}, which ignores PYTHONPATH or sitecustomize")
            return
        paths(args[i + 1:], here)
        return
    if name == "git":                                  # b. git
        if not system_program(prog, "git"):
            refuse(f"a git that is not the system's ({prog})")
            return
        base, i = here, 1
        while i < len(args) and args[i].startswith("-"):
            a = args[i]
            if a in GIT_GLOBAL_FLAGS:
                i += 1
            elif a == "-C" and i + 1 < len(args):
                c = args[i + 1]
                base = _real(c) if os.path.isabs(c) else (_real(os.path.join(base, c)) if base else None)
                i += 2
            elif a == "-c" and i + 1 < len(args) and args[i + 1].startswith(GIT_CONFIG_OK):
                i += 2
            else:
                refuse(f"git option {a}{' ' + args[i + 1] if a == '-c' and i + 1 < len(args) else ''} is not on the "
                       f"allow list")
                return
        sub = args[i] if i < len(args) else ""
        writes = sub in GIT_IN_MADE_FOLDER
        allowed = GIT_IN_MADE_FOLDER[sub] if writes else GIT_READ.get(sub)
        if allowed is None:
            refuse(f"git {sub or '(no subcommand)'} is not on the allow list (reads: {', '.join(GIT_READ)}; in a "
                   f"folder the step made: {', '.join(GIT_IN_MADE_FOLDER)})")
            return
        if base is None:
            refuse(f"git {sub} with no recorded working folder")
            return
        in_repo = _under(base, ctx.root)
        if writes and (in_repo or not step_folder(base)):
            refuse(f"git {sub} writes, and is accepted only in a folder the step made (here {base})")
            return
        if not in_repo and not step_folder(base):
            refuse(f"git {sub} run in {base}, outside the repository and the folders the step made")
            return
        words, dashdash = [], False
        for a in args[i + 1:]:
            if not dashdash and a.startswith("-") and a != "-":
                if a == "--":
                    dashdash = True
                elif not _git_option_ok(a, allowed):
                    refuse(f"git {sub} option {a} is not on the allow list")
                    return
                continue
            words.append(a)
        # git show / cat-file <rev>:<path> (F1b): a read of <path>, so the step is blocked when the step that owns
        # <path> fails; at HEAD, a path this run rewrote before the step was read as it stood before the rewrite.
        # Only a rev that resolves to HEAD's commit or an ancestor of it reads committed content (audit 27 Oct, R4
        # and R5): the index (':a.txt'), a stash, another branch's commit or a rev that does not resolve fails.
        for rev, rel in git_rev_paths(["git", sub, *words], base, ctx.root):
            commit, why = ctx.committed(rev)
            if commit is None:
                out["violations"].append((rel, via + f"reads content that is not committed on main ({why})"))
            elif ctx.is_head(rev) and rel in ctx.changed:
                out["violations"].append((rel, via + "read at HEAD, but an earlier step of this run rewrote it, so "
                                                     "the step used the version before the rewrite"))
            elif rel in ctx.head_files and rel not in out["repo_reads"]:
                out["repo_reads"].append(rel)
        paths(words, base)
        return
    if name in SHELLS:                                 # c. a reviewed shell string
        if system_program(prog, name) and len(args) == 3 and args[1] == "-c":
            h = hashlib.sha256(args[2].encode("utf-8", "surrogateescape")).hexdigest()
            if h in REVIEWED_SHELL:
                if here and not _under(here, ctx.root) and step_folder(here):
                    return
                refuse(f"a reviewed shell string run in {here}, not in a folder the step made")
                return
        refuse("a shell (sh -c, bash -c, os.system, subprocess shell=True); only an exact string pinned by sha256 "
               "in REVIEWED_SHELL is accepted, in a folder the step made")
        return
    refuse(f"{name or '(no program)'} is not on the allow list (Python with the hook, git with a listed subcommand, "
           f"a reviewed shell string)")


def python_isolating_flags(args: list) -> list[str]:
    """The options of a Python command line (python ... or uv run ... python ...) that make it skip the hook: -I
    (isolated: ignores PYTHONPATH), -E (ignores PYTHON* variables) and -S (no site, so no sitecustomize), alone or in a
    cluster (-IB). Empty for any other command."""
    i = next((k for k, a in enumerate(args) if isinstance(a, str)
              and re.fullmatch(r"python[0-9.]*", os.path.basename(a))), None)
    if i is None:
        return []
    found, k = [], i + 1
    while k < len(args):
        a = args[k]
        if not isinstance(a, str) or not a.startswith("-") or a in ("-", "--") or a in ("-c", "-m"):
            break
        if a in ("-X", "-W"):                          # options that take a value
            k += 2
            continue
        if a.startswith("--") or a[1] in "XW":
            k += 1
            continue
        found += [f"-{ch}" for ch in a[1:] if ch in "IES"]
        k += 1
    return found


if __name__ == "__main__":
    print(__doc__)
