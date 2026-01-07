import re

def extract_fields(text):
    name = re.findall(r"Name[:\s]+([A-Za-z ]+)", text)
    dob = re.findall(r"(\d{2}/\d{2}/\d{4})", text)

    return {
        "name": name[0] if name else None,
        "dob": dob[0] if dob else None
    }

def validate_fields(fields):
    issues = []
    if not fields["name"]:
        issues.append("Name missing")
    if not fields["dob"]:
        issues.append("DOB missing")

    return issues
