"""Embedding function for decision memory.

Groq serves no embedding endpoint, so a local sentence-transformers model is used
instead of the Groq chat model that powers agent decisions.
"""
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


def get_embedding_function() -> SentenceTransformerEmbeddingFunction:
    return SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL_NAME)
