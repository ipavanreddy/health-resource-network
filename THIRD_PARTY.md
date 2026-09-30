# Third-party datasets, models and libraries

Every reused dataset, model and library must be cited here (hackathon rule).

## Libraries

| Name | Type | Licence | Source URL | Used for |
|---|---|---|---|---|
| Next.js | Library | MIT | https://nextjs.org | Frontend |
| React | Library | MIT | https://react.dev | Frontend |
| shadcn/ui | Library | MIT | https://ui.shadcn.com | UI components |
| Base UI (@base-ui/react) | Library | MIT | https://base-ui.com | UI primitives under shadcn/ui |
| Tailwind CSS | Library | MIT | https://tailwindcss.com | Styling |
| lucide-react | Library | ISC | https://lucide.dev | Icons |
| sonner | Library | MIT | https://sonner.emilkowal.ski | Toast notifications |
| Leaflet | Library | BSD-2-Clause | https://leafletjs.com | Dashboard map fallback when no Google Maps key |
| @types/leaflet | Library | MIT | https://github.com/DefinitelyTyped/DefinitelyTyped | Leaflet type definitions |
| Geist font | Font | SIL OFL 1.1 | https://vercel.com/font | UI typography (scaffold) |
| FastAPI | Library | MIT | https://fastapi.tiangolo.com | API |
| Pydantic / pydantic-settings | Library | MIT | https://docs.pydantic.dev | Schemas, validation, config |
| Uvicorn | Library | BSD-3-Clause | https://www.uvicorn.org | ASGI server |
| HTTPX | Library | BSD-3-Clause | https://www.python-httpx.org | REST calls to Routes / Speech / TTS / Translation |
| NumPy | Library | BSD-3-Clause | https://numpy.org | Synthetic data generator, forecast baseline |
| Google OR-Tools | Library | Apache-2.0 | https://developers.google.com/optimization | Redistribution optimiser (min-cost flow) |
| pandas | Library | BSD-3-Clause | https://pandas.pydata.org | Transitive dependency of OR-Tools |
| Google Gen AI SDK (google-genai) | Library | Apache-2.0 | https://github.com/googleapis/python-genai | Gemini calls |
| google-cloud-bigquery | Library | Apache-2.0 | https://github.com/googleapis/python-bigquery | BigQuery sink and BQML forecast |
| firebase-admin | Library | Apache-2.0 | https://github.com/firebase/firebase-admin-python | Firestore notifications |
| pytest | Library | MIT | https://pytest.org | Tests |
| Ruff | Tool | MIT | https://docs.astral.sh/ruff | Python lint |

## Services / models (used when the corresponding env var is set)

| Name | Type | Terms | Source URL | Used for |
|---|---|---|---|---|
| Gemini (model from `GEMINI_MODEL`) | Model API | Google AI / Google Cloud terms | https://ai.google.dev | Stock extraction, register photo reading, audio transcription, transfer explanations |
| Cloud Speech-to-Text, Text-to-Speech, Translation | API | Google Cloud terms | https://cloud.google.com | Voice reports, spoken confirmations, translation |
| Google Maps Platform (Routes API, Maps JavaScript API) | API | Google Maps Platform terms | https://developers.google.com/maps | Travel times, dashboard map |
| BigQuery / BigQuery ML (ARIMA_PLUS) | Service | Google Cloud terms | https://cloud.google.com/bigquery | Event storage, shared forecast model |
| Firebase / Firestore | Service | Firebase terms | https://firebase.google.com | Notifications |
| OpenStreetMap tiles and map data | Dataset / tiles | ODbL 1.0 (data), OSMF Tile Usage Policy | https://www.openstreetmap.org/copyright | Map fallback tiles, attributed "© OpenStreetMap contributors" |

## Datasets and reference material

| Name | Type | Licence | Source URL | Used for |
|---|---|---|---|---|
| PHC Pulse synthetic dataset (`data/generator/synth.py`) | Dataset (generated) | Project licence | this repo | All facility, stock, consumption, beds and staff data. **Synthetic; not real data.** |
| National List of Essential Medicines 2022 (India) | Reference | Government of India publication | https://cdsco.gov.in | Choice of tracer medicines and strengths in the medicine master (names only) |
| Indian district / block names (Madurai, Thanjavur, Gorakhpur, Deoria, Koraput, Rayagada) | Reference | Public administrative names | https://lgdirectory.gov.in | Labels for synthetic facilities; locations are jittered and facilities are fictional |
| Sample register page (`apps/phc-web/public/sample-register.svg`) | Image | Project licence | this repo | Team-made synthetic register page for the photo demo |
