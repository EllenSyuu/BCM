#' Compile (or load) the Stan model
#'
#' The model in `inst/stan/oosc_cohort_model.stan` is compiled once per session
#' and cached on disk, keyed by the model file's checksum and the rstan
#' version. Compilation takes a few minutes the first time.
#'
#' @param cache_dir Directory for the compiled model; `NULL` disables the disk
#'   cache. Defaults to the `oosccohort.cache_dir` option, or the user cache
#'   directory from [tools::R_user_dir()].
#' @return A `stanmodel` object.
#' @export
oosc_stan_model <- function(cache_dir = getOption("oosccohort.cache_dir", tools::R_user_dir("oosccohort", "cache"))) {
  file <- oosc_stan_file()
  key <- paste0("oosc-", unname(tools::md5sum(file)), "-rstan-", utils::packageVersion("rstan"))
  if (!is.null(.oosc_cache$model) && identical(.oosc_cache$key, key)) return(.oosc_cache$model)
  path <- if (!is.null(cache_dir)) file.path(cache_dir, paste0(key, ".rds"))
  model <- if (!is.null(path) && file.exists(path)) readRDS(path) else NULL
  if (is.null(model)) {
    # rstan compiles the model at run time and needs these header packages; binary
    # installs of rstan do not always bring them, so they are package dependencies.
    headers <- c("BH", "RcppEigen", "RcppParallel", "StanHeaders")
    missing <- headers[!vapply(headers, function(p) nzchar(system.file("include", package = p)), logical(1))]
    if (length(missing)) {
      stop("Compiling the Stan model needs the C++ headers of: ", paste(missing, collapse = ", "),
           ". Install them with install.packages(c(", paste0('"', missing, '"', collapse = ", "), ")).", call. = FALSE)
    }
    message("Compiling the Stan model (first use only; this takes a few minutes)...")
    model <- rstan::stan_model(file = file, model_name = "oosc_cohort_model")
    if (!is.null(path)) {
      dir.create(cache_dir, recursive = TRUE, showWarnings = FALSE)
      saveRDS(model, path)
    }
  }
  .oosc_cache$model <- model
  .oosc_cache$key <- key
  model
}

#' Path to the Stan model file shipped with the package
#' @return Path to `oosc_cohort_model.stan`.
#' @export
oosc_stan_file <- function() {
  file <- system.file("stan", "oosc_cohort_model.stan", package = "oosccohort")
  if (!nzchar(file)) stop("Stan model file not found; is oosccohort installed?", call. = FALSE)
  file
}

.oosc_cache <- new.env(parent = emptyenv())

#' Fit the Bayesian cohort model
#'
#' Runs NUTS with rstan. The defaults are the paper's settings (Sec. 3.4,
#' App. C): 4 chains, 2,000 warm-up and 2,000 sampling iterations per chain,
#' thinned to 1,000 draws in total. The paper does not state the target
#' acceptance rate; 0.99 is used (audit item I6).
#'
#' @param data An `oosc_data` object from [prepare_oosc_data()].
#' @param chains,iter_warmup,iter_sampling,thin Sampler settings.
#' @param adapt_delta Target acceptance rate.
#' @param max_treedepth Maximum tree depth.
#' @param seed Random seed.
#' @param cores Number of chains run in parallel.
#' @param refresh Progress output interval (0 for none).
#' @param ... Passed to [rstan::sampling()].
#' @return An object of class `oosc_fit` with elements `stanfit`, `data` and `settings`.
#' @export
fit_oosc <- function(data, chains = 4L, iter_warmup = 2000L, iter_sampling = 2000L, thin = 8L,
                     adapt_delta = 0.99, max_treedepth = 10L, seed = 2022L,
                     cores = getOption("mc.cores", 1L), refresh = max(iter_sampling %/% 10L, 1L), ...) {
  if (!inherits(data, "oosc_data")) stop("`data` must come from prepare_oosc_data().", call. = FALSE)
  settings <- list(chains = chains, iter_warmup = iter_warmup, iter_sampling = iter_sampling, thin = thin,
                   adapt_delta = adapt_delta, max_treedepth = max_treedepth, seed = seed)
  stanfit <- rstan::sampling(
    oosc_stan_model(), data = data$stan_data,
    chains = chains, iter = iter_warmup + iter_sampling, warmup = iter_warmup, thin = thin,
    seed = seed, cores = cores, refresh = refresh,
    control = list(adapt_delta = adapt_delta, max_treedepth = max_treedepth),
    # the full latent surface is rebuilt from mu_star and alpha when needed; not storing it keeps memory bounded
    pars = c("kappa_probit", "Mu"), include = FALSE,
    ...
  )
  structure(list(stanfit = stanfit, data = data, settings = settings), class = "oosc_fit")
}

#' @export
print.oosc_fit <- function(x, ...) {
  d <- oosc_diagnostics(x)
  s <- x$settings
  cat("<oosc_fit>\n")
  cat(sprintf("  %d chains x %d sampling iterations (warm-up %d, thin %d), seed %s\n",
              s$chains, s$iter_sampling, s$iter_warmup, s$thin, s$seed))
  cat(sprintf("  max R-hat %.3f   min ESS %.0f   divergences %d   convergence thresholds met: %s\n",
              d$max_rhat, d$min_ess, d$divergences, d$converged))
  invisible(x)
}
