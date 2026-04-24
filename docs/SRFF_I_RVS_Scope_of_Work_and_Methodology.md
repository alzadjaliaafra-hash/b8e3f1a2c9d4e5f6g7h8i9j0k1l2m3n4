# SRFF-I Rescue Viability Score (RVS) — Complete Scope of Work & Methodology

**Inventor:** Aafra Al Zadjali
**Platform:** ALiF (Private Equity) — Powered by MURSHIDI Ai
**Classification:** Strictly Private & Confidential — Proprietary Intellectual Property
**Date:** April 18, 2026

---

## 1. Project Origin and Vision

The SRFF-I Rescue Viability Score (RVS) is a proprietary financial model invented by Aafra Al Zadjali to solve a fundamental gap in the GCC Islamic finance market: **there is no statistically validated, Shariah-compliant scoring engine for evaluating whether a distressed company is worth rescuing through structured financing.**

The project originated from three converging sources of expertise:

The first was a **private company case study** — a real distressed-company deal that Aafra structured as a Diminishing Musharaka rescue financing transaction. The case study analysis, LBO model, and fund framework (the "SRFF-I Fund") provided the practical foundation: real cash flows, real haircuts, real exit assumptions, and a real Investment Committee decision process.

The second was Aafra's **Cranfield University master's thesis**, which tested the predictive power of Altman Z-Score, Shumway Hazard Model, Black-Scholes-Merton (BSM), and Down-and-Out Call (DOC) models on 1,615 UK LSE-listed companies. This academic background in distress prediction models — their strengths, limitations, and implementation pitfalls — directly informed the design of the RVS.

The third was **Aswath Damodaran's valuation framework** for distressed and declining companies, which provided the theoretical rigour for survival probability weighting, cost of capital adjustments, and the treatment of negative earnings in valuation.

The vision is to deploy the RVS as the core screening engine within the ALiF platform, enabling Aafra's private equity practice to systematically identify, evaluate, and structure rescue financing deals across the GCC — starting with Oman's Muscat Stock Exchange (MSX) and expanding to private companies.

---

## 2. What Has Been Achieved — Complete Chronology

### Phase 0: Foundation (PharmaCo X Case Study & Fund Framework)

The project began with the SRFF-I Fund framework — a Shariah-compliant rescue financing fund designed to acquire distressed debt at a haircut and restructure it through Diminishing Musharaka. The PharmaCo X case study served as the prototype deal, with a full LBO model, sources and uses of funds, and exit analysis.

An expert review (conducted via Claude AI) identified a critical discrepancy between the Excel model returns (27.8% IRR, 3.94x MoM on incremental capital) and the narrative documents (13-15% IRR, 2.0-2.2x MoM blended). This was resolved by recalibrating the model: the Whole-Fund Blended IRR settled at 14.3% with a 1.83x MoM, and the fund's total income to the Lead Arranger (as LP) was projected at OMR 13.40 million on OMR 7.31M capital at risk.

**Key deliverables:** Revised PharmaCo X LBO model, SRFF-I Fund framework, HSBC-style presentation slides (Sources & Uses, financing structure, fact sheet appendix).

### Phase 1: The Original RVS Formula (v1.0)

The first version of the Rescue Viability Score was designed as a custom alternative to Altman Z-Score, specifically calibrated for rescue financing decisions rather than bankruptcy prediction. The critical distinction: Altman tells you whether a company will fail; the RVS tells you whether a distressed company is worth rescuing.

**The 6 Variables:**

| Variable | Formula | What It Measures |
|---|---|---|
| V1 | Working Capital / Total Assets | Short-term liquidity buffer |
| V2 | Retained Earnings / Total Assets | Cumulative profitability and reinvestment history |
| V3 | EBITDA / Total Debt | Debt service capacity from operations |
| V4 | Operating Cash Flow / Total Debt | Actual cash generation relative to debt burden |
| V5 | Collateral Value / Total Liabilities | Hard asset backing for rescue financing |
| V6 | Revenue / Total Assets | Asset utilisation efficiency |

