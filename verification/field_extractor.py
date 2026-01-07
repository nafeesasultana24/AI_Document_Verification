import re

def extract_fields(text, verified_aadhaar=None):   # ✅ ADDED PARAMETER
    fields = {}

    # ---------- NAME ----------
    name_match = re.search(r"\b([A-Z][A-Z ]{3,})\b", text)
    fields["Name"] = name_match.group(1).strip() if name_match else None

    # ---------- DATE (DOB / ISSUE DATE) ----------
    date_match = re.search(
        r"\b(\d{2}[\/\-]\d{2}[\/\-]\d{4})\b", text
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
            match = re.search(pattern, text)
            if match:
                fields["Date"] = match.group()
                break

    # ---------- AADHAAR ----------
    aadhaar_match = re.search(r"\b[2-9]\d{11}\b", text.replace(" ", ""))
    fields["Aadhaar Number"] = aadhaar_match.group() if aadhaar_match else None

    # ✅ FIX 1: TRUST VERIFIED AADHAAR (DO NOT REMOVE ABOVE)
    if verified_aadhaar:
        fields["Aadhaar Number"] = verified_aadhaar

    # ---------- PAN ----------
    pan_match = re.search(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", text)
    fields["PAN Number"] = pan_match.group() if pan_match else None

    # ---------- ADDRESS ----------
    address_keywords = ["ADDRESS", "VILLAGE", "ROAD", "DISTRICT", "STATE", "PIN"]
    if any(k in text for k in address_keywords):
        fields["Address"] = "Present"
    else:
        fields["Address"] = None

    return fields
