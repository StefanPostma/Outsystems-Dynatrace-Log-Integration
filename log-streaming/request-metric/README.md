# Unified API traffic view (`outsystems.api.*`)

`3.0 Integrations` wants one field pair — an endpoint and a response time — that works across **consumed** calls (`Integration`, `WebReference`) and **exposed** calls (`ServiceAPI`). None of these log types share a field name with each other, so this derives three extra attributes at ingest time:

| Field | Derived from | Present on |
|---|---|---|
| `outsystems.api.endpoint` | `Integration` / `WebReference`: `outsystems.log.endpoint` · `ServiceAPI`: `outsystems.log.entrypoint_name` (ServiceAPI logs have no URL endpoint, only the exposed service's name) | `Integration`, `ServiceAPI`, `WebReference` |
| `outsystems.api.response_time` | `outsystems.request.duration` | `Integration`, `ServiceAPI`, `WebReference` |
| `outsystems.api.direction` | constant | `"consumed"` on `Integration` and `WebReference`, `"exposed"` on `ServiceAPI` |

These are **additions**, not replacements — `outsystems.log.type` stays `Integration`, `ServiceAPI` or `WebReference` on every record. Dashboards that want the unified view filter `in(outsystems.log.type, "Integration", "ServiceAPI", "WebReference")` and read the `outsystems.api.*` fields; dashboards that want one type only keep filtering on the single log type as before.

> `WebReference` is Logstash-DB-only (`db-web-reference.conf`) — it has no log-streaming or MonitorProbe equivalent, so `logstash/dashboards/3.0 Integrations.json` includes it and `log-streaming/dashboards/3.0 Integrations.json` doesn't. That's the one place the two tracks' `3.0 Integrations` dashboards are allowed to genuinely differ — everything else stays query-identical.

> This intentionally does **not** reproduce a `outsystems.log.type == "Request"` value some earlier dashboards queried against a specific tenant. That value was never part of the OutSystems-documented schema — see [Documentation/OTEL-Field-Mapping.md](../../Documentation/OTEL-Field-Mapping.md#derived-fields-unified-api-traffic-view). Reusing the real log type avoids colliding with the other tiles in `3.0 Integrations` that already filter on `"Integration"` directly.

## Logstash

Already built in. See the `mutate { copy => ... }` block at the end of `db-integration.conf`, `app-integration.conf`, `db-web-service.conf`, and `db-web-reference.conf`. No further setup needed.

## Log streaming (OTLP)

Log streaming has no pipeline of its own — OutSystems pushes OTLP straight to Dynatrace — so the same derivation has to run somewhere in that path. Two equivalent options, same output fields:

| | [OpenPipeline rule](openpipeline-processing-rule.md) | [OTel Collector](otel-collector-config.yaml) |
|---|---|---|
| Runs | Inside Dynatrace, after ingest | In front of Dynatrace, before ingest |
| New infrastructure | None — one-time config in Settings | A Collector instance to deploy and run |
| Best for | Customers who want zero extra components | Customers who already run a Collector, or want the transform under their own version control before data leaves their network |

Pick one per customer — they produce identical fields, so dashboards don't need to know which was used.
