import os
os.environ["OMP_NUM_THREADS"] = "1"

import streamlit as st
import tempfile
import numpy as np
from PIL import Image
from pdf2image import convert_from_bytes

from ocr.ocr_engine import ocr_on_image
from verification.final_verification import verify_document
from utils.pdf_report import generate_pdf


# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="AI Govt-ID Verification System",
    page_icon="🆔",
    layout="centered"
)

st.title("🆔 AI Government Document Verification System")
st.caption(
    "AI-Powered OCR-Based Government Document Analysis, Validation & Confidence Analysis"
)

# ---------------- FILE UPLOADER ----------------
st.markdown("<div class='card'>", unsafe_allow_html=True)
uploaded_files = st.file_uploader(
    "📤 Upload Aadhaar / PAN Image or PDF",
    type=["png", "jpg", "jpeg", "pdf"],
    accept_multiple_files=True
)
st.markdown("</div>", unsafe_allow_html=True)

all_text = ""
final_report = {}

# ---------------- PROCESS FILES ----------------
if uploaded_files:
    for file in uploaded_files:

        st.markdown(
            f"""
            <div class='card'>
                <b>📌 Uploaded Document:</b> {file.name}
            </div>
            """,
            unsafe_allow_html=True
        )

        # ========== PDF HANDLING ==========
        if file.name.lower().endswith(".pdf"):
            pages = convert_from_bytes(file.read(), dpi=300)


            for i, page in enumerate(pages):
                st.markdown(f"### 📄 Page {i+1}")

                # PIL → NumPy (NO cv2)
                img = np.array(page.convert("RGB"))

                progress = st.progress(0)
                status = st.empty()

                status.info("🔍 Preprocessing document...")
                progress.progress(30)

                status.info("🧠 Running OCR engine...")
                progress.progress(65)

                result = ocr_on_image(img)

                st.write("🔎 RAW OCR RESULT (PDF):")
                st.write(result)

                text = result["final"]["text"]
                confidence = result["final"]["confidence"]


                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown("**📄 OCR Extracted Text**")
                st.text_area("", text, height=150)
                st.markdown(f"**OCR Confidence:** {confidence}%")
                st.progress(confidence / 100)
                st.markdown("</div>", unsafe_allow_html=True)

                report = verify_document(text, confidence, file.name)
                final_report.update(report)
                all_text += text + "\n"

        # ========== IMAGE HANDLING ==========
        else:
            # PIL → NumPy (NO cv2)
            img = Image.open(file).convert("RGB")
            img = np.array(img)

            progress = st.progress(0)
            status = st.empty()

            status.info("🔍 Preprocessing document...")
            progress.progress(30)

            status.info("🧠 Running OCR engine...")
            progress.progress(65)

            result = ocr_on_image(img)

            st.write("🔎 RAW OCR RESULT:")
            st.write(result)

            text = result["final"]["text"]
            confidence = result["final"]["confidence"]

            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("**📄 OCR Extracted Text**")
            st.text_area("", text, height=150)

            color = "🟢" if confidence >= 80 else "🟡"
            st.markdown(f"{color} **OCR Confidence:** {confidence}%")
            st.progress(confidence / 100)
            st.markdown("</div>", unsafe_allow_html=True)

            report = verify_document(text, confidence, file.name)
            final_report.update(report)
            all_text += text + "\n"

    # ---------------- VERIFICATION RESULTS ----------------
    st.markdown("## ✅ Verification Results")

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    for k, v in final_report.items():
        if isinstance(v, bool):
            st.markdown(f"**{k}:** {'YES' if v else 'NO'}")
        else:
            st.markdown(f"**{k}:** {v}")
    st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- EXPORT PDF ----------------
    pdf_path = "verification_report.pdf"
    generate_pdf(final_report, pdf_path)

    with open(pdf_path, "rb") as f:
        st.download_button(
            label="📄 Download Verification Report (PDF)",
            data=f,
            file_name="AI_Govt_ID_Report.pdf",
            mime="application/pdf"
        )

# ---------------- COMBINED TEXT ----------------
if all_text:
    st.subheader("📄 Combined Extracted Text")
    st.text_area("", all_text, height=300)
