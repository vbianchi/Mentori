#!/usr/bin/env Rscript
# S11 - Corpus-scaling controlled analysis
# -----------------------------------------------------------------------------
# Task: S11 (corpus-mixed-model), Wave B. Adjudicated numbers in
#   findings/adversarial/T06_memo.md.
# Input (via python pre-processor scripts/S11_prep.py):
#   findings/recompute/S11_exp05_tidy.csv   (9894 rows; flat from the TRUSTED,
#     READ-ONLY exp05_scaling_latest.json = the merged/canonical exp05 file).
# Canonical file choice: exp05_scaling_latest.json is the merged master
#   (n_results=9894, merge_sources = non_rlm_archive + rlm_regenerated). The
#   per-size/noise exp05_rlm_generated_s*.json shards are RLM generation slices
#   that feed the merge; the merged file is the single source of truth and the
#   only one carrying every strategy (single_pass/verified_pass/multi_hop as
#   well as rlm_*). We use ONLY the merged file.
# Pass metric (analysis_deep.py:766-797): pass = correctness>=3; answerable
#   only; empty answers (len<10) and unjudged (correctness None) excluded.
# Deliverables: (1) nesting verification, (2) headline slice, (3) fixed-subset
#   panel + CSV, (4) mixed model glmer + Wald/VB CI + cluster-bootstrap CI,
#   (5) caveats (McNemar, corr>=4 flip), (6) crash clustering.
# Outputs: findings/recompute/S11_corpus_scaling.json + .md +
#   S11_fig3d_subset_panel.csv
# -----------------------------------------------------------------------------
suppressPackageStartupMessages({
  library(lme4); library(boot); library(jsonlite)
})
# scripts/machine.R, beside this file, owns where this repo and the upstream data are
MACHINE <- local({
  a <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
  file.path(if (length(a)) dirname(sub("^--file=", "", a[1])) else getwd(), "machine.R")
})
source(MACHINE)
set.seed(20260722)

RECOMPUTE <- mentori_recompute()
TIDY  <- file.path(RECOMPUTE, "S11_exp05_tidy.csv")
CELLS <- file.path(RECOMPUTE, "S11_cellcounts.csv")
STAMP <- trimws(system("date", intern = TRUE))

df <- read.csv(TIDY, comment.char = "#", stringsAsFactors = FALSE)
cells <- read.csv(CELLS, comment.char = "#", stringsAsFactors = FALSE)

# valid accuracy-scoreable rows: answerable, non-empty, judged
df$pass <- ifelse(df$answerable == 1 & df$empty == 0 & df$unjudged == 0,
                  as.integer(df$correctness >= 3), NA_integer_)
df$pass4 <- ifelse(df$answerable == 1 & df$empty == 0 & df$unjudged == 0,
                   as.integer(df$correctness >= 4), NA_integer_)
V <- subset(df, !is.na(pass))     # valid accuracy rows

out <- list(
  script = "scripts/S11_corpus_mixed_model.R",
  input  = mentori_shown(TIDY),
  canonical_source = "exp05_scaling_latest.json (merged master, n_results=9894)",
  pass_metric = "correctness>=3; answerable only; empty(len<10)/unjudged excluded (analysis_deep.py:766-797)",
  generated = STAMP
)

## ---------------------------------------------------------------------------
## (1) NESTING VERIFICATION
## ---------------------------------------------------------------------------
sizes <- c(5, 10, 20, 50)
qset  <- lapply(sizes, function(s) unique(df$question_id[df$size == s]))
names(qset) <- as.character(sizes)
aset  <- lapply(sizes, function(s) unique(df$question_id[df$size == s & df$answerable == 1]))
oset  <- lapply(sizes, function(s) unique(df$question_id[df$size == s & df$answerable == 0]))
names(aset) <- names(oset) <- as.character(sizes)

nested <- function(sets) all(sapply(seq_len(length(sets)-1), function(i)
  all(sets[[i]] %in% sets[[i+1]])))
ood_identical <- all(sapply(2:4, function(i) setequal(oset[[1]], oset[[i]])))

