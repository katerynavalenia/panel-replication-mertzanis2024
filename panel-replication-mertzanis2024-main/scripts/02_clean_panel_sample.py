# =============================================================================
# 02_clean_panel_sample.py
# Step 2 — Panel sample selection: keep countries with ≥ MIN_CONSEC
#          consecutive observations of Y; describe attrition and holes.
# =============================================================================
# Run:  python scripts/02_clean_panel_sample.py
# Input:  data/processed/panel_raw.csv
# Output: data/processed/panel_clean.csv
#         outputs/tables/t02a_sample_selection.csv
#         outputs/tables/t02b_obs_per_year.csv
#         outputs/tables/t02c_T_distribution.csv
#         outputs/figures/fig_obs_per_year.png
# =============================================================================

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (PROC_DIR, TABLE_DIR, FIG_DIR, LOG_DIR,
                    ID_COL, TIME_COL, Y_COL, MIN_CONSEC, FIG_DPI, FIG_FORMAT)


# ─────────────────────────────────────────────────────────────────────────────
# Helper: find consecutive runs ≥ MIN_CONSEC within a sorted group
# ─────────────────────────────────────────────────────────────────────────────
def mark_valid_consecutive(series: pd.Series, min_run: int) -> pd.Series:
    """
    Given a boolean Series (True where Y is observed) indexed the same as the
    data for one individual, returns a boolean Series where True means the
    observation belongs to a run of at least `min_run` consecutive True values.
    """
    valid   = series.notna().values
    keep    = np.zeros(len(valid), dtype=bool)
    i = 0
    while i < len(valid):
        if valid[i]:
            j = i
            while j < len(valid) and valid[j]:
                j += 1
            run_len = j - i
            if run_len >= min_run:
                keep[i:j] = True
            i = j
        else:
            i += 1
    return pd.Series(keep, index=series.index)


