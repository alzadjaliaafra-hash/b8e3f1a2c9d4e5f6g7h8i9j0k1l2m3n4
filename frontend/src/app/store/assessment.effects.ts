import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { of } from 'rxjs';
import { catchError, finalize, map, switchMap, tap } from 'rxjs/operators';

import { AssessmentAPIService } from '../services/assessment-api.service';
import { AssessmentActions } from './assessment.actions';

@Injectable()
export class AssessmentEffects {
  initiateAssessment$ = createEffect(() =>
    this.actions$.pipe(
      ofType(AssessmentActions.initiateNewAssessment),
      switchMap(action =>
        this.api.create(action.payload).pipe(
          map(assessment => AssessmentActions.assessmentCreated({ assessment })),
          catchError(error => of(AssessmentActions.assessmentCreationFailed({ error }))),
          finalize(() => {
            /* loading handled by reducer */
          })
        )
      )
    )
  );

  loadAssessments$ = createEffect(() =>
    this.actions$.pipe(
      ofType(AssessmentActions.loadAssessments),
      switchMap(action =>
        this.api.getAll(action.page, action.pageSize).pipe(
          map(response =>
            AssessmentActions.assessmentsLoaded({
              assessments: response.data,
              totalCount: response.total,
              page: action.page,
            })
          ),
          catchError(error => of(AssessmentActions.assessmentsLoadFailed({ error })))
        )
      )
    )
  );

  loadAssessmentById$ = createEffect(() =>
    this.actions$.pipe(
      ofType(AssessmentActions.loadAssessmentById),
      switchMap(action =>
        this.api.getById(action.id).pipe(
          map(assessment => AssessmentActions.assessmentLoaded({ assessment })),
          catchError(error => of(AssessmentActions.assessmentLoadFailed({ error })))
        )
      )
    )
  );

  selectAssessment$ = createEffect(
    () =>
      this.actions$.pipe(
        ofType(AssessmentActions.selectAssessment),
        tap(action => this.router.navigate(['/assessments', action.id]))
      ),
    { dispatch: false }
  );

  downloadReport$ = createEffect(() =>
    this.actions$.pipe(
      ofType(AssessmentActions.downloadReport),
      switchMap(action =>
        this.api.downloadReport(action.id).pipe(
          map(blob => {
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `assessment-report-${action.id}.pdf`;
            link.click();
            window.URL.revokeObjectURL(url);
            return AssessmentActions.reportDownloaded({ id: action.id });
          }),
          catchError(error => of(AssessmentActions.reportDownloadFailed({ error })))
        )
      )
    )
  );

  deleteAssessment$ = createEffect(() =>
    this.actions$.pipe(
      ofType(AssessmentActions.deleteAssessment),
      switchMap(action =>
        this.api.delete(action.id).pipe(
          map(() => AssessmentActions.assessmentDeleted({ id: action.id })),
          catchError(error => of(AssessmentActions.assessmentDeleteFailed({ error })))
        )
      )
    )
  );

  constructor(
    private actions$: Actions,
    private api: AssessmentAPIService,
    private router: Router,
    private _store: Store
  ) {}
}
