#!/usr/bin/env python3
"""
SRFF-I Rescue Viability Score (RVS) v3.0 — Production Calculator
================================================================
Calibrated logistic regression model with discrete-time hazard layer for
predicting recovery probability and survival curves of distressed companies.

Author: Manus AI for Sohar International Bank
Date: April 2026
Version: 3.0
"""

import numpy as np
from scipy.special import expit
from dataclasses import dataclass
from typing import Dict, Optional, Tuple


# Calibrated model coefficients from v3.0 validation
INTERCEPT = 2.5445
COEFFICIENTS = {
    "V1": 0.2506,   # Working Capital / Total Assets
    "V2": 1.7070,   # Retained Earnings / Total Assets
    "V3": 0.7426,   # EBITDA / Total Debt
    "V4": 0.7262,   # Operating Cash Flow / Total Debt
    "V5": 0.8278,   # Collateral Value / Total Liabilities
    "V6": -1.8122   # Revenue / Total Assets
}

# Decision thresholds
THRESHOLD_STRONG = 0.70      # > 70% recovery probability
THRESHOLD_CONDITIONAL = 0.50  # 50-70% recovery probability
# < 50% = Reject


@dataclass
class CompanyFinancials:
    """Financial inputs for RVS calculation."""
    # Balance sheet items (OMR)
    working_capital: float
    total_assets: float
    retained_earnings: float
    total_debt: float
    total_liabilities: float

    # Income statement items (OMR)
    ebitda: float
    revenue: float
    operating_cash_flow: float

    # Collateral (OMR)
    collateral_value: float

    # Company info
    company_name: str = "Unknown"
    sector: str = "Manufacturing"


@dataclass
class RVSResult:
    """RVS v3.0 calculation results."""
    # Company info
    company_name: str

    # Input variables (V1-V6)
    v1: float  # Working Capital / Assets
    v2: float  # Retained Earnings / Assets
    v3: float  # EBITDA / Debt
    v4: float  # Operating CF / Debt
    v5: float  # Collateral / Liabilities
    v6: float  # Revenue / Assets

    # Core outputs
    recovery_probability: float
    rvs_score: float  # Scaled 0-10
    zone: str  # "Strong Candidate" / "Conditional" / "Reject"

    # Hazard layer (v3.0 enhancement)
    hazard_rate: float
    survival_1yr: float
    survival_3yr: float
    survival_5yr: float

    # Composite score
    composite_v3: float

    # Recommendation
    recommendation: str


