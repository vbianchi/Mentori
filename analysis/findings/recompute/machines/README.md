# The machines that ran the local models

The Methods' hardware sentence (the laptop's 48 GB among it) rests on this note. The facts come from the project's
operating log, `experiments/RUNNING.md`, a working file that is not released; this note carries them with their
source so a reader of the release can find them.

| Machine | Chip | Memory |
|---|---|---|
| laptop | Apple M4 Max | 48 GB |
| Studio | Apple M3 Ultra | 512 GB |
| Beelink | AMD Ryzen AI Max+ 395 | not stated (the operating system sees 23 GB) |

The log says the three were checked with `sysctl` and `/proc/cpuinfo`.

Source: `experiments/RUNNING.md` line 24, the entry of 6 November 10:00 (added in commit 9745a193): "hardware sentence
checked by sysctl and /proc/cpuinfo (laptop M4 Max 48 GB, Studio M3 Ultra 512 GB, Beelink Ryzen AI Max+ 395, its
memory left out: the OS sees 23 GB)". The same log records the Studio's 512 GB at line 1748 ("318 of 512 GB free") and
the Beelink's chip at line 882 ("12 physical cores (24 threads, Ryzen AI Max+ 395)"). Line numbers are those of
`experiments/RUNNING.md` at Mentori-reanalysis commit ccedb933 (git blob 741ef6fbc67ea060c636e4474ffb09e2a0b18ec3).

No script reads this file. It is shipped with the release (`scripts/S608_release_analysis.py` EVIDENCE) because the
log it quotes is not.
