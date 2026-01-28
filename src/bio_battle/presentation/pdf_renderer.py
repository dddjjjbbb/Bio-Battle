"""PDF rendering for Bio Battle cards."""

import unicodedata
from datetime import date
from io import BytesIO
from pathlib import Path

from PIL import Image
from reportlab.lib.colors import Color, black, white
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from bio_battle.config.settings import Settings
from bio_battle.domain.entities import Card, EntityMode
from bio_battle.domain.nationality import get_flags_for_text
from bio_battle.presentation.layout import (
    SheetLayout,
    calculate_card_positions,
)


def _sanitize_text(text: str) -> str:
    """Sanitize text for PDF rendering by replacing unsupported characters.

    Converts accented characters to ASCII equivalents and removes
    characters that won't render in standard PDF fonts.

    Args:
        text: Input text that may contain Unicode characters.

    Returns:
        Sanitized text safe for PDF rendering.
    """
    # Normalize to decomposed form (separates base chars from diacritics)
    normalized = unicodedata.normalize("NFD", text)

    # Keep only ASCII characters (removes combining diacritics)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")

    # If we lost too much, try a smarter approach
    if len(ascii_text) < len(text) * 0.7:
        # Manual replacements for common characters
        replacements = {
            "\u0101": "a",  # ā
            "\u0113": "e",  # ē
            "\u012b": "i",  # ī
            "\u014d": "o",  # ō
            "\u016b": "u",  # ū
            "\u2013": "-",  # en-dash
            "\u2014": "-",  # em-dash
            "\u2018": "'",  # left single quote
            "\u2019": "'",  # right single quote
            "\u201c": '"',  # left double quote
            "\u201d": '"',  # right double quote
            "\u00e9": "e",  # e acute
            "\u00e8": "e",  # e grave
            "\u00e0": "a",  # a grave
            "\u00f1": "n",  # n tilde
            "\u00fc": "u",  # u umlaut
            "\u00f6": "o",  # o umlaut
            "\u00e4": "a",  # a umlaut
            "\u00df": "ss", # eszett
        }
        result = text
        for char, replacement in replacements.items():
            result = result.replace(char, replacement)
        # Final cleanup - remove any remaining non-ASCII
        result = result.encode("ascii", "ignore").decode("ascii")
        return result

    return ascii_text

# Card colours
CARD_BACKGROUND = Color(0.95, 0.95, 0.90)  # Light cream
CARD_BORDER = Color(0.2, 0.2, 0.2)  # Dark grey
SCORE_BAR_BG = Color(0.85, 0.85, 0.85)  # Light grey
SCORE_BAR_FG = Color(0.3, 0.5, 0.7)  # Blue
HEADER_BG = Color(0.2, 0.2, 0.2)  # Dark header

# Category display names
CATEGORY_NAMES = {
    "age": "Lifespan",
    "page_views": "Fame",
    "article_length": "Legacy",
    "languages": "Reach",
}


def _format_number(value: float) -> str:
    """Format large numbers with K/M suffixes."""
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    elif value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(int(value))


def _truncate_to_sentence(text: str, max_chars: int) -> str:
    """Truncate text to the last complete sentence that fits within max_chars.

    Finds sentence boundaries (periods, exclamation marks, question marks)
    and returns text up to the last complete sentence that fits.
    Always ensures the result ends with a full stop.

    Args:
        text: The full text to truncate.
        max_chars: Maximum number of characters allowed.

    Returns:
        Text truncated at the last sentence boundary that fits, ending with full stop.
    """
    if len(text) <= max_chars:
        return _ensure_full_stop(text)

    # Look for sentence endings within the allowed range
    # A sentence ends with . ! or ? followed by a space or end of string
    search_text = text[:max_chars]

    # Find all sentence boundaries
    best_end = -1
    for i, char in enumerate(search_text):
        if char in ".!?":
            # Check if this is a real sentence end (not abbreviation like "Dr.")
            # Simple heuristic: must be followed by space and capital, or end of text
            next_pos = i + 1
            if next_pos >= len(search_text):
                best_end = next_pos
            elif next_pos < len(text) and text[next_pos] == " ":
                # Check if followed by capital letter (new sentence)
                if next_pos + 1 < len(text) and text[next_pos + 1].isupper():
                    best_end = next_pos

    if best_end > max_chars * 0.3:  # Don't cut too early (at least 30% of space used)
        return _ensure_full_stop(text[:best_end].strip())

    # No good sentence boundary found - fall back to word boundary with ellipsis
    last_space = search_text.rfind(" ")
    if last_space > max_chars * 0.5:
        return search_text[:last_space].strip() + "..."

    return search_text.strip() + "..."


