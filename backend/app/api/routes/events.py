"""Event routes"""
from typing import Any, Dict

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(prefix="/api/events", tags=["events"])


class PublishEventRequest(BaseModel):
    event_type: str
    data: Dict[str, Any] = {}
    source: str = "api"


@router.get("")
async def list_events(request: Request, limit: int = 100):
    agent_manager = request.app.state.agent_manager
    return agent_manager.event_bus.get_event_history(limit=limit)


@router.post("")
async def publish_event(payload: PublishEventRequest, request: Request):
    agent_manager = request.app.state.agent_manager
    await agent_manager.process_event(payload.event_type, payload.data, source=payload.source)
    return {"status": "published", "event_type": payload.event_type}
