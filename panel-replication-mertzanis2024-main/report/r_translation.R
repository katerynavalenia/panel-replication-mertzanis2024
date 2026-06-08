# =============================================================================
# R TRANSLATION: Mertzanis (2024) Replication
# "Central bank policies and green bond issuance on a global scale"
# Energy Economics, 133, 107541
#
# Translated from Python using LLM assistance.
#
# KEY FINDING (preserved from Python analysis):
# cbmnd, cbenf, cbsys are ALL time-invariant (0% within variance).
# Entity FE and First-Difference estimators CANNOT identify their coefficients.
# Only Pooled OLS, Between, and Random Effects estimators capture their effects.
# This is not a bug — it reflects the data structure.
#
# Required packages:
#   readxl, dplyr, plm, lmtest, sandwich, AER, stargazer (optional)
# Install with: install.packages(c("readxl","dplyr","plm","lmtest","sandwich","AER","stargazer"))
# =============================================================================

# =============================================================================
# SECTION 0: SETUP AND PACKAGE LOADING
# =============================================================================

# Install missing packages automatically (comment out if not desired)
required_pkgs <- c("readxl", "dplyr", "plm", "lmtest", "sandwich", "AER", "stargazer")
new_pkgs <- required_pkgs[!(required_pkgs %in% installed.packages()[, "Package"])]
if (length(new_pkgs)) install.packages(new_pkgs, repos = "https://cloud.r-project.org")

library(readxl)
library(dplyr)
library(plm)
library(lmtest)     # coeftest()
library(sandwich)   # vcovCL() for clustered SE
library(AER)        # ivreg()

# Optional: stargazer for formatted tables
if (requireNamespace("stargazer", quietly = TRUE)) library(stargazer)

# Set working directory to project root (adjust as needed)
# setwd("/Users/solaforsure/Desktop/panel-replication-mertzanis2024-main/Econometrics_project")

# =============================================================================
# SECTION 1: LOAD DATA
# =============================================================================

# Python used pd.read_excel(); R equivalent:
data_path <- "../data/raw/data.xlsx"  # adjust if needed

df_raw <- read_excel(data_path, sheet = 1)

cat("Dimensions of raw data:", nrow(df_raw), "rows x", ncol(df_raw), "cols\n")
cat("Column names:\n")
print(names(df_raw))

# =============================================================================
# SECTION 2: VARIABLE RENAMING
# (Python used a rename_map dict; adjust the mapping below to match your Excel)
# =============================================================================

# Example: rename if your Excel uses different column names
# df_raw <- df_raw %>% rename(bndgrn = "LogGreenBonds", cbmnd = "CB_Mandate", ...)
# For now we assume the Excel already uses the target column names.
df <- df_raw

# Confirm key variables are present
required_vars <- c("country", "year", "bndgrn", "cbmnd", "cbenf", "cbsys",
                   "infl", "rating", "fie", "gdpg", "dum9", "dum12",
                   "hierarchy", "openness", "purity",
                   "prodstr", "bigtech", "ngain")

missing_vars <- setdiff(required_vars, names(df))
if (length(missing_vars) > 0) {
  warning("The following variables are missing — check rename mapping:\n",
          paste(missing_vars, collapse = ", "))
}

# Ensure correct types
df$country <- as.character(df$country)
df$year    <- as.integer(df$year)

# Sort panel
df <- df %>% arrange(country, year)

# =============================================================================
# SECTION 3: SAMPLE SELECTION
# (Python: keep countries with >= 3 CONSECUTIVE non-missing bndgrn observations)
# R equivalent using rle() to find maximum run of non-missing Y per country.
# =============================================================================

#' Find the maximum length of consecutive TRUE values in a logical vector.
#' Uses rle() (run-length encoding) — base R function.
max_consecutive_true <- function(x) {
  # x: logical vector (TRUE = non-missing observation)
  r <- rle(x)
  if (!any(r$values)) return(0L)
  max(r$lengths[r$values])
}

# Flag non-missing bndgrn and compute max consecutive run per country
df <- df %>%
  mutate(has_y = !is.na(bndgrn)) %>%
  group_by(country) %>%
  mutate(max_consec = max_consecutive_true(has_y)) %>%
  ungroup() %>%
  filter(max_consec >= 3) %>%
  select(-has_y, -max_consec)

