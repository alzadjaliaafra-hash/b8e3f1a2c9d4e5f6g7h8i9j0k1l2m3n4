package services

import (
	"log"

	"github.com/alzadjaliaafra-hash/srff-i-rvs-model/backend/internal/models"
)

// DataTransformer converts external payload shapes into internal RVS inputs.
type DataTransformer struct {
	logger *log.Logger
}

func NewDataTransformer(logger *log.Logger) *DataTransformer {
	return &DataTransformer{logger: logger}
}

// TransformExternalToInternal converts external accounting data to RVSv4Input.
func (dt *DataTransformer) TransformExternalToInternal(external models.ExternalDataPayload) (models.RVSv4Input, error) {
	workingCapital := external.BalanceSheet.CurrentAssets - external.BalanceSheet.CurrentLiabilities
	totalDebt := external.BalanceSheet.LongTermDebt + external.BalanceSheet.ShortTermDebt

	ebitda := external.IncomeStatement.NetIncome +
		external.IncomeStatement.InterestExpense +
		external.IncomeStatement.TaxExpense +
		external.IncomeStatement.Depreciation +
		external.IncomeStatement.Amortization

	collateralValue := external.BalanceSheet.PropertyPlantEquipment + external.BalanceSheet.Inventory

	var (
		ownerCompExcess             float64
		rptRevenuePercent           float64
		rptCostPercent              float64
		appraisalFactor             = 1.0
		revenueUnderreportingFactor = 1.0
	)

	if external.Adjustments != nil {
		ownerCompExcess = external.Adjustments.OwnerCompensation - external.Adjustments.MarketCompensation
		if ownerCompExcess < 0 {
			ownerCompExcess = 0
		}

		if external.IncomeStatement.Revenue > 0 {
			rptRevenuePercent = (external.Adjustments.RelatedPartyRevenue / external.IncomeStatement.Revenue) * 100
		}

		totalCosts := external.IncomeStatement.CostOfGoodsSold + external.IncomeStatement.OperatingExpenses
		if totalCosts > 0 {
			rptCostPercent = (external.Adjustments.RelatedPartyCosts / totalCosts) * 100
		}

		if collateralValue > 0 && external.Adjustments.AssetAppraisalValue > 0 {
			appraisalFactor = external.Adjustments.AssetAppraisalValue / collateralValue
		}

		if external.Adjustments.EstimatedRevenueAdjustment != 0 {
			revenueUnderreportingFactor = external.Adjustments.EstimatedRevenueAdjustment
		}
	}

	var (
		governanceScore      float64 = 50
		concentrationScore   float64 = 50
		infoAsymmetryPercent float64 = 10
		isShariahCompliant   bool
	)

	if external.Qualitative != nil {
		governanceScore = external.Qualitative.GovernanceScore
		concentrationScore = external.Qualitative.CustomerConcentrationScore
		infoAsymmetryPercent = 20 - (external.Qualitative.InformationQualityScore * 0.2)
		isShariahCompliant = external.Qualitative.ShariahCompliant
	}

	input := models.RVSv4Input{
		WorkingCapital:              workingCapital,
		TotalAssets:                 external.BalanceSheet.TotalAssets,
		RetainedEarnings:            external.BalanceSheet.RetainedEarnings,
		EBITDA:                      ebitda,
		TotalDebt:                   totalDebt,
		OperatingCashFlow:           external.CashFlowStatement.OperatingCashFlow,
		CollateralValue:             collateralValue,
		TotalLiabilities:            external.BalanceSheet.TotalLiabilities,
		Revenue:                     external.IncomeStatement.Revenue,
		OwnerCompensationExcess:     ownerCompExcess,
		RPTRevenuePercent:           rptRevenuePercent,
		RPTCostPercent:              rptCostPercent,
		AppraisalFactor:             appraisalFactor,
		RevenueUnderreportingFactor: revenueUnderreportingFactor,
		GovernanceScore:             governanceScore,
		ConcentrationScore:          concentrationScore,
		InformationAsymmetryPercent: infoAsymmetryPercent,
		IsShariahCompliant:          isShariahCompliant,
	}

	dt.logger.Printf("Transformed external data from system %s (ref: %s) for company %s",
		external.SystemID, external.ReferenceID, external.CompanyName)

	return input, nil
}
