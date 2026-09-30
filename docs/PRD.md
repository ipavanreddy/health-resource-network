# AI-Powered Federated Health Resource & Supply Chain Intelligence Platform

## Product Requirements Document (PRD)

**Document Version:** 2.0 (aligned to the PRD 04 template)
**Working Name:** PHC Pulse
**Track:** 3: National-scale health resource & supply chain management for Primary Health Centres
**Product Type:** AI-powered Public Health Supply Chain Platform / Interoperable Public Infrastructure
**Target Geography:** India
**Primary User:** PHC Staff (pharmacist / staff nurse / Medical Officer)
**Secondary User:** District Health Officer
**Primary Objective:** Give real-time visibility into medicine stock, beds and staff presence across PHCs, forecast demand, warn early about stock-outs (especially during health emergencies), and recommend redistribution between facilities and districts, on an interoperable foundation that lets states share predictive models.

---

# 1. Executive Summary

Primary Health Centres (PHCs) are the first point of care for much of rural India. Yet PHC networks often can't see, in real time:

- How much of each essential medicine each facility has
- How many beds are available
- Which staff are present
- How patient footfall is changing
- Where surplus stock sits while other facilities run out

The data that exists is spread across registers, spreadsheets and separate state systems, and it is often updated late.

The proposed solution is an **AI-powered health resource intelligence platform** that:

1. Makes **reporting stock, beds and attendance** take seconds, by voice, text or a photo of a paper register.
2. Provides **real-time visibility** of stock cover, beds and staff for every facility.
3. **Forecasts medicine demand** per facility.
4. Generates **early warnings** for likely stock-outs and unusual demand surges (possible outbreaks).
5. **Recommends redistribution** of surplus stock between facilities and districts, with a clear explanation and human approval.
6. Supports **multilingual and voice** interaction for frontline staff.
7. Provides **a common data and model architecture** so states can join and share predictive models without rebuilding the platform.

The hackathon MVP will focus on a single, polished end-to-end journey:

> **PHC Stock Update → Real-time Visibility → Demand Forecast → Stock-out Warning → Redistribution Recommendation → Approval → Action**

The prototype will also show that the same architecture supports several Indian states.

---

# 2. Problem Statement

## 2.1 Core Problem

Public healthcare systems across India face persistent supply chain vulnerabilities. Medicines, patient footfall and resource use can't be tracked in real time across large PHC networks.

Facilities often rely on:

- Paper stock registers
- Periodic manual reports
- Phone calls to the district warehouse
- Fixed indent cycles regardless of demand
- Informal knowledge of which facility has surplus

This creates several risks:

- Stock-outs of essential medicines
- Expiry and waste of surplus stock elsewhere
- Late detection of disease outbreaks
- Beds and staff unavailable when needed
- Weak response during health emergencies (outbreaks, floods, heatwaves)
- Patients forced to buy medicines out of pocket or travel further

The relevant data is fragmented across facilities, districts and state systems.

---

# 3. Challenge

The challenge is to build a **federated AI platform for national-scale health resource and supply chain management** that:

- Provides **real-time visibility** into **medicine stocks, bed availability and medical personnel attendance** across the PHC network.
- **Forecasts demand**.
- Generates **early warnings for potential stock-outs during health emergencies**.
- **Recommends automated cross-district resource redistribution**.
- Allows **shared predictive modelling across India's states**.
- Uses AI meaningfully rather than as a generic chatbot.

---

# 4. Product Vision

> **Build a health resource intelligence layer so no PHC runs out of a life-saving medicine while a neighbouring facility lets the same medicine expire.**

Long term, the platform should function as shared public health infrastructure, where:

- Each state keeps its facility-level data (health is a State subject).
- A common data contract defines how facilities, stock, beds, staff and transfers are represented.
- Shared APIs expose stock visibility, forecasts, warnings and recommendations.
- Predictive models are shared across states because they consume standardised features.
- New states are onboarded through data adapters rather than a rebuilt application.

---

# 5. Product Goals

## 5.1 Primary Goals

1. Let PHC staff report stock, beds and attendance quickly by voice, text or register photo.
2. Use Google AI to turn spoken or handwritten reports into structured stock records.
3. Show real-time days of stock cover for each facility and essential medicine.
4. Show bed availability and staff presence.
5. Forecast weekly medicine demand per facility.
6. Warn early about likely stock-outs.
7. Detect unusual demand surges that may indicate an outbreak.
8. Recommend stock redistribution between facilities and districts with explanations.
9. Demonstrate a common data model and a shared forecast model across at least two state configurations.
10. Deliver a working, deployed end-to-end prototype.

## 5.2 Secondary Goals

- Reduce expiry waste by moving near-expiry stock first.
- Provide an emergency scenario view (e.g. an outbreak raising demand).
- Establish reusable health supply chain APIs.
- Capture feedback on recommendations for model improvement.

---

# 6. Non-Goals for the Hackathon MVP

The prototype will not become a full hospital or health management system.

Out of scope for the MVP:

- Patient-level clinical records or any personal health information
- Electronic health records / prescriptions
- Procurement tendering and supplier management
- Payments and finance
- Replacing existing state drug-distribution systems (integration via adapters instead)
- Biometric attendance hardware
- Cold-chain sensor hardware
- Fully automatic transfers without human approval
- Inter-state transfer execution (visibility only)

---

# 7. Target Users

The MVP contains only two application roles.

## 7.1 Primary User: PHC Staff

PHC staff (pharmacist, staff nurse, Medical Officer) are the main source of data and the first to be affected by stock-outs.

### Characteristics

- Busy, with limited time for data entry
- Mobile-first
- Often keeps paper stock registers
- May prefer a regional language
- May prefer speaking to typing

### Primary Questions

The platform should help answer:

- How do I report today's stock quickly?
- Which medicines will run out soon?
- Is an indent or transfer on the way?
- Are patient numbers unusually high for something?
- What should I do next?

---

## 7.2 Secondary User: District Health Officer

The District Health Officer represents the government side: district health administration, with state-level views for state officials.

### Primary Needs

