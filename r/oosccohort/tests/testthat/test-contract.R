countries <- data.frame(country = c("AAA", "BBB"), region = c("R1", "R2"), entry_age = c(6, 7))

test_that("valid tables pass and are standardised", {
  out <- validate_countries(countries)
  expect_type(out$entry_age, "integer")
  admin <- data.frame(country = "AAA", year = 2010, age = 6:8, rate = c(0.1, -0.05, 0.2))
  expect_s3_class(validate_admin(admin, out), "data.frame")
})

test_that("contract violations give clear errors", {
  expect_error(validate_countries(countries[, -2]), "missing column\\(s\\): region")
  expect_error(validate_countries(rbind(countries, countries[1, ])), "duplicated country")
  expect_error(validate_admin(data.frame(country = "ZZZ", year = 2010, age = 6, rate = 0.1), countries), "not in `countries`")
  expect_error(validate_admin(data.frame(country = "AAA", year = 2010.5, age = 6, rate = 0.1), countries), "whole numbers")
  expect_error(validate_admin(data.frame(country = "AAA", year = 2010, age = 6, rate = 1.2), countries), "above 1")
  expect_error(validate_admin(data.frame(country = "AAA", year = c(2010, 2010), age = 6, rate = 0.1), countries), "duplicated")
  expect_error(validate_admin(data.frame(country = "AAA", year = 2010, age = 6, rate = NA_real_), countries), "missing values")
  sv <- data.frame(country = "AAA", year = 2010, age = 6, rate = 0.2, se = 0, series = "DHS", wave = "DHS5")
  expect_error(validate_survey(sv, countries), "se must be positive")
  expect_error(validate_survey(transform(sv, se = 0.01, rate = 1.5), countries), "\\[0, 1\\]")
})
