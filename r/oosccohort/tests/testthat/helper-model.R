# Compiled models are cached in a temporary directory unless OOSC_MODEL_CACHE
# points somewhere persistent (useful locally; CI compiles once per run).
options(oosccohort.cache_dir = Sys.getenv("OOSC_MODEL_CACHE", file.path(tempdir(), "oosc-model-cache")))

fixture <- function(name) jsonlite::fromJSON(test_path("fixtures", name), simplifyVector = TRUE)

skip_if_no_stan <- function() {
  skip_on_cran()
  skip_if(identical(Sys.getenv("OOSC_SKIP_STAN"), "true"), "Stan tests disabled with OOSC_SKIP_STAN=true")
}
