# =============================================================================
# config.py  —  Central configuration for the replication project
# Paper: Mertzanis (2024), "Central bank policies and green bond issuance"
#        Energy Economics, 133, 107541
# Data:  Mendeley doi:10.17632/xb2m4m8h24.1  →  data/raw/data.xlsx
# =============================================================================

import os

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR   = os.path.join(BASE_DIR, "data", "raw")
PROC_DIR  = os.path.join(BASE_DIR, "data", "processed")
TABLE_DIR = os.path.join(BASE_DIR, "outputs", "tables")
FIG_DIR   = os.path.join(BASE_DIR, "outputs", "figures")
LOG_DIR   = os.path.join(BASE_DIR, "outputs", "logs")

# ── Raw data file ─────────────────────────────────────────────────────────────
RAW_FILE = "data.xlsx"

# ── Column rename map: Excel long header → short Stata-style name ─────────────
# All scripts work with the short names after 01_load_explore_data.py renames.
RENAME_MAP = {
    "country"                                                              : "country",
    "country-numeric"                                                      : "country_num",
    "year"                                                                 : "year",
    "iso3"                                                                 : "iso3",
    "income level, 2-levels"                                               : "devlev2",
    "1 if country=China, 0 otherwise"                                      : "china",
    "log value of total green bond issuance value"                         : "bndgrn",
    "log value of government green bond issuance value"                    : "x1l",
    "log value of corporate green bond issuance value"                     : "x2l",
    "Environmental Taxes (%GDP)"                                           : "envtax",
    "GDP growth (annual %) [NY.GDP.MKTP.KD.ZG]"                           : "gdpg",
    "bitech finance as a percent of GDP"                                   : "bigtech",
    "Notre Dame-Global Adaptation Index to climate disruptions"            : "ngain",
    "Moody's rating, numeric 4-1"                                          : "rating",
    "Total equity risk premium, Damodaran"                                 : "riskeqt",
    "Country risk premium, Damodaran"                                      : "riskctr",
    "1 if member of EU27"                                                  : "dum9",
    "1 if member of OECD"                                                  : "dum12",
    "IMF: financial institutions efficiency"                               : "fie",
    "square value of CB mandate"                                           : "cbmndsq",
    "CB mandate - rowtotal"                                                : "cbmnd",
    "square value of CB enforcement"                                       : "cbenfsq",
    "CB enforcement - rowtotal"                                            : "cbenf",
    "square value of CB control of syst risk tools"                        : "cbsyssq",
    "CB control sys risk tool - rowtotal"                                  : "cbsys",
    "world uncertainty index"                                              : "wui",
    "log of geopolitical risk index"                                       : "gprlog",
    "Official Core Consumer Price Inflation, IMF"                          : "infl",
    "Share of primary energy consumption that comes from oil"              : "enrgoil",
    "1st principal component of value added: agriculture, manufacuring, industry, ser": "prodstr",
    "Heirarchy-Schwartz-2007"                                              : "hierarchy",
    "Openness-Schmitt et al.-2007"                                         : "openness",
    "Purity-Atari et al.-2020"                                             : "purity",
}

# ── Panel identifiers ─────────────────────────────────────────────────────────
ID_COL    = "country"      # string country identifier
TIME_COL  = "year"         # integer year
CLUST_COL = "country_num"  # numeric country code for clustering

# ── Dependent variables ───────────────────────────────────────────────────────
Y_COL      = "bndgrn"   # log total green bond issuance  (main)
Y_GOV_COL  = "x1l"      # log government green bond issuance
Y_CORP_COL = "x2l"      # log corporate green bond issuance

# ── Three central bank policy variables (key explanatory) ────────────────────
CB_COLS = ["cbmnd", "cbenf", "cbsys"]
# cbmnd = CB mandate (sustainability scope)
# cbenf = CB enforcement power
# cbsys = CB control of systemic risk tools

# Generic X_COL used by generic transform/descriptive scripts
X_COL = "cbmnd"

# ── Baseline control variables (paper's $xvar minus CB_COLS) ─────────────────
CONTROL_COLS = ["infl", "rating", "fie", "gdpg", "dum9", "dum12"]
# infl   = Official CPI inflation
# rating = Moody's country rating (numeric)
# fie    = IMF financial institutions efficiency
# gdpg   = GDP growth (annual %)
# dum9   = 1 if EU27 member  (time-invariant → absorbed by entity FE)
# dum12  = 1 if OECD member  (time-invariant → absorbed by entity FE)

# Full baseline xvar (CB policy + controls) as in the paper
XVAR_COLS = CB_COLS + CONTROL_COLS

# ── Squared CB terms (for non-linear Table 5 spec) ───────────────────────────
CB_SQ_COLS = ["cbmndsq", "cbenfsq", "cbsyssq"]

# ── Robustness: additional controls ──────────────────────────────────────────
RISK_COLS  = ["riskeqt", "riskctr"]   # Table 7, col 1
ENERGY_COLS = ["enrgoil", "envtax"]   # Table 7, col 2
UNCERT_COLS = ["gprlog", "wui"]       # Table 7, col 3

# ── IV instruments ────────────────────────────────────────────────────────────
# cbmnd instrumented by: hierarchy, purity
# cbenf instrumented by: hierarchy, openness
# cbsys instrumented by: hierarchy, openness
IV_INSTRUMENTS = ["hierarchy", "openness", "purity"]

# ── Interaction variables (Table 9) ──────────────────────────────────────────
INTERACT_VARS = ["prodstr", "bigtech", "ngain"]
# Interaction is always cbenf × interact_var

# ── Panel sample selection ────────────────────────────────────────────────────
MIN_CONSEC = 3   # minimum consecutive Y observations to keep a country

# ── Plot / output settings ────────────────────────────────────────────────────
FIG_DPI    = 150
FIG_FORMAT = "png"

# ── Balanced sub-panel TWFE ───────────────────────────────────────────────────
TWFE_MIN_T = None   # None = max T; or integer minimum T per country
