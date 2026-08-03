"""CEO Agent - arbitrates cross-department budget conflicts"""
from typing import Any, Dict

from ..core.llm import get_groq_llm
from .base_agent import BaseAgent
from .schemas import ArbitrationDecision


class CEOAgent(BaseAgent):
    """CEO Agent for arbitrating disputes between department agents"""

    def __init__(self):
        super().__init__(
            agent_id="ceo_001",
            agent_name="CEO",
            description="Arbitrates cross-department conflicts and sets strategic direction",
        )
        self._structured_llm = get_groq_llm().with_structured_output(ArbitrationDecision)

    async def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        if event.get("type") == "arbitration_request":
            return await self.handle_arbitration_request(event)
        return {"status": "unknown_event"}

    async def handle_arbitration_request(self, event: Dict[str, Any]) -> Dict[str, Any]:
        finance_position = event.get("finance_position", {})
        marketing_position = event.get("marketing_position", {})
        depth = event.get("depth", 0)

        prompt = (
            "You are the CEO of a startup, arbitrating a budget disagreement between "
            "the Finance and Marketing departments.\n"
            f"Marketing's position: requested ${marketing_position.get('requested_amount', 0):.2f} "
            f"for campaign '{marketing_position.get('campaign_name', 'unknown')}'. "
            f"Marketing's reasoning: {marketing_position.get('reasoning', 'n/a')}\n"
            f"Finance's position: approved={finance_position.get('approved')}, "
            f"counter_proposal=${(finance_position.get('counter_proposal') or 0):.2f}, "
            f"reasoning: {finance_position.get('reasoning', 'n/a')}\n"
            "Decide who prevails: 'finance' (the denial stands, final_amount=0), "
            "'marketing' (grant the full requested amount), or 'compromise' (grant an amount "
            "between Finance's counter-proposal and Marketing's request). "
            "Reference both positions in your rationale."
        )

        try:
            decision = await self._structured_llm.ainvoke(prompt)
        except Exception:
            counter = marketing_position.get("requested_amount", 0)
            fallback_amount = finance_position.get("counter_proposal") or 0
            decision = ArbitrationDecision(
                winner="compromise" if fallback_amount else "finance",
                final_amount=fallback_amount,
                rationale="llm_fallback: sided with Finance's counter-proposal (or denial) deterministically",
            )

        self.decision_count += 1

        if self.event_bus is not None:
            await self.event_bus.publish(
                "arbitration_result",
                {
                    "winner": decision.winner,
                    "final_amount": decision.final_amount,
                    "rationale": decision.rationale,
                    "department": marketing_position.get("department", "Marketing"),
                    "campaign_name": marketing_position.get("campaign_name"),
                    "depth": depth + 1,
                },
                source="ceo_agent",
            )

        return {
            "status": "arbitrated",
            "winner": decision.winner,
            "final_amount": decision.final_amount,
            "rationale": decision.rationale,
        }

    async def get_status(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "decision_count": self.decision_count,
        }
