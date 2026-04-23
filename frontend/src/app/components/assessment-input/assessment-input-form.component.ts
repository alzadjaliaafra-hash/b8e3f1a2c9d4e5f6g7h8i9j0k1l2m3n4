import { Component, OnInit } from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  FormGroup,
  ValidationErrors,
  ValidatorFn,
  Validators,
} from '@angular/forms';
import { Store } from '@ngrx/store';

import { AssessmentInitiation, RVSv4Input } from '../../models/rvs.model';
import { AssessmentActions } from '../../store/assessment.actions';

@Component({
  selector: 'app-assessment-input-form',
  templateUrl: './assessment-input-form.component.html',
})
export class AssessmentInputFormComponent implements OnInit {
  assessmentForm!: FormGroup;

  constructor(private fb: FormBuilder, private store: Store) {}

  ngOnInit(): void {
    this.assessmentForm = this.fb.group({
      companyIdentification: this.fb.group({
        companyName: ['', [Validators.required, Validators.minLength(2)]],
        industryClassification: ['', Validators.required],
        assessmentDate: [new Date(), Validators.required],
      }),

      balanceSheetData: this.fb.group({
        workingCapital: [null, [Validators.required, Validators.min(0)]],
        totalAssets: [null, [Validators.required, Validators.min(1)]],
        retainedEarnings: [null, Validators.required],
        totalDebt: [null, [Validators.required, Validators.min(0)]],
        collateralValue: [null, [Validators.required, Validators.min(0)]],
        totalLiabilities: [null, [Validators.required, Validators.min(0)]],
      }),

      incomeStatementData: this.fb.group({
        revenue: [null, [Validators.required, Validators.min(1)]],
        ebitda: [null, Validators.required],
        operatingCashFlow: [null, Validators.required],
      }),

      privateCompanyAdjustments: this.fb.group({
        ownerCompensationExcess: [0, [Validators.min(0)]],
        rptRevenuePercent: [0, [Validators.min(0), Validators.max(100)]],
        rptCostPercent: [0, [Validators.min(0), Validators.max(100)]],
        appraisalFactor: [1.0, [Validators.min(0.5), Validators.max(1.5)]],
        revenueUnderreportingFactor: [1.0, [Validators.min(0.8), Validators.max(1.2)]],
      }),

      qualitativeFactors: this.fb.group({
        governanceScore: [50, [Validators.required, Validators.min(0), Validators.max(100)]],
        concentrationScore: [50, [Validators.required, Validators.min(0), Validators.max(100)]],
        informationAsymmetryPercent: [10, [Validators.required, Validators.min(0), Validators.max(20)]],
      }),

      shariahCompliance: this.fb.group({
        isShariahCompliant: [false, Validators.required],
      }),
    });

    this.setupCrossFieldValidation();
  }

  private setupCrossFieldValidation(): void {
    const balance = this.assessmentForm.get('balanceSheetData') as FormGroup;
    balance.setValidators(this.assetLiabilityValidator());
    balance.valueChanges.subscribe(() => this.validateWorkingCapitalConsistency());
  }

  private validateWorkingCapitalConsistency(): void {
    /* hook for cross-field WC sanity checks */
  }

  private assetLiabilityValidator(): ValidatorFn {
    return (group: AbstractControl): ValidationErrors | null => {
      const assets = group.get('totalAssets')?.value;
      const liabilities = group.get('totalLiabilities')?.value;
      if (assets && liabilities && liabilities > assets * 1.5) {
        return { excessiveLeverage: 'Total liabilities exceed 150% of assets - verify data' };
      }
      return null;
    };
  }

  onSubmit(): void {
    if (this.assessmentForm.valid) {
      const payload = this.transformFormToDTO(this.assessmentForm.value);
      this.store.dispatch(
        AssessmentActions.initiateNewAssessment({ payload, source: 'manual' })
      );
    } else {
      this.highlightValidationErrors();
    }
  }

  private highlightValidationErrors(): void {
    this.assessmentForm.markAllAsTouched();
  }

  private transformFormToDTO(formValue: any): AssessmentInitiation {
    const inputs: RVSv4Input = {
      workingCapital: formValue.balanceSheetData.workingCapital,
      totalAssets: formValue.balanceSheetData.totalAssets,
      retainedEarnings: formValue.balanceSheetData.retainedEarnings,
      totalDebt: formValue.balanceSheetData.totalDebt,
      collateralValue: formValue.balanceSheetData.collateralValue,
      totalLiabilities: formValue.balanceSheetData.totalLiabilities,

      revenue: formValue.incomeStatementData.revenue,
      ebitda: formValue.incomeStatementData.ebitda,
      operatingCashFlow: formValue.incomeStatementData.operatingCashFlow,

      ownerCompensationExcess: formValue.privateCompanyAdjustments.ownerCompensationExcess,
      rptRevenuePercent: formValue.privateCompanyAdjustments.rptRevenuePercent,
      rptCostPercent: formValue.privateCompanyAdjustments.rptCostPercent,
      appraisalFactor: formValue.privateCompanyAdjustments.appraisalFactor,
      revenueUnderreportingFactor: formValue.privateCompanyAdjustments.revenueUnderreportingFactor,

      governanceScore: formValue.qualitativeFactors.governanceScore,
      concentrationScore: formValue.qualitativeFactors.concentrationScore,
      informationAsymmetryPercent: formValue.qualitativeFactors.informationAsymmetryPercent,

      isShariahCompliant: formValue.shariahCompliance.isShariahCompliant,
    };

    return {
      companyName: formValue.companyIdentification.companyName,
      inputs,
    };
  }
}
