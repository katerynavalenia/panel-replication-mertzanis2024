/*
================================================================================
  STATA TRANSLATION: Mertzanis (2024) Replication
  "Central bank policies and green bond issuance on a global scale"
  Energy Economics, 133, 107541

  Translated from Python using LLM assistance.
  Note: xtabond2 for GMM not attempted in Python version.
  Hausman-Taylor would require: xthtaylor bndgrn $xvar_tv $xvar_tv_endog ...

  KEY FINDING (preserved from Python analysis):
  cbmnd, cbenf, cbsys are ALL time-invariant (0% within variance).
  Entity FE and First-Difference estimators CANNOT identify their coefficients.
  Only Pooled OLS, Between, and Random Effects estimators capture their effects.
  This is not a bug — it reflects the data structure.

  Author note: Cluster-robust SEs are by country throughout (matching Python).
================================================================================
*/

clear all
set more off
capture log close
log using "replication_mertzanis2024.log", replace text

* ============================================================
* SECTION 0: PATHS AND GLOBALS
* ============================================================

* Adjust this path to your local data directory
global datadir "../data/raw"
global outdir  "."

* ============================================================
* SECTION 1: LOAD DATA
* ============================================================

* Python used pd.read_excel; Stata equivalent:
import excel using "$datadir/data.xlsx", sheet("Sheet1") firstrow clear

* Inspect raw variable names (Python renamed columns using a mapping dict)
describe
list in 1/5

* ============================================================
* SECTION 2: VARIABLE RENAMING
* (Python: df.rename(columns=rename_map))
* Key variables expected after rename:
*   bndgrn  = log total green bond issuance (dependent)
*   cbmnd   = CB mandate
*   cbenf   = CB enforcement
*   cbsys   = CB systemic risk
*   infl    = CPI inflation
*   rating  = Moody's rating
*   fie     = financial institutions efficiency
*   gdpg    = GDP growth
*   dum9    = EU27 dummy
*   dum12   = OECD dummy
*   hierarchy, openness, purity = cultural IV instruments
*   prodstr, bigtech, ngain     = interaction variables
*   x1l     = government bonds (robustness DV)
*   x2l     = corporate bonds (robustness DV)
* ============================================================

* If your Excel file uses different column names, rename here:
* rename OldName bndgrn
* rename OldCBMandate cbmnd
* (etc.)

* Confirm key variables exist
foreach v of varlist bndgrn cbmnd cbenf cbsys infl rating fie gdpg dum9 dum12 {
    capture confirm variable `v'
    if _rc != 0 {
        di as error "Variable `v' not found — check rename mapping."
    }
}

* ============================================================
* SECTION 3: DATA CLEANING AND ENCODING
* ============================================================

* country is a string in the raw data — must encode to numeric for xtset
encode country, gen(country_num)

* Ensure year is integer
destring year, replace force

* Sort panel
sort country_num year

* Label key variables
label variable bndgrn   "Log total green bond issuance"
label variable cbmnd    "CB mandate (time-invariant)"
label variable cbenf    "CB enforcement (time-invariant)"
label variable cbsys    "CB systemic risk (time-invariant)"
label variable infl     "CPI inflation"
label variable rating   "Moody's sovereign rating"
label variable fie      "Financial institutions efficiency"
label variable gdpg     "GDP growth"
label variable dum9     "EU27 member dummy"
label variable dum12    "OECD member dummy"

* ============================================================
* SECTION 4: SAMPLE SELECTION
* (Python: keep countries with >= 3 CONSECUTIVE non-missing Y obs)
* Translation note: Python used a custom rolling-window function.
* In Stata we replicate with a loop over countries.
* ============================================================

* Step 1: flag non-missing bndgrn obs
gen byte has_y = !missing(bndgrn)

* Step 2: within each country, find max run of consecutive has_y == 1
*         keep country if max consecutive run >= 3
bysort country_num (year): gen cons_run = 0
bysort country_num (year): replace cons_run = cond(has_y == 1, cons_run[_n-1] + 1, 0) if _n > 1
bysort country_num (year): replace cons_run = has_y if _n == 1

bysort country_num: egen max_consec = max(cons_run)

* Keep only countries with at least 3 consecutive observations
keep if max_consec >= 3
drop cons_run max_consec has_y