nesting <- list(
  total_qids   = sapply(qset, length),
  answerable_qids = sapply(aset, length),
  ood_qids     = sapply(oset, length),
  strict_nesting_total = nested(qset),
  strict_nesting_answerable = nested(aset),
  ood_identical_all_sizes = ood_identical,
  answerable_share = round(sapply(sizes, function(s)
    length(aset[[as.character(s)]]) / length(qset[[as.character(s)]])), 3)
)
nesting$verdict <- sprintf(
  "Strict nesting %s->%s->%s->%s; answerable %s->%s->%s->%s; OOD 50 identical all sizes: %s; answerable share %.0f%%->%.0f%%.",
  nesting$total_qids["5"], nesting$total_qids["10"], nesting$total_qids["20"], nesting$total_qids["50"],
  nesting$answerable_qids["5"], nesting$answerable_qids["10"], nesting$answerable_qids["20"], nesting$answerable_qids["50"],
  ood_identical, 100*nesting$answerable_share[1], 100*nesting$answerable_share[4])
out$nesting <- nesting

## ---------------------------------------------------------------------------
## (2) HEADLINE SLICE  (s50, corr>=3)
## ---------------------------------------------------------------------------
rate <- function(data, sz, strat, noise = NA) {
  s <- data[data$size == sz & data$strategy == strat, ]
  if (!is.na(noise)) s <- s[s$noise == noise, ]
  list(pass_pct = round(100 * mean(s$pass), 1), n = nrow(s))
}
strategies_core <- c("single_pass", "rlm_5", "rlm_10", "rlm_20")
headline_n0 <- lapply(strategies_core, function(st) rate(V, 50, st, 0))
names(headline_n0) <- strategies_core
headline_pooled <- lapply(strategies_core, function(st) rate(V, 50, st, NA))
names(headline_pooled) <- strategies_core
out$headline <- list(
  slice = "s50, answerable, corr>=3",
  no_noise_n0 = headline_n0,
  noise_pooled = headline_pooled,
  prose_target = "single-pass 83.0% vs RLM 61.2-63.1% (n0); ~81% vs ~58-60% (pooled)"
)

## ---------------------------------------------------------------------------
## (3) FIXED-SUBSET PANEL: 22 answerable qids common to all sizes
## ---------------------------------------------------------------------------
common22 <- Reduce(intersect, aset)             # 22 answerable common to all sizes
stopifnot(length(common22) == 22)
FS <- V[V$question_id %in% common22, ]

panel_strats <- c("single_pass", "verified_pass", "multi_hop", "rlm_5", "rlm_10", "rlm_20")
panel_rows <- list()
for (st in panel_strats) {
  for (sz in sizes) {
    # pooled over noise
    sp <- FS[FS$strategy == st & FS$size == sz, ]
    sn0 <- sp[sp$noise == 0, ]
    panel_rows[[length(panel_rows)+1]] <- data.frame(
      strategy = st, size = sz,
      pass_pct_pooled = if (nrow(sp)>0) round(100*mean(sp$pass),1) else NA,
      n_pooled = nrow(sp),
      pass_pct_n0 = if (nrow(sn0)>0) round(100*mean(sn0$pass),1) else NA,
      n_n0 = nrow(sn0),
      stringsAsFactors = FALSE)
  }
}
panel <- do.call(rbind, panel_rows)
panel_csv <- file.path(RECOMPUTE, "S11_fig3d_subset_panel.csv")
writeLines(c(
  paste0("# S11_fig3d_subset_panel.csv - fixed common 22-answerable-question subset"),
  paste0("# generated by scripts/S11_corpus_mixed_model.R  ", STAMP),
  paste0("# pass=correctness>=3; pooled=over noise 0/1/3; n0=no-noise only")), panel_csv)
suppressWarnings(write.table(panel, panel_csv, sep = ",", row.names = FALSE,
                             append = TRUE, col.names = TRUE, quote = FALSE))
out$fixed_subset_panel <- list(
  common22_qids = sort(common22),
  panel = panel,
  csv = mentori_shown(panel_csv),
  note = "single-pass expected flat ~79-82%; rlm_10 expected 83%->67% (pooled)"
)

## ---------------------------------------------------------------------------
## (4) MIXED MODEL: pass ~ strategy*log(size) + (1|question_id)
##     Primary focus single_pass vs rlm_10, n0, corr>=3.
## ---------------------------------------------------------------------------
mm_data <- function(data, strat_pair, noise0 = TRUE) {
  d <- data[data$strategy %in% strat_pair, ]
  if (noise0) d <- d[d$noise == 0, ]
  d$strategy <- factor(d$strategy, levels = strat_pair)  # ref = first
  d$logsize_c <- log(d$size) - mean(log(d$size))          # centered log size
  d
}

