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
# AADHAAR EXTRACTION (ROBUST)
# -------------------------------
def extract_aadhaar_number(text):
    if not text:
        return None

    digits = re.sub(r"\D", "", text)
    candidates = re.findall(r"[2-9]\d{11}", digits)

    for num in candidates:
        if verhoeff_check(num):
            return num

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

    # Initial ML classification
    classification = classify_document(norm_text)
    report["Document Type"] = classification.get("document", "Unknown")
    report["Document Category"] = classification.get("category", "Other")
    report["Template Match Score"] = classification.get("score", 0)

    # Extract IDs
    aadhaar_no = extract_aadhaar_number(norm_text)
    pan_no = extract_pan(norm_text)

    # Aadhaar keyword detection (OCR tolerant)
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

    # PAN detection
    pan_detected = pan_no is not None

    # -------------------------------
    # RULE-BASED OVERRIDE (IMPORTANT)
    # -------------------------------
    if aadhaar_detected:
        report["Document Type"] = "Aadhaar Card"
        report["Document Category"] = "Government ID"

    elif pan_detected:
        report["Document Type"] = "PAN Card"
        report["Document Category"] = "Government ID"

    # Store results
    report["Aadhaar Detected"] = aadhaar_detected
    report["Aadhaar Number"] = aadhaar_no if aadhaar_detected else None

    report["PAN Detected"] = pan_detected
    report["PAN Number"] = pan_no if pan_detected else None

    # -------------------------------
    # FIELD EXTRACTION & VALIDATION
    # -------------------------------
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
    # CONFIDENCE HANDLING
    # -------------------------------
    report["OCR Confidence"] = confidence

    if confidence < 40:
        report["OCR Warning"] = "Low OCR quality – text may be incomplete"

    report["Verification Confidence"] = round(
        (confidence * 0.4) + (field_conf * 0.6), 2
    )

    return report
