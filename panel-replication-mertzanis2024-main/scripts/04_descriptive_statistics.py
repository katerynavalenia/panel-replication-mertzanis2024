# =============================================================================
# 04_descriptive_statistics.py
# Step 4 — All descriptive statistics, distribution plots, and correlation
#          matrices for all four panel transformations.
#          Also produces paper Tables 2 and 3.
# =============================================================================
# Paper Table 2: estpost summarize bndgrn $xvar, listwise detail
# Paper Table 3: estpost correlate bndgrn $xvar, matrix  +  VIF
# =============================================================================
# Run:  python scripts/04_descriptive_statistics.py
# Input:  data/processed/panel_transforms.csv
# Output: outputs/tables/t04a_*.csv,  outputs/figures/fig02_*.png – fig09_*.png
# =============================================================================

import os
import sys
import warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (PROC_DIR, TABLE_DIR, FIG_DIR, LOG_DIR,
                    ID_COL, TIME_COL, Y_COL, X_COL, CB_COLS, CONTROL_COLS,
                    XVAR_COLS, FIG_DPI, FIG_FORMAT)

warnings.filterwarnings("ignore")
plt.rcParams["figure.dpi"] = FIG_DPI
PALETTE = "#4C8BE2"


def log(msg, f=None):
    print(msg)
    if f:
        f.write(msg + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# Plotting helpers
# ─────────────────────────────────────────────────────────────────────────────

def plot_dist(series, title, save_path):
    """Histogram + KDE + fitted normal."""
    s = series.dropna()
    if len(s) < 5:
        return
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(s, bins=30, density=True, alpha=0.4, color=PALETTE,
            label="Histogram", edgecolor="white")
    kde_xs = np.linspace(s.min(), s.max(), 300)
    try:
        kde = stats.gaussian_kde(s)
        ax.plot(kde_xs, kde(kde_xs), color="#E25C4C", lw=2, label="KDE")
    except Exception:
        pass
    mu, sigma = s.mean(), s.std()
    ax.plot(kde_xs, stats.norm.pdf(kde_xs, mu, sigma),
            color="#2CA02C", lw=2, linestyle="--",
            label=f"Normal(μ={mu:.2f}, σ={sigma:.2f})")
    sk = stats.skew(s)
    ku = stats.kurtosis(s)
    ax.set_title(f"{title}\nskewness={sk:.2f}, excess kurtosis={ku:.2f}")
    ax.set_ylabel("Density")
    ax.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(save_path, dpi=FIG_DPI)
    plt.close()


def plot_bivariate(x, y, xlabel, ylabel, title, save_path):
    """Scatter + regression line + marginal KDE."""
    mask  = x.notna() & y.notna()
    xs, ys = x[mask].values, y[mask].values
    if len(xs) < 5:
        return
    if np.std(xs) == 0 or np.std(ys) == 0:
        return
    r, p  = stats.pearsonr(xs, ys)
    fig   = plt.figure(figsize=(8, 7))
    gs    = gridspec.GridSpec(4, 4, figure=fig)
    ax_main  = fig.add_subplot(gs[1:, :-1])
    ax_top   = fig.add_subplot(gs[0, :-1], sharex=ax_main)
    ax_right = fig.add_subplot(gs[1:, -1],  sharey=ax_main)
    ax_main.scatter(xs, ys, alpha=0.4, s=18, color=PALETTE)
    try:
        m, b = np.polyfit(xs, ys, 1)
    except Exception:
        plt.close(); return
    xlim = np.array([xs.min(), xs.max()])
    ax_main.plot(xlim, m*xlim + b, color="#E25C4C", lw=1.5,
                 label=f"r={r:.3f}  p={p:.3f}")
    ax_main.set_xlabel(xlabel)
    ax_main.set_ylabel(ylabel)
    ax_main.legend(fontsize=8)
    kde_x = stats.gaussian_kde(xs)
    xs_l  = np.linspace(xs.min(), xs.max(), 200)
    ax_top.plot(xs_l, kde_x(xs_l), color=PALETTE)
    ax_top.fill_between(xs_l, kde_x(xs_l), alpha=0.3, color=PALETTE)
    ax_top.axis("off")
    kde_y = stats.gaussian_kde(ys)
    ys_l  = np.linspace(ys.min(), ys.max(), 200)
    ax_right.plot(kde_y(ys_l), ys_l, color=PALETTE)
    ax_right.fill_betweenx(ys_l, kde_y(ys_l), alpha=0.3, color=PALETTE)
    ax_right.axis("off")
    fig.suptitle(title, fontsize=11)
    plt.tight_layout()
    plt.savefig(save_path, dpi=FIG_DPI)
    plt.close()


def plot_bivariate_fits(x, y, xlabel, ylabel, title, save_path):
    """Scatter with linear, quadratic, and LOWESS fits."""
    from statsmodels.nonparametric.smoothers_lowess import lowess
    mask = x.notna() & y.notna()
    xs, ys = x[mask].values, y[mask].values
    if len(xs) < 5:
        return
    if np.std(xs) == 0 or np.std(ys) == 0:
        return
    idx = np.argsort(xs)
    xs, ys = xs[idx], ys[idx]
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(xs, ys, alpha=0.35, s=18, color=PALETTE, label="Data")
    m, b = np.polyfit(xs, ys, 1)
    ax.plot(xs, m*xs + b, color="#E25C4C", lw=1.5, label="Linear")
    p2 = np.polyfit(xs, ys, 2)
    ax.plot(xs, np.polyval(p2, xs), color="#2CA02C", lw=1.5,
            linestyle="--", label="Quadratic")
    low = lowess(ys, xs, frac=0.4)
    ax.plot(low[:, 0], low[:, 1], color="#FF7F0E", lw=1.5,
            linestyle=":", label="LOWESS")
    r, _ = stats.pearsonr(xs, ys)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(f"{title}  (r={r:.3f})")
    ax.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(save_path, dpi=FIG_DPI)
    plt.close()


def plot_boxplots_by_country(series, country, title, save_path, max_countries=50):
    """Boxplots ordered by variance, smallest to largest."""
    data = pd.DataFrame({"val": series, "country": country}).dropna()
    if data.empty:
        return
    var_order = (data.groupby("country")["val"]
                     .var().sort_values().index.tolist())
    if len(var_order) > max_countries:
        step = max(1, len(var_order) // max_countries)
        var_order = var_order[::step][:max_countries]
    fig, ax = plt.subplots(figsize=(max(10, len(var_order) * 0.35), 5))
    data_f = data[data["country"].isin(var_order)].copy()
    data_f["country"] = pd.Categorical(data_f["country"],
                                        categories=var_order, ordered=True)
    data_f.sort_values("country", inplace=True)
    groups = [g["val"].dropna().values
              for _, g in data_f.groupby("country", observed=True)]
    ax.boxplot(groups, labels=var_order, vert=True)
    ax.set_xticklabels(var_order, rotation=90, fontsize=7)
    ax.set_ylabel("Value")
    ax.set_title(title)
    plt.tight_layout()
    plt.savefig(save_path, dpi=FIG_DPI)
    plt.close()


def univariate_stats(series, name):
    s = series.dropna()
    if len(s) == 0:
        return {}
    mu, sigma = s.mean(), s.std()
    return {
        "variable"  : name,
        "N"         : len(s),
        "mean"      : round(mu, 5),
        "p50_median": round(s.median(), 5),
        "sd"        : round(sigma, 5),
        "min_std"   : round((s.min()-mu)/sigma, 3) if sigma > 0 else np.nan,
        "p25"       : round(s.quantile(0.25), 5),
        "p75"       : round(s.quantile(0.75), 5),
        "max_std"   : round((s.max()-mu)/sigma, 3) if sigma > 0 else np.nan,
        "skewness"  : round(stats.skew(s), 4),
        "kurtosis"  : round(stats.kurtosis(s), 4),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Paper Table 2: summary statistics, listwise (regression sample)
# Replicates: estpost summarize bndgrn $xvar, listwise detail
# ─────────────────────────────────────────────────────────────────────────────

def paper_table2(df, logfile):
    """Summary statistics on the regression sample (all xvar non-missing)."""
    log("\n--- PAPER TABLE 2: Summary statistics (listwise = regression sample) ---",
        logfile)
    reg_vars = [Y_COL] + [v for v in XVAR_COLS if v in df.columns]
    sample   = df[reg_vars].dropna()
    log(f"  Listwise N = {len(sample)}", logfile)

    rows = []
    for v in reg_vars:
        s = sample[v]
        rows.append({
            "variable": v,
            "N"       : len(s),
            "mean"    : round(s.mean(), 4),
            "sd"      : round(s.std(), 4),
            "min"     : round(s.min(), 4),
            "p25"     : round(s.quantile(0.25), 4),
            "p50"     : round(s.median(), 4),
            "p75"     : round(s.quantile(0.75), 4),
            "max"     : round(s.max(), 4),
            "skewness": round(stats.skew(s), 4),
            "kurtosis": round(stats.kurtosis(s), 4),
        })
    tbl2 = pd.DataFrame(rows)
    tbl2.to_csv(os.path.join(TABLE_DIR, "t04_paper_table2_summary_stats.csv"),
                index=False)
    log(tbl2.to_string(index=False), logfile)
    return tbl2


# ─────────────────────────────────────────────────────────────────────────────
# Paper Table 3: correlation matrix + VIF
# Replicates: estpost correlate bndgrn $xvar, matrix
#             collin bndgrn $xvar if !missing(bndgrn), corr
# ─────────────────────────────────────────────────────────────────────────────

def paper_table3(df, logfile):
    """Correlation matrix and VIF for the regression sample."""
    log("\n--- PAPER TABLE 3: Correlation matrix and VIF ---", logfile)
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    import statsmodels.api as sm

    reg_vars = [Y_COL] + [v for v in XVAR_COLS if v in df.columns]
    sample   = df[reg_vars].dropna()

    # Correlation matrix
    corr = sample.corr(method="pearson").round(4)
    corr.to_csv(os.path.join(TABLE_DIR, "t04_paper_table3a_corr_matrix.csv"))
    log("\nCorrelation matrix:", logfile)
    log(corr.to_string(), logfile)

    # Correlation heatmap
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm",
                center=0, linewidths=0.4, ax=ax, annot_kws={"size": 7})
    ax.set_title("Correlation Matrix — Regression Sample (Paper Table 3)")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, f"fig02_corr_matrix_paper.{FIG_FORMAT}"),
                dpi=FIG_DPI)
    plt.close()

    # VIF (on X variables only, not Y)
    x_vars = [v for v in XVAR_COLS if v in sample.columns]
    X_vif  = sm.add_constant(sample[x_vars].astype(float))
    vif_rows = []
    for i, col in enumerate(X_vif.columns):
        if col == "const":
            continue
        vif_val = variance_inflation_factor(X_vif.values, i)
        vif_rows.append({"variable": col, "VIF": round(vif_val, 3)})
    vif_df = pd.DataFrame(vif_rows).sort_values("VIF", ascending=False)
    vif_df.to_csv(os.path.join(TABLE_DIR, "t04_paper_table3b_vif.csv"),
                  index=False)
    log("\nVIF (mean VIF and individual):", logfile)
    log(f"  Mean VIF = {vif_df['VIF'].mean():.3f}", logfile)
    log(vif_df.to_string(index=False), logfile)
    if vif_df["VIF"].max() > 10:
        log("  [WARNING] Max VIF > 10: potential multicollinearity.", logfile)

    return corr, vif_df


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def run_descriptives():
    os.makedirs(TABLE_DIR, exist_ok=True)
    os.makedirs(FIG_DIR,   exist_ok=True)
    os.makedirs(LOG_DIR,   exist_ok=True)

    df = pd.read_csv(os.path.join(PROC_DIR, "panel_transforms.csv"))
    df[TIME_COL] = pd.to_numeric(df[TIME_COL], errors="coerce")

    f = open(os.path.join(LOG_DIR, "04_descriptives.txt"), "w")
    log("=" * 70, f)
    log("STEP 4 — DESCRIPTIVE STATISTICS AND PLOTS", f)
    log("=" * 70, f)

    # Variables to transform/plot
    all_vars = [Y_COL] + CB_COLS + [c for c in CONTROL_COLS if c in df.columns]
    transforms = {"bet": "Between", "wi": "One-Way Within",
                  "twfe": "TWFE", "fd": "First Diff"}

    # ── A. Paper Tables 2 & 3 ─────────────────────────────────────────────────
    paper_table2(df, f)
    paper_table3(df, f)

    # ── B. Univariate stats for all 4 transformations ─────────────────────────
    log("\n--- B. Univariate stats (all 4 transformations) ---", f)
    stat_rows = []
    for suffix, label in transforms.items():
        for v in all_vars:
            col = f"{v}_{suffix}"
            if col in df.columns:
                row = univariate_stats(df[col], f"{v} [{label}]")
                stat_rows.append(row)
    stat_df = pd.DataFrame(stat_rows)
    stat_df.to_csv(os.path.join(TABLE_DIR, "t04a_univariate_all_transforms.csv"),
                   index=False)
    log(stat_df.to_string(index=False), f)

    # ── C. Distribution plots: Y and each CB variable (all 4 transforms) ─────
    log("\n--- C. Distribution plots ---", f)
    for v in [Y_COL] + CB_COLS:
        for suffix, label in transforms.items():
            col = f"{v}_{suffix}"
            if col not in df.columns:
                continue
            fname = f"fig03_{v}_{suffix}_dist.{FIG_FORMAT}"
            plot_dist(df[col], f"{v} — {label}", os.path.join(FIG_DIR, fname))
            log(f"  [SAVED] {fname}", f)

    # ── D. Bivariate scatter: Y vs cbmnd for each transform ──────────────────
    log("\n--- D. Bivariate Y vs cbmnd ---", f)
    for suffix, label in transforms.items():
        y_col = f"{Y_COL}_{suffix}"
        x_col = f"{X_COL}_{suffix}"
        if y_col not in df.columns or x_col not in df.columns:
            continue
        fname = f"fig04_bivariate_{suffix}.{FIG_FORMAT}"
        plot_bivariate(df[x_col], df[y_col],
                       xlabel=f"cbmnd [{label}]",
                       ylabel=f"bndgrn [{label}]",
                       title=f"bndgrn vs cbmnd — {label}",
                       save_path=os.path.join(FIG_DIR, fname))
        log(f"  [SAVED] {fname}", f)

    # ── E. Multi-fit plots (linear, quadratic, LOWESS) ────────────────────────
    log("\n--- E. Multi-fit bivariate plots ---", f)
    for suffix, label in transforms.items():
        y_col = f"{Y_COL}_{suffix}"
        x_col = f"{X_COL}_{suffix}"
        if y_col not in df.columns or x_col not in df.columns:
            continue
        fname = f"fig05_multfit_{suffix}.{FIG_FORMAT}"
        plot_bivariate_fits(df[x_col], df[y_col],
                            xlabel=f"cbmnd [{label}]",
                            ylabel=f"bndgrn [{label}]",
                            title=f"bndgrn vs cbmnd — {label} (multi-fit)",
                            save_path=os.path.join(FIG_DIR, fname))
        log(f"  [SAVED] {fname}", f)

    # ── F. Boxplots by country (TWFE and FD) ─────────────────────────────────
    log("\n--- F. Boxplots by country ---", f)
    for suffix, label in [("twfe", "TWFE"), ("fd", "First Diff")]:
        col = f"{Y_COL}_{suffix}"
        if col not in df.columns:
            continue
        fname = f"fig06_boxplot_{suffix}_bndgrn.{FIG_FORMAT}"
        plot_boxplots_by_country(df[col], df[ID_COL],
                                  title=f"bndgrn [{label}] — Boxplot by Country",
                                  save_path=os.path.join(FIG_DIR, fname))
        log(f"  [SAVED] {fname}", f)

    # ── G. Correlation matrices for all 4 transforms ─────────────────────────
    log("\n--- G. Correlation matrices (all transformations) ---", f)
    for suffix, label in transforms.items():
        cols = [f"{v}_{suffix}" for v in all_vars if f"{v}_{suffix}" in df.columns]
        if len(cols) < 2:
            continue
        corr_mat = df[cols].corr(method="pearson").round(4)
        clean    = {c: c.replace(f"_{suffix}", "") for c in cols}
        corr_mat.rename(index=clean, columns=clean, inplace=True)
        corr_mat.to_csv(
            os.path.join(TABLE_DIR, f"t04b_corr_{suffix}.csv"))
        fig, ax = plt.subplots(figsize=(max(6, len(cols)), max(5, len(cols))))
        sns.heatmap(corr_mat, annot=True, fmt=".2f", cmap="coolwarm",
                    center=0, linewidths=0.4, ax=ax, annot_kws={"size": 7})
        ax.set_title(f"Correlation Matrix — {label}")
        plt.tight_layout()
        fname = f"fig07_corr_{suffix}.{FIG_FORMAT}"
        plt.savefig(os.path.join(FIG_DIR, fname), dpi=FIG_DPI)
        plt.close()
        log(f"  [SAVED] {fname}", f)

    # ── H. Heterogeneity by country: r(Y,X) for TWFE and FD ─────────────────
    log("\n--- H. Heterogeneity by country (r sorted) ---", f)
    for suffix, label in [("twfe", "TWFE"), ("fd", "First Diff")]:
        y_col = f"{Y_COL}_{suffix}"
        x_col = f"{X_COL}_{suffix}"
        if y_col not in df.columns or x_col not in df.columns:
            continue
        rows_het = []
        for cid, grp in df.groupby(ID_COL):
            sub = grp[[y_col, x_col]].dropna()
            if len(sub) < 3:
                continue
            r_val, _ = stats.pearsonr(sub[y_col], sub[x_col])
            sy = sub[y_col].std()
            sx = sub[x_col].std()
            rows_het.append({
                "country"    : cid,
                "T_i"        : len(sub),
                "r(bndgrn,cbmnd)": round(r_val, 4),
                "sigma_Y"    : round(sy, 5),
                "sigma_X"    : round(sx, 5),
                "sigma_Y/X"  : round(sy/sx, 4) if sx > 0 else np.nan,
                "beta"       : round(r_val*sy/sx, 5) if sx > 0 else np.nan,
            })
        het_df = pd.DataFrame(rows_het).sort_values("r(bndgrn,cbmnd)",
                                                     ascending=False)
        het_df.to_csv(
            os.path.join(TABLE_DIR, f"t04c_heterogeneity_{suffix}.csv"),
            index=False)
        log(f"\n  [{label}] heterogeneity (top/bottom 10):", f)
        log(pd.concat([het_df.head(10), het_df.tail(10)]).to_string(index=False), f)

    # ── I. First-difference sanity check ─────────────────────────────────────
    log("\n--- I. First-difference check (first 30 obs) ---", f)
    fd_show = [ID_COL, TIME_COL] + [f"{v}_fd" for v in [Y_COL, X_COL]
                                      if f"{v}_fd" in df.columns]
    log(df[fd_show].head(30).to_string(), f)

    f.close()
    print(f"\n[OK] Step 4 complete. Log: outputs/logs/04_descriptives.txt")


if __name__ == "__main__":
    run_descriptives()
