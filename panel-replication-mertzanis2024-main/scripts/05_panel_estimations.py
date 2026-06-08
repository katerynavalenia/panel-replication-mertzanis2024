# =============================================================================
# 05_panel_estimations.py  —  Fixed version
# Step 5 — Panel regressions matching the paper's tables + homework estimators.
#
# KEY METHODOLOGICAL NOTE:
#   cbmnd, cbenf, cbsys, dum9, dum12 are TIME-INVARIANT (0% within variance).
#   They are perfectly collinear with entity (country) dummies and CANNOT be
#   identified by entity FE or TWFE.  Stata drops them automatically with
#   "dropped due to collinearity".  We follow the same rule here:
#     • Pooled OLS  (col 1) — all regressors included, between-variation identifies CB vars
#     • + Year FE   (col 2) — all regressors included, year dummies added
#     • + Entity FE (col 3) — only time-varying controls remain; CB vars dropped
#     • TWFE        (col 4) — only time-varying controls remain; CB vars dropped
#   This is the correct replication of the paper's Table 4.
#
# PART A — PAPER REPLICATION
#   Table 4: Pooled OLS | +Year FE | +Entity FE | TWFE  (cluster by country)
#   Table 5: Robustness — gov bonds, corp bonds, devlev, ex-China, non-linear
#   Table 7: Robustness — risk premiums | energy vars | geopolitical vars
#
# PART B — HOMEWORK ADDITIONAL ESTIMATORS
#   Table H: Between | One-Way FE | Mundlak RE | TWFE | First Differences
#
# Stata reference:
#   global xvar cbmnd cbenf cbsys infl rating fie gdpg dum9 dum12
#   reg bndgrn $xvar [i.year] [i.country1], cluster(country1)
#   (Stata automatically drops cbmnd/cbenf/cbsys/dum9/dum12 in FE specs)
# =============================================================================

import os, sys, warnings
import pandas as pd
import numpy as np
import statsmodels.api as sm
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (PROC_DIR, TABLE_DIR, LOG_DIR,
                    ID_COL, TIME_COL, CLUST_COL,
                    Y_COL, Y_GOV_COL, Y_CORP_COL,
                    CB_COLS, CB_SQ_COLS, CONTROL_COLS, XVAR_COLS,
                    RISK_COLS, ENERGY_COLS, UNCERT_COLS)

warnings.filterwarnings("ignore")

try:
    from linearmodels.panel import (BetweenOLS, PanelOLS,
                                    RandomEffects, FirstDifferenceOLS,
                                    PooledOLS as lmPooledOLS)
    HAS_LM = True
except ImportError:
    HAS_LM = False

# Variables that are time-invariant — dropped by entity FE/TWFE automatically
TIME_INVAR = ["cbmnd", "cbenf", "cbsys", "cbmndsq", "cbenfsq", "cbsyssq",
              "dum9", "dum12"]
# Time-varying controls only
TV_CONTROLS = ["infl", "rating", "fie", "gdpg"]


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


def fmt_coef(coef, se, p, decimals=4):
    st = stars(p)
    c  = f"{round(coef, decimals)}{st}" if not pd.isna(coef) else ""
    s  = f"({round(se,   decimals)})"   if not pd.isna(se)   else ""
    return c, s


