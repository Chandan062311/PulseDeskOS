"""Supervisor demo run: route 4 release subtasks via live Jev, log the trace.

Usage: /tmp/opencode/pdvenv/bin/python pulsedesk-os/sandbox/supervise.py route
"""

from __future__ import annotations

import asyncio
import json
import os
import sys

sys.path.insert(0, "pulsedesk-os")

for line in open("pulsedesk-os/.env", encoding="utf-8"):
    line = line.strip()
    if line.startswith("TYPESAFE_API_KEY=") and "your-key" not in line:
        os.environ["TYPESAFE_API_KEY"] = line.split("=", 1)[1].strip().strip('"')

from backend.orchestration.router import route_live  # noqa: E402
from backend.orchestration.schemas import SubTask  # noqa: E402
from backend.orchestration.trace import TraceLogger  # noqa: E402

SUBTASKS = [
    SubTask(
        id="R1-benchmark",
        title="Benchmark pipeline latency",
        brief="Measure live latency of triage, recall, orchestrate (10 samples each). "
        "Report p50/max per endpoint plus sample size. Read-only.",
        acceptance=("p50 and max per endpoint", "sample size stated", "numbers actually measured"),
    ),
    SubTask(
        id="R2-security",
        title="Security review pass",
        brief="Grep repo for leaked secrets, re-test tenant isolation on delete, "
        "confirm injection docs are still gated. Report findings with repros. Read-only.",
        acceptance=("secret grep result", "isolation re-test result", "injection re-test result"),
    ),
    SubTask(
        id="R3-docs",
        title="Docs-truth re-audit",
        brief="Re-check README API table, ARCHITECTURE gates, skill thresholds/routes "
        "against current code after brutal repairs. List any remaining drift. Read-only.",
        acceptance=("per-doc verdict", "drift list (empty if none)"),
    ),
    SubTask(
        id="R4-release",
        title="Write release notes",
        brief="Write pulsedesk-os/RELEASE_v1.md and CHANGELOG snippet from sandbox "
        "reports (report.md, brutal/REPORT.md). Match docs to code exactly.",
        acceptance=("RELEASE_v1.md written", "claims match code"),
    ),
]


async def main() -> None:
    trace = TraceLogger("pulsedesk-os/sandbox/agent-run/trace.jsonl")
    routed = []
    for sub in SUBTASKS:
        decision = await route_live(sub)
        routed.append(decision.model_dump())
        trace.event(
            "route",
            sub.id,
            f"worker={decision.worker} conf={decision.worker_confidence:.2f} "
            f"risk={decision.risky:.2f} diff={decision.difficulty:.2f} "
            f"reviewer={decision.needs_reviewer}",
        )
        print(
            f"{sub.id}: worker={decision.worker} conf={decision.worker_confidence:.2f} "
            f"risk={decision.risky:.2f} diff={decision.difficulty:.2f} "
            f"reviewer={decision.needs_reviewer}"
        )
    with open("pulsedesk-os/sandbox/agent-run/routing.json", "w", encoding="utf-8") as f:
        json.dump(routed, f, indent=2)


if __name__ == "__main__":
    asyncio.run(main())