fit_interaction <- function(d) {
  m <- glmer(pass ~ strategy * logsize_c + (1 | question_id),
             data = d, family = binomial,
             control = glmerControl(optimizer = "bobyqa",
                                    optCtrl = list(maxfun = 2e5)))
  cf <- summary(m)$coefficients
  ix <- grep(":logsize_c$", rownames(cf))
  list(model = m, coef_name = rownames(cf)[ix],
       est = cf[ix, "Estimate"], se = cf[ix, "Std. Error"],
       wald_lo = cf[ix,"Estimate"] - 1.96*cf[ix,"Std. Error"],
       wald_hi = cf[ix,"Estimate"] + 1.96*cf[ix,"Std. Error"])
}

# plain GLM (no random effect, independence assumption) - returns est + Wald CI.
# This is the "naive" interval: ignoring question clustering understates the SE.
fit_glm <- function(d) {
  m <- glm(pass ~ strategy * logsize_c, data = d, family = binomial)
  cf <- summary(m)$coefficients
  ix <- grep(":logsize_c$", rownames(cf))
  est <- cf[ix,"Estimate"]; se <- cf[ix,"Std. Error"]
  list(est = est, se = se, wald_lo = est-1.96*se, wald_hi = est+1.96*se)
}

# cluster bootstrap: resample question_ids with replacement, refit GLM
cluster_boot <- function(d, R = 500) {
  qids <- unique(d$question_id)
  ests <- numeric(0)
  for (b in seq_len(R)) {
    samp <- sample(qids, length(qids), replace = TRUE)
    # build resampled frame (new cluster ids to keep clusters distinct)
    parts <- lapply(seq_along(samp), function(i) {
      s <- d[d$question_id == samp[i], ]; s$question_id <- paste0(samp[i],"_",i); s })
    db <- do.call(rbind, parts)
    est <- tryCatch({
      m <- glm(pass ~ strategy * logsize_c, data = db, family = binomial)
      cf <- coef(m); cf[grep(":logsize_c$", names(cf))]
    }, error = function(e) NA_real_, warning = function(w) {
      m <- suppressWarnings(glm(pass ~ strategy*logsize_c, data=db, family=binomial))
      cf <- coef(m); cf[grep(":logsize_c$", names(cf))] })
    ests <- c(ests, est)
  }
  ests <- ests[is.finite(ests)]
  list(n_reps = length(ests),
       est = median(ests),
       ci_lo = unname(quantile(ests, 0.025)),
       ci_hi = unname(quantile(ests, 0.975)),
       glm = fit_glm(d))
}

primary_pair <- c("single_pass", "rlm_10")
dP  <- mm_data(V, primary_pair, noise0 = TRUE)   # n0-only primary spec
fitP <- fit_interaction(dP)                      # glmer w/ random intercept
bootP <- cluster_boot(dP, R = 1000)              # cluster bootstrap (resample questions)
naive_n0 <- fit_glm(dP)                          # naive independence GLM, n0
# noise-pooled naive GLM: triples n while questions repeat -> artificially tight CI
dPool <- mm_data(V, primary_pair, noise0 = FALSE)
naive_pooled <- fit_glm(dPool)

w_boot   <- bootP$ci_hi - bootP$ci_lo
w_glmer  <- fitP$wald_hi - fitP$wald_lo
w_naive0 <- naive_n0$wald_hi - naive_n0$wald_lo
w_naivep <- naive_pooled$wald_hi - naive_pooled$wald_lo
# Persona-2's flagged over-tight VB CI (from T06; SUPERSEDED, reproduced for ratio)
p2_ci <- c(-1.197, -1.039); w_p2 <- abs(diff(p2_ci)) # 0.158

