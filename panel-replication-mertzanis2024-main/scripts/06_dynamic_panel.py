# =============================================================================
# 06_dynamic_panel.py
# Step 6 (Optional) — Anderson-Hsiao (1981) dynamic panel estimator.
#   Condition: run only if autocorrelation of ΔY > 0.1
#   Model: ΔY_it = β_y ΔY_{i,t-1} + β1 ΔX_it + β2 ΔX_{i,t-1} + Δcontrols
#                + Δα_t + Δε_it
#   Instruments: Y_{i,t-2} and X_{i,t-2}
# =============================================================================
# Run:  python scripts/06_dynamic_panel.py
# Input:  data/processed/panel_clean.csv
# Output: outputs/tables/t06a_dynamic_univariate.csv
#         outputs/tables/t06b_dynamic_corr.csv
#         outputs/tables/t06c_dynamic_ols.csv
#         outputs/tables/t06d_dynamic_iv.csv
#         outputs/figures/fig14_impulse_response.png
#         outputs/logs/06_dynamic_panel.txt
# =============================================================================

import os
import sys
import warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (PROC_DIR, TABLE_DIR, FIG_DIR, LOG_DIR,
                    ID_COL, TIME_COL, Y_COL, X_COL, CONTROL_COLS,
                    FIG_DPI, FIG_FORMAT)

warnings.filterwarnings("ignore")

# Try optional imports
try:
    from linearmodels.iv import IV2SLS
    HAS_IV2SLS = True
except ImportError:
    HAS_IV2SLS = False
    print("[WARNING] linearmodels.iv not found. IV estimation will use statsmodels.")


