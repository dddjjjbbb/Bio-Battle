"""Layout engine for Bio Battle card sheets."""

from dataclasses import dataclass

from bio_battle.config.settings import Settings

# Conversion constant: 1mm = 72/25.4 points
MM_TO_POINTS = 72.0 / 25.4

# A4 page dimensions in mm
A4_WIDTH_MM = 210.0
A4_HEIGHT_MM = 297.0


@dataclass(frozen=True)
class CardLayout:
    """Defines card dimensions."""

    width_mm: float
    height_mm: float

    @classmethod
    def from_settings(cls, settings: Settings) -> "CardLayout":
        """Create CardLayout from application settings."""
        return cls(
            width_mm=settings.card_width_mm,
            height_mm=settings.card_height_mm,
        )

    @property
    def width_pt(self) -> float:
        """Card width in points."""
        return self.width_mm * MM_TO_POINTS

    @property
    def height_pt(self) -> float:
        """Card height in points."""
        return self.height_mm * MM_TO_POINTS


@dataclass(frozen=True)
class CardPosition:
    """Position of a card on a sheet in points."""

    x_pt: float
    y_pt: float
    width_pt: float
    height_pt: float


@dataclass(frozen=True)
class SheetLayout:
    """Defines sheet layout for cards."""

    cards_per_row: int
    cards_per_column: int
    card_layout: CardLayout
    page_width_mm: float = A4_WIDTH_MM
    page_height_mm: float = A4_HEIGHT_MM

    @classmethod
    def from_settings(cls, settings: Settings) -> "SheetLayout":
        """Create SheetLayout from application settings."""
        return cls(
            cards_per_row=settings.cards_per_row,
            cards_per_column=settings.cards_per_column,
            card_layout=CardLayout.from_settings(settings),
        )

    @property
    def cards_per_sheet(self) -> int:
        """Total number of cards per sheet."""
        return self.cards_per_row * self.cards_per_column

    @property
    def page_width_pt(self) -> float:
        """Page width in points."""
        return self.page_width_mm * MM_TO_POINTS

    @property
    def page_height_pt(self) -> float:
        """Page height in points."""
        return self.page_height_mm * MM_TO_POINTS


def calculate_card_positions(layout: SheetLayout, gap_mm: float = 3.0) -> list[CardPosition]:
    """Calculate positions for all cards on a sheet.

    Cards are arranged in a grid and centred on the page with gaps between them.
    Positions are returned in row-major order (left to right, top to bottom).

    Note: In PDF coordinate system, y=0 is at bottom of page.
    Positions are returned with higher y values for top rows.

    Args:
        layout: The sheet layout configuration.
        gap_mm: Gap between cards in millimetres.

    Returns:
        List of CardPosition objects for each card slot.
    """
    card_width = layout.card_layout.width_pt
    card_height = layout.card_layout.height_pt
    gap_pt = gap_mm * MM_TO_POINTS

    # Calculate total grid dimensions including gaps
    total_grid_width = (card_width * layout.cards_per_row) + (gap_pt * (layout.cards_per_row - 1))
    total_grid_height = (card_height * layout.cards_per_column) + (gap_pt * (layout.cards_per_column - 1))

    # Calculate margins to centre the grid
    horizontal_margin = (layout.page_width_pt - total_grid_width) / 2
    vertical_margin = (layout.page_height_pt - total_grid_height) / 2

    positions = []

    for row in range(layout.cards_per_column):
        for col in range(layout.cards_per_row):
            # x increases left to right, with gaps between cards
            x = horizontal_margin + (col * (card_width + gap_pt))
            # y decreases top to bottom (PDF origin is bottom-left)
            # Start from top and work down, with gaps between cards
            y = layout.page_height_pt - vertical_margin - ((row + 1) * card_height) - (row * gap_pt)

            positions.append(
                CardPosition(
                    x_pt=x,
                    y_pt=y,
                    width_pt=card_width,
                    height_pt=card_height,
                )
            )

    return positions
