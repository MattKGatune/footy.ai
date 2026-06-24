# syntax=docker/dockerfile:1

# ---- Stage 1: build the React client ----
FROM node:20-slim AS frontend
WORKDIR /client

# Install deps first so this layer caches unless package files change
COPY client/package.json client/package-lock.json ./
RUN npm ci

# Build the static bundle into /client/dist
COPY client/ ./
RUN npm run build

# ---- Stage 2: Python API runtime ----
FROM python:3.12-slim AS runtime

# libgomp1 is the OpenMP runtime XGBoost links against; without it imports fail
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first for layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Application code and trained models (loaded from repo root by api/models.py)
COPY api/ ./api/
COPY xg_model.pkl xg_feature_cols.pkl wp_model.pkl ./

# Pre-built frontend from stage 1 (served by FastAPI StaticFiles at /)
COPY --from=frontend /client/dist ./client/dist

EXPOSE 8000
ENV PORT=8000

# JSON/exec form (uvicorn becomes PID 1 so SIGTERM → graceful shutdown);
# sh -c expands ${PORT}, which Render injects at runtime
CMD ["sh", "-c", "exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
