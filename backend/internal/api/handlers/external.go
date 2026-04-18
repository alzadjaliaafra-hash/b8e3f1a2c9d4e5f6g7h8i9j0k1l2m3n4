package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"

	"github.com/alzadjaliaafra-hash/srff-i-rvs-model/backend/internal/models"
)

// HandleExternalDataIngestion handles POST /api/v1/external/assessments.
// It authenticates via API key, transforms the external payload into the
// internal RVS input shape, validates, and persists as an assessment.
func (h *AssessmentHandler) HandleExternalDataIngestion(w http.ResponseWriter, r *http.Request) {
	apiKey := r.Header.Get("X-API-Key")
	if h.authService == nil || !h.authService.ValidateExternalAPIKey(apiKey) {
		respondWithError(w, http.StatusUnauthorized, "Invalid API key")
		return
	}

	var payload models.ExternalDataPayload
	if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
		respondWithError(w, http.StatusBadRequest, "Invalid JSON payload")
		return
	}

	internalData, err := h.dataTransformer.TransformExternalToInternal(payload)
	if err != nil {
		respondWithError(w, http.StatusUnprocessableEntity, fmt.Sprintf("Data transformation failed: %v", err))
		return
	}

	if err := h.validator.ValidateRVSInput(internalData); err != nil {
		respondWithError(w, http.StatusBadRequest, fmt.Sprintf("Validation failed: %v", err))
		return
	}

	userID, err := h.authService.GetOrCreateExternalSystemUser(apiKey)
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, "User resolution failed")
		return
	}

	dto := models.CreateAssessmentDTO{
		CompanyName: payload.CompanyName,
		Inputs:      internalData,
	}

	meta := models.AssessmentMetadata{
		Source:              "external_api",
		ExternalSystemID:    payload.SystemID,
		ExternalReferenceID: payload.ReferenceID,
	}

	assessment, err := h.assessmentService.CreateAndProcess(r.Context(), userID, dto, meta)
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, fmt.Sprintf("Assessment creation failed: %v", err))
		return
	}

	respondWithJSON(w, http.StatusCreated, assessment)
}
