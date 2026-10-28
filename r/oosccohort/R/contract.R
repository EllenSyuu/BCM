#' Validate model inputs against the data contract
#'
#' The model reads three tables. Each function checks one of them and returns
#' it with standardised column types, or stops with a message that names the
#' problem. Columns not listed are ignored.
#'
#' **countries**: one row per country.
#' \describe{
#'   \item{country}{Country code or name (character, unique).}
#'   \item{region}{Region label (character). The paper uses the seven SDG regions.}
#'   \item{entry_age}{Minimum official primary entry age over the period (integer). Relative age 1 is this age (paper Sec. 3).}
#'   \item{max_age}{Optional. Oldest single age to model (integer); observations above it are dropped.}
#' }
#'
#' **admin**: administrative out-of-school rates, one row per country, year and single age.
#' \describe{
#'   \item{country, year, age}{Keys; `age` is the calendar age in years.}
#'   \item{rate}{1 - enrolment / population. Values may be negative; the paper drops values below -0.1 (Sec. 2.1), which [prepare_oosc_data()] does.}
#' }
#'
#' **survey**: survey or census out-of-school rates.
#' \describe{
#'   \item{country, year, age}{Keys, as above.}
#'   \item{rate}{Weighted out-of-school share, strictly between 0 and 1.}
#'   \item{se}{Sampling standard error in real space (for example from a clustered jackknife), positive.}
#'   \item{series}{Survey programme (for example "DHS", "MICS", "Census").}
#'   \item{wave}{Survey wave (for example "DHS5", "MICS4", "Census").}
#' }
#'
#' @param countries,admin,survey Data frames as described above.
#' @return The validated data frame.
#' @name data_contract
NULL

#' @rdname data_contract
#' @export
validate_countries <- function(countries) {
  countries <- .require_columns(countries, c("country", "region", "entry_age"), "countries")
  countries$country <- as.character(countries$country)
  countries$region <- as.character(countries$region)
  countries$entry_age <- .as_whole(countries$entry_age, "countries$entry_age")
  if (anyDuplicated(countries$country)) {
    stop("countries: duplicated country: ", .first(countries$country[duplicated(countries$country)]), call. = FALSE)
  }
  if (any(countries$entry_age < 3 | countries$entry_age > 9)) {
    stop("countries$entry_age: expected values between 3 and 9.", call. = FALSE)
  }
  if ("max_age" %in% names(countries)) {
    countries$max_age <- .as_whole(countries$max_age, "countries$max_age")
    if (any(countries$max_age < countries$entry_age)) {
      stop("countries$max_age must not be below entry_age.", call. = FALSE)
    }
  }
  countries
}

#' @rdname data_contract
#' @export
validate_admin <- function(admin, countries) {
  admin <- .require_columns(admin, c("country", "year", "age", "rate"), "admin")
  admin <- .validate_keys(admin, countries, "admin")
  admin$rate <- .as_finite(admin$rate, "admin$rate")
  if (any(admin$rate > 1)) {
    stop("admin$rate: values above 1 are impossible for 1 - enrolment / population.", call. = FALSE)
  }
  .check_unique(admin, c("country", "year", "age"), "admin")
  admin
}

#' @rdname data_contract
#' @export
validate_survey <- function(survey, countries) {
  survey <- .require_columns(survey, c("country", "year", "age", "rate", "se", "series", "wave"), "survey")
  survey <- .validate_keys(survey, countries, "survey")
  survey$rate <- .as_finite(survey$rate, "survey$rate")
  survey$se <- .as_finite(survey$se, "survey$se")
  if (any(survey$rate < 0 | survey$rate > 1)) stop("survey$rate must lie in [0, 1].", call. = FALSE)
  if (any(survey$se <= 0)) stop("survey$se must be positive.", call. = FALSE)
  survey$series <- as.character(survey$series)
  survey$wave <- as.character(survey$wave)
  if (anyNA(survey$series) || anyNA(survey$wave)) stop("survey$series and survey$wave must not be missing.", call. = FALSE)
  survey
}

.require_columns <- function(df, cols, what) {
  if (!is.data.frame(df)) stop(what, " must be a data frame.", call. = FALSE)
  missing <- setdiff(cols, names(df))
  if (length(missing)) stop(what, ": missing column(s): ", paste(missing, collapse = ", "), call. = FALSE)
  if (!nrow(df)) stop(what, " has no rows.", call. = FALSE)
  for (col in cols) {
    if (anyNA(df[[col]])) stop(what, "$", col, " contains missing values.", call. = FALSE)
  }
  as.data.frame(df, stringsAsFactors = FALSE)
}

.validate_keys <- function(df, countries, what) {
  df$country <- as.character(df$country)
  unknown <- setdiff(unique(df$country), countries$country)
  if (length(unknown)) stop(what, ": country not in `countries`: ", .first(unknown), call. = FALSE)
  df$year <- .as_whole(df$year, paste0(what, "$year"))
  df$age <- .as_whole(df$age, paste0(what, "$age"))
  df
}

.as_whole <- function(x, what) {
  if (!is.numeric(x) || any(!is.finite(x)) || any(abs(x - round(x)) > 1e-8)) {
    stop(what, " must contain whole numbers.", call. = FALSE)
  }
  as.integer(round(x))
}

.as_finite <- function(x, what) {
  if (!is.numeric(x) || any(!is.finite(x))) stop(what, " must be finite numbers.", call. = FALSE)
  as.numeric(x)
}

.check_unique <- function(df, keys, what) {
  dup <- duplicated(df[keys])
  if (any(dup)) {
    stop(what, ": duplicated ", paste(keys, collapse = "/"), " combination, first at row ", which(dup)[1], ".", call. = FALSE)
  }
}

.first <- function(x) paste0("'", x[1], "'", if (length(x) > 1) paste0(" (and ", length(x) - 1, " more)") else "")
