import re

def validate_aadhaar(text):
    # Standardizing text for keyword search
    text_upper = text.upper()
    raw_text = text # Keeping raw for name/dob extraction

    # 1. FIXED AADHAAR NUMBER LOGIC
    # Look for all 12-digit patterns; usually the last one in the OCR is the actual ID
    aadhaar_pattern = r'\b\d{4}\s?\d{4}\s?\d{4}\b'
    aadhaar_matches = re.findall(aadhaar_pattern, raw_text)
    
    # 2. FIXED DATE OF BIRTH LOGIC
    dob_pattern = r'(\d{2}/\d{2}/\d{4})|(\d{4})'
    dob_match = re.search(dob_pattern, raw_text)
    dob = dob_match.group(0) if dob_match else "Not Found"

    # 3. FIXED NAME LOGIC
    name_pattern = r'(?:To\s+[\d]*\s*)([A-Z][a-z]+\s[A-Z][a-z]+)'
    name_match = re.search(name_pattern, raw_text)
    name = name_match.group(1) if name_match else "Check OCR Quality"

    # Keyword signals (Existing logic kept)
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

    # Partial Aadhaar check (Existing logic kept)
    partial_aadhaar = re.search(r"\b\d{4}\s?__\b|\b\d{4}\b", text_upper)

    # FINAL DECISION
    aadhaar_detected = aadhaar_keywords or address_keywords or bool(aadhaar_matches or partial_aadhaar)

    # Aadhaar number output assignment
    if aadhaar_matches:
        # Taking the last match fixes the issue of picking up mobile fragments
        aadhaar_number = aadhaar_matches[-1]
    elif partial_aadhaar:
        aadhaar_number = "Partially masked / not fully visible"
    else:
        aadhaar_number = "Not Found"

    return {
        "Aadhaar Detected": aadhaar_detected,
        "Aadhaar Number": aadhaar_number,
        "Name": name,
        "DOB": dob
    }