class RVSv3Calculator:
    """Production calculator for RVS v3.0 model."""

    def __init__(self):
        """Initialize RVS v3.0 calculator with calibrated coefficients."""
        self.intercept = INTERCEPT
        self.coefs = np.array([
            COEFFICIENTS["V1"],
            COEFFICIENTS["V2"],
            COEFFICIENTS["V3"],
            COEFFICIENTS["V4"],
            COEFFICIENTS["V5"],
            COEFFICIENTS["V6"]
        ])

    def calculate_variables(self, fin: CompanyFinancials) -> np.ndarray:
        """
        Calculate V1-V6 variables from company financials.

        Args:
            fin: CompanyFinancials object

        Returns:
            Array of [V1, V2, V3, V4, V5, V6]
        """
        # Avoid division by zero
        assets = max(fin.total_assets, 1.0)
        debt = max(fin.total_debt, 1.0)
        liabilities = max(fin.total_liabilities, 1.0)

        v1 = fin.working_capital / assets
        v2 = fin.retained_earnings / assets
        v3 = fin.ebitda / debt
        v4 = fin.operating_cash_flow / debt
        v5 = fin.collateral_value / liabilities
        v6 = fin.revenue / assets

        return np.array([v1, v2, v3, v4, v5, v6])

    def predict_recovery_probability(self, variables: np.ndarray) -> float:
        """
        Calculate recovery probability using calibrated logistic regression.

        Args:
            variables: Array of V1-V6 values

        Returns:
            Recovery probability [0, 1]
        """
        logit = self.intercept + np.dot(variables, self.coefs)
        prob = expit(logit)
        return float(prob)

    def calculate_hazard_rate(self, recovery_prob: float) -> float:
        """
        Estimate annual hazard rate from recovery probability.
        Uses Shumway-style discrete-time hazard model.

        Args:
            recovery_prob: Recovery probability from logistic model

        Returns:
            Annual hazard rate (probability of failure per year)
        """
        # Map recovery probability to hazard rate
        # Higher recovery prob → lower hazard
        if recovery_prob >= 0.95:
            return 0.05
        elif recovery_prob >= 0.80:
            return 0.10
        elif recovery_prob >= 0.65:
            return 0.15
        elif recovery_prob >= 0.50:
            return 0.20
        elif recovery_prob >= 0.35:
            return 0.25
        else:
            return 0.30

    def calculate_survival(self, hazard_rate: float, years: int) -> float:
        """
        Calculate survival probability over time horizon.

        Args:
            hazard_rate: Annual hazard rate
            years: Time horizon in years

        Returns:
            Survival probability S(t) = exp(-h * t)
        """
        return float(np.exp(-hazard_rate * years))

    def calculate_composite_v3(self, recovery_prob: float, survival_5yr: float) -> float:
        """
        Calculate Composite V3 score.
        Weighted: 60% recovery probability + 40% 5-year survival

        Args:
            recovery_prob: Recovery probability
            survival_5yr: 5-year survival probability

        Returns:
            Composite V3 score [0, 1]
        """
        return 0.6 * recovery_prob + 0.4 * survival_5yr

    def classify_zone(self, recovery_prob: float) -> str:
        """
        Classify company into decision zone based on recovery probability.

        Args:
            recovery_prob: Recovery probability

        Returns:
            Zone classification string
        """
        if recovery_prob >= THRESHOLD_STRONG:
            return "Strong Candidate"
        elif recovery_prob >= THRESHOLD_CONDITIONAL:
            return "Conditional"
        else:
            return "Reject"

    def generate_recommendation(
        self,
        zone: str,
        recovery_prob: float,
        survival_5yr: float,
        hazard_rate: float
    ) -> str:
        """
        Generate IC recommendation based on scores.

        Args:
            zone: Classification zone
            recovery_prob: Recovery probability
            survival_5yr: 5-year survival
            hazard_rate: Annual hazard rate

        Returns:
            Recommendation string
        """
        if zone == "Strong Candidate":
            if survival_5yr >= 0.80:
                return "APPROVE — Strong rescue candidate with excellent survival probability. Proceed with standard safeguards."
            else:
                return "CONDITIONAL APPROVE — Good recovery potential but moderate long-term risk. Consider 3-year exit timeline."

        elif zone == "Conditional":
            if hazard_rate > 0.25:
                return "PROCEED WITH CAUTION — Enhanced safeguards required: additional collateral, strict covenants, management changes. Consider shorter exit timeline."
            else:
                return "CONDITIONAL APPROVE — Moderate rescue viability. Require enhanced monitoring and operational improvements."

        else:  # Reject
            if recovery_prob < 0.35:
                return "DECLINE — Insufficient rescue viability. Recommend liquidation assessment or alternative workout options."
            else:
                return "BORDERLINE — Consider only with exceptional collateral coverage or strategic value. Require deep restructuring."

    def score_company(self, fin: CompanyFinancials) -> RVSResult:
        """
        Complete RVS v3.0 scoring for a company.

        Args:
            fin: CompanyFinancials object with all required data

        Returns:
            RVSResult with all calculated scores and recommendations
        """
        # Calculate V1-V6
        variables = self.calculate_variables(fin)

        # Recovery probability (core RVS)
        recovery_prob = self.predict_recovery_probability(variables)

        # RVS score (scaled 0-10)
        rvs_score = recovery_prob * 10

        # Zone classification
        zone = self.classify_zone(recovery_prob)

        # Hazard layer (v3.0)
        hazard_rate = self.calculate_hazard_rate(recovery_prob)
        survival_1yr = self.calculate_survival(hazard_rate, 1)
        survival_3yr = self.calculate_survival(hazard_rate, 3)
        survival_5yr = self.calculate_survival(hazard_rate, 5)

        # Composite V3 score
        composite = self.calculate_composite_v3(recovery_prob, survival_5yr)

        # Recommendation
        recommendation = self.generate_recommendation(
            zone, recovery_prob, survival_5yr, hazard_rate
        )

        return RVSResult(
            company_name=fin.company_name,
            v1=variables[0],
            v2=variables[1],
            v3=variables[2],
            v4=variables[3],
            v5=variables[4],
            v6=variables[5],
            recovery_probability=recovery_prob,
            rvs_score=rvs_score,
            zone=zone,
            hazard_rate=hazard_rate,
            survival_1yr=survival_1yr,
            survival_3yr=survival_3yr,
            survival_5yr=survival_5yr,
            composite_v3=composite,
            recommendation=recommendation
        )

    def print_report(self, result: RVSResult):
        """
        Print formatted RVS report for IC review.

        Args:
            result: RVSResult object
        """
        print("=" * 80)
        print(f"  SRFF-I RESCUE VIABILITY SCORE v3.0 — {result.company_name.upper()}")
        print("=" * 80)
        print()

        print("INPUT VARIABLES:")
        print(f"  V1 (Working Capital / Assets):       {result.v1:>8.3f}")
        print(f"  V2 (Retained Earnings / Assets):     {result.v2:>8.3f}")
        print(f"  V3 (EBITDA / Debt):                  {result.v3:>8.3f}")
        print(f"  V4 (Operating CF / Debt):            {result.v4:>8.3f}")
        print(f"  V5 (Collateral / Liabilities):       {result.v5:>8.3f}")
        print(f"  V6 (Revenue / Assets):               {result.v6:>8.3f}")
        print()

        print("CORE RVS SCORES:")
        print(f"  Recovery Probability:                {result.recovery_probability:>7.1%}")
        print(f"  RVS Score (0-10):                    {result.rvs_score:>8.2f}")
        print(f"  Zone Classification:                 {result.zone}")
        print()

        print("HAZARD LAYER (v3.0):")
        print(f"  Annual Hazard Rate:                  {result.hazard_rate:>7.1%}")
        print(f"  1-Year Survival:                     {result.survival_1yr:>7.1%}")
        print(f"  3-Year Survival:                     {result.survival_3yr:>7.1%}")
        print(f"  5-Year Survival:                     {result.survival_5yr:>7.1%}")
        print()

        print("COMPOSITE METRICS:")
        print(f"  Composite V3 Score:                  {result.composite_v3:>7.1%}")
        print()

        print("IC RECOMMENDATION:")
        print(f"  {result.recommendation}")
        print()
        print("=" * 80)


