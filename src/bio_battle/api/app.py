"""FastAPI application for Bio Battle REST API."""

from typing import Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from returns.result import Failure, Success

from bio_battle.data.wikipedia_client import WikipediaClient
from bio_battle.domain.entities import Card
from bio_battle.main import create_card_factory


class DeckRequest(BaseModel):
    """Request body for deck generation."""

    identifiers: list[str]


def _card_to_dict(card: Card) -> dict[str, Any]:
    """Convert a Card to a JSON-serializable dictionary."""
    subject = card.subject
    return {
        "subject": {
            "identifier": subject.identifier,
            "name": subject.name,
            "description": subject.description,
            "extract": subject.extract,
            "birth_date": subject.birth_date.isoformat() if subject.birth_date else None,
            "death_date": subject.death_date.isoformat() if subject.death_date else None,
            "image_url": subject.image_url,
            "page_views": subject.page_views,
            "article_length": subject.article_length,
            "languages_count": subject.languages_count,
        },
        "scores": {
            name: {
                "raw_value": score.raw_value,
                "bracket_score": score.bracket_score,
            }
            for name, score in card.scores.items()
        },
        "total_score": card.total_score,
    }


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Bio Battle API",
        description="Generate trading cards from Wikipedia biographies",
        version="0.1.0",
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/cards/{identifier}")
    def get_card(identifier: str) -> dict[str, Any]:
        factory = create_card_factory()
        result = factory.create_card(identifier)

        if isinstance(result, Failure):
            raise HTTPException(status_code=404, detail=str(result.failure()))

        return _card_to_dict(result.unwrap())

    @app.get("/api/search")
    def search_wikipedia(
        q: str = Query(..., description="Search query"),
        limit: int = Query(default=10, ge=1, le=50),
    ) -> dict[str, Any]:
        client = WikipediaClient()
        result = client.search_pages(q, limit=limit)

        if isinstance(result, Failure):
            raise HTTPException(status_code=502, detail="Search failed")

        return {"results": result.unwrap()}

    @app.post("/api/deck")
    def generate_deck(request: DeckRequest) -> dict[str, Any]:
        factory = create_card_factory()

        cards: list[dict[str, Any]] = []
        errors: list[str] = []

        for identifier in request.identifiers:
            result = factory.create_card(identifier)
            if isinstance(result, Success):
                cards.append(_card_to_dict(result.unwrap()))
            else:
                errors.append(identifier)

        return {
            "cards": cards,
            "errors": errors,
        }

    return app