The original v1.0 used expert-calibrated coefficients (not empirically derived) and was tested on a private company as the first calibration case. The test case scored RVS = 7.802, classified as a "Strong Rescue Candidate," consistent with its 90/100 IC score.

**Key deliverable:** RVS methodology document with formula, coefficient justification, and calibration walkthrough.

### Phase 2: First Backtesting (5 Companies)

The model was tested against 5 historically distressed companies (mix of recovered and failed) from public markets. Results:

- Altman Z-Score classified ALL 5 as "Distress Zone" with zero ability to distinguish survivors from failures
- The original RVS showed conservative bias — high specificity (catches failures) but low sensitivity (rejects viable candidates)
- 2 false negatives identified, suggesting the model needed calibration for large-scale companies with strong market positions

**Key finding:** The 6 variables had discriminatory power, but the expert-calibrated coefficients were not optimal. Empirical calibration was needed.

### Phase 3: Large-Scale Backtesting & Logistic Regression Calibration (v2.0)

A dataset of **47 companies** (2018-2024, known outcomes — recovered vs. failed) was assembled. The original expert-calibrated RVS achieved only 63.8% accuracy overall, though with 92.3% specificity and 94.7% precision.

**Logistic regression recalibration** was then performed on the same 6 variables using the 47-company dataset. This produced the v2.0 calibrated coefficients:

> **z = 2.5445 + 0.2506(V1) + 1.7070(V2) + 0.7426(V3) + 0.7262(V4) + 0.8278(V5) − 1.8122(V6)**

> **P(Recovery) = 1 / (1 + e^(−z))**

Results after calibration:

| Metric | v1.0 (Expert) | v2.0 (Calibrated) |
|---|---|---|
| Accuracy | 63.8% | 93.6% |
| AUC-ROC | — | 0.989 |
| Cross-Validated | — | 91.3% |
| Specificity | 92.3% | 100% |

**Key insight:** The 6 variables have exceptional discriminatory power (AUC-ROC 0.989) — they just needed empirically-derived coefficients. No new variables were required. This significantly outperforms Altman Z-Score (83.7%) and is comparable to Shumway (89.6%) on the same dataset.

**Key deliverables:** 47-company backtesting report, calibrated coefficients, confusion matrix, statistical analysis, Excel workbook with all company data.

### Phase 4: Damodaran Cross-Check & Gap Analysis

The calibrated v2.0 model was cross-checked against Aswath Damodaran's framework for valuing distressed companies. **Five gaps** were identified:

1. **Survival Probability Weighting** — Damodaran explicitly weights cash flows by survival probability; the RVS captured it implicitly but not explicitly
2. **Cost of Capital Adjustment** — No explicit adjustment for the elevated cost of capital in distressed situations
3. **Negative Earnings Treatment** — The model handled negative EBITDA but didn't have a formal framework for it
4. **Going Concern Discount** — No explicit going concern risk factor
5. **Temporal Stability** — The model hadn't been tested across different market cycles

All 5 gaps were addressed in Phase 5.

### Phase 5: Damodaran Gap Fixes + Academic Validation (10 Tests)

**Phase 5A — Fix the 5 Damodaran Gaps:**

Each gap was resolved with specific methodological enhancements:
- Survival probability weighting added to cash flow projections
- Cost of capital adjustment framework implemented
- Formal negative earnings treatment protocol established
- Going concern discount factor integrated
- Temporal stability tested across 2018-2024 market cycles (including COVID)

**Phase 5B — Academic Validation Suite (10 Tests):**

Ten rigorous statistical tests were designed and executed on the 47-company dataset, following academic standards from Shumway (2001), Chava & Jarrow (2004), and Ohlson (1980):

