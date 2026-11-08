# S505: question-aware concept matchers (Q18, O3)

Written by `uv run python scripts/S505_question_aware_matcher.py` (script sha256 `179a80fbde63`, 2026-10-30T14:08:32Z). Inputs and their sha256 are in `results.json` under provenance. The rule is the docstring of `question_aware` in `scripts/S505_question_aware_matcher.py`; nothing in `concept_match_loose.py` or `concept_match_stem.py` changed.

Variant names: `<matcher>_Q<rule>_<empty>`. rule `all`: every remaining word must be in the answer; `need`: ceil(2/3) of the remaining words, the base matchers' own proportion. empty `a`: a concept whose content words are all in the question is not found; `b`: it is left out of the denominator. `<matcher>_base_b` is the base matcher on the pairs left under (b), for an equal comparison.

## M3. Free credit: the question scored as its own answer

205 answerable questions, 1191 concepts of the reviewed v2.5 key.

| matcher | concepts credited by the question alone |
|---|---:|
| exact | 18 of 1191 (1.5%) |
| loose | 77 of 1191 (6.5%) |
| stem | 85 of 1191 (7.1%) |
| loose_Qall | 0 of 1191 (0.0%) |
| loose_Qneed | 0 of 1191 (0.0%) |
| stem_Qall | 0 of 1191 (0.0%) |
| stem_Qneed | 0 of 1191 (0.0%) |

Still credited under a Q variant (0):

- none

Concepts with no remaining word under the loose removal (34 of 1191):

- 01_sarek_FR1: "BAM files, annotated VCF files and CNV files" (content words ['annotated', 'bam', 'cnv', 'files', 'vcf'])
- 06_star_aligner_FR1: "12-core server" (content words ['12', 'core', 'server'])
- 10_cutadapt_TE3: "2.66 GHz Intel Core 2 processor" (content words ['2', '2.66', 'core', 'ghz', 'intel', 'processor'])
- 10_cutadapt_TE3: "35 bp colour-space reads" (content words ['35', 'bp', 'colour', 'reads', 'space'])
- 13_lsd_nepal_FR1: "overall morbidity rate" (content words ['morbidity', 'overall', 'rate'])
- 13_lsd_nepal_FR1: "mortality rate" (content words ['mortality', 'rate'])
- 13_lsd_nepal_FR1: "case fatality rate" (content words ['case', 'fatality', 'rate'])
- 13_lsd_nepal_TE3: "Multivariable logistic regression analysis" (content words ['analysis', 'logistic', 'multivariable', 'regression'])
- 16_ppr_ethiopia_TE3: "purchased animals" (content words ['animals', 'purchased'])
- 18_fmd_review_CO2: "no FMDV carrier state in pigs" (content words ['carrier', 'fmdv', 'pigs', 'state'])
- 19_hpai_canada_FR1: "culled in Canada" (content words ['canada', 'culled'])
- 20_lsd_review_TE3: "cross-protection rate" (content words ['cross', 'protection', 'rate'])
- 21_livestock_gut_microbiome_review_FR1: "most abundant phyla" (content words ['abundant', 'most', 'phyla'])
- 26_gut_meat_quality_TE3: "finishing weight" (content words ['finishing', 'weight'])
- 29_16s_best_practices_FR1: "raw read number target" (content words ['number', 'raw', 'read', 'target'])
- 31_amr_one_health_FR1: "classified as innovative" (content words ['classified', 'innovative'])
- 31_amr_one_health_FR1: "32 antimicrobials in hospital development" (content words ['32', 'antimicrobials', 'development', 'hospital'])
- 31_amr_one_health_FR1: "In 2019" (content words ['2019'])
- 31_amr_one_health_TE3: "third- and fourth generation cephalosporins" (content words ['cephalosporins', 'fourth', 'generation', 'third'])
- 32_amr_livestock_environment_FR1: "if current trends continue" (content words ['continue', 'current', 'if', 'trends'])
- 32_amr_livestock_environment_FR1: "by 2050" (content words ['2050'])
- 32_amr_livestock_environment_TE3: "2020 to 2030" (content words ['2020', '2030'])
- 33_amr_food_animals_FR1: "not absorbed by the animals" (content words ['absorbed', 'animals'])
- 35_isse_framework_amr_FR1: "five evaluation levels" (content words ['evaluation', 'five', 'levels'])
- 37_data_driven_one_health_TE3: "Mollentze et al." (content words ['al', 'et', 'mollentze'])
- 38_one_health_africa_TE3: "low- and middle-income countries" (content words ['countries', 'income', 'low', 'middle'])
- 40_animal_agriculture_one_health_FR1: "zoonotic" (content words ['zoonotic'])
- 40_animal_agriculture_one_health_TE3: "by 2050" (content words ['2050'])
- 45_kenya_amr_digital_TE3: "Of the 17 surveillance sites" (content words ['17', 'sites', 'surveillance'])
- 48_myc_oncogene_FR1: "MYC-induced and repressed genes" (content words ['genes', 'induced', 'myc', 'repressed'])
- 48_myc_oncogene_FR1: "16 hours" (content words ['16', 'hours'])
- 50_4cseq_protocol_FR1: "reproducible 4C profiles" (content words ['4c', 'profiles', 'reproducible'])
- 50_4cseq_protocol_FR1: "Subsampling analysis" (content words ['analysis', 'subsampling'])
- 50_4cseq_protocol_TE3: "motifPosperc" (content words ['motifposperc'])

Concepts with no remaining word under the stem removal (37 of 1191):

- 01_sarek_FR1: "BAM files, annotated VCF files and CNV files" (content words ['annotated', 'bam', 'cnv', 'files', 'vcf'])
- 06_star_aligner_FR1: "12-core server" (content words ['12', 'core', 'server'])
- 10_cutadapt_TE3: "2.66 GHz Intel Core 2 processor" (content words ['2', '2.66', 'core', 'ghz', 'intel', 'processor'])
- 10_cutadapt_TE3: "35 bp colour-space reads" (content words ['35', 'bp', 'colour', 'reads', 'space'])
- 13_lsd_nepal_FR1: "overall morbidity rate" (content words ['morbidity', 'overall', 'rate'])
- 13_lsd_nepal_FR1: "mortality rate" (content words ['mortality', 'rate'])
- 13_lsd_nepal_FR1: "case fatality rate" (content words ['case', 'fatality', 'rate'])
- 13_lsd_nepal_TE3: "Multivariable logistic regression analysis" (content words ['analysis', 'logistic', 'multivariable', 'regression'])
- 16_ppr_ethiopia_TE3: "purchased animals" (content words ['animals', 'purchased'])
- 18_fmd_review_CO2: "no FMDV carrier state in pigs" (content words ['carrier', 'fmdv', 'pigs', 'state'])
- 19_hpai_canada_FR1: "culled in Canada" (content words ['canada', 'culled'])
- 20_lsd_review_TE3: "cross-protection rate" (content words ['cross', 'protection', 'rate'])
- 21_livestock_gut_microbiome_review_FR1: "most abundant phyla" (content words ['abundant', 'most', 'phyla'])
- 26_gut_meat_quality_TE3: "finishing weight" (content words ['finishing', 'weight'])
- 29_16s_best_practices_FR1: "raw read number target" (content words ['number', 'raw', 'read', 'target'])
- 31_amr_one_health_FR1: "classified as innovative" (content words ['classified', 'innovative'])
- 31_amr_one_health_FR1: "32 antimicrobials in hospital development" (content words ['32', 'antimicrobials', 'development', 'hospital'])
- 31_amr_one_health_FR1: "In 2019" (content words ['2019'])
- 31_amr_one_health_TE3: "third- and fourth generation cephalosporins" (content words ['cephalosporins', 'fourth', 'generation', 'third'])
- 32_amr_livestock_environment_FR1: "if current trends continue" (content words ['continue', 'current', 'if', 'trends'])
- 32_amr_livestock_environment_FR1: "by 2050" (content words ['2050'])
- 32_amr_livestock_environment_TE3: "statistical models" (content words ['models', 'statistical'])
- 32_amr_livestock_environment_TE3: "2020 to 2030" (content words ['2020', '2030'])
- 33_amr_food_animals_FR1: "not absorbed by the animals" (content words ['absorbed', 'animals'])
- 35_isse_framework_amr_FR1: "five evaluation levels" (content words ['evaluation', 'five', 'levels'])
- 37_data_driven_one_health_TE3: "Mollentze et al." (content words ['al', 'et', 'mollentze'])
- 38_one_health_africa_TE3: "low- and middle-income countries" (content words ['countries', 'income', 'low', 'middle'])
- 39_zoonotic_southeast_asia_TE3: "95 publications were included" (content words ['95', 'included', 'publications'])
- 40_animal_agriculture_one_health_FR1: "zoonotic" (content words ['zoonotic'])
- 40_animal_agriculture_one_health_TE3: "by 2050" (content words ['2050'])
- 45_kenya_amr_digital_TE3: "Of the 17 surveillance sites" (content words ['17', 'sites', 'surveillance'])
- 48_myc_oncogene_FR1: "MYC-induced and repressed genes" (content words ['genes', 'induced', 'myc', 'repressed'])
- 48_myc_oncogene_FR1: "16 hours" (content words ['16', 'hours'])
- 50_4cseq_protocol_FR1: "reproducible 4C profiles" (content words ['4c', 'profiles', 'reproducible'])
- 50_4cseq_protocol_FR1: "Subsampling analysis" (content words ['analysis', 'subsampling'])
- 50_4cseq_protocol_TE3: "motifPosperc" (content words ['motifposperc'])
- CD_019: "Sarek is implemented in Nextflow" (content words ['implemented', 'nextflow', 'sarek'])

