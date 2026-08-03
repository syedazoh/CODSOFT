"""Mongo document shapes.

These are not an ODM — plain dicts are written to Mongo directly; these models
exist to document and validate the shape before insertion.
"""
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class DecisionLogDocument(BaseModel):
    simulation_run_id: str
    tick: int
    event_type: str
    data: Dict[str, Any]
    timestamp: datetime


class AgentSnapshotDocument(BaseModel):
    simulation_run_id: str
    agent_id: str
    state: Dict[str, Any]
    timestamp: datetime


class SimulationRunDocument(BaseModel):
    run_id: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    status: str  # "running" | "stopped" | "completed"
    tick_count: int = 0
    config: Dict[str, Any] = Field(default_factory=dict)
