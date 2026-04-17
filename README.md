# SRFF-I Rescue Viability Score (RVS) — v3.0

**Strictly Private & Confidential**
Production-ready rescue viability scoring engine for distressed companies in the GCC Islamic finance market.

## Overview
The SRFF-I RVS v3.0 is a statistically validated, Damodaran-aligned, hazard-enhanced model designed to:
- Select high-probability rescue candidates from Sohar's NPL/distressed pool
- Predict 5-year survival probability and successful exit (IPO/M&A)
- Provide monthly early-warning monitoring post-deployment
- Support Shariah-compliant Diminishing Musharaka structuring

## Key Performance Metrics
- Forward accuracy: 93.0%
- Hazard AUC: 0.985
- 5-year survival separation: 91.8% (recovered) vs 14.7% (failed)
- Specificity: 100% (zero false positives)
- Composite V3 accuracy with hazard layer: 93.0%

## Repository Structure
- `srff_validation_v3.py` → Full academic validation suite (12 tests)
- `rvs_v3_with_hazard.xlsx` → Enhanced workbook with survival probabilities and Composite V3 scores
- `docs/` → IC memos, methodology addendums, and dashboard templates

## Quick Start
1. Run the validation suite: `python srff_validation_v3.py`
2. Open `rvs_v3_with_hazard.xlsx` for per-company scores and survival curves
3. Use the Excel frontend (coming in next PR) for live screening

## Collaboration Workflow
- All new work on feature branches
- Every change reviewed via Pull Request
- Squash & Merge to keep main clean

Last updated: April 17, 2026
