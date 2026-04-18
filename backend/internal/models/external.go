package models

// ExternalDataPayload represents the structure from external accounting systems.
type ExternalDataPayload struct {
	SystemID          string              `json:"systemId"`
	ReferenceID       string              `json:"referenceId"`
	CompanyName       string              `json:"companyName"`
	ReportingPeriod   string              `json:"reportingPeriod"`
	BalanceSheet      BalanceSheetData    `json:"balanceSheet"`
	IncomeStatement   IncomeStatementData `json:"incomeStatement"`
	CashFlowStatement CashFlowData        `json:"cashFlowStatement"`
	Adjustments       *AdjustmentFactors  `json:"adjustments,omitempty"`
	Qualitative       *QualitativeFactors `json:"qualitative,omitempty"`
}

type BalanceSheetData struct {
	CurrentAssets          float64 `json:"currentAssets"`
	CurrentLiabilities     float64 `json:"currentLiabilities"`
	TotalAssets            float64 `json:"totalAssets"`
	TotalLiabilities       float64 `json:"totalLiabilities"`
	RetainedEarnings       float64 `json:"retainedEarnings"`
	LongTermDebt           float64 `json:"longTermDebt"`
	ShortTermDebt          float64 `json:"shortTermDebt"`
	Inventory              float64 `json:"inventory"`
	PropertyPlantEquipment float64 `json:"propertyPlantEquipment"`
}

type IncomeStatementData struct {
	Revenue           float64 `json:"revenue"`
	CostOfGoodsSold   float64 `json:"costOfGoodsSold"`
	OperatingExpenses float64 `json:"operatingExpenses"`
	InterestExpense   float64 `json:"interestExpense"`
	Depreciation      float64 `json:"depreciation"`
	Amortization      float64 `json:"amortization"`
	TaxExpense        float64 `json:"taxExpense"`
	NetIncome         float64 `json:"netIncome"`
}

type CashFlowData struct {
	OperatingCashFlow float64 `json:"operatingCashFlow"`
	InvestingCashFlow float64 `json:"investingCashFlow"`
	FinancingCashFlow float64 `json:"financingCashFlow"`
}

type AdjustmentFactors struct {
	OwnerCompensation          float64 `json:"ownerCompensation"`
	MarketCompensation         float64 `json:"marketCompensation"`
	RelatedPartyRevenue        float64 `json:"relatedPartyRevenue"`
	RelatedPartyCosts          float64 `json:"relatedPartyCosts"`
	AssetAppraisalValue        float64 `json:"assetAppraisalValue"`
	EstimatedRevenueAdjustment float64 `json:"estimatedRevenueAdjustment"`
}

type QualitativeFactors struct {
	GovernanceScore            float64 `json:"governanceScore"`
	CustomerConcentrationScore float64 `json:"customerConcentrationScore"`
	InformationQualityScore    float64 `json:"informationQualityScore"`
	ShariahCompliant           bool    `json:"shariahCompliant"`
}
