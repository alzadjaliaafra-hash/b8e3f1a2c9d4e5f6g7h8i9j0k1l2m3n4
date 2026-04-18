import { Component, OnDestroy, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import { Observable, Subject } from 'rxjs';
import { filter, takeUntil } from 'rxjs/operators';

import { Assessment } from '../../models/rvs.model';
import { AssessmentActions } from '../../store/assessment.actions';
import {
  selectAllAssessments,
  selectAssessmentsLoading,
} from '../../store/assessment.selectors';

@Component({
  selector: 'app-assessment-list',
  templateUrl: './assessment-list.component.html',
})
export class AssessmentListComponent implements OnInit, OnDestroy {
  assessments$!: Observable<Assessment[]>;
  loading$!: Observable<boolean>;
  currentPage = 1;
  pageSize = 20;

  private destroy$ = new Subject<void>();

  constructor(private store: Store) {}

  ngOnInit(): void {
    this.assessments$ = this.store.select(selectAllAssessments);
    this.loading$ = this.store.select(selectAssessmentsLoading);
    this.loadAssessments();

    this.store
      .select((state: any) => state.auth?.currentUser)
      .pipe(
        takeUntil(this.destroy$),
        filter(user => !!user)
      )
      .subscribe(user => {
        this.store.dispatch(AssessmentActions.subscribeToUpdates({ userId: user.id }));
      });
  }

  loadAssessments(): void {
    this.store.dispatch(
      AssessmentActions.loadAssessments({ page: this.currentPage, pageSize: this.pageSize })
    );
  }

  onPageChange(page: number): void {
    this.currentPage = page;
    this.loadAssessments();
  }

  viewAssessment(assessment: Assessment): void {
    this.store.dispatch(AssessmentActions.selectAssessment({ id: assessment.id }));
  }

  deleteAssessment(assessment: Assessment): void {
    if (confirm(`Delete assessment for ${assessment.companyName}?`)) {
      this.store.dispatch(AssessmentActions.deleteAssessment({ id: assessment.id }));
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
}
