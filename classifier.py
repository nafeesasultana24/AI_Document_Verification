def classify_document(text):
    text = text.lower()
    if "birth" in text:
        return "Birth Certificate"
    elif "identity" in text or "aadhaar" in text:
        return "ID Proof"
    elif "license" in text:
        return "License"
    else:
        return "Unknown"
