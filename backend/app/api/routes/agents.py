"""Agent status routes"""
from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("")
async def list_agents(request: Request):
    agent_manager = request.app.state.agent_manager
    return await agent_manager.get_all_agents_status()


@router.get("/{agent_key}")
async def get_agent(agent_key: str, request: Request):
    agent_manager = request.app.state.agent_manager
    agent = agent_manager.agents.get(agent_key)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_key}")
    return await agent.get_status()


@router.get("/{agent_key}/history")
async def get_agent_history(agent_key: str, request: Request, limit: int = 50):
    agent_manager = request.app.state.agent_manager
    agent = agent_manager.agents.get(agent_key)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_key}")

    db = request.app.state.db
    cursor = (
        db["agent_snapshots"]
        .find({"agent_id": agent.agent_id})
        .sort("timestamp", -1)
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)
    for doc in docs:
        doc["_id"] = str(doc["_id"])
    return docs
