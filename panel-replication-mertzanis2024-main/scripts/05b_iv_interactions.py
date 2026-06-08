# =============================================================================
# 05b_iv_interactions.py  —  Fixed version
# Step 5b — IV/2SLS (paper Table 6) and Interaction terms (paper Table 9).
#
# TABLE 6 — IV regressions
#   cbmnd, cbenf, cbsys are time-invariant → IV must exploit between-country
#   (cross-sectional) variation.  Instruments (hierarchy, openness, purity) are
#   also time-invariant → the between estimator (country means) is the correct
#   framework, giving N = number of countries in the cross-section.
#
#   We use IV on the between (country-mean) regression:
#     Y_bar_i = β·X_bar_i + ε_bar_i
#   where X_bar includes the CB variable instrumented by cultural values.
#   This matches the paper's ivreg2 approach which, given time-invariant
#   regressors and instruments, reduces to a cross-sectional 2SLS.
#
# TABLE 9 — Interaction terms (pooled OLS, cluster by country)
#   bndgrn ~ $xvar + interact_var + cbenf×interact_var  (no entity FE,
#   because cbenf is time-invariant and would be absorbed)
#   Cluster-robust SE by country.
#
# Stata reference (Table 6):
#   ivreg2 bndgrn cbenf cbsys infl rating fie gdpg dum9 dum12
#          (cbmnd = hierarchy purity), ffirst cluster(country1)
# Stata reference (Table 9):
#   reg bndgrn $xvar prodstr c.cbenf#c.prodstr, cluster(country1)
# =============================================================================

import os, sys, warnings
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import statsmodels.api as sm
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (PROC_DIR, TABLE_DIR, FIG_DIR, LOG_DIR,
                    ID_COL, TIME_COL, CLUST_COL,
                    Y_COL, CB_COLS, CONTROL_COLS, XVAR_COLS,
                    INTERACT_VARS, FIG_DPI, FIG_FORMAT)

warnings.filterwarnings("ignore")
os.makedirs(TABLE_DIR, exist_ok=True)
os.makedirs(FIG_DIR,   exist_ok=True)
os.makedirs(LOG_DIR,   exist_ok=True)


def log(msg, f=None):
    print(msg)
    if f:
        f.write(msg + "\n")


def stars(p):
    if pd.isna(p): return ""
    if p < 0.01:   return "***"
    if p < 0.05:   return "**"
    if p < 0.10:   return "*"
    return ""


# =============================================================================
# Between-IV helper: 2SLS on country means
# =============================================================================

def between_iv2sls(df, y_col, endog_col, exog_cols, instr_cols, label="", f=None):
    """
    Two-stage least squares on country means (between estimator).
    - endog_col : the one endogenous CB variable being instrumented
    - exog_cols : remaining regressors (other CB vars + controls, all time-invariant)
    - instr_cols: excluded instruments (cultural values)

    Returns (label, fs_res, ss_res, n_countries, fs_fstat, fs_r2)
    """
    # Collapse to country means
    all_vars = [y_col, endog_col] + exog_cols + instr_cols
    avail    = [v for v in all_vars if v in df.columns]
    means    = df[avail + [ID_COL]].groupby(ID_COL).mean()
    means    = means.dropna(subset=[y_col, endog_col] +
                            [v for v in exog_cols + instr_cols if v in means.columns])

    if len(means) < 5:
        log(f"  [SKIP] {label}: too few observations ({len(means)})", f)
        return label, None, None, len(means), np.nan, np.nan

    # First stage: endog ~ exog + instruments
    exog_avail  = [v for v in exog_cols  if v in means.columns]
    instr_avail = [v for v in instr_cols if v in means.columns]

    X_fs = sm.add_constant(means[exog_avail + instr_avail].astype(float))
    y_fs = means[endog_col].astype(float)
    fs   = sm.OLS(y_fs, X_fs).fit(cov_type="HC1")

    fs_r2    = fs.rsquared
    # Partial F on excluded instruments
    k_instr  = len(instr_avail)
    k_total  = X_fs.shape[1]
    n_cs     = len(means)
    # Restricted model (without instruments)
    X_restr  = sm.add_constant(means[exog_avail].astype(float))
    fs_restr = sm.OLS(y_fs, X_restr).fit()
    ess_unr  = fs.ssr
    ess_r    = fs_restr.ssr
    if ess_unr > 0 and k_instr > 0:
        fs_fstat = ((ess_r - ess_unr) / k_instr) / (ess_unr / (n_cs - k_total))
    else:
        fs_fstat = np.nan

    log(f"  {label}", f)
    log(f"    First-stage R² = {fs_r2:.4f}  |  partial F = {fs_fstat:.3f}  "
        f"|  N = {n_cs} countries", f)
    for inst in instr_avail:
        p = fs.pvalues[inst]
        log(f"      instrument {inst}: coef={fs.params[inst]:.4f} "
            f"({fs.bse[inst]:.4f}){stars(p)}", f)

    # Fitted values from first stage
    means["_yhat_endog"] = fs.fittedvalues

    # Second stage: y ~ exog + fitted_endog
    X_ss = sm.add_constant(
        means[exog_avail + ["_yhat_endog"]].astype(float))
    X_ss = X_ss.rename(columns={"_yhat_endog": endog_col})
    y_ss = means[y_col].astype(float)
    ss   = sm.OLS(y_ss, X_ss).fit(cov_type="HC1")

    log(f"    Second-stage results:", f)
    for v in [endog_col] + exog_avail[:3]:
        if v in ss.params.index:
            log(f"      {v}: {ss.params[v]:.4f} ({ss.bse[v]:.4f})"
                f"{stars(ss.pvalues[v])}", f)

    return label, fs, ss, n_cs, fs_fstat, fs_r2


