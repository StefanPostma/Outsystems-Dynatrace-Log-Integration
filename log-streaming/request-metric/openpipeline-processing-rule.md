# OpenPipeline processing rule

Runs inside Dynatrace, right after the OutSystems OTLP logs are ingested and before they're written to Grail. No extra infrastructure — a one-time configuration step per tenant.

> ⚠️ Not verified against a live tenant. The DQL below is the source of truth for *what* to compute; the exact processor name and screen layout in **Settings → Log Monitoring → OpenPipeline** may differ by Dynatrace version. Confirm the current UI path (or the OpenPipeline configuration API) before rolling this out to a customer.

## Where to add it

1. Settings → Log Monitoring → OpenPipeline
2. Open (or create) the pipeline that matches the OutSystems log source — typically the one carrying `outsystems.log.type`
3. Add a **processing** stage → a DQL-based field extraction processor
4. Paste the DQL below as its definition
5. Scope the processor to records where `outsystems.log.type` is `Integration` or `ServiceAPI`, if the stage supports a matching condition separately from the DQL itself

## DQL

```dql
fieldsAdd outsystems.api.endpoint = if(outsystems.log.type == "Integration", outsystems.log.endpoint,
                                    else: if(outsystems.log.type == "ServiceAPI", outsystems.log.entrypoint_name))

fieldsAdd outsystems.api.response_time = if(in(outsystems.log.type, "Integration", "ServiceAPI"),
                                          outsystems.request.duration)

fieldsAdd outsystems.api.direction = if(outsystems.log.type == "Integration", "consumed",
                                     else: if(outsystems.log.type == "ServiceAPI", "exposed"))
```

`outsystems.log.type` is left untouched — these three fields are additions, not a type override. Records of any other type pass through with `outsystems.api.*` simply absent (the `if()` calls fall through to null with no `else`).

## Verifying

```dql
fetch logs
| filter in(outsystems.log.type, "Integration", "ServiceAPI")
| fields timestamp, outsystems.log.type, outsystems.api.endpoint, outsystems.api.response_time, outsystems.api.direction
| limit 20
```