Concepts with no content word at all: 0.
Concepts with at least one word removed: loose 392, stem 461.

## M1. Agreement with the P2 labels (249 pairs, 36 answers)

found among stated = sensitivity; not stated among found = false finds. In brackets: pairs, then the 95% bootstrap interval (S439's replicates). Weighted = 1 / inclusion probability, as S439.

### stated = yes or partly

| matcher | pairs | found among stated, unweighted | weighted | not stated among found, unweighted | weighted |
|---|---:|---|---|---|---|
| loose | 249 | 76.3% (106/139; 68.5% to 82.2%) | 85.0% (106/139; 76.3% to 91.0%) | 10.9% (13/119; 4.8% to 19.0%) | 10.8% (13/119; 3.6% to 21.1%) |
| loose_Qall_a | 249 | 59.0% (82/139; 49.4% to 66.4%) | 65.1% (82/139; 55.0% to 72.8%) | 2.4% (2/84; 0.0% to 6.5%) | 2.2% (2/84; 0.0% to 7.1%) |
| loose_Qneed_a | 249 | 71.2% (99/139; 63.5% to 77.4%) | 77.4% (99/139; 68.7% to 84.2%) | 8.3% (9/108; 2.9% to 15.5%) | 7.6% (9/108; 2.1% to 15.8%) |
| loose_base_b | 243 | 75.4% (101/134; 67.6% to 81.2%) | 84.0% (101/134; 75.6% to 90.0%) | 11.4% (13/114; 4.9% to 19.7%) | 11.5% (13/114; 3.9% to 22.2%) |
| loose_Qall_b | 243 | 61.2% (82/134; 51.3% to 69.0%) | 69.2% (82/134; 58.1% to 77.8%) | 2.4% (2/84; 0.0% to 6.5%) | 2.2% (2/84; 0.0% to 7.1%) |
| loose_Qneed_b | 243 | 73.9% (99/134; 66.2% to 79.8%) | 82.4% (99/134; 74.1% to 88.4%) | 8.3% (9/108; 2.9% to 15.5%) | 7.6% (9/108; 2.1% to 15.8%) |
| stem | 249 | 85.6% (119/139; 78.9% to 90.7%) | 89.2% (119/139; 81.5% to 94.9%) | 15.6% (22/141; 8.7% to 25.0%) | 12.9% (22/141; 5.8% to 23.3%) |
| stem_Qall_a | 249 | 66.2% (92/139; 56.5% to 73.7%) | 71.9% (92/139; 63.7% to 78.1%) | 2.1% (2/94; 0.0% to 5.9%) | 2.0% (2/94; 0.0% to 6.6%) |
| stem_Qneed_a | 249 | 78.4% (109/139; 70.0% to 85.3%) | 80.6% (109/139; 72.3% to 87.6%) | 13.5% (17/126; 6.7% to 23.0%) | 10.0% (17/126; 4.1% to 18.9%) |
| stem_base_b | 243 | 85.1% (114/134; 78.3% to 90.2%) | 88.5% (114/134; 81.0% to 94.3%) | 16.2% (22/136; 9.0% to 25.9%) | 13.7% (22/136; 6.2% to 24.3%) |
| stem_Qall_b | 243 | 68.7% (92/134; 58.5% to 76.6%) | 76.5% (92/134; 67.6% to 83.8%) | 2.1% (2/94; 0.0% to 5.9%) | 2.0% (2/94; 0.0% to 6.6%) |
| stem_Qneed_b | 243 | 81.3% (109/134; 73.3% to 87.9%) | 85.8% (109/134; 78.2% to 91.9%) | 13.5% (17/126; 6.7% to 23.0%) | 10.0% (17/126; 4.1% to 18.9%) |

### stated = yes only

| matcher | pairs | found among stated, unweighted | weighted | not stated among found, unweighted | weighted |
|---|---:|---|---|---|---|
| loose | 249 | 78.5% (102/130; 71.1% to 84.5%) | 87.6% (102/130; 81.0% to 92.8%) | 14.3% (17/119; 8.0% to 23.0%) | 12.9% (17/119; 5.5% to 24.0%) |
| loose_Qall_a | 249 | 62.3% (81/130; 52.7% to 70.8%) | 68.5% (81/130; 59.0% to 76.9%) | 3.6% (3/84; 0.0% to 7.7%) | 2.6% (3/84; 0.0% to 7.6%) |
| loose_Qneed_a | 249 | 73.1% (95/130; 65.2% to 79.8%) | 79.6% (95/130; 70.7% to 87.2%) | 12.0% (13/108; 6.6% to 20.0%) | 10.1% (13/108; 4.2% to 19.3%) |
| loose_base_b | 243 | 77.6% (97/125; 70.3% to 83.7%) | 86.8% (97/125; 80.0% to 92.1%) | 14.9% (17/114; 8.2% to 23.7%) | 13.8% (17/114; 5.9% to 25.3%) |
| loose_Qall_b | 243 | 64.8% (81/125; 54.9% to 73.6%) | 73.1% (81/125; 63.4% to 81.4%) | 3.6% (3/84; 0.0% to 7.7%) | 2.6% (3/84; 0.0% to 7.6%) |
| loose_Qneed_b | 243 | 76.0% (95/125; 68.7% to 82.1%) | 85.0% (95/125; 78.5% to 90.4%) | 12.0% (13/108; 6.6% to 20.0%) | 10.1% (13/108; 4.2% to 19.3%) |
| stem | 249 | 88.5% (115/130; 81.7% to 93.9%) | 92.1% (115/130; 86.0% to 97.1%) | 18.4% (26/141; 11.1% to 28.4%) | 14.9% (26/141; 7.4% to 26.0%) |
| stem_Qall_a | 249 | 69.2% (90/130; 60.0% to 77.2%) | 75.3% (90/130; 67.6% to 82.5%) | 4.3% (4/94; 1.2% to 8.7%) | 2.9% (4/94; 0.5% to 7.8%) |
| stem_Qneed_a | 249 | 80.8% (105/130; 72.2% to 88.4%) | 83.0% (105/130; 74.3% to 91.2%) | 16.7% (21/126; 9.6% to 26.8%) | 12.3% (21/126; 6.0% to 22.2%) |
| stem_base_b | 243 | 88.0% (110/125; 81.1% to 93.6%) | 91.6% (110/125; 85.3% to 96.8%) | 19.1% (26/136; 11.6% to 29.4%) | 15.8% (26/136; 8.0% to 27.2%) |
| stem_Qall_b | 243 | 72.0% (90/125; 62.7% to 80.2%) | 80.4% (90/125; 73.4% to 87.0%) | 4.3% (4/94; 1.2% to 8.7%) | 2.9% (4/94; 0.5% to 7.8%) |
| stem_Qneed_b | 243 | 84.0% (105/125; 76.1% to 90.8%) | 88.7% (105/125; 82.3% to 94.4%) | 16.7% (21/126; 9.6% to 26.8%) | 12.3% (21/126; 6.0% to 22.2%) |

## M2. Where the Q variants and the base matchers disagree on the labelled pairs

stated = yes or partly. lost: stated pairs the base finds and the variant does not (the penalty). dropped: pairs labelled no that the base finds and the variant does not (false finds removed). Causes of a loss: no remaining word (lost under (a), left out under (b)); removal (some words removed, too few remaining words in the answer); rule only (nothing removed, the all-words rule alone).

| variant | stated lost (a) | stated lost (b) | of which: no remaining / removal / rule only | false finds dropped (a) | (b) | added: stated / not stated |
|---|---:|---:|---|---:|---:|---|
| loose_Qall | 24 | 19 | 5 / 5 / 14 | 11 | 11 | 0 / 0 |
| loose_Qneed | 7 | 2 | 5 / 2 / 0 | 4 | 4 | 0 / 0 |
| stem_Qall | 27 | 22 | 5 / 9 / 13 | 20 | 20 | 0 / 0 |
| stem_Qneed | 10 | 5 | 5 / 5 / 0 | 5 | 5 | 0 / 0 |

### Stated pairs lost (the penalty list) (34)

**R002** (yes), 11_asf_burkina_faso_CO2, single_pass

- question: How did the researchers use multi-gene analysis to establish the genetic identity and classification of the ASFV strains responsible for the outbreaks?
- concept: "partial CD2v, and partial B602L"
- variants: loose_Qall, stem_Qall
- removed: loose [], stem []
- remaining: loose ['b602l', 'cd2v', 'partial'] (in the answer ['b602l', 'cd2v']), stem ['b602l', 'cd2v', 'partial'] (in the answer ['b602l', 'cd2v'])
- answer passage: > Researchers used multi-gene analysis targeting the **p72**, **p54**, **CD2v**, and **B602L** genes to characterize and classify the African swine fever virus (ASFV) strains responsible for the 2018 ou

**R011** (yes), 04_fastp_TE3, verified_pass

- question: How does fastp's methodology for adapter detection differ between single-end and paired-end sequencing data?
- concept: "finding the overlap of each pair"
- variants: loose_Qall, stem_Qall, stem_Qneed
- removed: loose [], stem ['pair']
- remaining: loose ['finding', 'overlap', 'pair'] (in the answer ['overlap', 'pair']), stem ['finding', 'overlap'] (in the answer ['overlap'])
- answer passage: > lid, a backward extension is then performed to identify the complete adapter sequence [04_fastp.pdf:0]. *   **Paired-end data:** The tool employs an overlap-analysis-based method derived from AfterQC [04_fastp.pdf:0]. It identifies the overlap between each pair of r

**R012** (yes), 04_fastp_TE3, verified_pass

- question: How does fastp's methodology for adapter detection differ between single-end and paired-end sequencing data?
- concept: "considered as adapter seeds"
- variants: loose_Qall, loose_Qneed, stem_Qall, stem_Qneed
- removed: loose ['adapter'], stem ['adapter']
- remaining: loose ['considered', 'seeds'] (in the answer ['seeds']), stem ['considered', 'seeds'] (in the answer ['seeds'])
- answer passage: > Based on the provided passage, fastp uses different algorithms for adapter detection depending on the sequencing data type:  *   **Single-end data:** The algorithm utilizes an "adapter seed" approach. It attempts to extend a seed in the forward direction to verify its validity, as valid adapters sh

**R014** (yes), 04_fastp_TE3, verified_pass

- question: How does fastp's methodology for adapter detection differ between single-end and paired-end sequencing data?
- concept: "fall out of the overlapped regions"
- variants: stem_Qall
- removed: loose [], stem []
- remaining: loose ['fall', 'out', 'overlapped', 'regions'] (in the answer ['overlapped', 'regions']), stem ['fall', 'out', 'overlapped', 'regions'] (in the answer ['fall', 'overlapped', 'regions'])
- answer passage: > rmed to identify the complete adapter sequence [04_fastp.pdf:0]. *   **Paired-end data:** The tool employs an overlap-analysis-based method derived from AfterQC [04_fastp.pdf:0]. It identifies the overlap between each pair of reads and designates any bases falling outside of these overlapped regions as adapter content [04_fastp.pdf:0].  This overlap-analysis method for paired-end data is noted as an advanta

**R017** (yes), 10_cutadapt_CO2, rlm_5

- question: How does the implementation of Cutadapt balance the trade-off between user accessibility and computational efficiency?
- concept: "mainly written in Python"
- variants: loose_Qall
- removed: loose [], stem []
- remaining: loose ['mainly', 'python', 'written'] (in the answer ['python', 'written']), stem ['mainly', 'python', 'written'] (in the answer ['mainly', 'python', 'written'])
- answer passage: > ## Cutadapt Implementation: Accessibility vs Efficiency  Cutadapt is primarily written in Python to ensure it remains a user-friendly and maintainable tool [2]. It is designed as a standalone, easy-to-use c

**R039** (yes), 05_multiqc_CO2, multi_hop

- question: How does MultiQC's approach to data presentation assist researchers in identifying quality issues across large-scale projects?
- concept: "single summary report"
- variants: loose_Qall, stem_Qall
- removed: loose [], stem []
- remaining: loose ['report', 'single', 'summary'] (in the answer ['report', 'single']), stem ['report', 'single', 'summary'] (in the answer ['report', 'single'])
- answer passage: > sues across large-scale projects by aggregating results from multiple samples and bioinformatics tools into a single, interactive HTML report [05_multiqc.pdf:0]. This centralized approach allows for the direct comparison of datasets, making it easier

**R040** (yes), 05_multiqc_CO2, multi_hop

- question: How does MultiQC's approach to data presentation assist researchers in identifying quality issues across large-scale projects?
- concept: "output from multiple tools"
- variants: loose_Qall, stem_Qall
- removed: loose [], stem []
- remaining: loose ['multiple', 'output', 'tools'] (in the answer ['multiple', 'tools']), stem ['multiple', 'output', 'tools'] (in the answer ['multiple', 'tools'])
- answer passage: > iQC assists researchers in identifying quality issues across large-scale projects by aggregating results from multiple samples and bioinformatics tools into a single, interactive HTML report [05_multiqc.pdf:0]. This centralized approach allows for the direct co

**R043** (yes), 05_multiqc_CO2, multi_hop

- question: How does MultiQC's approach to data presentation assist researchers in identifying quality issues across large-scale projects?
- concept: "aids batch effect detection"
- variants: stem_Qall
- removed: loose [], stem []
- remaining: loose ['aids', 'batch', 'detection', 'effect'] (in the answer ['batch', 'effect']), stem ['aids', 'batch', 'detection', 'effect'] (in the answer ['batch', 'detection', 'effect'])
- answer passage: > This centralized approach allows for the direct comparison of datasets, making it easier to spot outliers and batch effects that would be difficult to detect in individual per-sample reports [05_multiqc.pdf:0]. The reports feature interactive elements such as dynamic

**R044** (yes), 05_multiqc_CO2, multi_hop

- question: How does MultiQC's approach to data presentation assist researchers in identifying quality issues across large-scale projects?
- concept: "identify abnormal samples"
- variants: stem_Qall, stem_Qneed
- removed: loose [], stem ['identify']
- remaining: loose ['abnormal', 'identify', 'samples'] (in the answer ['samples']), stem ['abnormal', 'samples'] (in the answer ['samples'])
- answer passage: > MultiQC assists researchers in identifying quality issues across large-scale projects by aggregating results from multiple samples and bioinformatics tools into a single, interactive HTML report [05_multiqc.pdf:0]. This centralized approach

**R072** (partly), 02_snakemake_TE3, multi_hop

- question: Explain the technical approach Snakemake uses to optimize job scheduling and how it handles job submission overhead in cluster or cloud environments.
- concept: "maximize the number of used cores"
- variants: loose_Qall
- removed: loose [], stem ['used']
- remaining: loose ['cores', 'maximize', 'number', 'used'] (in the answer ['cores', 'maximize', 'number']), stem ['cores', 'maximize', 'number'] (in the answer ['cores', 'maximize', 'number'])
- Valerio's comment: in the constraints it mentioned that selected jobs do not exceed resource limits, such as CPU cores and memory
- answer passage: > ailable resources and workflow priorities [02_snakemake.pdf:0].  *   **Objective Function:** The MILP aims to maximize the "value" of the jobs scheduled in each step. This value is typically a combination of job priority and the [...] lver ensures that the selected subset of jobs does not exceed defined resource limits, such as:     *   **CPU Cores and Memory:** Standard hardware constraints [02_snakemake.pdf:0].     *   **Temporary Storage:** Snakemake tr [...] dividually, the entire group is submitted as a single unit to the cluster or cloud provider. This reduces the number of interactions with the external scheduler and ensures that the grouped jobs run sequentially on the same al

**R073** (yes), 02_snakemake_TE3, multi_hop

- question: Explain the technical approach Snakemake uses to optimize job scheduling and how it handles job submission overhead in cluster or cloud environments.
- concept: "delete existing temporary files"
- variants: stem_Qall
- removed: loose [], stem []
- remaining: loose ['delete', 'existing', 'files', 'temporary'] (in the answer ['files', 'temporary']), stem ['delete', 'existing', 'files', 'temporary'] (in the answer ['delete', 'files', 'temporary'])
- answer passage: > y a combination of job priority and the potential to free up disk space by completing jobs that allow for the deletion of temporary files [02_snakemake.pdf:0]. *   **Constraints:** The solver ensures that the selected subset of jobs does not excee

**R079** (yes), 17_brucellosis_ethiopia_CO2, single_pass

- question: Based on the study's findings, how does the clinical history of livestock relate to the likelihood of brucellosis seropositivity in both small ruminants and camels?
- concept: "RFM had a significant association"
- variants: stem_Qall
- removed: loose [], stem []
- remaining: loose ['association', 'had', 'rfm', 'significant'] (in the answer ['had']), stem ['association', 'had', 'rfm', 'significant'] (in the answer ['association', 'had', 'significant'])
- answer passage: > Based on the study's findings, the clinical and physiological history of livestock is significantly associated with brucellosis seropositivity in both small ruminants and camels:  **Small Ruminants (Sheep and Goats)** * [...] ) [17_brucellosis_ethiopia.pdf:0].  **Camels** *   **History of Abortion:** Camels with a history of abortion had a significantly higher likelihood of seropositivity, with odds 3.9 times higher than those without such a his

**R084** (yes), 04_fastp_CO2, rlm_20

- question: What design choices and implementation strategies allow fastp to achieve higher performance and lower I/O overhead than traditional FASTQ tools?
- concept: "read and load data multiple times"
- variants: loose_Qall
- removed: loose [], stem []
- remaining: loose ['data', 'load', 'multiple', 'read', 'times'] (in the answer ['data', 'multiple', 'read', 'times']), stem ['data', 'load', 'multiple', 'read', 'times'] (in the answer ['data', 'load', 'multiple', 'read', 'times'])
- answer passage: > tp` is designed as an ultra-fast, all-in-one FASTQ preprocessor that achieves high performance by integrating multiple functions—including quality profiling, adapter trimming, read filtering, and base correction—into a single tool [7][10][14][16]. To maximize execution speed, the tool is d [...] O overhead is the "all-in-one" processing flow, which performs all operations with a single scan of the FASTQ data [2][7][10][14][20]. This approach avoids the inefficiency of traditional workflows where multiple tools (such [...] as FASTQC, Cutadapt, and Trimmomatic) are used in sequence, requiring the data to be read and loaded multiple times [7][8][14][15][18].  The multi-threading architecture of `fastp` utilizes a thread pool where reads are packe

**R085** (yes), 04_fastp_CO2, rlm_20

- question: What design choices and implementation strategies allow fastp to achieve higher performance and lower I/O overhead than traditional FASTQ tools?
- concept: "developed in C/Cþþ"
- variants: loose_Qall, stem_Qall
- removed: loose [], stem []
- remaining: loose ['c', 'cþþ', 'developed'] (in the answer ['c', 'developed']), stem ['c', 'cþþ', 'developed'] (in the answer ['c', 'developed'])
- answer passage: > d filtering, and base correction—into a single tool [7][10][14][16]. To maximize execution speed, the tool is developed in C/C++ and features a solid multi-threading implementation [10][16][19]. This contrasts with older tools develop

**R094** (yes), 13_lsd_nepal_FR1, single_pass

- question: What were the overall morbidity, mortality, and case fatality rates recorded during the LSD outbreak in the study area?
- concept: "overall morbidity rate"
- variants: loose_Qall, loose_Qneed, stem_Qall, stem_Qneed; no remaining word under loose, stem
- removed: loose ['morbidity', 'overall', 'rate'], stem ['morbidity', 'overall', 'rate']
- remaining: loose [] (in the answer []), stem [] (in the answer [])
- answer passage: > During the Lumpy Skin Disease (LSD) outbreak in the study area of Nawalpur, the following overall rates were recorded:  *   **Morbidity rate:** 28.02% (n = 431/1,538) [13_lsd_nepal.pdf:0]. *   **Mortality rate:** 3.06% (n = 47/1,538) [13_lsd_nep

**R095** (yes), 13_lsd_nepal_FR1, single_pass

- question: What were the overall morbidity, mortality, and case fatality rates recorded during the LSD outbreak in the study area?
- concept: "mortality rate"
- variants: loose_Qall, loose_Qneed, stem_Qall, stem_Qneed; no remaining word under loose, stem
- removed: loose ['mortality', 'rate'], stem ['mortality', 'rate']
- remaining: loose [] (in the answer []), stem [] (in the answer [])
- answer passage: > During the Lumpy Skin Disease (LSD) outbreak in the study area of Nawalpur, the following overall rates were recorded:  *   **Morbidity rate:** 28.02% (n = 431/1,538) [13_lsd_nepal.pdf:0]. *   **Mortality rate:** 3.06% (n = 47/1,538) [13_lsd_nepal.pdf:0]. *   **Case fatality rate:** 10.90% (n = 47/431) [13_lsd_ne

**R096** (yes), 13_lsd_nepal_FR1, single_pass

- question: What were the overall morbidity, mortality, and case fatality rates recorded during the LSD outbreak in the study area?
- concept: "case fatality rate"
- variants: loose_Qall, loose_Qneed, stem_Qall, stem_Qneed; no remaining word under loose, stem
- removed: loose ['case', 'fatality', 'rate'], stem ['case', 'fatality', 'rate']
- remaining: loose [] (in the answer []), stem [] (in the answer [])
- answer passage: > During the Lumpy Skin Disease (LSD) outbreak in the study area of Nawalpur, the following overall rates were recorded:  *   **Morbidity rate:** 28.02% (n = 431/1,538) [13_lsd_nepal.pdf:0]. *   **Mortality rate:** 3.06% (n = 47/1,538) [13_lsd_nepal.pdf:0]. *   **Case fatality rate:** 10.90% (n = 47/431) [13_lsd_nepal.pdf:0].

**R106** (partly), SY_001, rlm_10

- question: Based on the development of Sarek, Snakemake, nf-core, and fastp, what is the emerging meta-strategy for balancing high-performance computational efficiency with scientific reproducibility in large-scale genomics?
- concept: "exact release version"
- variants: loose_Qall, stem_Qall
- removed: loose [], stem []
- remaining: loose ['exact', 'release', 'version'] (in the answer ['exact', 'version']), stem ['exact', 'release', 'version'] (in the answer ['exact', 'version'])
- answer passage: > and Relaunching:** Sarek is designed to be highly resilient; incomplete runs can be easily restarted from the exact point of failure ("any stage in the workflow process") without re-processing successful upstream steps [Chunk [...] *Singularity** containers [Chunk 4, 18]. *   **Environment Agnosticism:** This ensures that the same software versions are used whether the user is on a local POSIX-compatible computer, an HPC cluster, or a cloud environment. Sa

**R118** (yes), 10_cutadapt_TE3, rlm_5

- question: What are the specific performance metrics for Cutadapt when processing 35 bp colour-space reads with an 18 bp adapter on a 2.66 GHz Intel Core 2 processor?
- concept: "2.66 GHz Intel Core 2 processor"
- variants: loose_Qall, loose_Qneed, stem_Qall, stem_Qneed; no remaining word under loose, stem
- removed: loose ['2', '2.66', 'core', 'ghz', 'intel', 'processor'], stem ['2', '2.66', 'core', 'ghz', 'intel', 'processor']
- remaining: loose [] (in the answer []), stem [] (in the answer [])
- answer passage: > ## Performance Metrics  When using a single core of a 2.66 GHz Intel Core 2 processor to process 35 bp colour-space reads with an 18 bp adapter, Cutadapt trims approximately 1 million reads per m

**R119** (yes), 10_cutadapt_TE3, rlm_5

- question: What are the specific performance metrics for Cutadapt when processing 35 bp colour-space reads with an 18 bp adapter on a 2.66 GHz Intel Core 2 processor?
- concept: "35 bp colour-space reads"
- variants: loose_Qall, loose_Qneed, stem_Qall, stem_Qneed; no remaining word under loose, stem
- removed: loose ['35', 'bp', 'colour', 'reads', 'space'], stem ['35', 'bp', 'colour', 'reads', 'space']
- remaining: loose [] (in the answer []), stem [] (in the answer [])
- answer passage: > ## Performance Metrics  When using a single core of a 2.66 GHz Intel Core 2 processor to process 35 bp colour-space reads with an 18 bp adapter, Cutadapt trims approximately 1 million reads per minute [1]. This processing speed equ

**R126** (partly), 16_ppr_ethiopia_CO2, rlm_20

- question: Why does the study conclude that the current PPR herd immunity in the Borena Zone is insufficient according to international standards?
- concept: "128 small ruminants"
- variants: loose_Qall, stem_Qall
- removed: loose [], stem []
- remaining: loose ['128', 'ruminants', 'small'] (in the answer ['ruminants', 'small']), stem ['128', 'ruminants', 'small'] (in the answer ['ruminants', 'small'])
- Valerio's comment: it get the proper information attached to the small ruminants data, but failed to mention the size of the herd.
- answer passage: > ## PPR Herd Immunity Analysis  The study concludes that herd immunity against Peste des Petits Ruminants (PPR) in the Borena Zone is insufficient because the protection level in vaccinated small ruminants was found to be 68.8% [1][2][8]. This figure is significantly lower than the 80% herd immunity thre

**R132** (yes), 09_seqkit_FR1, multi_hop

- question: Which operating systems are supported by SeqKit and what are the requirements for their installation and configuration?
- concept: "without any dependencies or pre-configurations"
- variants: loose_Qall, loose_Qneed, stem_Qall, stem_Qneed
- removed: loose ['configurations'], stem ['configurations']
- remaining: loose ['dependencies', 'pre'] (in the answer ['dependencies']), stem ['dependencies', 'pre'] (in the answer ['dependencies'])
- answer passage: > fically **Windows, Linux, Mac OS X, and FreeBSD** [source_file:09_seqkit.pdf:0].   Regarding installation and configuration requirements, SeqKit is designed to be lightweight and used "**out-of-the-box**" without any external dependencies or complex configurations [source_file:09_seqkit.pdf:0]. Because it is implemented in the Go programming lang

**R136** (yes), 02_snakemake_CO2, multi_hop

- question: How does Snakemake's implementation of a blockchain-style hashing scheme facilitate cross-workflow result caching?
- concept: "created before in a different workflow"
- variants: loose_Qall, stem_Qall
- removed: loose ['workflow'], stem ['workflow']
- remaining: loose ['before', 'created', 'different'] (in the answer ['before', 'created']), stem ['before', 'created', 'different'] (in the answer ['before', 'created'])
- answer passage: > Snakemake facilitates cross-workflow result caching through a **blockchain-style hashing scheme** that generates a unique identifier for each job [...] le:02_snakemake.pdf:0]. This hash allows Snakemake to unambiguously identify the provenance of an output file before it is created. If a rule is marked for caching, Snakemake checks a **central cache** (local or remote) for the calculated h

**R147** (yes), 09_seqkit_CO2, verified_pass

- question: How does SeqKit achieve stable memory usage and efficiency when processing datasets that are significantly larger than the human genome?
- concept: "parallelized by multiple Goroutines"
- variants: stem_Qall
- removed: loose [], stem []
- remaining: loose ['goroutines', 'multiple', 'parallelized'] (in the answer ['goroutines']), stem ['goroutines', 'multiple', 'parallelized'] (in the answer ['goroutines', 'parallelized'])
- answer passage: > greatly reduces the memory footprint [09_seqkit.pdf:0].  ### 2. Efficiency and Performance Optimization *   **Parallelization:** SeqKit utilizes the multi-CPU environment of modern computers by parallelizing CPU-intensive tasks using "Goroutines" (lightweight processes in the Go language). These tasks include sequence letter validation, reverse compleme

**R157** (yes), 06_star_aligner_CO2, rlm_10

- question: How does the Maximum Mappable Prefix (MMP) search mechanism facilitate the identification of diverse sequence features beyond simple genomic mapping?
- concept: "repeated for the unmapped portion"
- variants: loose_Qall
- removed: loose [], stem []
- remaining: loose ['portion', 'repeated', 'unmapped'] (in the answer ['portion', 'unmapped']), stem ['portion', 'repeated', 'unmapped'] (in the answer ['portion', 'repeated', 'unmapped'])
- answer passage: > nds the MMP for the first part of the read (e.g., a donor site) and then repeats the search for the remaining unmapped portion (e.g., an acceptor site) [3]. This allows for the detection of splice junctions in a single pass without prio

**R161** (yes), 06_star_aligner_CO2, rlm_10

- question: How does the Maximum Mappable Prefix (MMP) search mechanism facilitate the identification of diverse sequence features beyond simple genomic mapping?
- concept: "MMPs will serve as anchors"
- variants: loose_Qall, stem_Qall
- removed: loose ['mmps'], stem ['mmps']
- remaining: loose ['anchors', 'serve', 'will'] (in the answer ['anchors', 'serve']), stem ['anchors', 'serve', 'will'] (in the answer ['anchors', 'serve'])
- answer passage: > ## MMP Search Mechanism  The Maximum Mappable Prefix (MMP) is defined as the longest substring of a read sequence th [...] locations or properties [2]. *   **Mismatches and Indels:** If a search is terminated by a mismatch, the MMPs serve as genomic anchors that can be extended to allow for alignments with mismatches [2]. A subsequent "frugal" dynamic programming a

**R167** (yes), 03_nfcore_framework_TE3, rlm_20

- question: Based on the benchmarking of mapping processes, what was the numerical impact of input sharding on median runtime, and at what point was the maximum efficiency plateau reached?
- concept: "mapping processes decreases"
- variants: stem_Qall, stem_Qneed
- removed: loose ['mapping', 'processes'], stem ['mapping', 'processes']
- remaining: loose ['decreases'] (in the answer []), stem ['decreases'] (in the answer [])
- answer passage: > ## Impact of Input Sharding on Mapping Runtime  Benchmarking of the mapping process in the nf-core/sarek framework showed that input sharding significantly reduces runtime. Specifically, the me

**R174** (yes), CD_005, verified_pass

- question: In the context of scaling large-scale genomic analyses, how do the parallelization strategies of the nf-core framework differ from the job scheduling approach of Snakemake?
- concept: "mixed integer linear program (MILP)"
- variants: loose_Qall
- removed: loose [], stem []
- remaining: loose ['integer', 'linear', 'milp', 'mixed', 'program'] (in the answer ['integer', 'linear', 'milp', 'mixed']), stem ['integer', 'linear', 'milp', 'mixed', 'program'] (in the answer ['integer', 'linear', 'milp', 'mixed', 'program'])
- answer passage: > , the passages provide the following details regarding Snakemake’s job scheduling and parallelization:  *   **MILP Scheduling:** Snakemake solves a scheduling problem using Mixed Integer Linear Programming (MILP) to select a subset of pending jobs for efficient execution [02_snakemake.pdf:0]. *   **Opt

**R175** (yes), CD_005, verified_pass

- question: In the context of scaling large-scale genomic analyses, how do the parallelization strategies of the nf-core framework differ from the job scheduling approach of Snakemake?
- concept: "maximize the number of used cores"
- variants: loose_Qall
- removed: loose ['cores'], stem ['cores']
- remaining: loose ['maximize', 'number', 'used'] (in the answer ['number', 'used']), stem ['maximize', 'number', 'used'] (in the answer ['maximize', 'number', 'used'])
- answer passage: > Based on the provided passages, there is no information regarding the **nf-core framework**. Therefore, it is not possible to compare its parallelization strategies with Snakemake’s job sch [...] specific criteria:     1.  Prioritizing jobs with high priority [02_snakemake.pdf:0].     2.  Maximizing the number of cores used to increase parallelization [02_snakemake.pdf:0].     3.  Deleting temporary files as quickly as possible [02

**R194** (yes), CD_016, rlm_5

- question: Contrast the epidemiological findings of the 2022 Lumpy Skin Disease (LSD) outbreak in Nawalpur, Nepal, with the general disease characteristics and prevention strategies outlined in global systematic reviews.
- concept: "neighboring farms having sick animals"
- variants: loose_Qall
- removed: loose [], stem []
- remaining: loose ['animals', 'farms', 'having', 'neighboring', 'sick'] (in the answer ['animals', 'farms', 'neighboring', 'sick']), stem ['animals', 'farms', 'having', 'neighboring', 'sick'] (in the answer ['animals', 'farms', 'having', 'neighboring', 'sick'])
- answer passage: > mortality) compared to Gaidakot municipality (11.53% morbidity, 0.72% mortality) [12][15]. The most affected animals were dry cattle, which had the highest morbidity at 47.62%, while cattle heifers and milking cattle recorded the highest mortality and case fatality rates [12][14][18]. Predominant clinical symptoms observed in case farms included skin nodules (97%), decreased milk production (87%), and lameness (55%) [2][13][16]. Risk factors id [...] d included importing animals from disease-prevalent regions, sharing feed and water troughs, and proximity to neighboring farms with sick animals [2][10][13].  Prior to the outbreak, the Nepalese government attempted to strengthen border quarantin

**R198** (yes), CD_016, rlm_5

- question: Contrast the epidemiological findings of the 2022 Lumpy Skin Disease (LSD) outbreak in Nawalpur, Nepal, with the general disease characteristics and prevention strategies outlined in global systematic reviews.
- concept: "not yet vaccinated against LSD"
- variants: stem_Qall
- removed: loose ['lsd'], stem ['lsd']
- remaining: loose ['against', 'vaccinated', 'yet'] (in the answer ['yet']), stem ['against', 'vaccinated', 'yet'] (in the answer ['vaccinated', 'yet'])
- answer passage: > ## Epidemiological Findings and Global Contrast  The 2022 lumpy skin disease (LSD) outbreak in Nawalpur, Nepal, which occurred between August and December, resulted in an overall morbidity ra [...] treated with topical medications like potassium permanganate, antipyretics, and antibiotics [6]. Although LSD vaccination was approved by the government, it had not been implemented in the study area during the investigation [6]. R [...] orbidity and Mortality Rates *   **Contrast with India:** The Nawalpur study recorded a "low mortality rate," yet Figure 4 shows that 16% of case farms reported animal deaths. This contrasts with findings from **Odisha, Ind

**R212** (yes), CD_002, rlm_10

- question: How does the 'all-in-one' preprocessing approach of fastp complement the visualization and quality control capabilities of MultiQC in a bioinformatics pipeline?
- concept: "produced on a per-sample basis"
- variants: stem_Qall
- removed: loose [], stem []
- remaining: loose ['basis', 'produced', 'sample'] (in the answer ['sample']), stem ['basis', 'produced', 'sample'] (in the answer ['produced', 'sample'])
- Valerio's comment: The caveat here is that there is no mention of fastp in the answer provided, but given it was a mix of comparing and putting together fastp and multiqc, these concept are real and exist in the answer because they belong to multiqc.
- answer passage: > sing Integration  MultiQC complements bioinformatics preprocessing tools by addressing the limitations of per-sample log files, which are often time-consuming and error-prone to compile manually [1][2]. While the specific tool [...] ned in the provided text [Not found in source material], the document notes that most bioinformatics programs produce logs detailing their results [1][2]. MultiQC automates the quality control (QC) process by recursively search

**R226** (yes), 17_brucellosis_ethiopia_TE3, rlm_20

- question: Describe the laboratory diagnostic sequence and the statistical methods used to identify significant risk factors for brucellosis in this study.
- concept: "Two tests were used serially"
- variants: stem_Qall
- removed: loose ['used'], stem ['used']
- remaining: loose ['serially', 'tests', 'two'] (in the answer ['tests']), stem ['serially', 'tests', 'two'] (in the answer ['serially', 'tests'])
- answer passage: > # Laboratory Diagnostic Sequence  The laboratory diagnostic sequence for brucellosis in this study followed a serial testing approach to maximize specificity and rule out false-positive results [7][11].   1.  **Sample Collection and P [...] 0°C for processing [2][8]. 2.  **Screening Step**: All animal and human serum samples were initially screened using the Rose Bengal Plate Test (RBPT) [2][3][6][8][9][10][12].      *   For camels, 30 μL of RBPT was used [3][6]

**R242** (yes), SY_004, rlm_10

- question: Based on the various stages of data processing described, what meta-conclusion can be drawn regarding the relationship between technical artifact removal and statistical reliability in high-throughput sequencing analysis?
- concept: "avoids type-I errors"
- variants: loose_Qall, stem_Qall
- removed: loose [], stem []
- remaining: loose ['avoids', 'errors', 'i', 'type'] (in the answer ['avoids', 'errors', 'type']), stem ['avoids', 'errors', 'i', 'type'] (in the answer ['avoids', 'errors', 'type'])
- answer passage: > equencing data is inherently noisy, suffering from adapter contamination, base content biases, and sequencing errors [2]. Pre-processing tools like fastp are essential for "clean data" generation by performing quality control, [...] i (MAP) estimates [1][6]. This procedure shrinks noisy gene-wise estimates toward the trend line, which helps avoid false positives that can result from underestimating dispersion [2][6][7]. Unlike other methods like edgeR, w [...] raudulent.   --- ## Sources (from your corpus)  [1] 04_fastp.pdf, page 0: "Document: OP-CBIO180574 884..890 | Type: paper  particu- larly for noninvasive prenatal testing (Bia..." [2] 07_salmon.pdf, page 0: "Document: Salmon

### False finds dropped (pairs labelled no) (20)

**R013** (no), 04_fastp_TE3, verified_pass

- question: How does fastp's methodology for adapter detection differ between single-end and paired-end sequencing data?
- concept: "tree-based algorithm"
- variants: loose_Qall, stem_Qall
- removed: loose [], stem []
- remaining: loose ['algorithm', 'based', 'tree'] (in the answer ['algorithm', 'based']), stem ['algorithm', 'based', 'tree'] (in the answer ['algorithm', 'based'])
- answer passage: > Based on the provided passage, fastp uses different algorithms for adapter detection depending on the sequencing data type:  *   **Single-end data:** The algorithm utilizes

**R023** (no), SY_006, rlm_20

- question: Analyze how the choice of diagnostic methodology and specific assay thresholds influences the reported prevalence and epidemiological understanding of transboundary diseases.
- concept: "threshold values 3 mm and 4 mm"
- variants: loose_Qall, stem_Qall
- removed: loose ['threshold'], stem ['threshold']
- remaining: loose ['3', '4', 'mm', 'values'] (in the answer ['3', '4', 'values']), stem ['3', '4', 'mm', 'values'] (in the answer ['3', '4', 'values'])
- answer passage: > ## Diagnostic Methodology: Serial Testing  Not found in source material.  ## Assay Thresholds: Interpretation Criteria  The provided documents describe the methodology for performing the Single Intraderm [...] s 'severe' interpretation thresholds influence reported prevalence is not found in the source material [1][2][3]. While the text includes references to studies that appraise interpretation criteria and evaluate the compar [...] ot found in source material. No content or chunks were provided to summarize regarding the analysis of PCR Ct values, viral shedding, or transmission potential across species.   --- ## Sources (from your corpus)  [1] 17_brucel [...] d between different poultry types and virus strains to evaluate the level of viral shedding..." (unverified) [4] 14_bovine_tb_cameroon.pdf, page 0: "Document: Veterinary World, EISSN: 2231-0916 | Authors: Veterinary Worl

**R028** (no), SY_006, rlm_20

- question: Analyze how the choice of diagnostic methodology and specific assay thresholds influences the reported prevalence and epidemiological understanding of transboundary diseases.
- concept: "Two tests were used serially"
- variants: stem_Qall
- removed: loose [], stem []
- remaining: loose ['serially', 'tests', 'two', 'used'] (in the answer ['tests']), stem ['serially', 'tests', 'two', 'used'] (in the answer ['serially', 'tests', 'used'])
- answer passage: > ## Diagnostic Methodology: Serial Testing  Not found in source material.  ## Assay Thresholds: Interpretation Criteria  The provided documents describe [...] # Sources (from your corpus)  [1] 17_brucellosis_ethiopia.pdf, page 0: "serum samples were initially screened using the Rose Bengal Plate Test (RBPT)... confirmed using a competitive enzyme-li..." (unverified) [2] 14_bovine_t

**R029** (no), SY_006, rlm_20

- question: Analyze how the choice of diagnostic methodology and specific assay thresholds influences the reported prevalence and epidemiological understanding of transboundary diseases.
- concept: "sensitivity and specificity tests used"
- variants: stem_Qall
- removed: loose [], stem ['specificity']
- remaining: loose ['sensitivity', 'specificity', 'tests', 'used'] (in the answer ['tests']), stem ['sensitivity', 'tests', 'used'] (in the answer ['tests', 'used'])
- answer passage: > ## Diagnostic Methodology: Serial Testing  Not found in source material.  ## Assay Thresholds: Interpretation Criteria  The provided documents describe [...] ater based on an interpretation grid from the World Organization for Animal Health (WOAH) [1].   However, the specific information regarding how 'standard' versus 'severe' interpretation thresholds influence reported prevalence [...] # Sources (from your corpus)  [1] 17_brucellosis_ethiopia.pdf, page 0: "serum samples were initially screened using the Rose Bengal Plate Test (RBPT)... confirmed using a competitive enzyme-li..." (unverified) [2] 14_bovine_t

**R031** (no), 12_hpai_netherlands_TE3, rlm_5

- question: How did the researchers define and calculate the Mortality Ratio (MR) metric used to assess early warning signals on the infected farms?
- concept: "percentage of daily mortality"
- variants: loose_Qall, loose_Qneed, stem_Qall, stem_Qneed
- removed: loose ['mortality'], stem ['mortality']
- remaining: loose ['daily', 'percentage'] (in the answer ['daily']), stem ['daily', 'percentage'] (in the answer ['daily'])
- answer passage: > ## Mortality Ratio (MR) Definition and Calculation  The provided text mentions that researchers used a Mortality Ratio (MR [...] )  [1] 12_hpai_netherlands.pdf, page 0: "The mortality ratio (MR) was calculated as the ratio of the observed daily mortality and the expected daily mortality (t..." (unverified) [2] 12_hpai_netherlands.pdf, page 0: "The thre

**R037** (no), 12_hpai_netherlands_TE3, rlm_5

- question: How did the researchers define and calculate the Mortality Ratio (MR) metric used to assess early warning signals on the infected farms?
- concept: "average mortality of the previous week"
- variants: loose_Qall, stem_Qall
- removed: loose ['mortality'], stem ['mortality']
- remaining: loose ['average', 'previous', 'week'] (in the answer ['average', 'previous']), stem ['average', 'previous', 'week'] (in the answer ['average', 'previous'])
- Valerio's comment: The answer provided mentione MR>3, but not the fact that dutch leglislation requires notification when dailyu mortality is 3 times higher the average mortaility of the previous week for two consecutive days.
- answer passage: > ## Mortality Ratio (MR) Definition and Calculation  The provided text mentions that researchers used a Mortality Ratio (MR [...] daily mortality (t..." (unverified) [2] 12_hpai_netherlands.pdf, page 0: "The threshold was calculated as the average daily mortality of the previous 7 days plus 3 times the standard deviation (..." (unverified) [3] 12_hpai_netherlands.pdf, page 0: "An EWS wa

**R053** (no), CD_014, verified_pass

- question: How do the risk factors identified for brucellosis in Ethiopian camels and small ruminants compare to the risk factors for Peste des petits ruminants (PPR) in the same region?
- concept: "8.3 times higher in gifted small ruminants"
- variants: loose_Qall, loose_Qneed, stem_Qall, stem_Qneed
- removed: loose ['ruminants', 'small'], stem ['ruminants', 'small']
- remaining: loose ['8.3', 'gifted', 'higher', 'times'] (in the answer ['higher', 'times']), stem ['8.3', 'gifted', 'higher', 'times'] (in the answer ['higher', 'times'])
- answer passage: > Based on the provided passages, the risk factors for brucellosis and Peste des petits ruminants (PPR) in Ethiopian livestock share similarities regarding animal movement and flock size, but differ in their [...] brucellosis [17_brucellosis_ethiopia.pdf:0]. For PPR, goats and sheep raised in medium-sized flocks exhibited higher seropositivity rates [16_ppr_ethiopia.pdf:0].  ### Distinct Risk Factors *   **Reproductive Status (Brucellos [...] actor for brucellosis in the provided text, it is a significant risk factor for PPR. Older animals have a 7.3 times higher likelihood of being seropositive for PPRV compared to adult small ruminants [16_ppr_ethiopia.pdf:0]. *   **Species Sensitivity (PPR):** For PPR, some research indicates higher

**R058** (no), SY_002, verified_pass

- question: How do the collective methodologies across Sarek, Snakemake, nf-core, and MultiQC redefine the concept of 'quality control' from a single-sample metric to a system-wide diagnostic process?
- concept: "quality control (QC) reporting"
- variants: stem_Qall, stem_Qneed
- removed: loose ['control', 'quality'], stem ['control', 'quality']
- remaining: loose ['qc', 'reporting'] (in the answer []), stem ['qc', 'reporting'] (in the answer ['reporting'])
- answer passage: > gh information to explain how the collective methodologies of Sarek, Snakemake, nf-core, and MultiQC redefine quality control. The retrieved text only contains information regarding **MultiQC**.  According to the available documentatio [...] **MultiQC** is designed to summarize analysis results from multiple tools and multiple samples into a single report [05_multiqc.pdf:0].  The provided text does not mention Sarek, Snakemake, or nf-core, nor does it discuss the

**R090** (no), 04_fastp_CO2, rlm_20

- question: What design choices and implementation strategies allow fastp to achieve higher performance and lower I/O overhead than traditional FASTQ tools?
- concept: "2–5 times faster"
- variants: loose_Qall, stem_Qall
- removed: loose [], stem []
- remaining: loose ['2', '5', 'faster', 'times'] (in the answer ['2', 'faster', 'times']), stem ['2', '5', 'faster', 'times'] (in the answer ['2', 'faster', 'times'])
- answer passage: > head is the "all-in-one" processing flow, which performs all operations with a single scan of the FASTQ data [2][7][10][14][20]. This approach avoids the inefficiency of traditional workflows where multiple tools (such as FASTQC, Cutadapt, and Trimmomatic) are used in sequence, requiring the data to be read and loaded multiple times [7][8][14][15][18].  The multi-threading architecture of `fastp` utilizes a thread pool where reads are packe [...] [1] 04_fastp.pdf, page 0: "Document: OP-CBIO180574 884..890 | Type: paper  fastp is approximately 2.7 times faster than umis and about 6.1 times fa..." [2] 04_fastp.pdf, page 0: "Document: OP-CBIO180574 884..890 | Type: pape

**R102** (no), SY_001, rlm_10

- question: Based on the development of Sarek, Snakemake, nf-core, and fastp, what is the emerging meta-strategy for balancing high-performance computational efficiency with scientific reproducibility in large-scale genomics?
- concept: "reduces the needed CPU hours by 66%"
- variants: stem_Qall
- removed: loose [], stem []
- remaining: loose ['66', 'cpu', 'hours', 'needed', 'reduces'] (in the answer ['cpu', 'hours', 'reduces']), stem ['66', 'cpu', 'hours', 'needed', 'reduces'] (in the answer ['cpu', 'hours', 'needed', 'reduces'])
- answer passage: > scatter-gather approach, which divides the genome into smaller chunks for parallel processing across multiple CPU cores, significantly reducing wall-clock runtime [13]. The workflow also includes robust error reporting and the ability to restart incompl [...] rated strategy allows Sarek to provide fast, reproducible results—processing 90X WGS data in approximately 48 hours—while remaining flexible for user modifications [8][24].  ## Synthesis of Genomics Meta-Strategy  Based on th [...] ws users to choose between various state-of-the-art tools (like Manta, Mutect2, and FreeBayes) to balance the need for sensitivity versus precision in different research contexts [Chunk 1, 3, 17].  In summary, Sarek’s meta-s

**R105** (no), SY_001, rlm_10

- question: Based on the development of Sarek, Snakemake, nf-core, and fastp, what is the emerging meta-strategy for balancing high-performance computational efficiency with scientific reproducibility in large-scale genomics?
- concept: "2–5 times faster"
- variants: loose_Qall, stem_Qall
- removed: loose [], stem []
- remaining: loose ['2', '5', 'faster', 'times'] (in the answer ['2', '5', 'times']), stem ['2', '5', 'faster', 'times'] (in the answer ['2', '5', 'times'])
- answer passage: > eproducibility is maintained by managing all software dependencies through Conda, Docker, and Singularity [1][2][13]. Tools are initially installed in Conda and then pushed to DockerHub, ensuring they are accessible acros [...] files are stored centrally, allowing for "robust portability" across different compute environments [Chunk 4, 5]. *   **Quality Control:** Being part of nf-core means the pipeline is community-tested and well-documented, [...] d portability as first-class citizens**, using Nextflow and containerization to ensure that "human management time" is minimized while scientific output remains strictly reproducible.  ## Technical Implementation of the Meta

**R110** (no), CD_012, rlm_5

- question: How do the challenges of disease control identified in the Serengeti rabies vaccination campaigns relate to the vaccine efficacy findings for Lumpy Skin Disease (LSD)?
- concept: "reaching 50% in 2022"
- variants: stem_Qall
- removed: loose [], stem []
- remaining: loose ['2022', '50', 'reaching'] (in the answer ['2022']), stem ['2022', '50', 'reaching'] (in the answer ['2022', 'reaching'])
- answer passage: > ocument states that vaccination is an imperative control measure to mitigate economic impacts (Dhakal et al., 2022). It emphasizes that a vaccine coverage level exceeding 80% in susceptible populations is necessary to preven [...] stics of the Lumpy Skin Disease Outbreak in Nawalpur, Nepal, 2022 | Authors: Epidemi..."  --- *Note: Analysis reached turn limit. Results may be incomplete.*

**R156** (no), SY_009, single_pass

- question: Identify the gaps in translating standardized, large-scale genomic workflows into the context of rapid, localized veterinary outbreak characterization based on current literature.
- concept: "limited scope of surveillance"
- variants: stem_Qall
- removed: loose [], stem []
- remaining: loose ['limited', 'scope', 'surveillance'] (in the answer ['surveillance']), stem ['limited', 'scope', 'surveillance'] (in the answer ['limited', 'surveillance'])
- answer passage: > y, though it does not specifically mention genomic workflow translation [18_fmd_review.pdf:0]. *   **Data and surveillance gaps:** In the context of rabies control, researchers note that the impact of vaccination heterogeneity on disease incidence is rarely quantified in real systems, likely due to a "lack of fine-scale data" and the limitations of "coarsely aggregated data" [15_rabies_tanzania.pdf:0]. *   **Genetic analysis in outbreaks:** While geneti

**R165** (no), 03_nfcore_framework_TE3, rlm_20

- question: Based on the benchmarking of mapping processes, what was the numerical impact of input sharding on median runtime, and at what point was the maximum efficiency plateau reached?
- concept: "median runtime to 37%"
- variants: loose_Qall, loose_Qneed, stem_Qall, stem_Qneed
- removed: loose ['median', 'runtime'], stem ['median', 'runtime']
- remaining: loose ['37'] (in the answer []), stem ['37'] (in the answer [])
- answer passage: > ## Impact of Input Sharding on Mapping Runtime  Benchmarking of the mapping process in the nf-core/sarek framework showed that input sharding significantly reduces runtime. Specifically, the median runtime for the mapping process was reduced from 104.5 minutes to 11.5 minutes, representing a 9.1-fold reduc

**R182** (no), 07_salmon_FR1, verified_pass

- question: By what percentage range was Salmon's sensitivity higher in differential expression testing compared to other tools at the same False Discovery Rates (FDRs)?
- concept: "kallisto’s estimates"
- variants: loose_Qall, loose_Qneed, stem_Qall, stem_Qneed
- removed: loose ['s'], stem ['s']
- remaining: loose ['estimates', 'kallisto'] (in the answer ['kallisto']), stem ['estimates', 'kallisto'] (in the answer ['kallisto'])
- answer passage: > provided passages, there is not enough information to determine the specific percentage range by which Salmon's sensitivity was higher in differential expression testing compared to other tools.  While the documents state that Salmon "typically outperforms both kallisto and eXpress in terms of accuracy" [07_salmon.pdf:0] and yields "improved inter-replicate concordance" when us

**R186** (no), 10_cutadapt_FR1, single_pass

- question: What unique capability does Cutadapt offer compared to other standalone tools in the context of read trimming?
- concept: "correctly trim colour-space reads"
- variants: stem_Qall
- removed: loose ['reads'], stem ['reads', 'trim']
- remaining: loose ['colour', 'correctly', 'space', 'trim'] (in the answer ['colour', 'space']), stem ['colour', 'correctly', 'space'] (in the answer ['colour', 'space'])
- Valerio's comment: The answer talk about using colour space reads, but no mention that it can correctly trim reads based on that feature
- answer passage: > Based on the provided passages, Cutadapt offers several specific capabilities compared to other standalone trimming tools like Vectorstrip:  *   **Colour-space support:** Cutadapt supports colour-space data (SOLiD), a feature that was notably absent from previous solut [...] ed repeatedly [10_cutadapt.pdf:0]. *   **Specific algorithm modifications:** To prevent the removal of entire reads due to short random matches at the beginning, Cutadapt utilizes a modified alignment approach that penalizes

**R207** (no), CD_002, rlm_10

- question: How does the 'all-in-one' preprocessing approach of fastp complement the visualization and quality control capabilities of MultiQC in a bioinformatics pipeline?
- concept: "single scan of the FASTQ data"
- variants: loose_Qall, stem_Qall
- removed: loose [], stem []
- remaining: loose ['data', 'fastq', 'scan', 'single'] (in the answer ['data', 'scan', 'single']), stem ['data', 'fastq', 'scan', 'single'] (in the answer ['data', 'scan', 'single'])
- answer passage: > (QC) process by recursively searching directories for these recognized log files and reports, aggregating the data into a single, centralized summary [2][3]. This allows researchers to identify global trends, batch effects, and outlier sa [...] for multiple tools and samples into a single report, Visualizes global trends and biases across project data, Scans directories recursively for log files and QC reports, Interactive and resizeable plots using HighCharts, Supp

**R209** (no), CD_002, rlm_10

- question: How does the 'all-in-one' preprocessing approach of fastp complement the visualization and quality control capabilities of MultiQC in a bioinformatics pipeline?
- concept: "pre- and post-filtered data"
- variants: stem_Qall
- removed: loose [], stem []
- remaining: loose ['data', 'filtered', 'post', 'pre'] (in the answer ['data', 'post']), stem ['data', 'filtered', 'post', 'pre'] (in the answer ['data', 'filtered', 'post'])
- answer passage: > (QC) process by recursively searching directories for these recognized log files and reports, aggregating the data into a single, centralized summary [2][3]. This allows researchers to identify global trends, batch effects, [...] ML report, parsed data can be exported as tab-delimited text, YAML, or JSON files for downstream analysis and post-processing [3][4]. *   **Customization:** Reports can be branded using templates, and plots can be exported i [...] such as **tab-delimited text, YAML, or JSON**. This allows the output to be used for post-processing, dataset filtering, or integration into databases and LIMS (Laboratory Information Management Systems).  By acting as a "central

**R222** (no), SY_003, multi_hop

- question: How does the corpus demonstrate an evolution from localized tool optimization to systemic computational efficiency across different layers of the bioinformatics stack?
- concept: "70% cost reduction"
- variants: loose_Qall, stem_Qall
- removed: loose [], stem []
- remaining: loose ['70', 'cost', 'reduction'] (in the answer ['cost', 'reduction']), stem ['70', 'cost', 'reduction'] (in the answer ['cost', 'reduction'])
- Valerio's comment: The value reported in there is either hallucinated or completely misunderstood from the blocks of text evaluated by the LLM.
- answer passage: > rated, containerized workflows (like nf-core/sarek) managed by Nextflow. This shift is characterized by a 69% reduction in compute costs (down to $20 per sample for WGS), the ability to perform population-scale recomputing on commercial clouds, a

**R239** (no), SY_004, rlm_10

- question: Based on the various stages of data processing described, what meta-conclusion can be drawn regarding the relationship between technical artifact removal and statistical reliability in high-throughput sequencing analysis?
- concept: "batch effect detection"
- variants: stem_Qall
- removed: loose [], stem []
- remaining: loose ['batch', 'detection', 'effect'] (in the answer []), stem ['batch', 'detection', 'effect'] (in the answer ['detection', 'effect'])
- answer passage: > in a single scan [2]. This stage is critical for eliminating false positives and negatives, particularly when detecting ultra-low mutation allele frequencies (MAF) in liquid biopsies, where technical noise can easily obscure real [...] Salmon addresses these by learning sample-specific parameters during its online phase and re-estimating the "effective length" of transcripts [4][5]. This bias-aware quantification is a prerequisite for accurate expression estim

### Pairs a Q variant finds and the base does not (0)

## M4. Mean concept recall per strategy (516 exp04 answers)

Key: the v1-format key of S439's population (data/ground_truth_v2/ground_truth_v2_4_as_v1.json). Under (b) the mean is over the answers with a defined recall (n in brackets when below the strategy's count).

| strategy | n | loose_o30 | loose | stem | loose_Qall_a | loose_Qall_b | loose_Qneed_a | loose_Qneed_b | stem_Qall_a | stem_Qall_b | stem_Qneed_a | stem_Qneed_b |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| single_pass | 86 | 0.4112 | 0.4026 | 0.4398 | 0.2063 | 0.2259 | 0.3016 | 0.3222 | 0.2292 | 0.2488 | 0.3258 | 0.3464 |
| multi_hop | 86 | 0.3816 | 0.3743 | 0.4071 | 0.1750 | 0.1855 | 0.2832 | 0.3012 | 0.2039 | 0.2175 | 0.3086 | 0.3286 |
| rlm_5 | 86 | 0.6708 | 0.6645 | 0.6975 | 0.4734 | 0.5040 | 0.5890 | 0.6256 | 0.5235 | 0.5561 | 0.6233 | 0.6623 |
| rlm_10 | 86 | 0.7339 | 0.7310 | 0.7637 | 0.5395 | 0.5680 | 0.6618 | 0.6964 | 0.5746 | 0.6078 | 0.6972 | 0.7368 |
| rlm_20 | 86 | 0.6916 | 0.6901 | 0.7454 | 0.5249 | 0.5514 | 0.6230 | 0.6497 | 0.5529 | 0.5830 | 0.6672 | 0.6976 |
| verified_pass | 86 | 0.3491 | 0.3381 | 0.3760 | 0.1632 | 0.1714 | 0.2457 | 0.2544 | 0.1794 | 0.1876 | 0.2700 | 0.2788 |
| all | 516 | 0.5397 | 0.5335 | 0.5716 | 0.3471 | 0.3677 | 0.4507 | 0.4749 | 0.3773 | 0.4001 | 0.4820 | 0.5084 |

Concepts of the population key (distinct question and concept): loose: 160 of 571 lose a word, 18 lose all; stem: 193 of 571 lose a word, 20 lose all.

No remaining word under the loose removal, population key:

- 01_sarek_FR1: "BAM files, annotated VCF files and CNV files" (['annotated', 'bam', 'cnv', 'files', 'vcf'])
- 01_sarek_TE3: "GATK4 Mutect2 and Strelka2" (['gatk4', 'mutect2', 'strelka2'])
- 01_sarek_TE3: "SSMs" (['ssms'])
- 01_sarek_TE3: "intersection" (['intersection'])
- 05_multiqc_FR1: "At the time of writing" (['time', 'writing'])
- 06_star_aligner_FR1: "12-core server" (['12', 'core', 'server'])
- 07_salmon_FR1: "at the same FDRs" (['fdrs', 'same'])
- 10_cutadapt_TE3: "2.66 GHz Intel Core 2 processor" (['2', '2.66', 'core', 'ghz', 'intel', 'processor'])
- 10_cutadapt_TE3: "35 bp colour-space reads" (['35', 'bp', 'colour', 'reads', 'space'])
- 13_lsd_nepal_FR1: "case fatality rate" (['case', 'fatality', 'rate'])
- 13_lsd_nepal_FR1: "mortality rate" (['mortality', 'rate'])
- 13_lsd_nepal_FR1: "overall morbidity rate" (['morbidity', 'overall', 'rate'])
- 13_lsd_nepal_TE3: "Multivariable logistic regression analysis" (['analysis', 'logistic', 'multivariable', 'regression'])
- 16_ppr_ethiopia_FR1: "between 2018 and 2022" (['2018', '2022'])
- 16_ppr_ethiopia_TE3: "purchased animals" (['animals', 'purchased'])
- 18_fmd_review_CO2: "no FMDV carrier state in pigs" (['carrier', 'fmdv', 'pigs', 'state'])
- 19_hpai_canada_FR1: "culled in Canada" (['canada', 'culled'])
- 20_lsd_review_TE3: "cross-protection rate" (['cross', 'protection', 'rate'])

No remaining word under the stem removal, population key:

- 01_sarek_FR1: "BAM files, annotated VCF files and CNV files" (['annotated', 'bam', 'cnv', 'files', 'vcf'])
- 01_sarek_TE3: "GATK4 Mutect2 and Strelka2" (['gatk4', 'mutect2', 'strelka2'])
- 01_sarek_TE3: "SSMs" (['ssms'])
- 01_sarek_TE3: "intersection" (['intersection'])
- 05_multiqc_FR1: "At the time of writing" (['time', 'writing'])
- 06_star_aligner_FR1: "12-core server" (['12', 'core', 'server'])
- 07_salmon_FR1: "at the same FDRs" (['fdrs', 'same'])
- 10_cutadapt_TE3: "2.66 GHz Intel Core 2 processor" (['2', '2.66', 'core', 'ghz', 'intel', 'processor'])
- 10_cutadapt_TE3: "35 bp colour-space reads" (['35', 'bp', 'colour', 'reads', 'space'])
- 12_hpai_netherlands_FR1: "increased for meat-type poultry" (['increased', 'meat', 'poultry', 'type'])
- 13_lsd_nepal_FR1: "case fatality rate" (['case', 'fatality', 'rate'])
- 13_lsd_nepal_FR1: "mortality rate" (['mortality', 'rate'])
- 13_lsd_nepal_FR1: "overall morbidity rate" (['morbidity', 'overall', 'rate'])
- 13_lsd_nepal_TE3: "Multivariable logistic regression analysis" (['analysis', 'logistic', 'multivariable', 'regression'])
- 16_ppr_ethiopia_FR1: "between 2018 and 2022" (['2018', '2022'])
- 16_ppr_ethiopia_TE3: "purchased animals" (['animals', 'purchased'])
- 18_fmd_review_CO2: "no FMDV carrier state in pigs" (['carrier', 'fmdv', 'pigs', 'state'])
- 19_hpai_canada_FR1: "culled in Canada" (['canada', 'culled'])
- 20_lsd_review_FR1: "homologous vaccination" (['homologous', 'vaccination'])
- 20_lsd_review_TE3: "cross-protection rate" (['cross', 'protection', 'rate'])

## Gates

| gate | result | what was tested |
|---|---|---|
| G1 | ok | base matchers' own cases and 19 hand cases hold |
| G2 | ok | S439 population: 516 answers, 3426 pairs, loose finds 1774 (known 516, 3426, 1774) |
| G3 | ok | with an empty question Q-need equals the base loose and stem verdicts on 4617 of 4617 pairs (3,426 exp04 pairs and the v2.5 key's concepts scored on their questions) |
| G4a | ok | the labelled sheet is the one S439 --analyze scored (response/concept_match_labels/concept_labels_v1_ai_panel.xlsx, sha256 6e3f94bfad2e) |
| G4 | ok | the base verdicts of the 249 sampled pairs are S439's key file's |
| G5 | ok | the base loose and stem rates reproduce S439_concept_label_analysis.json on 16 of 16 cells (share, counts, interval) |
| G6 | ok | loose_o30 per answer equals S382 csv concept_recall_loose_v22 on 516 of 516 answers; csv records the present key and answers file: True |
