<!-- provenance
{
 "script": "scripts/S599_key_v25_curation_hours.py",
 "script_sha256": "2f501a09bd8ea6cd6784d39fc125d2d8238b276d5fc8cd0b48da685aed3a85ae",
 "command": "uv run --frozen python scripts/S599_key_v25_curation_hours.py",
 "inputs_sha256": {
  "data/ground_truth_v2/agent_review_r2_r3_workflow_result.json": "24f912e11f3407d76940453bd79f76e8611dc51c0c9572a5a5b531096fc5ec0b",
  "data/ground_truth_v2/agent_review_workflow_result.json": "2ca82ded02689bfe2afb5bb705b8bb3eebe62125b615d6ac06d5784f0848ad1b",
  "data/ground_truth_v2/all_v2_1_workflow_result.json": "4c3eeb138f9c8eca38fcef8f59cec9fa757878ff8711bca18f8f9f7e59672abe",
  "data/ground_truth_v2/all_workflow_result.json": "0513b1f8a8634e30c216dc1da0910af260965af07608dc29d9f2e861616d9d86",
  "data/ground_truth_v2/concepts_conceptual_workflow_result.json": "cdc2b116b280e688019fe56bf131ac01f8322ea3d1be9711dc1319a6b9970d76",
  "data/ground_truth_v2/extractors_cde_workflow_result.json": "5055790f43962d02b87ce91eb59418dda57e99890475dca96861bd5d2589e1e4",
  "data/ground_truth_v2/pilot_workflow_result.json": "7b32a6eb563ee86ab436d46ec921ce7803470e29cca2528b73f3202a2c7e7e8b",
  "data/ground_truth_v2/replacements_workflow_result.json": "05ccc1c8918d728bab3da60f7895cde1154bfd9dd44a8a2dadd9b6535f1e48a1",
  "data/ground_truth_v2/rest_workflow_result.json": "d8ec2846d1dacf8cb5ca1e6b4aa817a370eb0656b5e2293a6d057ba6169b81ae",
  "data/ground_truth_v2/signoff_v2_2_workflow_result.json": "aec3f3b9bded225cfdc0834837dad6f526bcc910dcf652f67d5cf303c62ff281",
  "data/ground_truth_v2/sy018_v2_2_workflow_result.json": "27334e7b3f9a4d0f2c665b22a7265c3925d9314c0dd81f10fe544dcfa3323cbd",
  "response/ground_truth_v2/pilot_signoff.xlsx#docProps/core.xml": "205ab6ca55da1c5f6b400871232ad4d1b66db05a31810ecc1cf61a8a914f52f4",
  "response/ground_truth_v2/all_signoff.xlsx#docProps/core.xml": "3696058b7c470691d522d0fb5405f39f50c6767272c01affa2b7ae2a6ab7828b",
  "response/ground_truth_v2/replacements_signoff.xlsx#docProps/core.xml": "3159166aeca61f731c9d07108791703e8934d820082b55ec83385ac0deac8c5a",
  "response/ground_truth_v2/v2_2_review.xlsx#docProps/core.xml": "f4c56cf291dc222fe8c2114ef6951ec7dcd537cef4f39492c4e9f217a534c746",
  "response/ground_truth_v2/concept_premise_check_v1.xlsx#docProps/core.xml": "9416757f8d64f93784bef22c7512df4d76a1ab0409b820f1a21a2a61770c9e18",
  "response/ground_truth_v2/concept_premise_check_v2.xlsx#docProps/core.xml": "7a1da33c95d1cbc0cd0b5128db11e021e6ee2fc620b3ae9433390ddce2d0af76",
  "response/ground_truth_v2/concept_premise_check_v3.xlsx#docProps/core.xml": "1936b8522b9ba80337ff48e29c583f4249163fee4d2bc5d42591be41dac0113c",
  "response/ground_truth_v2/key_v2_5_review.xlsx#docProps/core.xml": "f85da496eee9139d21827ecf4b10559de9f70a43d1fb259f1663b6fd0e63b080",
  "data/ground_truth_v2/ground_truth_v2_5_as_v1.json": "a42161841980792f5da521819c97b16dc54999b45838b8eb87cd4315f798270a"
 },
 "model_calls": 0
}
-->

# S599: the curation effort for answer key v2.5, from its build records (CURATION, O1)

Reproduced first:

- (1) key v2.5: sha256 a4216184, 244 questions, 1,157 expected concepts (commit c1c13184)
- (2) rest workflow: '213 of 213 reconciled', 639 agents; pilot: '37 of 37 reconciled' (commit d4b8ec1d)

## Agent work (workflow records)

| workflow | agents | agent hours | clock span h | first start (UTC) | log |
|---|---|---|---|---|---|
| agent_review_r2_r3 | 500 | 2.36 | 0.17 | 2026-10-08T17:00:10Z | 500 of 500 reviewed; missing: none |
| agent_review | 250 | 1.32 | 0.10 | 2026-10-08T16:47:40Z | 250 of 250 reviewed; missing: none |
| all_v2_1 | | | | | no timing: records only |
| all | | | | | no timing: records only |
| concepts_conceptual | 150 | 0.98 | 0.08 | 2026-10-08T19:47:58Z | 50 of 50 reconciled |
| extractors_cde | 750 | 9.08 | 0.65 | 2026-10-08T14:54:34Z | 750 of 750 extractions returned |
| pilot | 111 | 1.47 | 0.13 | 2026-10-08T08:06:56Z | 37 of 37 reconciled; missing: none |
| replacements | 9 | 0.14 | 0.04 | 2026-10-08T14:22:34Z | 3 of 3 reconciled; missing: none |
| rest | 639 | 8.43 | 0.61 | 2026-10-08T08:37:02Z | 213 of 213 reconciled; missing: none |
| signoff_v2_2 | | | | | no timing: records only |
| sy018_v2_2 | | | | | no timing: records only |

