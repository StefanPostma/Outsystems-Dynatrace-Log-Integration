# Connecting OutSystems log data to RUM session data in Grail

Customer ask: join the OTel log data this repo ingests (`outsystems.log.*`) with real user session data, so a slow or failed screen a user experienced can be traced back to the backend request that caused it, and vice versa.

Everything below was verified live against the `hrr20220.sprint` tenant (`dtctl ctx` → `sprint`) — no OutSystems app runs there, so the RUM↔trace mechanism is proven against a different (PHP/Laravel) stack. The OutSystems-specific piece is a design, not yet verified end to end.

## What "new RUM" actually is

Dynatrace has replaced classic RUM (USQL, a proprietary session store) with a Grail-native model:

| | Classic RUM | New RUM |
|---|---|---|
| Storage | Proprietary RUM store | Grail, alongside logs/spans/bizevents |
| Query | USQL only | DQL — joins with any other Grail data |
| Data objects | none queryable directly | `user.sessions`, `user.events`, `user.replays` |
| Ingestion | fixed agent pipeline | OpenPipeline (`user.events:default`, `user.sessions:default`) — customizable |

**This repo's `shared/dashboards/4.0 RUM Overview.json` is built entirely on the classic path** — it calls `rumUserSessionsClient.getUsqlResultAsTable()` from a code tile. That's deprecated by the new model and, more importantly, **cannot be joined against `outsystems.log.*` at all** — USQL results never enter Grail as rows. Migrating that dashboard to `fetch user.sessions` / `fetch user.events` is a prerequisite for any of the correlation work below, independent of what the customer decides next.

## Verified schema (live queries, this tenant)

`user.sessions` — one row per browser session:
`dt.rum.session.id`, `dt.rum.session_id_classic`, `dt.rum.browser.session_id`, `dt.rum.application.id`, `dt.smartscape.frontend`, `start_time`/`end_time`, `duration`, `request_count`, `error.count` (+ `.exception_count`, `.http_4xx_count`, `.http_5xx_count`, `.anr_count`), `user_action_count`, `browser.*`, `device.*`, `os.name`, `geo.*`, `dt.rum.user_type` (`real_user` / `robot`), `characteristics.is_bounce`, `characteristics.has_replay`.

`user.events` — one row per page view / resource / XHR / user action:
all of the above session-scoped fields, plus `view.url.full`, `page.url.full`, `request.type` (`doc`, `fetch_xhr`, `xmlhttprequest`, `script`, …), `http.response.status_code`, `duration`, Core Web Vitals (`web_vitals.*`), and — the correlation-relevant ones:

- **`trace.id`** (uid) — W3C trace id, when present
- **`span.id`** (uid) — the span the RUM agent itself created for that resource/request
- **`request.trace_context_hint`** — why trace context is or isn't present:

  | value | meaning (observed in this tenant) |
  |---|---|
  | `set` | the RUM agent added a fresh `traceparent` header to this outgoing request |
  | `from_server` | trace context came back via the `Server-Timing` response header (backend already had a OneAgent-issued trace) |
  | `cross_origin` | request went to a different origin — no header added |
  | `not_http` | non-network event |
  | `disabled` | trace context propagation turned off in RUM config |
  | `missing_values` | expected values absent (agent-side issue) |
  | `not_set` | no attempt was made (most static asset loads) |

No custom user-identifier field (e.g. from a `dtrum.identifyUser()`-style call) was observed in this tenant's live data — none of the sampled apps use it. If a customer already tags sessions with their own user id, the field name needs verifying against their tenant; don't assume one.

## Proof the mechanism works

```dql
fetch user.events, from: now()-7d
| filter request.trace_context_hint == "set" and isNotNull(trace.id)
| fields trace.id
```
→ real trace ids, e.g. `affd21baad7fe8bbc8fe4f836c06f1ce`

```dql
fetch spans, from: now()-7d
| filter trace.id == toUid("affd21baad7fe8bbc8fe4f836c06f1ce")
| fields trace.id, span.id, span.name
```
→ real backend spans for that exact trace: `GET {language}/xhr/get-prices/{location_id}`, `Illuminate\Foundation\Http\Kernel.handle`, `Illuminate\Routing\Route.run`, `PREPARE mib_website` (a DB call).

