"""Test Agent Implementations"""
import pytest
import pytest_asyncio
from app.agents import FinanceAgent
from app.agents.schemas import FinanceDecision


class FakeStructuredLLM:
    """Stand-in for ChatGroq.with_structured_output(...) in tests"""
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    async def ainvoke(self, prompt):
        response = self.responses[min(self.calls, len(self.responses) - 1)]
        self.calls += 1
        if isinstance(response, Exception):
            raise response
        return response


@pytest.mark.asyncio
class TestFinanceAgent:
    @pytest_asyncio.fixture
    async def finance_agent(self):
        return FinanceAgent()

    async def test_budget_request_approved(self, finance_agent):
        finance_agent._structured_llm = FakeStructuredLLM([
            FinanceDecision(approved=True, reasoning="Sufficient funds available", amount_approved=1000)
        ])
        event = {"type": "budget_request", "amount": 1000, "department": "Marketing"}
        result = await finance_agent.process_event(event)
        assert result["status"] == "approved"
        assert finance_agent.budget_pool == 99000.0

    async def test_budget_request_denied(self, finance_agent):
        finance_agent._structured_llm = FakeStructuredLLM([
            FinanceDecision(approved=False, reasoning="Amount exceeds available budget", amount_approved=0.0)
        ])
        event = {"type": "budget_request", "amount": 500000, "department": "Marketing"}
        result = await finance_agent.process_event(event)
        assert result["status"] == "denied"
        assert finance_agent.budget_pool == 100000.0

    async def test_budget_request_retries_on_bad_output(self, finance_agent):
        good_decision = FinanceDecision(approved=True, reasoning="Approved after retry", amount_approved=200)
        fake = FakeStructuredLLM([ValueError("malformed tool call"), good_decision])
        finance_agent._structured_llm = fake
        event = {"type": "budget_request", "amount": 200, "department": "Operations"}
        result = await finance_agent.process_event(event)
        assert fake.calls == 2
        assert result["reasoning"] == "Approved after retry"

    async def test_budget_request_falls_back_after_exhausting_retries(self, finance_agent):
        fake = FakeStructuredLLM([ValueError("bad json"), ValueError("bad json again")])
        finance_agent._structured_llm = fake
        event = {"type": "budget_request", "amount": 500, "department": "HR"}
        result = await finance_agent.process_event(event)
        assert fake.calls == 2
        assert "llm_fallback" in result["reasoning"]
        assert result["status"] == "approved"
