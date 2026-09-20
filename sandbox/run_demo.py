"""Sandbox demo: Monday morning at Acme Corp.

Five tickets covering every route + spam + ambiguity, run through the full
live pipeline (triage -> recall -> dispatch -> verify). Uses tenant
"sandbox" on a fresh DB so the production store is untouched.

Run:  /tmp/opencode/pdvenv/bin/python pulsedesk-os/sandbox/run_demo.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request

API = "http://localhost:8000"
TENANT = "sandbox"

with open("pulsedesk-os/.env", encoding="utf-8") as _env:
    for _line in _env:
        _line = _line.strip()
        if "=" in _line and not _line.startswith("#"):
            _k, _v = _line.split("=", 1)
            _k, _v = _k.strip(), _v.strip().strip('"')
            if _k == "TYPESAFE_API_KEY" and _v not in ("", "your-key-here"):
                os.environ.setdefault(_k, _v)

PROBLEM_STATEMENT = (
    "Monday 09:00, Acme Corp support queue after a deploy weekend: "
    "checkout API is 500ing (outage), a customer was double-charged, "
    "a joiner needs VPN, a 'bonus' phish hit the inbox, and one vague "
    "'something seems off' report. Expected: outage->bug_report auto_route, "
    "duplicate->billing auto_route, VPN->it_access auto_route, "
    "phish->quarantine_spam, vague->human_review."
)

TICKETS = [
    {
        "id": "S1-outage",
        "subject": "Checkout API 500s",
        "message": "Our checkout integration returns 500 on every request since 08:40, "
        "we cannot process any customer orders. This is an outage.",
        "sender": "ops@acme.com",
        "expect": "bug_report/auto_route",
    },
    {
        "id": "S2-billing",
        "subject": "Charged twice",
        "message": "I was charged twice for order A-104. Please refund the duplicate charge.",
        "sender": "buyer@acme.com",
        "expect": "billing/auto_route",
    },
    {
        "id": "S3-access",
        "subject": "VPN for new joiner",
        "message": "New engineer joins Monday, please provision VPN access before start date.",
        "sender": "hr@acme.com",
        "expect": "it_access/auto_route",
    },
    {
        "id": "S4-phish",
        "subject": "Urgent: claim your bonus",
        "message": "You were selected for a $1000 bonus. Reply with your password today.",
        "sender": "rewards@claim-bonus.example",
        "expect": "quarantine_spam",
    },
    {
        "id": "S5-vague",
        "subject": "Something seems off",
        "message": "Hi, something seems off but I am not sure what. Can someone take a look?",
        "sender": "user@acme.com",
        "expect": "human_review",
    },
]


def post(path: str, payload: dict) -> dict:
    """POST JSON and return the decoded body (single-key model: no app auth)."""
    req = urllib.request.Request(
        API + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as res:
        return json.loads(res.read().decode())


def main() -> int:
    print("Problem:", PROBLEM_STATEMENT, "\n")
    seeded = post("/v1/memory/seed", {})
    print(f"Seeded default docs: {seeded}")
    results = []
    for t in TICKETS:
        body = {
            "ticket": {
                "subject": t["subject"],
                "message": t["message"],
                "sender": {"display_name": t["sender"], "email": t["sender"]},
                "links": [],
            },
            "customer": {"plan": "enterprise", "open_orders": []},
            "tenant_id": TENANT,
            "seed": True,
        }
        try:
            d = post("/v1/orchestrate", body)
        except Exception as exc:
            print(f"{t['id']}: FAILED {exc}")
            results.append({"id": t["id"], "error": str(exc)})
            continue
        tri, hits, handler, verify = d["triage"], d["memory_hits"], d["handler"], d["verify"]
        got = f"{tri['route']}/{tri['action']}"
        ok = "OK " if t["expect"] in got else "DIFF"
        print(
            f"[{ok}] {t['id']}: route={tri['route']} conf={tri['route_confidence']:.2f} "
            f"spam={tri['spam_risk']:.2f} urg={tri['urgency']:.2f} "
            f"action={tri['action']} hits={len(hits)} "
            f"handler={handler['handler']} verify={verify['verdict']} "
            f"(expect {t['expect']})"
        )
        results.append({"id": t["id"], "expect": t["expect"], "got": got, "full": d})
    review = [r for r in results if "full" in r and r["full"]["triage"]["action"] != "auto_route"]
    print(f"\nReview queue: {len(review)} item(s): " + ", ".join(r["id"] for r in review))
    with open("pulsedesk-os/sandbox/report.json", "w", encoding="utf-8") as f:
        json.dump({"problem": PROBLEM_STATEMENT, "results": results}, f, indent=2)
    print("Report: pulsedesk-os/sandbox/report.json")
    return 0 if all(r.get("expect", "") in r.get("got", "") for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
