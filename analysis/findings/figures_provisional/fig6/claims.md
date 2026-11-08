# Figure 6 claims list (D82, plan row A0)

Provenance: written 2026-10-22T12:20:20Z by `uv run --frozen python scripts/S447_fig6_panels.py claims` from this template
(`scripts/S447_fig6_claims_template.md`). Every provisional value is computed from
`findings/figures_provisional/fig6/fig6_numbers.json` (written by `S447 draw` at 2026-10-22T12:20:16Z, repository
HEAD de8ff4f (the script uncommitted), script sha256 8033ee667babd070), JSON key named in each row. Data stamp:
**PROVISIONAL: 2,420 of 2,860 attempts, 11 of 13 variants complete, records of 2026-10-21 16:16 CEST; before the D75 (S4) and D80 V1 / D81 reruns**. It is the plate's data state: the claims step refuses unless `figure6_provenance.json` (the plate,
`S447 figure`) carries the same stamp. The "Where" and "Claimed" columns quote the documents as read on 16 October
and are carried by the template; they were read, never written: the accepted text of `manuscript/submission/0*.docx`
and of `response/Point_by_point_response_all_reviewers.docx` (every `w:t`, so deleted text is left out, as
`scripts/docx_track.py` `accepted_text` reads it, tables included), `manuscript/submission/source/*.md` (the text as
submitted, `manuscript/submission/README.md`) and `manuscript/submission/figures/Figure_6_caption.md`. Paragraphs
are located by section and opening words, never by number.

## Panel letters: the documents' plates against the redraw

The "Where" and "Claimed" columns quote the documents, whose "Fig. 6" letters are those of the plate each was
written for: the accepted .docx text (rows A, L, S, R) cites the revision's plate (`S290_figure6.R`); the text as
submitted (rows M, `manuscript/submission/source/*.md`) cites the submitted plate, whose legend
(`04_Figures_Tables.md`, "Figure 6 \| Code generation benchmark") letters a and b as heatmaps and c as the context
arm. The "Provisional" and "Redraw panel" columns use the redraw's letters.

| Revision plate (`S290_figure6.R`; accepted .docx) | Submitted plate (`source/04_Figures_Tables.md`) | Redraw (`S447 figure`) |
|---|---|---|
| a, per strategy: median, IQR and range of the per-model pass rates ("Fig. 6a shows the median model") | a, pass-rate heatmap | no such panel; every cell is in a, and each strategy's gain per variant and its median in b |
| b, model by strategy heatmap of pass rates | b, pass-rate heatmap | **a**, strategy by variant heatmap, complete variants only |
| (none) | (none) | **b**, each strategy's gain over free-form, one dot per complete variant, median line |
| c, the 2,048-token arm against 24,576 (removed by D22) | c, context window, 2,048 against 24,576 | **c**, pass rate per thinking setting within each model (mean over operations), 95% interval over resampled operations |
| (none) | (none) | **d**, share of attempts failed, by kind, per model and setting |

Each row maps its own sentence: **Redraw panel** names where the redraw shows the claim's quantity (or "none"), and
**Citation change** quotes the sentence's own Figure 6 citation and says what it becomes, or says the sentence
cites no panel. The citations were read on 17 October from the same accepted text as the "Where" column (every
"Fig. 6" and "Figure 6" in the five .docx and the letter, Supplementary Figure 6 excluded) and from
`source/*.md`. A citation one parenthesis gives to several claims is mapped on each of them.

The JSON keys keep the working view's names (`S447 draw`, `fig6_provisional.png`): `panel_a_per_strategy` and
`panel_a_variants` are the per-strategy spread and its variant set, `panel_b_cells` the heatmap's cells,
`panel_c_thinking` the thinking factor.

## How a status is given

