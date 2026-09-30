#!/usr/bin/env bash
# Build and deploy PHC Pulse to Cloud Run (asia-south1): one API service + one service per Next.js app.
#
#   infrastructure/cloud-run/deploy.sh                    # deploy everything (api, phc-web, officer-dashboard)
#   infrastructure/cloud-run/deploy.sh api                # deploy one or more services
#   infrastructure/cloud-run/deploy.sh --local [svc...]   # build the same images with local Docker (no deploy)
#   infrastructure/cloud-run/deploy.sh --print-urls
#
# Each service is built from a minimal *staged* copy of the repo (a temp dir), so only what the image needs is
# uploaded to Cloud Build. The browser Maps key (NEXT_PUBLIC_MAPS_API_KEY) is baked into the Next.js bundles at
# build time from a generated `.env.production` inside that temp dir: it is never written into the git tree.
# It is read from $NEXT_PUBLIC_MAPS_API_KEY or, if unset, from apps/officer-dashboard/.env.local (gitignored).
#
# Server-side keys come from Secret Manager (never from env files):
#   MAPS_API_KEY=maps-api-key:latest          Routes API travel times
#   GOOGLE_CLOUD_API_KEY=google-api-key:latest Speech-to-Text, Text-to-Speech, Translation
#   GEMINI_API_KEY=gemini-api-key:latest       attached automatically once that secret exists (see README)
# Gemini runs on Vertex AI with the service account by default (GEMINI_BACKEND=vertex). Set GEMINI_BACKEND=apikey
# to use the AI Studio key from the gemini-api-key secret instead.
set -euo pipefail

export PATH="/opt/homebrew/share/google-cloud-sdk/bin:$PATH"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PROJECT="${GOOGLE_CLOUD_PROJECT:-spontom-build-with-ai}"
REGION="${REGION:-asia-south1}"
PREFIX="health-resource-network"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT:-hackathon-dev@${PROJECT}.iam.gserviceaccount.com}"
BIGQUERY_DATASET="${BIGQUERY_DATASET:-health_resource_network}"
GCS_BUCKET="${GCS_BUCKET:-${PROJECT}-media}"
GEMINI_MODEL="${GEMINI_MODEL:-gemini-2.5-flash}"
GEMINI_LOCATION="${GEMINI_LOCATION:-global}"
GEMINI_BACKEND="${GEMINI_BACKEND:-vertex}"
FORECAST_BACKEND="${FORECAST_BACKEND:-baseline}"
APPS=(phc-web officer-dashboard)

LOCAL=0
SERVICES=()
for arg in "$@"; do
  case "$arg" in
    --local) LOCAL=1 ;;
    --print-urls) PRINT_ONLY=1 ;;
    all) SERVICES+=(api "${APPS[@]}") ;;
    api | phc-web | officer-dashboard) SERVICES+=("$arg") ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done
