def generate_pdf(data, output_path):
    """
    Streamlit-safe fallback.
    PDF generation disabled if reportlab is unavailable.
    """
    with open(output_path, "w") as f:
        f.write("PDF generation is disabled on Streamlit Cloud.\n\n")
        for k, v in data.items():
            f.write(f"{k}: {v}\n")
