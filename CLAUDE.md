# PHC Pulse (Track 3): agent instructions

The spec is `docs/PRD.md` (58 sections). Read §8 (core journey), §31–§38 (entities, AI, APIs, FRs)
and §57 (build priority) before writing code. Do not build Priority 2+ items until the Priority 1
journey works end to end.

## Non-negotiables (from the PRD pack)
- Gemini never invents measurements. Give it structured context and require schema-validated JSON
  (`services/api/app/ai/gemini.py::generate_structured`). Separate observed data → AI interpretation → recommendation.
- Every AI-generated record stores `model_name`, `model_version`, `prompt_version`.
- Every data point carries source + timestamp. Sample/synthetic data is labelled as such in the data and the UI.
- Canonical schema + state adapters; at least two state configs (Tamil Nadu (post-flood diarrhoea), Uttar Pradesh (vector-borne season), Odisha (malaria)).
- Consequential actions (alerts, transfers, advisories, recommendations) need human approval.
- Exactly two roles: PHC Staff and District Health Officer.
- Never commit secrets. Config comes from `.env` (see `.env.example`).
- Cite every reused dataset/model/library in `THIRD_PARTY.md`.

## Layout and ports
- `apps/phc-web` → :3030 · `apps/officer-dashboard` → :3031 (Next.js 16, pnpm workspace; read `apps/*/AGENTS.md`)
- `services/api` → :8030 (FastAPI, uv, Python 3.12). Domain services listed in `services/*/README.md`
  start as routers/modules inside `services/api/app/`; split to separate Cloud Run services only if needed.
- Prompts in `ai/prompts/` (versioned filenames, e.g. `extract_v1.md`), schemas in `ai/schemas/`.

## Commands
- `pnpm dev:api`, `pnpm dev:phc-web`, `pnpm dev:officer-dashboard`
- `pnpm test:api`, `pnpm build`, `pnpm lint`
