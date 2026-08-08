"""Simulation control routes"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from ...models.schemas import SimulationStatusOut
from ...simulation import SimulationConfig, SimulationEngine

router = APIRouter(prefix="/api/simulation", tags=["simulation"])


@router.post("/start")
async def start_simulation(payload: SimulationConfig, request: Request):
    app_state = request.app.state
    existing: Optional[SimulationEngine] = getattr(app_state, "simulation_engine", None)
    if existing is not None and existing.is_running:
        raise HTTPException(status_code=409, detail="Simulation already running")

    run_id = str(uuid.uuid4())
    db = app_state.db
    started_at = datetime.now(timezone.utc)

    await db["simulation_runs"].insert_one({
        "run_id": run_id,
        "started_at": started_at,
        "ended_at": None,
        "status": "running",
        "tick_count": 0,
        "config": payload.model_dump(),
    })

    async def on_decision(record):
        await db["decision_logs"].insert_one({**record, "simulation_run_id": run_id})
        await db["simulation_runs"].update_one(
            {"run_id": run_id}, {"$set": {"tick_count": record["tick"]}}
        )
        statuses = await app_state.agent_manager.get_all_agents_status()
        now = datetime.now(timezone.utc)
        snapshots = [
            {
                "agent_id": status.get("agent_id", key),
                "state": status,
                "timestamp": now,
                "simulation_run_id": run_id,
            }
            for key, status in statuses.items()
        ]
        if snapshots:
            await db["agent_snapshots"].insert_many(snapshots)

    async def on_complete(summary):
        now = datetime.now(timezone.utc)
        await db["run_summaries"].insert_one({
            "run_id": run_id,
            "headline": summary.headline,
            "key_decisions": summary.key_decisions,
            "risks": summary.risks,
            "recommendation": summary.recommendation,
            "created_at": now,
        })
        # Marks the run "completed" whenever run() ends for any reason (tick limit
        # reached, or stop() cancelling it); stop_simulation() below overwrites this
        # with "stopped" for the user-initiated case, so the final status still
        # distinguishes "ran to completion" from "stopped early".
        await db["simulation_runs"].update_one(
            {"run_id": run_id}, {"$set": {"status": "completed", "ended_at": now}}
        )

    engine = SimulationEngine(app_state.agent_manager, on_decision=on_decision, on_complete=on_complete)
    app_state.simulation_engine = engine
    app_state.current_run_id = run_id
    engine.start(config=payload)

    return {"status": "started", "run_id": run_id}


@router.post("/stop")
async def stop_simulation(request: Request):
    app_state = request.app.state
    engine: Optional[SimulationEngine] = getattr(app_state, "simulation_engine", None)
    if engine is None or not engine.is_running:
        raise HTTPException(status_code=409, detail="No simulation is running")

    await engine.stop()

    db = app_state.db
    await db["simulation_runs"].update_one(
        {"run_id": app_state.current_run_id},
        {"$set": {"status": "stopped", "ended_at": datetime.now(timezone.utc)}},
    )
    return {"status": "stopped", "run_id": app_state.current_run_id}


@router.post("/pause")
async def pause_simulation(request: Request):
    app_state = request.app.state
    engine: Optional[SimulationEngine] = getattr(app_state, "simulation_engine", None)
    if engine is None or not engine.is_running:
        raise HTTPException(status_code=409, detail="No simulation is running")
    engine.pause()
    return {"status": "paused"}


@router.post("/resume")
async def resume_simulation(request: Request):
    app_state = request.app.state
    engine: Optional[SimulationEngine] = getattr(app_state, "simulation_engine", None)
    if engine is None or not engine.is_running:
        raise HTTPException(status_code=409, detail="No simulation is running")
    engine.resume()
    return {"status": "resumed"}


@router.get("/status", response_model=SimulationStatusOut)
async def simulation_status(request: Request):
    app_state = request.app.state
    engine: Optional[SimulationEngine] = getattr(app_state, "simulation_engine", None)
    if engine is None:
        return SimulationStatusOut(is_running=False, tick_count=0, decision_log_size=0, run_id=None)
    status = engine.status()
    return SimulationStatusOut(**status, run_id=getattr(app_state, "current_run_id", None))


@router.get("/runs/{run_id}/log")
async def get_run_log(run_id: str, request: Request, limit: int = 500):
    db = request.app.state.db
    cursor = db["decision_logs"].find({"simulation_run_id": run_id}).sort("tick", 1).limit(limit)
    docs = await cursor.to_list(length=limit)
    for doc in docs:
        doc["_id"] = str(doc["_id"])
    return docs
