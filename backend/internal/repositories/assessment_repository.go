package repositories

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/alzadjaliaafra-hash/srff-i-rvs-model/backend/internal/models"
)

// PostgresAssessmentRepository persists assessments to PostgreSQL using pgx.
type PostgresAssessmentRepository struct {
	db *pgxpool.Pool
}

func NewPostgresAssessmentRepository(db *pgxpool.Pool) *PostgresAssessmentRepository {
	return &PostgresAssessmentRepository{db: db}
}

func (r *PostgresAssessmentRepository) CreateWithTx(ctx context.Context, tx pgx.Tx, a *models.Assessment) error {
	const q = `
		INSERT INTO assessments (
			id, company_name, status, user_id, inputs,
			results, murshidi_analysis, source, external_system_id,
			external_reference_id, created_at, updated_at
		) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)`

	inputsJSON, err := json.Marshal(a.Inputs)
	if err != nil {
		return fmt.Errorf("failed to marshal inputs: %w", err)
	}

	var resultsJSON, analysisJSON []byte
	if a.Results != nil {
		if resultsJSON, err = json.Marshal(a.Results); err != nil {
			return fmt.Errorf("failed to marshal results: %w", err)
		}
	}
	if a.MurshidiAnalysis != nil {
		if analysisJSON, err = json.Marshal(a.MurshidiAnalysis); err != nil {
			return fmt.Errorf("failed to marshal analysis: %w", err)
		}
	}

	_, err = tx.Exec(ctx, q,
		a.ID, a.CompanyName, a.Status, a.UserID, inputsJSON,
		resultsJSON, analysisJSON, a.Source, a.ExternalSystemID,
		a.ExternalReferenceID, a.CreatedAt, a.UpdatedAt,
	)
	if err != nil {
		return fmt.Errorf("failed to insert assessment: %w", err)
	}
	return nil
}

func (r *PostgresAssessmentRepository) UpdateWithTx(ctx context.Context, tx pgx.Tx, a *models.Assessment) error {
	const q = `
		UPDATE assessments
		SET company_name = $2,
			status = $3,
			inputs = $4,
			results = $5,
			murshidi_analysis = $6,
			updated_at = $7
		WHERE id = $1`

	inputsJSON, _ := json.Marshal(a.Inputs)
	resultsJSON, _ := json.Marshal(a.Results)
	analysisJSON, _ := json.Marshal(a.MurshidiAnalysis)

	_, err := tx.Exec(ctx, q, a.ID, a.CompanyName, a.Status, inputsJSON, resultsJSON, analysisJSON, a.UpdatedAt)
	return err
}

func (r *PostgresAssessmentRepository) UpdateStatusWithTx(ctx context.Context, tx pgx.Tx, id, status string) error {
	const q = `UPDATE assessments SET status = $2, updated_at = $3 WHERE id = $1`
	_, err := tx.Exec(ctx, q, id, status, time.Now())
	return err
}

func (r *PostgresAssessmentRepository) FindByID(ctx context.Context, id string) (*models.Assessment, error) {
	const q = `
		SELECT id, company_name, status, user_id, inputs, results,
			murshidi_analysis, source, external_system_id, external_reference_id,
			created_at, updated_at
		FROM assessments
		WHERE id = $1`

	var a models.Assessment
	var inputsJSON, resultsJSON, analysisJSON []byte

	err := r.db.QueryRow(ctx, q, id).Scan(
		&a.ID, &a.CompanyName, &a.Status, &a.UserID, &inputsJSON,
		&resultsJSON, &analysisJSON, &a.Source, &a.ExternalSystemID,
		&a.ExternalReferenceID, &a.CreatedAt, &a.UpdatedAt,
	)
	if err != nil {
		if err == pgx.ErrNoRows {
			return nil, fmt.Errorf("assessment not found")
		}
		return nil, err
	}

	if err := json.Unmarshal(inputsJSON, &a.Inputs); err != nil {
		return nil, fmt.Errorf("failed to unmarshal inputs: %w", err)
	}
	if resultsJSON != nil {
		var results models.RVSv4Output
		if err := json.Unmarshal(resultsJSON, &results); err != nil {
			return nil, fmt.Errorf("failed to unmarshal results: %w", err)
		}
		a.Results = &results
	}
	if analysisJSON != nil {
		var analysis models.MurshidiAnalysisDTO
		if err := json.Unmarshal(analysisJSON, &analysis); err != nil {
			return nil, fmt.Errorf("failed to unmarshal analysis: %w", err)
		}
		a.MurshidiAnalysis = &analysis
	}
	return &a, nil
}

func (r *PostgresAssessmentRepository) FindByUserID(ctx context.Context, userID string, limit, offset int) ([]*models.Assessment, error) {
	const q = `
		SELECT id, company_name, status, user_id, inputs, results,
			murshidi_analysis, source, external_system_id, external_reference_id,
			created_at, updated_at
		FROM assessments
		WHERE user_id = $1
		ORDER BY created_at DESC
		LIMIT $2 OFFSET $3`

	rows, err := r.db.Query(ctx, q, userID, limit, offset)
	if err != nil {
		return nil, fmt.Errorf("failed to query assessments: %w", err)
	}
	defer rows.Close()

	var out []*models.Assessment
	for rows.Next() {
		var a models.Assessment
		var inputsJSON, resultsJSON, analysisJSON []byte

		if err := rows.Scan(
			&a.ID, &a.CompanyName, &a.Status, &a.UserID, &inputsJSON,
			&resultsJSON, &analysisJSON, &a.Source, &a.ExternalSystemID,
			&a.ExternalReferenceID, &a.CreatedAt, &a.UpdatedAt,
		); err != nil {
			return nil, fmt.Errorf("failed to scan row: %w", err)
		}

		_ = json.Unmarshal(inputsJSON, &a.Inputs)
		if resultsJSON != nil {
			var results models.RVSv4Output
			_ = json.Unmarshal(resultsJSON, &results)
			a.Results = &results
		}
		if analysisJSON != nil {
			var analysis models.MurshidiAnalysisDTO
			_ = json.Unmarshal(analysisJSON, &analysis)
			a.MurshidiAnalysis = &analysis
		}
		out = append(out, &a)
	}
	return out, nil
}

func (r *PostgresAssessmentRepository) CountByUserID(ctx context.Context, userID string) (int, error) {
	const q = `SELECT COUNT(*) FROM assessments WHERE user_id = $1`
	var n int
	err := r.db.QueryRow(ctx, q, userID).Scan(&n)
	return n, err
}

func (r *PostgresAssessmentRepository) Delete(ctx context.Context, id string) error {
	const q = `DELETE FROM assessments WHERE id = $1`
	_, err := r.db.Exec(ctx, q, id)
	return err
}