The District Health Officer should be able to:

- See stock cover, beds and staff presence across all facilities.
- Identify facilities at risk of stock-out.
- See demand surges that may indicate outbreaks.
- Review and approve redistribution recommendations.
- Compare districts and view state-level readiness.

### MVP Scope

The District Health Officer experience is primarily a dashboard with one action workflow:

- Dashboard
- Facility map
- Risk indicators
- Early warnings
- Redistribution recommendations (review and approve)
- State comparison / configuration

Wider administrative workflows (procurement, HR) are outside the MVP.

---

# 8. Core Product Experience

The product centres on one high-quality end-to-end journey:

```text
PHC Staff
   ↓
Report Stock (voice / text / register photo)
   ↓
AI Extraction → Structured Stock Record
   ↓
Confirmation (in staff's language)
   ↓
Real-time Stock Cover + Beds + Staff
   ↓
Demand Forecast
   ↓
Stock-out Warning / Surge Alert
   ↓
Redistribution Recommendation (optimised)
   ↓
AI Explanation
   ↓
District Health Officer Approves
   ↓
Both Facilities Notified
   ↓
Receipt Confirmed
```

This journey is the primary demonstration for the hackathon.

---

# 9. Module 1: Facility & Resource Registry

## Purpose

Create a simple digital representation of each facility and its resources.

### Facility Data

- Facility ID (mapped to the national Health Facility Registry ID where available)
- Name and type (PHC / CHC / district warehouse)
- State, district, block
- Location
- Linked district warehouse
- Replenishment lead time
- Total beds
- Sanctioned staff positions

### Medicine Master

- Essential medicine list (national list plus state list)
- Drug code, name, strength, form
- Common local and brand names (for voice matching)
- Tracer-drug flag (a priority subset for the MVP)

### Requirements

The system must allow a demo user to:

- Select a facility.
- View its medicines, beds and staff.
- See its location and linked warehouse.

---

# 10. Module 2: Stock Capture

## Purpose

Make stock reporting take seconds so the data is truly real-time.

### Capture Methods (MVP)

- **Voice**: "Paracetamol 500, 1,200 tablets left. ORS 40 packets. Amoxicillin finished."
- **Text**: short free-text message
- **Register photo**: photo of a handwritten stock register page
- **Form**: simple structured web form (fallback)

### Google AI Role

- **Speech-to-Text** transcribes voice.
- **Gemini** extracts line items (medicine, quantity, unit) and matches them to the medicine master.
- **Gemini multimodal** reads handwritten register tables.

### Requirements

- Extracted items are shown for confirmation before saving.
- Unrecognised medicines are flagged for review.
- Every stock record keeps its source (voice / text / photo / form) and timestamp.

---

# 11. Module 3: Beds & Staff Attendance

## Purpose

Provide visibility into beds and personnel alongside medicines.

### Beds

- Total, occupied and available beds
- Updated by quick command or form

### Staff Attendance

- Daily check-in by staff through the web app
- Location check against a geo-fence around the facility
- Designed as an adapter, so data from existing attendance systems can be imported instead

### Requirement

Dashboards show **aggregate presence** (e.g. "4 of 6 staff present"), not continuous tracking of individuals.

---

# 12. Module 4: Real-time Stock Visibility

## Purpose

Show, for every facility and medicine, how long current stock will last.

### Inputs

- Stock on hand
- Stock in transit
- Recent daily consumption
- Forecast demand
- Expiry dates (where available)

### Output

- **Days of cover** per facility × medicine
- Stock status: Adequate / Low / Critical / Stocked out
- Near-expiry stock

### Example

```text
PHC Melur – Stock Status

Paracetamol 500mg     42 days   Adequate
ORS sachet             3 days   Critical
Amoxicillin 500mg      0 days   Stocked out
Zinc 20mg             11 days   Low
```

---

# 13. Facility Readiness Score

The prototype should present an easy-to-understand readiness score per facility.

Example:

```text
Facility Readiness
68 / 100
Moderate
```

### Factors

- Essential medicine stock cover
- Bed availability
- Staff presence
- Reporting freshness
- Demand surge signal

### MVP Implementation

The score uses a **transparent weighted model**:

```text
Facility Readiness =
  Stock Cover Score × 40%
+ Bed Availability × 20%
+ Staff Presence × 20%
+ Reporting Freshness × 10%
+ Surge Stability × 10%
```

The weights are configurable and documented.

### Future Evolution

The rule-based score can later be replaced or supplemented by a Vertex AI predictive model.

---

# 14. Module 5: Demand Forecasting

## Purpose

Predict how much of each medicine each facility will need.

### Inputs

- Historical consumption
- Patient footfall
- Seasonality (e.g. monsoon diarrhoea, dengue and malaria seasons)
- Weather (rainfall, temperature)
- Disease surveillance signals (district level)
- Holidays and local events

### Output

- Weekly demand forecast per facility × medicine, 1–8 weeks ahead
- Range (low / expected / high)

### MVP Technical Approach

- **Vertex AI** forecasting or **BigQuery ML** time-series forecasting for tracer medicines
- Compared against a simple baseline (e.g. the same week last year / moving average)

### Important Modelling Detail

When a facility is stocked out, recorded consumption is zero. That does **not** mean demand was zero. These periods must be flagged so the model doesn't learn that stock-outs mean low demand.

---

# 15. Module 6: Early Warning

## Purpose

Warn **before** a stock-out happens, and detect unusual demand that may signal an outbreak.

### 15.1 Stock-out Warning

```text
Stock-out Risk = probability that demand during the replenishment lead time
                 exceeds (stock on hand + stock in transit)

Low < 50%  ·  Medium 50–80%  ·  High > 80%  ·  Stocked out = immediate
```

### 15.2 Demand Surge Detection

- Detect unusual increases in specific medicine groups or footfall compared with the expected level (e.g. ORS and zinc rising sharply across several PHCs in one block after floods).
- Flag it as a **possible outbreak signal** for the district health team to verify.

### 15.3 Emergency Scenario View

