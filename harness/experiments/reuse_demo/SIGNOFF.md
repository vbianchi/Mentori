# Reuse demonstration in plant science: answer key for sign-off

Decision D74: the reuse claim is shown once, on a corpus that is not ours, inside the life sciences. This is the five-question key on five open-access papers about lettuce downy mildew resistance. Each question is in one of answer key v2.4's answer types (2 extractive, 1 synthesis, 1 refutation, 1 not answerable). Claude drafted it and you sign off its content.

- **Status: signed off by Valerio Bianchi, 16 October 2026 (D75).** Q1 to Q3 below were decided as recommended (cards Q53, Q54, Q55 of `experiments/fix_design/decisions_round3.html`). The signed-off key is `experiments/reuse_demo/key_v1.json`; `key_draft.json` (draft 3) holds the same records under the draft header. The one content change from draft 2 is Q2: note (2) of PB_003 keeps the corpus part and drops the outside date. Rebuild both in one command from the repo root: `uv run python experiments/reuse_demo/build_key.py`. The build refuses to write if any quote is not on its page or any key concept is not inside its quote.
- Quote check: `uv run python experiments/reuse_demo/check_quotes.py experiments/reuse_demo key_v1.json` (without the file name it checks `key_draft.json`). Last run, 16 October after D75: `key_v1.json: TOTAL support entries: 78; defects: 0`, and the same for `key_draft.json`. Every quote is on its page once and on no other page.
- Quotes keep the PDF text layer exactly, including its faults ("ofDm3", "signiﬁcantly", "QTL 3 QTL" for QTL x QTL). Page numbers count from the first page of each PDF.

**What you were asked to judge**, besides the content as a whole (decided 16 October, D75, each as recommended):

- **Q1 (PB_003).** The key reads BLR38 as fitting Giesbers' suppression explanation only. It does not count BLR38 as a case of "a second unlinked gene is required for resistance", because both BLR38 loci are needed for recognition itself, and resistance maps with recognition. Do you agree? *Decided (Q53): agreed; the reading and note (1) stand.*
- **Q2 (PB_003).** Giesbers writes "older" isolates. The corpus does not date the races, so the key notes from outside it that Bl:29 to Bl:31 were nominated after IBEB's 30 November 2012 meeting (HortiDaily, 13 August 2013). Keep this note, or drop it as outside the corpus? *Decided (Q54): the corpus part is kept ("the corpus does not date Bl:22 to Bl:31, so an answer should not call them older"); the outside date and the conclusion drawn from it are dropped.*
- **Q3 (PB_004).** The paper names eight 3:1 populations but then calls them "nine". The key states eight. Is that right? *Decided (Q55): eight, as the text names them; note (a) keeps the paper's "nine" and the likely ninth row.*


## PB_001: QTLs in Grand Rapids x Iceberg (Simko 2013)

**Question.** In the Grand Rapids x Iceberg recombinant inbred line population, which QTLs for downy mildew resistance were found, which legacy cultivar contributes the resistance allele at each, and do any of them map to the known clusters of Dm genes?

**Answer type.** **Extractive** (category factual_recall). One paper, Simko 2013, states every part of the answer in a few sentences; nothing has to be combined across papers.

**Short answer.** Three QTLs. qDM2.1 on LG 2b and qDM5.1 on LG 5a were significant in individual experiments and were effective in field experiments both in Salinas, California and in the Netherlands; the alleles for elevated resistance at both come from cultivar Iceberg. A third QTL, qDM9.1 on linkage group 9, was found only by the mixed-model analysis of all experiments together (LOD 0.9 to 2.1 when experiments were analysed separately); its additive effect was about 60% to 75% of those of qDM5.1 and qDM2.1, and its resistance allele comes from Grand Rapids. None of the three is located in the clusters of known Dm genes; the LG 2b QTL is well separated from the Dm cluster on LG 2a. No QTL x QTL or QTL x environment interaction was detected.

**Key concepts** (quote number in brackets). "qDM2.1" (0); "qDM5.1" (0); "originate from cultivar Iceberg" (1); "qDM9.1" (2); "originate from cultivar Grand Rapids" (3); "Neither of the QTLs mapped to the clusters of known Dm genes" (7); "well separated from the Dm gene cluster" (9).

**min_core.** 5

**Supporting quotes.**