1. Confusion Matrix & Classification Accuracy
2. Temporal Stability (pre-COVID vs post-COVID)
3. Sector Robustness
4. Leave-One-Out Cross-Validation
5. Calibration (Hosmer-Lemeshow)
6. Variable Importance (Wald Statistics)
7. Multicollinearity (VIF)
8. Stress Testing (4 scenarios)
9. Threshold Sensitivity
10. Forward-Looking Validation

All 10 tests passed. The model demonstrated robust performance across sectors, time periods, and stress scenarios.

### Phase 6: Hazard Layer & RVS v3.0

The most significant upgrade: adding a **Shumway-style discrete-time hazard model** as a second layer on top of the logistic regression. This was directly inspired by Aafra's Cranfield thesis work on Shumway hazard models.

**The Hazard Model:**

> **h(t) = 1 / (1 + e^(−w))**

> **w = −1.9295 − 0.2312(V1) + 0.3298(V2) + 0.7437(V3) − 7.1443(V4) − 27.7134(V5) + 3.8640(V6) − 0.8840(TimeDummy) + 3.8256(COVID)**

Where TimeDummy = 1 for years 4-5 (late-stage risk) and COVID = 1 for 2020-2021.

The hazard layer produces a **5-year cumulative survival probability** for each company, which is then combined with P(Recovery) into the **Composite V3 Score:**

> **Composite V3 = 0.60 × P(Recovery) + 0.40 × (5-Year Survival)**

**Expanded Validation Suite (12 Tests):**

Two additional tests were added for the hazard layer:
- Test 11: Hazard Model Validation (AUC, calibration, survival separation)
- Test 12: Composite V3 Integration Test

**Final v3.0 Performance:**

| Metric | Result |
|---|---|
| Forward Accuracy | 93.0% |
| Hazard AUC | 0.985 |
| 5-Year Survival Separation | 91.8% (recovered) vs 14.7% (failed) |
| Specificity | 100% (zero false positives) |
| Composite V3 Accuracy | 93.0% |
| Leave-One-Out AUC | 0.979 |

All 12/12 tests PASS.

**Key deliverables:** srff_validation_v3.py (full 12-test suite), rvs_v3_with_hazard.xlsx (enhanced workbook), SRFF_I_RVS_V3_Validation_Report.md (academic report), validation_results_v3.json.

### Phase 7: Excel VBA Frontend

A production-ready Excel workbook (SRFF-I_RVS_v3.0_Frontend.xlsm) was built with 6 sheets:

1. **Input** — Company info + V1-V6 inputs (blue = user input, grey = auto-calculated)
2. **Scorecard** — Full RVS v3.0 analysis with LR score, hazard model, survival table, Composite V3, verdict
3. **Survival Curve** — 5-year line chart with threshold lines
4. **Stress Test** — 4 scenarios with verdict change tracking
5. **IC Summary** — Print-ready A4 executive summary
6. **Reference** — Full model documentation and version history

Pushed to GitHub on feature/excel-frontend branch, PR #6 open.

### Phase 8: Live Screening — 13 MSX Companies

The v3.0 model was deployed to screen 13 Muscat Stock Exchange companies across Financial, Industrial, and Services sectors:

| Verdict | Count | Companies |
|---|---|---|
| **GO** | 10 | SUWP, BATP, AFIC, AMAT, ORDS, RCCI, UBAR, ORCI, NGCI, NAPI |
| **CONDITIONAL** | 2 | AFAI, TAOI |
| **NO-GO** | 1 | AMCI |

Top candidates: Al Suwadi Power (Composite V3: 0.9626) and Al Batinah Power (0.9623) — both PPA-backed IPP utilities.

**Key deliverables:** 13-company screening report, Excel workbook (6 sheets), public data collection workbook (8 sheets with all data sourced and dated).

### Phase 9: RVS v4.0 — Private Company Model

