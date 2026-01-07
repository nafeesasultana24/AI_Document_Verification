def detect_fake_document(text):
    suspicious = ["lorem", "sample", "dummy", "xxxx"]
    text = text.lower()
    return any(word in text for word in suspicious)
