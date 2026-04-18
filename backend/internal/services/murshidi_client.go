package services

import (
	"context"
	"errors"

	"github.com/alzadjaliaafra-hash/srff-i-rvs-model/backend/internal/models"
)

// NoopMurshidiClient is a stand-in for the real Murshidi AI client. It always
// returns an error, which causes AssessmentService.CreateAndProcess to fall
// back to its built-in heuristic analysis.
type NoopMurshidiClient struct{}

func NewNoopMurshidiClient() *NoopMurshidiClient { return &NoopMurshidiClient{} }

func (NoopMurshidiClient) GetDiagnosis(_ context.Context, _ MurshidiRequest) (models.MurshidiAnalysisDTO, error) {
	return models.MurshidiAnalysisDTO{}, errors.New("murshidi client not configured")
}
