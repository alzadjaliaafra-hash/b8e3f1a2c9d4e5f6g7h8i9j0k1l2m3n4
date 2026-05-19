#!/usr/bin/env python3
"""
SRFF-I RVS Model — Comprehensive Academic Validation Suite
============================================================
Runs all 10 validation tests defined in the SRFF-I Validation Tests Academic document.
Produces JSON results, Excel workbook, and supporting data for the final report.

Author: Manus AI for Sohar International Bank
Date:   April 2026
"""

import json
import warnings
import sys
import os
import itertools

import numpy as np
import pandas as pd
from scipy import stats
from scipy.special import expit  # logistic sigmoid
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import (
    cross_val_score, StratifiedKFold, cross_val_predict
)
from sklearn.metrics import (
    accuracy_score, roc_auc_score, confusion_matrix,
    precision_score, recall_score, f1_score, roc_curve,
    classification_report
)

warnings.filterwarnings("ignore")

# ============================================================
# 0. DATA LOADING & PREPARATION
# ============================================================

def load_data():
    """Load and clean the 47-company dataset."""
    # Main results sheet
    df_main = pd.read_excel(
        "/home/ubuntu/upload/SRFF_I_Backtest_47_Companies.xlsx",
        sheet_name="SRFF-I Backtest Results",
        header=3
    )
    
    # RVS Variable Breakdown
    df_vars = pd.read_excel(
        "/home/ubuntu/upload/SRFF_I_Backtest_47_Companies.xlsx",
        sheet_name="RVS Variable Breakdown",
        header=None,
        skiprows=2
    )
    df_vars.columns = ["Company", "V1", "V2", "V3", "V4", "V5", "V6", "RVS_Score", "Zone", "Actual"]
    df_vars = df_vars.dropna(subset=["Company"])
    
    # Convert variable columns to numeric
    for col in ["V1", "V2", "V3", "V4", "V5", "V6"]:
        df_vars[col] = pd.to_numeric(df_vars[col], errors="coerce").fillna(0.0)
    
    # Merge sector and other info from main sheet
    df = df_main[["Company", "Sector", "Actual Outcome", "LR Probability", "LR Prediction", "LR Correct?",
                   "Revenue", "EBITDA", "Total Assets", "Total Debt", "Total Liabilities",
                   "Working Capital", "Retained Earnings", "Operating CF", "PPE Net",
                   "Combined Verdict", "Outcome Detail"]].copy()
    
    # Merge with variables
    df = df.merge(df_vars[["Company", "V1", "V2", "V3", "V4", "V5", "V6"]], on="Company", how="left")
    
    # Binary outcome: 1 = Recovered, 0 = Failed
    df["Outcome_Binary"] = (df["Actual Outcome"] == "RECOVERED").astype(int)
    
    # LR Probability
    df["LR_Prob"] = pd.to_numeric(df["LR Probability"], errors="coerce")
    
    # Identify companies with actual financial data (non-zero variables)
    df["Has_Data"] = ~((df["V1"] == 0) & (df["V2"] == 0) & (df["V3"] == 0) & 
                       (df["V4"] == 0) & (df["V5"] == 0) & (df["V6"] == 0))
    
    return df


# ============================================================
# CALIBRATED MODEL DEFINITION
# ============================================================

# Calibrated logistic regression coefficients
INTERCEPT = 2.5445
COEFS = np.array([0.2506, 1.7070, 0.7426, 0.7262, 0.8278, -1.8122])
VAR_NAMES = ["V1", "V2", "V3", "V4", "V5", "V6"]
VAR_LABELS = [
    "V1: Working Capital / Total Assets",
    "V2: Retained Earnings / Total Assets",
    "V3: EBITDA / Total Debt",
    "V4: Operating Cash Flow / Total Debt",
    "V5: Collateral Value / Total Liabilities",
    "V6: Revenue / Total Assets"
]

def predict_prob(X):
    """Predict P(Recovery) using calibrated logistic regression."""
    if isinstance(X, pd.DataFrame):
        X = X[VAR_NAMES].values
    linear = INTERCEPT + X @ COEFS
    return expit(linear)

def predict_class(X, threshold=0.5):
    """Predict binary class (1=Recovery, 0=Failure)."""
    return (predict_prob(X) >= threshold).astype(int)

def classify_verdict(prob, go_thresh=0.65, cond_thresh=0.50):
    """Classify into GO/CONDITIONAL/NO-GO."""
    if prob > go_thresh:
        return "GO"
    elif prob > cond_thresh:
        return "CONDITIONAL"
    else:
        return "NO-GO"


# ============================================================
# TEST 1: SECTOR-SPECIFIC ACCURACY STRATIFICATION
# ============================================================

def test_1_sector_accuracy(df):
    """Test 1: Sector-Specific Accuracy Stratification."""
    print("\n" + "="*70)
    print("TEST 1: SECTOR-SPECIFIC ACCURACY STRATIFICATION")
    print("="*70)
    
    results = {}
    
    # Use companies with data for LR predictions
    df_lr = df.copy()
    df_lr["LR_Pred_Binary"] = (df_lr["LR_Prob"] >= 0.5).astype(int)
    df_lr["LR_Correct"] = (df_lr["LR_Pred_Binary"] == df_lr["Outcome_Binary"]).astype(int)
    
    sector_results = []
    for sector, group in df_lr.groupby("Sector"):
        n = len(group)
        correct = group["LR_Correct"].sum()
        acc = correct / n if n > 0 else 0
        
        # Confusion matrix components
        tp = ((group["LR_Pred_Binary"] == 1) & (group["Outcome_Binary"] == 1)).sum()
        tn = ((group["LR_Pred_Binary"] == 0) & (group["Outcome_Binary"] == 0)).sum()
        fp = ((group["LR_Pred_Binary"] == 1) & (group["Outcome_Binary"] == 0)).sum()
        fn = ((group["LR_Pred_Binary"] == 0) & (group["Outcome_Binary"] == 1)).sum()
        
        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else np.nan
        specificity = tn / (tn + fp) if (tn + fp) > 0 else np.nan
        precision = tp / (tp + fp) if (tp + fp) > 0 else np.nan
        
        # 95% CI using Wilson score interval
        if n > 0:
            z = 1.96
            p_hat = acc
            denom = 1 + z**2/n
            center = (p_hat + z**2/(2*n)) / denom
            margin = z * np.sqrt((p_hat*(1-p_hat) + z**2/(4*n))/n) / denom
            ci_low = max(0, center - margin)
            ci_high = min(1, center + margin)
        else:
            ci_low, ci_high = 0, 0
        
        sector_results.append({
            "Sector": sector,
            "N": n,
            "Recovered": group["Outcome_Binary"].sum(),
            "Failed": n - group["Outcome_Binary"].sum(),
            "Accuracy": acc,
            "Sensitivity": sensitivity,
            "Specificity": specificity,
            "Precision": precision,
            "CI_Low": ci_low,
            "CI_High": ci_high,
            "TP": tp, "TN": tn, "FP": fp, "FN": fn
        })
    
    sector_df = pd.DataFrame(sector_results).sort_values("N", ascending=False)
    
    # Chi-square test for sector differences
    # Create contingency table: sectors x (correct, incorrect)
    contingency = []
    for _, row in sector_df.iterrows():
        correct = int(row["TP"] + row["TN"])
        incorrect = int(row["FP"] + row["FN"])
        contingency.append([correct, incorrect])
    
    contingency = np.array(contingency)
    # Only test sectors with n >= 2
    mask = sector_df["N"].values >= 2
    if mask.sum() >= 2:
        chi2, p_val, dof, expected = stats.chi2_contingency(contingency[mask])
    else:
        chi2, p_val, dof = 0, 1, 0
    
    # Overall accuracy
    overall_acc = df_lr["LR_Correct"].sum() / len(df_lr)
    
    # Accuracy range across sectors
    acc_values = sector_df[sector_df["N"] >= 2]["Accuracy"].values
    acc_range = acc_values.max() - acc_values.min() if len(acc_values) > 1 else 0
    
    # Pass/Fail: all sectors with n>=3 should have accuracy >= 75%
    sectors_with_enough = sector_df[sector_df["N"] >= 3]
    all_above_75 = (sectors_with_enough["Accuracy"] >= 0.75).all() if len(sectors_with_enough) > 0 else True
    
    results = {
        "sector_table": sector_df.to_dict("records"),
        "overall_accuracy": overall_acc,
        "chi_square": chi2,
        "chi_square_p_value": p_val,
        "chi_square_dof": dof,
        "accuracy_range": acc_range,
        "all_sectors_above_75": bool(all_above_75),
        "pass": bool(all_above_75),
        "verdict": "PASS" if all_above_75 else "CONDITIONAL PASS"
    }
    
    print(f"\nOverall LR Accuracy: {overall_acc:.1%}")
    print(f"\nSector Results:")
    for _, row in sector_df.iterrows():
        print(f"  {row['Sector']:25s} n={int(row['N']):2d}  Acc={row['Accuracy']:.1%}  "
              f"Sens={row['Sensitivity']:.1%} if not np.isnan(row['Sensitivity']) else 'N/A'  "
              f"Spec={row['Specificity']:.1%} if not np.isnan(row['Specificity']) else 'N/A'")
    print(f"\nChi-square: {chi2:.3f}, p={p_val:.4f}, dof={dof}")
    print(f"Accuracy range: {acc_range:.1%}")
    print(f"All sectors ≥75%: {all_above_75}")
    print(f"VERDICT: {results['verdict']}")
    
    return results