* Report sample
di "Countries remaining after sample selection:"
quietly levelsof country_num, local(nctries)
di "  N countries = `r(r)'"
di "  N obs = `=_N'"

* ============================================================
* SECTION 5: PANEL SETUP
* ============================================================

xtset country_num year
xtdescribe

* ============================================================
* SECTION 6: VARIANCE DECOMPOSITION
* (Python: computed within/between variance for each variable)
* This replicates the time-invariance check for CB variables.
* ============================================================

di "========================================================"
di "VARIANCE DECOMPOSITION (Within vs Between)"
di "KEY: cbmnd, cbenf, cbsys should show ~0% within variance"
di "========================================================"

foreach v of varlist cbmnd cbenf cbsys infl rating fie gdpg bndgrn {
    quietly xtsum `v'
    di "`v':  overall SD = `r(sd_o)', between SD = `r(sd_b)', within SD = `r(sd_w)'"
}

/*
NOTE: If cbmnd/cbenf/cbsys have within SD ≈ 0, FE and FD will drop them
or produce imprecise estimates. This is expected and matches the Python output.
*/

* ============================================================
* SECTION 7: DEFINE VARIABLE LISTS (globals)
* ============================================================

* Main controls
global xctrl "infl rating fie gdpg dum9 dum12"

* Full RHS for main tables (CB policy + controls)
global xvar  "cbmnd cbenf cbsys $xctrl"

* Time-varying and time-invariant splits (for Mundlak RE)
global xvar_tv    "infl rating fie gdpg"          // time-varying
global xvar_ti    "cbmnd cbenf cbsys dum9 dum12"  // time-invariant

* IV instruments
global ziv    "hierarchy purity openness"

* Additional controls for Table 7
global xtab7  "risk energy geopolitical"

* ============================================================
* SECTION 8: PANEL ESTIMATORS (Homework estimators)
* ============================================================

di ""
di "========================================================"
di "HOMEWORK ESTIMATORS"
di "========================================================"

* --- 8.1 BETWEEN ESTIMATOR ---
* (Python: xtreg with between='country')
* Between estimator regresses group means on group-mean RHS.
* Works for time-invariant variables.
di ""
di "--- Between Estimator ---"
xtreg bndgrn $xvar, be
estimates store est_between

* --- 8.2 ONE-WAY ENTITY FE (Within) ---
* WARNING: cbmnd, cbenf, cbsys are time-invariant → will be omitted by FE.
di ""
di "--- Within (Entity FE) Estimator ---"
di "NOTE: cbmnd/cbenf/cbsys time-invariant — FE cannot identify them (collinear with FE)."
xtreg bndgrn $xvar, fe
estimates store est_fe
* FE drops time-invariant regressors; their coefficients will be omitted or set to 0.

* --- 8.3 RANDOM EFFECTS with Mundlak Correction ---
* Mundlak (1978): augment RE with group means of time-varying X to partial out
* correlated effects, while still identifying time-invariant coefficients.
* Python: included mean_infl, mean_fie, mean_gdpg, mean_rating as extra regressors.
di ""
di "--- Random Effects with Mundlak Correction ---"

* Generate group means of time-varying controls
foreach v of varlist $xvar_tv {
    bysort country_num: egen mean_`v' = mean(`v')
}

global mundlak_means "mean_infl mean_rating mean_fie mean_gdpg"

xtreg bndgrn $xvar $mundlak_means, re vce(cluster country_num)
estimates store est_re_mundlak
/*
Translation note: Python used statsmodels BetweenOLS for between and a custom
Mundlak approach. Stata's xtreg, re directly supports RE; we add group means
manually to implement Mundlak. The re estimator uses GLS; Python used OLS on
demeaned data (Mundlak correction via included means).
*/

* --- 8.4 TWO-WAY FIXED EFFECTS (TWFE) ---
* WARNING: Time-invariant CB vars will again be dropped.
di ""
di "--- Two-Way Fixed Effects (Entity + Year FE) ---"
di "NOTE: cbmnd/cbenf/cbsys are time-invariant — TWFE cannot identify them."
xi: xtreg bndgrn $xvar i.year, fe vce(cluster country_num)
estimates store est_twfe
* Alternative: absorb(country_num year) with reghdfe if installed:
* reghdfe bndgrn $xvar, absorb(country_num year) cluster(country_num)