0. Simko 2013, p1: "We developed a population of recombinant inbred lines (RILs) originating from a cross between these two legacy cultivars, constructed a linkage map, and identified two QTLs for resistance on linkage groups 2 ( qDM2.1) and 5 (qDM5.1) that determined resistance under field conditions in California and the Netherlands."
1. Simko 2013, p1: "Alleles conferring elevated resistance at both QTLs originate from cultivar Iceberg."
2. Simko 2013, p1: "An additional QTL on linkage group 9 (qDM9.1) was detected through simultaneous analysis of all experiments with mixed-model approach."
3. Simko 2013, p1: "Alleles for elevated resistance at this locus originate from cultivar Grand Rapids."
4. Simko 2013, p4: "The two QTLs were located on LG 2b ( qDM2.1) and LG 5a ( qDM5.1)."
5. Simko 2013, p4: "This QTL was not detected as significant when experiments were analyzed separately, with LOD scores ranging from 0.9 to 2.1."
6. Simko 2013, p4: "The additive effect of this QTL assessed on combined data was 0.088 what is ca. 60% to 75% of the additive effects of QTLs qDM5.1 and qDM2.1, respectively."
7. Simko 2013, p4: "Neither of the QTLs mapped to the clusters of known Dm genes."
8. Simko 2013, p7: "None of qDM2.1, qDM5.1,o r qDM9.1 is located in these resistance gene clusters."
9. Simko 2013, p7: "The QTL on LG 2b is well separated from the Dm gene cluster on LG 2a."
10. Simko 2013, p7: "Two significant QTLs for downy mildew resistance were detected in the present study when experiments were analyzed individually."
11. Simko 2013, p7: "The two QTLs were effective both in Salinas, California and The Netherlands field experiments."
12. Simko 2013, p4: "No significant QTL 3 QTL or QTL 3 environment interaction was detected for these three QTLs at P # 0.001."

**Notes in the key** (`question_issues`). The paper uses "QTLs" for two levels of evidence. qDM2.1 and qDM5.1 were significant in individual experiments; qDM9.1 was significant only in the mixed-model analysis of all seven experiments. An answer that names only the two main QTLs is incomplete but not wrong in substance. The page 4 sentence "Neither of the QTLs mapped to the clusters of known Dm genes" is about the two main QTLs; page 7 extends it to all three (evidence 8). The key concept for the clusters points at the page 4 sentence because the page 7 one carries a text-layer artifact (",o r"). Linked markers, if an answer gives them: BYET and BISR for qDM2.1, AFLP E45/M49-286.64 for qDM5.1 (page 4). The paper places qDM2.1 in the same region as rbq5 (quantitative resistance from L. saligna), which is context, not part of the answer.


## PB_002: RGC2B RNAi triggers and Dm16 (Christopoulou 2015)

**Question.** In the RNAi tester stocks for the RGC2 family at MRC2, which Dm specificities were abrogated by the trigger sequence from the NB-encoding domain of RGC2B and which by the LRR-derived trigger, and what did the authors infer about Dm16 from the difference?

**Answer type.** **Extractive** (category technical). One paper, Christopoulou 2015, gives the answer in its page 10 prose and its Table 1; the reader lifts it out.

**Short answer.** The NB-derived RGC2B trigger abrogated Dm3, Dm6 and Dm18. The LRR-derived trigger abrogated Dm3, Dm14, Dm16 and Dm18, and also Ra (resistance to root aphid); the LRR result is from Wroblewski et al. 2007. So Dm3 and Dm18 were lost with both triggers, Dm16 only with the LRR trigger, and Dm6 only with the NB trigger; Dm14 was lost with the LRR trigger and was not tested with the NB construct. Dm2 and Dm15 were tested with both constructs and lost with neither, and Dm1 was tested with the LRR construct and not lost (Table 1). Because NB domains are usually more conserved than LRR domains, the authors found this surprising and inferred that Dm16 is a chimeric Type I gene whose LRR domain is more closely related to Dm3 than to Dm6, but whose NB domain is more distantly related.

**Key concepts** (quote number in brackets). "Dm3 and Dm18 were abrogated by trigger sequences derived from both the NB and LRR domains" (0); "Dm14 and Dm16 were abrogated by the LRR-derived trigger sequence" (0); "Dm6 was compromised by the NB-derived trigger sequences" (1); "chimeric Type I gene" (2); "more closely related to Dm3 than Dm6" (2); "Dm14, Dm16, Dm18" (3).

**min_core.** 5

**Supporting quotes.**

0. Christopoulou 2015, p10: "Dm3 and Dm18 were abrogated by trigger sequences derived from both the NB and LRR domains ofDm3; however, Dm14 and Dm16 were abrogated by the LRR-derived trigger sequence but not the NB-derived trigger sequence (Dm14 was not tested with the NB-RNAi construct)."
1. Christopoulou 2015, p10: "Conversely, Dm6 was compromised by the NB-derived trigger sequences but not those derived from the LRR."
2. Christopoulou 2015, p10: "This was surprising because NB domains tend to be more conserved than LRR domains; this suggests thatDm16 is a chimeric Type I gene with a LRR domain that is more closely related to Dm3 than Dm6 but with a more distantly related NB domain."
3. Christopoulou 2015, p2: "A fragment of the LRR-encoding sequence of RGC2B used as the trigger sequence for RNA interference (RNAi) abrogated the resistance mediated by not only Dm3 but also Dm14, Dm16, Dm18,a n d Ra, suggesting that these linked resistance phenotypes also are encoded by RGC2 family members (Wroblewski et al. 2007)."
4. Christopoulou 2015, p4: "RGC2B_LRR_RNAie (chr 2) RGC2B 11/20 RGC2 Dm1 , Dm3, Dm2, Dm6, Dm14, Dm15, Dm16, Dm18, Ra Dm3, Dm14, Dm16, Dm18, Ra pGollum"
5. Christopoulou 2015, p4: "RGC2B_NB_RNAi (chr 2) RGC2B 12/20 RGC2 Dm2 , Dm3, Dm6, Dm15, Dm16, Dm18 Dm3, Dm6, Dm18 pGollum"
6. Christopoulou 2015, p10: "The two cv. Diana transgenics with the greatest levels of silencing were crossed to different genotypes to test forDm2, Dm6, Dm15, Dm16, and Dm18 speciﬁcities."
7. Christopoulou 2015, p8: "Eight Dm genes and resistance to root aphid (Ra) are clustered near one end of chromosome 2 that genetically de ﬁne the borders of MRC2 (McHale et al. 2009) ( Table S2 )."

