# Python RVS Sidecar

FastAPI wrapper around `rvs_calculator_enhanced.calculate_enhanced_rvs`, called
by the Go backend when `PYTHON_RVS_URL` is set.

## Contract

- **POST `/calculate`** — accepts `RVSv4Input` JSON (same shape the Go backend
  uses), returns `RVSv4Output` JSON.
- **GET `/health`** — liveness probe.

## How it works

1. The Go `RVSEngineImpl.Calculate` marshals `models.RVSv4Input` and POSTs it
   to `${PYTHON_RVS_URL}/calculate`.
2. This sidecar receives the rich RVSv4Input (working capital, EBITDA,
   governance score, etc.) and derives the six V-variables the SRFF model
   expects (DSCR, collateral coverage, EBITDA margin, EBITDA/debt, asset
   identifiability, GP control factor).
3. `calculate_enhanced_rvs(RVSInputs)` runs the real model.
4. The result is mapped back into the `RVSv4Output` shape and returned.

**The V-variable derivations are proxies**, not canonical definitions. The Go
scaffold's input shape and the SRFF model's input shape don't map 1:1 —
`main.py._derive_v_variables` is where the approximation happens. Review
before production.

## Running locally

```bash
cd backend/python_rvs_service
pip install -r requirements.txt
cd ../..                             # back to repo root so imports resolve
uvicorn backend.python_rvs_service.main:app --port 8001 --reload
```

Then run the Go backend with `PYTHON_RVS_URL=http://localhost:8001`.

## Running via docker-compose

`docker compose up backend python-rvs postgres` from the repo root. The
compose file wires `PYTHON_RVS_URL=http://python-rvs:8001` automatically.
