from verification.templates import DOCUMENT_TEMPLATES

def classify_document(normalized_text):
    text = normalized_text.replace(" ", "")

    best_match = {
        "document": "Unknown Document",
        "category": "Unknown",
        "score": 0
    }

    for doc, info in DOCUMENT_TEMPLATES.items():
        keywords = info["keywords"]
        matched = 0

        for kw in keywords:
            if kw.replace(" ", "") in text:
                matched += 1

        # ✅ SCORE AS PERCENTAGE (BOOST)
        score = int((matched / len(keywords)) * 100)

        if score > best_match["score"]:
            best_match = {
                "document": doc,
                "category": info["category"],
                "score": score
            }

    # ✅ FALLBACK BOOST
    if best_match["score"] >= 30:
        return best_match

    return {
        "document": "Unknown Document",
        "category": "Other",
        "score": best_match["score"]
    }
