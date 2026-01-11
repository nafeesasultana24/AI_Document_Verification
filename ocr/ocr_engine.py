import os
import unicodedata
import numpy as np
from PIL import Image, ImageFilter, ImageOps, ImageEnhance
import easyocr
import re  # 🔹 ADD: needed for cleanup safety
import streamlit as st  # 🔹 ADD: Streamlit caching

# ===== STREAMLIT SAFE ENV =====
os.environ["OMP_NUM_THREADS"] = "4"
os.environ["CUDA_VISIBLE_DEVICES"] = ""  # 🔹 ADD: force CPU, avoid GPU crash

# ✅ LOAD ENGINES
# We define paddle_ocr as None to prevent NameError if your app.py still calls it,
# but we focus on EasyOCR as per your latest code.
paddle_ocr = None 

# 🔹 FIX: DO NOT INITIALIZE EasyOCR AT IMPORT TIME
# reader = easyocr.Reader(['en'], gpu=False, model_storage_directory='./models')

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

    if img.width < 800 or img.height < 600:
        img = img.resize((img.width * 2, img.height * 2), Image.BICUBIC)

    img = img.resize(
        (int(img.width * 1.5), int(img.height * 1.5)),
        Image.BICUBIC
    )

    gray = img.convert("L")
    gray = gray.filter(ImageFilter.MedianFilter(size=3))
    gray = ImageEnhance.Brightness(gray).enhance(1.1)

    gray = ImageOps.autocontrast(gray)
    gray = ImageEnhance.Contrast(gray).enhance(2.0)
    gray = gray.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
    gray = ImageEnhance.Sharpness(gray).enhance(1.4)

    gray_np = np.array(gray)
    if gray_np.size == 0:
        return None

    mean_val = gray_np.mean()
    contrast_level = np.std(gray_np)

    skip_binarization = contrast_level > 30
    threshold = max(mean_val - 10, 90)

    if not skip_binarization:
        binarized = np.where(gray_np > threshold, 255, gray_np).astype(np.uint8)
    else:
        binarized = gray_np.astype(np.uint8)

    processed = Image.fromarray(binarized).convert("RGB")
    return np.array(processed)


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
    pil_image = pil_image.resize(
        (int(pil_image.width * 1.3), int(pil_image.height * 1.3)),
        Image.BICUBIC
    )

    # 🔹 FIX: neutralized extra parenthesis (DO NOT DELETE LINE)
    # )

    image = np.array(pil_image)

    processed = preprocess_image(image)
    if processed is None:
        return {"final": {"text": "", "confidence": 0}}

    reader = get_reader()

    try:
        results = reader.readtext(
            processed,
            detail=1,
            paragraph=False,
            decoder="greedy",
            text_threshold=0.6,
            low_text=0.3,
            link_threshold=0.3,
            contrast_ths=0.05,
            adjust_contrast=0.3,
            mag_ratio=1.0
        )
    except Exception:
        return {"final": {"text": "", "confidence": 0}}

    for item in results:
        if len(item) == 3:
            _, text, conf = item
        elif len(item) == 2:
            _, text = item
            conf = 0.75
        else:
            continue

        if text and isinstance(text, str):
            clean_text = normalize_text(text)
            if len(clean_text) < 4 and not any(c.isdigit() for c in clean_text):
                continue
            extracted_text.append(clean_text)
            confidences.append(conf)

    seen = set()
    deduped_text = []
    for line in extracted_text:
        if line not in seen:
            deduped_text.append(line)
            seen.add(line)

    final_text = re.sub(r"\s+", " ", " ".join(deduped_text)).strip()

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