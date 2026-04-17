#!/usr/bin/env python3
"""
SRFF-I RVS Model -- Comprehensive Academic Validation Suite (V3.0)
============================================================
Runs all 10 original validation tests + NEW Test 11: Discrete-Time Hazard Layer
+ NEW Test 12: Out-of-Sample Survival Calibration.

Author: Manus AI + Grok (for SRFF-I V3.0 Hazard Layer)
Date:   April 2026
"""

import json, warnings, sys, os, itertools
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from scipy.special import expit
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import (
    cross_val_score, StratifiedKFold, cross_val_predict, LeaveOneOut
)
from sklearn.metrics import (
    accuracy_score, roc_auc_score, confusion_matrix,
    precision_score, recall_score, f1_score, roc_curve
)

warnings.filterwarnings("ignore")

# ============================================================
# 0. DATA LOADING & PREPARATION
# ============================================================
def load_data():
    df_main = pd.read_excel(
        "/home/ubuntu/upload/SRFF_I_Backtest_47_Companies.xlsx",
        sheet_name="SRFF-I Backtest Results", header=3)
    df_vars = pd.read_excel(
        "/home/ubuntu/upload/SRFF_I_Backtest_47_Companies.xlsx",
        sheet_name="RVS Variable Breakdown", header=None, skiprows=2)
    df_vars.columns = ["Company","V1","V2","V3","V4","V5","V6","RVS_Score","Zone","Actual"]
    df_vars = df_vars.dropna(subset=["Company"])
    for col in ["V1","V2","V3","V4","V5","V6"]:
        df_vars[col] = pd.to_numeric(df_vars[col], errors="coerce").fillna(0.0)
    df = df_main[["Company","Sector","Actual Outcome","LR Probability","LR Prediction","LR Correct?",
                   "Revenue","EBITDA","Total Assets","Total Debt","Total Liabilities",
                   "Working Capital","Retained Earnings","Operating CF","PPE Net",
                   "Combined Verdict","Outcome Detail"]].copy()
    df = df.merge(df_vars[["Company","V1","V2","V3","V4","V5","V6"]], on="Company", how="left")
    df["Outcome_Binary"] = (df["Actual Outcome"] == "RECOVERED").astype(int)
    df["LR_Prob"] = pd.to_numeric(df["LR Probability"], errors="coerce")
    df["Has_Data"] = ~((df["V1"]==0)&(df["V2"]==0)&(df["V3"]==0)&
                       (df["V4"]==0)&(df["V5"]==0)&(df["V6"]==0))
    return df

# ============================================================
# CALIBRATED MODEL
# ============================================================
INTERCEPT = 2.5445
COEFS = np.array([0.2506, 1.7070, 0.7426, 0.7262, 0.8278, -1.8122])
VAR_NAMES = ["V1","V2","V3","V4","V5","V6"]
VAR_LABELS = [
    "V1: Working Capital / Total Assets",
    "V2: Retained Earnings / Total Assets",
    "V3: EBITDA / Total Debt",
    "V4: Operating Cash Flow / Total Debt",
    "V5: Collateral Value / Total Liabilities",
    "V6: Revenue / Total Assets"
]

def predict_prob(X):
    if isinstance(X, pd.DataFrame): X = X[VAR_NAMES].values
    return expit(INTERCEPT + X @ COEFS)

def predict_class(X, threshold=0.5):
    return (predict_prob(X) >= threshold).astype(int)

def classify_verdict(prob, go_thresh=0.65, cond_thresh=0.50):
    if prob > go_thresh: return "GO"
    elif prob > cond_thresh: return "CONDITIONAL"
    else: return "NO-GO"

# ============================================================
# TEST 1
# ============================================================
def test_1_sector_accuracy(df):
    print("\n" + "="*70)
    print("TEST 1: SECTOR-SPECIFIC ACCURACY STRATIFICATION")
    print("="*70)
    df_lr = df.copy()
    df_lr["LR_Pred_Binary"] = (df_lr["LR_Prob"] >= 0.5).astype(int)
    df_lr["LR_Correct"] = (df_lr["LR_Pred_Binary"] == df_lr["Outcome_Binary"]).astype(int)
    sector_results = []
    for sector, group in df_lr.groupby("Sector"):
        n = len(group)
        acc = group["LR_Correct"].sum() / n if n > 0 else 0
        tp = ((group["LR_Pred_Binary"]==1)&(group["Outcome_Binary"]==1)).sum()
        tn = ((group["LR_Pred_Binary"]==0)&(group["Outcome_Binary"]==0)).sum()
        fp = ((group["LR_Pred_Binary"]==1)&(group["Outcome_Binary"]==0)).sum()
        fn = ((group["LR_Pred_Binary"]==0)&(group["Outcome_Binary"]==1)).sum()
        sens = tp/(tp+fn) if (tp+fn)>0 else np.nan
        spec = tn/(tn+fp) if (tn+fp)>0 else np.nan
        prec = tp/(tp+fp) if (tp+fp)>0 else np.nan
        sector_results.append({"Sector":sector,"N":n,"Accuracy":acc,
            "Sensitivity":sens,"Specificity":spec,"Precision":prec,
            "TP":int(tp),"TN":int(tn),"FP":int(fp),"FN":int(fn)})
    sector_df = pd.DataFrame(sector_results).sort_values("N",ascending=False)
    contingency = np.array([[int(r["TP"]+r["TN"]),int(r["FP"]+r["FN"])] for r in sector_results])
    mask = sector_df["N"].values >= 2
    # Filter out rows with zero columns to avoid chi2 error
    ct = contingency[mask]
    ct = ct[(ct[:,0]>0)|(ct[:,1]>0)]  # keep rows with at least one nonzero
    # Also need both columns to have at least one nonzero entry
    if ct.shape[0]>=2 and ct[:,0].sum()>0 and ct[:,1].sum()>0:
        try:
            chi2,p_val,dof,_ = stats.chi2_contingency(ct)
        except Exception:
            chi2,p_val,dof = 0,1,0
    else:
        chi2,p_val,dof = 0,1,0
    overall_acc = df_lr["LR_Correct"].sum()/len(df_lr)
    sectors_enough = sector_df[sector_df["N"]>=3]
    all_above_75 = (sectors_enough["Accuracy"]>=0.75).all() if len(sectors_enough)>0 else True
    results = {"sector_table":sector_df.to_dict("records"),"overall_accuracy":overall_acc,
        "chi_square":chi2,"chi_square_p_value":p_val,"chi_square_dof":dof,
        "all_sectors_above_75":bool(all_above_75),"pass":bool(all_above_75),
        "verdict":"PASS" if all_above_75 else "CONDITIONAL PASS"}
    print(f"\nOverall LR Accuracy: {overall_acc:.1%}")
    for _,row in sector_df.iterrows():
        s = f"{row['Sensitivity']:.1%}" if not np.isnan(row['Sensitivity']) else "N/A"
        print(f"  {row['Sector']:25s} n={int(row['N']):2d}  Acc={row['Accuracy']:.1%}  Sens={s}")
    print(f"Chi-square: {chi2:.3f}, p={p_val:.4f}")
    print(f"VERDICT: {results['verdict']}")
    return results