**Notes in the key** (`question_issues`). (1) The page 10 sentence is loosely worded, not contradictory: "but not the NB-derived trigger sequence" is true of Dm16, and the parenthesis says Dm14 "was not tested with the NB-RNAi construct". The list of specificities tested with the NB transgenics (page 10) and the Table 1 NB row both leave Dm14 out. The answer treats Dm14 as lost with the LRR trigger and untested with NB. (2) The LRR result (Dm3, Dm14, Dm16, Dm18, Ra) was published earlier (Wroblewski et al. 2007) and is restated here; the NB construct is this paper's. (3) The prose names Dm2 and Dm15 among the specificities tested with the NB transgenics; only Table 1 states that they were not lost, and only Table 1 shows Dm1 tested with the LRR construct. (4) The figure 4 caption on page 11 calls the Dm3 gene "RGC2DB" while the text calls it RGC2B; the question uses the text's name.


## PB_003: BLN08 and BLR38, recognition without Bl:24 resistance (Giesbers 2017, Pelgrom 2019)

**Question.** Two Bremia lactucae effectors cloned from race Bl:24, BLN08 in Lactuca saligna and BLR38 in L. serriola LS102, trigger a hypersensitive response, yet recognition of neither co-segregates with Bl:24 resistance. Comparing the two studies, how is each recognition inherited, where does it map relative to the major resistance clusters, and how do the BLR38 results bear on the explanations Giesbers et al. give for effector recognition that does not co-segregate with resistance?

**Answer type.** **Synthesis** (category cross_document). Neither paper answers alone. Giesbers 2017 gives BLN08 and the list of explanations; Pelgrom 2019 gives BLR38, which came later. Judging how BLR38 bears on Giesbers' explanations needs both.

**Short answer.** BLN08 (Giesbers et al. 2017) triggered an HR in 55% of L. saligna accessions. In BC1_CGN05318 the response was mapped as one dominant gene on chromosome 8 (20 to 33 cM), and in CGN05271 and CGN05318 it co-localizes with MRC8A to B, a region with 42 NLR-encoding genes and no known Dm gene. It did not co-segregate with Bl:24 resistance, which in CGN05318 came from a separate dominant R gene on chromosome 1 (32 to 73 cM, overlapping MRC1). BLR31, by contrast, did co-segregate with Bl:24 resistance and mapped to MRC2. Giesbers et al. list explanations for recognition without resistance: other effectors of the isolate suppress the resistance, so the R gene may be effective against "older" isolates in which the suppressors have not yet evolved; a second unlinked gene is required for resistance; a second tightly linked gene, as in NLR pairs; the R gene targets another pathogen; poor effector translocation; mis-timed expression; or incomplete resistance, which they exclude for BLN08. BLR38 (Pelgrom et al. 2019) recognition in L. serriola LS102 needs two unlinked, semi-dominant loci (F2 7:4:5, unresponsive : chlorosis : necrosis), one on chromosome 4 partly overlapping the upstream border of MRC4 and one on chromosome 8 just downstream of MRC8A; plants lacking either locus never responded. Recognition is not linked to Bl:24 resistance, which in LS102 is Dm17 at the top of chromosome 1, but it is linked to resistance against Bl:22, Bl:23, Bl:26, Bl:28 and Bl:31, and resistance and recognition map to the same markers. Pelgrom et al. explain the missing Bl:24 link by suppression: Bl:24 is thought to suppress recognition of, or response to, at least five of its own effectors, but not the one recognized by Dm17. So BLR38 fits the suppression explanation: the resistance works, but not against the effector's own race. The corpus does not say whether the five races are older than Bl:24. The two-locus requirement concerns recognition itself, so BLR38 is not a case of Giesbers' second unlinked gene required for resistance. Pelgrom et al. suggest the two loci may be a sensor and helper NLR pair, or an R protein and an effector target; this relates to Giesbers' NLR-pair explanation, though there the second gene is tightly linked and the BLR38 loci are unlinked. In both systems Bl:24 resistance maps to chromosome 1, apart from the effector-recognition locus.

