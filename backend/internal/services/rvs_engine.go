package services

import (
	"time"

	"github.com/alzadjaliaafra-hash/srff-i-rvs-model/backend/internal/models"
)

// RVSEngineImpl is a stub engine that derives simple ratio proxies from the
// RVSv4Input and composes a placeholder viability score. It satisfies the
// RVSEngine interface declared in assessment_service.go.
type RVSEngineImpl struct{}

func NewRVSEngine() *RVSEngineImpl { return &RVSEngineImpl{} }

// Calculate computes a placeholder score and fills in survival curve, stress
// tests, and a recommendation. The arithmetic is intentionally simple and
// must be replaced by the real SRFF-I RVS algorithm before go-live.
func (e *RVSEngineImpl) Calculate(input models.RVSv4Input) (models.RVSv4Output, error) {
	// Derive ratio proxies from the richer RVSv4Input shape.
	equity := input.TotalAssets - input.TotalLiabilities

	var currentRatio, debtEquity, roa, interestCoverage float64
	if input.TotalAssets > 0 {
		currentRatio = 1 + input.WorkingCapital/input.TotalAssets
		roa = input.EBITDA / input.TotalAssets
	}
	if equity > 0 {
		debtEquity = input.TotalDebt / equity
	}
	if input.TotalDebt > 0 {
		interestCoverage = input.EBITDA / input.TotalDebt
	} else {
		interestCoverage = 2.0
	}

	score := (currentRatio*10 + debtEquity*5 + roa*15 + interestCoverage*20) / 50 * 100
	if score > 100 {
		score = 100
	}
	if score < 0 {
		score = 0
	}

	return models.RVSv4Output{
		FinalScore:          score,
		RiskRating:          calculateRating(score),
		RiskBand:            calculateRating(score),
		SurvivalProbability: []float64{0.85, 0.72, 0.65, 0.58, 0.52},
		StressTestResults:   generateStubStressTests(),
		Recommendation:      generateRecommendation(score),
		CalculatedAt:        time.Now(),
		ComponentScores: map[string]float64{
			"currentRatio":     currentRatio,
			"debtEquity":       debtEquity,
			"roa":              roa,
			"interestCoverage": interestCoverage,
		},
	}, nil
}

func calculateRating(score float64) string {
	switch {
	case score >= 80:
		return "AAA"
	case score >= 70:
		return "AA"
	case score >= 60:
		return "A"
	case score >= 50:
		return "BBB"
	case score >= 40:
		return "BB"
	default:
		return "B"
	}
}

func generateStubStressTests() map[string]models.StressTestScenario {
	return map[string]models.StressTestScenario{
		"base":       {Name: "Base Case", ViabilityScore: 65.0, Probability: 0.85},
		"recession":  {Name: "Recession", ViabilityScore: 42.0, Probability: 0.58},
		"recovery":   {Name: "Recovery", ViabilityScore: 78.0, Probability: 0.92},
		"oil_shock":  {Name: "Oil Price Shock", ViabilityScore: 38.0, Probability: 0.52},
		"currency":   {Name: "Currency Crisis", ViabilityScore: 45.0, Probability: 0.61},
		"optimistic": {Name: "Optimistic Growth", ViabilityScore: 82.0, Probability: 0.94},
	}
}

func generateRecommendation(score float64) string {
	switch {
	case score >= 70:
		return "STRONG_BUY"
	case score >= 50:
		return "CONDITIONAL_BUY"
	default:
		return "PASS"
	}
}