- Apply a demand multiplier to a region and medicine group (e.g. "dengue outbreak: 3× paracetamol and IV fluids for 4 weeks").
- Show projected stock-outs by week and what redistribution can cover.

### Example

```text
Early Warning – Block X

Possible acute diarrhoea cluster
ORS use 3.2× normal across 6 PHCs after recent flooding.

Stock-out Risk: High (78%) within 5 days at 4 PHCs.

Suggested next steps
• Notify the district surveillance officer to verify.
• Review redistribution recommendations below.
```

### Safety Requirement

Surge alerts are **possible signals for verification**, not confirmed outbreaks.

---

# 16. Module 7: Redistribution Recommendations

## Purpose

Move surplus stock to where it's needed before patients go without.

### Approach

- **Optimisation engine** (Google OR-Tools, open source) finds the best transfers:
  - From facilities or warehouses with surplus (especially near-expiry stock)
  - To facilities at risk
  - Within travel-time limits (Google Maps Routes API)
  - Without taking donors below their safety stock
- **Gemini** explains each recommendation in plain language and drafts the transfer note.
- A **human approves** every transfer.

### Recommendation Output

1. From facility → to facility
2. Medicine and quantity
3. Reason (risk at receiver, surplus / expiry at donor)
4. Travel time
5. Impact (stock-out days avoided)
6. Status: Proposed → Approved → Dispatched → Received

### Example

```text
Recommended Transfer

Move 2,000 ORS sachets
From: PHC Y (112 days of cover, 600 expiring in 45 days)
To:   PHC Z (2 days of cover, demand surge)
Travel time: 52 minutes

Why: Prevents a likely stock-out at PHC Z during a possible diarrhoea cluster
while using stock at PHC Y that would otherwise expire.
```

### Cross-district

Transfers across district boundaries can be enabled by state policy and are clearly marked.

---

# 17. Module 8: Multilingual Support & Voice

## MVP Languages

The prototype should demonstrate at least:

- English
- Hindi
- Tamil

The architecture should support additional Indian languages without redesigning the core application.

### Flow

```text
Staff Speech
     ↓
Speech-to-Text
     ↓
Gemini Extraction + Medicine Matching
     ↓
Confirmation (translated)
     ↓
Text-to-Speech (where supported)
```

### Requirement

Staff can report and receive confirmations and alerts in their preferred language. Medicine names are always shown in their standard form alongside any local name.

---

# 18. Module 9: District Health Officer Dashboard

## Purpose

Show how facility-level data aggregates into district and state health readiness.

### Dashboard Levels

```text
India
 ↓
State
 ↓
District
 ↓
Block
 ↓
Facility
```

### Dashboard Metrics

- Facilities reporting (and how recently)
- Facilities at stock-out risk
- Medicines at risk
- Bed availability
- Staff presence
- Demand surge alerts
- Pending redistribution recommendations
- Near-expiry stock

### Map View

The dashboard should visualise:

- Facilities coloured by readiness / risk
- Surge alert areas
- Recommended transfer routes

The MVP can use realistic sample data, clearly labelled, where live state data is unavailable.

---

# 19. Module 10: Shared Predictive Models Across States

## Purpose

Meet the brief's requirement for **shared predictive modelling across India's states**.

### Approach

- Forecasting models consume **standardised features** from the common data model.
- A base forecast model is registered in **Vertex AI Model Registry** with a model card (training data scope, accuracy, limitations).
- Each state configuration can **reuse** the base model and fine-tune it on its own data, then publish its accuracy back.
- Facility-level data stays within the state's scope. Only models and aggregate metrics are shared.

### MVP Scope

- At least one shared model registered with a model card.
- At least two state configurations using it.

### Future

Federated learning (e.g. with the open-source Flower framework), so states train a common model without moving facility data.

---

# 20. Module 11: Interoperability Layer

This is a core architectural requirement and a major differentiator of the solution.

## Objective

Provide a common data and service structure so different Indian states can participate without separate applications.

### Core Principle

> **State-specific data, common interfaces.**

Each state may have:

- Different drug-distribution software
- Different essential medicine lists
- Different facility coding
- Different reporting formats
- Different models

But the platform exposes a standardised canonical representation.

---

# 21. Common Health Resource Data Model

Example:

```json
{
  "state": "TN",
  "district": "Madurai",
  "facility_id": "PHC-TN-MDU-014",
  "hfr_id": "IN33XXXXXXXX",
  "timestamp": "2026-08-12T10:30:00+05:30",
  "stock": [
    {
      "drug_code": "ORS-SACHET",
      "on_hand": 40,
      "in_transit": 0,
      "days_of_cover": 3,
      "near_expiry_qty": 0
    }
  ],
  "beds": { "total": 6, "occupied": 5 },
  "staff": { "sanctioned": 6, "present": 4 },
  "footfall": { "opd_today": 142 },
  "risk": { "stockout_risk": 0.78, "surge_flag": true }
}
```

The same structure should support examples such as:

```text
Tamil Nadu → Monsoon diarrhoea season
Uttar Pradesh → Dengue / vector-borne season
Odisha → Malaria season
```

The MVP does not need complete national coverage. It needs to prove that the architecture is state-agnostic.

---

# 22. Interoperability Principles

## 22.1 Common Interfaces

State services expose compatible APIs.

## 22.2 Canonical Schema

Core concepts have common definitions for:

- Facility
- Medicine
- Stock Transaction
- Stock Snapshot
- Beds
- Staff Attendance
- Forecast
- Alert
- Transfer

## 22.3 State Data Adapters

A state-specific adapter transforms local formats (e.g. exports from state drug-distribution software) into the canonical schema.

```text
State Dataset
     ↓
State Adapter
     ↓
Canonical Health Resource Schema
     ↓
Shared Platform Services
```

## 22.4 Model Portability

Forecast and risk models consume standardised feature structures, so they can be shared across states.

## 22.5 Standards Alignment

- National Health Facility Registry IDs as facility keys
- LGD codes for administrative units
- National / WHO essential medicine lists as the base medicine master
- FHIR-aligned export for supply resources (roadmap)

## 22.6 API-First Design

