# Build context: a staged copy of the repo (see infrastructure/cloud-run/deploy-api.sh), because the API
# reads versioned prompts (ai/prompts), state adapters (data/adapters) and the synthetic generator
# (data/generator) from the repository root.
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /srv/services/api
COPY services/api/pyproject.toml services/api/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY services/api/app ./app
COPY ai/prompts /srv/ai/prompts
COPY data/adapters /srv/data/adapters
COPY data/generator /srv/data/generator
ENV PORT=8080
CMD ["sh", "-c", "uv run --no-dev uvicorn app.main:app --host 0.0.0.0 --port $PORT"]
