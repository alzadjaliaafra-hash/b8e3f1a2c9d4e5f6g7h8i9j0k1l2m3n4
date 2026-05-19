# SRFF-I RVS Model (ALiF Platform)

## Overview
This repository serves as the single source of truth for the **SRFF-I (Rescue Valuation Score) Model**, a core component of the ALiF Private Equity Platform developed by Afra Al Zadjali. 

The SRFF-I model is designed to evaluate GCC bank acquisitions, structure Islamic finance transactions, and provide robust valuation frameworks for special situations and rescue financing.

## Repository Structure

```text
SRFF-I-RVS-Model/
├── backend/            # Go backend for the RVS web application
├── frontend/           # Angular frontend for the RVS web application
├── models/             # Core quantitative models
│   ├── rvs/            # Main Rescue Valuation Score models (Excel & Python)
│   ├── screening/      # Forward screening algorithms
│   └── monitoring/     # IC dashboard and monthly monitoring tools
├── case-studies/       # Applied models on real-world scenarios (e.g., PharmaCo X)
├── docs/               # Technical notes, methodology, and validation reports
├── scripts/            # Automation, backtesting, and validation scripts
└── templates/          # ALiF/Murshidi AI branded templates
    ├── branded/        # Slide decks and pitchbooks
    ├── emails/         # Institutional outreach formats
    └── reports/        # IC memos and research dispatches
```

## Latest Version: RVS 3.7 (May 2026)
The repository currently implements the RVS 3.7 methodology, which includes:
- Short-Term Price Prediction Layer
- Strict Complete-Data Backtesting
- 3 Top Buy / 3 Top Sell / 3 Rescue Financing recommendations
- Full coefficient sensitivity analysis
- Murshidi AI interpretation integration

## How to Use This Repository (Cost Optimization)
This repository is structured to minimize AI agent credit consumption by storing reusable assets:
1. **Templates**: Always pull from `templates/` before generating new emails or reports.
2. **Models**: Use `models/` for baseline calculations rather than recreating formulas.
3. **Automation**: Use GitHub Actions (in `.github/workflows/`) for recurring data tasks.

---
*Maintained by Afra Al Zadjali | ALiF Special Situations Desk | Powered by Murshidi AI*