cat("After sample selection:\n")
cat("  Countries:", n_distinct(df$country), "\n")
cat("  Observations:", nrow(df), "\n")

# =============================================================================
# SECTION 4: PANEL DATA OBJECT
# (plm package requires a pdata.frame with panel index variables)
# =============================================================================

pdf <- pdata.frame(df, index = c("country", "year"))

# Verify panel structure
cat("Panel dimensions (plm):\n")
print(pdim(pdf))

# =============================================================================
# SECTION 5: VARIANCE DECOMPOSITION
# (Python: computed within/between/overall SD for each variable)
# plm::summary.pseries gives between/within decomposition.
# =============================================================================

cat("\n")
cat("========================================================\n")
cat("VARIANCE DECOMPOSITION\n")
cat("KEY: cbmnd, cbenf, cbsys should show near-zero within variance\n")
cat("========================================================\n")

decomp_vars <- c("bndgrn", "cbmnd", "cbenf", "cbsys", "infl", "rating", "fie", "gdpg")

for (v in decomp_vars) {
  if (v %in% names(pdf)) {
    s <- summary(pdf[[v]])  # plm pseries summary
    # Manual decomposition using plm::Between and Within
    x     <- as.numeric(pdf[[v]])
    x_b   <- as.numeric(plm::Between(pdf[[v]]))   # group means (between)
    x_w   <- x - x_b                               # within deviations
    cat(sprintf("%-10s  overall SD=%.4f  between SD=%.4f  within SD=%.4f\n",
                v, sd(x, na.rm = TRUE),
                sd(x_b, na.rm = TRUE),
                sd(x_w, na.rm = TRUE)))
  }
}

# Translation note: Python used df.groupby(country)[var].transform('std') for
# within SD and df.groupby(country)[var].mean() for between. R's plm::Between()
# and plm::Within() are direct equivalents.

# =============================================================================
# SECTION 6: DEFINE FORMULA COMPONENTS
# =============================================================================

xctrl   <- c("infl", "rating", "fie", "gdpg", "dum9", "dum12")
xvar    <- c("cbmnd", "cbenf", "cbsys", xctrl)
xvar_tv <- c("infl", "rating", "fie", "gdpg")    # time-varying
xvar_ti <- c("cbmnd", "cbenf", "cbsys", "dum9", "dum12")  # time-invariant
ziv     <- c("hierarchy", "purity", "openness")
xtab7   <- c("risk", "energy", "geopolitical")   # Table 7 extras

# Helper to build formula strings
make_formula <- function(lhs, rhs) {
  as.formula(paste(lhs, "~", paste(rhs, collapse = " + ")))
}

# Helper: cluster-robust SE using sandwich::vcovCL (clustered by country)
clust_se <- function(model, df_data, cluster_var = "country") {
  coeftest(model, vcov = vcovCL(model, cluster = df_data[[cluster_var]]))
}

# =============================================================================
# SECTION 7: HOMEWORK ESTIMATORS
# =============================================================================

cat("\n")
cat("========================================================\n")
cat("HOMEWORK ESTIMATORS\n")
cat("========================================================\n")

# --- 7.1 BETWEEN ESTIMATOR ---
# Python: statsmodels BetweenOLS — regress group means on group-mean RHS.
# plm: model="between"
cat("--- Between Estimator ---\n")
fm_main <- make_formula("bndgrn", xvar)

est_between <- plm(fm_main, data = pdf, model = "between")
summary(est_between)
# Note: between estimator uses country-level means; SE not clustered (one obs/country)

# --- 7.2 ONE-WAY ENTITY FE (Within) ---
# WARNING: cbmnd, cbenf, cbsys are time-invariant → plm will drop them (perfect
# collinearity with entity dummies). Coefficients will be NA.
cat("\n--- Within (Entity FE) Estimator ---\n")
cat("NOTE: cbmnd/cbenf/cbsys are time-invariant — FE cannot identify them.\n")

est_fe <- plm(fm_main, data = pdf, model = "within", effect = "individual")
summary(est_fe)
# Clustered SE:
coeftest(est_fe, vcov = vcovHC(est_fe, type = "HC1", cluster = "group"))

