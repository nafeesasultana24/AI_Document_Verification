from verification.templates import DOCUMENT_TEMPLATES
import re

def classify_document(normalized_text):
    text = normalized_text.upper().replace(" ", "")

    best_match = {
        "document": "Unknown Document",
        "category": "Unknown",
        "score": 0
    }

    # ================= TEMPLATE MATCHING =================
    for doc, info in DOCUMENT_TEMPLATES.items():
        keywords = info["keywords"]
        matched = 0

        for kw in keywords:
            if kw.upper().replace(" ", "") in text:
                matched += 1

        score = int((matched / len(keywords)) * 100)

        if score > best_match["score"]:
            best_match = {
                "document": doc,
                "category": info["category"],
                "score": score
            }

    # ================= AUTO-DETECT OVERRIDE =================
    aadhaar_pattern = re.search(r"\b\d{4}\s?\d{4}\s?\d{4}\b", normalized_text)
    pan_pattern = re.search(r"\b[A-Z]{5}\d{4}[A-Z]\b", normalized_text)

    aadhaar_keywords = [
        "UNIQUE IDENTIFICATION",
        "UIDAI",
        "AADHAAR",
        "GOVERNMENT OF INDIA"
    ]

    pan_keywords = [
        "INCOME TAX DEPARTMENT",
        "PERMANENT ACCOUNT NUMBER",
        "INCOME TAX"
    ]

    aadhaar_hits = sum(k in normalized_text.upper() for k in aadhaar_keywords)
    pan_hits = sum(k in normalized_text.upper() for k in pan_keywords)

    # 🔥 STRONG AADHAAR DETECTION
    if aadhaar_pattern and aadhaar_hits >= 2:
        return {
            "document": "Aadhaar Card",
            "category": "Government ID",
            "score": max(best_match["score"], 85)
        }

    # 🔥 STRONG PAN DETECTION
    if pan_pattern and pan_hits >= 2:
        return {
            "document": "PAN Card",
            "category": "Government ID",
            "score": max(best_match["score"], 85)
        }

    # ================= FALLBACK =================
    if best_match["score"] >= 30:
        return best_match

    return {
        "document": "Unknown Document",
        "category": "Other",
        "score": best_match["score"]
    }
