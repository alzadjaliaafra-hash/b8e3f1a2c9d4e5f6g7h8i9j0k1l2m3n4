# SRFF-I Enhanced Rescue Viability Score (RVS v2.0) Methodology
## Incorporating Damodaran's Distressed Firm Valuation Framework

**Prepared for:** Sohar International Bank — SRFF-I Investment Committee  
**Prepared by:** Manus AI  
**Date:** April 17, 2026  
**Classification:** Strictly Private and Confidential  
**Version:** 2.0

---

## Executive Summary

A systematic cross-check of the SRFF-I Rescue Viability Score against Aswath Damodaran's *Investment Valuation* framework identified five gaps in the methodology's treatment of distressed firm valuation. This document presents the **Enhanced RVS v2.0**, which resolves all five gaps while preserving the Islamic finance constraints and governance scoring that make the SRFF-I framework unique.

The five enhancements are:

1. **Survival Probability Weighting** — explicitly discounts the RVS by the cumulative probability that the firm survives the restructuring period, replacing the implicit assumption of 100% survival.
2. **Sector-Specific Bankruptcy Cost Adjustments** — modifies the collateral coverage variable to reflect that liquidation costs vary dramatically by industry (from 15% for technology to 40%+ for financial services).
3. **Option-Adjusted Equity Valuation** — adds a Black-Scholes cross-check for public companies that captures the convexity of distressed equity value.
4. **Explicit Tax Shield Analysis** — quantifies the value destroyed when restructuring reduces the firm's debt (and therefore its interest tax shields) using the APV framework.
5. **Merton Distance-to-Default** — provides a market-based default probability estimate for listed targets as a cross-check against the accounting-based RVS.

Enhancements 1 and 2 are integrated directly into the RVS formula. Enhancements 3, 4, and 5 are implemented as supplementary analytical modules that produce independent cross-check metrics alongside the core RVS score.

For the NPI anchor case, the Enhanced RVS produces a score of **7.15** (down from the original 7.80), correctly maintaining its "Strong Rescue Candidate" classification while mathematically penalizing the inherent survival risk that the original model ignored.

---

## Part 1: The Enhanced RVS Formula

### 1.1 Original Formula (v1.0)

The original RVS formula is a six-variable linear discriminant model calibrated against the NPI anchor case [1]:

> **RVS = 0.90($V_1$) + 1.05($V_2$) + 5.85($V_3$) + 13.80($V_4$) + 1.10($V_5$) + 1.15($V_6$)**

This formula assumes that the firm survives the entire restructuring period (implicit 100% survival probability) and applies identical liquidation cost assumptions regardless of sector. Both assumptions are inconsistent with Damodaran's framework for valuing distressed firms [2].

### 1.2 Enhanced Formula (v2.0)

The Enhanced RVS modifies the core equation in two ways: (a) the collateral coverage variable $V_2$ is adjusted by a sector-specific bankruptcy cost factor, and (b) the entire score is multiplied by a Survival Adjustment Factor.

> **Enhanced RVS = $\left[ 0.90(V_1) + 1.05(V_2^{\text{adj}}) + 5.85(V_3) + 13.80(V_4) + 1.10(V_5) + 1.15(V_6) \right] \times \text{SAF}$**

Where:

- $V_2^{\text{adj}} = V_2 \times S_{\text{adj}}$ is the **Sector-Adjusted Collateral Coverage Ratio**
- $\text{SAF} = \frac{1}{T} \sum_{t=1}^{T} (1 - p)^t$ is the **Survival Adjustment Factor**
- $S_{\text{adj}}$ is the sector-specific bankruptcy cost adjustment factor
- $p$ is the estimated annual default probability
- $T$ is the projection horizon in years (typically 3)

### 1.3 Complete Variable Specification

| Symbol | Variable Name | Coefficient | Range | Enhancement |
| :--- | :--- | :---: | :---: | :--- |
| $V_1$ | Projected DSCR (Year 3) | 0.90 | 0.5 – 3.0 | Unchanged |
| $V_2^{\text{adj}}$ | Sector-Adjusted Collateral Coverage | 1.05 | 0.5 – 2.5 | **Gap 2: Sector adjustment** |
| $V_3$ | Projected EBITDA Margin (Year 3) | 5.85 | 0.02 – 0.35 | Unchanged |
| $V_4$ | Entry EBITDA-to-Debt Ratio | 13.80 | 0.03 – 0.25 | Unchanged |
| $V_5$ | Asset Identifiability Ratio | 1.10 | 0.2 – 0.9 | Unchanged |
| $V_6$ | GP Control Factor | 1.15 | 0.0 – 1.0 | Unchanged |
| SAF | Survival Adjustment Factor | Multiplier | 0.5 – 1.0 | **Gap 1: Survival weighting** |