**Synthesis statement** (numbers are the quotes below). Giesbers et al. (paper 04) map BLN08 recognition in L. saligna as one dominant gene on chromosome 8 that co-localizes with MRC8A to B, a region with NLR genes and no known Dm gene, and find it unlinked to Bl:24 resistance [0, 1, 2, 3, 4, 5]; Bl:24 resistance in that population is a separate R gene on chromosome 1 overlapping MRC1 [6, 7], and BLR31, unlike BLN08, is linked to Bl:24 resistance and maps to MRC2 [16, 31]. They list explanations for recognition without resistance, suppression by other effectors of the isolate with the R gene effective against older isolates, a second unlinked or tightly linked gene, another pathogen as the R gene's target, translocation and timing, and exclude incomplete resistance for BLN08 [9, 10, 11, 12, 13, 14, 15]. Pelgrom et al. (paper 05) find that BLR38 recognition in L. serriola LS102 needs two unlinked semi-dominant loci, segregating 7:4:5, partly overlapping MRC4 on chromosome 4 and just downstream of MRC8A on chromosome 8 [18, 19, 20, 21, 22], which they contrast with paper 04's single loci [27]. BLR38 recognition is unlinked to Bl:24 resistance, which is Dm17 on chromosome 1, but linked to resistance against five other races, and resistance co-maps with recognition [17, 24, 25, 23]. Paper 05 lists BLN08 among effectors whose recognition is unlinked to Bl:24 resistance and attributes this to suppression by Bl:24 [26, 28]. BLR38 therefore fits paper 04's suppression explanation, while its second locus is needed for recognition, not for resistance after recognition, so it does not illustrate the second-unlinked-gene explanation; paper 05's sensor and helper or guardee models [29, 30] bear on paper 04's NLR-pair explanation, although the BLR38 loci are unlinked. In both papers Bl:24 resistance maps to chromosome 1 [7, 24].

**Key concepts** (quote number in brackets). "55% of the L. saligna accessions" (0); "dominant gene on C8" (2); "co-localized with MRC8" (4); "other effectors in this isolate suppress the resistance response" (9); "both required to mediate the recognition of BLR38" (20); "7 : 4 : 5" (21); "upstream border of MRC4" (22); "just downstream of MRC8A" (22); "maximum LOD scores at the same marker positions" (23); "corresponding to the reported location of Dm17" (24); "Bl:22, Bl:23, Bl:26, Bl:28 and Bl:31" (25); "suppress the recognition or response to at least five Bl:24-derived effectors" (28).

**min_core.** 5

**Supporting quotes.**

