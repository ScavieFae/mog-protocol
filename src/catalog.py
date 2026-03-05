"""Service catalog with embedding-based semantic search."""

import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ServiceEntry:
    service_id: str
    name: str
    description: str
    price_credits: int
    example_params: dict
    provider: str
    embedding: list[float] = field(default_factory=list)


class ServiceCatalog:
    def __init__(self):
        self._services: dict[str, ServiceEntry] = {}
        self._openai_client = None
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            try:
                import openai
                self._openai_client = openai.OpenAI(api_key=api_key)
            except ImportError:
                pass

    def _embed(self, text: str) -> list[float]:
        if self._openai_client is None:
            return []
        response = self._openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding

    def register(
        self,
        service_id: str,
        name: str,
        description: str,
        price_credits: int,
        example_params: dict[str, Any],
        provider: str,
    ) -> None:
        embedding = self._embed(description)
        self._services[service_id] = ServiceEntry(
            service_id=service_id,
            name=name,
            description=description,
            price_credits=price_credits,
            example_params=example_params,
            provider=provider,
            embedding=embedding,
        )

    def search(self, query: str, budget: int | None = None, top_k: int = 3) -> list[dict]:
        candidates = list(self._services.values())
        if budget is not None:
            candidates = [s for s in candidates if s.price_credits <= budget]

        if not candidates:
            return []

        if self._openai_client is not None:
            query_embedding = self._embed(query)
            scored = [(self._cosine(query_embedding, s.embedding), s) for s in candidates]
        else:
            q = query.lower()
            scored = [
                (int(q in s.name.lower() or q in s.description.lower()), s)
                for s in candidates
            ]

        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "service_id": s.service_id,
                "name": s.name,
                "description": s.description,
                "price_credits": s.price_credits,
                "example_params": s.example_params,
                "provider": s.provider,
                "score": score,
            }
            for score, s in scored[:top_k]
        ]

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        if not a or not b:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
