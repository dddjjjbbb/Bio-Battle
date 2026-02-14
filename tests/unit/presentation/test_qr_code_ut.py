"""Unit tests for QR code generation."""

from PIL import Image

from bio_battle.presentation.qr_code import generate_qr_code


class TestGenerateQrCode:
    """Tests for QR code generation."""

    def test_should_generate_qr_image_from_url(self) -> None:
        """generate_qr_code should return a PIL Image."""
        url = "https://en.wikipedia.org/wiki/Albert_Einstein"

        image = generate_qr_code(url)

        assert isinstance(image, Image.Image)

    def test_should_generate_square_image(self) -> None:
        """QR code image should be square."""
        url = "https://en.wikipedia.org/wiki/Oak"

        image = generate_qr_code(url)

        width, height = image.size
        assert width == height

    def test_should_generate_rgb_image(self) -> None:
        """QR code image should be in RGB mode for PDF compatibility."""
        url = "https://en.wikipedia.org/wiki/Albert_Einstein"

        image = generate_qr_code(url)

        assert image.mode == "RGB"

    def test_should_respect_size_parameter(self) -> None:
        """generate_qr_code should accept a size hint for the output."""
        url = "https://en.wikipedia.org/wiki/Albert_Einstein"

        small = generate_qr_code(url, box_size=4)
        large = generate_qr_code(url, box_size=10)

        assert large.size[0] > small.size[0]
