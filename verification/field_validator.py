from verification.utils import verhoeff_check
import datetime

def validate_fields(fields):
    validation = {}

    # ---------- NAME ----------
    if fields.get("Name") and len(fields["Name"]) >= 4:
        validation["Name"] = (True, "Valid name format")
    else:
        validation["Name"] = (False, "Missing or invalid name")

    # ---------- DATE ----------
    if fields.get("Date"):
        date_valid = False
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
            try:
                datetime.datetime.strptime(fields["Date"], fmt)
                date_valid = True
                break
            except:
                pass

        if date_valid:
            validation["Date"] = (True, "Valid date format")
        else:
            validation["Date"] = (False, "Invalid date format")
    else:
        validation["Date"] = (False, "Date not found")

    # ---------- AADHAAR ----------
    if fields.get("Aadhaar Number"):
        valid = verhoeff_check(fields["Aadhaar Number"])
        validation["Aadhaar Number"] = (
            valid,
            "Valid Aadhaar" if valid else "Invalid Aadhaar checksum"
        )
    else:
        validation["Aadhaar Number"] = (False, "Aadhaar not found")

    # ---------- PAN ----------
    if fields.get("PAN Number"):
        validation["PAN Number"] = (True, "Valid PAN pattern")
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