### 1.4 Interpretation Zones (Unchanged)

| RVS Range | Classification | Decision |
| :---: | :--- | :--- |
| > 7.0 | Strong Rescue Candidate | Proceed to full due diligence and Shariah structuring |
| 4.5 – 7.0 | Conditional Candidate | Proceed with enhanced safeguards |
| < 4.5 | Reject | Do not pursue |

---

## Part 2: Enhancement Details

### 2.1 Enhancement 1 — Survival Probability Weighting

#### Theoretical Foundation

Damodaran's framework for valuing distressed firms requires that cash flows be explicitly weighted by the probability that the firm survives to generate them [2]. The standard DCF approach implicitly assumes 100% survival, which systematically overvalues distressed firms. The survival-adjusted DCF is:

> $\text{Value} = \sum_{t=1}^{n} \frac{CF_t \times P(\text{survival to year } t)}{(1 + \text{WACC})^t}$

The survival probability can be estimated from historical bankruptcy rates for the firm's sector and distress level, credit spreads on the firm's outstanding debt, or hazard models such as Shumway (2001) [3] or Campbell, Hilscher, and Szilagyi (2008) [4].

#### Integration into the RVS

Rather than modifying each variable individually, the Enhanced RVS applies the survival adjustment as a single multiplicative factor on the total score. This is mathematically equivalent to weighting each variable's contribution by the same survival probability, which is appropriate because all six variables measure aspects of the same firm's viability over the same time horizon.

The **Survival Adjustment Factor (SAF)** is calculated as the arithmetic mean of the cumulative survival probabilities over the projection horizon:

> $\text{SAF} = \frac{1}{T} \sum_{t=1}^{T} (1 - p)^t$

Where $p$ is the annual default probability and $T$ is the projection horizon (default: 3 years for the SRFF-I restructuring period).

#### Estimating the Annual Default Probability

The annual default probability $p$ should be estimated using the following hierarchy of methods, in order of preference:

| Method | Data Required | Applicability | Reference |
| :--- | :--- | :--- | :--- |
| Merton model (Enhancement 5) | Market cap, equity volatility | Public companies | Merton (1974) [5] |
| Credit spread decomposition | Bond yield spread over risk-free | Firms with traded debt | Damodaran Ch. 22 [2] |
| Sector historical rates | Moody's/Fitch default tables | All firms | Moody's Annual Default Study |
| RVS-implied estimate | RVS score itself | Fallback for private firms | Internal calibration |

For the fallback method, the following mapping from RVS score to implied annual default probability is recommended:

| RVS Score | Implied Annual Default Probability |
| :---: | :---: |
| > 8.0 | 3% |
| 7.0 – 8.0 | 5% |
| 5.5 – 7.0 | 8% |
| 4.5 – 5.5 | 12% |
| < 4.5 | 20%+ |

#### Worked Example (NPI)

NPI is a distressed pharmaceutical manufacturer with an original RVS of 7.80. Using a 5% annual default probability (consistent with a "Strong" candidate in a defensive sector):

- Year 1 survival: $(1 - 0.05)^1 = 0.9500$
- Year 2 survival: $(1 - 0.05)^2 = 0.9025$
- Year 3 survival: $(1 - 0.05)^3 = 0.8574$
- **SAF** = $(0.9500 + 0.9025 + 0.8574) / 3 = 0.9033$

#### Sensitivity Analysis

The following table shows how the Enhanced RVS for NPI varies with different default probability assumptions:

| Annual Default Prob. | SAF | Enhanced RVS | Zone |
| :---: | :---: | :---: | :--- |
| 0% | 1.0000 | 7.912 | Strong |
| 3% | 0.9412 | 7.447 | Strong |
| 5% | 0.9033 | 7.147 | Strong |
| 8% | 0.8484 | 6.712 | Conditional |
| 10% | 0.8130 | 6.433 | Conditional |
| 15% | 0.7289 | 5.767 | Conditional |
| 20% | 0.6507 | 5.148 | Conditional |

