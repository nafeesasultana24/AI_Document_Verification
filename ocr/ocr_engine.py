import os
import unicodedata
import numpy as np
from PIL import Image, ImageFilter, ImageOps
import math
import easyocr

# ===== STREAMLIT SAFE ENV =====
os.environ["OMP_NUM_THREADS"] = "4"

# ❌ DISABLED (DO NOT REMOVE LINE – prevents crash)
PaddleOCR = None

# ✅ Load EasyOCR ONCE
reader = easyocr.Reader(['en'], gpu=False)


def normalize_text(text):
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    return text.replace("\n", " ").strip()


def preprocess_image(image):
    """
    Streamlit-safe preprocessing using PIL + NumPy only
    """

    if image is None or not isinstance(image, np.ndarray):
        return None

    # NumPy → PIL
    img = Image.fromarray(image).convert("L")

    # Noise reduction
    img = img.filter(ImageFilter.MedianFilter(size=3))

    # Contrast enhancement
    img = ImageOps.autocontrast(img)

    # Thresholding (OCR-friendly)
    img = img.point(lambda x: 255 if x > 140 else 0)

    # Convert back to RGB NumPy (EasyOCR requirement)
    img = img.convert("RGB")
    return np.array(img)


def ocr_on_image(image):
    extracted_text = []
    confidences = []

    processed = preprocess_image(image)
    if processed is None:
        return {
            "final": {
                "text": "",
                "confidence": 0
            }
        }

    try:
        # ✅ EASYOCR EXECUTION
        results = reader.readtext(processed)
    except Exception:
        return {
            "final": {
                "text": "",
                "confidence": 0
            }
        }

    for box, text, conf in results:
        if text and isinstance(text, str):
            clean_text = normalize_text(text)
            if clean_text:
                extracted_text.append(clean_text)
                confidences.append(conf)

    final_text = " ".join(extracted_text)
    avg_conf = round(float(np.mean(confidences)) * 100, 2) if confidences else 0

    return {
        "final": {
            "text": final_text,
            "confidence": avg_conf
        }
    }