out$mixed_model <- list(
  spec = "pass ~ strategy*log(size) + (1|question_id), binomial; corr>=3",
  focus = "single_pass (ref) vs rlm_10; primary = no-noise (n0)",
  n_obs = nrow(dP), n_questions = length(unique(dP$question_id)),
  interaction_term = fitP$coef_name,
  glmer_wald = list(est = round(fitP$est,3), se = round(fitP$se,3),
                    wald_ci = round(c(fitP$wald_lo, fitP$wald_hi),3),
                    width = round(w_glmer,3),
                    note = "properly specified random-intercept (Laplace); Wald CI"),
  naive_glm_n0 = list(est = round(naive_n0$est,3), se = round(naive_n0$se,3),
                      wald_ci = round(c(naive_n0$wald_lo, naive_n0$wald_hi),3),
                      width = round(w_naive0,3),
                      note = "independence GLM ignoring question clustering (n0)"),
  naive_glm_noise_pooled = list(est = round(naive_pooled$est,3), se = round(naive_pooled$se,3),
                      wald_ci = round(c(naive_pooled$wald_lo, naive_pooled$wald_hi),3),
                      width = round(w_naivep,3), n_obs = nrow(dPool),
                      note = "THE naive too-narrow interval: pools noise 0/1/3 as if independent, tripling n while the same questions repeat"),
  cluster_bootstrap = list(n_reps = bootP$n_reps, est = round(bootP$est,3),
                           ci = round(c(bootP$ci_lo, bootP$ci_hi),3),
                           width = round(w_boot,3),
                           note = "resample question_ids w/ replacement, refit GLM; primary CI to publish"),
  superseded_persona2_VB_ci = list(ci = p2_ci, width = round(w_p2,3),
                           note = "T06-flagged over-tight VB interval; DO NOT publish"),
  width_ratios = list(
    boot_over_naive_pooled = round(w_boot / w_naivep, 2),
    boot_over_naive_n0     = round(w_boot / w_naive0, 2),
    boot_over_persona2VB   = round(w_boot / w_p2, 2),
    boot_over_glmer_wald   = round(w_boot / w_glmer, 2)),
  interpretation = paste(
    "Negative interaction = rlm_10 loses ground vs single_pass as corpus grows.",
    "The cluster bootstrap CI [~ -1.0, (-1.9,-0.4)] is the honest interval.",
    "Naive independence GLMs are far too narrow: the noise-pooled naive CI is",
    round(w_boot/w_naivep,1), "x narrower than the bootstrap, and the specific VB CI",
    "T06 flagged (Persona 2) is", round(w_boot/w_p2,1), "x narrower (~the '6x' claim).",
    "By contrast the properly-specified n0 glmer Wald CI is close to the bootstrap.")
)

## Supplementary: all RLM strategies vs single_pass
supp <- list()
for (st in c("rlm_5","rlm_10","rlm_20")) {
  d <- mm_data(V, c("single_pass", st), noise0 = TRUE)
  ft <- tryCatch(fit_interaction(d), error = function(e) NULL)
  bt <- cluster_boot(d, R = 500)
  if (!is.null(ft)) {
    supp[[st]] <- list(
      interaction = st,
      glmer_est = round(ft$est,3), glmer_wald_ci = round(c(ft$wald_lo, ft$wald_hi),3),
      boot_est = round(bt$est,3), boot_ci = round(c(bt$ci_lo, bt$ci_hi),3),
      n_obs = nrow(d))
  }
}
out$mixed_model_supplement <- supp

