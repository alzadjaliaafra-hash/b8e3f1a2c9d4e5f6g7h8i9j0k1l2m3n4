# Hazard Layer Implementation for SRFF-I RVS v3.0

## Dynamic Time-to-Event (Hazard) Extension

**Prepared for:** Sohar International Bank — SRFF-I Investment Committee  
**Date:** April 17, 2026  
**Classification:** Strictly Private and Confidential  
**Version:** 1.0

---

## Executive Summary

This document specifies the **Discrete-Time Hazard Layer** that transforms the static Enhanced RVS v2.0 into a dynamic, forward-looking survival engine. The hazard layer directly answers the fund's core question:

> *"Given today's financials, what is the probability this company survives all milestones and reaches a successful exit within the 5-year Musharaka tenor?"*

The layer builds on:
- Your master's thesis (bankruptcy prediction)
- Shumway (2001) hazard model framework
- The 47-company validation dataset with temporal cohorts (Pre-COVID, Late-Cycle, COVID-Shock)

---

## 1. Why Discrete-Time Hazard (Not Continuous or Plain Logistic)

### The Problem with Static Models

The original RVS is a **single-period logistic regression** that estimates P(eventual recovery/failure). It implicitly assumes 100% survival through the restructuring period, which systematically overvalues distressed firms.

### The Hazard Solution

A **hazard model** estimates the instantaneous risk of failure at each future time period, conditional on having survived so far. The discrete-time version is perfect for SRFF-I because:

- **Your data is annual/quarterly financials** (not daily)
- **The fund tenor is fixed** (5 years) with clear milestones:
  - DSCR ≥ 1.2×
  - Cash sweep compliance
  - PIK moratorium end
- **It naturally produces a cumulative survival probability curve to Year 5** — exactly what multiplies into the Composite Rescue Score

---

## 2. Data Requirements

### Training / Backtest Data (Already Available)

- **Dataset:** 47 companies (2018–2019 financials → 2024–2025 outcomes)
- **Format:** Convert to firm-year or firm-quarter panel format:
  - Each row = one company in one time period (t = 1 to T)
  - Dependent variable = binary "failure event" in that period (1 if failed, 0 otherwise)
  - Right-censored for companies that survived the full horizon
- **Variables:** Original 6 RVS variables + time-varying covariates:
  - DSCR (Debt Service Coverage Ratio)
  - EBITDA margin
  - Cash balance
  - Covenant compliance flag

### Live / Post-Investment Data

- **Frequency:** Monthly actuals from portfolio companies
- **Content:** P&L, cash flow, DSCR, cash sweep hit/miss
- **Purpose:** Enables monthly re-scoring after deployment

---

## 3. Model Specification (Shumway-Style Discrete-Time Hazard)

### Hazard Rate Formula

The hazard rate h_{i,t} (probability of failure in period t for company i, given survival until t-1) is modeled as:

```
h_{i,t} = 1 / (1 + exp(-z_{i,t}))
```

### Linear Predictor

```
z_{i,t} = β₀ + Σ(β_k × V_{k,i,t}) + γ × TimeDummy_t + δ × MacroShock_t + ε_{i,t}
```

Where:
- **V_{k,i,t}:** The 6 RVS variables (updated at each t)
- **TimeDummy:** Captures duration dependence (e.g., higher risk in Year 1 vs Year 4)
- **MacroShock:** Dummy for COVID-type regimes (already tested in validation)

### Cumulative Survival Probability to Year 5

The key output is:

```
S_i(5) = ∏(1 - h_{i,t}) for t=1 to 5
```

This S_i(5) becomes the **Hazard Survival Probability multiplier** in the Composite Rescue Score.

---

## 4. Step-by-Step Implementation Guide

### Step 1: Data Transformation (1–2 days)

**Objective:** Reshape the 47-company dataset into panel format

