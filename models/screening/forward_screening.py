#!/usr/bin/env python3
"""
SRFF-I Forward-Looking Screening — Automated Distressed Company Pipeline
========================================================================
Automates identification and screening of distressed companies using:
- Yahoo Finance API for market data
- Financial metrics from MSX (Muscat), ADX (Abu Dhabi), DFM (Dubai), Tadawul (Saudi)
- Automated distress signals: stock price drops, high debt ratios, negative cash flow
- RVS pre-screening for rescue viability

Replaces manual 50-company dataset with automated pipeline.

Author: Manus AI for Sohar International Bank
Date: April 2026
Version: 1.0
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Try importing yfinance (optional dependency)
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️  yfinance not installed. Install with: pip install yfinance")


# GCC Market Exchanges and Sample Tickers
GCC_EXCHANGES = {
    "MSX": {
        "name": "Muscat Securities Market",
        "country": "Oman",
        "suffix": ".OM",
        "sample_tickers": [
            "ORDS", "BKMB", "AHLI", "HSBC", "ABAR", "AIIN",  # Banks
            "NOOF", "OTEL", "ONIC", "OIFC", "ORAB"  # Others
        ]
    },
    "ADX": {
        "name": "Abu Dhabi Securities Exchange",
        "country": "UAE",
        "suffix": ".AD",
        "sample_tickers": [
            "ADCB", "FAB", "ADIB", "TAQA", "ADNOC", "ALDAR"
        ]
    },
    "DFM": {
        "name": "Dubai Financial Market",
        "country": "UAE",
        "suffix": ".DU",
        "sample_tickers": [
            "EMAAR", "DIB", "DFM", "ENBD", "ARAMEX", "TAKAFUL"
        ]
    },
    "TADAWUL": {
        "name": "Saudi Stock Exchange (Tadawul)",
        "country": "Saudi Arabia",
        "suffix": ".SAU",
        "sample_tickers": [
            "1180.SAU", "2010.SAU", "4030.SAU", "1120.SAU"  # Al Rajhi, SABIC, etc.
        ]
    }
}


# Distress signal thresholds
DISTRESS_THRESHOLDS = {
    "price_drop_6m": -0.30,      # 30% price drop in 6 months
    "price_drop_1y": -0.50,      # 50% price drop in 1 year
    "debt_to_equity": 2.0,       # D/E ratio > 200%
    "debt_to_assets": 0.70,      # Debt > 70% of assets
    "current_ratio": 1.0,        # Current ratio < 1.0
    "roe_negative": True,        # Negative ROE
    "earnings_decline": -0.25,   # 25% earnings decline YoY
    "beta": 1.5                  # High volatility (beta > 1.5)
}


class DistressedScreener:
    """Automated screener for distressed companies in GCC markets."""

    def __init__(self, exchanges: List[str] = None):
        """
        Initialize screener for specific exchanges.

        Args:
            exchanges: List of exchange codes (MSX, ADX, DFM, TADAWUL)
                      If None, screens all exchanges
        """
        if not YFINANCE_AVAILABLE:
            raise ImportError("yfinance required. Install: pip install yfinance")

        if exchanges is None:
            self.exchanges = list(GCC_EXCHANGES.keys())
        else:
            self.exchanges = [ex.upper() for ex in exchanges if ex.upper() in GCC_EXCHANGES]

    def _fetch_company_data(self, ticker: str) -> Optional[Dict]:
        """
        Fetch financial and market data for a company.

        Args:
            ticker: Stock ticker symbol with exchange suffix

        Returns:
            Dictionary with company data or None if fetch fails
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="1y")

            if hist.empty or not info:
                return None

            # Extract key metrics
            data = {
                "ticker": ticker,
                "company_name": info.get("longName", ticker),
                "sector": info.get("sector", "Unknown"),
                "industry": info.get("industry", "Unknown"),
                "market_cap": info.get("marketCap", 0),
                "employees": info.get("fullTimeEmployees", 0),

                # Financial metrics
                "total_debt": info.get("totalDebt", 0),
                "total_assets": info.get("totalAssets", 0),
                "total_equity": info.get("totalStockholderEquity", 0),
                "total_liabilities": info.get("totalLiabilities", 0),
                "revenue": info.get("totalRevenue", 0),
                "ebitda": info.get("ebitda", 0),
                "operating_cash_flow": info.get("operatingCashflow", 0),
                "free_cash_flow": info.get("freeCashflow", 0),
                "working_capital": info.get("workingCapital", 0),
                "retained_earnings": info.get("retainedEarnings", 0),

                # Market metrics
                "current_price": info.get("currentPrice", hist['Close'].iloc[-1] if not hist.empty else 0),
                "52w_high": info.get("fiftyTwoWeekHigh", 0),
                "52w_low": info.get("fiftyTwoWeekLow", 0),
                "beta": info.get("beta", 1.0),

                # Ratios
                "debt_to_equity": info.get("debtToEquity", 0) / 100 if info.get("debtToEquity") else None,
                "current_ratio": info.get("currentRatio", 0),
                "quick_ratio": info.get("quickRatio", 0),
                "roe": info.get("returnOnEquity", 0),
                "profit_margin": info.get("profitMargins", 0),

                # Historical prices
                "price_6m_ago": hist['Close'].iloc[-126] if len(hist) >= 126 else hist['Close'].iloc[0],
                "price_1y_ago": hist['Close'].iloc[0] if not hist.empty else 0,

                "fetch_date": datetime.now().strftime("%Y-%m-%d")
            }

            return data

        except Exception as e:
            print(f"  ⚠️  Failed to fetch {ticker}: {str(e)}")
            return None

    def _calculate_distress_signals(self, company: Dict) -> Dict:
        """
        Calculate distress signals for a company.

        Returns:
            Dictionary with distress scores and flags
        """
        signals = {
            "distress_score": 0,
            "flags": [],
            "severity": "normal"
        }

        current_price = company.get("current_price", 0)
        price_6m = company.get("price_6m_ago", current_price)
        price_1y = company.get("price_1y_ago", current_price)

        # Signal 1: Price drop
        if price_6m > 0:
            price_change_6m = (current_price - price_6m) / price_6m
            if price_change_6m < DISTRESS_THRESHOLDS["price_drop_6m"]:
                signals["flags"].append(f"Price dropped {price_change_6m:.1%} in 6 months")
                signals["distress_score"] += 2

        if price_1y > 0:
            price_change_1y = (current_price - price_1y) / price_1y
            if price_change_1y < DISTRESS_THRESHOLDS["price_drop_1y"]:
                signals["flags"].append(f"Price dropped {price_change_1y:.1%} in 1 year")
                signals["distress_score"] += 3

        # Signal 2: High debt ratios
        debt_to_equity = company.get("debt_to_equity")
        if debt_to_equity and debt_to_equity > DISTRESS_THRESHOLDS["debt_to_equity"]:
            signals["flags"].append(f"High D/E ratio: {debt_to_equity:.2f}")
            signals["distress_score"] += 2

        total_debt = company.get("total_debt", 0)
        total_assets = company.get("total_assets", 1)
        if total_assets > 0:
            debt_to_assets = total_debt / total_assets
            if debt_to_assets > DISTRESS_THRESHOLDS["debt_to_assets"]:
                signals["flags"].append(f"High debt/assets: {debt_to_assets:.1%}")
                signals["distress_score"] += 2

        # Signal 3: Liquidity issues
        current_ratio = company.get("current_ratio", 0)
        if current_ratio > 0 and current_ratio < DISTRESS_THRESHOLDS["current_ratio"]:
            signals["flags"].append(f"Low current ratio: {current_ratio:.2f}")
            signals["distress_score"] += 1

        # Signal 4: Negative profitability
        roe = company.get("roe", 0)
        if roe < 0:
            signals["flags"].append(f"Negative ROE: {roe:.1%}")
            signals["distress_score"] += 2

        # Signal 5: Negative cash flow
        fcf = company.get("free_cash_flow", 0)
        if fcf < 0:
            signals["flags"].append(f"Negative free cash flow")
            signals["distress_score"] += 1

        # Signal 6: High volatility
        beta = company.get("beta", 1.0)
        if beta and beta > DISTRESS_THRESHOLDS["beta"]:
            signals["flags"].append(f"High volatility (β={beta:.2f})")
            signals["distress_score"] += 1

        # Classify severity
        if signals["distress_score"] >= 7:
            signals["severity"] = "critical"
        elif signals["distress_score"] >= 4:
            signals["severity"] = "moderate"
        elif signals["distress_score"] >= 2:
            signals["severity"] = "mild"

        return signals

    def _calculate_rvs_variables(self, company: Dict) -> Optional[Dict]:
        """
        Calculate RVS input variables (V1-V6) from financial data.

        Returns:
            Dictionary with V1-V6 or None if insufficient data
        """
        try:
            total_assets = company.get("total_assets", 0)
            total_debt = company.get("total_debt", 1)  # Avoid division by zero
            total_liabilities = company.get("total_liabilities", 1)
            revenue = company.get("revenue", 0)

            if total_assets == 0 or total_debt == 0:
                return None

            variables = {
                "V1": company.get("working_capital", 0) / total_assets,  # WC / Assets
                "V2": company.get("retained_earnings", 0) / total_assets,  # RE / Assets
                "V3": company.get("ebitda", 0) / total_debt,  # EBITDA / Debt
                "V4": company.get("operating_cash_flow", 0) / total_debt,  # OCF / Debt
                "V5": 0.70,  # Placeholder: would need detailed asset breakdown
                "V6": revenue / total_assets  # Revenue / Assets
            }

            return variables

        except Exception:
            return None

    def screen_exchange(self, exchange: str, custom_tickers: List[str] = None) -> pd.DataFrame:
        """
        Screen companies from a specific exchange.

        Args:
            exchange: Exchange code (MSX, ADX, DFM, TADAWUL)
            custom_tickers: Optional list of specific tickers to screen

        Returns:
            DataFrame with screened companies and distress scores
        """
        if exchange.upper() not in GCC_EXCHANGES:
            raise ValueError(f"Unknown exchange: {exchange}")

        exchange_data = GCC_EXCHANGES[exchange.upper()]
        print(f"\n📊 Screening {exchange_data['name']} ({exchange})...")

        # Get tickers
        if custom_tickers:
            tickers = custom_tickers
        else:
            # Use sample tickers (in production, would fetch full exchange listings)
            base_tickers = exchange_data["sample_tickers"]
            suffix = exchange_data.get("suffix", "")
            tickers = [t if suffix in t else t + suffix for t in base_tickers]

        results = []

        for ticker in tickers:
            print(f"  Fetching {ticker}...", end=" ")

            # Fetch company data
            company_data = self._fetch_company_data(ticker)

            if company_data is None:
                print("❌ No data")
                continue

            # Calculate distress signals
            distress = self._calculate_distress_signals(company_data)

            # Calculate RVS variables
            rvs_vars = self._calculate_rvs_variables(company_data)

            # Combine all data
            result = {
                **company_data,
                "distress_score": distress["distress_score"],
                "distress_severity": distress["severity"],
                "distress_flags": "; ".join(distress["flags"]) if distress["flags"] else "None",
                "exchange": exchange.upper()
            }

            if rvs_vars:
                result.update(rvs_vars)

            results.append(result)
            print(f"✅ Score: {distress['distress_score']} ({distress['severity']})")

        df = pd.DataFrame(results)
        return df

    def screen_all_exchanges(self, save_to_file: str = None) -> pd.DataFrame:
        """
        Screen all configured GCC exchanges.

        Args:
            save_to_file: Optional path to save results as Excel/CSV

        Returns:
            DataFrame with all screened companies
        """
        print("=" * 70)
        print("  SRFF-I FORWARD-LOOKING SCREENING — GCC DISTRESSED COMPANIES")
        print("=" * 70)

        all_results = []

        for exchange in self.exchanges:
            try:
                df = self.screen_exchange(exchange)
                all_results.append(df)
            except Exception as e:
                print(f"  ⚠️  Error screening {exchange}: {str(e)}")

        if not all_results:
            print("\n❌ No data retrieved from any exchange")
            return pd.DataFrame()

        # Combine all results
        combined_df = pd.concat(all_results, ignore_index=True)

        # Sort by distress score (highest first)
        combined_df = combined_df.sort_values("distress_score", ascending=False)

        # Filter to only distressed companies (score >= 2)
        distressed_df = combined_df[combined_df["distress_score"] >= 2].copy()

        print("\n" + "=" * 70)
        print(f"✅ Screening complete!")
        print(f"   Total companies screened: {len(combined_df)}")
        print(f"   Distressed companies identified: {len(distressed_df)}")
        print(f"   Critical: {len(distressed_df[distressed_df['distress_severity']=='critical'])}")
        print(f"   Moderate: {len(distressed_df[distressed_df['distress_severity']=='moderate'])}")
        print(f"   Mild: {len(distressed_df[distressed_df['distress_severity']=='mild'])}")
        print("=" * 70)

        # Save results
        if save_to_file:
            if save_to_file.endswith('.xlsx'):
                distressed_df.to_excel(save_to_file, index=False)
            else:
                distressed_df.to_csv(save_to_file, index=False)
            print(f"💾 Results saved to: {save_to_file}")

        return distressed_df

    def generate_pipeline_report(self, df: pd.DataFrame, output_file: str = "distressed_pipeline.json"):
        """
        Generate structured pipeline report for IC review.

        Args:
            df: DataFrame with screened companies
            output_file: Path for JSON output
        """
        pipeline = {
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "total_screened": len(df),
            "distressed_identified": len(df[df["distress_score"] >= 2]),
            "exchanges": df["exchange"].unique().tolist() if "exchange" in df.columns else [],

            "summary_by_severity": {
                "critical": len(df[df["distress_severity"] == "critical"]),
                "moderate": len(df[df["distress_severity"] == "moderate"]),
                "mild": len(df[df["distress_severity"] == "mild"])
            },

            "summary_by_sector": df.groupby("sector")["distress_score"].agg(["count", "mean"]).to_dict()
            if "sector" in df.columns else {},

            "top_20_candidates": df.nlargest(20, "distress_score")[[
                "ticker", "company_name", "sector", "exchange",
                "distress_score", "distress_severity", "distress_flags"
            ]].to_dict(orient="records") if len(df) > 0 else []
        }

        with open(output_file, 'w') as f:
            json.dump(pipeline, f, indent=2)

        print(f"📄 Pipeline report saved: {output_file}")
        return pipeline


