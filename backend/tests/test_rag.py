"""Test RAG decision memory (Phase 4)"""
import shutil
import tempfile

import pytest

from app.config import settings
from app.rag.store import DecisionMemoryStore


@pytest.fixture
def memory_store(monkeypatch):
    tmp_dir = tempfile.mkdtemp()
    monkeypatch.setattr(settings, "chroma_persist_dir", tmp_dir)
    store = DecisionMemoryStore()
    yield store
    shutil.rmtree(tmp_dir, ignore_errors=True)


class TestDecisionMemoryStore:
    def test_query_similar_on_empty_store_returns_empty(self, memory_store):
        results = memory_store.query_similar("finance_001", "Budget request from Marketing for $1000", k=3)
        assert results == []

    def test_query_similar_returns_nearest_precedent(self, memory_store):
        memory_store.add_decision(
            agent_id="finance_001",
            event_type="budget_request",
            summary_text="Budget request from Marketing for $1000.00: approved (amount_approved=$1000.00). Reasoning: within budget",
            metadata={"department": "Marketing", "amount": 1000, "approved": True, "amount_approved": 1000.0},
        )
        memory_store.add_decision(
            agent_id="finance_001",
            event_type="budget_request",
            summary_text="Recruitment request from HR for 3 engineers: approved. Reasoning: growth phase justified hiring",
            metadata={"department": "HR", "amount": 0, "approved": True, "amount_approved": 0.0},
        )

        results = memory_store.query_similar("finance_001", "Budget request from Marketing for $1050.00", k=1)

        assert len(results) == 1
        assert "Marketing" in results[0]["document"]
        assert results[0]["metadata"]["department"] == "Marketing"

    def test_query_similar_filters_by_agent_id(self, memory_store):
        memory_store.add_decision(
            agent_id="finance_001",
            event_type="budget_request",
            summary_text="Budget request from Marketing for $1000.00: approved",
            metadata={"department": "Marketing"},
        )
        results = memory_store.query_similar("hr_001", "Budget request from Marketing for $1000.00", k=3)
        assert results == []
