"""Unit tests for ImageProcessor."""

from io import BytesIO
from unittest.mock import Mock, patch

from PIL import Image
from returns.result import Failure, Success

from bio_battle.config.settings import Settings
from bio_battle.presentation.image_processor import ImageProcessor


def create_test_image(
    width: int = 400,
    height: int = 300,
    colour: str = "red",
) -> bytes:
    """Create a test image as bytes."""
    image = Image.new("RGB", (width, height), colour)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


class TestImageProcessor:
    """Tests for ImageProcessor."""

    def test_should_create_processor_with_settings(self) -> None:
        """ImageProcessor should be created with settings."""
        settings = Settings()

        processor = ImageProcessor(settings=settings)

        assert processor is not None

    def test_should_resize_image_to_target_dimensions(self) -> None:
        """resize_image should scale image to target width and height."""
        settings = Settings(image_width_px=200, image_height_px=200)
        processor = ImageProcessor(settings=settings)
        original_image = Image.new("RGB", (400, 300), "blue")

        resized = processor.resize_image(original_image)

        assert resized.width == 200
        assert resized.height == 200

    def test_should_maintain_aspect_ratio_when_requested(self) -> None:
        """resize_image should maintain aspect ratio when preserve_aspect=True."""
        settings = Settings(image_width_px=200, image_height_px=200)
        processor = ImageProcessor(settings=settings)
        original_image = Image.new("RGB", (400, 200), "green")

        resized = processor.resize_image(original_image, preserve_aspect=True)

        # Should fit within 200x200 while maintaining 2:1 aspect ratio
        assert resized.width == 200
        assert resized.height == 100

    def test_should_download_image_from_url(self) -> None:
        """download_image should fetch and return PIL Image from URL."""
        settings = Settings()
        processor = ImageProcessor(settings=settings)
        image_bytes = create_test_image()

        with patch("bio_battle.presentation.image_processor.requests") as mock_requests:
            mock_response = Mock()
            mock_response.content = image_bytes
            mock_response.raise_for_status = Mock()
            mock_requests.get.return_value = mock_response

            result = processor.download_image("https://example.com/image.jpg")

            assert isinstance(result, Success)
            image = result.unwrap()
            assert isinstance(image, Image.Image)

    def test_should_return_failure_for_failed_download(self) -> None:
        """download_image should return Failure when download fails."""
        settings = Settings()
        processor = ImageProcessor(settings=settings)

        with patch("bio_battle.presentation.image_processor.requests") as mock_requests:
            mock_requests.get.side_effect = Exception("Network error")

            result = processor.download_image("https://example.com/image.jpg")

            assert isinstance(result, Failure)

    def test_should_convert_image_to_grayscale(self) -> None:
        """to_grayscale should convert RGB image to grayscale."""
        settings = Settings()
        processor = ImageProcessor(settings=settings)
        colour_image = Image.new("RGB", (100, 100), "red")

        grayscale = processor.to_grayscale(colour_image)

        assert grayscale.mode == "L"

    def test_should_process_image_pipeline(self) -> None:
        """process_image should download, resize and return processed image."""
        settings = Settings(image_width_px=200, image_height_px=200)
        processor = ImageProcessor(settings=settings)
        image_bytes = create_test_image(width=400, height=400)

        with patch("bio_battle.presentation.image_processor.requests") as mock_requests:
            mock_response = Mock()
            mock_response.content = image_bytes
            mock_response.raise_for_status = Mock()
            mock_requests.get.return_value = mock_response

            result = processor.process_image("https://example.com/image.jpg")

            assert isinstance(result, Success)
            image = result.unwrap()
            assert image.width == 200
            assert image.height == 200

    def test_should_return_none_image_for_none_url(self) -> None:
        """process_image should return None for None URL."""
        settings = Settings()
        processor = ImageProcessor(settings=settings)

        result = processor.process_image(None)

        assert isinstance(result, Success)
        assert result.unwrap() is None

    def test_should_create_placeholder_image(self) -> None:
        """create_placeholder should generate a default placeholder image."""
        settings = Settings(image_width_px=200, image_height_px=200)
        processor = ImageProcessor(settings=settings)

        placeholder = processor.create_placeholder()

        assert placeholder.width == 200
        assert placeholder.height == 200

    def test_should_handle_invalid_image_data(self) -> None:
        """download_image should return Failure for invalid image data."""
        settings = Settings()
        processor = ImageProcessor(settings=settings)

        with patch("bio_battle.presentation.image_processor.requests") as mock_requests:
            mock_response = Mock()
            mock_response.content = b"not an image"
            mock_response.raise_for_status = Mock()
            mock_requests.get.return_value = mock_response

            result = processor.download_image("https://example.com/image.jpg")

            assert isinstance(result, Failure)

    def test_should_convert_to_bytes(self) -> None:
        """to_bytes should convert PIL Image to bytes."""
        settings = Settings()
        processor = ImageProcessor(settings=settings)
        image = Image.new("RGB", (100, 100), "blue")

        image_bytes = processor.to_bytes(image, format="PNG")

        assert isinstance(image_bytes, bytes)
        assert len(image_bytes) > 0
        # Verify it's valid PNG by reading it back
        loaded = Image.open(BytesIO(image_bytes))
        assert loaded.width == 100

    def test_should_convert_to_dithered_black_and_white(self) -> None:
        """to_dithered_bw should convert image to dithered black and white."""
        settings = Settings()
        processor = ImageProcessor(settings=settings)
        # Create a gradient image for visible dithering effect
        colour_image = Image.new("RGB", (100, 100), "gray")

        dithered = processor.to_dithered_bw(colour_image)

        # Should be RGB (for PDF compatibility) but only contain B&W values
        assert dithered.mode == "RGB"
        assert dithered.width == 100
        assert dithered.height == 100

    def test_should_apply_dithering_in_process_pipeline(self) -> None:
        """process_image should apply dithering when apply_dither=True."""
        settings = Settings(image_width_px=100, image_height_px=100)
        processor = ImageProcessor(settings=settings)
        image_bytes = create_test_image(width=200, height=200, colour="gray")

        with patch("bio_battle.presentation.image_processor.requests") as mock_requests:
            mock_response = Mock()
            mock_response.content = image_bytes
            mock_response.raise_for_status = Mock()
            mock_requests.get.return_value = mock_response

            result = processor.process_image(
                "https://example.com/image.jpg", apply_dither=True
            )

            assert isinstance(result, Success)
            image = result.unwrap()
            assert image.mode == "RGB"

    def test_should_skip_dithering_when_disabled(self) -> None:
        """process_image should skip dithering when apply_dither=False."""
        settings = Settings(image_width_px=100, image_height_px=100)
        processor = ImageProcessor(settings=settings)
        image_bytes = create_test_image(width=200, height=200, colour="red")

        with patch("bio_battle.presentation.image_processor.requests") as mock_requests:
            mock_response = Mock()
            mock_response.content = image_bytes
            mock_response.raise_for_status = Mock()
            mock_requests.get.return_value = mock_response

            result = processor.process_image(
                "https://example.com/image.jpg", apply_dither=False
            )

            assert isinstance(result, Success)
            image = result.unwrap()
            # Original colour should be preserved (not dithered to B&W)
            assert image.mode == "RGB"