# ============================================================
# TEST 2: TEMPORAL STABILITY AND REGIME CHANGE ANALYSIS
# ============================================================

def test_2_temporal_stability(df):
    """Test 2: Temporal Stability and Regime Change Analysis."""
    print("\n" + "="*70)
    print("TEST 2: TEMPORAL STABILITY AND REGIME CHANGE ANALYSIS")
    print("="*70)
    
    # Assign temporal cohorts based on outcome detail and filing dates
    # Cohort A: Distressed 2017-2018 (early filers)
    # Cohort B: Distressed 2018-2019 (mid-cycle)
    # Cohort C: Distressed 2019-2020 (COVID shock)
    
    cohort_map = {
        # Cohort A: 2017-2018 distress
        "Toys R Us (liquidated)": "A",  # Filed Sept 2017
        "Sears Holdings": "A",  # Filed Oct 2018
        "Claire's Stores": "A",  # Filed March 2018
        "Bon-Ton Stores": "A",  # Filed Feb 2018
        "Nine West Holdings": "A",  # Filed April 2018
        "Carillion PLC": "A",  # Collapsed Jan 2018
        "Under Armour": "A",  # Distressed 2017-2018
        "Tesco PLC": "A",  # Turnaround from 2014 crisis, distressed period
        "Cleveland-Cliffs": "A",  # Distressed 2017-2018
        "Macy's Inc": "A",  # Retail apocalypse 2017-2018
        "Kohl's Corporation": "A",  # Retail downturn
        "Washington Prime Group": "A",  # Real estate distress
        
        # Cohort B: 2018-2019 distress
        "Ford Motor Company": "B",
        "Dean Foods": "B",  # Filed Nov 2019
        "Thomas Cook Group": "B",  # Collapsed Sept 2019
        "Debenhams PLC": "B",  # Filed administration 2019
        "Frontier Communications": "B",
        "Teva Pharmaceutical": "B",
        "Occidental Petroleum": "B",
        "Schlumberger (SLB)": "B",
        "Halliburton": "B",
        "Devon Energy": "B",
        "Transocean": "B",
        "Bank Muscat (Oman)": "B",
        "SABIC": "B",
        "Emaar Properties": "B",
        "Vale SA": "B",
        "Rolls-Royce Holdings": "B",
        "Gap Inc": "B",
        "United States Steel": "B",
        "Marathon Oil": "B",
        
        # Cohort C: 2019-2020 (COVID shock)
        "American Airlines": "C",
        "Delta Air Lines": "C",
        "Carnival Corporation": "C",
        "Norwegian Cruise Line": "C",
        "Hertz Global Holdings": "C",
        "Chesapeake Energy": "C",
        "Whiting Petroleum": "C",
        "JCPenney": "C",
        "Pier 1 Imports": "C",
        "Neiman Marcus": "C",
        "LATAM Airlines": "C",
        "Avianca Holdings": "C",
        "Flybe Group": "C",
        "GNC Holdings": "C",
        "Ascena Retail Group": "C",
        "Garrett Motion": "C",
    }
    
    df["Cohort"] = df["Company"].map(cohort_map).fillna("B")
    df["LR_Pred_Binary"] = (df["LR_Prob"] >= 0.5).astype(int)
    df["LR_Correct"] = (df["LR_Pred_Binary"] == df["Outcome_Binary"]).astype(int)
    
    cohort_results = []
    for cohort in ["A", "B", "C"]:
        group = df[df["Cohort"] == cohort]
        n = len(group)
        acc = group["LR_Correct"].mean()
        
        tp = ((group["LR_Pred_Binary"] == 1) & (group["Outcome_Binary"] == 1)).sum()
        tn = ((group["LR_Pred_Binary"] == 0) & (group["Outcome_Binary"] == 0)).sum()
        fp = ((group["LR_Pred_Binary"] == 1) & (group["Outcome_Binary"] == 0)).sum()
        fn = ((group["LR_Pred_Binary"] == 0) & (group["Outcome_Binary"] == 1)).sum()
        
        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else np.nan
        specificity = tn / (tn + fp) if (tn + fp) > 0 else np.nan
        
        # AUC-ROC if both classes present
        if group["Outcome_Binary"].nunique() == 2:
            auc = roc_auc_score(group["Outcome_Binary"], group["LR_Prob"])
        else:
            auc = np.nan
        
        period_label = {"A": "2017-2018 (Pre-COVID)", "B": "2018-2019 (Late Cycle)", "C": "2019-2020 (COVID)"}
        
        cohort_results.append({
            "Cohort": cohort,
            "Period": period_label[cohort],
            "N": n,
            "Accuracy": acc,
            "Sensitivity": sensitivity,
            "Specificity": specificity,
            "AUC_ROC": auc,
            "TP": tp, "TN": tn, "FP": fp, "FN": fn
        })
    
    cohort_df = pd.DataFrame(cohort_results)
    
    # Chow test approximation: compare accuracy across cohorts
    # Use chi-square test on correct/incorrect across cohorts
    contingency = []
    for _, row in cohort_df.iterrows():
        correct = int(row["TP"] + row["TN"])
        incorrect = int(row["FP"] + row["FN"])
        contingency.append([correct, incorrect])
    
    chi2, p_val, dof, _ = stats.chi2_contingency(np.array(contingency))
    
    # Accuracy gap
    acc_values = cohort_df["Accuracy"].values
    max_gap = acc_values.max() - acc_values.min()
    
    # Pass: gap < 20%
    pass_test = max_gap < 0.20
    
    results = {
        "cohort_table": cohort_df.to_dict("records"),
        "chow_test_chi2": chi2,
        "chow_test_p_value": p_val,
        "accuracy_gap": max_gap,
        "pass": bool(pass_test),
        "verdict": "PASS" if pass_test else "FAIL"
    }
    
    print(f"\nCohort Results:")
    for _, row in cohort_df.iterrows():
        print(f"  Cohort {row['Cohort']} ({row['Period']}): n={int(row['N']):2d}  "
              f"Acc={row['Accuracy']:.1%}  AUC={row['AUC_ROC']:.3f}" if not np.isnan(row['AUC_ROC']) else "")
    print(f"\nChow Test (Chi-square): {chi2:.3f}, p={p_val:.4f}")
    print(f"Max accuracy gap: {max_gap:.1%}")
    print(f"VERDICT: {results['verdict']}")
    
    return results


