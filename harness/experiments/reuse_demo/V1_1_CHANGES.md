# I2 key v1.1: what changed from v1

Valerio, 25 October: "go with v1.1". The changes come from the 25 October re-read (`reread_2026-10-25.json`: fresh
readers checked each answer against its papers, and a second reader tried to refute every flag) and from D137. Only the
fixes confirmed by the second reader and kept in the verdict given to Valerio are applied. No fact of v1 was wrong, and
no conclusion changes.

- **Files.** `key_v1_1.json` is built by `build_key_v1_1.py` from `key_v1.json`. The signed-off `key_v1.json` and
  `build_key.py` are unchanged (key_v1.json sha256 fa76f092... before and after).
- **Status.** Signed off by Valerio on 26 October ("Go with it", Q-I2a, D153). The key file's `status` field says so
  since 27 October (only that field changed; sha256 `eb58a724...`, before `dccbd6b4...`). It is the key of the I2 run.
- **Quote check.** `check_quotes.py`: v1 has 78 support entries and 0 defects; v1.1 has 89 and 0 defects. The 11 new
  quotes are added at the end of each list, so every v1 evidence number still means the same.

## PB_001 (Simko 2013): the QTLs in Grand Rapids x Iceberg

- **Interaction sentence (p4).** Was: "No QTL x QTL or QTL x environment interaction was detected." Now: "... was
  significant at P ≤ 0.001", the paper's own test.
- **Note.** Was: no mention of the TIR-NBS-LRR gene. Now: page 4 places qDM5.1 near a gene that may encode a
  TIR-NBS-LRR protein. That gene is not a known Dm cluster, so an answer that mentions it does not contradict "not in a
  Dm cluster". New quote 13 (p4).

## PB_002 (Christopoulou 2015): the RGC2B RNAi triggers and Dm16

- **Concepts 2 and 3 (p10).** Was: only the first half of each contrast ("Dm14 and Dm16 were abrogated by the
  LRR-derived trigger sequence"; "Dm6 was compromised by the NB-derived trigger sequences"). Now they carry both halves:
  "... but not the NB-derived trigger sequence" and "... but not those derived from the LRR". The question asks what
  the authors inferred from the difference.
- **The chimera inference (p10).** Was: concept 5 "more closely related to Dm3 than Dm6". Now concept 5 names the LRR
  domain ("LRR domain that is more closely related to Dm3 than Dm6"), and a new concept 6 gives the other half ("with a
  more distantly related NB domain").
- **Old concept 6.** Was: "Dm14, Dm16, Dm18", which repeated concepts 1 and 2. Now dropped. Its quote (p2) stays as
  support.
- **Note (5).** Explains the above, and says an answer stating that Dm14 was not tested with the NB construct is right.
- **Unchanged.** The short answer, and min_core (it sets which corpus size the question runs at; it is not a pass mark).

## PB_003 (Giesbers 2017, Pelgrom 2019): BLN08 and BLR38

- **Joint mapping (Pelgrom p8).** Was: "and resistance and recognition map to the same markers", which reads as true
  for all five races. Now: "in F3 family #108 resistance to Bl:22 and BLR38 recognition map to the same markers on
  chromosomes 4 and 8". The synthesis statement is changed to match. New quote 32 (p8).
- **Chromosome 1 (Giesbers p6, p8).** Was: "In both systems Bl:24 resistance maps to chromosome 1". Now: in L. saligna
  CGN05318 and L. serriola LS102. In L. saligna CGN05271 resistance is probably quantitative, and BLN08-responsive
  plants were as susceptible to Bl:24 as cv. Olof. The synthesis statement is changed to match. New quotes 33 (p6) and
  34 (p8).
- **Note (8), points an answer gets credit for.**
  - Bl:23 and Bl:28 carry the same BLR38 allele as Bl:24 and are still resisted, and every BLR38 variant is still
    recognized (Pelgrom p8, p9). So Bl:24's escape is not in the effector sequence. New quotes 35 (p8) and 36 (p9). The
    sentence that names the three races as homozygous for the Bl:24 allele crosses the page 7 to 8 break with figure
    text between, so it is not quoted.
  - Pelgrom's "at least five" suppressed effectors follow page 9's list of four effectors unlinked to Bl:24 resistance,
    BLN08 among them, plus BLR38. The five are not named, but the count implies that Pelgrom apply the suppression
    idea to BLN08 too.
  - The BLR38 loci give strong resistance to Bl:22 (Fig. 6c, p8). That counts against the "another pathogen" and
    "incomplete resistance" explanations. New quotes 37 and 38 (p8).
- **Notes (9) and (10).** Record the two scope limits above.
- **Unchanged.** The reading that BLR38 fits suppression only (D75 Q53), and every key concept.

## PB_004 (Parra 2021): the eleven near-isogenic lines

- **UC07106's region (p8).** Was: "a region of about 40 Mb". Now: "about 40 Mb in the F2, narrowed to 31 Mb with F3
  families". New quote 15 (p8). Note (e) says an answer giving either size is right.
- **Note (d), Table 2's chi-square.** Was: no note. Now: Table 2 prints 3.59 for UC07106, but its counts (90R/44S
  against 3:1, expected 100.5 and 33.5) give 1.10 + 3.29 = 4.39. That is above 3.84 (1 df, P = 0.05), which agrees
  with the page 8 text: the segregation "deviated". An answer that calls UC07106 3:1 is not wrong.
- **Unchanged.** Eight 3:1 populations (D75 Q55), and the key concepts (no line names added).

## PB_005 (not answerable): Dm3's effector and its motif

- **A fourth trap.** Was: three traps. Now: four. BLR38, paper 05's effector, is RXLR-like with an RLLR motif (Table 1,
  p2). Its recognition maps to loci on chromosomes 4 and 8 (p4), not to MRC2, and paper 05 never mentions Dm3. New
  quotes 10 (p2) and 11 (p4).
- **D137, grading a hedged answer.** An answer that adds "probably an RXLR effector, as oomycete effectors often are"
  is acceptable only when it is clear that the answer is not in the papers and that there are no supporting data. An
  answer that gives RXLR, or any motif or effector, as the answer is wrong. The papers mention RXLR only as background,
  and paper 05 p2 lists recognized effectors without RXLR (BLG01 GKLR, BLN08).
- **Unchanged.** The short answer and the not-answerable type.

## Not applied (refuted by the second reader, or left out in the verdict)

- **PB_001.** A rule that a reversed donor fails the answer (the judge's Correctness score sees the expected answer);
  Iceberg as a Batavia; "respectively"; qDM9.1's footing; Dm13; seedling sporulation.
- **PB_002.** The Ra gloss; "inferred" against "suggests"; the cv. Diana context; the Discussion framing.
- **PB_003.** 83% for the chromosome 1 gene; "explain" read as a hypothesis; the dominant against semi-dominant note;
  gene dosage; CGN05947.
- **PB_004.** Line names in the key concepts; chromosome 1 for the five outside-MRC resistances; the C15L1691 isolate
  wording; UC07107's linkage drag.
- **PB_005.** The RGC2DB alias; the Avr3 wording; the out_of_domain label; the BLR31 screening.
