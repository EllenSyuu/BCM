#' Simulate a small synthetic data set
#'
#' Draws administrative and survey observations from a known out-of-school
#' surface for four synthetic countries (codes `SYA`-`SYD`, not real countries)
#' in two regions, single ages 6-13 and years 2000-2022. Country `SYD` has
#' administrative data only every third year. Survey observations carry a
#' country-by-series bias. This is the same design as the Python synthetic
#' demo; it contains no real data.
#'
#' @param seed Random seed.
#' @param n_survey Survey observations per country.
#' @return A list with `countries`, `admin`, `survey` (tables in the format of
#'   [data_contract]) and `truth` (the true rate for every cell).
#' @examples
#' sim <- simulate_oosc(seed = 1)
#' head(sim$admin)
#' @export
simulate_oosc <- function(seed = 2022L, n_survey = 8L) {
  old <- if (exists(".Random.seed", envir = globalenv())) get(".Random.seed", envir = globalenv())
  on.exit(if (!is.null(old)) assign(".Random.seed", old, envir = globalenv()), add = TRUE)
  set.seed(seed)

  years <- 2000:2022
  a_max <- 8L
  entry_age <- 6L
  countries <- data.frame(country = c("SYA", "SYB", "SYC", "SYD"), region = c("Region 1", "Region 1", "Region 2", "Region 2"),
                          entry_age = entry_age, stringsAsFactors = FALSE)
  level <- c(-1.1, -0.6, -0.3, -1.4)
  decline <- c(0.030, 0.020, 0.035, 0.015)
  true_probit <- function(c, year, a) level[c] - decline[c] * ((year - a + 1) - 2000) + 0.06 * (a - 1)

  admin <- survey <- list()
  for (c in seq_len(nrow(countries))) {
    admin_years <- if (countries$country[c] == "SYD") years[seq(1, length(years), by = 3)] else years
    g <- expand.grid(a = seq_len(a_max), year = admin_years)
    admin[[c]] <- data.frame(country = countries$country[c], year = g$year, age = entry_age + g$a - 1L,
                             rate = stats::pnorm(true_probit(c, g$year, g$a)) + stats::rnorm(nrow(g), 0, 0.02))
    bias <- stats::rnorm(2, 0, 0.08)
    j <- seq_len(n_survey) - 1L
    year <- sample(years, n_survey, replace = TRUE)
    a <- sample.int(a_max, n_survey, replace = TRUE)
    s <- j %% 2L + 1L
    k <- true_probit(c, year, a) + bias[s] + stats::rnorm(n_survey, 0, 0.05)
    survey[[c]] <- data.frame(country = countries$country[c], year = year, age = entry_age + a - 1L,
                              rate = stats::pnorm(k), se = 0.02, series = c("Survey A", "Survey B")[s],
                              wave = paste("Wave", (j %/% 4L) %% 2L + 1L), stringsAsFactors = FALSE)
  }
  g <- expand.grid(a = seq_len(a_max), year = years, c = seq_len(nrow(countries)))
  truth <- data.frame(country = countries$country[g$c], year = g$year, age = entry_age + g$a - 1L, age_rel = g$a,
                      true_rate = stats::pnorm(true_probit(g$c, g$year, g$a)), stringsAsFactors = FALSE)
  list(countries = countries, admin = do.call(rbind, admin), survey = do.call(rbind, survey), truth = truth)
}