- **matches**: same definition, every record it needs is stored, equal at the text's precision.
- **differs**: same definition, every record it needs is stored or it is a design count, and the value differs.
- **not yet measurable**: it needs a variant still incomplete (2 of 13 are incomplete, attempts stored of 220: nemotron-3-nano:30b default 0, nemotron-3-nano:30b off 0), or a rerun still owed, or a
  statistic S447 does not compute. The provisional value is given with its scope, for orientation only. The reruns
  owed, counted from calls.jsonl joined by ctx_uid (`claims_support.reruns_owed`), on this list's records of 21 October. What ran (corrected 5 November, D252): no call in those records names a commit, so each attempt's version there is the clone commit the manifest gives its run, read from the clone and not from the record. 91a21921 and e89eaf5c predate D80; 6457ae69c has D80 (`clone_commits_have_d80`) and is the commit given to gemma3:27b and devstral-small-2:24b (6457ae69c: the commit ~/projects/mentori-runs-s2-d75 had at the manifest of 2026-10-16T21:27:40Z, read over ssh; not read again, so not yet checked as the commit that wrote these runs). Since then S4 ran the 165 attempts of `findings/recompute/S502_fig6_s4_reruns/S502_rerun_list.json` again on code with D80, and each records its own commit in its calls: 0b8074d7 for 118, 92f1d3ef for 47 (`records_manifest.json` `attempt_code_commit`). The plate's records (`s2_after_s4_20261105.tar`) hold these 165; their other 2,255 attempts record no commit. In those records the 18 failed attempts that met a tool-call parse error are all among the 165, so each ran with the D80 V1 retry and failed again (D251). The counts below are of the records of 21 October:
  - D80 V1 (Ollama only): 38 failed attempts met a tool-call parse error or a stall: gpt-oss:20b low 20 (parse), gpt-oss:20b medium 13 (parse), gpt-oss:20b high 4 (parse), qwen3-coder-next 1 (stall). No Ollama call met an HTTP 500 or a dropped connection. Apart, 7 attempts passed although a call met such an event: gpt-oss:20b low 4, gpt-oss:20b medium 2, gpt-oss:20b high 1.
  - D81 Q137: 75 failed attempts wrote add_cell as text: gpt-oss:20b high 65, qwen3-coder-next 4, gpt-oss:20b medium 3, devstral-small-2:24b 2, qwen3-coder:30b 1; 4 of them also owe D80 V1. Apart, 9 passing attempts did the same (gpt-oss:20b high 6, qwen3-coder-next 2, qwen3-coder:30b 1); see open item R4 for the call sites counted.
  - D75 S4: Q62 56 structured attempts across 7 variants, Q58 1, Q60 2 (S445's audit, `findings/recompute/S445_s2_d75_audit/`, over the 1,560 attempts it read; Q101 changes only the record, 60 attempts)
- **no longer applies**: the design changed (D22: the 2,048-token arm and every sentence resting on it go; D63: the
  gpt-oss arm with no effort level set is dropped; D71: both Gemini models also run with thinking off; the lock:
  num_ctx 131,072 and each maker's sampling).

A row is counted once, under the first status its Status cell gives; a second status in the same cell is listed
apart in the summary.

"Complete variants" below are the 11 complete in every strategy (all 220 attempts stored): qwen3-coder:30b, qwen3-coder-next, gpt-oss:20b low and medium and high, gemma3:27b, devstral-small-2:24b, gemini-2.5-pro default and off, gemini-3-flash default and off
(`claims_support.complete_variants`). This is the one set the plate's panels a and b draw (`panel_a_variants`, the
same 11), so a claim over complete variants and the plate compare strategies on the same variants; a partial
variant appears in panel c (on its matched attempts) and panel d only.

## (a) Main text, accepted text of the .docx

| # | Where | Claim | Claimed | Provisional (S447) | Redraw panel | Citation change | Status |
|---|---|---|---|---|---|---|---|
| A1 | 01_Title_Abstract.docx, abstract, "Retrieval-augmented generation grounds large language models" | extended reasoning in a small context window cut one model's pass rate | 73.8% to 6.2% | none: no 2,048-token arm | none (no 2,048-token arm) | no Figure 6 citation | no longer applies (D22) |
| A2 | 02_Main_Text.docx, Introduction, "We report a factorial evaluation of the design decisions" | code generation variants | 15 | 13 (`design.variants`; runner dry run "variants: 16 of 10 models") | none (a design count) | no Figure 6 citation | differs (+1: D63 drops 1, D71 adds 2) |
| A3 | same paragraph | "the serving software's default context window can increase the cost of extended reasoning" | (2,048-token arm) | none | none (D22) | no Figure 6 citation | no longer applies (D22) |
| A4 | 02_Main_Text.docx, Results heading "Code generation performance is sensitive to model family and context budget" | "context budget" | (2,048-token arm) | none | none (D22) | no Figure 6 citation | no longer applies (D22) |
| A5 | Results, "We evaluated 15 model variants across 11 code-generation strategies" | model variants | 15 | 13 | a (complete variants as columns), d (every variant with records) | "Fig. 6" (the whole figure): unchanged | differs (+1) |
| A6 | same | strategies | 11 | 11 (`design.strategies`; every record names one of the 11) | a and b (the 11 rows) | "Fig. 6": unchanged | matches |
| A7 | same | tasks | 20 | 20 operations, airway 10, lung 10 (`claims_support.operations`) | a (n = 20 operations per cell) | "Fig. 6": unchanged | matches |
| A8 | same | evaluations | 3,300 | 2,860 by design; 2,420 stored | none as a number (d gives each variant's n) | "Fig. 6": unchanged | differs (+220) |
| A9 | same | Pearson chi-square on pass counts | chi-square(140) = 299.2, P < 0.001 | chi-square(100) = 86.4, P = 0.83 over the 11 complete variants (`interaction_chi2`) | a (the heatmap the test is computed on; the test is not drawn) | "Fig. 6b" (the heatmap) becomes "Fig. 6a": the heatmap moved to a, and b is now the gain panel | not yet measurable (2 variants incomplete) |
| A10 | same | logistic likelihood-ratio chi-square | chi-square(140) = 582.7 on 3,300 records, P < 0.001 | not computed by S447 | a (as A9) | "Fig. 6b" becomes "Fig. 6a" (same parenthesis as A9) | not yet measurable (statistic not computed; 2 variants incomplete) |
| A11 | Results, "Free-form with best-of-3 selection achieved the highest mean pass rate" | best-of-3 mean pass rate across models, and highest of 11 | 65.0%, highest | 78.6%, still highest (11 complete; `claims_support.strategy_mean_over_complete_variants`) | a (the cells the mean is taken over) and b (the median gain over free-form); the mean across models is not drawn | "Fig. 6a shows the median model" cites a panel the redraw no longer has (the per-strategy median-model panel is gone): cite "Fig. 6a" for the cells and drop "shows the median model", or cite b for the median gain | not yet measurable (2 variants incomplete) |
| A12 | same | single-attempt free-form | 63.7% | 75.9% (11 complete) | a (row free-form) | as A11 (one parenthesis covers A11 to A13) | not yet measurable |
| A13 | same | error-recovery introspection | 62.7% | 76.4% (11 complete) | a (row error-recovery introspect) | as A11 | not yet measurable |
| A14 | same | best-of-3 minus free-form, McNemar | 1.3 points, P = 0.73, n = 300 pairs | +2.7 points, P = 0.38, n = 220 pairs (`claims_support.mcnemar_best_of_3_vs_free_form`) | b (row free-form best of 3: gain per variant and median; the McNemar test is not drawn) | no Figure 6 citation (the paragraph's only one is A11's); could cite "Fig. 6b" | not yet measurable |
| A15 | same | model calls, best-of-3 against free-form | 4.0 times | 4.0 (`claims_support.ratio_n_llm_calls_best_of_3_to_free_form`; fixed by the design, 3 candidates and a pick) | none (calls are not drawn) | no Figure 6 citation | matches (on 11 complete variants) |
| A16 | same | wall-clock time, best-of-3 against free-form | 3.1 times | 3.4 (11 complete; ratio of mean latency_s) | none (time is not drawn) | no Figure 6 citation | not yet measurable |
| A17 | same | merging candidates (free-form combined) | 57.0% | 74.1% (11 complete) | a (row free-form combined), b (its gains) | no Figure 6 citation | not yet measurable |
| A18 | same | combined minus free-form, McNemar | -6.7 points, P = 0.019 | -1.8 points, P = 0.67, n = 220 pairs (`claims_support.mcnemar_combined_vs_free_form`) | b (row free-form combined; the test is not drawn) | no Figure 6 citation; could cite "Fig. 6b" | not yet measurable |
| A19 | Results, "Extended reasoning produced divergent outcomes across model families" | nemotron-3-nano:30b outside structured output, off to reasoning | 39.3% to 52.9%, P = 0.002, 140 pairs | none stored | c (nemotron-3-nano:30b off and default, once both are stored; none yet) | "Fig. 6b" (the heatmap) becomes "Fig. 6c" (thinking) | not yet measurable (nemotron: 0 and 0 attempts stored) |
| A20 | same | gpt-oss:20b with no effort level set | 48.6% | none | none (D63 drops the arm) | "Fig. 6b" (same parenthesis as A21, A22) goes with the 48.6% clause | no longer applies (D63; the lock sends low as gpt-oss's off) |
| A21 | same | gpt-oss:20b low, outside structured | 72.9% (140 records) | outside structured, passes over attempts: 70.7%, 140 of 140 (`claims_support.outside_structured_by_variant`); plate c (Rule 2: mean of the 20 operations' shares, on the 220 matched attempts): 64.1% (95% interval 50.5 to 76.4) | c (gpt-oss:20b low, on matched attempts of every strategy; the rate outside structured output is not drawn) | "Fig. 6b" becomes "Fig. 6c" | not yet measurable (20 failed attempts owe the D80 V1 rerun) |
| A22 | same | gpt-oss:20b medium, outside structured | 60.0% (140 records) | outside structured, passes over attempts: 72.1%, 140 of 140; plate c (Rule 2: mean of the 20 operations' shares, on the 220 matched attempts): 66.8% (95% interval 54.5 to 77.7) | c (gpt-oss:20b medium, as A21) | "Fig. 6b" becomes "Fig. 6c" (same parenthesis as A21) | not yet measurable (variant incomplete, run on code before D80; 13 failed attempts owe the D80 V1 rerun; 3 add_cell-as-text attempts owe the D81 rerun) |
| A23 | same | glm-4.7-flash:30b, baseline against reasoning | 48.6% vs 44.3%, P = 0.49 | none stored | c (glm-4.7-flash off and default, once both are stored) | no Figure 6 citation; could cite "Fig. 6c" | not yet measurable (glm: 0 and 0 attempts stored) |
| A24 | same | gpt-oss:20b at the 2,048-token default, no effort to high | 73.8% to 6.2% (Fig. 6c) | none | none (D22) | "Fig. 6c" (the 2,048-token arm) goes with the sentence; the letter c now names the thinking panel, so it must not be carried into a sentence about context length | no longer applies (D22) |
| A25 | same | gpt-oss:20b high at 24,576 tokens | 33.2% | pooled, passes over every stored attempt: 50.9%, 220 of 220 stored, over 11 strategies: free_form 20, free_form_n3_best 20, free_form_n3_combined 20, error_recovery_introspect 20, introspect_then_code 20, introspect_with_recovery 20, thinker_coder_split 20, coder_v2_n1 20, coder_v2_n1_cell3_best 20, coder_v2_n1_cell3_combined 20, coder_v2_n3 20 (`panel_b_variant_order_and_pooled`, `claims_support.strategies_stored_by_variant`); plate c (Rule 2: mean of the 20 operations' shares, on the 220 matched attempts): 50.9% (95% interval 41.8 to 59.5) | c (gpt-oss:20b high) | no Figure 6 citation (it follows A24's "Fig. 6c"); could cite "Fig. 6c" | not yet measurable (variant incomplete; context is now 131,072) |
| A26 | Results, "Introspection did not help consistently" | best introspection strategy minus free-form, range across variants | -15.0 to +35.0 points over 15 variants | 0.0 to +15.0 over 11 complete (`claims_support.introspection_best_minus_free_form_pts`) | b (the four introspection rows, gain per variant) and a (their cells) | "Fig. 6b" keeps its letter, which now names the gain panel: each variant's best introspection gain is read across b's four introspection rows, no longer from heatmap cells | not yet measurable |
| A27 | same | the four variants with the lowest pooled rates gained nothing | 4 variants, gain 0 | of the 11 complete, the lowest are gemma3:27b (0.0), gpt-oss:20b high (+15.0), qwen3-coder-next (+10.0), devstral-small-2:24b (+10.0) | b (as A26), a (columns ordered by pooled rate) | as A26 (same parenthesis) | not yet measurable |
| A28 | same | n per cell | 20 operations | 20 (`design.operations`, one draw) | a and b (n = 20 operations per cell) | as A26 (same parenthesis) | matches |
| A29 | same | structured output produced no code in any record for gemma3:27b, deepseek-r1:70b, nemotron-3-nano:30b | 0 code in 3 variants | deepseek-r1:70b none stored; gemma3:27b structured: 80 of 80 records hold no code (coder_v2_n1, coder_v2_n1_cell3_best, coder_v2_n1_cell3_combined, coder_v2_n3 stored; 0 of the 4 structured strategies not complete); nemotron-3-nano:30b default none stored; nemotron-3-nano:30b off none stored (`claims_support.structured_by_variant`) | d (failure kinds; the three variants are incomplete, so not in a or b) | no Figure 6 citation; could cite "Fig. 6d" | not yet measurable (gemma3 and nemotron have no structured attempt stored; deepseek incomplete) |
| A30 | same | qwen3-coder:30b structured, best cell | up to 65.0% | 75.0% (structured combined; `claims_support.structured_by_variant`) | a (qwen3-coder:30b column, the four structured rows) | no Figure 6 citation; could cite "Fig. 6a" | not yet measurable (Q62: some of its structured attempts may be rerun, Q1 open; 1 add_cell-as-text attempt owes the D81 rerun) |
| A31 | same | cause for gemma3 and deepseek: tool-call rejections by Ollama | 151 of 160 evaluations | deepseek's 0 failed structured records: 0 parse errors,  (`panel_b_cells`) | d (tool-call parse error, tool call written as text) | no Figure 6 citation; could cite "Fig. 6d" | not yet measurable (gemma3 has no attempt stored; deepseek's text-form calls owe the D81 Q137 rerun) |
| A32 | same | cause for nemotron: a test-harness exception | (no count) | none stored | d (harness error) | no Figure 6 citation; could cite "Fig. 6d" | not yet measurable (nemotron incomplete) |
| A33 | Discussion, "Multi-agent orchestration lowered accuracy where intermediate stages lost information" | reasoning helped two of three families at low or medium effort, cost at high | 2 of 3 | gpt-oss:20b matched on 220 attempts over 20 operations (20 with 11); pass rate as Rule 2's mean of the operations' shares: low 64.1 (95% interval 50.5 to 76.4), medium 66.8 (95% interval 54.5 to 77.7), high 50.9 (95% interval 41.8 to 59.5) (`panel_c_thinking`; plate c); nemotron, glm: no matched pair of settings stored | c | the sentence's one citation, "Fig. 6c", sits on the 2,048 clause (A34), which goes; if the reasoning clause stays, "Fig. 6c" now fits it (the thinking panel) | not yet measurable (nemotron and glm incomplete) |
| A34 | same | at the 2,048 default, gpt-oss | 73.8% to 6.2% (Fig. 6c) | none | none (D22) | "Fig. 6c" goes with the clause | no longer applies (D22) |
| A35 | 03_Methods.docx, Code generation benchmark, "Fifteen model variants and 11 strategies were evaluated on 20 operations" | variants | 15 | 13 | a, d | no Figure 6 citation (the paragraph's "Fig. 6c" is A42's) | differs (+1) |
| A36 | same | operations, ten on each of two datasets | 20, 10 + 10 | 20, airway 10, lung 10 | a (n = 20 operations) | no Figure 6 citation | matches |
| A37 | same | 13 local Ollama configurations and 2 Gemini API models | 13 + 2 | 9 Ollama + 4 Gemini (`design`; runner dry run) | a, c, d (row labels) | no Figure 6 citation | differs (-1 local, +2 Gemini) |
| A38 | same | airway: eight samples, 38,694 genes | 8, 38,694 | 8 samples, 38,694 genes (reference values, `claims_support.reference_values_op1`) | none | no Figure 6 citation | matches |
| A39 | same | NCCTG lung: 228 patients, ten variables | 228, 10 | 228 patients, 10 variables | none | no Figure 6 citation | matches |
| A40 | same | tolerances 0.001 to 30, 8-of-10 set overlap, exact equality for four integer-count operations, clustering pairs and one field in two more | as stated | not read by S447 (coder_ground_truth.json, pinned by sha256 in exp_05_coder_benchmark.py) | none (the pass rule; stated in the legend) | no Figure 6 citation | not yet measurable (outside the records S447 reads) |
| A41 | same | main analysis | 3,300 evaluations at 24,576 tokens (15 x 11 x 20; num_ctx = 24,576) | 2,860 (13 x 11 x 20); 20,727 Ollama generator calls sent num_ctx 131,072, Gemini sends none (`claims_support.generator_num_ctx_sent`) | none (a design count) | no Figure 6 citation | differs (+220) / no longer applies (num_ctx, lock) |
| A42 | same | ten variants also ran at 2,048 tokens (Fig. 6c) | 10 | none | none (D22) | "Fig. 6c" goes with the sentence | no longer applies (D22) |
| A43 | 03_Methods.docx, Statistics and Reproducibility, "In the question-answering experiments the unit of analysis" | code-generation benchmark ran each item once per variant and configuration | once | one draw (D49); no answer_key stored twice (`records.duplicates_dropped` empty) | c (the operation is the unit of the interval) | no Figure 6 citation | matches |
| A44 | 03_Methods.docx, Use of large language models, "LLMs were used as the research subject" | Gemini API code-generation runs | 4 to 27 March 2026 | Gemini generator calls 15 Oct 2026 23:00 to 16 Oct 2026 08:24 (`records.generator_call_dates_by_provider`) | none | no Figure 6 citation | no longer applies (rerun under the lock) |
| A45 | 03_Methods.docx, Code availability, "Mentor::i, the multi-agent AI workspace" | reproduce.sh regenerates Fig. 6c from a deposited summary | panel c | plate c is now the thinking factor, drawn from records | c (now drawn from the records, like every panel) | "(Fig. 6c from a deposited summary, as its legend states)" goes: no panel is an exception any more | no longer applies (D22) |
| A46 | 01_Title_Abstract.docx, abstract, "Retrieval-augmented generation grounds large language models" | "the benefit of querying installed libraries depends on the model" (the introspection half; the other half is A1) | depends on the model | best introspection strategy minus free-form: 0.0 (qwen3-coder:30b, gpt-oss:20b medium, gemma3:27b, gemini-2.5-pro off, gemini-3-flash default and off), +5.0 (gpt-oss:20b low), +10.0 (qwen3-coder-next, devstral-small-2:24b), +15.0 (gpt-oss:20b high, gemini-2.5-pro default), over 11 complete (`claims_support.introspection_best_minus_free_form_pts`) | b (introspection rows) | no Figure 6 citation | not yet measurable (2 variants incomplete) |
| A47 | 02_Main_Text.docx, Introduction, "We report a factorial evaluation of the design decisions", the fourth finding | "the benefit of programmatic API introspection in code generation depends on the model" (the introspection half; the other half is A3) | depends on the model | as A46 | b (introspection rows) | no Figure 6 citation | not yet measurable (2 variants incomplete) |
| A48 | Results, "Extended reasoning produced divergent outcomes across model families", second sentence | "The gpt-oss:20b model has no setting without reasoning: a request to turn it off is accepted and the model reasons regardless" | reasons when asked not to | no S2 call sends think off to gpt-oss: the lock sends low, its lowest level (D63). Generator calls that returned reasoning text: low 3,156 of 3,364 (93.8%), medium 2,424 of 2,511, high 1,843 of 1,876 (`claims_support.generator_reasoning_by_variant`) | c (gpt-oss:20b low, its lowest level, as off) | no Figure 6 citation (A21's "Fig. 6b" is the next sentence's) | not yet measurable (outside the records S447 reads: none asks for reasoning off) |
| A49 | Discussion, "Across our experiments, steps that processed the model's own intermediate output" | high-effort reasoning lowered accuracy (the code-generation instance) | lowered | gpt-oss:20b matched on 220 attempts over 20 operations (20 with 11); pass rate as Rule 2's mean of the operations' shares: low 64.1 (95% interval 50.5 to 76.4), medium 66.8 (95% interval 54.5 to 77.7), high 50.9 (95% interval 41.8 to 59.5) (`panel_c_thinking`; plate c); nemotron, glm: no matched pair of settings stored | c | no Figure 6 citation | not yet measurable (gpt-oss high incomplete; nemotron, glm incomplete) |
| A50 | 03_Methods.docx, Use of large language models, "LLMs were used as the research subject" | "All local models ran on one Mac Studio (Apple M3 Ultra, 512 GB of unified memory)" | one Mac Studio | devstral-small-2:24b (220 attempts), gpt-oss:20b low (220 attempts), gpt-oss:20b medium (220 attempts) ran on the laptop; the other 8 variants with records on the Studio (`claims_support.attempts_by_machine`) | none | no Figure 6 citation | differs (two machines) |

## (a') Main text as submitted, `manuscript/submission/source/*.md`

Already superseded in the accepted .docx where noted; listed because the task names these files.

| # | Where | Claim | Claimed | Provisional (S447) | Redraw panel | Citation change | Status |
|---|---|---|---|---|---|---|---|
| M1 | 01_Title_Abstract.md, "Retrieval-augmented generation (RAG) systems increasingly ground" | code generation evaluations | 3,300 | 2,860 by design | none | no Figure 6 citation | differs (+220); sentence gone from the accepted abstract |
| M2 | 02_Main_Text.md, "To test whether context quality outweighs context quantity" | 15 variants, 11 strategies, 20 operations, 3,300 | as stated | 13, 11, 20, 2,860 | a, d | "Fig. 6" (the whole figure): unchanged | differs (variants +1, evaluations +220); 11 and 20 match |
| M3 | same | best-of-3, free-form, error-recovery introspection | 65.0%, 63.7%, 62.7% | 78.6%, 75.9%, 76.4% (11 complete) | a (the cells the mean is taken over; the mean is not drawn) | "Fig. 6a" (the submitted a, a heatmap) keeps its letter: the redraw's a is the heatmap; the accepted text already reads "Fig. 6a shows the median model" (A11) | not yet measurable |
| M4 | same | moderate thinking improved three families, McNemar P < 0.03 each | 3 families | gpt-oss only so far | c | "Fig. 6b" at the end of the sentence (the submitted b, a heatmap) becomes "Fig. 6c" | not yet measurable (2 families incomplete) |
| M5 | same | gpt-oss at 2,048, no thinking to think high | 73.8% to 6.2% | none | none (D22) | "Fig. 6b" goes with the 2,048 clause | no longer applies (D22) |
| M6 | same | gpt-oss think high at 24,576 | 48.2% | pooled, passes over every stored attempt: 50.9%, 220 of 220 stored; plate c (Rule 2: mean of the 20 operations' shares, on the 220 matched attempts): 50.9% (95% interval 41.8 to 59.5) | c (gpt-oss:20b high) | "Fig. 6b" becomes "Fig. 6c" | not yet measurable (variant incomplete); the accepted text says 33.2% |
| M7 | 02_Main_Text.md, "Strategy effectiveness was highly model-dependent" | chi-square P < 0.001 | P < 0.001 | P = 0.83 over 11 complete | a (the heatmap the test is computed on; not drawn) | "Fig. 6c" (the submitted c, the context arm, so mis-cited already) becomes "Fig. 6a"; superseded by the accepted text (A9) | not yet measurable |
| M8 | same | introspection gain for gpt-oss without thinking | +35 points | none: "without thinking" is the arm with no effort level set (the paragraph's 73.8% "no thinking"), which D63 dropped; for reference, gpt-oss low, the lock's off, gains +5.0 | none (D63) | "Fig. 6c" (same parenthesis as M7, M9) goes with the clause | no longer applies (D63) |
| M9 | same | structured 0% for gemma3, deepseek-r1, nemotron; qwen3-coder up to 65% | 0%, 65% | deepseek coder_v2_n1 0 of 0; qwen3-coder best structured cell 75.0% | a (qwen3-coder:30b column) and d (the three incomplete variants) | "Fig. 6c" becomes "Fig. 6a" for qwen3-coder and "Fig. 6d" for the three with no code | not yet measurable (as A29, A30) |
| M10 | 03_Methods.md, "Fifteen model variants (13 local Ollama configurations" | airway genes | about 64K | 38,694 | none | no Figure 6 citation | differs (about -25,300); corrected in the accepted Methods |
| M11 | same | 3,300 = 15 x 11 x 20 plus 2 Gemini x 7 x 20 | 3,300 (sums to 3,580) | 2,860 | none | no Figure 6 citation | no longer applies (corrected in the accepted Methods, R4 2a) |
| M12 | same | complexity tiers | simple 6, medium 8, complex 6 | 6, 8, 6 (`claims_support.operations.by_complexity`) | none | no Figure 6 citation | matches |
| M13 | 04_Figures_Tables.md, "Figure 6 \| Code generation benchmark" | 15 variants, 11 strategies, 20 operations, 3,300; panel c 2,048 against 24,576 | as stated | 13, 11, 20, 2,860; plate c now thinking | a to d (the legend) | the submitted legend (a, b heatmaps; c the context arm) is replaced by legend_draft.md (a heatmap, b gain, c thinking, d failures) | differs (+1, +220); c no longer applies (D22) |

## (b) Figure 6 legend and Supplementary Information

Legend: `04_Figures_Tables.docx`, "Figure 6 | Code generation pass rates", identical in numbers to
`figures/Figure_6_caption.md`. Its letters are the submitted plate's (table above).

| # | Where | Claim | Claimed | Provisional (S447) | Redraw panel | Citation change | Status |
|---|---|---|---|---|---|---|---|
| L1 | legend a, "Pass rate of each of the 11 prompting strategies" | context length | 24,576 tokens | 131,072 (lock; Ollama calls) | none (the lock) | legend a now defines the heatmap; its context length goes | no longer applies (lock) |
| L2 | legend a | "no LLM judge is involved" | passed by tests | `passed` is the field-by-field result; the soft-pass judge never decides it (exp_v2_8 `_evaluate_failed_result`) | every panel (the legend's opening: no language-model judge decides a pass) | moves from legend a to the legend's opening sentence | matches |
| L3 | legend a | models per strategy | 15, or 11 or 12 | 11 in every strategy: the plate's a and b draw one set, the variants complete in all 11 (`panel_a_variants`), the same set as the claims here; partial variants in plate c (matched attempts) and d only | a and b (the 7 complete variants) | legend a's per-strategy spread is gone; a and b define one set of variants | not yet measurable |
| L4 | legend a, b | cells in which no record produced code, records | 15 cells, 300 records | 4 cells so far (gemma3:27b coder_v2_n1, 20 records, gemma3:27b coder_v2_n1_cell3_best, 20 records, gemma3:27b coder_v2_n1_cell3_combined, 20 records, gemma3:27b coder_v2_n3, 20 records) (`claims_support.cells_where_no_record_produced_code`) | a (cells), d (no code, in other) | legend a and b's no-code cells: a draws complete variants only; d counts no code | not yet measurable |
| L5 | legend b | 3,300 records, 15 models by 11 strategies, n = 20 per cell | 3,300; 15 x 11; 20 | 2,860; 13 x 11; 20 (plate a) | a | legend b (the heatmap) becomes legend a | differs (+220, +1 row); 20 matches |
| L6 | legend b | pooled structured output and free-form, over cells that ran | 49.9% and 61.9% | 53.5% and 76.2% (free-form family of 3 strategies; 11 complete; `pooled_structured_vs_free_form`) | none (pooled rates are not drawn) | goes from the legend | not yet measurable |
| L7 | legend b | interaction chi-square, with and without "not run" | 299.2 on 140 df | 86.4 on 100 df over 11 complete | none (no test is shown) | goes from the legend | not yet measurable |
| L8 | legend b | logistic LR chi-square and AIC | 582.7 on 140; AIC 3,747.3 vs 4,050.0; 369.0 on 125 | not computed | none (no test is shown) | goes from the legend | not yet measurable (statistic not computed) |
| L9 | legend b | gpt-oss:20b [effort not set] row | 1 row | none | none (D63) | goes | no longer applies (D63) |
| L10 | legend c | 2,048 against 24,576, 10 models, n = 80 and 220 | as stated | plate c is the thinking factor | c (thinking) | legend c now defines the thinking panel | no longer applies (D22) |
| L11 | legend source line | drawn from S289_codegen_cells.csv by S290_figure6.R | old sources | S447 from findings/runs/exp_05__* | every panel | the source line becomes the Source Data caption's (S447 figure, from the run records) | no longer applies |
| S1 | 06_Supplementary_Information.docx, Supplementary Table 1, row "Code generation" | design and evaluations | 15 x 11 x 20; 3,300 | 13 x 11 x 20; 2,860 | none | no Figure 6 citation | differs (+1, +220) |
| S2 | Supplementary Table 7, rows "exp08_coder_benchmark" | records per model (design): deepseek-r1 220, devstral 220, gemma3 220, glm 440, nemotron 440, qwen3-coder-next 220, qwen3-coder 220 | as listed | same design counts; stored 0, 220, 220, 0, 0, 220, 220 (`claims_support.records_per_model`) | none (d gives each variant's n) | no Figure 6 citation | matches (design; 1 of 7 still being run) |
| S3 | same | gpt-oss:20b, 4 files | 880 | 660 by design (low, medium, high), 660 stored | none | no Figure 6 citation | differs (-220; D63) |
| S4 | same | gemini-2.5-pro and gemini-3-flash, 1 file each | 220 each | 440 and 440 by design, 440 and 440 stored | none | no Figure 6 citation | differs (+220 each; D71) |
| S5 | same | run file names exp08_coder_benchmark_<model>_latest.json, judge "-" | as listed | records in findings/runs/exp_05__<strategy>__<variant>/ (11 sinks per variant); the soft-pass judge (devstral-small-2:24b) is called on failures but never decides passed | none | no Figure 6 citation | no longer applies |
| S6 | Supplementary Table of stored fields, row "Code generation" | Records; judge_score; passed; field_results; exec_error | 3,300; 91.5%; 100.0%; 66.2%; 100.0% | 2,420 stored; non-empty 100.0 / 100.0 / 80.6 / 19.4, present 100.0 / 100.0 / 100.0 / 100.0 (`claims_support.field_coverage_pct`, `field_present_pct`) | none | no Figure 6 citation | not yet measurable (2,420 of 2,860; the column's definition is not stated) |
| S7 | Supplementary Data 5, "Source data for Figure 6" | one worksheet per panel, a to c | a to c | panels a to d (Source Data Fig. 6, one sheet per panel), c replaced | a to d (Source Data Fig. 6, one sheet per panel) | "One worksheet per panel, a to c" becomes "a to d" | no longer applies (D22) |
| S8 | Supplementary Methods, Code generation benchmark, "Operations were assigned to three complexity tiers" | simple, medium, complex | 6, 8, 6 | 6, 8, 6 | none | no Figure 6 citation | matches |
| S9 | same section, "The 11 strategies fell into three families" | free-form 3, structured 4, introspection 4 | 3 + 4 + 4 | the 11 configs of the records, same families | a and b (row labels) | no Figure 6 citation | matches |
| S10 | same | best of 3: three scripts at temperature 0.7 | 0.7 | candidate calls sent 0.15 (devstral-small-2:24b), 0.7 (qwen3-coder:30b), 1.0 (all others) (`claims_support.best_of_3_candidate_temperature_sent`) | none | no Figure 6 citation | no longer applies (lock [sampling.models]) |
| S11 | 06_Supplementary_Information.docx, Supplementary Table 1, row "Total", and its caption "Supplementary Table 1 \| Evaluation counts by experiment" ("Total: 50,835 for all twelve experiments") | evaluations, all twelve experiments | 50,835 | 50,395 with code generation's 2,860 (+-440 from this row alone; the other rows are outside S447) | none | no Figure 6 citation | differs (+-440) |
| S12 | supplementary/Supplementary_Figure_1.svg, the "Code generation" box | design and evaluations | 15 model variants x 11 strategies x 20 operations, 3,300 evaluations | 13 x 11 x 20, 2,860 | none | no Figure 6 citation | differs (+1, +220) |
| S13 | Supplementary Table 7 caption, "Supplementary Table 7 \| Generator and judge pairing, experiment by experiment" | run files and the Files column (the code-generation rows hold 15 files: gpt-oss 4, glm 2, nemotron 2, the other seven 1 each) | 39 rows from 75 run files; Files sums to 76 | one file per variant gives 13 code-generation files (D63 -1, D71 +2): 76 run files, Files summing to 77; still 39 rows (the same 10 models). The records now sit in 11 sinks per variant, 143 by design, 121 mirrored (`records_manifest.json`) | none | no Figure 6 citation | differs (+1 file; the file layout also changed, see S5) |

## (c) Response letter, accepted text of `response/Point_by_point_response_all_reviewers.docx`

| # | Where | Claim | Claimed | Provisional (S447) | Redraw panel | Citation change | Status |
|---|---|---|---|---|---|---|---|
| R1 | Reviewer 1, Comment 1.2, the abstract quoted, "Retrieval-augmented generation grounds large language models" | 73.8% to 6.2% | as A1 | none | none (D22) | no Figure 6 citation | no longer applies (D22) |
| R2 | Reviewer 1, Comment 1.7, "Mentor::i, the multi-agent AI workspace" | Fig. 6c from a deposited summary | panel c | as A45 | c | as A45: "(Fig. 6c from a deposited summary, as its legend states)" goes | no longer applies (D22) |
| R3 | Reviewer 3, Major Point 1b, the per-experiment table, row "Code generation" | Records; judge_score; passed; field_results; exec_error | 3,300; 91.5%; 100.0%; 66.2%; 100.0% | as S6 | none | no Figure 6 citation | differs (3,300 against 2,860 by design); percentages not yet measurable |
| R4 | Reviewer 4, Comment 2a, heading "the 3,300 code-generation decomposition" | 3,300 | 3,300 | 2,860 | none | no Figure 6 citation | differs (+220) |
| R5 | Reviewer 4, Comment 2a, "Corrected. The Methods text now reads" | 15 variants, 13 local + 2 Gemini, 11 strategies, 20 operations, 3,300 at 24,576 (num_ctx = 24,576) | as quoted | 13, 9 + 4, 11, 20, 2,860 at 131,072 | none | no Figure 6 citation | differs (variants +1, local -1, Gemini +2, evaluations +220); num_ctx no longer applies; 11 and 20 match |
| R6 | Reviewer 4, Comment 2a, "We verified this against the raw code-generation benchmark files" | the files hold exactly 3,300 records; the earlier phrasing summed to 3,580 | 3,300; 3,580 | 2,420 stored of 2,860 | none | no Figure 6 citation | no longer applies (new runs; the 3,580 history stays true of the submitted text) |
| R7 | Reviewer 4, Question 2, "We did test the third comparator, best-of-n" | best-of-3 across 15 variants and 20 operations: 300 of 3,300 | 300 of 3,300 | 260 of 2,860 by design (`claims_support.best_of_3_design_attempts`); 220 stored | b (row free-form best of 3) | no Figure 6 citation | differs (+20 of +220) |
| R8 | Reviewer 4, Question 2, "Free-form with best-of-3 selection achieved the highest mean pass rate" | 65.0, 63.7, 62.7; 1.3 points, P = 0.73, n = 300; 4.0 times calls, 3.1 times time; 57.0, -6.7, P = 0.019 | as A11 to A18 | as A11 to A18 | as A11 to A18 | the letter quotes "Fig. 6a shows the median model": as A11 | not yet measurable (as A11 to A18); 4.0 matches |
| R9 | Reviewer 4, Question 2, "The two attempts mostly agree" | further attempts do not help in code generation either | (best-of-3 result) | best-of-3 +2.7 points, P = 0.38 over 11 complete | b (row free-form best of 3) | no Figure 6 citation | not yet measurable |

## Summary

96 claims, each counted once under its first status:

| Status | Rows | Which |
|---|---|---|
| matches | 13 | A6 A7 A15 A28 A36 A38 A39 A43 M12 L2 S2 S8 S9 |
| differs | 22 | A2 A5 A8 A35 A37 A41 A50 M1 M2 M10 M13 L5 S1 S3 S4 S11 S12 S13 R3 R4 R5 R7 |
| not yet measurable | 39 | A9 A10 A11 A12 A13 A14 A16 A17 A18 A19 A21 A22 A23 A25 A26 A27 A29 A30 A31 A32 A33 A40 A46 A47 A48 A49 M3 M4 M6 M7 M9 L3 L4 L6 L7 L8 S6 R8 R9 |
| no longer applies | 22 | A1 A3 A4 A20 A24 A34 A42 A44 A45 M5 M8 M11 L1 L9 L10 L11 S5 S7 S10 R1 R2 R6 |

Rows that also carry a second status: A41 (no longer applies), M2 (matches), M13 (no longer applies), L5 (matches), R3 (not yet measurable), R5 (no longer applies, matches), R8 (matches).

The largest differences where the claim is measurable (design counts and reference values):

1. M10, airway genes, submitted Methods: about 64K against 38,694 (already corrected in the accepted Methods).
2. A8, A41, L5, S1, S12, R3, R4, R5, M1, M2, M13: 3,300 evaluations against 2,860 (+-440), in eleven places.
3. S11, Supplementary Table 1, Total: 50,835 against 50,395 (+-440, from code generation alone).
4. S3, Supplementary Table 7, gpt-oss:20b: 880 against 660 records (D63).
5. S4, Supplementary Table 7, gemini-2.5-pro: 220 against 440 (D71).
6. S4, Supplementary Table 7, gemini-3-flash: 220 against 440 (D71).
7. R7, letter Reviewer 4 Question 2: best-of-3 300 of 3,300 against 260 of 2,860.
8. A37, R5: 13 local + 2 Gemini variants against 9 + 4.
9. A2, A5, A35, M2, M13, L5, S1, S12, R5: 15 variants against 13 (+1).
10. S13, Supplementary Table 7 caption: 75 run files (Files sum 76) against 76 (77), +1.

A50 also differs, not as a number: the local models ran on two machines, not one.

The largest provisional gaps among the not yet measurable rows follow, for orientation only (scope: 11 complete
variants unless stated; every one before the D75 (S4) and D80 V1 / D81 reruns). M8 is not among them: its arm is
D63's and no longer applies.

| Row | Claim | Text | Provisional | Gap |
|---|---|---|---|---|
| A26 | top of the introspection range | +35.0 | +15.0 | -20.0 |
| A25 | gpt-oss high at 24,576 (now 131,072); plate c's value | 33.2% | 50.9% (plate c, Rule 2, 220 matched attempts; pooled over the 220 stored, 50.9%) | +17.7 |
| A17 | free-form combined | 57.0% | 74.1% | +17.1 |
| A26 | bottom of the introspection range | -15.0 | 0.0 | +15.0 |
| L6 | free-form family pooled | 61.9% | 76.2% | +14.3 |
| A13 | error-recovery introspection | 62.7% | 76.4% | +13.7 |
| A11 | best-of-3 | 65.0% | 78.6% | +13.6 |
| A12 | free-form | 63.7% | 75.9% | +12.2 |
| A22 | gpt-oss medium outside structured (not drawn; plate c draws the matched rate) | 60.0% | 72.1% (140 of 140) | +12.1 |
| L6 | structured output pooled | 49.9% | 53.5% | +3.6 |

The pass rates are higher across the board on the 11 complete variants, which are the strongest of the
submitted set (gemini, qwen3-coder); the weaker models are among the 2 still incomplete, so these gaps are
expected to narrow and say nothing yet about the final figure.

## Open items from the review of 16 October (to add in the next pass)

- R1. F1. S11 covers only one of five places that carry the study total. claims.md S11 lists Supplementary Table 1's Total row and its caption, and summary item 3 calls it one place. Grepping the accepted text finds 50,835 in four more places, none of them a claims row: (a) the 06_Supplementary_Information.docx legend 'Supplementary Figure 1 |' ('The 12 experiments total 50,835 evaluations'), also in manuscript/submission/supplementary/Supplementary_Figure_1_caption.md; (b) the letter, Reviewer 2, Comment 2, paragraph opening 'What this changes in the manuscript. The three-draw campaign adds 12,420' ('the submitted manuscript total 37,449, so the study now totals 50,835'); (c) the letter, Reviewer 4, Comment 2g, paragraph opening 'The manuscript now defines what an evaluation is' ('contribute 37,449: 34,705 scored answer evaluations ... giving 50,835'). With 3,520, each total moves by +220 (51,055). Whether the 37,449 subtotal of already-counted experiments moves too, to 37,669, needs a decision. The 'more than 50,000' phrasing (abstract, Introduction, Methods data availability, letter) stays true and could be listed as matches.
- R2. F2. R1 (Reviewer 1, Comment 1.2, the abstract quoted in the letter) covers only the 73.8% to 6.2% half. The quoted sentence also carries 'the benefit of querying installed libraries depends on the model', which A46 tracks for the manuscript abstract but no row tracks for the letter.
- R3. F3. Methods, Statistics paragraph opening 'Hypothesis tests on the primary outcome, pass or fail at a threshold' has no row. Its code-generation method sentences ('Whether code-generation pass counts depend on strategy and model was tested with Pearson's χ² test of independence on the strategy by model table of pass counts', and the upper-tail χ² and likelihood-ratio tests) are not tracked. S447 computes the Pearson test but not the likelihood-ratio test.
- R4. F4. The passing-side add_cell-as-text tally does not follow the definition the code cites. call_flags matches any call_site containing 'step_executor', including step_executor.py:607, the extra-candidate call inside _judge_cell_candidates. The docstring cites the audit A5/F35 tally (AUDIT_2026-10-16/COUNTERCHECKS.md:306-318), which counts only step_executor.py:357 execute_step. Either state the wider definition or restrict it to execute_step. (Counts as of 16 October, 1,802 attempts: 3 passing under the narrow definition against 5; not recomputed here.)
- R5. F5. The status counting was inconsistent (L5 counted under 'matches' for its '20 matches' clause, M2 and R5 not). Addressed in this regeneration by rule: every row is counted once, under its first status, and rows carrying a second status are listed apart.
- R6. F6. The working view's per-strategy panel (`S447 draw`, `draw_plate`) has no strategy labels. The plate (`S447 figure`) does not have this panel; its a and b both carry the strategy names.