def build_display_table(results, report_vars):
    rows = {}
    for vname in report_vars:
        rows[vname]         = {}
        rows[f"se_{vname}"] = {}
    rows["N_obs"]  = {}
    rows["N_ids"]  = {}
    rows["R2"]     = {}

    for model_name, res, n_obs, n_ids in results:
        if res is None:
            for vname in report_vars:
                rows[vname][model_name]         = ""
                rows[f"se_{vname}"][model_name] = ""
            rows["N_obs"][model_name] = n_obs
            rows["N_ids"][model_name] = n_ids
            rows["R2"][model_name]    = ""
            continue
        for vname in report_vars:
            try:
                params  = res.params
                bse     = res.bse if hasattr(res, "bse") else res.std_errors
                pvalues = res.pvalues
                coef  = float(params[vname])
                se    = float(bse[vname])
                p_val = float(pvalues[vname])
                c, s  = fmt_coef(coef, se, p_val)
            except (KeyError, AttributeError):
                c, s = "", ""
            rows[vname][model_name]         = c
            rows[f"se_{vname}"][model_name] = s
        rows["N_obs"][model_name] = n_obs
        rows["N_ids"][model_name] = n_ids
        try:
            rows["R2"][model_name] = round(float(res.rsquared), 4)
        except Exception:
            try:
                rows["R2"][model_name] = round(float(res.rsquared_overall), 4)
            except Exception:
                rows["R2"][model_name] = ""
    return pd.DataFrame(rows).T


# =============================================================================
# OLS helper (Pooled OLS and +Year FE only — no entity FE here)
# =============================================================================

def run_pooled_ols(df, y_col, x_cols, year_fe=False, subset_mask=None, label=""):
    """
    Pooled OLS with optional year dummies, cluster-robust SE by country.
    Used for columns (1) and (2) of Table 4 — CB vars CAN be identified here.
    """
    try:
        sub = df.loc[subset_mask].copy() if subset_mask is not None else df.copy()
        needed = [y_col] + x_cols + [CLUST_COL, TIME_COL, ID_COL]
        needed = [c for c in needed if c in sub.columns]
        sub    = sub[needed].dropna(subset=[y_col] + x_cols)

        X = sub[x_cols].copy().astype(float)
        if year_fe:
            ydums = pd.get_dummies(sub[TIME_COL], prefix="yr",
                                   drop_first=True).astype(float)
            X = pd.concat([X, ydums], axis=1)

        X      = sm.add_constant(X, has_constant="add")
        Y      = sub[y_col].astype(float)
        groups = sub[CLUST_COL].astype(int)
        n_ids  = int(sub[ID_COL].nunique())

        if len(sub) < (X.shape[1] + 3) or n_ids < 5:
            return label, None, len(sub), n_ids

        res    = sm.OLS(Y, X).fit(cov_type="cluster",
                                  cov_kwds={"groups": groups},
                                  use_t=True)
        n_obs  = int(res.nobs)
        return label, res, n_obs, n_ids
    except Exception as e:
        print(f"  [ERROR] {label}: {e}")
        return label, None, 0, 0


# =============================================================================
# Entity FE / TWFE via linearmodels (time-invariant vars properly excluded)
# =============================================================================

def run_fe(df, y_col, x_cols, time_effects=False, subset_mask=None, label=""):
    """
    Entity FE (or TWFE) via linearmodels.PanelOLS.
    Time-invariant variables are automatically excluded before fitting.
    """
    if not HAS_LM:
        return label, None, 0, 0
    try:
        sub = df.loc[subset_mask].copy() if subset_mask is not None else df.copy()
        # Remove time-invariant regressors — they are absorbed by entity FE
        x_tv = [v for v in x_cols if v not in TIME_INVAR and v in sub.columns]
        needed = [y_col] + x_tv + [ID_COL, TIME_COL]
        sub    = sub[[c for c in needed if c in sub.columns]].dropna(
                    subset=[y_col] + x_tv)
        n_ent = sub[ID_COL].nunique()
        if n_ent < 3 or len(sub) < (n_ent + len(x_tv) + 5):
            return label, None, len(sub), n_ent

        sub = sub.set_index([ID_COL, TIME_COL])
        Y   = sub[y_col]
        X   = sub[x_tv]
        mod = PanelOLS(Y, X, entity_effects=True,
                       time_effects=time_effects,
                       drop_absorbed=True)
        res = mod.fit(cov_type="clustered", cluster_entity=True)
        return label, res, int(res.nobs), int(Y.index.get_level_values(0).nunique())
    except Exception as e:
        print(f"  [ERROR] {label}: {e}")
        return label, None, 0, 0


