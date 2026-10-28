# Synthetic demonstration of the R package: simulate -> prepare -> fit -> summarise.
# No real data is used. Run from the repository root after installing the package:
#   Rscript examples/r/synthetic_demo.R
library(oosccohort)

sim <- simulate_oosc(seed = 2022)
data <- prepare_oosc_data(sim$countries, sim$admin, sim$survey)
print(data)

# A short run for demonstration; use the defaults (paper settings) for real fits.
fit <- fit_oosc(data, chains = 2, iter_warmup = 300, iter_sampling = 160, thin = 1, seed = 2022,
                cores = 2, refresh = 0)
print(fit)

rates <- merge(oosc_rates(fit), sim$truth, by = c("country", "year", "age", "age_rel"))
cat(sprintf("True rates inside the 90%% interval: %.1f%%\n",
            100 * mean(rates$q05 <= rates$true_rate & rates$true_rate <= rates$q95)))
cat(sprintf("Mean absolute error of the posterior median: %.2f percentage points\n",
            100 * mean(abs(rates$q50 - rates$true_rate))))
cat("Simulated data and a short run: a pipeline check, not a formal or empirical result.\n")
