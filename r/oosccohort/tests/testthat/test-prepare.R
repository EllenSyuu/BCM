countries <- data.frame(country = c("AAA", "BBB"), region = c("R1", "R2"), entry_age = c(6, 7))
admin <- data.frame(country = c("AAA", "AAA", "AAA", "BBB", "BBB"), year = c(2010, 2010, 2012, 2010, 2010),
                    age = c(5, 9, 6, 7, 10), rate = c(0.3, 0.2, -0.2, 0.1, 0.05))
survey <- data.frame(country = c("AAA", "BBB", "BBB"), year = c(2005, 2015, 2015), age = c(8, 9, 9),
                     rate = c(0.25, 0, 0.4), se = 0.02, series = c("DHS", "MICS", "MICS"), wave = c("DHS5", "MICS4", "MICS4"))

test_that("paper data rules are applied and reported", {
  expect_message(
    expect_message(
      expect_message(d <- prepare_oosc_data(countries, admin, survey), "below -0.1"),
      "equal to 0 or 1"),
    "outside the modelled ages")
  expect_equal(d$stan_data$N_A, 3)   # dropped: age 5 (below entry age) and rate -0.2
  expect_equal(d$stan_data$N_S, 2)   # dropped: survey rate 0
})

test_that("observations map to their country, relative age and entry cohort", {
  d <- suppressMessages(prepare_oosc_data(countries, admin, survey))
  s <- d$stan_data
  ey <- d$index$ey_grid
  expect_equal(s$A_age, c(4, 1, 4))                        # 9 - 6 + 1, 7 - 7 + 1, 10 - 7 + 1
  expect_equal(ey[s$A_ey_idx], c(2007, 2010, 2007))        # entry year = year - age_rel + 1
  expect_equal(s$A_country, c(1, 2, 2))
  expect_equal(s$A_region, c(1, 2, 2))
  expect_equal(s$K_obs, qnorm(c(0.25, 0.4)))
  expect_equal(s$f_obs, dnorm(qnorm(c(0.25, 0.4))))
  expect_equal(ey[s$S_ey_idx], c(2005 - 3 + 1, 2015 - 3 + 1))
  # the grid covers the oldest cohort in the first estimation year and the whole window
  expect_equal(min(ey), 2000 - s$A_max + 1)
  expect_equal(max(ey), 2022)
  expect_equal(s$N_K1, ncol(s$B1))
  expect_equal(ey[1] + 0, min(ey))
})

test_that("administrative-only input works", {
  d <- suppressMessages(prepare_oosc_data(countries, admin))
  expect_equal(d$stan_data$N_S, 0)
  expect_equal(d$stan_data$N_SERIES, 1)
})