* --- 8.5 FIRST DIFFERENCES ---
* WARNING: Time-invariant variables difference out to 0 → dropped.
di ""
di "--- First Differences Estimator ---"
di "NOTE: cbmnd/cbenf/cbsys difference to zero — FD cannot identify them."

* Python computed first differences manually, then ran pooled OLS on them.
* In Stata, first-difference regression for a balanced panel:
reg D.(bndgrn $xvar), noconstant cluster(country_num)
estimates store est_fd
/*
Note: D.varname = first difference operator in Stata time-series.
The noconstant is standard for FD (the constant differences out).
Python: computed diff = df.groupby(country)[vars].diff().dropna(), then OLS.
*/

* ============================================================
* SECTION 9: PAPER TABLE 4 — POOLED OLS, +YEAR FE, +ENTITY FE, TWFE
* (Python: main regression table, cluster SE by country)
* ============================================================

di ""
di "========================================================"
di "TABLE 4: MAIN REGRESSIONS"
di "========================================================"

* Col 1: Pooled OLS
di "--- Table 4, Col 1: Pooled OLS ---"
reg bndgrn $xvar, cluster(country_num)
estimates store t4_col1

* Col 2: Pooled OLS + Year FE
di "--- Table 4, Col 2: Pooled OLS + Year FE ---"
xi: reg bndgrn $xvar i.year, cluster(country_num)
estimates store t4_col2

* Col 3: Entity FE (cbmnd/cbenf/cbsys dropped)
di "--- Table 4, Col 3: Entity FE ---"
di "NOTE: Time-invariant CB vars absorbed by entity FE."
xtreg bndgrn $xvar, fe vce(cluster country_num)
estimates store t4_col3

* Col 4: TWFE (cbmnd/cbenf/cbsys dropped)
di "--- Table 4, Col 4: TWFE ---"
xi: xtreg bndgrn $xvar i.year, fe vce(cluster country_num)
estimates store t4_col4

* Display all Table 4 estimates together
* (requires estout or esttab — install if needed: ssc install estout)
capture which esttab
if _rc == 0 {
    esttab t4_col1 t4_col2 t4_col3 t4_col4, ///
        b(3) se(3) star(* 0.10 ** 0.05 *** 0.01) ///
        title("Table 4: Main Regressions") ///
        mtitle("Pooled OLS" "+Year FE" "+Entity FE" "TWFE") ///
        note("Clustered SE by country. cbmnd/cbenf/cbsys dropped in FE/TWFE.")
} else {
    di "Install estout for formatted tables: ssc install estout"
    estimates table t4_col1 t4_col2 t4_col3 t4_col4, star stats(N r2)
}

* ============================================================
* SECTION 10: PAPER TABLE 5 — ROBUSTNESS CHECKS
* ============================================================

di ""
di "========================================================"
di "TABLE 5: ROBUSTNESS CHECKS"
di "========================================================"

* --- 10.1 Gov bonds DV (x1l) ---
di "--- Table 5: DV = Gov bonds (x1l) ---"
capture confirm variable x1l
if _rc == 0 {
    reg x1l $xvar, cluster(country_num)
    estimates store t5_gov
    xi: reg x1l $xvar i.year, cluster(country_num)
    estimates store t5_gov_yfe
} else {
    di "Variable x1l not found — skipping."
}

* --- 10.2 Corp bonds DV (x2l) ---
di "--- Table 5: DV = Corp bonds (x2l) ---"
capture confirm variable x2l
if _rc == 0 {
    reg x2l $xvar, cluster(country_num)
    estimates store t5_corp
    xi: reg x2l $xvar i.year, cluster(country_num)
    estimates store t5_corp_yfe
} else {
    di "Variable x2l not found — skipping."
}

* --- 10.3 Developed vs Developing split ---
* Python: split by GDP per capita or a pre-coded dummy
di "--- Table 5: Developed/Developing split ---"
* Assumption: a variable 'developed' (0/1) codes the split
capture confirm variable developed
if _rc == 0 {
    reg bndgrn $xvar if developed == 1, cluster(country_num)
    estimates store t5_dev
    reg bndgrn $xvar if developed == 0, cluster(country_num)
    estimates store t5_developing
} else {
    di "Variable 'developed' not found — adjust split variable name."
}

* --- 10.4 Ex-China ---
di "--- Table 5: Ex-China sample ---"
reg bndgrn $xvar if country != "China", cluster(country_num)
estimates store t5_exchina

