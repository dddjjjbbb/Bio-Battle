"""Image processing for Bio Battle cards."""

from io import BytesIO

import requests
from PIL import Image
from returns.result import Failure, Result, Success

from bio_battle.config.settings import Settings
from bio_battle.domain.errors import FetchError

# User-Agent for downloading images from Wikimedia Commons
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


class ImageProcessingError(FetchError):
    """Error during image processing."""

    pass


class ImageProcessor:
    """Handles image downloading, resizing, and processing."""

    def __init__(self, settings: Settings) -> None:
        """Initialise processor with settings.

        Args:
            settings: Application settings containing image dimensions.
        """
        self._settings = settings
        self._target_width = settings.image_width_px
        self._target_height = settings.image_height_px
        self._headers = {"User-Agent": USER_AGENT}

    def download_image(self, url: str) -> Result[Image.Image, ImageProcessingError]:
        """Download an image from a URL.

        Args:
            url: The URL of the image to download.

        Returns:
            Result containing PIL Image or ImageProcessingError.
        """
        try:
            response = requests.get(
                url,
                timeout=self._settings.wikipedia_api_timeout,
                headers=self._headers,
            )
            response.raise_for_status()

            image = Image.open(BytesIO(response.content))
            # Convert to RGB if necessary
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
            return Success(image)
        except Exception as e:
            return Failure(
                ImageProcessingError(
                    message=f"Failed to download image: {e}",
                    identifier=url,
                )
            )

    def resize_image(
        self,
        image: Image.Image,
        preserve_aspect: bool = False,
    ) -> Image.Image:
        """Resize an image to target dimensions.

        Args:
            image: The PIL Image to resize.
            preserve_aspect: If True, maintain aspect ratio and fit within target.

        Returns:
            Resized PIL Image.
        """
        if preserve_aspect:
            image.thumbnail(
                (self._target_width, self._target_height),
                Image.Resampling.LANCZOS,
            )
            return image
        else:
            return image.resize(
                (self._target_width, self._target_height),
                Image.Resampling.LANCZOS,
            )

    def to_grayscale(self, image: Image.Image) -> Image.Image:
        """Convert an image to grayscale.

        Args:
            image: The PIL Image to convert.

        Returns:
            Grayscale PIL Image.
        """
        return image.convert("L")

    def to_dithered_bw(self, image: Image.Image) -> Image.Image:
        """Convert an image to dithered black and white.

        Uses Floyd-Steinberg dithering to create an old-school
        halftone effect using only black and white pixels.

        Args:
            image: The PIL Image to convert.

        Returns:
            Dithered black and white PIL Image (converted back to RGB for PDF).
        """
        # First convert to grayscale
        grayscale = image.convert("L")

        # Apply Floyd-Steinberg dithering (convert to 1-bit with dithering)
        dithered = grayscale.convert("1", dither=Image.Dither.FLOYDSTEINBERG)

        # Convert back to RGB for PDF compatibility
        return dithered.convert("RGB")

    def process_image(
        self,
        url: str | None,
        apply_dither: bool = True,
    ) -> Result[Image.Image | None, ImageProcessingError]:
        """Process an image: download, resize, and prepare for card.

        Args:
            url: The URL of the image, or None.
            apply_dither: If True, convert to dithered black and white.

        Returns:
            Result containing processed PIL Image, None, or ImageProcessingError.
        """
        if url is None:
            return Success(None)

        download_result = self.download_image(url)
        if isinstance(download_result, Failure):
            return download_result

        image = download_result.unwrap()
        resized = self.resize_image(image)

        if apply_dither:
            resized = self.to_dithered_bw(resized)

        return Success(resized)

    def create_placeholder(self) -> Image.Image:
        """Create a placeholder image for cards without images.

        Returns:
            A placeholder PIL Image.
        """
        placeholder = Image.new(
            "RGB",
            (self._target_width, self._target_height),
            (200, 200, 200),  # Light grey
        )
        return placeholder

    def to_bytes(self, image: Image.Image, format: str = "PNG") -> bytes:
        """Convert a PIL Image to bytes.

        Args:
            image: The PIL Image to convert.
            format: The image format (PNG, JPEG, etc.).

        Returns:
            Image data as bytes.
        """
        buffer = BytesIO()
        image.save(buffer, format=format)
        return buffer.getvalue()