External government and partner applications should eventually be able to consume:

- Stock visibility
- Facility readiness
- Forecasts
- Early warnings
- Redistribution recommendations

---

# 23. System Architecture

```text
                         PHC STAFF
                            │
                ┌───────────┴───────────┐
                │                       │
             Web/PWA            Voice / Photo
                │                       │
                └───────────┬───────────┘
                            ▼
                     Next.js Frontend
                            │
                            ▼
                        API Layer
                            │
     ┌──────────────┬───────┴───────┬───────────────┐
     ▼              ▼               ▼               ▼
 Capture        Visibility      Forecast &      Redistribution
 Service        Service         Warning Service Service (OR-Tools)
     │              │               │               │
     └──────────────┴───────┬───────┴───────────────┘
                            ▼
                 Health Resource Data Layer
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
      BigQuery          Firebase         Cloud Storage
          │
   ┌──────┴──────────────────────┐
   ▼                             ▼
Public Data                  State Data
 ├── Facility registry        ├── Tamil Nadu
 ├── Medicine lists           ├── Uttar Pradesh
 ├── Health statistics        ├── Odisha
 └── Weather                  └── Other States
   └─────────────┬───────────────┘
                 ▼
            AI / ML Layer
                 │
     ┌───────────┼────────────┐
     ▼           ▼            ▼
  Gemini     Vertex AI     Gemini
 Extraction  Forecasting   Multimodal
 & Explain   & Anomaly     (registers)
     └───────────┼────────────┘
                 ▼
   Visibility / Warning / Recommendation
                 │
         ┌───────┴────────┐
         ▼                ▼
   PHC Staff Alert   District Officer Approval
 (Translation + Voice)
```

---

# 24. Recommended Technology Stack

## 24.1 Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- PWA capabilities (with offline-friendly data entry as a goal)
- Google Maps JavaScript API

### Frontend Responsibilities

- Facility selection
- Stock capture (voice, text, photo, form)
- Confirmation screens
- Beds and attendance entry
- Facility stock status
- Language switching and voice
- District Health Officer dashboard
- Redistribution review and approval

---

# 25. Backend

## Recommended

**Google Cloud Run** (+ Cloud Scheduler for forecast and warning jobs)

Backend may be implemented using:

- FastAPI / Python for AI, forecasting and optimisation services
- Node.js where application services benefit from it

### Responsibilities

- API routing
- Stock capture and extraction
- Stock ledger and days-of-cover calculation
- Forecast and warning jobs
- Surge detection
- Redistribution optimisation
- Approval workflow
- State adapters
- Authentication / authorisation

---

# 26. Google AI Technology Stack

## Gemini API / Vertex AI

Use for:

- Extracting stock line items from voice transcripts and text
- Matching local medicine names to the medicine master
- Explaining redistribution recommendations
- Writing early-warning summaries
- Drafting transfer notes

## Gemini Multimodal

Use for:

- Reading handwritten stock register photos
- Extracting table rows and quantities

## Vertex AI / BigQuery ML

Use for:

- Demand forecasting
- Demand surge (anomaly) detection
- Shared model registry
- Model training and serving

## Google OR-Tools (open source, by Google)

Use for:

- Redistribution optimisation

## Google AI Studio

Use for:

- Prompt experimentation
- Evaluating extraction behaviour
- Initial prompt development

---

# 27. Geospatial Stack

## Google Maps Platform

- Facility map
- Travel-time calculation between facilities (Routes API)
- Transfer route visualisation

## Google Earth Engine (optional)

- Rainfall and flood extent as covariates for surge and demand forecasting

---

# 28. Data Platform

## BigQuery

Primary analytical store for:

- Stock ledger (every receipt, issue, adjustment, transfer, expiry)
- Stock snapshots and days of cover
- Beds, attendance and footfall
- Forecasts and warnings
- Model features
- State-level analytics

## Firebase

Use for:

- Authentication
- Real-time dashboard updates
- Lightweight application state

## Cloud Storage

Use for:

- Register photos
- Voice recordings
- Model artifacts

---

# 29. Public Data Sources

The architecture should be able to consume data from sources such as:

- **Rural Health Statistics** (Ministry of Health): facility, bed and staff counts by district
- **HMIS** public reports: service volumes and seasonality
- **National List of Essential Medicines** and state essential medicine lists
- **Health Facility Registry** (national digital health mission): facility identifiers
- **Integrated Disease Surveillance Programme** weekly outbreak reports
- **IMD** weather data
- **WHO** Global Health Observatory data
- data.gov.in and state health portals

Where live APIs are unavailable during the hackathon, use realistic sample or cached public data.

Every dataset must keep its source metadata and timestamps.

---

# 30. Data Architecture

```text
Staff Capture (voice/text/photo)     State Systems / Public Data
             │                                  │
             ▼                                  ▼
      AI Extraction                      Data Ingestion
             │                                  │
             ▼                                  ▼
      Confirmation                   Validation / Normalisation
             │                                  │
             │                        State Adapter (where needed)
             └────────────────┬─────────────────┘
                              ▼
            Canonical Health Resource Schema
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
             BigQuery                Feature Data
                 │                         │
                 └────────────┬────────────┘
                              ▼
             Forecast / Warning / Optimisation
                              │
                              ▼
          Visibility / Alerts / Recommendations
```

---

# 31. Core Data Entities

## Facility

```text
facility_id
hfr_id
name
type
state
district
block
location
warehouse_id
lead_time_days
beds_total
staff_sanctioned
```

## Medicine

```text
drug_code
name
strength
form
local_names[]
is_tracer
```

## Stock Transaction

```text
transaction_id
facility_id
drug_code
type (receipt / issue / adjustment / expiry / transfer_in / transfer_out)
quantity
batch
expiry_date
source (voice / text / photo / form / adapter)
created_at
model_name
model_version
prompt_version
```

## Stock Snapshot

```text
facility_id
drug_code
on_hand
in_transit
days_of_cover
status
stockout_risk
near_expiry_qty
updated_at
```

## Beds & Attendance

```text
facility_id
date
beds_total
beds_occupied
staff_present
staff_sanctioned
source
```

