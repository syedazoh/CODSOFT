"""Groq LLM client factory, shared by every agent's LangGraph graph"""
from langchain_groq import ChatGroq

from ..config import settings


def get_groq_llm(temperature: float = 0.0) -> ChatGroq:
    return ChatGroq(
        groq_api_key=settings.groq_api_key,
        model_name=settings.groq_model,
        temperature=temperature,
    )