# =============================================================================
# PAPER TABLE 4: Main Results
# =============================================================================

def run_table4(df, f):
    log("\n" + "=" * 70, f)
    log("PAPER TABLE 4 — MAIN RESULTS  (dep. var: bndgrn)", f)
    log("xvar = cbmnd cbenf cbsys infl rating fie gdpg dum9 dum12", f)
    log("NOTE: cbmnd/cbenf/cbsys/dum9/dum12 are time-invariant.", f)
    log("      They are identified only in cols (1)-(2). In cols (3)-(4)", f)
    log("      they are dropped (collinear with entity dummies, as in Stata).", f)
    log("=" * 70, f)

    x_all = [v for v in XVAR_COLS if v in df.columns]

    results = []

    # (1) Pooled OLS — all regressors
    log("\n  (1) Pooled OLS ...", f)
    r1 = run_pooled_ols(df, Y_COL, x_all, year_fe=False, label="(1) Pooled OLS")
    results.append(r1)

    # (2) + Year FE (pooled with year dummies) — all regressors
    log("  (2) + Year FE ...", f)
    r2 = run_pooled_ols(df, Y_COL, x_all, year_fe=True, label="(2) + Year FE")
    results.append(r2)

    # (3) + Entity FE — only time-varying controls
    log("  (3) + Entity FE ...", f)
    r3 = run_fe(df, Y_COL, x_all, time_effects=False, label="(3) + Entity FE")
    results.append(r3)

    # (4) TWFE — only time-varying controls
    log("  (4) TWFE (Year+Entity) ...", f)
    r4 = run_fe(df, Y_COL, x_all, time_effects=True, label="(4) TWFE")
    results.append(r4)

    # Log key coefficients
    for label, res, n_obs, n_ids in results:
        if res is None:
            continue
        log(f"\n  {label}: N={n_obs}, N_countries={n_ids}", f)
        params  = res.params
        bse     = res.bse if hasattr(res, "bse") else res.std_errors
        pvalues = res.pvalues
        for v in CB_COLS + TV_CONTROLS:
            if v in params.index:
                log(f"    {v}: {float(params[v]):.4f} "
                    f"({float(bse[v]):.4f}){stars(float(pvalues[v]))}", f)

    report_vars = CB_COLS + CONTROL_COLS
    tbl = build_display_table(
        [(r[0], r[1], r[2], r[3]) for r in results],
        report_vars)
    tbl.to_csv(os.path.join(TABLE_DIR, "t05_table4_main.csv"))
    log("\n--- Table 4 ---", f)
    log(tbl.to_string(), f)
    log("\n*** p<0.01  ** p<0.05  * p<0.10  (cluster-robust SE in parentheses)", f)
    log("Blank cells in cols (3)-(4): variable dropped due to collinearity with entity FE.", f)
    return results


# =============================================================================
# PAPER TABLE 5: Robustness
# =============================================================================