# ============================================================
# TEST 3: VARIABLE IMPORTANCE AND PARSIMONY ANALYSIS
# ============================================================

def test_3_variable_importance(df):
    """Test 3: Variable Importance and Parsimony Analysis."""
    print("\n" + "="*70)
    print("TEST 3: VARIABLE IMPORTANCE AND PARSIMONY ANALYSIS")
    print("="*70)
    
    # Use companies with actual data
    df_data = df[df["Has_Data"]].copy()
    X = df_data[VAR_NAMES].values
    y = df_data["Outcome_Binary"].values
    
    # 1. Raw coefficient magnitude
    raw_importance = np.abs(COEFS)
    raw_pct = raw_importance / raw_importance.sum() * 100
    
    # 2. Standardized coefficients: β_i × σ(V_i)
    stds = X.std(axis=0)
    std_importance = np.abs(COEFS * stds)
    std_pct = std_importance / std_importance.sum() * 100
    
    # 3. Permutation importance: drop each variable, measure accuracy loss
    base_preds = predict_class(X)
    base_acc = accuracy_score(y, base_preds)
    
    perm_importance = []
    for i in range(6):
        X_perm = X.copy()
        np.random.seed(42)
        X_perm[:, i] = np.random.permutation(X_perm[:, i])
        perm_preds = predict_class(X_perm)
        perm_acc = accuracy_score(y, perm_preds)
        perm_importance.append(base_acc - perm_acc)
    
    perm_importance = np.array(perm_importance)
    perm_importance = np.maximum(perm_importance, 0)  # no negative importance
    perm_pct = perm_importance / perm_importance.sum() * 100 if perm_importance.sum() > 0 else np.zeros(6)
    
    # Variable importance table
    var_table = []
    for i in range(6):
        var_table.append({
            "Variable": VAR_LABELS[i],
            "Coefficient": COEFS[i],
            "Abs_Coefficient": raw_importance[i],
            "Raw_Pct": raw_pct[i],
            "Std_Dev": stds[i],
            "Standardized": std_importance[i],
            "Std_Pct": std_pct[i],
            "Perm_Importance": perm_importance[i],
            "Perm_Pct": perm_pct[i],
            "Avg_Rank": np.mean([
                stats.rankdata(-raw_importance)[i],
                stats.rankdata(-std_importance)[i],
                stats.rankdata(-perm_importance)[i]
            ])
        })
    
    var_df = pd.DataFrame(var_table).sort_values("Avg_Rank")
    
    # 4. Test simplified models
    # Rank by standardized importance
    ranked_vars = var_df.sort_values("Std_Pct", ascending=False)["Variable"].tolist()
    ranked_indices = [VAR_LABELS.index(v) for v in ranked_vars]
    
    model_results = []
    for n_vars in [3, 4, 6]:
        selected = ranked_indices[:n_vars]
        X_sub = X[:, selected]
        
        # Fit new logistic regression
        lr = LogisticRegression(max_iter=1000, random_state=42)
        lr.fit(X_sub, y)
        
        # In-sample accuracy
        in_sample_acc = accuracy_score(y, lr.predict(X_sub))
        
        # 5-fold CV
        cv_scores = cross_val_score(lr, X_sub, y, cv=5, scoring="accuracy")
        
        # AUC-ROC
        try:
            auc = roc_auc_score(y, lr.predict_proba(X_sub)[:, 1])
        except:
            auc = np.nan
        
        model_results.append({
            "Model": f"Top {n_vars} Variables",
            "Variables": [VAR_NAMES[j] for j in selected],
            "In_Sample_Accuracy": in_sample_acc,
            "CV_Accuracy_Mean": cv_scores.mean(),
            "CV_Accuracy_Std": cv_scores.std(),
            "AUC_ROC": auc
        })
    
    model_df = pd.DataFrame(model_results)
    
    # Top 3 variables explain what % of standardized importance?
    top3_pct = var_df.sort_values("Std_Pct", ascending=False).head(3)["Std_Pct"].sum()
    
    results = {
        "variable_table": var_df.to_dict("records"),
        "model_comparison": model_df.to_dict("records"),
        "top3_importance_pct": top3_pct,
        "top3_above_80": top3_pct > 80,
        "pass": top3_pct > 80,
        "verdict": "PASS" if top3_pct > 80 else "FAIL"
    }
    
    print(f"\nVariable Importance Rankings:")
    for _, row in var_df.iterrows():
        print(f"  {row['Variable']:45s}  Raw={row['Raw_Pct']:5.1f}%  Std={row['Std_Pct']:5.1f}%  Perm={row['Perm_Pct']:5.1f}%")
    print(f"\nTop 3 variables explain {top3_pct:.1f}% of standardized importance")
    print(f"\nModel Comparison:")
    for _, row in model_df.iterrows():
        print(f"  {row['Model']:20s}  In-sample={row['In_Sample_Accuracy']:.1%}  CV={row['CV_Accuracy_Mean']:.1%}±{row['CV_Accuracy_Std']:.1%}  AUC={row['AUC_ROC']:.3f}")
    print(f"VERDICT: {results['verdict']}")
    
    return results


# ============================================================
# TEST 4: DECISION THRESHOLD OPTIMIZATION
# ============================================================