# --- 7.3 RANDOM EFFECTS WITH MUNDLAK CORRECTION ---
# Mundlak (1978): add group means of time-varying controls to RE model.
# This controls for correlation between regressors and individual effects
# while retaining identification of time-invariant variables.
cat("\n--- Random Effects with Mundlak Correction ---\n")

# Generate group means (between transformation) for time-varying controls
for (v in xvar_tv) {
  if (v %in% names(df)) {
    df[[paste0("mean_", v)]] <- ave(df[[v]], df$country, FUN = function(x) mean(x, na.rm = TRUE))
  }
}

mundlak_means <- paste0("mean_", xvar_tv)
fm_mundlak <- make_formula("bndgrn", c(xvar, mundlak_means))

# Re-create pdata.frame with new columns
pdf_m <- pdata.frame(df, index = c("country", "year"))
est_re_mundlak <- plm(fm_mundlak, data = pdf_m, model = "random")
summary(est_re_mundlak)
coeftest(est_re_mundlak, vcov = vcovHC(est_re_mundlak, type = "HC1", cluster = "group"))

# Translation note: Python added group means as extra columns and ran pooled OLS.
# plm's model="random" with GLS is preferred; the Mundlak means make it
# asymptotically equivalent to the Python approach.

# --- 7.4 TWO-WAY FIXED EFFECTS (TWFE) ---
# WARNING: Time-invariant CB vars will be dropped.
cat("\n--- Two-Way Fixed Effects (Entity + Year FE) ---\n")
cat("NOTE: cbmnd/cbenf/cbsys dropped by TWFE.\n")

est_twfe <- plm(fm_main, data = pdf, model = "within", effect = "twoways")
summary(est_twfe)
coeftest(est_twfe, vcov = vcovHC(est_twfe, type = "HC1", cluster = "group"))

# --- 7.5 FIRST DIFFERENCES ---
# WARNING: Time-invariant vars difference to 0 → dropped.
cat("\n--- First Differences Estimator ---\n")
cat("NOTE: cbmnd/cbenf/cbsys difference to zero — FD cannot identify them.\n")

est_fd <- plm(fm_main, data = pdf, model = "fd")
summary(est_fd)
# Translation note: Python computed df.groupby(country)[vars].diff() and ran OLS.
# plm model="fd" is the direct equivalent.

# =============================================================================
# SECTION 8: PAPER TABLE 4 — POOLED OLS, +YEAR FE, +ENTITY FE, TWFE
# (Python: main regression table, cluster SE by country)
# =============================================================================

cat("\n")
cat("========================================================\n")
cat("TABLE 4: MAIN REGRESSIONS\n")
cat("========================================================\n")

# Col 1: Pooled OLS
cat("--- Table 4, Col 1: Pooled OLS ---\n")
t4_col1 <- lm(fm_main, data = df)
t4_col1_se <- clust_se(t4_col1, df)
print(t4_col1_se)

# Col 2: Pooled OLS + Year FE
cat("\n--- Table 4, Col 2: Pooled OLS + Year FE ---\n")
fm_yearfe <- make_formula("bndgrn", c(xvar, "factor(year)"))
t4_col2 <- lm(fm_yearfe, data = df)
t4_col2_se <- clust_se(t4_col2, df)
print(t4_col2_se)

# Col 3: Entity FE (cbmnd/cbenf/cbsys will be dropped by plm)
cat("\n--- Table 4, Col 3: Entity FE ---\n")
t4_col3 <- plm(fm_main, data = pdf, model = "within", effect = "individual")
t4_col3_se <- coeftest(t4_col3, vcov = vcovHC(t4_col3, type = "HC1", cluster = "group"))
print(t4_col3_se)

# Col 4: TWFE
cat("\n--- Table 4, Col 4: TWFE ---\n")
t4_col4 <- plm(fm_main, data = pdf, model = "within", effect = "twoways")
t4_col4_se <- coeftest(t4_col4, vcov = vcovHC(t4_col4, type = "HC1", cluster = "group"))
print(t4_col4_se)

# =============================================================================
# SECTION 9: PAPER TABLE 5 — ROBUSTNESS CHECKS
# =============================================================================

cat("\n")
cat("========================================================\n")
cat("TABLE 5: ROBUSTNESS CHECKS\n")
cat("========================================================\n")

