"""Test the FastAPI routes with a mocked Mongo (Phase 6)"""
import pytest
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient

import app.database.mongodb as mongodb_module
from app.main import app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(mongodb_module, "AsyncIOMotorClient", lambda *a, **kw: AsyncMongoMockClient())
    with TestClient(app) as test_client:
        yield test_client


class TestHealthAndRoot:
    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_health_reports_mongo_connected(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["mongo"] == "connected"


class TestAgentRoutes:
    def test_list_agents(self, client):
        response = client.get("/api/agents")
        assert response.status_code == 200
        body = response.json()
        assert set(body.keys()) == {"finance", "marketing", "hr", "operations", "ceo"}

    def test_get_single_agent(self, client):
        response = client.get("/api/agents/finance")
        assert response.status_code == 200
        assert response.json()["agent_id"] == "finance_001"

    def test_get_unknown_agent_404s(self, client):
        response = client.get("/api/agents/does-not-exist")
        assert response.status_code == 404


class TestEventRoutes:
    def test_list_events_starts_empty(self, client):
        response = client.get("/api/events")
        assert response.status_code == 200
        assert response.json() == []

    def test_publish_recruitment_event(self, client):
        response = client.post(
            "/api/events",
            json={"event_type": "recruitment_request", "data": {"role": "Engineer"}, "source": "test"},
        )
        assert response.status_code == 200

        history = client.get("/api/events").json()
        assert len(history) == 1
        assert history[0]["event_type"] == "recruitment_request"


class TestSimulationRoutes:
    def test_status_before_any_run(self, client):
        response = client.get("/api/simulation/status")
        assert response.status_code == 200
        body = response.json()
        assert body["is_running"] is False
        assert body["run_id"] is None

    def test_stop_without_running_simulation_conflicts(self, client):
        response = client.post("/api/simulation/stop")
        assert response.status_code == 409