## Forecast

```text
facility_id
drug_code
week
demand_low
demand_expected
demand_high
model_name
model_version
```

## Alert

```text
alert_id
type (stockout_risk / surge / stocked_out)
facility_ids[]
drug_codes[]
severity
summary
created_at
language
model_name
model_version
prompt_version
```

## Transfer

```text
transfer_id
from_facility_id
to_facility_id
drug_code
quantity
reason
travel_minutes
status (proposed / approved / dispatched / received)
approved_by
explanation
created_at
model_name
model_version
prompt_version
```

---

# 32. AI Orchestration Architecture

AI services follow a predictable pipeline.

```text
Staff Report / Scheduled Job
      ↓
Retrieve Facility Context
      ↓
Validate Data
      ↓
Gemini Extraction / Multimodal (for reports)
      ↓
Schema Validation + Medicine Matching
      ↓
Update Stock Ledger
      ↓
Vertex AI Forecast
      ↓
Stock-out Risk + Surge Detection (deterministic + model)
      ↓
OR-Tools Redistribution
      ↓
Gemini Explanation (from optimiser output only)
      ↓
Structured JSON Output
      ↓
Validation
      ↓
Localisation
      ↓
Presentation / Voice / Approval
```

The optimiser decides the transfers. Gemini explains them and never changes the quantities.

---

# 33. Structured AI Output

AI services return structured outputs rather than free text.

## Stock Extraction

```json
{
  "items": [
    { "spoken_name": "Paracetamol 500", "drug_code": "PCM-500-TAB", "quantity": 1200, "unit": "tablet", "match_confidence": 0.97 },
    { "spoken_name": "ORS", "drug_code": "ORS-SACHET", "quantity": 40, "unit": "sachet", "match_confidence": 0.95 },
    { "spoken_name": "Amoxicillin", "drug_code": "AMX-500-CAP", "quantity": 0, "unit": "capsule", "match_confidence": 0.9 }
  ],
  "unrecognised": [],
  "requires_confirmation": true
}
```

## Redistribution Explanation

```json
{
  "summary": "Move 2,000 ORS sachets from PHC Y to PHC Z.",
  "risk_level": "high",
  "reasons": [
    "PHC Z has 2 days of cover during a demand surge",
    "PHC Y has 112 days of cover with 600 sachets expiring in 45 days"
  ],
  "impact": "Avoids an estimated 9 stock-out days at PHC Z",
  "travel_minutes": 52,
  "confidence": 0.85,
  "requires_human_review": true
}
```

---

# 34. Prompt Architecture

Use specialised prompts for distinct capabilities.

## 34.1 Stock Extraction Prompt

### Inputs

- Transcript or text
- Facility's medicine master (with local names)

### Requirements

- Extract only the items mentioned.
- Never invent quantities.
- Match to the medicine master and give a match confidence.
- List unrecognised items separately.
- Return structured JSON.

## 34.2 Register Photo Prompt

### Inputs

- Register photo
- Medicine master

### Requirements

- Extract table rows (medicine, opening, received, issued, closing).
- Mark illegible cells as unknown rather than guessing.
- Return structured JSON for confirmation.

## 34.3 Recommendation Explanation Prompt

### Inputs

- Optimiser output
- Facility stock snapshots
- Forecasts and warnings

### Requirements

- Use only the supplied numbers.
- Explain in simple language.
- State the impact and any uncertainties.
- Return structured JSON.

---

# 35. AI Safety & Trust

The platform must distinguish between:

```text
Reported Data
      ↓
AI Interpretation / Forecast
      ↓
Recommendation
```

### Requirements

- Never fabricate stock quantities.
- Always confirm AI-extracted stock with staff before saving.
- Never present a surge as a confirmed outbreak.
- Never execute transfers without human approval.
- Never take donor stock below safety levels.
- Include confidence for extraction and forecasts.
- Show how fresh each facility's data is.
- Store no patient-level personal health data.

---

# 36. Data Freshness

Every data source should expose freshness metadata.

Example:

```text
Stock (PHC Melur)
Reported: 2 hours ago (voice)

Beds
Updated: this morning

Staff Attendance
Updated: 09:40 today

Forecast
Generated: Monday
```

The District Health Officer should understand whether a warning is based on:

- A report from today
- An older report
- A forecast

Facilities that haven't reported recently are highlighted.

---

# 37. API Architecture

## Facilities

```http
GET /api/facilities?state=&district=
GET /api/facilities/:id
```

## Capture

```http
POST /api/capture/voice
POST /api/capture/text
POST /api/capture/photo
POST /api/capture/:id/confirm
POST /api/facilities/:id/beds
POST /api/facilities/:id/attendance
```

## Visibility & Intelligence

```http
GET /api/facilities/:id/stock
GET /api/facilities/:id/readiness
GET /api/facilities/:id/forecast
GET /api/alerts?district=
```

## Redistribution

```http
POST /api/redistribution/optimize
GET  /api/transfers?district=&status=
POST /api/transfers/:id/approve
POST /api/transfers/:id/dispatch
POST /api/transfers/:id/receive
```

## Scenarios

```http
POST /api/scenarios/simulate
```

## Language / Voice

```http
POST /api/speech-to-text
POST /api/translate
POST /api/text-to-speech
```

## State / Models / Analytics

```http
GET /api/states
GET /api/states/:id/analytics
GET /api/models
GET /api/models/:id/card
```

---

# 38. Functional Requirements

## FR-01: Facility Access

The system must allow a PHC staff member or demo user to access their facility.

### Acceptance Criteria

- User can sign in or select a demo facility.
- Preferred language can be selected.
- Facility details are displayed.

---

## FR-02: Stock Capture

### Acceptance Criteria

- Stock can be reported by voice.
- Stock can be reported by text.
- Stock can be reported by register photo.
- Extracted items are shown for confirmation.
- Confirmed items update the stock ledger.

---

## FR-03: Beds & Attendance

### Acceptance Criteria

- Bed availability can be updated.
- Staff can check in.
- Aggregate presence is displayed.

---