A Damodaran-adjusted version specifically for non-publicly listed companies, addressing the fundamental challenge of scoring private firms with no market data:

**Damodaran Adjustments Added:**
- **Total Beta** (instead of market beta) — captures total risk for undiversified private owners
- **Synthetic Credit Rating** — derived from Interest Coverage Ratio using Damodaran's lookup tables
- **Illiquidity Discount** — 15-30% discount for lack of marketability
- **Key-Person Discount** — 5-25% for founder/owner dependency risk
- **Control/Minority Adjustment** — premium or discount based on stake size
- **Governance Quality Score** — formal scoring of board independence, audit quality, RPT exposure
- **Concentration Risk** — customer/supplier/geographic concentration penalties
- **Information Asymmetry Adjustment** — penalty for unaudited or inconsistent financials

**Accounting-Only Hazard Model** — no market variables required (replaces market-based inputs with governance and concentration risk factors).

**Shariah Compliance Screening** — automatic check: debt/total assets < 33% threshold, with automatic verdict downgrade if non-compliant.

**6 Stress Scenarios** (vs 4 in v3.0) — adds Key-Person Loss and Governance Collapse scenarios specific to private companies.

**Key deliverables:** srff_rvs_v4_private.py, SRFF-I_RVS_v4.0_Private_Frontend.xlsx, SRFF_I_RVS_V4_Methodology.md, SRFF_I_RVS_V4_Validation_Report.md, SRFF-I_RVS_v4.0_Analyst_Workbook.xlsx (8-sheet formula-driven), SRFF_I_RVS_V4_Analyst_Guide.md.

### Phase 12: PharmaCo X Case Study & CEO Negotiation

**Purpose:** End-to-end execution of a real-world distressed private company restructuring using the v4.0 Toolkit and Murshidi AI Deal Architect mode.

**Methodology:**
The PharmaCo X (PharmaCo X) case study was processed through the v4.0 toolkit, yielding a NO-GO baseline verdict due to an 89% Debt/Assets ratio and OMR -33.3M accumulated losses. 

Murshidi AI architected a rescue LBO featuring:
1. **Fulcrum Security Acquisition:** Buying OMR 20.3M in senior debt at a 45% haircut (the mathematical floor for Shariah compliance).
2. **Debt-for-Equity Swap:** Converting OMR 12.8M to equity to bring Debt/Assets below the 33% AAOIFI ceiling.
3. **Rescue Tranche (PSIA-Hybrid):** Injecting OMR 2.5M as a hybrid Profit-Sharing Investment Account (OMR 1.5M) and Commodity Murabaha (OMR 1.0M). This structure optimized the Year 2 DSCR (1.63x) and protected the Day 1 Shariah leverage ratio (18.8%).
4. **Anchor Lender Strategy:** Identifying the swing-vote lender to reach a 68.9% supermajority, enabling a cram-down of holdouts under Omani commercial law.
5. **Working Capital Plan B:** Structuring an OMR 1.5M Receivable Murabaha factoring facility to bridge potential Ministry of Health payment delays without breaching the 33% debt ceiling.

**Outcome:** The Lead Arranger's CEO moved from a 70% HOLD to an 82% NON-BINDING LOI, and finally to a **95% FULL EXECUTION AUTHORIZED** mandate based on the quantitative defense of the PSIA structure and exit multiples.

**Key deliverables:** PharmaCo X_LBO_Model_ALiF_v2.xlsx, ALiF_PharmaCo X_Term_Sheet.md, CEO_Response_Memo.md, Final_Confidence_Gap_Memo.md, PharmaCo X_Final_13pct_Gap.xlsx.

### Phase 12: Private Company Case Study & Institutional Negotiation

**Purpose:** End-to-end execution of a real-world distressed private company restructuring using the v4.0 Toolkit and Murshidi AI Deal Architect mode.