def run_table5(df, f):
    log("\n" + "=" * 70, f)
    log("PAPER TABLE 5 — ROBUSTNESS", f)
    log("=" * 70, f)

    x_base = [v for v in XVAR_COLS   if v in df.columns]
    x_sq   = [v for v in CB_SQ_COLS  if v in df.columns]

    specs = []

    # (1) Gov bonds, TWFE (time-varying controls only)
    if Y_GOV_COL in df.columns:
        specs.append(("(1) Gov bonds TWFE", Y_GOV_COL,
                      TV_CONTROLS, "fe_twfe", None))

    # (2) Corp bonds, entity FE (time-varying controls only)
    if Y_CORP_COL in df.columns:
        specs.append(("(2) Corp bonds +Entity FE", Y_CORP_COL,
                      TV_CONTROLS, "fe_entity", None))

    # (3) Developed, pooled with year FE (all regressors)
    if "devlev2" in df.columns:
        mask_dev = df["devlev2"] == "High income"
        specs.append(("(3) Developed Pooled+YrFE", Y_COL,
                      x_base, "pooled_year", mask_dev))

    # (4) Developing — only pooled OLS (too few countries for FE)
    if "devlev2" in df.columns:
        mask_low = df["devlev2"] == "Low income"
        n_dev = df.loc[mask_low].dropna(subset=[Y_COL]+TV_CONTROLS)[ID_COL].nunique()
        if n_dev >= 3:
            specs.append(("(4) Developing Pooled OLS", Y_COL,
                          x_base, "pooled", mask_low))
        else:
            log(f"  [SKIP] Developing countries: only {n_dev} with full data "
                f"— too few for regression.", f)

    # (5) Ex-China, pooled with year FE
    if "china" in df.columns:
        mask_noc = df["china"] == 0
        specs.append(("(5) Ex-China Pooled+YrFE", Y_COL,
                      x_base, "pooled_year", mask_noc))

    # (6) Non-linear: pooled + year FE + squared CB terms
    if x_sq:
        specs.append(("(6) Non-linear Pooled+YrFE", Y_COL,
                      x_base + x_sq, "pooled_year", None))

    results = []
    for label, y_col, x_cols, spec_type, mask in specs:
        mask_series = mask if mask is None else mask.values
        log(f"\n  {label} ...", f)
        if spec_type == "fe_twfe":
            r = run_fe(df, y_col, x_cols, time_effects=True,
                       subset_mask=None if mask is None else df.index[mask],
                       label=label)
        elif spec_type == "fe_entity":
            r = run_fe(df, y_col, x_cols, time_effects=False,
                       subset_mask=None if mask is None else df.index[mask],
                       label=label)
        elif spec_type == "pooled_year":
            r = run_pooled_ols(df, y_col, x_cols, year_fe=True,
                               subset_mask=mask_series, label=label)
        else:
            r = run_pooled_ols(df, y_col, x_cols, year_fe=False,
                               subset_mask=mask_series, label=label)
        results.append(r)
        if r[1] is not None:
            log(f"    N={r[2]}, N_ids={r[3]}", f)
            params  = r[1].params
            bse     = r[1].bse if hasattr(r[1], "bse") else r[1].std_errors
            pvalues = r[1].pvalues
            for v in CB_COLS + TV_CONTROLS:
                if v in params.index:
                    log(f"    {v}: {float(params[v]):.4f} "
                        f"({float(bse[v]):.4f}){stars(float(pvalues[v]))}", f)

    rep_vars = CB_COLS + TV_CONTROLS + [v for v in CB_SQ_COLS if v in df.columns]
    valid = [(r[0], r[1], r[2], r[3]) for r in results if r[1] is not None]
    if valid:
        tbl = build_display_table(valid, rep_vars)
        tbl.to_csv(os.path.join(TABLE_DIR, "t05_table5_robustness.csv"))
        log("\n--- Table 5 ---", f)
        log(tbl.to_string(), f)
    return results


# =============================================================================
# PAPER TABLE 7: Additional Controls (all pooled + year FE)
# =============================================================================

