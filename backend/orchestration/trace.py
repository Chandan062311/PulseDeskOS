"""Supervisor trace: JSONL log of every routing/verification decision."""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Literal

from .schemas import SupervisorTrace


class TraceLogger:
    """Append-only JSONL trace. One line per supervisor event."""

    def __init__(self, path: str | Path) -> None:
        """Open (creating parents for) the trace file."""
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def event(
        self,
        stage: Literal["route", "execute", "verify", "compose", "escalate"],
        subtask_id: str = "",
        detail: str = "",
    ) -> SupervisorTrace:
        """Append one event and return it."""
        entry = SupervisorTrace(
            run_id=self._path.stem,
            stage=stage,
            subtask_id=subtask_id,
            detail=detail,
        )
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "ts": datetime.datetime.now(datetime.UTC).isoformat(),
                        "run_id": entry.run_id,
                        "stage": entry.stage,
                        "subtask_id": entry.subtask_id,
                        "detail": entry.detail,
                    }
                )
                + "\n"
            )
        return entry
