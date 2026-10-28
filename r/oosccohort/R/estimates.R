#' Out-of-school rate estimates by country, year and single age
#'
#' Rebuilds the latent rate \eqn{\kappa_{c,y,a} = \Phi(\mu_{c,y-a+1} + \Theta_{c,y,a})}
#' (paper Eq. 3, 4, 10) from the posterior draws of the spline coefficients,
#' for every country, year in the estimation window and relative age, and
#' summarises it by posterior quantiles. Survey bias is not added, so these
#' are the model's estimates of the true rate.
#'
#' @param fit An `oosc_fit` object.
#' @param years Years to report (default: the estimation window).
#' @param probs Quantiles to report; the default gives the median and a 90\% interval.
#' @return A data frame with columns `country`, `year`, `age`, `age_rel` and one
#'   column per quantile (`q05`, `q50`, `q95` by default).
#' @export
oosc_rates <- function(fit, years = fit$data$index$years, probs = c(0.05, 0.5, 0.95)) {
  draws <- oosc_rate_draws(fit, years)
  idx <- draws$cells
  q <- t(apply(draws$draws, 2, stats::quantile, probs = probs, names = FALSE))
  colnames(q) <- sprintf("q%02d", round(100 * probs))
  cbind(idx, as.data.frame(q))
}

#' Posterior draws of out-of-school rates
#'
#' @inheritParams oosc_rates
#' @return A list with `cells` (a data frame of country, year, age, age_rel) and
#'   `draws` (a matrix with one row per posterior draw and one column per cell).
#' @export
oosc_rate_draws <- function(fit, years = fit$data$index$years) {
  s <- fit$data$stan_data
  ix <- fit$data$index
  post <- rstan::extract(fit$stanfit, pars = c("mu_star", if (s$A_max > 1) "alpha"))
  cells <- expand.grid(age_rel = seq_len(s$A_max), year = as.integer(years), c = seq_len(s$C))
  row <- cells$year - cells$age_rel + 1L - ix$ey_grid[1] + 1L
  if (any(row < 1L | row > s$N_EY)) stop("Requested years fall outside the entry-year grid.", call. = FALSE)
  out <- matrix(NA_real_, nrow = dim(post$mu_star)[1], ncol = nrow(cells))
  for (c in seq_len(s$C)) {
    mu <- post$mu_star[, c, , drop = TRUE]
    if (is.null(dim(mu))) mu <- matrix(mu, nrow = 1)
    cum_alpha <- if (s$A_max > 1) .cumsum_ages(post$alpha[, c, , , drop = FALSE]) else NULL
    for (a in seq_len(s$A_max)) {
      j <- which(cells$c == c & cells$age_rel == a)
      eta <- mu %*% t(s$B1[row[j], , drop = FALSE])
      if (a > 1) eta <- eta + cum_alpha[, a - 1L, ] %*% t(s$B5[row[j], , drop = FALSE])
      out[, j] <- stats::pnorm(eta)
    }
  }
  entry <- ix$countries$entry_age[cells$c]
  list(
    cells = data.frame(country = ix$countries$country[cells$c], year = cells$year,
                       age = entry + cells$age_rel - 1L, age_rel = cells$age_rel, stringsAsFactors = FALSE),
    draws = out
  )
}

# alpha draws for one country: [draws, 1, A_max - 1, K5] -> cumulative sums over ages
.cumsum_ages <- function(alpha) {
  d <- dim(alpha)
  a <- array(alpha, dim = c(d[1], d[3], d[4]))
  for (g in seq_len(d[3])[-1]) a[, g, ] <- a[, g - 1L, ] + a[, g, ]
  a
}

#' Convergence diagnostics
#'
#' Reports the largest R-hat, the smallest effective sample size and the number
#' of divergent transitions over all sampled parameters, and whether the
#' project's thresholds (R-hat at most 1.01, ESS at least 400, no divergences)
#' are met. The paper does not state numerical thresholds.
#'
#' @param fit An `oosc_fit` object.
#' @return A list with `max_rhat`, `min_ess`, `divergences`, `max_treedepth_hits` and `converged`.
#' @export
oosc_diagnostics <- function(fit) {
  sm <- rstan::summary(fit$stanfit)$summary
  sm <- sm[rownames(sm) != "lp__", , drop = FALSE]
  rhat <- sm[, "Rhat"]
  ess <- sm[, "n_eff"]
  divergences <- rstan::get_num_divergent(fit$stanfit)
  out <- list(
    max_rhat = max(rhat, na.rm = TRUE),
    min_ess = min(ess, na.rm = TRUE),
    divergences = divergences,
    max_treedepth_hits = rstan::get_num_max_treedepth(fit$stanfit)
  )
  out$converged <- out$max_rhat <= 1.01 && out$min_ess >= 400 && divergences == 0
  out
}
