<!-- provenance: scripts/S603_tokens_cost.py sha256 1f17babcd822d029, inputs findings/recompute/S520_inputs + findings/recompute/S520_inputs_d311 (S520) and findings/recompute/S603_inputs + findings/recompute/S603_inputs_d311 (S603), HEAD not stamped, written not stamped -->
# Tokens and cloud cost of the study's language-model calls

One call is one line of a named call log, counted by S520's rule on S520's frozen inputs of 7 November joined with the D311 collect of 9 November (D311, Q4); each counted line's tokens are read from S603's collects by the same line hash. Command: `uv run --frozen python scripts/S603_tokens_cost.py report`.

Collects read: beelink 2026-11-07T08:29:07Z to 2026-11-07T08:29:31Z (CET +0100); laptop 2026-11-07T08:28:15Z to 2026-11-07T08:28:52Z (CET +0100); laptop (D311) 2026-11-09T20:03:45Z to 2026-11-09T20:03:47Z (CET +0100); studio 2026-11-07T08:29:10Z to 2026-11-07T08:32:01Z (CET +0100).

## Reproduced first

| Gate | Pass |
|---|---|
| R3 line reader equals S520's | yes |
| R1 S520 total over its frozen inputs | yes |
| R1 S520 calls per model | yes |
| R1 S520 total with the D311 collect joined | yes |
| R1 S520 calls per model, D311 joined | yes |
| R2 hashes per S520 row equal its calls | yes |
| R2 run-tier hashes equal the total | yes |

S520's calls per provider (run tier): Anthropic 13,668, Google 218,172, local (Ollama) 950,302, unknown 2.

## Tokens, run tier (the 1,182,144 calls)

| Provider, model | Calls | With prompt and output | Total only | No count | Prompt tokens | Output tokens | Thinking tokens | Tokens of total-only calls | Anthropic cache tokens |
|---|---|---|---|---|---|---|---|---|---|
| local (Ollama), devstral-small-2:24b | 894,272 | 894,016 | 0 | 256 | 1,538,016,069 | 25,829,652 | 0 | 0 | 0 |
| Google, gemini-3-flash-preview | 204,181 | 204,140 | 0 | 41 | 1,742,093,122 | 179,612,454 | 196,380,387 | 0 | 0 |
| local (Ollama), gpt-oss:20b-date20261010 | 16,965 | 16,866 | 0 | 99 | 54,566,946 | 20,819,189 | 0 | 0 | 0 |
| Google, gemini-2.5-pro | 13,991 | 13,989 | 0 | 2 | 44,046,906 | 2,826,040 | 9,901,207 | 0 | 0 |
| Anthropic, claude-haiku-4-5 | 13,668 | 13,549 | 0 | 119 | 178,518,117 | 17,318,335 | 0 | 0 | 0 |
| local (Ollama), qwen3.8:27b | 12,293 | 12,241 | 0 | 52 | 94,615,855 | 2,256,679 | 0 | 0 | 0 |
| local (Ollama), qwen3-coder:30b | 11,051 | 11,051 | 0 | 0 | 39,641,186 | 3,151,258 | 0 | 0 | 0 |
| local (Ollama), gemma3:27b | 9,251 | 8,871 | 0 | 380 | 34,492,740 | 1,761,466 | 0 | 0 | 0 |
| local (Ollama), qwen3-coder-next:q4_K_M | 5,444 | 5,441 | 0 | 3 | 11,740,871 | 900,048 | 0 | 0 | 0 |
| local (Ollama), llama3:8b | 1,026 | 1,022 | 0 | 4 | 1,345,303 | 207,440 | 0 | 0 | 0 |
| unknown, ? | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 |

| Provider | Calls | With prompt and output | Total only | No count | Prompt tokens | Output tokens | Thinking tokens | Tokens of total-only calls | Anthropic cache tokens |
|---|---|---|---|---|---|---|---|---|---|
| local (Ollama) | 950,302 | 949,508 | 0 | 794 | 1,774,418,970 | 54,925,732 | 0 | 0 | 0 |
| Google | 218,172 | 218,129 | 0 | 43 | 1,786,140,028 | 182,438,494 | 206,281,594 | 0 | 0 |
| Anthropic | 13,668 | 13,549 | 0 | 119 | 178,518,117 | 17,318,335 | 0 | 0 | 0 |
| unknown | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 |

No count = no token field on the line (or the line not in the collects, 0 calls of the run tier).

Of the calls with prompt and output, 1,142 Gemini calls record no output_tokens (no candidatesTokenCount in the reply) but a total_tokens, so output = total - prompt - thinking, 0 tokens over all of them, exact, not estimated.

Gemini: output tokens exclude thinking (candidatesTokenCount); thinking is thoughtsTokenCount. Calls whose totalTokenCount exceeds prompt + output + thinking: 0, by 0 tokens in all (not priced).

## Cloud cost, USD

Run tier:

| Provider, model | USD from split counts | USD estimated (total only) | USD | Estimated share | Calls with prompt > 200k |
|---|---|---|---|---|---|
| Google, gemini-3-flash-preview | 1999.03 | 0.00 | 1999.03 | 0.0% | 0 |
| Google, gemini-2.5-pro | 183.91 | 0.00 | 183.91 | 0.0% | 5 |
| Anthropic, claude-haiku-4-5 | 265.11 | 0.00 | 265.11 | 0.0% | 0 |

