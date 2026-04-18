package handlers

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"strconv"
	"strings"

	"github.com/go-chi/chi/v5"

	"github.com/alzadjaliaafra-hash/srff-i-rvs-model/backend/internal/models"
	"github.com/alzadjaliaafra-hash/srff-i-rvs-model/backend/internal/services"
	"github.com/alzadjaliaafra-hash/srff-i-rvs-model/backend/internal/validators"
)

// AssessmentHandler groups all HTTP handlers related to assessments.
type AssessmentHandler struct {
	assessmentService *services.AssessmentService
	validator         *validators.RVSValidator
	fileProcessor     FileProcessor
	dataTransformer   *services.DataTransformer
	authService       AuthService
	logger            *log.Logger
}

// FileProcessor extracts RVS input data from uploaded spreadsheet files.
type FileProcessor interface {
	ProcessCSV(file interface{}) (models.RVSv4Input, error)
	ProcessExcel(file interface{}) (models.RVSv4Input, error)
}

// AuthService provides identity resolution for API-key based integrations.
type AuthService interface {
	ValidateExternalAPIKey(key string) bool
	GetOrCreateExternalSystemUser(key string) (string, error)
}

// NewAssessmentHandler constructs an AssessmentHandler with its dependencies.
func NewAssessmentHandler(
	svc *services.AssessmentService,
	validator *validators.RVSValidator,
	transformer *services.DataTransformer,
	logger *log.Logger,
) *AssessmentHandler {
	return &AssessmentHandler{
		assessmentService: svc,
		validator:         validator,
		dataTransformer:   transformer,
		logger:            logger,
	}
}

// CreateAssessment handles POST /api/v1/assessments.
func (h *AssessmentHandler) CreateAssessment(w http.ResponseWriter, r *http.Request) {
	userID, ok := r.Context().Value("userID").(string)
	if !ok {
		respondWithError(w, http.StatusUnauthorized, "User not authenticated")
		return
	}

	var createDTO models.CreateAssessmentDTO
	if err := json.NewDecoder(r.Body).Decode(&createDTO); err != nil {
		respondWithError(w, http.StatusBadRequest, "Invalid JSON payload")
		return
	}

	if err := h.validator.ValidateRVSInput(createDTO.Inputs); err != nil {
		respondWithError(w, http.StatusBadRequest, fmt.Sprintf("Validation failed: %v", err))
		return
	}

	if err := h.validateBusinessRules(createDTO.Inputs); err != nil {
		respondWithError(w, http.StatusUnprocessableEntity, err.Error())
		return
	}

	assessment, err := h.assessmentService.CreateAndProcess(r.Context(), userID, createDTO, models.AssessmentMetadata{Source: "manual"})
	if err != nil {
		h.logger.Printf("Assessment creation failed for user %s: %v", userID, err)
		respondWithError(w, http.StatusInternalServerError, "Failed to create assessment")
		return
	}

	respondWithJSON(w, http.StatusCreated, assessment)
}

// validateBusinessRules enforces domain-specific sanity checks on the input.
func (h *AssessmentHandler) validateBusinessRules(input models.RVSv4Input) error {
	if input.TotalAssets <= 0 {
		return fmt.Errorf("total assets must be greater than zero")
	}
	if input.TotalLiabilities > input.TotalAssets*2 {
		return fmt.Errorf("total liabilities exceed 200%% of total assets - data may be incorrect")
	}
	if input.Revenue <= 0 {
		return fmt.Errorf("revenue must be greater than zero")
	}
	if input.WorkingCapital < -input.TotalAssets*0.5 {
		h.logger.Printf("Warning: Working capital is severely negative (< -50%% of assets)")
	}
	if input.CollateralValue > input.TotalAssets*1.2 {
		return fmt.Errorf("collateral value exceeds 120%% of total assets - verify appraisal")
	}
	if input.RPTRevenuePercent < 0 || input.RPTRevenuePercent > 100 {
		return fmt.Errorf("RPT revenue percentage must be between 0 and 100")
	}
	if input.RPTCostPercent < 0 || input.RPTCostPercent > 100 {
		return fmt.Errorf("RPT cost percentage must be between 0 and 100")
	}
	if input.InformationAsymmetryPercent < 0 || input.InformationAsymmetryPercent > 20 {
		return fmt.Errorf("information asymmetry percentage must be between 0 and 20")
	}
	if input.GovernanceScore < 0 || input.GovernanceScore > 100 {
		return fmt.Errorf("governance score must be between 0 and 100")
	}
	if input.ConcentrationScore < 0 || input.ConcentrationScore > 100 {
		return fmt.Errorf("concentration score must be between 0 and 100")
	}
	return nil
}

