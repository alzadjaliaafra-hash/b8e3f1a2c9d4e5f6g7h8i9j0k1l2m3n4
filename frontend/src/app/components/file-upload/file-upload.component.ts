import { Component, EventEmitter, Output } from '@angular/core';
import * as XLSX from 'xlsx';
import Papa from 'papaparse';

import { RVSv4Input } from '../../models/rvs.model';

@Component({
  selector: 'app-file-upload',
  templateUrl: './file-upload.component.html',
})
export class FileUploadComponent {
  @Output() dataExtracted = new EventEmitter<RVSv4Input>();
  @Output() uploadError = new EventEmitter<string>();

  readonly allowedFileTypes = ['.xlsx', '.xls', '.csv'];
  uploadProgress = 0;

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (!input.files?.length) {
      return;
    }
    this.validateAndProcessFile(input.files[0]);
  }

  private validateAndProcessFile(file: File): void {
    if (!this.isValidFileType(file)) {
      this.showError('Invalid file type. Please upload Excel or CSV files only.');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      this.showError('File size exceeds 5MB limit.');
      return;
    }
    this.parseFile(file);
  }

  private isValidFileType(file: File): boolean {
    const lower = file.name.toLowerCase();
    return this.allowedFileTypes.some(ext => lower.endsWith(ext));
  }

  private parseFile(file: File): void {
    const reader = new FileReader();
    reader.onload = (e: ProgressEvent<FileReader>) => {
      try {
        const data = e.target?.result;
        if (file.name.toLowerCase().endsWith('.csv')) {
          this.parseCSV(data as string);
        } else {
          this.parseExcel(data as ArrayBuffer);
        }
      } catch {
        this.showError('Failed to parse file. Please check the file format.');
      }
    };

    if (file.name.toLowerCase().endsWith('.csv')) {
      reader.readAsText(file);
    } else {
      reader.readAsArrayBuffer(file);
    }
  }

  private parseExcel(data: ArrayBuffer): void {
    const workbook = XLSX.read(data, { type: 'array' });
    const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
    const jsonData = XLSX.utils.sheet_to_json<Record<string, unknown>>(firstSheet, { header: 1 });
    this.extractFinancialData(jsonData as any[]);
  }

  private parseCSV(data: string): void {
    const parsed = Papa.parse<Record<string, unknown>>(data, { header: true });
    this.extractFinancialData(parsed.data as any[]);
  }

  private extractFinancialData(rawData: any[]): void {
    const extracted: RVSv4Input = {
      workingCapital: this.findValue(rawData, 'Working Capital') as number,
      totalAssets: this.findValue(rawData, 'Total Assets') as number,
      retainedEarnings: this.findValue(rawData, 'Retained Earnings') as number,
      totalDebt: this.findValue(rawData, 'Total Debt') as number,
      collateralValue: this.findValue(rawData, 'Collateral Value') as number,
      totalLiabilities: this.findValue(rawData, 'Total Liabilities') as number,
      revenue: this.findValue(rawData, 'Revenue') as number,
      ebitda: this.findValue(rawData, 'EBITDA') as number,
      operatingCashFlow: this.findValue(rawData, 'Operating Cash Flow') as number,
      ownerCompensationExcess: this.findValue(rawData, 'Owner Compensation Excess', 0) as number,
      rptRevenuePercent: this.findValue(rawData, 'RPT Revenue %', 0) as number,
      rptCostPercent: this.findValue(rawData, 'RPT Cost %', 0) as number,
      appraisalFactor: this.findValue(rawData, 'Appraisal Factor', 1.0) as number,
      revenueUnderreportingFactor: this.findValue(rawData, 'Revenue Underreporting Factor', 1.0) as number,
      governanceScore: this.findValue(rawData, 'Governance Score', 50) as number,
      concentrationScore: this.findValue(rawData, 'Concentration Score', 50) as number,
      informationAsymmetryPercent: this.findValue(rawData, 'Information Asymmetry %', 10) as number,
      isShariahCompliant: this.findValue(rawData, 'Shariah Compliant', false) as boolean,
    };

    this.dataExtracted.emit(extracted);
  }

  private findValue(data: any[], fieldName: string, defaultValue: unknown = null): unknown {
    const row = data.find(r => r?.['Field'] === fieldName || r?.['Metric'] === fieldName);
    if (!row) {
      return defaultValue;
    }
    const value = row['Value'] ?? row['Amount'];
    return value === undefined || value === null || value === '' ? defaultValue : value;
  }

  private showError(message: string): void {
    this.uploadError.emit(message);
  }
}
