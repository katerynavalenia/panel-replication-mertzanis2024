# =============================================================================
# main_workflow.py
# Master script — runs all steps of the replication end-to-end.
# Paper: Mertzanis (2024), "Central bank policies and green bond issuance"
#        Energy Economics, 133, 107541
# =============================================================================
# Before running, install packages:
#   pip install pandas numpy matplotlib seaborn scipy statsmodels
#               linearmodels openpyxl
# Then:
#   python scripts/main_workflow.py
# =============================================================================

import os
import sys
import time
import importlib.util
import traceback

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from config import BASE_DIR, LOG_DIR, TABLE_DIR, FIG_DIR, PROC_DIR


# ─────────────────────────────────────────────────────────────────────────────
# Load a script module by filename (handles names starting with digits)
# ─────────────────────────────────────────────────────────────────────────────

def load_script(filename):
    path = os.path.join(SCRIPT_DIR, filename)
    spec = importlib.util.spec_from_file_location(filename, path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def banner(n, title):
    print(f"\n{'='*70}\n  STEP {n}: {title}\n{'='*70}")


def run_step(n, title, filename, func_name, skip=False):
    banner(n, title)
    if skip:
        print("[SKIPPED]")
        return "skipped"
    t0 = time.time()
    try:
        mod = load_script(filename)
        getattr(mod, func_name)()
        print(f"[DONE]  {title}  ({time.time()-t0:.1f}s)")
        return "ok"
    except Exception:
        print(f"\n[FAILED]  {title}")
        traceback.print_exc()
        return "failed"


# ─────────────────────────────────────────────────────────────────────────────
# Step list  (set skip=True for any step you want to bypass)
# ─────────────────────────────────────────────────────────────────────────────

STEPS = [
    # (step_num, title, filename, function_name, skip?)
    (1, "Load & explore raw data (rename columns)",
        "01_load_explore_data.py",     "load_and_explore",    False),
    (2, "Clean panel sample (>=3 consecutive obs of Y)",
        "02_clean_panel_sample.py",    "clean_panel_sample",  False),
    (3, "Panel transformations (Between, Within, TWFE, FD)",
        "03_panel_transformations.py", "compute_transforms",  False),
    (4, "Descriptive stats & plots (paper Tables 2-3)",
        "04_descriptive_statistics.py","run_descriptives",    False),
    (5, "Panel regressions (paper Tables 4, 5, 7 + homework)",
        "05_panel_estimations.py",     "run_estimations",     False),
    (6, "IV/2SLS & interactions (paper Tables 6, 9)",
        "05b_iv_interactions.py",      "run_iv_interactions", False),
    (7, "Dynamic panel - Anderson-Hsiao (optional)",
        "06_dynamic_panel.py",         "run_dynamic_panel",   False),
]


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "#" * 70)
    print("  PANEL DATA REPLICATION -- Mertzanis (2024)")
    print("  Energy Economics 133, 107541")
    print("  dep.var: bndgrn | key X: cbmnd, cbenf, cbsys")
    print("#" * 70)

    for d in [LOG_DIR, TABLE_DIR, FIG_DIR, PROC_DIR]:
        os.makedirs(d, exist_ok=True)

    t_start = time.time()
    report  = {}

    for step_num, title, fname, func_name, skip in STEPS:
        status = run_step(step_num, title, fname, func_name, skip=skip)
        report[f"Step {step_num}"] = status

    total = time.time() - t_start
    print("\n" + "=" * 70)
    print("  WORKFLOW SUMMARY")
    print("=" * 70)
    for step, status in report.items():
        icon = "OK" if status == "ok" else ("--" if status == "skipped" else "!!")
        print(f"  {icon}  {step}: {status}")
    print(f"\n  Total elapsed: {total:.1f}s")
    print("=" * 70)
    print(f"\n  Tables : {TABLE_DIR}")
    print(f"  Figures: {FIG_DIR}")
    print(f"  Logs   : {LOG_DIR}")
    print()


if __name__ == "__main__":
    main()