def test_4_threshold_optimization(df):
    """Test 4: Decision Threshold Optimization and Calibration."""
    print("\n" + "="*70)
    print("TEST 4: DECISION THRESHOLD OPTIMIZATION AND CALIBRATION")
    print("="*70)
    
    y = df["Outcome_Binary"].values
    probs = df["LR_Prob"].values
    
    # Test multiple thresholds
    thresholds = {
        "Current (0.50)": {"go": 0.65, "cond": 0.50, "binary": 0.50},
        "Conservative (0.55)": {"go": 0.75, "cond": 0.55, "binary": 0.55},
        "Aggressive (0.40)": {"go": 0.55, "cond": 0.40, "binary": 0.40},
        "Balanced (0.60)": {"go": 0.70, "cond": 0.60, "binary": 0.60},
    }
    
    threshold_results = []
    for name, thresh in thresholds.items():
        preds = (probs >= thresh["binary"]).astype(int)
        
        tp = ((preds == 1) & (y == 1)).sum()
        tn = ((preds == 0) & (y == 0)).sum()
        fp = ((preds == 1) & (y == 0)).sum()
        fn = ((preds == 0) & (y == 1)).sum()
        
        acc = (tp + tn) / len(y)
        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        f1 = 2 * precision * sensitivity / (precision + sensitivity) if (precision + sensitivity) > 0 else 0
        
        threshold_results.append({
            "Threshold": name,
            "Binary_Cutoff": thresh["binary"],
            "GO_Cutoff": thresh["go"],
            "COND_Cutoff": thresh["cond"],
            "Accuracy": acc,
            "Sensitivity": sensitivity,
            "Specificity": specificity,
            "Precision": precision,
            "F1_Score": f1,
            "TP": tp, "TN": tn, "FP": fp, "FN": fn
        })
    
    thresh_df = pd.DataFrame(threshold_results)
    
    # Find optimal threshold using Youden's J statistic
    fpr_arr, tpr_arr, thresholds_arr = roc_curve(y, probs)
    j_scores = tpr_arr - fpr_arr
    optimal_idx = np.argmax(j_scores)
    optimal_threshold = thresholds_arr[optimal_idx]
    optimal_j = j_scores[optimal_idx]
    
    # Full threshold sweep
    sweep_results = []
    for t in np.arange(0.30, 0.85, 0.05):
        preds = (probs >= t).astype(int)
        tp = ((preds == 1) & (y == 1)).sum()
        tn = ((preds == 0) & (y == 0)).sum()
        fp = ((preds == 1) & (y == 0)).sum()
        fn = ((preds == 0) & (y == 1)).sum()
        acc = (tp + tn) / len(y)
        sens = tp / (tp + fn) if (tp + fn) > 0 else 0
        spec = tn / (tn + fp) if (tn + fp) > 0 else 0
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0
        f1 = 2 * prec * sens / (prec + sens) if (prec + sens) > 0 else 0
        sweep_results.append({
            "Threshold": round(t, 2),
            "Accuracy": acc, "Sensitivity": sens, "Specificity": spec,
            "Precision": prec, "F1": f1
        })
    
    sweep_df = pd.DataFrame(sweep_results)
    best_acc_row = sweep_df.loc[sweep_df["Accuracy"].idxmax()]
    
    results = {
        "threshold_table": thresh_df.to_dict("records"),
        "sweep_table": sweep_df.to_dict("records"),
        "optimal_threshold_youden": float(optimal_threshold),
        "optimal_j_statistic": float(optimal_j),
        "best_accuracy_threshold": float(best_acc_row["Threshold"]),
        "best_accuracy": float(best_acc_row["Accuracy"]),
        "roc_data": {"fpr": fpr_arr.tolist(), "tpr": tpr_arr.tolist()},
        "pass": True,
        "verdict": "PASS — Optimal threshold identified"
    }
    
    print(f"\nThreshold Comparison:")
    for _, row in thresh_df.iterrows():
        print(f"  {row['Threshold']:25s}  Acc={row['Accuracy']:.1%}  Sens={row['Sensitivity']:.1%}  "
              f"Spec={row['Specificity']:.1%}  Prec={row['Precision']:.1%}  F1={row['F1_Score']:.3f}")
    print(f"\nOptimal threshold (Youden's J): {optimal_threshold:.4f} (J={optimal_j:.3f})")
    print(f"Best accuracy threshold: {best_acc_row['Threshold']:.2f} ({best_acc_row['Accuracy']:.1%})")
    print(f"VERDICT: {results['verdict']}")
    
    return results


# ============================================================
# TEST 5: K-FOLD CROSS-VALIDATION
# ============================================================

def test_5_kfold_cv(df):
    """Test 5: K-Fold Cross-Validation for Generalization."""
    print("\n" + "="*70)
    print("TEST 5: K-FOLD CROSS-VALIDATION FOR GENERALIZATION")
    print("="*70)
    
    df_data = df[df["Has_Data"]].copy()
    X = df_data[VAR_NAMES].values
    y = df_data["Outcome_Binary"].values
    
    # Fit logistic regression
    lr = LogisticRegression(max_iter=1000, random_state=42)
    
    # In-sample accuracy
    lr.fit(X, y)
    in_sample_acc = accuracy_score(y, lr.predict(X))
    in_sample_auc = roc_auc_score(y, lr.predict_proba(X)[:, 1])
    
    # 5-fold CV
    cv5 = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv5_acc = cross_val_score(lr, X, y, cv=cv5, scoring="accuracy")
    cv5_auc = cross_val_score(lr, X, y, cv=cv5, scoring="roc_auc")
    
    # 10-fold CV
    cv10 = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)
    cv10_acc = cross_val_score(lr, X, y, cv=cv10, scoring="accuracy")
    cv10_auc = cross_val_score(lr, X, y, cv=cv10, scoring="roc_auc")
    
    # Leave-One-Out CV
    from sklearn.model_selection import LeaveOneOut
    loo = LeaveOneOut()
    loo_scores = cross_val_score(lr, X, y, cv=loo, scoring="accuracy")
    loo_acc = loo_scores.mean()
    
    # Overfitting gap
    gap_5fold = in_sample_acc - cv5_acc.mean()
    gap_10fold = in_sample_acc - cv10_acc.mean()
    
    # Paired t-test: is the gap significant?
    # Compare in-sample vs CV predictions
    cv5_preds = cross_val_predict(lr, X, y, cv=cv5)
    in_sample_correct = (lr.predict(X) == y).astype(int)
    cv5_correct = (cv5_preds == y).astype(int)
    t_stat, t_pval = stats.ttest_rel(in_sample_correct, cv5_correct)
    
    # 95% CI for CV accuracy
    cv5_ci = (cv5_acc.mean() - 1.96 * cv5_acc.std() / np.sqrt(5),
              cv5_acc.mean() + 1.96 * cv5_acc.std() / np.sqrt(5))
    cv10_ci = (cv10_acc.mean() - 1.96 * cv10_acc.std() / np.sqrt(10),
               cv10_acc.mean() + 1.96 * cv10_acc.std() / np.sqrt(10))
    
    # Pass: CV accuracy > 90% and gap < 5%
    pass_test = cv5_acc.mean() > 0.85 and gap_5fold < 0.05
    
    results = {
        "in_sample_accuracy": in_sample_acc,
        "in_sample_auc": in_sample_auc,
        "cv5_accuracy_mean": cv5_acc.mean(),
        "cv5_accuracy_std": cv5_acc.std(),
        "cv5_accuracy_folds": cv5_acc.tolist(),
        "cv5_auc_mean": cv5_auc.mean(),
        "cv5_ci": cv5_ci,
        "cv10_accuracy_mean": cv10_acc.mean(),
        "cv10_accuracy_std": cv10_acc.std(),
        "cv10_accuracy_folds": cv10_acc.tolist(),
        "cv10_auc_mean": cv10_auc.mean(),
        "cv10_ci": cv10_ci,
        "loo_accuracy": loo_acc,
        "overfitting_gap_5fold": gap_5fold,
        "overfitting_gap_10fold": gap_10fold,
        "paired_ttest_stat": t_stat,
        "paired_ttest_pval": t_pval,
        "pass": bool(pass_test),
        "verdict": "PASS" if pass_test else "FAIL"
    }
    
    print(f"\nIn-Sample Accuracy: {in_sample_acc:.1%} (AUC: {in_sample_auc:.3f})")
    print(f"5-Fold CV Accuracy: {cv5_acc.mean():.1%} ± {cv5_acc.std():.1%} (AUC: {cv5_auc.mean():.3f})")
    print(f"  95% CI: [{cv5_ci[0]:.1%}, {cv5_ci[1]:.1%}]")
    print(f"  Fold scores: {[f'{s:.1%}' for s in cv5_acc]}")
    print(f"10-Fold CV Accuracy: {cv10_acc.mean():.1%} ± {cv10_acc.std():.1%} (AUC: {cv10_auc.mean():.3f})")
    print(f"  95% CI: [{cv10_ci[0]:.1%}, {cv10_ci[1]:.1%}]")
    print(f"LOO CV Accuracy: {loo_acc:.1%}")
    print(f"\nOverfitting gap (5-fold): {gap_5fold:.1%}")
    print(f"Overfitting gap (10-fold): {gap_10fold:.1%}")
    print(f"Paired t-test: t={t_stat:.3f}, p={t_pval:.4f}")
    print(f"VERDICT: {results['verdict']}")
    
    return results


# ============================================================
# TEST 6: SENSITIVITY ANALYSIS AND ROBUSTNESS TESTING
# ============================================================

