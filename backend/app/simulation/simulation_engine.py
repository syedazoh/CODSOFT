"""Autonomous tick loop that feeds synthetic events through the AgentManager"""
import asyncio
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from ..orchestration.agent_manager import AgentManager
from .event_generator import generate_event


def _noop_on_decision(record: Dict[str, Any]) -> None:
    pass


def _noop_on_complete(summary: Any) -> None:
    pass


class SimulationEngine:
    """Runs ticks against a shared AgentManager without any human clicking each step.

    `on_decision` and `on_complete` are seams for later phases (e.g. persisting each
    tick, and the final run summary, to Mongo) without this class needing to know
    about storage.
    """

    def __init__(
        self,
        agent_manager: AgentManager,
        on_decision: Callable[[Dict[str, Any]], Any] = _noop_on_decision,
        on_complete: Callable[[Any], Any] = _noop_on_complete,
    ):
        self.agent_manager = agent_manager
        self.on_decision = on_decision
        self.on_complete = on_complete
        self.tick_count = 0
        self.is_running = False
        self.decision_log: List[Dict[str, Any]] = []
        self._task: Optional[asyncio.Task] = None

    async def _tick(self) -> None:
        event_type, data = generate_event()
        await self.agent_manager.process_event(event_type, data, source="simulation")

        self.tick_count += 1
        record = {
            "tick": self.tick_count,
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }
        self.decision_log.append(record)

        result = self.on_decision(record)
        if asyncio.iscoroutine(result):
            await result

    async def run(self, ticks: Optional[int] = None, interval_seconds: float = 1.0) -> None:
        self.is_running = True
        try:
            while self.is_running:
                if ticks is not None and self.tick_count >= ticks:
                    break
                await self._tick()
                if self.is_running:
                    await asyncio.sleep(interval_seconds)
        finally:
            self.is_running = False
            await self._complete()

    async def _complete(self) -> None:
        ceo = self.agent_manager.agents.get("ceo")
        if ceo is None or not hasattr(ceo, "summarize_run"):
            return
        summary = await ceo.summarize_run(self.decision_log)
        result = self.on_complete(summary)
        if asyncio.iscoroutine(result):
            await result

    def start(self, ticks: Optional[int] = None, interval_seconds: float = 1.0) -> None:
        if self._task is not None and not self._task.done():
            return
        self._task = asyncio.create_task(self.run(ticks=ticks, interval_seconds=interval_seconds))

    async def stop(self) -> None:
        # Cancel outright rather than relying only on the is_running flag: if the
        # task hasn't started executing yet, run()'s own `self.is_running = True`
        # would otherwise stomp a stop() that raced ahead of it.
        self.is_running = False
        if self._task is not None and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None

    def status(self) -> Dict[str, Any]:
        return {
            "is_running": self.is_running,
            "tick_count": self.tick_count,
            "decision_log_size": len(self.decision_log),
        }
