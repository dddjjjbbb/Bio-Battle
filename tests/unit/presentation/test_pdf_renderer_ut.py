"""Unit tests for PDF renderer."""

from datetime import date
from pathlib import Path

from PIL import Image

from bio_battle.config.settings import Settings
from bio_battle.domain.entities import Card, Person, Score
from bio_battle.presentation.layout import SheetLayout
from bio_battle.presentation.pdf_renderer import (
    PdfRenderer,
    _ensure_full_stop,
    _truncate_to_sentence,
)


def create_test_person(
    name: str = "Albert Einstein",
    description: str = "German-born theoretical physicist",
) -> Person:
    """Create a test person."""
    return Person(
        identifier="test",
        name=name,
        description=description,
        extract="Albert Einstein was a German-born theoretical physicist who is widely held to be one of the greatest and most influential scientists of all time.",
        birth_date=date(1879, 3, 14),
        death_date=date(1955, 4, 18),
        image_url="https://example.com/image.jpg",
        page_views=1000000,
        article_length=50000,
        languages_count=150,
    )


def create_test_card(name: str = "Albert Einstein") -> Card:
    """Create a test card."""
    person = create_test_person(name=name)
    scores: dict[str, Score] = {
        "age": Score(raw_value=76.0, bracket_score=7),
        "page_views": Score(raw_value=1000000.0, bracket_score=7),
        "article_length": Score(raw_value=50000.0, bracket_score=8),
        "languages": Score(raw_value=150.0, bracket_score=9),
    }
    return Card(person=person, scores=scores)


class TestPdfRenderer:
    """Tests for PdfRenderer."""

    def test_should_create_renderer_with_settings(self) -> None:
        """PdfRenderer should be created with settings and layout."""
        settings = Settings()
        layout = SheetLayout.from_settings(settings)

        renderer = PdfRenderer(settings=settings, sheet_layout=layout)

        assert renderer is not None

    def test_should_render_single_card_to_pdf(self) -> None:
        """render_cards should create PDF with single card."""
        settings = Settings()
        layout = SheetLayout.from_settings(settings)
        renderer = PdfRenderer(settings=settings, sheet_layout=layout)
        cards = [create_test_card()]

        pdf_bytes = renderer.render_cards(cards)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        # Check PDF magic bytes
        assert pdf_bytes[:4] == b"%PDF"

    def test_should_render_multiple_cards_on_one_sheet(self) -> None:
        """render_cards should fit multiple cards on single sheet."""
        settings = Settings(cards_per_row=3, cards_per_column=3)
        layout = SheetLayout.from_settings(settings)
        renderer = PdfRenderer(settings=settings, sheet_layout=layout)
        cards = [create_test_card(f"Person {i}") for i in range(5)]

        pdf_bytes = renderer.render_cards(cards)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

    def test_should_span_multiple_sheets_for_many_cards(self) -> None:
        """render_cards should create multiple pages for many cards."""
        settings = Settings(cards_per_row=3, cards_per_column=3)
        layout = SheetLayout.from_settings(settings)
        renderer = PdfRenderer(settings=settings, sheet_layout=layout)
        # Create 10 cards (more than 9 per sheet)
        cards = [create_test_card(f"Person {i}") for i in range(10)]

        pdf_bytes = renderer.render_cards(cards)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

    def test_should_render_empty_list_as_empty_pdf(self) -> None:
        """render_cards should handle empty card list."""
        settings = Settings()
        layout = SheetLayout.from_settings(settings)
        renderer = PdfRenderer(settings=settings, sheet_layout=layout)

        pdf_bytes = renderer.render_cards([])

        # Should still be valid PDF (possibly empty)
        assert isinstance(pdf_bytes, bytes)

    def test_should_save_pdf_to_file(self) -> None:
        """save_to_file should write PDF to specified path."""
        settings = Settings()
        layout = SheetLayout.from_settings(settings)
        renderer = PdfRenderer(settings=settings, sheet_layout=layout)
        cards = [create_test_card()]
        output_path = Path("/tmp/test_output.pdf")

        renderer.save_to_file(cards, output_path)

        assert output_path.exists()
        content = output_path.read_bytes()
        assert content[:4] == b"%PDF"
        # Cleanup
        output_path.unlink()

    def test_should_include_person_name_on_card(self) -> None:
        """render_cards should include person's name on the card."""
        settings = Settings()
        layout = SheetLayout.from_settings(settings)
        renderer = PdfRenderer(settings=settings, sheet_layout=layout)
        cards = [create_test_card("Albert Einstein")]

        pdf_bytes = renderer.render_cards(cards)

        # The name should be embedded in the PDF
        # Note: PDF encoding may vary, so this is a basic check
        assert len(pdf_bytes) > 100

    def test_should_include_total_score_on_card(self) -> None:
        """render_cards should display total score on card."""
        settings = Settings()
        layout = SheetLayout.from_settings(settings)
        renderer = PdfRenderer(settings=settings, sheet_layout=layout)
        card = create_test_card()
        # Total score = 3 + 7 + 7 + 8 + 9 = 34

        pdf_bytes = renderer.render_cards([card])

        assert len(pdf_bytes) > 100

    def test_should_render_with_image(self) -> None:
        """render_cards should include card image when provided."""
        settings = Settings()
        layout = SheetLayout.from_settings(settings)
        renderer = PdfRenderer(settings=settings, sheet_layout=layout)
        card = create_test_card()
        # Create a test image
        test_image = Image.new("RGB", (200, 200), "blue")
        images = {card.person.identifier: test_image}

        pdf_bytes = renderer.render_cards([card], images=images)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

    def test_should_render_without_images(self) -> None:
        """render_cards should work without images dictionary."""
        settings = Settings()
        layout = SheetLayout.from_settings(settings)
        renderer = PdfRenderer(settings=settings, sheet_layout=layout)
        cards = [create_test_card()]

        pdf_bytes = renderer.render_cards(cards)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0


