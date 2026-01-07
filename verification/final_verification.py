import re
import unicodedata
from verification.utils import verhoeff_check
from verification.classifier import classify_document
from verification.field_extractor import extract_fields
from verification.field_validator import validate_fields
from verification.field_confidence import calculate_field_confidence




# -------------------------------
# TEXT NORMALIZATION
# -------------------------------
def normalize_text(text):
    text = unicodedata.normalize("NFKC", text).upper()
    text = re.sub(r"[^A-Z0-9]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# -------------------------------
# NUMBER EXTRACTION
# -------------------------------
def extract_aadhaar_number(text):
    cleaned = re.sub(r"[^\d ]", "", text)

    candidates = re.findall(r"\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b", cleaned)

    for c in candidates:
        aadhaar = c.replace(" ", "")
        if len(aadhaar) == 12 and verhoeff_check(aadhaar):
            return aadhaar

    return None



def extract_pan(text):
    match = re.search(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", text)
    return match.group() if match else None


# -------------------------------
# DOCUMENT TYPE DETECTION (STRICT)
# -------------------------------
def detect_document_type(text, aadhaar_no, pan_no):
    t = text.replace(" ", "")

    # ✅ PAN HAS PRIORITY
    if pan_no:
        return "PAN Card"

    # ✅ Aadhaar requires UIDAI-specific signals
    aadhaar_keywords = [
        "UIDAI",
        "UNIQUEIDENTIFICATION",
        "AADHAAR",
        "AADHAR",
        "YOURAADHAAR",
        "MAADHAAR"
    ]

    if aadhaar_no and any(k in t for k in aadhaar_keywords):
        return "Aadhaar Card"

    return "Unknown Document"


# -------------------------------
# MAIN VERIFICATION FUNCTION
# -------------------------------
def verify_document(text, confidence, filename):

    report = {}
    report["Uploaded File Name"] = filename

    # -------------------------------
    # TEXT NORMALIZATION
    # -------------------------------
    norm_text = normalize_text(text)

    # -------------------------------
    # DOCUMENT CLASSIFICATION
    # -------------------------------
    classification = classify_document(norm_text)

    report["Document Type"] = classification.get("document", "Unknown")
    report["Document Category"] = classification.get("category", "Unknown")
    report["Template Match Score"] = classification.get("score", 0)

    document_type = report["Document Type"]

    # -------------------------------
    # PAN & AADHAAR EXTRACTION
    # -------------------------------
    pan_no = extract_pan(norm_text)
    aadhaar_no = extract_aadhaar_number(text)

    aadhaar_keywords = ["AADHAAR", "UIDAI", "UNIQUE IDENTIFICATION"]
    aadhaar_detected = aadhaar_no is not None and any(k in norm_text for k in aadhaar_keywords)

    # -------------------------------
    # Aadhaar Logic
    # -------------------------------
    if document_type == "Aadhaar Card" and aadhaar_detected:
        report["Aadhaar Detected"] = True
        report["Aadhaar Number"] = aadhaar_no
    else:
        report["Aadhaar Detected"] = False
        report["Aadhaar Number"] = None

    # -------------------------------
    # PAN Logic
    # -------------------------------
    if document_type == "PAN Card" and pan_no:
        report["PAN Detected"] = True
        report["PAN Number"] = pan_no
    else:
        report["PAN Detected"] = False
        report["PAN Number"] = None

    # =====================================================
    # 🔍 FIELD EXTRACTION & VALIDATION  (ADD HERE ✅)
    # =====================================================
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

    # -------------------------------
    # CONFIDENCE SCORES
    # -------------------------------
    report["OCR Confidence"] = confidence
    report["Verification Confidence"] = round(
    (confidence * 0.4) + (report["Field Confidence"] * 0.6), 2
)


    return report
