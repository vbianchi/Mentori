#!/usr/bin/env python3
"""S603 - tokens and cloud cost of the study's language-model calls, on S520's call ledger (F1, D287: "a new script totals
tokens and cost over the study's stored records, to fill the Methods cost sentence"). It also gives the first and last
call time of the cloud calls and of every run, and how long the machines were busy, for the two other Methods sentences
that wait on it (the rerun span and the API run dates).

THE UNIT IS S520's. A call is one line of a named call log, counted by S520's rule, joined across machines by S520's
8-byte line hash (scripts/S520_llm_calls.py, rules 1 to 8). S603 does not count calls itself: it runs S520's own join
(S520.Book) over S520's frozen inputs (findings/recompute/S520_inputs/, sha256 in its SHA256SUMS), notes for each counted
line hash the S520 row it fell in, and looks the hash up in its own collects, which hold, per call-log line, the same hash
and the token and time fields. A line counts once, where S520 counted it.

D311, Q4 (Valerio, 9 November, "extend"): S603 covers the same calls as S520's joined total. S520's report --frozen
joins the D311 collect (findings/recompute/S520_inputs_d311/s520_laptop_d311.json: 155 laptop files its frozen collects
left unmapped) after the three machines' and gives 1,182,144 calls (was 1,158,418). S603 runs the same join
(S520.build over S520_inputs plus the D311 collect, which S520.check_d311_input holds to D311_RULES and to the frozen
laptop collect), and reads the D311 files' tokens and times from its own D311 collect, frozen in
findings/recompute/S603_inputs_d311/ (all laptop files; plan --d311, collect, freeze). The D311 lines bring T3's Gemini
calls into the cost. Without S520_inputs_d311 the report is the base one of 7 November.

REPRODUCE FIRST (README.md:75-79). `report` writes nothing (exit 2) unless:
  R1  S520's build over its frozen inputs gives the frozen total, 1,158,418 calls (laptop_gates.json total_calls), and
      the calls per model of the committed findings/recompute/S520_llm_calls/summary.json's d311.base_by_model (the
      base by_model before D311), so the calls per provider too. Then (D311) S520's build with the D311 collect joined
      gives the committed summary's total.calls and by_model (1,182,144 on 9 November).
  R2  the line hashes S603 attributes to each S520 row sum to that row's calls, row by row, on the joined build, and
      the run-tier hashes sum to the joined total.
  R3  the line reader S603 ships to the machines (top_fields, value_at and their patterns) is S520's, character for
      character, so a hash means the same line in both.
Then the token join: every counted line of the run tier whose hash is not in S603's collects is counted and named (a
log rewritten after 7 November); none is refused, as tokens are then missing, not wrong.

TOKENS. From each line's top-level fields as the clients write them: Gemini (experiments/runner/gemini_client.py:301-302)
prompt_tokens = promptTokenCount, output_tokens = candidatesTokenCount, thinking_tokens = thoughtsTokenCount,
total_tokens = totalTokenCount; Anthropic (experiments/runner/anthropic_client.py:254-258) prompt_tokens = input_tokens,
output_tokens (thinking included), cache_creation_input_tokens, cache_read_input_tokens; Ollama prompt_tokens and
output_tokens (prompt_eval_count and eval_count). S454's resend lines hold the call in `resend`; S357's in
prompt_eval_count and eval_count. A Gemini line with a prompt count and a total but no output count (no candidatesTokenCount
in the reply's usageMetadata) gets output = total - prompt - thinking; the report prints the sum of these outputs (0 on
the inputs of 7 November: on every such line total = prompt + thinking). A call
with no prompt or no output count but a total (total_tokens or tokens_used) is "total only"; one with none is "no
count" (mostly failed calls that got no reply).

PRICES (USD per million tokens, the provider's paid Standard tier). Thinking bills as output.
  gemini-3-flash-preview  input 0.50, output 3.00, no prompt-size tier: D234 (experiments/README.md:1562, Google's price
                          read 4 Nov); confirmed on https://aistudio.google.com/docs/pricing (redirect of
                          ai.google.dev/gemini-api/docs/pricing), fetched 7 November 2026.
  gemini-2.5-pro          input 1.25 (prompt <= 200k tokens) or 2.50 (> 200k), output 10.00 or 15.00: not in the repo;
                          https://aistudio.google.com/docs/pricing, fetched 7 November 2026.
  claude-haiku-4-5        input 1.00, output 5.00, 5-minute cache write 1.25, cache hit 0.10: not in the repo;
                          https://platform.claude.com/docs/en/about-claude/pricing, fetched 7 November 2026.
  The tier of a Gemini 2.5 Pro call is read from its own prompt_tokens. Google's implicit caching bills cached input at a
  lower price, and the Gemini records keep no cached-token count, so the Gemini cost is at the full input price: an upper
  bound on that part. A total-only call is priced at its model's cost per token over the calls with a split (estimated,
  and reported apart). A no-count call is priced at 0 and counted. Local Ollama calls cost nothing; their tokens are
  reported apart. The repository records no USD to EUR rate, so no EUR value is written.

TIMES. Every client writes `at` = time.strftime("%Y-%m-%dT%H:%M:%S") when the call starts (gemini_client.py:346,
anthropic_client.py:289, ollama_client.py:216, lock_adapter.py:418): the machine's local clock, no zone. collect turns it
into epoch seconds on that machine (time.mktime, the machine's own zone rules), and the end is the start plus wall_s.
Reported: first and last start, in UTC and Europe/Amsterdam; per machine and across the machines, the time with at least
one call in flight (the union of the calls' intervals), and the sum of wall_s. A call counts on the machine whose disk
holds its log (S520's machine column).

MODES.
  plan --machine <m> --out <json>         (laptop) the call logs of S520's frozen input for that machine, copies left out.
  plan --d311 --out <json>                (laptop) the same for S520's D311 collect, each file with its listed size;
      collect refuses a file whose size differs, and writes source "d311", so freeze names it s603_laptop_d311.json.gz:
      freeze --in <it> --dest findings/recompute/S603_inputs_d311.
  collect --machine <m> --files <json> --out <json.gz>   (ON the machine; standard library only; sent by stdin)
      ssh <host> 'python3 - collect --machine studio --files s603_files_studio.json --out s603_studio.json.gz' \
          < scripts/S603_tokens_cost.py
      Opens only the listed files, reads each line as S520 does (bytes, only the wanted top-level keys decoded, no answer
      text), and writes per file a packed record per line: hash, the token counts, start, wall_s.
  freeze --in <collects> --dest findings/recompute/S603_inputs   (once) copies them and writes SHA256SUMS.
  report [--out-dir findings/recompute/S603_tokens_cost]          the one command for the numbers; reads tracked files only.
"""
import argparse
import base64
import gzip
import hashlib
import json
import os
import re
import socket
import struct
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone

