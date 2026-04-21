package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/go-chi/chi/v5"
	chimw "github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/cors"
	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/alzadjaliaafra-hash/srff-i-rvs-model/backend/internal/api/handlers"
	"github.com/alzadjaliaafra-hash/srff-i-rvs-model/backend/internal/api/routes"
	"github.com/alzadjaliaafra-hash/srff-i-rvs-model/backend/internal/middleware"
	"github.com/alzadjaliaafra-hash/srff-i-rvs-model/backend/internal/repositories"
	"github.com/alzadjaliaafra-hash/srff-i-rvs-model/backend/internal/services"
	"github.com/alzadjaliaafra-hash/srff-i-rvs-model/backend/internal/validators"
)

func main() {
	logger := log.New(os.Stdout, "[srff-i-rvs] ", log.LstdFlags|log.Lshortfile)

	dsn := os.Getenv("DATABASE_URL")
	if dsn == "" {
		dsn = "postgres://postgres:postgres@localhost:5432/srff_rvs?sslmode=disable"
	}

	ctx := context.Background()
	db, err := pgxpool.New(ctx, dsn)
	if err != nil {
		logger.Fatalf("failed to connect to database: %v", err)
	}
	defer db.Close()

	// Wire repositories, services, handlers
	assessmentRepo := repositories.NewPostgresAssessmentRepository(db)
	validator := validators.NewRVSValidator(logger)
	transformer := services.NewDataTransformer(logger)

	rvsEngine := services.NewRVSEngine()

	var murshidiClient services.MurshidiClient
	if os.Getenv("ANTHROPIC_API_KEY") != "" {
		claudeClient, err := services.NewClaudeMurshidiClient()
		if err != nil {
			logger.Printf("claude murshidi client disabled, using noop fallback: %v", err)
			murshidiClient = services.NewNoopMurshidiClient()
		} else {
			logger.Printf("claude murshidi client enabled (model=%s)", claudeClient.Model())
			murshidiClient = claudeClient
		}
	} else {
		murshidiClient = services.NewNoopMurshidiClient()
	}

	assessmentService := services.NewAssessmentService(
		assessmentRepo,
		rvsEngine,
		murshidiClient,
		db,
		logger,
	)

	assessmentHandler := handlers.NewAssessmentHandler(
		assessmentService,
		validator,
		transformer,
		logger,
	)

	logoPath := os.Getenv("IC_MEMO_LOGO_PATH")
	pdfGenerator := services.NewPDFGenerator(logoPath)
	pdfHandler := handlers.NewPDFHandler(assessmentService, pdfGenerator)

	handlerSet := &routes.Handlers{
		Assessment: assessmentHandler,
		PDF:        pdfHandler,
	}

	r := chi.NewRouter()
	r.Use(chimw.RequestID)
	r.Use(chimw.RealIP)
	r.Use(chimw.Logger)
	r.Use(chimw.Recoverer)
	r.Use(chimw.Timeout(60 * time.Second))
	r.Use(cors.Handler(cors.Options{
		AllowedOrigins:   []string{"http://localhost:4200"},
		AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowedHeaders:   []string{"Accept", "Authorization", "Content-Type", "X-API-Key"},
		ExposedHeaders:   []string{"Link", "Content-Disposition"},
		AllowCredentials: true,
		MaxAge:           300,
	}))

	authMw := middleware.NewAuthMiddleware()
	routes.SetupRoutes(r, handlerSet, authMw)

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	logger.Printf("starting server on :%s", port)
	if err := http.ListenAndServe(":"+port, r); err != nil {
		logger.Fatalf("server error: %v", err)
	}
}