# =============================================================================
# TABLE 6 — Between IV/2SLS
# =============================================================================

def run_table6(df, f):
    log("\n" + "=" * 70, f)
    log("PAPER TABLE 6 — IV / 2SLS  (between / cross-sectional)", f)
    log("Instruments: cultural values (time-invariant, vary only across countries)", f)
    log("Method: 2SLS on country means — correct for time-invariant endogenous vars", f)
    log("=" * 70, f)

    instr_all   = ["hierarchy", "openness", "purity"]
    instr_avail = [v for v in instr_all if v in df.columns]
    if len(instr_avail) < 2:
        log(f"[SKIP] Instruments not found.", f)
        return

    base_controls = [v for v in CONTROL_COLS if v in df.columns]

    specs = [
        ("(1) IV: cbmnd ~ hierarchy+purity",
         "cbmnd", ["cbenf", "cbsys"] + base_controls,
         ["hierarchy", "purity"]),
        ("(2) IV: cbenf ~ hierarchy+openness",
         "cbenf", ["cbmnd", "cbsys"] + base_controls,
         ["hierarchy", "openness"]),
        ("(3) IV: cbsys ~ hierarchy+openness",
         "cbsys", ["cbmnd", "cbenf"] + base_controls,
         ["hierarchy", "openness"]),
    ]

    summary_rows = []
    all_results  = []

    for spec_label, endog, exog, instruments in specs:
        inst_ok = [v for v in instruments if v in instr_avail]
        exog_ok = [v for v in exog if v in df.columns]
        label, fs, ss, n_cs, fs_f, fs_r2 = between_iv2sls(
            df, Y_COL, endog, exog_ok, inst_ok, label=spec_label, f=f)
        all_results.append((label, fs, ss, n_cs, fs_f, fs_r2))
        if ss is not None:
            row = {"spec": label, "N_countries": n_cs,
                   "fs_R2": round(fs_r2, 4), "fs_Fstat": round(fs_f, 3)}
            for v in CB_COLS:
                if v in ss.params.index:
                    row[f"coef_{v}"]  = round(float(ss.params[v]), 4)
                    row[f"se_{v}"]    = round(float(ss.bse[v]), 4)
                    row[f"stars_{v}"] = stars(float(ss.pvalues[v]))
            summary_rows.append(row)

    if summary_rows:
        summary = pd.DataFrame(summary_rows)
        summary.to_csv(os.path.join(TABLE_DIR, "t05b_table6_iv.csv"), index=False)
        log("\n--- Table 6 summary ---", f)
        log(summary.to_string(index=False), f)

    log("\nWeak instrument rule of thumb: F-stat > 10 is adequate.", f)
    return all_results


# =============================================================================
# TABLE 9 — Interaction terms
# (pooled OLS without entity FE — cbenf is time-invariant)
# =============================================================================