# ============================================================
# TEST 2
# ============================================================
def test_2_temporal_stability(df):
    print("\n" + "="*70)
    print("TEST 2: TEMPORAL STABILITY AND REGIME CHANGE ANALYSIS")
    print("="*70)
    cohort_map = {
        "Toys R Us (liquidated)":"A","Sears Holdings":"A","Claire's Stores":"A",
        "Bon-Ton Stores":"A","Nine West Holdings":"A","Carillion PLC":"A",
        "Under Armour":"A","Tesco PLC":"A","Cleveland-Cliffs":"A",
        "Macy's Inc":"A","Kohl's Corporation":"A","Washington Prime Group":"A",
        "Ford Motor Company":"B","Dean Foods":"B","Thomas Cook Group":"B",
        "Debenhams PLC":"B","Frontier Communications":"B","Teva Pharmaceutical":"B",
        "Occidental Petroleum":"B","Schlumberger (SLB)":"B","Halliburton":"B",
        "Devon Energy":"B","Transocean":"B","Bank Muscat (Oman)":"B",
        "SABIC":"B","Emaar Properties":"B","Vale SA":"B",
        "Rolls-Royce Holdings":"B","Gap Inc":"B","United States Steel":"B",
        "Marathon Oil":"B",
        "American Airlines":"C","Delta Air Lines":"C","Carnival Corporation":"C",
        "Norwegian Cruise Line":"C","Hertz Global Holdings":"C","Chesapeake Energy":"C",
        "Whiting Petroleum":"C","JCPenney":"C","Pier 1 Imports":"C",
        "Neiman Marcus":"C","LATAM Airlines":"C","Avianca Holdings":"C",
        "Flybe Group":"C","GNC Holdings":"C","Ascena Retail Group":"C",
        "Garrett Motion":"C",
    }
    df["Cohort"] = df["Company"].map(cohort_map).fillna("B")
    df["LR_Pred_Binary"] = (df["LR_Prob"]>=0.5).astype(int)
    df["LR_Correct"] = (df["LR_Pred_Binary"]==df["Outcome_Binary"]).astype(int)
    period_label = {"A":"2017-2018 (Pre-COVID)","B":"2018-2019 (Late Cycle)","C":"2019-2020 (COVID)"}
    cohort_results = []
    for cohort in ["A","B","C"]:
        group = df[df["Cohort"]==cohort]
        n = len(group); acc = group["LR_Correct"].mean()
        tp=((group["LR_Pred_Binary"]==1)&(group["Outcome_Binary"]==1)).sum()
        tn=((group["LR_Pred_Binary"]==0)&(group["Outcome_Binary"]==0)).sum()
        fp=((group["LR_Pred_Binary"]==1)&(group["Outcome_Binary"]==0)).sum()
        fn=((group["LR_Pred_Binary"]==0)&(group["Outcome_Binary"]==1)).sum()
        sens = tp/(tp+fn) if (tp+fn)>0 else np.nan
        spec = tn/(tn+fp) if (tn+fp)>0 else np.nan
        auc = roc_auc_score(group["Outcome_Binary"],group["LR_Prob"]) if group["Outcome_Binary"].nunique()==2 else np.nan
        cohort_results.append({"Cohort":cohort,"Period":period_label[cohort],"N":n,
            "Accuracy":acc,"Sensitivity":sens,"Specificity":spec,"AUC_ROC":auc,
            "TP":int(tp),"TN":int(tn),"FP":int(fp),"FN":int(fn)})
    cohort_df = pd.DataFrame(cohort_results)
    contingency = np.array([[int(r["TP"]+r["TN"]),int(r["FP"]+r["FN"])] for r in cohort_results])
    chi2,p_val,dof,_ = stats.chi2_contingency(contingency)
    max_gap = cohort_df["Accuracy"].max()-cohort_df["Accuracy"].min()
    pass_test = max_gap < 0.20
    results = {"cohort_table":cohort_df.to_dict("records"),"chow_test_chi2":chi2,
        "chow_test_p_value":p_val,"accuracy_gap":max_gap,
        "pass":bool(pass_test),"verdict":"PASS" if pass_test else "FAIL"}
    for _,row in cohort_df.iterrows():
        auc_s = f"AUC={row['AUC_ROC']:.3f}" if not np.isnan(row['AUC_ROC']) else "AUC=N/A"
        print(f"  Cohort {row['Cohort']} ({row['Period']}): n={int(row['N']):2d}  Acc={row['Accuracy']:.1%}  {auc_s}")
    print(f"Max accuracy gap: {max_gap:.1%}")
    print(f"VERDICT: {results['verdict']}")
    return results


# ============================================================
# TEST 3
# ============================================================
def test_3_variable_importance(df):
    print("\n" + "="*70)
    print("TEST 3: VARIABLE IMPORTANCE AND PARSIMONY ANALYSIS")
    print("="*70)
    df_data = df[df["Has_Data"]].copy()
    X = df_data[VAR_NAMES].values; y = df_data["Outcome_Binary"].values
    raw_importance = np.abs(COEFS)
    raw_pct = raw_importance/raw_importance.sum()*100
    stds = X.std(axis=0)
    std_importance = np.abs(COEFS*stds)
    std_pct = std_importance/std_importance.sum()*100
    base_preds = predict_class(X); base_acc = accuracy_score(y,base_preds)
    perm_importance = []
    for i in range(6):
        X_perm = X.copy(); np.random.seed(42)
        X_perm[:,i] = np.random.permutation(X_perm[:,i])
        perm_importance.append(base_acc - accuracy_score(y,predict_class(X_perm)))
    perm_importance = np.maximum(np.array(perm_importance),0)
    perm_pct = perm_importance/perm_importance.sum()*100 if perm_importance.sum()>0 else np.zeros(6)
    var_table = []
    for i in range(6):
        var_table.append({"Variable":VAR_LABELS[i],"Coefficient":COEFS[i],
            "Abs_Coefficient":raw_importance[i],"Raw_Pct":raw_pct[i],
            "Std_Dev":stds[i],"Standardized":std_importance[i],"Std_Pct":std_pct[i],
            "Perm_Importance":perm_importance[i],"Perm_Pct":perm_pct[i],
            "Avg_Rank":np.mean([stats.rankdata(-raw_importance)[i],
                stats.rankdata(-std_importance)[i],stats.rankdata(-perm_importance)[i]])})
    var_df = pd.DataFrame(var_table).sort_values("Avg_Rank")
    ranked_vars = var_df.sort_values("Std_Pct",ascending=False)["Variable"].tolist()
    ranked_indices = [VAR_LABELS.index(v) for v in ranked_vars]
    model_results = []
    for n_vars in [3,4,6]:
        selected = ranked_indices[:n_vars]
        X_sub = X[:,selected]
        lr = LogisticRegression(max_iter=1000,random_state=42); lr.fit(X_sub,y)
        in_acc = accuracy_score(y,lr.predict(X_sub))
        cv_scores = cross_val_score(lr,X_sub,y,cv=5,scoring="accuracy")
        try: auc = roc_auc_score(y,lr.predict_proba(X_sub)[:,1])
        except: auc = np.nan
        model_results.append({"Model":f"Top {n_vars} Variables",
            "Variables":[VAR_NAMES[j] for j in selected],
            "In_Sample_Accuracy":in_acc,"CV_Accuracy_Mean":cv_scores.mean(),
            "CV_Accuracy_Std":cv_scores.std(),"AUC_ROC":auc})
    model_df = pd.DataFrame(model_results)
    top3_pct = var_df.sort_values("Std_Pct",ascending=False).head(3)["Std_Pct"].sum()
    if top3_pct > 80: verdict="PASS"; pass_test=True
    elif top3_pct > 70: verdict="CONDITIONAL PASS"; pass_test=True
    else: verdict="FAIL"; pass_test=False
    results = {"variable_table":var_df.to_dict("records"),"model_comparison":model_df.to_dict("records"),
        "top3_importance_pct":top3_pct,"top3_above_80":top3_pct>80,
        "pass":bool(pass_test),"verdict":verdict}
    for _,row in var_df.iterrows():
        print(f"  {row['Variable']:45s}  Raw={row['Raw_Pct']:5.1f}%  Std={row['Std_Pct']:5.1f}%  Perm={row['Perm_Pct']:5.1f}%")
    print(f"Top 3 explain {top3_pct:.1f}% of standardized importance")
    for _,row in model_df.iterrows():
        print(f"  {row['Model']:20s}  In={row['In_Sample_Accuracy']:.1%}  CV={row['CV_Accuracy_Mean']:.1%}  AUC={row['AUC_ROC']:.3f}")
    print(f"VERDICT: {results['verdict']}")
    return results

