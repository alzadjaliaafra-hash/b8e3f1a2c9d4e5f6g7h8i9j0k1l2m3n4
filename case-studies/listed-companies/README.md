# SRFF-I v3.0 — Listed Company Screening

**Model Version:** SRFF-I RVS v3.0 (Listed/Public Company Edition)  
**Market:** Muscat Stock Exchange (MSX), Oman  
**Universe:** 13 companies across Financial, Industrial, and Services sectors  
**Status:** Completed screening

---

## Model Overview

The v3.0 model applies the core 6-variable logistic regression to listed companies using publicly reported financials. No private company adjustments (owner comp add-backs, RPT haircuts, collateral appraisal factors) are applied.

**Core Formula:**
z = 2.5445 + 0.2506(V1) + 1.7070(V2) + 0.7426(V3) + 0.7262(V4) + 0.8278(V5) - 1.8122(V6)

**Composite V3 Score** = 0.60 × P(Recovery) + 0.40 × S(5yr)

**Verdict Thresholds:** GO ≥ 0.65 | CONDITIONAL 0.50–0.64 | NO-GO < 0.50

---

## Screening Results Summary

| Verdict | Count | % |
|---|---|---|
| GO | 10 | 76.9% |
| CONDITIONAL | 2 | 15.4% |
| NO-GO | 1 | 7.7% |

**Sector Pass Rates:** Financial 100% | Services 100% | Industrial 80%

---

## Files in This Directory

| File | Description |
|---|---|
| `SRFF_I_13_Company_Screening.xlsx` | Full screening workbook (6 sheets: Executive Summary, Detailed Financials, RVS Scorecard, Hazard Analysis, Stress Test Results, Sector Analysis) |
| `listed-company-model.md` | v3.0 model reference: formulas, hazard model, composite score, stress scenarios |

---

**Powered by MURSHIDI Ai**  
*Solving Patterns, Revealing Value*