def log(msg, f=None):
    print(msg)
    if f:
        f.write(msg + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# Build dynamic panel dataset
# ─────────────────────────────────────────────────────────────────────────────

def build_dynamic_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create FD variables and their lags/level instruments.
    Returns a dataset with:
      dY   = ΔY_it
      dY1  = ΔY_{i,t-1}   (lag of dY)
      dX   = ΔX_it
      dX1  = ΔX_{i,t-1}
      Y_l2 = Y_{i,t-2}    (instrument)
      X_l2 = X_{i,t-2}    (instrument)
    """
    d = df[[ID_COL, TIME_COL, Y_COL, X_COL] + CONTROL_COLS].copy()
    d = d[[c for c in d.columns if c in df.columns]]
    d.sort_values([ID_COL, TIME_COL], inplace=True)

    # First differences (NaN at individual breaks)
    d["dY"]  = d.groupby(ID_COL)[Y_COL].diff()
    d["dX"]  = d.groupby(ID_COL)[X_COL].diff()
    for c in [c for c in CONTROL_COLS if c in d.columns]:
        d[f"d{c}"] = d.groupby(ID_COL)[c].diff()

    # Lags of FD
    d["dY1"] = d.groupby(ID_COL)["dY"].shift(1)
    d["dX1"] = d.groupby(ID_COL)["dX"].shift(1)

    # Level instruments
    d["Y_l2"] = d.groupby(ID_COL)[Y_COL].shift(2)
    d["X_l2"] = d.groupby(ID_COL)[X_COL].shift(2)

    # Time dummies (for Δα_t)
    time_dummies = pd.get_dummies(d[TIME_COL], prefix="td", drop_first=True)
    d = pd.concat([d, time_dummies], axis=1)

    return d


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def run_dynamic_panel():
    os.makedirs(TABLE_DIR, exist_ok=True)
    os.makedirs(FIG_DIR,   exist_ok=True)
    os.makedirs(LOG_DIR,   exist_ok=True)

    df = pd.read_csv(os.path.join(PROC_DIR, "panel_clean.csv"))
    df[TIME_COL] = pd.to_numeric(df[TIME_COL], errors="coerce")
    df.sort_values([ID_COL, TIME_COL], inplace=True)

    f = open(os.path.join(LOG_DIR, "06_dynamic_panel.txt"), "w")
    log("=" * 70, f)
    log("STEP 6 — OPTIONAL: ANDERSON-HSIAO DYNAMIC PANEL", f)
    log("=" * 70, f)

    controls = [c for c in CONTROL_COLS if c in df.columns]

    # ── Check autocorrelation of ΔY ───────────────────────────────────────────
    df["dY"] = df.groupby(ID_COL)[Y_COL].diff()
    df["dY1"] = df.groupby(ID_COL)["dY"].shift(1)
    acf_mask = df[["dY", "dY1"]].notna().all(axis=1)
    if acf_mask.sum() > 10:
        r_ac, p_ac = stats.pearsonr(df.loc[acf_mask, "dY"],
                                     df.loc[acf_mask, "dY1"])
        log(f"\nAutocorrelation r(ΔY_t, ΔY_{{t-1}}) = {r_ac:.4f}  (p = {p_ac:.4f})",
            f)
        if abs(r_ac) < 0.1:
            log("→ Autocorrelation < 0.1. Dynamic panel estimator optional.", f)
        else:
            log("→ Autocorrelation ≥ 0.1. Running Anderson-Hsiao estimator.", f)
    else:
        log("\nInsufficient observations to test autocorrelation.", f)

    # ── Build dynamic dataset ─────────────────────────────────────────────────
    dyn = build_dynamic_dataset(df.drop(columns=["dY", "dY1"], errors="ignore"))
    time_dummy_cols = [c for c in dyn.columns if c.startswith("td_")]

    # ── 1. Univariate stats for dynamic variables ─────────────────────────────
    dyn_vars = ["dY", "dY1", "dX", "dX1", "Y_l2", "X_l2"]
    dyn_vars = [v for v in dyn_vars if v in dyn.columns]
    stat_rows = []
    for v in dyn_vars:
        s = dyn[v].dropna()
        if len(s) == 0:
            continue
        mu, sigma = s.mean(), s.std()
        stat_rows.append({
            "variable": v, "N": len(s),
            "mean": round(mu, 5), "median": round(s.median(), 5),
            "std": round(sigma, 5),
            "skewness": round(stats.skew(s), 4),
            "kurtosis": round(stats.kurtosis(s), 4),
            "min": round(s.min(), 5), "max": round(s.max(), 5),
        })
    stat_df = pd.DataFrame(stat_rows)
    stat_df.to_csv(os.path.join(TABLE_DIR, "t06a_dynamic_univariate.csv"), index=False)
    log("\n--- 1. Univariate stats ---", f)
    log(stat_df.to_string(index=False), f)

    # ── 2. Correlation matrix ─────────────────────────────────────────────────
    corr_vars = dyn_vars
    corr_data = dyn[corr_vars].dropna()
    if len(corr_data) > 10:
        corr_mat = corr_data.corr().round(4)
        corr_mat.to_csv(os.path.join(TABLE_DIR, "t06b_dynamic_corr.csv"))
        log("\n--- 2. Correlation matrix ---", f)
        log(corr_mat.to_string(), f)
        # Check instrument strength: r(dY1, Y_l2) and r(dX, X_l2)
        if "Y_l2" in corr_mat.columns and "dY1" in corr_mat.index:
            log(f"\n  Instrument strength r(dY1, Y_l2) = "
                f"{corr_mat.loc['dY1', 'Y_l2']:.4f}", f)
        if "X_l2" in corr_mat.columns and "dX" in corr_mat.index:
            log(f"  Instrument strength r(dX,  X_l2) = "
                f"{corr_mat.loc['dX', 'X_l2']:.4f}", f)

    # ── 3. OLS (FD with lag of FD dep variable) ───────────────────────────────
    log("\n--- 3. OLS (Anderson-Hsiao step 1, no IV) ---", f)
    ols_vars  = ["dY1", "dX", "dX1"] + [f"d{c}" for c in controls
                                          if f"d{c}" in dyn.columns]
    ols_vars += time_dummy_cols
    ols_vars  = [v for v in ols_vars if v in dyn.columns]
    ols_data  = dyn[["dY"] + ols_vars].dropna()

    if len(ols_data) > len(ols_vars) + 5:
        Y_ols = ols_data["dY"].astype(float)
        X_ols = sm.add_constant(ols_data[ols_vars].astype(float))
        res_ols = sm.OLS(Y_ols, X_ols).fit(cov_type="HC1")
        log(str(res_ols.summary()), f)
        n_ids_ols = dyn.loc[ols_data.index, ID_COL].nunique()
        log(f"\n  N obs = {len(ols_data)}, N countries = {n_ids_ols}", f)

        ols_summary = res_ols.summary2().tables[1]
        ols_summary.to_csv(os.path.join(TABLE_DIR, "t06c_dynamic_ols.csv"))

        beta_y_ols  = res_ols.params.get("dY1", np.nan)
        beta1_ols   = res_ols.params.get("dX",  np.nan)
        beta2_ols   = res_ols.params.get("dX1", np.nan)
    else:
        log("  [SKIP] Not enough observations for OLS.", f)
        beta_y_ols  = np.nan
        beta1_ols   = np.nan
        beta2_ols   = np.nan

    # ── 4. IV (Anderson-Hsiao) ────────────────────────────────────────────────
    log("\n--- 4. IV — Anderson-Hsiao (instruments: Y_l2, X_l2) ---", f)
    endog_vars   = ["dY1", "dX1"]   # endogenous regressors
    instruments  = ["Y_l2", "X_l2"]
    exog_iv_vars = ["dX"] + [f"d{c}" for c in controls
                              if f"d{c}" in dyn.columns] + time_dummy_cols
    exog_iv_vars = [v for v in exog_iv_vars if v in dyn.columns]

    all_needed = (["dY"] + endog_vars + instruments + exog_iv_vars)
    iv_data    = dyn[[c for c in all_needed if c in dyn.columns]].dropna()

    if len(iv_data) > len(endog_vars) + len(exog_iv_vars) + 5:
        Y_iv    = iv_data["dY"]
        endog_v = iv_data[[v for v in endog_vars  if v in iv_data.columns]]
        instrum = iv_data[[v for v in instruments if v in iv_data.columns]]
        exog_v  = sm.add_constant(
                    iv_data[[v for v in exog_iv_vars if v in iv_data.columns]])

        use_iv2sls = HAS_IV2SLS
        if use_iv2sls:
            from linearmodels.iv import IV2SLS as IV2SLS_lm
            try:
                # Combine exog + endog for linearmodels interface
                res_iv = IV2SLS_lm(
                    dependent=Y_iv,
                    exog=exog_v,
                    endog=endog_v,
                    instruments=instrum
                ).fit(cov_type="robust")
            except Exception as e:
                log(f"  [ERROR IV2SLS] {e}. Falling back to manual 2SLS.", f)
                use_iv2sls = False
        if use_iv2sls:
            log(str(res_iv.summary), f)
            iv_params = res_iv.params
            beta_y_iv  = float(iv_params.get("dY1", np.nan))
            beta1_iv   = float(iv_params.get("dX",  np.nan))
            beta2_iv   = float(iv_params.get("dX1", np.nan))
            res_iv.params.to_csv(os.path.join(TABLE_DIR, "t06d_dynamic_iv.csv"))
        else:
            # Fallback: 2SLS via manual first-stage OLS
            log("  Using manual 2SLS (linearmodels not available).", f)

            # First stage for dY1
            X_fs1 = sm.add_constant(
                pd.concat([instrum, exog_v.drop("const", axis=1, errors="ignore")],
                          axis=1).astype(float))
            fs1 = sm.OLS(endog_v.iloc[:, 0].astype(float), X_fs1).fit()
            log(f"\n  First-stage R² (dY1): {fs1.rsquared:.4f}", f)
            if fs1.rsquared < 0.1:
                log("  [WARNING] Weak instrument: first-stage R² < 0.10", f)

            # First stage for dX1
            fs2 = sm.OLS(endog_v.iloc[:, 1], X_fs1).fit() \
                  if endog_v.shape[1] > 1 else None
            if fs2:
                log(f"  First-stage R² (dX1): {fs2.rsquared:.4f}", f)

            # Second stage
            endog_hat = pd.DataFrame({
                endog_v.columns[0]: fs1.fittedvalues,
            })
            if fs2 is not None and endog_v.shape[1] > 1:
                endog_hat[endog_v.columns[1]] = fs2.fittedvalues

            X_2nd = sm.add_constant(
                pd.concat([exog_v.drop("const", axis=1, errors="ignore"),
                           endog_hat], axis=1).astype(float))
            res_2nd = sm.OLS(Y_iv.astype(float), X_2nd).fit(cov_type="HC1")
            log(str(res_2nd.summary()), f)
            beta_y_iv  = res_2nd.params.get("dY1", np.nan)
            beta1_iv   = res_2nd.params.get("dX",  np.nan)
            beta2_iv   = res_2nd.params.get("dX1", np.nan)
            res_2nd.summary2().tables[1].to_csv(
                os.path.join(TABLE_DIR, "t06d_dynamic_iv.csv"))

        # ── 5. Impulse Response Function ──────────────────────────────────────
        log("\n--- 5. Impulse Response Function (IV estimates) ---", f)
        beta_y = beta_y_iv
        beta1  = beta1_iv
        beta2  = beta2_iv

        if not any(np.isnan([beta_y, beta1, beta2])):
            irf = [
                beta1,                                    # t=1
                beta_y * beta1 + beta2,                  # t=2
                beta_y**2 * beta1 + beta_y * beta2,      # t=3
                beta_y**3 * beta1 + beta_y**2 * beta2,   # t=4
            ]
            log(f"\n  β_y = {beta_y:.4f},  β1 = {beta1:.4f},  β2 = {beta2:.4f}", f)
            log(f"  IRF t=1 : {irf[0]:.5f}", f)
            log(f"  IRF t=2 : {irf[1]:.5f}", f)
            log(f"  IRF t=3 : {irf[2]:.5f}", f)
            log(f"  IRF t=4 : {irf[3]:.5f}", f)

            if abs(beta_y) < 1:
                lr_coef = (beta1 + beta2) / (1 - beta_y)
                log(f"\n  Long-run coefficient: (β1+β2)/(1-β_y) = {lr_coef:.5f}", f)
            else:
                log(f"\n  [WARNING] β_y = {beta_y:.4f} ≥ 1: IRF is explosive. "
                    "Long-run coefficient formula is not valid.", f)

            # Plot IRF
            fig, ax = plt.subplots(figsize=(6, 4))
            periods = [1, 2, 3, 4]
            ax.bar(periods, irf, color="#4C8BE2", edgecolor="white")
            ax.axhline(0, color="black", lw=0.8, linestyle="--")
            ax.set_xlabel("Period")
            ax.set_ylabel("Effect on Y")
            ax.set_title("Impulse Response: 1-unit increase in X → Y\n"
                         f"(Anderson-Hsiao IV,  β_y={beta_y:.3f})")
            ax.set_xticks(periods)
            plt.tight_layout()
            fig_path = os.path.join(FIG_DIR, f"fig14_impulse_response.{FIG_FORMAT}")
            plt.savefig(fig_path, dpi=FIG_DPI)
            plt.close()
            log(f"\n[SAVED] {fig_path}", f)

        # Compare OLS vs IV
        log("\n--- OLS vs IV comparison ---", f)
        comp = pd.DataFrame({
            "parameter": ["beta_y (dY1)", "beta1 (dX)", "beta2 (dX1)"],
            "OLS"      : [beta_y_ols, beta1_ols, beta2_ols],
            "IV"       : [beta_y_iv,  beta1_iv,  beta2_iv],
        })
        log(comp.to_string(index=False), f)

    else:
        log("  [SKIP] Not enough observations for IV estimation.", f)

    f.close()
    print(f"\n[OK] Step 6 complete. Log: outputs/logs/06_dynamic_panel.txt")


if __name__ == "__main__":
    run_dynamic_panel()
