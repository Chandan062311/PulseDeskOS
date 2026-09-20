"""Supervisor verify step: live Jev verdicts on the 4 worker outputs."""

from __future__ import annotations

import asyncio
import json
import os
import sys

sys.path.insert(0, "pulsedesk-os")

with open("pulsedesk-os/.env", encoding="utf-8") as _env_file:
    for line in _env_file:
        line = line.strip()
        if line.startswith("TYPESAFE_API_KEY=") and "your-key" not in line:
            os.environ["TYPESAFE_API_KEY"] = line.split("=", 1)[1].strip().strip('"')

from backend.orchestration.schemas import WorkerResult
from backend.orchestration.trace import TraceLogger
from backend.orchestration.verifier import verify_live
from sandbox.supervise import SUBTASKS

SOURCES = {
    "R1-benchmark": ["pulsedesk-os/sandbox/agent-run/R1-benchmark.md"],
    "R2-security": ["pulsedesk-os/sandbox/agent-run/R2-security.md"],
    "R3-docs": ["pulsedesk-os/sandbox/agent-run/R3-docs.md"],
    "R4-release": ["pulsedesk-os/RELEASE_v1.md", "pulsedesk-os/CHANGELOG.md"],
}
WORKERS = {
    "R1-benchmark": "scout",
    "R2-security": "scout",
    "R3-docs": "scout",
    "R4-release": "scribe",
}


def _read(path: str) -> str:
    """Read a text file (sandbox helper with proper file handling)."""
    with open(path, encoding="utf-8") as f:
        return f.read()


async def _main() -> None:
    trace = TraceLogger("pulsedesk-os/sandbox/agent-run/trace.jsonl")
    verdicts = []
    for sub in SUBTASKS:
        output = "\n\n".join(_read(p) for p in SOURCES[sub.id])
        result = WorkerResult(subtask_id=sub.id, worker=WORKERS[sub.id], output=output)  # type: ignore[arg-type]
        verdict = await verify_live(result, list(sub.acceptance))
        verdicts.append(verdict.model_dump())
        trace.event(
            "verify",
            sub.id,
            f"verdict={verdict.verdict} meets={verdict.meets_criteria:.2f} "
            f"complete={verdict.complete:.2f} honest={verdict.honest:.2f} ({verdict.reason})",
        )
        print(
            f"{sub.id}: {verdict.verdict} "
            f"(meets={verdict.meets_criteria:.2f} complete={verdict.complete:.2f} "
            f"honest={verdict.honest:.2f})"
        )
    with open("pulsedesk-os/sandbox/agent-run/verdicts.json", "w", encoding="utf-8") as f:
        json.dump(verdicts, f, indent=2)


if __name__ == "__main__":
    asyncio.run(_main())