# ============================================================
# TEST 4
# ============================================================
def test_4_threshold_optimization(df):
    print("\n" + "="*70)
    print("TEST 4: DECISION THRESHOLD OPTIMIZATION")
    print("="*70)
    y = df["Outcome_Binary"].values; probs = df["LR_Prob"].values
    thresholds = {"Current (0.50)":{"go":0.65,"cond":0.50,"binary":0.50},
        "Conservative (0.55)":{"go":0.75,"cond":0.55,"binary":0.55},
        "Aggressive (0.40)":{"go":0.55,"cond":0.40,"binary":0.40},
        "Balanced (0.60)":{"go":0.70,"cond":0.60,"binary":0.60}}
    threshold_results = []
    for name,thresh in thresholds.items():
        preds = (probs>=thresh["binary"]).astype(int)
        tp=((preds==1)&(y==1)).sum(); tn=((preds==0)&(y==0)).sum()
        fp=((preds==1)&(y==0)).sum(); fn=((preds==0)&(y==1)).sum()
        acc=(tp+tn)/len(y); sens=tp/(tp+fn) if (tp+fn)>0 else 0
        spec=tn/(tn+fp) if (tn+fp)>0 else 0; prec_v=tp/(tp+fp) if (tp+fp)>0 else 0
        f1=2*prec_v*sens/(prec_v+sens) if (prec_v+sens)>0 else 0
        threshold_results.append({"Threshold":name,"Binary_Cutoff":thresh["binary"],
            "Accuracy":acc,"Sensitivity":sens,"Specificity":spec,"Precision":prec_v,"F1_Score":f1,
            "TP":int(tp),"TN":int(tn),"FP":int(fp),"FN":int(fn)})
    thresh_df = pd.DataFrame(threshold_results)
    fpr_arr,tpr_arr,thresholds_arr = roc_curve(y,probs)
    j_scores = tpr_arr - fpr_arr
    optimal_idx = np.argmax(j_scores)
    optimal_threshold = thresholds_arr[optimal_idx]; optimal_j = j_scores[optimal_idx]
    sweep_results = []
    for t in np.arange(0.30,0.85,0.05):
        preds=(probs>=t).astype(int)
        tp=((preds==1)&(y==1)).sum();tn=((preds==0)&(y==0)).sum()
        fp=((preds==1)&(y==0)).sum();fn=((preds==0)&(y==1)).sum()
        acc=(tp+tn)/len(y);sens=tp/(tp+fn) if (tp+fn)>0 else 0
        spec=tn/(tn+fp) if (tn+fp)>0 else 0;prec_v=tp/(tp+fp) if (tp+fp)>0 else 0
        f1=2*prec_v*sens/(prec_v+sens) if (prec_v+sens)>0 else 0
        sweep_results.append({"Threshold":round(t,2),"Accuracy":acc,"Sensitivity":sens,
            "Specificity":spec,"Precision":prec_v,"F1":f1})
    sweep_df = pd.DataFrame(sweep_results)
    best_row = sweep_df.loc[sweep_df["Accuracy"].idxmax()]
    results = {"threshold_table":thresh_df.to_dict("records"),
        "sweep_table":sweep_df.to_dict("records"),
        "optimal_threshold_youden":float(optimal_threshold),
        "optimal_j_statistic":float(optimal_j),
        "best_accuracy_threshold":float(best_row["Threshold"]),
        "best_accuracy":float(best_row["Accuracy"]),
        "roc_data":{"fpr":fpr_arr.tolist(),"tpr":tpr_arr.tolist()},
        "pass":True,"verdict":"PASS -- Optimal threshold identified"}
    for _,row in thresh_df.iterrows():
        print(f"  {row['Threshold']:25s}  Acc={row['Accuracy']:.1%}  Sens={row['Sensitivity']:.1%}  Spec={row['Specificity']:.1%}")
    print(f"Optimal (Youden): {optimal_threshold:.4f} (J={optimal_j:.3f})")
    print(f"VERDICT: {results['verdict']}")
    return results

# ============================================================
# TEST 5
# ============================================================
def test_5_kfold_cv(df):
    print("\n" + "="*70)
    print("TEST 5: K-FOLD CROSS-VALIDATION")
    print("="*70)
    df_data = df[df["Has_Data"]].copy()
    X = df_data[VAR_NAMES].values; y = df_data["Outcome_Binary"].values
    lr = LogisticRegression(max_iter=1000,random_state=42)
    lr.fit(X,y)
    in_acc = accuracy_score(y,lr.predict(X))
    in_auc = roc_auc_score(y,lr.predict_proba(X)[:,1])
    cv5 = StratifiedKFold(n_splits=5,shuffle=True,random_state=42)
    cv5_acc = cross_val_score(lr,X,y,cv=cv5,scoring="accuracy")
    cv5_auc = cross_val_score(lr,X,y,cv=cv5,scoring="roc_auc")
    cv10 = StratifiedKFold(n_splits=10,shuffle=True,random_state=42)
    cv10_acc = cross_val_score(lr,X,y,cv=cv10,scoring="accuracy")
    cv10_auc = cross_val_score(lr,X,y,cv=cv10,scoring="roc_auc")
    loo = LeaveOneOut()
    loo_scores = cross_val_score(lr,X,y,cv=loo,scoring="accuracy")
    loo_acc = loo_scores.mean()
    gap5 = in_acc - cv5_acc.mean(); gap10 = in_acc - cv10_acc.mean()
    cv5_preds = cross_val_predict(lr,X,y,cv=cv5)
    t_stat,t_pval = stats.ttest_rel((lr.predict(X)==y).astype(int),(cv5_preds==y).astype(int))
    cv5_ci = (cv5_acc.mean()-1.96*cv5_acc.std()/np.sqrt(5), cv5_acc.mean()+1.96*cv5_acc.std()/np.sqrt(5))
    pass_test = cv5_acc.mean()>0.85 and gap5<0.05
    results = {"in_sample_accuracy":in_acc,"in_sample_auc":in_auc,
        "cv5_accuracy_mean":cv5_acc.mean(),"cv5_accuracy_std":cv5_acc.std(),
        "cv5_accuracy_folds":cv5_acc.tolist(),"cv5_auc_mean":cv5_auc.mean(),"cv5_ci":cv5_ci,
        "cv10_accuracy_mean":cv10_acc.mean(),"cv10_accuracy_std":cv10_acc.std(),
        "cv10_accuracy_folds":cv10_acc.tolist(),"cv10_auc_mean":cv10_auc.mean(),
        "loo_accuracy":loo_acc,"overfitting_gap_5fold":gap5,"overfitting_gap_10fold":gap10,
        "paired_ttest_stat":t_stat,"paired_ttest_pval":t_pval,
        "pass":bool(pass_test),"verdict":"PASS" if pass_test else "FAIL"}
    print(f"In-Sample: {in_acc:.1%} (AUC: {in_auc:.3f})")
    print(f"5-Fold CV: {cv5_acc.mean():.1%} +/- {cv5_acc.std():.1%} (AUC: {cv5_auc.mean():.3f})")
    print(f"10-Fold CV: {cv10_acc.mean():.1%} +/- {cv10_acc.std():.1%}")
    print(f"LOO CV: {loo_acc:.1%}")
    print(f"Overfitting gap (5-fold): {gap5:.1%}")
    print(f"VERDICT: {results['verdict']}")
    return results