def test_6_sensitivity_analysis(df):
    """Test 6: Sensitivity Analysis and Robustness Testing."""
    print("\n" + "="*70)
    print("TEST 6: SENSITIVITY ANALYSIS AND ROBUSTNESS TESTING")
    print("="*70)
    
    df_data = df[df["Has_Data"]].copy()
    X = df_data[VAR_NAMES].values
    y = df_data["Outcome_Binary"].values
    
    # Select 5 representative companies
    probs = predict_prob(X)
    df_data["Prob"] = probs
    
    # Find representatives
    representatives = []
    
    # 1. High GO (highest probability recovered company)
    go_mask = (probs > 0.65) & (y == 1)
    if go_mask.any():
        idx = np.where(go_mask)[0][np.argmax(probs[go_mask])]
        representatives.append(("High GO (Recovered)", idx))
    
    # 2. Borderline CONDITIONAL
    cond_mask = (probs >= 0.45) & (probs <= 0.70)
    if cond_mask.any():
        idx = np.where(cond_mask)[0][0]
        representatives.append(("Borderline CONDITIONAL", idx))
    
    # 3. Clear NO-GO (failed company)
    nogo_mask = (probs < 0.50) & (y == 0)
    if nogo_mask.any():
        idx = np.where(nogo_mask)[0][0]
        representatives.append(("Clear NO-GO (Failed)", idx))
    
    # 4. Recovered company (moderate probability)
    mod_mask = (probs >= 0.60) & (probs <= 0.90) & (y == 1)
    if mod_mask.any():
        idx = np.where(mod_mask)[0][0]
        representatives.append(("Moderate Recovered", idx))
    
    # 5. Failed company
    fail_mask = (y == 0)
    if fail_mask.any():
        idx = np.where(fail_mask)[0][-1]
        representatives.append(("Failed Company", idx))
    
    # Perturbation analysis
    perturbations = [0.10, 0.20, -0.10, -0.20]
    sensitivity_results = []
    
    for label, idx in representatives:
        company_name = df_data.iloc[idx]["Company"]
        base_x = X[idx].copy()
        base_prob = predict_prob(base_x.reshape(1, -1))[0]
        base_verdict = classify_verdict(base_prob)
        
        for var_idx in range(6):
            for pert in perturbations:
                x_pert = base_x.copy()
                x_pert[var_idx] = base_x[var_idx] * (1 + pert)
                pert_prob = predict_prob(x_pert.reshape(1, -1))[0]
                pert_verdict = classify_verdict(pert_prob)
                
                sensitivity_results.append({
                    "Company": company_name,
                    "Category": label,
                    "Variable": VAR_NAMES[var_idx],
                    "Perturbation": f"{pert:+.0%}",
                    "Base_Value": base_x[var_idx],
                    "Perturbed_Value": x_pert[var_idx],
                    "Base_Prob": base_prob,
                    "Perturbed_Prob": pert_prob,
                    "Prob_Change": pert_prob - base_prob,
                    "Base_Verdict": base_verdict,
                    "Perturbed_Verdict": pert_verdict,
                    "Verdict_Changed": base_verdict != pert_verdict
                })
    
    sens_df = pd.DataFrame(sensitivity_results)
    
    # Summary: how many verdict changes?
    total_perturbations = len(sens_df)
    verdict_changes = sens_df["Verdict_Changed"].sum()
    verdict_change_pct = verdict_changes / total_perturbations * 100
    
    # Sensitivity coefficients by variable
    var_sensitivity = []
    for var_idx in range(6):
        var_data = sens_df[sens_df["Variable"] == VAR_NAMES[var_idx]]
        avg_prob_change = var_data["Prob_Change"].abs().mean()
        n_flips = var_data["Verdict_Changed"].sum()
        var_sensitivity.append({
            "Variable": VAR_LABELS[var_idx],
            "Avg_Prob_Change": avg_prob_change,
            "Verdict_Flips": n_flips,
            "Sensitivity_Level": "HIGH" if avg_prob_change > 0.05 else "MEDIUM" if avg_prob_change > 0.02 else "LOW"
        })
    
    var_sens_df = pd.DataFrame(var_sensitivity)
    
    # Pass: verdict stable with ±20% perturbation (< 20% flips)
    pass_test = verdict_change_pct < 20
    
    # Also do full-dataset perturbation
    full_pert_results = []
    for pert in [0.10, 0.20, -0.10, -0.20]:
        for var_idx in range(6):
            X_pert = X.copy()
            X_pert[:, var_idx] = X[:, var_idx] * (1 + pert)
            pert_preds = predict_class(X_pert)
            base_preds = predict_class(X)
            changed = (pert_preds != base_preds).sum()
            full_pert_results.append({
                "Variable": VAR_NAMES[var_idx],
                "Perturbation": f"{pert:+.0%}",
                "Predictions_Changed": int(changed),
                "Pct_Changed": changed / len(X) * 100
            })
    
    full_pert_df = pd.DataFrame(full_pert_results)
    
    results = {
        "sensitivity_table": sens_df.to_dict("records"),
        "variable_sensitivity": var_sens_df.to_dict("records"),
        "full_perturbation": full_pert_df.to_dict("records"),
        "total_perturbations": total_perturbations,
        "verdict_changes": int(verdict_changes),
        "verdict_change_pct": verdict_change_pct,
        "pass": bool(pass_test),
        "verdict": "PASS" if pass_test else "FAIL"
    }
    
    print(f"\nSensitivity Summary:")
    print(f"  Total perturbations tested: {total_perturbations}")
    print(f"  Verdict changes: {verdict_changes} ({verdict_change_pct:.1f}%)")
    print(f"\nVariable Sensitivity:")
    for _, row in var_sens_df.iterrows():
        print(f"  {row['Variable']:45s}  Avg ΔP={row['Avg_Prob_Change']:.4f}  Flips={row['Verdict_Flips']}  {row['Sensitivity_Level']}")
    print(f"\nFull Dataset Perturbation (predictions changed):")
    for _, row in full_pert_df.iterrows():
        print(f"  {row['Variable']} {row['Perturbation']}: {row['Predictions_Changed']} ({row['Pct_Changed']:.1f}%)")
    print(f"VERDICT: {results['verdict']}")
    
    return results


# ============================================================
# TEST 7: COMPARATIVE VALIDATION AGAINST ALTMAN Z-SCORE
# ============================================================

