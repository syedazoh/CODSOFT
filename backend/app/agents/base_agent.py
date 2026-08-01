"""Base Agent Class"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional

class BaseAgent(ABC):
    """Base class for all agents"""
    def __init__(self, agent_id: str, agent_name: str, description: str):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.description = description
        self.created_at = datetime.now()
        self.decision_count = 0

    @abstractmethod
    async def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        pass

    def __repr__(self) -> str:
        return f"{self.agent_name}(id={self.agent_id})"