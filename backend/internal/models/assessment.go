package models

import "time"

// Assessment is the root aggregate persisted for each RVS evaluation.
type Assessment struct {
	ID                  string              `json:"id"`
	CompanyName         string              `json:"companyName"`
	Status              string              `json:"status"`
	UserID              string              `json:"userId"`
	Inputs              RVSv4Input          `json:"inputs"`
	Results             *RVSv4Output        `json:"results,omitempty"`
	MurshidiAnalysis    *MurshidiAnalysisDTO `json:"murshidiAnalysis,omitempty"`
	Source              string              `json:"source,omitempty"`
	ExternalSystemID    string              `json:"externalSystemId,omitempty"`
	ExternalReferenceID string              `json:"externalReferenceId,omitempty"`
	CreatedAt           time.Time           `json:"createdAt"`
	UpdatedAt           time.Time           `json:"updatedAt"`
}

// RVSv4Input mirrors the frontend input DTO. Field names match the JSON
// payload shape used by the Angular client.
type RVSv4Input struct {
	WorkingCapital              float64 `json:"workingCapital"`
	TotalAssets                 float64 `json:"totalAssets"`
	RetainedEarnings            float64 `json:"retainedEarnings"`
	EBITDA                      float64 `json:"ebitda"`
	TotalDebt                   float64 `json:"totalDebt"`
	OperatingCashFlow           float64 `json:"operatingCashFlow"`
	CollateralValue             float64 `json:"collateralValue"`
	TotalLiabilities            float64 `json:"totalLiabilities"`
	Revenue                     float64 `json:"revenue"`
	OwnerCompensationExcess     float64 `json:"ownerCompensationExcess"`
	RPTRevenuePercent           float64 `json:"rptRevenuePercent"`
	RPTCostPercent              float64 `json:"rptCostPercent"`
	AppraisalFactor             float64 `json:"appraisalFactor"`
	RevenueUnderreportingFactor float64 `json:"revenueUnderreportingFactor"`
	GovernanceScore             float64 `json:"governanceScore"`
	ConcentrationScore          float64 `json:"concentrationScore"`
	InformationAsymmetryPercent float64 `json:"informationAsymmetryPercent"`
	IsShariahCompliant          bool    `json:"isShariahCompliant"`
}

// RVSv4Output is the computational result produced by the RVS engine.
type RVSv4Output struct {
	FinalScore       float64            `json:"finalScore"`
	ComponentScores  map[string]float64 `json:"componentScores,omitempty"`
	RiskBand         string             `json:"riskBand,omitempty"`
	Recommendations  []string           `json:"recommendations,omitempty"`
}

// MurshidiAnalysisDTO is the qualitative AI analysis layered on top of the
// quantitative RVS result.
type MurshidiAnalysisDTO struct {
	Pattern       string `json:"pattern"`
	Structure     string `json:"structure"`
	RevealedValue string `json:"revealedValue"`
}
