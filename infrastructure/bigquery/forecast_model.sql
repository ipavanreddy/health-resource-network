-- Shared weekly demand model in BigQuery ML (PRD §14, §19). Enable in the API with FORECAST_BACKEND=bigquery.
-- One ARIMA_PLUS series per facility x medicine; stock-out weeks (>= 2 stock-out days) are excluded so
-- censored zero consumption is not learned as low demand.

CREATE OR REPLACE VIEW `${PROJECT}.${DATASET}.weekly_demand` AS
SELECT
  CONCAT(facility_id, '|', drug_code) AS series_id,
  TIMESTAMP(DATE_TRUNC(date, WEEK(MONDAY))) AS week,
  SUM(consumption) * 7 / GREATEST(7 - COUNTIF(stocked_out), 1) AS demand,
  COUNTIF(stocked_out) AS stockout_days
FROM `${PROJECT}.${DATASET}.daily_consumption`
GROUP BY series_id, week
HAVING stockout_days < 2;

CREATE OR REPLACE MODEL `${PROJECT}.${DATASET}.weekly_demand_arima`
OPTIONS (
  model_type = 'ARIMA_PLUS',
  time_series_timestamp_col = 'week',
  time_series_data_col = 'demand',
  time_series_id_col = 'series_id',
  data_frequency = 'WEEKLY',
  holiday_region = 'IN',
  auto_arima = TRUE
) AS
SELECT series_id, week, demand FROM `${PROJECT}.${DATASET}.weekly_demand`;

-- Evaluate against the baseline in the model card:
-- SELECT * FROM ML.ARIMA_EVALUATE(MODEL `${PROJECT}.${DATASET}.weekly_demand_arima`);
