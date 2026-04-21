package services

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"strings"

	"github.com/anthropics/anthropic-sdk-go"
	"github.com/anthropics/anthropic-sdk-go/option"

	"github.com/alzadjaliaafra-hash/srff-i-rvs-model/backend/internal/models"
)

const defaultMurshidiModel = "claude-opus-4-7"

// ClaudeMurshidiClient is an Anthropic-backed implementation of MurshidiClient.
// Any error (SDK, auth, parse) bubbles up to AssessmentService, which then
// falls back to its built-in heuristic analysis.
type ClaudeMurshidiClient struct {
	client anthropic.Client
	model  string
}

func NewClaudeMurshidiClient() (*ClaudeMurshidiClient, error) {
	apiKey := os.Getenv("ANTHROPIC_API_KEY")
	if apiKey == "" {
		return nil, fmt.Errorf("ANTHROPIC_API_KEY is not set")
	}
	model := os.Getenv("MURSHIDI_MODEL")
	if model == "" {
		model = defaultMurshidiModel
	}
	return &ClaudeMurshidiClient{
		client: anthropic.NewClient(option.WithAPIKey(apiKey)),
		model:  model,
	}, nil
}

func (c *ClaudeMurshidiClient) Model() string { return c.model }

const murshidiSystemPrompt = `You are Murshidi, an AI investment analyst supporting SRFF-I's Rescue Viability Score (RVS) model. ` +
	`Given the quantitative assessment inputs and outputs for an Oman-based SME seeking rescue financing, ` +
	`produce a qualitative three-part diagnosis.

Return ONLY a JSON object with exactly three string fields, no other text, no code fences:
{
  "pattern": "What the numbers say — the observable financial trajectory and the most salient metrics.",
  "structure": "What underlies the pattern — root causes, governance, market position, operational posture.",
  "revealedValue": "Investment recommendation — is this a rescue-worthy business and why, with specific conditions."
}

Each field should be 2–4 sentences, specific to the data provided. Do not fabricate data.`

func (c *ClaudeMurshidiClient) GetDiagnosis(ctx context.Context, req MurshidiRequest) (models.MurshidiAnalysisDTO, error) {
	inputsJSON, err := json.MarshalIndent(req.RVSInputs, "", "  ")
	if err != nil {
		return models.MurshidiAnalysisDTO{}, fmt.Errorf("marshal RVS inputs: %w", err)
	}
	outputsJSON, err := json.MarshalIndent(req.RVSOutputs, "", "  ")
	if err != nil {
		return models.MurshidiAnalysisDTO{}, fmt.Errorf("marshal RVS outputs: %w", err)
	}

	userMsg := fmt.Sprintf(
		"Company: %s\n\nRVS Inputs:\n%s\n\nRVS Outputs:\n%s",
		req.CompanyName, string(inputsJSON), string(outputsJSON),
	)

	resp, err := c.client.Messages.New(ctx, anthropic.MessageNewParams{
		Model:     anthropic.Model(c.model),
		MaxTokens: 1024,
		System: []anthropic.TextBlockParam{
			{Text: murshidiSystemPrompt},
		},
		Messages: []anthropic.MessageParam{
			anthropic.NewUserMessage(anthropic.NewTextBlock(userMsg)),
		},
		Thinking: anthropic.ThinkingConfigParamUnion{
			OfAdaptive: &anthropic.ThinkingConfigAdaptiveParam{},
		},
	})
	if err != nil {
		return models.MurshidiAnalysisDTO{}, fmt.Errorf("claude messages.new: %w", err)
	}

	var sb strings.Builder
	for _, block := range resp.Content {
		if block.Text != "" {
			sb.WriteString(block.Text)
		}
	}
	raw := strings.TrimSpace(sb.String())
	if raw == "" {
		return models.MurshidiAnalysisDTO{}, fmt.Errorf("claude returned no text content")
	}

	// Models occasionally wrap JSON in ```json ... ``` despite instructions.
	if strings.HasPrefix(raw, "```") {
		if idx := strings.IndexByte(raw, '\n'); idx >= 0 {
			raw = raw[idx+1:]
		}
		raw = strings.TrimSpace(strings.TrimSuffix(raw, "```"))
	}

	var parsed struct {
		Pattern       string `json:"pattern"`
		Structure     string `json:"structure"`
		RevealedValue string `json:"revealedValue"`
	}
	if err := json.Unmarshal([]byte(raw), &parsed); err != nil {
		return models.MurshidiAnalysisDTO{}, fmt.Errorf("parse diagnosis JSON: %w", err)
	}
	if parsed.Pattern == "" || parsed.Structure == "" || parsed.RevealedValue == "" {
		return models.MurshidiAnalysisDTO{}, fmt.Errorf("diagnosis missing required fields")
	}

	return models.MurshidiAnalysisDTO{
		Pattern:       parsed.Pattern,
		Structure:     parsed.Structure,
		RevealedValue: parsed.RevealedValue,
	}, nil
}
