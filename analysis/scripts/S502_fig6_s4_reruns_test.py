#!/usr/bin/env python3
"""S502 test (plan row S4, Step 1): apply's dry run, its archive-then-remove and every refusal on synthetic sinks in a
temporary folder (S502 selftest), then the committed list read back: its keys give its keys_sha256, it holds 165
attempts (162 structured, owed 108 and Q62 on old code 59 sharing 5, plus 3 Q60), deepseek-r1:70b is not in it
(D100), and every variant's launch command is exp_05 with --resume and --length-stop stop and no port chosen. No model
call; no real sink is read or written.

  uv run python scripts/S502_fig6_s4_reruns_test.py      last line "S502 test: <k> of <k> pass"
"""
from __future__ import annotations

import contextlib
import io
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import S502_fig6_s4_reruns as m  # noqa: E402


def main() -> int:
    results = []

    def check(name, cond):
        results.append(bool(cond))
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ok = m.selftest()
    check(f"selftest on synthetic sinks ({buf.getvalue().count('PASS')} checks)", ok)

    lst = m.load_list()
    keys = [(rid, k, kk["reasons"]) for vv in lst["variants"].values() for rid, r in vv["runs"].items()
            for k, kk in r["keys"].items()]
    reasons = Counter(w for _, _, ws in keys for w in ws)
    struct = [x for x in keys if m.config_of(x[0]).startswith("coder_v2")]
    owed = {(r, k) for r, k, ws in keys if "D80 V1" in ws or "D81" in ws}
    q62 = {(r, k) for r, k, ws in keys if "Q62 old code" in ws}
    q60 = {(m.variant_of(r), m.config_of(r)) for r, k, ws in keys if "Q60" in ws}
    check("committed list: 165 attempts, its keys give its keys_sha256", len(keys) == 165 == lst["n_keys"])
    check("committed list: 162 structured = owed 108 + Q62 old code 59 - 5",
          len(struct) == 162 and len(owed) == 108 and len(q62) == 59 and len(owed & q62) == 5)
    check("committed list: 3 Q60, the expected variants, error_recovery_introspect", q60 == m.EXPECTED_Q60)
    check("committed list: no deepseek-r1:70b attempt (D100)", not any("deepseek" in r for r, _, _ in keys))
    check("committed list: per-variant counts add up to 165",
          sum(vv["attempts"] for vv in lst["variants"].values()) == 165)
    check("committed list: every launch command resumes under --length-stop stop with the affected configs",
          all(vv["launch_command"] == m.launch_command(vv["model"], vv["thinking"], vv["configs"])
              and "--resume --length-stop stop --base-url <BASE_URL>" in vv["launch_command"]
              for vv in lst["variants"].values()))
    check("committed list: owed reasons D80 V1 37 and D81 75 (4 both)",
          reasons["D80 V1"] == 37 and reasons["D81"] == 75
          and sum(1 for _, _, ws in keys if "D80 V1" in ws and "D81" in ws) == 4)
    n = len(results)
    print(f"S502 test: {sum(results)} of {n} pass")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
