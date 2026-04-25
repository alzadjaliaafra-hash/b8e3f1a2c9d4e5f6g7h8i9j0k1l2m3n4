# SRFF-I v3.0 Listed Company Model

This document serves as the permanent reference for the SRFF-I v3.0 Listed Company Model, as used in the 13-company Omani market screening.

## 1. Core Logistic Regression (v3.0)

The model relies on the 6-variable logistic regression:
$z = 2.5445 + 0.2506(V_1) + 1.7070(V_2) + 0.7426(V_3) + 0.7262(V_4) + 0.8278(V_5) - 1.8122(V_6)$
$P(\text{Recovery}) = \frac{1}{1+e^{-z}}$

Where:
- $V_1$ = Working Capital / Total Assets
- $V_2$ = Retained Earnings / Total Assets
- $V_3$ = EBITDA / Total Debt
- $V_4$ = Operating Cash Flow / Total Debt
- $V_5$ = Collateral Value (Net PPE + Inventory) / Total Liabilities
- $V_6$ = Revenue / Total Assets

*Note: For listed companies, no private adjustments (RPT haircuts, owner comp add-backs) are applied. Raw reported financials are used directly.*

## 2. Hazard Model (Shumway 2001)

The discrete-time hazard model predicts the probability of failure in any given year:
$h(t) = \frac{1}{1+e^{-z_h(t)}}$

Where $z_h(t)$ uses the same variables but different coefficients, optimized for hazard:
$z_h(t) = -3.0 + 0.15(V_1) + 0.80(V_2) + 0.45(V_3) + 0.40(V_4) + 0.50(V_5) - 0.90(V_6)$

**Annual Decay:**
Financial strength decays over time without intervention:
$V(k,t) = V(k,0) \times 0.95^{(t-1)}$ (5% annual decay)

**5-Year Survival Probability:**
$S(5) = \prod_{t=1}^5 (1 - h(t))$

## 3. Composite V3 Score & Verdict

The final score blends the static recovery probability with the dynamic survival probability:
**Composite V3** = $0.60 \times P(\text{Recovery}) + 0.40 \times S(5)$

**Verdict Thresholds:**
- **GO**: Composite ≥ 0.65
- **CONDITIONAL**: Composite 0.50–0.64
- **NO-GO**: Composite < 0.50

## 4. Stress Testing Scenarios

The model requires running four standard stress tests to evaluate resilience:
1. **Working Capital Crisis**: $V_1$ drops by 50%, $V_4$ drops by 30%
2. **Margin Compression**: $V_3$ drops by 40%, $V_6$ increases by 20%
3. **Refinancing Crisis**: $V_3$ drops by 60%, $V_5$ drops by 25%
4. **Perfect Storm**: All the above shocks combined simultaneously

**Resilience Rating:**
- **Robust**: 0 verdict downgrades across all 4 scenarios
- **Moderate**: 1-2 verdict downgrades
- **Fragile**: 3-4 verdict downgrades

## 5. Market Screening Output (Oman 13-Company Case)

In the 13-company screening of the Omani market:
- **10 GO** (Robust resilience)
- **2 CONDITIONAL** (Robust resilience)
- **1 NO-GO** (Robust resilience)

*Sectors covered: Financial (3), Industrial (5), Services (5).*
