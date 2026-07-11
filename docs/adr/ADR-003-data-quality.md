# ADR-003: Data Quality Strategy for Anomalous Sensor Readings

**Date:** 27 June 2026  
**Status:** Accepted  
**Author:** Abhijeet Sirohi

---

## Context

During Week 1 development, two real data quality issues were discovered in the OpenAQ data:

**Issue 1 — Dead sensor selection:** Mumbai's Sion station (ID 6967) has multiple PM2.5 sensors — one active, one that stopped reporting in October 2022. The initial ingestion script grabbed the dead sensor by taking the first PM2.5 match in the API response. This produced a reading dated 2022-10-31 appearing as "current" data.

**Issue 2 — Anomalous active readings:** After fixing the sensor selection bug, the active Sion sensor was found to consistently report PM2.5 values of 900+ µg/m³ across multiple days (941.53 on 23 June, 929.32 on 26 June). For context, WHO's safe annual PM2.5 limit is 5 µg/m³, and even Delhi's worst recorded winter pollution events rarely exceed 400 µg/m³. A value consistently above 900, repeated across different days, is almost certainly a miscalibrated or malfunctioning sensor rather than real air quality.

A decision was needed on how to handle both issues in the pipeline.

## Decision

**For Issue 1 (dead sensor selection):** fixed in the ingestion script. Instead of taking the first PM2.5 sensor match, the script now collects all PM2.5 sensors at a station and selects the one with the most recent `datetime.utc`. This is a permanent fix applied at the source, before data lands in the warehouse.

**For Issue 2 (anomalous active readings):** preserve the raw data exactly as received, and flag suspicious rows in the mart layer rather than deleting or correcting them. Specifically, `mart_city_pollution_trends` adds a `likely_sensor_error` boolean column: `true` when `max_pm25 > 500`, `false` otherwise. The dashboard excludes flagged rows from averages and city metrics.

## Alternatives Considered

- **Delete anomalous rows from raw table** — rejected. Raw data is a permanent, honest record of what the sensor actually reported. Deleting it silently would make the pipeline unauditable and remove the ability to prove "this is genuinely what the source said."
- **Cap values at a ceiling in the ingestion script** — rejected. Silently capping a 929 to 400 before storing it misrepresents the source data and hides the underlying sensor problem.
- **Switch Mumbai to a different station** — considered, but the anomaly is worth documenting rather than avoiding. Every other nearby station with active PM2.5 coverage showed similar or worse data freshness issues.

## Consequences

- Raw table always reflects exactly what OpenAQ reported — no silent corrections, full auditability.
- The `likely_sensor_error` flag is transparent — anyone querying the mart can see both the raw value and its quality status side by side.
- Two custom dbt tests enforce this logic automatically: `test_no_negative_pm25.sql` and `test_flag_consistency.sql` — both passing as of Week 1.
- Mumbai's data is effectively excluded from clean averages until the sensor is recalibrated or a better station is identified. This is documented as a known limitation in the README.
- This pattern (preserve raw, flag downstream) is the standard approach in production DE pipelines and is directly defensible in interviews.