0. Giesbers 2017, p1: "BLN08 induced a hypersensitive response (HR) in 55% of the L. saligna accessions, but responsiveness did not co -segregate with resistance to Bl:24."
1. Giesbers 2017, p8: "In BC1_CGN05318, a range of responses to BLN08 from 0.3 to 1.7 was observed in 32 (53%) of 60 plants (Table S4)."
2. Giesbers 2017, p8: "The response was mapped as a dominant gene on C8 from 20 to 33 cM."
3. Giesbers 2017, p8: "For both L. saligna accessions CGN05271 and CGN05318, the gene causing responsiveness to BLN08 may overlap with resistance cluster MRC8A or B in L. sativa cv Salinas (Fig. 5)."
4. Giesbers 2017, p9: "However, the response to BLN08 was mapped to C8 and co-localized with MRC8(A –B) on C8 in L. sativa."
5. Giesbers 2017, p9: "MRC8A and MRC8B contain 42 NLR-encoding genes (Christopoulou et al., 2015) without known Dm genes (Parra et al., 2016)."
6. Giesbers 2017, p8: "Instead, an R gene on C1 that was not associated with BLN08 responsiveness was identiﬁed in L. saligna CGN05318."
7. Giesbers 2017, p8: "This gene mapped on C1 between 32 –73 cM, which overlaps with MRC1 in L. sativa cv Salinas (Fig. S4)."
8. Giesbers 2017, p8: "Average responses to effectors were signiﬁcantly higher (P < 0.001) for plants with two L. saligna alleles compared with plants with one L. saligna allele in all accessions, except for CGN05310 ( P > 0.1) (Fig. S5)."
9. Giesbers 2017, p9: "A potential explanation for the lack of co-segregation between responsiveness to an effector and resistance is that the R gene is not functional against the B. lactucae isolate from which the effector has been cloned, because other effectors in this isolate suppress the resistance response (King et al., 2014; Teper et al., 2014)."
10. Giesbers 2017, p9: "It is possible that the R gene is effective against older downy mildew isolates, in which the R gene-suppressing effectors have not yet evolved."
11. Giesbers 2017, p9: "Another possibility is that a second unlinked gene is required for resistance (Cooley et al., 2000; Kachroo et al., 2000)."
12. Giesbers 2017, p9: "Or, a functional version of a second tightly linked gene, as in NLR pairs (Cesari et al., 2014; Williams et al., 2014), may be required as an inducer of disease resistance signalling."
13. Giesbers 2017, p9: "The R gene might also confer resistance against another pathogen and recognize the downy mildew effector as a side effect."
14. Giesbers 2017, p9: "Other explanations for the absence of co-segregation between responsiveness to an effector and disease resistance may be a lack of proper effector translocation in the host, mis-timed expression of the effector or the R gene, or incomplete resistance mediated by the R gene (Krasileva et al., 2011; Goritschnig et al., 2012)."
15. Giesbers 2017, p9: "The latter explanation can be excluded, as the average resistance level of BLN08-responsive BC1 plants was not signiﬁcantly lower than that of BLN08-nonresponsive BC1 plants."
16. Giesbers 2017, p9: "The induced response to BLR31 in a narrow range of accessions was associated with Bl:24 resistance, whereas the response to BLN08 in a broad range of accessions was not."
17. Pelgrom 2019, p1: "The recognition of effector BLR38 in Lactuca serriola LS102 did not co-segregate with resistance against race Bl:24, but was linked to resistance against multiple other B. lactucae races."
18. Pelgrom 2019, p1: "Two unlinked loci are both required for effector recognition and are located near known major resistance clusters."
19. Pelgrom 2019, p5: "In the absence of at least one of the L. serriola LS102 loci at either chr 4 and/or chr 8 (aabb, AAbb, aaBB, aaBb, Aabb), plants were, without exception, unresponsive to BLR38 (Fig. 3b)."
20. Pelgrom 2019, p5: "In conclusion, the L. serriola LS102 loci on chr 4 and chr 8 are semi-dominant and are both required to mediate the recognition of BLR38."
21. Pelgrom 2019, p5: "The observed requirement for both loci was confirmed by the segregation ratio in the F2 population, where the response segregates in a 7 : 4 : 5 (unresponsive : chlorosis : necrosis) ratio (tested ratio, 7 : 4 : 5; χ2 = 0.89; df = 2; 95% confidence cut-off χ2 ≤ 5.991)."
22. Pelgrom 2019, p8: "The smallest mapping interval on chr 4 partially overlapped with the upstream border of MRC4 (Fig. 7a), whereas the smallest mapping interval on chr 8 was located just downstream of MRC8A (Fig. 7b)."
23. Pelgrom 2019, p8: "Mapping of either disease resistance or BLR38 recognition resulted in maximum LOD scores at the same marker positions on chr 4 and chr 8, confirming previous results."
24. Pelgrom 2019, p7: "Disease resistance to Bl:24 was mapped to a single, highly significant peak at the top of chromosome 1 with a LOD score of 79 (Fig. 2c), corresponding to the reported location of Dm17 (Maisonneuve et al., 1994)."
25. Pelgrom 2019, p7: "In summary, these results demonstrate that the recognition of BLR38 is linked to resistance against races Bl:22, Bl:23, Bl:26, Bl:28 and Bl:31."
26. Pelgrom 2019, p9: "In addition, the recognition of effectors BLG01, BLG03, BLN06 and BLN08 was not genetically linked to resistance against Bl:24, whereas the recognition of BLR31 did provide resistance to Bl:24 (Giesbers et al., 2017; Stassen et al., 2013)."
27. Pelgrom 2019, p9: "Yet, our data contrasted with previously characterized B. lactucae effector responses that mapped to single loci (Giesbers et al., 2017; Stassen et al., 2013)."
28. Pelgrom 2019, p10: "Race Bl:24 is thought to suppress the recognition or response to at least five Bl:24-derived effectors, but not to that recognized by Dm17."
29. Pelgrom 2019, p10: "To determine whether the loci mediating BLR38 recognition constitute a ‘sensor’ and ‘helper’ NLR pair, sequencing of the corresponding regions in the L. serriola LS102 genome is required."
30. Pelgrom 2019, p10: "Alternatively, the loci mediating BLR38 recognition could constitute an R protein and an effector target."
31. Pelgrom 2019, p2: "BLR31 recognition also co-segregated with resistance to B. lactucae race 24 (Bl:24) and was mapped to MRC2 (Giesbers et al., 2017)."

**Notes in the key** (`question_issues`). (1) How far the papers compare. Pelgrom et al. cite Giesbers et al., contrast their two loci with Giesbers' single loci, list BLN08 among effectors unlinked to Bl:24 resistance, and adopt the suppression postulate. Matching BLR38 against each explanation in Giesbers' list is this key's own reading: it fits suppression; it is not an instance of "a second unlinked gene is required for resistance", because both BLR38 loci are needed for recognition itself and resistance co-maps with recognition. An answer saying BLR38 confirms the second-gene explanation is wrong. An answer linking Pelgrom's sensor and helper model to Giesbers' NLR-pair explanation is right if it notes the BLR38 loci are unlinked. (2) "Older". Giesbers et al. write "older downy mildew isolates". The corpus does not date Bl:22 to Bl:31, so an answer should not call them older. (3) Dominance. Giesbers et al. call the BLN08 response dominant but measured a dose effect too: two alleles gave higher responses than one in every accession except CGN05310, and in CGN05318 the ranges did not overlap (page 8). The difference the papers show is one locus against two loci both required, not dominant against semi-dominant. (4) Species differ: BLN08 was mapped in L. saligna (CGN05318 and CGN05271 progeny), BLR38 in L. serriola LS102; MRC positions in both papers are positions in the L. sativa cv. Salinas reference. (5) Both involve chromosome 8 near MRC8A, but Giesbers et al. give a genetic interval (C8, 20 to 33 cM, "may overlap with resistance cluster MRC8A or B") and Pelgrom et al. a physical one (just downstream of MRC8A). Neither paper claims the same locus, and an answer that equates them goes beyond the text. (6) BLN08 recognition in L. saligna CGN05947 was absent from its F1 and BC1 progeny (page 8), so "one dominant gene" holds for CGN05318 and CGN05271 progeny only. (7) Giesbers' explanations are written about lack of co-segregation in general; only the exclusion of incomplete resistance is tested on BLN08 data.


