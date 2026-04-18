package models

import "time"

// CreateAssessmentDTO is the payload received on POST /api/v1/assessments.
type CreateAssessmentDTO struct {
	CompanyName string     `json:"companyName"`
	Inputs      RVSv4Input `json:"inputs"`
}

// AssessmentDTO is the response shape returned to clients.
type AssessmentDTO struct {
	ID               string               `json:"id"`
	CompanyName      string               `json:"companyName"`
	Status           string               `json:"status"`
	UserID           string               `json:"userId"`
	Inputs           RVSv4Input           `json:"inputs"`
	Results          *RVSv4Output         `json:"results,omitempty"`
	MurshidiAnalysis *MurshidiAnalysisDTO `json:"murshidiAnalysis,omitempty"`
	CreatedAt        time.Time            `json:"createdAt"`
	UpdatedAt        time.Time            `json:"updatedAt"`
}

// AssessmentMetadata carries ingestion-source tracking info alongside an
// assessment. It is set by handlers and propagated into the repository layer.
type AssessmentMetadata struct {
	Source              string `json:"source"`
	ExternalSystemID    string `json:"externalSystemId,omitempty"`
	ExternalReferenceID string `json:"externalReferenceId,omitempty"`
}
