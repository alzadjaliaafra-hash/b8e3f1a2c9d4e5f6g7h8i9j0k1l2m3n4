package services

import (
	"bytes"
	"fmt"
	"sort"
	"time"

	"github.com/jung-kurt/gofpdf"

	"github.com/alzadjaliaafra-hash/srff-i-rvs-model/backend/internal/models"
)

// PDFGenerator renders an Investment Committee memo from an Assessment.
type PDFGenerator struct {
	logoPath string
}

func NewPDFGenerator(logoPath string) *PDFGenerator {
	return &PDFGenerator{logoPath: logoPath}
}

// GenerateICMemo renders the complete memo and returns the PDF bytes.
func (g *PDFGenerator) GenerateICMemo(assessment *models.Assessment) ([]byte, error) {
	if assessment == nil {
		return nil, fmt.Errorf("assessment is nil")
	}

	pdf := gofpdf.New("P", "mm", "A4", "")
	pdf.AddPage()

	g.addHeader(pdf)
	g.addExecutiveSummary(pdf, assessment)
	g.addFinancialMetrics(pdf, assessment)
	g.addViabilityScore(pdf, assessment)
	g.addSurvivalCurve(pdf, assessment)
	g.addStressTests(pdf, assessment)
	g.addRecommendation(pdf, assessment)
	g.addFooter(pdf)

	var buf bytes.Buffer
	if err := pdf.Output(&buf); err != nil {
		return nil, err
	}
	return buf.Bytes(), nil
}

func (g *PDFGenerator) addHeader(pdf *gofpdf.Fpdf) {
	if g.logoPath != "" {
		pdf.ImageOptions(g.logoPath, 15, 10, 25, 0, false, gofpdf.ImageOptions{}, 0, "")
	}

	pdf.SetFont("Arial", "B", 20)
	pdf.SetTextColor(184, 134, 11)
	pdf.CellFormat(0, 15, "INVESTMENT COMMITTEE MEMO", "", 1, "C", false, 0, "")

	pdf.SetFont("Arial", "", 10)
	pdf.SetTextColor(0, 0, 0)
	pdf.CellFormat(0, 5, "Rescue Viability Assessment", "", 1, "C", false, 0, "")
	pdf.Ln(5)
}

func (g *PDFGenerator) addExecutiveSummary(pdf *gofpdf.Fpdf, a *models.Assessment) {
	pdf.SetFont("Arial", "B", 14)
	pdf.SetTextColor(26, 42, 64)
	pdf.CellFormat(0, 8, "EXECUTIVE SUMMARY", "", 1, "L", false, 0, "")
	pdf.Ln(2)

	pdf.SetFont("Arial", "", 11)
	pdf.SetTextColor(0, 0, 0)

	pdf.CellFormat(50, 6, "Company Name:", "", 0, "L", false, 0, "")
	pdf.SetFont("Arial", "B", 11)
	pdf.CellFormat(0, 6, a.CompanyName, "", 1, "L", false, 0, "")

	pdf.SetFont("Arial", "", 11)
	pdf.CellFormat(50, 6, "Assessment Date:", "", 0, "L", false, 0, "")
	pdf.CellFormat(0, 6, a.CreatedAt.Format("02 Jan 2006"), "", 1, "L", false, 0, "")

	pdf.CellFormat(50, 6, "Analyst:", "", 0, "L", false, 0, "")
	pdf.CellFormat(0, 6, a.UserID, "", 1, "L", false, 0, "")

	pdf.Ln(5)
}

func (g *PDFGenerator) addFinancialMetrics(pdf *gofpdf.Fpdf, a *models.Assessment) {
	pdf.SetFont("Arial", "B", 14)
	pdf.SetTextColor(26, 42, 64)
	pdf.CellFormat(0, 8, "CORE FINANCIAL METRICS", "", 1, "L", false, 0, "")
	pdf.Ln(2)

	pdf.SetFont("Arial", "B", 10)
	pdf.SetFillColor(240, 240, 240)
	pdf.CellFormat(95, 7, "Metric", "1", 0, "L", true, 0, "")
	pdf.CellFormat(95, 7, "Value", "1", 1, "C", true, 0, "")

	pdf.SetFont("Arial", "", 10)

	in := a.Inputs
	var ebitdaMargin float64
	if in.Revenue > 0 {
		ebitdaMargin = in.EBITDA / in.Revenue * 100
	}

	metrics := []struct{ name, value string }{
		{"Total Assets", fmt.Sprintf("RO %.0f", in.TotalAssets)},
		{"Total Liabilities", fmt.Sprintf("RO %.0f", in.TotalLiabilities)},
		{"Revenue", fmt.Sprintf("RO %.0f", in.Revenue)},
		{"EBITDA", fmt.Sprintf("RO %.0f", in.EBITDA)},
		{"EBITDA Margin", fmt.Sprintf("%.2f%%", ebitdaMargin)},
		{"Working Capital", fmt.Sprintf("RO %.0f", in.WorkingCapital)},
		{"Total Debt", fmt.Sprintf("RO %.0f", in.TotalDebt)},
		{"Collateral Value", fmt.Sprintf("RO %.0f", in.CollateralValue)},
		{"Operating Cash Flow", fmt.Sprintf("RO %.0f", in.OperatingCashFlow)},
	}

	for _, m := range metrics {
		pdf.CellFormat(95, 6, m.name, "1", 0, "L", false, 0, "")
		pdf.CellFormat(95, 6, m.value, "1", 1, "C", false, 0, "")
	}

	pdf.Ln(5)
}

