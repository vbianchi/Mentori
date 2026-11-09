"""B4: the authors' RLM package (rlms 0.1.3) run as Figure 2's reference arm, every model call under the lock (D31, D60,
D73). Imported by run_rlm_ref.py and check_rlm_ref.py, inside this folder's own uv project (Python >= 3.11, rlms
pinned by hash in uv.lock).

    from experiments.rlm_ref import adapter as ad
    bundle = ad.load_context()                         # findings/recompute/B4_rlm_ref_context.json, checked
    image = ad.ensure_image()                          # IMAGE_ID, the pinned sandbox image; never built by a run
    image["network"] = ad.ensure_network()             # b4-sandbox and its firewall (patch 6)
    assert not ad.probe_network()["open"]              # run_rlm_ref.py refuses instead
    ad.clean_stale(sink)                               # a killed run's containers and workspaces
    ad.add_sandbox_forms(bundle, image)                # repr(context) as the sandbox's Python writes it
    with rc.run(ctx):                                  # experiments.runner.run_context, one (question, draw)
        rec = ad.run_question(ctx, question, cap, bundle, image, "all135", "cap5", answer_key)

WHAT RUNS. The package's own RLM.completion(context, root_prompt=question) with max_depth 1 (Q44), max_iterations = the
turn cap (Q45), environment "docker" (Q46), compaction off, its own system prompt, orchestrator addendum, per-turn
prompts and 20,000-character cut of each code block's output (round 1 Q15). context is the 20 paper texts of the
context file (Q43). Nothing of the package is edited on disk; the patches below replace names in its modules at import.

PATCHES (each named in every answer record's "patches"):
  0 dotenv     The package's clients call python-dotenv's load_dotenv() at import, which reads the first .env found
               walking up from the package's folder (this repository's tree). It is replaced by a no-op first.
  1 client     rlm.core.rlm.get_client returns LockedGemini (below) for the root model; rlm.clients.get_client refuses,
               so none of the package's own clients (which send no temperature, top_p, top_k, output limit or seed,
               rlm/clients/gemini.py:61-69) can be built. Root turns go through LMHandler.completion, which is wrapped
               only to mark the call as a root turn.
  2 timeouts   comms_utils.socket_request (300 s per sub-call socket, comms_utils.py:179) waits without limit, and so do
               the container's requests (600 s, docker_repl.py:289-290): the lock's stall rule (stall_s 600 after the
               first chunk) ends a stuck call, and its record says so.
  3 subcall    In the container, llm_query, llm_query_batched, rlm_query and rlm_query_batched (rlm_query falls back to
               llm_query at max_depth 1) raise LLMQueryError when the host's call failed or stopped on the output limit
               (D73 Q47, as D67 A5 for Mentori), instead of returning the text "Error: ..." as an answer. The exception
               carries the host's message; a batch raises when any of its prompts failed, after every prompt has run,
               and the exception's .responses holds the others (None where one failed). An ok call's empty text is
               returned as "" (the package turned it into "Error: None"). The host proxy's batched handler returns a
               per-prompt "errors" list to make this possible. The replaced block of the container script is pinned
               by sha256, so a different package text refuses to run.
  4 loopback   The package binds its container proxy on 0.0.0.0 (docker_repl.py:514), which would let any machine on
               the network send model calls through it, paid by our key, while a question runs. It binds 127.0.0.1,
               on the first free port of PROXY_PORTS (the one host port range the sandbox network lets through, 6);
               colima's host.docker.internal reaches the host's loopback (checked by check_rlm_ref.py).
  5 bookkeeping RLM._default_answer (the forced final answer at the cap, rlm/core/rlm.py:673-696) and
               DockerREPL.execute_code are wrapped to know the turn and the code block a sub-call belongs to. Neither
               changes what the package does, except that execute_code raises a fatal error kept in the session
               (FATAL below) once the block has returned, and a Ctrl-C there stops the run with nothing stored for
               the question (the package would turn it into CancellationError, an ordinary failed answer).
  6 sandbox    The container's "docker run" (docker_repl.py:524-538) gets "--network b4-sandbox" and the labels
               b4.sandbox, b4.pid and b4.run; nothing else in it changes, and any other shape of that command is
               refused. On b4-sandbox (bridge b4sandbox0) the colima VM's firewall (ensure_network) lets the container
               reach the host only on PROXY_PORTS and the VM only for DNS, and refuses every private, link-local and
               multicast address, so code the model writes cannot reach the laptop's loopback services (a local
               Ollama, the ssh tunnel to the Studio's paper server) or the Studio's network. The public internet stays
               reachable, as in the package's default. probe_network checks this from a container before every run.
               The labels let a later run remove the containers a killed run left behind (clean_stale).
  7 exec stdin The package rewrites <workspace>/_exec.py on the host before every code block (docker_repl.py:696-698),
               in a folder the container mounts read-write, so model code could replace that file with a symlink and
               make the host overwrite any file the user can write. execute_code is replaced by the package's own
               body (pinned by the sha256 of its source) except that the script goes to "docker exec -i ... python -c
               STUB" on stdin; STUB runs it as __main__ under the name /workspace/_exec.py with sys.path[0] =
               /workspace and its lines in linecache, so tracebacks and imports read as before. After the container
               starts the host writes nothing into the workspace.

LockedGemini. One runner record per call in <sink>/calls.jsonl through run_context.append, the record shape of
experiments/mentori/backend/agents/lock_adapter.py: the runner's record (send_chat for a root turn and for a sub-call
given a message list, gemini_client.generate for a sub-call given a string) plus provider, role, caller_asked,
call_site and the request (messages_sent or prompt_sent), and "b4": call (root, forced_final, sub), turn, block (the
code block of the turn, 1-based), batch (id and index of an llm_query_batched prompt), cap, draw, question_id.
Settings: lock.gemini(gemini-3-flash-preview, draw, thinking=the run context's, None = [thinking] generator,
"default": Google's default thinking, nothing sent, D66). The model a code block names in llm_query(model=...) is
recorded in caller_asked.model_arg and never sent. Root turns carry passages [] (as Mentori's root turns); a sub-call's
prompt is whatever text the code built, so its passages are None and the answer record names the whole corpus.
Retries: gemini_client's own only. A root call (root or forced_final) that stops on the output limit (status length)
is recorded with status length and goes back to the package as the reply (D75 Q48), as the package's own Gemini client
returns response.text without reading why the reply ended (rlms 0.1.3 rlm/clients/gemini.py:72, :95): what
google-genai 2.30.1's response.text gives for the recorded parts (package_text, D78 Q114), the non-thought text parts
joined when the reply has a text part ('' when it is empty), None when it has none. Given None, a root turn's search
for code blocks raises TypeError (rlm/core/rlm.py:658, rlm/utils/parsing.py:18), stored as the answer's failure (stop
reason error); a closing call's None is the package's answer, stored as "". The answer record counts these length
stops in calls.root_length. A reply gemini_client labels "empty" (D83 Q145: STOP with no text and no function call,
stored as "ok" before; D89: a clean stream with no finishReason and nothing in it, stored as "error" before) or
"blocked" (gemini_client.EMPTY_TEXT_STATUSES), and a "recitation" (D90 Q1), "malformed_function_call",
"malformed_response" (D90 Q2) or other-reason reply ("language", "other", "unexpected_tool_call",
"too_many_tool_calls", D92 Q188; gemini_client.PASSED_ON_STATUSES), returns to the package and the record keeps the
status and Google's reason (D89, Q145 O3; LIST.md Rule 10). What it returns:
- a root or closing call: package_text of the parts passed on (D78 Q114, D92 Q185, audit F6), as rlms' own Gemini
  client returns response.text: the text parts joined, "" when every text part is "" (a part {"text": ""} beside a
  thought signature, as the 4 malformed G6 root replies cap2 04_fastp_TE3 d3, cap3 19_hpai_canada_CO2 d1, cap5
  OOD_009 d3 and cap5 SY_006 d3 hold), None when the reply has no text part (the 15 G6 root replies with no
  finishReason and no part at all). A blocked reply passes on no parts (D89), so it returns None. Given None, a root
  turn's search for code blocks raises TypeError and the question fails (stop reason error); the closing call's reply
  is the package's answer (rlm/core/rlm.py:673-695), None stored as "". (Before D92 Q185 the record's text went back,
  "" and not None for a reply with no text part; the docstring then cited D78 Q114 for that, but Q114 is the rule
  that adopted package_text.)
- a sub-call: the record's text ("" when it held none; a blocked reply ""), as an "ok" reply, and the code goes on.
calls.sub_failed counts blocked, recitation, malformed and other-reason sub-calls (grouped with the failures, Q145 O1)
and empty ones that ended with no finishReason, as before D89 when each raised (gemini_client.raised_before_d89), and
not STOP empty ones, as before D89. A root call with any other status that is not ok or length (error, stalled)
raises RootCallError after its record is written (the question ends: stop_reason root_call_failed, or
forced_final_failed for the closing call at the cap); a sub-call's raises SubCallError into the code (patch 3).
closing_answer(record) gives the answer a stored closing-call record yields under these rules (D92 Q187: G6's 72
failed closing calls take it with no rerun). Token counts come from these records; the package's usage_summary is not
used (LockedGemini reports zeros to it).
send_chat is gemini_client.chat with one change: a message list becomes Gemini contents by the authors' client's rule
(package_contents, rlm/clients/gemini.py:106-123), not by gemini_client.to_contents. Only role and content are read;
the last system message is the system instruction; assistant is sent as model, user and every other role (or none) as
user; each content is sent as its text, "" included. to_contents refuses roles such as "model" (a ValueError that
stopped the run) and sends "[Empty]" for an empty model turn. The lock's settings, the stream, the retry rule and the
record (contents_sent, system_sent) are gemini_client's own (_settings, _record, _call). A prompt the package's client
could not send (not a string or a list of message dicts, or a content that is not a string) is written as a record
with status error, b4.not_sent true and no request, and raises SubCallError into the code.

FATAL. A key found in a record or trace (KeyLeakError), a LockError or RunContextError, or an exception from the runner
itself inside a sub-call is kept in the session and raised when the code block returns, even if the model's code
caught it: the run stops and nothing more is written for the question. An exception before the first root turn
(the container did not start, the image is wrong) is a setup error and is raised as well.

TRACE. <sink>/traces/<arm>__<question>__d<draw>.json: the package's run metadata and, per turn, the root call's seq,
the model's reply, and per code block its code, stdout, stderr, locals, final answer, execution time and the seqs of
its sub-calls. Whole messages are in the root call's record, not repeated. In stdout, stderr, locals and final answers,
a string equal to the corpus (repr(context), a paper's text or its repr) is written as {"corpus": context_sha256, ...}
(design R3: the container's locals repeat the whole corpus in every block), and any other string of 4,096 characters or
more is written once to <sink>/blobs/<sha256>.txt and referenced as {"blob": sha256, "chars": n}; the model's replies
are written whole. Every record, trace, blob and answer is
scanned for the values of GEMINI_API_KEY and ANTHROPIC_API_KEY before it is written (KeyLeakError; the key is never
printed).
"""

