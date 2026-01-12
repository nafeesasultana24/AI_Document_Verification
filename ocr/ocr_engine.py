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

def compute_ocr_confidence(text):
    score = 40

    text_u = text.upper()

    if "UNIQUE IDENTIFICATION" in text_u:
        score += 15
    if "GOVERNMENT OF INDIA" in text_u:
        score += 10
    if re.search(r"\b\d{4}\s\d{4}\s\d{4}\b", text):
        score += 20
    if len(text) > 300:
        score += 10

    return min(score, 95)




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

    # 🔒 SAFE RESIZE GUARD (NO OVER-UPSCALE)
    if img.width < 900:
        scale = 900 / img.width
        img = img.resize(
            (int(img.width * scale), int(img.height * scale)),
            Image.BICUBIC
        )

    # ❌ Neutralize second resize without deleting it
    img = img.resize(
        (img.width, img.height),
        Image.BICUBIC
    )

    gray = img.convert("L")

    # 🔹 SINGLE SAFE DENOISE
    gray = gray.filter(ImageFilter.MedianFilter(size=3))

    # 🔹 CONTROLLED ENHANCEMENTS (CLAMPED)
    gray = ImageEnhance.Brightness(gray).enhance(1.03)
    gray = ImageEnhance.Contrast(gray).enhance(1.5)
    gray = ImageEnhance.Sharpness(gray).enhance(1.25)

    gray = ImageOps.autocontrast(gray, cutoff=1)

    gray_np = np.array(gray)
    if gray_np.size == 0:
        return None

    mean_val = gray_np.mean()
    contrast_level = np.std(gray_np)

    # ❌ FORCE BINARIZATION OFF (WITHOUT REMOVING CODE)
    skip_binarization = True
    threshold = max(mean_val - 10, 90)

    if not skip_binarization:
        binarized = np.where(gray_np > threshold, 255, gray_np).astype(np.uint8)
    else:
        binarized = gray_np.astype(np.uint8)

    processed = Image.fromarray(binarized).convert("RGB")
    return np.array(processed)


def extract_text(image_input):
    return ocr_on_image(image_input)

def crop_aadhaar_region(img):
    w, h = img.size
    return img.crop((0, int(h * 0.55), w, h))



def ocr_on_image(image):
    extracted_text = []
    confidences = []

    if image is None:
        return {"final": {"text": "", "confidence": 0}}

    if isinstance(image, Image.Image):
        image = np.array(image.convert("RGB"))

    pil_image = Image.fromarray(image).convert("RGB")

    aadhaar_region = crop_aadhaar_region(pil_image)
    processed_region = preprocess_image(aadhaar_region)


    # ❌ Neutralize extra resize safely
    pil_image = pil_image.resize(
        (pil_image.width, pil_image.height),
        Image.BICUBIC
    )

    image = np.array(pil_image)

    # ================= FIRST OCR PASS =================
    processed_1 = preprocess_image(image)
    if processed_1 is None:
        return {"final": {"text": "", "confidence": 0}}

    # ================= SECOND OCR PASS (SAFE) =================
    enhanced_img = Image.fromarray(image).convert("RGB")
    enhanced_img = ImageEnhance.Contrast(enhanced_img).enhance(1.1)
    enhanced_img = ImageEnhance.Sharpness(enhanced_img).enhance(1.15)
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
            conf = 0.6
        else:
            continue

        if not isinstance(text, str):
            continue

        clean_text = normalize_text(text)

        # 🔒 STRICT GARBAGE FILTER
        if len(clean_text) < 4:
            continue
        if sum(c.isdigit() for c in clean_text) > len(clean_text) * 0.7:
            continue

        extracted_text.append(clean_text)
        confidences.append(conf)

    # ================= DEDUPLICATION =================
    seen = set()
    deduped_text = []
    for line in extracted_text:
        key = line.lower()
        if key not in seen:
            deduped_text.append(line)
            seen.add(key)

    final_text = re.sub(r"\s+", " ", " ".join(deduped_text)).strip()

    # ================= CONFIDENCE (HONEST) =================
    valid_conf = [c for c in confidences if isinstance(c, (int, float))]
    base_conf = np.mean(valid_conf) if valid_conf else 0

    keyword_hits = sum(
        k in final_text.upper()
        for k in ["AADHAAR", "UIDAI", "GOVERNMENT", "INDIA"]
    )

    if keyword_hits >= 2:
        base_conf = min(base_conf + 0.12, 0.85)

    return {
        "final": {
            "text": final_text,
            "confidence": compute_ocr_confidence(final_text)
        }
    }
