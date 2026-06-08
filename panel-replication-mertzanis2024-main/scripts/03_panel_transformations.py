# =============================================================================
# 03_panel_transformations.py
# Step 3 — Compute all four panel transformations:
#   (A) Between:      x_bar_i  = mean over t for each country i
#   (B) One-way FE:   x_it - x_bar_i
#   (C) First Diff:   x_it - x_{i,t-1}  (NaN at individual breaks)
#   (D) TWFE:         x_it - x_bar_i - x_bar_t + x_bar   (balanced sub-panel)
#                     or Wansbeek-Kapteijn residuals (unbalanced full panel)
# Also computes variance decomposition for every variable.
# =============================================================================
# Run:  python scripts/03_panel_transformations.py
# Input:  data/processed/panel_clean.csv
# Output: data/processed/panel_transforms.csv
#         outputs/tables/t03a_variance_decomp.csv
#         outputs/tables/t03b_variable_classification.csv
#         outputs/logs/03_transforms.txt
# =============================================================================

import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (PROC_DIR, TABLE_DIR, LOG_DIR,
                    ID_COL, TIME_COL, Y_COL, X_COL, CONTROL_COLS,
                    TWFE_MIN_T)


def log(msg, f=None):
    print(msg)
    if f:
        f.write(msg + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# Core transformation functions
# ─────────────────────────────────────────────────────────────────────────────

def between_transform(df: pd.DataFrame, col: str) -> pd.Series:
    """Return group mean: x_bar_i for each individual."""
    return df.groupby(ID_COL)[col].transform("mean")


def within_transform(df: pd.DataFrame, col: str) -> pd.Series:
    """Return within (one-way FE) demeaned: x_it - x_bar_i."""
    return df[col] - between_transform(df, col)


def first_diff(df: pd.DataFrame, col: str) -> pd.Series:
    """
    Return first difference x_it - x_{i,t-1}.
    NaN is inserted whenever the individual changes (no cross-individual diff).
    Dataframe must be sorted by [ID_COL, TIME_COL] before calling.
    """
    fd = df.groupby(ID_COL)[col].diff()
    return fd


def twfe_balanced(df: pd.DataFrame, col: str) -> pd.Series:
    """
    Two-way FE transformation on a balanced sub-panel:
       x_it - x_bar_i - x_bar_t + x_bar
    Requires df to already be a balanced sub-panel.
    """
    x_bar_i  = df.groupby(ID_COL)[col].transform("mean")        # country mean
    x_bar_t  = df.groupby(TIME_COL)[col].transform("mean")      # year mean
    x_bar    = df[col].mean()                                     # grand mean
    return df[col] - x_bar_i - x_bar_t + x_bar


def twfe_unbalanced(df: pd.DataFrame, col: str) -> pd.Series:
    """
    Wansbeek-Kapteijn TWFE for unbalanced panels.
    Regresses the within-transformed variable on time dummies; residuals = TWFE.
    """
    import statsmodels.api as sm
    within = within_transform(df, col).dropna()
    if within.empty:
        return pd.Series(np.nan, index=df.index)
    time_dummies = pd.get_dummies(df.loc[within.index, TIME_COL],
                                  drop_first=True).astype(float)
    X_fit = sm.add_constant(time_dummies)
    model = sm.OLS(within, X_fit).fit()
    result = pd.Series(np.nan, index=df.index)
    result.loc[within.index] = model.resid.values
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Variance decomposition
# ─────────────────────────────────────────────────────────────────────────────

def variance_decomposition(df: pd.DataFrame, col: str) -> dict:
    """
    Compute overall, between, and within variance for a variable.
    Between and within variances are weighted averages (T-weights).
    """
    grp  = df.groupby(ID_COL)[col]
    T_i  = grp.count()                     # obs per individual
    xbar_i = grp.mean()                    # between means

    overall_var  = df[col].var(ddof=1)
    between_var  = xbar_i.var(ddof=1)
    within_vals  = df[col] - df[ID_COL].map(xbar_i)
    within_var   = within_vals.var(ddof=1)

    N   = df[ID_COL].nunique()
    NT  = df[col].notna().sum()
    pct = within_var / overall_var * 100 if overall_var > 0 else np.nan

    return {
        "variable"      : col,
        "N"             : N,
        "NT"            : NT,
        "NT/N"          : round(NT / N, 2),
        "overall_var"   : overall_var,
        "between_var"   : between_var,
        "within_var"    : within_var,
        "pct_within"    : pct,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def compute_transforms():
    os.makedirs(TABLE_DIR, exist_ok=True)
    os.makedirs(LOG_DIR,   exist_ok=True)

    df = pd.read_csv(os.path.join(PROC_DIR, "panel_clean.csv"))
    df[TIME_COL] = pd.to_numeric(df[TIME_COL], errors="coerce")
    df.sort_values([ID_COL, TIME_COL], inplace=True)
    df.reset_index(drop=True, inplace=True)

    f = open(os.path.join(LOG_DIR, "03_transforms.txt"), "w")
    log("=" * 70, f)
    log("STEP 3 — PANEL TRANSFORMATIONS", f)
    log("=" * 70, f)

    all_vars = [Y_COL, X_COL] + CONTROL_COLS
    # Keep only vars that exist in the data
    all_vars = [v for v in all_vars if v in df.columns]
    log(f"Variables to transform: {all_vars}\n", f)

    # ── A. Between transformation ─────────────────────────────────────────────
    log("--- A. Between transformation ---", f)
    between_df = pd.DataFrame()
    between_df[ID_COL]   = df[ID_COL]
    between_df[TIME_COL] = df[TIME_COL]
    for v in all_vars:
        between_df[f"{v}_bet"] = between_transform(df, v)

    # ── B. One-way within (FE) transformation ─────────────────────────────────
    log("--- B. One-way within (FE) transformation ---", f)
    within_df = pd.DataFrame()
    within_df[ID_COL]   = df[ID_COL]
    within_df[TIME_COL] = df[TIME_COL]
    for v in all_vars:
        within_df[f"{v}_wi"] = within_transform(df, v)

    # ── C. First differences ──────────────────────────────────────────────────
    log("--- C. First differences ---", f)
    fd_df = pd.DataFrame()
    fd_df[ID_COL]   = df[ID_COL]
    fd_df[TIME_COL] = df[TIME_COL]
    for v in all_vars:
        fd_df[f"{v}_fd"] = first_diff(df, v)

    # Sanity check: first row of each new individual must be NaN in FD
    log("\nFirst-difference check (first 15 obs) —", f)
    check_cols = [ID_COL, TIME_COL, f"{Y_COL}_fd", f"{X_COL}_fd"]
    check_cols = [c for c in check_cols if c in fd_df.columns]
    log(fd_df[check_cols].head(15).to_string(), f)

    # ── D. TWFE transformation ────────────────────────────────────────────────
    log("\n--- D. TWFE transformation ---", f)
    twfe_df = pd.DataFrame()
    twfe_df[ID_COL]   = df[ID_COL]
    twfe_df[TIME_COL] = df[TIME_COL]

    # Build balanced sub-panel
    t_per_id = df.groupby(ID_COL)[Y_COL].count()
    if TWFE_MIN_T is None:
        t_threshold = t_per_id.max()        # require full T
    else:
        t_threshold = int(TWFE_MIN_T)

    balanced_ids = t_per_id[t_per_id >= t_threshold].index.tolist()
    df_bal = df[df[ID_COL].isin(balanced_ids)].copy()

    # Check if truly balanced (all have same T)
    t_bal = df_bal.groupby(ID_COL)[Y_COL].count()
    is_balanced = (t_bal == t_bal.max()).all()
    N_bal = len(balanced_ids)
    T_bal = t_bal.max() if N_bal > 0 else 0
    log(f"  Balanced sub-panel: N={N_bal}, T={T_bal}", f)

    for v in all_vars:
        if v not in df.columns:
            continue
        if is_balanced and N_bal > 0:
            bal_vals = twfe_balanced(df_bal, v)
            twfe_df[f"{v}_twfe"] = np.nan
            twfe_df.loc[df_bal.index, f"{v}_twfe"] = bal_vals.values
        else:
            log(f"  Using Wansbeek-Kapteijn (unbalanced) for {v}", f)
            twfe_df[f"{v}_twfe"] = twfe_unbalanced(df, v)

    # ── E. TWFE time means for balanced sub-panel ─────────────────────────────
    log("\n--- Time means (balanced sub-panel) for TWFE ---", f)
    if N_bal > 0 and Y_COL in df_bal.columns:
        time_means = df_bal.groupby(TIME_COL)[Y_COL].mean()
        grand_mean = df_bal[Y_COL].mean()
        time_demean = time_means - grand_mean
        log("  x_bar_t - x_bar  (should sum close to 0):", f)
        log(time_demean.round(4).to_string(), f)
        time_demean.to_csv(
            os.path.join(TABLE_DIR, "t03c_twfe_time_means.csv"), header=True)

    # ── F. Variance decomposition ─────────────────────────────────────────────
    log("\n--- F. Variance decomposition ---", f)
    decomp_rows = []
    for v in all_vars:
        if v in df.columns:
            row = variance_decomposition(df, v)
            decomp_rows.append(row)
    decomp = pd.DataFrame(decomp_rows)
    decomp.sort_values("pct_within", inplace=True)
    decomp.to_csv(os.path.join(TABLE_DIR, "t03a_variance_decomp.csv"), index=False)
    log(decomp.round(4).to_string(index=False), f)

    # ── G. Variable classification ────────────────────────────────────────────
    log("\n--- G. Variable classification ---", f)
    eps = 1e-10
    time_invariant  = decomp[decomp["pct_within"] < eps]["variable"].tolist()
    ind_invariant   = decomp[decomp["pct_within"] > 100 - eps]["variable"].tolist()
    double_indexed  = decomp[(decomp["pct_within"] >= eps) &
                             (decomp["pct_within"] <= 100 - eps)]["variable"].tolist()

    log(f"  Time-invariant (0% within)   : {time_invariant}", f)
    log(f"  Individual-invariant (100%)  : {ind_invariant}", f)
    log(f"  Double-indexed (0-100%)      : {double_indexed}", f)

    class_df = pd.DataFrame({
        "variable"  : time_invariant + ind_invariant + double_indexed,
        "category"  : (["time_invariant"] * len(time_invariant) +
                       ["individual_invariant"] * len(ind_invariant) +
                       ["double_indexed"] * len(double_indexed))
    })
    class_df.to_csv(os.path.join(TABLE_DIR, "t03b_variable_classification.csv"),
                    index=False)

    # ── H. Merge all transforms and save ─────────────────────────────────────
    result = df.copy()
    for sub_df in [between_df, within_df, fd_df, twfe_df]:
        # Merge on ID and TIME (avoid duplicating identifier cols)
        merge_cols = [c for c in sub_df.columns
                      if c not in [ID_COL, TIME_COL]]
        result = result.merge(
            sub_df[[ID_COL, TIME_COL] + merge_cols],
            on=[ID_COL, TIME_COL], how="left"
        )

    out_path = os.path.join(PROC_DIR, "panel_transforms.csv")
    result.to_csv(out_path, index=False)
    log(f"\n[SAVED] {out_path}", f)
    log(f"  Shape: {result.shape}", f)

    f.close()
    print(f"\n[OK] Step 3 complete. Log: outputs/logs/03_transforms.txt")
    return result


if __name__ == "__main__":
    compute_transforms()
