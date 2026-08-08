"""Test Simulation Mode (Phase 5), end-of-run summary (Phase 7), and polish (Phase 8)"""
import asyncio

import pytest

from app.agents.schemas import FinanceDecision, MarketingDecision, RunSummary
from app.orchestration.agent_manager import AgentManager
from app.simulation import SimulationConfig, SimulationEngine
from app.simulation.simulation_engine import REVENUE_AMOUNT


class FakeStructuredLLM:
    """Always returns the same canned decision, for deterministic simulation tests"""
    def __init__(self, response):
        self.response = response

    async def ainvoke(self, prompt):
        return self.response


class FakeMemoryStore:
    """Stands in for DecisionMemoryStore — real embeddings are CPU-bound enough to
    make timing-sensitive tests (pause/duration) flaky, and would otherwise write
    synthetic test data into the real chroma_data directory."""
    def query_similar(self, agent_id, query_text, k=3):
        return []

    def add_decision(self, **kwargs):
        pass


def _build_manager_with_fakes(monkeypatch) -> AgentManager:
    monkeypatch.setattr(
        "app.agents.finance_agent.get_decision_memory_store", lambda: FakeMemoryStore()
    )
    mgr = AgentManager()
    # Finance always approves so campaigns never escalate to a real (unmocked) CEO LLM call.
    mgr.agents["finance"]._structured_llm = FakeStructuredLLM(
        FinanceDecision(approved=True, reasoning="Simulated approval", amount_approved=100.0)
    )
    mgr.agents["marketing"]._structured_llm = FakeStructuredLLM(
        MarketingDecision(campaign_name="Sim Campaign", desired_budget=100.0, reasoning="Simulated ask")
    )
    mgr.agents["ceo"]._summary_llm = FakeStructuredLLM(
        RunSummary(
            headline="Simulated run summary",
            key_decisions=["Approved a campaign"],
            risks=[],
            recommendation="Keep simulating",
        )
    )
    return mgr


@pytest.mark.asyncio
class TestSimulationEngine:
    async def test_run_produces_expected_number_of_ticks(self, monkeypatch):
        engine = SimulationEngine(_build_manager_with_fakes(monkeypatch))
        await engine.run(SimulationConfig(ticks=10, min_interval=0, max_interval=0))

        assert engine.tick_count == 10
        assert len(engine.decision_log) == 10

    async def test_on_decision_hook_is_called_each_tick(self, monkeypatch):
        received = []
        engine = SimulationEngine(_build_manager_with_fakes(monkeypatch), on_decision=received.append)
        await engine.run(SimulationConfig(ticks=5, min_interval=0, max_interval=0))

        assert len(received) == 5

    async def test_stop_halts_a_running_simulation(self, monkeypatch):
        engine = SimulationEngine(_build_manager_with_fakes(monkeypatch))
        engine.start(SimulationConfig(ticks=None, min_interval=0, max_interval=0))
        await engine.stop()

        assert engine.is_running is False

    async def test_on_complete_hook_receives_run_summary(self, monkeypatch):
        received = []
        engine = SimulationEngine(_build_manager_with_fakes(monkeypatch), on_complete=received.append)
        await engine.run(SimulationConfig(ticks=3, min_interval=0, max_interval=0))

        assert len(received) == 1
        assert received[0].headline == "Simulated run summary"

    async def test_duration_seconds_stops_the_run(self, monkeypatch):
        engine = SimulationEngine(_build_manager_with_fakes(monkeypatch))
        await engine.run(
            SimulationConfig(ticks=None, duration_seconds=0.2, min_interval=0, max_interval=0.05)
        )

        assert engine.tick_count > 0
        assert engine.is_running is False

    async def test_revenue_injected_periodically(self, monkeypatch):
        mgr = _build_manager_with_fakes(monkeypatch)
        finance = mgr.agents["finance"]
        starting_revenue = finance.revenue
        starting_budget = finance.budget_pool

        engine = SimulationEngine(mgr)
        # REVENUE_TICK_INTERVAL is 5; six ticks guarantees exactly one injection.
        await engine.run(SimulationConfig(ticks=6, min_interval=0, max_interval=0))

        assert finance.revenue == starting_revenue + REVENUE_AMOUNT
        assert finance.budget_pool >= starting_budget + REVENUE_AMOUNT - 600  # minus up to 6 approved requests

    async def test_pause_halts_progress_until_resumed(self, monkeypatch):
        # pause() can only stop the *next* tick from starting — a tick already past
        # the resume-event gate finishes regardless — so allow one in-flight tick
        # before asserting the loop is actually held.
        engine = SimulationEngine(_build_manager_with_fakes(monkeypatch))
        engine.start(SimulationConfig(ticks=None, min_interval=0, max_interval=0))
        await asyncio.sleep(0.05)

        engine.pause()
        assert engine.is_paused is True
        tick_count_at_pause = engine.tick_count
        await asyncio.sleep(0.05)
        tick_count_settled = engine.tick_count
        assert tick_count_settled - tick_count_at_pause <= 1

        await asyncio.sleep(0.1)
        assert engine.tick_count == tick_count_settled

        engine.resume()
        assert engine.is_paused is False
        await asyncio.sleep(0.05)
        assert engine.tick_count > tick_count_settled

        await engine.stop()
