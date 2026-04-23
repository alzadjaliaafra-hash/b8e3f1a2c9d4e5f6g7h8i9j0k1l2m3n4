package services

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/alzadjaliaafra-hash/srff-i-rvs-model/backend/internal/models"
)

// AssessmentRepository is the persistence abstraction used by the service.
type AssessmentRepository interface {
	CreateWithTx(ctx context.Context, tx pgx.Tx, assessment *models.Assessment) error
	UpdateWithTx(ctx context.Context, tx pgx.Tx, assessment *models.Assessment) error
	UpdateStatusWithTx(ctx context.Context, tx pgx.Tx, id string, status string) error
	FindByID(ctx context.Context, id string) (*models.Assessment, error)
	FindByUserID(ctx context.Context, userID string, limit, offset int) ([]*models.Assessment, error)
	CountByUserID(ctx context.Context, userID string) (int, error)
	Delete(ctx context.Context, id string) error
}

// RVSEngine computes the quantitative RVS output from input features.
type RVSEngine interface {
	Calculate(input models.RVSv4Input) (models.RVSv4Output, error)
}

// MurshidiClient fetches qualitative AI diagnoses.
type MurshidiClient interface {
	GetDiagnosis(ctx context.Context, req MurshidiRequest) (models.MurshidiAnalysisDTO, error)
}

// MurshidiRequest is the payload sent to the Murshidi AI service.
type MurshidiRequest struct {
	CompanyName string
	RVSInputs   models.RVSv4Input
	RVSOutputs  models.RVSv4Output
}

// AssessmentService orchestrates the full create-and-process flow.
type AssessmentService struct {
	repo           AssessmentRepository
	rvsEngine      RVSEngine
	murshidiClient MurshidiClient
	db             *pgxpool.Pool
	logger         *log.Logger
}

func NewAssessmentService(
	repo AssessmentRepository,
	rvsEngine RVSEngine,
	murshidiClient MurshidiClient,
	db *pgxpool.Pool,
	logger *log.Logger,
) *AssessmentService {
	return &AssessmentService{
		repo:           repo,
		rvsEngine:      rvsEngine,
		murshidiClient: murshidiClient,
		db:             db,
		logger:         logger,
	}
}

// CreateAndProcess runs the full assessment pipeline in a single transaction:
// create initial record, compute RVS, fetch Murshidi analysis, persist, return.
func (s *AssessmentService) CreateAndProcess(
	ctx context.Context,
	userID string,
	dto models.CreateAssessmentDTO,
	meta models.AssessmentMetadata,
) (*models.AssessmentDTO, error) {
	tx, err := s.db.Begin(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback(ctx)

	assessmentID := uuid.New().String()
	initial := &models.Assessment{
		ID:                  assessmentID,
		CompanyName:         dto.CompanyName,
		Status:              "processing",
		UserID:              userID,
		Inputs:              dto.Inputs,
		Source:              meta.Source,
		ExternalSystemID:    meta.ExternalSystemID,
		ExternalReferenceID: meta.ExternalReferenceID,
		CreatedAt:           time.Now(),
		UpdatedAt:           time.Now(),
	}

	if err := s.repo.CreateWithTx(ctx, tx, initial); err != nil {
		return nil, fmt.Errorf("failed to create initial assessment: %w", err)
	}

	s.logger.Printf("Created assessment %s for user %s, company %s", assessmentID, userID, dto.CompanyName)

	output, err := s.rvsEngine.Calculate(dto.Inputs)
	if err != nil {
		_ = s.repo.UpdateStatusWithTx(ctx, tx, assessmentID, "failed")
		_ = tx.Commit(ctx)
		return nil, fmt.Errorf("RVS calculation failed: %w", err)
	}

	s.logger.Printf("RVS calculation completed for assessment %s. Score: %.2f", assessmentID, output.FinalScore)

	analysis, err := s.murshidiClient.GetDiagnosis(ctx, MurshidiRequest{
		CompanyName: dto.CompanyName,
		RVSInputs:   dto.Inputs,
		RVSOutputs:  output,
	})
	if err != nil {
		s.logger.Printf("Murshidi analysis failed for assessment %s: %v", assessmentID, err)
		analysis = s.generateFallbackAnalysis(output)
	}

	complete := &models.Assessment{
		ID:                  assessmentID,
		CompanyName:         dto.CompanyName,
		Status:              "completed",
		UserID:              userID,
		Inputs:              dto.Inputs,
		Results:             &output,
		MurshidiAnalysis:    &analysis,
		Source:              meta.Source,
		ExternalSystemID:    meta.ExternalSystemID,
		ExternalReferenceID: meta.ExternalReferenceID,
		CreatedAt:           initial.CreatedAt,
		UpdatedAt:           time.Now(),
	}

	if err := s.repo.UpdateWithTx(ctx, tx, complete); err != nil {
		return nil, fmt.Errorf("failed to update assessment with results: %w", err)
	}

	if err := tx.Commit(ctx); err != nil {
		return nil, fmt.Errorf("failed to commit transaction: %w", err)
	}

	s.logger.Printf("Assessment %s completed successfully", assessmentID)
	return s.ToDTO(complete), nil
}

// GetByID retrieves a single assessment by ID.
func (s *AssessmentService) GetByID(ctx context.Context, id string) (*models.Assessment, error) {
	return s.repo.FindByID(ctx, id)
}

// GetByUserID retrieves a paginated list of assessments for a user.
func (s *AssessmentService) GetByUserID(ctx context.Context, userID string, limit, offset int) ([]*models.Assessment, error) {
	return s.repo.FindByUserID(ctx, userID, limit, offset)
}

// CountByUserID returns the total number of assessments for a user.
func (s *AssessmentService) CountByUserID(ctx context.Context, userID string) (int, error) {
	return s.repo.CountByUserID(ctx, userID)
}

// Delete removes an assessment.
func (s *AssessmentService) Delete(ctx context.Context, id string) error {
	return s.repo.Delete(ctx, id)
}

// ToDTO converts the domain model into its API-facing DTO shape.
func (s *AssessmentService) ToDTO(a *models.Assessment) *models.AssessmentDTO {
	return &models.AssessmentDTO{
		ID:               a.ID,
		CompanyName:      a.CompanyName,
		Status:           a.Status,
		UserID:           a.UserID,
		Inputs:           a.Inputs,
		Results:          a.Results,
		MurshidiAnalysis: a.MurshidiAnalysis,
		CreatedAt:        a.CreatedAt,
		UpdatedAt:        a.UpdatedAt,
	}
}

// generateFallbackAnalysis is used when the Murshidi client is unavailable.
func (s *AssessmentService) generateFallbackAnalysis(output models.RVSv4Output) models.MurshidiAnalysisDTO {
	var pattern, structure, revealed string

	switch {
	case output.FinalScore >= 70:
		pattern = "Strong financial position with healthy rescue viability indicators."
		structure = "The company demonstrates solid fundamentals across liquidity, profitability, and leverage metrics."
		revealed = "Recommend proceeding with rescue financing. Monitor ongoing performance."
	case output.FinalScore >= 50:
		pattern = "Moderate financial position with mixed rescue viability signals."
		structure = "Some strengths are offset by areas of concern requiring attention."
		revealed = "Conditional recommendation. Require detailed turnaround plan and monitoring."
	default:
		pattern = "Weak financial position with significant rescue viability challenges."
		structure = "Multiple risk factors indicate structural financial difficulties."
		revealed = "High-risk scenario. Recommend enhanced due diligence before proceeding."
	}

	return models.MurshidiAnalysisDTO{Pattern: pattern, Structure: structure, RevealedValue: revealed}
}
