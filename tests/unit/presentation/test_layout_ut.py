"""Unit tests for layout engine."""



from bio_battle.config.settings import Settings
from bio_battle.presentation.layout import (
    CardLayout,
    CardPosition,
    SheetLayout,
    calculate_card_positions,
)


class TestCardLayout:
    """Tests for CardLayout."""

    def test_should_create_card_layout_from_settings(self) -> None:
        """CardLayout should be created with dimensions from settings."""
        settings = Settings(card_width_mm=63.5, card_height_mm=88.9)

        layout = CardLayout.from_settings(settings)

        assert layout.width_mm == 63.5
        assert layout.height_mm == 88.9

    def test_should_convert_mm_to_points(self) -> None:
        """CardLayout should convert millimetres to points."""
        layout = CardLayout(width_mm=25.4, height_mm=25.4)  # 1 inch = 25.4mm

        # 1 inch = 72 points
        assert abs(layout.width_pt - 72.0) < 0.1
        assert abs(layout.height_pt - 72.0) < 0.1

    def test_should_calculate_standard_card_size(self) -> None:
        """CardLayout should correctly calculate standard trading card size."""
        # Standard trading card: 63.5mm x 88.9mm (2.5" x 3.5")
        layout = CardLayout(width_mm=63.5, height_mm=88.9)

        # 2.5 inches = 180 points
        # 3.5 inches = 252 points
        assert abs(layout.width_pt - 180.0) < 1.0
        assert abs(layout.height_pt - 252.0) < 1.0


class TestSheetLayout:
    """Tests for SheetLayout."""

    def test_should_create_sheet_layout_from_settings(self) -> None:
        """SheetLayout should be created with dimensions from settings."""
        settings = Settings(
            cards_per_row=3,
            cards_per_column=3,
            card_width_mm=63.5,
            card_height_mm=88.9,
        )

        layout = SheetLayout.from_settings(settings)

        assert layout.cards_per_row == 3
        assert layout.cards_per_column == 3
        assert layout.card_layout.width_mm == 63.5

    def test_should_calculate_total_cards_per_sheet(self) -> None:
        """SheetLayout should calculate total cards per sheet."""
        layout = SheetLayout(
            cards_per_row=3,
            cards_per_column=3,
            card_layout=CardLayout(width_mm=63.5, height_mm=88.9),
        )

        assert layout.cards_per_sheet == 9

    def test_should_use_a4_page_size_by_default(self) -> None:
        """SheetLayout should use A4 page size by default."""
        layout = SheetLayout(
            cards_per_row=3,
            cards_per_column=3,
            card_layout=CardLayout(width_mm=63.5, height_mm=88.9),
        )

        # A4: 210mm x 297mm
        assert layout.page_width_mm == 210.0
        assert layout.page_height_mm == 297.0

    def test_should_calculate_page_size_in_points(self) -> None:
        """SheetLayout should calculate page size in points."""
        layout = SheetLayout(
            cards_per_row=3,
            cards_per_column=3,
            card_layout=CardLayout(width_mm=63.5, height_mm=88.9),
        )

        # A4 in points: approximately 595 x 842
        assert abs(layout.page_width_pt - 595.28) < 1.0
        assert abs(layout.page_height_pt - 841.89) < 1.0


class TestCardPosition:
    """Tests for CardPosition."""

    def test_should_store_position_coordinates(self) -> None:
        """CardPosition should store x, y, width, height in points."""
        position = CardPosition(x_pt=100.0, y_pt=200.0, width_pt=180.0, height_pt=252.0)

        assert position.x_pt == 100.0
        assert position.y_pt == 200.0
        assert position.width_pt == 180.0
        assert position.height_pt == 252.0


class TestCalculateCardPositions:
    """Tests for calculate_card_positions function."""

    def test_should_calculate_positions_for_3x3_grid(self) -> None:
        """calculate_card_positions should return 9 positions for 3x3 grid."""
        layout = SheetLayout(
            cards_per_row=3,
            cards_per_column=3,
            card_layout=CardLayout(width_mm=63.5, height_mm=88.9),
        )

        positions = calculate_card_positions(layout)

        assert len(positions) == 9

    def test_should_space_cards_evenly(self) -> None:
        """calculate_card_positions should space cards evenly on sheet."""
        layout = SheetLayout(
            cards_per_row=3,
            cards_per_column=3,
            card_layout=CardLayout(width_mm=63.5, height_mm=88.9),
        )

        positions = calculate_card_positions(layout)

        # All positions should be unique
        unique_positions = set((p.x_pt, p.y_pt) for p in positions)
        assert len(unique_positions) == 9

    def test_should_place_cards_within_page_bounds(self) -> None:
        """calculate_card_positions should place all cards within page bounds."""
        layout = SheetLayout(
            cards_per_row=3,
            cards_per_column=3,
            card_layout=CardLayout(width_mm=63.5, height_mm=88.9),
        )

        positions = calculate_card_positions(layout)

        for pos in positions:
            # Card should fit within page
            assert pos.x_pt >= 0
            assert pos.y_pt >= 0
            assert pos.x_pt + pos.width_pt <= layout.page_width_pt
            assert pos.y_pt + pos.height_pt <= layout.page_height_pt

    def test_should_return_positions_in_row_major_order(self) -> None:
        """calculate_card_positions should return positions row by row."""
        layout = SheetLayout(
            cards_per_row=2,
            cards_per_column=2,
            card_layout=CardLayout(width_mm=63.5, height_mm=88.9),
        )

        positions = calculate_card_positions(layout)

        # First row positions should have same y coordinate
        assert positions[0].y_pt == positions[1].y_pt
        # Second row should be below first row
        assert positions[2].y_pt < positions[0].y_pt

    def test_should_calculate_margins_for_centering(self) -> None:
        """calculate_card_positions should centre cards on page."""
        layout = SheetLayout(
            cards_per_row=3,
            cards_per_column=3,
            card_layout=CardLayout(width_mm=63.5, height_mm=88.9),
        )

        positions = calculate_card_positions(layout)

        # Find leftmost and rightmost cards
        min_x = min(p.x_pt for p in positions)
        max_x = max(p.x_pt + p.width_pt for p in positions)

        # Left and right margins should be approximately equal
        left_margin = min_x
        right_margin = layout.page_width_pt - max_x
        assert abs(left_margin - right_margin) < 1.0