* --- 10.5 Nonlinear CB terms (quadratic) ---
di "--- Table 5: Nonlinear (quadratic) CB terms ---"
gen cbmnd_sq = cbmnd^2
gen cbenf_sq = cbenf^2
gen cbsys_sq = cbsys^2

reg bndgrn cbmnd cbmnd_sq cbenf cbenf_sq cbsys cbsys_sq $xctrl, cluster(country_num)
estimates store t5_nonlin
/*
Note: Python tested nonlinearity with squared terms and a Ramsey RESET test.
Stata RESET test: ovtest after regress.
*/
quietly reg bndgrn $xvar, cluster(country_num)
ovtest

* ============================================================
* SECTION 11: TABLE 7 — ADDITIONAL CONTROLS
* (Python: added risk, energy, geopolitical risk indices)
* ============================================================

di ""
di "========================================================"
di "TABLE 7: ADDITIONAL CONTROLS"
di "========================================================"

* Check if Table 7 controls are available
foreach v of varlist $xtab7 {
    capture confirm variable `v'
    if _rc != 0 di "WARNING: `v' not found for Table 7."
}

reg bndgrn $xvar $xtab7, cluster(country_num)
estimates store t7_col1

xi: reg bndgrn $xvar $xtab7 i.year, cluster(country_num)
estimates store t7_col2

xtreg bndgrn $xvar $xtab7, fe vce(cluster country_num)
estimates store t7_col3

xi: xtreg bndgrn $xvar $xtab7 i.year, fe vce(cluster country_num)
estimates store t7_col4

capture which esttab
if _rc == 0 {
    esttab t7_col1 t7_col2 t7_col3 t7_col4, ///
        b(3) se(3) star(* 0.10 ** 0.05 *** 0.01) ///
        title("Table 7: Additional Controls") ///
        mtitle("Pooled OLS" "+Year FE" "+Entity FE" "TWFE")
}

* ============================================================
* SECTION 12: IV / 2SLS
* (Python: ivreg2 / linearmodels IV2SLS, one CB var instrumented at a time)
* Cultural instruments: hierarchy, purity, openness
* NOTE: Since CB vars are time-invariant, IV should be estimated in pooled OLS
*       (not FE), because FE would absorb the endogenous variable.
* ============================================================

di ""
di "========================================================"
di "IV / 2SLS ESTIMATES"
di "========================================================"

* Check ivreg2 is installed (ssc install ivreg2)
capture which ivreg2
if _rc != 0 {
    di "ivreg2 not installed. Install: ssc install ivreg2"
    di "Falling back to ivregress 2sls"
}

* --- IV for cbmnd ---
di "--- IV: cbmnd instrumented by hierarchy purity openness ---"
capture ivreg2 bndgrn (cbmnd = hierarchy purity openness) cbenf cbsys $xctrl, ///
    cluster(country_num) first
if _rc != 0 {
    ivregress 2sls bndgrn (cbmnd = hierarchy purity openness) cbenf cbsys $xctrl, ///
        vce(cluster country_num) first
}
estimates store iv_cbmnd

* --- IV for cbenf ---
di "--- IV: cbenf instrumented by hierarchy purity openness ---"
capture ivreg2 bndgrn cbmnd (cbenf = hierarchy purity openness) cbsys $xctrl, ///
    cluster(country_num) first
if _rc != 0 {
    ivregress 2sls bndgrn cbmnd (cbenf = hierarchy purity openness) cbsys $xctrl, ///
        vce(cluster country_num) first
}
estimates store iv_cbenf

* --- IV for cbsys ---
di "--- IV: cbsys instrumented by hierarchy purity openness ---"
capture ivreg2 bndgrn cbmnd cbenf (cbsys = hierarchy purity openness) $xctrl, ///
    cluster(country_num) first
if _rc != 0 {
    ivregress 2sls bndgrn cbmnd cbenf (cbsys = hierarchy purity openness) $xctrl, ///
        vce(cluster country_num) first
}
estimates store iv_cbsys

/*
Translation note: Python used linearmodels.IV2SLS with clustered SE.
Stata's ivreg2 (Baum, Schaffer, Stillman) is more flexible; ivregress is base Stata.
For weak instrument tests, ivreg2 reports Kleibergen-Paap and Cragg-Donald stats
automatically with the `first` option.
*/

