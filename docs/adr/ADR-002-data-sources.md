# ADR-002: OpenAQ + OpenWeather as Data Sources

**Date:** 24 June 2026  
**Status:** Accepted  
**Author:** Abhijeet Sirohi

---

## Context

H1 requires picking a public API as the primary data source. The choice needed to satisfy three criteria: real data (not synthetic), reliable free access with no trial-credit expiry risk, and a natural second source for the Week 3 mini-extension.

## Decision

Use OpenAQ as the primary source (air quality, PM2.5) and OpenWeather as the Week 3 second source (temperature, humidity, wind speed) for the same five cities.

## Alternatives Considered and Rejected

- **OpenWeather alone (weather data)** — reliable and well-documented, but weather alone is a generic tutorial choice with no real analytical payoff. Rejected because every DE beginner picks weather; it produces nothing worth talking about in an interview.
- **CoinGecko (crypto market data)** — real API, real auth, real rate limits. Rejected on personal interest grounds — building something for 5 weeks requires genuine motivation, and crypto held none.
- **GitHub Events API** — the doc's own recommended H1 source. Rejected for the same reason as crypto — no personal connection to the domain.
- **OpenSky Network (flight traffic)** — technically the strongest option (real OAuth2, globally unique domain). Rejected because coverage is sparse over India, and OAuth2 token refresh added friction for a first project.
- **Cricket / sports APIs** — investigated. Most "free" tiers cap at 100 calls/day and several are unofficial scrapers that can break mid-project. Too fragile for a graded 5-week deliverable.

## Why OpenAQ + OpenWeather

- OpenAQ provides real government and sensor-network data — not estimated, not synthetic. PM2.5 readings from actual monitoring stations run by CPCB, MPCB, KSPCB, WBPCB, and TNPCB.
- The pairing with OpenWeather is analytically motivated, not just "a second API." The mart layer question — does humidity or wind speed predict next-day PM2.5 spikes — is a real question with a real answer, not a checkbox.
- Both APIs have genuinely free tiers with no trial-credit expiry risk.

## Consequences

- Station selection required manual verification — not all cities had active PM2.5 sensors. Several stations were ruled out for stale data (last reported 2018-2022). This added real work in Week 1 but produced a defensible, verified station list.
- Mumbai's Sion station (ID 6967) consistently reports anomalous PM2.5 values (900+ µg/m³). This is documented separately in ADR-003.
- OpenAQ coverage is uneven across India — Kolkata's chosen station updates less frequently than the others. Acceptable for this project's cadence.