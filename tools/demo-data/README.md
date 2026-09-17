# Demo data generator

Ingests synthetic OutSystems logs into a Dynatrace tenant using the canonical OTEL field names from [Documentation/OTEL-Field-Mapping.md](../../Documentation/OTEL-Field-Mapping.md). Use it to validate both dashboard sets ([log-streaming](../../log-streaming/dashboards/) and [logstash](../../logstash/dashboards/)) without a live OutSystems environment.

Covers all log types: Error, General (incl. SLOWSQL), Screen, MobileRequest, Integration, Extension, CyclicJob, RequestEvent.

## Usage

```bash
export DT_ENVIRONMENT_URL="https://<tenant>.live.dynatrace.com"
export DT_API_TOKEN="dt0c01...."   # scope: logs.ingest (+ bizevents.ingest for --bizevents)

# preview without sending
python3 generate_demo_logs.py --dry-run

# 2 hours of history, 200 records/hour
python3 generate_demo_logs.py --hours 2 --rate 200

# also send the outsystems.error.patterns bizevents used by 1.0 Top Findings
python3 generate_demo_logs.py --hours 2 --rate 200 --bizevents
```

Dynatrace rejects log timestamps older than 24 hours, so keep `--hours` ≤ 24.

Verify:

```dql
fetch logs
| filter isNotNull(outsystems.log.type)
| summarize count(), by: {outsystems.log.type}
```