# --- 9.1 Gov bonds DV (x1l) ---
cat("--- Table 5: DV = Gov bonds (x1l) ---\n")
if ("x1l" %in% names(df)) {
  fm_x1l <- make_formula("x1l", xvar)
  t5_gov <- lm(fm_x1l, data = df)
  print(clust_se(t5_gov, df))
} else {
  cat("Variable x1l not found — skipping.\n")
}

# --- 9.2 Corp bonds DV (x2l) ---
cat("\n--- Table 5: DV = Corp bonds (x2l) ---\n")
if ("x2l" %in% names(df)) {
  fm_x2l <- make_formula("x2l", xvar)
  t5_corp <- lm(fm_x2l, data = df)
  print(clust_se(t5_corp, df))
} else {
  cat("Variable x2l not found — skipping.\n")
}

# --- 9.3 Developed vs Developing split ---
cat("\n--- Table 5: Developed/Developing split ---\n")
if ("developed" %in% names(df)) {
  t5_dev        <- lm(fm_main, data = df[df$developed == 1, ])
  t5_developing <- lm(fm_main, data = df[df$developed == 0, ])
  cat("Developed countries:\n"); print(clust_se(t5_dev, df[df$developed == 1, ]))
  cat("Developing countries:\n"); print(clust_se(t5_developing, df[df$developed == 0, ]))
} else {
  cat("Variable 'developed' not found — adjust split variable name.\n")
}

# --- 9.4 Ex-China ---
cat("\n--- Table 5: Ex-China ---\n")
df_exchina <- df[df$country != "China", ]
t5_exchina <- lm(fm_main, data = df_exchina)
print(clust_se(t5_exchina, df_exchina))

# --- 9.5 Nonlinear CB terms ---
cat("\n--- Table 5: Nonlinear (quadratic) CB terms ---\n")
df$cbmnd_sq <- df$cbmnd^2
df$cbenf_sq <- df$cbenf^2
df$cbsys_sq <- df$cbsys^2

fm_nonlin <- make_formula("bndgrn",
  c("cbmnd", "cbmnd_sq", "cbenf", "cbenf_sq", "cbsys", "cbsys_sq", xctrl))
t5_nonlin <- lm(fm_nonlin, data = df)
print(clust_se(t5_nonlin, df))

# RESET test for nonlinearity (Python used Ramsey RESET)
# lmtest::resettest() is the R equivalent
cat("\nRAMSEY RESET TEST for functional form:\n")
resettest(lm(fm_main, data = df), power = 2:3, type = "fitted")

# =============================================================================
# SECTION 10: TABLE 7 — ADDITIONAL CONTROLS
# (Python: added risk, energy, geopolitical risk indices)
# =============================================================================

cat("\n")
cat("========================================================\n")
cat("TABLE 7: ADDITIONAL CONTROLS\n")
cat("========================================================\n")

# Check availability of Table 7 variables
missing_t7 <- setdiff(xtab7, names(df))
if (length(missing_t7) > 0) {
  warning("Table 7 variables not found: ", paste(missing_t7, collapse = ", "))
}

available_t7 <- intersect(xtab7, names(df))
fm_t7 <- make_formula("bndgrn", c(xvar, available_t7))

t7_col1 <- lm(fm_t7, data = df)
print(clust_se(t7_col1, df))

fm_t7_yfe <- make_formula("bndgrn", c(xvar, available_t7, "factor(year)"))
t7_col2 <- lm(fm_t7_yfe, data = df)
print(clust_se(t7_col2, df))

pdf2 <- pdata.frame(df, index = c("country", "year"))
t7_col3 <- plm(fm_t7, data = pdf2, model = "within", effect = "individual")
print(coeftest(t7_col3, vcov = vcovHC(t7_col3, type = "HC1", cluster = "group")))

t7_col4 <- plm(fm_t7, data = pdf2, model = "within", effect = "twoways")
print(coeftest(t7_col4, vcov = vcovHC(t7_col4, type = "HC1", cluster = "group")))

# =============================================================================
# SECTION 11: IV / 2SLS
# (Python: linearmodels IV2SLS; R equivalent: ivreg() from AER package)
# NOTE: Since CB vars are time-invariant, IV should NOT use entity FE
#       (FE would absorb the endogenous variable). Use pooled IV instead.
# =============================================================================

