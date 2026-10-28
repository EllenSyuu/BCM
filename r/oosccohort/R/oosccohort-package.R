#' oosccohort: Bayesian cohort model for out-of-school rates
#'
#' An independent implementation, written from the published methodology, of
#' the Bayesian cohort model for SDG indicator 4.1.4 described in:
#'
#' Dharamshi, A., Barakat, B., Antoninis, M. and Montoya, S. (2022).
#' *A Bayesian Cohort Model for Estimating SDG Indicator 4.1.4: Out-of-School
#' Rates.* UNESCO Institute for Statistics and Global Education Monitoring
#' Report, Technical Cooperation Group on the Indicators for SDG 4, document
#' WG/HHS/2.
#'
#' It is not an official UNESCO product and does not produce official estimates.
#'
#' Workflow: [validate_countries()], [validate_admin()] and [validate_survey()]
#' check the inputs ([data_contract]); [prepare_oosc_data()] builds the model
#' input; [fit_oosc()] samples the posterior; [oosc_rates()] and
#' [oosc_diagnostics()] summarise it. [simulate_oosc()] makes a synthetic data
#' set for trying the workflow.
#'
#' @keywords internal
"_PACKAGE"
