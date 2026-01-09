import os
import unicodedata
import numpy as np
from PIL import Image, ImageFilter, ImageOps, ImageEnhance
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


def preprocess_image(image_input):
    """
    Streamlit-safe preprocessing using PIL + NumPy only
    Step 2 style: upscale, contrast, denoise, threshold
    """

    # ---------- INPUT HANDLING ----------
    if image_input is None or not isinstance(image_input, np.ndarray):
        return None

    # NumPy → PIL RGB
    img = Image.fromarray(image_input).convert("RGB")

    # ---------- UPSCALE FOR OCR ----------
    new_width = int(img.width * 1.5)
    new_height = int(img.height * 1.5)
    img = img.resize((new_width, new_height), Image.BICUBIC)

    # ---------- GRAYSCALE & DENOISE ----------
    gray = img.convert("L")
    gray = gray.filter(ImageFilter.MedianFilter(size=3))

    # ---------- CONTRAST & SHARPEN ----------
    gray = ImageOps.autocontrast(gray)
    gray = ImageEnhance.Contrast(gray).enhance(2.0)
    gray = gray.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))

    # ---------- ADAPTIVE-LIKE BINARIZATION ----------
    gray_np = np.array(gray)
    mean_val = gray_np.mean()
    binarized = np.where(gray_np > mean_val - 10, 255, 0).astype(np.uint8)

    # ---------- BACK TO RGB FOR EasyOCR ----------
    processed = Image.fromarray(binarized).convert("RGB")
    return np.array(processed)


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
