package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/alzadjaliaafra-hash/srff-i-rvs-model/backend/internal/api/handlers"
	"github.com/alzadjaliaafra-hash/srff-i-rvs-model/backend/internal/api/routes"
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
	murshidiClient := services.NewNoopMurshidiClient()

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
	r.Use(middleware.RequestID)
	r.Use(middleware.RealIP)
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)
	r.Use(middleware.Timeout(60 * time.Second))

	routes.SetupRoutes(r, handlerSet, nil)

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	logger.Printf("starting server on :%s", port)
	if err := http.ListenAndServe(":"+port, r); err != nil {
		logger.Fatalf("server error: %v", err)
	}
}