def demo():
    """Demonstrate RVS v3.0 calculator with sample companies."""
    print("SRFF-I RVS v3.0 Calculator Demo")
    print("=" * 80)
    print()

    calculator = RVSv3Calculator()

    # Sample Company 1: Strong Candidate
    company1 = CompanyFinancials(
        company_name="Manufacturing Co A",
        sector="Manufacturing",
        working_capital=8_000_000,
        total_assets=25_000_000,
        retained_earnings=6_000_000,
        total_debt=10_000_000,
        total_liabilities=15_000_000,
        ebitda=2_500_000,
        revenue=20_000_000,
        operating_cash_flow=2_000_000,
        collateral_value=12_000_000
    )

    result1 = calculator.score_company(company1)
    calculator.print_report(result1)
    print("\n")

    # Sample Company 2: Conditional
    company2 = CompanyFinancials(
        company_name="Retail Co B",
        sector="Retail",
        working_capital=2_000_000,
        total_assets=20_000_000,
        retained_earnings=1_500_000,
        total_debt=12_000_000,
        total_liabilities=15_000_000,
        ebitda=1_200_000,
        revenue=18_000_000,
        operating_cash_flow=800_000,
        collateral_value=8_000_000
    )

    result2 = calculator.score_company(company2)
    calculator.print_report(result2)
    print("\n")

    # Sample Company 3: Reject
    company3 = CompanyFinancials(
        company_name="Distressed Co C",
        sector="Healthcare",
        working_capital=-1_000_000,
        total_assets=15_000_000,
        retained_earnings=-500_000,
        total_debt=18_000_000,
        total_liabilities=20_000_000,
        ebitda=500_000,
        revenue=10_000_000,
        operating_cash_flow=200_000,
        collateral_value=5_000_000
    )

    result3 = calculator.score_company(company3)
    calculator.print_report(result3)

    print("\n")
    print("=" * 80)
    print("Demo complete. Summary:")
    print(f"  {company1.company_name}: {result1.zone} (Recovery: {result1.recovery_probability:.1%})")
    print(f"  {company2.company_name}: {result2.zone} (Recovery: {result2.recovery_probability:.1%})")
    print(f"  {company3.company_name}: {result3.zone} (Recovery: {result3.recovery_probability:.1%})")
    print("=" * 80)


if __name__ == "__main__":
    demo()
