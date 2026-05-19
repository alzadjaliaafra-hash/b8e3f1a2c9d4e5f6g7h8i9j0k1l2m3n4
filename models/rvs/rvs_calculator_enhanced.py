#!/usr/bin/env python3
"""
SRFF Enhanced Rescue Viability Score (RVS) Calculator
=====================================================
Version 2.0 — Incorporating Damodaran's Distressed Firm Valuation Framework

This enhanced calculator implements five improvements identified through a
cross-check against Aswath Damodaran's *Investment Valuation*:

  1. Survival Probability Weighting (SAF)
  2. Sector-Specific Bankruptcy Cost Adjustments (V2_adj)
  3. Option-Adjusted Equity Valuation (Black-Scholes)
  4. Explicit Tax Shield Analysis (APV Framework)
  5. Merton Distance-to-Default (Market-Based Default Probability)

Enhanced Model:
  Enhanced RVS = [0.90(V1) + 1.05(V2_adj) + 5.85(V3) + 13.80(V4)
                  + 1.10(V5) + 1.15(V6)] x SAF

Zones (unchanged):
    > 7.0   Strong Rescue Candidate  (Proceed)
    4.5-7.0 Conditional Candidate    (Proceed with safeguards)
    < 4.5   Reject                   (Do not pursue)

Author:  Manus AI for Sohar International Bank
Date:    April 2026
Version: 2.0
"""

from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass, field
from typing import Optional


# ============================================================
# MODEL CONSTANTS
# ============================================================

COEFFICIENTS = {
    "V1": 0.90,   # Projected DSCR (Year 3)
    "V2": 1.05,   # Collateral Coverage Ratio (sector-adjusted)
    "V3": 5.85,   # Projected EBITDA Margin (Year 3)
    "V4": 13.80,  # Entry EBITDA-to-Debt Ratio
    "V5": 1.10,   # Asset Identifiability Ratio
    "V6": 1.15,   # GP Control Factor
}

ZONE_STRONG = 7.0
ZONE_CONDITIONAL = 4.5

# Enhancement 2 — Sector-specific bankruptcy cost adjustment factors
# Baseline: Manufacturing at 25% bankruptcy cost = 1.00
SECTOR_ADJUSTMENT_FACTORS: dict[str, float] = {
    "technology":          1.13,   # 15% bankruptcy cost
    "healthcare":          1.07,   # 20% bankruptcy cost
    "pharma":              1.07,   # 20% bankruptcy cost (alias)
    "logistics":           1.04,   # 22% bankruptcy cost
    "manufacturing":       1.00,   # 25% bankruptcy cost (baseline)
    "telecom":             0.93,   # 28% bankruptcy cost
    "oil_gas":             0.90,   # 30% bankruptcy cost
    "retail":              0.87,   # 35% bankruptcy cost
    "financial_services":  0.80,   # 40%+ bankruptcy cost
}

LIQUIDATION_DISCOUNTS = {
    "real_estate":            0.30,
    "plant_machinery":        0.60,
    "receivables_government": 0.20,
    "receivables_corporate":  0.40,
    "licences":               0.00,
    "goodwill_intangibles":   1.00,
}


# ============================================================
# HELPER: CUMULATIVE NORMAL DISTRIBUTION
# ============================================================