So: **RUM → backend span correlation via `trace.id` already works, natively, with zero OutSystems-specific work — provided the backend process is monitored by a full-stack Dynatrace OneAgent** (a separate capability from OTel log streaming/Logstash, which this repo doesn't otherwise depend on).

## The actual gap

`outsystems.log.*` records have no `trace.id` field and never will natively — OutSystems' own `Request_Key`/`Session_Id` are platform-internal identifiers with no relationship to W3C trace context. Backend spans (if OneAgent monitors the OutSystems servers) and RUM events already share `trace.id`; **logs are the disconnected third leg.**

## The customer split changes which approach applies

Per the actual customer base:

| | Non-SaaS (on-prem / IaaS) | SaaS (OutSystems Cloud) — **most customers** |
|---|---|---|
| Can install OneAgent on OutSystems servers | Yes | No — not their infrastructure |
| Log ingestion | Logstash only (no log streaming) | Log streaming only |
| RUM | Auto-injected by OneAgent, or agentless | **Agentless RUM** (manual JS snippet in the app) — only option, no OneAgent to auto-inject |
| Viable approach | **B** — full-stack OneAgent already produces backend spans | **A** — no spans exist at all; the log stream is the only backend signal |

Since most customers are SaaS, **A is the approach that matters for most of this repo's audience.** Two facts made it fully buildable, verified today:

1. **The agentless RUM JS agent adds a `traceparent` header to same-origin XHR/fetch/AJAX calls automatically — no configuration needed.** (Confirmed via Dynatrace docs.) OutSystems screens and their AJAX/postback calls are same-origin by definition, so every RUM-captured interaction with the app already carries a real W3C trace id on the wire, with or without a backend agent. `request.trace_context_hint == "set"` shows up on `user.events` regardless.
2. **OutSystems 11's `HTTPRequestHandler` API exposes `GetRequestHeader(HeaderName)`, reading any inbound header by name — works in Traditional Web, Reactive Web, and Mobile, in REST API entry points and screens, in AJAX calls, on-premises and in the cloud.** (Confirmed via OutSystems docs.) So `GetRequestHeader("traceparent")` gets the exact same trace id the RUM agent just put on the request.

### The recipe (SaaS / log streaming path)

1. Add a shared server action, called early in each request (a common flow, or a screen's `Preparation`), that does:
   ```
   TraceParent = HTTPRequestHandler.GetRequestHeader("traceparent")   // "00-<32 hex trace-id>-<16 hex parent-id>-<flags>"
   If TraceParent <> "":
       TraceId = Substr(TraceParent, 3, 32)   // strip "00-" prefix, take the 32-char trace id
       LogMessage(Message: "TRACECTX " + TraceId, MessageType: "TraceContext")
   ```
   This reuses the exact mechanism OutSystems developers already use for custom logging — it lands in the same `General` log (`oslog_General` / `outsystems.log.type == "General"`) that both tracks already ingest. No new log table, no platform change.
2. Both pipelines already have a message-tag pattern for this (`outsystems.log.message.tag == "SLOWSQL"` is the existing precedent — see [OTEL-Field-Mapping.md](OTEL-Field-Mapping.md)). Add a matching `TraceContext` tag and a `trace.id` extraction:
   - **Logstash**: extend the existing `grok` stage in `db-general.conf`/`app-general.conf` with a second pattern matching `TRACECTX (?<trace_id>[0-9a-f]{32})`, renamed to `[trace][id]`.
   - **Log streaming**: same logic as a DQL `parse` step in an OpenPipeline processing rule, or an OTTL `set()` in the Collector config already introduced for `outsystems.api.*` in [`log-streaming/request-metric/`](../log-streaming/request-metric/).
3. Every `General` record carrying this tag now has both `trace.id` and `outsystems.request.key` for that request. Other log types from the *same* request (`Error`, `Screen`, `Integration`, …) don't need `trace.id` written onto them directly — a DQL `lookup` on `outsystems.request.key` at query time pulls it in:
   ```dql
   fetch logs
   | filter outsystems.log.type == "Error"
   | lookup [fetch logs | filter outsystems.log.message.tag == "TraceContext" | fields outsystems.request.key, trace.id],
       sourceField: outsystems.request.key, lookupField: outsystems.request.key
   | filter isNotNull(lookup.trace.id)
   | lookup [fetch user.events | fields trace.id, dt.rum.session.id, view.url.full],
       sourceField: lookup.trace.id, lookupField: trace.id
   ```
   That's the full chain — an OutSystems error joined to the exact RUM session and page it happened on — in one query, no new data object needed.

### Non-SaaS / Logstash + OneAgent path (approach B)

Full-stack OneAgent already produces spans with real `trace.id` for OutSystems requests (same mechanism proven above against the Laravel backend). The only missing link is `outsystems.request.key` on those spans, via a Dynatrace **Request Attribute** rule capturing it from wherever OutSystems exposes it (needs checking — likely not on the wire today, so this may still need the same `GetRequestHeader`-adjacent pattern in reverse: an OutSystems action *setting* a response header or cookie with `Request_Key`, which OneAgent then picks up as a Request Attribute). Once that exists: `outsystems.request.key` joins spans↔logs directly, and `trace.id` joins spans↔RUM natively — no manual log-side trace id parsing needed at all for this segment.

### Fallback for both segments

**C (time + screen name)** needs nothing new and is worth shipping regardless as a same-day, approximate view while A or B is built out.

## What's still open

1. **Verify `HTTPRequestHandler.GetRequestHeader` against a real OutSystems Cloud app** — confirmed via documentation, not yet tested live (no OutSystems app in the tenant used for this research).
2. **Confirm the agentless RUM snippet's application id/config used by these SaaS customers actually treats the OutSystems app domain as same-origin** — true by default for a standard single-domain OutSystems app; worth double-checking for factory setups behind a reverse proxy or multiple frontend domains.
3. **Decide where the shared "read header, log trace id" action lives** — a factory-wide shared module all apps extend, versus something each app team adds individually. This is a delivery/packaging decision, not a technical one.
