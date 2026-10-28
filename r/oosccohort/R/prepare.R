#' Build the model input from validated tables
#'
#' Applies the paper's data rules, indexes every observation by country,
#' relative age and entry cohort, and builds the spline bases. Fit one sex
#' population at a time (paper Sec. 3.4).
#'
#' Rules applied, each reported with a message:
#' * administrative rates below `negative_cutoff` (default -0.1) are dropped
#'   (paper Sec. 2.1); other negative values are kept;
#' * survey rates of exactly 0 or 1 are dropped, because their probit is
#'   infinite (the paper is silent; audit item I5);
#' * observations below a country's entry age, or above its `max_age`, are dropped.
#'
#' @param countries,admin,survey Tables described in [data_contract]. `survey`
#'   may be `NULL` for an administrative-only fit.
#' @param years Estimation window; the entry-year grid always covers it.
#' @param negative_cutoff Administrative rates below this value are dropped.
#' @return An object of class `oosc_data`: a list with `stan_data` (the list
#'   passed to Stan, 1-based indices), `index` (labels and grids) and the
#'   observations kept, `admin` and `survey`.
#' @examples
#' sim <- simulate_oosc(seed = 1)
#' d <- prepare_oosc_data(sim$countries, sim$admin, sim$survey)
#' d
#' @export
prepare_oosc_data <- function(countries, admin, survey = NULL, years = 2000:2022, negative_cutoff = -0.1) {
  countries <- validate_countries(countries)
  admin <- validate_admin(admin, countries)
  has_survey <- !is.null(survey) && NROW(survey) > 0
  survey <- if (has_survey) validate_survey(survey, countries) else NULL

  low <- admin$rate < negative_cutoff
  if (any(low)) message(sprintf("Dropped %d administrative rate(s) below %s.", sum(low), negative_cutoff))
  admin <- admin[!low, , drop = FALSE]
  if (has_survey) {
    degenerate <- survey$rate <= 0 | survey$rate >= 1
    if (any(degenerate)) message(sprintf("Dropped %d survey rate(s) equal to 0 or 1.", sum(degenerate)))
    survey <- survey[!degenerate, , drop = FALSE]
  }
  admin <- .attach_relative_age(admin, countries, "administrative")
  if (has_survey) survey <- .attach_relative_age(survey, countries, "survey")

  used <- countries$country[countries$country %in% c(admin$country, if (has_survey) survey$country)]
  countries <- countries[match(used, countries$country), , drop = FALSE]
  regions <- sort(unique(countries$region))
  series <- if (has_survey) sort(unique(survey$series)) else "none"
  waves <- if (has_survey) sort(unique(survey$wave)) else "none"

  a_max <- max(admin$age_rel, if (has_survey) survey$age_rel)
  all_years <- c(admin$year, if (has_survey) survey$year)
  first_year <- min(min(all_years), min(years))
  last_year <- max(max(all_years), max(years))
  # entry year = year - age_rel + 1; the oldest cohort is at the first year and the oldest age
  ey_grid <- seq.int(first_year - a_max + 1L, last_year)
  B1 <- bspline_basis(ey_grid, knot_spacing = 1L)
  B5 <- bspline_basis(ey_grid, knot_spacing = 5L)

  ey_idx <- function(df) df$year - df$age_rel + 1L - ey_grid[1] + 1L
  country_id <- function(df) match(df$country, countries$country)
  region_of_country <- match(countries$region, regions)
  empty_i <- integer(0)
  empty_r <- numeric(0)
  if (has_survey) {
    k_obs <- stats::qnorm(survey$rate)
  }

  stan_data <- list(
    C = nrow(countries), R = length(regions), A_max = a_max, N_EY = length(ey_grid),
    N_K1 = ncol(B1), MU_ANCHOR = mu_anchor_index(ey_grid), N_K5 = ncol(B5),
    N_SERIES = length(series), N_WAVE = length(waves),
    B1 = B1, B5 = B5, region_of_country = region_of_country,
    N_A = nrow(admin), A_obs = admin$rate, A_country = country_id(admin),
    A_region = region_of_country[country_id(admin)], A_age = admin$age_rel, A_ey_idx = ey_idx(admin),
    N_S = if (has_survey) nrow(survey) else 0L,
    K_obs = if (has_survey) k_obs else empty_r,
    f_obs = if (has_survey) stats::dnorm(k_obs) else empty_r,
    nu = if (has_survey) survey$se else empty_r,
    S_country = if (has_survey) country_id(survey) else empty_i,
    S_age = if (has_survey) survey$age_rel else empty_i,
    S_ey_idx = if (has_survey) ey_idx(survey) else empty_i,
    S_series = if (has_survey) match(survey$series, series) else empty_i,
    S_wave = if (has_survey) match(survey$wave, waves) else empty_i
  )
  structure(
    list(
      stan_data = stan_data,
      index = list(countries = countries, regions = regions, series = series, waves = waves,
                   ey_grid = ey_grid, years = as.integer(years), negative_cutoff = negative_cutoff),
      admin = admin,
      survey = survey
    ),
    class = "oosc_data"
  )
}

#' @export
print.oosc_data <- function(x, ...) {
  s <- x$stan_data
  cat("<oosc_data>\n")
  cat(sprintf("  countries: %d   regions: %d   relative ages: 1-%d\n", s$C, s$R, s$A_max))
  cat(sprintf("  administrative observations: %d   survey observations: %d\n", s$N_A, s$N_S))
  cat(sprintf("  entry-year grid: %d-%d (%d years); spline bases %d (annual) and %d (5-year)\n",
              min(x$index$ey_grid), max(x$index$ey_grid), s$N_EY, s$N_K1, s$N_K5))
  invisible(x)
}

.attach_relative_age <- function(df, countries, what) {
  i <- match(df$country, countries$country)
  df$age_rel <- df$age - countries$entry_age[i] + 1L
  keep <- df$age_rel >= 1L
  if ("max_age" %in% names(countries)) keep <- keep & df$age <= countries$max_age[i]
  if (any(!keep)) message(sprintf("Dropped %d %s observation(s) outside the modelled ages.", sum(!keep), what))
  df[keep, , drop = FALSE]
}