## FR-04: Real-time Visibility

### Acceptance Criteria

- Days of cover is displayed per medicine.
- Stock status is displayed.
- Facility readiness score is displayed with a breakdown.

---

## FR-05: Demand Forecast

### Acceptance Criteria

- Weekly forecast is displayed for tracer medicines.
- Forecast range is shown.
- Accuracy compared with a simple baseline is documented.

---

## FR-06: Early Warning

### Acceptance Criteria

- Stock-out risk is calculated and displayed.
- Demand surges are flagged as possible signals.
- Alerts are shown to staff and the District Health Officer.

---

## FR-07: Redistribution Recommendation

### Acceptance Criteria

- At least one transfer recommendation is generated by the optimiser.
- Donor safety stock is respected.
- Gemini explanation is displayed.
- District Health Officer can approve.
- Status updates through to "received".

---

## FR-08: Multilingual & Voice

### Acceptance Criteria

- Staff can switch between English, Hindi and Tamil.
- At least one complete voice stock report works.
- Confirmation can be played as audio.

---

## FR-09: District Health Officer Dashboard

### Acceptance Criteria

Officer can view:

- District overview
- Facility map with readiness / risk
- Early warnings
- Pending transfers
- Reporting freshness

---

## FR-10: Interoperability & Shared Models

### Acceptance Criteria

The prototype demonstrates:

- Canonical health resource schema.
- At least two state configurations.
- State-specific data mapped into the common model.
- A shared forecast model with a model card used by both configurations.

---

## FR-11: Emergency Scenario (Secondary)

### Acceptance Criteria

- A demand multiplier can be applied to a region and medicine group.
- Projected stock-outs by week are displayed.

---

# 39. Non-Functional Requirements

## Performance

- Fast initial application load
- Standard API response under about 2 seconds where practical
- Voice report → confirmation in about 15 seconds where practical
- Clear loading states for AI and optimisation operations

## Scalability

The system should support:

- Multiple states
- Tens of thousands of facilities
- Hundreds of medicines
- Multiple languages
- Horizontal cloud scaling

## Reliability

- Don't lose reports (queue them and retry).
- Handle poor connectivity gracefully (offline-friendly entry as a goal).
- Show clear fallback states when AI services fail (form entry is always available).
- Keep dashboards working if one data source fails.

## Accessibility

- Mobile-first
- Touch-friendly
- Regional-language capable
- Voice-capable
- Designed for busy frontline staff

## Security

- HTTPS
- Protect API secrets
- Authenticated APIs
- Role-based access
- No patient-level data
- Secure photo and audio storage
- Least-privilege cloud permissions

---

# 40. State Onboarding Architecture

A new state can be onboarded without rewriting the core application.

## Onboarding Flow

```text
Register State
      ↓
Load Facility List (registry IDs)
      ↓
Load State Essential Medicine List
      ↓
Register Data Sources (drug distribution exports)
      ↓
Map Local Fields to Canonical Schema
      ↓
Validate Data
      ↓
Configure Languages, Lead Times, Safety Stock Rules
      ↓
Select / Fine-tune Shared Forecast Model
      ↓
Enable APIs
      ↓
State Becomes Available
```

## Example

```text
State: Tamil Nadu

Local Drug Distribution Export
     ↓
TN Adapter
     ↓
Canonical Schema
     ↓
Shared Forecast Model + Shared AI Services
```

The same pattern can be used for Uttar Pradesh, Odisha or any future state.

---

# 41. Repository Structure

```text
health-resource-network/
│
├── apps/
│   ├── phc-web/
│   └── officer-dashboard/
│
├── services/
│   ├── api/
│   ├── capture/
│   ├── visibility/
│   ├── forecasting/
│   ├── early-warning/
│   ├── redistribution/
│   └── localization/
│
├── ai/
│   ├── prompts/
│   ├── schemas/
│   ├── models/
│   └── evaluation/
│
├── data/
│   ├── schemas/
│   ├── adapters/
│   ├── sample/
│   ├── generator/
│   └── transformations/
│
├── infrastructure/
│   ├── cloud-run/
│   ├── bigquery/
│   └── firebase/
│
├── docs/
│
└── README.md
```

---

# 42. MVP Data Strategy

Prioritise **real or realistic** data over complicated ingestion.

## Use real / public data where feasible

- Facility counts, beds and staff by district (Rural Health Statistics)
- Essential medicine lists
- Seasonality patterns (HMIS public reports)
- Weather

## Use realistic sample data where needed

- **Facility-level stock transactions**: a transparent data generator producing about 3 years of daily data for about 200 facilities across 2–3 states, based on public seasonality and facility counts, with injected outbreaks and stock-outs. **Clearly labelled synthetic.**
- **Register photos**: team-made sample register pages.

## Data Source Metadata

Every dataset retains:

- Source
- Observation timestamp
- Dataset version
- Geographic scope
- "Synthetic / sample" flag where applicable

---

# 43. Recommended MVP Demo Scenarios

## Scenario A

```text
State: Tamil Nadu
District: Madurai
Language: Tamil (voice)
Situation: Post-flood diarrhoea surge → ORS stock-out risk
```

## Scenario B

```text
State: Uttar Pradesh
District: Gorakhpur
Language: Hindi
Situation: Vector-borne season → paracetamol / IV fluid demand forecast
```

## Scenario C

```text
State: Odisha
District: Koraput
Language: English
Situation: Malaria season → antimalarial redistribution
```

The number of demo states doesn't matter much. The point is to prove that one platform structure supports different state, season and medicine combinations.

---

# 44. Hackathon Demo Flow

The demo should be one continuous story rather than a collection of disconnected features.

## 0:00–0:30: Introduce the PHC

> Meet a staff nurse at a PHC in Madurai. Floods hit last week, and more patients are arriving with diarrhoea.

## 0:30–1:10: Stock Report

Show:

- Tamil voice stock report
- AI extraction and confirmation
- Register photo extraction

## 1:10–1:40: Real-time Visibility

Show:

- Days of cover
- Beds and staff presence
- Facility readiness score

