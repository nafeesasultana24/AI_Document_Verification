# verification/export_pdf.py

from fpdf import FPDF
import os
import re

def safe_text(text, max_word_len=40):
    """
    Breaks long unbroken words to avoid FPDF crash
    """
    words = text.split(" ")
    safe_words = []

    for word in words:
        if len(word) > max_word_len:
            # break long word
            broken = "\n".join(
                [word[i:i+max_word_len] for i in range(0, len(word), max_word_len)]
            )
            safe_words.append(broken)
        else:
            safe_words.append(word)

    return " ".join(safe_words)

def export_verification_report(report):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "AI Document Verification Report", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", size=11)

    for key, value in report.items():
        # Clean text
        line = f"{key}: {value}"
        line = re.sub(r"[^\x00-\x7F]+", " ", line)  # remove unicode
        line = safe_text(line)

        pdf.set_x(10)  # IMPORTANT: reset cursor
        pdf.multi_cell(190, 8, line)  # FIXED WIDTH (NOT 0)
        pdf.ln(1)

    output_path = os.path.abspath("verification_report.pdf")
    pdf.output(output_path)

    return output_path
