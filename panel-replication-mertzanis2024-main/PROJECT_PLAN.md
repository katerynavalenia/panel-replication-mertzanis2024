# Project Plan: Panel Data Partial Replication
## Mertzanis (2024) — "Central Bank Policies and Green Bond Issuance on a Global Scale"
### Energy Economics, 133, 107541

---

## Paper Summary

| Item | Detail |
|---|---|
| **Dependent variable Y** | Green bond issuance (volume/amount at country level, log-transformed) |
| **Key explanatory variable X** | Central bank policy indicators (green/ESG policy index or programme dummy) |
| **Controls** | GDP per capita (log), financial development (credit/GDP), trade openness, governance quality, carbon emissions, energy structure, interest rate, institutional quality |
| **Data level** | Country-level panel |
| **Frequency** | Annual |
| **Approx. time span** | ~2010–2021 (confirm after downloading data) |
| **Econometric methods** | FE (one-way), TWFE, RE/Mundlak, FD, possibly System-GMM |
| **Data source** | Mendeley Data: doi:10.17632/xb2m4m8h24.1 |

---

## Day-by-Day Schedule (2 days)

### Day 1 — Data + Transformations + Descriptives

| Time block | Tasks |
|---|---|
| Morning (3h) | Steps 0–2: Download data, load, inspect, clean, select panel sample |
| Afternoon (3h) | Steps 3–5: Panel transformations (between, within, TWFE, FD), variance decomposition |
| Evening (2h) | Steps 6–7: Descriptive statistics tables, distribution plots, correlation matrices |

### Day 2 — Estimations + Report

| Time block | Tasks |
|---|---|
| Morning (3h) | Step 8: Run all panel regressions (Between, FE, RE/Mundlak, TWFE, FD) |
| Afternoon (3h) | Step 9: Optional Anderson-Hsiao, heterogeneity tables, bivariate graphs |
| Evening (2h) | Step 10: Write report, fill tables, compile PDF |

---

## Step-by-Step Plan

---

### Step 0 — Environment Setup
- [ ] Install required Python packages: `pandas`, `numpy`, `matplotlib`, `seaborn`, `scipy`, `statsmodels`, `linearmodels`
- [ ] Download dataset from: https://data.mendeley.com/datasets/xb2m4m8h24/1
- [ ] Place raw data in `data/raw/`

---

### Step 1 — Understand the Paper (Section 2 of report)
- [ ] Read paper abstract, introduction, and data section
- [ ] Identify exact variable names in the dataset
- [ ] Record: Y, X, controls, N countries, T years, panel type
- [ ] Fill Table 1 (key correlation) and Table 3 (data characteristics)

---

### Step 2 — Load and Inspect Raw Data (`01_load_explore_data.py`)
- [ ] Load Excel/CSV file with `pandas`
- [ ] Print shape, column names, dtypes
- [ ] Identify the country identifier and time identifier columns
- [ ] Rename to standard names: `country`, `year`, `Y`, `X`, controls
- [ ] Check for duplicates (country × year)
- [ ] Report: N countries, T years, NT total observations

---

### Step 3 — Clean and Select Panel Sample (`02_clean_panel_sample.py`)
- [ ] Drop observations where Y is missing
- [ ] **Panel sample selection rule**: keep only countries with **at least 3 consecutive observations** of Y
  - Sort by country then year
  - Detect consecutive runs; mark countries that never reach a run of 3+
  - Replace isolated Y values (runs < 3) with NaN
- [ ] Build and export **sample selection table** (Table 3 from requirements)
- [ ] Check whether excluded countries are systematically different (small/poor)
- [ ] Save cleaned panel to `data/processed/panel_clean.csv`

---

### Step 4 — Panel Structure Description (`02_clean_panel_sample.py` continued)
- [ ] Table: number of observations per year (attrition check)
- [ ] Table: number of individuals by number of time observations (T distribution)
- [ ] Identify countries with holes (discontinuous observations)
- [ ] Classify panel as balanced or unbalanced

---

### Step 5 — Panel Variable Classification (`03_panel_transformations.py`)
For **every variable** compute:
- [ ] **Between transformation**: $\bar{x}_{i\cdot}$ — mean over time for each country
- [ ] **One-way within transformation**: $x_{it} - \bar{x}_{i\cdot}$
- [ ] Compute overall variance, between variance, within variance
- [ ] Compute `% within variance / total variance`
- [ ] Sort and classify into:
  - 100% within: common time series (individual-invariant)
  - 0% within: time-invariant variables
  - Mixed: 0% < within% < 100%
