"""Finance Agent Implementation"""
from typing import Any, Dict, Optional, TypedDict

from langgraph.graph import END, StateGraph

from ..core.llm import get_groq_llm
from .base_agent import BaseAgent
from .schemas import FinanceDecision

MAX_LLM_ATTEMPTS = 2
MAX_ARBITRATION_DEPTH = 1


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
            "If you cannot approve the full amount, consider offering a smaller "
            "counter_proposal (e.g. the amount actually available) instead of a flat denial. "
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
        budget_pool = state["budget_pool"]
        approved = amount <= budget_pool
        decision = FinanceDecision(
            approved=approved,
            reasoning="llm_fallback: deterministic rule applied",
            amount_approved=amount if approved else 0.0,
            counter_proposal=None if approved or budget_pool <= 0 else budget_pool,
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
        if event_type == "arbitration_result":
            return await self.handle_arbitration_result(event)
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

        requested_by = event.get("requested_by")
        depth = event.get("depth", 0)

        if requested_by and self.event_bus is not None:
            await self.event_bus.publish(
                "budget_negotiation",
                {
                    "finance_decision": decision.model_dump(),
                    "original_request": event,
                    "depth": depth,
                },
                source=self.agent_id,
            )
            if (
                not decision.approved
                and event.get("escalate_on_denial")
                and depth < MAX_ARBITRATION_DEPTH
            ):
                await self.event_bus.publish(
                    "arbitration_request",
                    {
                        "finance_position": decision.model_dump(),
                        "marketing_position": {
                            "department": event.get("department", "Unknown"),
                            "campaign_name": event.get("campaign_name"),
                            "requested_amount": event.get("amount", 0),
                            "reasoning": event.get("marketing_reasoning", ""),
                        },
                        "depth": depth,
                    },
                    source=self.agent_id,
                )

        return {
            "status": "approved" if decision.approved else "denied",
            "department": event.get("department", "Unknown"),
            "amount": event.get("amount", 0),
            "amount_approved": decision.amount_approved,
            "reasoning": decision.reasoning,
            "risk_notes": decision.risk_notes,
            "counter_proposal": decision.counter_proposal,
        }

    async def handle_arbitration_result(self, event: Dict[str, Any]) -> Dict[str, Any]:
        winner = event.get("winner")
        final_amount = event.get("final_amount", 0) or 0
        if winner != "finance" and final_amount > 0:
            self.budget_pool -= final_amount
        self.decision_count += 1
        return {"status": "arbitration_applied", "winner": winner, "final_amount": final_amount}

    async def get_status(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "budget_pool": self.budget_pool,
            "revenue": self.revenue,
            "expenses": self.expenses,
        }
