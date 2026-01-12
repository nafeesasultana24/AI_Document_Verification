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

    image = np.array(pil_image)

    # ================= FIRST OCR PASS =================
    processed_1 = preprocess_image(image)
    if processed_1 is None:
        return {"final": {"text": "", "confidence": 0}}

    # ================= SECOND OCR PASS (ENHANCED) =================
    enhanced_img = Image.fromarray(image).convert("RGB")
    enhanced_img = ImageEnhance.Contrast(enhanced_img).enhance(1.3)
    enhanced_img = ImageEnhance.Sharpness(enhanced_img).enhance(1.3)
    enhanced_img = np.array(enhanced_img)
    processed_2 = preprocess_image(enhanced_img)

    reader = get_reader()

    all_results = []

    try:
        all_results.extend(reader.readtext(processed_1, detail=1))
        if processed_2 is not None:
            all_results.extend(reader.readtext(processed_2, detail=1))
    except Exception:
        return {"final": {"text": "", "confidence": 0}}

    # ================= MERGE RESULTS =================
    for item in all_results:
        if len(item) == 3:
            _, text, conf = item
        elif len(item) == 2:
            _, text = item
            conf = 0.7
        else:
            continue

        if text and isinstance(text, str):
            clean_text = normalize_text(text)
            if len(clean_text) < 4 and not any(c.isdigit() for c in clean_text):
                continue
            extracted_text.append(clean_text)
            confidences.append(conf)

    # Deduplicate intelligently
    seen = set()
    deduped_text = []
    for line in extracted_text:
        key = line.lower()
        if key not in seen:
            deduped_text.append(line)
            seen.add(key)

    final_text = re.sub(r"\s+", " ", " ".join(deduped_text)).strip()

    # ================= CONFIDENCE BOOST (SAFE) =================
    valid_conf = [c for c in confidences if isinstance(c, (int, float))]
    base_conf = ((np.mean(valid_conf) + np.median(valid_conf)) / 2) if valid_conf else 0

    # 🔹 Dual-pass OCR confidence boost
    boosted_conf = min(base_conf * 1.25, 0.92)

    return {
        "final": {
            "text": final_text,
            "confidence": round(boosted_conf * 100, 2)
        }
    }