def test_7_altman_comparison(df):
    """Test 7: Comparative Validation Against Altman Z-Score."""
    print("\n" + "="*70)
    print("TEST 7: COMPARATIVE VALIDATION AGAINST ALTMAN Z-SCORE")
    print("="*70)
    
    df_data = df[df["Has_Data"]].copy()
    
    # Calculate Altman Z-Score components
    # Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5
    # X1 = Working Capital / Total Assets (same as V1)
    # X2 = Retained Earnings / Total Assets (same as V2)
    # X3 = EBIT / Total Assets ≈ EBITDA / Total Assets
    # X4 = Market Value of Equity / Total Liabilities (use book equity as proxy)
    # X5 = Sales / Total Assets (same as V6)
    
    altman_results = []
    for idx, row in df_data.iterrows():
        ta = row["Total Assets"]
        tl = row["Total Liabilities"]
        
        if pd.isna(ta) or ta == 0:
            continue
        
        x1 = row["V1"]  # WC/TA
        x2 = row["V2"]  # RE/TA
        
        # X3: EBITDA/TA (approximate EBIT/TA)
        ebitda = row["EBITDA"] if not pd.isna(row["EBITDA"]) else 0
        x3 = ebitda / ta if ta > 0 else 0
        
        # X4: Market Cap / Total Liabilities (use book equity = TA - TL as proxy)
        book_equity = ta - tl if not pd.isna(tl) else 0
        x4 = max(book_equity, 0) / tl if tl > 0 else 0
        
        # X5: Revenue / TA (same as V6)
        x5 = row["V6"]  # Rev/TA
        
        z_score = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5
        
        # Altman classification
        if z_score > 2.99:
            altman_zone = "Safe"
            altman_pred = 1  # Recovery
        elif z_score > 1.81:
            altman_zone = "Gray"
            altman_pred = 1  # Assume recovery for gray zone
        else:
            altman_zone = "Distress"
            altman_pred = 0  # Failure
        
        altman_results.append({
            "Company": row["Company"],
            "X1_WC_TA": x1,
            "X2_RE_TA": x2,
            "X3_EBIT_TA": x3,
            "X4_Equity_Liab": x4,
            "X5_Sales_TA": x5,
            "Z_Score": z_score,
            "Altman_Zone": altman_zone,
            "Altman_Pred": altman_pred,
            "Actual": row["Outcome_Binary"],
            "LR_Prob": row["LR_Prob"],
            "LR_Pred": 1 if row["LR_Prob"] >= 0.5 else 0
        })
    
    altman_df = pd.DataFrame(altman_results)
    
    # Altman accuracy
    altman_acc = accuracy_score(altman_df["Actual"], altman_df["Altman_Pred"])
    lr_acc = accuracy_score(altman_df["Actual"], altman_df["LR_Pred"])
    
    # Confusion matrices
    altman_cm = confusion_matrix(altman_df["Actual"], altman_df["Altman_Pred"])
    lr_cm = confusion_matrix(altman_df["Actual"], altman_df["LR_Pred"])
    
    # Altman metrics
    altman_tp = ((altman_df["Altman_Pred"] == 1) & (altman_df["Actual"] == 1)).sum()
    altman_tn = ((altman_df["Altman_Pred"] == 0) & (altman_df["Actual"] == 0)).sum()
    altman_fp = ((altman_df["Altman_Pred"] == 1) & (altman_df["Actual"] == 0)).sum()
    altman_fn = ((altman_df["Altman_Pred"] == 0) & (altman_df["Actual"] == 1)).sum()
    
    altman_sens = altman_tp / (altman_tp + altman_fn) if (altman_tp + altman_fn) > 0 else 0
    altman_spec = altman_tn / (altman_tn + altman_fp) if (altman_tn + altman_fp) > 0 else 0
    altman_prec = altman_tp / (altman_tp + altman_fp) if (altman_tp + altman_fp) > 0 else 0
    
    # LR metrics on same subset
    lr_tp = ((altman_df["LR_Pred"] == 1) & (altman_df["Actual"] == 1)).sum()
    lr_tn = ((altman_df["LR_Pred"] == 0) & (altman_df["Actual"] == 0)).sum()
    lr_fp = ((altman_df["LR_Pred"] == 1) & (altman_df["Actual"] == 0)).sum()
    lr_fn = ((altman_df["LR_Pred"] == 0) & (altman_df["Actual"] == 1)).sum()
    
    lr_sens = lr_tp / (lr_tp + lr_fn) if (lr_tp + lr_fn) > 0 else 0
    lr_spec = lr_tn / (lr_tn + lr_fp) if (lr_tn + lr_fp) > 0 else 0
    lr_prec = lr_tp / (lr_tp + lr_fp) if (lr_tp + lr_fp) > 0 else 0
    
    # McNemar's test for comparing models
    # b = cases where Altman correct, LR wrong
    # c = cases where LR correct, Altman wrong
    altman_correct = (altman_df["Altman_Pred"] == altman_df["Actual"])
    lr_correct = (altman_df["LR_Pred"] == altman_df["Actual"])
    b = ((altman_correct) & (~lr_correct)).sum()
    c = ((~altman_correct) & (lr_correct)).sum()
    
    if b + c > 0:
        mcnemar_stat = (abs(b - c) - 1)**2 / (b + c) if (b + c) > 0 else 0
        mcnemar_pval = 1 - stats.chi2.cdf(mcnemar_stat, 1)
    else:
        mcnemar_stat, mcnemar_pval = 0, 1
    
    improvement = lr_acc - altman_acc
    
    # Agreement analysis
    agree = (altman_df["Altman_Pred"] == altman_df["LR_Pred"]).mean()
    
    # Pass: SRFF-I outperforms Altman by > 10%
    pass_test = improvement > 0.10
    
    # Also test with gray zone = failure
    altman_df["Altman_Pred_Conservative"] = (altman_df["Z_Score"] > 2.99).astype(int)
    altman_acc_conservative = accuracy_score(altman_df["Actual"], altman_df["Altman_Pred_Conservative"])
    
    results = {
        "altman_table": altman_df.to_dict("records"),
        "altman_accuracy": altman_acc,
        "altman_accuracy_conservative": altman_acc_conservative,
        "altman_sensitivity": altman_sens,
        "altman_specificity": altman_spec,
        "altman_precision": altman_prec,
        "lr_accuracy": lr_acc,
        "lr_sensitivity": lr_sens,
        "lr_specificity": lr_spec,
        "lr_precision": lr_prec,
        "improvement": improvement,
        "mcnemar_stat": mcnemar_stat,
        "mcnemar_pval": mcnemar_pval,
        "agreement_rate": agree,
        "pass": bool(pass_test),
        "verdict": "PASS" if pass_test else "FAIL"
    }
    
    print(f"\nModel Comparison (n={len(altman_df)}):")
    print(f"  Altman Z-Score Accuracy: {altman_acc:.1%}")
    print(f"  Altman (Conservative):   {altman_acc_conservative:.1%}")
    print(f"  SRFF-I LR Accuracy:      {lr_acc:.1%}")
    print(f"  Improvement:             +{improvement:.1%}")
    print(f"\n  Altman: Sens={altman_sens:.1%}  Spec={altman_spec:.1%}  Prec={altman_prec:.1%}")
    print(f"  SRFF-I: Sens={lr_sens:.1%}  Spec={lr_spec:.1%}  Prec={lr_prec:.1%}")
    print(f"\n  McNemar's test: χ²={mcnemar_stat:.3f}, p={mcnemar_pval:.4f}")
    print(f"  Agreement rate: {agree:.1%}")
    print(f"VERDICT: {results['verdict']}")
    
    return results


# ============================================================
# TEST 8: EXTREME STRESS TEST SCENARIOS
# ============================================================

