# ADR-001: PostgreSQL as the Warehouse

**Date:** 24 June 2026  
**Status:** Accepted  
**Author:** Abhijeet Sirohi

---

## Context

I needed a warehouse to permanently store air quality readings ingested from OpenAQ. The warehouse needed to support SQL queries, work directly with dbt, and be runnable locally without a cloud account or paid tier.

## Decision

Use PostgreSQL 18, running natively on the local machine for development, and Supabase's free-tier Postgres for the deployed version.

## Alternatives Considered

- **DuckDB** — simpler, no server needed, runs as a file. Rejected because it doesn't run as a persistent background service, which a continuously-ingesting pipeline needs. Also less common in real DE job postings than Postgres.
- **BigQuery / Snowflake free tier** — powerful and cloud-native, but adds cloud account complexity and burn-rate risk on trial credits. Unnecessary at this data volume (5 cities, hourly readings).
- **SQLite** — the simplest option. Rejected because it doesn't support concurrent connections well, and dbt's Postgres adapter is more transferable to real job environments.

## Consequences

- Postgres is the most widely-used warehouse in real DE roles at the companies this track targets (Razorpay, PhonePe, Flipkart, Tiger Analytics). This choice is directly transferable.
- Running natively instead of in Docker was a forced substitution due to a WSL2/Hyper-V virtualization conflict on this machine. Docker Compose containerization is planned before Milestone 1 (19 July) — this is a tracked risk, not a permanent decision.
- Supabase as the deployed warehouse avoids any cloud trial-credit expiry risk. It auto-pauses after 7 days of inactivity but resumes in ~2 seconds on the next request, which is acceptable for this project's cadence.