"""Test crude Simulation Mode (Phase 5) and end-of-run summary (Phase 7)"""
import pytest

from app.agents.schemas import FinanceDecision, MarketingDecision, RunSummary
from app.orchestration.agent_manager import AgentManager
from app.simulation.simulation_engine import SimulationEngine


class FakeStructuredLLM:
    """Always returns the same canned decision, for deterministic simulation tests"""
    def __init__(self, response):
        self.response = response

    async def ainvoke(self, prompt):
        return self.response


def _build_manager_with_fakes() -> AgentManager:
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
    async def test_run_produces_expected_number_of_ticks(self):
        engine = SimulationEngine(_build_manager_with_fakes())
        await engine.run(ticks=10, interval_seconds=0)

        assert engine.tick_count == 10
        assert len(engine.decision_log) == 10

    async def test_on_decision_hook_is_called_each_tick(self):
        received = []
        engine = SimulationEngine(_build_manager_with_fakes(), on_decision=received.append)
        await engine.run(ticks=5, interval_seconds=0)

        assert len(received) == 5

    async def test_stop_halts_a_running_simulation(self):
        engine = SimulationEngine(_build_manager_with_fakes())
        engine.start(ticks=None, interval_seconds=0)
        await engine.stop()

        assert engine.is_running is False

    async def test_on_complete_hook_receives_run_summary(self):
        received = []
        engine = SimulationEngine(_build_manager_with_fakes(), on_complete=received.append)
        await engine.run(ticks=3, interval_seconds=0)

        assert len(received) == 1
        assert received[0].headline == "Simulated run summary"
