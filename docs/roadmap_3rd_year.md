# AirWatch — 3rd Year Extension Roadmap
**Author:** Abhijeet Sirohi | B.Tech CSE-AIDE  
**Written:** July 2026  
**Based on:** Doc 02 H1 → B1 Unified Commerce Lakehouse extension path

---

## What AirWatch is today (July 2026)

A batch data pipeline ingesting real PM2.5 air quality data from OpenAQ government sensors and OpenWeather across 5 Indian cities, stored in PostgreSQL, transformed through 6 dbt models, served on a live Streamlit dashboard. The pipeline runs hourly, collects both pollution and weather data, and produces a weather-pollution correlation analysis and a next-day PM2.5 forecast using linear regression.

The foundation is solid. The data is real. The transformation layer is defensible. What it lacks is scale, streaming, statistical robustness, and production-grade infrastructure.

---

## The arc: where this becomes by 3rd year internship (June 2027)

A multi-source, streaming-capable, forecasting-enabled environmental intelligence platform — one that ingests data in real time, predicts next-day pollution with weather features as inputs, alerts users when AQI crosses dangerous thresholds, and runs entirely in a containerized, CI/CD-deployed infrastructure.

---

## Semester Plan (August 2026 — May 2027)

### Milestone 1 (August — September 2026): Forecasting Model

**What:** Replace the current linear regression (trained on PM2.5 trend only) with a multi-feature model using wind speed, humidity, and temperature from OpenWeather as inputs alongside the PM2.5 trend.

**Why now:** by August, there will be 6+ weeks of overlapping pollution and weather data — enough for a statistically meaningful model. The current model is honest about its limitations; this one will be genuinely predictive.

**Tools to learn:** scikit-learn (already started), pandas feature engineering, train/test split, RMSE evaluation, model persistence with joblib

**Time commitment:** 4-6 hours/week across August-September

**Done looks like:** a forecast that outperforms a naive "tomorrow = today" baseline on held-out test data, with RMSE documented and displayed on the dashboard

---

### Milestone 2 (October — November 2026): Streaming Ingestion

**What:** Replace hourly polling with OpenAQ's WebSocket feed for real-time event-driven ingestion. Instead of "check every hour," the pipeline wakes up when new data arrives.

**Why:** polling is inefficient and introduces up to 60 minutes of data lag. Event-driven ingestion is how production pipelines at scale actually work.

**Tools to learn:** websockets library in Python, Apache Kafka (basic producer-consumer), connection management for long-lived streams

**Time commitment:** 5-8 hours/week across October-November

**Done looks like:** the raw_air_quality table updates within seconds of a new sensor reading, rather than on a fixed hourly schedule. Kafka sits between the WebSocket feed and Postgres as a buffer.

---

### Milestone 3 (December 2026): Docker + CI/CD + Data Contracts

**What:** Three things that should have been in the 2nd year build but weren't:

1. **Docker Compose** — containerize Postgres, the ingestion scripts, and dbt into a single `docker-compose up` stack that anyone can run anywhere
2. **GitHub Actions CI/CD** — on every push to main, run `dbt test` automatically and block the merge if any test fails
3. **Data contracts** — use dbt's built-in contract feature to formally define what "valid" data looks like at each source boundary, so a sensor going offline or changing its schema breaks loudly rather than silently

**Tools to learn:** Docker Compose (fixing the WSL2 issue from the 2nd year build), GitHub Actions workflows, dbt contracts

**Time commitment:** 3-4 hours/week across December

**Done looks like:** `docker-compose up` starts the entire stack from scratch on a fresh machine. Every push to GitHub runs the test suite. A malformed sensor reading at ingestion triggers a contract violation, not a silent bad row.

---

## 3rd Year Internship Plan (June — July 2027)

By June 2027, AirWatch will have 12 months of real pollution and weather data, a streaming ingestion layer, a multi-feature forecasting model, and a containerized CI/CD-deployed infrastructure.

The 3rd year internship project built on top of this becomes **B1 — Unified Commerce Lakehouse** in spirit: a multi-source, production-grade data platform with real analytical outputs. Specifically:

- Expand from 5 cities to 20+ Indian cities
- Add a public health alert layer: when any city's PM2.5 crosses 120 µg/m³ (Poor threshold), trigger an automated notification
- Add a data quality framework using Great Expectations at the ingestion boundary
- Present the forecasting model's accuracy metrics publicly on the dashboard

This is no longer a student project at that point — it's a real, publicly useful environmental intelligence tool with a defensible technical architecture.

---

## What I need from the placement/mentor ecosystem

- Mentorship on Kafka setup and stream processing patterns (H3 skill family)
- Code review on the forecasting model's feature engineering and evaluation methodology
- Access to a Linux environment for Docker (resolves the WSL2 constraint from 2nd year)
- Guidance on Great Expectations vs dbt contracts for the data quality layer

---

## Risks and open questions

- OpenAQ's WebSocket API availability and rate limits at scale — needs investigation before Milestone 2
- The forecasting model's accuracy is unknown until tested on held-out data — may need feature engineering beyond the three current weather variables
- Expanding to 20+ cities requires station verification at scale — the manual discovery process from 2nd year won't work, needs automation
- Docker Desktop on Windows 10 had a WSL2/Hyper-V conflict throughout 2nd year — resolved by switching to Linux or WSL2 properly configured on Windows 11