from __future__ import annotations

import asyncio
import contextvars
import copy
import errno
import hashlib
import inspect
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import dotenv  # noqa: E402

dotenv.load_dotenv = lambda *a, **k: False          # patch 0, before the package imports it by name

import rlm  # noqa: E402,F401
import rlm.clients as rlm_clients  # noqa: E402
from rlm.clients.base_lm import BaseLM  # noqa: E402
from rlm.core import comms_utils  # noqa: E402
from rlm.core import lm_handler  # noqa: E402
from rlm.core import rlm as rlm_core  # noqa: E402
from rlm.core.types import ModelUsageSummary, UsageSummary  # noqa: E402
from rlm.environments import docker_repl  # noqa: E402
from rlm.logger import RLMLogger  # noqa: E402
from rlm.utils.exceptions import CancellationError  # noqa: E402
from rlm.utils.parsing import find_code_blocks  # noqa: E402

from experiments.runner import gemini_client  # noqa: E402
from experiments.runner import run_context as rc  # noqa: E402
from experiments.runner.lock import LockError  # noqa: E402
from experiments.runner.lock import load as load_lock  # noqa: E402

MODEL = "gemini-3-flash-preview"                    # D27, through experiments/runner/gemini_client
IDENT = f"gemini::{MODEL}"
PACKAGE = {"name": "rlms", "version": "0.1.3",
           "wheel_sha256": "fac541ff745242540fee47b6e41a74c847fd7022091330dad7844d413eb5944f"}
MAX_DEPTH = 1                                       # D73 Q44
CONTEXT_FILE = ROOT / "findings" / "recompute" / "B4_rlm_ref_context.json"
SANDBOX = HERE / "sandbox"
IMAGE_TAG = "rlm-ref-sandbox:b4"
# The sandbox image every run uses, by content id (built 15 October 2026 from sandbox/ by build_image()). A run refuses
# any other image and never builds one: after a rebuild (a reset colima, a prune) the new id is written here by hand.
IMAGE_ID = "sha256:81cfc1d87bb8aeadb2f47c8cd011fde70fff9e744ce792afe9f2e822bb395f31"
BASE_IMAGE = "python:3.11-slim@sha256:e88e9763f943ec1834f992a4b51e0f24500486803e8bc534e5767af9ea65f6ce"
BLOB_MIN = 4096
KEY_NAMES = ("GEMINI_API_KEY", "ANTHROPIC_API_KEY")
EXEC_BLOCK_SHA256 = "28d8a7feb23ae4a00c612893cc10fb30fd7e8c02b294b381c278016765488228"   # rlms 0.1.3's container block
EXECUTE_CODE_SHA256 = "c4df6981d7d700b8a19f6a04c3aeab3da84b3e865af51a57648b0a5d308de6e8"   # DockerREPL.execute_code
NETWORK, BRIDGE = "b4-sandbox", "b4sandbox0"        # patch 6
PROXY_PORTS = (47300, 47399)                        # patch 4: the host ports the sandbox may reach (inclusive)
BLOCKED = ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "100.64.0.0/10", "169.254.0.0/16", "127.0.0.0/8",
           "224.0.0.0/4", "240.0.0.0/4")
PATCHES = ("0 dotenv", "1 client", "2 timeouts", "3 subcall", "4 loopback", "5 bookkeeping", "6 sandbox",
           "7 exec stdin")


class KeyLeakError(Exception):
    pass


class SetupError(Exception):
    pass


class RootCallError(RuntimeError):
    """A root turn whose status is not ok. .record is the record written for it."""

    def __init__(self, record: dict):
        self.record = record
        super().__init__(f"root call {record.get('b4', {}).get('call')} turn {record.get('b4', {}).get('turn')}: "
                         f"status {record.get('status')}: {record.get('error') or record.get('stop_reason')} "
                         f"(seq {record.get('seq')})")


class SubCallError(RuntimeError):
    """A sub-call whose status is not ok; its message is what the model's code sees (patch 3)."""


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_text(s: str) -> str:
    return sha256_bytes(s.encode("utf-8", "surrogatepass"))


# ---------------------------------------------------------------- keys

_keys: list | None = None


def key_values() -> list:
    """The API key values to scan for, read once (environment, else ~/.config/mentori-runs/keys.env)."""
    global _keys
    if _keys is None:
        vals = []
        for name in KEY_NAMES:
            try:
                v = gemini_client.key(name)
            except RuntimeError:
                continue
            if v and len(v) >= 8:
                vals.append(v)
        _keys = vals
    return _keys


def scan(text: str, what: str) -> None:
    """Raises KeyLeakError when text holds an API key value. The key is never printed."""
    for v in key_values():
        if v in text:
            raise KeyLeakError(f"{what} holds the value of an API key ({len(v)} characters); nothing was written")


def _scan_obj(obj, what: str) -> None:
    scan(json.dumps(obj, ensure_ascii=False, default=repr), what)


# ---------------------------------------------------------------- the context file

