"""Unit tests for the audit logger."""

import uuid

import pytest

from src.audit.logger import AuditLogger
from src.core.models import AuditEvent


@pytest.mark.unit
class TestAuditLogger:
    @pytest.mark.asyncio
    async def test_log_event(self):
        logger = AuditLogger()
        event = AuditEvent(goal_id=uuid.uuid4(), agent="test", action="test_action")
        await logger.log(event)
        assert logger.event_count == 1

    @pytest.mark.asyncio
    async def test_get_events_by_goal(self):
        logger = AuditLogger()
        goal_id = uuid.uuid4()
        other_id = uuid.uuid4()
        await logger.log(AuditEvent(goal_id=goal_id, agent="a", action="x"))
        await logger.log(AuditEvent(goal_id=other_id, agent="b", action="y"))
        await logger.log(AuditEvent(goal_id=goal_id, agent="c", action="z"))
        events = await logger.get_events(goal_id=goal_id)
        assert len(events) == 2
        assert all(e.goal_id == goal_id for e in events)

    @pytest.mark.asyncio
    async def test_get_events_by_agent(self):
        logger = AuditLogger()
        gid = uuid.uuid4()
        await logger.log(AuditEvent(goal_id=gid, agent="planner", action="plan"))
        await logger.log(AuditEvent(goal_id=gid, agent="executor", action="exec"))
        events = await logger.get_events(agent="planner")
        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_get_timeline(self):
        logger = AuditLogger()
        gid = uuid.uuid4()
        await logger.log(AuditEvent(goal_id=gid, agent="a", action="first"))
        await logger.log(AuditEvent(goal_id=gid, agent="b", action="second"))
        timeline = await logger.get_timeline(gid)
        assert len(timeline) == 2
        assert timeline[0]["action"] == "first"

    @pytest.mark.asyncio
    async def test_event_limit(self):
        logger = AuditLogger()
        gid = uuid.uuid4()
        for i in range(10):
            await logger.log(AuditEvent(goal_id=gid, agent="a", action=f"act_{i}"))
        events = await logger.get_events(goal_id=gid, limit=5)
        assert len(events) == 5