The SAF provides a natural "tipping point" mechanism: NPI remains in the Strong zone up to approximately 7% annual default probability, beyond which it drops to Conditional. This is a desirable property — it forces the IC to explicitly justify its survival assumption rather than implicitly assuming 100%.

---

### 2.2 Enhancement 2 — Sector-Specific Bankruptcy Cost Adjustments

#### Theoretical Foundation

Damodaran's APV framework explicitly adjusts firm value for expected bankruptcy costs, which vary dramatically by sector [2]. A retail firm facing liquidation loses 30–40% of firm value to inventory obsolescence, lease breakage costs, and brand destruction. A technology firm loses only 10–15% because its assets (primarily intellectual property and human capital) can be redeployed quickly. The original RVS applied identical liquidation haircuts regardless of sector, which systematically overvalued collateral for high-bankruptcy-cost sectors and undervalued it for low-cost sectors.

#### Implementation

The sector adjustment factor $S_{\text{adj}}$ modifies the raw collateral coverage ratio $V_2$ before it enters the RVS formula:

> $V_2^{\text{adj}} = V_2 \times S_{\text{adj}}$

The adjustment factors are calibrated relative to the manufacturing baseline (25% bankruptcy cost = 1.00):

| Sector | Expected Bankruptcy Cost | $S_{\text{adj}}$ | Rationale |
| :--- | :---: | :---: | :--- |
| Technology | 15% | 1.13 | Low tangible assets; quick IP redeployment |
| Healthcare / Pharma | 20% | 1.07 | Regulated assets retain value; essential products |
| Logistics | 22% | 1.04 | Fleet and warehouse assets have secondary markets |
| Manufacturing | 25% | 1.00 | Baseline — specialized equipment, moderate costs |
| Telecom | 28% | 0.93 | Network assets are location-specific; high switching costs |
| Oil & Gas | 30% | 0.90 | Environmental liabilities; commodity price exposure |
| Retail | 35% | 0.87 | Inventory obsolescence; lease obligations; brand destruction |
| Financial Services | 40%+ | 0.80 | Regulatory constraints; depositor/counterparty runs |

#### Worked Example (NPI)

NPI operates in the pharmaceutical manufacturing sector, classified as Healthcare/Pharma:

- Raw $V_2$ = 1.50
- $S_{\text{adj}}$ = 1.07 (Healthcare)
- $V_2^{\text{adj}}$ = 1.50 x 1.07 = **1.605**

The adjustment reflects the fact that pharmaceutical manufacturing equipment, regulatory licences, and branded drug portfolios retain higher value in liquidation than generic manufacturing assets.

#### Sector Sensitivity (NPI Base Case)

| Sector | $S_{\text{adj}}$ | $V_2^{\text{adj}}$ | Enhanced RVS | Zone |
| :--- | :---: | :---: | :---: | :--- |
| Technology | 1.13 | 1.695 | 7.232 | Strong |
| Healthcare | 1.07 | 1.605 | 7.147 | Strong |
| Logistics | 1.04 | 1.560 | 7.104 | Strong |
| Manufacturing | 1.00 | 1.500 | 7.047 | Strong |
| Telecom | 0.93 | 1.395 | 6.948 | Conditional |
| Oil & Gas | 0.90 | 1.350 | 6.905 | Conditional |
| Retail | 0.87 | 1.305 | 6.862 | Conditional |
| Financial Services | 0.80 | 1.200 | 6.763 | Conditional |

The sector adjustment creates meaningful differentiation: the same company would score "Strong" in healthcare but "Conditional" in retail, reflecting the genuine difference in liquidation recovery dynamics.

---

### 2.3 Enhancement 3 — Option-Adjusted Equity Valuation (Black-Scholes)

#### Theoretical Foundation

Damodaran explicitly treats distressed firm equity as a European call option on the firm's value, with the strike price equal to the face value of debt [2]. This captures the **convexity** of distressed equity — small improvements in firm value produce disproportionately large improvements in equity value. For a firm where $V < D$ (i.e., the firm is technically insolvent), the equity still has positive value because there is a non-zero probability that the firm's value will exceed the debt threshold before maturity.

