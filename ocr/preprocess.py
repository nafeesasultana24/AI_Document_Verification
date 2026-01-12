import os
import numpy as np
from PIL import Image, ImageFilter, ImageOps, ImageEnhance


def preprocess_image(image_input):
    # ---------------- INPUT HANDLING ----------------
    # Accept NumPy array or file path
    if isinstance(image_input, np.ndarray):
        # 🔹 ADD: Ensure uint8 (Streamlit uploads sometimes break this)
        if image_input.dtype != np.uint8:
            image_input = image_input.astype(np.uint8)
        img = Image.fromarray(image_input).convert("RGB")

    elif isinstance(image_input, str):
        if not os.path.exists(image_input):
            raise ValueError(f"Image not found at path: {image_input}")
        img = Image.open(image_input).convert("RGB")

    else:
        raise ValueError("Unsupported image input")

    # 🔹 ADD: Safety check for corrupted images
    if img.width == 0 or img.height == 0:
        raise ValueError("Invalid image dimensions")

    # 🔹 ADD: Ensure minimum resolution (helps small Aadhaar text)
    if img.width < 800 or img.height < 600:
        img = img.resize(
            (img.width * 2, img.height * 2),
            Image.BICUBIC
        )

    # ---------------- RESIZE FOR OCR ----------------
    # Mild upscale helps OCR detect small fonts
    new_width = int(img.width * 1.5)
    new_height = int(img.height * 1.5)
    img = img.resize((new_width, new_height), Image.BICUBIC)

    # ---------------- GRAYSCALE & DENOISE ----------------
    gray = img.convert("L")

    # 🔹 IMPROVED: double denoise pass (safe for Aadhaar)
    gray = gray.filter(ImageFilter.MedianFilter(size=3))
    gray = gray.filter(ImageFilter.SMOOTH_MORE)

    # 🔹 ADD: Slight brightness boost (OCR stability)
    gray = ImageEnhance.Brightness(gray).enhance(1.15)

    # ---------------- CONTRAST & SHARPEN ----------------
    # 🔹 IMPROVED: safer autocontrast with cutoff
    gray = ImageOps.autocontrast(gray, cutoff=2)

    # Extra contrast boost for OCR stability
    gray = ImageEnhance.Contrast(gray).enhance(2.2)

    # Optional sharpening to enhance text edges
    gray = gray.filter(
        ImageFilter.UnsharpMask(radius=1.2, percent=170, threshold=3)
    )

    # 🔹 ADD: Second gentle sharpen for Aadhaar fonts
    gray = ImageEnhance.Sharpness(gray).enhance(1.6)

    # ---------------- OCR-SAFE BINARIZATION ----------------
    gray_np = np.array(gray)

    # 🔹 ADD: Ensure numeric stability
    if gray_np.size == 0:
        raise ValueError("Empty image after preprocessing")

    mean_val = gray_np.mean()

    # 🔹 IMPROVED: dynamic threshold window (no hard clipping)
    threshold_low = max(mean_val - 20, 85)
    threshold_high = min(mean_val + 40, 220)

    # 🔹 IMPORTANT:
    # Keep grayscale for darker pixels → avoids losing thin UIDAI font
    binarized = np.where(
        gray_np > threshold_high,
        255,
        np.where(gray_np < threshold_low, gray_np, gray_np)
    ).astype(np.uint8)

    # ---------------- FINAL OCR STABILIZATION ----------------
    processed = Image.fromarray(binarized)

    # 🔹 ADD: gentle final contrast normalization
    processed = ImageEnhance.Contrast(processed).enhance(1.1)

    # 🔹 ADD: convert back to RGB (EasyOCR safe)
    processed = processed.convert("RGB")

    # 🔹 ADD: Final resize safety for PaddleOCR / EasyOCR
    processed = processed.resize(
        (processed.width, processed.height),
        Image.BICUBIC
    )

    # 🔹 ADD: Return BOTH formats safely
    # EasyOCR → NumPy
    # Streamlit display → PIL
    return np.array(processed), processed