## PB_004: Segregation and MRC position of new resistances (Parra 2021)

**Question.** According to the Parra et al. study of eleven near-isogenic lines, every new downy mildew resistance it mapped segregated 3:1 in F2 as a single dominant Dm gene and mapped inside one of the major resistance clusters. Is this correct?

**Answer type.** **Refutation** (category out_of_domain, as for every v2.4 refutation question). The question carries a false premise in two parts; the right answer is "No", with the text that contradicts each part.

**Short answer.** No, on both counts. Segregation: eight F2 populations (from UC02202, UC02204, UC02206, UC07105, UC07106, UC12100, UC12102 and UC12103) fitted 3:1, one dominant gene, UC07106 only as the closest fit to a ratio that deviated from simple Mendelian ratios. The populations from UC07108 and UC12101 segregated 9:7, consistent with two dominant genes being required for resistance; the two genes in each line are genetically unlinked, so the authors think them unlikely to be NLR pairs. The population from UC07107 segregated 1:3, consistent with a recessive gene. Position: the resistances to isolate C11O1326 in UC02202, UC02204, UC02206, UC12100 and UC12103 mapped outside the MRCs. Inside MRCs were UC07107's recessive gene (MRC1), UC07106's resistance (MRC1, a region of about 40 Mb; the authors suspect the gene itself lies in sequence missing from the reference genome), the resistance of UC07105 and UC12102 (MRC4), the two genes of UC07108 (MRC2 and MRC4) and of UC12101 (MRC1 and MRC2, the chromosome 2 gene supported by only a few markers), and a second gene in UC12103, for resistance to isolate C15L1691 (MRC1). So UC12103 has one resistance outside the MRCs and one inside MRC1. All F2 populations were screened with isolate C11O1326 except UC07108's, screened with C13O1407 because C11O1326 was virulent on it.

**Key concepts** (quote number in brackets). "9:7" (0); "two dominant genes being required for resistance" (0); "recessive resistance gene" (1); "1:3" (1); "mapped outside the MRC regions" (4); "genetically unlinked" (13).

**min_core.** 5

**Supporting quotes.**

0. Parra 2021, p5: "The F2 populations derived from UC07108 and UC12101 showed a segregation ratio of 9:7, consistent with two dominant genes being required for resistance."
1. Parra 2021, p5: "The population derived from UC07107 had a segregation ratio of 1:3 between resistant and susceptible individuals, consistent with the presence of a recessive resistance gene."
2. Parra 2021, p5: "The F2 populations derived from UC02202, UC02204, UC02206, UC07105, UC07106, UC12100, UC12102, and UC12103 showed a segregation ratio of 3:1 between resistant and susceptible individuals, consistent with one dominant resistant gene conferring resistance to downy mildew."
3. Parra 2021, p5: "The F2 population derived from UC07108 was screened for resistance to B. lactucae isolate C13C1407 rather than C11O1326 because the latter isolate was virulent on UC07108."
4. Parra 2021, p5: "The resistances to C11O1326 present in UC02202, UC02204, UC02206, UC12100, and UC12103 mapped outside the MRC regions (Fig. 3)."
5. Parra 2021, p5: "For the resistance genes present in the F2 populations derived from UC07108 and UC12101, which had segregation ratios of 9:7, the resistances were mapped to MRC2 and MRC4, and MRC1 and MRC2, respectively."
6. Parra 2021, p5: "The recessive resistance to B. lactucae isolate C11O1326 present in UC07107 was positioned inside MRC1, while the resistance to the same isolate present in UC07105 and UC12102 was positioned inside MRC4."
7. Parra 2021, p4: "UC07106 C11O1326 90R/44S ~3:1 3.59 1 Dominant C15L1752 96 MRC1 R42"
8. Parra 2021, p8: "For UC07106, a ~ 40 Mb region in MRC1 was significantly associated with resistance to isolate C11O1326 (Supplementary Fig. 2), although not all the susceptible individuals had a homozygous susceptible genotype, indicative of incomplete penetrance of this resistance."
9. Parra 2021, p8: "Segregation in the Salinas x UC07106 F2 population deviated from simple Mendelian expected ratios; however, the closest fit was to a 3:1 segregation ratio, consistent with the presence of a dominant resistance gene."
10. Parra 2021, p8: "Therefore, we hypothesize that the resistance gene in line UC07106 is located in a chromosomal region that is not present in the reference genome."
11. Parra 2021, p5: "Moreover, we found an additional resistance gene in UC12103 that confers resistance to C15L1691, which was positioned inside MRC1."
12. Parra 2021, p8: "Two NILs, UC07108 and UC12101, had an F2 segregation ratio that indicates that two dominant genes are required for the resistance phenotype."
13. Parra 2021, p8: "The two genes in both lines are genetically unlinked, making it unlikely for them to be NLR pairs."
14. Parra 2021, p8: "However, the second gene was mapped to Chr2, with only a few markers to support this location."

