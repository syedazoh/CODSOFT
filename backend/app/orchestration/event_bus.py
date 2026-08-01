"""Event Bus for Agent Communication"""
from datetime import datetime
from typing import Any, Callable, Dict, List
from uuid import uuid4

class Event:
    def __init__(self, event_type: str, data: Dict[str, Any], source: str = "system"):
        self.event_id = str(uuid4())
        self.event_type = event_type
        self.data = data
        self.source = source
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "data": self.data,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
        }

class EventBus:
    """Central event bus for agent communication"""
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.event_history: List[Event] = []
        self.max_history_size = 1000

    def subscribe(self, event_type: str, callback: Callable) -> None:
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    async def publish(self, event_type: str, data: Dict[str, Any], source: str = "system") -> Event:
        event = Event(event_type, data, source)
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                await callback(event)
        self.event_history.append(event)
        if len(self.event_history) > self.max_history_size:
            self.event_history.pop(0)
        return event

    def get_event_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        return [event.to_dict() for event in self.event_history[-limit:]]