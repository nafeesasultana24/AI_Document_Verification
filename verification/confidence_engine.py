import re

def calculate_confidence(text, ocr_conf):
    text_upper = text.upper()
    score = 0

    # Aadhaar signals
    if "AADHAAR" in text_upper:
        score += 30
    if "UIDAI" in text_upper or "UNIQUE IDENTIFICATION" in text_upper:
        score += 20
    if any(k in text_upper for k in ["DISTRICT", "STATE", "PIN"]):
        score += 20
    if re.search(r"\b\d{4}\s?\d{4}\s?\d{4}\b", text):
        score += 30
    elif re.search(r"\b\d{4}\b", text):
        score += 15

    detection_conf = min(score, 100)

    # Consistency check
    consistency = 0
    names = re.findall(r"[A-Z][a-z]+", text)
    if len(names) > 10:
        consistency += 30
    if text.count("INDIA") > 1:
        consistency += 40
    if text.count(",") > 5:
        consistency += 30

    consistency = min(consistency, 100)

    # Final weighted confidence
    final_conf = (
        0.4 * ocr_conf +
        0.4 * detection_conf +
        0.2 * consistency
    )

    return round(final_conf, 2)
