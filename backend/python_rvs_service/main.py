"""FastAPI sidecar around calculate_enhanced_rvs.

This wrapper is called by the Go backend when PYTHON_RVS_URL is set. It
accepts the Go-side RVSv4Input shape, derives the six V-variables that
calculate_enhanced_rvs() expects, and maps the RVSResult back into the
Go-side RVSv4Output shape.

The V-variable derivations are proxies — they produce a runnable result
but must be reviewed before any production use. The inputs the scaffold
exposes (working capital, EBITDA, total debt, governance score, etc.)
don't map 1:1 to the DSCR / collateral coverage / EBITDA margin etc.
that the SRFF model was designed around.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Add repo root to sys.path so we can import rvs_calculator_enhanced.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from rvs_calculator_enhanced import (  # noqa: E402
    RVSInputs,
    calculate_enhanced_rvs,
)

log = logging.getLogger("rvs-sidecar")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="SRFF-I RVS Sidecar", version="0.1.0")


class RVSv4Input(BaseModel):
    """Mirror of models.RVSv4Input in the Go backend."""

    workingCapital: float
    totalAssets: float
    retainedEarnings: float
    ebitda: float
    totalDebt: float
    operatingCashFlow: float
    collateralValue: float
    totalLiabilities: float
    revenue: float
    ownerCompensationExcess: float = 0.0
    rptRevenuePercent: float = 0.0
    rptCostPercent: float = 0.0
    appraisalFactor: float = 1.0
    revenueUnderreportingFactor: float = 1.0
    governanceScore: float = 50.0
    concentrationScore: float = 50.0
    informationAsymmetryPercent: float = 10.0
    isShariahCompliant: bool = False
    sector: str = "manufacturing"
    annualDefaultProbability: float = 0.05


class StressTestScenario(BaseModel):
    name: str
    viabilityScore: float = Field(alias="viabilityScore")
    probability: float


class RVSv4Output(BaseModel):
    """Mirror of models.RVSv4Output in the Go backend."""

    finalScore: float
    componentScores: dict[str, float] = {}
    riskBand: Optional[str] = None
    recommendations: Optional[list[str]] = None
    riskRating: Optional[str] = None
    survivalProbability: Optional[list[float]] = None
    stressTestResults: Optional[dict[str, StressTestScenario]] = None
    recommendation: Optional[str] = None
    calculatedAt: Optional[datetime] = None


def _derive_v_variables(i: RVSv4Input) -> RVSInputs:
    """Derive the six V-variables from the richer Go input.

    These are proxies, not canonical definitions. Each one is annotated
    with the substitution being made.
    """
    # V1 projected DSCR Y3 — proxy: operating cash flow / annualized debt
    # service at 5-year amortization + 5% interest.
    v1 = 0.0
    if i.totalDebt > 0:
        annual_debt_service = (i.totalDebt / 5.0) + (i.totalDebt * 0.05)
        v1 = i.operatingCashFlow / annual_debt_service if annual_debt_service > 0 else 0.0
    else:
        v1 = 5.0  # cap at the warning threshold when no debt

    # V2 collateral coverage — direct: collateral / debt.
    v2 = i.collateralValue / i.totalDebt if i.totalDebt > 0 else 5.0

    # V3 projected EBITDA margin Y3 — proxy: current EBITDA margin.
    v3 = i.ebitda / i.revenue if i.revenue > 0 else 0.0
    v3 = max(0.0, min(1.0, v3))  # clamp to [0, 1] for validate()

    # V4 entry EBITDA / debt — direct.
    v4 = i.ebitda / i.totalDebt if i.totalDebt > 0 else 10.0

    # V5 asset identifiability — proxy: collateral / assets.
    v5 = i.collateralValue / i.totalAssets if i.totalAssets > 0 else 0.5
    v5 = max(0.0, min(1.0, v5))

    # V6 GP control factor — proxy: governance score (0-100 → 0-1).
    v6 = max(0.0, min(1.0, i.governanceScore / 100.0))

    return RVSInputs(
        projected_dscr_y3=v1,
        collateral_coverage=v2,
        projected_ebitda_margin_y3=v3,
        entry_ebitda_to_debt=v4,
        asset_identifiability=v5,
        gp_control_factor=v6,
        sector=i.sector,
        annual_default_probability=i.annualDefaultProbability,
    )


def _zone_to_rating(zone: str) -> str:
    """Map the SRFF zone string to an agency-style rating label."""
    if zone.startswith("Strong"):
        return "AA"
    if zone.startswith("Conditional"):
        return "BBB"
    return "B"


def _zone_to_recommendation(zone: str) -> str:
    if zone.startswith("Strong"):
        return "STRONG_BUY"
    if zone.startswith("Conditional"):
        return "CONDITIONAL_BUY"
    return "PASS"


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/calculate", response_model=RVSv4Output)
def calculate(payload: RVSv4Input) -> RVSv4Output:
    try:
        rvs_inputs = _derive_v_variables(payload)
        result = calculate_enhanced_rvs(rvs_inputs)
    except Exception as exc:  # surface as 422 to match Go handler shape
        log.exception("calculate_enhanced_rvs failed")
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Scale the SRFF enhanced score (roughly 0.0-1.0 in practice) to 0-100.
    final_score = max(0.0, min(100.0, result.enhanced_score * 100.0))

    return RVSv4Output(
        finalScore=final_score,
        componentScores=dict(result.contributions),
        riskBand=result.zone,
        riskRating=_zone_to_rating(result.zone),
        recommendation=_zone_to_recommendation(result.zone),
        recommendations=[result.decision] + list(result.warnings),
        calculatedAt=datetime.now(tz=timezone.utc),
        # survivalProbability and stressTestResults intentionally omitted —
        # the Go caller falls back to its own stub values when absent.
    )
