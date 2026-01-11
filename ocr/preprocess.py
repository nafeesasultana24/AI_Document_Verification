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

    # Median filter to reduce noise
    gray = gray.filter(ImageFilter.MedianFilter(size=3))

    # 🔹 ADD: Slight brightness boost (OCR stability)
    gray = ImageEnhance.Brightness(gray).enhance(1.1)

    # ---------------- CONTRAST & SHARPEN ----------------
    gray = ImageOps.autocontrast(gray)

    # Extra contrast boost for OCR stability
    gray = ImageEnhance.Contrast(gray).enhance(2.0)

    # Optional sharpening to enhance text edges
    gray = gray.filter(
        ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3)
    )

    # 🔹 ADD: Second gentle sharpen for Aadhaar fonts
    gray = ImageEnhance.Sharpness(gray).enhance(1.5)

    # ---------------- ADAPTIVE-LIKE BINARIZATION ----------------
    gray_np = np.array(gray)

    # 🔹 ADD: Ensure numeric stability
    if gray_np.size == 0:
        raise ValueError("Empty image after preprocessing")

    mean_val = gray_np.mean()

    # 🔹 ADD: Clamp threshold to avoid over-binarization
    threshold = max(mean_val - 10, 90)

    binarized = np.where(gray_np > threshold, 255, gray_np).astype(np.uint8)
    # ⚠️ IMPORTANT CHANGE:
    # Instead of hard 0 (which destroys thin text),
    # we keep original gray values for darker pixels

    # ---------------- CONVERT BACK TO RGB ----------------
    processed = Image.fromarray(binarized).convert("RGB")

    # 🔹 ADD: Final resize safety for PaddleOCR / EasyOCR
    processed = processed.resize(
        (processed.width, processed.height),
        Image.BICUBIC
    )

    # 🔹 ADD: Return BOTH formats safely
    # EasyOCR → NumPy
    # Streamlit display → PIL
    return np.array(processed), processed