The Black-Scholes formula gives:

> $\text{Equity Value} = V \cdot N(d_1) - D \cdot e^{-rt} \cdot N(d_2)$

Where:

- $V$ = Current firm value (estimated via DCF)
- $D$ = Face value of outstanding debt
- $r$ = Risk-free rate (Oman government bond yield)
- $t$ = Time to debt maturity or restructuring horizon
- $\sigma$ = Volatility of firm value
- $d_1 = \frac{\ln(V/D) + (r + \sigma^2/2)t}{\sigma\sqrt{t}}$
- $d_2 = d_1 - \sigma\sqrt{t}$
- $N(\cdot)$ = Standard normal cumulative distribution function

#### Applicability

This module is applicable **only to publicly traded companies** where equity volatility is observable. For private companies (the majority of SRFF-I targets), the module should be skipped unless peer-derived volatility estimates are available.

#### Worked Example (NPI)

NPI is listed on the Oman MSX. Using illustrative market data:

| Parameter | Value | Source |
| :--- | :---: | :--- |
| Firm Value ($V$) | OMR 20,000K | DCF estimate |
| Face Value Debt ($D$) | OMR 25,714K | Restructured debt facility |
| Risk-Free Rate ($r$) | 4.50% | Oman 5-year government bond |
| Time to Maturity ($t$) | 5.0 years | Restructuring horizon |
| Firm Volatility ($\sigma$) | 40.0% | Estimated from sector peers |

**Calculation:**

- $d_1 = \frac{\ln(20{,}000/25{,}714) + (0.045 + 0.16/2) \times 5}{0.40 \times \sqrt{5}} = \frac{-0.2513 + 0.625}{0.8944} = +0.4178$
- $d_2 = 0.4178 - 0.8944 = -0.4766$
- $N(d_1) = N(0.4178) = 0.6620$
- $N(d_2) = N(-0.4766) = 0.3168$
- **Equity Value** = $20{,}000 \times 0.6620 - 25{,}714 \times e^{-0.045 \times 5} \times 0.3168$
- **Equity Value** = $13{,}240 - 25{,}714 \times 0.7985 \times 0.3168$
- **Equity Value** = $13{,}240 - 6{,}506 = $ **OMR 6,734K**

#### Interpretation

Despite NPI being technically insolvent (firm value of OMR 20M is less than debt of OMR 25.7M), the option-adjusted equity value is **OMR 6.7M**. This reflects the probability that the restructuring will succeed and push firm value above the debt threshold. If the fund can acquire equity at a significant discount to OMR 6.7M, the deal offers attractive risk-adjusted returns. This cross-check validates the RVS's "Strong" classification — the option market would price NPI's equity as having substantial value.

---

### 2.4 Enhancement 4 — Explicit Tax Shield Analysis (APV Framework)

#### Theoretical Foundation

The Adjusted Present Value (APV) framework decomposes firm value into three components [2]:

> $\text{Value of Firm} = \text{Value if All-Equity Financed} + \text{PV of Tax Shields} - \text{Expected Bankruptcy Costs}$

In a restructuring, debt is typically written down or converted to equity. This deleveraging destroys the tax shields generated by interest payments — a real economic cost that the standard WACC-based valuation captures only implicitly. The APV framework requires explicit quantification.

#### Implementation

The tax shield analysis calculates the present value of interest tax shields before and after restructuring:

> $\text{PV of Tax Shields} = \sum_{t=1}^{n} \frac{\text{Interest}_t \times \tau}{(1 + k_d)^t}$

Where $\tau$ is the corporate tax rate and $k_d$ is the cost of debt (used as the discount rate for tax shields, following the Miles-Ezzell convention).

For a constant debt level and interest rate, this simplifies to an annuity:

> $\text{PV of Tax Shields} = (\text{Debt} \times r_d \times \tau) \times \frac{1 - (1 + k_d)^{-n}}{k_d}$

#### Worked Example (NPI)

| Parameter | Pre-Restructuring | Post-Restructuring |
| :--- | :---: | :---: |
| Total Debt | OMR 25,714K | OMR 15,000K |
| Average Interest Rate | 8.0% | 6.0% |
| Corporate Tax Rate | 15% | 15% |
| Annual Tax Shield | OMR 309K | OMR 135K |
| PV of Tax Shields (5yr) | OMR 1,300K | OMR 569K |