## ---------------------------------------------------------------------------
## (5) CAVEATS
## ---------------------------------------------------------------------------
# McNemar helpers (exact binomial on discordant pairs).
# (a) size comparison: same strategy across two sizes, paired by question_id.
mcnemar_size <- function(data, st, sz_a, sz_b, noise = 0) {
  a <- data[data$strategy==st & data$size==sz_a & data$noise==noise, c("question_id","pass")]
  b <- data[data$strategy==st & data$size==sz_b & data$noise==noise, c("question_id","pass")]
  m <- merge(a, b, by="question_id", suffixes=c("_a","_b"))
  b01 <- sum(m$pass_a==0 & m$pass_b==1)   # improved a->b
  b10 <- sum(m$pass_a==1 & m$pass_b==0)   # worsened a->b
  disc <- b01 + b10
  p <- if (disc==0) 1 else binom.test(min(b01,b10), disc, 0.5)$p.value
  list(n_pairs=nrow(m), discordant_01=b01, discordant_10=b10, exact_p=round(p,4))
}
# (b) strategy comparison at one size: two strategies, paired by question_id.
mcnemar_strat <- function(data, st_a, st_b, sz, noise = 0) {
  a <- data[data$strategy==st_a & data$size==sz & data$noise==noise, c("question_id","pass")]
  b <- data[data$strategy==st_b & data$size==sz & data$noise==noise, c("question_id","pass")]
  m <- merge(a, b, by="question_id", suffixes=c("_a","_b"))
  a1 <- sum(m$pass_a==1 & m$pass_b==0)     # st_a passes, st_b fails
  b1 <- sum(m$pass_a==0 & m$pass_b==1)     # st_b passes, st_a fails
  disc <- a1 + b1
  p <- if (disc==0) 1 else binom.test(min(a1,b1), disc, 0.5)$p.value
  list(n_pairs=nrow(m), a_wins=a1, b_wins=b1, exact_p=round(p,4))
}
# Primary caveat McNemar (matches T06 ~0.125): single_pass vs rlm_10 at s50, n0, fixed subset
mc_strat_s50 <- mcnemar_strat(FS, "single_pass", "rlm_10", 50, 0)
# Secondary: single_pass across s20->s50 on the fixed subset (size stability of single_pass)
mc_20v50 <- mcnemar_size(FS, "single_pass", 20, 50, 0)
mc_20v50_rlm <- mcnemar_size(FS, "rlm_10", 20, 50, 0)

# corr>=4 subset flip at s50 n0
FS4 <- df[df$question_id %in% common22 & df$answerable==1 & df$empty==0 & df$unjudged==0, ]
rate4 <- function(data, sz, st, noise=0) {
  s <- data[data$size==sz & data$strategy==st & data$noise==noise, ]
  round(100*mean(s$pass4), 1)
}
# also full-set corr>=4 at s50
full4 <- function(sz, st, noise=0) {
  s <- df[df$size==sz & df$strategy==st & df$noise==noise & df$answerable==1 &
          df$empty==0 & df$unjudged==0, ]
  round(100*mean(s$pass4), 1)
}
out$caveats <- list(
  mcnemar_subset_s50_single_pass_vs_rlm10 = c(mc_strat_s50,
    note="primary underpowered caveat: fixed 22-q subset, s50, n0; discordant a_wins(sp) vs b_wins(rlm), exact p~0.125 ns"),
  mcnemar_subset_s20_vs_s50_single_pass = mc_20v50,
  mcnemar_subset_s20_vs_s50_rlm_10 = mc_20v50_rlm,
  corr4_subset_s50_n0 = list(
    single_pass = rate4(FS4, 50, "single_pass"),
    rlm_10 = rate4(FS4, 50, "rlm_10"),
    note = "on the fixed 22-q subset the inversion flips at corr>=4 (single_pass < rlm_10)"),
  corr4_full_s50_n0 = list(
    single_pass = full4(50, "single_pass"),
    rlm_5 = full4(50, "rlm_5"), rlm_10 = full4(50, "rlm_10"), rlm_20 = full4(50, "rlm_20"),
    note = "on the FULL s50 set the inversion HOLDS at corr>=4 (single_pass > RLM)")
)

## ---------------------------------------------------------------------------
## (6) CRASH CLUSTERING: RLM generation crashes = missing records.
##     A crash for (size, noise, strategy, question) => that row absent from file.
##     Build the expected full grid (question present at that size x each rlm
##     strategy x 3 noise) and find missing cells; count per question; test
##     dispersion (variance/mean) vs Poisson (chisq dispersion test).
## ---------------------------------------------------------------------------
rlm_strats <- c("rlm_5","rlm_10","rlm_20")
noises <- c(0,1,3)
present <- with(df[df$strategy %in% rlm_strats, ],
                paste(question_id, size, noise, strategy))
miss_count <- list()
for (sz in sizes) {
  qids_sz <- qset[[as.character(sz)]]
  for (st in rlm_strats) for (nz in noises) {
    for (q in qids_sz) {
      key <- paste(q, sz, nz, st)
      if (!(key %in% present)) {
        miss_count[[q]] <- (if (is.null(miss_count[[q]])) 0 else miss_count[[q]]) + 1
      }
    }
  }
}
# per-question crash counts over its universe of expected rlm cells
# expected cells for a question = (#sizes it appears in) * 3 strats * 3 noises
sizes_of_q <- function(q) sum(sapply(sizes, function(s) q %in% qset[[as.character(s)]]))
allq <- unique(df$question_id)
crash_df <- data.frame(
  question_id = allq,
  crashes = sapply(allq, function(q) if (is.null(miss_count[[q]])) 0 else miss_count[[q]]),
  expected_cells = sapply(allq, function(q) sizes_of_q(q) * length(rlm_strats) * length(noises)),
  stringsAsFactors = FALSE)