def demo_screening():
    """Demonstrate forward-looking screening (mock data if yfinance unavailable)."""
    print("=" * 70)
    print("  SRFF-I FORWARD-LOOKING SCREENING — DEMO")
    print("=" * 70)
    print()

    if not YFINANCE_AVAILABLE:
        print("⚠️  yfinance not available. Generating mock screening results...")
        print()

        # Generate mock data
        mock_data = []
        sectors = ["Manufacturing", "Retail", "Healthcare", "Technology", "Energy"]
        exchanges = ["MSX", "ADX", "DFM"]

        for i in range(30):
            distress_score = np.random.randint(0, 10)
            severity = "critical" if distress_score >= 7 else "moderate" if distress_score >= 4 else "mild"

            mock_data.append({
                "ticker": f"TICK{i:02d}",
                "company_name": f"Company {chr(65+i%26)}",
                "sector": np.random.choice(sectors),
                "exchange": np.random.choice(exchanges),
                "market_cap": np.random.randint(10, 500) * 1e6,
                "total_debt": np.random.randint(5, 100) * 1e6,
                "total_assets": np.random.randint(20, 200) * 1e6,
                "distress_score": distress_score,
                "distress_severity": severity,
                "distress_flags": "Mock distress signal"
            })

        df = pd.DataFrame(mock_data)
        df = df.sort_values("distress_score", ascending=False)

        print(f"✅ Mock screening complete!")
        print(f"   Total companies: {len(df)}")
        print(f"   Distressed: {len(df[df['distress_score'] >= 2])}")
        print()

        # Save results
        df.to_excel("mock_distressed_pipeline.xlsx", index=False)
        print("💾 Mock results saved to: mock_distressed_pipeline.xlsx")

        # Generate report
        screener = DistressedScreener([])
        screener.generate_pipeline_report(df, "mock_pipeline_report.json")

    else:
        # Real screening with yfinance
        print("Running live screening of GCC exchanges...")
        print("Note: Using sample tickers from each exchange")
        print()

        screener = DistressedScreener(exchanges=["MSX"])  # Start with MSX only
        df = screener.screen_all_exchanges(save_to_file="distressed_pipeline.xlsx")

        if not df.empty:
            screener.generate_pipeline_report(df)

    print("\n" + "=" * 70)
    print("✅ Forward-looking screening demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    demo_screening()
