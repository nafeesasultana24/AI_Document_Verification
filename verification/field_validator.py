from verification.utils import verhoeff_check
import datetime
import re   # 🔹 ADD: safety cleanup


def validate_fields(fields):
    validation = {}

    # 🔹 ADD: Safety guard for Streamlit
    if not fields or not isinstance(fields, dict):
        return {}

    # ---------- NAME ----------
    if fields.get("Name") and isinstance(fields.get("Name"), str) and len(fields["Name"]) >= 4:
        validation["Name"] = (True, "Valid name format")
    else:
        validation["Name"] = (False, "Missing or invalid name")

    # ---------- DATE ----------
    if fields.get("Date"):
        date_valid = False

        # 🔹 ADD: Normalize date text
        date_text = fields["Date"]
        if isinstance(date_text, str):
            date_text = date_text.replace("DOB", "").replace("DATE", "").strip()

        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
            try:
                datetime.datetime.strptime(date_text, fmt)
                date_valid = True
                break
            except Exception:
                pass

        if date_valid:
            validation["Date"] = (True, "Valid date format")
        else:
            validation["Date"] = (False, "Invalid date format")
    else:
        validation["Date"] = (False, "Date not found")

    # ---------- AADHAAR ----------
    if fields.get("Aadhaar Number"):
        aadhaar_raw = fields["Aadhaar Number"]

        # 🔹 ADD: Clean Aadhaar safely (spaces, garbage chars)
        if isinstance(aadhaar_raw, str):
            aadhaar_clean = re.sub(r"\D", "", aadhaar_raw)
        else:
            aadhaar_clean = ""

        # 🔹 ADD: Length check before checksum
        if len(aadhaar_clean) == 12:
            valid = verhoeff_check(aadhaar_clean)
            validation["Aadhaar Number"] = (
                valid,
                "Valid Aadhaar" if valid else "Invalid Aadhaar checksum"
            )
        else:
            validation["Aadhaar Number"] = (False, "Invalid Aadhaar length")
    else:
        validation["Aadhaar Number"] = (False, "Aadhaar not found")

    # ---------- PAN ----------
    if fields.get("PAN Number"):
        pan_val = fields["PAN Number"]

        # 🔹 ADD: Pattern re-check for safety
        if isinstance(pan_val, str) and re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", pan_val):
            validation["PAN Number"] = (True, "Valid PAN pattern")
        else:
            validation["PAN Number"] = (False, "Invalid PAN format")
    else:
        validation["PAN Number"] = (False, "PAN not found")

    # ---------- ADDRESS ----------
    if fields.get("Address"):
        validation["Address"] = (True, "Address detected")
    else:
        validation["Address"] = (False, "Address missing")

    # =====================================================
    # ✅ FALLBACK (DOES NOT REMOVE ANY ABOVE LOGIC)
    # Ensures all fields are always validated
    # =====================================================
    for field, value in fields.items():
        if field not in validation:
            if value:
                validation[field] = (True, "Valid")
            else:
                validation[field] = (False, "Missing or unreadable")

    return validation
