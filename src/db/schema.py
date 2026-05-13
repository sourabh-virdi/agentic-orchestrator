"""SQLAlchemy ORM models and database schema definition."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship

from src.core.config import settings


class Base(DeclarativeBase):
    pass


class GoalRecord(Base):
    __tablename__ = "goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    constraints = Column(JSON, default=dict)
    status = Column(String(50), default="pending")
    task_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    tasks = relationship("TaskNodeRecord", back_populates="goal")
    audit_events = relationship("AuditEventRecord", back_populates="goal")


class TaskNodeRecord(Base):
    __tablename__ = "task_nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    goal_id = Column(UUID(as_uuid=True), ForeignKey("goals.id"), nullable=False)
    name = Column(String(200), nullable=False)
    agent_type = Column(String(50), nullable=False)
    params = Column(JSON, default=dict)
    dependencies = Column(JSON, default=list)
    status = Column(String(50), default="pending")
    result = Column(JSON, nullable=True)
    retries = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)

    goal = relationship("GoalRecord", back_populates="tasks")


class AuditEventRecord(Base):
    __tablename__ = "audit_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    goal_id = Column(UUID(as_uuid=True), ForeignKey("goals.id"), nullable=False)
    task_id = Column(UUID(as_uuid=True), nullable=True)
    agent = Column(String(100), nullable=False)
    action = Column(String(200), nullable=False)
    payload = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=func.now())

    goal = relationship("GoalRecord", back_populates="audit_events")


class PolicySnapshotRecord(Base):
    __tablename__ = "policy_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version = Column(String(50), nullable=False)
    metrics = Column(JSON, default=dict)
    weights_path = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=func.now())


def create_engine():
    return create_async_engine(settings.database_url, echo=settings.app_debug)


def create_session_factory(engine=None):
    if engine is None:
        engine = create_engine()
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db(engine=None):
    if engine is None:
        engine = create_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


SQL_SCHEMA = """
-- Agentic Orchestrator Database Schema
-- Run this SQL to initialize the database manually if not using SQLAlchemy

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS goals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    constraints JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'pending',
    task_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS task_nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    goal_id UUID NOT NULL REFERENCES goals(id),
    name VARCHAR(200) NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    params JSONB DEFAULT '{}',
    dependencies JSONB DEFAULT '[]',
    status VARCHAR(50) DEFAULT 'pending',
    result JSONB,
    retries INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    goal_id UUID NOT NULL REFERENCES goals(id),
    task_id UUID,
    agent VARCHAR(100) NOT NULL,
    action VARCHAR(200) NOT NULL,
    payload JSONB DEFAULT '{}',
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS policy_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    version VARCHAR(50) NOT NULL,
    metrics JSONB DEFAULT '{}',
    weights_path VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_task_nodes_goal_id ON task_nodes(goal_id);
CREATE INDEX idx_audit_events_goal_id ON audit_events(goal_id);
CREATE INDEX idx_audit_events_timestamp ON audit_events(timestamp);
"""
