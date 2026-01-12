import os
import unicodedata
import numpy as np
from PIL import Image, ImageFilter, ImageOps, ImageEnhance
import easyocr
import re
import streamlit as st

# ===== STREAMLIT SAFE ENV =====
os.environ["OMP_NUM_THREADS"] = "4"
os.environ["CUDA_VISIBLE_DEVICES"] = ""

# ✅ LOAD ENGINES
paddle_ocr = None

@st.cache_resource(show_spinner="Loading OCR engine (first run only)...")
def load_easyocr_reader():
    return easyocr.Reader(
        ['en'],
        gpu=False,
        model_storage_directory="./models",
        download_enabled=True
    )

def get_reader():
    return load_easyocr_reader()


def normalize_text(text):
    if not text:
        return ""

    text = unicodedata.normalize("NFKC", text)

    replacements = {
        "1ndia": "India",
        "1dentification": "Identification",
        "MA1E": "MALE",
        "P1N": "PIN",
        "5ub": "Sub",
        "Disuict": "District",
        "Govemment": "Government"
    }

    for k, v in replacements.items():
        text = text.replace(k, v)

    text = re.sub(r"[^\w\s:/\-\.]", " ", text)
    return text.replace("\n", " ").strip()


# ================= CONFIDENCE (HONEST) =================
def compute_ocr_confidence(text):
    score = 40
    text_u = text.upper()

    if "UNIQUE IDENTIFICATION" in text_u:
        score += 15
    if "GOVERNMENT OF INDIA" in text_u:
        score += 10
    if re.search(r"\b\d{4}\s?\d{4}\s?\d{4}\b", text):
        score += 20
    if re.search(r"\b[A-Z]{5}\d{4}[A-Z]\b", text):
        score += 20
    if len(text) > 300:
        score += 10

    return min(score, 95)


# ================= IMAGE PREPROCESS =================
def preprocess_image(image_input):
    if image_input is None:
        return None

    if isinstance(image_input, Image.Image):
        image_input = np.array(image_input.convert("RGB"))

    if not isinstance(image_input, np.ndarray):
        return None

    if image_input.dtype != np.uint8:
        image_input = image_input.astype(np.uint8)

    img = Image.fromarray(image_input).convert("RGB")

    if img.width == 0 or img.height == 0:
        return None

    if img.width < 900:
        scale = 900 / img.width
        img = img.resize(
            (int(img.width * scale), int(img.height * scale)),
            Image.BICUBIC
        )

    img = img.resize((img.width, img.height), Image.BICUBIC)

    gray = img.convert("L")
    gray = gray.filter(ImageFilter.MedianFilter(size=3))
    gray = ImageEnhance.Brightness(gray).enhance(1.03)
    gray = ImageEnhance.Contrast(gray).enhance(1.5)
    gray = ImageEnhance.Sharpness(gray).enhance(1.25)
    gray = ImageOps.autocontrast(gray, cutoff=1)

    gray_np = np.array(gray)
    if gray_np.size == 0:
        return None

    processed = Image.fromarray(gray_np).convert("RGB")
    return np.array(processed)


# ================= REGION CROPPERS =================
def crop_aadhaar_region(img):
    w, h = img.size
    return img.crop((0, int(h * 0.55), w, h))

def crop_pan_region(img):
    w, h = img.size
    return img.crop((0, 0, w, int(h * 0.45)))


# ================= AUTO DOCUMENT TYPE DETECTOR =================
def detect_document_type(text):
    t = text.upper()

    if re.search(r"\b[A-Z]{5}\d{4}[A-Z]\b", t):
        return "PAN"

    if re.search(r"\b\d{4}\s?\d{4}\s?\d{4}\b", t) and (
        "UIDAI" in t or "AADHAAR" in t or "UNIQUE IDENTIFICATION" in t
    ):
        return "AADHAAR"

    return "UNKNOWN"


# ================= OCR CORE =================
def extract_text(image_input):
    return ocr_on_image(image_input)


def ocr_on_image(image):
    extracted_text = []
    confidences = []

    if image is None:
        return {"final": {"text": "", "confidence": 0}}

    if isinstance(image, Image.Image):
        image = np.array(image.convert("RGB"))

    pil_image = Image.fromarray(image).convert("RGB")

    # 🔍 FIRST PASS — LIGHT OCR FOR TYPE DETECTION
    preview_img = preprocess_image(pil_image)
    preview_text = ""
    try:
        preview_results = get_reader().readtext(preview_img, detail=0)
        preview_text = " ".join(preview_results)
    except Exception:
        pass

    doc_type = detect_document_type(preview_text)

    # 🎯 AUTO-SELECT OCR REGION
    if doc_type == "AADHAAR":
        region_img = crop_aadhaar_region(pil_image)
    elif doc_type == "PAN":
        region_img = crop_pan_region(pil_image)
    else:
        region_img = pil_image

    processed_region = preprocess_image(region_img)

    # ================= REGION OCR =================
    try:
        region_results = get_reader().readtext(
            processed_region,
            detail=1,
            paragraph=True
        )
    except Exception:
        region_results = []

    for item in region_results:
        if len(item) == 3:
            _, text, conf = item
        else:
            continue

        clean_text = normalize_text(text)
        if len(clean_text) < 4:
            continue

        extracted_text.append(clean_text)
        confidences.append(conf)

    # ================= FINAL MERGE =================
    final_text = re.sub(r"\s+", " ", " ".join(extracted_text)).strip()

    return {
        "final": {
            "text": final_text,
            "confidence": compute_ocr_confidence(final_text)
        }
    }