* ============================================================
* SECTION 13: INTERACTION TERMS
* (Python: cbenf × prodstr, cbenf × bigtech, cbenf × ngain)
* ============================================================

di ""
di "========================================================"
di "INTERACTION TERMS"
di "========================================================"

* Generate interaction variables
gen cbenf_prodstr = cbenf * prodstr
gen cbenf_bigtech = cbenf * bigtech
gen cbenf_ngain   = cbenf * ngain

label variable cbenf_prodstr "cbenf × prodstr"
label variable cbenf_bigtech "cbenf × bigtech"
label variable cbenf_ngain   "cbenf × ngain"

* --- Interaction: cbenf × prodstr ---
di "--- Interaction: cbenf × prodstr ---"
reg bndgrn cbmnd cbenf cbsys prodstr cbenf_prodstr $xctrl, cluster(country_num)
estimates store int_prodstr

* --- Interaction: cbenf × bigtech ---
di "--- Interaction: cbenf × bigtech ---"
reg bndgrn cbmnd cbenf cbsys bigtech cbenf_bigtech $xctrl, cluster(country_num)
estimates store int_bigtech

* --- Interaction: cbenf × ngain ---
di "--- Interaction: cbenf × ngain ---"
reg bndgrn cbmnd cbenf cbsys ngain cbenf_ngain $xctrl, cluster(country_num)
estimates store int_ngain

/*
Note: Python used c_() in statsmodels for interactions.
Stata: generate cross-product manually or use ## syntax in regress:
    reg bndgrn cbmnd c.cbenf##c.prodstr cbsys $xctrl, cluster(country_num)
The ## syntax automatically includes main effects + interaction.
*/

* Using Stata's ## syntax as alternative
di "--- Interaction (## syntax): cbenf × prodstr ---"
reg bndgrn cbmnd c.cbenf##c.prodstr cbsys $xctrl, cluster(country_num)

* ============================================================
* SECTION 14: DYNAMIC PANEL — Anderson-Hsiao
* (Python: custom Anderson-Hsiao implementation — lagged Y and lagged X as IVs)
* ============================================================

di ""
di "========================================================"
di "DYNAMIC PANEL: Anderson-Hsiao"
di "========================================================"

/*
Anderson-Hsiao (1982) approach:
1. Take first differences to remove fixed effects
2. Instrument Δy(t-1) with y(t-2) [level] or Δy(t-2) [difference]
   and ΔX(t) with X(t-1) or ΔX(t-1)
3. Estimate via IV/2SLS

Python: manually constructed lagged differences.
Stata note: xtabond2 (Roodman 2009) provides full Arellano-Bond GMM,
which is more efficient but NOT attempted in the Python version.
Anderson-Hsiao is a simpler IV version.
*/

* Generate lags and differences needed for AH
sort country_num year
bysort country_num: gen L1_bndgrn   = bndgrn[_n-1]
bysort country_num: gen L2_bndgrn   = bndgrn[_n-2]
bysort country_num: gen D_bndgrn    = bndgrn - L1_bndgrn
bysort country_num: gen D_L1_bndgrn = L1_bndgrn - L2_bndgrn

* Differenced controls
foreach v of varlist $xctrl {
    bysort country_num: gen L1_`v' = `v'[_n-1]
    bysort country_num: gen D_`v'  = `v' - L1_`v'
}

* CB vars are time-invariant → their differences = 0; use levels as instruments
* AH IV regression: D_bndgrn on D(X), with L2_bndgrn as IV for D_L1_bndgrn

di "Anderson-Hsiao: ΔY on Δcontrols, IV for ΔY(t-1) = Y(t-2)"
ivregress 2sls D_bndgrn ///
    (D_L1_bndgrn = L2_bndgrn) ///
    D_infl D_rating D_fie D_gdpg ///
    if !missing(D_bndgrn, D_L1_bndgrn, L2_bndgrn), ///
    vce(cluster country_num)
estimates store est_ah

/*
IMPORTANT: Since cbmnd/cbenf/cbsys are time-invariant, their first differences
equal zero for all observations. They are therefore excluded from the FD equation.
This means the dynamic panel (Anderson-Hsiao) cannot estimate CB policy effects.
Only pooled OLS / between / RE can do so for these variables.

For full Arellano-Bond GMM, use:
    xtabond2 bndgrn L.bndgrn $xctrl, gmm(L.bndgrn) iv($xctrl) twostep robust
(Requires: ssc install xtabond2)
*/

