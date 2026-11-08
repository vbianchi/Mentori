#!/usr/bin/env Rscript
# S565 - the strategy-by-corpus-size interaction model of D213 (2), the R half of S565_corpus_interaction.py.
# -----------------------------------------------------------------------------------------------------------------
# Called by S565_corpus_interaction.py, never by hand:
#   Rscript S565_corpus_interaction.R <tidy.csv> <counts folder> <out.json> <cores> <n_boot> [<only strategies, comma>]
#
# The model is the submitted S11's (scripts/S11_corpus_mixed_model.R, fit_interaction), ported with the two changes
# D213 (2) fixes: log2 of core papers in place of log, and the distractor level as a term:
#   glmer(pass ~ strategy * log2c + factor(ratio) + (1 | question), binomial, bobyqa, maxfun 2e5)
# fitted, as S11 fitted it, on two strategies at a time, single pass the reference level, so the term
# strategy<s>:log2c is the strategy's change in log odds against single pass per doubling of core papers.
# log2c is log2(core papers) centred on the mean over the fitted rows (as S11 centred log size); centring moves the
# main effects only, not the interaction.
#
# Interval: two-sided 95% percentile over n_boot cluster-bootstrap resamples of questions. The resamples are not drawn
# here: the counts file of the question set holds, per resample, how often each question is drawn (S463.resample_counts,
# default_rng(20261013), 10,000 x n), so the model and the Python companion use the same resamples. A question drawn
# k times enters k times, each copy its own cluster (as S11's cluster_boot relabelled them). Each resample refits the
# same glmer (S11's bootstrap refitted a plain glm instead; D213 fixes the model, so the glmer is refitted). A refit
# that errors is counted and left out; a singular fit (random intercept variance 0) is kept and counted.
# -----------------------------------------------------------------------------------------------------------------
suppressPackageStartupMessages({ library(lme4); library(jsonlite); library(parallel) })

args <- commandArgs(trailingOnly = TRUE)
TIDY <- args[1]; COUNTS <- args[2]; OUTJ <- args[3]
CORES <- as.integer(args[4]); NBOOT <- as.integer(args[5])
ONLY <- if (length(args) >= 6 && nzchar(args[6])) strsplit(args[6], ",")[[1]] else NULL

d0 <- read.csv(TIDY, comment.char = "#", stringsAsFactors = FALSE)
CTRL <- glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5))
CTRL_B <- glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5), calc.derivs = FALSE)
# calc.derivs FALSE in the refits skips lme4's derivative check after the optimum is found; the optimum is the same.

prep <- function(d, s) {
  d <- d[d$strategy %in% c("single_pass", s), ]
  d$strategy <- factor(d$strategy, levels = c("single_pass", s))
  d$log2c <- log2(d$core_papers) - mean(log2(d$core_papers))
  d$ratio <- factor(d$distractor_ratio, levels = c(0, 1, 3))
  d
}
FORM <- pass ~ strategy * log2c + ratio + (1 | cluster)
term_of <- function(s) paste0("strategy", s, ":log2c")

fit_one <- function(d, ctrl) {
  m <- glmer(FORM, data = d, family = binomial, control = ctrl)
  list(coef = fixef(m), m = m)
}