**Methodology:**
A GCC-based private pharmaceutical manufacturer was processed through the v4.0 toolkit, yielding a NO-GO baseline verdict due to an 89% Debt/Assets ratio and massive accumulated losses. 

Murshidi AI architected a rescue LBO featuring:
1. **Fulcrum Security Acquisition:** Buying OMR 20.3M in senior debt at a 45% haircut (the mathematical floor for Shariah compliance).
2. **Debt-for-Equity Swap:** Converting OMR 12.8M to equity to bring Debt/Assets below the 33% AAOIFI ceiling.
3. **Rescue Tranche (PSIA-Hybrid):** Injecting OMR 2.5M as a hybrid Profit-Sharing Investment Account (OMR 1.5M) and Commodity Murabaha (OMR 1.0M). This structure optimized the Year 2 DSCR (1.63x) and protected the Day 1 Shariah leverage ratio (18.8%).
4. **Anchor Lender Strategy:** Identifying the swing-vote lender to reach a 68.9% supermajority, enabling a cram-down of holdouts under commercial law.
5. **Working Capital Plan B:** Structuring an OMR 1.5M Receivable Murabaha factoring facility to bridge potential government payment delays without breaching the 33% debt ceiling.

**Outcome:** The Lead Arranger's Investment Committee moved from a 70% HOLD to an 82% NON-BINDING LOI, and finally to a **95% FULL EXECUTION AUTHORIZED** mandate based on the quantitative defense of the PSIA structure and exit multiples.

**Key deliverables:** LBO_Model_ALiF_v2.xlsx, ALiF_Term_Sheet.md, Institutional_Response_Memo.md, Final_Confidence_Gap_Memo.md, Final_13pct_Gap.xlsx.

### Phase 10: Supporting Tools & Deliverables

**M&A Reference Guide** — 85 numbered formulas extracted from "Mergers, Acquisitions, Divestitures, and Other Restructurings: A Practical Guide to Investment Banking and Private Equity." Covers income statement analysis, depreciation, accretion/dilution, balance sheet adjustments, working capital, debt schedules, FCF, EV/equity bridges, tax shields, and synergies.

**M&A Toolkit for Private Companies** — VBA-powered 7-sheet Excel workbook with Altman Z-Score (private formula), LBO analysis (MOIC, IRR), accretion-dilution, deal dashboard, and 9-metric traffic-light summary.

**Analyst Application Manual** — 18-slide PPTX/PDF using Raysut Cement (RCCI) as a worked example, showing actual financial statements in tables and pulling each number step by step through the scoring process.

**ALiF Global Macro Focus Report** — 3-page A4 landscape market intelligence report using v3.0 screening outcomes, framed as ALiF market research with zero disclosure of the proprietary scoring methodology.

### Phase 11: GitHub Repository & Collaboration

Repository: https://github.com/alzadjaliaafra-hash/SRFF-I-RVS-Model

All v3.0 files pushed to master with professional README. PR template established. 5 Issues backlog created. Three-person collaboration workflow active (Aafra + Manus + Grok).

---

## 3. Methodology Summary — The Two Models

### RVS v3.0 (Publicly Listed Companies)

**Layer 1 — Logistic Regression:**
Takes 6 accounting-based variables from audited financial statements. Produces P(Recovery) — the probability that a distressed company can be successfully rescued.

**Layer 2 — Shumway Hazard Model:**
Uses the same 6 variables plus time dummies to produce year-by-year hazard rates and a cumulative 5-year survival probability.

**Layer 3 — Composite V3:**
Combines both layers: 60% weight on P(Recovery) + 40% weight on 5-Year Survival.

**Output:** GO (≥0.70) / CONDITIONAL (0.50-0.69) / NO-GO (<0.50)

### RVS v4.0 (Private Companies)

Same core architecture as v3.0, plus:
- Damodaran adjustments for Total Beta, synthetic credit rating, illiquidity, key-person risk
- Governance and concentration risk scoring
- Accounting-only hazard model (no market data)
- Shariah compliance screening with automatic downgrade
- 6 stress scenarios (2 additional private-company-specific)