total_crashes <- sum(crash_df$crashes)
total_cells   <- sum(crash_df$expected_cells)
p_hat <- total_crashes / total_cells
# dispersion test: observed variance of per-question crash counts vs Poisson
lambda <- mean(crash_df$crashes)
disp_index <- var(crash_df$crashes) / lambda
# chisq dispersion statistic ~ (n-1)*var/mean under H0 Poisson
n_q <- nrow(crash_df)
chi_stat <- (n_q - 1) * disp_index
disp_p <- pchisq(chi_stat, df = n_q - 1, lower.tail = FALSE)
# how many questions have >1 crash; max
crash_tab <- as.list(table(crash_df$crashes))
out$crash_clustering <- list(
  total_crashes = total_crashes, total_expected_rlm_cells = total_cells,
  overall_crash_rate = round(p_hat, 4),
  n_questions = n_q, mean_crashes_per_q = round(lambda,3),
  var_crashes_per_q = round(var(crash_df$crashes),3),
  dispersion_index = round(disp_index, 3),
  dispersion_chisq = round(chi_stat,2), dispersion_df = n_q-1,
  dispersion_p = signif(disp_p, 4),
  crash_count_distribution = crash_tab,
  max_crashes_one_question = max(crash_df$crashes),
  top_questions = head(crash_df[order(-crash_df$crashes),], 8),
  verdict = if (disp_p < 0.05 & disp_index > 1)
    "Over-dispersed vs Poisson: crashes cluster on some questions (dispersion index >1, p<0.05)."
    else "Not significantly over-dispersed: crashes ~ Poisson (no strong clustering on particular questions).")

## ---------------------------------------------------------------------------
## WRITE OUTPUTS
## ---------------------------------------------------------------------------
json_path <- file.path(RECOMPUTE, "S11_corpus_scaling.json")
write_json(out, json_path, auto_unbox = TRUE, pretty = TRUE, digits = 6)
cat("wrote", json_path, "\n")

