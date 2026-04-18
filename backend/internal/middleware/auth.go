package middleware

import (
	"context"
	"net/http"
)

// Handlers currently read the user ID with a bare string key:
//   r.Context().Value("userID").(string)
// so the middleware writes to the same key. A follow-up refactor should
// introduce a typed context key and update the handler call sites.
const userIDKey = "userID"

// DevUserID is the fixed user ID used by the dev-mode stub. A matching row
// must exist in the users table (see migrations/000_create_users_table.sql).
const DevUserID = "00000000-0000-0000-0000-000000000001"

// AuthMiddleware provides HTTP middleware for authentication. The current
// implementation is a dev-mode stub that populates the request context with
// DevUserID on every request. Swap for real JWT / API-key validation before
// production.
type AuthMiddleware struct{}

func NewAuthMiddleware() *AuthMiddleware { return &AuthMiddleware{} }

// Authenticate sets userID = DevUserID on the request context.
func (m *AuthMiddleware) Authenticate(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		ctx := context.WithValue(r.Context(), userIDKey, DevUserID)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// AuthenticateAPIKey mirrors Authenticate for external integrations in
// dev-mode. Real deployments should validate the X-API-Key header here.
func (m *AuthMiddleware) AuthenticateAPIKey(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		ctx := context.WithValue(r.Context(), userIDKey, DevUserID)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}
