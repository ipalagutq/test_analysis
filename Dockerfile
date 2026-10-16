# Stage 1: static export of the Next.js UI into frontend/out
FROM node:20.19-slim AS frontend

WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: FastAPI runtime that also serves the exported UI
FROM python:3.12-slim AS runtime

COPY --from=ghcr.io/astral-sh/uv:0.11.8 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# all runtime paths (data/, frontend/out) are relative to the working directory
WORKDIR /app

# dependencies change less often than the code: cache them in their own layer
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src/ src/
RUN uv sync --frozen --no-dev --no-editable

COPY data/lab_catalog.json data/lab_catalog.json
COPY data/seed/ data/seed/
COPY data/samples/ data/samples/
COPY data/fixtures/ data/fixtures/
COPY --from=frontend /build/frontend/out frontend/out

EXPOSE 8000

CMD ["uvicorn", "test_analysis.main:app", "--host", "0.0.0.0", "--port", "8000"]