def run_table7(df, f):
    log("\n" + "=" * 70, f)
    log("PAPER TABLE 7 — ADDITIONAL CONTROLS (pooled + year FE)", f)
    log("=" * 70, f)

    x_base = [v for v in XVAR_COLS if v in df.columns]

    extra_groups = [
        ("(1) + Risk premiums",  RISK_COLS),
        ("(2) + Energy/Env",     ENERGY_COLS),
        ("(3) + Geopolitical",   UNCERT_COLS),
    ]

    results = []
    for label, extra in extra_groups:
        x_cols = x_base + [v for v in extra if v in df.columns]
        log(f"\n  {label} ...", f)
        r = run_pooled_ols(df, Y_COL, x_cols, year_fe=True, label=label)
        results.append(r)
        if r[1] is not None:
            log(f"    N={r[2]}", f)
            params  = r[1].params
            bse     = r[1].bse
            pvalues = r[1].pvalues
            for v in CB_COLS:
                if v in params.index:
                    log(f"    {v}: {float(params[v]):.4f} "
                        f"({float(bse[v]):.4f}){stars(float(pvalues[v]))}", f)

    extra_all = RISK_COLS + ENERGY_COLS + UNCERT_COLS
    rep_vars  = CB_COLS + CONTROL_COLS + [v for v in extra_all if v in df.columns]
    valid     = [(r[0], r[1], r[2], r[3]) for r in results if r[1] is not None]
    if valid:
        tbl = build_display_table(valid, rep_vars)
        tbl.to_csv(os.path.join(TABLE_DIR, "t05_table7_add_controls.csv"))
        log("\n--- Table 7 ---", f)
        log(tbl.to_string(), f)
    return results


# =============================================================================
# HOMEWORK ESTIMATORS
# =============================================================================

def run_homework_estimators(df, f):
    log("\n" + "=" * 70, f)
    log("HOMEWORK TABLE H — ADDITIONAL ESTIMATORS", f)
    log("Between | One-Way FE | Mundlak RE | TWFE | First Differences", f)
    log("NOTE: CB variables shown only where estimator identifies them.", f)
    log("=" * 70, f)

    if not HAS_LM:
        log("[SKIP] linearmodels not installed.", f)
        return []

    x_all = [v for v in XVAR_COLS if v in df.columns]
    x_tv  = [v for v in TV_CONTROLS if v in df.columns]   # time-varying only

    needed = [Y_COL] + x_all + [ID_COL, TIME_COL]
    sub    = df[[c for c in needed if c in df.columns]].dropna(subset=[Y_COL]+x_all)
    sub_mi = sub.set_index([ID_COL, TIME_COL])
    Y      = sub_mi[Y_COL]
    X_all  = sub_mi[x_all]
    X_tv   = sub_mi[x_tv]

    results = []

    # 1. Between OLS — identifies time-invariant CB vars (uses country means)
    log("\n  [HW1] Between OLS ...", f)
    try:
        res1 = BetweenOLS(Y, X_all).fit(cov_type="robust")
        log(str(res1.summary), f)
        results.append(("Between", res1, int(res1.nobs),
                         Y.index.get_level_values(0).nunique()))
    except Exception as e:
        log(f"  [ERROR] {e}", f)

    # 2. One-Way FE — only time-varying controls (CB vars dropped)
    log("\n  [HW2] One-Way FE (entity) ...", f)
    try:
        res2 = PanelOLS(Y, X_tv, entity_effects=True,
                        drop_absorbed=True).fit(cov_type="clustered",
                                                cluster_entity=True)
        log(str(res2.summary), f)
        results.append(("One-Way FE", res2, int(res2.nobs),
                         Y.index.get_level_values(0).nunique()))
    except Exception as e:
        log(f"  [ERROR] {e}", f)

    # 3. Mundlak RE — includes group means of time-varying X as correlated RE correction
    log("\n  [HW3] Mundlak RE ...", f)
    try:
        sub_m = sub.copy()
        mundlak_extras = []
        for xc in x_tv:           # only add group-means for time-varying vars
            bar_col = f"{xc}_bar"
            sub_m[bar_col] = sub_m.groupby(ID_COL)[xc].transform("mean")
            if not np.allclose(sub_m[xc].fillna(0), sub_m[bar_col].fillna(0),
                               equal_nan=True):
                mundlak_extras.append(bar_col)
        mundlak_x = x_all + mundlak_extras
        sub_m2    = sub_m.set_index([ID_COL, TIME_COL])
        Y_m  = sub_m2[Y_COL]
        X_m  = sub_m2[[c for c in mundlak_x if c in sub_m2.columns]]
        res3 = RandomEffects(Y_m, X_m).fit(cov_type="robust")
        log(str(res3.summary), f)
        results.append(("Mundlak RE", res3, int(res3.nobs),
                         Y_m.index.get_level_values(0).nunique()))
    except Exception as e:
        log(f"  [ERROR] {e}", f)

    # 4. TWFE — only time-varying controls (CB vars dropped)
    log("\n  [HW4] TWFE ...", f)
    try:
        res4 = PanelOLS(Y, X_tv, entity_effects=True,
                        time_effects=True, drop_absorbed=True).fit(
            cov_type="clustered", cluster_entity=True)
        log(str(res4.summary), f)
        results.append(("TWFE", res4, int(res4.nobs),
                         Y.index.get_level_values(0).nunique()))
    except Exception as e:
        log(f"  [ERROR] {e}", f)

    # 5. First Differences — only time-varying controls (CB vars differenced to 0)
    log("\n  [HW5] First Differences ...", f)
    try:
        res5 = FirstDifferenceOLS(Y, X_tv).fit(cov_type="clustered",
                                                cluster_entity=True)
        log(str(res5.summary), f)
        results.append(("First Diff", res5, int(res5.nobs),
                         Y.index.get_level_values(0).nunique()))
    except Exception as e:
        log(f"  [ERROR] {e}", f)

    # Summary table
    if results:
        all_vars = CB_COLS + TV_CONTROLS
        rows = []
        for name, res, n_obs, n_ids in results:
            row = {"model": name, "N_obs": n_obs, "N_ids": n_ids}
            params  = res.params
            bse     = res.bse if hasattr(res, "bse") else res.std_errors
            pvalues = res.pvalues
            for v in all_vars:
                try:
                    coef = float(params[v])
                    se   = float(bse[v])
                    p    = float(pvalues[v])
                    row[f"coef_{v}"]  = round(coef, 4)
                    row[f"se_{v}"]    = round(se, 4)
                    row[f"stars_{v}"] = stars(p)
                except Exception:
                    row[f"coef_{v}"]  = np.nan
                    row[f"se_{v}"]    = np.nan
                    row[f"stars_{v}"] = ""
            rows.append(row)
        hw_df = pd.DataFrame(rows)
        hw_df.to_csv(os.path.join(TABLE_DIR, "t05_homework_estimators.csv"), index=False)
        log("\n--- Homework comparison ---", f)
        log(hw_df.to_string(index=False), f)
    return results


