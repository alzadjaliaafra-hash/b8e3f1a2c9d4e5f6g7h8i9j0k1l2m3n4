import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import {
  Assessment,
  AssessmentInitiation,
  PaginatedAssessments,
} from '../models/rvs.model';

@Injectable({ providedIn: 'root' })
export class AssessmentAPIService {
  private readonly baseUrl = '/api/v1/assessments';

  constructor(private http: HttpClient) {}

  create(payload: AssessmentInitiation): Observable<Assessment> {
    return this.http.post<Assessment>(this.baseUrl, payload);
  }

  getAll(page: number, pageSize: number): Observable<PaginatedAssessments> {
    return this.http.get<PaginatedAssessments>(this.baseUrl, {
      params: { page: String(page), pageSize: String(pageSize) },
    });
  }

  getById(id: string): Observable<Assessment> {
    return this.http.get<Assessment>(`${this.baseUrl}/${id}`);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${id}`);
  }

  downloadReport(id: string): Observable<Blob> {
    return this.http.get(`${this.baseUrl}/${id}/report`, { responseType: 'blob' });
  }

  recalculate(id: string): Observable<Assessment> {
    return this.http.post<Assessment>(`${this.baseUrl}/${id}/recalculate`, {});
  }

  checkDuplicateCompany(companyName: string): Observable<boolean> {
    return this.http.get<boolean>(`${this.baseUrl}/check-duplicate`, {
      params: { companyName },
    });
  }

  uploadFile(file: File): Observable<{ extractedData: unknown; message: string }> {
    const form = new FormData();
    form.append('financialData', file);
    return this.http.post<{ extractedData: unknown; message: string }>(
      `${this.baseUrl}/upload`,
      form
    );
  }
}
