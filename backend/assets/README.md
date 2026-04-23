# Assets Directory

Place the Alif logo here as `alif-logo.png` for PDF generation.

Expected format: PNG, recommended size 200x200px minimum.

The runtime path is read from `IC_MEMO_LOGO_PATH` (see `cmd/server/main.go`).
If the env var is empty, the PDF generator omits the logo without failing.
