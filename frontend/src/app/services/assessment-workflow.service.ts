import { Injectable } from '@angular/core';
import { Store } from '@ngrx/store';

import { AssessmentActions } from '../store/assessment.actions';
import { AssessmentInitiation, RVSv4Input } from '../models/rvs.model';

type Source = 'manual' | 'file' | 'api';

interface ValidationResult {
  isValid: boolean;
  errors: string[];
}

@Injectable({ providedIn: 'root' })
export class AssessmentWorkflowService {
  constructor(private store: Store) {}

  /** Unified entry point for all three ingestion pathways. */
  submitAssessmentData(
    source: Source,
    data: AssessmentInitiation | { companyName: string; extractedInputs: RVSv4Input }
  ): void {
    let processed: AssessmentInitiation;

    switch (source) {
      case 'manual':
        processed = data as AssessmentInitiation;
        break;
      case 'file': {
        const fileData = data as { companyName: string; extractedInputs: RVSv4Input };
        processed = { companyName: fileData.companyName, inputs: fileData.extractedInputs };
        break;
      }
      case 'api':
        processed = data as AssessmentInitiation;
        break;
    }

    const result = this.validateComplete(processed);
    if (!result.isValid) {
      this.store.dispatch(AssessmentActions.validationFailed({ errors: result.errors }));
      return;
    }

    this.store.dispatch(
      AssessmentActions.initiateNewAssessment({ payload: processed, source })
    );
  }

  private validateComplete(payload: AssessmentInitiation): ValidationResult {
    const errors: string[] = [];
    if (!payload.companyName || payload.companyName.trim().length < 2) {
      errors.push('Company name is required (min 2 characters).');
    }
    if (payload.inputs.totalAssets <= 0) errors.push('Total assets must be greater than zero.');
    if (payload.inputs.revenue <= 0) errors.push('Revenue must be greater than zero.');
    return { isValid: errors.length === 0, errors };
  }
}
