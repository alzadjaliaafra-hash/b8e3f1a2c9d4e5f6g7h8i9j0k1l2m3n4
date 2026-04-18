package routes

import (
	"net/http"

	"github.com/go-chi/chi/v5"

	"github.com/alzadjaliaafra-hash/srff-i-rvs-model/backend/internal/api/handlers"
)

// Handlers bundles every HTTP handler set wired by the router.
type Handlers struct {
	Assessment *handlers.AssessmentHandler
	PDF        *handlers.PDFHandler
	// Auth, User, Analytics, Health handlers would live here once implemented.
}

// AuthMiddleware is a placeholder for JWT / API-key middleware. Real
// implementations should attach user context via context.WithValue.
type AuthMiddleware struct{}

func (a *AuthMiddleware) Authenticate(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		next.ServeHTTP(w, r)
	})
}

func (a *AuthMiddleware) AuthenticateAPIKey(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		next.ServeHTTP(w, r)
	})
}

// SetupRoutes wires every endpoint under /api/v1.
func SetupRoutes(r chi.Router, h *Handlers, auth *AuthMiddleware) {
	if auth == nil {
		auth = &AuthMiddleware{}
	}

	// Public (no auth).
	r.Group(func(r chi.Router) {
		r.Get("/health", func(w http.ResponseWriter, req *http.Request) {
			w.WriteHeader(http.StatusOK)
			_, _ = w.Write([]byte(`{"status":"ok"}`))
		})
	})

	// Protected routes.
	r.Group(func(r chi.Router) {
		r.Use(auth.Authenticate)

		r.Route("/api/v1/assessments", func(r chi.Router) {
			r.Post("/", h.Assessment.CreateAssessment)
			r.Get("/", h.Assessment.GetAssessments)
			r.Get("/{id}", h.Assessment.GetAssessmentByID)
			r.Put("/{id}", h.Assessment.UpdateAssessment)
			r.Delete("/{id}", h.Assessment.DeleteAssessment)
			r.Post("/upload", h.Assessment.HandleFileUpload)
			r.Get("/{id}/report", h.Assessment.GenerateReport)
			r.Post("/{id}/recalculate", h.Assessment.Recalculate)
			if h.PDF != nil {
				r.Get("/{id}/export-pdf", h.PDF.ExportPDF)
			}
		})
	})

	// External API (API-key auth).
	r.Group(func(r chi.Router) {
		r.Use(auth.AuthenticateAPIKey)
		r.Post("/api/v1/external/assessments", h.Assessment.HandleExternalDataIngestion)
	})
}