## 1:40–2:20: Forecast & Early Warning

Show:

- Demand forecast
- Stock-out risk
- Surge alert across nearby PHCs

## 2:20–3:00: Redistribution

Show:

- Optimiser recommendation
- Gemini explanation
- District Health Officer approval
- Both facilities notified

## 3:00–3:30: District Dashboard

Show the facility map, warnings and transfer routes.

## 3:30–4:10: Interoperability & Shared Models

Switch to Uttar Pradesh and show the common data structure and the shared forecast model card.

## 4:10–4:30: Emergency Scenario

Apply an outbreak multiplier and show projected stock-outs.

## 4:30–5:00: Scale & Deployment

```text
One PHC
   ↓
One Block
   ↓
One District
   ↓
One State
   ↓
Multiple States
   ↓
National Health Resource Intelligence Network
```

Show the Google AI / Cloud stack powering the solution.

---

# 45. Deployment Architecture

```text
                         Internet
                            │
                            ▼
                    Google Cloud Platform
                            │
                         Cloud Run
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
     Next.js App       API Layer         AI Services
          │                 │          (+ OR-Tools optimiser)
          │          Cloud Scheduler          │
          ▼                 ▼                 ▼
       Firebase         BigQuery          Vertex AI
                                              │
                                              ▼
                                           Gemini
                            │
                            ▼
                      External Data
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
    Facility Registry   Maps Routes API    State Systems
```

Primary region: `asia-south1` (Mumbai).

---

# 46. Environment & Secrets

Secrets must never be committed to GitHub.

Example configuration:

```text
GEMINI_API_KEY
GOOGLE_CLOUD_PROJECT
GOOGLE_APPLICATION_CREDENTIALS
BIGQUERY_DATASET
FIREBASE_PROJECT_ID
MAPS_API_KEY
```

Store them in Secret Manager for Cloud Run.

---

# 47. Observability

The system should log:

- API latency
- AI request latency
- AI failures and schema-validation failures
- Extraction confirmation / correction rate
- Facility reporting gaps
- Forecast and warning job runs
- Optimiser runs and results
- Dataset freshness
- Model and prompt version
- Transfer status changes

Future production metrics:

- Reporting compliance
- Stock-out days
- Expiry waste
- Transfer approval and completion rate
- Forecast accuracy

---

# 48. AI Evaluation

A basic internal evaluation layer should test:

## Stock Extraction

- Line-item accuracy (medicine + quantity) on sample voice and text reports
- Medicine-matching accuracy for local names

## Register Photos

- Cell-level accuracy on sample register photos

## Forecasting

- Accuracy compared with a simple baseline

## Early Warning

- Backtest: share of past stock-outs that would have been warned about in advance

## Explanations

- Every number in an explanation matches the optimiser output

## Multilingual

- Transcription quality
- Medicine-name handling across languages

The hackathon MVP doesn't need a formal scientific evaluation system, but the architecture should make evaluation possible.

---

# 49. Success Metrics

## 49.1 Hackathon Success

The prototype should demonstrate:

- Complete end-to-end report → warning → transfer flow
- Meaningful Google AI integration
- Voice, text and photo stock capture
- Stock, beds and attendance visibility
- Demand forecast
- Stock-out warning and surge detection
- Optimised redistribution with explanation and approval
- Multilingual voice interaction
- District Health Officer dashboard
- Multiple state configurations
- Shared forecast model
- Public deployment
- Public or access-granted GitHub repository

## 49.2 Long-Term Impact Metrics

### Patient Impact

- Reduction in stock-out days for essential medicines
- Patients served without out-of-pocket medicine purchases

### System Impact

- Facilities reporting regularly
- Near-expiry stock redistributed instead of wasted
- Warning lead time before stock-outs
- Outbreak signals detected early

### Platform Impact

- States integrated
- Facilities covered
- Shared models reused
- API consumers

---

# 50. Scalability Strategy

## Phase 1: Hackathon

```text
2–3 state configurations
~200 synthetic facilities
~30 tracer medicines
3 languages
```

## Phase 2: District Pilot

```text
1 district (~20–40 PHCs)
Real opening stock from state systems
Staff reporting by voice / photo
District Health Officer approvals
```

## Phase 3: State Deployment

```text
State-level integration with drug distribution software
State-specific model fine-tuning
More languages
Offline-first capture
```

## Phase 4: National Network

```text
Multiple states
Shared data contracts
Shared model registry
Federated learning
National readiness view for emergencies
```

---

# 51. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| No real facility data during the hackathon | Transparent synthetic generator based on public patterns. Show that the adapter accepts a state export format. |
| Staff reporting fatigue | Voice and photo capture take seconds. Ask only about high-risk medicines. |
| Medicine name ambiguity | Medicine master with local names, match confidence and confirmation |
| Forecast errors | Show ranges, compare with a baseline, keep a human in the loop |
| Stock-outs hide true demand | Flag stock-out periods in training data |
| Transfers weaken donors | Safety-stock constraint and human approval |
| Attendance privacy concerns | Aggregate presence only, check-in rather than tracking, clear notices |
| State data incompatibility | Canonical schema + state adapters |
| Poor connectivity | PWA with offline-friendly entry as a goal, and retry queues |
| Vendor coupling | Abstract AI and data providers behind internal service interfaces |

---

# 52. Security & Privacy

## Patient Data

The platform stores **no patient-level personal health information**. Footfall is recorded as aggregate counts only.

## Staff Data

Collect only what attendance visibility needs. Dashboards show aggregate presence.

## Photos & Audio

Store register photos and voice recordings securely with retention limits.

## Access Control

The MVP supports two roles:

```text
PHC Staff (scoped to their facility)
District Health Officer (scoped to their district; state officials to their state)
```

Role permissions should ensure:

- Staff see and update only their own facility.
- Officers see only the facilities in their authorised geography.

---

# 53. Future Roadmap

## Health Supply Intelligence

- Cold-chain monitoring for vaccines
- Staffing-gap forecasting
- Procurement planning support
- Expiry optimisation across the network

## Government Intelligence