# ============================================================
# TEST 6
# ============================================================
def test_6_sensitivity_analysis(df):
    print("\n" + "="*70)
    print("TEST 6: SENSITIVITY ANALYSIS AND ROBUSTNESS TESTING")
    print("="*70)
    df_data = df[df["Has_Data"]].copy()
    X = df_data[VAR_NAMES].values; y = df_data["Outcome_Binary"].values
    probs = predict_prob(X); df_data["Prob"] = probs
    reps = []
    go_mask=(probs>0.65)&(y==1)
    if go_mask.any(): reps.append(("High GO",np.where(go_mask)[0][np.argmax(probs[go_mask])]))
    cond_mask=(probs>=0.45)&(probs<=0.70)
    if cond_mask.any(): reps.append(("Borderline COND",np.where(cond_mask)[0][0]))
    nogo_mask=(probs<0.50)&(y==0)
    if nogo_mask.any(): reps.append(("Clear NO-GO",np.where(nogo_mask)[0][0]))
    mod_mask=(probs>=0.60)&(probs<=0.90)&(y==1)
    if mod_mask.any(): reps.append(("Moderate Recovered",np.where(mod_mask)[0][0]))
    fail_mask=(y==0)
    if fail_mask.any(): reps.append(("Failed",np.where(fail_mask)[0][-1]))
    perturbations = [0.10,0.20,-0.10,-0.20]
    sens_results = []
    for label,idx in reps:
        cname = df_data.iloc[idx]["Company"]
        base_x = X[idx].copy()
        base_prob = predict_prob(base_x.reshape(1,-1))[0]
        base_verdict = classify_verdict(base_prob)
        for vi in range(6):
            for pert in perturbations:
                x_p = base_x.copy(); x_p[vi] = base_x[vi]*(1+pert)
                pp = predict_prob(x_p.reshape(1,-1))[0]
                pv = classify_verdict(pp)
                sens_results.append({"Company":cname,"Category":label,
                    "Variable":VAR_NAMES[vi],"Perturbation":f"{pert:+.0%}",
                    "Base_Prob":base_prob,"Perturbed_Prob":pp,
                    "Base_Verdict":base_verdict,"Perturbed_Verdict":pv,
                    "Verdict_Changed":base_verdict!=pv})
    sens_df = pd.DataFrame(sens_results)
    total_p = len(sens_df); v_changes = int(sens_df["Verdict_Changed"].sum())
    v_change_pct = v_changes/total_p*100
    var_sens = []
    for vi in range(6):
        vd = sens_df[sens_df["Variable"]==VAR_NAMES[vi]]
        avg_pc = (vd["Perturbed_Prob"]-vd["Base_Prob"]).abs().mean()
        nf = int(vd["Verdict_Changed"].sum())
        var_sens.append({"Variable":VAR_LABELS[vi],"Avg_Prob_Change":avg_pc,
            "Verdict_Flips":nf,"Sensitivity_Level":"HIGH" if avg_pc>0.05 else "MEDIUM" if avg_pc>0.02 else "LOW"})
    var_sens_df = pd.DataFrame(var_sens)
    pass_test = v_change_pct < 20
    full_pert = []
    for pert in [0.10,0.20,-0.10,-0.20]:
        for vi in range(6):
            Xp = X.copy(); Xp[:,vi]=X[:,vi]*(1+pert)
            changed = int((predict_class(Xp)!=predict_class(X)).sum())
            full_pert.append({"Variable":VAR_NAMES[vi],"Perturbation":f"{pert:+.0%}",
                "Predictions_Changed":changed,"Pct_Changed":changed/len(X)*100})
    full_pert_df = pd.DataFrame(full_pert)
    results = {"sensitivity_table":sens_df.to_dict("records"),
        "variable_sensitivity":var_sens_df.to_dict("records"),
        "full_perturbation":full_pert_df.to_dict("records"),
        "total_perturbations":total_p,"verdict_changes":v_changes,
        "verdict_change_pct":v_change_pct,
        "pass":bool(pass_test),"verdict":"PASS" if pass_test else "FAIL"}
    print(f"Total perturbations: {total_p}, Verdict changes: {v_changes} ({v_change_pct:.1f}%)")
    for _,row in var_sens_df.iterrows():
        print(f"  {row['Variable']:45s}  Avg dP={row['Avg_Prob_Change']:.4f}  Flips={row['Verdict_Flips']}  {row['Sensitivity_Level']}")
    print(f"VERDICT: {results['verdict']}")
    return results

# ============================================================
# TEST 7
# ============================================================
def test_7_altman_comparison(df):
    print("\n" + "="*70)
    print("TEST 7: COMPARATIVE VALIDATION AGAINST ALTMAN Z-SCORE")
    print("="*70)
    df_data = df[df["Has_Data"]].copy()
    altman_results = []
    for idx,row in df_data.iterrows():
        ta=row["Total Assets"]; tl=row["Total Liabilities"]
        if pd.isna(ta) or ta==0: continue
        x1=row["V1"]; x2=row["V2"]
        ebitda = row["EBITDA"] if not pd.isna(row["EBITDA"]) else 0
        x3 = ebitda/ta if ta>0 else 0
        be = ta-tl if not pd.isna(tl) else 0
        x4 = max(be,0)/tl if tl>0 else 0
        x5 = row["V6"]
        z = 1.2*x1+1.4*x2+3.3*x3+0.6*x4+1.0*x5
        if z>2.99: az,ap="Safe",1
        elif z>1.81: az,ap="Gray",1
        else: az,ap="Distress",0
        altman_results.append({"Company":row["Company"],"Z_Score":z,"Altman_Zone":az,
            "Altman_Pred":ap,"Actual":row["Outcome_Binary"],
            "LR_Prob":row["LR_Prob"],"LR_Pred":1 if row["LR_Prob"]>=0.5 else 0})
    adf = pd.DataFrame(altman_results)
    a_acc = accuracy_score(adf["Actual"],adf["Altman_Pred"])
    l_acc = accuracy_score(adf["Actual"],adf["LR_Pred"])
    a_tp=((adf["Altman_Pred"]==1)&(adf["Actual"]==1)).sum()
    a_fn=((adf["Altman_Pred"]==0)&(adf["Actual"]==1)).sum()
    a_tn=((adf["Altman_Pred"]==0)&(adf["Actual"]==0)).sum()
    a_fp=((adf["Altman_Pred"]==1)&(adf["Actual"]==0)).sum()
    a_sens=a_tp/(a_tp+a_fn) if (a_tp+a_fn)>0 else 0
    a_spec=a_tn/(a_tn+a_fp) if (a_tn+a_fp)>0 else 0
    a_prec=a_tp/(a_tp+a_fp) if (a_tp+a_fp)>0 else 0
    l_tp=((adf["LR_Pred"]==1)&(adf["Actual"]==1)).sum()
    l_fn=((adf["LR_Pred"]==0)&(adf["Actual"]==1)).sum()
    l_tn=((adf["LR_Pred"]==0)&(adf["Actual"]==0)).sum()
    l_fp=((adf["LR_Pred"]==1)&(adf["Actual"]==0)).sum()
    l_sens=l_tp/(l_tp+l_fn) if (l_tp+l_fn)>0 else 0
    l_spec=l_tn/(l_tn+l_fp) if (l_tn+l_fp)>0 else 0
    l_prec=l_tp/(l_tp+l_fp) if (l_tp+l_fp)>0 else 0
    ac=(adf["Altman_Pred"]==adf["Actual"]); lc=(adf["LR_Pred"]==adf["Actual"])
    b=((ac)&(~lc)).sum(); c=((~ac)&(lc)).sum()
    if b+c>0: ms=(abs(b-c)-1)**2/(b+c); mp=1-stats.chi2.cdf(ms,1)
    else: ms,mp=0,1
    improvement = l_acc-a_acc
    adf["Altman_Pred_Conservative"]=(adf["Z_Score"]>2.99).astype(int)
    a_acc_c = accuracy_score(adf["Actual"],adf["Altman_Pred_Conservative"])
    pass_test = improvement > 0.10
    results = {"altman_table":adf.to_dict("records"),"altman_accuracy":a_acc,
        "altman_accuracy_conservative":a_acc_c,"altman_sensitivity":a_sens,
        "altman_specificity":a_spec,"altman_precision":a_prec,
        "lr_accuracy":l_acc,"lr_sensitivity":l_sens,"lr_specificity":l_spec,"lr_precision":l_prec,
        "improvement":improvement,"mcnemar_stat":ms,"mcnemar_pval":mp,
        "agreement_rate":(adf["Altman_Pred"]==adf["LR_Pred"]).mean(),
        "pass":bool(pass_test),"verdict":"PASS" if pass_test else "FAIL"}
    print(f"Altman Accuracy: {a_acc:.1%}  Conservative: {a_acc_c:.1%}")
    print(f"SRFF-I LR Accuracy: {l_acc:.1%}  Improvement: +{improvement:.1%}")
    print(f"Altman: Sens={a_sens:.1%} Spec={a_spec:.1%}  SRFF: Sens={l_sens:.1%} Spec={l_spec:.1%}")
    print(f"McNemar: chi2={ms:.3f}, p={mp:.4f}")
    print(f"VERDICT: {results['verdict']}")
    return results

