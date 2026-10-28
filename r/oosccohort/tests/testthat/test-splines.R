test_that("bases are non-negative and sum to one", {
  for (spacing in c(1, 5)) {
    B <- bspline_basis(1990:2022, knot_spacing = spacing)
    expect_true(all(B >= 0))
    expect_equal(rowSums(B), rep(1, 33), tolerance = 1e-12)
  }
})

test_that("bases and anchor are identical to the Python implementation", {
  f <- fixture("numpyro_parity.json")
  expect_equal(bspline_basis(f$ey_grid, 1), f$stan_data$B1, tolerance = 1e-12)
  expect_equal(bspline_basis(f$ey_grid, 5), f$stan_data$B5, tolerance = 1e-12)
  expect_identical(mu_anchor_index(f$ey_grid), as.integer(f$stan_data$MU_ANCHOR))
})

test_that("grids that cannot anchor at 2000 are rejected", {
  expect_error(mu_anchor_index(2001:2022), "interior coefficient")
  expect_error(bspline_basis(c(2000, 2002, 2003), 1), "consecutive")
})
