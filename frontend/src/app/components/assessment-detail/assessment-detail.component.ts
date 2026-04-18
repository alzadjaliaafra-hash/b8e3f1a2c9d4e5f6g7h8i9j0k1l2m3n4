import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { filter, map, take } from 'rxjs/operators';

import {
  Assessment,
  MurshidiAnalysisDTO,
  RVSv4Input,
  RVSv4Output,
} from '../../models/rvs.model';
import { AssessmentActions } from '../../store/assessment.actions';
import {
  selectAssessmentDetailLoading,
  selectCurrentAssessment,
} from '../../store/assessment.selectors';

@Component({
  selector: 'app-assessment-detail',
  templateUrl: './assessment-detail.component.html',
})
export class AssessmentDetailComponent implements OnInit {
  assessment$!: Observable<Assessment | null>;
  loading$!: Observable<boolean>;
  financialInputs$!: Observable<RVSv4Input | null>;
  calculationResults$!: Observable<RVSv4Output | null>;
  aiAnalysis$!: Observable<MurshidiAnalysisDTO | null>;

  constructor(private store: Store, private route: ActivatedRoute) {}

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.store.dispatch(AssessmentActions.loadAssessmentById({ id }));
    }

    this.assessment$ = this.store.select(selectCurrentAssessment);
    this.loading$ = this.store.select(selectAssessmentDetailLoading);

    this.financialInputs$ = this.assessment$.pipe(map(a => a?.inputs ?? null));
    this.calculationResults$ = this.assessment$.pipe(map(a => a?.results ?? null));
    this.aiAnalysis$ = this.assessment$.pipe(map(a => a?.murshidiAnalysis ?? null));
  }

  downloadReport(): void {
    this.assessment$
      .pipe(take(1), filter((a): a is Assessment => !!a))
      .subscribe(a => this.store.dispatch(AssessmentActions.downloadReport({ id: a.id })));
  }

  recalculate(): void {
    this.assessment$
      .pipe(take(1), filter((a): a is Assessment => !!a))
      .subscribe(a =>
        this.store.dispatch(AssessmentActions.recalculateAssessment({ id: a.id }))
      );
  }
}