**Tasks:**
1. Convert to company × time format
2. Define "failure event" = actual outcome in 2024–2025 (already labeled in validation report)
3. Add lagged variables (e.g., prior-period DSCR) if desired
4. Create time dummies and macro shock indicators

**Output:** Panel dataset with one row per company-period

### Step 2: Model Estimation

**Tools:** Python (statsmodels) or R (survival package)

**Pseudocode:**

```python
import pandas as pd
import statsmodels.api as sm
from lifelines import KaplanMeierFitter  # for diagnostics only

# Assume df is the panel dataset
df['intercept'] = 1
X = df[['intercept', 'V1_DSCR', 'V2_Collateral_adj', 'V3_EBITDA_mgn', 
        'V4_EBITDA_Debt', 'V5_Asset_ID', 'V6_Gov_Control', 
        'TimeDummy', 'COVID_Shock']]
y = df['failure_event']   # 1 if failed in this period

logit_model = sm.Logit(y, X).fit()
print(logit_model.summary())
```

**Expected Output:**
- Estimated coefficients (β₀, β₁, ..., β₆, γ, δ)
- Standard errors and t-statistics
- Model diagnostics (AIC, BIC, log-likelihood)

### Step 3: Generate Survival Curve for Each Company

**For any new candidate (or existing portfolio company):**

```python
def hazard_survival_prob(model, row, horizon=5):
    surv = 1.0
    for t in range(1, horizon+1):
        # Update inputs with projected or actual values at time t
        z = model.predict(row_at_t)  
        h = 1 / (1 + np.exp(-z))
        surv *= (1 - h)
    return surv
```

**Inputs:**
- Calibrated hazard model
- Company financials at t=0
- Projection horizon (default: 5 years)

**Output:**
- Cumulative 5-year survival probability S_i(5)

### Step 4: Integrate into Composite Rescue Score (V3 Formula)

```
Composite RVS v3 = Enhanced RVS v2 × S_i(5) × Governance Score × Shariah Multiplier × Projection Confidence
```

Where:
- **Enhanced RVS v2:** Original 6-variable score (already calibrated)
- **S_i(5):** New hazard survival probability (0.85+ target for "Strong")
- **Governance Score:** Existing governance assessment
- **Shariah Multiplier:** Existing Shariah compliance factor
- **Projection Confidence:** Confidence in forward projections

---

## 5. Monthly Updating Post-Investment (Fund Operating System)

### Workflow

1. **Input:** Monthly actuals from portfolio companies
   - P&L (Revenue, EBITDA, Net Income)
   - Cash flow (Operating CF, Free CF)
   - DSCR (actual vs target)
   - Cash sweep compliance (yes/no)
   - Covenant breaches (if any)

2. **Processing:**
   - Update the 6 RVS variables with monthly actuals
   - Re-compute z_{i,t} using the calibrated hazard model
   - Re-compute h_{i,t} (monthly hazard rate)
   - Re-compute S_i(remaining tenor) (e.g., if 2 years remain, compute S_i(2))

3. **Monitoring:**
   - If S_i(remaining tenor) drops below 80%, trigger GP step-in rights automatically (already in fund docs)
   - If S_i drops below 70%, escalate to Investment Committee for immediate review

4. **Output:**
   - Live "Survival Drift" chart for IC monitoring
   - Monthly update email: "Company X: 5-yr Survival down from 92% to 87% (Q2 → Q3)"

---

## 6. Validation Plan (Reuse Existing 47-Company Dataset)

### Test 11: Hazard Discrimination

**Objective:** Measure how well the hazard layer discriminates between companies that survived vs failed

**Methodology:**
- Run full 10-test academic suite on hazard-augmented model
- Calculate AUC on time-to-failure
- Compare predicted vs actual survival curves

**Pass Criteria:**
- AUC > 0.85
- Mean 5-year survival probability > 80% for recovered companies
- Mean 5-year survival probability < 60% for failed companies

