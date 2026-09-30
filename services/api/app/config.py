import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    project_name: str = "health-resource-network"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    google_genai_use_vertexai: bool = False
    google_cloud_project: str = ""
    google_cloud_location: str = "asia-south1"
    # Vertex AI endpoint for Gemini. "global" has the most capacity (regional endpoints can return 429);
    # set asia-south1 for in-country processing.
    gemini_location: str = "global"
    # Gemini 2.5 "thinking" token budget: 0 = off (fastest; extraction is schema-constrained), -1 = dynamic.
    gemini_thinking_budget: int = 0
    google_application_credentials: str = ""
    bigquery_dataset: str = "health_resource_network"
    gcs_bucket: str = ""
    firebase_project_id: str = ""
    maps_api_key: str = ""
    cors_origins: str = "http://localhost:3030,http://localhost:3031"
    # Extra CORS origin regex, e.g. the project's Cloud Run URLs (https://health-resource-network-.*\\.run\\.app).
    cors_origin_regex: str = ""

    # Cloud Speech-to-Text / Text-to-Speech / Translation REST APIs (API key restricted to those APIs).
    google_cloud_api_key: str = ""
    # Forecast backend: "baseline" (local, explainable) or "bigquery" (BigQuery ML ARIMA_PLUS).
    forecast_backend: str = "baseline"
    # Force every integration into demo mode even if keys are present (tests, offline demos).
    force_demo_mode: bool = False
    # Synthetic data: deterministic seed and optional pinned reference time (ISO, IST). Empty = now.
    data_seed: int = 20260930
    demo_reference_time: str = ""


settings = Settings()

# pydantic-settings reads .env into Settings only; Google client libraries read ADC from os.environ.
if settings.google_application_credentials:
    os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", settings.google_application_credentials)