cat("\n")
cat("========================================================\n")
cat("IV / 2SLS ESTIMATES\n")
cat("========================================================\n")

# ivreg formula syntax: y ~ exogenous | instruments
# Full formula: bndgrn ~ controls + endogenous | controls + instruments
# AER::ivreg uses: y ~ x1 + x2 + (endogenous ~ instruments)
# Translation note: Python used linearmodels.IV2SLS with separate lists for
# endog and instruments. AER::ivreg uses a two-part formula.

controls_str <- paste(xctrl, collapse = " + ")

# --- IV for cbmnd ---
cat("--- IV: cbmnd instrumented by hierarchy, purity, openness ---\n")
fm_iv_cbmnd <- as.formula(
  paste("bndgrn ~ cbenf + cbsys +", controls_str,
        "| (cbmnd ~ hierarchy + purity + openness) | cbenf + cbsys +", controls_str)
)
# Simpler AER syntax using | for all instruments:
fm_iv_cbmnd2 <- as.formula(
  paste("bndgrn ~ cbmnd + cbenf + cbsys +", controls_str,
        "| hierarchy + purity + openness + cbenf + cbsys +", controls_str)
)
iv_cbmnd <- ivreg(fm_iv_cbmnd2, data = df)
print(summary(iv_cbmnd, diagnostics = TRUE))
print(coeftest(iv_cbmnd, vcov = vcovCL(iv_cbmnd, cluster = df$country)))

# --- IV for cbenf ---
cat("\n--- IV: cbenf instrumented by hierarchy, purity, openness ---\n")
fm_iv_cbenf <- as.formula(
  paste("bndgrn ~ cbmnd + cbenf + cbsys +", controls_str,
        "| cbmnd + hierarchy + purity + openness + cbsys +", controls_str)
)
iv_cbenf <- ivreg(fm_iv_cbenf, data = df)
print(summary(iv_cbenf, diagnostics = TRUE))
print(coeftest(iv_cbenf, vcov = vcovCL(iv_cbenf, cluster = df$country)))

# --- IV for cbsys ---
cat("\n--- IV: cbsys instrumented by hierarchy, purity, openness ---\n")
fm_iv_cbsys <- as.formula(
  paste("bndgrn ~ cbmnd + cbenf + cbsys +", controls_str,
        "| cbmnd + cbenf + hierarchy + purity + openness +", controls_str)
)
iv_cbsys <- ivreg(fm_iv_cbsys, data = df)
print(summary(iv_cbsys, diagnostics = TRUE))
print(coeftest(iv_cbsys, vcov = vcovCL(iv_cbsys, cluster = df$country)))

# Note: ivreg(..., diagnostics = TRUE) reports:
#   - Weak instruments test (F-stat on first stage)
#   - Wu-Hausman endogeneity test
#   - Sargan overidentification test
# Python's linearmodels reports similar tests; the naming differs slightly.

# =============================================================================
# SECTION 12: INTERACTION TERMS
# (Python: cbenf × prodstr, cbenf × bigtech, cbenf × ngain)
# =============================================================================

cat("\n")
cat("========================================================\n")
cat("INTERACTION TERMS\n")
cat("========================================================\n")

# Generate interaction variables
df$cbenf_prodstr <- df$cbenf * df$prodstr
df$cbenf_bigtech <- df$cbenf * df$bigtech
df$cbenf_ngain   <- df$cbenf * df$ngain

# --- Interaction: cbenf × prodstr ---
cat("--- Interaction: cbenf × prodstr ---\n")
fm_int_prodstr <- make_formula("bndgrn",
  c("cbmnd", "cbenf", "cbsys", "prodstr", "cbenf_prodstr", xctrl))
int_prodstr <- lm(fm_int_prodstr, data = df)
print(clust_se(int_prodstr, df))

# Alternative R syntax using * (includes main effects automatically):
cat("\n--- Interaction via * syntax: cbenf × prodstr ---\n")
fm_int2 <- as.formula(
  paste("bndgrn ~ cbmnd + cbenf * prodstr + cbsys +", paste(xctrl, collapse = " + ")))
int_prodstr2 <- lm(fm_int2, data = df)
print(clust_se(int_prodstr2, df))