### Test 12: Out-of-Sample Survival Calibration

**Objective:** Test if predicted survival curves match actual outcomes

**Methodology:**
- Split 47-company dataset into training (35) and test (12)
- Fit hazard model on training set
- Predict survival curves for test set
- Compare predicted vs actual survival to Year 5

**Pass Criteria:**
- Calibration error < 5%
- No systematic over/under-prediction by sector

---

## 7. Practical Deliverables You Can Build This Week

### 1. Excel Template (with Python Backend)

**Features:**
- Accepts 6 RVS inputs + monthly actuals
- Outputs survival curve (graphical)
- Outputs Composite v3 score
- Accepts Power Query or Manus AI backend

**Timeline:** 3 days

### 2. One-Page IC Dashboard Line Item

**Content:**
- "Hazard 5-yr Survival: 89% (down from 92% last quarter)"
- Portfolio-level survival distribution
- Early warning flags (companies below 80%)

**Timeline:** 1 day

### 3. NPI Live Example

**Objective:** Re-run hazard layer on NPI's actual post-restructuring data

**Purpose:** Prove the layer works on a real deployed deal

**Timeline:** 2 days

---

## 8. Expected Results

### Accuracy Improvement

- **Original RVS v2.0:** 93.6% accuracy (Tests 1-10)
- **With Hazard Layer (v3.0):** ≥94% accuracy (Tests 1-11)
- **Benefit:** Adds dynamic early-warning capability without sacrificing accuracy

### Survival Probability Distribution

**Expected for 47-company dataset:**
- Mean 5-year survival: 82–88%
- Median: 85%
- Strong candidates (>85%): 28–32 companies
- Conditional candidates (70–85%): 12–16 companies
- Weak candidates (<70%): 3–5 companies

### Monthly Monitoring

**Expected portfolio drift:**
- Average monthly change: ±2–3%
- Quarterly review triggers: ±5% change
- Crisis triggers: >10% drop in single month

---

## 9. Technical Implementation Notes

### Python Libraries

```python
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.special import expit
from lifelines import KaplanMeierFitter  # optional, for diagnostics
```

### Data Validation Checks

Before fitting hazard model:
1. Check for missing values in X and y
2. Verify y is binary (0/1)
3. Check for multicollinearity (VIF < 5)
4. Verify sufficient variation in each variable

### Model Diagnostics

After fitting:
1. Check coefficient signs (all should be negative for failure, positive for recovery)
2. Verify p-values < 0.05 for key variables
3. Plot predicted vs actual survival curves
4. Calculate calibration error

---

## 10. Limitations & Future Enhancements

### Current Limitations

1. **Single-period approximation:** Current implementation uses single-period hazard rates, not full quarterly panel
2. **No time-varying covariates:** Future version should include quarterly DSCR, cash balance updates
3. **Limited macroeconomic variables:** Could add oil price, interest rate, GDP growth dummies

### Future Enhancements (Post-V3.0)

1. **Quarterly panel data:** Convert to full 20-quarter (5-year) panel for more granular predictions
2. **Competing risks:** Model different failure modes (liquidation vs restructuring vs acquisition)
3. **Portfolio-level analysis:** Aggregate survival probabilities for fund-level stress testing
4. **Machine learning:** Test XGBoost, neural networks as alternatives to logit

---

## 11. References

- Shumway, T. (2001). "Forecasting bankruptcy more accurately: A simple hazard model." *Journal of Business*, 74(1), 101-124.
- Campbell, J. Y., Hilscher, J., & Szilagyi, J. (2008). "In search of distress risk." *Journal of Finance*, 63(6), 2899-2939.
- Damodaran, A. (2006). *Investment Valuation: Tools and Techniques for Determining the Value of Any Asset* (2nd ed.). Wiley Finance.

---

**Document Version:** 1.0  
**Last Updated:** April 17, 2026  
**Classification:** Strictly Private and Confidential