SCHEMA = 1
REC = struct.Struct("<8s6iII")       # hash, prompt, output, thinking, total, cache_write, cache_read, start, wall (0.1 s)
NONE_I = -1
NONE_U = 0xFFFFFFFF
TOKEN_KEYS = (b"prompt_tokens", b"output_tokens", b"thinking_tokens", b"total_tokens", b"tokens_used",
              b"cache_creation_input_tokens", b"cache_read_input_tokens", b"prompt_eval_count", b"eval_count",
              b"at", b"t", b"wall_s", b"latency_s")

# ---------------------------------------------------------------------------------------------------------------
# S520's line reader, copied so collect runs with the standard library alone; report's gate R3 holds it equal to S520's.
# ---------------------------------------------------------------------------------------------------------------
STRING = re.compile(rb'"[^"\\]*(?:\\.[^"\\]*)*"', re.S)
TOKEN = re.compile(rb'"[^"\\]*(?:\\.[^"\\]*)*"(\s*:)?|[\[{\]}]', re.S)
SCALAR = re.compile(rb"\s*(-?\d+(?:\.\d+)?|true|false|null)")


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


def line_hash(line):
    return hashlib.blake2b(line, digest_size=8).digest()


# ---------------------------------------------------------------------------------------------------------------
# collect (on a machine)
# ---------------------------------------------------------------------------------------------------------------
def _int(v):
    return v if isinstance(v, int) and not isinstance(v, bool) and 0 <= v < 2 ** 31 else None


def _epoch(v):
    """Epoch seconds of a start time: a local-clock 'YYYY-MM-DDTHH:MM:SS' read in this machine's zone; a string with an
    offset or Z by it; a number as epoch seconds."""
    if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 1e9:
        return int(v)
    if not isinstance(v, str) or len(v) < 19:
        return None
    try:
        if len(v) > 19 and (v[19:].startswith(("+", "-", "Z")) or "+" in v[19:]):
            return int(datetime.fromisoformat(v.replace("Z", "+00:00")).timestamp())
        return int(time.mktime(time.strptime(v[:19], "%Y-%m-%dT%H:%M:%S")))
    except (ValueError, OverflowError):
        return None


def tokens_of(f):
    """(prompt, output, thinking, total, cache_write, cache_read, start, wall_s) of one line's decoded fields."""
    p = _int(f.get(b"prompt_tokens"))
    if p is None:
        p = _int(f.get(b"prompt_eval_count"))
    o = _int(f.get(b"output_tokens"))
    if o is None:
        o = _int(f.get(b"eval_count"))
    tot = _int(f.get(b"total_tokens"))
    if tot is None:
        tot = _int(f.get(b"tokens_used"))
    w = f.get(b"wall_s")
    if not isinstance(w, (int, float)) or isinstance(w, bool):
        w = f.get(b"latency_s")
    w = w if isinstance(w, (int, float)) and not isinstance(w, bool) and w >= 0 else None
    start = _epoch(f.get(b"at"))
    if start is None:
        start = _epoch(f.get(b"t"))
    return (p, o, _int(f.get(b"thinking_tokens")), tot, _int(f.get(b"cache_creation_input_tokens")),
            _int(f.get(b"cache_read_input_tokens")), start, w)


