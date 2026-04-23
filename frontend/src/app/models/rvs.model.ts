export interface RVSv4Input {
  workingCapital: number;
  totalAssets: number;
  retainedEarnings: number;
  ebitda: number;
  totalDebt: number;
  operatingCashFlow: number;
  collateralValue: number;
  totalLiabilities: number;
  revenue: number;
  ownerCompensationExcess: number;
  rptRevenuePercent: number;
  rptCostPercent: number;
  appraisalFactor: number;
  revenueUnderreportingFactor: number;
  governanceScore: number;
  concentrationScore: number;
  informationAsymmetryPercent: number;
  isShariahCompliant: boolean;
}

export interface RVSv4Output {
  finalScore: number;
  componentScores?: Record<string, number>;
  riskBand?: string;
  recommendations?: string[];
}

export interface MurshidiAnalysisDTO {
  pattern: string;
  structure: string;
  revealedValue: string;
}

export interface Assessment {
  id: string;
  companyName: string;
  status: 'draft' | 'processing' | 'completed' | 'failed';
  userId: string;
  inputs: RVSv4Input;
  results?: RVSv4Output;
  murshidiAnalysis?: MurshidiAnalysisDTO;
  createdAt: string;
  updatedAt: string;
}

export interface AssessmentInitiation {
  companyName: string;
  inputs: RVSv4Input;
}

export interface PaginatedAssessments {
  data: Assessment[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}
