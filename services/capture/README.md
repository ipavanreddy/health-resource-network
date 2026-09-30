# capture

Stock capture (voice, text, register photo) + Gemini extraction

Starts as a router/module in `services/api/app/` (e.g. `app/capture/`).
Split into its own Cloud Run service here only if it needs separate scaling or runtime.
