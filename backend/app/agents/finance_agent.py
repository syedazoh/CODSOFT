"""Finance Agent Implementation"""
from typing import Any, Dict
from .base_agent import BaseAgent

class FinanceAgent(BaseAgent):
    """Finance Agent for budgeting and financial analysis"""
    def __init__(self):
        super().__init__(
            agent_id="finance_001",
            agent_name="Finance Manager",
            description="Manages budgets, forecasts revenue, tracks expenses",
        )
        self.budget_pool = 100000.0
        self.revenue = 0.0
        self.expenses = 0.0

    async def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        event_type = event.get("type")
        if event_type == "budget_request":
            return await self.handle_budget_request(event)
        return {"status": "unknown_event"}

    async def handle_budget_request(self, event: Dict[str, Any]) -> Dict[str, Any]:
        amount = event.get("amount", 0)
        department = event.get("department", "Unknown")
        if amount <= self.budget_pool:
            self.budget_pool -= amount
            return {"status": "approved", "department": department, "amount": amount}
        return {"status": "denied", "reason": "insufficient_funds"}

    async def get_status(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "budget_pool": self.budget_pool,
            "revenue": self.revenue,
            "expenses": self.expenses,
        }