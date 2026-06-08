# Panel Data Econometrics Homework: Replication

**Name of student:**  

**Submission platform:** EPI  
**Due date:** _as indicated on EPI_

---

## Files to upload on EPI

Upload the following files at the due date:

1. The original paper in PDF format.
2. The database that you use, possibly updated with respect to the paper, possibly in Excel format.
3. The database formatted for the software you used: Python, Stata, or R.
4. The code of your preferred software, for example Python, in a format such that anyone can run your code immediately.
5. The code translated into Stata and R with the help of an LLM, with comments mentioning difficulties for running these versions.
6. A Word or TEX version and a PDF version of your answers, following the guidelines below, using this Word file or copying it into TEX.
7. A Word file and then a PDF file containing a copy-paste of all your LLM prompts and answers for doing this homework, including code. There is no problem if it is 300 pages.
8. A “to-do list” of steps for panel data for the next time you will use panel data.

You may add a commented HTML file of the code and output of your software, but it is **not accepted as a substitute** for the written version of the answers.

Some panel data estimates, in particular GMM with `xtabond2` and Hausman-Taylor, are coded in **Stata**.

A book with R code for panel data is in the folder **BOOKS**.

> **Remark on autoregressive parameters:** If you estimate an autoregressive parameter, or the sum of autoregressive parameters, larger than one, the series of long-run coefficients is infinite and the formula with `1 / (1 - rho)` is not valid. You can compute impulse responses for the first periods, but they explode.

> **Remark on readability:** Pay attention to whether your work is readable. Copy-pasting patchy answers from an LLM is not enough. The reader may not grasp anything that you did not understand yourself. The aim of statistics is to extract signal from noise and explain it clearly. You may have a perfect “to-do list” proposed by an LLM that contradicts what you have written.

---

# Homework: Panel Data Partial Replication

**Name of the student:**  

**APA reference of the replicated paper:**  
Use Google Scholar and check the authors, title, journal, and pages.

**Link to the paper:**  
Include the DOI if available.

---

## Table 1. Key correlation of the paper

| Dependent variables, denoted `Y` in what follows | Key preferred explanatory variables, denoted `X` in what follows |
|---|---|
| Name and link to the website of the data source for updates: | Name and link to the website of the data source for updates: |
|  |  |
| Select the level(s): country, sectors, firm, bank, households, assets of financial markets |  |

**Link to the data set:**  

**Links to the data set sources:**  

**Abstract:**  
Write a 100-word abstract of what you have done.

---

## 1. Introduction

Length: **1 page**.

Summarize in three paragraphs what you find that was not seen in the paper. This should be done at the end of your partial replication.

### Table 2. Key items found, by order of interest of this partial replication

| Rank | Key item found |
|---:|---|
| 1 |  |
| 2 |  |
| 3 |  |
| 4 |  |
| 5 |  |

---

## 2. Database update

If the data set can be updated with recent years from a freely and publicly available database, update it.

Specify whether:

- updates of variables have observations different from the original database, for example GDP updated by national accountants for recent years;
- you add variables;
- you add individuals, for example countries.

Mention any issue with the available original database, for example if it is incomplete with respect to the paper or if it was sent by the authors upon your request.

### Table 3. Data characteristics

| Maximal time span | Frequency | Number of individuals | Maximal number of time observations for an individual | Balanced or unbalanced panel |
|---|---|---|---|---|
| _2020Q2-2022Q3_ | _Quarterly_ | _Ntotal = 76_ | _Tmax =_ <br> _For individual “Germany”_ | _Balanced_ |
| _Update: 2022Q4-2024Q4_ |  | _Ntotal =_ | _Tmax =_ |  |

---

## 3. Panel data sample selection

### Table 3. Sample selection for dynamic panel data

Requirement: each individual must have **at least 3 consecutive observations of the dependent variable**.

You may have missing data in between. For example, for a given individual, there can be 3 consecutive years, then 2 missing years, then again 3 consecutive years.