**Notes in the key** (`question_issues`). False premise with two parts, both contradicted by paper 01 (Parra et al. 2021, TAG). (1) Not all 3:1: two 9:7 populations and one 1:3 population. (2) Not all inside MRCs: five resistances to C11O1326 mapped outside. Inconsistencies in the paper: (a) page 5 lists eight 3:1 populations by name, then says "From the nine populations with simple Mendelian segregation (3:1), six had resistance that mapped to Chr 1, while two populations had resistance that mapped to Chr 4" (six plus two is eight). Table 2 has nine 3:1 rows, counting UC12103's second gene (22R/10S), which may be the ninth. The key states eight populations, as named. (b) For UC07106 the page 5 prose says only "a region in Chr 1"; Table 2 and page 8 put it in MRC1. (c) The UC07108 isolate is printed C13C1407 in the text and C13O1407 in Table 2. The category follows v2.4, where all ten refutation questions carry category out_of_domain.


## PB_005: The effector of Dm3 (no paper answers it)

**Question.** Which Bremia lactucae effector is recognized by the cloned Dm3 resistance protein (RGC2B), and does it carry an RXLR motif?

**Answer type.** **Not answerable** (category out_of_domain, as in v2.4). The topic is in the corpus's domain and the papers come close, but none names the effector Dm3 recognizes.

**Short answer.** Not answerable from the five papers. They say Dm3 is RGC2B, an NLR gene in MRC2 on chromosome 2, and test Dm3 with isolate IM25P11, listed as carrying Avr3, but no paper names the effector protein that Dm3 recognizes or describes its motifs.

**Key concepts.** None, as for every not-answerable question in v2.4.

**min_core.** null (not answerable)

**What was searched.** Searched, case-insensitive, over the page text of all five papers: "Dm3", "Avr3", "RGC2B" and "RGC2DB", "RXLR", "avirulen", "cognate", "recognized in" and "recognized by", "BLG0", "Dm2". What came closest, and why it is not the answer:

- Dm3 is RGC2B (Christopoulou p2) and is tested with isolate IM25P11 "(Avr3)" (Christopoulou Table 2, p6). That names the isolate's avirulence, not a protein.
- **Trap 1.** BLR31 (RXLR) is recognized by an *L. saligna* gene in the Dm3 region of MRC2 (Giesbers p5). The paper calls the locus new for *L. saligna* and possibly an NLR gene. No paper identifies it with Dm3 or tests BLR31 on Dm3 or RGC2B.
- **Trap 2.** BLG03 is recognized in lines carrying Dm2, not Dm3 (Pelgrom p2).
- **Trap 3.** Cv. Ninja carries Dm3, Dm11 and Dm36 and gives an HR to AvrB, AvrRpm1 and AvrRpt2 (Christopoulou Table 2, p6). These are bacterial effectors, and Table 1 (p3) shows their HR silenced by a chromosome 1 RGC1 construct.
- Outside the corpus, the expert reviewer searched the literature twice and found no source naming Dm3's *B. lactucae* effector. Two searches do not prove there is none.

**Supporting quotes.**

0. Giesbers 2017, p5: "The map interval overlaps with the Dm3 region within Major Resistance gene Cluster 2 (MRC2) in L. sativa cv Salinas (Christopoulou et al., 2015)."
1. Giesbers 2017, p9: "This resistance locus is new for the species L. saligna."
2. Giesbers 2017, p9: "All other R genes against B. lactucae that have been mapped in L. saligna are located on C1 ( n = 3) and C9 (n = 1) (Parra et al., 2016)."
3. Giesbers 2017, p9: "In L. sativa, MRC2 contains 61 NLR-encoding genes (Christopoulou et al., 2015) and nine known Dm genes, of which Dm3 is cloned and explained by an NLR gene (Parra et al., 2016)."
4. Christopoulou 2015, p2: "Sequencing ofdm3 mutants and transgenic complementation establishedRGC2B a st h eg e n ec o n f e rring Dm3 (Shen et al. 2002)."
5. Pelgrom 2019, p2: "Effectors BLG01 (GKLR motif), BLN08 (no RXLR motif) and BLR31 (RXLR motif) were specifically recognized in multiple L. saligna accessions."
6. Pelgrom 2019, p2: "Finally, BLG03 (GKLR motif) is recognized in L. sativa cv. Amplus and UCDM2 that harbour the resistance gene Dm2."
7. Christopoulou 2015, p6: "Diana Dm1, Dm3, Dm5/8, Dm7 IM25P11 (Avr3)"
8. Christopoulou 2015, p6: "Ninja Dm3, Dm11, Dm36 AvrB, AvrRpm1, AvrRpt2 CG1 (Avr36)"
9. Christopoulou 2015, p3: "QGF16M04_LRR_RNAid (chr 1) Lsa039421.1 (88%), RGC1 15/22 RGC1 Dm10 , Dm43, Dm5/8, Dm17, Dm45, Dm36 AvrB, Avrpm1, AvrRpt2 Dm5/8, Dm45, HR-AvrB, HR-AvrRpm1, HR-AvrRpt2 pGollum"

