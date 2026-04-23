import { createReducer, on } from '@ngrx/store';
import { Assessment } from '../models/rvs.model';
import { AssessmentActions } from './assessment.actions';

export interface AssessmentState {
  entities: Record<string, Assessment>;
  ids: string[];
  totalCount: number;
  currentPage: number;
  selectedId: string | null;
  loading: boolean;
  detailLoading: boolean;
  validationErrors: string[];
  error: unknown | null;
}

export const initialAssessmentState: AssessmentState = {
  entities: {},
  ids: [],
  totalCount: 0,
  currentPage: 1,
  selectedId: null,
  loading: false,
  detailLoading: false,
  validationErrors: [],
  error: null,
};

export const assessmentReducer = createReducer(
  initialAssessmentState,

  on(AssessmentActions.initiateNewAssessment, state => ({
    ...state,
    loading: true,
    validationErrors: [],
    error: null,
  })),

  on(AssessmentActions.validationFailed, (state, { errors }) => ({
    ...state,
    loading: false,
    validationErrors: errors,
  })),

  on(AssessmentActions.assessmentCreated, (state, { assessment }) => ({
    ...state,
    loading: false,
    entities: { ...state.entities, [assessment.id]: assessment },
    ids: state.ids.includes(assessment.id) ? state.ids : [assessment.id, ...state.ids],
    totalCount: state.totalCount + 1,
  })),

  on(AssessmentActions.assessmentCreationFailed, (state, { error }) => ({
    ...state,
    loading: false,
    error,
  })),

  on(AssessmentActions.loadAssessments, state => ({ ...state, loading: true, error: null })),

  on(AssessmentActions.assessmentsLoaded, (state, { assessments, totalCount, page }) => {
    const entities: Record<string, Assessment> = { ...state.entities };
    const ids: string[] = [];
    for (const a of assessments) {
      entities[a.id] = a;
      ids.push(a.id);
    }
    return {
      ...state,
      loading: false,
      entities,
      ids,
      totalCount,
      currentPage: page,
    };
  }),

  on(AssessmentActions.assessmentsLoadFailed, (state, { error }) => ({
    ...state,
    loading: false,
    error,
  })),

  on(AssessmentActions.loadAssessmentById, state => ({ ...state, detailLoading: true })),

  on(AssessmentActions.assessmentLoaded, (state, { assessment }) => ({
    ...state,
    detailLoading: false,
    entities: { ...state.entities, [assessment.id]: assessment },
    selectedId: assessment.id,
  })),

  on(AssessmentActions.assessmentLoadFailed, (state, { error }) => ({
    ...state,
    detailLoading: false,
    error,
  })),

  on(AssessmentActions.selectAssessment, (state, { id }) => ({ ...state, selectedId: id })),

  on(AssessmentActions.assessmentDeleted, (state, { id }) => {
    const { [id]: _removed, ...entities } = state.entities;
    return {
      ...state,
      entities,
      ids: state.ids.filter(existing => existing !== id),
      totalCount: Math.max(0, state.totalCount - 1),
      selectedId: state.selectedId === id ? null : state.selectedId,
    };
  }),
);
