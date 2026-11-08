"""A rolling pool of answers (D80 V16; B9 F2 and O2 of findings/recompute/B9_smoke/B9_REPORT.md).

    from experiments.runner import pool
    await pool.rolling(items, size, run, done, stops=STOPS)

WHY. exp_01_generation.py and exp_02_scaling_factorial.py ran a config's answers in fixed batches (6 for single pass,
multi-hop and verified pass; 2 in exp_01 and 4 in exp_02 for the RLM configs), each batch an asyncio.gather, the next
batch starting only when the slowest answer of the last had ended. One RLM answer whose reply runs to the output
maximum (B9 F2: up to 1,165 s a call) held every slot of its batch. Here a slot freed by an answer that ends starts the
next item at once, so a slow answer holds one slot only.

WHAT IS THE SAME. The items start in the order given (the work list's order), and never more than `size` run at once,
the old batch size, so the concurrency against a server is what the batches allowed at their fullest. What each item
runs is the caller's run(item), unchanged.

WHAT DIFFERS. done(item, result, in_flight) is called as each item ends, in the order they end, so a slow answer is
stored when it ends instead of with its batch. in_flight is the number of items running when this one started, itself
included (1 to size): the answer's busy count. result is what run(item) returned, or the exception it raised.

A STOP. When a result is an instance of `stops` (a lock refusal or an RLMStop, Q38 and Q73), no further item starts;
the items already running end and are passed to done, then the first stop is raised. This is the batches' rule (store
the batch's other answers, then end the run), with "the items running" in place of "the batch". An exception raised by
done itself cancels the items still running (each then stores nothing and stays to do) and is raised.

Standard library only.
"""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Iterable


async def rolling(items: Iterable[Any], size: int, run: Callable[[Any], Awaitable[Any]],
                  done: Callable[[Any, Any, int], None], stops: tuple = ()) -> None:
    """Runs run(item) for every item, in order, at most size at once (module docstring)."""
    if isinstance(size, bool) or not isinstance(size, int) or size < 1:
        raise ValueError(f"pool size {size!r}: an integer from 1")
    items = list(items)
    running: dict = {}                     # task -> (position in items, items in flight when it started)
    nxt = 0
    stopped: list = []
    try:
        while running or (nxt < len(items) and not stopped):
            while nxt < len(items) and not stopped and len(running) < size:
                task = asyncio.ensure_future(run(items[nxt]))
                running[task] = (nxt, len(running) + 1)
                nxt += 1
            ended, _ = await asyncio.wait(running, return_when=asyncio.FIRST_COMPLETED)
            for task in sorted(ended, key=lambda t: running[t][0]):
                pos, in_flight = running.pop(task)
                if task.cancelled():
                    result = asyncio.CancelledError()
                else:
                    result = task.exception()
                    if result is None:
                        result = task.result()
                if stops and isinstance(result, stops):
                    stopped.append(result)
                done(items[pos], result, in_flight)
    finally:
        if running:
            for task in running:
                task.cancel()
            await asyncio.gather(*running, return_exceptions=True)
    if stopped:
        raise stopped[0]