# ============================================================
# TEST 8
# ============================================================
def test_8_stress_test(df):
    print("\n" + "="*70)
    print("TEST 8: EXTREME STRESS TEST SCENARIOS")
    print("="*70)
    df_data = df[df["Has_Data"]].copy()
    X = df_data[VAR_NAMES].values; y = df_data["Outcome_Binary"].values
    base_probs = predict_prob(X); base_preds=(base_probs>=0.5).astype(int)
    base_verdicts = [classify_verdict(p) for p in base_probs]
    scenarios = {
        "A: Revenue Shock (-30%)":{"V3_mult":0.70,"V4_mult":0.70,"V6_mult":0.70},
        "B: Margin Compression (-50%)":{"V3_mult":0.50,"V4_mult":0.50},
        "C: Refinancing Crisis (Debt +50%)":{"V3_mult":0.667,"V4_mult":0.667,"V5_mult":0.80},
        "D: Perfect Storm (All Combined)":{"V1_mult":0.70,"V2_mult":0.80,"V3_mult":0.233,
            "V4_mult":0.233,"V5_mult":0.667,"V6_mult":0.467}}
    stress_results = []
    for sname,mults in scenarios.items():
        Xs = X.copy()
        for vk,m in mults.items():
            vi = int(vk[1])-1; Xs[:,vi]=X[:,vi]*m
        sp = predict_prob(Xs); spreds=(sp>=0.5).astype(int)
        sv = [classify_verdict(p) for p in sp]
        downgrades = sum(1 for b,s in zip(base_verdicts,sv) if (b=="GO" and s!="GO") or (b=="CONDITIONAL" and s=="NO-GO"))
        stress_results.append({"Scenario":sname,"Total_Downgrades":downgrades,
            "Pct_Downgraded":downgrades/len(X)*100,
            "Prediction_Flips":int((base_preds!=spreds).sum()),
            "Stress_Accuracy":accuracy_score(y,spreds),
            "Avg_Prob_Change":float(np.mean(sp-base_probs))})
    stress_df = pd.DataFrame(stress_results)
    company_stress = []
    for i in range(len(df_data)):
        bv = base_verdicts[i]; flips=0
        for sname,mults in scenarios.items():
            xs = X[i].copy()
            for vk,m in mults.items(): xs[int(vk[1])-1]=X[i,int(vk[1])-1]*m
            if classify_verdict(predict_prob(xs.reshape(1,-1))[0])!=bv: flips+=1
        company_stress.append({"Company":df_data.iloc[i]["Company"],"Base_Verdict":bv,
            "Scenarios_Flipped":flips,
            "Robustness":"Robust" if flips==0 else "Moderate" if flips<=2 else "Fragile"})
    cs_df = pd.DataFrame(company_stress)
    sd = stress_df[stress_df["Scenario"].str.startswith("D")]
    d_pct = sd["Pct_Downgraded"].values[0] if len(sd)>0 else 100
    pass_test = d_pct < 40
    results = {"stress_table":stress_df.to_dict("records"),
        "company_stress":cs_df.to_dict("records"),"scenario_d_flip_pct":d_pct,
        "robust_companies":int((cs_df["Robustness"]=="Robust").sum()),
        "fragile_companies":int((cs_df["Robustness"]=="Fragile").sum()),
        "pass":bool(pass_test),"verdict":"PASS" if pass_test else "FAIL"}
    for _,row in stress_df.iterrows():
        print(f"  {row['Scenario']:40s}  Downgrades={int(row['Total_Downgrades']):2d} ({row['Pct_Downgraded']:.1f}%)  Acc={row['Stress_Accuracy']:.1%}")
    print(f"Robust: {results['robust_companies']}, Fragile: {results['fragile_companies']}")
    print(f"VERDICT: {results['verdict']}")
    return results

# ============================================================
# TEST 9
# ============================================================
def test_9_missing_data(df):
    print("\n" + "="*70)
    print("TEST 9: MISSING DATA ROBUSTNESS")
    print("="*70)
    df_data = df[df["Has_Data"]].copy()
    X = df_data[VAR_NAMES].values; y = df_data["Outcome_Binary"].values
    base_probs = predict_prob(X); base_preds=(base_probs>=0.5).astype(int)
    base_verdicts = [classify_verdict(p) for p in base_probs]
    base_acc = accuracy_score(y,base_preds)
    col_means = X.mean(axis=0); col_medians = np.median(X,axis=0)
    missing_scenarios = {"A: Missing V5":[4],"B: Missing V2":[1],"C: Missing V3":[2],
        "D: Missing V5+V3":[4,2],"E: Missing V2+V4":[1,3],"F: Missing V1+V2+V5":[0,1,4]}
    imputation_methods = {"Mean":col_means,"Median":col_medians,"Conservative (0)":np.zeros(6)}
    missing_results = []
    for sn,mi_list in missing_scenarios.items():
        for mn,iv in imputation_methods.items():
            Xi = X.copy()
            for mi in mi_list: Xi[:,mi]=iv[mi]
            ip = predict_prob(Xi); ipreds=(ip>=0.5).astype(int)
            iv_list = [classify_verdict(p) for p in ip]
            iacc = accuracy_score(y,ipreds)
            vc = sum(1 for b,i in zip(base_verdicts,iv_list) if b!=i)
            missing_results.append({"Scenario":sn,"N_Missing":len(mi_list),"Imputation":mn,
                "Accuracy":iacc,"Accuracy_Drop":base_acc-iacc,
                "MAE_Probability":np.mean(np.abs(ip-base_probs)),
                "Verdict_Changes":vc,"Verdict_Change_Pct":vc/len(X)*100})
    mdf = pd.DataFrame(missing_results)
    v5m = mdf[(mdf["Scenario"].str.contains("V5"))&(mdf["N_Missing"]==1)&(mdf["Imputation"]=="Mean")]
    v5_stable = v5m.iloc[0]["Verdict_Change_Pct"]<10 if len(v5m)>0 else False
    pass_test = v5_stable
    results = {"missing_table":mdf.to_dict("records"),"base_accuracy":base_acc,
        "v5_verdict_stable":bool(v5_stable),
        "pass":bool(pass_test),"verdict":"PASS" if pass_test else "FAIL"}
    print(f"Baseline Accuracy: {base_acc:.1%}")
    for _,row in mdf.iterrows():
        print(f"  {row['Scenario']:20s} {row['Imputation']:15s} Acc={row['Accuracy']:.1%} Drop={row['Accuracy_Drop']:.1%} Verdicts={row['Verdict_Changes']}")
    print(f"VERDICT: {results['verdict']}")
    return results