// GetAssessments handles GET /api/v1/assessments (paginated list).
func (h *AssessmentHandler) GetAssessments(w http.ResponseWriter, r *http.Request) {
	userID := r.Context().Value("userID").(string)

	page, _ := strconv.Atoi(r.URL.Query().Get("page"))
	pageSize, _ := strconv.Atoi(r.URL.Query().Get("pageSize"))
	if page < 1 {
		page = 1
	}
	if pageSize < 1 || pageSize > 100 {
		pageSize = 20
	}
	offset := (page - 1) * pageSize

	assessments, err := h.assessmentService.GetByUserID(r.Context(), userID, pageSize, offset)
	if err != nil {
		h.logger.Printf("Failed to retrieve assessments for user %s: %v", userID, err)
		respondWithError(w, http.StatusInternalServerError, "Failed to retrieve assessments")
		return
	}

	totalCount, err := h.assessmentService.CountByUserID(r.Context(), userID)
	if err != nil {
		h.logger.Printf("Failed to count assessments for user %s: %v", userID, err)
		totalCount = 0
	}

	dtos := make([]models.AssessmentDTO, len(assessments))
	for i, a := range assessments {
		dtos[i] = *h.assessmentService.ToDTO(a)
	}

	respondWithJSON(w, http.StatusOK, map[string]interface{}{
		"data":       dtos,
		"total":      totalCount,
		"page":       page,
		"pageSize":   pageSize,
		"totalPages": (totalCount + pageSize - 1) / pageSize,
	})
}

// GetAssessmentByID handles GET /api/v1/assessments/{id}.
func (h *AssessmentHandler) GetAssessmentByID(w http.ResponseWriter, r *http.Request) {
	userID := r.Context().Value("userID").(string)
	id := chi.URLParam(r, "id")

	assessment, err := h.assessmentService.GetByID(r.Context(), id)
	if err != nil {
		h.logger.Printf("Assessment %s not found: %v", id, err)
		respondWithError(w, http.StatusNotFound, "Assessment not found")
		return
	}

	if assessment.UserID != userID {
		h.logger.Printf("User %s attempted to access assessment %s owned by %s", userID, id, assessment.UserID)
		respondWithError(w, http.StatusForbidden, "Access denied")
		return
	}

	respondWithJSON(w, http.StatusOK, h.assessmentService.ToDTO(assessment))
}

// UpdateAssessment handles PUT /api/v1/assessments/{id}. Stub implementation.
func (h *AssessmentHandler) UpdateAssessment(w http.ResponseWriter, r *http.Request) {
	respondWithError(w, http.StatusNotImplemented, "Update not yet implemented")
}

// DeleteAssessment handles DELETE /api/v1/assessments/{id}.
func (h *AssessmentHandler) DeleteAssessment(w http.ResponseWriter, r *http.Request) {
	userID := r.Context().Value("userID").(string)
	id := chi.URLParam(r, "id")

	assessment, err := h.assessmentService.GetByID(r.Context(), id)
	if err != nil {
		respondWithError(w, http.StatusNotFound, "Assessment not found")
		return
	}

	if assessment.UserID != userID {
		respondWithError(w, http.StatusForbidden, "Access denied")
		return
	}

	if err := h.assessmentService.Delete(r.Context(), id); err != nil {
		h.logger.Printf("Failed to delete assessment %s: %v", id, err)
		respondWithError(w, http.StatusInternalServerError, "Failed to delete assessment")
		return
	}

	respondWithJSON(w, http.StatusOK, map[string]string{"message": "Assessment deleted successfully"})
}

// HandleFileUpload handles POST /api/v1/assessments/upload.
func (h *AssessmentHandler) HandleFileUpload(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseMultipartForm(10 << 20); err != nil {
		respondWithError(w, http.StatusBadRequest, "File too large or invalid format")
		return
	}

	file, header, err := r.FormFile("financialData")
	if err != nil {
		respondWithError(w, http.StatusBadRequest, "No file uploaded")
		return
	}
	defer file.Close()

	if !isValidFileType(header.Filename) {
		respondWithError(w, http.StatusBadRequest, "Invalid file type")
		return
	}

	var extracted models.RVSv4Input
	if strings.HasSuffix(strings.ToLower(header.Filename), ".csv") {
		extracted, err = h.fileProcessor.ProcessCSV(file)
	} else {
		extracted, err = h.fileProcessor.ProcessExcel(file)
	}
	if err != nil {
		respondWithError(w, http.StatusUnprocessableEntity, fmt.Sprintf("Failed to extract data: %v", err))
		return
	}

	if err := h.validator.ValidateRVSInput(extracted); err != nil {
		respondWithError(w, http.StatusBadRequest, fmt.Sprintf("Invalid financial data: %v", err))
		return
	}

	respondWithJSON(w, http.StatusOK, map[string]interface{}{
		"extractedData": extracted,
		"message":       "Data extracted successfully. Please review before submission.",
	})
}

// GenerateReport handles GET /api/v1/assessments/{id}/report. Stub.
func (h *AssessmentHandler) GenerateReport(w http.ResponseWriter, r *http.Request) {
	respondWithError(w, http.StatusNotImplemented, "Report generation not yet implemented")
}

// Recalculate handles POST /api/v1/assessments/{id}/recalculate. Stub.
func (h *AssessmentHandler) Recalculate(w http.ResponseWriter, r *http.Request) {
	respondWithError(w, http.StatusNotImplemented, "Recalculate not yet implemented")
}