# --- Interaction: cbenf × bigtech ---
cat("\n--- Interaction: cbenf × bigtech ---\n")
fm_int_bigtech <- make_formula("bndgrn",
  c("cbmnd", "cbenf", "cbsys", "bigtech", "cbenf_bigtech", xctrl))
int_bigtech <- lm(fm_int_bigtech, data = df)
print(clust_se(int_bigtech, df))

# --- Interaction: cbenf × ngain ---
cat("\n--- Interaction: cbenf × ngain ---\n")
fm_int_ngain <- make_formula("bndgrn",
  c("cbmnd", "cbenf", "cbsys", "ngain", "cbenf_ngain", xctrl))
int_ngain <- lm(fm_int_ngain, data = df)
print(clust_se(int_ngain, df))

# Translation note: Python used statsmodels formula interface with "cbenf:prodstr".
# R's lm() uses: cbenf:prodstr for interaction only, cbenf*prodstr for main + interaction.
# The * operator is cleaner but make sure not to double-count main effects.

# =============================================================================
# SECTION 13: DYNAMIC PANEL — ANDERSON-HSIAO
# (Python: custom AH implementation using lagged Y and lagged X as instruments)
# =============================================================================

cat("\n")
cat("========================================================\n")
cat("DYNAMIC PANEL: Anderson-Hsiao\n")
cat("========================================================\n")

# Anderson-Hsiao (1982):
# 1. Take first differences to remove fixed effects: Δy = ΔβX + Δε
# 2. Instrument Δy(t-1) with y(t-2) or Δy(t-2)
# 3. Estimate via 2SLS

# Generate lags and differences manually (equivalent to Python .diff())
df <- df %>%
  arrange(country, year) %>%
  group_by(country) %>%
  mutate(
    L1_bndgrn    = lag(bndgrn, 1),
    L2_bndgrn    = lag(bndgrn, 2),
    D_bndgrn     = bndgrn - lag(bndgrn, 1),
    D_L1_bndgrn  = lag(bndgrn, 1) - lag(bndgrn, 2),
    # Differences for time-varying controls
    D_infl       = infl  - lag(infl,  1),
    D_rating     = rating - lag(rating, 1),
    D_fie        = fie   - lag(fie,   1),
    D_gdpg       = gdpg  - lag(gdpg,  1)
  ) %>%
  ungroup()

# Drop rows with NA lags (first two years per country)
df_ah <- df %>% filter(!is.na(D_bndgrn), !is.na(D_L1_bndgrn), !is.na(L2_bndgrn))

cat("Anderson-Hsiao sample size:", nrow(df_ah), "observations\n")

# AH IV: D_bndgrn ~ D_L1_bndgrn + D_controls, instrument D_L1_bndgrn with L2_bndgrn
fm_ah <- as.formula(
  "D_bndgrn ~ D_L1_bndgrn + D_infl + D_rating + D_fie + D_gdpg |
   L2_bndgrn + D_infl + D_rating + D_fie + D_gdpg"
)
est_ah <- ivreg(fm_ah, data = df_ah)
print(summary(est_ah, diagnostics = TRUE))
print(coeftest(est_ah, vcov = vcovCL(est_ah, cluster = df_ah$country)))

