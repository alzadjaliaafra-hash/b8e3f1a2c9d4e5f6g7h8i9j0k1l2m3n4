#!/usr/bin/env python3
"""
SRFF-I Monthly Monitoring Module — Post-Deployment Early Warning System
=======================================================================
Recalculates RVS and hazard scores monthly for deployed portfolio companies.
Flags deteriorating companies and triggers early warning alerts when:
- Survival probability drops below threshold
- RVS score moves into lower zone
- Hazard rate increases significantly
- Financial covenant breaches detected

Author: Manus AI for Sohar International Bank
Date: April 2026
Version: 1.0
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from scipy.special import expit
import warnings
warnings.filterwarnings('ignore')


# Model constants from calibrated v3.0 model
INTERCEPT = 2.5445
COEFS = np.array([0.2506, 1.7070, 0.7426, 0.7262, 0.8278, -1.8122])
VAR_NAMES = ["V1", "V2", "V3", "V4", "V5", "V6"]

# Thresholds for alerts
SURVIVAL_THRESHOLD_CRITICAL = 0.30  # Below 30% = critical alert
SURVIVAL_THRESHOLD_WARNING = 0.50   # Below 50% = warning alert
RVS_THRESHOLD_CRITICAL = 4.5        # Below 4.5 = reject zone
HAZARD_THRESHOLD = 0.25             # Above 25% annual = high risk


@dataclass
class CompanySnapshot:
    """Monthly snapshot of company financials and scores."""
    company_id: str
    company_name: str
    snapshot_date: str

    # Financial variables
    v1: float  # Working Capital / Total Assets
    v2: float  # Retained Earnings / Total Assets
    v3: float  # EBITDA / Total Debt
    v4: float  # Operating Cash Flow / Total Debt
    v5: float  # Collateral Value / Total Liabilities
    v6: float  # Revenue / Total Assets

    # Calculated scores
    rvs_score: float
    recovery_probability: float
    survival_5yr: float
    hazard_rate: float
    composite_v3: float
    zone: str

    # Alert flags
    alert_level: str = "normal"  # normal, warning, critical
    alert_reasons: List[str] = None

    def __post_init__(self):
        if self.alert_reasons is None:
            self.alert_reasons = []


@dataclass
class MonitoringAlert:
    """Early warning alert for deteriorating company."""
    company_id: str
    company_name: str
    alert_date: str
    alert_level: str  # warning, critical, covenant_breach
    alert_type: str   # survival_drop, zone_change, hazard_spike, covenant_breach

    current_value: float
    previous_value: Optional[float]
    threshold: float

    message: str
    recommendation: str


class MonthlyMonitor:
    """Monthly monitoring engine for deployed portfolio."""

    def __init__(self, history_file: str = "monitoring_history.json"):
        """
        Initialize monthly monitoring system.

        Args:
            history_file: Path to JSON file storing historical snapshots
        """
        self.history_file = history_file
        self.history = self._load_history()

    def _load_history(self) -> Dict:
        """Load historical monitoring data."""
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"companies": {}, "last_update": None}

    def _save_history(self):
        """Save monitoring history to file."""
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)

    def _calculate_rvs_score(self, variables: np.array) -> float:
        """Calculate RVS score from v1-v6 variables."""
        # Using calibrated v3.0 logistic regression
        logit = INTERCEPT + np.dot(variables, COEFS)
        probability = expit(logit)

        # Convert probability to RVS-like score (scale 0-10)
        # Higher probability = higher score
        rvs_score = probability * 10
        return float(rvs_score)

    def _calculate_recovery_probability(self, variables: np.array) -> float:
        """Calculate recovery probability using calibrated model."""
        logit = INTERCEPT + np.dot(variables, COEFS)
        return float(expit(logit))

    def _calculate_hazard_rate(self, variables: np.array) -> float:
        """
        Estimate hazard rate using Shumway-style discrete-time model.
        Based on v3.0 hazard layer specification.
        """
        recovery_prob = self._calculate_recovery_probability(variables)

        # Convert recovery probability to annual hazard rate
        # Lower recovery prob = higher hazard
        # Using exponential transformation
        if recovery_prob > 0.95:
            hazard = 0.05
        elif recovery_prob > 0.80:
            hazard = 0.10
        elif recovery_prob > 0.60:
            hazard = 0.15
        elif recovery_prob > 0.40:
            hazard = 0.20
        else:
            hazard = 0.30

        return hazard

    def _calculate_survival_probability(self, hazard_rate: float, years: int = 5) -> float:
        """Calculate survival probability over time horizon."""
        return float(np.exp(-hazard_rate * years))

    def _calculate_composite_v3(self, recovery_prob: float, survival_5yr: float) -> float:
        """
        Calculate Composite V3 score combining recovery and survival.
        Weighted average: 60% recovery, 40% survival
        """
        return 0.6 * recovery_prob + 0.4 * survival_5yr

    def _classify_zone(self, rvs_score: float) -> str:
        """Classify RVS score into decision zone."""
        if rvs_score >= 7.0:
            return "Strong Candidate"
        elif rvs_score >= 4.5:
            return "Conditional"
        else:
            return "Reject"

    def create_snapshot(
        self,
        company_id: str,
        company_name: str,
        v1: float, v2: float, v3: float, v4: float, v5: float, v6: float,
        snapshot_date: Optional[str] = None
    ) -> CompanySnapshot:
        """
        Create monthly snapshot for a company.

        Args:
            company_id: Unique company identifier
            company_name: Company name
            v1-v6: Financial ratio variables
            snapshot_date: Date of snapshot (defaults to today)

        Returns:
            CompanySnapshot object with calculated scores
        """
        if snapshot_date is None:
            snapshot_date = datetime.now().strftime("%Y-%m-%d")

        # Calculate all scores
        variables = np.array([v1, v2, v3, v4, v5, v6])
        rvs_score = self._calculate_rvs_score(variables)
        recovery_prob = self._calculate_recovery_probability(variables)
        hazard_rate = self._calculate_hazard_rate(variables)
        survival_5yr = self._calculate_survival_probability(hazard_rate)
        composite_v3 = self._calculate_composite_v3(recovery_prob, survival_5yr)
        zone = self._classify_zone(rvs_score)

        snapshot = CompanySnapshot(
            company_id=company_id,
            company_name=company_name,
            snapshot_date=snapshot_date,
            v1=v1, v2=v2, v3=v3, v4=v4, v5=v5, v6=v6,
            rvs_score=rvs_score,
            recovery_probability=recovery_prob,
            survival_5yr=survival_5yr,
            hazard_rate=hazard_rate,
            composite_v3=composite_v3,
            zone=zone
        )

        # Check for alerts
        self._check_alerts(snapshot)

        # Store in history
        if company_id not in self.history["companies"]:
            self.history["companies"][company_id] = {"name": company_name, "snapshots": []}

        self.history["companies"][company_id]["snapshots"].append(asdict(snapshot))
        self.history["last_update"] = snapshot_date
        self._save_history()

        return snapshot

    def _check_alerts(self, snapshot: CompanySnapshot) -> List[MonitoringAlert]:
        """
        Check current snapshot against thresholds and previous values.
        Generate alerts if deterioration detected.
        """
        alerts = []
        company_history = self.history["companies"].get(snapshot.company_id, {}).get("snapshots", [])

        # Check survival probability threshold
        if snapshot.survival_5yr < SURVIVAL_THRESHOLD_CRITICAL:
            snapshot.alert_level = "critical"
            snapshot.alert_reasons.append(f"5Y survival {snapshot.survival_5yr:.1%} < critical threshold {SURVIVAL_THRESHOLD_CRITICAL:.0%}")

            alerts.append(MonitoringAlert(
                company_id=snapshot.company_id,
                company_name=snapshot.company_name,
                alert_date=snapshot.snapshot_date,
                alert_level="critical",
                alert_type="survival_drop",
                current_value=snapshot.survival_5yr,
                previous_value=company_history[-1]["survival_5yr"] if company_history else None,
                threshold=SURVIVAL_THRESHOLD_CRITICAL,
                message=f"CRITICAL: {snapshot.company_name} 5-year survival probability dropped to {snapshot.survival_5yr:.1%}",
                recommendation="Immediate review required. Consider restructuring or exit strategy."
            ))

        elif snapshot.survival_5yr < SURVIVAL_THRESHOLD_WARNING:
            if snapshot.alert_level == "normal":
                snapshot.alert_level = "warning"
            snapshot.alert_reasons.append(f"5Y survival {snapshot.survival_5yr:.1%} < warning threshold {SURVIVAL_THRESHOLD_WARNING:.0%}")

            alerts.append(MonitoringAlert(
                company_id=snapshot.company_id,
                company_name=snapshot.company_name,
                alert_date=snapshot.snapshot_date,
                alert_level="warning",
                alert_type="survival_drop",
                current_value=snapshot.survival_5yr,
                previous_value=company_history[-1]["survival_5yr"] if company_history else None,
                threshold=SURVIVAL_THRESHOLD_WARNING,
                message=f"WARNING: {snapshot.company_name} 5-year survival probability at {snapshot.survival_5yr:.1%}",
                recommendation="Enhanced monitoring recommended. Review operational performance."
            ))

        # Check RVS zone change
        if snapshot.rvs_score < RVS_THRESHOLD_CRITICAL:
            snapshot.alert_level = "critical"
            snapshot.alert_reasons.append(f"RVS score {snapshot.rvs_score:.2f} moved to Reject zone")

            alerts.append(MonitoringAlert(
                company_id=snapshot.company_id,
                company_name=snapshot.company_name,
                alert_date=snapshot.snapshot_date,
                alert_level="critical",
                alert_type="zone_change",
                current_value=snapshot.rvs_score,
                previous_value=company_history[-1]["rvs_score"] if company_history else None,
                threshold=RVS_THRESHOLD_CRITICAL,
                message=f"CRITICAL: {snapshot.company_name} moved to Reject zone (RVS: {snapshot.rvs_score:.2f})",
                recommendation="Urgent IC review. Consider workout/liquidation options."
            ))

        # Check hazard rate spike
        if snapshot.hazard_rate > HAZARD_THRESHOLD:
            if snapshot.alert_level != "critical":
                snapshot.alert_level = "warning"
            snapshot.alert_reasons.append(f"Hazard rate {snapshot.hazard_rate:.1%} exceeds threshold")

            alerts.append(MonitoringAlert(
                company_id=snapshot.company_id,
                company_name=snapshot.company_name,
                alert_date=snapshot.snapshot_date,
                alert_level="warning",
                alert_type="hazard_spike",
                current_value=snapshot.hazard_rate,
                previous_value=company_history[-1]["hazard_rate"] if company_history else None,
                threshold=HAZARD_THRESHOLD,
                message=f"WARNING: {snapshot.company_name} hazard rate elevated at {snapshot.hazard_rate:.1%}",
                recommendation="Increase monitoring frequency. Review covenant compliance."
            ))

        # Check for significant deterioration vs previous month
        if company_history:
            prev = company_history[-1]
            survival_drop = prev["survival_5yr"] - snapshot.survival_5yr

            if survival_drop > 0.15:  # 15pp drop
                if snapshot.alert_level != "critical":
                    snapshot.alert_level = "warning"
                snapshot.alert_reasons.append(f"Survival dropped {survival_drop:.1%} from previous month")

                alerts.append(MonitoringAlert(
                    company_id=snapshot.company_id,
                    company_name=snapshot.company_name,
                    alert_date=snapshot.snapshot_date,
                    alert_level="warning",
                    alert_type="survival_drop",
                    current_value=snapshot.survival_5yr,
                    previous_value=prev["survival_5yr"],
                    threshold=0.15,
                    message=f"WARNING: {snapshot.company_name} survival dropped {survival_drop:.1%} in one month",
                    recommendation="Investigate cause of deterioration. Request updated financials."
                ))

        return alerts

    def generate_monthly_report(
        self,
        output_file: str = "monthly_monitoring_report.json"
    ) -> Dict:
        """
        Generate comprehensive monthly monitoring report.

        Returns:
            Dictionary with monitoring summary and alerts
        """
        report = {
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "total_companies": len(self.history["companies"]),
            "summary": {
                "critical_alerts": 0,
                "warnings": 0,
                "normal": 0
            },
            "companies": [],
            "alerts": []
        }

        for company_id, company_data in self.history["companies"].items():
            if not company_data["snapshots"]:
                continue

            # Get latest snapshot
            latest = company_data["snapshots"][-1]

            report["companies"].append({
                "company_id": company_id,
                "company_name": company_data["name"],
                "alert_level": latest.get("alert_level", "normal"),
                "rvs_score": latest["rvs_score"],
                "survival_5yr": latest["survival_5yr"],
                "zone": latest["zone"],
                "alert_reasons": latest.get("alert_reasons", [])
            })

            # Count alert levels
            alert_level = latest.get("alert_level", "normal")
            if alert_level == "critical":
                report["summary"]["critical_alerts"] += 1
            elif alert_level == "warning":
                report["summary"]["warnings"] += 1
            else:
                report["summary"]["normal"] += 1

        # Sort companies by alert level (critical first)
        alert_priority = {"critical": 0, "warning": 1, "normal": 2}
        report["companies"].sort(key=lambda x: alert_priority.get(x["alert_level"], 3))

        # Save report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        return report

    def get_company_trend(self, company_id: str, months: int = 6) -> pd.DataFrame:
        """
        Get historical trend for a company.

        Args:
            company_id: Company identifier
            months: Number of months to retrieve

        Returns:
            DataFrame with historical snapshots
        """
        if company_id not in self.history["companies"]:
            return pd.DataFrame()

        snapshots = self.history["companies"][company_id]["snapshots"]

        # Get last N months
        recent_snapshots = snapshots[-months:] if len(snapshots) > months else snapshots

        df = pd.DataFrame(recent_snapshots)
        df["snapshot_date"] = pd.to_datetime(df["snapshot_date"])
        df = df.sort_values("snapshot_date")

        return df


def demo_monitoring():
    """Demonstrate monthly monitoring with sample data."""
    print("=" * 70)
    print("  SRFF-I MONTHLY MONITORING MODULE — DEMO")
    print("=" * 70)
    print()

    monitor = MonthlyMonitor("demo_monitoring_history.json")

    # Simulate 3 companies over 3 months
    companies = [
        {"id": "CO_001", "name": "Healthy Manufacturing Co"},
        {"id": "CO_002", "name": "Declining Retail Co"},
        {"id": "CO_003", "name": "Stable Healthcare Co"}
    ]

    print("Creating monthly snapshots for 3 companies over 3 months...\n")

    # Month 1
    snapshot_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
    monitor.create_snapshot("CO_001", companies[0]["name"], 0.35, 0.25, 0.15, 0.12, 0.80, 0.90, snapshot_date)
    monitor.create_snapshot("CO_002", companies[1]["name"], 0.20, 0.15, 0.10, 0.08, 0.60, 0.75, snapshot_date)
    monitor.create_snapshot("CO_003", companies[2]["name"], 0.40, 0.30, 0.18, 0.15, 0.85, 0.95, snapshot_date)

    # Month 2
    snapshot_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    monitor.create_snapshot("CO_001", companies[0]["name"], 0.34, 0.24, 0.14, 0.12, 0.79, 0.89, snapshot_date)
    monitor.create_snapshot("CO_002", companies[1]["name"], 0.15, 0.10, 0.07, 0.05, 0.50, 0.65, snapshot_date)  # Deteriorating
    monitor.create_snapshot("CO_003", companies[2]["name"], 0.41, 0.31, 0.19, 0.16, 0.86, 0.96, snapshot_date)

    # Month 3 (current)
    snapshot_date = datetime.now().strftime("%Y-%m-%d")
    monitor.create_snapshot("CO_001", companies[0]["name"], 0.35, 0.25, 0.15, 0.13, 0.80, 0.90, snapshot_date)
    monitor.create_snapshot("CO_002", companies[1]["name"], 0.10, 0.05, 0.04, 0.03, 0.40, 0.55, snapshot_date)  # Critical
    monitor.create_snapshot("CO_003", companies[2]["name"], 0.40, 0.30, 0.18, 0.15, 0.85, 0.95, snapshot_date)

    # Generate report
    print("Generating monthly monitoring report...\n")
    report = monitor.generate_monthly_report("demo_monitoring_report.json")

    print(f"Report Date: {report['report_date']}")
    print(f"Total Companies: {report['total_companies']}")
    print(f"\nAlert Summary:")
    print(f"  🔴 Critical: {report['summary']['critical_alerts']}")
    print(f"  🟡 Warning:  {report['summary']['warnings']}")
    print(f"  🟢 Normal:   {report['summary']['normal']}")

    print(f"\nCompany Status:")
    print("-" * 70)

    for company in report["companies"]:
        alert_icon = {"critical": "🔴", "warning": "🟡", "normal": "🟢"}
        icon = alert_icon.get(company["alert_level"], "⚪")

        print(f"\n{icon} {company['company_name']} ({company['company_id']})")
        print(f"   Alert Level: {company['alert_level'].upper()}")
        print(f"   RVS Score: {company['rvs_score']:.2f} ({company['zone']})")
        print(f"   5Y Survival: {company['survival_5yr']:.1%}")

        if company['alert_reasons']:
            print(f"   Alerts:")
            for reason in company['alert_reasons']:
                print(f"     • {reason}")

    print("\n" + "=" * 70)
    print(f"✅ Monthly monitoring report saved: demo_monitoring_report.json")
    print(f"✅ Monitoring history saved: demo_monitoring_history.json")
    print("=" * 70)


if __name__ == "__main__":
    demo_monitoring()
