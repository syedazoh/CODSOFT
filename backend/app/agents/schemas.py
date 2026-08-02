"""Structured-output schemas for agent LLM decisions"""
from typing import Optional

from pydantic import BaseModel, Field


class FinanceDecision(BaseModel):
    """Finance agent's structured decision on a budget request"""
    approved: bool = Field(description="Whether the budget request is approved")
    reasoning: str = Field(description="Brief explanation of the decision")
    amount_approved: float = Field(description="Amount approved (0 if denied)")
    risk_notes: Optional[str] = Field(default=None, description="Any financial risk notes")