# =============================================================================
# MAIN
# =============================================================================

def run_estimations():
    os.makedirs(TABLE_DIR, exist_ok=True)
    os.makedirs(LOG_DIR,   exist_ok=True)

    df = pd.read_csv(os.path.join(PROC_DIR, "panel_clean.csv"))
    df[TIME_COL]  = pd.to_numeric(df[TIME_COL], errors="coerce")
    df[CLUST_COL] = pd.factorize(df[ID_COL])[0] + 1
    df.sort_values([ID_COL, TIME_COL], inplace=True)
    df.reset_index(drop=True, inplace=True)

    f = open(os.path.join(LOG_DIR, "05_estimations.txt"), "w")
    log("=" * 70, f)
    log("STEP 5 — PANEL DATA REGRESSIONS", f)
    log("Paper: Mertzanis (2024), Energy Economics 133, 107541", f)
    log("=" * 70, f)
    log(f"Sample: N={df[ID_COL].nunique()} countries, "
        f"NT={df[Y_COL].notna().sum()} obs with Y", f)

    r4 = run_table4(df, f)
    r5 = run_table5(df, f)
    r7 = run_table7(df, f)
    rh = run_homework_estimators(df, f)

    f.close()
    print("[OK] Step 5 complete. Log: outputs/logs/05_estimations.txt")
    return r4, r5, r7, rh


if __name__ == "__main__":
    run_estimations()
