# Panel Data Replication Project

**Paper:** Mertzanis, C. (2024). *Central bank policies and green bond issuance on a global scale.* Energy Economics, 133, 107541.

**Data:** Mendeley Data, doi: [10.17632/xb2m4m8h24.1](https://data.mendeley.com/datasets/xb2m4m8h24/1)

---

## Quick Start

### 1. Install dependencies
```bash
pip install pandas numpy matplotlib seaborn scipy statsmodels linearmodels openpyxl
```

### 2. Download data
Go to https://data.mendeley.com/datasets/xb2m4m8h24/1  
Download the Excel/CSV file → place it in `data/raw/`

### 3. Configure variable names
Open `scripts/config.py` and update:
```python
RAW_FILE     = "Central_bank_policies_green_bonds.xlsx"  # ← your filename
ID_COL       = "country"    # ← country identifier column
TIME_COL     = "year"       # ← year column
Y_COL        = "gb_issuance"  # ← dependent variable
X_COL        = "cbp_index"    # ← key explanatory variable
CONTROL_COLS = [...]          # ← list of control variable names
```

### 4. Run
```bash
python scripts/main_workflow.py
```

All outputs appear in `outputs/tables/` and `outputs/figures/`.

---

## Folder Structure

```
Econometrics_project/
├── data/
│   ├── raw/                     ← downloaded Mendeley dataset
│   └── processed/               ← cleaned and transformed CSVs
├── scripts/
│   ├── config.py                ← EDIT THIS: paths and variable names
│   ├── 01_load_explore_data.py  ← load, inspect, rename
│   ├── 02_clean_panel_sample.py ← consecutive-obs rule, sample selection
│   ├── 03_panel_transformations.py ← between, within, TWFE, FD
│   ├── 04_descriptive_statistics.py ← plots, tables, correlation matrices
│   ├── 05_panel_estimations.py  ← Between, FE, RE/Mundlak, TWFE, FD
│   ├── 06_dynamic_panel.py      ← Anderson-Hsiao IV (optional)
│   └── main_workflow.py         ← runs everything end-to-end
├── outputs/
│   ├── tables/                  ← CSV tables for the report
│   ├── figures/                 ← PNG plots
│   └── logs/                    ← detailed run logs
├── report/                      ← Word/LaTeX report
├── paper/                       ← Mertzanis_2024.pdf
├── PROJECT_PLAN.md              ← step-by-step plan
├── README.md                    ← this file
└── panel_replication_requirements.md
```

---

## Script Descriptions

| Script | What it does |
|---|---|
| `config.py` | Central config: paths, variable names, plot settings |
| `01_load_explore_data.py` | Load raw file, print column names/dtypes/missing, save `panel_raw.csv` |
| `02_clean_panel_sample.py` | Apply ≥3 consecutive-obs rule, attrition table, T distribution |
| `03_panel_transformations.py` | Between, one-way within, first diff (with NaN at breaks), TWFE (balanced or Wansbeek-Kapteijn), variance decomposition |
| `04_descriptive_statistics.py` | Histogram+KDE+normal plots, bivariate scatters, correlation heatmaps, boxplots by country, heterogeneity tables |
| `05_panel_estimations.py` | Between, FE (1-way), Mundlak RE, TWFE (2-way), First Differences — single comparison table |
| `06_dynamic_panel.py` | Anderson-Hsiao IV, first-stage R², impulse response, long-run coefficient |
| `main_workflow.py` | Runs all scripts sequentially with error handling and a summary |

---

## Key Outputs

### Tables (`outputs/tables/`)

| File | Content |
|---|---|
| `t01b_missing_values.csv` | Missing % by variable |
| `t02a_sample_selection.csv` | Included / excluded countries |
| `t02b_obs_per_year.csv` | N countries per year (attrition) |
| `t02c_T_distribution.csv` | Distribution of T across individuals |
| `t03a_variance_decomp.csv` | Between/within variance decomposition (all vars) |
| `t03b_variable_classification.csv` | Time-invariant / individual-invariant / mixed |
| `t04a_univariate_stats.csv` | Univariate stats (mean, median, std, skew, kurt) for all 4 transformations |
| `t04b_corr_bet/wi/twfe/fd.csv` | Correlation matrices for each transformation |
| `t04c_heterogeneity_twfe/fd.csv` | r(Y,X) and β by country |
| `t05_panel_regressions.csv` | Comparison: Between, FE, Mundlak, TWFE, FD |
| `t06d_dynamic_iv.csv` | Anderson-Hsiao IV results |

### Figures (`outputs/figures/`)

| File | Content |
|---|---|
| `fig01_obs_per_year.png` | Bar chart of N per year |
| `fig02_Y/X_bet/wi/fd/twfe_dist.png` | Histogram + KDE + normal for each transformation |
| `fig03_bivariate_*.png` | Y vs X scatter with marginal KDE |
| `fig04_multfit_*.png` | Y vs X with linear, quadratic, LOWESS fits |
| `fig05_boxplot_twfe/fd_Y.png` | Boxplots by country |
| `fig06_corr_*.png` | Correlation heatmaps |
| `fig14_impulse_response.png` | IRF from Anderson-Hsiao |

---

## Econometric Models

$$\text{Between: } \bar{Y}_i = \beta \bar{X}_i + \bar{\varepsilon}_i$$

$$\text{One-way FE: } (Y_{it} - \bar{Y}_i) = \beta (X_{it} - \bar{X}_i) + (u_{it} - \bar{u}_i)$$

$$\text{TWFE: } (Y_{it} - \bar{Y}_i - \bar{Y}_t + \bar{Y}) = \beta(\ldots) + \varepsilon$$

$$\text{First Diff: } \Delta Y_{it} = \beta \Delta X_{it} + \Delta u_{it}$$

$$\text{Anderson-Hsiao: } \Delta Y_{it} = \beta_y \Delta Y_{i,t-1} + \beta_1 \Delta X_{it} + \beta_2 \Delta X_{i,t-1} + \ldots$$

$$\text{Long-run: } \beta_{LT} = \frac{\beta_1 + \beta_2}{1 - \beta_y}$$