def _norm_cdf(x: float) -> float:
    """Standard normal cumulative distribution function (pure Python)."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class RVSInputs:
    """Core input variables for the RVS calculation."""
    projected_dscr_y3: float          # V1
    collateral_coverage: float         # V2 (raw, before sector adjustment)
    projected_ebitda_margin_y3: float  # V3 (decimal, e.g. 0.20)
    entry_ebitda_to_debt: float        # V4
    asset_identifiability: float       # V5
    gp_control_factor: float           # V6

    # Enhancement inputs
    sector: str = "manufacturing"      # Sector key for bankruptcy cost adj.
    annual_default_probability: float = 0.05  # For SAF calculation
    projection_years: int = 3          # Restructuring horizon

    def validate(self) -> list[str]:
        """Return a list of validation warnings."""
        warnings: list[str] = []
        if self.projected_dscr_y3 < 0:
            warnings.append("V1 (DSCR) is negative — check input.")
        if self.projected_dscr_y3 > 5.0:
            warnings.append("V1 (DSCR) exceeds 5.0x — unusually high.")
        if self.collateral_coverage < 0:
            warnings.append("V2 (Collateral Coverage) is negative.")
        if not (0.0 <= self.projected_ebitda_margin_y3 <= 1.0):
            warnings.append("V3 (EBITDA Margin) should be 0–1 decimal.")
        if self.entry_ebitda_to_debt < 0:
            warnings.append("V4 (EBITDA/Debt) is negative.")
        if not (0.0 <= self.asset_identifiability <= 1.0):
            warnings.append("V5 (Asset Identifiability) should be 0–1.")
        if not (0.0 <= self.gp_control_factor <= 1.0):
            warnings.append("V6 (GP Control) should be 0–1.")
        if self.sector.lower() not in SECTOR_ADJUSTMENT_FACTORS:
            warnings.append(
                f"Sector '{self.sector}' not recognised. "
                f"Valid: {', '.join(sorted(SECTOR_ADJUSTMENT_FACTORS))}. "
                f"Defaulting to 'manufacturing' (1.00)."
            )
        if not (0.0 <= self.annual_default_probability <= 1.0):
            warnings.append("Annual default probability must be 0–1.")
        return warnings


@dataclass
class BlackScholesInputs:
    """Inputs for the option-adjusted equity valuation (Enhancement 3)."""
    firm_value: float           # V — estimated via DCF (OMR)
    face_value_debt: float      # D — face value of outstanding debt (OMR)
    risk_free_rate: float       # r — annualised risk-free rate (decimal)
    time_to_maturity: float     # t — years to debt maturity / horizon
    firm_value_volatility: float  # sigma — annualised volatility of V


@dataclass
class TaxShieldInputs:
    """Inputs for the APV tax shield analysis (Enhancement 4)."""
    pre_debt: float             # Outstanding debt before restructuring
    pre_interest_rate: float    # Average interest rate before
    post_debt: float            # Restructured debt amount
    post_interest_rate: float   # Restructured interest rate
    tax_rate: float             # Corporate tax rate (decimal)
    cost_of_debt: float         # Discount rate for tax shields
    horizon_years: int = 5      # Analysis horizon


@dataclass
class MertonInputs:
    """Inputs for the Merton distance-to-default (Enhancement 5)."""
    market_cap: float           # E — market value of equity
    face_value_debt: float      # D — face value of debt
    equity_volatility: float    # sigma_E — annualised equity volatility
    risk_free_rate: float       # r — annualised risk-free rate
    time_horizon: float = 1.0   # T — typically 1 year


# ============================================================
# RESULT DATA CLASSES
# ============================================================

@dataclass
class RVSResult:
    """Output of the Enhanced RVS calculation."""
    # Core scores
    original_score: float
    enhanced_score: float
    zone: str
    decision: str

    # Breakdown
    contributions: dict[str, float]
    sector_adjustment_factor: float
    survival_adjustment_factor: float
    v2_adjusted: float

    # Metadata
    inputs: RVSInputs
    warnings: list[str]

    def summary(self) -> str:
        """Return a formatted summary string."""
        lines = [
            "=" * 70,
            "  SRFF ENHANCED RESCUE VIABILITY SCORE (RVS v2.0) — RESULT",
            "=" * 70,
            "",
            f"  Original RVS Score:   {self.original_score:.3f}",
            f"  Enhanced RVS Score:   {self.enhanced_score:.3f}",
            f"  Classification:       {self.zone}",
            f"  Decision:             {self.decision}",
            "",
            "  Enhancement Parameters:",
            f"    Sector:                    {self.inputs.sector}",
            f"    Sector Adj. Factor:        {self.sector_adjustment_factor:.4f}",
            f"    V2 (raw):                  {self.inputs.collateral_coverage:.4f}",
            f"    V2 (sector-adjusted):      {self.v2_adjusted:.4f}",
            f"    Annual Default Prob:       {self.inputs.annual_default_probability:.2%}",
            f"    Survival Adj. Factor:      {self.survival_adjustment_factor:.4f}",
            "",
            "  Variable Contributions (pre-SAF):",
        ]
        total_pre = sum(self.contributions.values())
        var_labels = {
            "V1": "DSCR Y3",
            "V2": "Collateral (adj)",
            "V3": "Margin Y3",
            "V4": "EBITDA/Debt",
            "V5": "Asset Ident.",
            "V6": "GP Control",
        }
        for key in ["V1", "V2", "V3", "V4", "V5", "V6"]:
            c = self.contributions[key]
            pct = (c / total_pre * 100) if total_pre > 0 else 0
            lines.append(f"    {key} ({var_labels[key]:16s}): {c:6.3f}  ({pct:5.1f}%)")
        lines.append(f"    {'Pre-SAF Total':22s}: {total_pre:6.3f}")
        lines.append(f"    x SAF ({self.survival_adjustment_factor:.4f})"
                      f"{'':12s}: {self.enhanced_score:6.3f}")
        lines.append("")
        if self.warnings:
            lines.append("  Warnings:")
            for w in self.warnings:
                lines.append(f"    [!] {w}")
            lines.append("")
        lines.append("=" * 70)
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Return a JSON-serialisable dictionary."""
        return {
            "original_rvs_score": round(self.original_score, 3),
            "enhanced_rvs_score": round(self.enhanced_score, 3),
            "zone": self.zone,
            "decision": self.decision,
            "sector": self.inputs.sector,
            "sector_adjustment_factor": round(self.sector_adjustment_factor, 4),
            "v2_adjusted": round(self.v2_adjusted, 4),
            "survival_adjustment_factor": round(self.survival_adjustment_factor, 4),
            "contributions": {k: round(v, 3) for k, v in self.contributions.items()},
            "inputs": {
                "V1_projected_dscr_y3": self.inputs.projected_dscr_y3,
                "V2_collateral_coverage": self.inputs.collateral_coverage,
                "V3_projected_ebitda_margin_y3": self.inputs.projected_ebitda_margin_y3,
                "V4_entry_ebitda_to_debt": self.inputs.entry_ebitda_to_debt,
                "V5_asset_identifiability": self.inputs.asset_identifiability,
                "V6_gp_control_factor": self.inputs.gp_control_factor,
            },
            "warnings": self.warnings,
        }