**Notes in the key** (`question_issues`). Plausible for the topic (a standard question about the best-studied Dm gene) and in the corpus's domain, but none of the five papers answers it. Searched, case-insensitive, over the page text of all five papers: "Dm3" (papers 02, 03, 04: cluster membership, cloning as RGC2B, RNAi abrogation, the Dm3 region of MRC2, the BLR31 map interval), "Avr3" (paper 03 Table 2, isolate IM25P11 only; paper 02 hits are Avr36, Avr37, Avr38), "RGC2B" and "RGC2DB" (paper 03 only, no effector), "RXLR", "avirulen" (paper 02: isolate phenotypes; paper 04: BLR31 as a candidate avirulence effector of its own L. saligna R gene), "cognate" (paper 04, BLR31 and its L. saligna R gene), "recognized in" and "recognized by", "BLG0" (BLG01, BLG03; BLG03 with Dm2), "Dm2". Three traps. (1) BLR31 (RXLR) is recognized by an L. saligna gene on C2 in the Dm3 region of MRC2. The paper calls the locus new for L. saligna (the first R gene mapped there in that species) and says it may be an NLR gene; the corpus neither identifies this gene with Dm3 nor tests BLR31 against Dm3 or RGC2B. (2) BLG03 goes with Dm2, not Dm3. (3) Cv. Ninja carries Dm3, Dm11 and Dm36 and gives an HR to AvrB, AvrRpm1 and AvrRpt2, which are bacterial effectors (paper 03 Table 2 column "HR to Bacterial Effectors"; Table 1 shows these HRs silenced by a chromosome 1 RGC1 construct). Paper 04's germplasm included "a differential set of L. sativa cultivars with single dominant R genes" and BLR31 triggered an HR only in L. saligna accessions, which suggests but does not show that Dm3 lines do not recognize BLR31 (Table S1, which would show it, is not in the corpus). The expert reviewer searched the published literature twice and found no source naming Dm3's B. lactucae effector; two searches cannot prove there is none. The v2.4 category for not-answerable questions is out_of_domain.


## The five papers

| # | Title | First author, year | Journal | DOI | Licence |
|---|---|---|---|---|---|
| 01 | Identification and mapping of new genes for resistance to downy mildew in lettuce | Parra, 2021 | Theor Appl Genet 134:519-528 | 10.1007/s00122-020-03711-z | CC BY 4.0 (stated in the PDF, p9) |
| 02 | Identification of QTLs conferring resistance to downy mildew in legacy cultivars of lettuce | Simko, 2013 | Sci Rep 3:2875 | 10.1038/srep02875 | CC BY 3.0 Unported (PDF, p10) |
| 03 | Genome-Wide Architecture of Disease Resistance Genes in Lettuce | Christopoulou, 2015 | G3 | 10.1534/g3.115.020818 | CC BY 4.0 (PDF, p1) |
| 04 | Effector-mediated discovery of a novel resistance gene against Bremia lactucae in a nonhost lettuce species | Giesbers, 2017 | New Phytol 216:915-926 | 10.1111/nph.14741 | CC BY (the PDF gives no version; the manifest records 4.0, Europe PMC "cc by") |
| 05 | Recognition of lettuce downy mildew effector BLR38 in Lactuca serriola LS102 requires two unlinked loci | Pelgrom, 2019 | Mol Plant Pathol 20(2):240-253 | 10.1111/mpp.12751 | CC BY (the PDF gives no version; the manifest records 4.0, Europe PMC "cc by") |

Paper 04's title says "novel", a word on the editor's banned list. It is quoted here only as the paper's title.

## How long each step took

Times on 16 October, read from the files' modification times (`stat`). The start of step 1 and the end of step 3 are not recorded in any file and are estimates.

| Step | From | To | Time |
|---|---|---|---|
| 1. Corpus: Europe PMC lookups, manifest, download, page text | 00:10:39 (lookups saved) | 00:13:37 (page text written) | 3 min measured; choosing the topic before the lookups is not recorded (estimate: a few minutes after the D74 commit at 00:09:03) |
| 2. Key drafted (draft 1) | 00:13:37 | 00:20:05 (build script last saved) | 6.5 min measured |
| 3. Three reviews in parallel (quotes, answerability, expert) | 00:20:44 (review page dumps written) | before 00:26:12 | about 5 min, estimate (upper bound) |
| 4. Findings checked against the text, key rebuilt (draft 2), quote check rerun | 00:26:12 (first search script) | 00:33:19 (key written) | 7 min measured |
| 5. This file | 00:33:19 | 00:34:44 | 1.5 min measured; generated from the key by a script |