func (g *PDFGenerator) addViabilityScore(pdf *gofpdf.Fpdf, a *models.Assessment) {
	pdf.SetFont("Arial", "B", 14)
	pdf.SetTextColor(26, 42, 64)
	pdf.CellFormat(0, 8, "VIABILITY ASSESSMENT", "", 1, "L", false, 0, "")
	pdf.Ln(2)

	out := a.Results
	if out == nil {
		pdf.SetFont("Arial", "I", 11)
		pdf.SetTextColor(0, 0, 0)
		pdf.CellFormat(0, 6, "Results not yet available for this assessment.", "", 1, "C", false, 0, "")
		pdf.Ln(5)
		return
	}

	pdf.SetFont("Arial", "B", 36)
	c := g.getScoreColor(out.FinalScore)
	pdf.SetTextColor(c[0], c[1], c[2])
	pdf.CellFormat(0, 15, fmt.Sprintf("%.1f / 100", out.FinalScore), "", 1, "C", false, 0, "")

	pdf.SetFont("Arial", "", 12)
	pdf.SetTextColor(0, 0, 0)
	rating := out.RiskRating
	if rating == "" {
		rating = out.RiskBand
	}
	pdf.CellFormat(0, 6, fmt.Sprintf("Risk Rating: %s", rating), "", 1, "C", false, 0, "")

	pdf.Ln(5)
}

func (g *PDFGenerator) addSurvivalCurve(pdf *gofpdf.Fpdf, a *models.Assessment) {
	if a.Results == nil || len(a.Results.SurvivalProbability) == 0 {
		return
	}

	pdf.SetFont("Arial", "B", 14)
	pdf.SetTextColor(26, 42, 64)
	pdf.CellFormat(0, 8, "5-YEAR SURVIVAL PROBABILITY", "", 1, "L", false, 0, "")
	pdf.Ln(2)

	pdf.SetFont("Arial", "", 10)
	pdf.SetTextColor(0, 0, 0)
	for i, prob := range a.Results.SurvivalProbability {
		pdf.CellFormat(40, 6, fmt.Sprintf("Year %d:", i+1), "", 0, "L", false, 0, "")
		pdf.CellFormat(0, 6, fmt.Sprintf("%.1f%%", prob*100), "", 1, "L", false, 0, "")
	}
	pdf.Ln(5)
}

func (g *PDFGenerator) addStressTests(pdf *gofpdf.Fpdf, a *models.Assessment) {
	if a.Results == nil || len(a.Results.StressTestResults) == 0 {
		return
	}

	pdf.SetFont("Arial", "B", 14)
	pdf.SetTextColor(26, 42, 64)
	pdf.CellFormat(0, 8, "STRESS TEST SCENARIOS", "", 1, "L", false, 0, "")
	pdf.Ln(2)

	pdf.SetFont("Arial", "B", 10)
	pdf.SetFillColor(240, 240, 240)
	pdf.CellFormat(70, 7, "Scenario", "1", 0, "L", true, 0, "")
	pdf.CellFormat(60, 7, "Viability Score", "1", 0, "C", true, 0, "")
	pdf.CellFormat(60, 7, "Survival Probability", "1", 1, "C", true, 0, "")

	pdf.SetFont("Arial", "", 10)

	keys := make([]string, 0, len(a.Results.StressTestResults))
	for k := range a.Results.StressTestResults {
		keys = append(keys, k)
	}
	sort.Strings(keys)

	for _, k := range keys {
		s := a.Results.StressTestResults[k]
		pdf.CellFormat(70, 6, s.Name, "1", 0, "L", false, 0, "")
		pdf.CellFormat(60, 6, fmt.Sprintf("%.1f", s.ViabilityScore), "1", 0, "C", false, 0, "")
		pdf.CellFormat(60, 6, fmt.Sprintf("%.1f%%", s.Probability*100), "1", 1, "C", false, 0, "")
	}

	pdf.Ln(5)
}

func (g *PDFGenerator) addRecommendation(pdf *gofpdf.Fpdf, a *models.Assessment) {
	if a.Results == nil || a.Results.Recommendation == "" {
		return
	}

	pdf.SetFont("Arial", "B", 14)
	pdf.SetTextColor(26, 42, 64)
	pdf.CellFormat(0, 8, "INVESTMENT RECOMMENDATION", "", 1, "L", false, 0, "")
	pdf.Ln(2)

	pdf.SetFont("Arial", "B", 18)
	c := g.getRecommendationColor(a.Results.Recommendation)
	pdf.SetTextColor(c[0], c[1], c[2])
	pdf.CellFormat(0, 10, a.Results.Recommendation, "", 1, "C", false, 0, "")
	pdf.Ln(3)
}

func (g *PDFGenerator) addFooter(pdf *gofpdf.Fpdf) {
	pdf.SetY(-20)
	pdf.SetFont("Arial", "I", 8)
	pdf.SetTextColor(128, 128, 128)
	pdf.CellFormat(0, 5, "Powered by Murshidi AI", "", 1, "C", false, 0, "")
	pdf.CellFormat(0, 5, fmt.Sprintf("Generated: %s", time.Now().Format("02 Jan 2006 15:04 MST")), "", 1, "C", false, 0, "")
	pdf.CellFormat(0, 5, "Confidential - For Professional Investors Only", "", 0, "C", false, 0, "")
}

func (g *PDFGenerator) getScoreColor(score float64) [3]int {
	switch {
	case score >= 70:
		return [3]int{0, 128, 0}
	case score >= 50:
		return [3]int{255, 165, 0}
	default:
		return [3]int{255, 0, 0}
	}
}

func (g *PDFGenerator) getRecommendationColor(rec string) [3]int {
	switch rec {
	case "STRONG_BUY":
		return [3]int{0, 128, 0}
	case "CONDITIONAL_BUY":
		return [3]int{255, 165, 0}
	default:
		return [3]int{255, 0, 0}
	}
}