[ ${#SERVICES[@]} -eq 0 ] && SERVICES=(api "${APPS[@]}")

# Cloud Run URLs are deterministic (https://SERVICE-PROJECT_NUMBER.REGION.run.app), so every service can be
# configured with the others' URLs before they exist.
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')"
url() { echo "https://${PREFIX}-$1-${PROJECT_NUMBER}.${REGION}.run.app"; }
API_URL="$(url api)"
PHC_URL="$(url phc-web)"
DHO_URL="$(url officer-dashboard)"
echo "API:               $API_URL"
echo "PHC Staff app:     $PHC_URL"
echo "DHO dashboard:     $DHO_URL"
[ "${PRINT_ONLY:-0}" = 1 ] && exit 0

STAGES=()
cleanup() { for s in "${STAGES[@]:-}"; do [ -n "$s" ] && rm -rf "$s"; done; }
trap cleanup EXIT

RSYNC_EXCLUDES=(--exclude node_modules --exclude .next --exclude .venv --exclude __pycache__ --exclude '.env'
  --exclude '.env.local' --exclude '.env.*.local' --exclude '*.tsbuildinfo' --exclude .pytest_cache
  --exclude .ruff_cache --exclude tests)

# stage_* create a temp build context and set $STAGE (not via $(...) so the cleanup list is kept).
stage_api() {
  local s; s="$(mktemp -d)"; STAGES+=("$s"); STAGE="$s"
  mkdir -p "$s/services/api" "$s/ai" "$s/data"
  rsync -a "${RSYNC_EXCLUDES[@]}" "$ROOT/services/api/app" "$ROOT/services/api/pyproject.toml" \
    "$ROOT/services/api/uv.lock" "$s/services/api/"
  rsync -a "$ROOT/ai/prompts" "$ROOT/ai/schemas" "$s/ai/"
  rsync -a "${RSYNC_EXCLUDES[@]}" "$ROOT/data/adapters" "$ROOT/data/generator" "$ROOT/data/schemas" "$s/data/"
  cp "$ROOT/services/api/Dockerfile" "$s/Dockerfile"
  printf '# Upload everything in this staged context\n' > "$s/.gcloudignore"
}

maps_browser_key() {
  if [ -n "${NEXT_PUBLIC_MAPS_API_KEY:-}" ]; then echo "$NEXT_PUBLIC_MAPS_API_KEY"; return; fi
  local f="$ROOT/apps/officer-dashboard/.env.local"
  [ -f "$f" ] && sed -n 's/^NEXT_PUBLIC_MAPS_API_KEY=//p' "$f" | tail -1
}

stage_app() {
  local app="$1" s; s="$(mktemp -d)"; STAGES+=("$s"); STAGE="$s"
  cp "$ROOT/package.json" "$ROOT/pnpm-lock.yaml" "$ROOT/pnpm-workspace.yaml" "$s/"
  for a in "${APPS[@]}"; do mkdir -p "$s/apps/$a"; cp "$ROOT/apps/$a/package.json" "$s/apps/$a/"; done
  rsync -a "${RSYNC_EXCLUDES[@]}" --exclude .gitignore --exclude Dockerfile "$ROOT/apps/$app/" "$s/apps/$app/"
  # Build-time public config (inlined into the browser bundle). Temp dir only; never committed.
  {
    echo "NEXT_PUBLIC_API_URL=$API_URL"
    echo "NEXT_PUBLIC_MAPS_API_KEY=$(maps_browser_key)"
  } > "$s/apps/$app/.env.production"
  cp "$ROOT/apps/$app/Dockerfile" "$s/Dockerfile"
  # An explicit .gcloudignore so gcloud does not fall back to .gitignore rules (which would drop .env.production).
  printf '# Upload everything in this staged context (including the generated .env.production)\n' > "$s/.gcloudignore"
  printf 'node_modules\n.next\n' > "$s/.dockerignore"
}

secret_exists() { gcloud secrets describe "$1" --project "$PROJECT" >/dev/null 2>&1; }

deploy_api() {
  stage_api; local s="$STAGE"
  local secrets="MAPS_API_KEY=maps-api-key:latest,GOOGLE_CLOUD_API_KEY=google-api-key:latest"
  local vertex=true
  if secret_exists gemini-api-key; then
    secrets="$secrets,GEMINI_API_KEY=gemini-api-key:latest"
    [ "$GEMINI_BACKEND" = apikey ] && vertex=false
    echo "gemini-api-key secret found: attached as GEMINI_API_KEY (backend: $GEMINI_BACKEND)"
  else
    echo "gemini-api-key secret not found: Gemini via Vertex AI with the service account"
  fi
  local envs="^|^GOOGLE_CLOUD_PROJECT=$PROJECT|GOOGLE_CLOUD_LOCATION=$REGION|BIGQUERY_DATASET=$BIGQUERY_DATASET"
  envs+="|GCS_BUCKET=$GCS_BUCKET|GEMINI_MODEL=$GEMINI_MODEL|GEMINI_LOCATION=$GEMINI_LOCATION"
  envs+="|GOOGLE_GENAI_USE_VERTEXAI=$vertex|FORECAST_BACKEND=$FORECAST_BACKEND"
  envs+="|CORS_ORIGINS=$PHC_URL,$DHO_URL,http://localhost:3030,http://localhost:3031"
  [ -n "${FIREBASE_PROJECT_ID:-}" ] && envs+="|FIREBASE_PROJECT_ID=$FIREBASE_PROJECT_ID"
  # One instance: the demo store is in memory, so every request must see the same state (BigQuery is the
  # durable mirror). min-instances=1 keeps the demo warm.
  gcloud run deploy "$PREFIX-api" --source "$s" --project "$PROJECT" --region "$REGION" \
    --service-account "$SERVICE_ACCOUNT" --allow-unauthenticated \
    --memory 1Gi --cpu 1 --min-instances 1 --max-instances 1 --concurrency 40 --timeout 120 --cpu-boost \
    --set-env-vars "$envs" --set-secrets "$secrets" \
    --labels "app=$PREFIX,component=api" --quiet
}

deploy_app() {
  local app="$1"; stage_app "$app"; local s="$STAGE"
  gcloud run deploy "$PREFIX-$app" --source "$s" --project "$PROJECT" --region "$REGION" \
    --service-account "$SERVICE_ACCOUNT" --allow-unauthenticated \
    --memory 512Mi --cpu 1 --min-instances 0 --max-instances 3 --cpu-boost \
    --labels "app=$PREFIX,component=$app" --quiet
}

build_local() {
  local svc="$1"
  if [ "$svc" = api ]; then stage_api; else stage_app "$svc"; fi
  docker build -t "$PREFIX-$svc:local" "$STAGE"
}

for svc in "${SERVICES[@]}"; do
  echo "=== $svc"
  if [ "$LOCAL" = 1 ]; then build_local "$svc"
  elif [ "$svc" = api ]; then deploy_api
  else deploy_app "$svc"; fi
done

if [ "$LOCAL" = 0 ]; then
  echo "Smoke test:"
  curl -fsS "$API_URL/health" && echo
  for u in "$PHC_URL" "$DHO_URL"; do echo "$u -> $(curl -s -o /dev/null -w '%{http_code}' "$u")"; done
fi
