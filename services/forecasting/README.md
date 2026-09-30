# forecasting

Demand forecast (Vertex AI / BigQuery ML)

Starts as a router/module in `services/api/app/` (e.g. `app/forecasting/`).
Split into its own Cloud Run service here only if it needs separate scaling or runtime.