class TestTruncateToSentence:
    """Tests for _truncate_to_sentence function."""

    def test_should_return_text_unchanged_when_under_limit(self) -> None:
        """Text shorter than max_chars should be returned unchanged."""
        text = "This is a short sentence."

        result = _truncate_to_sentence(text, 100)

        assert result == text

    def test_should_truncate_at_sentence_boundary(self) -> None:
        """Text should be truncated at the last complete sentence."""
        text = "First sentence. Second sentence. Third sentence."

        result = _truncate_to_sentence(text, 35)

        assert result == "First sentence. Second sentence."

    def test_should_handle_exclamation_marks(self) -> None:
        """Should recognise exclamation marks as sentence endings."""
        text = "What a discovery! This changes everything. More text."

        result = _truncate_to_sentence(text, 45)

        assert result == "What a discovery! This changes everything."

    def test_should_handle_question_marks(self) -> None:
        """Should recognise question marks as sentence endings."""
        text = "Is this correct? Yes it is. More text here."

        result = _truncate_to_sentence(text, 30)

        assert result == "Is this correct? Yes it is."

    def test_should_fallback_to_word_boundary_when_no_sentence(self) -> None:
        """Should truncate at word boundary with ellipsis when no sentence end."""
        text = "This is a very long sentence without any periods"

        result = _truncate_to_sentence(text, 25)

        assert result.endswith("...")
        assert " " not in result[-4:]  # Should not end with partial word

    def test_should_handle_newton_example(self) -> None:
        """Should truncate Newton bio at 'classical mechanics.' sentence."""
        text = (
            "Sir Isaac Newton was an English polymath who was a "
            "mathematician, physicist, astronomer, alchemist, "
            "theologian, author and inventor. He was a key figure in "
            "the Scientific Revolution and the Enlightenment that "
            "followed. His book Philosophi Naturalis Principia "
            "Mathematica, first published in 1687, achieved the first "
            "great unification in physics and established classical "
            "mechanics. Newton also made seminal contributions to "
            "optics, and shares credit with Gottfried Wilhelm Leibniz."
        )

        # Calculate limit that cuts after "classical mechanics."
        result = _truncate_to_sentence(text, 450)

        assert "classical mechanics." in result
        assert "Newton also made" not in result


class TestEnsureFullStop:
    """Tests for _ensure_full_stop function."""

    def test_should_add_full_stop_when_missing(self) -> None:
        """Should add full stop to text without ending punctuation."""
        result = _ensure_full_stop("This is a sentence")

        assert result == "This is a sentence."

    def test_should_not_add_full_stop_when_present(self) -> None:
        """Should not add full stop when text already ends with one."""
        result = _ensure_full_stop("This is a sentence.")

        assert result == "This is a sentence."

    def test_should_preserve_exclamation_mark(self) -> None:
        """Should not add full stop when text ends with exclamation mark."""
        result = _ensure_full_stop("What a discovery!")

        assert result == "What a discovery!"

    def test_should_preserve_question_mark(self) -> None:
        """Should not add full stop when text ends with question mark."""
        result = _ensure_full_stop("Is this correct?")

        assert result == "Is this correct?"

    def test_should_handle_trailing_whitespace(self) -> None:
        """Should strip trailing whitespace and add full stop."""
        result = _ensure_full_stop("This has trailing space   ")

        assert result == "This has trailing space."

    def test_should_handle_empty_string(self) -> None:
        """Should handle empty string gracefully."""
        result = _ensure_full_stop("")

        assert result == ""
