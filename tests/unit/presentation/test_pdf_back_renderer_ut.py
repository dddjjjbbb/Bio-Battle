"""Unit tests for PDF card-back rendering."""

from datetime import date

from bio_battle.config.settings import Settings
from bio_battle.domain.entities import Card, Score, Subject
from bio_battle.presentation.layout import SheetLayout
from bio_battle.presentation.pdf_renderer import PdfRenderer


def create_test_card(identifier: str = "Albert_Einstein") -> Card:
    """Create a test card for rendering."""
    subject = Subject(
        identifier=identifier,
        name="Albert Einstein",
        description="Theoretical physicist",
        extract="Albert Einstein was a German-born theoretical physicist.",
        birth_date=date(1879, 3, 14),
        death_date=date(1955, 4, 18),
        image_url=None,
        page_views=1000000,
        article_length=50000,
        languages_count=150,
    )
    scores: dict[str, Score] = {
        "age": Score(raw_value=76.0, bracket_score=7),
        "page_views": Score(raw_value=1000000.0, bracket_score=7),
        "article_length": Score(raw_value=50000.0, bracket_score=7),
        "languages": Score(raw_value=150.0, bracket_score=8),
    }
    return Card(subject=subject, scores=scores)


class TestCardBackRendering:
    """Tests for card-back PDF rendering."""

    def test_should_render_card_backs_as_pdf_bytes(self) -> None:
        """render_card_backs should return non-empty PDF bytes."""
        settings = Settings()
        layout = SheetLayout.from_settings(settings)
        renderer = PdfRenderer(settings=settings, sheet_layout=layout)
        cards = [create_test_card()]

        pdf_bytes = renderer.render_card_backs(cards)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:5] == b"%PDF-"

    def test_should_render_backs_for_multiple_cards(self) -> None:
        """render_card_backs should handle multiple cards."""
        settings = Settings()
        layout = SheetLayout.from_settings(settings)
        renderer = PdfRenderer(settings=settings, sheet_layout=layout)
        cards = [
            create_test_card("Einstein"),
            create_test_card("Curie"),
            create_test_card("Newton"),
        ]

        pdf_bytes = renderer.render_card_backs(cards)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

    def test_should_render_empty_list_as_empty_pdf(self) -> None:
        """render_card_backs should handle empty card list."""
        settings = Settings()
        layout = SheetLayout.from_settings(settings)
        renderer = PdfRenderer(settings=settings, sheet_layout=layout)

        pdf_bytes = renderer.render_card_backs([])

        assert isinstance(pdf_bytes, bytes)