def load_context(path: Path = CONTEXT_FILE) -> dict:
    """The context file, checked against its .sha256 file and its own context_sha256."""
    raw = Path(path).read_bytes()
    file_sha = sha256_bytes(raw)
    side = Path(path).with_suffix(".json.sha256")
    if not side.exists():
        raise SetupError(f"{side} is missing; build the context with experiments/rlm_ref/build_context.py")
    want = side.read_text().split()[0]
    if want != file_sha:
        raise SetupError(f"{path} has sha256 {file_sha}, its .sha256 file says {want}")
    doc = json.loads(raw)
    context = doc["context"]
    csha = sha256_bytes(json.dumps(context, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    if csha != doc["context_sha256"]:
        raise SetupError(f"{path}: the context's sha256 is {csha}, the file says {doc['context_sha256']}")
    if not (isinstance(context, list) and len(context) == 20 and all(isinstance(t, str) for t in context)):
        raise SetupError(f"{path}: the context is not a list of 20 texts")
    forms = {sha256_text(repr(context)): {"corpus": csha, "form": "repr(context)"}}
    for i, t in enumerate(context):
        name = doc["papers"][i]["file_name"]
        forms.setdefault(sha256_text(t), {"corpus": csha, "paper": name, "form": "text"})
        forms.setdefault(sha256_text(repr(t)), {"corpus": csha, "paper": name, "form": "repr"})
    rel = str(Path(path).resolve().relative_to(ROOT)) if Path(path).resolve().is_relative_to(ROOT) else str(path)
    return {"context": context, "context_sha256": csha, "file": rel, "file_sha256": file_sha, "forms": forms,
            "papers": [p["file_name"] for p in doc["papers"]]}


# ---------------------------------------------------------------- the sandbox image

def add_sandbox_forms(bundle: dict, image: dict) -> int:
    """Adds the sha256 of repr(context) and of each paper's repr as the sandbox's Python computes them (its Unicode
    tables decide which characters repr escapes), so a container's locals match the corpus forms. Returns how many
    forms were new (0 when the host's and the sandbox's reprs agree)."""
    prog = ("import hashlib, json, sys\n"
            "c = json.load(sys.stdin)\n"
            "h = lambda s: hashlib.sha256(s.encode('utf-8', 'surrogatepass')).hexdigest()\n"
            "print(json.dumps([h(repr(c))] + [h(repr(t)) for t in c]))\n")
    p = _docker("run", "--rm", "-i", "--network", "none", image["image_id"], "python", "-c", prog,
                input=json.dumps(bundle["context"], ensure_ascii=False))
    hs = json.loads(p.stdout)
    new = 0
    for i, h in enumerate(hs):
        form = ({"corpus": bundle["context_sha256"], "form": "repr(context)"} if i == 0 else
                {"corpus": bundle["context_sha256"], "paper": bundle["papers"][i - 1], "form": "repr"})
        if h not in bundle["forms"]:
            bundle["forms"][h] = form
            new += 1
    return new


def _docker(*args, check=True, **kw) -> subprocess.CompletedProcess:
    p = subprocess.run(["docker", *args], capture_output=True, text=True, **kw)
    if check and p.returncode != 0:
        raise SetupError(f"docker {' '.join(args[:2])}: exit {p.returncode}: {p.stderr.strip()[-2000:]}")
    return p


def sandbox_labels() -> dict:
    return {"b4.base": BASE_IMAGE,
            "b4.dockerfile_sha256": sha256_bytes((SANDBOX / "Dockerfile").read_bytes()),
            "b4.requirements_sha256": sha256_bytes((SANDBOX / "requirements.txt").read_bytes())}


def build_image() -> str:
    """Builds the sandbox image from sandbox/ with labels naming its inputs and returns its content id. Run only by
    hand (run_rlm_ref.py --build-image); a run uses IMAGE_ID and refuses any other."""
    labels = sandbox_labels()
    if BASE_IMAGE.split("@")[1] not in (SANDBOX / "Dockerfile").read_text():
        raise SetupError("sandbox/Dockerfile does not name BASE_IMAGE's digest")
    args = ["build", "-t", IMAGE_TAG]
    for k, v in labels.items():
        args += ["--label", f"{k}={v}"]
    _docker(*args, str(SANDBOX))
    return json.loads(_docker("image", "inspect", IMAGE_TAG, "--format", "{{json .}}").stdout)["Id"]


def ensure_image(image_id: str = IMAGE_ID) -> dict:
    """The pinned sandbox image: {"image_id", **labels}. Refuses when Docker holds no image with that content id, or
    when its labels differ from sandbox/'s files. Never builds."""
    p = _docker("image", "inspect", image_id, "--format", "{{json .}}", check=False)
    if p.returncode != 0:
        raise SetupError(f"Docker holds no image {image_id[:19]} (IMAGE_ID). Build it with run_rlm_ref.py "
                         f"--build-image and write the id it prints into adapter.IMAGE_ID; a run never builds one")
    info = json.loads(p.stdout)
    if info["Id"] != image_id:
        raise SetupError(f"image {image_id[:19]} resolved to {info['Id'][:19]}")
    labels = (info.get("Config") or {}).get("Labels") or {}
    want = sandbox_labels()
    differ = [k for k, v in want.items() if labels.get(k) != v]
    if differ:
        raise SetupError(f"image {image_id[:19]} was built from other inputs than sandbox/ ({', '.join(differ)})")
    return {"image_id": info["Id"], **want}


# ---------------------------------------------------------------- the sandbox network (patch 6)

def _vm(script: str, check: bool = True) -> subprocess.CompletedProcess:
    """A shell script run as root in the colima VM (the Docker host on the laptop)."""
    p = subprocess.run(["colima", "ssh", "--", "sudo", "sh", "-c", script], capture_output=True, text=True)
    if check and p.returncode != 0:
        raise SetupError(f"colima VM: exit {p.returncode}: {p.stderr.strip()[-1000:]}")
    return p


def _rules(gateway: str) -> tuple[list, list]:
    """(forward rules, input rules) for the chains B4-SANDBOX and B4-SANDBOX-IN, as iptables -S prints them."""
    fwd = [f"-A B4-SANDBOX -d {gateway}/32 -p tcp -m tcp --dport {PROXY_PORTS[0]}:{PROXY_PORTS[1]} -j RETURN"]
    fwd += [f"-A B4-SANDBOX -d {net} -j REJECT --reject-with icmp-port-unreachable" for net in BLOCKED]
    inp = ["-A B4-SANDBOX-IN -p udp -m udp --dport 53 -j RETURN", "-A B4-SANDBOX-IN -p tcp -m tcp --dport 53 -j RETURN",
           "-A B4-SANDBOX-IN -j REJECT --reject-with icmp-port-unreachable"]
    return fwd, inp


def ensure_network(image_id: str = IMAGE_ID) -> dict:
    """Patch 6: the Docker network b4-sandbox (bridge b4sandbox0) and the colima VM's firewall for it, made the same
    every time (the VM forgets its rules when colima restarts). Refuses unless Docker runs in colima. Returns what a
    run records: network, bridge, host gateway, the rules and their sha256."""
    if subprocess.run(["colima", "status"], capture_output=True).returncode != 0:
        raise SetupError("the sandbox firewall is set in colima's VM, and colima is not running (colima start); "
                         "a run never starts without it")
    if _docker("network", "inspect", NETWORK, check=False).returncode != 0:
        _docker("network", "create", "--driver", "bridge", "-o", f"com.docker.network.bridge.name={BRIDGE}",
                "--label", "b4.sandbox=1", NETWORK)
    net = json.loads(_docker("network", "inspect", NETWORK, "--format", "{{json .}}").stdout)
    if (net.get("Options") or {}).get("com.docker.network.bridge.name") != BRIDGE:
        raise SetupError(f"network {NETWORK} exists without bridge name {BRIDGE}; remove it (docker network rm)")
    gw = _docker("run", "--rm", "--network", "none", "--add-host", "host.docker.internal:host-gateway", image_id,
                 "python", "-c", "import socket; print(socket.gethostbyname('host.docker.internal'))").stdout.strip()
    fwd, inp = _rules(gw)
    have = _vm("iptables -S B4-SANDBOX 2>/dev/null; echo ==; iptables -S B4-SANDBOX-IN 2>/dev/null", check=False).stdout
    want = "\n".join(["-N B4-SANDBOX", *fwd, "==", "-N B4-SANDBOX-IN", *inp])
    if have.strip() != want:
        script = ["set -e", "iptables -N B4-SANDBOX 2>/dev/null || iptables -F B4-SANDBOX",
                  "iptables -N B4-SANDBOX-IN 2>/dev/null || iptables -F B4-SANDBOX-IN"]
        script += ["iptables " + r for r in fwd + inp]
        _vm("\n".join(script))
    _vm("iptables -C DOCKER-USER -i b4sandbox0 -j B4-SANDBOX 2>/dev/null || "
        "iptables -I DOCKER-USER 1 -i b4sandbox0 -j B4-SANDBOX\n"
        "iptables -C INPUT -i b4sandbox0 -j B4-SANDBOX-IN 2>/dev/null || "
        "iptables -I INPUT 1 -i b4sandbox0 -j B4-SANDBOX-IN")
    shown = _vm("iptables -S B4-SANDBOX; echo ==; iptables -S B4-SANDBOX-IN; echo ==; "
                "iptables -S DOCKER-USER | grep -c 'b4sandbox0 -j B4-SANDBOX$'; "
                "iptables -S INPUT | grep -c 'b4sandbox0 -j B4-SANDBOX-IN$'").stdout.strip()
    if shown != want + "\n==\n1\n1":
        raise SetupError(f"the colima VM's rules for {BRIDGE} are not the ones set:\n{shown}")
    return {"network": NETWORK, "bridge": BRIDGE, "host_gateway": gw, "proxy_ports": list(PROXY_PORTS),
            "blocked": list(BLOCKED), "rules": want.splitlines(), "rules_sha256": sha256_text(want)}


def host_listeners() -> list[int]:
    """The laptop's listening TCP ports (any address), from lsof."""
    p = subprocess.run(["lsof", "-nP", "-iTCP", "-sTCP:LISTEN", "-Fn"], capture_output=True, text=True)
    return sorted({int(x.rsplit(":", 1)[1]) for x in p.stdout.splitlines() if x.startswith("n") and ":" in x})


def check_proxy_ports() -> None:
    """Refuses when a process other than this adapter listens on PROXY_PORTS (the sandbox could reach it)."""
    a, b = PROXY_PORTS
    p = subprocess.run(["lsof", "-nP", f"-iTCP:{a}-{b}", "-sTCP:LISTEN", "-Fp"], capture_output=True, text=True)
    for pid in sorted({x[1:] for x in p.stdout.splitlines() if x.startswith("p")}):
        args = subprocess.run(["ps", "-o", "args=", "-p", pid], capture_output=True, text=True).stdout.strip()
        if "rlm_ref" not in args:
            raise SetupError(f"process {pid} ({args[:80]}) listens on the sandbox's proxy ports {a}-{b}; the "
                             "sandbox could reach it")


_PROBE = """import json, socket, sys
out = {}
for host, port in json.loads(sys.argv[1]):
    s = socket.socket(); s.settimeout(3)
    try:
        s.connect((host, port)); out[f"{host}:{port}"] = "open"
    except Exception as e:
        out[f"{host}:{port}"] = type(e).__name__
    finally:
        s.close()
print(json.dumps(out))
"""


def _probe(image_id: str, targets: list) -> dict:
    p = _docker("run", "--rm", "--network", NETWORK, "--add-host", "host.docker.internal:host-gateway",
                "--label", "b4.sandbox=1", "--label", f"b4.pid={os.getpid()}", image_id,
                "python", "-c", _PROBE, json.dumps(targets))
    return json.loads(p.stdout)


def probe_network(image_id: str = IMAGE_ID) -> dict:
    """From a container on b4-sandbox: first a canary, a listener this function opens on the laptop's loopback
    outside PROXY_PORTS; only when the canary is refused, a TCP connection to every port the laptop listens on
    outside PROXY_PORTS (through host.docker.internal), to the VM's ssh and to a private address. So a broken
    firewall is found on the canary, before any connection reaches a real service (the ssh tunnel to the Studio).
    Returns {"targets": n, "open": [...], "results": {...}}; open must be empty."""
    a, b = PROXY_PORTS
    canary = socket.socket()
    try:
        canary.bind(("127.0.0.1", 0))
        while a <= canary.getsockname()[1] <= b:
            canary.close()
            canary = socket.socket()
            canary.bind(("127.0.0.1", 0))
        canary.listen(1)
        port = canary.getsockname()[1]
        res = _probe(image_id, [["host.docker.internal", port]])
    finally:
        canary.close()
    if any(v == "open" for v in res.values()):
        return {"targets": 1, "open": sorted(res), "results": res, "canary": "open; nothing else was probed"}
    targets = [["host.docker.internal", p] for p in host_listeners() if not a <= p <= b and p != port]
    targets += [["192.168.5.1", 22], ["10.255.255.1", 80]]
    res.update(_probe(image_id, targets))
    return {"targets": len(res), "open": sorted(k for k, v in res.items() if v == "open"), "results": res,
            "canary": "refused"}


def clean_stale(sink: Path | None) -> dict:
    """Removes the sandbox containers whose b4.pid process has ended (a killed run's, patch 6) and, under
    <sink>/docker_ws, every workspace folder not of a running process (p<pid>), so no unscanned workspace stays in
    the sink."""
    p = _docker("ps", "-a", "--filter", "label=b4.sandbox=1", "--format", '{{.ID}} {{.Label "b4.pid"}}')
    gone = []
    for line in p.stdout.splitlines():
        cid, _, pid = line.partition(" ")
        if not _alive(pid):
            _docker("rm", "-f", cid, check=False)
            gone.append(cid)
    removed = []
    ws = Path(sink) / "docker_ws" if sink is not None else None
    if ws is not None and ws.is_dir():
        for d in ws.iterdir():
            if not (d.name.startswith("p") and _alive(d.name[1:])):
                if d.is_dir() and not d.is_symlink():
                    shutil.rmtree(d, ignore_errors=True)
                else:
                    d.unlink(missing_ok=True)
                removed.append(d.name)
    return {"containers_removed": gone, "workspaces_removed": removed}


def _alive(pid: str) -> bool:
    if not pid.isdigit():
        return False
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


# ---------------------------------------------------------------- the session of one question

class Session:
    """What one question's calls share: the run context, the turn and block now running, the records' summaries."""

    def __init__(self, ctx: rc.RunContext, cap: int, question_id: str, sink: Path):
        self.ctx, self.cap, self.question_id, self.sink = ctx, cap, question_id, sink
        self.turn = 0                  # root turns made (1..cap); the forced final answer is turn cap + 1
        self.block = 0                 # code blocks run in the current turn
        self.forced = False
        self.calls: list[dict] = []    # one summary per record written
        self.batches: list[dict] = []  # registered by the proxy's batched handler
        self.fatal: BaseException | None = None
        self.lock = threading.Lock()
        self._batch_seq = 0

    def register_batch(self, prompts: list) -> int:
        with self.lock:
            self._batch_seq += 1
            self.batches.append({"id": self._batch_seq, "prompts": [sha256_text(json.dumps(p, sort_keys=True,
                                                                                              default=repr))
                                                                     for p in prompts],
                                 "taken": [False] * len(prompts)})
            return self._batch_seq

    def take_batch_slot(self, prompt) -> tuple:
        h = sha256_text(json.dumps(prompt, sort_keys=True, default=repr))
        with self.lock:
            for b in self.batches:
                for i, (ph, t) in enumerate(zip(b["prompts"], b["taken"], strict=True)):
                    if ph == h and not t:
                        b["taken"][i] = True
                        return b["id"], i
        return None, None

    def fail(self, e: BaseException) -> None:
        with self.lock:
            if self.fatal is None:
                self.fatal = e


_session: Session | None = None
_session_guard = threading.Lock()
_root: contextvars.ContextVar[bool] = contextvars.ContextVar("b4_root_call", default=False)


def current_session() -> Session:
    if _session is None:
        raise SetupError("no B4 session: the package was called outside run_question()")
    return _session


# ---------------------------------------------------------------- LockedGemini (patch 1)

def sub_failed(subs: list) -> int:
    """calls.sub_failed of an answer, from its sub-call summaries. D83 Q145: a STOP "empty" sub-call returned to the
    code as an "ok" one did, so it is not a failure. D89, D90: a blocked, recitation, malformed or no-finishReason
    empty sub-call returns to the code too and is still counted, as before D89 when it raised (Q145 O1;
    gemini_client.raised_before_d89)."""
    return sum(c["status"] not in ("ok", "empty") or gemini_client.raised_before_d89(c) for c in subs)


def _summary(rec: dict) -> dict:
    return {"seq": rec.get("seq"), **rec["b4"], "status": rec.get("status"), "stop_reason": rec.get("stop_reason"),
            "prompt_tokens": rec.get("prompt_tokens"), "output_tokens": rec.get("output_tokens"),
            "thinking_tokens": rec.get("thinking_tokens"), "wall_s": rec.get("wall_s")}


class _NotSent(Exception):
    """A prompt the package's Gemini client could not have sent; nothing is sent."""


def package_contents(messages: list) -> tuple[str | None, list[dict]]:
    """The authors' Gemini client's mapping of a message list (rlm/clients/gemini.py:106-123), as (system instruction,
    contents): only role and content are read; the last system message is the system instruction; assistant is sent
    as model, user and any other role (or none) as user; each content is one text part as given, "" included. A
    content that is not a string raises _NotSent."""
    system, contents = None, []
    for i, m in enumerate(messages):
        role, content = m.get("role"), m.get("content", "")
        if not isinstance(content, str):
            raise _NotSent(f"message {i}: content is {type(content).__name__}, not a string")
        if role == "system":
            system = content
        else:
            contents.append({"role": "model" if role == "assistant" else "user", "parts": [{"text": content}]})
    return system, contents


def send_chat(lock, draw: int, messages: list, thinking=None, passages=None) -> dict:
    """gemini_client.chat with package_contents in place of gemini_client.to_contents; everything else (the lock's
    settings, the stream, the retry rule, the record) is gemini_client's own."""
    system, contents = package_contents(messages)
    cfg, stall_s, override = gemini_client._settings(lock, MODEL, draw, thinking, None, None, None)
    gen = gemini_client.generation_config(cfg)
    payload = {"contents": contents, "generationConfig": gen}
    if system is not None:
        payload["systemInstruction"] = {"parts": [{"text": system}]}
    rec = gemini_client._record(MODEL, draw, None, thinking, gen, override, stall_s, lock, passages)
    rec.update(system_sent=system, contents_sent=copy.deepcopy(contents), tools_sent=None)
    return gemini_client._call(MODEL, payload, rec, stall_s)


def package_text(raw_parts: list) -> str | None:
    """What the package's Gemini client returns for a reply with these parts: google-genai 2.30.1's response.text
    (types.py:8741-8789, _get_text; the version experiments/rlm_ref/uv.lock pins), which the client returns unread
    (rlms 0.1.3 rlm/clients/gemini.py:72). A text part is a part whose text is a string and whose thought is not true;
    the text parts' texts joined when there is at least one ('' when they are all empty), None when there is none."""
    texts = [p["text"] for p in raw_parts
             if isinstance(p, dict) and isinstance(p.get("text"), str) and p.get("thought") is not True]
    return "".join(texts) if texts else None


def closing_answer(call: dict) -> str:
    """D92 Q187: the answer a stored closing-call record (b4.call forced_final) gives under today's rules, exactly what
    run_question would store: the package returns the closing reply unread as its answer (rlm/core/rlm.py:673-695),
    LockedGemini hands it package_text of the parts passed on (a returned status, D89, D90, D92 Q185 and Q188; a cut
    reply, D75 Q48 and D78 Q114) or the text of an ok reply, and run_question stores None as "". Raises ValueError
    for a record that is not a closing call or whose status still raises RootCallError (no answer)."""
    b4 = call.get("b4") or {}
    if b4.get("call") != "forced_final":
        raise ValueError(f"seq {call.get('seq')}: not a closing call (b4.call {b4.get('call')!r})")
    st = call.get("status")
    if st in gemini_client.RETURNED_STATUSES:
        t = package_text([] if st == "blocked" else call.get("raw_parts") or [])
    elif st == "length":
        t = package_text(call.get("raw_parts") or [])
    elif st == "ok":
        t = call.get("text")
    else:
        raise ValueError(f"seq {call.get('seq')}: status {st!r} still ends the question (RootCallError)")
    return "" if t is None else t if isinstance(t, str) else str(t)


REBUILT_FIELDS = ("answer", "status", "stop_reason", "error", "forced_final_has_code")


def rebuild_from_closing(answer: dict, calls: list[dict], provenance: dict) -> dict:
    """D92 Q187: an answer record stored as forced_final_failed, rebuilt from its own stored call records with no
    model call: the answer is closing_answer(the closing call), status ok, stop_reason turn_cap, error None,
    forced_final_has_code from the package's own parser, as run_question writes them. Every other field (calls,
    tokens, wall_s, trace, adapter_sha256, lock_sha256, seq, ctx_uid) stays as stored: the attempt is the one that ran
    (Q29). "rebuilt" records the decision, the closing call's seq and status, the stored values of REBUILT_FIELDS and
    provenance (the script, its commit, the adapter's sha256). Refuses (ValueError) unless the answer is
    forced_final_failed with forced_final true, calls are exactly its ctx_uid's records with the seqs it lists, and the
    closing call is the last of them and the only root or closing call that raised, and no sub-call is one D89, D90
    or Q188 now returns (gemini_client.raised_before_d89), so nothing before the closing call would run differently."""
    if answer.get("status") != "failed" or answer.get("stop_reason") != "forced_final_failed" \
            or answer.get("forced_final") is not True:
        raise ValueError(f"{answer.get('answer_key')}: not a forced_final_failed answer")
    seqs = sorted(c.get("seq") for c in calls)
    if seqs != sorted(answer["calls"]["seqs"]) or any(c.get("ctx_uid") != answer.get("ctx_uid") for c in calls):
        raise ValueError(f"{answer.get('answer_key')}: the calls given are not the answer's ({len(calls)} records)")
    last = max(calls, key=lambda c: c["seq"])
    roots_raised = [c for c in calls if (c.get("b4") or {}).get("call") in ("root", "forced_final")
                    and c.get("status") not in ("ok", "length", "empty")]
    if (last.get("b4") or {}).get("call") != "forced_final" or roots_raised != [last]:
        raise ValueError(f"{answer.get('answer_key')}: the closing call is not the last call and the only root or "
                         f"closing call that raised ({[(c['seq'], c.get('status')) for c in roots_raised]})")
    subs_changed = [c["seq"] for c in calls if (c.get("b4") or {}).get("call") == "sub"
                    and gemini_client.raised_before_d89(c)]
    if subs_changed:
        raise ValueError(f"{answer.get('answer_key')}: sub-calls {subs_changed} raised before D89 and now return, so "
                         "the code before the closing call would have run differently; rerun, not rebuild")
    text = closing_answer(last)
    out = copy.deepcopy(answer)
    out.update(answer=text, status="ok", stop_reason="turn_cap", error=None,
               forced_final_has_code=bool(text and find_code_blocks(text)))
    out["rebuilt"] = {"decision": "D92 Q187", "from_call_seq": last["seq"], "call_status": last.get("status"),
                      "call_stop_reason": last.get("stop_reason"),
                      "as_stored": {k: answer.get(k) for k in REBUILT_FIELDS}, **provenance}
    _scan_obj(out, f"the rebuilt answer record of {answer.get('answer_key')}")
    return out


def _not_sent(lock, draw: int, thinking, passages, reason: str) -> dict:
    """The record of a call refused before sending: the settings it would have had, no request, status error."""
    cfg, stall_s, override = gemini_client._settings(lock, MODEL, draw, thinking, None, None, None)
    rec = gemini_client._record(MODEL, draw, None, thinking, gemini_client.generation_config(cfg), override,
                                stall_s, lock, passages)
    rec.update(status="error", error=f"not sent: {reason}", wall_s=0.0)
    return rec


class LockedGemini(BaseLM):
    """The package's client interface over experiments/runner/gemini_client, one runner record per call."""

    def __init__(self, session: Session):
        super().__init__(model_name=MODEL, timeout=None)
        self.session = session

    # the package's usage accounting is not used (tokens come from the records)
    def get_usage_summary(self) -> UsageSummary:
        return UsageSummary(model_usage_summaries={})

    def get_last_usage(self) -> ModelUsageSummary:
        return ModelUsageSummary(total_calls=0, total_input_tokens=0, total_output_tokens=0)

    def completion(self, prompt, model: str | None = None) -> str:
        return self._call(prompt, model, batched=False, root=_root.get())

    async def acompletion(self, prompt, model: str | None = None) -> str:
        # only the proxy's batched handler (lm_handler.py:88-100) calls acompletion
        return await asyncio.to_thread(self._call, prompt, model, True, False)

    def _call(self, prompt, model_arg, batched: bool, root: bool) -> str:
        s = self.session
        if s.fatal is not None:
            raise SubCallError(f"the run has stopped: {type(s.fatal).__name__}")
        with rc.run(s.ctx):
            try:
                return self._call_in_run(s, prompt, model_arg, batched, root)
            except (SubCallError, RootCallError):
                raise
            except BaseException as e:              # KeyLeakError, LockError, RunContextError, the runner's own errors
                s.fail(e)
                raise

    def _call_in_run(self, s: Session, prompt, model_arg, batched: bool, root: bool) -> str:
        ctx = s.ctx
        if root:
            with s.lock:
                if s.forced:
                    call, turn = "forced_final", s.cap + 1
                else:
                    s.turn += 1
                    call, turn = "root", s.turn
                s.block = 0
            block, batch = None, (None, None)
            rc.set_passages([])
        else:
            call, turn, block = "sub", s.turn, s.block
            batch = s.take_batch_slot(prompt) if batched else (None, None)
        lock = load_lock()
        not_sent = False
        try:
            if isinstance(prompt, str):
                method = "generate"
                extra = {"prompt_sent": prompt}
                rec = gemini_client.generate(lock, MODEL, ctx.draw, prompt, thinking=ctx.thinking,
                                             passages=rc.passages())
            elif isinstance(prompt, list) and all(isinstance(m, dict) for m in prompt):
                method = "chat"
                extra = {"messages_sent": copy.deepcopy(prompt), "messages_sent_verified": None, "tools_given": None}
                rec = send_chat(lock, ctx.draw, prompt, thinking=ctx.thinking, passages=rc.passages())
            else:
                method = "none"
                extra = {"prompt_given": prompt if isinstance(prompt, (dict, list, int, float, type(None)))
                         else repr(prompt)}
                raise _NotSent(f"a prompt must be a string or a list of message dicts, not {type(prompt).__name__}")
        except _NotSent as e:
            not_sent = True
            rec = _not_sent(lock, ctx.draw, ctx.thinking, rc.passages(), str(e))
        asked = {"method": method, "model_identifier": IDENT, "think_suffix": None, "options": None, "think": None,
                 "tools": False, "system": False, "images": 0, "model_arg": model_arg}
        site = ("rlms core/rlm.py _default_answer" if call == "forced_final" else
                "rlms core/rlm.py _completion_turn" if call == "root" else
                "rlms lm_handler batched (llm_query_batched / rlm_query_batched)" if batched else
                "rlms lm_handler single (llm_query / rlm_query)")
        b4 = {"call": call, "turn": turn, "block": block, "batch_id": batch[0], "batch_index": batch[1],
              "cap": s.cap, "draw": ctx.draw, "question_id": s.question_id, "not_sent": not_sent}
        record = {**rec, "provider": "gemini", "role": "generator", "caller_asked": asked, "call_site": site,
                  **extra, "b4": b4}
        _scan_obj(record, f"the record of {call} turn {turn}")
        written = rc.append(record)
        with s.lock:
            s.calls.append(_summary(written))
        status = written["status"]
        if root and status in gemini_client.RETURNED_STATUSES:
            # D92 Q185 (audit F6), D78 Q114: a root or closing reply that returns to the package goes back as the
            # package's own Gemini client returns it, response.text of the parts passed on (package_text): the text
            # parts joined, "" when every text part is "", None when there is none. A blocked reply passes on no
            # parts (D89), so it goes back as None too. Given None, the root turn's search for code blocks raises
            # TypeError and the question fails (stop reason error); a closing call's None is the answer, stored as ""
            return package_text([] if status == "blocked" else written["raw_parts"])
        if status in gemini_client.EMPTY_TEXT_STATUSES:
            # sub-calls only from here (root replies above). D83 Q145, D89 (Q145 O3): an empty or blocked sub-call
            # reply goes back to the code as an "ok" reply with its blank text (an empty one's, as before D89) or ""
            # (a blocked reply: the parts it streamed before Google stopped it are not passed on); the record keeps
            # the status and the reason
            return written["text"] if status == "empty" else ""
        if status in gemini_client.PASSED_ON_STATUSES:
            # D90, D92 Q188: a recitation stop (Q1), a malformed reply (Q2) or a reply Google ended for another reason
            # (language, other, unexpected tool call, too many tool calls) goes back to the code as an "ok" reply with
            # the text the stream held ("" when none); the record keeps the status and the reason
            return written["text"]
        if root:
            # D75 Q48: a cut root reply is passed on (its record says status length); any other status ends the question
            if status not in ("ok", "length"):
                raise RootCallError(written)
            if status == "length":
                # D78 Q114: what the package's client would return for these parts (response.text), None included
                return package_text(written["raw_parts"])
            return written["text"]
        if status == "ok":
            return written["text"]
        if status == "length":
            raise SubCallError(
                f"sub-call stopped on the output limit (status length, finishReason {written.get('stop_reason')}; "
                f"{written.get('output_tokens')} answer and {written.get('thinking_tokens')} thinking tokens, "
                f"max_output_tokens {written['options_sent'].get('maxOutputTokens')}); recorded as seq {written['seq']}")
        raise SubCallError(f"sub-call failed (status {status}: {written.get('error') or written.get('stop_reason')}); "
                           f"recorded as seq {written['seq']}")


# ---------------------------------------------------------------- the patches

_EXEC_BLOCK = '''_LLM_TIMEOUT = None   # B4 patch 2: no client-side limit; the host's stall rule ends a stuck call
_RLM_TIMEOUT = None

class LLMQueryError(RuntimeError):
    """B4 patch 3 (D73 Q47): a sub-call stopped on the output limit or failed; the host recorded the call."""
    def __init__(self, message, responses=None):
        super().__init__(message)
        self.responses = responses

def _post(path, payload, timeout):
    r = requests.post(f"{PROXY}{path}", json=payload, timeout=timeout)
    return r.json()

def _one(path, prompt, model):
    d = _post(path, {"prompt": prompt, "model": model, "depth": DEPTH}, _LLM_TIMEOUT)
    if d.get("error") is not None or "response" not in d:
        raise LLMQueryError(str(d.get("error")))
    return d["response"]

def _many(path, prompts, model):
    d = _post(path, {"prompts": prompts, "model": model, "depth": DEPTH}, _LLM_TIMEOUT)
    if d.get("error") is not None or "responses" not in d:
        raise LLMQueryError(str(d.get("error")))
    errors = d.get("errors") or [None] * len(d["responses"])
    failed = [i for i, e in enumerate(errors) if e is not None]
    if failed:
        raise LLMQueryError(f"{len(failed)} of {len(errors)} prompts failed: "
                            + "; ".join(f"prompt {i}: {errors[i]}" for i in failed), responses=d["responses"])
    return d["responses"]

def llm_query(prompt, model=None):
    return _one("/llm_query", prompt, model)

def llm_query_batched(prompts, model=None):
    return _many("/llm_query_batched", prompts, model)

def rlm_query(prompt, model=None):
    return _one("/rlm_query", prompt, model)

def rlm_query_batched(prompts, model=None):
    return _many("/rlm_query_batched", prompts, model)

'''

_orig = {}


def _patched_exec_script(code, proxy_port, depth=1, custom_tools=None, compaction=False):
    s = _orig["build_exec_script"](code, proxy_port, depth, custom_tools=custom_tools, compaction=compaction)
    a, b = s.find("_LLM_TIMEOUT = 600\n"), s.find("def load_state():")
    if a < 0 or b < a or sha256_text(s[a:b]) != EXEC_BLOCK_SHA256:
        raise SetupError("the package's container script differs from rlms 0.1.3's; patch 3 is not applied")
    return s[:a] + _EXEC_BLOCK + s[b:]


def _patched_handle_batched(self, body: dict) -> dict:
    """The proxy's batched handler (docker_repl.py:133-152) with a per-prompt "errors" list (patch 3)."""
    address = self._resolve_address()
    if not address:
        return {"error": "No LM handler configured"}
    prompts = body.get("prompts", [])
    if not prompts:
        return {"responses": [], "errors": []}
    if _session is not None:
        _session.register_batch(prompts)
    responses = docker_repl.send_lm_request_batched(address, prompts, model=body.get("model"), depth=self.depth)
    results, errors = [], []
    for resp in responses:
        if not resp.success:
            results.append(None)
            errors.append(resp.error)
        else:
            with self.lock:
                self.pending_calls.append(resp.chat_completion)
            results.append(resp.chat_completion.response)
            errors.append(None)
    return {"responses": results, "errors": errors}


def _patched_socket_request(address, data, timeout=None):
    return _orig["socket_request"](address, data, timeout=None)


class _LoopbackHTTPServer(docker_repl.ThreadingHTTPServer):
    def __init__(self, server_address, handler, *a, **k):
        if tuple(server_address) != ("0.0.0.0", 0):
            raise SetupError(f"the package's proxy asked for {server_address}, not ('0.0.0.0', 0); patch 4 is out "
                             "of date")
        for port in range(PROXY_PORTS[0], PROXY_PORTS[1] + 1):
            try:
                super().__init__(("127.0.0.1", port), handler, *a, **k)
                return
            except OSError as e:
                if e.errno != errno.EADDRINUSE:
                    raise
        raise SetupError(f"every proxy port {PROXY_PORTS[0]}-{PROXY_PORTS[1]} is in use")


_EXEC_STUB = ("import sys, linecache\n"
              "_b4_src = sys.stdin.read()\n"
              "__file__ = sys.argv[0] = '/workspace/_exec.py'\n"
              "sys.path[0] = '/workspace'\n"
              "linecache.cache[__file__] = (len(_b4_src), None, _b4_src.splitlines(True), __file__)\n"
              "exec(compile(_b4_src, __file__, 'exec'))\n")


def _execute_code(self, code):
    """Patches 5 and 7: rlms 0.1.3's DockerREPL.execute_code (docker_repl.py:684-731) with the script sent on stdin
    (_EXEC_STUB) instead of written to <workspace>/_exec.py, plus the turn's block count, the session's fatal error
    and Ctrl-C."""
    s = _session
    if s is not None and s.turn > 0:
        with s.lock:
            s.block += 1
    try:
        start = time.perf_counter()
        with self._calls_lock:
            self.pending_calls.clear()
        script = docker_repl._build_exec_script(code, self.proxy_port, self.depth, custom_tools=self.custom_tools,
                                                compaction=self.compaction)
        result = subprocess.run(["docker", "exec", "-i", self.container_id, "python", "-c", _EXEC_STUB],
                                input=script, capture_output=True, text=True)
        with self._calls_lock:
            calls = self.pending_calls.copy()
            self.pending_calls.clear()
        try:
            lines = result.stdout.strip().split("\n")
            data = json.loads(lines[-1]) if lines and lines[-1] else {}
            out = docker_repl.REPLResult(stdout=data.get("stdout", ""), stderr=data.get("stderr", "") + result.stderr,
                                         locals=data.get("locals", {}), execution_time=time.perf_counter() - start,
                                         rlm_calls=calls, final_answer=data.get("final_answer"))
        except json.JSONDecodeError:
            out = docker_repl.REPLResult(stdout=result.stdout, stderr=result.stderr or "Parse error", locals={},
                                         execution_time=time.perf_counter() - start, rlm_calls=calls)
    except KeyboardInterrupt as e:
        if s is not None:
            s.fail(e)
        raise
    if s is not None and s.fatal is not None:
        raise s.fatal
    return out


class _DockerSubprocess:
    """docker_repl's subprocess module (patch 6): the container's "docker run" gets the sandbox network and labels;
    every other call passes unchanged."""

    def __getattr__(self, name):
        return getattr(subprocess, name)

    @staticmethod
    def run(args, *a, **k):
        if isinstance(args, list) and args[:2] == ["docker", "run"]:
            args = _sandbox_run_args(args)
        return subprocess.run(args, *a, **k)


def _sandbox_run_args(args: list) -> list:
    shape = ["docker", "run", "-d", "--rm", "-v", None, "--add-host", "host.docker.internal:host-gateway", None,
             "tail", "-f", "/dev/null"]
    if len(args) != len(shape) or any(w is not None and w != a for w, a in zip(shape, args, strict=True)):
        raise SetupError(f"the package's docker run differs from rlms 0.1.3's ({args[:4]}...); patch 6 is not applied")
    if args[8] != IMAGE_ID:
        raise SetupError(f"the sandbox would run image {args[8][:19]}, not IMAGE_ID")
    s = _session
    run_id = s.ctx.run_id if s is not None else "none"
    return args[:3] + ["--network", NETWORK, "--label", "b4.sandbox=1", "--label", f"b4.pid={os.getpid()}",
                       "--label", f"b4.run={run_id}"] + args[3:]


def _get_client(backend, backend_kwargs):
    s = current_session()
    if backend != "gemini" or dict(backend_kwargs or {}) != {"model_name": MODEL}:
        raise LockError(f"the reference arm runs only {IDENT}, not {backend!r} {backend_kwargs!r}")
    return LockedGemini(s)


def _refuse_client(backend, backend_kwargs):
    raise LockError(f"rlm.clients.get_client({backend!r}): the package's own clients are not used (B4 patch 1)")


def _root_completion(self, prompt, model=None):
    token = _root.set(True)
    try:
        return _orig["lmh_completion"](self, prompt, model)
    finally:
        _root.reset(token)


def _default_answer(self, message_history, lm_handler_):
    s = current_session()
    with s.lock:
        s.forced = True
    return _orig["default_answer"](self, message_history, lm_handler_)


def apply_patches() -> None:
    if _orig:
        return
    if sha256_text(inspect.getsource(docker_repl.DockerREPL.execute_code)) != EXECUTE_CODE_SHA256:
        raise SetupError("DockerREPL.execute_code differs from rlms 0.1.3's; patch 7 is not applied")
    if docker_repl.subprocess is not subprocess:
        raise SetupError("docker_repl's subprocess is not the subprocess module; patch 6 is not applied")
    _orig.update(build_exec_script=docker_repl._build_exec_script, socket_request=comms_utils.socket_request,
                 lmh_completion=lm_handler.LMHandler.completion, default_answer=rlm_core.RLM._default_answer,
                 execute_code=docker_repl.DockerREPL.execute_code, handle_batched=docker_repl.LLMProxyHandler._handle_batched,
                 http_server=docker_repl.ThreadingHTTPServer, get_client=rlm_core.get_client)
    docker_repl.subprocess = _DockerSubprocess()                        # 6
    rlm_core.get_client = _get_client                                   # 1
    rlm_clients.get_client = _refuse_client
    lm_handler.LMHandler.completion = _root_completion
    comms_utils.socket_request = _patched_socket_request                # 2 (+ the container's timeouts in 3)
    docker_repl._build_exec_script = _patched_exec_script               # 3
    docker_repl.LLMProxyHandler._handle_batched = _patched_handle_batched
    docker_repl.ThreadingHTTPServer = _LoopbackHTTPServer               # 4
    rlm_core.RLM._default_answer = _default_answer                      # 5
    docker_repl.DockerREPL.execute_code = _execute_code


apply_patches()


# ---------------------------------------------------------------- traces

class _Store:
    def __init__(self, sink: Path, forms: dict):
        self.blobs, self.forms, self.written = sink / "blobs", forms, set()

    def __call__(self, v):
        if not isinstance(v, str):
            return v
        h = sha256_text(v)
        if h in self.forms:
            return dict(self.forms[h])
        if len(v) < BLOB_MIN:
            return v
        path = self.blobs / f"{h}.txt"
        if h not in self.written and not path.exists():
            scan(v, f"blob {h}")
            self.blobs.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(f".{os.getpid()}.tmp")
            tmp.write_text(v, encoding="utf-8", errors="surrogatepass")
            os.replace(tmp, path)
        self.written.add(h)
        return {"blob": h, "chars": len(v)}


def build_trace(s: Session, trajectory: dict | None, bundle: dict, store: _Store) -> dict:
    roots = [c for c in s.calls if c["call"] in ("root", "forced_final")]
    seq_of_turn = {c["turn"]: c["seq"] for c in roots}
    subs: dict = {}
    for c in s.calls:
        if c["call"] == "sub":
            subs.setdefault((c["turn"], c["block"]), []).append(c["seq"])
    its = []
    for it in (trajectory or {}).get("iterations", []):
        n = it["iteration"]
        forced = n == s.cap + 1                      # _default_answer logs the forced final answer after turn cap
        turn = n
        blocks = []
        for j, cb in enumerate(it["code_blocks"], 1):
            r = cb["result"]
            blocks.append({"block": j, "code": cb["code"], "stdout": store(r.get("stdout")),
                           "stderr": store(r.get("stderr")),
                           "locals": {k: store(v) for k, v in (r.get("locals") or {}).items()},
                           "execution_time": r.get("execution_time"), "final_answer": store(r.get("final_answer")),
                           "sub_calls_returned": len(r.get("rlm_calls") or []),
                           "sub_call_seqs": sorted(subs.get((turn, j), []))})
        its.append({"iteration": n, "kind": "forced_final" if forced else "turn", "timestamp": it.get("timestamp"),
                    "root_call_seq": seq_of_turn.get(turn), "response": it.get("response"),
                    "final_answer": store(it.get("final_answer")), "iteration_time": it.get("iteration_time"),
                    "code_blocks": blocks})
    return {"run_metadata": (trajectory or {}).get("run_metadata"), "iterations": its,
            "calls": s.calls, "context": {"file": bundle["file"], "file_sha256": bundle["file_sha256"],
                                          "context_sha256": bundle["context_sha256"]}}


def _write_json(path: Path, obj, what: str) -> str:
    raw = (json.dumps(obj, ensure_ascii=True, indent=1, allow_nan=False) + "\n").encode("utf-8")
    scan(raw.decode("utf-8"), what)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_bytes(raw)
    os.replace(tmp, path)
    return sha256_bytes(raw)


def adapter_sha256() -> str:
    return sha256_bytes(Path(__file__).read_bytes())


def _tokens(calls: list) -> dict:
    out = {}
    for kind in ("root", "forced_final", "sub"):
        cs = [c for c in calls if c["call"] == kind]
        d = {"calls": len(cs)}
        for k in ("prompt_tokens", "output_tokens", "thinking_tokens"):
            vals = [c[k] for c in cs if isinstance(c.get(k), int)]
            d[k] = sum(vals)
            d[k + "_missing"] = len(cs) - len(vals)
        out[kind] = d
    out["total"] = {k: sum(out[c][k] for c in ("root", "forced_final", "sub"))
                    for k in ("calls", "prompt_tokens", "output_tokens", "thinking_tokens")}
    return out


# ---------------------------------------------------------------- one question

def run_question(ctx: rc.RunContext, question: dict, cap: int, bundle: dict, image: dict, question_set: str,
                 arm: str, answer_key: str) -> dict:
    """Runs one (question, draw) at turn cap `cap` inside rc.run(ctx); writes its trace and its answer record
    (<sink>/answers.jsonl) and returns the answer record. Raises on a fatal or setup error (nothing is written then)."""
    global _session
    if not isinstance(cap, int) or isinstance(cap, bool) or cap < 1:
        raise SetupError(f"cap {cap!r}: a turn cap is an integer from 1")
    if rc.current() is not ctx:
        raise SetupError("run_question runs inside rc.run(ctx) of its own context")
    sink = ctx.sink
    ws = sink / "docker_ws" / f"p{os.getpid()}"     # one per process, so clean_stale knows a killed run's
    ws.mkdir(parents=True, exist_ok=True)
    os.environ["RLM_DOCKER_WORKSPACE_DIR"] = str(ws)
    with _session_guard:
        if _session is not None:
            raise SetupError("one question at a time in a process")
        s = _session = Session(ctx, cap, question["id"], sink)
    logger = RLMLogger()
    t0 = time.time()
    answer, stop, error = "", None, None
    try:
        r = rlm_core.RLM(backend="gemini", backend_kwargs={"model_name": MODEL}, environment="docker",
                         environment_kwargs={"image": image["image_id"]}, max_depth=MAX_DEPTH, max_iterations=cap,
                         logger=logger, verbose=False, compaction=False)
        result = r.completion(bundle["context"], root_prompt=question["question"])
        # Q114: a closing call cut with no text part gives the package's answer None (its _default_answer returns the
        # reply unread); stored as "" (no answer), never as the text "None"
        answer = ("" if result.response is None else result.response if isinstance(result.response, str)
                  else str(result.response))
        stop = "turn_cap" if s.forced else "answer_ready"
    except RootCallError as e:
        # the forced final answer at the cap failing is its own stop reason: with Gemini 3 the package's closing turn
        # (an assistant message last) came back MALFORMED_RESPONSE in the live smoke (design R2)
        stop = "forced_final_failed" if e.record.get("b4", {}).get("call") == "forced_final" else "root_call_failed"
        error = str(e)
    except Exception as e:
        if s.fatal is not None:
            raise s.fatal from None
        if isinstance(e, CancellationError):
            # Ctrl-C anywhere in the package's turn loop (rlm/core/rlm.py:463): the run stops, nothing is stored
            raise KeyboardInterrupt(f"{question['id']} d{ctx.draw}: interrupted; nothing stored") from None
        if isinstance(e, (LockError, rc.RunContextError, KeyLeakError, SetupError)):
            raise
        if not s.calls:
            raise SetupError(f"before the first root turn: {type(e).__name__}: {e}") from e
        stop, error = "error", f"{type(e).__name__}: {e}"
    finally:
        with _session_guard:
            _session = None
    if s.fatal is not None:
        raise s.fatal
    wall = round(time.time() - t0, 3)
    store = _Store(sink, bundle["forms"])
    trace = build_trace(s, logger.get_trajectory(), bundle, store)
    trace.update(answer_key=answer_key, question_id=question["id"], cap=cap, draw=ctx.draw)
    tpath = sink / "traces" / f"{arm}__{question['id']}__d{ctx.draw}.json"
    tsha = _write_json(tpath, trace, f"the trace of {answer_key}")
    roots = [c for c in s.calls if c["call"] == "root"]
    subs = [c for c in s.calls if c["call"] == "sub"]
    rec = {
        "answer_key": answer_key, "question_id": question["id"], "question_set": question_set, "cap": cap,
        "draw": ctx.draw, "model": MODEL, "thinking": ctx.thinking,
        "answer": answer, "status": "ok" if stop in ("answer_ready", "turn_cap") else "failed",
        "stop_reason": stop, "error": error,
        "turns_used": len(roots), "forced_final": s.forced,
        # R2 (16 October): an answer from the closing call at the cap that holds a ```repl block (the package's own
        # parser, rlm/utils/parsing.py:10-15) is kept as the package returned it, and counted by this flag
        "forced_final_has_code": bool(s.forced and answer and find_code_blocks(answer)),
        "calls": {"root": len(roots), "forced_final": sum(c["call"] == "forced_final" for c in s.calls),
                  "sub": len(subs), "sub_failed": sub_failed(subs),
                  "sub_length": sum(c["status"] == "length" for c in subs),
                  # D75 Q48: root and forced_final calls cut by the output limit whose reply was passed on (Q114)
                  "root_length": sum(c["status"] == "length" for c in s.calls if c["call"] != "sub"),
                  "seqs": sorted(c["seq"] for c in s.calls)},
        "tokens": _tokens(s.calls), "wall_s": wall,
        "passages": {"whole_corpus": True, "context_sha256": bundle["context_sha256"], "papers": bundle["papers"]},
        "trace": {"path": str(tpath.relative_to(sink)), "sha256": tsha},
        "context": {"file": bundle["file"], "file_sha256": bundle["file_sha256"],
                    "context_sha256": bundle["context_sha256"]},
        "package": {**PACKAGE, "rlm_kwargs": {"backend": "gemini (LockedGemini)", "environment": "docker",
                                               "max_depth": MAX_DEPTH, "max_iterations": cap, "compaction": False,
                                               "orchestrator": True, "persistent": False}},
        "sandbox": image, "adapter_sha256": adapter_sha256(), "patches": list(PATCHES),
        "lock_sha256": load_lock().sha256,
    }
    _scan_obj(rec, f"the answer record of {answer_key}")
    return rc.append(rec, file="answers.jsonl")
