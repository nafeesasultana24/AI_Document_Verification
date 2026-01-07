import re

def validate_aadhaar(text):
    text_upper = text.upper()

    # Regex patterns
    full_aadhaar = re.search(r"\b\d{4}\s?\d{4}\s?\d{4}\b", text_upper)
    partial_aadhaar = re.search(r"\b\d{4}\s?__\b|\b\d{4}\b", text_upper)

    # Keyword signals
    aadhaar_keywords = any(
        kw in text_upper
        for kw in [
            "AADHAAR",
            "UIDAI",
            "UNIQUE IDENTIFICATION",
            "IDENTIFICATION AUTHORITY"
        ]
    )

    address_keywords = any(
        kw in text_upper
        for kw in [
            "VTC",
            "DISTRICT",
            "STATE",
            "PIN"
        ]
    )

    # FINAL DECISION (THIS WAS WRONG EARLIER)
    aadhaar_detected = aadhaar_keywords or address_keywords or bool(full_aadhaar or partial_aadhaar)

    # Aadhaar number output
    if full_aadhaar:
        aadhaar_number = full_aadhaar.group()
    elif partial_aadhaar:
        aadhaar_number = "Partially masked / not fully visible"
    else:
        aadhaar_number = None

    return {
        "Aadhaar Detected": aadhaar_detected,
        "Aadhaar Number": aadhaar_number
    }
