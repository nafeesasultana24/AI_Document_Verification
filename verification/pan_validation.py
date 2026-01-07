import re

PAN_REGEX = r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"

def validate_pan(text):
    text_upper = text.upper()

    pan_match = re.search(PAN_REGEX, text_upper)

    keyword_found = any(
        kw in text_upper
        for kw in ["INCOME TAX", "PAN", "DEPARTMENT"]
    )

    # simple name heuristic (2+ words, alphabets only)
    name_found = len(
        re.findall(r"\b[A-Z]{3,}\b", text_upper)
    ) >= 2

    pan_detected = keyword_found and (pan_match or name_found)

    return {
        "PAN Detected": pan_detected,
        "PAN Number": pan_match.group() if pan_match else "Not clearly visible"
    }
