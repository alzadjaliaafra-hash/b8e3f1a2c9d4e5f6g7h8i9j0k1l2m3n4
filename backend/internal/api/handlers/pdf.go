package handlers

import (
	"fmt"
	"net/http"

	"github.com/go-chi/chi/v5"

	"github.com/alzadjaliaafra-hash/srff-i-rvs-model/backend/internal/services"
)

// PDFHandler renders an Investment Committee memo for an assessment.
type PDFHandler struct {
	assessmentService *services.AssessmentService
	pdfGenerator      *services.PDFGenerator
}

func NewPDFHandler(svc *services.AssessmentService, gen *services.PDFGenerator) *PDFHandler {
	return &PDFHandler{assessmentService: svc, pdfGenerator: gen}
}

// ExportPDF handles GET /api/v1/assessments/{id}/export-pdf.
func (h *PDFHandler) ExportPDF(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")

	assessment, err := h.assessmentService.GetByID(r.Context(), id)
	if err != nil {
		respondWithError(w, http.StatusNotFound, "Assessment not found")
		return
	}

	pdfBytes, err := h.pdfGenerator.GenerateICMemo(assessment)
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, "Failed to generate PDF")
		return
	}

	w.Header().Set("Content-Type", "application/pdf")
	w.Header().Set(
		"Content-Disposition",
		fmt.Sprintf("attachment; filename=\"%s-viability-report.pdf\"", assessment.CompanyName),
	)
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(pdfBytes)
}
