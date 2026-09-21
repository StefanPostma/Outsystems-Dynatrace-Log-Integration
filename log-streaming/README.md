# OutSystems 11 Log Streaming → Dynatrace

This is the **recommended** track for OutSystems 11. The platform streams all Service Center logs natively to Dynatrace using the OpenTelemetry protocol (OTLP over HTTP/gRPC) — no infrastructure to run yourself.

## Requirements

- Platform Server **11.23.1+** (11.30.0+ recommended), LifeTime **11.19.0+** (11.25.0+ recommended)
- [Log separation](https://success.outsystems.com/documentation/11/monitoring_and_troubleshooting_apps/introduction_to_log_streaming/) enabled in your environment
- A Dynatrace environment whose OTLP endpoint is publicly reachable
- A Dynatrace access token with the **`logs.ingest`** scope

## Setup

1. Follow the OutSystems guide: [Introduction to log streaming](https://success.outsystems.com/documentation/11/monitoring_and_troubleshooting_apps/introduction_to_log_streaming/) and select **Dynatrace** as destination.
2. Endpoint: `https://<your-tenant>.live.dynatrace.com/api/v2/otlp/v1/logs` with the API token above.
3. Verify data arrives:
   ```dql
   fetch logs
   | filter isNotNull(outsystems.log.type)
   | summarize count(), by: {outsystems.log.type}
   ```
4. Import the dashboards from [`dashboards/`](dashboards/) (Dynatrace → Dashboards → Upload).
5. In each dashboard, replace the placeholders:
   - `TENANTID` → your Dynatrace tenant id (in drill-down links)
   - `DASHBOARD-ID-2.1` → the id of your imported *2.1 Error Raw Data* dashboard (visible in its URL)

## Field names

All queries use the attribute names OutSystems documents for log streaming ([logged data fields](https://success.outsystems.com/documentation/11/monitoring_and_troubleshooting_apps/introduction_to_log_streaming/logged_data_fields/)) as they appear in Dynatrace Grail — e.g. `outsystems.log.type`, `outsystems.app.name`, `outsystems.request.duration`, `exception.message`.

The [Logstash track](../logstash/) emits the **same names**, so these dashboards and the Logstash ones are interchangeable. The full contract: [Documentation/OTEL-Field-Mapping.md](../Documentation/OTEL-Field-Mapping.md).

## Dashboards

| Dashboard | Purpose |
|---|---|
| 1.0 Top findings | Errors and slow queries per application/environment at a glance |
| 2.0 Error Trends | Error volume over time, drill-down links to raw data |
| 2.1 Error Raw Data | Filterable raw error records |
| 2.2 Error Deep Dive | Single-error investigation |
| 3.0 Integrations | Integration endpoints: volume, response time, error rate |
| 4.0 Request performance | Request-event based load-time analysis |
| 5.0 Screen Session Health | Session/viewstate size (Good/Fair/Bad), AJAX vs full-screen access mode, size trend over time |
| 6.0 Extensions and Timers | Slowest extensions, timer execution duration, timer drift (scheduled vs. actual start) |

No live OutSystems environment yet? Validate the dashboards with [`tools/demo-data/`](../tools/demo-data/).
