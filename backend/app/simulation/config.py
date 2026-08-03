"""Simulation Mode configuration"""
from typing import Dict, Optional

from pydantic import BaseModel, Field

from .event_generator import EVENT_WEIGHTS


class SimulationConfig(BaseModel):
    ticks: Optional[int] = None
    duration_seconds: Optional[float] = None
    min_interval: float = Field(default=0.5, ge=0)
    max_interval: float = Field(default=2.0, ge=0)
    event_weights: Optional[Dict[str, float]] = None

    def resolved_weights(self) -> Dict[str, float]:
        if not self.event_weights:
            return dict(EVENT_WEIGHTS)
        # Fall back to the default weight for any event type the caller omitted,
        # so a partial override doesn't silently zero out the others.
        return {**EVENT_WEIGHTS, **self.event_weights}