@dataclass
class BlackScholesResult:
    """Output of the option-adjusted equity valuation."""
    equity_value: float
    d1: float
    d2: float
    n_d1: float
    n_d2: float
    inputs: BlackScholesInputs

    def summary(self) -> str:
        lines = [
            "=" * 70,
            "  OPTION-ADJUSTED EQUITY VALUATION (Black-Scholes)",
            "=" * 70,
            "",
            f"  Firm Value (V):          {self.inputs.firm_value:,.0f}",
            f"  Face Value Debt (D):     {self.inputs.face_value_debt:,.0f}",
            f"  Risk-Free Rate (r):      {self.inputs.risk_free_rate:.2%}",
            f"  Time to Maturity (t):    {self.inputs.time_to_maturity:.1f} years",
            f"  Firm Volatility (sigma):  {self.inputs.firm_value_volatility:.2%}",
            "",
            f"  d1:                      {self.d1:+.4f}",
            f"  d2:                      {self.d2:+.4f}",
            f"  N(d1):                   {self.n_d1:.4f}",
            f"  N(d2):                   {self.n_d2:.4f}",
            "",
            f"  Option-Adjusted Equity:  {self.equity_value:,.0f}",
            "=" * 70,
        ]
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "equity_value": round(self.equity_value, 2),
            "d1": round(self.d1, 4),
            "d2": round(self.d2, 4),
            "n_d1": round(self.n_d1, 4),
            "n_d2": round(self.n_d2, 4),
        }


@dataclass
class TaxShieldResult:
    """Output of the APV tax shield analysis."""
    pv_pre_shields: float
    pv_post_shields: float
    value_destroyed: float
    annual_pre_shield: float
    annual_post_shield: float
    inputs: TaxShieldInputs

    def summary(self) -> str:
        lines = [
            "=" * 70,
            "  APV TAX SHIELD ANALYSIS",
            "=" * 70,
            "",
            f"  Pre-Restructuring:",
            f"    Debt:                  {self.inputs.pre_debt:,.0f}",
            f"    Interest Rate:         {self.inputs.pre_interest_rate:.2%}",
            f"    Annual Tax Shield:     {self.annual_pre_shield:,.0f}",
            f"    PV of Tax Shields:     {self.pv_pre_shields:,.0f}",
            "",
            f"  Post-Restructuring:",
            f"    Debt:                  {self.inputs.post_debt:,.0f}",
            f"    Interest Rate:         {self.inputs.post_interest_rate:.2%}",
            f"    Annual Tax Shield:     {self.annual_post_shield:,.0f}",
            f"    PV of Tax Shields:     {self.pv_post_shields:,.0f}",
            "",
            f"  Tax Shield Value Destroyed: {self.value_destroyed:,.0f}",
            f"  Tax Rate:                {self.inputs.tax_rate:.1%}",
            f"  Discount Rate (k_d):     {self.inputs.cost_of_debt:.2%}",
            f"  Horizon:                 {self.inputs.horizon_years} years",
            "=" * 70,
        ]
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "pv_pre_shields": round(self.pv_pre_shields, 2),
            "pv_post_shields": round(self.pv_post_shields, 2),
            "value_destroyed": round(self.value_destroyed, 2),
            "annual_pre_shield": round(self.annual_pre_shield, 2),
            "annual_post_shield": round(self.annual_post_shield, 2),
        }


