package services

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"time"

	"github.com/alzadjaliaafra-hash/srff-i-rvs-model/backend/internal/models"
)

// RVSEngineImpl satisfies the RVSEngine interface declared in
// assessment_service.go. It has two modes:
//
//  1. Sidecar mode (PYTHON_RVS_URL is set): POST the RVSv4Input to
//     {PYTHON_RVS_URL}/calculate and decode the response.
//  2. Stub mode (PYTHON_RVS_URL is unset): derive ratio proxies from the
//     RVSv4Input and compose a placeholder score. Used until the Python
//     sidecar around rvs_calculator_enhanced.py is in place.
type RVSEngineImpl struct {
	pythonServiceURL string
	httpClient       *http.Client
}

func NewRVSEngine() *RVSEngineImpl {
	return &RVSEngineImpl{
		pythonServiceURL: os.Getenv("PYTHON_RVS_URL"),
		httpClient:       &http.Client{Timeout: 10 * time.Second},
	}
}

// Calculate dispatches to the Python sidecar when configured; otherwise runs
// the local stub.
func (e *RVSEngineImpl) Calculate(input models.RVSv4Input) (models.RVSv4Output, error) {
	if e.pythonServiceURL != "" {
		return e.calculateViaPython(input)
	}
	return e.calculateStub(input), nil
}

// calculateViaPython shells out to the FastAPI sidecar. The sidecar is
// expected to wrap calculate_enhanced_rvs() from rvs_calculator_enhanced.py
// and return the canonical RVSv4Output JSON shape.
func (e *RVSEngineImpl) calculateViaPython(input models.RVSv4Input) (models.RVSv4Output, error) {
	payload, err := json.Marshal(input)
	if err != nil {
		return models.RVSv4Output{}, fmt.Errorf("marshal input: %w", err)
	}

	resp, err := e.httpClient.Post(
		e.pythonServiceURL+"/calculate",
		"application/json",
		bytes.NewReader(payload),
	)
	if err != nil {
		return models.RVSv4Output{}, fmt.Errorf("python service unreachable: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return models.RVSv4Output{}, fmt.Errorf("python service error %d: %s", resp.StatusCode, string(body))
	}

	var out models.RVSv4Output
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return models.RVSv4Output{}, fmt.Errorf("decode response: %w", err)
	}
	if out.CalculatedAt.IsZero() {
		out.CalculatedAt = time.Now()
	}
	return out, nil
}

// calculateStub composes a placeholder score from the richer RVSv4Input.
// Replace with the real algorithm (or point PYTHON_RVS_URL at the sidecar)
// before any production use.
func (e *RVSEngineImpl) calculateStub(input models.RVSv4Input) models.RVSv4Output {
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
	}
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
