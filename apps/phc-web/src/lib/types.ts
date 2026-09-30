// Types mirroring the PHC Pulse API (services/api). Keep in sync with both apps.

export type StockStatus = "adequate" | "low" | "critical" | "stocked_out";
export type RiskBand = "low" | "medium" | "high" | "stocked_out";

export interface DataLabel {
  source: string;
  dataset_version: string;
  is_synthetic: boolean;
  reference_timestamp: string;
}

export interface IntegrationMode {
  id: string;
  label: string;
  mode: "real" | "demo";
  /** Env vars present (null when forced into demo mode). */
  configured?: boolean;
  /** Result of the start-up verification probe: true = working, false = configured but failing. */
  verified?: boolean | null;
  detail?: string;
  checked_at?: string | null;
  enable_with: string;
  fallback: string;
}

export interface SystemModes {
  integrations: IntegrationMode[];
  demo_mode: boolean;
  synthetic_data: boolean;
  data_label: DataLabel;
  notice: string;
}

export interface FacilitySummary {
  facility_id: string;
  hfr_id: string;
  name: string;
  type: "PHC" | "CHC" | "DWH";
  state: string;
  district: string;
  district_name: string;
  block: string;
  lat: number;
  lng: number;
  warehouse_id: string | null;
  lead_time_days: number;
  is_warehouse: boolean;
  readiness: { score: number; band: string } | null;
  worst_status?: StockStatus;
  stocked_out?: string[];
  critical?: string[];
  high_risk?: string[];
  max_stockout_risk?: number;
  surge_groups?: string[];
  beds?: { total: number; occupied: number };
  staff?: { sanctioned: number; present: number };
  freshness_hours?: number;
  stale?: boolean;
  near_expiry_qty?: number;
}

export interface Freshness {
  stock: { at: string; source: string; hours_ago: number };
  beds: { at: string; hours_ago: number };
  attendance: { at: string; hours_ago: number };
  forecast: { at: string; model: string };
  stale: boolean;
}

export interface FacilityDetail extends FacilitySummary {
  warehouse: FacilitySummary | null;
  freshness?: Freshness;
  opd_today?: number;
  state_config?: { name: string; default_language: string; season_focus: string };
}

export interface StockRow {
  drug_code: string;
  name: string;
  strength: string;
  unit: string;
  group: string;
  is_tracer: boolean;
  on_hand: number;
  in_transit: number;
  daily_demand: number;
  days_of_cover: number | null;
  status: StockStatus;
  stockout_risk: number;
  risk_band: RiskBand;
  lead_time_days: number;
  near_expiry_qty: number;
  near_expiry_date: string | null;
  updated_at: string;
  source: string;
  hours_since_update: number;
  surge: boolean;
  surge_ratio: number;
  forecast_next_week: number;
}

export interface ReadinessComponent {
  key: string;
  label: string;
  weight: number;
  score: number;
  points: number;
  detail: string;
}

export interface Readiness {
  facility_id?: string;
  score: number;
  band: string;
  components: ReadinessComponent[];
  weights: Record<string, number>;
  method: string;
}

export interface ForecastWeek {
  week_start: string;
  demand_low: number;
  demand_expected: number;
  demand_high: number;
}

export interface Forecast {
  drug_code: string;
  name: string;
  strength: string;
  unit: string;
  weeks: ForecastWeek[];
  history: { week_start: string; consumption: number; stockout_days: number }[];
  model: { id: string; version: string; backend: string; is_demo: boolean };
  relative_error_sd: number;
  note: string;
}

export interface Provenance {
  model_name: string;
  model_version: string;
  prompt_version: string;
  generated_at?: string | null;
  mode: string;
  is_demo: boolean;
}

export interface CaptureItem {
  spoken_name: string;
  drug_code: string | null;
  quantity: number | null;
  unit: string | null;
  match_confidence: number;
  standard_name: string | null;
  current_on_hand: number | null;
  needs_review: boolean;
}

export interface RegisterRow {
  medicine_text: string;
  drug_code: string | null;
  opening: number | null;
  received: number | null;
  issued: number | null;
  closing: number | null;
  match_confidence: number;
  illegible_cells: string[];
}

export interface Capture {
  capture_id: string;
  facility_id: string;
  source: "voice" | "text" | "photo" | "form";
  language: string;
  status: string;
  created_at: string;
  items: CaptureItem[];
  unrecognised: string[];
  rows: RegisterRow[] | null;
  register_date: string | null;
  transcript: { transcript: string; provider: string; is_demo?: boolean } | null;
  confirmation_text: string;
  provenance: Provenance;
  /** Original photo / recording kept in Cloud Storage (real mode only). */
  media?: { uri: string; bytes: number; content_type: string } | null;
}

export interface ConfirmResult {
  capture: Capture;
  saved: string[];
  stock: StockRow[];
  readiness: Readiness;
  message: string;
}

export interface Alert {
  alert_id: string;
  type: "surge" | "stocked_out" | "stockout_risk";
  facility_ids: string[];
  drug_codes: string[];
  severity: "high" | "medium" | "low";
  summary: string;
  created_at: string;
  language: string;
  status: string;
  model_name: string;
  model_version: string;
  context: Record<string, unknown> & {
    facility_name?: string;
    label?: string;
    ratio?: number;
    blocks?: string[];
    max_risk?: number;
  };
  review?: { status: string; by: string; at: string } | null;
}

export interface Explanation {
  summary: string;
  risk_level: "low" | "medium" | "high";
  reasons: string[];
  impact: string;
  uncertainties: string[];
  travel_minutes: number;
  confidence: number;
  transfer_note: string;
  requires_human_review: boolean;
}

export interface Transfer {
  transfer_id: string;
  state: string;
  district: string;
  from_facility_id: string;
  to_facility_id: string;
  from_name: string;
  to_name: string;
  from_location: { lat: number; lng: number };
  to_location: { lat: number; lng: number };
  drug_code: string;
  medicine: string;
  unit: string;
  quantity: number;
  reason: string;
  travel_minutes: number;
  travel_mode: string;
  cross_district: boolean;
  status: "proposed" | "approved" | "rejected" | "dispatched" | "received";
  approved_by: string | null;
  explanation: Explanation;
  optimiser: {
    receiver_cover_before: number;
    receiver_cover_after: number;
    receiver_stockout_risk: number;
    donor_cover_before: number;
    donor_cover_after: number;
    donor_safety_days: number;
    donor_near_expiry_qty: number;
    stockout_days_avoided: number;
  };
  created_at: string;
  model_name: string;
  model_version: string;
  prompt_version: string;
  ai_mode: string;
  is_demo: boolean;
  history: { status: string; at: string; by: string; note: string | null }[];
}

export interface Notification {
  notification_id: string;
  target: string;
  type: string;
  texts: Record<string, string>;
  transfer_id: string | null;
  created_at: string;
  channel: string;
}

export interface Scenario {
  id: string;
  state: string;
  district: string;
  title: string;
  language: string;
  hero_facility_id: string;
  hero_facility_name: string;
  focus_drugs: string[];
}
