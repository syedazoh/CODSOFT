"""Main FastAPI Application"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import agents as agents_routes
from .api.routes import events as events_routes
from .api.routes import simulation as simulation_routes
from .database.mongodb import close_mongo_connection, connect_to_mongo, get_database, ping_mongo
from .orchestration.agent_manager import AgentManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    app.state.db = get_database()
    app.state.agent_manager = AgentManager()
    app.state.simulation_engine = None
    app.state.current_run_id = None
    yield
    await close_mongo_connection()


app = FastAPI(
    title="Startup Simulator API",
    description="Multi-Agent AI-powered Business Simulation Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents_routes.router)
app.include_router(events_routes.router)
app.include_router(simulation_routes.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to Startup Simulator API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    mongo_ok = await ping_mongo()
    return {
        "status": "healthy",
        "service": "startup-simulator-backend",
        "mongo": "connected" if mongo_ok else "unavailable",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