@dataclass
class MertonResult:
    """Output of the Merton distance-to-default calculation."""
    distance_to_default: float
    default_probability: float
    firm_value_estimate: float
    firm_volatility: float
    inputs: MertonInputs

    def summary(self) -> str:
        lines = [
            "=" * 70,
            "  MERTON DISTANCE-TO-DEFAULT",
            "=" * 70,
            "",
            f"  Market Cap (E):          {self.inputs.market_cap:,.0f}",
            f"  Face Value Debt (D):     {self.inputs.face_value_debt:,.0f}",
            f"  Equity Volatility:       {self.inputs.equity_volatility:.2%}",
            f"  Risk-Free Rate:          {self.inputs.risk_free_rate:.2%}",
            f"  Time Horizon:            {self.inputs.time_horizon:.1f} years",
            "",
            f"  Estimated Firm Value:    {self.firm_value_estimate:,.0f}",
            f"  Estimated Firm Vol:      {self.firm_volatility:.2%}",
            f"  Distance-to-Default:     {self.distance_to_default:+.4f}",
            f"  Default Probability:     {self.default_probability:.2%}",
            "",
        ]
        if self.default_probability > 0.25:
            lines.append("  [!] WARNING: Market-implied default probability > 25%.")
            lines.append("      Investigate market-accounting divergence before proceeding.")
        elif self.default_probability > 0.10:
            lines.append("  [*] CAUTION: Elevated market-implied default probability.")
        else:
            lines.append("  [OK] Market-implied default probability within acceptable range.")
        lines.append("")
        lines.append("=" * 70)
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "distance_to_default": round(self.distance_to_default, 4),
            "default_probability": round(self.default_probability, 4),
            "firm_value_estimate": round(self.firm_value_estimate, 2),
            "firm_volatility": round(self.firm_volatility, 4),
        }


# ============================================================
# CORE CALCULATIONS
# ============================================================

def calculate_sector_adjustment(sector: str) -> float:
    """Return the sector-specific bankruptcy cost adjustment factor."""
    return SECTOR_ADJUSTMENT_FACTORS.get(sector.lower(), 1.00)


def calculate_survival_adjustment_factor(
    annual_default_prob: float,
    years: int = 3,
) -> float:
    """
    Calculate the Survival Adjustment Factor (SAF).

    SAF = (1/T) * sum_{t=1}^{T} (1 - p)^t

    Parameters
    ----------
    annual_default_prob : float
        Annual probability of default (0–1).
    years : int
        Number of projection years (default 3).

    Returns
    -------
    float
        The SAF multiplier (0–1).
    """
    if annual_default_prob <= 0:
        return 1.0
    if annual_default_prob >= 1:
        return 0.0
    survival_probs = [(1 - annual_default_prob) ** t for t in range(1, years + 1)]
    return sum(survival_probs) / years


def calculate_enhanced_rvs(inputs: RVSInputs) -> RVSResult:
    """
    Calculate the Enhanced SRFF Rescue Viability Score.

    Enhancements over v1.0:
      - V2 adjusted by sector-specific bankruptcy cost factor
      - Entire score multiplied by Survival Adjustment Factor (SAF)

    Parameters
    ----------
    inputs : RVSInputs
        The six core variables plus sector and default probability.

    Returns
    -------
    RVSResult
        Enhanced score, zone classification, and detailed breakdown.
    """
    warnings = inputs.validate()

    # Enhancement 2: Sector-specific adjustment
    s_adj = calculate_sector_adjustment(inputs.sector)
    v2_adj = inputs.collateral_coverage * s_adj

    # Enhancement 1: Survival Adjustment Factor
    saf = calculate_survival_adjustment_factor(
        inputs.annual_default_probability,
        inputs.projection_years,
    )

    # Calculate contributions (using adjusted V2)
    contributions = {
        "V1": COEFFICIENTS["V1"] * inputs.projected_dscr_y3,
        "V2": COEFFICIENTS["V2"] * v2_adj,
        "V3": COEFFICIENTS["V3"] * inputs.projected_ebitda_margin_y3,
        "V4": COEFFICIENTS["V4"] * inputs.entry_ebitda_to_debt,
        "V5": COEFFICIENTS["V5"] * inputs.asset_identifiability,
        "V6": COEFFICIENTS["V6"] * inputs.gp_control_factor,
    }

    pre_saf_total = sum(contributions.values())
    enhanced_score = pre_saf_total * saf

    # Original score (no enhancements) for comparison
    original_contributions = {
        "V1": COEFFICIENTS["V1"] * inputs.projected_dscr_y3,
        "V2": COEFFICIENTS["V2"] * inputs.collateral_coverage,
        "V3": COEFFICIENTS["V3"] * inputs.projected_ebitda_margin_y3,
        "V4": COEFFICIENTS["V4"] * inputs.entry_ebitda_to_debt,
        "V5": COEFFICIENTS["V5"] * inputs.asset_identifiability,
        "V6": COEFFICIENTS["V6"] * inputs.gp_control_factor,
    }
    original_score = sum(original_contributions.values())

    # Zone classification (based on enhanced score)
    if enhanced_score > ZONE_STRONG:
        zone = "Strong Rescue Candidate"
        decision = "PROCEED — Advance to full due diligence and Shariah structuring."
    elif enhanced_score > ZONE_CONDITIONAL:
        zone = "Conditional Candidate"
        decision = ("PROCEED WITH SAFEGUARDS — Require enhanced collateral, "
                     "pricing, or governance.")
    else:
        zone = "Reject"
        decision = "DO NOT PURSUE — Candidate is non-viable for rescue financing."

    return RVSResult(
        original_score=original_score,
        enhanced_score=enhanced_score,
        zone=zone,
        decision=decision,
        contributions=contributions,
        sector_adjustment_factor=s_adj,
        survival_adjustment_factor=saf,
        v2_adjusted=v2_adj,
        inputs=inputs,
        warnings=warnings,
    )


