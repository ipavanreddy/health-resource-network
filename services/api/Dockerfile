# PHC Pulse API (FastAPI) for Cloud Run.
# Build context = the repository root (or the minimal staged copy made by infrastructure/cloud-run/deploy.sh),
# because the API reads versioned prompts (ai/prompts), schemas (ai/schemas), state adapters (data/adapters)
# and the synthetic data generator (data/generator) from the repository root at runtime.
#   docker build -f services/api/Dockerfile -t phc-pulse-api .
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1
WORKDIR /srv/services/api
COPY services/api/pyproject.toml services/api/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY services/api/app ./app
COPY ai/prompts /srv/ai/prompts
COPY ai/schemas /srv/ai/schemas
COPY data/adapters /srv/data/adapters
COPY data/generator /srv/data/generator
COPY data/schemas /srv/data/schemas
# Fail the build (not the first request) if a runtime file is missing.
RUN .venv/bin/python -c "from app.store import get_store; from app.ai.gemini import load_prompt; \
    get_store(); [load_prompt(n, 'v1') for n in ('extract_stock', 'extract_register', 'transcribe', 'explain_transfer')]"
ENV PATH=/srv/services/api/.venv/bin:$PATH PORT=8080
RUN useradd --uid 10001 --no-create-home app
USER app
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
