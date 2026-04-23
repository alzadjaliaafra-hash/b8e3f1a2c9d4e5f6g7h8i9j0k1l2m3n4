package handlers

import (
	"encoding/json"
	"net/http"
	"strings"
)

func respondWithJSON(w http.ResponseWriter, status int, payload interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(payload)
}

func respondWithError(w http.ResponseWriter, status int, message string) {
	respondWithJSON(w, status, map[string]string{"error": message})
}

func isValidFileType(filename string) bool {
	lower := strings.ToLower(filename)
	for _, ext := range []string{".xlsx", ".xls", ".csv"} {
		if strings.HasSuffix(lower, ext) {
			return true
		}
	}
	return false
}