def pack(h, t):
    p, o, th, tot, cw, cr, start, w = t
    n = lambda x: NONE_I if x is None else x          # noqa: E731
    return REC.pack(h, n(p), n(o), n(th), n(tot), n(cw), n(cr), NONE_U if start is None else start,
                    NONE_U if w is None else min(int(round(w * 10)), NONE_U - 1))


def scan_file(path, scan_kind):
    """Every line S520's scan_calls would count, as packed records, in file order."""
    nested = (b"resend",) if scan_kind == "resend" else ()
    out, lines, skipped = bytearray(), 0, 0
    with open(path, "rb") as fh:
        for raw in fh:
            line = raw.rstrip(b"\r\n")
            if not line:
                continue
            try:
                f = top_fields(line, TOKEN_KEYS, nested)
                if not line.endswith(b"}"):
                    raise ValueError("no close")
                if scan_kind == "resend":
                    f = top_fields(f.get(b"resend") or b"{}", TOKEN_KEYS)
            except ValueError:
                skipped += 1
                continue
            out.extend(pack(line_hash(line), tokens_of(f)))
            lines += 1
    return out, lines, skipped


def collect(machine, files_path, out_path):
    try:
        os.nice(10)                       # the machines are running jobs; this read yields to them
    except (OSError, AttributeError):
        pass
    with open(os.path.expanduser(files_path)) as fh:
        wanted = json.load(fh)
    if wanted.get("machine") != machine:
        print("REFUSED: the file list is for %s" % wanted.get("machine"))
        sys.exit(2)
    home = os.path.expanduser("~")
    now = time.time()
    doc = {"schema": SCHEMA, "machine": machine, "source": wanted.get("source"), "host": socket.gethostname(),
           "zone": "%s %s" % (time.strftime("%Z"), time.strftime("%z")),
           "started_utc": datetime.fromtimestamp(now, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "files": []}
    for e in wanted["files"]:
        path = os.path.join(home, "projects", e["clone"], "findings", e["path"])
        entry = {"clone": e["clone"], "path": e["path"]}
        if "size" in e:
            try:
                size = os.stat(path).st_size
            except OSError:
                size = None
            if size is not None and size != e["size"]:
                print("REFUSED: %s holds %d bytes, S520's collect listed %d" % (e["path"], size, e["size"]))
                sys.exit(2)
        try:
            rec, lines, skipped = scan_file(path, e["scan_kind"])
            entry.update(lines=lines, skipped=skipped, rec=base64.b64encode(bytes(rec)).decode("ascii"))
        except OSError as err:
            entry.update(error=type(err).__name__)
        doc["files"].append(entry)
    doc["ended_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out_path = os.path.expanduser(out_path)
    tmp = out_path + ".tmp"
    with gzip.open(tmp, "wt", encoding="ascii") as fh:
        json.dump(doc, fh)
    os.replace(tmp, out_path)
    print("collected %s: %d files, %d lines, %d missing" % (machine, len(doc["files"]),
                                                            sum(f.get("lines", 0) for f in doc["files"]),
                                                            sum(1 for f in doc["files"] if "error" in f)))


# ---------------------------------------------------------------------------------------------------------------
# Everything below runs on the laptop, in the repository.
# ---------------------------------------------------------------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S520_FROZEN = "findings/recompute/S520_inputs"
S520_SUMMARY = "findings/recompute/S520_llm_calls/summary.json"
FROZEN_DIR = "findings/recompute/S603_inputs"
S520_D311 = "findings/recompute/S520_inputs_d311"        # S520.D311_DIR
FROZEN_DIR_D311 = "findings/recompute/S603_inputs_d311"
DEFAULT_OUT = "findings/recompute/S603_tokens_cost"
SUMS = "SHA256SUMS"
TZ_NAME = "Europe/Amsterdam"

PRICES = {   # USD per million tokens; see the module docstring for the source of each row
    "gemini-3-flash-preview": {"provider": "Google", "input": 0.50, "output": 3.00,
                               "source": "D234 (experiments/README.md:1562); aistudio.google.com/docs/pricing, 7 Nov 2026"},
    "gemini-2.5-pro": {"provider": "Google", "input": 1.25, "output": 10.00, "tier_above": 200000,
                       "input_above": 2.50, "output_above": 15.00,
                       "source": "aistudio.google.com/docs/pricing, fetched 7 Nov 2026"},
    "claude-haiku-4-5": {"provider": "Anthropic", "input": 1.00, "output": 5.00, "cache_write": 1.25, "cache_read": 0.10,
                         "source": "platform.claude.com/docs/en/about-claude/pricing, fetched 7 Nov 2026"},
}


def s520():
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import S520_llm_calls as S520
    return S520


def provider_of(model):
    m = str(model or "")
    if m in PRICES:
        return PRICES[m]["provider"]
    if m.startswith("gemini"):
        return "Google"
    if m.startswith("claude"):
        return "Anthropic"
    return "local (Ollama)" if m and m != "?" else "unknown"


def sha256_path(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def frozen_s520(S520):
    files, sums = S520.read_frozen(os.path.join(ROOT, S520_FROZEN))
    with open(files.pop(S520.LAPTOP_GATES)) as fh:
        doc = json.load(fh)
    inputs = []
    for name in doc["collect_order"]:
        with open(files[name]) as fh:
            inp = json.load(fh)
        if inp.get("table_sha256") != S520.table_sha():
            print("REFUSED: %s was collected with other tables than S520's" % name)
            sys.exit(2)
        inputs.append(inp)
    return inputs, doc, sums


def frozen_d311(S520, sums520):
    """S520's frozen D311 collect (None when the folder is absent), held to its SHA256SUMS and to S520's D311 rules."""
    folder = os.path.join(ROOT, S520_D311)
    if not os.path.isdir(folder):
        return None, {}
    files, sums = S520.read_frozen(folder)
    with open(files[S520.D311_INPUT]) as fh:
        extra = json.load(fh)
    S520.check_d311_input(extra, sums520["s520_laptop.json"])
    return extra, sums


def plan(machine, out, d311=False):
    S520 = s520()
    inputs, _, sums520 = frozen_s520(S520)
    if d311:
        inp, _ = frozen_d311(S520, sums520)
        if inp is None:
            print("REFUSED: %s is absent" % S520_D311)
            sys.exit(2)
        machine = inp["machine"]
    else:
        inp = next(i for i in inputs if i["machine"] == machine)
    files = [dict({"clone": f["clone"], "path": f["path"], "scan_kind": f["scan_kind"]},
                  **({"size": f["size"]} if d311 else {})) for f in inp["files"] if f["kind"] != "copy"]
    with open(out, "w") as fh:
        json.dump(dict({"machine": machine, "files": files}, **({"source": "d311"} if d311 else {})), fh)
    print("%s%s: %d call logs (copies left out)" % (machine, " (D311)" if d311 else "", len(files)))


def freeze(in_paths, dest):
    if os.path.exists(dest):
        print("REFUSED: %s exists: the collects are frozen once" % dest)
        sys.exit(2)
    os.makedirs(dest)
    names = []
    for p in in_paths:
        with gzip.open(p, "rt") as fh:
            d = json.load(fh)
        name = "s603_%s%s.json.gz" % (d["machine"], "_" + d["source"] if d.get("source") else "")
        with open(p, "rb") as src, open(os.path.join(dest, name), "wb") as out:
            out.write(src.read())
        names.append(name)
    with open(os.path.join(dest, SUMS), "w") as fh:
        for name in sorted(names):
            fh.write("%s  %s\n" % (sha256_path(os.path.join(dest, name)), name))
    print("froze %s in %s" % (", ".join(sorted(names)), dest))


def read_collects(folder, tokens=None, meta=None):
    """Adds a frozen collect folder's records to tokens (a hash already held keeps its first record: the same line)."""
    S520 = s520()
    files, sums = S520.read_frozen(folder)
    tokens = {} if tokens is None else tokens
    meta = {} if meta is None else meta
    for name in sorted(files):
        with gzip.open(files[name], "rt") as fh:
            doc = json.load(fh)
        key = doc["machine"] + (" (%s)" % doc["source"].upper() if doc.get("source") else "")
        meta[key] = {k: doc[k] for k in ("host", "zone", "started_utc", "ended_utc")}
        meta[key]["files_missing"] = [f["clone"] + "/" + f["path"] for f in doc["files"] if "error" in f]
        for f in doc["files"]:
            raw = base64.b64decode(f.get("rec", ""))
            for i in range(0, len(raw), REC.size):
                r = REC.unpack_from(raw, i)
                tokens.setdefault(r[0], r[1:])
    return tokens, meta, sums


class RecordingRows(defaultdict):
    """S520.Book's row table, noting the last key it was asked for: Book.add asks once per counted group."""
    last = None

    def __getitem__(self, k):
        self.last = k
        return super().__getitem__(k)


def attribute(S520, inputs, changed):
    """S520's join, as S520.build runs it, with each counted line hash noted against its row key."""
    order = []
    for inp in inputs:
        rank = S520.MACHINE_ORDER.index(inp["machine"])
        for f in inp["files"]:
            tier = S520.classify(f["clone"], f["path"], f["kind"])["tier"]
            order.append((S520.TIER_RANK[tier], rank, f["clone"], f["path"], inp["machine"], f))
    order.sort(key=lambda t: t[:4])
    book = S520.Book(changed, S520.s6_rejudged(inputs))
    book.rows = RecordingRows(book.rows.default_factory)
    hashes = defaultdict(bytearray)
    for *_, machine, f in order:
        for g in f["groups"]:
            raw = base64.b64decode(g["h"])
            new, local = bytearray(), set()
            for i in range(0, len(raw), 8):
                h = raw[i:i + 8]
                if h in book.seen or h in local:
                    continue
                local.add(h)
                new.extend(h)
            book.rows.last = None
            book.add(machine, dict(f, groups=[g]))
            if book.rows.last is not None and new:
                hashes[book.rows.last].extend(new)
    return book, hashes


def call_cost(model, p, o, th, cw, cr):
    """USD of one call with a split; None when the model has no price (a local model)."""
    pr = PRICES.get(model)
    if pr is None:
        return None
    out = (o or 0) + (th or 0)
    above = pr.get("tier_above") is not None and (p or 0) > pr["tier_above"]
    pin = pr["input_above"] if above else pr["input"]
    pout = pr["output_above"] if above else pr["output"]
    usd = (p or 0) * pin + out * pout + (cw or 0) * pr.get("cache_write", 0) + (cr or 0) * pr.get("cache_read", 0)
    return usd / 1e6


def new_stat():
    return {"calls": 0, "split": 0, "output_from_total": 0, "output_from_total_tokens": 0, "total_only": 0, "no_count": 0, "not_in_collects": 0, "prompt": 0, "output": 0,
            "thinking": 0, "total_only_tokens": 0, "cache_write": 0, "cache_read": 0, "total_gap_calls": 0,
            "total_gap_tokens": 0, "above_200k_calls": 0, "usd_split": 0.0, "usd_estimated": 0.0}


def union_seconds(intervals):
    total, end = 0, None
    for s, e in sorted(intervals):
        if end is None or s > end:
            total += e - s
            end = e
        elif e > end:
            total += e - end
            end = e
    return total


def fmt_t(epoch):
    from zoneinfo import ZoneInfo
    if epoch is None:
        return None
    d = datetime.fromtimestamp(epoch, timezone.utc)
    return {"utc": d.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "amsterdam": d.astimezone(ZoneInfo(TZ_NAME)).strftime("%Y-%m-%d %H:%M %Z")}


def tally(rows_hashes, tokens):
    """Per (tier, provider, model): calls, tokens and cost; and the times."""
    stats = defaultdict(new_stat)
    times = defaultdict(list)            # (tier, machine, provider) -> [(start, end)]
    for key, hs in rows_hashes.items():
        e, plan_row, role, model, machine, tier, box = key
        prov = provider_of(model)
        st = stats[(tier, prov, model)]
        for i in range(0, len(hs), 8):
            st["calls"] += 1
            t = tokens.get(bytes(hs[i:i + 8]))
            if t is None:
                st["not_in_collects"] += 1
                continue
            p, o, th, tot, cw, cr, start, wall = [None if x in (NONE_I, NONE_U) else x for x in t]
            if start is not None:
                times[(tier, machine, prov)].append((start, start + (wall or 0) / 10.0))
            if p is not None and o is None and tot is not None and tot >= p + (th or 0):
                o = tot - p - (th or 0)          # no candidatesTokenCount in the reply
                st["output_from_total"] += 1
                st["output_from_total_tokens"] += o
            if p is not None and o is not None:
                st["split"] += 1
                st["prompt"] += p
                st["output"] += o
                st["thinking"] += th or 0
                st["cache_write"] += cw or 0
                st["cache_read"] += cr or 0
                if tot is not None and tot > p + o + (th or 0):
                    st["total_gap_calls"] += 1
                    st["total_gap_tokens"] += tot - p - o - (th or 0)
                pr = PRICES.get(model, {})
                if pr.get("tier_above") and p > pr["tier_above"]:
                    st["above_200k_calls"] += 1
                c = call_cost(model, p, o, th, cw, cr)
                if c is not None:
                    st["usd_split"] += c
            elif tot is not None:
                st["total_only"] += 1
                st["total_only_tokens"] += tot
            else:
                st["no_count"] += 1
    for (tier, prov, model), st in stats.items():
        if model in PRICES and st["total_only"]:
            per_token = st["usd_split"] / max(st["prompt"] + st["output"] + st["thinking"], 1)
            st["usd_estimated"] = st["total_only_tokens"] * per_token
    return stats, times


def time_summary(times, tiers):
    sel = {k: v for k, v in times.items() if k[0] in tiers}

    def span(iv):
        if not iv:
            return None
        s, e = min(x[0] for x in iv), max(x[1] for x in iv)
        return {"first_start": fmt_t(s), "last_end": fmt_t(int(e)), "span_days": round((e - s) / 86400, 2),
                "busy_hours": round(union_seconds(iv) / 3600, 1), "wall_s_sum_hours": round(sum(b - a for a, b in iv) / 3600, 1),
                "calls_with_time": len(iv)}

    out = {"all": span([x for v in sel.values() for x in v]), "by_machine": {}, "by_provider": {}}
    for m in sorted({k[1] for k in sel}):
        out["by_machine"][m] = span([x for k, v in sel.items() if k[1] == m for x in v])
    for p in sorted({k[2] for k in sel}):
        out["by_provider"][p] = span([x for k, v in sel.items() if k[2] == p for x in v])
    cloud = [x for k, v in sel.items() if k[2] in ("Google", "Anthropic") for x in v]
    out["cloud"] = span(cloud)
    return out


def roll(stats, tiers, by):
    out = defaultdict(new_stat)
    for k, st in stats.items():
        if k[0] not in tiers:
            continue
        o = out[by(k)]
        for f, v in st.items():
            o[f] += v
    return dict(sorted(out.items(), key=lambda kv: -kv[1]["calls"]))


def n(v):
    return "{:,}".format(v) if isinstance(v, int) else str(v)


def usd(v):
    return "%.2f" % v


def md_table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    return out + ["| " + " | ".join(n(c) for c in r) + " |" for r in rows]


def report(out_dir):
    S520 = s520()
    me = os.path.abspath(__file__)
    g = []

    def gate(name, got, want, source):
        g.append({"gate": name, "got": got, "want": want, "source": source, "pass": got == want})

    import inspect
    src520 = "".join(inspect.getsource(getattr(S520, k)) for k in ("top_fields", "value_at", "line_hash"))
    srcme = "".join(inspect.getsource(globals()[k]) for k in ("top_fields", "value_at", "line_hash"))
    pats = all(getattr(S520, k).pattern == globals()[k].pattern for k in ("STRING", "TOKEN", "SCALAR"))
    gate("R3 line reader equals S520's", src520 == srcme and pats, True, "scripts/S520_llm_calls.py top_fields, value_at")

    inputs, doc, sums520 = frozen_s520(S520)
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import S512_s6_rejudge_v25 as S512
    changed = S512.changed_ids()
    built = S520.build(inputs, changed)["summary"]
    gate("R1 S520 total over its frozen inputs", built["total"]["calls"], doc["total_calls"],
         S520_FROZEN + "/laptop_gates.json total_calls")
    with open(os.path.join(ROOT, S520_SUMMARY)) as fh:
        committed = json.load(fh)
    # D311: the committed summary joins S520_inputs_d311 too; S603 reads S520_inputs alone, which d311.base_by_model holds
    want_by_model = (committed.get("d311") or {}).get("base_by_model") or {
        k: v["calls"] for k, v in committed["by_model"].items()}
    gate("R1 S520 calls per model", {k: v["calls"] for k, v in built["by_model"].items()}, want_by_model,
         S520_SUMMARY + (" d311.base_by_model" if committed.get("d311") else " by_model"))
    extra, sums_d311 = frozen_d311(S520, sums520)
    ledger, want_total, total_src = inputs, doc["total_calls"], "laptop_gates.json total_calls"
    if extra is not None:          # D311, Q4: the same join S520's report --frozen runs
        joined = S520.build(inputs + [extra], changed)["summary"]
        gate("R1 S520 total with the D311 collect joined", joined["total"]["calls"], committed["total"]["calls"],
             S520_SUMMARY + " total.calls")
        gate("R1 S520 calls per model, D311 joined", {k: v["calls"] for k, v in joined["by_model"].items()},
             {k: v["calls"] for k, v in committed["by_model"].items()}, S520_SUMMARY + " by_model")
        ledger, want_total, total_src = inputs + [extra], committed["total"]["calls"], S520_SUMMARY + " total.calls"
        built = joined
    book, hashes = attribute(S520, ledger, changed)
    rows = {k: sum(r["status"].values()) for k, r in book.rows.items()}
    mine = {k: len(v) // 8 for k, v in hashes.items()}
    gate("R2 hashes per S520 row equal its calls", mine == {k: v for k, v in rows.items() if v}, True, "S520.Book rows")
    run_mine = sum(v for k, v in mine.items() if k[5] == "run")
    gate("R2 run-tier hashes equal the total", run_mine, want_total, total_src)
    for r in g:
        print("  %s %s: %s" % ("PASS" if r["pass"] else "FAIL", r["gate"],
                               r["got"] if not isinstance(r["got"], dict) else "%d models" % len(r["got"])))
    if not all(r["pass"] for r in g):
        print("REFUSED: %d gates differ; nothing written" % sum(1 for r in g if not r["pass"]))
        sys.exit(2)
    per_provider = Counter()
    for k, v in built["by_model"].items():
        per_provider[provider_of(k)] += v["calls"]
    print("Reproduced S520: %d calls; per provider %s" % (built["total"]["calls"], dict(per_provider)))

    tokens, meta, sums603 = read_collects(os.path.join(ROOT, FROZEN_DIR))
    if extra is not None:
        _, _, sums603_d311 = read_collects(os.path.join(ROOT, FROZEN_DIR_D311), tokens, meta)
        sums520 = dict(sums520, **{"S520_inputs_d311/" + k: v for k, v in sums_d311.items()})
        sums603 = dict(sums603, **{"S603_inputs_d311/" + k: v for k, v in sums603_d311.items()})
    stats, times = tally(hashes, tokens)
    RUN = ("run",)
    ALL = ("run", "dropped", "check", "smoke", "unmapped")
    unm = committed.get("unmapped")
    res = {
        "provenance": {"script": "scripts/S603_tokens_cost.py", "script_sha256": sha256_path(me),
                       "command": "uv run --frozen python scripts/S603_tokens_cost.py report",
                       "s520_inputs_sha256": sums520, "s603_inputs_sha256": sums603, "collects": meta,
                       "d311": extra is not None},
        "s520_total": built["total"]["calls"],
        "s520_unmapped_files": len(unm) if isinstance(unm, (list, dict)) else None,
        "gates": g, "s520_calls_per_provider": dict(per_provider), "prices_usd_per_million": PRICES,
        "eur": "not converted: the repository records no USD to EUR rate (Valerio's, from the invoices)",
        "run": {"by_model": {"%s|%s" % k: v for k, v in roll(stats, RUN, lambda k: (k[1], k[2])).items()},
                "by_provider": roll(stats, RUN, lambda k: k[1])},
        "all_tiers": {"by_model": {"%s|%s" % k: v for k, v in roll(stats, ALL, lambda k: (k[1], k[2])).items()},
                      "by_provider": roll(stats, ALL, lambda k: k[1]),
                      "by_tier": roll(stats, ALL, lambda k: k[0])},
        "times_run": time_summary(times, RUN), "times_all_tiers": time_summary(times, ALL),
    }
    write(res, out_dir)
    rp = res["run"]["by_provider"]
    for p, st in rp.items():
        print("%-15s calls %9d  prompt %13d  output %12d  thinking %12d  total-only %11d  usd %.2f (+%.2f est.)" % (
            p, st["calls"], st["prompt"], st["output"], st["thinking"], st["total_only_tokens"], st["usd_split"],
            st["usd_estimated"]))


def write(res, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "summary.json"), "w") as fh:
        json.dump(res, fh, indent=1, sort_keys=True)
        fh.write("\n")
    prov = res["provenance"]
    d311 = prov.get("d311")
    L = ["<!-- provenance: %s sha256 %s, inputs %s (S520) and %s (S603), HEAD not stamped, written not stamped -->" % (
        prov["script"], prov["script_sha256"][:16],
        S520_FROZEN + (" + " + S520_D311 if d311 else ""), FROZEN_DIR + (" + " + FROZEN_DIR_D311 if d311 else "")),
        "# Tokens and cloud cost of the study's language-model calls", "",
        "One call is one line of a named call log, counted by S520's rule on S520's frozen inputs of 7 November%s; each "
        "counted line's tokens are read from S603's collects by the same line hash. Command: `%s`." % (
            " joined with the D311 collect of 9 November (D311, Q4)" if d311 else "", prov["command"]), "",
        "Collects read: " + "; ".join("%s %s to %s (%s)" % (m, v["started_utc"], v["ended_utc"], v["zone"])
                                       for m, v in sorted(prov["collects"].items())) + ".", "",
        "## Reproduced first", ""]
    L += md_table(["Gate", "Pass"], [[r["gate"], "yes" if r["pass"] else "NO"] for r in res["gates"]])
    L += ["", "S520's calls per provider (run tier): " + ", ".join("%s %s" % (k, n(v)) for k, v in
                                                                   sorted(res["s520_calls_per_provider"].items())) + ".", ""]

    def tok_rows(by):
        out = []
        for k, st in by.items():
            out.append([k.replace("|", ", ") if isinstance(k, str) else k, st["calls"], st["split"], st["total_only"],
                        st["no_count"] + st["not_in_collects"], st["prompt"], st["output"], st["thinking"],
                        st["total_only_tokens"], st["cache_write"] + st["cache_read"]])
        return out

    head = ["Provider, model", "Calls", "With prompt and output", "Total only", "No count", "Prompt tokens",
            "Output tokens", "Thinking tokens", "Tokens of total-only calls", "Anthropic cache tokens"]
    L += ["## Tokens, run tier (the %s calls)" % n(res["s520_total"]), ""] + md_table(head, tok_rows(res["run"]["by_model"]))
    L += [""] + md_table(["Provider"] + head[1:], tok_rows(res["run"]["by_provider"]))
    L += ["", "No count = no token field on the line (or the line not in the collects, %s calls of the run tier)." %
          n(sum(st["not_in_collects"] for st in res["run"]["by_provider"].values())), "",
          "Of the calls with prompt and output, %s Gemini calls record no output_tokens (no candidatesTokenCount in the "
          "reply) but a total_tokens, so output = total - prompt - thinking, %s tokens over all of them, "
          "exact, not estimated." % (n(sum(st["output_from_total"] for st in res["run"]["by_provider"].values())),
                                     n(sum(st["output_from_total_tokens"] for st in res["run"]["by_provider"].values()))), "",
          "Gemini: output tokens exclude thinking (candidatesTokenCount); thinking is thoughtsTokenCount. Calls whose "
          "totalTokenCount exceeds prompt + output + thinking: %s, by %s tokens in all (not priced)." % (
              n(sum(st["total_gap_calls"] for st in res["run"]["by_provider"].values())),
              n(sum(st["total_gap_tokens"] for st in res["run"]["by_provider"].values()))), ""]

    def cost_rows(by):
        out = []
        for k, st in by.items():
            if k.split("|")[-1] not in PRICES and k not in ("Google", "Anthropic"):
                continue
            tot = st["usd_split"] + st["usd_estimated"]
            out.append([k.replace("|", ", "), usd(st["usd_split"]), usd(st["usd_estimated"]), usd(tot),
                        "%.1f%%" % (100 * st["usd_estimated"] / tot) if tot else "0%", st["above_200k_calls"]])
        return out

    ch = ["Provider, model", "USD from split counts", "USD estimated (total only)", "USD", "Estimated share",
          "Calls with prompt > 200k"]
    run_cloud = sum(st["usd_split"] + st["usd_estimated"] for k, st in res["run"]["by_provider"].items()
                    if k in ("Google", "Anthropic"))
    run_est = sum(st["usd_estimated"] for k, st in res["run"]["by_provider"].items() if k in ("Google", "Anthropic"))
    all_cloud = sum(st["usd_split"] + st["usd_estimated"] for k, st in res["all_tiers"]["by_provider"].items()
                    if k in ("Google", "Anthropic"))
    L += ["## Cloud cost, USD", "", "Run tier:", ""] + md_table(ch, cost_rows(res["run"]["by_model"])) + [""]
    L += md_table(ch, cost_rows(res["run"]["by_provider"]))
    L += ["", "Run tier, cloud: USD %s, of which USD %s (%.1f%%) estimated from total-only calls." % (
        usd(run_cloud), usd(run_est), 100 * run_est / run_cloud if run_cloud else 0), "",
        "Every tier S520 reads (run, dropped by decision, checks, smokes; copies excluded), what an invoice would also "
        "hold:", ""] + md_table(ch, cost_rows(res["all_tiers"]["by_provider"]))
    L += ["", "All tiers, cloud: USD %s." % usd(all_cloud), "",
          "Prices (USD per million tokens, thinking as output): " + "; ".join(
              "%s input %s, output %s%s (%s)" % (m, p["input"], p["output"],
                                                 ", above %s prompt tokens %s and %s" % (n(p["tier_above"]), p["input_above"], p["output_above"])
                                                 if p.get("tier_above") else "", p["source"]) for m, p in PRICES.items()) + ".",
          "", "Not in these costs: Google's implicit-cache discount (the Gemini records hold no cached-token count, so "
          "Gemini input is at the full price, an upper bound); calls outside S520's ledger (April and pre-lock work, the "
          "%s unmapped call-log files, Gemini countTokens); taxes and any free-tier credit. EUR: %s." % (
              n(res["s520_unmapped_files"]), res["eur"]), ""]

    def time_rows(t):
        rows = []
        for label, s in [("all machines", t["all"])] + list(t["by_machine"].items()) + \
                [("cloud calls (Google and Anthropic)", t["cloud"])] + list(t["by_provider"].items()):
            if s:
                rows.append([label, s["first_start"]["amsterdam"], s["last_end"]["amsterdam"], s["span_days"],
                             s["busy_hours"], s["wall_s_sum_hours"], s["calls_with_time"]])
        return rows

    th = ["Calls", "First start (Amsterdam)", "Last end (Amsterdam)", "Span (days)",
          "Hours with a call in flight", "Sum of call wall time (hours)", "Calls with a time"]
    L += ["## When the calls ran, run tier", ""] + md_table(th, time_rows(res["times_run"]))
    L += ["", "## When the calls ran, every tier", ""] + md_table(th, time_rows(res["times_all_tiers"]))
    L += ["", "Start = the record's `at` (the machine's local clock when the call starts), end = start + wall_s. A "
          "call counts on the machine whose disk holds its log. Hours with a call in flight = the union of the calls' "
          "intervals; the sum of wall time counts parallel calls each."]
    with open(os.path.join(out_dir, "summary.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")


def main():
    ap = argparse.ArgumentParser(description="Tokens and cloud cost on S520's call ledger.")
    sub = ap.add_subparsers(dest="mode")
    p = sub.add_parser("plan")
    p.add_argument("--machine")
    p.add_argument("--d311", action="store_true", help="S520's D311 collect (laptop) instead of a machine's")
    p.add_argument("--out", required=True)
    c = sub.add_parser("collect")
    c.add_argument("--machine", required=True)
    c.add_argument("--files", required=True)
    c.add_argument("--out", required=True)
    z = sub.add_parser("freeze")
    z.add_argument("--in", dest="inputs", nargs="+", required=True)
    z.add_argument("--dest", default=os.path.join(ROOT, FROZEN_DIR))
    r = sub.add_parser("report")
    r.add_argument("--out-dir", default=os.path.join(ROOT, DEFAULT_OUT))
    a = ap.parse_args()
    if a.mode == "plan":
        if not a.d311 and not a.machine:
            ap.error("plan needs --machine or --d311")
        plan(a.machine, a.out, a.d311)
    elif a.mode == "collect":
        collect(a.machine, a.files, a.out)
    elif a.mode == "freeze":
        freeze(a.inputs, a.dest)
    elif a.mode == "report":
        report(a.out_dir)
    else:
        ap.error("plan, collect, freeze or report")


if __name__ == "__main__":
    main()