- [ ] Fill Table 4 (variable count by category) and Table 5 (time-varying variables sorted by within%)

---

### Step 6 — Between + Within Distributions (`04_descriptive_statistics.py`)

For **Y and X only**:
- [ ] Plot histogram + KDE + fitted normal — between transformation $\bar{x}_{i\cdot}$
- [ ] Plot histogram + KDE + fitted normal — within transformation $x_{it} - \bar{x}_{i\cdot}$
- [ ] Report skewness, kurtosis, number of outliers
- [ ] Bivariate scatter: within-Y vs within-X with regression line + marginal KDEs
- [ ] Bivariate scatter: between-Y vs between-X with regression line + marginal KDEs

---

### Step 7 — First Differences and TWFE Transformations (`03_panel_transformations.py`)

**First Differences:**
- [ ] Sort data by `country` then `year`
- [ ] Compute $\Delta x_{it} = x_{it} - x_{i,t-1}$, setting to NaN at every change of individual
- [ ] Verify first 3×T+1 rows: NaN at individual breaks
- [ ] Plot FD distributions for ΔY and ΔX

**TWFE (Two-Way Fixed Effects):**
- [ ] Restrict to balanced subsample (countries available for the longest duration)
- [ ] Compute time means $\bar{x}_{\cdot t}$ and grand mean $\bar{x}_{\cdot\cdot}$
- [ ] Compute: $x_{it} - \bar{x}_{i\cdot} - \bar{x}_{\cdot t} + \bar{x}_{\cdot\cdot}$
- [ ] For unbalanced panel: use Wansbeek–Kapteijn (1989) method (regress within-Y on time dummies, collect residuals)
- [ ] Plot TWFE distributions

---

### Step 8 — Descriptive Statistics Tables (`04_descriptive_statistics.py`)

- [ ] **Table**: univariate stats for all 4 transformations: min, Q1, median, Q3, max, mean, std
  - Report standardized min/max: $(MIN - \mu)/\sigma$ and $(MAX - \mu)/\sigma$
- [ ] **Correlation matrices**:
  - Between-transformed variables
  - One-way within-transformed variables
  - TWFE-transformed variables
  - First-difference-transformed variables (include lag of FD)
- [ ] **Boxplots by country** for TWFE and FD (ordered by variance)
- [ ] **Bivariate correlation table** by country for TWFE (sorted by r)
- [ ] **Bivariate correlation table** by country for FD (sorted by r)
- [ ] Bivariate graphs: Y vs X for each transformation (linear + quadratic + LOWESS fit)

---

### Step 9 — Panel Regressions (`05_panel_estimations.py`)

All regressions use the cleaned panel sample. Report in a single comparison table.

| # | Estimator | Python implementation |
|---|---|---|
| 1 | **Between** | `linearmodels.BetweenOLS` |
| 2 | **One-way FE** | `linearmodels.PanelOLS(entity_effects=True)` |
| 3 | **Mundlak (RE)** | `linearmodels.RandomEffects` + group means of X as controls |
| 4 | **Two-way FE** | `linearmodels.PanelOLS(entity_effects=True, time_effects=True)` |
| 5 | **First Differences** | `linearmodels.FirstDifferenceOLS` |

For each regression:
- [ ] Report: coefficient on X, standard errors (clustered by country), t-stat, p-value
- [ ] Report: R², N, number of countries
- [ ] Comment: sign, magnitude, significance

---

### Step 10 — Optional: Anderson-Hsiao Dynamic Panel (`06_dynamic_panel.py`)

Condition: run only if FD autocorrelation of ΔY > 0.1

Model: $\Delta Y_{it} = \beta_y \Delta Y_{i,t-1} + \beta_1 \Delta X_{it} + \beta_2 \Delta X_{i,t-1} + \Delta Controls + \Delta\alpha_t + \Delta\varepsilon_{it}$

- [ ] Compute instruments: $Y_{i,t-2}$ and $X_{i,t-2}$
- [ ] Check instrument strength (correlation with endogenous variable, first-stage R²)
- [ ] IV estimation using `linearmodels.IV2SLS` or `statsmodels` IVREG
- [ ] Report first-stage regressions
- [ ] Compute impulse response function for 4 periods
- [ ] Compute long-run coefficient: $\beta_{LT} = (\beta_1 + \beta_2) / (1 - \beta_y)$