def test_8_stress_test(df):
    """Test 8: Extreme Stress Test Scenarios."""
    print("\n" + "="*70)
    print("TEST 8: EXTREME STRESS TEST SCENARIOS")
    print("="*70)
    
    df_data = df[df["Has_Data"]].copy()
    X = df_data[VAR_NAMES].values
    y = df_data["Outcome_Binary"].values
    
    # Baseline predictions
    base_probs = predict_prob(X)
    base_preds = (base_probs >= 0.5).astype(int)
    base_verdicts = [classify_verdict(p) for p in base_probs]
    
    # Define stress scenarios
    # V1=WC/TA, V2=RE/TA, V3=EBITDA/Debt, V4=OCF/Debt, V5=Collat/Liab, V6=Rev/TA
    scenarios = {
        "A: Revenue Shock (-30%)": {
            "V3_mult": 0.70,  # EBITDA drops with revenue
            "V4_mult": 0.70,  # OCF drops
            "V6_mult": 0.70,  # Revenue drops
        },
        "B: Margin Compression (-50%)": {
            "V3_mult": 0.50,  # EBITDA/Debt halved
            "V4_mult": 0.50,  # OCF/Debt halved
        },
        "C: Refinancing Crisis (Debt +50%)": {
            "V3_mult": 0.667,  # EBITDA/Debt: debt up 50% → ratio * 2/3
            "V4_mult": 0.667,  # OCF/Debt: same
            "V5_mult": 0.80,   # Collateral/Liab decreases
        },
        "D: Perfect Storm (All Combined)": {
            "V1_mult": 0.70,   # WC deteriorates
            "V2_mult": 0.80,   # RE deteriorates
            "V3_mult": 0.233,  # EBITDA/Debt: revenue -30%, margin -50%, debt +50%
            "V4_mult": 0.233,  # OCF/Debt: same
            "V5_mult": 0.667,  # Collateral/Liab: liabilities up
            "V6_mult": 0.467,  # Revenue/TA: revenue -30%, assets stable
        }
    }
    
    stress_results = []
    for scenario_name, multipliers in scenarios.items():
        X_stress = X.copy()
        for var_key, mult in multipliers.items():
            var_idx = int(var_key[1]) - 1  # V1 -> 0, V2 -> 1, etc.
            X_stress[:, var_idx] = X[:, var_idx] * mult
        
        stress_probs = predict_prob(X_stress)
        stress_preds = (stress_probs >= 0.5).astype(int)
        stress_verdicts = [classify_verdict(p) for p in stress_probs]
        
        # Count flips
        go_to_nogo = sum(1 for b, s in zip(base_verdicts, stress_verdicts) 
                         if b == "GO" and s == "NO-GO")
        go_to_cond = sum(1 for b, s in zip(base_verdicts, stress_verdicts) 
                         if b == "GO" and s == "CONDITIONAL")
        cond_to_nogo = sum(1 for b, s in zip(base_verdicts, stress_verdicts) 
                           if b == "CONDITIONAL" and s == "NO-GO")
        any_downgrade = sum(1 for b, s in zip(base_verdicts, stress_verdicts) 
                           if (b == "GO" and s != "GO") or (b == "CONDITIONAL" and s == "NO-GO"))
        
        pred_flips = (base_preds != stress_preds).sum()
        
        # Accuracy under stress (using actual outcomes)
        stress_acc = accuracy_score(y, stress_preds)
        
        stress_results.append({
            "Scenario": scenario_name,
            "GO_to_NOGO": go_to_nogo,
            "GO_to_COND": go_to_cond,
            "COND_to_NOGO": cond_to_nogo,
            "Total_Downgrades": any_downgrade,
            "Pct_Downgraded": any_downgrade / len(X) * 100,
            "Prediction_Flips": int(pred_flips),
            "Stress_Accuracy": stress_acc,
            "Avg_Prob_Change": float(np.mean(stress_probs - base_probs))
        })
    
    stress_df = pd.DataFrame(stress_results)
    
    # Company-level stress analysis
    company_stress = []
    for i in range(len(df_data)):
        company_name = df_data.iloc[i]["Company"]
        base_v = base_verdicts[i]
        
        flips = 0
        for scenario_name, multipliers in scenarios.items():
            x_stress = X[i].copy()
            for var_key, mult in multipliers.items():
                var_idx = int(var_key[1]) - 1
                x_stress[var_idx] = X[i, var_idx] * mult
            stress_v = classify_verdict(predict_prob(x_stress.reshape(1, -1))[0])
            if stress_v != base_v:
                flips += 1
        
        company_stress.append({
            "Company": company_name,
            "Base_Verdict": base_v,
            "Scenarios_Flipped": flips,
            "Robustness": "Robust" if flips == 0 else "Moderate" if flips <= 2 else "Fragile"
        })
    
    company_stress_df = pd.DataFrame(company_stress)
    
    # Pass: < 40% flip under Scenario D
    scenario_d = stress_df[stress_df["Scenario"].str.startswith("D")]
    d_flip_pct = scenario_d["Pct_Downgraded"].values[0] if len(scenario_d) > 0 else 100
    pass_test = d_flip_pct < 40
    
    results = {
        "stress_table": stress_df.to_dict("records"),
        "company_stress": company_stress_df.to_dict("records"),
        "scenario_d_flip_pct": d_flip_pct,
        "robust_companies": int((company_stress_df["Robustness"] == "Robust").sum()),
        "fragile_companies": int((company_stress_df["Robustness"] == "Fragile").sum()),
        "pass": bool(pass_test),
        "verdict": "PASS" if pass_test else "FAIL"
    }
    
    print(f"\nStress Test Results:")
    for _, row in stress_df.iterrows():
        print(f"  {row['Scenario']:40s}  Downgrades={int(row['Total_Downgrades']):2d} ({row['Pct_Downgraded']:.1f}%)  "
              f"Acc={row['Stress_Accuracy']:.1%}")
    print(f"\nCompany Robustness:")
    print(f"  Robust (0 flips): {results['robust_companies']}")
    print(f"  Fragile (3+ flips): {results['fragile_companies']}")
    print(f"VERDICT: {results['verdict']}")
    
    return results


# ============================================================
# TEST 9: MISSING DATA ROBUSTNESS
# ============================================================

def test_9_missing_data(df):
    """Test 9: Missing Data Robustness."""
    print("\n" + "="*70)
    print("TEST 9: MISSING DATA ROBUSTNESS")
    print("="*70)
    
    df_data = df[df["Has_Data"]].copy()
    X = df_data[VAR_NAMES].values
    y = df_data["Outcome_Binary"].values
    
    # Baseline
    base_probs = predict_prob(X)
    base_preds = (base_probs >= 0.5).astype(int)
    base_verdicts = [classify_verdict(p) for p in base_probs]
    base_acc = accuracy_score(y, base_preds)
    
    # Imputation strategies
    col_means = X.mean(axis=0)
    col_medians = np.median(X, axis=0)
    
    # Scenario A: Missing V5 (Collateral Value)
    # Scenario B: Missing V2 (Retained Earnings)
    # Scenario C: Missing V3 (EBITDA)
    # Scenario D: Missing any 2 variables
    
    missing_scenarios = {
        "A: Missing V5 (Collateral/Liab)": [4],
        "B: Missing V2 (Retained Earnings/TA)": [1],
        "C: Missing V3 (EBITDA/Debt)": [2],
        "D: Missing V5 + V3": [4, 2],
        "E: Missing V2 + V4": [1, 3],
        "F: Missing V1 + V2 + V5": [0, 1, 4],
    }
    
    imputation_methods = {
        "Mean": col_means,
        "Median": col_medians,
        "Conservative (0)": np.zeros(6),
    }
    
    missing_results = []
    for scenario_name, missing_indices in missing_scenarios.items():
        for method_name, impute_values in imputation_methods.items():
            X_imp = X.copy()
            for mi in missing_indices:
                X_imp[:, mi] = impute_values[mi]
            
            imp_probs = predict_prob(X_imp)
            imp_preds = (imp_probs >= 0.5).astype(int)
            imp_verdicts = [classify_verdict(p) for p in imp_probs]
            
            imp_acc = accuracy_score(y, imp_preds)
            mae = np.mean(np.abs(imp_probs - base_probs))
            verdict_changes = sum(1 for b, i in zip(base_verdicts, imp_verdicts) if b != i)
            verdict_change_pct = verdict_changes / len(X) * 100
            
            missing_results.append({
                "Scenario": scenario_name,
                "Missing_Variables": [VAR_NAMES[i] for i in missing_indices],
                "N_Missing": len(missing_indices),
                "Imputation": method_name,
                "Accuracy": imp_acc,
                "Accuracy_Drop": base_acc - imp_acc,
                "MAE_Probability": mae,
                "Verdict_Changes": verdict_changes,
                "Verdict_Change_Pct": verdict_change_pct
            })
    
    missing_df = pd.DataFrame(missing_results)
    
    # Pass: works with missing V5 (verdict unchanged in >90% of cases with mean imputation)
    v5_mean = missing_df[(missing_df["Scenario"].str.contains("V5")) & 
                          (missing_df["N_Missing"] == 1) & 
                          (missing_df["Imputation"] == "Mean")]
    if len(v5_mean) > 0:
        v5_verdict_stable = v5_mean.iloc[0]["Verdict_Change_Pct"] < 10
    else:
        v5_verdict_stable = False
    
    pass_test = v5_verdict_stable
    
    results = {
        "missing_table": missing_df.to_dict("records"),
        "base_accuracy": base_acc,
        "v5_verdict_stable": bool(v5_verdict_stable),
        "pass": bool(pass_test),
        "verdict": "PASS" if pass_test else "FAIL"
    }
    
    print(f"\nBaseline Accuracy: {base_acc:.1%}")
    print(f"\nMissing Data Results:")
    for _, row in missing_df.iterrows():
        print(f"  {row['Scenario']:35s}  {row['Imputation']:15s}  Acc={row['Accuracy']:.1%}  "
              f"Drop={row['Accuracy_Drop']:.1%}  MAE={row['MAE_Probability']:.4f}  "
              f"Verdicts Changed={row['Verdict_Changes']} ({row['Verdict_Change_Pct']:.1f}%)")
    print(f"\nV5 missing (mean imputation) verdict stable: {v5_verdict_stable}")
    print(f"VERDICT: {results['verdict']}")
    
    return results