cat("
IMPORTANT: Since cbmnd/cbenf/cbsys are time-invariant, their first differences
equal zero for all observations. They are therefore excluded from the FD/AH equation.
The dynamic panel (Anderson-Hsiao) cannot estimate CB policy effects.
Only pooled OLS / between / RE can do so for these variables.

For full Arellano-Bond GMM, use the 'pgmm' function in plm:
  pgmm(bndgrn ~ lag(bndgrn, 1) + infl + rating + fie + gdpg |
       lag(bndgrn, 2:99) + lag(infl, 1:2),
       data = pdf, model = 'twosteps')
\n")

# =============================================================================
# SECTION 14: DIAGNOSTIC TESTS
# =============================================================================

cat("\n")
cat("========================================================\n")
cat("DIAGNOSTIC TESTS\n")
cat("========================================================\n")

# --- Hausman Test: FE vs RE ---
# Note: only uses time-varying controls because FE drops time-invariant vars
cat("--- Hausman Test (FE vs RE) ---\n")
fm_ctrl_only <- make_formula("bndgrn", xctrl)
phtest_fe <- plm(fm_ctrl_only, data = pdf, model = "within")
phtest_re <- plm(fm_ctrl_only, data = pdf, model = "random")
print(phtest(phtest_fe, phtest_re))

# --- Breusch-Pagan LM Test for RE vs Pooled OLS ---
cat("\n--- Breusch-Pagan LM Test (RE vs Pooled OLS) ---\n")
plmtest(plm(fm_ctrl_only, data = pdf, model = "pooling"), type = "bp")

# --- Pesaran Cross-Sectional Dependence ---
cat("\n--- Pesaran Cross-Sectional Dependence Test ---\n")
tryCatch({
  pcdtest(phtest_fe, test = "pesaran")
}, error = function(e) cat("pcdtest failed:", conditionMessage(e), "\n"))

# --- Wooldridge Serial Correlation Test (pbgtest) ---
cat("\n--- Wooldridge/Breusch-Godfrey Serial Correlation ---\n")
tryCatch({
  pbgtest(phtest_fe)
}, error = function(e) cat("pbgtest failed:", conditionMessage(e), "\n"))

# =============================================================================
# SECTION 15: FORMATTED OUTPUT (optional, requires stargazer)
# =============================================================================

if (requireNamespace("stargazer", quietly = TRUE)) {
  cat("\n--- Stargazer Table 4 ---\n")

  # Get clustered SE vectors for stargazer
  se_col1 <- sqrt(diag(vcovCL(t4_col1, cluster = df$country)))
  se_col3 <- sqrt(diag(vcovHC(t4_col3, type = "HC1", cluster = "group")))
  se_col4 <- sqrt(diag(vcovHC(t4_col4, type = "HC1", cluster = "group")))

  stargazer(t4_col1, t4_col3, t4_col4,
            se          = list(se_col1, se_col3, se_col4),
            column.labels = c("Pooled OLS", "Entity FE", "TWFE"),
            title       = "Table 4: Main Regressions",
            type        = "text",
            notes       = "Clustered SE by country. cbmnd/cbenf/cbsys dropped in FE/TWFE.")
}

# =============================================================================
# TRANSLATION NOTES (Python -> R):
# =============================================================================
# 1. Sample selection: Python used a custom pandas rolling-window function.
#    R replicates with rle() (run-length encoding) on the has_y logical vector
#    per country. Results should match exactly.
#
# 2. Clustered SE: Python used cov_type='clustered' in statsmodels.
#    R uses sandwich::vcovCL(model, cluster = df$country) with lmtest::coeftest().
#    For plm models, vcovHC(..., cluster = "group") clusters by the panel unit.
#
# 3. Between estimator: Python used statsmodels BetweenOLS.
#    R uses plm(model = "between") — equivalent.
#
# 4. Mundlak RE: Python added group means as extra OLS regressors.
#    R adds dplyr::ave()-computed group means to the data, then uses plm RE.
#    The interpretation is equivalent; plm uses GLS rather than OLS.
#
# 5. FD estimator: Python computed .diff() per group and ran OLS.
#    R uses plm(model = "fd") — direct equivalent.
#
# 6. TWFE: Python added entity + year dummies in OLS.
#    R uses plm(effect = "twoways") — equivalent.
#
# 7. IV/2SLS: Python used linearmodels.IV2SLS.
#    R uses AER::ivreg(). The formula syntax for instruments differs:
#    Python: endog=[...], instruments=[...] as separate arguments.
#    R: y ~ X | Z where Z replaces the full instrument set (exog + IVs).
#
# 8. Anderson-Hsiao: Python implemented manually with pandas lag operations.
#    R replicates with dplyr::lag() inside group_by, then AER::ivreg.
#
# 9. Interaction terms: Python used statsmodels formula "var1:var2" notation.
#    R: use var1*var2 (includes main effects) or var1:var2 (interaction only).
#    When main effects are already in the formula, either approach is equivalent.
#
# 10. Time-invariant CB variables: This is the central econometric challenge.
#     cbmnd, cbenf, cbsys have 0% within variance. plm's within/fd models
#     will silently drop or produce NAs for these. This is expected behavior.
#     The paper's main results rely on pooled OLS and between/RE for CB vars.
# =============================================================================

cat("\n========================================================\n")
cat("REPLICATION COMPLETE\n")
cat("Mertzanis (2024) — R Translation\n")
cat("========================================================\n")
