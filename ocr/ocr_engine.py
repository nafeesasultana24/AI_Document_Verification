import os
import unicodedata
import numpy as np
from PIL import Image, ImageFilter, ImageOps, ImageEnhance
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
    Document-optimized (Aadhaar / PAN / certificates)
    """

    # ---------- INPUT HANDLING ----------
    if image_input is None or not isinstance(image_input, np.ndarray):
        return None

    # Force uint8 for EasyOCR stability
    if image_input.dtype != np.uint8:
        image_input = image_input.astype(np.uint8)

    # NumPy → PIL RGB
    img = Image.fromarray(image_input).convert("RGB")

    # Ensure minimum resolution
    if img.width < 800 or img.height < 600:
        img = img.resize((img.width * 2, img.height * 2), Image.BICUBIC)

    # ---------- UPSCALE ----------
    img = img.resize(
        (int(img.width * 1.5), int(img.height * 1.5)),
        Image.BICUBIC
    )

    # ---------- GRAYSCALE & DENOISE ----------
    gray = img.convert("L")
    gray = gray.filter(ImageFilter.MedianFilter(size=3))
    gray = ImageEnhance.Brightness(gray).enhance(1.1)

    # ---------- CONTRAST & SHARPEN ----------
    gray = ImageOps.autocontrast(gray)
    gray = ImageEnhance.Contrast(gray).enhance(2.0)
    gray = gray.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
    gray = ImageEnhance.Sharpness(gray).enhance(1.4)

    # ---------- CONDITIONAL BINARIZATION ----------
    gray_np = np.array(gray)
    mean_val = gray_np.mean()
    contrast_level = np.std(gray_np)

    skip_binarization = contrast_level > 45
    threshold = max(mean_val - 10, 90)

    if not skip_binarization:
        binarized = np.where(gray_np > threshold, 255, 0).astype(np.uint8)
    else:
        binarized = gray_np.astype(np.uint8)

    # ---------- BACK TO RGB ----------
    processed = Image.fromarray(binarized).convert("RGB")
    return np.array(processed)


def ocr_on_image(image):
    extracted_text = []
    confidences = []

    # Increase resolution BEFORE preprocessing
    pil_image = Image.fromarray(image).convert("RGB")
    pil_image = pil_image.resize(
        (pil_image.width * 2, pil_image.height * 2),
        Image.BICUBIC
    )
    image = np.array(pil_image)

    processed = preprocess_image(image)
    if processed is None:
        return {"final": {"text": "", "confidence": 0}}

    try:
        # ✅ EasyOCR document-tuned execution
        results = reader.readtext(
            processed,
            detail=1,
            paragraph=True,
            decoder="beamsearch",
            text_threshold=0.7,
            low_text=0.4,
            link_threshold=0.4,
            contrast_ths=0.1,
            adjust_contrast=0.5,
            mag_ratio=2.0
        )
    except Exception:
        return {"final": {"text": "", "confidence": 0}}

    # ✅ SAFE RESULT HANDLING (paragraph mode compatible)
    for item in results:
        if len(item) == 3:
            box, text, conf = item
        elif len(item) == 2:
            box, text = item
            conf = 0.8  # default confidence for paragraph mode
        else:
            continue

        if text and isinstance(text, str):
            clean_text = normalize_text(text)
            if clean_text:
                extracted_text.append(clean_text)
                confidences.append(conf)

    final_text = " ".join(extracted_text)

    # ✅ SAFE CONFIDENCE CALCULATION
    valid_conf = [c for c in confidences if isinstance(c, (int, float))]
    avg_conf = round(
        ((np.mean(valid_conf) + np.median(valid_conf)) / 2) * 100,
        2
    ) if valid_conf else 0

    return {
        "final": {
            "text": final_text,
            "confidence": avg_conf
        }
    }