def _ensure_full_stop(text: str) -> str:
    """Ensure text ends with a full stop."""
    text = text.rstrip()
    if text and text[-1] not in ".!?":
        return text + "."
    return text


def _format_score_value(category: str, raw_value: float, card: Card) -> str:
    """Format a score's raw value for display.

    Values are formatted to be roughly similar lengths for visual uniformity.
    Target length is around 8-12 characters.
    """
    if category == "age":
        # Handle unknown age (raw_value of -1)
        if raw_value < 0:
            return "Unknown"
        return f"{int(raw_value)} yrs old"
    elif category == "page_views":
        # "187.5K views" = 12 chars
        return f"{_format_number(raw_value)} views"
    elif category == "article_length":
        # "14.3K words" = 11 chars
        return f"{_format_number(raw_value)} words"
    elif category == "languages":
        # "192 editions" = 12 chars
        return f"{int(raw_value)} editions"
    return str(int(raw_value))


class PdfRenderer:
    """Renders Bio Battle cards to PDF."""

    def __init__(
        self,
        settings: Settings,
        sheet_layout: SheetLayout,
    ) -> None:
        """Initialise renderer with settings and layout.

        Args:
            settings: Application settings.
            sheet_layout: Sheet layout configuration.
        """
        self._settings = settings
        self._layout = sheet_layout

    def render_cards(
        self,
        cards: list[Card],
        images: dict[str, Image.Image] | None = None,
    ) -> bytes:
        """Render cards to PDF and return as bytes.

        Args:
            cards: List of cards to render.
            images: Optional dictionary mapping person identifiers to images.

        Returns:
            PDF file content as bytes.
        """
        if images is None:
            images = {}

        buffer = BytesIO()
        c = canvas.Canvas(
            buffer,
            pagesize=(self._layout.page_width_pt, self._layout.page_height_pt),
        )

        if not cards:
            c.save()
            return buffer.getvalue()

        positions = calculate_card_positions(self._layout)
        cards_per_sheet = self._layout.cards_per_sheet

        for i, card in enumerate(cards):
            # Start new page if needed
            if i > 0 and i % cards_per_sheet == 0:
                c.showPage()

            position_index = i % cards_per_sheet
            position = positions[position_index]

            # Get image if available
            image = images.get(card.person.identifier)

            self._render_card(c, card, position, image)

        c.save()
        return buffer.getvalue()

    def save_to_file(
        self,
        cards: list[Card],
        output_path: Path,
        images: dict[str, Image.Image] | None = None,
    ) -> None:
        """Render cards and save to file.

        Args:
            cards: List of cards to render.
            output_path: Path to save the PDF.
            images: Optional dictionary mapping person identifiers to images.
        """
        pdf_bytes = self.render_cards(cards, images)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(pdf_bytes)

    def _render_card(
        self,
        c: canvas.Canvas,
        card: Card,
        position,
        image: Image.Image | None,
    ) -> None:
        """Render a single card at the specified position."""
        x = position.x_pt
        y = position.y_pt
        width = position.width_pt
        height = position.height_pt

        # Draw cut lines (dashed) around card
        c.setStrokeColor(Color(0.6, 0.6, 0.6))
        c.setLineWidth(0.5)
        c.setDash(3, 2)  # 3pt dash, 2pt gap
        c.rect(x - 2, y - 2, width + 4, height + 4, fill=False, stroke=True)
        c.setDash()  # Reset to solid line

        # Draw card background with sharp corners (matches header/footer)
        c.setFillColor(CARD_BACKGROUND)
        c.setStrokeColor(CARD_BORDER)
        c.setLineWidth(1)
        c.rect(x, y, width, height, fill=True, stroke=True)

        # Margins
        margin = 6
        inner_width = width - 2 * margin
        inner_x = x + margin

        # === HEADER: Name with dark background ===
        header_height = 16
        header_y = y + height - header_height
        c.setFillColor(HEADER_BG)
        c.rect(x, header_y, width, header_height, fill=True, stroke=False)

        # Draw name (white on dark) - Helvetica for name
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 8)

        # Sanitize name for PDF rendering
        safe_name = _sanitize_text(card.person.name)

        # Add nationality codes if available (e.g., "[PL/FR]")
        country_codes = get_flags_for_text(card.person.description)
        name_with_codes = f"{safe_name} {country_codes}" if country_codes else safe_name
        name_text = self._truncate_text(name_with_codes, inner_width - 4, c)
        c.drawString(inner_x + 2, header_y + 4, name_text)

        # === IMAGE SECTION (larger) ===
        image_top = header_y - 3
        image_height = 90  # Taller image
        image_y = image_top - image_height

        # Draw image border
        c.setStrokeColor(CARD_BORDER)
        c.setLineWidth(0.5)
        c.rect(inner_x, image_y, inner_width, image_height, fill=False, stroke=True)

        if image is not None:
            self._draw_image(c, image, inner_x + 1, image_y + 1, inner_width - 2, image_height - 2)
        else:
            # Draw placeholder
            c.setFillColor(Color(0.9, 0.9, 0.9))
            c.rect(inner_x + 1, image_y + 1, inner_width - 2, image_height - 2, fill=True, stroke=False)
            c.setFillColor(Color(0.6, 0.6, 0.6))
            c.setFont("Courier", 7)
            c.drawCentredString(x + width / 2, image_y + image_height / 2 - 3, "NO IMAGE")

        # === SCORES SECTION with actual values ===
        scores_top = image_y - 4
        scores_bottom = self._draw_scores(c, card, inner_x, scores_top, inner_width)

        # === INFO SECTION (dates, description) ===
        info_top = scores_bottom - 4
        footer_height = 14
        info_bottom = y + footer_height + 2
        self._draw_info_section(c, card, inner_x, info_top, inner_width, info_bottom)

        # === TOTAL SCORE (bottom) ===
        total_y = y + 3
        c.setFillColor(HEADER_BG)
        c.rect(x, y, width, footer_height, fill=True, stroke=False)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(x + width / 2, total_y, f"TOTAL: {card.total_score}")

    def _draw_scores(
        self,
        c: canvas.Canvas,
        card: Card,
        x: float,
        top_y: float,
        width: float,
    ) -> float:
        """Draw score bars for all categories with actual values.

        Returns the y position after the last score bar.
        """
        bar_height = 9
        bar_spacing = 11
        label_width = 38
        score_width = 10

        y = top_y

        for category, score in card.scores.items():
            display_name = CATEGORY_NAMES.get(category, category)
            value_text = _format_score_value(category, score.raw_value, card)

            # Draw category label - monospace
            c.setFont("Courier", 5)
            c.setFillColor(black)
            c.drawString(x, y - bar_height + 2, display_name)

            # Draw score bar background
            bar_x = x + label_width
            bar_width = width - label_width - score_width - 2

            c.setFillColor(SCORE_BAR_BG)
            c.rect(bar_x, y - bar_height, bar_width, bar_height - 1, fill=True, stroke=False)

            # Draw score bar fill (proportional to bracket_score / 10)
            fill_width = (score.bracket_score / 10.0) * bar_width
            c.setFillColor(SCORE_BAR_FG)
            c.rect(bar_x, y - bar_height, fill_width, bar_height - 1, fill=True, stroke=False)

            # Draw actual value inside bar - monospace
            c.setFillColor(Color(0.15, 0.15, 0.15))
            c.setFont("Courier", 4)
            c.drawString(bar_x + 2, y - bar_height + 2, value_text)

            # Draw score number (right aligned) - monospace bold
            c.setFillColor(black)
            c.setFont("Courier-Bold", 6)
            c.drawRightString(x + width, y - bar_height + 2, str(score.bracket_score))

            y -= bar_spacing

        return y

    def _draw_info_section(
        self,
        c: canvas.Canvas,
        card: Card,
        x: float,
        top_y: float,
        width: float,
        bottom_y: float,
    ) -> None:
        """Draw info section with dates, stats, and description."""
        small_line = 5
        y = top_y
        subject = card.subject
        text_color = Color(0.3, 0.3, 0.3)
        is_person = subject.mode == EntityMode.PERSON

        # === STATS with bold labels ===
        # Left column: birth/death info (only for people)
        if is_person and subject.birth_date:
            birth_year = subject.birth_date.year
            y = self._draw_label_value(c, x, y, "Born:", str(birth_year), text_color)
            if subject.death_date:
                death_year = subject.death_date.year
                y = self._draw_label_value(c, x, y, "Died:", str(death_year), text_color)

        # Right column stats (drawn on same lines)
        right_y = top_y

        # Age/Lived only shown for people
        if is_person:
            if subject.age is not None:
                label = "Lived:" if subject.death_date else "Age:"
                self._draw_label_value_right(c, x + width, right_y, label, f"{subject.age} yrs", text_color)
            else:
                self._draw_label_value_right(c, x + width, right_y, "Age:", "Unknown", text_color)
            right_y -= small_line

        self._draw_label_value_right(c, x + width, right_y, "Views:", f"{_format_number(subject.page_views)}/mo", text_color)
        right_y -= small_line
        self._draw_label_value_right(c, x + width, right_y, "Words:", f"{_format_number(subject.article_length)}", text_color)
        right_y -= small_line
        self._draw_label_value_right(c, x + width, right_y, "Wiki Langs:", str(subject.languages_count), text_color)
        right_y -= small_line  # Account for last line

        # Move y to account for right column
        y = min(y, right_y)

        # Draw separator line
        y -= 1
        c.setStrokeColor(Color(0.7, 0.7, 0.7))
        c.setLineWidth(0.3)
        c.line(x, y, x + width, y)
        y -= 3

        # === BIO/DESCRIPTION (wrapped, fills remaining space) ===
        c.setFont("Courier", 5)
        c.setFillColor(Color(0.25, 0.25, 0.25))

        # Calculate available space for bio text
        available_height = y - bottom_y
        max_lines = int(available_height / small_line)

        # Sanitize bio text
        safe_bio = _sanitize_text(subject.bio)

        # Word wrap and find sentence boundaries that fit
        lines = self._wrap_text_to_lines(c, safe_bio, width)

        # If too many lines, find the last complete sentence that fits
        if len(lines) > max_lines:
            lines = self._truncate_lines_at_sentence(c, lines, max_lines, width)

        # Draw the lines
        for line in lines:
            c.drawString(x, y - small_line + 1, line)
            y -= small_line

    def _wrap_text_to_lines(
        self,
        c: canvas.Canvas,
        text: str,
        width: float,
    ) -> list[str]:
        """Wrap text into lines that fit within the given width."""
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()
            if c.stringWidth(test_line) <= width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines

    def _truncate_lines_at_sentence(
        self,
        c: canvas.Canvas,
        lines: list[str],
        max_lines: int,
        width: float,
    ) -> list[str]:
        """Truncate lines at the last complete sentence that fits.

        Finds the last sentence boundary (. ! ?) within max_lines
        and returns only the lines up to and including that sentence.
        """
        if not lines or max_lines <= 0:
            return []

        # Join lines to find sentence boundaries
        text = " ".join(lines[:max_lines])

        # Find the last sentence boundary
        last_sentence_end = -1
        for i, char in enumerate(text):
            if char in ".!?":
                # Check if this looks like a real sentence end
                next_pos = i + 1
                if next_pos >= len(text):
                    # End of text
                    last_sentence_end = next_pos
                elif text[next_pos] == " ":
                    # Followed by space - likely sentence end
                    if next_pos + 1 < len(text) and text[next_pos + 1].isupper() or next_pos + 1 >= len(text):
                        last_sentence_end = next_pos

        if last_sentence_end > 0:
            # Truncate at sentence boundary and ensure full stop
            truncated = _ensure_full_stop(text[:last_sentence_end].strip())
            # Re-wrap the truncated text using the canvas
            return self._wrap_text_to_lines(c, truncated, width)

        # No sentence boundary found - just return max_lines with ellipsis
        result = lines[:max_lines]
        if result:
            result[-1] = result[-1].rstrip() + "..."
        return result

    def _draw_label_value(
        self,
        c: canvas.Canvas,
        x: float,
        y: float,
        label: str,
        value: str,
        color: Color,
    ) -> float:
        """Draw a label: value pair with bold label, return new y position."""
        small_line = 5

        # Draw bold label
        c.setFont("Courier-Bold", 5)
        c.setFillColor(color)
        c.drawString(x, y - small_line + 1, label)

        # Draw regular value after label
        label_width = c.stringWidth(label)
        c.setFont("Courier", 5)
        c.drawString(x + label_width + 2, y - small_line + 1, value)

        return y - small_line

    def _draw_label_value_right(
        self,
        c: canvas.Canvas,
        right_x: float,
        y: float,
        label: str,
        value: str,
        color: Color,
    ) -> None:
        """Draw a label: value pair right-aligned with bold label."""
        small_line = 5

        # Calculate positions
        c.setFont("Courier", 5)
        value_width = c.stringWidth(value)
        c.setFont("Courier-Bold", 5)
        label_width = c.stringWidth(label)

        total_width = label_width + 2 + value_width
        start_x = right_x - total_width

        # Draw bold label
        c.setFillColor(color)
        c.drawString(start_x, y - small_line + 1, label)

        # Draw regular value
        c.setFont("Courier", 5)
        c.drawString(start_x + label_width + 2, y - small_line + 1, value)

    def _draw_image(
        self,
        c: canvas.Canvas,
        image: Image.Image,
        x: float,
        y: float,
        target_width: float,
        target_height: float,
    ) -> None:
        """Draw a PIL image on the canvas, cropping to fill the space.

        For portraits, uses smart cropping to preserve faces:
        - Horizontal crops are centered
        - Vertical crops start slightly below top (faces are typically
          in upper-middle portion, not at very top edge)
        """
        # Crop image to fill target area (cover mode, not contain)
        img_width, img_height = image.size
        img_aspect = img_width / img_height
        target_aspect = target_width / target_height

        if img_aspect > target_aspect:
            # Image is wider - crop sides (center crop)
            new_width = int(img_height * target_aspect)
            left = (img_width - new_width) // 2
            cropped = image.crop((left, 0, left + new_width, img_height))
        else:
            # Image is taller - smart crop for faces
            new_height = int(img_width / target_aspect)
            # Start crop at 10% from top - faces are usually in upper-middle
            # not at the very edge (which often has hair/background)
            available_height = img_height - new_height
            top_offset = int(available_height * 0.1)  # Start 10% down
            cropped = image.crop((0, top_offset, img_width, top_offset + new_height))

        # Convert to bytes for ReportLab
        img_buffer = BytesIO()
        cropped.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        # Draw at exact target size
        img_reader = ImageReader(img_buffer)
        c.drawImage(
            img_reader,
            x,
            y,
            width=target_width,
            height=target_height,
        )

    def _truncate_text(
        self,
        text: str,
        max_width: float,
        c: canvas.Canvas,
    ) -> str:
        """Truncate text to fit within max_width."""
        if c.stringWidth(text) <= max_width:
            return text

        while len(text) > 0 and c.stringWidth(text + "...") > max_width:
            text = text[:-1]

        return text + "..." if text else ""
