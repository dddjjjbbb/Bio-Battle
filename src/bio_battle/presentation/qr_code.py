"""QR code generation for Bio Battle cards."""

import qrcode
from PIL import Image


def generate_qr_code(url: str, box_size: int = 6) -> Image.Image:
    """Generate a QR code image for the given URL.

    Args:
        url: The URL to encode in the QR code.
        box_size: Size of each QR module box in pixels.

    Returns:
        PIL Image in RGB mode containing the QR code.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=box_size,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)

    image = qr.make_image(fill_color="black", back_color="white")
    return image.convert("RGB")
