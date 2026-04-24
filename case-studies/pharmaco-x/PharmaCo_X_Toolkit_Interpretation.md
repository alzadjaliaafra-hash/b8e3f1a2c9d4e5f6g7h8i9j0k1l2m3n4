# PharmaCo X SRFF-I v4.0 Toolkit: Comprehensive Sheet-by-Sheet Interpretation

This document provides a detailed interpretation of the SRFF-I v4.0 Private Company Toolkit populated with the financial data of PharmaCo X (PharmaCo X). The analysis evaluates the company's viability for rescue financing under the the Lead Arranger framework.

## Sheet 1: User Guide
The User Guide serves as the static operational manual for the v4.0 Private Company Edition. It outlines the methodology for the new 10-component architecture, including the 1.20× private firm hazard multiplier, Damodaran valuation inputs, and the Shariah compliance screening logic. No computational outputs are generated on this sheet.

## Sheet 2: Deal Input
This sheet aggregates all foundational data for PharmaCo X. The company is classified within the defensive pharmaceutical manufacturing sector in Oman. 

The financial inputs reveal severe distress. PharmaCo X carries a massive debt burden of OMR 20.3 million against total assets of OMR 22.8 million. The company is technically insolvent, with accumulated retained earnings showing a deficit of OMR 33.3 million, resulting in negative equity of OMR -6.29 million. Operating cash flow is deeply negative at OMR -3.03 million (based on 2025 projections, following an even worse 2024). 

However, there is a clear restructuring plan. The projected EBITDA for the base restructuring year (2025) is OMR 1.19 million, growing to OMR 3.83 million by Year 5. Shareholders have committed OMR 7.61 million via subordinated loans to support the turnaround. Governance is rated as "Adequate" (60/100), and concentration risk is "Moderate" (60/100), reflecting the typical profile of a regional family-controlled pharmaceutical manufacturer.

## Sheet 3: Logistic Model — P(Recovery)
The core logistic regression model computes the Probability of Recovery based on six normalized financial variables. 

The model applies private company adjustments: an estimated OMR 500,000 owner compensation add-back to EBITDA, a 5% Related Party Transaction (RPT) haircut to revenue and assets, and a 0.75 appraisal factor to collateral. 

The most critical variables dragging down the score are **V2 (Retained Earnings / Total Assets)** at -1.5391 and **V4 (Operating Cash Flow / Total Debt)** at -0.1493. The massive accumulated losses and negative cash generation overwhelm the positive contributions from the working capital position and the adjusted collateral base. 

The resulting z-score is **-0.4704**, translating to a **Probability of Recovery of 38.45%**. This falls firmly into the "LOW Recovery Probability" tier, indicating that without fundamental structural changes, the company is highly unlikely to service a rescue facility successfully.

## Sheet 4: Hazard Model — 5-Year Survival
The Hazard Model evaluates the risk of default over a five-year horizon. Because PharmaCo X is unlisted, the model applies the v4.0 private firm multiplier of 1.20× to the base hazard rate.

The base hazard rate (derived from the logistic z-score) is 38.45%. Applying the 1.20× multiplier increases the annual hazard rate to a severe **46.14%**. 

When compounded over the five-year restructuring period, the cumulative survival probability plummets drastically year over year. By Year 5, the **Cumulative Survival Probability is merely 4.53%**. This indicates an extreme risk of failure during the turnaround period, driven by the compounding effect of the company's deeply negative equity and cash flow deficits.

## Sheet 5: Damodaran Adjustments
This sheet calculates the private company valuation metrics and synthetic credit rating using Aswath Damodaran's methodology.

Given the undiversified nature of private ownership, the market beta (0.80) is divided by the R-squared correlation (0.25), resulting in a high **Total Beta of 3.20**. This drives the **Cost of Equity up to an expensive 27.43%**. The Weighted Average Cost of Capital (WACC) sits at 14.83%.

The Interest Coverage Ratio (ICR), using the adjusted EBITDA of OMR 1.69 million against interest expenses of OMR 1.49 million, is a razor-thin **1.13**. This maps to a **Synthetic Credit Rating of CCC**, indicating near-default vulnerability. Furthermore, the model applies a combined 40% private company discount (25% for illiquidity and 15% for key-person dependency).

## Sheet 6: Shariah Compliance Screening
The Shariah screening module evaluates PharmaCo X against three Islamic finance criteria. 

