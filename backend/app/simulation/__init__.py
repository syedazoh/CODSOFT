"""Simulation Mode — autonomous synthetic event generation and tick loop"""
from .config import SimulationConfig
from .simulation_engine import SimulationEngine

__all__ = ["SimulationEngine", "SimulationConfig"]
