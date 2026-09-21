# OTEL Field Mapping — the alignment contract

Both ingestion tracks in this repository — **OutSystems 11 Log Streaming** (OTLP) and **Logstash** — must produce the **same attribute names** in Dynatrace, so that one set of aligned dashboards works regardless of how the data was ingested.

The canonical names follow the OutSystems log streaming documentation:

- [Introduction to log streaming](https://success.outsystems.com/documentation/11/monitoring_and_troubleshooting_apps/introduction_to_log_streaming/)
- [Logged data fields](https://success.outsystems.com/documentation/11/monitoring_and_troubleshooting_apps/introduction_to_log_streaming/logged_data_fields/)

The OutSystems documentation writes attributes in Elastic notation (`log.attributes.outsystems.log.type`). In Dynatrace Grail the `log.attributes.` / `resource.attributes.` prefixes are dropped — the tables below use the **Dynatrace attribute names** as you query them with DQL.

> ⚠️ **Verification note:** the connected demo tenant currently has no OutSystems data. Names marked *(verify)* were taken from dashboards previously built against a live streaming tenant, or are a best-effort choice where OutSystems documents nothing. Re-validate against a live tenant with `fetch logs | filter isNotNull(outsystems.log.type) | limit 10` and adjust here first — this file is the contract, everything else follows it.

## Derived fields: unified API traffic view

Unlike every other field in this document, `outsystems.api.endpoint`, `outsystems.api.response_time` and `outsystems.api.direction` are **not emitted by OutSystems** — they're computed at ingest time from `Integration`, `ServiceAPI` and `WebReference` records, so one field pair works across consumed and exposed API calls instead of three type-specific ones. Full derivation logic, and three interchangeable ways to compute it (Logstash filter, Dynatrace OpenPipeline rule, OpenTelemetry Collector/OTTL), live in [log-streaming/request-metric/](../log-streaming/request-metric/).

| Field | Value | Present on |
|---|---|---|
| `outsystems.api.endpoint` | `Integration` / `WebReference`: copy of `outsystems.log.endpoint` · `ServiceAPI`: copy of `outsystems.log.entrypoint_name` (this type has no URL endpoint) | `Integration`, `ServiceAPI`, `WebReference` |
| `outsystems.api.response_time` | copy of `outsystems.request.duration` | `Integration`, `ServiceAPI`, `WebReference` |
| `outsystems.api.direction` | `"consumed"` on `Integration` and `WebReference`, `"exposed"` on `ServiceAPI` | `Integration`, `ServiceAPI`, `WebReference` |

`WebReference` is Logstash-DB-only — no log-streaming or MonitorProbe equivalent exists — so it's the one place `logstash/dashboards/3.0 Integrations.json` and `log-streaming/dashboards/3.0 Integrations.json` are allowed to genuinely differ.

`outsystems.log.type` is never overwritten to a synthetic value — an earlier version of `3.0 Integrations` queried `outsystems.log.type == "Request"`, which came from a one-off Dynatrace log processing rule configured by hand in a specific tenant, undocumented and not shipped anywhere in this repo. That value is retired; don't reintroduce it.

## Log type discriminator

Every record carries `outsystems.log.type`. Canonical values:

| `outsystems.log.type` | Service Center log | Logstash pipeline |
|---|---|---|
| `General` | General log | `db-general` / `app-general` |
| `Error` | Error log | `db-error` / `app-error` |
| `Screen` | Traditional web request / screen | `db-web-request` / `app-web-request` |
| `MobileRequest` | Mobile request | `db-mobile-request` / `app-mobile-request` |
| `Integration` | Integration | `db-integration` / `app-integration` |
| `Extension` | Extension | `db-extension` / `app-extension` |
| `CyclicJob` | Timer / cyclic job | `db-timer` / `app-timer` |
| `RequestEvent` | Request event | `db-request-event` / `app-request-event` |
| `ServiceAPI` | Service API / web service | `db-web-service` |
| `WebReference` *(Logstash-only)* | Consumed SOAP reference | `db-web-reference` |

## Common fields (all log types)

| Source field | Dynatrace attribute | Notes |
|---|---|---|
| `Instant` | `timestamp` | Log record timestamp |
| `Message` | `content` | Log body |
| `Application_Name` | `outsystems.app.name` | *(verify — not in OutSystems doc, used by live-built dashboards)* |
| `Application_Key` | `outsystems.app.key` | |
| `Espace_Id` / `Espace_Name` | `outsystems.espace.id` / `outsystems.espace.name` | Logstash-only detail |
| `Module_Name` / `Module_Key` | `outsystems.module.name` / `outsystems.module.key` | |
| `Action_Name` | `code.function` | OTEL semconv |
| `Entrypoint_Name` | `outsystems.log.entrypoint_name` | |
| `Request_Key` | `outsystems.request.key` | Correlation GUID across log types |
| `Session_Id` | `outsystems.user.session.id` | |
| `User_Id` | `enduser.id` | OTEL semconv |
| `Username` | `outsystems.user.name` | Logstash-only |
| `Login_Id` | `outsystems.user.login_id` | |
| `Client_IP` | `http.client_ip` | |
| `Server` | `host.name` | |
| `Tenant_Id` | `outsystems.tenant.id` | |
| — (deployment config) | `deployment.environment` | Streaming: environment; Logstash: `DATA_ENVIRONMENT_NAME` |
| — (Logstash config) | `outsystems.customer.name`, `outsystems.location.name` | Logstash-only enrichment |
| — (Logstash internal) | `outsystems.logstash.import_latency` | Minutes between log write and ingestion |
| — (Logstash internal) | `outsystems.logstash.duration_class` | Good/Fair/Bad bucketing added by pipelines |

## Error

| Source field | Dynatrace attribute | Notes |
|---|---|---|
| `Message` | `content` **and** `exception.message` | Dashboards filter on `exception.message` |
| `Stack` | `exception.stacktrace` | |
| `Id` | `outsystems.log.error.uid`, copied to `outsystems.log.uid` | Doc says `error.uid`; dashboards count `outsystems.log.uid` *(verify which one streaming actually sends)* |
| `EnvironmentInformation` | `outsystems.log.environment_information` | |

## General

| Source field | Dynatrace attribute | Notes |
|---|---|---|
| `Message_Type` | `outsystems.log.message.tag` | e.g. `SLOWSQL`, `SLOWEXTENSION` *(verify)* |
| parsed object name | `outsystems.log.message.object` | Logstash grok on SLOWSQL-style messages |
| parsed duration | `outsystems.request.duration` | Logstash grok; streaming sends it natively |

## Screen (traditional web request)

| Source field | Dynatrace attribute | Notes |
|---|---|---|
| `Screen` | `outsystems.log.screen.name` | |
| `Screen_Type` | `outsystems.log.screen.type` | `WEB` / `MOBILE` |
| `Access_Mode` | `outsystems.log.screen.access_mode` | `AJAX` / `SCREEN` |
| `Duration` | `outsystems.request.duration` | milliseconds |
| `Session_Bytes` | `outsystems.traditional.ss` | per OutSystems doc |
| `Session_Requests` | `outsystems.traditional.sr` | *(verify)* |
| `Viewstate_Bytes` | `outsystems.log.viewstate_bytes` | |
| `MSISDN` | `outsystems.log.msisdn` | Logstash-only |
| `Executed_By` | `outsystems.log.executed_by` | Logstash-only |

## MobileRequest

| Source field | Dynatrace attribute |
|---|---|
| `Screen` | `outsystems.log.screen.name` |
| `Endpoint` | `outsystems.log.endpoint` |
| `Id` | `outsystems.log.uid` |
| `Login_Id` | `outsystems.user.login_id` |
| `Detail label / link` | `outsystems.log.detail_label` / `outsystems.log.detail_link` |

## Integration

| Source field | Dynatrace attribute | Notes |
|---|---|---|
| `Action` | `code.function` | service + method |
| `Endpoint` | `outsystems.log.endpoint` | external system URL |
| `Duration` | `outsystems.request.duration` | milliseconds |
| `Type` | `http.method` | `SOAP` / `REST` — odd, but this is the published OutSystems mapping |
| `Is_Expose` | `outsystems.integration.type` | per OutSystems doc |
| `Source` | `net.host.ip` | |
| `Id` | `outsystems.log.uid` | |
| `ErrorId` | `outsystems.log.error.uid` | links to the Error record |

## Extension

| Source field | Dynatrace attribute | Notes |
|---|---|---|
| `Extension_Name` | `outsystems.code.function.owner` | |
| `Extension_Id` | `outsystems.code.owner.function.id` | |
| `Duration` | `outsystems.request.duration` | **Seconds** — confirmed via [OutSystems 11 Log data reference](https://success.outsystems.com/Documentation/11/Managing_the_Applications_Lifecycle/Monitor_and_Troubleshoot/Logging_database_and_architecture/Log_data_reference) ("Time in seconds the extension call took"). `db-extension.conf` copies the raw `oslog_Extension.Duration` column verbatim, so it's seconds too — consistent with streaming. `app-extension.conf` (MonitorProbe) is unverified; MonitorProbe wraps the same table via its own REST API and could reformat the unit. |

## CyclicJob (timer)

| Source field | Dynatrace attribute | Notes |
|---|---|---|
| `Cyclic_Job_Name` | `code.function` | |
| `Cyclic_Job_Key` | `outsystems.code.function.key` | |
| `Duration` | `outsystems.request.duration` | **Seconds** — same source confirms "Duration, in seconds, of the execution of the job." Same DB-vs-MonitorProbe caveat as Extension above. |
| `Should_Have_Run_At` | `outsystems.timer.shouldhaverunat` | |
| `Next_Run` | `outsystems.timer.nextrun` | |

## RequestEvent

| Source field | Dynatrace attribute | Notes |
|---|---|---|
| `RequestEventName` | `outsystems.log.event.type` | `WebScreenClientExecuted`, `QueryExecuted`, … |
| `EventDetails` (raw JSON) | `content` | |
| `EventDetails` keys | `outsystems.request.event.details.<key>` (lowercased) | e.g. `.d` (duration ms), `.tqt` (query time), `.tcit` (integration call time), `.lt`, `.ttfb`, `.sat`, `.ss`, `.vss` |

## ServiceAPI / WebReference

| Source field | Dynatrace attribute |
|---|---|
| `Endpoint` / consumed reference URL | `outsystems.log.endpoint` |
| `Entrypoint_Name` / web service name | `outsystems.log.entrypoint_name` |
| method name | `code.function` |
| `Original_Request_Key` | `outsystems.request.original_key` |

## Legacy → canonical rename table (dashboards)

For anyone migrating existing dashboards or notebooks built on the old Logstash names:

| Legacy field | Canonical field |
|---|---|
| `message_type` / `log.data_source` | `outsystems.log.type` |
| `application_name` / `application.name` | `outsystems.app.name` |
| `environment_name` | `deployment.environment` |
| `tenant_name` / `tenant_id` | `outsystems.tenant.id` |
| `error_message` | `exception.message` |
| `stack_trace` / `message_content.stack_trace` | `exception.stacktrace` |
| `id` (error id) | `outsystems.log.uid` |
| `instant` | `timestamp` |
| `request_key` | `outsystems.request.key` |
| `session_id` | `outsystems.user.session.id` |
| `server` / `server_name` | `host.name` |
| `module_name` | `outsystems.module.name` |
| `module_name == "SLOWSQL"` | `outsystems.log.message.tag == "SLOWSQL"` |
| `outsystems.request.slowquery.query.duration.ms` | `outsystems.request.duration` |
| `outsystems.request.slowquery.query` (tenant-side processing rule) | `outsystems.log.message.object` |
| `server` as dashboard Host column | `coalesce(host.name, outsystems.cloud.infrastructure_orn)` — self-managed sends `host.name`, OutSystems Cloud streaming sends the infrastructure ORN |
| `action_name` | `code.function` |
| `duration` | `outsystems.request.duration` |
| `process_*` (BPT dashboards) | `outsystems.process.*` |
