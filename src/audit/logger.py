"""Immutable audit logger backed by PostgreSQL."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

import structlog

from src.core.models import AuditEvent

logger = structlog.get_logger(__name__)


class AuditLogger:
    """Append-only audit log for recording all agent actions and decisions."""

    def __init__(self, db_pool: Any | None = None) -> None:
        self._db_pool = db_pool
        self._in_memory_log: list[AuditEvent] = []

    async def log(self, event: AuditEvent) -> None:
        """Append an audit event. Writes to DB if available, always stores in memory."""
        self._in_memory_log.append(event)
        logger.info(
            "audit_event",
            event_id=str(event.id),
            goal_id=str(event.goal_id),
            agent=event.agent,
            action=event.action,
        )

        if self._db_pool is not None:
            try:
                await self._write_to_db(event)
            except Exception as exc:
                logger.error("audit_db_write_failed", error=str(exc))

    async def _write_to_db(self, event: AuditEvent) -> None:
        """Write audit event to PostgreSQL (append-only)."""
        async with self._db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO audit_events (id, goal_id, task_id, agent, action, payload, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                event.id,
                event.goal_id,
                event.task_id,
                event.agent,
                event.action,
                json.dumps(event.payload),
                event.timestamp,
            )

    async def get_events(
        self,
        goal_id: uuid.UUID | None = None,
        agent: str | None = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Retrieve audit events with optional filtering."""
        events = self._in_memory_log
        if goal_id:
            events = [e for e in events if e.goal_id == goal_id]
        if agent:
            events = [e for e in events if e.agent == agent]
        return sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]

    async def get_timeline(self, goal_id: uuid.UUID) -> list[dict]:
        """Get chronological timeline of events for a goal."""
        events = [e for e in self._in_memory_log if e.goal_id == goal_id]
        return [
            {
                "timestamp": e.timestamp.isoformat(),
                "agent": e.agent,
                "action": e.action,
                "task_id": str(e.task_id) if e.task_id else None,
                "payload": e.payload,
            }
            for e in sorted(events, key=lambda e: e.timestamp)
        ]

    @property
    def event_count(self) -> int:
        return len(self._in_memory_log)
