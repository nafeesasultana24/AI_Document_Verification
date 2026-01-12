import re
import unicodedata
import streamlit as st

from verification.utils import verhoeff_check
from verification.classifier import classify_document
from verification.field_extractor import extract_fields
from verification.field_validator import validate_fields
from verification.field_confidence import calculate_field_confidence


# -------------------------------
# TEXT NORMALIZATION
# -------------------------------
def normalize_text(text):
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = text.upper()
    text = re.sub(r"[^A-Z0-9]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def clean_ocr_text(text):
    if not text:
        return ""

    lines = re.split(r"[.\n]", text)
    clean_lines = []

    for line in lines:
        line = line.strip()

        # Remove lines with too much noise
        digit_ratio = sum(c.isdigit() for c in line) / max(len(line), 1)
        alpha_ratio = sum(c.isalpha() for c in line) / max(len(line), 1)

        if digit_ratio > 0.7:
            continue  # mostly garbage numbers

        if alpha_ratio < 0.25:
            continue  # unreadable text

        if len(line) < 6:
            continue

        clean_lines.append(line)

    return " ".join(clean_lines)

# -------------------------------
# FUZZY KEYWORD MATCH (OCR SAFE)
# -------------------------------
def fuzzy_contains(text, keywords, max_errors=2):
    text = text.upper()
    for kw in keywords:
        kw = kw.upper()
        for i in range(len(text) - len(kw) + 1):
            window = text[i:i + len(kw)]
            errors = sum(a != b for a, b in zip(window, kw))
            if errors <= max_errors:
                return True
    return False


# -------------------------------
# AADHAAR EXTRACTION (FIXED & ROBUST)
# -------------------------------
import re

# Step 1: Simple Aadhaar extraction fallback
def extract_aadhaar_number(text):
    if not text:
        return None

    text_upper = text.upper()

    aadhaar_keywords = [
        "AADHAAR",
        "AADHAR",
        "YOUR AADHAAR",
        "UIDAI",
        "UNIQUE IDENTIFICATION"
    ]

    # Split text into logical chunks (prevents random long numbers)
    chunks = re.split(r"[.\n]", text_upper)
    candidates = []

    for chunk in chunks:
        # Aadhaar context required
        if any(k in chunk for k in aadhaar_keywords):
            # 🔹 Extract digit groups (12–14 digits with optional spaces/dashes)
            digit_groups = re.findall(r"(?:\d[\s\-]*){12,14}", chunk)

            for grp in digit_groups:
                # Remove non-digit characters
                num = re.sub(r"\D", "", grp)

                # Step 1: Basic length & starting digit checks
                if len(num) != 12:
                    continue
                if num[0] in ("0", "1"):
                    continue

                # Reject repeated digits
                if re.search(r"(\d)\1{3,}", num):
                    continue

                # Reject obvious sequences
                if num in "12345678901234567890":
                    continue

                # ✅ Final UIDAI validation if available
                try:
                    from verification.utils import verhoeff_check
                    if verhoeff_check(num):
                        candidates.append(num)
                except Exception:
                    # If verhoeff_check fails, still accept basic valid 12-digit number
                    candidates.append(num)

    # Return most confident Aadhaar (voting)
    if candidates:
        return max(set(candidates), key=candidates.count)

    # 🔹 Step 1 fallback: Simple 12-digit search anywhere in text if no context
    fallback = re.findall(r"\b\d{12}\b", text)
    if fallback:
        for num in fallback:
            if num[0] not in ("0", "1"):
                return num[:4] + " " + num[4:8] + " " + num[8:]

    return None



# -------------------------------
# PAN EXTRACTION
# -------------------------------
def extract_pan(text):
    if not text:
        return None
    match = re.search(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", text)
    return match.group() if match else None


# -------------------------------
# MAIN VERIFICATION FUNCTION
# -------------------------------
def verify_document(text, confidence, filename):

    report = {}
    report["Uploaded File Name"] = filename

    norm_text = normalize_text(text)

    classification = classify_document(norm_text)
    report["Document Type"] = classification.get("document", "Unknown")
    report["Document Category"] = classification.get("category", "Other")
    report["Template Match Score"] = classification.get("score", 0)

    aadhaar_no = extract_aadhaar_number(text)   # 🔴 IMPORTANT: use raw OCR text
    pan_no = extract_pan(norm_text)

    aadhaar_keywords = [
        "AADHAAR",
        "AADHAR",
        "UIDAI",
        "UNIQUE IDENTIFICATION",
        "YOUR AADHAAR"
    ]

    aadhaar_detected = (
        aadhaar_no is not None or
        fuzzy_contains(norm_text, aadhaar_keywords)
    )

    pan_detected = pan_no is not None

    if aadhaar_detected:
        report["Document Type"] = "Aadhaar Card"
        report["Document Category"] = "Government ID"

    elif pan_detected:
        report["Document Type"] = "PAN Card"
        report["Document Category"] = "Government ID"

    report["Aadhaar Detected"] = aadhaar_detected
    report["Aadhaar Number"] = aadhaar_no if aadhaar_detected else None

    report["PAN Detected"] = pan_detected
    report["PAN Number"] = pan_no if pan_detected else None

    fields = extract_fields(norm_text, verified_aadhaar=aadhaar_no)
    report["Extracted Fields"] = fields

    validation = validate_fields(fields)
    report["Field Validation"] = {
        k: {"valid": v[0], "reason": v[1]}
        for k, v in validation.items()
    }

    field_conf, suspicious = calculate_field_confidence(validation)
    report["Field Confidence"] = field_conf
    report["Suspicious Fields"] = suspicious

    report["Overall Integrity"] = (
        "REVIEW REQUIRED" if suspicious else "HIGH"
    )

    # -------------------------------
    # SMART CONFIDENCE BOOST
    # -------------------------------
    report["OCR Confidence"] = confidence

    if confidence < 40:
        report["OCR Warning"] = "Low OCR quality – text may be incomplete"

    base_conf = (confidence * 0.4) + (field_conf * 0.6)
    bonus = 0

    if aadhaar_no:
        bonus += 6

    if report["Document Category"] == "Government ID":
        bonus += 4

    if not suspicious:
        bonus += 5

    if report.get("Template Match Score", 0) > 70:
        bonus += 3

    if confidence < 30:
        bonus -= 4

    final_conf = base_conf + bonus
    final_conf = max(0, min(final_conf, 95))

    report["Verification Confidence"] = round(final_conf, 2)

    return report


# =====================================================
# LEGACY IMAGE-BASED ENTRY POINT (DO NOT REMOVE)
# =====================================================
def final_verify(image_path):

    try:
        from ocr.ocr_engine import run_ocr
    except ImportError:
        raise ImportError("run_ocr not found. Check ocr/ocr_engine.py")

    raw_text, clean_text, confidence = run_ocr(image_path)

    # 🔹 ADD: Clean noisy OCR text (post-OCR filtering)
    clean_text = clean_ocr_text(clean_text)

    # 🔹 ADD: SMART OCR CONFIDENCE BOOST (HONEST & SAFE)
    if confidence < 60:
        keyword_hits = sum(
            k in clean_text.upper()
            for k in ["AADHAAR", "UIDAI", "GOVERNMENT", "INDIA"]
        )

        if keyword_hits >= 2:
            confidence = min(confidence + 12, 70)

    report = verify_document(
        text=clean_text,
        confidence=confidence,
        filename=image_path
    )

    # Extract Aadhaar number from OCR text
    aadhaar_number = extract_aadhaar_number(clean_text)

    result = {
        "aadhaar_number": aadhaar_number,   # ✅ FIXED
        "pan_number": report.get("PAN Number"),
        "dob": report.get("Extracted Fields", {}).get("Date"),
        "name": report.get("Extracted Fields", {}).get("Name"),
        "address": report.get("Extracted Fields", {}).get("Address"),
        "verification_report": report,
        "raw_text": raw_text,
        "clean_text": clean_text
    }


    return result
