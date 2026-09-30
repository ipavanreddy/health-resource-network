# early-warning

Stock-out warnings and surge detection

Starts as a router/module in `services/api/app/` (e.g. `app/early_warning/`).
Split into its own Cloud Run service here only if it needs separate scaling or runtime.