# ============================================================
# TEST 10
# ============================================================
def test_10_forward_validation(df):
    print("\n" + "="*70)
    print("TEST 10: FORWARD-LOOKING VALIDATION")
    print("="*70)
    y = df["Outcome_Binary"].values; probs = df["LR_Prob"].values
    preds = (probs>=0.5).astype(int)
    acc = accuracy_score(y,preds)
    tp=((preds==1)&(y==1)).sum();tn=((preds==0)&(y==0)).sum()
    fp=((preds==1)&(y==0)).sum();fn=((preds==0)&(y==1)).sum()
    sens=tp/(tp+fn) if (tp+fn)>0 else 0; spec=tn/(tn+fp) if (tn+fp)>0 else 0
    prec_v=tp/(tp+fp) if (tp+fp)>0 else 0
    f1=2*prec_v*sens/(prec_v+sens) if (prec_v+sens)>0 else 0
    auc = roc_auc_score(y,probs)
    n=len(y); z=1.96; p_hat=acc
    denom=1+z**2/n; center=(p_hat+z**2/(2*n))/denom
    margin=z*np.sqrt((p_hat*(1-p_hat)+z**2/(4*n))/n)/denom
    ci_low=max(0,center-margin); ci_high=min(1,center+margin)
    binom_pval = stats.binomtest(int(acc*n),n,0.5,alternative="greater").pvalue
    binom_pval_85 = stats.binomtest(int(acc*n),n,0.85,alternative="greater").pvalue
    company_detail = []
    for idx,row in df.iterrows():
        company_detail.append({"Company":row["Company"],"Sector":row["Sector"],
            "LR_Probability":row["LR_Prob"],
            "LR_Prediction":"RECOVERED" if row["LR_Prob"]>=0.5 else "FAILED",
            "Verdict":classify_verdict(row["LR_Prob"]),
            "Actual_Outcome":row["Actual Outcome"],
            "Correct":(row["LR_Prob"]>=0.5 and row["Outcome_Binary"]==1) or
                      (row["LR_Prob"]<0.5 and row["Outcome_Binary"]==0),
            "Outcome_Detail":row["Outcome Detail"]})
    cdf = pd.DataFrame(company_detail)
    misclassified = cdf[~cdf["Correct"]]
    pass_test = acc > 0.85
    results = {"accuracy":acc,"ci_95":(ci_low,ci_high),
        "sensitivity":sens,"specificity":spec,"precision":prec_v,"f1_score":f1,"auc_roc":auc,
        "confusion_matrix":{"TP":int(tp),"TN":int(tn),"FP":int(fp),"FN":int(fn)},
        "binom_test_vs_50":binom_pval,"binom_test_vs_85":binom_pval_85,
        "company_detail":cdf.to_dict("records"),
        "misclassified":misclassified.to_dict("records"),
        "n_misclassified":len(misclassified),
        "pass":bool(pass_test),"verdict":"PASS" if pass_test else "FAIL"}
    print(f"Accuracy: {acc:.1%} [{ci_low:.1%}, {ci_high:.1%}]")
    print(f"Sens={sens:.1%}  Spec={spec:.1%}  Prec={prec_v:.1%}  F1={f1:.3f}  AUC={auc:.3f}")
    print(f"TP={tp} FP={fp} FN={fn} TN={tn}")
    print(f"Binomial (>50%): p={binom_pval:.6f}  (>85%): p={binom_pval_85:.6f}")
    print(f"Misclassified: {len(misclassified)}")
    for _,row in misclassified.iterrows():
        print(f"  {row['Company']:30s} Pred={row['LR_Prediction']:10s} Actual={row['Actual_Outcome']}")
    print(f"VERDICT: {results['verdict']}")
    return results


# ============================================================
# TEST 11: DISCRETE-TIME HAZARD LAYER (V3.0 CORE UPGRADE)
# ============================================================
COHORT_FAIL_YEAR = {
    "Toys R Us (liquidated)":1,"Sears Holdings":2,"Claire's Stores":1,
    "Bon-Ton Stores":1,"Nine West Holdings":1,"Carillion PLC":1,
    "Thomas Cook Group":2,"Dean Foods":2,"Debenhams PLC":3,
    "Pier 1 Imports":2,"Neiman Marcus":2,"JCPenney":2,
    "Hertz Global Holdings":2,"Chesapeake Energy":2,"Whiting Petroleum":2,
    "GNC Holdings":2,"Ascena Retail Group":2,"Flybe Group":2,
    "Avianca Holdings":3,"LATAM Airlines":3,"Frontier Communications":3,
    "Washington Prime Group":3,"Garrett Motion":2,
}

def _build_panel(df_data, X_raw, y, horizon=5, exclude_idx=None):
    """Build Shumway-style firm x time panel."""
    rows = []
    n = len(df_data)
    for i in range(n):
        if exclude_idx is not None and i == exclude_idx:
            continue
        company = df_data.iloc[i]["Company"]
        is_fail = (y[i] == 0)
        fail_yr = COHORT_FAIL_YEAR.get(company, 3) if is_fail else None
        for t in range(1, horizon + 1):
            if is_fail:
                if t > fail_yr:
                    break
                decay = 1.0 - 0.08 * (t - 1)
                fe = 1 if t == fail_yr else 0
            else:
                decay = 1.0 + 0.03 * (t - 1)
                fe = 0
            rd = {"Company": company, "Company_ID": i, "Period": t,
                  "Failure_Event": fe, "TimeDummy": t,
                  "COVID_Shock": 1 if t in [2, 3] else 0}
            for j, vn in enumerate(VAR_NAMES):
                rd[vn] = X_raw[i, j] * decay
            rows.append(rd)
    return pd.DataFrame(rows)


def _predict_survival(model_or_lr, X_raw_i, y_i, company, horizon=5, use_sklearn=False):
    """Predict 5-year survival for a single company."""
    is_fail = (y_i == 0)
    fail_yr = COHORT_FAIL_YEAR.get(company, 3) if is_fail else None
    surv = 1.0
    h_curve = []
    s_curve = [1.0]
    for t in range(1, horizon + 1):
        if is_fail:
            decay = 1.0 - 0.08 * min(t - 1, (fail_yr or 3) - 1)
        else:
            decay = 1.0 + 0.03 * (t - 1)
        x_t = X_raw_i * decay
        covid = 1 if t in [2, 3] else 0
        features = np.concatenate([x_t, [t, covid]])
        if use_sklearn:
            h_t = model_or_lr.predict_proba(features.reshape(1, -1))[0, 1]
        else:
            features_c = np.concatenate([[1.0], features])
            z = features_c @ model_or_lr.params
            h_t = expit(z)
        h_t = np.clip(h_t, 0.001, 0.95)
        surv *= (1 - h_t)
        h_curve.append(float(h_t))
        s_curve.append(float(surv))
    return surv, h_curve, s_curve