Replace non-consecutive observations or only two consecutive observations of the dependent variable by `not available` or `.` for the dependent variable, if the individual remains in the sample because it has 3 other consecutive observations on other dates.

The point is to keep descriptive statistics matched to the maximal sample used for estimating the dependent variable.

> **Remark:** For within estimation, at least two consecutive observations are needed, but the benchmark sample should preferably have at least 3 consecutive observations. This allows first differences to be regressed on first differences and allows the Anderson-Hsiao estimator to be used. Many economic variables are persistent, so a lagged dependent variable should be included at least in robustness checks for a dynamic model. With small `T`, the within transformation faces a large Nickell (1981) bias on the parameter of the lagged dependent variable.

### Panel data sample selection table

| Individuals excluded from the panel data selection | Individuals with at least three consecutive observations for the dependent variable, kept in all next questions |
|---|---|
| Number: `N1 =` | `Ntotal - N1 = N` |
|  | Maximal time span for an individual, for example 2016-2020 yearly |
| List: | List: |

Comment on the panel data sample selection bias.

Questions to answer:

- Are small firms excluded because of missing observations of the dependent variable?
- Are poor countries excluded because of missing observations of the dependent variable?
- Is any major country excluded because of missing observations of the dependent variable?

> **Important rule from now on:** All statistics must be computed only on this selected panel data sample, using a restriction such as: dependent variable not equal to `not a number` or `.`.

---

## 4. Sample selection within an unbalanced panel

Data availability often implies sample selection leading to an unbalanced panel, meaning missing time observations for some individuals.

### Table. Number of individuals per date

| Date | 2010 | 2011 | 2012 | ... |  |  |  |  |  |
|---|---:|---:|---:|---|---|---|---|---|---|
| N | 10 | 30 |  |  |  |  |  |  |  |

If there are more than 30 periods, draw a graph of the number of observations.

Comment on attrition, meaning fewer observations at the beginning and at the end.

### Table. Number of individuals with the same number of temporal observations

| Observations by individuals | Tmax | Tmax - 1 | Tmax - 2 | ... |  |  |  | 4 | 3 |
|---|---:|---:|---:|---|---|---|---|---:|---:|
| Number of individuals in this case | 10 | 30 | 50 |  |  |  |  | 90 | 100 |

Give the number and the proportion of individuals with holes, meaning discontinuity with missing observations.

If the number of individuals with holes is below 100, give their list.

Comment whether there is a pattern in this unbalanced panel sample selection, for example whether it concerns small firms or poor countries.

---

## 5. Panel data variables classification

Compute the following transformations for all variables:

- between-transformed variables;
- one-way-within-transformed variables.

Then:

1. Compute their variance.
2. Compute the share of within variance in the overall variance.
3. Sort variables by their share of within variance.
4. Split variables into 3 categories:
   - **100% within:** common time series to all individuals;
   - **0% < share of within < 100%:** variables with double indices; the closer to 100%, the closer to common time series; the closer to 0%, the closer to time-invariant variables;
   - **0% within / 100% between:** time-invariant variables.
5. Report the information in the next four tables and comment on each table.

### Table 4. Variable count by categories

| Variables varying with two indices, time and individuals | Time-invariant variables, share of between variance = 100%, wiped out by individual dummies | Individual-invariant variables, time series invariant for all individuals, wiped out by time dummies |
|---|---|---|
| Number: `K =` | `K1 =` | `K2 =` |

### Table 5. Time-varying variables

Variables with `0% < % within variance < 100%` should be sorted by their percentage of within variance, from the highest within variance down to the lowest.

| Variable, in words | N | NT | NT / N | Overall variance | Between variance | Within variance | % within variance / total, sorted by this column |
|---|---:|---:|---:|---:|---:|---:|---:|
| Dependent variable(s) first |  |  |  |  |  |  |  |
| Explanatory variables ordered by % of within variance |  |  |  |  |  |  |  |