| Provider, model | USD from split counts | USD estimated (total only) | USD | Estimated share | Calls with prompt > 200k |
|---|---|---|---|---|---|
| Google | 2182.94 | 0.00 | 2182.94 | 0.0% | 5 |
| Anthropic | 265.11 | 0.00 | 265.11 | 0.0% | 0 |

Run tier, cloud: USD 2448.05, of which USD 0.00 (0.0%) estimated from total-only calls.

Every tier S520 reads (run, dropped by decision, checks, smokes; copies excluded), what an invoice would also hold:

| Provider, model | USD from split counts | USD estimated (total only) | USD | Estimated share | Calls with prompt > 200k |
|---|---|---|---|---|---|
| Google | 2223.83 | 0.00 | 2223.83 | 0.0% | 5 |
| Anthropic | 265.52 | 0.00 | 265.52 | 0.0% | 0 |

All tiers, cloud: USD 2489.35.

Prices (USD per million tokens, thinking as output): gemini-3-flash-preview input 0.5, output 3.0 (D234 (experiments/README.md:1562); aistudio.google.com/docs/pricing, 7 Nov 2026); gemini-2.5-pro input 1.25, output 10.0, above 200,000 prompt tokens 2.5 and 15.0 (aistudio.google.com/docs/pricing, fetched 7 Nov 2026); claude-haiku-4-5 input 1.0, output 5.0 (platform.claude.com/docs/en/about-claude/pricing, fetched 7 Nov 2026).

Not in these costs: Google's implicit-cache discount (the Gemini records hold no cached-token count, so Gemini input is at the full price, an upper bound); calls outside S520's ledger (April and pre-lock work, the 28 unmapped call-log files, Gemini countTokens); taxes and any free-tier credit. EUR: not converted: the repository records no USD to EUR rate (Valerio's, from the invoices).

## When the calls ran, run tier

| Calls | First start (Amsterdam) | Last end (Amsterdam) | Span (days) | Hours with a call in flight | Sum of call wall time (hours) | Calls with a time |
|---|---|---|---|---|---|---|
| all machines | 2026-10-15 23:00 CEST | 2026-11-07 01:50 CET | 22.16 | 490.5 | 3951.0 | 1,182,144 |
| beelink | 2026-10-17 17:09 CEST | 2026-11-02 16:38 CET | 16.02 | 345.8 | 530.0 | 332,546 |
| laptop | 2026-10-16 00:27 CEST | 2026-11-06 17:01 CET | 21.73 | 407.8 | 646.5 | 309,507 |
| studio | 2026-10-15 23:00 CEST | 2026-11-07 01:50 CET | 22.16 | 476.7 | 2774.5 | 540,091 |
| cloud calls (Google and Anthropic) | 2026-10-15 23:00 CEST | 2026-11-07 01:50 CET | 22.16 | 163.6 | 652.7 | 231,840 |
| Anthropic | 2026-10-26 07:45 CET | 2026-10-28 01:28 CET | 1.74 | 22.7 | 48.3 | 13,668 |
| Google | 2026-10-15 23:00 CEST | 2026-11-07 01:50 CET | 22.16 | 142.9 | 604.4 | 218,172 |
| local (Ollama) | 2026-10-15 23:00 CEST | 2026-11-06 17:01 CET | 21.79 | 487.1 | 3298.3 | 950,302 |
| unknown | 2026-10-21 21:24 CEST | 2026-10-24 10:01 CEST | 2.53 | 0.0 | 0.0 | 2 |

## When the calls ran, every tier

| Calls | First start (Amsterdam) | Last end (Amsterdam) | Span (days) | Hours with a call in flight | Sum of call wall time (hours) | Calls with a time |
|---|---|---|---|---|---|---|
| all machines | 2026-10-03 00:27 CEST | 2026-11-07 01:50 CET | 35.1 | 497.8 | 4347.3 | 1,301,691 |
| beelink | 2026-10-15 19:04 CEST | 2026-11-02 16:38 CET | 17.94 | 391.3 | 579.8 | 426,975 |
| laptop | 2026-10-15 23:48 CEST | 2026-11-06 17:01 CET | 21.76 | 413.9 | 656.4 | 311,153 |
| studio | 2026-10-03 00:27 CEST | 2026-11-07 01:50 CET | 35.1 | 483.2 | 3111.1 | 563,563 |
| cloud calls (Google and Anthropic) | 2026-10-15 23:00 CEST | 2026-11-07 01:50 CET | 22.16 | 166.2 | 666.2 | 235,618 |
| Anthropic | 2026-10-26 07:31 CET | 2026-10-28 01:28 CET | 1.75 | 22.8 | 48.4 | 13,696 |
| Google | 2026-10-15 23:00 CEST | 2026-11-07 01:50 CET | 22.16 | 145.5 | 617.8 | 221,922 |
| local (Ollama) | 2026-10-03 00:27 CEST | 2026-11-06 17:01 CET | 34.73 | 493.9 | 3681.1 | 1,066,071 |
| unknown | 2026-10-21 21:24 CEST | 2026-10-24 10:01 CEST | 2.53 | 0.0 | 0.0 | 2 |

Start = the record's `at` (the machine's local clock when the call starts), end = start + wall_s. A call counts on the machine whose disk holds its log. Hours with a call in flight = the union of the calls' intervals; the sum of wall time counts parallel calls each.
