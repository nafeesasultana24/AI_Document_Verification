import os
import numpy as np
from PIL import Image, ImageFilter, ImageOps, ImageEnhance


def preprocess_image(image_input):
    # ================= INPUT HANDLING =================
    if isinstance(image_input, np.ndarray):
        if image_input.dtype != np.uint8:
            image_input = image_input.astype(np.uint8)
        img = Image.fromarray(image_input)

    elif isinstance(image_input, str):
        if not os.path.exists(image_input):
            raise ValueError(f"Image not found at path: {image_input}")
        img = Image.open(image_input)

    else:
        raise ValueError("Unsupported image input")

    img = img.convert("RGB")

    if img.width == 0 or img.height == 0:
        raise ValueError("Invalid image dimensions")

    # ================= RESOLUTION SAFETY =================
    # Upscale ONLY if image is genuinely small
    if img.width < 1000:
        scale = 1000 / img.width
        img = img.resize(
            (int(img.width * scale), int(img.height * scale)),
            Image.BICUBIC
        )

    # ================= GRAYSCALE =================
    gray = img.convert("L")

    # ================= NOISE REDUCTION (SAFE) =================
    # Single median filter — no double denoise
    gray = gray.filter(ImageFilter.MedianFilter(size=3))

    # ================= CONTRAST (CONTROLLED) =================
    gray = ImageEnhance.Contrast(gray).enhance(1.6)

    # ================= BRIGHTNESS (MINIMAL) =================
    gray = ImageEnhance.Brightness(gray).enhance(1.05)

    # ================= SHARPEN (ONCE ONLY) =================
    gray = ImageEnhance.Sharpness(gray).enhance(1.3)

    # ================= AUTOCONTRAST (SAFE) =================
    gray = ImageOps.autocontrast(gray, cutoff=1)

    # ================= NO BINARIZATION =================
    # Aadhaar UIDAI font is thin → binarization destroys it
    processed = gray

    # ================= FINAL FORMAT =================
    processed = processed.convert("RGB")

    # ================= RETURN =================
    # EasyOCR → numpy
    # Streamlit → PIL
    return np.array(processed), processed