---

## 4. What Is Pending — Methodology for Remaining Work

### Issue #2: IC Dashboard
**Purpose:** A one-page Investment Committee decision support dashboard.
**Methodology:** Aggregate the Composite V3 score, survival curve, stress test results, and expected fund income into a single visual dashboard. Include deal-level P&L projection (Sources & Uses, IRR, MoM) alongside the RVS verdict. Format: Excel or web-based, designed for projection in IC meetings.

### Issue #3: Monthly Monitoring Module
**Purpose:** Post-deployment early-warning system for portfolio companies.
**Methodology:** After a rescue financing deal is deployed, the monitoring module takes actual monthly/quarterly financial data and re-computes the survival probability in real time. If the hazard rate exceeds a pre-set threshold (e.g., cumulative survival drops below 65%), the system triggers an alert. This follows Shumway's (2001) dynamic hazard framework — the model updates as new data arrives, unlike static models like Altman that score once and assume stationarity. The module will track V1-V6 trends over time and flag deterioration in any individual variable before the composite score triggers.

### Issue #4: Forward-Looking Screening Automation
**Purpose:** Automate the pipeline screening for new distressed names.
**Methodology:** Build a data pipeline that periodically pulls financial data from MSX disclosures, annual reports, and financial databases for a watchlist of companies. Automatically compute V1-V6, run the logistic regression and hazard model, and produce a ranked pipeline report. This transforms the RVS from a one-time scoring tool into a continuous screening engine. For private companies (v4.0), the pipeline would accept manual data uploads (Excel, PDF) and compute scores on demand.

### Issue #5: Documentation
**Purpose:** IC Memo Template and Methodology Addendum.
**Methodology:** Produce two documents: (1) A standardised IC Memo template that any analyst can fill in after running the RVS, containing the company profile, variable values, scores, stress test results, deal structure recommendation, and risk factors. (2) A Methodology Addendum suitable for external review (e.g., by the Lead Arranger's risk committee or external auditors), documenting the statistical foundations, validation results, and limitations of the model without disclosing proprietary coefficients.

### v4.0 Analyst Slide Deck
**Purpose:** Same as the v3.0 slide deck (18-slide PPTX) but for private companies, incorporating the Damodaran adjustments and governance scoring.

### Model Enhancement via M&A Book Formulas
**Purpose:** Integrate relevant formulas from the M&A reference guide into the RVS toolkit — particularly the Sources & Uses framework, purchase price allocation, and synergy analysis — to create a complete deal structuring workflow that flows from RVS screening → deal evaluation → IC presentation.

---

## 5. Intellectual Property Summary

| Component | Status | IP Owner |
|---|---|---|
| RVS v3.0 Formula & Coefficients | Complete | Aafra Al Zadjali |
| RVS v4.0 Private Company Model | Complete | Aafra Al Zadjali |
| Hazard Layer Design & Coefficients | Complete | Aafra Al Zadjali |
| Composite V3 Scoring Framework | Complete | Aafra Al Zadjali |
| 47-Company Validation Dataset | Complete | Aafra Al Zadjali |
| SRFF-I Fund Framework | Complete | Aafra Al Zadjali |
| ALiF Platform & MURSHIDI Ai | In Development | Aafra Al Zadjali |
| All Excel Toolkits & VBA Code | Complete | Aafra Al Zadjali |
| All Python Validation Scripts | Complete | Aafra Al Zadjali |

the Lead Arranger is an interested party and potential LP in the SRFF-I Fund. They are not the owner of the methodology, the model, or any associated intellectual property. The RVS is Aafra Al Zadjali's proprietary invention, developed through the ALiF platform.

---

*Document Version: 1.0 — April 18, 2026*
*Prepared by: Manus AI on behalf of Aafra Al Zadjali*
