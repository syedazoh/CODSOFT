"""Finance Agent Implementation"""
from typing import Any, Dict, Optional, TypedDict

from langgraph.graph import END, StateGraph

from ..core.llm import get_groq_llm
from .base_agent import BaseAgent
from .schemas import FinanceDecision

MAX_LLM_ATTEMPTS = 2


class FinanceGraphState(TypedDict):
    event: Dict[str, Any]
    budget_pool: float
    attempt: int
    decision: Optional[FinanceDecision]


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
        self._structured_llm = get_groq_llm().with_structured_output(FinanceDecision)
        self._graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(FinanceGraphState)
        graph.add_node("call_llm", self._call_llm)
        graph.add_node("fallback_decision", self._fallback_decision)
        graph.add_node("apply_decision", self._apply_decision)

        graph.set_entry_point("call_llm")
        graph.add_conditional_edges(
            "call_llm",
            self._route_after_llm,
            {"retry": "call_llm", "fallback": "fallback_decision", "apply": "apply_decision"},
        )
        graph.add_edge("fallback_decision", "apply_decision")
        graph.add_edge("apply_decision", END)
        return graph.compile()

    def _route_after_llm(self, state: FinanceGraphState) -> str:
        if state.get("decision") is not None:
            return "apply"
        if state["attempt"] < MAX_LLM_ATTEMPTS:
            return "retry"
        return "fallback"

    async def _call_llm(self, state: FinanceGraphState) -> FinanceGraphState:
        event = state["event"]
        amount = event.get("amount", 0)
        department = event.get("department", "Unknown")
        attempt = state.get("attempt", 0) + 1

        prompt = (
            "You are the Finance Manager of a startup. Decide whether to approve this "
            "budget request.\n"
            f"Current available budget pool: ${state['budget_pool']:.2f}\n"
            f"Requesting department: {department}\n"
            f"Requested amount: ${amount:.2f}\n"
            "Approve only if the amount does not exceed the available budget pool. "
            "Give a brief, concrete reasoning for your decision."
        )
        try:
            decision = await self._structured_llm.ainvoke(prompt)
        except Exception:
            decision = None

        return {**state, "attempt": attempt, "decision": decision}

    async def _fallback_decision(self, state: FinanceGraphState) -> FinanceGraphState:
        event = state["event"]
        amount = event.get("amount", 0)
        approved = amount <= state["budget_pool"]
        decision = FinanceDecision(
            approved=approved,
            reasoning="llm_fallback: deterministic rule applied",
            amount_approved=amount if approved else 0.0,
        )
        return {**state, "decision": decision}

    async def _apply_decision(self, state: FinanceGraphState) -> FinanceGraphState:
        decision: FinanceDecision = state["decision"]
        if decision.approved:
            self.budget_pool -= decision.amount_approved
        self.decision_count += 1
        return state

    async def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        event_type = event.get("type")
        if event_type == "budget_request":
            return await self.handle_budget_request(event)
        return {"status": "unknown_event"}

    async def handle_budget_request(self, event: Dict[str, Any]) -> Dict[str, Any]:
        initial_state: FinanceGraphState = {
            "event": event,
            "budget_pool": self.budget_pool,
            "attempt": 0,
            "decision": None,
        }
        final_state = await self._graph.ainvoke(initial_state)
        decision: FinanceDecision = final_state["decision"]
        return {
            "status": "approved" if decision.approved else "denied",
            "department": event.get("department", "Unknown"),
            "amount": event.get("amount", 0),
            "amount_approved": decision.amount_approved,
            "reasoning": decision.reasoning,
            "risk_notes": decision.risk_notes,
        }

    async def get_status(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "budget_pool": self.budget_pool,
            "revenue": self.revenue,
            "expenses": self.expenses,
        }
