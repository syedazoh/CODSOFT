"""Agent Manager for Orchestrating Multiple Agents"""
from typing import Any, Dict

from ..agents import CEOAgent, FinanceAgent, HRAgent, MarketingAgent, OperationsAgent
from .event_bus import EventBus

class AgentManager:
    """Manages all agents and their interactions"""
    def __init__(self):
        self.event_bus = EventBus()
        self.agents: Dict[str, Any] = {}
        self.initialize_agents()

    def initialize_agents(self) -> None:
        finance_agent = FinanceAgent()
        marketing_agent = MarketingAgent()
        hr_agent = HRAgent()
        operations_agent = OperationsAgent()
        ceo_agent = CEOAgent()
        self.agents = {
            "finance": finance_agent,
            "marketing": marketing_agent,
            "hr": hr_agent,
            "operations": operations_agent,
            "ceo": ceo_agent,
        }

        for agent in self.agents.values():
            agent.set_event_bus(self.event_bus)

        self.event_bus.subscribe("budget_request", finance_agent.process_event)
        self.event_bus.subscribe("campaign_launch", marketing_agent.process_event)
        self.event_bus.subscribe("recruitment_request", hr_agent.process_event)
        self.event_bus.subscribe("resource_request", operations_agent.process_event)

        # Negotiation / arbitration wiring (Phase 3)
        self.event_bus.subscribe("budget_negotiation", marketing_agent.process_event)
        self.event_bus.subscribe("arbitration_request", ceo_agent.process_event)
        self.event_bus.subscribe("arbitration_result", finance_agent.process_event)
        self.event_bus.subscribe("arbitration_result", marketing_agent.process_event)

    async def process_event(self, event_type: str, data: Dict[str, Any], source: str = "user") -> None:
        await self.event_bus.publish(event_type, data, source)

    async def get_all_agents_status(self) -> Dict[str, Any]:
        status = {}
        for agent_name, agent in self.agents.items():
            status[agent_name] = await agent.get_status()
        return status
