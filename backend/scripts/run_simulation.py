"""Standalone Simulation Mode runner — no FastAPI/Mongo dependency.

Usage (from the backend/ directory, with the venv active):
    python scripts/run_simulation.py --ticks 20 --interval 0.5
    python scripts/run_simulation.py --duration 60 --min-interval 0.2 --max-interval 1.5
"""
import argparse
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.orchestration.agent_manager import AgentManager  # noqa: E402
from app.simulation import SimulationConfig, SimulationEngine  # noqa: E402


async def main(config: SimulationConfig, output_path: str) -> None:
    agent_manager = AgentManager()
    engine = SimulationEngine(agent_manager)
    await engine.run(config=config)

    with open(output_path, "w") as f:
        json.dump(engine.decision_log, f, indent=2)

    print(f"Ran {engine.tick_count} ticks. Decision log written to {output_path}")
    print(f"Event bus history has {len(agent_manager.event_bus.event_history)} entries.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a Simulation Mode session")
    parser.add_argument("--ticks", type=int, default=20, help="Stop after this many ticks (default 20)")
    parser.add_argument("--duration", type=float, default=None, help="Stop after this many seconds")
    parser.add_argument("--interval", type=float, default=None, help="Fixed interval between ticks (overrides min/max)")
    parser.add_argument("--min-interval", type=float, default=0.5)
    parser.add_argument("--max-interval", type=float, default=2.0)
    parser.add_argument("--output", type=str, default="simulation_log.json")
    args = parser.parse_args()

    min_interval = args.interval if args.interval is not None else args.min_interval
    max_interval = args.interval if args.interval is not None else args.max_interval

    simulation_config = SimulationConfig(
        ticks=args.ticks,
        duration_seconds=args.duration,
        min_interval=min_interval,
        max_interval=max_interval,
    )

    asyncio.run(main(simulation_config, args.output))
