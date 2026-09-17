# OutSystems ↔ Dynatrace Log Integration

## About 📑
This repository contains templates to provide better and faster insights on top of [OutSystems](https://www.outsystems.com/) monitoring data in [Dynatrace](https://www.dynatrace.com/).

There are **two clearly separated ingestion tracks**, and both produce the **same OTEL-standard field names** in Dynatrace, so the dashboards are aligned and interchangeable:

| | [`log-streaming/`](log-streaming/) | [`logstash/`](logstash/) |
|---|---|---|
| **What** | Native OutSystems 11 [log streaming](https://success.outsystems.com/documentation/11/monitoring_and_troubleshooting_apps/introduction_to_log_streaming/) (OTLP over HTTP/gRPC) | Logstash pipelines pulling from the OutSystems log database or the MonitorProbe API |
| **For** | **Recommended** for OutSystems 11.23.1+ | O11 versions without streaming, or setups needing DB-level extras (BPT processes, web references) |
| **Managed by** | OutSystems platform (LifeTime) | You (self-hosted Logstash) |
| **Field names** | OutSystems OTEL standard | Same OTEL standard — see the [field mapping](Documentation/OTEL-Field-Mapping.md) |

> 📐 **The alignment contract:** [Documentation/OTEL-Field-Mapping.md](Documentation/OTEL-Field-Mapping.md) defines the canonical attribute names both tracks must emit. Change that file first, everything else follows it.

## Repository layout

- **[`log-streaming/`](log-streaming/)** — setup guide + Dynatrace Gen3 dashboards for the native OutSystems 11 log streaming track, plus [derived-field options](log-streaming/request-metric/) (OpenPipeline rule or OTel Collector) for customers who need pre-ingest calculations
- **[`logstash/`](logstash/)** — Logstash install guide, pipeline configurations (database + MonitorProbe), and the same aligned dashboards plus Logstash-only extras (BPT Processes)
- **[`shared/dashboards/`](shared/dashboards/)** — ingestion-independent dashboards (RUM Overview, demo landing page)
- **[`Documentation/`](Documentation/)** — [field mapping](Documentation/OTEL-Field-Mapping.md), [how to access OutSystems monitoring data](Documentation/Access-Monitoring-Data.md), [monitoring data types](Documentation/Monitoring-Data.md), [dashboard screenshots](Documentation/images/)
- **[`tools/demo-data/`](tools/demo-data/)** — generator that ingests synthetic OutSystems logs (canonical field names) into a Dynatrace tenant, to validate the dashboards without a live OutSystems environment

## Goal 🎯
Provide OutSystems customers with an out-of-the-box solution to:
- **Observe OutSystems monitoring data in Dynatrace** with advanced visualizations, unified observability, and easy automation — beyond the built-in tools of the OutSystems platform
- Search OutSystems logs with Dynatrace Query Language (DQL), with **one set of field names regardless of ingestion method**
- Retain logs for up to 10 years
- **Do more advanced monitoring**: alerts per environment or factory, Davis AI insights, Site Reliability Guardian quality gates, release automation with Dynatrace Workflows
- **Track application performance and errors through time**: slow queries, slow integrations, slow extensions
- Provide an example of how to set up and monitor SLOs

## Getting started

1. No Dynatrace environment yet? [Start a trial](https://www.dynatrace.com/trial).
2. Decide how to collect the data: [How to access OutSystems log data](Documentation/Access-Monitoring-Data.md)
   - **OutSystems 11.23.1+** → use [log streaming](log-streaming/) (recommended)
   - Otherwise → use the [Logstash track](logstash/)
3. Import the dashboards of your track (they use the same fields either way).
4. Optional: validate with [synthetic demo data](tools/demo-data/) before connecting a real environment.

Example visualizations: [Documentation/images](Documentation/images)

**Want support to implement or extend these assets?** Contact [Dynatrace Professional Services](https://www.dynatrace.com/services-support/#dynatrace-services/).

## Examples of metrics you can extract

- **Request time duration** (per request): client time, server time — decomposable into session acquisition time, query execution time, integration execution time, extension execution time
- **Server-side performance**: session size, viewstate size, number of slow queries / integrations / extensions
- **Errors**: number of errors, errors by type / application / environment
