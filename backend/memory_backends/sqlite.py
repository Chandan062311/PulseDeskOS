"""SQLite-backed memory store with naive lexical shortlist.

No embeddings here: ranking is plain token overlap so results stay
deterministic and testable offline. TypeSafe Jev reranks the shortlist
later in :mod:`backend.memory`.
"""

from __future__ import annotations

import sqlite3
import threading
import uuid


class SqliteMemoryBackend:
    """Tenant-scoped text store on a SQLite file.

    Schema: ``memory(id TEXT PK, tenant_id TEXT, text TEXT, type TEXT)``.
    """

    def __init__(self, path: str = "memory.db") -> None:
        """Open (creating) the SQLite file and ensure the schema exists.

        Args:
            path: Filesystem path, or ``":memory:"`` for an ephemeral store.
        """
        self._path = path
        # check_same_thread=False + a lock: uvicorn serves requests on a
        # thread pool while the backend singleton is created once at import.
        # WAL mode: safe for multi-worker (multi-process) production serving.
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._lock = threading.Lock()
        with self._lock:
            self._conn.execute("PRAGMA journal_mode=WAL;")
            self._conn.commit()
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memory (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                text TEXT NOT NULL,
                type TEXT NOT NULL
            )
            """,
        )
        self._conn.commit()

    def store(self, tenant_id: str, text: str, type: str) -> str:
        """Persist ``text`` for ``tenant_id`` and return the new id."""
        mem_id = uuid.uuid4().hex
        with self._lock:
            self._conn.execute(
                "INSERT INTO memory (id, tenant_id, text, type) VALUES (?, ?, ?, ?)",
                (mem_id, tenant_id, text, type),
            )
            self._conn.commit()
        return mem_id

    def search_bm25(self, tenant_id: str, query: str, top_k: int) -> list[dict[str, str]]:
        """Rank tenant rows by lowercase token overlap with ``query``.

        Score is the count of shared whitespace-separated tokens. Rows are
        returned best-first as ``[{id, text, type}]``, truncated to ``top_k``.
        """
        query_tokens = set(query.lower().split())
        with self._lock:
            rows = self._conn.execute(
                "SELECT id, text, type FROM memory WHERE tenant_id = ?",
                (tenant_id,),
            ).fetchall()
        scored: list[tuple[int, str, str, str]] = []
        for mem_id, text, mem_type in rows:
            overlap = len(query_tokens & set(str(text).lower().split()))
            scored.append((overlap, str(mem_id), str(text), str(mem_type)))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            {"id": mem_id, "text": text, "type": mem_type}
            for _, mem_id, text, mem_type in scored[: max(top_k, 0)]
        ]

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        self._conn.close()

    def list(self, tenant_id: str, limit: int) -> list[dict[str, str]]:
        """Return newest-first rows for a tenant as [{id,text,type}]."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT id, text, type FROM memory WHERE tenant_id = ? ORDER BY rowid DESC LIMIT ?",
                (tenant_id, max(limit, 0)),
            ).fetchall()
        return [{"id": str(i), "text": str(t), "type": str(y)} for i, t, y in rows]

    def delete(self, mem_id: str, tenant_id: str | None = None) -> bool:
        """Delete one row by id, optionally scoped to a tenant.

        Args:
            mem_id: Row id to remove.
            tenant_id: When given, the row must belong to this tenant;
                mismatches report False like a missing id.

        Returns:
            True when a row was removed.
        """
        with self._lock:
            if tenant_id is None:
                cur = self._conn.execute("DELETE FROM memory WHERE id = ?", (mem_id,))
            else:
                cur = self._conn.execute(
                    "DELETE FROM memory WHERE id = ? AND tenant_id = ?", (mem_id, tenant_id)
                )
            self._conn.commit()
            return cur.rowcount > 0

    def count(self, tenant_id: str) -> int:
        """Count rows for a tenant."""
        with self._lock:
            row = self._conn.execute(
                "SELECT COUNT(*) FROM memory WHERE tenant_id = ?", (tenant_id,)
            ).fetchone()
        return int(row[0]) if row else 0
