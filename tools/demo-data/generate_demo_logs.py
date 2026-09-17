#!/usr/bin/env python3
"""Ingest synthetic OutSystems demo logs into Dynatrace.

Generates logs for every OutSystems log type using the canonical OTEL
attribute names from Documentation/OTEL-Field-Mapping.md, so both the
logstash/dashboards and log-streaming/dashboards sets can be validated
without a live OutSystems environment.

Usage:
    export DT_ENVIRONMENT_URL="https://<tenant>.live.dynatrace.com"
    export DT_API_TOKEN="dt0c01...."   # needs logs.ingest (and events.ingest for --bizevents)
    python3 generate_demo_logs.py --hours 2 --rate 200
    python3 generate_demo_logs.py --hours 2 --rate 200 --bizevents

Notes:
- Dynatrace rejects log records older than 24h; keep --hours <= 24.
- The token needs the "Ingest logs" (logs.ingest) scope; for --bizevents
  also "Ingest bizevents" (bizevents.ingest).
"""
import argparse
import json
import os
import random
import sys
import time
import urllib.request

APPS = [
    ("CustomerPortal", "b1f9c2d0-1111-4a71-9c60-000000000001"),
    ("FieldServices", "b1f9c2d0-2222-4a71-9c60-000000000002"),
    ("OrderManagement", "b1f9c2d0-3333-4a71-9c60-000000000003"),
    ("HRSelfService", "b1f9c2d0-4444-4a71-9c60-000000000004"),
]
ENVIRONMENTS = ["Development", "Test", "Production"]
TENANTS = ["1", "2"]
SERVERS = ["osfe-prod-01", "osfe-prod-02", "osfe-test-01"]
SCREENS = ["Home", "OrderList", "OrderDetail", "CustomerSearch", "Dashboard", "Login"]
ENDPOINTS = [
    "https://api.paymentprovider.com/v2/charge",
    "https://erp.internal.local/soap/OrderService",
    "https://api.postcode.eu/nl/v1/addresses",
    "https://crm.internal.local/rest/customers",
]
ERRORS = [
    ("Invalid login attempt. User not found.", "at OutSystems.HubEdition.RuntimePlatform.Login..."),
    ("Timeout expired. The timeout period elapsed prior to completion of the operation.",
     "at System.Data.SqlClient.SqlConnection.OnError(SqlException exception)..."),
    ("Object reference not set to an instance of an object.",
     "at ssCustomerPortal.Flows.FlowMain.ScrnOrderDetail..."),
    ("The remote server returned an error: (500) Internal Server Error.",
     "at System.Net.HttpWebRequest.GetResponse()..."),
    ("A network-related or instance-specific error occurred while establishing a connection to SQL Server.",
     "at System.Data.ProviderBase.DbConnectionPool.TryGetConnection..."),
]
SLOW_OBJECTS = ["GetOrdersForCustomer", "SyncProductCatalog", "SearchCustomersAdv", "GetOpenInvoices"]


def now_ms():
    return int(time.time() * 1000)


def base_record(ts, app, log_type, env, extra):
    app_name, app_key = app
    rec = {
        "timestamp": ts,
        "outsystems.log.type": log_type,
        "outsystems.app.name": app_name,
        "outsystems.app.key": app_key,
        "outsystems.espace.name": app_name + "Core",
        "outsystems.module.name": app_name + "Core",
        "deployment.environment": env,
        "outsystems.tenant.id": random.choice(TENANTS),
        "outsystems.request.key": f"req-{random.getrandbits(64):016x}",
        "outsystems.user.session.id": f"ses-{random.getrandbits(48):012x}",
        "enduser.id": str(random.randint(1000, 1200)),
        "host.name": random.choice(SERVERS),
        "outsystems.log.uid": f"uid-{random.getrandbits(64):016x}",
        "log.source": "outsystems-demo-generator",
    }
    rec.update(extra)
    return rec


