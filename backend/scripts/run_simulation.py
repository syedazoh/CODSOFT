"""Standalone Simulation Mode runner — no FastAPI/Mongo dependency.

Usage (from the backend/ directory, with the venv active):
    python scripts/run_simulation.py --ticks 20 --interval 0.5
"""
import argparse
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.orchestration.agent_manager import AgentManager  # noqa: E402
from app.simulation.simulation_engine import SimulationEngine  # noqa: E402


async def main(ticks: int, interval: float, output_path: str) -> None:
    agent_manager = AgentManager()
    engine = SimulationEngine(agent_manager)
    await engine.run(ticks=ticks, interval_seconds=interval)

    with open(output_path, "w") as f:
        json.dump(engine.decision_log, f, indent=2)

    print(f"Ran {engine.tick_count} ticks. Decision log written to {output_path}")
    print(f"Event bus history has {len(agent_manager.event_bus.event_history)} entries.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a crude Simulation Mode session")
    parser.add_argument("--ticks", type=int, default=20)
    parser.add_argument("--interval", type=float, default=0.5)
    parser.add_argument("--output", type=str, default="simulation_log.json")
    args = parser.parse_args()

    asyncio.run(main(args.ticks, args.interval, args.output))
