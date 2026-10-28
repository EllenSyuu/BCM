test_that("a short fit on simulated data recovers the known surface", {
  skip_if_no_stan()
  sim <- simulate_oosc(seed = 2022)
  d <- suppressMessages(prepare_oosc_data(sim$countries, sim$admin, sim$survey))
  # short chains do not meet the convergence thresholds; rstan warns about that by design here
  fit <- suppressWarnings(fit_oosc(d, chains = 2, iter_warmup = 200, iter_sampling = 150, thin = 1, seed = 1, refresh = 0))
  expect_s3_class(fit, "oosc_fit")

  rates <- oosc_rates(fit)
  expect_equal(nrow(rates), 4 * 23 * 8)
  expect_true(all(rates$q05 >= 0 & rates$q95 <= 1 & rates$q05 <= rates$q50 & rates$q50 <= rates$q95))
  m <- merge(rates, sim$truth, by = c("country", "year", "age", "age_rel"))
  expect_equal(nrow(m), nrow(rates))
  coverage <- mean(m$q05 <= m$true_rate & m$true_rate <= m$q95)
  mae <- mean(abs(m$q50 - m$true_rate))
  expect_gt(coverage, 0.6)
  expect_lt(mae, 0.03)

  diag <- oosc_diagnostics(fit)
  expect_named(diag, c("max_rhat", "min_ess", "divergences", "max_treedepth_hits", "converged"))
  expect_true(is.finite(diag$max_rhat))
})