Comment on the relative share for the key dependent variable and key explanatory variables of interest.

A small share of within variance may correspond to small within variance, as if the variable is nearly time-invariant. By contrast, high within variance may be related to a few high-leverage observations of opposite sign after the within transformation.

### Table 4. Time-invariant variables, 100% between variance

| Variable, in words | N | NT | NT / N | Overall variance | Between variance | Within variance | % within variance |
|---|---:|---:|---:|---:|---:|---:|---:|
|  |  |  |  |  |  | 0 | 0% |

### Table 5. Individual-invariant variables, 0% between variance

| Variable, in words | N | NT | NT / N | Overall variance | Between variance | Within variance | % within variance |
|---|---:|---:|---:|---:|---:|---:|---:|
|  |  |  |  |  | 0 |  | 100% |

The number of observations matters because some explanatory variables have fewer observations than the dependent variable.

---

## 6. Between plus one-way within decomposition: univariate and bivariate descriptive statistics after variable transformations

For the dependent variable and the key preferred explanatory variable, not all explanatory variables:

1. Plot the distribution of the one-way-fixed-effects-within transformation:

   $$x_{it} - x_{i.}$$

2. Plot the distribution of the between transformation:

   $$x_{i.}$$

3. On the same graph, include:
   - a histogram;
   - a normal law with the same empirical mean and standard error;
   - a kernel continuous approximation.

4. Comment on the between and within differences for each variable.
5. Compare:
   - within/within for the dependent and explanatory variable;
   - between/between for the dependent and explanatory variable.
6. Discuss:
   - kurtosis;
   - skewness;
   - non-normality;
   - high-leverage observations far from the mean;
   - several modes, meaning a mixture of distributions.

---

## 7. First differences versus two-way fixed effects: univariate and bivariate descriptive statistics after variable transformations

These transformations eliminate deterministic trends.

### 7.1. First-difference variable transformations

Compute first differences for panel data:

$$x_{it} - x_{i,t-1}$$

Check the first 3 changes of individuals in the first `3T + 1` observations, after sorting the data by individual and then by time.

When there is a change of individual in the stacked vector `individuals × time`, the first difference must be `.` or missing. It must **not** be computed as the first observation of the second individual minus the last observation of the first individual.

### 7.2. First-difference distributions

Plot the distributions for:

- first-difference dependent variable `ΔY`;
- first-difference explanatory variable `ΔX`.

For each, include:

- histogram;
- KDE;
- normal law with the same mean and standard error.

### 7.3. First-difference simple correlation

For the first-difference transformed variables:

1. Plot the bivariate cloud of points with a regression line.
2. Add the marginal distribution of the horizontal axis on top.
3. Add the marginal distribution of the vertical axis on the right-hand side.
4. Compare with one-way fixed effects and between distributions.
5. Report the simple correlation coefficient on the graph.

### 7.4. Restricted sample with a balanced panel: TWFE formula

Restrict the sample to the countries or individuals available for the longest duration:

- `N = ...` countries or individuals;
- `T = ...` periods.

Compute:

$$-x_{.t} + x_{..}$$

Report the `T` numbers in a table as a function of the time index, plot them as a function of time, and comment.

Then compute the two-way fixed effects transformed variables:

$$x_{it} - x_{i.} - x_{.t} + x_{..}$$

### 7.5. TWFE balanced panel: descriptive statistics and boxplots

Compute descriptive statistics.

Plot boxplots by country, ordered by variance from smallest to largest.

### 7.6. TWFE balanced panel: correlation by country

Present a table ordering the simple correlation coefficients of the TWFE-transformed dependent variable `Y` and preferred explanatory variable `X` by country, from the largest positive to the lowest negative.

Also include:

- the standard error of `GDPG`;
- the standard error of `EDA`;
- the coefficient of the simple regression:

$$\text{correlation coefficient} \times \frac{\text{standard error of GDPG}}{\text{standard error of EDA/GDP}}$$

