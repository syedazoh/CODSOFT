"""API-facing request/response schemas"""
from typing import Optional

from pydantic import BaseModel


class SimulationStartRequest(BaseModel):
    ticks: Optional[int] = None
    interval_seconds: float = 1.0


class SimulationStatusOut(BaseModel):
    is_running: bool
    tick_count: int
    decision_log_size: int
    run_id: Optional[str] = None