**Tax Shield Value Destroyed by Restructuring:** OMR 1,300K - OMR 569K = **OMR 731K**

This means the restructuring destroys approximately OMR 731K in tax shield value over the 5-year horizon. The IC must ensure that the operational value created by the restructuring (improved EBITDA, reduced distress costs) exceeds this tax shield loss. For NPI, the projected EBITDA improvement from OMR 2.9M to OMR 5.8M (a OMR 2.9M annual increase) far exceeds the OMR 731K cumulative tax shield loss, confirming the restructuring is value-accretive.

#### Excel Toolkit Integration

A new worksheet titled **"APV Tax Shield Analysis"** should be added to the SRFF-I toolkit with the following structure:

| Row | Item | Formula |
| :--- | :--- | :--- |
| A | Pre-Restructuring Debt | Input |
| B | Pre-Restructuring Interest Rate | Input |
| C | Post-Restructuring Debt | Input |
| D | Post-Restructuring Interest Rate | Input |
| E | Corporate Tax Rate | Input |
| F | Discount Rate ($k_d$) | Input |
| G | Horizon (years) | Input |
| H | Annual Pre-Tax Shield | = A x B x E |
| I | Annual Post-Tax Shield | = C x D x E |
| J | Annuity Factor | = (1 - (1+F)^(-G)) / F |
| K | PV Pre-Tax Shields | = H x J |
| L | PV Post-Tax Shields | = I x J |
| M | **Value Destroyed** | = K - L |

---

### 2.5 Enhancement 5 — Merton Distance-to-Default

#### Theoretical Foundation

The Merton (1974) structural model treats the firm's equity as a call option on its assets, with the default boundary equal to the face value of debt [5]. The **distance-to-default (DD)** measures how many standard deviations the firm's asset value is above the default point:

> $DD = \frac{\ln(V/D) + (r - \sigma_V^2/2)T}{\sigma_V\sqrt{T}}$

The probability of default is then:

> $P(\text{Default}) = N(-DD)$

Where $N(\cdot)$ is the standard normal CDF. A higher DD indicates greater distance from default and lower default risk.

#### Applicability

This module is applicable **only to publicly traded companies** where market capitalization and equity volatility are observable. For private companies, the Merton model cannot be applied without significant assumptions.

#### Simplified Firm Value and Volatility Estimation

For the simplified implementation, firm value and volatility are estimated as:

- $V = E + D$ (market cap plus face value of debt)
- $\sigma_V = \sigma_E \times \frac{E}{V}$ (leverage-adjusted equity volatility)

A more rigorous implementation would solve the Merton system of equations iteratively, but the simplified approach is sufficient for cross-check purposes.

#### Worked Example (NPI)

| Parameter | Value | Source |
| :--- | :---: | :--- |
| Market Cap ($E$) | OMR 2,000K | MSX market data (distressed) |
| Face Value Debt ($D$) | OMR 25,714K | Restructured debt facility |
| Equity Volatility ($\sigma_E$) | 65.0% | 2-year historical (MSX) |
| Risk-Free Rate ($r$) | 4.50% | Oman government bond |
| Time Horizon ($T$) | 1.0 year | Standard Merton horizon |

**Calculation:**

- $V = 2{,}000 + 25{,}714 = 27{,}714$
- $\sigma_V = 0.65 \times (2{,}000 / 27{,}714) = 0.0469$ (4.69%)
- $DD = \frac{\ln(27{,}714 / 25{,}714) + (0.045 - 0.0469^2/2) \times 1}{0.0469 \times 1} = \frac{0.0750 + 0.0439}{0.0469} = +2.533$
- $P(\text{Default}) = N(-2.533) = 0.57\%$

#### Interpretation

The Merton model implies a very low default probability of 0.57% for NPI. This is because the firm's total asset value (OMR 27.7M) comfortably exceeds the debt threshold (OMR 25.7M), and the low firm-level volatility (4.69%, dampened by the high debt-to-equity ratio) means the probability of assets falling below the debt level within one year is minimal.

**Cross-Check Decision Rule:** If the Merton-implied default probability exceeds 25% while the RVS classifies the deal as "Strong," the IC must halt the transaction and investigate the market-accounting divergence before proceeding.

---

## Part 3: Comprehensive NPI Worked Example

