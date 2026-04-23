FROM python:3.11-slim

WORKDIR /app

# Install Python deps first for better layer caching.
COPY backend/python_rvs_service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# The sidecar imports rvs_calculator_enhanced from the repo root, so copy
# the repo root into the image alongside the service.
COPY rvs_calculator_enhanced.py /repo/rvs_calculator_enhanced.py
COPY backend/python_rvs_service /repo/backend/python_rvs_service

WORKDIR /repo/backend/python_rvs_service

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