def calculate_option_adjusted_equity(inputs: BlackScholesInputs) -> BlackScholesResult:
    """
    Enhancement 3: Option-adjusted equity valuation using Black-Scholes.

    Treats equity as a call option on firm value with strike = face value of debt.

    Equity = V * N(d1) - D * exp(-r*t) * N(d2)
    """
    V = inputs.firm_value
    D = inputs.face_value_debt
    r = inputs.risk_free_rate
    t = inputs.time_to_maturity
    sigma = inputs.firm_value_volatility

    if V <= 0 or D <= 0 or t <= 0 or sigma <= 0:
        return BlackScholesResult(
            equity_value=max(V - D, 0),
            d1=0.0, d2=0.0, n_d1=0.5, n_d2=0.5,
            inputs=inputs,
        )

    d1 = (math.log(V / D) + (r + sigma**2 / 2) * t) / (sigma * math.sqrt(t))
    d2 = d1 - sigma * math.sqrt(t)
    n_d1 = _norm_cdf(d1)
    n_d2 = _norm_cdf(d2)

    equity_value = V * n_d1 - D * math.exp(-r * t) * n_d2

    return BlackScholesResult(
        equity_value=max(equity_value, 0),
        d1=d1,
        d2=d2,
        n_d1=n_d1,
        n_d2=n_d2,
        inputs=inputs,
    )


def calculate_tax_shields(inputs: TaxShieldInputs) -> TaxShieldResult:
    """
    Enhancement 4: APV tax shield analysis.

    Calculates the PV of tax shields before and after restructuring,
    and the value destroyed by deleveraging.
    """
    annual_pre = inputs.pre_debt * inputs.pre_interest_rate * inputs.tax_rate
    annual_post = inputs.post_debt * inputs.post_interest_rate * inputs.tax_rate

    # PV of annuity of tax shields
    kd = inputs.cost_of_debt
    n = inputs.horizon_years

    if kd > 0:
        annuity_factor = (1 - (1 + kd) ** (-n)) / kd
    else:
        annuity_factor = float(n)

    pv_pre = annual_pre * annuity_factor
    pv_post = annual_post * annuity_factor
    value_destroyed = pv_pre - pv_post

    return TaxShieldResult(
        pv_pre_shields=pv_pre,
        pv_post_shields=pv_post,
        value_destroyed=value_destroyed,
        annual_pre_shield=annual_pre,
        annual_post_shield=annual_post,
        inputs=inputs,
    )


def calculate_merton_dd(inputs: MertonInputs) -> MertonResult:
    """
    Enhancement 5: Merton distance-to-default.

    Uses the simplified Merton model to estimate market-implied default probability.

    DD = [ln(V/D) + (r - sigma_V^2/2) * T] / (sigma_V * sqrt(T))
    P(Default) = N(-DD)
    """
    E = inputs.market_cap
    D = inputs.face_value_debt
    sigma_E = inputs.equity_volatility
    r = inputs.risk_free_rate
    T = inputs.time_horizon

    # Simplified firm value and volatility estimation
    V = E + D
    sigma_V = sigma_E * (E / V) if V > 0 else sigma_E

    if V <= 0 or D <= 0 or sigma_V <= 0 or T <= 0:
        return MertonResult(
            distance_to_default=0.0,
            default_probability=0.5,
            firm_value_estimate=V,
            firm_volatility=sigma_V,
            inputs=inputs,
        )

    dd = (math.log(V / D) + (r - sigma_V**2 / 2) * T) / (sigma_V * math.sqrt(T))
    p_default = _norm_cdf(-dd)

    return MertonResult(
        distance_to_default=dd,
        default_probability=p_default,
        firm_value_estimate=V,
        firm_volatility=sigma_V,
        inputs=inputs,
    )


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def calculate_collateral_coverage(
    real_estate_book: float = 0.0,
    plant_machinery_book: float = 0.0,
    receivables_govt_face: float = 0.0,
    receivables_corp_face: float = 0.0,
    licences_valuation: float = 0.0,
    total_restructured_debt: float = 1.0,
) -> float:
    """
    Calculate V2 (Collateral Coverage Ratio) using SRFF-I liquidation discounts.
    All monetary inputs should be in the same currency unit (e.g., OMR '000).
    """
    liquidation_value = (
        real_estate_book * (1 - LIQUIDATION_DISCOUNTS["real_estate"])
        + plant_machinery_book * (1 - LIQUIDATION_DISCOUNTS["plant_machinery"])
        + receivables_govt_face * (1 - LIQUIDATION_DISCOUNTS["receivables_government"])
        + receivables_corp_face * (1 - LIQUIDATION_DISCOUNTS["receivables_corporate"])
        + licences_valuation * (1 - LIQUIDATION_DISCOUNTS["licences"])
    )
    return liquidation_value / total_restructured_debt if total_restructured_debt > 0 else 0.0