In all: 2,409 agents in 7 workflows, 23.8 agent hours, 1.8 h of clock time (the workflows' spans added; agents ran in parallel).

## A person's time (workbook core properties)

| workbook | step | last saved by | created (UTC) | modified (UTC) | window h | reading |
|---|---|---|---|---|---|---|
| pilot_signoff.xlsx | v2 pilot sign-off sheet (37 questions) | openpyxl | 2026-10-08T09:15:36Z | 2026-10-08T09:15:36Z |  | last written by a tool: no time of a person's work |
| all_signoff.xlsx | v2 sign-off sheet (250 questions) | openpyxl | 2026-10-08T09:15:55Z | 2026-10-08T09:15:55Z |  | last written by a tool: no time of a person's work |
| replacements_signoff.xlsx | v2.1 replacement questions sign-off sheet | openpyxl | 2026-10-08T14:27:06Z | 2026-10-08T14:27:06Z |  | last written by a tool: no time of a person's work |
| all_v2_1_signoff.xlsx | v2.1 sign-off sheet (Valerio's 54 edits, applied in v2.2) |  |  |  |  | not opened (D168 forbidden list): no time read |
| v2_2_review.xlsx | v2.2 review sheet | openpyxl | 2026-10-09T17:06:53Z | 2026-10-09T17:06:53Z |  | last written by a tool: no time of a person's work |
| concept_premise_check_v1.xlsx | concept premise check, v1 layout | openpyxl | 2026-10-29T16:49:13Z | 2026-10-29T16:49:14Z |  | last written by a tool: no time of a person's work |
| concept_premise_check_v2.xlsx | concept premise check, v2 layout | openpyxl | 2026-10-29T17:01:26Z | 2026-10-29T17:01:27Z |  | last written by a tool: no time of a person's work |
| concept_premise_check_v3.xlsx | concept premise check, v3 (Valerio's calls, the input of key v2.5) | Bianchi, Valerio | 2026-10-29T17:29:48Z | 2026-10-30T11:40:58Z | 18.19 | created to last save spans more than 8 h (a night or more): it bounds nothing useful |
| key_v2_5_review.xlsx | key v2.5 draft review (Valerio's calls, D180) | Bianchi, Valerio | 2026-10-30T13:15:06Z | 2026-10-30T13:44:02Z | 0.48 | an upper bound on the person's time in the sheet (created to last save) |

A person's hours are not in the records. CURATION O1: Valerio confirms them.

## Timeline of the key's files (git author time)

- 2026-10-30T15:54:24+01:00 c1c13184 Key v2.5 final (data/ground_truth_v2/ground_truth_v2_5_as_v1.json, sha256 a4216184; 1,157 concepts; S504 --final, test 69/69); amendment 9 DRAFT for Valerio (completeness re-rated on the 36 items whos
- 2026-10-11T09:38:27+02:00 53dda7e2 O36 (Valerio, 11 October): CD_007 gets the five paper sentences its new short answer rests on (t-tests of log2(TPM + 1), the GEUVADIS sequencing-centre comparison, Polyester), evidence 26 to 30 from t
- 2026-10-11T09:22:45+02:00 dc754e42 Ground truth v2.4 (Q50, Valerio, 11 October 09:00): v2.3 with the 25 corrections verified in Q49, with Q52-Q54 as recommended (S398, gates K1-K7; an independent review matched all 25 records to the no
- 2026-10-11T00:28:01+02:00 a32c6cf4 Q48 (Valerio, 11 October 00:35): the Sarek key point (F1, 01_sarek_CO2) is "Docker and Singularity containers", shortened from "... as well as Conda environments" so answers naming the containers with
- 2026-10-11T00:20:08+02:00 1e0705a3 Q45 (Valerio, 11 October 00:00, "Fix the keys, add the fixes in the raters file"): ground truth v2.3 = v2.2 with the five errors found by the check of the 36 rated questions corrected (S396, gates K1-
- 2026-10-09T19:19:18+02:00 03440b4c Ground truth v2.2 frozen (Valerio, 9 October evening: review accepted as drafted; the ten choices resolve to the drafted versions): data/ground_truth_v2/all_v2_2.json, 250 records
- 2026-10-08T21:53:16+02:00 75c64533 Q4 (Valerio, 8 October): key concepts re-derived for the 50 conceptual questions (ideas a correct answer must state; numbers only when asked), two proposers and a reconciler each; all 322 proposed con
- 2026-10-08T16:27:39+02:00 d3adb45e Ground truth v2.1: OOD_011, CD_015 and SY_010 get new questions (D1, D2, 8 October), built by the same two-extractor-and-reconciler workflow and S364 checks (3 of 3 pass, 43 of 44 evidence sentences e
- 2026-10-08T11:16:10+02:00 d4b8ec1d Ground truth v2 for all 250 questions (separate set; v1 untouched): 213 more by workflow wf_b056c5ad-db7 (two blind extractors and a reconciler each; the 40 off-topic questions by a search of all 200 