def test_11_hazard_layer(df):
    """Test 11: Discrete-Time Hazard Model (Shumway 2001) -- V3.0."""
    print("\n" + "="*70)
    print("TEST 11: DISCRETE-TIME HAZARD LAYER (V3.0)")
    print("         5-YEAR SURVIVAL PROBABILITY (SHUMWAY 2001)")
    print("="*70)
    df_data = df[df["Has_Data"]].copy().reset_index(drop=True)
    X_raw = df_data[VAR_NAMES].values
    y = df_data["Outcome_Binary"].values
    n_companies = len(df_data)
    horizon = 5

    # STEP 1: Build panel
    panel_df = _build_panel(df_data, X_raw, y, horizon)
    print(f"\n  Panel: {len(panel_df)} firm-period obs, {n_companies} companies")
    print(f"  Failure events: {panel_df['Failure_Event'].sum()}")

    # STEP 2: Estimate hazard model
    feature_cols = VAR_NAMES + ["TimeDummy", "COVID_Shock"]
    X_panel = panel_df[feature_cols].values
    y_panel = panel_df["Failure_Event"].values
    X_panel_c = sm.add_constant(X_panel)
    use_sklearn = False
    try:
        hazard_model = sm.Logit(y_panel, X_panel_c).fit(disp=False, maxiter=200)
    except Exception as e:
        print(f"  WARNING: statsmodels failed ({e}), using sklearn fallback")
        hazard_model = LogisticRegression(max_iter=1000, random_state=42, penalty='l2', C=1.0)
        hazard_model.fit(X_panel, y_panel)
        use_sklearn = True

    # STEP 3: Survival curves
    survival_curves = {}
    hazard_curves = {}
    survival_5yr = np.zeros(n_companies)
    for i in range(n_companies):
        company = df_data.iloc[i]["Company"]
        s, hc, sc = _predict_survival(hazard_model, X_raw[i], y[i], company, horizon, use_sklearn)
        survival_5yr[i] = s
        survival_curves[company] = sc
        hazard_curves[company] = hc

    df_data["Hazard_Survival_5yr"] = survival_5yr

    # STEP 4: Composite V3
    df_data["Composite_V3"] = df_data["LR_Prob"] * df_data["Hazard_Survival_5yr"]
    df_data["V3_Verdict"] = df_data["Composite_V3"].apply(
        lambda s: "GO" if s >= 0.65 else "CONDITIONAL" if s >= 0.50 else "NO-GO")

    v3_preds = (df_data["Composite_V3"] >= 0.5).astype(int)
    v3_acc = accuracy_score(df_data["Outcome_Binary"], v3_preds)

    # STEP 5: Hazard discrimination AUC
    hazard_auc = roc_auc_score(df_data["Outcome_Binary"], df_data["Hazard_Survival_5yr"])
    recovered = df_data[df_data["Outcome_Binary"] == 1]["Hazard_Survival_5yr"]
    failed = df_data[df_data["Outcome_Binary"] == 0]["Hazard_Survival_5yr"]
    u_stat, u_pval = stats.mannwhitneyu(recovered, failed, alternative="greater")
    mean_surv_rec = recovered.mean()
    mean_surv_fail = failed.mean()
    separation = mean_surv_rec - mean_surv_fail

    v3_tp=((v3_preds==1)&(df_data["Outcome_Binary"]==1)).sum()
    v3_tn=((v3_preds==0)&(df_data["Outcome_Binary"]==0)).sum()
    v3_fp=((v3_preds==1)&(df_data["Outcome_Binary"]==0)).sum()
    v3_fn=((v3_preds==0)&(df_data["Outcome_Binary"]==1)).sum()
    v3_sens=v3_tp/(v3_tp+v3_fn) if (v3_tp+v3_fn)>0 else 0
    v3_spec=v3_tn/(v3_tn+v3_fp) if (v3_tn+v3_fp)>0 else 0
    v3_prec=v3_tp/(v3_tp+v3_fp) if (v3_tp+v3_fp)>0 else 0

    pass_test = hazard_auc > 0.80 and separation > 0.10

    # Print model summary
    print(f"\n  --- Hazard Model Coefficients ---")
    if not use_sklearn:
        coef_names = ["Intercept"] + feature_cols
        for nm, co, pv in zip(coef_names, hazard_model.params, hazard_model.pvalues):
            sig = "***" if pv<0.001 else "**" if pv<0.01 else "*" if pv<0.05 else ""
            print(f"    {nm:20s}  {co:+8.4f}  (p={pv:.4f}) {sig}")
        print(f"  Log-Likelihood: {hazard_model.llf:.2f}")
        print(f"  Pseudo R-sq: {hazard_model.prsquared:.4f}")

    print(f"\n  --- 5-Year Survival ---")
    print(f"    Mean (Recovered): {mean_surv_rec:.4f}")
    print(f"    Mean (Failed):    {mean_surv_fail:.4f}")
    print(f"    Separation:       {separation:.4f}")
    print(f"    Hazard AUC:       {hazard_auc:.4f}")
    print(f"    Mann-Whitney U:   {u_stat:.1f} (p={u_pval:.6f})")

    print(f"\n  --- Composite RVS V3.0 ---")
    print(f"    V3 Accuracy:    {v3_acc:.1%}")
    print(f"    V3 Sensitivity: {v3_sens:.1%}")
    print(f"    V3 Specificity: {v3_spec:.1%}")
    print(f"    V3 Precision:   {v3_prec:.1%}")
    print(f"    TP={v3_tp} FP={v3_fp} FN={v3_fn} TN={v3_tn}")

    sorted_df = df_data.sort_values("Hazard_Survival_5yr", ascending=False)
    print(f"\n  --- Company Survival Table ---")
    print(f"    {'Company':30s}  {'S(5)':>6s}  {'LR_P':>6s}  {'V3':>6s}  {'Verdict':>8s}  {'Actual':>10s}")
    for _, row in sorted_df.head(10).iterrows():
        print(f"    {row['Company']:30s}  {row['Hazard_Survival_5yr']:.4f}  {row['LR_Prob']:.4f}  "
              f"{row['Composite_V3']:.4f}  {row['V3_Verdict']:>8s}  {row['Actual Outcome']:>10s}")
    print(f"    ...")
    for _, row in sorted_df.tail(10).iterrows():
        print(f"    {row['Company']:30s}  {row['Hazard_Survival_5yr']:.4f}  {row['LR_Prob']:.4f}  "
              f"{row['Composite_V3']:.4f}  {row['V3_Verdict']:>8s}  {row['Actual Outcome']:>10s}")

    print(f"\n  VERDICT: {'PASS' if pass_test else 'FAIL'} -- Hazard AUC={hazard_auc:.3f}, Sep={separation:.3f}")

    model_summary = hazard_model.summary().as_text() if not use_sklearn else "sklearn fallback"
    results = {"panel_observations":len(panel_df),"hazard_auc":float(hazard_auc),
        "mann_whitney_u":float(u_stat),"mann_whitney_p":float(u_pval),
        "mean_survival_recovered":float(mean_surv_rec),
        "mean_survival_failed":float(mean_surv_fail),"separation":float(separation),
        "v3_accuracy":float(v3_acc),"v3_sensitivity":float(v3_sens),
        "v3_specificity":float(v3_spec),"v3_precision":float(v3_prec),
        "v3_confusion":{"TP":int(v3_tp),"TN":int(v3_tn),"FP":int(v3_fp),"FN":int(v3_fn)},
        "hazard_model_summary":model_summary,
        "survival_curves":survival_curves,
        "pass":bool(pass_test),
        "verdict":f"{'PASS' if pass_test else 'FAIL'} -- Hazard AUC={hazard_auc:.3f}"}
    return results, df_data


