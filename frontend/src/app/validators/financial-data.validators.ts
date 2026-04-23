import { AbstractControl, AsyncValidatorFn, ValidationErrors, ValidatorFn } from '@angular/forms';
import { Observable, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

import { AssessmentAPIService } from '../services/assessment-api.service';

export class FinancialDataValidators {
  static solvencyCheck(): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      const parent = control.parent;
      if (!parent) {
        return null;
      }
      const assets = parent.get('totalAssets')?.value;
      const liabilities = parent.get('totalLiabilities')?.value;
      if (assets && liabilities && liabilities > assets * 2) {
        return {
          insolvency: {
            message: 'Liabilities exceed 200% of assets - verify data accuracy',
            assets,
            liabilities,
            ratio: ((liabilities / assets) * 100).toFixed(1),
          },
        };
      }
      return null;
    };
  }

  static ebitdaReasonability(): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      const parent = control.parent;
      if (!parent) {
        return null;
      }
      const ebitda = control.value;
      const revenue = parent.get('revenue')?.value;
      if (ebitda && revenue) {
        const margin = (ebitda / revenue) * 100;
        if (margin < -50) {
          return {
            ebitdaUnreasonable: {
              message: 'EBITDA margin below -50% - verify calculation',
              ebitda,
              revenue,
              margin: margin.toFixed(1),
            },
          };
        }
        if (margin > 80) {
          return {
            ebitdaUnreasonable: {
              message: 'EBITDA margin above 80% - unusually high, verify data',
              ebitda,
              revenue,
              margin: margin.toFixed(1),
            },
          };
        }
      }
      return null;
    };
  }

  static collateralCoverage(): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      const parent = control.parent;
      if (!parent) {
        return null;
      }
      const collateral = control.value;
      const totalDebt = parent.get('totalDebt')?.value;
      if (collateral && totalDebt && totalDebt > 0) {
        const coverage = collateral / totalDebt;
        if (coverage < 0.5) {
          return {
            insufficientCollateral: {
              message: 'Collateral covers less than 50% of debt',
              collateral,
              debt: totalDebt,
              coverage: (coverage * 100).toFixed(1),
            },
          };
        }
      }
      return null;
    };
  }

  static duplicateCompanyCheck(api: AssessmentAPIService): AsyncValidatorFn {
    return (control: AbstractControl): Observable<ValidationErrors | null> => {
      if (!control.value) {
        return of(null);
      }
      return api.checkDuplicateCompany(control.value).pipe(
        map(exists =>
          exists
            ? {
                duplicateCompany: {
                  message: 'Assessment already exists for this company in the last 30 days',
                },
              }
            : null
        ),
        catchError(() => of(null))
      );
    };
  }
}