def calculate_entry_leverage(ebitda: float, total_debt: float) -> float:
    """Calculate V4 (Entry EBITDA-to-Debt Ratio) = EBITDA / Total Debt."""
    return ebitda / total_debt if total_debt > 0 else 0.0


# ============================================================
# COMPREHENSIVE EXAMPLE: NPI CASE STUDY
# ============================================================

def run_npi_example():
    """Run the full NPI case study with all five Damodaran enhancements."""
    print("\n" + "=" * 70)
    print("  NPI CASE STUDY — ENHANCED RVS v2.0 (DAMODARAN FRAMEWORK)")
    print("=" * 70)

    # ----------------------------------------------------------
    # 1. Enhanced RVS Calculation
    # ----------------------------------------------------------
    print("\n--- 1. ENHANCED RVS CALCULATION ---\n")

    npi_inputs = RVSInputs(
        projected_dscr_y3=2.15,
        collateral_coverage=1.50,
        projected_ebitda_margin_y3=0.200,
        entry_ebitda_to_debt=0.113,
        asset_identifiability=0.72,
        gp_control_factor=0.67,
        sector="healthcare",               # Pharma/Healthcare
        annual_default_probability=0.05,    # 5% annual default for distressed pharma
        projection_years=3,
    )

    rvs_result = calculate_enhanced_rvs(npi_inputs)
    print(rvs_result.summary())

    # ----------------------------------------------------------
    # 2. Option-Adjusted Equity Valuation (Enhancement 3)
    # ----------------------------------------------------------
    print("\n--- 2. OPTION-ADJUSTED EQUITY VALUATION ---\n")

    # NPI illustrative data (OMR '000)
    bs_inputs = BlackScholesInputs(
        firm_value=20_000,          # Estimated firm value via DCF
        face_value_debt=25_714,     # Total restructured debt
        risk_free_rate=0.045,       # Oman government bond yield
        time_to_maturity=5.0,       # Restructuring horizon
        firm_value_volatility=0.40, # Estimated from sector peers
    )

    bs_result = calculate_option_adjusted_equity(bs_inputs)
    print(bs_result.summary())

    # ----------------------------------------------------------
    # 3. Tax Shield Analysis (Enhancement 4)
    # ----------------------------------------------------------
    print("\n--- 3. APV TAX SHIELD ANALYSIS ---\n")

    ts_inputs = TaxShieldInputs(
        pre_debt=25_714,            # OMR '000 — current debt
        pre_interest_rate=0.08,     # 8% average interest rate
        post_debt=15_000,           # OMR '000 — restructured debt
        post_interest_rate=0.06,    # 6% restructured rate
        tax_rate=0.15,              # Oman corporate tax rate
        cost_of_debt=0.06,          # Discount rate for tax shields
        horizon_years=5,
    )

    ts_result = calculate_tax_shields(ts_inputs)
    print(ts_result.summary())

    # ----------------------------------------------------------
    # 4. Merton Distance-to-Default (Enhancement 5)
    # ----------------------------------------------------------
    print("\n--- 4. MERTON DISTANCE-TO-DEFAULT ---\n")

    # NPI is listed on Oman MSX — illustrative market data
    merton_inputs = MertonInputs(
        market_cap=2_000,           # OMR '000 — distressed market cap
        face_value_debt=25_714,     # OMR '000
        equity_volatility=0.65,     # High volatility for distressed stock
        risk_free_rate=0.045,
        time_horizon=1.0,
    )

    merton_result = calculate_merton_dd(merton_inputs)
    print(merton_result.summary())

    # ----------------------------------------------------------
    # 5. Sensitivity Analysis: SAF Impact
    # ----------------------------------------------------------
    print("\n--- 5. SENSITIVITY: IMPACT OF DEFAULT PROBABILITY ON RVS ---\n")
    print(f"  {'Default Prob':>12s}  {'SAF':>8s}  {'Enhanced RVS':>13s}  {'Zone':>25s}")
    print(f"  {'-'*12}  {'-'*8}  {'-'*13}  {'-'*25}")

    for p in [0.00, 0.03, 0.05, 0.08, 0.10, 0.15, 0.20]:
        test_inputs = RVSInputs(
            projected_dscr_y3=2.15,
            collateral_coverage=1.50,
            projected_ebitda_margin_y3=0.200,
            entry_ebitda_to_debt=0.113,
            asset_identifiability=0.72,
            gp_control_factor=0.67,
            sector="healthcare",
            annual_default_probability=p,
            projection_years=3,
        )
        r = calculate_enhanced_rvs(test_inputs)
        print(f"  {p:>11.0%}  {r.survival_adjustment_factor:>8.4f}  "
              f"{r.enhanced_score:>13.3f}  {r.zone:>25s}")

    print()

    # ----------------------------------------------------------
    # 6. Sensitivity Analysis: Sector Impact
    # ----------------------------------------------------------
    print("\n--- 6. SENSITIVITY: IMPACT OF SECTOR ON RVS ---\n")
    print(f"  {'Sector':>20s}  {'S_adj':>6s}  {'V2_adj':>7s}  "
          f"{'Enhanced RVS':>13s}  {'Zone':>25s}")
    print(f"  {'-'*20}  {'-'*6}  {'-'*7}  {'-'*13}  {'-'*25}")

    for sector in sorted(SECTOR_ADJUSTMENT_FACTORS.keys()):
        if sector == "pharma":
            continue  # Skip alias
        test_inputs = RVSInputs(
            projected_dscr_y3=2.15,
            collateral_coverage=1.50,
            projected_ebitda_margin_y3=0.200,
            entry_ebitda_to_debt=0.113,
            asset_identifiability=0.72,
            gp_control_factor=0.67,
            sector=sector,
            annual_default_probability=0.05,
            projection_years=3,
        )
        r = calculate_enhanced_rvs(test_inputs)
        s = calculate_sector_adjustment(sector)
        print(f"  {sector:>20s}  {s:>6.2f}  {r.v2_adjusted:>7.3f}  "
              f"{r.enhanced_score:>13.3f}  {r.zone:>25s}")

    print()
    return rvs_result


