import os
import cv2
import unicodedata
import numpy as np
import re
import math

# ===== FIX FOR WINDOWS CPU CRASH =====
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["OMP_NUM_THREADS"] = "4"

from paddleocr import PaddleOCR

# Load OCR model once
ocr_model = PaddleOCR(
    use_angle_cls=True,
    lang="en",            # base language  
    use_gpu=False,
    det=True,
    rec=True,
    cls=True
)

def normalize_text(text):
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\n", " ")

def preprocess_image(image):
    """
    Advanced preprocessing for noisy scanned documents
    """

    # Safety check
    if image is None or not isinstance(image, np.ndarray):
        return None

    # 1️⃣ Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 2️⃣ Noise removal (preserves text edges)
    gray = cv2.fastNlMeansDenoising(gray, h=30)

    # 3️⃣ Contrast enhancement (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    # 4️⃣ Adaptive thresholding (handles uneven lighting)
    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        15
    )

    # 5️⃣ Deskew (alignment correction)
    coords = np.column_stack(np.where(thresh > 0))
    angle = 0.0

    if len(coords) > 0:
        rect = cv2.minAreaRect(coords)
        angle = rect[-1]

        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        (h, w) = thresh.shape[:2]
        center = (w // 2, h // 2)

        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        thresh = cv2.warpAffine(
            thresh,
            M,
            (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )

    return thresh

def ocr_on_image(image):
    extracted_text = []
    confidences = []
    # ✅ APPLY PREPROCESSING HERE (THIS IS THE FIX)
    processed = preprocess_image(image)
    if processed is None:
        processed = image

    try:
        result = ocr_model.ocr(image, cls=True)
    except Exception as e:
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

            text = word_info[1][0]
            conf = word_info[1][1]

            # ✅ SAFETY CHECKS
            if text is None:
                continue
            if not isinstance(text, str):
                continue
            if text.strip() == "":
                continue

            extracted_text.append(text)
            confidences.append(conf)

    # ✅ FILTER AGAIN (DOUBLE SAFETY)
    extracted_text = [t for t in extracted_text if isinstance(t, str)]

    final_text = " ".join(extracted_text).strip()
    avg_conf = round((sum(confidences) / len(confidences)) * 100, 2) if confidences else 0

    return {
        "final": {
            "text": final_text,
            "confidence": avg_conf
        }
    }