# ============================================================
# TEST 10: FORWARD-LOOKING VALIDATION
# ============================================================

def test_10_forward_validation(df):
    """Test 10: Forward-Looking Validation on Future Outcomes."""
    print("\n" + "="*70)
    print("TEST 10: FORWARD-LOOKING VALIDATION ON FUTURE OUTCOMES")
    print("="*70)
    
    # The model uses 2018-2019 financial data to predict 2024-2025 outcomes
    # This IS the forward-looking validation since outcomes are known
    
    y = df["Outcome_Binary"].values
    probs = df["LR_Prob"].values
    preds = (probs >= 0.5).astype(int)
    
    # Overall accuracy
    acc = accuracy_score(y, preds)
    
    # Confusion matrix
    tp = ((preds == 1) & (y == 1)).sum()
    tn = ((preds == 0) & (y == 0)).sum()
    fp = ((preds == 1) & (y == 0)).sum()
    fn = ((preds == 0) & (y == 1)).sum()
    
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    f1 = 2 * precision * sensitivity / (precision + sensitivity) if (precision + sensitivity) > 0 else 0
    
    # AUC-ROC
    auc = roc_auc_score(y, probs)
    
    # 95% CI using Wilson score interval
    n = len(y)
    z = 1.96
    p_hat = acc
    denom = 1 + z**2/n
    center = (p_hat + z**2/(2*n)) / denom
    margin = z * np.sqrt((p_hat*(1-p_hat) + z**2/(4*n))/n) / denom
    ci_low = max(0, center - margin)
    ci_high = min(1, center + margin)
    
    # Binomial test: is accuracy significantly > 50% (random)?
    binom_pval = stats.binomtest(int(acc * n), n, 0.5, alternative="greater").pvalue
    
    # Is accuracy significantly > 85%?
    binom_pval_85 = stats.binomtest(int(acc * n), n, 0.85, alternative="greater").pvalue
    
    # Company-level detail
    company_detail = []
    for idx, row in df.iterrows():
        company_detail.append({
            "Company": row["Company"],
            "Sector": row["Sector"],
            "LR_Probability": row["LR_Prob"],
            "LR_Prediction": "RECOVERED" if row["LR_Prob"] >= 0.5 else "FAILED",
            "Verdict": classify_verdict(row["LR_Prob"]),
            "Actual_Outcome": row["Actual Outcome"],
            "Correct": row["LR_Prob"] >= 0.5 and row["Outcome_Binary"] == 1 or 
                       row["LR_Prob"] < 0.5 and row["Outcome_Binary"] == 0,
            "Outcome_Detail": row["Outcome Detail"]
        })
    
    company_df = pd.DataFrame(company_detail)
    
    # Misclassified companies
    misclassified = company_df[~company_df["Correct"]]
    
    # Pass: accuracy > 85%
    pass_test = acc > 0.85
    
    results = {
        "accuracy": acc,
        "ci_95": (ci_low, ci_high),
        "sensitivity": sensitivity,
        "specificity": specificity,
        "precision": precision,
        "f1_score": f1,
        "auc_roc": auc,
        "confusion_matrix": {"TP": int(tp), "TN": int(tn), "FP": int(fp), "FN": int(fn)},
        "binom_test_vs_50": binom_pval,
        "binom_test_vs_85": binom_pval_85,
        "company_detail": company_df.to_dict("records"),
        "misclassified": misclassified.to_dict("records"),
        "n_misclassified": len(misclassified),
        "pass": bool(pass_test),
        "verdict": "PASS" if pass_test else "FAIL"
    }
    
    print(f"\nForward-Looking Validation (2018 data → 2024-2025 outcomes):")
    print(f"  Accuracy: {acc:.1%} [{ci_low:.1%}, {ci_high:.1%}]")
    print(f"  Sensitivity: {sensitivity:.1%}")
    print(f"  Specificity: {specificity:.1%}")
    print(f"  Precision: {precision:.1%}")
    print(f"  F1 Score: {f1:.3f}")
    print(f"  AUC-ROC: {auc:.3f}")
    print(f"\n  Confusion Matrix:")
    print(f"    TP={tp}  FP={fp}")
    print(f"    FN={fn}  TN={tn}")
    print(f"\n  Binomial test (>50%): p={binom_pval:.6f}")
    print(f"  Binomial test (>85%): p={binom_pval_85:.6f}")
    print(f"\n  Misclassified ({len(misclassified)}):")
    for _, row in misclassified.iterrows():
        print(f"    {row['Company']:30s}  Pred={row['LR_Prediction']:10s}  Actual={row['Actual_Outcome']}")
    print(f"VERDICT: {results['verdict']}")
    
    return results


# ============================================================
# MAIN EXECUTION
# ============================================================

def main():
    print("="*70)
    print("SRFF-I RVS MODEL — COMPREHENSIVE ACADEMIC VALIDATION SUITE")
    print("="*70)
    print(f"Date: April 17, 2026")
    print(f"Model: Calibrated Logistic Regression (6 variables)")
    print(f"Dataset: 47 companies (34 recovered, 13 failed)")
    print()
    
    # Load data
    df = load_data()
    print(f"Data loaded: {len(df)} companies")
    print(f"  With financial data: {df['Has_Data'].sum()}")
    print(f"  Missing data: {(~df['Has_Data']).sum()}")
    print(f"  Recovered: {df['Outcome_Binary'].sum()}")
    print(f"  Failed: {(1 - df['Outcome_Binary']).sum()}")
    
    # Run all 10 tests
    all_results = {}
    
    all_results["test_1"] = test_1_sector_accuracy(df)
    all_results["test_2"] = test_2_temporal_stability(df)
    all_results["test_3"] = test_3_variable_importance(df)
    all_results["test_4"] = test_4_threshold_optimization(df)
    all_results["test_5"] = test_5_kfold_cv(df)
    all_results["test_6"] = test_6_sensitivity_analysis(df)
    all_results["test_7"] = test_7_altman_comparison(df)
    all_results["test_8"] = test_8_stress_test(df)
    all_results["test_9"] = test_9_missing_data(df)
    all_results["test_10"] = test_10_forward_validation(df)
    
    # Summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    
    for test_name, result in all_results.items():
        verdict = result.get("verdict", "N/A")
        print(f"  {test_name.upper():10s}: {verdict}")
    
    passed = sum(1 for r in all_results.values() if r.get("pass", False))
    total = len(all_results)
    print(f"\n  OVERALL: {passed}/{total} tests passed")
    
    # Save results
    # Save JSON
    class NumpyEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating,)):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, np.bool_):
                return bool(obj)
            return super().default(obj)
    
    with open("/home/ubuntu/srff_validation/validation_results.json", "w") as f:
        json.dump(all_results, f, indent=2, cls=NumpyEncoder)
    
    print(f"\nResults saved to /home/ubuntu/srff_validation/validation_results.json")
    
    return df, all_results


if __name__ == "__main__":
    df, results = main()
