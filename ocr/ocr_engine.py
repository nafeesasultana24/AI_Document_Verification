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

    # ✅ ADD: force uint8 for EasyOCR stability
    if image_input.dtype != np.uint8:
        image_input = image_input.astype(np.uint8)

    # NumPy → PIL RGB
    img = Image.fromarray(image_input).convert("RGB")

    # ✅ ADD: ensure minimum resolution (Aadhaar text is tiny)
    if img.width < 800 or img.height < 600:
        img = img.resize((img.width * 2, img.height * 2), Image.BICUBIC)

    # ---------- UPSCALE FOR OCR ----------
    new_width = int(img.width * 1.5)
    new_height = int(img.height * 1.5)
    img = img.resize((new_width, new_height), Image.BICUBIC)

    # ---------- GRAYSCALE & DENOISE ----------
    gray = img.convert("L")
    gray = gray.filter(ImageFilter.MedianFilter(size=3))

    # ✅ ADD: slight brightness normalization
    gray = ImageEnhance.Brightness(gray).enhance(1.1)

    # ---------- CONTRAST & SHARPEN ----------
    gray = ImageOps.autocontrast(gray)
    gray = ImageEnhance.Contrast(gray).enhance(2.0)
    gray = gray.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))

    # ✅ ADD: second gentle sharpening (helps Aadhaar fonts)
    gray = ImageEnhance.Sharpness(gray).enhance(1.4)

    # ---------- ADAPTIVE-LIKE BINARIZATION ----------
    gray_np = np.array(gray)
    mean_val = gray_np.mean()

    # ✅ ADD: clamp threshold to avoid over-binarization
    threshold = max(mean_val - 10, 90)

    binarized = np.where(gray_np > threshold, 255, 0).astype(np.uint8)

    # ---------- BACK TO RGB FOR EasyOCR ----------
    processed = Image.fromarray(binarized).convert("RGB")

    # ✅ ADD: final resize safety (EasyOCR prefers RGB uint8)
    processed = processed.resize(
        (processed.width, processed.height),
        Image.BICUBIC
    )

    return np.array(processed)


def ocr_on_image(image):
    extracted_text = []
    confidences = []

    # ✅ STEP 3: INCREASE OCR RESOLUTION (BEFORE PREPROCESSING)
    pil_image = Image.fromarray(image).convert("RGB")
    pil_image = pil_image.resize(
        (pil_image.width * 2, pil_image.height * 2),
        Image.BICUBIC
    )
    image = np.array(pil_image)

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
        # ✅ ADD: tuned parameters for ID cards
        results = reader.readtext(
            processed,
            detail=1,
            paragraph=False,
            contrast_ths=0.1,
            adjust_contrast=0.5,
            text_threshold=0.6,
            low_text=0.3,
            link_threshold=0.4
        )
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
