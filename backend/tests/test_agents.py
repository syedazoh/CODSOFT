"""Test Agent Implementations"""
import pytest
import pytest_asyncio
from app.agents import FinanceAgent

@pytest.mark.asyncio
class TestFinanceAgent:
    @pytest_asyncio.fixture
    async def finance_agent(self):
        return FinanceAgent()

    @pytest.mark.asyncio
    async def test_budget_request_approved(self, finance_agent):
        event = {"type": "budget_request", "amount": 1000, "department": "Marketing"}
        result = await finance_agent.process_event(event)
        assert result["status"] == "approved"