### 3.1 Enhanced RVS Calculation

The following table presents the complete Enhanced RVS calculation for NPI, showing both the original and enhanced contributions:

| Step | Variable | Raw Value | Adjustment | Adjusted Value | Coefficient | Contribution |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| 1 | $V_1$: DSCR (FY2027) | 2.15 | — | 2.15 | 0.90 | 1.935 |
| 2 | $V_2$: Collateral Coverage | 1.50 | x 1.07 (Healthcare) | 1.605 | 1.05 | 1.685 |
| 3 | $V_3$: EBITDA Margin (FY2027) | 0.200 | — | 0.200 | 5.85 | 1.170 |
| 4 | $V_4$: EBITDA / Total Debt | 0.113 | — | 0.113 | 13.80 | 1.559 |
| 5 | $V_5$: Asset Identifiability | 0.72 | — | 0.72 | 1.10 | 0.792 |
| 6 | $V_6$: GP Control | 0.67 | — | 0.67 | 1.15 | 0.770 |
| | **Pre-SAF Total** | | | | | **7.912** |
| 7 | SAF (5% default, 3yr) | | | 0.9033 | Multiplier | x 0.9033 |
| | **Enhanced RVS** | | | | | **7.147** |

**Classification:** Strong Rescue Candidate (> 7.0)

### 3.2 Score Comparison

| Metric | Original RVS | Enhanced RVS | Change |
| :--- | :---: | :---: | :---: |
| Score | 7.802 | 7.147 | -0.655 |
| Zone | Strong | Strong | Unchanged |
| V2 Contribution | 1.575 | 1.685 | +0.110 (sector premium) |
| SAF Impact | 1.000 | 0.903 | -0.097 (survival penalty) |