def make_record(ts, env):
    app = random.choice(APPS)
    roll = random.random()
    if roll < 0.15:  # Error
        msg, stack = random.choice(ERRORS)
        return base_record(ts, app, "Error", env, {
            "content": msg,
            "exception.message": msg,
            "exception.stacktrace": stack,
            "outsystems.log.error.uid": f"err-{random.getrandbits(64):016x}",
            "code.function": "Scrn" + random.choice(SCREENS),
            "severity": "ERROR",
        })
    if roll < 0.25:  # General (incl. SLOWSQL)
        if random.random() < 0.5:
            obj = random.choice(SLOW_OBJECTS)
            dur = random.randint(250, 9000)
            return base_record(ts, app, "General", env, {
                "content": f" {obj} took {dur} ms",
                "outsystems.log.message.tag": "SLOWSQL",
                "outsystems.log.message.object": obj,
                "outsystems.request.duration": str(dur),
                "code.function": obj,
            })
        return base_record(ts, app, "General", env, {
            "content": "Scheduled maintenance task completed",
            "outsystems.log.message.tag": "INFO",
            "code.function": "MaintenanceJob",
        })
    if roll < 0.45:  # Screen
        return base_record(ts, app, "Screen", env, {
            "content": "Screen request",
            "outsystems.log.screen.name": random.choice(SCREENS),
            "outsystems.log.screen.type": "WEB",
            "outsystems.log.screen.access_mode": random.choice(["AJAX", "SCREEN"]),
            "outsystems.request.duration": str(random.randint(30, 4000)),
            "outsystems.traditional.ss": str(random.randint(500, 6000)),
            "outsystems.log.viewstate_bytes": str(random.randint(1000, 12000)),
            "http.client_ip": f"10.1.{random.randint(0,255)}.{random.randint(1,254)}",
        })
    if roll < 0.60:  # Integration
        err = random.random() < 0.08
        rec = base_record(ts, app, "Integration", env, {
            "content": "Integration call",
            "outsystems.log.endpoint": random.choice(ENDPOINTS),
            "code.function": "OrderService.SubmitOrder",
            "outsystems.request.duration": str(random.randint(20, 6000)),
            "http.method": random.choice(["REST (Consume)", "SOAP (Consume)"]),
            "outsystems.integration.type": "False",
            "net.host.ip": f"10.1.{random.randint(0,255)}.{random.randint(1,254)}",
        })
        if err:
            rec["outsystems.log.error.uid"] = f"err-{random.getrandbits(64):016x}"
        return rec
    if roll < 0.72:  # RequestEvent
        d = random.randint(50, 5000)
        return base_record(ts, app, "RequestEvent", env, {
            "content": json.dumps({"D": d, "TQT": int(d * 0.4), "TCIT": int(d * 0.2)}),
            "outsystems.log.event.type": random.choice(
                ["WebScreenServerExecuted", "WebScreenClientExecuted", "QueryExecuted"]),
            "outsystems.request.event.details.d": str(d),
            "outsystems.request.event.details.tqt": str(int(d * 0.4)),
            "outsystems.request.event.details.tcit": str(int(d * 0.2)),
        })
    if roll < 0.82:  # Extension
        return base_record(ts, app, "Extension", env, {
            "content": "Extension executed",
            "outsystems.code.function.owner": "IntegrationUtils",
            "outsystems.code.owner.function.id": str(random.randint(1, 50)),
            "code.function": "FormatDocument",
            "outsystems.request.duration": str(random.randint(5, 800)),
        })
    if roll < 0.92:  # CyclicJob
        return base_record(ts, app, "CyclicJob", env, {
            "content": "Timer executed",
            "code.function": random.choice(["SyncCatalog", "CleanupSessions", "SendDigestEmails"]),
            "outsystems.code.function.key": f"tim-{random.getrandbits(48):012x}",
            "outsystems.request.duration": str(random.randint(1, 300)),
        })
    # MobileRequest
    return base_record(ts, app, "MobileRequest", env, {
        "content": "Mobile request",
        "outsystems.log.screen.name": random.choice(SCREENS),
        "outsystems.log.endpoint": "ScreenDataSetGetOrders",
        "outsystems.request.duration": str(random.randint(40, 3000)),
        "outsystems.user.login_id": f"login-{random.randint(1000,1200)}",
    })


def post(url, token, payload, content_type):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Api-Token {token}", "Content-Type": content_type},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hours", type=float, default=2, help="spread records over the last N hours (max 24)")
    ap.add_argument("--rate", type=int, default=200, help="records per hour")
    ap.add_argument("--bizevents", action="store_true", help="also send outsystems.error.patterns bizevents")
    ap.add_argument("--dry-run", action="store_true", help="print a sample instead of sending")
    args = ap.parse_args()

    env_url = os.environ.get("DT_ENVIRONMENT_URL", "").rstrip("/")
    token = os.environ.get("DT_API_TOKEN", "")
    if not args.dry_run and (not env_url or not token):
        sys.exit("Set DT_ENVIRONMENT_URL and DT_API_TOKEN (see --help)")

    total = int(args.hours * args.rate)
    span_ms = int(args.hours * 3600 * 1000)
    end = now_ms()
    records = []
    for _ in range(total):
        ts = end - random.randint(0, span_ms)
        env = random.choices(ENVIRONMENTS, weights=[2, 2, 6])[0]
        records.append(make_record(ts, env))

    if args.dry_run:
        print(json.dumps(records[:5], indent=2))
        print(f"... {total} records total (dry run, nothing sent)")
        return

    sent = 0
    for i in range(0, len(records), 500):
        batch = records[i:i + 500]
        status = post(f"{env_url}/api/v2/logs/ingest", token, batch, "application/json; charset=utf-8")
        sent += len(batch)
        print(f"logs: {sent}/{total} (HTTP {status})")

    if args.bizevents:
        events = []
        for app_name, _ in APPS:
            for msg, _stack in ERRORS[:3]:
                events.append({
                    "specversion": "1.0",
                    "id": f"demo-{random.getrandbits(64):016x}",
                    "source": "outsystems.demo.generator",
                    "type": "outsystems.error.patterns",
                    "data": {
                        "application": app_name,
                        "environment": random.choice(ENVIRONMENTS),
                        "tenant_name": random.choice(TENANTS),
                        "module": app_name + "Core",
                        "msg.pattern": msg,
                        "count": random.randint(1, 40),
                    },
                })
        status = post(f"{env_url}/api/v2/bizevents/ingest", token, events,
                      "application/cloudevent-batch+json")
        print(f"bizevents: {len(events)} (HTTP {status})")

    print("Done. Query with: fetch logs | filter isNotNull(outsystems.log.type)")


if __name__ == "__main__":
    main()
