import os
import unicodedata
import numpy as np
from PIL import Image, ImageFilter, ImageOps
import math

# ===== FIX FOR WINDOWS CPU CRASH =====
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["OMP_NUM_THREADS"] = "4"

from paddleocr import PaddleOCR

# Load OCR model once
ocr_model = PaddleOCR(
    use_angle_cls=True,
    lang="en"
)


def normalize_text(text):
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    return text.replace("\n", " ").strip()


def preprocess_image(image):
    """
    Streamlit-safe preprocessing using PIL + NumPy only
    """

    # Expect NumPy image (RGB)
    if image is None or not isinstance(image, np.ndarray):
        return None

    # Convert NumPy → PIL
    img = Image.fromarray(image).convert("L")

    # Noise reduction
    img = img.filter(ImageFilter.MedianFilter(size=3))

    # Contrast enhancement
    img = ImageOps.autocontrast(img)

    # Simple thresholding
    img = img.point(lambda x: 255 if x > 140 else 0, mode="1")

    # Convert back to NumPy
    return np.array(img)


def ocr_on_image(image):
    extracted_text = []
    confidences = []

    processed = preprocess_image(image)
    if processed is None:
        processed = image

    try:
        result = ocr_model.ocr(processed, cls=True)
    except Exception:
        return {
            "final": {
                "text": "",
                "confidence": 0
            }
        }

    for line in result:
        if not line:
            continue

        for word_info in line:
            if len(word_info) < 2:
                continue

            text = normalize_text(word_info[1][0])
            conf = word_info[1][1]

            if text.strip():
                extracted_text.append(text)
                confidences.append(conf)

    final_text = " ".join(extracted_text).strip()
    avg_conf = round((sum(confidences) / len(confidences)) * 100, 2) if confidences else 0

    return {
        "final": {
            "text": final_text,
            "confidence": avg_conf
        }
    }