def run_table9(df, f):
    log("\n" + "=" * 70, f)
    log("PAPER TABLE 9 — INTERACTION TERMS", f)
    log("interaction = cbenf × {prodstr, bigtech, ngain}", f)
    log("Estimator: pooled OLS with cluster-robust SE (no entity FE,", f)
    log("           since cbenf is time-invariant and would be absorbed)", f)
    log("=" * 70, f)

    df = df.copy()
    df[CLUST_COL] = pd.factorize(df[ID_COL])[0] + 1

    x_base = [v for v in XVAR_COLS if v in df.columns]
    summary_rows = []

    for ivar in INTERACT_VARS:
        if ivar not in df.columns:
            log(f"  [SKIP] {ivar} not in data", f)
            continue

        interact_col = f"cbenf_x_{ivar}"
        df[interact_col] = df["cbenf"] * df[ivar]

        x_cols = x_base + [ivar, interact_col]
        x_cols = [v for v in x_cols if v in df.columns]
        needed = [Y_COL] + x_cols + [CLUST_COL, ID_COL, TIME_COL]
        sub    = df[needed].dropna(subset=[Y_COL] + x_cols)

        if len(sub) < 10:
            log(f"  [SKIP] cbenf×{ivar}: too few obs ({len(sub)})", f)
            continue

        X      = sm.add_constant(sub[x_cols].astype(float), has_constant="add")
        Y      = sub[Y_COL].astype(float)
        groups = sub[CLUST_COL].astype(int)

        res = sm.OLS(Y, X).fit(cov_type="cluster",
                               cov_kwds={"groups": groups}, use_t=True)

        log(f"\n  [cbenf × {ivar}] N={len(sub)}, N_countries={sub[ID_COL].nunique()}", f)
        for v in x_base[:6] + [ivar, interact_col]:
            if v in res.params.index:
                log(f"    {v:25s}  {res.params[v]:9.4f}  ({res.bse[v]:.4f})"
                    f"{stars(res.pvalues[v])}", f)

        row = {
            "spec":          f"cbenf × {ivar}",
            "N_obs":         len(sub),
            "N_ids":         sub[ID_COL].nunique(),
            "coef_cbenf":    round(float(res.params.get("cbenf",  np.nan)), 4),
            "coef_ivar":     round(float(res.params.get(ivar,     np.nan)), 4),
            "coef_interact": round(float(res.params.get(interact_col, np.nan)), 4),
            "se_interact":   round(float(res.bse.get(interact_col,    np.nan)), 4),
            "p_interact":    round(float(res.pvalues.get(interact_col,np.nan)), 4),
            "stars_interact":stars(res.pvalues.get(interact_col, np.nan)),
            "R2":            round(float(res.rsquared), 4),
        }
        summary_rows.append(row)

        # Marginal effect plot: ∂Y/∂cbenf = coef_cbenf + coef_interact * ivar
        ivar_range  = np.linspace(sub[ivar].min(), sub[ivar].max(), 200)
        mfx         = res.params.get("cbenf", 0) + \
                      res.params.get(interact_col, 0) * ivar_range
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot(ivar_range, mfx, color="#1f497d", lw=2)
        ax.axhline(0, color="grey", lw=0.8, ls="--")
        ax.set_xlabel(ivar)
        ax.set_ylabel("∂ green bond issuance / ∂ cbenf")
        ax.set_title(f"Marginal effect of CB enforcement\nas a function of {ivar}")
        fig.tight_layout()
        outpath = os.path.join(FIG_DIR, f"fig15_mfx_cbenf_{ivar}.{FIG_FORMAT}")
        fig.savefig(outpath, dpi=FIG_DPI)
        plt.close(fig)
        log(f"  [SAVED] {outpath}", f)

    if summary_rows:
        tbl = pd.DataFrame(summary_rows)
        tbl.to_csv(os.path.join(TABLE_DIR, "t05b_table9_interactions.csv"), index=False)
        log("\n--- Table 9 summary ---", f)
        log(tbl.to_string(index=False), f)

    return summary_rows


# =============================================================================
# MAIN
# =============================================================================

def run_iv_interactions():
    df = pd.read_csv(os.path.join(PROC_DIR, "panel_clean.csv"))
    df[TIME_COL] = pd.to_numeric(df[TIME_COL], errors="coerce")
    df.sort_values([ID_COL, TIME_COL], inplace=True)
    df.reset_index(drop=True, inplace=True)

    f = open(os.path.join(LOG_DIR, "05b_iv_interactions.txt"), "w")
    log("=" * 70, f)
    log("STEP 5b — IV/2SLS AND INTERACTION TERMS", f)
    log("=" * 70, f)

    run_table6(df, f)
    run_table9(df, f)

    f.close()
    print("[OK] Step 5b complete. Log: outputs/logs/05b_iv_interactions.txt")


if __name__ == "__main__":
    run_iv_interactions()