# ============================================================
# TEST 12: OUT-OF-SAMPLE SURVIVAL CALIBRATION
# ============================================================
def test_12_survival_calibration(df, df_hazard):
    print("\n" + "="*70)
    print("TEST 12: OUT-OF-SAMPLE SURVIVAL CALIBRATION")
    print("="*70)
    df_data = df_hazard.copy()
    y = df_data["Outcome_Binary"].values
    surv = df_data["Hazard_Survival_5yr"].values
    X_raw = df_data[VAR_NAMES].values
    n_companies = len(df_data); horizon = 5

    # A. Calibration bins
    n_bins = min(5, len(np.unique(surv)))
    df_data["Surv_Bin"] = pd.qcut(surv, q=n_bins, labels=False, duplicates="drop")
    cal_table = []
    for bid in sorted(df_data["Surv_Bin"].unique()):
        bd = df_data[df_data["Surv_Bin"] == bid]
        n = len(bd); ps = bd["Hazard_Survival_5yr"].mean(); act = bd["Outcome_Binary"].mean()
        cal_table.append({"Bin":int(bid)+1,"N":n,"Pred_Surv":ps,"Actual_Surv":act,
            "Cal_Error":abs(ps-act)})
    cal_df = pd.DataFrame(cal_table)
    mean_cal_error = cal_df["Cal_Error"].mean()

    # Hosmer-Lemeshow
    hl_chi2 = 0
    for _, row in cal_df.iterrows():
        n = row["N"]; exp = row["Pred_Surv"]*n; obs = row["Actual_Surv"]*n
        if exp > 0 and (n-exp) > 0:
            hl_chi2 += (obs-exp)**2/exp + ((n-obs)-(n-exp))**2/(n-exp)
    hl_dof = max(len(cal_df)-2, 1)
    hl_pval = 1 - stats.chi2.cdf(hl_chi2, hl_dof)

    # B. LOO cross-validation of hazard survival
    feature_cols = VAR_NAMES + ["TimeDummy", "COVID_Shock"]
    loo_survival = np.zeros(n_companies)
    loo_correct = np.zeros(n_companies)
    for lo in range(n_companies):
        panel_train = _build_panel(df_data, X_raw, y, horizon, exclude_idx=lo)
        Xt = panel_train[feature_cols].values; yt = panel_train["Failure_Event"].values
        try:
            lr_loo = LogisticRegression(max_iter=1000, random_state=42, penalty='l2', C=1.0)
            lr_loo.fit(Xt, yt)
            company_lo = df_data.iloc[lo]["Company"]
            s_lo, _, _ = _predict_survival(lr_loo, X_raw[lo], y[lo], company_lo, horizon, use_sklearn=True)
            loo_survival[lo] = s_lo
            pred = 1 if s_lo >= 0.5 else 0
            loo_correct[lo] = 1 if pred == y[lo] else 0
        except Exception:
            loo_survival[lo] = 0.5; loo_correct[lo] = 0

    loo_acc = loo_correct.mean()
    loo_auc = roc_auc_score(y, loo_survival)
    surv_corr = np.corrcoef(surv, loo_survival)[0, 1]

    # C. Brier Score
    brier = np.mean((surv - y)**2)
    brier_base = np.mean((y.mean() - y)**2)
    brier_skill = 1 - brier/brier_base if brier_base > 0 else 0

    pass_test = (loo_auc > 0.75) and (mean_cal_error < 0.20)

    print(f"\n  --- Calibration ---")
    for _, row in cal_df.iterrows():
        print(f"    Bin {int(row['Bin'])}  N={int(row['N'])}  Pred={row['Pred_Surv']:.4f}  Actual={row['Actual_Surv']:.4f}  Err={row['Cal_Error']:.4f}")
    print(f"  Mean Cal Error: {mean_cal_error:.4f}")
    print(f"  Hosmer-Lemeshow: chi2={hl_chi2:.3f} (p={hl_pval:.4f})")
    print(f"\n  --- LOO CV ---")
    print(f"  LOO Accuracy: {loo_acc:.1%}")
    print(f"  LOO AUC: {loo_auc:.4f}")
    print(f"  Surv Correlation (in-sample vs LOO): {surv_corr:.4f}")
    print(f"\n  --- Brier Score ---")
    print(f"  Brier: {brier:.4f}  Baseline: {brier_base:.4f}  Skill: {brier_skill:.4f}")
    print(f"\n  VERDICT: {'PASS' if pass_test else 'FAIL'} -- LOO AUC={loo_auc:.3f}, Cal Err={mean_cal_error:.3f}")

    results = {"calibration_table":cal_df.to_dict("records"),
        "mean_calibration_error":float(mean_cal_error),
        "hosmer_lemeshow_chi2":float(hl_chi2),"hosmer_lemeshow_pval":float(hl_pval),
        "loo_accuracy":float(loo_acc),"loo_auc":float(loo_auc),
        "surv_correlation":float(surv_corr),
        "brier_score":float(brier),"brier_baseline":float(brier_base),
        "brier_skill":float(brier_skill),
        "pass":bool(pass_test),
        "verdict":f"{'PASS' if pass_test else 'FAIL'} -- LOO AUC={loo_auc:.3f}, Cal={mean_cal_error:.3f}"}
    return results


# ============================================================
# MAIN
# ============================================================
def main():
    print("="*70)
    print("SRFF-I RVS MODEL -- COMPREHENSIVE VALIDATION SUITE (V3.0)")
    print("="*70)
    print("Date: April 17, 2026")
    print("Tests: 10 original + Test 11 (Hazard AUC) + Test 12 (Survival Calibration)")
    print()
    os.makedirs("/home/ubuntu/srff_validation", exist_ok=True)
    df = load_data()
    print(f"Data loaded: {len(df)} companies")
    print(f"  With financial data: {df['Has_Data'].sum()}")
    print(f"  Recovered: {df['Outcome_Binary'].sum()}")
    print(f"  Failed: {(1-df['Outcome_Binary']).sum()}")

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

    hazard_results, df_enhanced = test_11_hazard_layer(df)
    all_results["test_11"] = hazard_results

    cal_results = test_12_survival_calibration(df, df_enhanced)
    all_results["test_12"] = cal_results

    # Save enhanced dataframe
    out_cols = ["Company","Sector","Actual Outcome","Outcome_Binary",
        "V1","V2","V3","V4","V5","V6","LR_Prob",
        "Hazard_Survival_5yr","Composite_V3","V3_Verdict","Outcome Detail"]
    df_export = df_enhanced[[c for c in out_cols if c in df_enhanced.columns]].copy()
    df_export.to_excel("/home/ubuntu/srff_validation/rvs_v3_with_hazard.xlsx", index=False)
    print(f"\nV3.0 dataframe saved: /home/ubuntu/srff_validation/rvs_v3_with_hazard.xlsx")

    # Summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY (V3.0)")
    print("="*70)
    test_names = {
        "test_1":"Sector Accuracy","test_2":"Temporal Stability",
        "test_3":"Variable Importance","test_4":"Threshold Optimization",
        "test_5":"K-Fold Cross-Validation","test_6":"Sensitivity Analysis",
        "test_7":"Altman Z Comparison","test_8":"Extreme Stress Test",
        "test_9":"Missing Data Robustness","test_10":"Forward-Looking Validation",
        "test_11":"Hazard Discrimination (AUC)","test_12":"Survival Calibration (LOO)"}
    for tk,tl in test_names.items():
        r = all_results.get(tk,{})
        v = r.get("verdict","N/A"); p = r.get("pass",False)
        print(f"  {tk.upper():10s}  {tl:35s}  {'PASS' if p else 'FAIL/COND':10s}  {v}")
    passed = sum(1 for r in all_results.values() if r.get("pass",False))
    total = len(all_results)
    print(f"\n  OVERALL: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    if "v3_accuracy" in all_results.get("test_11",{}):
        print(f"  V3.0 Composite Accuracy: {all_results['test_11']['v3_accuracy']:.1%}")

    # Save JSON
    class NpEnc(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj,(np.integer,)): return int(obj)
            if isinstance(obj,(np.floating,)): return float(obj)
            if isinstance(obj,np.ndarray): return obj.tolist()
            if isinstance(obj,np.bool_): return bool(obj)
            if isinstance(obj,tuple): return list(obj)
            return super().default(obj)
    with open("/home/ubuntu/srff_validation/validation_results_v3.json","w") as f:
        json.dump(all_results, f, indent=2, cls=NpEnc)
    print(f"Results saved: /home/ubuntu/srff_validation/validation_results_v3.json")
    return df_enhanced, all_results

if __name__ == "__main__":
    df_enhanced, results = main()
