# PHC Pulse: Federated Health Resource & Supply Chain Platform

Build with AI (Google) hackathon, Track 3. Full spec: [docs/PRD.md](docs/PRD.md).

## Core journey (PRD §57 Priority 1, working end to end)

```text
Stock Report (voice / register photo / text / form)      PHC Staff app      :3030
 ↓  Speech-to-Text → Gemini extraction → staff confirmation (EN / HI / TA)
Days of Cover + Beds + Staff + Facility Readiness
 ↓
Forecast (8 weeks, low/expected/high) + Stock-out Risk + Surge signal
 ↓
Redistribution (OR-Tools min-cost flow, Routes API travel times) + Gemini explanation
 ↓
District Health Officer approval → both facilities notified → dispatch → receipt   DHO dashboard :3031
```

**Headline score:** Facility Readiness = Stock cover 40 · Beds 20 · Staff 20 · Reporting freshness 10 · Surge stability 10
(weights configurable per state in `data/adapters/<state>.json`).
**Roles:** PHC Staff (`apps/phc-web`) · District Health Officer (`apps/officer-dashboard`).
**Demo states:** Tamil Nadu / Madurai (post-flood diarrhoea), Uttar Pradesh / Gorakhpur (vector-borne season),
Odisha / Koraput (malaria). All data is **synthetic** and labelled as such in the data and the UI.

## Run the demo

```bash
cp .env.example .env                      # keys optional: everything has a labelled demo fallback
for a in apps/*; do cp $a/.env.example $a/.env.local; done
pnpm install
(cd services/api && uv sync)

pnpm dev:api                  # http://localhost:8030  (OpenAPI docs at /docs)
pnpm dev:phc-web              # http://localhost:3030  PHC Staff
pnpm dev:officer-dashboard    # http://localhost:3031  District Health Officer
```

The API generates its synthetic dataset in memory at start-up (~1 s, deterministic seed) and pipes it through
the state adapters. `POST /api/demo/reset` restores the initial state between demo runs.

### 5-minute demo script (PRD §44)

1. **PHC app** (Scenario A, PHC Melur, Tamil): *Report stock → Voice*. Record in Tamil (Chrome also shows a
   live browser transcript) or press *Use sample voice report*. Review the extracted items (standard name +
   the Tamil name heard, match confidence), *Play confirmation*, *Confirm & save*.
   *Register photo → Use sample register page* shows handwritten-table extraction with an illegible cell and
   an unrecognised medicine flagged, never guessed.
2. *Stock & readiness*: days of cover per medicine (ORS critical, Amoxicillin stocked out), stock-out risk,
   next-week forecast, readiness score with its 5-part breakdown, beds and geo-fenced staff check-in.
3. **DHO dashboard** (Tamil Nadu / Madurai): KPIs, facility map coloured by readiness, *possible acute
   diarrhoea cluster* (verify & notify facilities), facility drill-down with the 8-week forecast chart.
4. *Run optimiser* (e.g. ORS): transfers with Gemini explanation, travel time, stock-out days avoided and donor
   safety stock → *Approve* → both PHCs are notified (in their language) → dispatched → PHC confirms receipt.
5. *Interoperability & models*: switch to Uttar Pradesh / Odisha; native state record vs canonical record;
   the shared forecast model card with per-state accuracy vs naive baselines.

## Demo mode vs real Google integrations

Every integration sits behind a small adapter; **adding the env var is the only step** to switch it on. The UI shows
a *Demo mode* badge (click it for the per-integration list) and a *Synthetic data* badge; `GET /api/system/modes`
reports the same.

