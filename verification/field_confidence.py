def calculate_field_confidence(validation_results):
    """
    validation_results format:
    {
        "Name": (True, "Looks valid"),
        "DOB": (False, "Missing"),
        ...
    }
    """

    # 🔴 Define importance
    CRITICAL_FIELDS = {"Name", "DOB", "ID Number", "Document Number"}
    OPTIONAL_FIELDS = {"Address", "Gender", "Issue Date", "Father Name"}

    score = 0
    max_score = 0
    suspicious = []

    for field, (is_valid, reason) in validation_results.items():

        # Assign weight
        if field in CRITICAL_FIELDS:
            weight = 3
        else:
            weight = 1

        max_score += weight

        if is_valid:
            score += weight
        else:
            suspicious.append(f"{field}: {reason}")

    # Avoid division error
    if max_score == 0:
        return 0, suspicious

    # 🔢 Normalize to 100
    confidence = round((score / max_score) * 100, 2)

    return confidence, suspicious