# ============================================================
# STRESS TEST SUITE
# ============================================================

def run_stress_tests():
    """Run the NPI stress scenarios with the enhanced model."""
    print("\n" + "=" * 70)
    print("  NPI STRESS SCENARIOS — ENHANCED RVS v2.0")
    print("=" * 70)

    scenarios = [
        ("Base Case",              2.15, 1.50, 0.200, 0.113, 0.72, 0.67, 0.05),
        ("EBITDA Stress (-30%)",   1.50, 1.50, 0.140, 0.079, 0.72, 0.67, 0.08),
        ("KSA Plant Delay (24m)",  1.80, 1.20, 0.180, 0.100, 0.60, 0.67, 0.07),
        ("KSA Total Write-Off",   1.60, 1.00, 0.170, 0.090, 0.50, 0.67, 0.10),
        ("Liquidity Crisis",      1.90, 1.40, 0.190, 0.105, 0.72, 0.67, 0.08),
        ("Combined Worst Case",   1.10, 0.80, 0.100, 0.060, 0.40, 0.33, 0.15),
    ]

    print(f"\n  {'Scenario':28s}  {'Orig RVS':>9s}  {'Enh RVS':>8s}  "
          f"{'SAF':>6s}  {'Zone':>25s}")
    print(f"  {'-'*28}  {'-'*9}  {'-'*8}  {'-'*6}  {'-'*25}")

    for name, v1, v2, v3, v4, v5, v6, p in scenarios:
        inp = RVSInputs(v1, v2, v3, v4, v5, v6,
                        sector="healthcare",
                        annual_default_probability=p,
                        projection_years=3)
        r = calculate_enhanced_rvs(inp)
        print(f"  {name:28s}  {r.original_score:>9.3f}  {r.enhanced_score:>8.3f}  "
              f"{r.survival_adjustment_factor:>6.3f}  {r.zone:>25s}")

    print()


# ============================================================
# INTERACTIVE MODE
# ============================================================

