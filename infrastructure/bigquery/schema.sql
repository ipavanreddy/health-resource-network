-- PHC Pulse BigQuery schema (dataset: ${BIGQUERY_DATASET}, region asia-south1).
-- Canonical tables loaded by data/transformations/load_bigquery.py; event tables written by the API sink.

CREATE SCHEMA IF NOT EXISTS `${PROJECT}.${DATASET}` OPTIONS (location = 'asia-south1');

CREATE TABLE IF NOT EXISTS `${PROJECT}.${DATASET}.facilities` (
  facility_id STRING NOT NULL, hfr_id STRING, name STRING, type STRING, state STRING, district STRING,
  district_name STRING, block STRING, lat FLOAT64, lng FLOAT64, warehouse_id STRING, lead_time_days INT64,
  beds_total INT64, staff_sanctioned INT64, is_synthetic BOOL, dataset_version STRING
);

-- Daily consumption per facility x medicine; stocked_out marks censored demand (PRD §14).
CREATE TABLE IF NOT EXISTS `${PROJECT}.${DATASET}.daily_consumption` (
  facility_id STRING NOT NULL, drug_code STRING NOT NULL, date DATE NOT NULL, consumption INT64,
  stocked_out BOOL, source STRING, is_synthetic BOOL, dataset_version STRING
) PARTITION BY DATE_TRUNC(date, MONTH) CLUSTER BY facility_id, drug_code;

CREATE TABLE IF NOT EXISTS `${PROJECT}.${DATASET}.stock_transactions` (
  transaction_id STRING, facility_id STRING, drug_code STRING, type STRING, quantity INT64, delta INT64,
  batch STRING, expiry_date STRING, source STRING, created_at TIMESTAMP, capture_id STRING, transfer_id STRING,
  confirmed_by STRING, model_name STRING, model_version STRING, prompt_version STRING
);

CREATE TABLE IF NOT EXISTS `${PROJECT}.${DATASET}.transfers` (
  transfer_id STRING, state STRING, district STRING, from_facility_id STRING, to_facility_id STRING,
  drug_code STRING, quantity INT64, reason STRING, travel_minutes FLOAT64, status STRING, approved_by STRING,
  created_at TIMESTAMP, model_name STRING, model_version STRING, prompt_version STRING, explanation JSON,
  optimiser JSON, history JSON
);

CREATE TABLE IF NOT EXISTS `${PROJECT}.${DATASET}.ai_outputs` (
  capture_id STRING, facility_id STRING, source STRING, items JSON, model_name STRING, model_version STRING,
  prompt_version STRING, generated_at TIMESTAMP, mode STRING, is_demo BOOL
);
