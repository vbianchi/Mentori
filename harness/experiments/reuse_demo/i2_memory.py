"""Free memory, as the I2 run's memory rule reads it (D160 (14), Q-I2e O-a: the answers are made on the laptop beside K1,
one process at a time, only while 2 GB stay free).

    uv run --no-sync python experiments/reuse_demo/i2_memory.py                 # prints free GB; exit 0
    uv run --no-sync python experiments/reuse_demo/i2_memory.py --floor-gb 2    # exit 3 when under the floor

FREE MEMORY. On macOS, what vm_stat reports as free, inactive, speculative and purgeable pages, times the page size:
memory a new process can take without paging out anything in use. This is the reading G4's launcher uses
(findings/recompute/G4_runs/g4_lib.sh avail_gb), so the two rules measure the same thing. On Linux (a reader's
machine), MemAvailable of /proc/meminfo. Anywhere else, or when neither can be read, the reading is None and the rule
refuses (unknown is not free).

Sampler. Sampler(interval_s) reads free memory in a thread until stopped and keeps the lowest reading and when it was
seen; the generation driver runs one for its whole life and writes the lowest reading into its record, which is how
the smoke shows whether 2 GB stayed free while an answer ran.

Standard library only.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

GB = 1024 ** 3
FLOOR_GB = 2.0                 # D160 (14): the floor, in GiB (vm_stat pages x page size / 2^30, as g4_lib.sh)
EXIT_UNDER = 3                 # the CLI's exit code under the floor (or unknown)
VM_KEYS = ("Pages free", "Pages inactive", "Pages speculative", "Pages purgeable")


def parse_vm_stat(text: str) -> float | None:
    """Free GB from vm_stat's output, None when a needed line is missing."""
    m = re.search(r"page size of (\d+) bytes", text)
    if not m:
        return None
    pages = {}
    for line in text.splitlines():
        k, _, v = line.partition(":")
        if k.strip() in VM_KEYS:
            try:
                pages[k.strip()] = int(v.strip().rstrip("."))
            except ValueError:
                return None
    if set(pages) != set(VM_KEYS):
        return None
    return sum(pages.values()) * int(m.group(1)) / GB


def parse_meminfo(text: str) -> float | None:
    m = re.search(r"^MemAvailable:\s+(\d+)\s+kB", text, re.M)
    return int(m.group(1)) * 1024 / GB if m else None


def free_gb(runner=subprocess.run, meminfo: Path = Path("/proc/meminfo")) -> float | None:
    """Free memory in GB now (module docstring), or None when it cannot be read."""
    if sys.platform == "darwin":
        try:
            out = runner(["vm_stat"], capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.SubprocessError):
            return None
        return parse_vm_stat(out.stdout) if out.returncode == 0 else None
    try:
        return parse_meminfo(meminfo.read_text())
    except OSError:
        return None


_NOW = object()


def under(floor_gb: float = FLOOR_GB, reading=_NOW) -> tuple[bool, float | None]:
    """(True when free memory is under floor_gb or unknown, the reading). reading: a reading already taken (None:
    unknown); read now when not given."""
    r = free_gb() if reading is _NOW else reading
    return (r is None or r < floor_gb), r


class Sampler:
    """Reads free memory every interval_s in a daemon thread; keeps the lowest reading (min_gb, min_at) and the count."""

    def __init__(self, interval_s: float = 5.0, read=None):
        self.interval_s, self.read = interval_s, read          # read: () -> GB or None; default free_gb
        self.min_gb, self.min_at, self.n, self.unknown = None, None, 0, 0
        self._stop = threading.Event()
        self._t = threading.Thread(target=self._loop, daemon=True)

    def sample(self) -> float | None:
        r = (self.read or free_gb)()
        self.n += 1
        if r is None:
            self.unknown += 1
        elif self.min_gb is None or r < self.min_gb:
            self.min_gb, self.min_at = r, time.strftime("%Y-%m-%dT%H:%M:%S")
        return r

    def _loop(self):
        while not self._stop.is_set():
            self.sample()
            self._stop.wait(self.interval_s)

    def start(self) -> "Sampler":
        self._t.start()
        return self

    def stop(self) -> dict:
        self._stop.set()
        if self._t.is_alive():
            self._t.join(timeout=self.interval_s + 5)
        self.sample()
        return self.record()

    def record(self) -> dict:
        return {"min_free_gb": None if self.min_gb is None else round(self.min_gb, 3), "min_at": self.min_at,
                "samples": self.n, "unknown_samples": self.unknown, "interval_s": self.interval_s,
                "reading": "vm_stat free+inactive+speculative+purgeable" if sys.platform == "darwin"
                else "/proc/meminfo MemAvailable"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--floor-gb", type=float, default=None, help="exit 3 when free memory is under this (or unknown)")
    a = ap.parse_args(argv)
    r = free_gb()
    print("free memory unknown" if r is None else f"free memory {r:.2f} GB")
    if a.floor_gb is not None:
        low, _ = under(a.floor_gb, r)
        if low:
            print(f"UNDER THE FLOOR: {a.floor_gb} GB")
            return EXIT_UNDER
    return 0


if __name__ == "__main__":
    sys.exit(main())
