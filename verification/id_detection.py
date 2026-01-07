import re

AADHAAR_REGEX = r"\b\d{4}\s?\d{4}\s?\d{4}\b"
PAN_REGEX = r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"

def detect_ids(text):
    aadhaar = re.findall(AADHAAR_REGEX, text)
    pan = re.findall(PAN_REGEX, text)

    return {
        "aadhaar_found": bool(aadhaar),
        "pan_found": bool(pan),
        "aadhaar_numbers": aadhaar,
        "pan_numbers": pan
    }