def log(msg, f=None):
    print(msg)
    if f:
        f.write(msg + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def clean_panel_sample():
    os.makedirs(TABLE_DIR, exist_ok=True)
    os.makedirs(FIG_DIR,   exist_ok=True)
    os.makedirs(LOG_DIR,   exist_ok=True)

    df = pd.read_csv(os.path.join(PROC_DIR, "panel_raw.csv"))
    df[TIME_COL] = pd.to_numeric(df[TIME_COL], errors="coerce")
    df.sort_values([ID_COL, TIME_COL], inplace=True)
    df.reset_index(drop=True, inplace=True)

    f = open(os.path.join(LOG_DIR, "02_clean_panel.txt"), "w")
    log("=" * 70, f)
    log("STEP 2 — PANEL SAMPLE SELECTION", f)
    log("=" * 70, f)

    N_total = df[ID_COL].nunique()
    NT_total = len(df)
    log(f"Starting sample: N={N_total}, NT={NT_total}", f)

    # ── 1. Drop rows where Y is missing (no Y at all) ─────────────────────────
    y_obs = df[Y_COL].notna()
    log(f"\nRows with observed Y: {y_obs.sum()} / {NT_total} "
        f"({y_obs.mean()*100:.1f}%)", f)

    # ── 2. For each individual, mark which Y observations belong to a
    #        consecutive run of length ≥ MIN_CONSEC ─────────────────────────
    def get_keep_mask(grp):
        return mark_valid_consecutive(grp[Y_COL], MIN_CONSEC)

    keep_mask = df.groupby(ID_COL, group_keys=False).apply(get_keep_mask)
    # Replace Y with NaN where not in a valid run
    df[Y_COL + "_selected"] = df[Y_COL].where(keep_mask, other=np.nan)

    # ── 3. Identify individuals with at least one valid Y observation ─────────
    valid_ids   = df.groupby(ID_COL)[Y_COL + "_selected"].any()
    kept_ids    = valid_ids[valid_ids].index.tolist()
    excluded_ids = valid_ids[~valid_ids].index.tolist()

    N_kept     = len(kept_ids)
    N_excluded = len(excluded_ids)
    log(f"\n--- Sample selection (min {MIN_CONSEC} consecutive obs of Y) ---", f)
    log(f"  N total      : {N_total}", f)
    log(f"  N kept       : {N_kept}", f)
    log(f"  N excluded   : {N_excluded}", f)
    log(f"\nExcluded individuals ({N_excluded}):", f)
    for i, name in enumerate(sorted(excluded_ids)):
        log(f"  {i+1:3d}. {name}", f)
    log(f"\nKept individuals ({N_kept}):", f)
    for i, name in enumerate(sorted(kept_ids)):
        log(f"  {i+1:3d}. {name}", f)

    # Save sample selection table
    sel_df = pd.DataFrame({
        "individual": excluded_ids + kept_ids,
        "in_sample" : [False] * N_excluded + [True] * N_kept
    })
    sel_df.to_csv(os.path.join(TABLE_DIR, "t02a_sample_selection.csv"), index=False)

    # ── 4. Restrict to kept individuals; use selected Y ───────────────────────
    df_clean = df[df[ID_COL].isin(kept_ids)].copy()
    # Replace original Y with the selected version (isolated runs set to NaN)
    df_clean[Y_COL] = df_clean[Y_COL + "_selected"]
    df_clean.drop(columns=[Y_COL + "_selected"], inplace=True)

    # Keep only rows where at least Y is not NaN for meaningful statistics,
    # but retain ALL rows for the selected individuals (requirement says
    # statistics must be computed on this selected sample).
    NT_clean = len(df_clean)
    log(f"\n  NT in cleaned sample: {NT_clean}", f)

    # ── 5. Observations per year (attrition) ──────────────────────────────────
    obs_year = df_clean.groupby(TIME_COL)[ID_COL].count().reset_index()
    obs_year.columns = ["year", "N_obs"]
    obs_year.to_csv(os.path.join(TABLE_DIR, "t02b_obs_per_year.csv"), index=False)

    log("\n--- Observations per year ---", f)
    log(obs_year.to_string(index=False), f)

    plt.figure(figsize=(9, 4))
    plt.bar(obs_year["year"], obs_year["N_obs"], color="#4C8BE2", edgecolor="white")
    plt.xlabel("Year")
    plt.ylabel("Number of countries")
    plt.title("Number of Countries per Year (Cleaned Panel)")
    plt.xticks(obs_year["year"], rotation=45, ha="right")
    plt.tight_layout()
    fig_path = os.path.join(FIG_DIR, f"fig01_obs_per_year.{FIG_FORMAT}")
    plt.savefig(fig_path, dpi=FIG_DPI)
    plt.close()
    log(f"\n[SAVED] {fig_path}", f)

    # ── 6. T distribution (individuals by number of observations) ─────────────
    t_per_id = df_clean.groupby(ID_COL)[Y_COL].count()
    t_max    = t_per_id.max()
    t_dist   = t_per_id.value_counts().sort_index(ascending=False).reset_index()
    t_dist.columns = ["T_obs", "N_individuals"]
    t_dist.to_csv(os.path.join(TABLE_DIR, "t02c_T_distribution.csv"), index=False)

    log("\n--- T distribution (individuals by number of Y observations) ---", f)
    log(f"  Tmax = {t_max}", f)
    log(t_dist.to_string(index=False), f)

    # ── 7. Identify individuals with holes (discontinuous obs) ────────────────
    def has_hole(grp):
        years = grp[TIME_COL][grp[Y_COL].notna()].sort_values().values
        if len(years) < 2:
            return False
        gaps = np.diff(years)
        return bool((gaps > 1).any())

    holes = df_clean.groupby(ID_COL).apply(has_hole)
    n_holes = holes.sum()
    log(f"\n--- Individuals with holes (discontinuous Y observations) ---", f)
    log(f"  Count: {n_holes} / {N_kept} "
        f"({n_holes/N_kept*100:.1f}%)", f)
    if n_holes <= 100:
        log("  List:", f)
        for name in holes[holes].index.tolist():
            log(f"    {name}", f)

    # ── 8. Balanced vs unbalanced ─────────────────────────────────────────────
    is_balanced = (t_per_id == t_max).all()
    log(f"\n--- Panel type ---", f)
    log(f"  Tmax     = {t_max}", f)
    log(f"  Balanced = {is_balanced}", f)
    if not is_balanced:
        log("  → Unbalanced panel. TWFE will use Wansbeek-Kapteijn residuals.", f)

    # ── 9. Save cleaned panel ─────────────────────────────────────────────────
    out_path = os.path.join(PROC_DIR, "panel_clean.csv")
    df_clean.to_csv(out_path, index=False)
    log(f"\n[SAVED] {out_path}", f)

    f.close()
    print(f"\n[OK] Step 2 complete. Log: outputs/logs/02_clean_panel.txt")
    return df_clean


if __name__ == "__main__":
    clean_panel_sample()
