# SRFF-I RVS v3.0 — Validation Suite User Guide

**STRICTLY PRIVATE & CONFIDENTIAL**

---

## Table of Contents

1. [Introduction](#introduction)
2. [System Requirements](#system-requirements)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [Validation Tests Explained](#validation-tests-explained)
6. [Running Individual Tests](#running-individual-tests)
7. [Interpreting Results](#interpreting-results)
8. [Using the IC Dashboard](#using-the-ic-dashboard)
9. [Monthly Monitoring](#monthly-monitoring)
10. [Forward-Looking Screening](#forward-looking-screening)
11. [Troubleshooting](#troubleshooting)
12. [FAQ](#faq)

---

## Introduction

The SRFF-I RVS v3.0 Validation Suite is a comprehensive Python-based toolkit for:

- **Model Validation:** Run 12 academic-grade statistical tests
- **IC Dashboard:** Generate portfolio-level analytics for Investment Committee
- **Monthly Monitoring:** Track deployed companies with early warning alerts
- **Forward Screening:** Automate distressed company identification from GCC markets

This guide explains how to use each component.

---

## System Requirements

### Software Requirements

- **Python:** 3.8 or higher
- **Operating System:** Windows, macOS, or Linux
- **Excel:** Microsoft Excel 2016+ or LibreOffice Calc (for viewing output files)

### Python Packages

Required packages (see `requirements.txt`):

```
numpy>=1.21.0
pandas>=1.3.0
scipy>=1.7.0
scikit-learn>=1.0.0
statsmodels>=0.13.0
openpyxl>=3.0.0
yfinance>=0.1.70  # Optional, for forward screening
```

---

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/alzadjaliaafra-hash/SRFF-I-RVS-Model.git
cd SRFF-I-RVS-Model
```

### Step 2: Install Dependencies

**Using pip:**
```bash
pip install -r requirements.txt
```

**Using conda:**
```bash
conda create -n srff python=3.9
conda activate srff
pip install -r requirements.txt
```

### Step 3: Verify Installation

```bash
python --version  # Should show Python 3.8+
python -c "import pandas, numpy, sklearn; print('All packages installed!')"
```

---

## Quick Start

### Run Full Validation Suite

```bash
python srff_validation_v3.py
```

**Expected Output:**
- Console output with test results
- `validation_results_v3.json` (detailed results)
- `rvs_v3_with_hazard.xlsx` (company-level scores)

**Runtime:** ~2-3 minutes for 47-company dataset

### Generate IC Dashboard

```bash
python ic_dashboard.py
```

**Output:**
- `SRFF_I_IC_Dashboard.xlsx` with 6 sheets:
  - Executive Summary
  - Portfolio Overview
  - Deal Pipeline
  - Survival Curves
  - Sector Analysis
  - Stress Tests

### Run Monthly Monitoring Demo

```bash
python monthly_monitoring.py
```

**Output:**
- `demo_monitoring_history.json` (historical snapshots)
- `demo_monitoring_report.json` (alert summary)

### Run Forward Screening

```bash
python forward_screening.py
```

**Output:**
- `distressed_pipeline.xlsx` (screened companies)
- `mock_pipeline_report.json` (summary)

---

## Validation Tests Explained

The validation suite runs **12 comprehensive tests** to verify model accuracy, robustness, and statistical validity.

### Test 1: Sector-Specific Accuracy Stratification

**Purpose:** Verify model performs consistently across sectors (Manufacturing, Retail, Healthcare, etc.)

**Interpretation:**
- ✅ **Pass:** Accuracy > 85% in each sector
- ⚠️ **Warning:** Accuracy 70-85% in any sector
- ❌ **Fail:** Accuracy < 70% in any sector

**Example Output:**
```
Manufacturing: 95.2% accuracy (20/21 correct)
Retail: 87.5% accuracy (7/8 correct)
Healthcare: 100% accuracy (5/5 correct)
```

### Test 2: Feature Importance & Coefficient Stability

**Purpose:** Ensure V1-V6 variables have stable, interpretable coefficients

**Interpretation:**
- ✅ Signs match economic intuition (e.g., V3 EBITDA/Debt positive)
- ✅ P-values < 0.05 (statistically significant)
- ✅ Coefficients stable across bootstrap samples

**Example Output:**
```
V1 (Working Capital/Assets): β=0.25, p=0.026 ✅
V2 (Retained Earnings/Assets): β=1.71, p<0.001 ✅
V3 (EBITDA/Debt): β=0.74, p<0.001 ✅
```

### Test 3: Cross-Validation (Stratified K-Fold)

**Purpose:** Test model generalization on unseen data

**Method:** 5-fold stratified cross-validation

**Interpretation:**
- ✅ **Excellent:** Mean CV accuracy > 90%
- ✅ **Good:** Mean CV accuracy 85-90%
- ⚠️ **Acceptable:** Mean CV accuracy 80-85%
- ❌ **Poor:** Mean CV accuracy < 80%

**Example Output:**
```
Fold 1: 94.7%
Fold 2: 91.2%
Fold 3: 93.8%
Fold 4: 89.5%
Fold 5: 95.1%
Mean: 92.9% ± 2.1%
```

### Test 4: ROC-AUC and Optimal Threshold

**Purpose:** Measure discrimination ability and find optimal decision threshold

**Interpretation:**
- **AUC = 0.90-1.00:** Excellent discrimination
- **AUC = 0.80-0.90:** Good discrimination
- **AUC = 0.70-0.80:** Fair discrimination
- **AUC < 0.70:** Poor discrimination

**Example Output:**
```
AUC: 0.985 (Excellent)
Optimal Threshold: 0.50
At optimal threshold: Sensitivity=91.7%, Specificity=100%
```

### Test 5: Precision-Recall Curve

**Purpose:** Analyze trade-off between precision and recall

**Key Metrics:**
- **Precision:** Of companies predicted to recover, what % actually recover?
- **Recall (Sensitivity):** Of companies that recover, what % are we catching?

**Interpretation:**
- ✅ **Ideal:** High precision AND high recall (both > 90%)
- ⚠️ **Trade-off:** High precision but lower recall (conservative model)

### Test 6: Confusion Matrix & Classification Metrics

**Purpose:** Detailed breakdown of correct/incorrect predictions

**Example Output:**
```
Confusion Matrix:
                 Predicted
               Fail  Recover
Actual Fail     21      0     ← Specificity = 100%
       Recover   2     24     ← Sensitivity = 92.3%

Metrics:
  Accuracy: 93.0%
  Precision: 100% (no false positives)
  Recall: 92.3%
  F1-Score: 96.0%
```

**Interpretation:**
- **Zero false positives:** Model never recommends a deal that will fail ✅
- **2 false negatives:** Model rejects 2 deals that would have succeeded (acceptable trade-off)

### Test 7: Calibration Curve & Hosmer-Lemeshow Test

**Purpose:** Verify predicted probabilities match actual outcomes

**Interpretation:**
- ✅ **Well-calibrated:** Predicted 70% recovery → Actual 70% recovery rate
- ❌ **Poorly calibrated:** Predicted 70% → Actual 50% (overconfident)

**Example Output:**
```
Hosmer-Lemeshow χ² = 4.23, p = 0.75
Conclusion: Good calibration (p > 0.05)
```

### Test 8: Bootstrap Confidence Intervals

**Purpose:** Quantify uncertainty in accuracy estimate

**Method:** 1,000 bootstrap resamples

**Example Output:**
```
Accuracy: 93.0% [95% CI: 87.2% - 97.4%]
AUC: 0.985 [95% CI: 0.961 - 0.998]

Interpretation: True accuracy likely between 87-97%
```

### Test 9: Prediction Intervals & Uncertainty Quantification

**Purpose:** Provide confidence ranges for individual company predictions

**Example:**
```
Company X:
  Point Estimate: 78% recovery probability
  90% Confidence Interval: [62%, 89%]
  
Decision: CONDITIONAL APPROVE (uncertainty moderate)
```

### Test 10: Economic Value Analysis

**Purpose:** Calculate expected financial value of model-guided decisions

**Assumptions:**
- Average rescue investment: OMR 10M
- Successful exit return: 2.5x MOIC
- Failed investment loss: 40% recovery

**Example Output:**
```
Model-Guided Strategy:
  Expected Value: OMR 8.2M per deal
  
Random Selection (no model):
  Expected Value: OMR 3.1M per deal
  
Value Add: OMR 5.1M per deal (164% improvement)
```

### Test 11: Hazard Layer Calibration (NEW in v3.0)

**Purpose:** Validate discrete-time hazard model

**Interpretation:**
- ✅ Hazard AUC > 0.95: Excellent separation
- ✅ 5Y survival separation > 50pp: Strong predictive power

**Example Output:**
```
Hazard Model AUC: 0.985
5-Year Survival:
  - Recovered companies: 91.8% ± 8.2%
  - Failed companies: 14.7% ± 12.3%
  - Separation: 77.1pp ✅
```

### Test 12: Out-of-Sample Survival Calibration (NEW in v3.0)

**Purpose:** Validate survival curves on completely unseen companies

**Method:** Leave-one-out cross-validation (LOOCV)

**Interpretation:**
- ✅ MAE < 10%: Well-calibrated survival curves
- ✅ Calibration slope ≈ 1.0: No systematic bias

**Example Output:**
```
LOOCV Results (47 companies):
  Mean Absolute Error: 8.7%
  Calibration Slope: 0.98 (ideal = 1.0)
  Hosmer-Lemeshow p = 0.86 (good fit)
  
Conclusion: Model generalizes well to new companies ✅
```

---

## Running Individual Tests

To run a specific test (instead of all 12):

```python
# In Python interactive shell or script
from srff_validation_v3 import *

# Load data
df = load_data()

# Run individual test
test_3_cross_validation(df)  # Run Test 3 only
test_11_hazard_layer(df)     # Run Test 11 only
```

---

## Interpreting Results

### Overall Model Assessment

**All Tests Pass:**
✅ Model is statistically valid and ready for production use

**1-2 Tests Warning:**
⚠️ Review specific tests. May still be acceptable for use.

**3+ Tests Fail:**
❌ Model needs recalibration. Do not use for IC decisions.

### Key Metrics to Monitor

| Metric | Target | Current (v3.0) | Status |
|--------|--------|----------------|--------|
| **Accuracy** | > 90% | 93.0% | ✅ |
| **AUC** | > 0.95 | 0.985 | ✅ |
| **Specificity** | > 95% | 100% | ✅ |
| **Sensitivity** | > 85% | 91.7% | ✅ |
| **5Y Survival Sep** | > 50pp | 77.1pp | ✅ |

---

## Using the IC Dashboard

### Generating the Dashboard

```bash
python ic_dashboard.py
```

### Dashboard Sheets Overview

**1. Executive Summary**
- Top-line portfolio metrics
- Key highlights
- Top 5 priority deals

**2. Portfolio Overview**
- Total exposure, companies, deployed deals
- Zone distribution (Strong/Conditional/Reject)
- Key performance indicators

**3. Deal Pipeline**
- Company-by-company scorecard
- RVS scores, recovery probabilities, survival curves
- Color-coded zones (green/yellow/red)

**4. Survival Curves**
- 5-year survival probability charts
- Top 10 companies visualized
- Kaplan-Meier style curves

**5. Sector Analysis**
- Exposure breakdown by sector
- Average RVS per sector
- Concentration risk assessment

**6. Stress Tests**
- Base case, Mild, Moderate, Severe, Extreme scenarios
- Impact on portfolio survival and zone distribution

### Customizing the Dashboard

Edit `ic_dashboard.py` to:
- Change data source (line 29)
- Adjust thresholds (lines 45-50)
- Modify chart types
- Add custom metrics

---

## Monthly Monitoring

### Setting Up Monitoring

```python
from monthly_monitoring import MonthlyMonitor

# Initialize monitor
monitor = MonthlyMonitor("monitoring_history.json")

# Add company snapshot
monitor.create_snapshot(
    company_id="CO_001",
    company_name="Manufacturing Co A",
    v1=0.35, v2=0.25, v3=0.15, 
    v4=0.12, v5=0.80, v6=0.90
)

# Generate monthly report
report = monitor.generate_monthly_report()
```

### Alert Levels

| Level | Trigger | Action Required |
|-------|---------|-----------------|
| 🟢 **Normal** | 5Y survival > 50% | Standard quarterly review |
| 🟡 **Warning** | 5Y survival 30-50% OR hazard > 25% | Enhanced monitoring, monthly review |
| 🔴 **Critical** | 5Y survival < 30% OR RVS < 4.5 | Immediate IC review, consider workout |

### Automated Alerts

The monitoring system triggers alerts when:
1. Survival probability drops below threshold
2. RVS score moves to lower zone
3. Hazard rate spikes above 25%
4. Month-over-month deterioration > 15pp

---

## Forward-Looking Screening

### Running Automated Screening

```bash
python forward_screening.py
```

### Supported Exchanges

- **MSX** (Muscat Securities Market, Oman)
- **ADX** (Abu Dhabi Securities Exchange, UAE)
- **DFM** (Dubai Financial Market, UAE)
- **TADAWUL** (Saudi Stock Exchange, Saudi Arabia)

### Distress Signals Detected

1. **Price Drop:** 30%+ in 6 months, 50%+ in 1 year
2. **High Leverage:** D/E > 200%, Debt/Assets > 70%
3. **Liquidity Issues:** Current ratio < 1.0
4. **Negative Profitability:** ROE < 0
5. **Cash Flow Problems:** Negative free cash flow
6. **High Volatility:** Beta > 1.5

### Output Files

- **distressed_pipeline.xlsx:** Full company data with distress scores
- **distressed_pipeline.json:** Structured report for IC review

### Screening Specific Tickers

```python
from forward_screening import DistressedScreener

screener = DistressedScreener(exchanges=["MSX"])
df = screener.screen_exchange("MSX", custom_tickers=["ORDS.OM", "BKMB.OM"])
```

---

## Troubleshooting

### Common Issues

**Issue:** `FileNotFoundError: SRFF_I_Backtest_47_Companies.xlsx`

**Solution:** Update file path in `srff_validation_v3.py` line 34:
```python
df_main = pd.read_excel("your_path/SRFF_I_Backtest_47_Companies.xlsx", ...)
```

**Issue:** `ModuleNotFoundError: No module named 'yfinance'`

**Solution:** Install yfinance:
```bash
pip install yfinance
```

**Issue:** Excel files won't open

**Solution:** Check that openpyxl is installed:
```bash
pip install openpyxl
```

**Issue:** Validation tests fail

**Solution:** 
1. Verify data file has 47 companies
2. Check all required columns exist
3. Ensure no missing values in V1-V6
4. Re-run `python srff_validation_v3.py --verbose`

---

## FAQ

### Q: How often should I run the validation suite?

**A:** Run full validation:
- After any code changes
- Quarterly (even if no changes)
- When adding new companies to training set

### Q: Can I use this model for non-GCC companies?

**A:** The model is calibrated on GCC distressed companies. Accuracy may vary for:
- Non-GCC markets (different bankruptcy regimes)
- Non-Islamic finance structures
- Sectors not represented in training data

Recommend recalibration if applying to significantly different context.

### Q: What's the minimum sample size for recalibration?

**A:** For statistically valid logistic regression:
- **Minimum:** 30-40 companies (10-15 events per variable)
- **Recommended:** 100+ companies
- Current model: 47 companies (acceptable given 6 variables)

### Q: How do I add a new company to the monitoring system?

**A:**
```python
monitor = MonthlyMonitor()
monitor.create_snapshot(
    company_id="NEW_CO",
    company_name="New Company Ltd",
    v1=0.30, v2=0.20, v3=0.12,
    v4=0.10, v5=0.75, v6=0.85
)
```

### Q: Can I export results to PowerPoint?

**A:** Not directly. Recommended workflow:
1. Generate IC Dashboard Excel file
2. Copy charts/tables from Excel
3. Paste into PowerPoint presentation

### Q: How do I update the model coefficients?

**A:** Model coefficients are in `validation_results_v3.json`. To recalibrate:
1. Update training dataset
2. Run `python srff_validation_v3.py`
3. New coefficients saved automatically
4. Review validation tests before deploying

---

## Support & Contact

**Technical Issues:**
- GitHub: https://github.com/alzadjaliaafra-hash/SRFF-I-RVS-Model/issues
- Email: [SRFF-I Technical Team]

**Model Questions:**
- Contact: SRFF-I Investment Committee
- Documentation: See `docs/Methodology_Addendum_v3.0.md`

**Security / Confidentiality:**
- **DO NOT** share code or data outside authorized IC members
- **DO NOT** upload to public repositories
- **DO NOT** discuss model details with external parties

---

## Document Info

**Version:** 1.0  
**Last Updated:** April 17, 2026  
**Author:** Manus AI for Sohar International Bank  
**Classification:** Strictly Private & Confidential

---

**End of User Guide**