# Markdown summary
md <- c(
"# S11 - Corpus-scaling controlled analysis",
paste0("_", STAMP, " - scripts/S11_corpus_mixed_model.R_"),
paste0("Canonical input: ", out$canonical_source, "  (via S11_prep.py -> S11_exp05_tidy.csv)"),
paste0("Pass metric: ", out$pass_metric),
"",
"## (1) Nesting verification",
sprintf("- Total qids/size: 5=%d, 10=%d, 20=%d, 50=%d; strict nesting = %s",
  nesting$total_qids["5"],nesting$total_qids["10"],nesting$total_qids["20"],nesting$total_qids["50"],
  nesting$strict_nesting_total),
sprintf("- Answerable qids/size: 22=%d, 44=%d, 88=%d, 200=%d; strict nesting = %s",
  nesting$answerable_qids["5"],nesting$answerable_qids["10"],nesting$answerable_qids["20"],nesting$answerable_qids["50"],
  nesting$strict_nesting_answerable),
sprintf("- OOD refusal qids: 50 at every size, identical set = %s", nesting$ood_identical_all_sizes),
sprintf("- Answerable share: %.0f%% -> %.0f%% -> %.0f%% -> %.0f%%",
  100*nesting$answerable_share[1],100*nesting$answerable_share[2],
  100*nesting$answerable_share[3],100*nesting$answerable_share[4]),
"",
"## (2) Headline slice (s50, answerable, corr>=3)",
sprintf("- No-noise (n0): single_pass %.1f%% | rlm_5 %.1f%% | rlm_10 %.1f%% | rlm_20 %.1f%%",
  headline_n0$single_pass$pass_pct, headline_n0$rlm_5$pass_pct,
  headline_n0$rlm_10$pass_pct, headline_n0$rlm_20$pass_pct),
sprintf("- Noise-pooled: single_pass %.1f%% | rlm_5 %.1f%% | rlm_10 %.1f%% | rlm_20 %.1f%%",
  headline_pooled$single_pass$pass_pct, headline_pooled$rlm_5$pass_pct,
  headline_pooled$rlm_10$pass_pct, headline_pooled$rlm_20$pass_pct),
"",
"## (3) Fixed 22-question subset panel (pooled noise; see S11_fig3d_subset_panel.csv)",
"| strategy | s5 | s10 | s20 | s50 |",
"|---|---|---|---|---|",
paste(sapply(panel_strats, function(st){
  r <- function(sz) panel$pass_pct_pooled[panel$strategy==st & panel$size==sz]
  sprintf("| %s | %.1f | %.1f | %.1f | %.1f |", st, r(5), r(10), r(20), r(50))
}), collapse="\n"),
"",
"## (4) Mixed model (single_pass vs rlm_10, corr>=3; interaction strategy:log(size))",
sprintf("- glmer + (1|question_id), n0: est %.3f, Wald 95%% CI [%.3f, %.3f] (width %.2f)",
  fitP$est, fitP$wald_lo, fitP$wald_hi, w_glmer),
sprintf("- Cluster bootstrap (%d reps, resample questions), n0: est %.3f, 95%% CI [%.3f, %.3f] (width %.2f)  <- PUBLISH THIS",
  bootP$n_reps, bootP$est, bootP$ci_lo, bootP$ci_hi, w_boot),
sprintf("- Naive independence GLM, n0: [%.3f, %.3f] (width %.2f)",
  naive_n0$wald_lo, naive_n0$wald_hi, w_naive0),
sprintf("- Naive GLM pooling noise 0/1/3 as independent (n=%d): [%.3f, %.3f] (width %.2f) = %.1fx narrower than bootstrap",
  nrow(dPool), naive_pooled$wald_lo, naive_pooled$wald_hi, w_naivep, w_boot/w_naivep),
sprintf("- Persona-2's flagged VB CI [%.3f, %.3f] (width %.3f) is %.1fx narrower than the bootstrap (the '~6x too narrow' T06 point) -- SUPERSEDED, do not publish.",
  p2_ci[1], p2_ci[2], w_p2, w_boot/w_p2),
"",
"## (5) Caveats",
sprintf("- McNemar fixed-subset s50 n0, single_pass vs rlm_10: %d pairs, sp-wins=%d, rlm-wins=%d, exact p=%.4f (ns, underpowered)",
  mc_strat_s50$n_pairs, mc_strat_s50$a_wins, mc_strat_s50$b_wins, mc_strat_s50$exact_p),
sprintf("- McNemar fixed-subset s20 vs s50 (single_pass, n0): %d pairs, discordant 0->1=%d, 1->0=%d, exact p=%.4f (single_pass flat across sizes)",
  mc_20v50$n_pairs, mc_20v50$discordant_01, mc_20v50$discordant_10, mc_20v50$exact_p),
sprintf("- corr>=4 fixed subset s50 n0: single_pass %.1f%% vs rlm_10 %.1f%% (subset inversion FLIPS at >=4)",
  out$caveats$corr4_subset_s50_n0$single_pass, out$caveats$corr4_subset_s50_n0$rlm_10),
sprintf("- corr>=4 FULL s50 n0: single_pass %.1f%% vs rlm_5/10/20 %.1f/%.1f/%.1f%% (full-set inversion HOLDS at >=4)",
  out$caveats$corr4_full_s50_n0$single_pass, out$caveats$corr4_full_s50_n0$rlm_5,
  out$caveats$corr4_full_s50_n0$rlm_10, out$caveats$corr4_full_s50_n0$rlm_20),
"",
"## (6) Crash clustering (RLM generation crashes = missing records)",
sprintf("- %d crashes / %d expected RLM cells (rate %.3f); dispersion index %.3f (Poisson=1), chisq p=%s",
  total_crashes, total_cells, p_hat, disp_index, signif(disp_p,4)),
paste0("- Verdict: ", out$crash_clustering$verdict))
md_path <- file.path(RECOMPUTE, "S11_corpus_scaling.md")
writeLines(md, md_path)
cat("wrote", md_path, "\n")
cat("wrote", panel_csv, "\n")