Comment on the results.

### 7.7. Unbalanced panel and TWFE transformation

Remove countries or individuals with a single observation.

For the dependent variable:

1. Regress the within-transformed dependent variable `Y` on time dummies.
2. Collect the residuals.
3. These residuals are the TWFE transformation.

For the preferred explanatory variable:

1. Regress the within-transformed preferred explanatory variable `X` on time dummies.
2. Collect the residuals.
3. These residuals are the TWFE transformation.

Alternatively, code the Wansbeek-Kapstein (1989) transformation for two-way fixed effects, based on their equation 2.13, which extends the balanced-panel formula:

$$x_{it} - x_{i.} - x_{.t} + x_{..}$$

### 7.8. TWFE unbalanced panel: distribution plots

Plot the distribution for the TWFE-transformed dependent variable `Y` and explanatory variable `X`, including:

- kernel density estimate;
- histogram;
- corresponding normal law with the same first two moments.

Compare these distributions with:

- one-way fixed effects distributions;
- between distributions.

---

## 8. Comparisons of the four transformed variables

Compare the following transformations:

- Between;
- one-way within;
- two-way within;
- first differences.

### 8.1. Boxplots by country or individual

For the dependent variable and the key explanatory variables, plot boxplots of:

1. between distribution for all countries or individuals;
2. one-way fixed effects distribution by country or individual;
3. two-way fixed effects distribution by country or individual;
4. first-difference distribution by country or individual.

If you have a very large number of individuals, for example more than 50, use a subset of individuals.

Comment whether you find the same insights as in Question 5.

Comment on differences in standard errors and means for each individual.

### 8.2. Univariate descriptive statistics

Compute univariate descriptive statistics for one-way within, between, two-way fixed effects, and first-difference transformed variables.

Report:

- minimum;
- Q1;
- median;
- Q3;
- maximum;
- mean;
- standard error.

Answer the following:

- Is the mean different from the median? Why?
- How many standard errors away from the mean are the minimum and maximum extremes?

In the tables, report standardized maximum and minimum instead of raw maximum and minimum:

$$\frac{MAX - average}{standard\ error}$$

$$\frac{MIN - average}{standard\ error}$$

### 8.3. Between versus one-way within bivariate correlation matrix

Compare and comment on the between-transformed versus one-way-within-transformed bivariate correlation matrix for all variables.

Include:

- a time trend `1, 2, ..., T`;
- lags for time-varying variables.

Check for:

- poor simple correlation with the dependent variables;
- high correlation between explanatory variables.

### 8.4. Autocorrelation and trend correlations

Comment on bivariate autocorrelation and trend correlations.

Check the number of observations.

### 8.5. TWFE and first-difference correlation matrices

In what follows, you do not need to include a deterministic time trend `1, 2, ..., T`, because the two transformations used eliminate it.

Compare and comment on:

1. the two-way-within-transformed bivariate simple correlation matrix of all variables;
2. the first-difference-transformed bivariate simple correlation matrix of all variables.

For first differences, also include the lag of all variables.

Check for:

- poor simple correlation below 0.1 with the dependent variables;
- high correlation above 0.8 between explanatory variables.

Show the first 30 observations for the first differences and the lag of first differences.

Check that each time you change individual, you have a `.` for the missing observation.

### 8.6. Bivariate graphs with fitted curves

Comment on the bivariate graphs with:

- linear fit;
- quadratic fit;
- LOWESS fit.

Use the dependent variable `Y` and key explanatory variable `X` on the horizontal axis for:

- within-transformed variables;
- between-transformed variables;
- first differences;
- two-way-within-transformed variables.

---

## 9. Investigating bivariate heterogeneity by individuals for TWFE and FD

### 9.1. Heterogeneity for first-difference transformed variables

Fill in the table for heterogeneity of key correlation between individuals and slopes of the simple regression for first-difference transformed variables.

