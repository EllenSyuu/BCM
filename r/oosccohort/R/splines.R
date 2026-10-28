#' Cubic B-spline basis on an entry-year grid
#'
#' Builds the spline basis matrices used by the model: annual knots for the
#' baseline \eqn{\mu} (paper Eq. 4) and five-year knots for the cohort changes
#' \eqn{\Theta} (Eq. 10). Boundary knots are clamped (repeated `degree + 1`
#' times); interior knots are placed every `knot_spacing` years strictly inside
#' the grid. The paper does not state the degree or the boundary treatment;
#' this is the convention documented in the project's paper audit (item I1),
#' and it matches the Python implementation exactly.
#'
#' @param ey_grid Sorted vector of consecutive integer entry years.
#' @param knot_spacing Years between interior knots (1 for \eqn{\mu}, 5 for \eqn{\Theta}).
#' @param degree Spline degree (default 3, cubic).
#' @return A matrix with one row per entry year and one column per basis function.
#' @examples
#' B <- bspline_basis(1990:2022, knot_spacing = 5)
#' dim(B)
#' range(rowSums(B))
#' @export
bspline_basis <- function(ey_grid, knot_spacing, degree = 3L) {
  knots <- .clamped_knots(ey_grid, knot_spacing, degree)
  basis <- splines::splineDesign(knots, x = as.numeric(ey_grid), ord = degree + 1L, outer.ok = FALSE)
  unname(basis)
}

#' Spline coefficient that the model anchors at calendar year 2000
#'
#' The paper (Eq. 27) puts its prior on the baseline at year 2000. Because
#' cohorts observed at older ages entered school before 2000, the entry-year
#' grid starts earlier, so the anchor is the annual-spline coefficient whose
#' Greville abscissa equals 2000 (paper audit item I2).
#'
#' @param ey_grid Sorted vector of consecutive integer entry years.
#' @param year Anchor year (default 2000).
#' @return The 1-based index of the anchored coefficient.
#' @export
mu_anchor_index <- function(ey_grid, year = 2000L) {
  greville <- .greville(ey_grid, knot_spacing = 1L, degree = 3L)
  hit <- which(abs(greville - year) < 1e-8)
  if (length(hit) != 1L || hit == 1L || hit == length(greville)) {
    stop("The annual spline must have exactly one interior coefficient at year ", year, ".", call. = FALSE)
  }
  hit
}

.clamped_knots <- function(ey_grid, knot_spacing, degree) {
  ey_grid <- as.integer(ey_grid)
  if (length(ey_grid) < 2L || any(diff(ey_grid) != 1L)) {
    stop("`ey_grid` must be sorted, consecutive integer years.", call. = FALSE)
  }
  lo <- min(ey_grid)
  hi <- max(ey_grid)
  interior <- if (lo + knot_spacing <= hi - knot_spacing) seq(lo + knot_spacing, hi - knot_spacing, by = knot_spacing) else numeric(0)
  interior <- interior[interior > lo & interior < hi]
  as.numeric(c(rep(lo, degree + 1L), interior, rep(hi, degree + 1L)))
}

.greville <- function(ey_grid, knot_spacing, degree) {
  knots <- .clamped_knots(ey_grid, knot_spacing, degree)
  n_basis <- length(knots) - degree - 1L
  vapply(seq_len(n_basis), function(i) mean(knots[(i + 1L):(i + degree)]), numeric(1))
}