---

### Step 11 — Time-Invariant Variables (Optional, `05_panel_estimations.py`)

If any variable is time-invariant:
- [ ] Hausman-Taylor estimation (note: better implemented in Stata)
- [ ] Between regression of Z(i) on group means X(i.)
- [ ] Interaction shortcut: include Z(i) × X(it) in one-way FE regression

---

### Step 12 — Output Organization (`outputs/`)

Tables:
- [ ] `table1_key_correlation.csv`
- [ ] `table2_data_characteristics.csv`
- [ ] `table3_sample_selection.csv`
- [ ] `table4_variable_classification.csv`
- [ ] `table5_variance_decomposition.csv`
- [ ] `table6_descriptive_stats_all_transforms.csv`
- [ ] `table7_correlation_between.csv`
- [ ] `table8_correlation_within.csv`
- [ ] `table9_correlation_twfe.csv`
- [ ] `table10_correlation_fd.csv`
- [ ] `table11_heterogeneity_fd.csv`
- [ ] `table12_heterogeneity_twfe.csv`
- [ ] `table13_panel_regressions.csv`

Figures:
- [ ] `fig1_between_dist_Y_X.png`
- [ ] `fig2_within_dist_Y_X.png`
- [ ] `fig3_fd_dist_Y_X.png`
- [ ] `fig4_twfe_dist_Y_X.png`
- [ ] `fig5_bivariate_within.png`
- [ ] `fig6_bivariate_between.png`
- [ ] `fig7_bivariate_fd.png`
- [ ] `fig8_bivariate_twfe.png`
- [ ] `fig9_boxplots_twfe_by_country.png`
- [ ] `fig10_boxplots_fd_by_country.png`
- [ ] `fig11_obs_per_year.png`

---

## Recommended Folder Structure

```
Econometrics_project/
├── data/
│   ├── raw/                    ← downloaded Mendeley dataset (Excel/CSV)
│   └── processed/              ← cleaned panel CSV files
├── scripts/
│   ├── 01_load_explore_data.py ← load, inspect, rename variables
│   ├── 02_clean_panel_sample.py← consecutive obs rule, sample selection tables
│   ├── 03_panel_transformations.py ← between, within, TWFE, FD
│   ├── 04_descriptive_statistics.py← plots, tables, correlation matrices
│   ├── 05_panel_estimations.py ← all panel regressions comparison table
│   ├── 06_dynamic_panel.py     ← Anderson-Hsiao (optional)
│   └── main_workflow.py        ← runs all steps end-to-end
├── outputs/
│   ├── tables/                 ← CSV/Excel tables for report
│   ├── figures/                ← PNG/PDF plots
│   └── logs/                   ← print logs
├── report/
│   └── report.docx / report.tex
├── paper/
│   └── Mertzanis_2024.pdf
├── PROJECT_PLAN.md             ← this file
├── README.md
└── panel_replication_requirements.md
```

---

## Key Python Libraries

| Library | Use |
|---|---|
| `pandas` | Data manipulation, panel transformations |
| `numpy` | Numerical operations, variance decomposition |
| `matplotlib` + `seaborn` | All plots |
| `scipy.stats` | Normal fit, skewness, kurtosis |
| `statsmodels` | OLS, IV, unit root tests |
| `linearmodels` | BetweenOLS, PanelOLS, RandomEffects, FirstDifferenceOLS |

Install with: `pip install pandas numpy matplotlib seaborn scipy statsmodels linearmodels openpyxl`

---

## Variable Naming Convention (to update after data download)

| Standard name in code | Expected meaning |
|---|---|
| `country` | Country identifier (string) |
| `year` | Year (integer) |
| `Y` | Dependent variable: green bond issuance |
| `X` | Key explanatory: central bank policy indicator |
| `controls` | List of control variable column names |

---

## Quick-Start Checklist

- [ ] Download data from https://data.mendeley.com/datasets/xb2m4m8h24/1
- [ ] Place in `data/raw/`
- [ ] Open `scripts/main_workflow.py`
- [ ] Update `RAW_FILE`, `ID_COL`, `TIME_COL`, `Y_COL`, `X_COL`, `CONTROL_COLS` at the top
- [ ] Run `python scripts/main_workflow.py`
- [ ] Outputs appear in `outputs/tables/` and `outputs/figures/`
