# Mentori, as the re-runs drive it

A copy of the Mentori code the paper's experiments run, taken byte for byte from Mentori at commit 83a4091 on
15 October 2026 (O2). `MANIFEST.json` lists every file with its sha256 at that commit. The first commit that adds this
folder holds the copy unchanged; every later commit that touches it is a fix, so `git log -p experiments/mentori/`
is the complete list of what the revision changed in Mentori and why.

The fixes come from `experiments/CUTS.md` (every cut, cap and limit on these code paths) and the decisions in
`experiments/README.md`: whole passages (D25), the RLM fixed (D31), every strategy reranks (D40), every answer
stores its passages and timings (D37), and every model call made through `experiments/runner/` under
`experiments/LOCK.toml`.

The code runs in its own environment, `pyproject.toml` and `uv.lock` as they were at 83a4091:

    uv run --project experiments/mentori python ...

`LICENSE` is Mentori's own.