While the company passes the operational screens (Interest Income is only 1.03% of Revenue, and Non-Permissible Income is 0.00%), it spectacularly fails the leverage screen. The **Debt to Total Assets ratio is 89.09%**, far exceeding the strict <33% threshold required for Shariah compliance. 

Because it fails this critical screen, the toolkit flags the deal as **NON-COMPLIANT** and triggers an automatic one-level downgrade for the final verdict.

## Sheet 7: Scorecard
The Scorecard provides a qualitative overlay based on the Deal Input parameters. PharmaCo X benefits from operating in a "Defensive" sector (pharmaceuticals) and possessing identifiable, tangible assets (manufacturing facilities). Management quality is rated as Moderate (3/5). While the business model is fundamentally viable, the heavy burden of legacy debt and operational inefficiencies severely constrains its near-term performance.

## Sheet 8: Credit Risk
The Credit Risk sheet translates the logistic probabilities into actionable banking metrics. 

The Probability of Default (PD) is the inverse of the recovery probability, sitting at **61.55%**. The Loss Given Default (LGD) is calculated at **44.62%**, representing the shortfall between the adjusted collateral (OMR 11.25 million) and the total debt (OMR 20.31 million). 

The resulting Expected Loss (EL) is capped at the model's ceiling of **27.46%**. Consequently, the toolkit recommends a mandatory haircut of 27.46% on the existing debt, implying that any rescue financing or acquisition of the debt should be priced at no more than OMR 14.73 million to absorb the inherent risk.

## Sheet 9: Fund Model
The Fund Model projects the five-year turnaround trajectory. It outlines the path from the current OMR 8.99 million in revenue to the projected Year 5 revenue of OMR 21.63 million. EBITDA is forecasted to scale from OMR 1.19 million to OMR 3.83 million, expanding margins from 7.97% to 17.74%. 

While these projections depict a successful operational turnaround supported by the OMR 7.61 million shareholder commitment, the baseline starting point is so degraded that the statistical models (Logistic and Hazard) heavily discount the probability of actually achieving these Year 5 targets.

## Sheet 10: Composite V4 Score
This sheet synthesizes the quantitative and qualitative outputs into the final decision matrix. 

The formula weights the P(Recovery) at 60% and the Governance-adjusted 5-Year Survival at 40%. 
- Weighted P(Recovery): 0.3845 × 0.60 = 0.2307
- Weighted Survival × Gov: 0.0453 × 0.60 × 0.40 = 0.0109

The resulting **Composite V4 Score is an abysmal 24.16%**, falling drastically short of the 50% minimum threshold for a "CONDITIONAL" approval. The pre-Shariah verdict is a definitive **NO-GO**. Because the deal also failed the Shariah leverage screen, the final verdict remains a hard **NO-GO**.

## Sheet 11: Stress Test
The Stress Test matrix subjects the model to six severe macroeconomic and operational shocks. 

Across all six scenarios—ranging from a Working Capital Crisis to a Perfect Storm—the stressed composite scores remain trapped between 22.39% and 41.95%. The company's baseline metrics are already so distressed that further shocks simply cement the outcome. **Every single stress scenario results in a NO-GO verdict.** 

Notably, the "Governance Collapse" scenario artificially inflates the recovery probability (due to the inverse relationship of V2 in extreme mathematical boundary conditions), but the 5-Year survival rate drops to near-zero (0.01%), ensuring the composite score still fails.

## Sheet 12: Summary
The Executive Summary aggregates the findings for the Investment Committee. It clearly presents the terminal metrics: a 38.45% recovery probability, a 4.53% survival probability, a CCC synthetic rating, and a recommended 27.46% debt haircut. The summary provides a concise, unified view that PharmaCo X, in its current highly leveraged and loss-making state, does not qualify for the SRFF-I facility without a massive, pre-emptive debt write-off or equity injection.

## Sheet 13: Formulas Reference
This static sheet documents the mathematical architecture of the v4.0 toolkit, providing transparency for risk officers and auditors regarding how the logistic coefficients, hazard multipliers, and composite weightings are applied.

---

### Conclusion
The PharmaCo X analysis demonstrates a company with a viable underlying business model (pharmaceuticals) that is entirely suffocated by an unsustainable capital structure. The technical insolvency, negative historical cash flows, and 89% debt-to-assets ratio trigger catastrophic failures across the Logistic, Hazard, and Shariah models. The toolkit definitively recommends a **NO-GO** for rescue financing under the current capital structure.
