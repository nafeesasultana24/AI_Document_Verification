import os
import numpy as np
from PIL import Image, ImageFilter, ImageOps, ImageEnhance

def preprocess_image(image_path):
    # -------- Path validation --------
    if not isinstance(image_path, str):
        # ✅ ADDED: allow NumPy image input (Streamlit)
        if isinstance(image_path, np.ndarray):
            img = Image.fromarray(image_path)
        else:
            raise ValueError("Expected image file path or NumPy array")
    else:
        if not os.path.exists(image_path):
            raise ValueError(f"Image not found at path: {image_path}")

        # -------- Read image (PIL) --------
        img = Image.open(image_path).convert("RGB")

    # -------- Resize for better OCR (1.5x, bicubic) --------
    new_width = int(img.width * 1.5)
    new_height = int(img.height * 1.5)
    img = img.resize((new_width, new_height), Image.BICUBIC)

    # -------- Convert to grayscale --------
    gray = img.convert("L")

    # -------- Noise removal (bilateral-like smoothing) --------
    gray = gray.filter(ImageFilter.MedianFilter(size=3))

    # -------- Improve contrast --------
    gray = ImageOps.autocontrast(gray)

    # ✅ ADDED: extra contrast boost (OCR stability)
    gray = ImageEnhance.Contrast(gray).enhance(2.0)

    # -------- Adaptive-like binarization (NumPy) --------
    gray_np = np.array(gray)

    # simple adaptive threshold approximation
    mean = gray_np.mean()
    processed = np.where(gray_np > mean - 10, 255, 0).astype(np.uint8)

    # ✅ ADDED: convert back to RGB for PaddleOCR
    processed = Image.fromarray(processed).convert("RGB")
    processed = np.array(processed)

    return processed