run_cell <- function(set, thr, s) {
  d <- d0[d0$question_set == set & d0$threshold == thr, ]
  d <- d[!is.na(d$pass), ]
  d <- prep(d, s)
  d$cluster <- d$question_id
  term <- term_of(s)
  w <- character(0)
  f <- withCallingHandlers(fit_one(d, CTRL),
         warning = function(x) { w <<- c(w, conditionMessage(x)); invokeRestart("muffleWarning") })
  cf <- summary(f$m)$coefficients
  est <- cf[term, "Estimate"]; se <- cf[term, "Std. Error"]
  sd_q <- as.data.frame(VarCorr(f$m))$sdcor[1]
  # bootstrap
  cnt <- read.csv(file.path(COUNTS, paste0("counts_", set, ".csv")), check.names = FALSE)
  qids <- colnames(cnt)
  if (!setequal(qids, unique(d$question_id))) stop(sprintf("%s: counts questions differ from the data's", set))
  rows_of <- split(seq_len(nrow(d)), factor(d$question_id, levels = qids))
  nr <- lengths(rows_of)
  cnt <- as.matrix(cnt)[seq_len(NBOOT), , drop = FALSE]
  one <- function(b) {
    k <- cnt[b, ]
    qsel <- rep(seq_along(qids), k)
    idx <- unlist(rows_of[qsel], use.names = FALSE)
    db <- d[idx, ]
    db$cluster <- rep(seq_along(qsel), nr[qsel])
    sing <- FALSE
    r <- tryCatch(withCallingHandlers({
        m <- glmer(FORM, data = db, family = binomial, control = CTRL_B)
        sing <- isSingular(m)
        fixef(m)[term]
      }, warning = function(x) invokeRestart("muffleWarning")),
      error = function(e) NA_real_)
    c(unname(r), as.numeric(sing))
  }
  t0 <- Sys.time()
  B <- do.call(rbind, mclapply(seq_len(NBOOT), one, mc.cores = CORES, mc.preschedule = TRUE))
  secs <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
  ok <- is.finite(B[, 1])
  q <- unname(quantile(B[ok, 1], c(0.025, 0.975), type = 7))
  pass_by <- aggregate(pass ~ strategy + core_papers, data = d, FUN = mean)
  list(question_set = set, threshold = thr, strategy = s, term = term,
       n_rows = nrow(d), n_questions = length(unique(d$question_id)),
       estimate_log_odds_per_doubling = est, wald_se = se,
       wald_ci95 = c(est - qnorm(0.975) * se, est + qnorm(0.975) * se),
       wald_p_two_sided = 2 * pnorm(-abs(est / se)),
       odds_ratio_per_doubling = exp(est),
       boot_ci95_percentile = q, boot_odds_ratio_ci95 = exp(q),
       boot_resamples = NBOOT, boot_ok = sum(ok), boot_errors = sum(!ok),
       boot_singular = sum(B[ok, 2] == 1), boot_median = median(B[ok, 1]),
       boot_seconds = secs,
       fit_warnings = unique(w), fit_singular = isSingular(f$m), random_intercept_sd = sd_q,
       fixed_effects = as.list(fixef(f$m)),
       pass_rate_by_size = lapply(split(pass_by, seq_len(nrow(pass_by))), as.list))
}

strategies <- c("rlm_10", "multi_hop", "verified_pass", "rlm_5", "rlm_20")
if (!is.null(ONLY)) strategies <- intersect(strategies, ONLY)
sets <- unique(d0$question_set); thrs <- sort(unique(d0$threshold), decreasing = TRUE)
RNGkind("L'Ecuyer-CMRG"); set.seed(20261013)   # no random draw is made here; fixed so the run is reproducible anyway
res <- list()
for (set in sets) for (thr in thrs) for (s in strategies) {
  if (!any(d0$strategy == s)) next
  t <- Sys.time()
  r <- run_cell(set, thr, s)
  res[[length(res) + 1]] <- r
  cat(sprintf("%s score %d %s: est %.4f, boot [%.4f, %.4f], ok %d, %.0f s\n", set, thr, s,
              r$estimate_log_odds_per_doubling, r$boot_ci95_percentile[1], r$boot_ci95_percentile[2],
              r$boot_ok, as.numeric(difftime(Sys.time(), t, units = "secs"))))
  # written after every cell (primary first), so a stopped run keeps what it finished; marked partial until the end
  out <- list(script = "S565_corpus_interaction.R", r_version = R.version.string,
              lme4 = as.character(packageVersion("lme4")), formula = deparse(FORM),
              cores = CORES, n_boot = NBOOT, complete = FALSE, fits = res)
  write_json(out, paste0(OUTJ, ".partial"), auto_unbox = TRUE, pretty = TRUE, digits = NA)
}
out$complete <- TRUE
write_json(out, OUTJ, auto_unbox = TRUE, pretty = TRUE, digits = NA)
unlink(paste0(OUTJ, ".partial"))
