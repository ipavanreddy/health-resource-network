#!/usr/bin/env bash
# Deploy services/api to Cloud Run (asia-south1). Secrets come from Secret Manager.
# The API needs ai/prompts, data/adapters and data/generator, so we stage a minimal build context.
set -euo pipefail
: "${GOOGLE_CLOUD_PROJECT:?set GOOGLE_CLOUD_PROJECT}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE/services/api" "$STAGE/ai" "$STAGE/data"
cp -R "$ROOT/services/api/app" "$ROOT/services/api/pyproject.toml" "$ROOT/services/api/uv.lock" "$STAGE/services/api/"
cp -R "$ROOT/ai/prompts" "$STAGE/ai/"
cp -R "$ROOT/data/adapters" "$ROOT/data/generator" "$STAGE/data/"
cp "$ROOT/services/api/Dockerfile" "$STAGE/Dockerfile"
find "$STAGE" -name '__pycache__' -prune -exec rm -rf {} +
gcloud run deploy health-resource-network-api \
  --source "$STAGE" \
  --project "$GOOGLE_CLOUD_PROJECT" \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,GOOGLE_CLOUD_LOCATION=asia-south1,BIGQUERY_DATASET=health_resource_network \
  --set-secrets GEMINI_API_KEY=gemini-api-key:latest,MAPS_API_KEY=maps-api-key:latest,GOOGLE_CLOUD_API_KEY=google-cloud-api-key:latest
