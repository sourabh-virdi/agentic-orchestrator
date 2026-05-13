"""Core data models for the orchestrator."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class GoalStatus(str, enum.Enum):
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class AgentType(str, enum.Enum):
    PLANNER = "planner"
    RETRIEVER = "retriever"
    EXECUTOR = "executor"
    VERIFIER = "verifier"


class GoalConstraints(BaseModel):
    budget_usd: float | None = None
    deadline: str | None = None
    channels: list[str] = Field(default_factory=list)
    audience: str | None = None
    extra: dict = Field(default_factory=dict)


class GoalCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1, max_length=5000)
    constraints: GoalConstraints = Field(default_factory=GoalConstraints)


class Goal(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    title: str
    description: str
    constraints: GoalConstraints = Field(default_factory=GoalConstraints)
    status: GoalStatus = GoalStatus.PENDING
    task_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}


class TaskNode(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    goal_id: uuid.UUID
    name: str
    agent_type: AgentType
    params: dict = Field(default_factory=dict)
    dependencies: list[uuid.UUID] = Field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: dict | None = None
    retries: int = 0
    max_retries: int = 3
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class AuditEvent(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    goal_id: uuid.UUID
    task_id: uuid.UUID | None = None
    agent: str
    action: str
    payload: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class GoalResponse(BaseModel):
    id: uuid.UUID
    status: GoalStatus
    task_count: int
    created_at: datetime


class TaskResponse(BaseModel):
    id: uuid.UUID
    name: str
    agent_type: AgentType
    status: TaskStatus
    dependencies: list[uuid.UUID]
    result: dict | None = None
    retries: int
    created_at: datetime
    completed_at: datetime | None = None


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    services: dict = Field(default_factory=dict)


class SimulateRequest(BaseModel):
    goal: GoalCreate
    seed: int = 42
    failure_rate: float = 0.1