| Integration | Env var(s) that switch it on | Demo-mode fallback |
|---|---|---|
| Gemini extraction, register photo reading, audio transcription, transfer explanations | `GEMINI_API_KEY` (or `GOOGLE_GENAI_USE_VERTEXAI=true` + `GOOGLE_CLOUD_PROJECT`); model from `GEMINI_MODEL` | Deterministic rule parser (EN/HI/TA), labelled register fixture, template explanations. Provenance says `demo-*` |
| Speech-to-Text / Text-to-Speech / Translation | `GOOGLE_CLOUD_API_KEY` | Gemini audio (if on) → browser Web Speech transcript → scripted demo transcript; browser `speechSynthesis`; pre-translated UI templates |
| Routes API travel times | `MAPS_API_KEY` (server) | Haversine distance × 1.35 road factor at 35 km/h |
| Google Maps (dashboard map) | `NEXT_PUBLIC_MAPS_API_KEY` in `apps/officer-dashboard/.env.local` | Leaflet + OpenStreetMap tiles |
| BigQuery (event sink: stock transactions, transfers, AI outputs) | `GOOGLE_CLOUD_PROJECT` + `BIGQUERY_DATASET` + ADC (`GOOGLE_APPLICATION_CREDENTIALS` locally) | In-memory store |
| BigQuery ML forecast (ARIMA_PLUS) | the above + `FORECAST_BACKEND=bigquery`, after running `infrastructure/bigquery/*.sql` and `data/transformations/load_bigquery.py` | Local seasonal exponential-smoothing baseline |
| Firestore notifications | `FIREBASE_PROJECT_ID` + ADC | In-app notifications (polled) |

`FORCE_DEMO_MODE=true` forces every fallback even with keys set (tests always do this).

## AI safety (PRD §35)

Gemini gets structured context and must return schema-validated JSON (`ai/schemas/`, prompts in
`ai/prompts/*_v1.md`); unknown drug codes are rejected; quantities are never invented (null when not stated);
staff confirm every extraction before the ledger changes; the optimiser (not Gemini) decides quantities and the
explanation can't alter them; donors never go below safety stock; surge alerts are *possible signals* that the DHO
must verify before facilities see them; every transfer needs DHO approval; every AI record stores `model_name`,
`model_version`, `prompt_version`. No patient-level data is stored.

## Tests and checks

```bash
pnpm test:api      # pytest: days of cover, readiness, forecast, risk, optimiser, parser, adapters, API, e2e journey
pnpm lint          # eslint for both apps
pnpm build         # next build for both apps
(cd services/api && uv run ruff check app tests scripts ../../data)
(cd services/api && uv run python -m scripts.eval_extraction)   # golden extraction set (Gemini if configured)
```

## Data

- `data/generator/synth.py`: transparent synthetic generator (PRD §42): ~200 facilities in 3 states, 3 years of
  daily consumption with seasonality, injected outbreaks and stock-outs, deterministic seed, labelled metadata.
  `python data/generator/synth.py --out data/generated` writes the full dataset (gitignored);
  `--sample --out data/sample` writes the small committed sample.
- `data/adapters/{tn,up,od}.json`: state configurations + declarative adapters (field map, drug-code map,
  timestamp format, unit conversion) mapping each state's illustrative native export to the canonical schema
  (`data/schemas/canonical_v1.json`).

## Layout

| Path | Purpose |
|---|---|
| `apps/phc-web/` | PHC Staff app (EN/HI/TA, voice, photo, text, form capture) |
| `apps/officer-dashboard/` | District Health Officer dashboard (map, warnings, transfer review, interoperability) |
| `services/api/app/` | FastAPI: `capture/`, `visibility/`, `forecasting/`, `early_warning/`, `redistribution/`, `interop/`, `localization/`, `integrations/` (Google adapters), `store.py`, `routers/` |
| `ai/` | Versioned prompts, JSON schemas, extraction golden set |
| `data/` | Generator, state adapters, canonical schema, committed sample, BigQuery loader |
| `infrastructure/` | Cloud Run deploy script, BigQuery schema + BQML model |

## Known gaps

- Demo auth: the role comes from an `X-Role` header set by each app (Firebase Auth custom claims in production).
- The in-memory store resets on API restart; BigQuery/Firestore are mirrors, not yet the read path.
- Forecasts use synthetic history only (no weather/surveillance features yet); accuracy is reported on synthetic data.
- Emergency scenario simulation and offline sync (PRD Priority 4) are not built.
