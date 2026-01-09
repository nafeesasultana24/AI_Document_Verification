import re
import unicodedata
import streamlit as st

from verification.utils import verhoeff_check
from verification.classifier import classify_document
from verification.field_extractor import extract_fields
from verification.field_validator import validate_fields
from verification.field_confidence import calculate_field_confidence


def normalize_text(text):
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text).upper()
    text = re.sub(r"[^A-Z0-9]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_aadhaar_number(text):
    if not text:
        return None

    cleaned = re.sub(r"[^\d ]", "", text)
    matches = re.findall(r"\b[2-9]\d{11}\b", cleaned.replace(" ", ""))

    for num in matches:
        if verhoeff_check(num):
            return num

    return None


def extract_pan(text):
    if not text:
        return None
    match = re.search(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", text)
    return match.group() if match else None


def verify_document(text, confidence, filename):
    report = {}

    report["Uploaded File Name"] = filename

    norm_text = normalize_text(text)

    classification = classify_document(norm_text)

    report["Document Type"] = classification.get("document", "Unknown")
    report["Document Category"] = classification.get("category", "Other")
    report["Template Match Score"] = classification.get("score", 0)

    pan_no = extract_pan(norm_text)
    aadhaar_no = extract_aadhaar_number(norm_text)

    report["PAN Detected"] = bool(pan_no)
    report["PAN Number"] = pan_no

    report["Aadhaar Detected"] = bool(aadhaar_no)
    report["Aadhaar Number"] = aadhaar_no

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
    report["Overall Integrity"] = "HIGH" if not suspicious else "REVIEW REQUIRED"

    report["OCR Confidence"] = confidence
    report["Verification Confidence"] = round(
        (confidence * 0.4) + (field_conf * 0.6), 2
    )

    return report
