import re


def extract_fields(text, verified_aadhaar=None):   # ✅ ADDED PARAMETER
    fields = {}

    # 🔹 ADD: Safety normalization (DO NOT remove original text usage)
    if not text or not isinstance(text, str):
        text = ""

    text_clean = re.sub(r"\s+", " ", text.upper()).strip()

    # ---------- NAME ----------
    name_match = re.search(r"\b([A-Z][A-Z ]{3,})\b", text_clean)
    extracted_name = name_match.group(1).strip() if name_match else None

    # 🔹 ADD: Filter obvious garbage names
    if extracted_name:
        blocked_words = [
            "GOVERNMENT", "INDIA", "UNIQUE", "IDENTIFICATION",
            "AUTHORITY", "AADHAAR", "ENROLMENT"
        ]
        if any(w in extracted_name for w in blocked_words):
            extracted_name = None

    fields["Name"] = extracted_name

    # ---------- DATE (DOB / ISSUE DATE) ----------
    date_match = re.search(
        r"\b(\d{2}[\/\-]\d{2}[\/\-]\d{4})\b", text_clean
    )
    fields["Date"] = date_match.group(1) if date_match else None

    # ✅ ADDITIONAL DATE FORMATS (DO NOT REMOVE ABOVE)
    if not fields["Date"]:
        extra_date_patterns = [
            r"\b\d{2}[.]\d{2}[.]\d{4}\b",                 # 12.05.2002
            r"\b\d{1,2}\s[A-Z]{3,9}\s\d{4}\b",            # 05 JAN 2001
            r"\bDOB[:\s]*\d{2}[\/\-]\d{2}[\/\-]\d{4}\b",  # DOB:12/05/2002
            r"\bDATE[:\s]*\d{2}[\/\-]\d{2}[\/\-]\d{4}\b"
        ]

        for pattern in extra_date_patterns:
            match = re.search(pattern, text_clean)
            if match:
                fields["Date"] = match.group()
                break

    # ---------- AADHAAR ----------
    aadhaar_match = re.search(
        r"\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b", text_clean
    )

    extracted_aadhaar = (
        aadhaar_match.group().replace(" ", "")
        if aadhaar_match else None
    )

    fields["Aadhaar Number"] = extracted_aadhaar

    # ✅ FIX 1: TRUST VERIFIED AADHAAR (DO NOT REMOVE ABOVE)
    if verified_aadhaar:
        fields["Aadhaar Number"] = verified_aadhaar

    # ---------- PAN ----------
    pan_match = re.search(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", text_clean)
    fields["PAN Number"] = pan_match.group() if pan_match else None

    # ---------- ADDRESS ----------
    address_keywords = [
        "ADDRESS", "VILLAGE", "ROAD", "DISTRICT",
        "STATE", "PIN", "PO", "VTC", "SUB DISTRICT"
    ]

    if any(k in text_clean for k in address_keywords):
        fields["Address"] = "Present"
    else:
        fields["Address"] = None

    return fields
