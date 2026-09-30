// PHC Pulse pitch deck (Build with AI (Google), Track 3), in the Spontom Enterprise proposal style.
// Build: (cd docs/pitch && npm install && node build-deck.js)  ->  docs/pitch/PHC_Pulse_Spontom_Pitch.pptx
//
// Every number on a slide comes from docs/PRD.md, the running app on its SYNTHETIC dataset
// (local run, 30 Sep 2026, scenario A) or a numbered reference on the last two slides.
const path = require("path");
const kit = require("./deck-kit");

// Live links (edit here, e.g. when friendly Firebase Hosting links are added).
const LINKS = [
  { label: "PHC staff app", url: "https://health-resource-network-phc-web-847963771142.asia-south1.run.app" },
  { label: "DHO dashboard", url: "https://health-resource-network-officer-dashboard-847963771142.asia-south1.run.app" },
  { label: "API (OpenAPI)", url: "https://health-resource-network-api-847963771142.asia-south1.run.app/docs" },
  { label: "Source", url: "https://github.com/ipavanreddy/health-resource-network" },
];

const A = (f) => path.join(__dirname, "assets", f);
const IMG_NOTE = "Illustrative image generated with Gemini 2.5 Flash Image (Google)";

const content = {
  meta: { product: "PHC Pulse", title: "Track 3 pitch deck" },
  slides: [
    // 1. Cover
    {
      type: "cover",
      kicker: "Build with AI (Google)  •  Track 3",
      product: "PHC\nPulse",
      tagline: "No stock-out here while the\nsame medicine expires next door.",
      subtitle: "Voice and photo stock reporting, demand forecasts and optimised transfers for Primary Health Centres, approved by the District Health Officer.",
      pills: ["AI-assisted", "Officer-approved", "State-ready"],
      image: A("cover-phc-nurse.jpg"),
      imageCaption: IMG_NOTE + ". Not a real person or facility.",
      byline: "A concept proposal and working prototype by Spontom Enterprise Private Limited",
      dateline: "DPIIT Recognised  •  Visakhapatnam  •  September 2026",
      notes: "PHC Pulse is our answer to Track 3: national-scale health resource and supply chain management for Primary Health Centres. A PHC nurse reports stock in seconds by voice or by photographing the paper register. The system turns that into days of cover, forecasts and warnings, and proposes transfers between nearby facilities. Nothing moves until the District Health Officer approves. Everything you will see runs today on Google Cloud, on clearly labelled synthetic data.",
    },

    // 2. Problem
    {
      type: "problem",
      section: "01 — Problem understanding",
      title: "Stock-outs and expiry sit side by side.",
      subtitle: "31,882 PHCs are the first point of care [2]; their stock data sits in registers, spreadsheets and separate systems [1].",
      card: {
        heading: "One nurse, one register, one flood week.",
        stats: [{ n: "3.6×", label: "ORS + zinc use" }, { n: "2.5", label: "days of ORS left" }, { n: "450", label: "sachets expiring nearby" }],
        story: "Kavitha copies stock into a paper register each evening. The district sees it days later, after the ORS has run out.",
        pill: "SYNTHETIC SCENARIO",
      },
      flow: [
        { title: "COUNT", desc: "Paper register at the PHC" },
        { title: "REPORT", desc: "Periodic and late" },
        { title: "?", desc: "Nobody sees the surplus next door", gap: true },
        { title: "INDENT", desc: "Fixed cycle, 10-day lead time" },
      ],
      focused: "Districts cannot see in time which PHC will run out, or which nearby PHC can spare the same medicine.",
      consequence: "Patients buy medicines or travel further; surplus expires on another shelf. [1]",
      footnote: "[1] Track 3 brief; PHC Pulse PRD §2.  [2] MoHFW, Health Dynamics of India 2022–23.  Card figures: synthetic scenario A (PHC Melur, Madurai).",
      notes: "India has 31,882 Primary Health Centres, according to the Ministry's Health Dynamics of India 2022–23. Stock is still counted into paper registers and reported periodically. In our flood-week scenario, ORS and zinc use is 3.6 times normal, PHC Melur has two and a half days of ORS left, and a PHC 54 minutes away holds 450 sachets that expire in December. The problem is not a lack of medicine in the district. It is that nobody can see both facts at the same time.",
    },

    // 3. Solution
    {
      type: "solution",
      section: "02 — Proposed solution",
      title: "From a spoken report to an approved transfer.",
      subtitle: "Staff report in their language; AI structures and forecasts; an optimiser proposes; the officer decides.",
      steps: [
        { title: "REPORT", desc: "Voice in Tamil, Hindi or English, a register photo or text. Gemini extracts; staff confirm." },
        { title: "SEE + FORECAST", desc: "Days of cover, readiness score, 8-week forecast and possible-surge signals.", highlight: true },
        { title: "OPTIMISE + APPROVE", desc: "OR-Tools proposes transfers; Gemini explains; the DHO approves each one.", coral: true },
      ],
      panel: {
        header: "PROPOSED TRANSFER",
        badge: "Awaiting DHO",
        title: "451 ORS sachets • PHC Thirumangalam II → PHC Melur",
        items: [
          "Melur: 2.5 → 10.3 days of cover (stock-out risk 99.8%)",
          "Donor keeps 50.6 days; its safety stock is 45 days",
          "Uses 450 sachets that expire on 6 Dec 2026",
          "54 min drive (Google Routes API) • 7.8 stock-out days avoided",
        ],
        fallback: "Gemini flags: Melur report is 30 h old; surge unverified",
        footer: "Gemini 2.5 Flash • explain_transfer_v1",
        button: "Approve",
      },
      footnote: "Real optimiser and Gemini output from the local build (30 Sep 2026) on synthetic data. Quantities come from OR-Tools; Gemini cannot change them.",
      notes: "The solution is one loop. Staff report the way they already work, by speaking or by photographing the register. The platform shows days of cover, a readiness score, an eight-week forecast and possible surges. The panel on the right is real output: OR-Tools proposed 451 ORS sachets from Thirumangalam II to Melur on Google Routes drive times, and Gemini explained why, including what it is unsure about. The officer approves or rejects.",
    },

    // 4. How it works
    {
      type: "loop",
      section: "03 — How it works",
      title: "One journey from report to receipt.",
      subtitle: "Observed data, then AI interpretation, then a recommendation, then a human decision (PRD §35).",
      highlight: 5,
      flow: [
        { title: "Speak", desc: "Voice, photo, text or form" },
        { title: "Extract", desc: "Gemini → validated JSON" },
        { title: "Confirm", desc: "Staff edit, then save" },
        { title: "See", desc: "Cover + readiness" },
        { title: "Forecast", desc: "8 weeks + surge check" },
        { title: "Optimise", desc: "OR-Tools transfers" },
        { title: "Approve", desc: "DHO → dispatch → receipt" },
      ],
      tiers: [
        { label: "Tier 0 • Automatic", text: "Cover, risk, forecasts and surge checks recompute on every confirmed report." },
        { label: "Tier 1 • DHO review", text: "The officer verifies surge signals and approves or rejects each proposed transfer." },
        { label: "Tier 2 • State", text: "Gaps local surplus cannot cover go to a state indent; cross-district moves follow state policy." },
      ],
      assumptionLabel: "Design assumption",
      assumption: "The 45-day donor safety stock, 30-day target cover and readiness weights are defaults to set with each state.",
      footnote: "Readiness = stock cover 40 • beds 20 • staff 20 • reporting freshness 10 • surge stability 10 (PRD §13; weights per state).",
      notes: "Here is the full journey. A report is extracted by Gemini into schema-validated JSON, and the nurse confirms it before anything is saved. Cover, readiness, forecasts and surge checks then update automatically. The optimiser proposes transfers, and the District Health Officer approves them, after which the facilities dispatch and confirm receipt. Anything the district cannot cover escalates to the state. The thresholds are defaults that each state sets; they are not validated norms yet.",
    },

    // 5. Users & context
    {
      type: "users",
      section: "04 — Users & context",
      title: "Design for the PHC nurse; serve the district.",
      subtitle: "Two roles in the product: PHC Staff and District Health Officer (PRD §7). No patient-level data.",
      image: A("users-phc-register.jpg"),
      imageLabel: "Kavitha  •  Staff nurse (persona)",
      imageCaption: "PHC Melur • 6 beds • 7 staff • one paper register",
      people: [
        { name: "PHC colleagues", role: "Pharmacist / MO", desc: "Same app and facility scope: report stock, update beds, confirm receipts." },
        { name: "District officer", role: "DHO • approver", desc: "Needs trusted cover, risk and transfers for 32 facilities, not phone calls." },
        { name: "Drug warehouse", role: "District supply", desc: "10-day indent lead time; forecast shortfalls show what to send first." },
        { name: "State health dept", role: "Configures + scales", desc: "Sets weights, adapter and transfer policy; sees aggregates, not raw data." },
      ],
      constraints: [
        { label: "Little time", text: "voice report in seconds" },
        { label: "Language", text: "Tamil • Hindi • English" },
        { label: "Paper register", text: "photo, Gemini reads" },
      ],
      footnote: IMG_NOTE + ". Persona from PRD §7 and scenario A; facility figures are synthetic.",
      notes: "We designed for the PHC nurse first, because she is the source of the data and the first to feel a stock-out. She is busy, mobile-first and often prefers speaking Tamil or Hindi to typing. Around her are colleagues who use the same app, the District Health Officer who approves transfers across about 32 facilities, the district warehouse, and the state health department, which configures the platform. Each constraint maps to a design response: voice, three languages and register photos.",
    },

    // 6. Journey
    {
      type: "journey",
      section: "05 — Journey",
      title: "Scenario A: a flood week in Madurai, end to end.",
      subtitle: "Tamil Nadu • Madurai • post-flood diarrhoea • ORS stock-out risk (PRD §43, synthetic data).",
      steps: [
        { label: "PHC Melur • Tamil voice", title: "Stock report", desc: "“ORS 40 packets… Amoxicillin finished” → 3 items matched, confirmed." },
        { label: "Instantly", title: "Days of cover", desc: "ORS 2.5 days • stock-out risk ≈100% • readiness 61/100." },
        { label: "District view", title: "Possible surge", desc: "ORS + zinc 3.6× normal across 8 facilities; DHO verifies." },
        { label: "Optimiser", title: "12 transfers proposed", desc: "8,142 ORS sachets on Routes drive times; each needs approval.", highlight: true },
      ],
      panel: {
        kicker: "After approval",
        headline: "Melur receives 885 sachets from two donors.",
        sub: "Both PHCs are notified in their own language:",
        items: ["DHO approves 451 + 434 sachets", "Donors stay at ≥ 45 days of cover", "Receipt closes the loop in the app"],
        whyLabel: "Why officers trust it",
        why: "Every record carries source, time and model version; unverified surges and old reports are flagged.",
      },
      footnote: "All figures from the synthetic dataset (local run, 30 Sep 2026). The Tamil sentence is the demo script from docs/SUBMISSION.md.",
      notes: "This is demo scenario A. The nurse at PHC Melur speaks her stock report in Tamil; Gemini matches three medicines and she confirms. Instantly she sees ORS at two and a half days of cover and a readiness of 61. At district level, ORS and zinc use is 3.6 times normal across eight facilities, which is shown as a possible signal for the officer to verify. The optimiser proposes twelve transfers, two of them into Melur totalling 885 sachets, and the officer approves each one.",
    },

    // 7. Innovation & differentiation
    {
      type: "table",
      section: "06 — Innovation & differentiation",
      title: "Complements state systems; closes the transfer gap.",
      subtitle: "Existing systems solve real parts of the problem. PHC Pulse plugs in through adapters instead of replacing them.",
      columns: ["Approach", "What it contributes", "Where PHC Pulse adds"],
      rows: [
        ["Paper register + periodic report", "Familiar, offline, the facility’s official record", "Photo of the same register becomes structured stock"],
        ["DVDMS / state drug software", "Procurement, warehouse and facility inventory (NHM FDSI) [3]", "Voice capture at PHCs; optimised facility-to-facility transfers"],
        ["HMIS", "National service-delivery reporting [4]", "Daily stock decisions, not monthly indicators"],
        ["IDSP / IHIP", "Disease surveillance and outbreak reporting [5]", "Medicine-use surge as a possible signal for the DHO to verify"],
        ["PHC Pulse", "Voice/photo → forecast → OR-Tools transfer → DHO approval; state adapters", "Prototype on synthetic data; not yet field-validated"],
      ],
      callout: "A spoken PHC report becomes an explained, officer-approved transfer.",
      footnote: "[3] NHM Free Drugs Service Initiative guidelines.  [4] HMIS.  [5] IHIP.  Features of state deployments vary; PHC Pulse integrates rather than replaces.",
      notes: "We are not replacing anything. Paper registers remain the official record, and PHC Pulse reads them. DVDMS, the state drug distribution software supported under NHM's Free Drugs Service Initiative, manages procurement and inventory; we add frontline voice capture and optimised transfers between facilities, connected through an adapter. HMIS is for service reporting, and IHIP for surveillance; our medicine-use surge signal can feed that verification. Our honest limit is that we have only run on synthetic data so far.",
    },

    // 8. Technology & Google AI
    {
      type: "tech",
      section: "07 — Technology & Google AI",
      title: "Bounded AI on Google Cloud, not a chatbot.",
      subtitle: "Every Google integration sits behind an adapter with a labelled fallback, so the journey never silently breaks.",
      rows: [
        { title: "Capture", desc: "Speech-to-Text (ta/hi/en) • register photo • text • form • staff confirmation" },
        { title: "AI extraction", desc: "Gemini 2.5 Flash on Vertex AI • schema-validated JSON • unknown codes rejected" },
        { title: "Canonical data", desc: "TN / UP / OD adapters → canonical schema • BigQuery ledger" },
        { title: "Decision layer", desc: "Shared 8-week forecast • surge rules • OR-Tools min-cost flow on Routes times", highlight: true },
        { title: "Delivery", desc: "PHC app (EN/HI/TA, TTS) • DHO dashboard with Maps • 3 Cloud Run services" },
      ],
      navy: {
        title: "Google AI integration map",
        bullets: [
          "Gemini: extraction, register reading, explanations",
          "Speech, TTS, Translation • OR-Tools on Maps Routes",
          "BigQuery ledger • BQML ARIMA_PLUS (1,536 series)",
        ],
        pillLabel: "Not yet",
        pillText: "Firestore alerts, Firebase Auth, Model Registry",
      },
      gate: {
        title: "Real-vs-demo rule",
        rows: [
          { label: "Live", text: "Probed at start-up; the badge shows live only if the call passes" },
          { label: "Fallback", text: "Labelled demo mode (rule parser, haversine); never silent", coral: true },
          { label: "Freshness", text: "Every record has source + time; reports > 72 h are flagged" },
        ],
      },
      footnote: "Shared forecast, synthetic data only: WAPE 0.134–0.145 vs 0.172–0.189 for same-week-last-year across the three states (model card).",
      notes: "The architecture has five layers. Capture uses Cloud Speech-to-Text in Tamil, Hindi and English. Gemini 2.5 Flash on Vertex AI returns schema-validated JSON and rejects unknown drug codes. State adapters map three different export formats to one canonical schema, with BigQuery as the ledger. The decision layer is a shared forecast, surge rules and an OR-Tools min-cost flow on Google Routes drive times. Each integration is probed at start-up, and anything running on a fallback is labelled as demo.",
    },

    // 9. Responsible AI & data
    {
      type: "responsible",
      section: "08 — Responsible AI & data",
      title: "AI proposes. People confirm and approve.",
      subtitle: "Reported data, AI interpretation and recommendations are kept separate and labelled (PRD §35).",
      left: {
        pills: ["Human approval", "Nothing moves without the DHO"],
        rows: [
          { label: "Staff confirm", text: "AI-extracted stock is editable; nothing reaches the ledger unconfirmed." },
          { label: "DHO approves", text: "Every transfer and every surge notice needs officer review first." },
        ],
      },
      dont: {
        label: "Never",
        items: ["Store patient-level or personal health data", "Invent quantities: unclear values stay blank", "Present a surge as a confirmed outbreak"],
      },
      safety: {
        title: "Safety by design",
        rows: [
          { label: "Schema-bound", text: "Gemini returns schema-validated JSON; unknown drug codes are rejected." },
          { label: "Optimiser decides", text: "OR-Tools sets quantities; Gemini explains but cannot change them." },
          { label: "Safety stock", text: "Donors never drop below their safety cover (45 days by default)." },
          { label: "Provenance", text: "Every AI output stores model name, version and prompt version." },
          { label: "Staff privacy", text: "Check-in, not tracking; dashboards show aggregate presence only." },
          { label: "Data stays in state", text: "States share models and aggregate metrics, never facility data." },
        ],
      },
      footnote: "Register photos and voice recordings are kept in Cloud Storage for audit; retention limits are a pilot decision (PRD §52).",
      notes: "Responsibility is built into the flow, not added later. Staff confirm every extraction, and the officer approves every transfer and every surge notice. We never store patient data, never invent a quantity, and never call a surge an outbreak. The optimiser decides quantities and Gemini only explains them. Every AI output records its model and prompt version, and states share models and metrics, not facility data.",
    },

    // 10. Outcomes, validation & scale
    {
      type: "outcomes",
      section: "09 — Outcomes, validation & scale",
      title: "Prove fewer stock-out days, then scale by state.",
      subtitle: "The first proof is not app usage. It is medicine on the shelf when patients arrive.",
      chain: [
        { title: "Reporting", desc: "Daily stock by voice or photo" },
        { title: "Visibility", desc: "Cover the DHO trusts" },
        { title: "Action", desc: "Approved transfers before stock-out" },
        { title: "Patient signal", desc: "Fewer stock-out days, less expiry" },
      ],
      measure: {
        items: ["Stock-out days per tracer medicine [3]", "Near-expiry units moved vs expired", "Warning lead time before stock-out", "Reporting rate + extraction accuracy"],
      },
      gates: [
        { title: "District pilot", desc: "1 district, 20–40 PHCs; real opening stock via the state adapter" },
        { title: "Compare fairly", desc: "Pilot vs matched blocks; baseline stock-out days from state records" },
        { title: "Claim carefully", desc: "Synthetic results show feasibility only; publish real accuracy and limits" },
      ],
      ownership: {
        title: "Ownership + scale",
        rows: [
          { label: "Owner", text: "State Health Dept / State NHM" },
          { label: "Channel", text: "DHO + district drug warehouse" },
          { label: "Gate", text: "Data access • language QA • DHO capacity" },
        ],
      },
      budget: { text: "NHM Free Drugs Service Initiative support for IT-enabled drug supply chains, via the State PIP. [3]" },
      footnote: "Scale path (PRD §50): district pilot → state integration with drug-distribution software → shared model registry across states.",
      notes: "We will measure what the Free Drugs Service Initiative already tracks: stock-out days for essential medicines, plus expiry avoided and warning lead time. The pilot is one district with 20 to 40 PHCs, compared against matched blocks, and we will not claim more than the data supports. The natural owner is the State Health Department under NHM, working through the District Health Officer and the district drug warehouse. The budget route already exists: NHM's support for IT-enabled drug supply chains, proposed through the state's Programme Implementation Plan.",
    },

    // 11. Live prototype
    {
      type: "live",
      section: "10 — Live prototype",
      title: "Working today, end to end.",
      subtitle: "Three Cloud Run services in asia-south1 (Mumbai). All data is synthetic and labelled as such.",
      screens: [
        { image: A("screen-phc-staff-app.png"), caption: "PHC staff app • Tamil • PHC Melur stock" },
        { image: A("screen-dho-dashboard.png"), caption: "DHO dashboard • map, KPIs, transfer review" },
      ],
      links: LINKS,
      criteria: [
        { weight: "25%", label: "AI / technical execution", how: "Gemini extraction and register reading, OR-Tools on Routes times, validated JSON" },
        { weight: "20%", label: "Problem-solution fit", how: "Report → cover → forecast → warning → transfer → approval in one journey" },
        { weight: "20%", label: "Depth & reach across India", how: "3 state adapters, EN/HI/TA voice, one shared model with per-state accuracy" },
        { weight: "20%", label: "Deployability & scalability", how: "3 Cloud Run services; onboarding a new state is a config file" },
        { weight: "15%", label: "Impact potential", how: "31,882 PHCs [2]; outcome = FDSI stock-out-day indicator [3]" },
      ],
      footnote: "Screenshots: local build, 30 Sep 2026, synthetic data. Locally the map uses the OpenStreetMap fallback.",
      notes: "Everything on these slides runs today. On the left are the PHC staff app in Tamil and the District Health Officer dashboard with the map, KPIs and transfer review. The links go to the live Cloud Run services, the API documentation and the public source code. Against the five evaluation criteria: Gemini and OR-Tools do real work, one journey fits the brief, three states and three languages show reach, a new state is a configuration file, and the impact is measured in stock-out days.",
    },

    // 12–13. References
    {
      type: "references",
      section: "Appendix — References",
      title: "Challenge evidence & public health sources",
      subtitle: "Numbered references correspond to citations in the core proposal.",
      refs: [
        { n: 1, title: "Track 3 brief and PHC Pulse PRD", desc: "Challenge statement and product requirements (docs/PRD.md), incl. demo scenarios §43 and scale plan §50. Synthetic dataset: data/generator/synth.py.", tag: "Local evidence" },
        { n: 2, title: "MoHFW (2024), Health Dynamics of India 2022–23", desc: "Formerly Rural Health Statistics. 31,882 PHCs and 47,932 staff nurses at PHCs as of 31 March 2023 (PIB release, 9 Sep 2024).", url: "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2053070" },
        { n: 3, title: "NHM Free Drugs Service Initiative guidelines", desc: "Supports IT-enabled supply chains such as DVDMS; stock-out days as an indicator; redistribute near-expiry drugs to facilities in need; PIPs.", url: "https://nhm.gov.in/images/pdf/NHM/NHM-Guidelines/Free_Drugs_Service_Intitiative.pdf" },
        { n: 4, title: "Health Management Information System (HMIS)", desc: "MoHFW portal for facility-level service-delivery reporting and publications.", url: "https://hmis.mohfw.gov.in" },
      ],
      notes: "These are the sources behind the numbers. The facility and staffing figures come from the Ministry's Health Dynamics of India 2022–23, released through PIB. The outcome indicator, the redistribution principle and the budget route come from NHM's Free Drugs Service Initiative guidelines. Everything about our own scenario comes from the PRD and the synthetic dataset in the repository.",
    },
    {
      type: "references",
      section: "Appendix — References",
      title: "Platform, registry & technology sources",
      subtitle: "Systems PHC Pulse complements, and the Google technology it runs on.",
      refs: [
        { n: 5, title: "Integrated Health Information Platform (IHIP)", desc: "MoHFW platform for disease surveillance under IDSP; where possible-surge signals would be verified.", url: "https://ihip.mohfw.gov.in" },
        { n: 6, title: "ABDM Health Facility Registry", desc: "National facility identifiers; PHC Pulse uses the HFR ID format as the facility key (synthetic IDs only).", url: "https://facility.abdm.gov.in" },
        { n: 7, title: "Google OR-Tools: minimum cost flow", desc: "Open-source solver (SimpleMinCostFlow) used for redistribution under donor safety-stock limits.", url: "https://developers.google.com/optimization/flow/mincostflow" },
        { n: 8, title: "Gemini models on Vertex AI", desc: "Gemini 2.5 Flash for stock extraction, register reading and transfer explanations.", url: "https://cloud.google.com/vertex-ai/generative-ai/docs/models" },
      ],
      notes: "The second page lists the national platforms PHC Pulse is designed to work alongside: IHIP for surveillance and the ABDM Health Facility Registry for facility identifiers. It also lists the Google technology the prototype runs on: OR-Tools for the optimiser and Gemini on Vertex AI. All reused datasets, models and libraries are also listed in THIRD_PARTY.md in the repository.",
    },
  ],
};

kit.build(content, path.join(__dirname, "PHC_Pulse_Spontom_Pitch.pptx")).then((p) => console.log("wrote", p));