* ============================================================
* SECTION 15: DIAGNOSTIC TESTS
* ============================================================

di ""
di "========================================================"
di "DIAGNOSTIC TESTS"
di "========================================================"

* Hausman test: FE vs RE (note: not very informative here since CB vars
* are time-invariant and FE drops them)
di "--- Hausman Test (FE vs RE) ---"
quietly xtreg bndgrn $xctrl, fe
estimates store hausman_fe
quietly xtreg bndgrn $xctrl, re
estimates store hausman_re
hausman hausman_fe hausman_re
/*
Note: Hausman test only uses time-varying controls here because
FE cannot accommodate time-invariant CB variables.
If you want to test endogeneity including CB vars, use Mundlak RE approach.
*/

* Cross-sectional dependence test (Pesaran 2004)
capture xtcd bndgrn
if _rc == 0 {
    di "Pesaran CD test completed."
} else {
    di "xtcd not available. Install: ssc install xtcd2"
}

* Wooldridge test for autocorrelation in panels
capture xtserial bndgrn $xvar
if _rc == 0 {
    di "Wooldridge serial correlation test completed."
} else {
    di "xtserial not available. Install: ssc install xtserial"
}

* ============================================================
* SECTION 16: EXPORT RESULTS
* ============================================================

di ""
di "========================================================"
di "EXPORT RESULTS"
di "========================================================"

* Export main Table 4 to .rtf (if estout installed)
capture which esttab
if _rc == 0 {
    esttab t4_col1 t4_col2 t4_col3 t4_col4 using "table4.rtf", ///
        replace b(3) se(3) star(* 0.10 ** 0.05 *** 0.01) ///
        title("Table 4: Main Regressions") ///
        note("Clustered SE by country. *p<0.10 **p<0.05 ***p<0.01")

    esttab iv_cbmnd iv_cbenf iv_cbsys using "table_iv.rtf", ///
        replace b(3) se(3) star(* 0.10 ** 0.05 *** 0.01) ///
        title("IV/2SLS Estimates")

    esttab int_prodstr int_bigtech int_ngain using "table_interactions.rtf", ///
        replace b(3) se(3) star(* 0.10 ** 0.05 *** 0.01) ///
        title("Interaction Terms")
}

log close

di ""
di "========================================================"
di "REPLICATION COMPLETE"
di "Mertzanis (2024) — Stata Translation"
di "========================================================"

/*
================================================================================
TRANSLATION NOTES (Python → Stata):
--------------------------------------------------------------------------------
1. Sample selection: Python used a vectorized pandas function to find max
   consecutive non-missing runs. Stata replicates this with a cumulative
   run-length counter in a bysort loop. Results should match exactly.

2. Clustered SE: Python used `cov_type='clustered', cov_kwds={'groups': country}`
   in statsmodels. Stata uses `vce(cluster country_num)` or `cluster(country_num)`.

3. Between estimator: Python used statsmodels BetweenOLS. Stata `xtreg, be`
   is equivalent (regress group means on group-mean RHS).

4. Mundlak RE: Python added group means as extra regressors in OLS.
   Stata replicates by adding bysort-mean variables to `xtreg, re`.

5. First differences: Python used .diff() on grouped data, then OLS.
   Stata uses `reg D.(varlist)` with time-series operators, equivalent.

6. TWFE: Python used entity + time dummies in OLS. Stata uses `xtreg, fe`
   with absorbed entity FE plus explicit time dummies via `xi: i.year`.
   For large panels, `reghdfe` (ssc install reghdfe) is more efficient.

7. IV/2SLS: Python used linearmodels.IV2SLS. Stata's ivreg2 or ivregress
   are equivalent; ivreg2 provides more diagnostic tests (Kleibergen-Paap).

8. Anderson-Hsiao: Python implemented manually. Stata replicates via
   ivregress 2sls on differenced data. xtabond2 provides more complete GMM.

9. Time-invariant CB variables: This is the central econometric challenge.
   cbmnd, cbenf, cbsys show 0% within variance. FE and FD cannot estimate
   their coefficients. The paper's main results rely on pooled OLS and
   between/RE estimators for these variables.
================================================================================
*/
