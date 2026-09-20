"""Worker execution interface. Runtime-agnostic by design.

In live supervisor sessions the executor is the host's subagent facility
(this repo's sessions use parallel Claude subagents: one ``Task`` call per
subtask, worker kind + skills + acceptance criteria in the prompt, result
returned as text). Any other runtime (local processes, remote agents)
implements this protocol instead — the supervisor never changes.
"""

from __future__ import annotations

from typing import Protocol

from .schemas import RouteDecision, SubTask, WorkerResult


class Executor(Protocol):
    """Runs one routed subtask to a result."""

    def run(self, subtask: SubTask, route: RouteDecision) -> WorkerResult:
        """Execute ``subtask`` with the scoped worker from ``route``."""
        ...


WORKER_BRIEFS: dict[str, str] = {
    "scout": (
        "Read-only worker. Inspect files, run measurement commands, query the "
        "API. Write nothing except your single findings file. Report numbers "
        "you actually observed; mark anything uncertain as such."
    ),
    "builder": (
        "Implementation worker. Change only the files your brief names. Keep "
        "contracts frozen, thresholds in config.yaml, and run the relevant "
        "tests before finishing."
    ),
    "scribe": (
        "Documentation worker. Write only the files your brief names. Match "
        "docs to code exactly — no invented endpoints, numbers, or files."
    ),
}