The table should be sorted by the correlation coefficient. Numbers should be rounded at the third non-zero digit.

`ΔY` and `ΔX` are first-difference transformed variables. `T(i)` is the number of observations used in the simple regression for individual `i`.

| Individual name `i` | `T(i)` | `r(ΔY, ΔX)` | `σ(ΔY)` | `σ(ΔX)` | `σ(ΔY) / σ(ΔX)` | `β = r(ΔY, ΔX) × σ(Y) / σ(X)` |
|---|---:|---:|---:|---:|---:|---:|
|  |  |  |  |  |  |  |

Diagnosis should be done in three groups:

1. individuals with positive correlation larger than 0.08;
2. individuals with negative correlation lower than -0.08;
3. individuals with weak correlation.

You may also consider 5 groups for the two extreme positive versus negative cases.

This is helpful for open questions and for doing regressions on subgroups.

### 9.2. Heterogeneity for TWFE-transformed variables

Fill in the table for heterogeneity of key correlation between individuals and slopes of the simple regression for two-way fixed effects transformed variables.

The table should be sorted by the correlation coefficient. Numbers should be rounded at the third non-zero digit.

`Y` and `X` are two-way fixed effects transformed variables. `T(i)` is the number of observations used in the simple regression for individual `i`.

| Individual name `i` | `T(i)` | `r(Y, X)` | `σ(Y)` | `σ(X)` | `σ(Y) / σ(X)` | `β = r(Y, X) × σ(Y) / σ(X)` |
|---|---:|---:|---:|---:|---:|---:|
|  |  |  |  |  |  |  |

Diagnosis should be done in three groups:

1. individuals with positive correlation larger than 0.08;
2. individuals with negative correlation lower than -0.08;
3. individuals with weak correlation.

### 9.3. Optional: time heterogeneity of bivariate correlation

If `T` is sufficiently large, for example `T > 20`, do rolling-window estimates for each individual and visualize the stability over time of estimated parameters.

The rolling window should be at least `T = 8`, for example 8 quarters.

Do this for both:

- TWFE;
- first differences.

Diagnosis: this may suggest a few periods for sample-period dummies for each individual.

---

## 10. Panel data estimates

### 10.1. Main estimation table

In a single table, report and comment on the results of the following estimations:

1. Between;
2. Within, meaning one-way fixed effects, `fe`;
3. Mundlak, meaning random effects, `re`, including all `X(i.)` as regressors;
4. Two-way fixed effects, by adding year dummies in the fixed effects regression;
5. First differences.

Include all explanatory variables except those with high near-multicollinearity after their transformation.

### 10.2. Optional dynamic panel estimator if autocorrelation remains

If, for the first-difference dependent variable, simple autocorrelation remains above 0.1, a dynamic panel estimator can be tried.

GMM estimators for panel data are only valid for short panels with `T < 10`, and they face the issue of too many weak instruments.

The suggested estimator is the Anderson-Hsiao (1981) estimator, the precursor of GMM. It allows you to check the first stage of instrumental variables and test for weak lagged instruments.

Estimate an autoregressive distributed lag model, ARDL, for dynamic panel data including:

- the first lag of the dependent variable;
- the first lag of the key explanatory variable;
- optionally, the first lag of other control variables.

Model:

$$
\Delta Y_{i,t}
= \beta_y \Delta Y_{i,t-1}
+ \beta_1 \Delta X_{i,t}
+ \beta_2 \Delta X_{i,t-1}
+ \Delta Controls_{i,t}
+ \Delta \alpha_t
+ \Delta \varepsilon_i
$$

Note: individual fixed effects are eliminated in first differences.

#### Required outputs for the dynamic panel part

1. For all these variables, report univariate statistics, namely mean, median, standard error, skewness, kurtosis, minimum, and maximum, and comment:

   - `ΔY_i,t`;
   - `ΔY_i,t-1`;
   - `ΔX_i,t`;
   - `ΔX_i,t-1`;
   - `Y_i,t-2`;
   - `X_i,t-2`.