def run_interactive():
    """Run an interactive session to score a new deal."""
    print("\n" + "=" * 70)
    print("  SRFF ENHANCED RVS v2.0 — INTERACTIVE CALCULATOR")
    print("=" * 70)
    print()

    try:
        v1 = float(input("  V1 — Projected DSCR (Year 3) [e.g., 2.15]:  "))
        v2 = float(input("  V2 — Collateral Coverage Ratio [e.g., 1.50]: "))
        v3 = float(input("  V3 — Projected EBITDA Margin Y3 (decimal) [e.g., 0.20]: "))
        v4 = float(input("  V4 — Entry EBITDA / Total Debt [e.g., 0.113]: "))
        v5 = float(input("  V5 — Asset Identifiability Ratio [e.g., 0.72]: "))
        v6 = float(input("  V6 — GP Control Factor (0.0-1.0) [e.g., 0.67]: "))
        print()
        print(f"  Available sectors: {', '.join(sorted(SECTOR_ADJUSTMENT_FACTORS))}")
        sector = input("  Sector [e.g., manufacturing]: ").strip() or "manufacturing"
        p = float(input("  Annual Default Probability (decimal) [e.g., 0.05]: ") or "0.05")
    except (ValueError, EOFError):
        print("\n  Error: Invalid input. Please enter numeric values.")
        return None

    inputs = RVSInputs(v1, v2, v3, v4, v5, v6,
                        sector=sector,
                        annual_default_probability=p)
    result = calculate_enhanced_rvs(inputs)
    print(result.summary())

    # Ask about optional modules
    print("\n  Optional Damodaran cross-checks:")
    run_bs = input("  Run Black-Scholes equity valuation? (y/n) [n]: ").strip().lower()
    if run_bs == "y":
        try:
            fv = float(input("    Firm Value (DCF estimate): "))
            fd = float(input("    Face Value of Debt: "))
            rf = float(input("    Risk-Free Rate (decimal): "))
            tm = float(input("    Time to Maturity (years): "))
            vol = float(input("    Firm Value Volatility (decimal): "))
            bs = calculate_option_adjusted_equity(
                BlackScholesInputs(fv, fd, rf, tm, vol))
            print(bs.summary())
        except (ValueError, EOFError):
            print("    Skipped — invalid input.")

    run_merton = input("  Run Merton Distance-to-Default? (y/n) [n]: ").strip().lower()
    if run_merton == "y":
        try:
            mc = float(input("    Market Cap: "))
            fd = float(input("    Face Value of Debt: "))
            ev = float(input("    Equity Volatility (decimal): "))
            rf = float(input("    Risk-Free Rate (decimal): "))
            m = calculate_merton_dd(MertonInputs(mc, fd, ev, rf))
            print(m.summary())
        except (ValueError, EOFError):
            print("    Skipped — invalid input.")

    return result


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        run_interactive()

    elif len(sys.argv) > 1 and sys.argv[1] == "--json":
        # JSON input: {"V1":2.15, "V2":1.50, ..., "sector":"healthcare", "default_prob":0.05}
        try:
            data = json.loads(sys.argv[2])
            inputs = RVSInputs(
                projected_dscr_y3=data["V1"],
                collateral_coverage=data["V2"],
                projected_ebitda_margin_y3=data["V3"],
                entry_ebitda_to_debt=data["V4"],
                asset_identifiability=data["V5"],
                gp_control_factor=data["V6"],
                sector=data.get("sector", "manufacturing"),
                annual_default_probability=data.get("default_prob", 0.05),
                projection_years=data.get("projection_years", 3),
            )
            result = calculate_enhanced_rvs(inputs)
            output = result.to_dict()

            # Optional: Black-Scholes
            if "bs" in data:
                bs = data["bs"]
                bs_result = calculate_option_adjusted_equity(BlackScholesInputs(
                    bs["firm_value"], bs["debt"], bs["rf"], bs["time"], bs["vol"]))
                output["black_scholes"] = bs_result.to_dict()

            # Optional: Tax Shields
            if "tax" in data:
                tx = data["tax"]
                ts_result = calculate_tax_shields(TaxShieldInputs(
                    tx["pre_debt"], tx["pre_rate"], tx["post_debt"],
                    tx["post_rate"], tx["tax_rate"], tx["kd"],
                    tx.get("years", 5)))
                output["tax_shields"] = ts_result.to_dict()

            # Optional: Merton
            if "merton" in data:
                mt = data["merton"]
                m_result = calculate_merton_dd(MertonInputs(
                    mt["market_cap"], mt["debt"], mt["equity_vol"],
                    mt["rf"], mt.get("time", 1.0)))
                output["merton"] = m_result.to_dict()

            print(json.dumps(output, indent=2))

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error: {e}")
            print('Usage: python rvs_calculator_enhanced.py --json '
                  '\'{"V1":2.15,"V2":1.50,"V3":0.20,"V4":0.113,'
                  '"V5":0.72,"V6":0.67,"sector":"healthcare","default_prob":0.05}\'')

    elif len(sys.argv) > 1 and sys.argv[1] == "--stress":
        run_stress_tests()

    else:
        # Default: run full NPI example with all enhancements
        run_npi_example()
        run_stress_tests()