- Integrated outbreak early warning with disease surveillance
- National emergency readiness view
- Inter-state transfer coordination

## Ecosystem

- Integration with state drug distribution systems
- FHIR-aligned supply data exchange
- Public bed-availability view (opt-in by state)
- Open health resource APIs

---

# 54. Google AI Integration Map

| Google Technology | Product Role |
|---|---|
| Gemini API | Stock extraction, medicine matching, explanations, warning summaries |
| Gemini Multimodal | Handwritten stock register reading |
| Vertex AI / BigQuery ML | Demand forecasting, surge detection, shared model registry |
| Google OR-Tools | Redistribution optimisation |
| Google AI Studio | Prompt experimentation and evaluation |
| BigQuery | Stock ledger, forecasts, analytics |
| Firebase | Authentication and real-time updates |
| Cloud Run | Backend, AI and optimisation services |
| Google Maps Platform | Facility map and travel times |
| Speech-to-Text | Voice stock reports |
| Text-to-Speech | Spoken confirmations and alerts |
| Translation API | Multilingual support |

---

# 55. Alignment with Hackathon Evaluation

## Problem-Solution Fit: 20%

The product directly addresses:

- Stock-outs
- Lack of real-time visibility (stock, beds, staff)
- Weak emergency response
- Fragmented data across facilities and states

## AI / Technical Execution: 25%

The prototype shows meaningful roles for:

- Gemini (voice and text extraction, explanations)
- Gemini multimodal (register reading)
- Vertex AI (forecasting, surge detection, shared models)
- OR-Tools (optimisation)
- Structured AI orchestration

## Depth & Reach Across India: 20%

The architecture shows:

- A state-independent data model
- Multi-state configuration
- Multi-language support
- Voice and photo capture for frontline staff
- Shared predictive models

## Impact Potential: 15%

PHCs serve a very large rural population. Fewer stock-outs directly improve access to essential care.

## Deployability & Scalability: 20%

The prototype shows:

- Cloud-native services
- API-first architecture
- State adapters that integrate with existing systems rather than replacing them
- Standardised schemas
- A deployable application

---

# 56. Definition of Done: Hackathon MVP

## PHC Staff Experience

- [ ] Staff can access the application.
- [ ] Staff can select their facility.
- [ ] Staff can report stock by voice.
- [ ] Staff can report stock by register photo.
- [ ] Staff can confirm extracted items.
- [ ] Beds and attendance can be updated.
- [ ] Days of cover is displayed.
- [ ] Facility readiness score is displayed.

## AI Experience

- [ ] Gemini extracts stock from voice / text.
- [ ] Gemini multimodal reads a register photo.
- [ ] Demand forecast is displayed.
- [ ] Stock-out risk is displayed.
- [ ] Surge alert is displayed.
- [ ] Redistribution recommendation is generated and explained.

## Language & Voice

- [ ] English supported.
- [ ] Hindi supported.
- [ ] Tamil supported.
- [ ] At least one complete voice interaction works.

## District Health Officer

- [ ] Officer dashboard exists.
- [ ] Facility map with risk is visible.
- [ ] Early warnings are visible.
- [ ] Transfers can be approved.

## Interoperability

- [ ] Canonical schema is documented.
- [ ] At least two state configurations exist.
- [ ] State-specific data maps to the common schema.
- [ ] A shared forecast model with a model card is used.

## Deployment & Submission

- [ ] Prototype is publicly deployed.
- [ ] Source code is available through GitHub.
- [ ] README contains setup and architecture documentation.
- [ ] Demo data is available and labelled.
- [ ] 3–5 minute demo video is prepared.
- [ ] 10–12 slide pitch deck is prepared.
- [ ] 2–3 line product description is prepared.

---

# 57. Recommended Build Priority

Prioritise **one polished end-to-end journey over many disconnected features**.

## Priority 1: Core Experience

```text
Stock Report (voice / photo)
 ↓
Gemini Extraction + Confirmation
 ↓
Days of Cover
 ↓
Forecast + Stock-out Risk
 ↓
Redistribution Recommendation + Explanation
 ↓
Approval
```

## Priority 2: Accessibility

```text
Multilingual
 ↓
Voice interaction
```

## Priority 3: Scale Story

```text
District Health Officer Dashboard
 ↓
Multi-state configurations
 ↓
Shared forecast model
```

## Priority 4: Future / Optional

```text
Surge detection (keep a simple threshold version if time is short)
Emergency scenario view
Offline synchronisation
```

Don't sacrifice the core report-to-redistribution journey to add lower-priority features.

---

# 58. Final Product Definition

The solution is an **AI-powered interoperable health resource intelligence network** for India's Primary Health Centres.

At the facility level:

```text
            PHC STAFF
               │
               ▼
   VOICE / TEXT / REGISTER PHOTO
               │
               ▼
         AI EXTRACTION
               │
      ┌────────┼────────┐
      ▼        ▼        ▼
    STOCK     BEDS     STAFF
      │        │        │
      └────────┼────────┘
               ▼
        AI HEALTH BRAIN
   Gemini + Vertex AI + OR-Tools
               │
       ┌───────┼────────┐
       ▼       ▼        ▼
   Forecast  Early   Redistribution
            Warning
       │       │        │
       └───────┼────────┘
               ▼
   Local Language / Voice + Officer Approval
               │
               ▼
     MEDICINE WHERE IT'S NEEDED
```

At the infrastructure level:

```text
    NATIONAL HEALTH RESOURCE NETWORK
                    │
           COMMON DATA MODEL
                    │
       ┌────────────┼────────────┐
       │            │            │
   Tamil Nadu  Uttar Pradesh   Odisha
       │            │            │
   Local Data   Local Data   Local Data
       │            │            │
       └────────────┼────────────┘
                    │
      Shared Models + Shared AI Services
                    │
              Shared APIs
```

The platform combines:

**Frontline capture + AI extraction + predictive modelling + optimisation + multilingual accessibility + interoperable health infrastructure**

in one scalable architecture.

The hackathon MVP should prove that the solution can move from:

> **One PHC → One block → One district → One state → Multiple Indian states**