2. Report the bivariate simple correlation coefficient matrix. The correlation between `ΔY_i,t-1`, `ΔX_i,t`, `ΔX_i,t-1` and the instruments in levels, `Y_i,t-2` and `X_i,t-2`, is a preliminary check of instrument strength.

3. Do a panel data unit root test of your choice on `ΔY_i,t` and `ΔX_i,t` and comment. Because of first differences, these variables may be stationary.

4. Report OLS including the lag of the first difference of the dependent variable, `ΔY_i,t-1`, and other explanatory variables. Report the number of observations and the number of countries remaining in the estimation, which requires at least three consecutive observations for each country.

5. Report the IV estimator, `IVREG`, when you use the instruments in levels `Y_i,t-2` and `X_i,t-2`. Comment on how much each parameter changes when using OLS versus IV.

6. Report the first-stage regressions. Comment on the `R²` of each first-stage regression. If it is below 10%, it is a signal of weak instruments. You may comment on statistics available in your software for weak instruments and for testing endogeneity of instruments.

7. Compute and plot the impulse response functions for the next four periods for a one-unit increase of `X` on `Y`:

   - `t = 1`: $\beta_1$
   - `t = 2`: $\beta_y \beta_1 + \beta_2$
   - `t = 3`: $\beta_y^2 \beta_1 + \beta_y \beta_2$
   - `t = 4`: $\beta_y^3 \beta_1 + \beta_y^2 \beta_2$

8. Compute the long-run coefficient of the key explanatory variable on the dependent variable and comment:

   $$
   \beta_{LT} = \frac{\beta_1 + \beta_2}{1 - \beta_y}
   $$

---

## 11. Optional: if one variable is time-invariant `z(i)`, panel data estimators

Skip this section if there is no time-invariant variable `z(i)`.

### 11.1. Hausman-Taylor estimation

If one of your variables is time-invariant `z(i)`, run a baseline Hausman-Taylor estimation. This is pre-coded only in Stata.

Include all `X(i.)` as instruments.

Comment on the results.

### 11.2. Between regression for `z(i)`

If one of your variables is time-invariant `z(i)`, run a between regression explaining `z(i)` by:

- `X(i.)`;
- other time-invariant variables.

This regression uses only `N` observations.

If the `R²` is low, this may signal that `X(i.)` variables are weak instruments, poorly correlated with the variable `z(i)` to be instrumented.

Comment on the result.

### 11.3. Interaction shortcut in one-way fixed effects

If one variable is time-invariant `z(i)`, remember that time-invariant explanatory variables cannot explain the time-varying within variance of the dependent variable. The Hausman-Taylor internal-instruments estimator is therefore not very practical.

A practical shortcut is to include a time-invariant variable multiplied by a time-varying variable:

$$Z_i \times X_{it}$$

Generate such an interaction variable.

Include both:

- the product `Z(i) × X(it)`;
- `X(it)`;

in a one-way fixed effects regression.

Plot the estimated marginal effect, derivative, with respect to `Z(i)` as a function of `X(it)` for the interval `[Xmin, Xmax]` in the sample.

---

## 12. Your own estimations not done in the paper

Do whatever seems interesting to you in terms of original estimations that were not already done by the replication of the original authors.

Use the same database.

Present the table(s) in this file with comments. Do not present them only in the HTML output with code and output.

---

## References

List all references cited in the text.

---

# Appendix

## To-do list

Fill in a to-do list for the next time you conduct a study involving panel data, especially for your master thesis.

This can be done jointly by pairs of students of Option 1.

## Ordered to-do list for the next econometric study using panel data

You may split the table into several tables for each step, for example:

- data selection;
- variable transformations;
- descriptive statistics tables and visualization;
- estimators and endogeneity;
- sample splits and robustness checks.

The number of items is unlimited.

| Tick | Items |
|---|---|
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
