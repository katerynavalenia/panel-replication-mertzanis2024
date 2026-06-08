# =============================================================================
# 01_load_explore_data.py
# Step 1 — Load raw data, rename columns to short Stata-style names,
#          inspect structure, produce paper Table 1 (means by country).
# =============================================================================
# Run:  python scripts/01_load_explore_data.py
# Input:  data/raw/data.xlsx
# Output: data/processed/panel_raw.csv   ← renamed, ready for all next steps
#         outputs/tables/t01a_obs_per_country.csv
#         outputs/tables/t01b_missing_values.csv
#         outputs/tables/t01c_raw_descriptives.csv
#         outputs/tables/t01d_means_by_country.csv   ← paper Table 1
#         outputs/logs/01_load_explore.txt
# =============================================================================

import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (RAW_DIR, PROC_DIR, TABLE_DIR, LOG_DIR,
                    RAW_FILE, RENAME_MAP,
                    ID_COL, TIME_COL, Y_COL, CB_COLS, CONTROL_COLS, XVAR_COLS)


def log(msg, f=None):
    print(msg)
    if f:
        f.write(msg + "\n")


def load_and_explore():
    os.makedirs(PROC_DIR,  exist_ok=True)
    os.makedirs(TABLE_DIR, exist_ok=True)
    os.makedirs(LOG_DIR,   exist_ok=True)

    raw_path = os.path.join(RAW_DIR, RAW_FILE)
    assert os.path.exists(raw_path), (
        f"\n[ERROR] Raw file not found:\n  {raw_path}\n"
        "  → Download from https://data.mendeley.com/datasets/xb2m4m8h24/1\n"
        "  → Place in data/raw/ as 'data.xlsx'"
    )

    # ── 1. Load ───────────────────────────────────────────────────────────────
    ext = os.path.splitext(RAW_FILE)[1].lower()
    if ext in (".xlsx", ".xls"):
        df = pd.read_excel(raw_path)
    else:
        df = pd.read_csv(raw_path)

    f = open(os.path.join(LOG_DIR, "01_load_explore.txt"), "w")
    log("=" * 70, f)
    log("STEP 1 — LOAD AND EXPLORE RAW DATA", f)
    log("=" * 70, f)
    log(f"File   : {RAW_FILE}", f)
    log(f"Shape  : {df.shape[0]} rows × {df.shape[1]} columns\n", f)

    # ── 2. Rename columns ─────────────────────────────────────────────────────
    # Build reverse map in case some headers are already short names
    rename_applied = {k: v for k, v in RENAME_MAP.items() if k in df.columns}
    df.rename(columns=rename_applied, inplace=True)
    log(f"Columns renamed: {len(rename_applied)} / {len(RENAME_MAP)}", f)

    # Report any RENAME_MAP entries not found
    not_found = [k for k in RENAME_MAP if k not in rename_applied]
    if not_found:
        log("\n[INFO] The following long headers were not found (may already be "
            "short names or not present):", f)
        for k in not_found:
            log(f"  '{k}'", f)

    # ── 3. Column overview after rename ──────────────────────────────────────
    log("\n--- Columns after rename ---", f)
    for c in df.columns:
        n_miss = df[c].isna().sum()
        pct    = n_miss / len(df) * 100
        log(f"  {c:<20} dtype={str(df[c].dtype):<12} "
            f"missing={n_miss:4d} ({pct:5.1f}%)", f)

    # ── 4. Validate key columns ───────────────────────────────────────────────
    log("\n--- Key column check ---", f)
    key_cols = [ID_COL, TIME_COL, Y_COL] + CB_COLS + CONTROL_COLS
    for c in key_cols:
        status = "OK" if c in df.columns else "MISSING"
        log(f"  {c:<20} {status}", f)

    # ── 5. Panel structure ────────────────────────────────────────────────────
    if ID_COL in df.columns and TIME_COL in df.columns:
        df[TIME_COL] = pd.to_numeric(df[TIME_COL], errors="coerce")
        df.sort_values([ID_COL, TIME_COL], inplace=True)

        n_ids  = df[ID_COL].nunique()
        t_min  = int(df[TIME_COL].min())
        t_max  = int(df[TIME_COL].max())
        NT     = len(df)

        log("\n--- Panel structure ---", f)
        log(f"  N (countries)  : {n_ids}", f)
        log(f"  Time span      : {t_min} – {t_max}", f)
        log(f"  NT (total obs) : {NT}", f)
        log(f"  NT / N         : {NT / n_ids:.1f}", f)

        dups = df.duplicated(subset=[ID_COL, TIME_COL]).sum()
        if dups > 0:
            log(f"  [WARNING] {dups} duplicate country×year rows found!", f)
        else:
            log("  No duplicates.", f)

        # Obs per country
        obs_per = df.groupby(ID_COL).size().sort_values(ascending=False)
        obs_per.to_frame("T").to_csv(
            os.path.join(TABLE_DIR, "t01a_obs_per_country.csv"))
        log(f"\n  T range: {obs_per.min()} – {obs_per.max()}", f)
        log(f"  Countries with T = {obs_per.max()}: "
            f"{(obs_per == obs_per.max()).sum()}", f)

    # ── 6. Missing values ─────────────────────────────────────────────────────
    miss = (df.isna().mean() * 100).round(2).reset_index()
    miss.columns = ["variable", "pct_missing"]
    miss.sort_values("pct_missing", ascending=False, inplace=True)
    miss.to_csv(os.path.join(TABLE_DIR, "t01b_missing_values.csv"), index=False)
    log("\n--- Missing values (%) for key variables ---", f)
    key_miss = miss[miss["variable"].isin(key_cols)]
    log(key_miss.to_string(index=False), f)

    # ── 7. Raw descriptive statistics ────────────────────────────────────────
    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    desc = df[num_cols].describe().T.round(4)
    desc.to_csv(os.path.join(TABLE_DIR, "t01c_raw_descriptives.csv"))
    log("\n--- Descriptive statistics (all numeric vars) ---", f)
    log(desc.to_string(), f)

    # ── 8. Paper Table 1 — means by country for Y and CB variables ───────────
    # Replicates: estpost tabstat bndgrn cbmnd cbenf cbsys if !missing(bndgrn),
    #             by(country1) statistics(mean)
    log("\n--- Paper Table 1: mean by country (observations with bndgrn) ---", f)
    tbl1_vars = [Y_COL] + CB_COLS
    tbl1_vars = [v for v in tbl1_vars if v in df.columns]
    tbl1_mask = df[Y_COL].notna() if Y_COL in df.columns else pd.Series(True, index=df.index)
    tbl1 = (df.loc[tbl1_mask.values, [ID_COL] + tbl1_vars]
              .groupby(ID_COL)[tbl1_vars]
              .mean()
              .round(4))
    tbl1.to_csv(os.path.join(TABLE_DIR, "t01d_means_by_country.csv"))
    log(tbl1.to_string(), f)

    # ── 9. Save renamed panel ─────────────────────────────────────────────────
    out_path = os.path.join(PROC_DIR, "panel_raw.csv")
    df.to_csv(out_path, index=False)
    log(f"\n[SAVED] {out_path}", f)

    f.close()
    print(f"\n[OK] Step 1 complete. Log: outputs/logs/01_load_explore.txt")
    return df


if __name__ == "__main__":
    load_and_explore()