The sector adjustment adds 0.110 points (reflecting NPI's favorable healthcare classification), but the survival adjustment removes 0.765 points (reflecting the ~10% cumulative default risk over 3 years). The net effect is a 0.655-point reduction, which is the correct direction — the original model was systematically optimistic by ignoring survival risk.

### 3.3 Stress Scenarios (Enhanced)

| Scenario | Original RVS | Enhanced RVS | SAF | Zone |
| :--- | :---: | :---: | :---: | :--- |
| Base Case | 7.802 | 7.147 | 0.903 | Strong |
| EBITDA Stress (-30%) | 6.397 | 5.520 | 0.848 | Conditional |
| KSA Plant Delay (24m) | 6.744 | 5.919 | 0.866 | Conditional |
| KSA Total Write-Off | 6.047 | 4.976 | 0.813 | Conditional |
| Liquidity Crisis | 7.303 | 6.283 | 0.848 | Conditional |
| Combined Worst Case | 4.062 | 3.004 | 0.729 | Reject |

The enhanced model produces more conservative scores across all stress scenarios, which is appropriate. Notably, the "KSA Total Write-Off" scenario now scores 4.98 (just above the 4.5 Reject threshold), compared to 6.05 in the original model. This reflects the compounding effect of higher default probability (10% in the write-off scenario) on the survival adjustment, making the model more sensitive to severe downside risks.

### 3.4 Supplementary Cross-Check Summary

| Module | Key Output | Interpretation |
| :--- | :--- | :--- |
| Black-Scholes Equity | OMR 6,734K | Equity has substantial option value despite insolvency |
| Tax Shield Loss | OMR 731K destroyed | Restructuring value creation (OMR 2.9M/yr) far exceeds tax shield loss |
| Merton Default Prob. | 0.57% | Market implies very low near-term default risk |

---

## Part 4: Implementation Guidance for the Excel Toolkit

### 4.1 Modifications to the RVS Calculator Sheet

The existing RVS calculator sheet requires two modifications:

**Modification A — Sector Selector.** Add a dropdown cell (e.g., cell B3) with the eight sector options. Use a VLOOKUP table to map the selected sector to its $S_{\text{adj}}$ factor. Multiply the raw $V_2$ value by this factor before it enters the RVS formula.

**Modification B — Survival Adjustment.** Add three input cells: (a) Annual Default Probability ($p$), (b) Projection Horizon ($T$, default 3), and (c) a calculated SAF cell using the formula:

```
SAF = AVERAGE((1-p)^1, (1-p)^2, (1-p)^3)
```

In Excel syntax: `=AVERAGE((1-B5)^1, (1-B5)^2, (1-B5)^3)`

Multiply the pre-SAF RVS total by the SAF to produce the Enhanced RVS.

### 4.2 New Worksheet: Option-Adjusted Valuation

Create a new worksheet for public company targets with the following inputs and calculations:

| Cell | Label | Formula |
| :--- | :--- | :--- |
| B2 | Firm Value (V) | Input |
| B3 | Face Value Debt (D) | Input |
| B4 | Risk-Free Rate (r) | Input |
| B5 | Time to Maturity (t) | Input |
| B6 | Firm Volatility (sigma) | Input |
| B8 | d1 | `=(LN(B2/B3)+(B4+B6^2/2)*B5)/(B6*SQRT(B5))` |
| B9 | d2 | `=B8-B6*SQRT(B5)` |
| B10 | N(d1) | `=NORM.S.DIST(B8,TRUE)` |
| B11 | N(d2) | `=NORM.S.DIST(B9,TRUE)` |
| B13 | **Equity Value** | `=B2*B10-B3*EXP(-B4*B5)*B11` |

### 4.3 New Worksheet: APV Tax Shield Analysis

See the implementation table in Section 2.4 above. This worksheet requires seven inputs and produces the PV of pre- and post-restructuring tax shields and the value destroyed.

### 4.4 New Worksheet: Merton Distance-to-Default

Create a worksheet for public company targets:

| Cell | Label | Formula |
| :--- | :--- | :--- |
| B2 | Market Cap (E) | Input |
| B3 | Face Value Debt (D) | Input |
| B4 | Equity Volatility | Input |
| B5 | Risk-Free Rate (r) | Input |
| B6 | Time Horizon (T) | Input (default 1) |
| B8 | Firm Value (V) | `=B2+B3` |
| B9 | Firm Volatility | `=B4*(B2/B8)` |
| B11 | Distance-to-Default | `=(LN(B8/B3)+(B5-B9^2/2)*B6)/(B9*SQRT(B6))` |
| B12 | **Default Probability** | `=NORM.S.DIST(-B11,TRUE)` |

### 4.5 Python Calculator

The accompanying `rvs_calculator_enhanced.py` file implements the complete Enhanced RVS model, including all five Damodaran enhancements. It supports three execution modes:

| Mode | Command | Description |
| :--- | :--- | :--- |
| Default | `python rvs_calculator_enhanced.py` | Runs full NPI example with all enhancements |
| JSON API | `python rvs_calculator_enhanced.py --json '{...}'` | Accepts JSON input, returns JSON output |
| Stress Test | `python rvs_calculator_enhanced.py --stress` | Runs NPI stress scenarios |
| Interactive | `python rvs_calculator_enhanced.py --interactive` | Guided input session |

---

## Part 5: Academic References

| # | Reference |
| :--- | :--- |
| [1] | SRFF-I CEO Review Methodology v5, "Rescue Finance Methodology and Scoring." Sohar International Bank. April 2026. |
| [2] | Damodaran, A. *Investment Valuation: Tools and Techniques for Determining the Value of Any Asset*. 3rd ed. John Wiley & Sons, 2012. |
| [3] | Shumway, T. "Forecasting Bankruptcy More Accurately: A Simple Hazard Model." *Journal of Business*, 74(1), 101–124. 2001. |
| [4] | Campbell, J.Y., Hilscher, J., and Szilagyi, J. "In Search of Distress Risk." *Journal of Finance*, 63(6), 2899–2939. 2008. |
| [5] | Merton, R.C. "On the Pricing of Corporate Debt: The Risk Structure of Interest Rates." *Journal of Finance*, 29(2), 449–470. 1974. |
| [6] | Black, F. and Scholes, M. "The Pricing of Options and Corporate Liabilities." *Journal of Political Economy*, 81(3), 637–654. 1973. |
| [7] | Altman, E.I. "Financial Ratios, Discriminant Analysis and the Prediction of Corporate Bankruptcy." *Journal of Finance*, 23(4), 589–609. 1968. |
| [8] | Miles, J.A. and Ezzell, J.R. "The Weighted Average Cost of Capital, Perfect Capital Markets, and Project Life: A Clarification." *Journal of Financial and Quantitative Analysis*, 15(3), 719–730. 1980. |
