import { createAction, props } from '@ngrx/store';
import { Assessment, AssessmentInitiation } from '../models/rvs.model';

export const AssessmentActions = {
  initiateNewAssessment: createAction(
    '[Assessment] Initiate New',
    props<{ payload: AssessmentInitiation; source?: 'manual' | 'file' | 'api' }>()
  ),
  validationFailed: createAction(
    '[Assessment] Validation Failed',
    props<{ errors: string[] }>()
  ),
  assessmentCreated: createAction(
    '[Assessment] Created',
    props<{ assessment: Assessment }>()
  ),
  assessmentCreationFailed: createAction(
    '[Assessment] Creation Failed',
    props<{ error: unknown }>()
  ),

  loadAssessments: createAction(
    '[Assessment] Load List',
    props<{ page: number; pageSize: number }>()
  ),
  assessmentsLoaded: createAction(
    '[Assessment] List Loaded',
    props<{ assessments: Assessment[]; totalCount: number; page: number }>()
  ),
  assessmentsLoadFailed: createAction(
    '[Assessment] List Load Failed',
    props<{ error: unknown }>()
  ),

  loadAssessmentById: createAction(
    '[Assessment] Load By Id',
    props<{ id: string }>()
  ),
  assessmentLoaded: createAction(
    '[Assessment] Loaded',
    props<{ assessment: Assessment }>()
  ),
  assessmentLoadFailed: createAction(
    '[Assessment] Load Failed',
    props<{ error: unknown }>()
  ),

  selectAssessment: createAction(
    '[Assessment] Select',
    props<{ id: string }>()
  ),

  deleteAssessment: createAction(
    '[Assessment] Delete',
    props<{ id: string }>()
  ),
  assessmentDeleted: createAction(
    '[Assessment] Deleted',
    props<{ id: string }>()
  ),
  assessmentDeleteFailed: createAction(
    '[Assessment] Delete Failed',
    props<{ error: unknown }>()
  ),

  downloadReport: createAction(
    '[Assessment] Download Report',
    props<{ id: string }>()
  ),
  reportDownloaded: createAction(
    '[Assessment] Report Downloaded',
    props<{ id: string }>()
  ),
  reportDownloadFailed: createAction(
    '[Assessment] Report Download Failed',
    props<{ error: unknown }>()
  ),

  recalculateAssessment: createAction(
    '[Assessment] Recalculate',
    props<{ id: string }>()
  ),

  subscribeToUpdates: createAction(
    '[Assessment] Subscribe To Updates',
    props<{ userId: string }>()
  ),
};
