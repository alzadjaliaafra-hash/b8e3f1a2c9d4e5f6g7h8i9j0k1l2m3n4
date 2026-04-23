import { createFeatureSelector, createSelector } from '@ngrx/store';
import { AssessmentState } from './assessment.reducer';

export const selectAssessmentState = createFeatureSelector<AssessmentState>('assessment');

export const selectAllAssessments = createSelector(
  selectAssessmentState,
  state => state.ids.map(id => state.entities[id]).filter(Boolean)
);

export const selectAssessmentsLoading = createSelector(
  selectAssessmentState,
  state => state.loading
);

export const selectAssessmentDetailLoading = createSelector(
  selectAssessmentState,
  state => state.detailLoading
);

export const selectCurrentAssessment = createSelector(
  selectAssessmentState,
  state => (state.selectedId ? state.entities[state.selectedId] ?? null : null)
);

export const selectAssessmentValidationErrors = createSelector(
  selectAssessmentState,
  state => state.validationErrors
);

export const selectAssessmentTotalCount = createSelector(
  selectAssessmentState,
  state => state.totalCount
);
