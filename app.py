import os
os.environ["OMP_NUM_THREADS"] = "1"
import streamlit as st
import tempfile
import numpy as np
import cv2
from pdf2image import convert_from_path
from ocr.ocr_engine import ocr_on_image
from verification.final_verification import verify_document
from verification.export_pdf import export_verification_report
from utils.pdf_report import generate_pdf

st.set_page_config(
    page_title="AI Govt-ID Verification System",
    page_icon="🆔",
    layout="centered"
)

st.title("🆔 AI Government Document Verification System")
st.markdown("""
<style>
.subtitle {
    text-align: center;
    font-size: 18px;
    font-weight: 600;
    color: var(--glow-color);
    opacity: 0;
    animation: slideFadeGlow 1.5s ease-out forwards;
    margin-top: -8px;
    text-shadow:
        0 0 6px var(--glow-shadow),
        0 0 14px var(--glow-shadow);
}

.stApp {
    --glow-color: #0284c7;
    --glow-shadow: rgba(2,132,199,0.45);
}

@keyframes slideFadeGlow {
    from {
        transform: translateY(12px);
        opacity: 0;
    }
    to {
        transform: translateY(0);
        opacity: 1;
    }
}
</style>

<p class="subtitle">
AI-Powered OCR-Based Government Document Analysis, Validation & Confidence Analysis
</p>
""", unsafe_allow_html=True)


st.markdown("""
<style>
/* -------- GLOBAL -------- */
html, body, [class*="css"]  {
    font-family: 'Segoe UI', sans-serif;
}

/* -------- TITLE -------- */
h1 {
    text-align: center;
    font-weight: 700;
    animation: fadeIn 1.2s ease-in-out;
}

/* -------- CARD STYLE -------- */
.card {
    background: rgba(255,255,255,0.08);
    padding: 20px;
    border-radius: 15px;
    margin-bottom: 20px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    animation: slideUp 0.8s ease;
}

/* -------- CONFIDENCE BADGE -------- */
.badge {
    padding: 8px 14px;
    border-radius: 999px;
    font-weight: 600;
    display: inline-block;
}

/* -------- ANIMATIONS -------- */
@keyframes fadeIn {
    from {opacity: 0;}
    to {opacity: 1;}
}

@keyframes slideUp {
    from {transform: translateY(20px); opacity: 0;}
    to {transform: translateY(0); opacity: 1;}
}
</style>
""", unsafe_allow_html=True)


st.markdown("""
<style>

/* ---------- BACKGROUND ---------- */
.stApp {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    font-family: 'Segoe UI', sans-serif;
}

/* ---------- MAIN CARD ---------- */
.block-container {
    background: rgba(255, 255, 255, 0.12);
    backdrop-filter: blur(14px);
    border-radius: 18px;
    padding: 2rem;
    animation: fadeIn 0.8s ease-in;
}

/* ---------- HEADINGS ---------- */
h1, h2, h3 {
    color: #ffffff !important;
    text-align: center;
    animation: slideDown 0.7s ease-in-out;
}

/* ---------- FILE UPLOADER ---------- */
section[data-testid="stFileUploader"] {
    background: rgba(255, 255, 255, 0.18);
    border-radius: 15px;
    padding: 20px;
    animation: pulse 2s infinite;
}

/* ---------- TEXT AREA ---------- */
textarea {
    background-color: #111 !important;
    color: #00ffcc !important;
    border-radius: 10px;
}

/* ---------- RESULT CARD ---------- */
.card {
    background: rgba(0, 0, 0, 0.55);
    padding: 18px;
    border-radius: 15px;
    margin-top: 15px;
    animation: fadeUp 0.6s ease-in-out;
}

/* ---------- LABELS ---------- */
.label {
    font-weight: bold;
    color: #00eaff;
}

.success {
    color: #00ff88;
    font-weight: bold;
}

.warning {
    color: #ffcc00;
    font-weight: bold;
}

.info {
    color: #ffffff;
}

/* ---------- BUTTON ---------- */
button {
    background: linear-gradient(135deg, #00c6ff, #0072ff) !important;
    color: white !important;
    border-radius: 12px !important;
    font-weight: bold !important;
}

/* ---------- ANIMATIONS ---------- */
@keyframes fadeIn {
    from { opacity: 0 }
    to { opacity: 1 }
}

@keyframes fadeUp {
    from { opacity: 0; transform: translateY(20px) }
    to { opacity: 1; transform: translateY(0) }
}

@keyframes slideDown {
    from { transform: translateY(-20px); opacity: 0 }
    to { transform: translateY(0); opacity: 1 }
}

@keyframes pulse {
    0% { box-shadow: 0 0 0px rgba(0,255,255,0.4) }
    50% { box-shadow: 0 0 20px rgba(0,255,255,0.8) }
    100% { box-shadow: 0 0 0px rgba(0,255,255,0.4) }
}

</style>
""", unsafe_allow_html=True)





mode = st.toggle("🌙 Dark Mode", value=True)

if mode:
    # 🌙 DARK MODE
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        color: #ffffff;
    }
    .card {
        background: rgba(255, 255, 255, 0.08);
        padding: 20px;
        border-radius: 14px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        margin-top: 15px;
    }
    .info { color: #eaeaea; }
    .label { color: #00ffd5; font-weight: bold; }
    .success { color: #4ade80; }
    .warning { color: #facc15; }
    </style>
    """, unsafe_allow_html=True)

else:
    # ☀️ LIGHT MODE (FIXED)
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #fdfbfb, #ebedee);
        color: #111111;
    }
    .card {
        background: #ffffff;
        padding: 20px;
        border-radius: 14px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        margin-top: 15px;
    }
    .info {
        color: #222222;
        font-size: 16px;
    }
    .label {
        color: #1e40af;
        font-weight: bold;
    }
    .success {
        color: #15803d;
    }
    .warning {
        color: #b45309;
    }
    h1, h2, h3, p {
        color: #111111 !important;
    }
    </style>
    """, unsafe_allow_html=True)



st.markdown("<div class='card'>", unsafe_allow_html=True)
uploaded_files = st.file_uploader(
    "📤 Upload Aadhaar / PAN Image or PDF",
    type=["png", "jpg", "jpeg", "pdf"],
    accept_multiple_files=True
)
st.markdown("</div>", unsafe_allow_html=True)



all_text = ""
final_report = {}

if uploaded_files:
    for file in uploaded_files:
        st.markdown(f"""
            <div class='card'>
            <span class='label'>📌 Uploaded Document:</span>
            <span class='info'>{file.name}</span>
            </div>
            """, unsafe_allow_html=True)

       
        # ---------- PDF ----------
        if file.name.lower().endswith(".pdf"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(file.read())
                pdf_path = tmp.name

            pages = convert_from_path(
                pdf_path,
                dpi=300,
                grayscale=True
            )

            for i, page in enumerate(pages):
                st.markdown(f"### 📄 Page {i+1}")
                img = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
                progress = st.progress(0)
                status = st.empty()

                status.info("🔍 Preprocessing document...")
                progress.progress(30)

                status.info("🧠 Running OCR engine...")
                progress.progress(65)

                result = ocr_on_image(img)
                status.success("✅ OCR Completed")
                progress.progress(100)

                text = result["final"]["text"]
                confidence = result["final"]["confidence"]

                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown("<span class='label'>📄 OCR Extracted Text</span>", unsafe_allow_html=True)
                st.text_area(
                    "OCR Extracted Text",
                    text,
                    height=150,
                    label_visibility="collapsed"
                )


                st.markdown(f"<span class='label'>OCR Confidence:</span> <span class='info'>{confidence}%</span>", unsafe_allow_html=True)
                st.progress(confidence / 100)
                st.markdown("</div>", unsafe_allow_html=True)


                report = verify_document(text, confidence, file.name)
                final_report.update(report)
                all_text += text + "\n"

        # ---------- IMAGE ----------
        else:
            file_bytes = np.asarray(bytearray(file.read()), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            progress = st.progress(0)
            status = st.empty()

            status.info("🔍 Preprocessing document...")
            progress.progress(30)

            status.info("🧠 Running OCR engine...")
            progress.progress(65)


            result = ocr_on_image(img)
            status.success("✅ OCR Completed")
            progress.progress(100)

            text = result["final"]["text"]
            confidence = result["final"]["confidence"]

            st.markdown("<div class='card'>", unsafe_allow_html=True)

            st.markdown("<span class='label'>📄 OCR Extracted Text</span>", unsafe_allow_html=True)

            st.text_area(
                "OCR Extracted Text",
                text,
                height=150,
                label_visibility="collapsed"
            )

            conf_color = "success" if confidence >= 80 else "warning"

            st.markdown(
                f"<span class='{conf_color}'>OCR Confidence: {confidence}%</span>",
                unsafe_allow_html=True
            )

            st.progress(confidence / 100)

            st.markdown("</div>", unsafe_allow_html=True)


            report = verify_document(text, confidence, file.name)
            final_report.update(report)
            all_text += text + "\n"

       # ---------- VERIFICATION RESULTS ----------
        st.markdown("<h3 style='text-align:center;'>✅ Verification Results</h3>", unsafe_allow_html=True)

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        for k, v in final_report.items():
            if isinstance(v, bool):
                color = "success" if v else "warning"
                value = "YES" if v else "NO"
                st.markdown(
                    f"<span class='label'>{k}:</span> "
                    f"<span class='{color}'>{value}</span>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"<span class='label'>{k}:</span> "
                    f"<span class='info'>{v}</span>",
                    unsafe_allow_html=True
                )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### 📊 Confidence Analysis")

        st.progress(int(final_report["OCR Confidence"]))
        st.caption(f"OCR Confidence: {final_report['OCR Confidence']}%")

        st.progress(int(final_report["Template Match Score"]))
        st.caption(f"Template Match Score: {final_report['Template Match Score']}%")

        st.progress(int(final_report["Field Confidence"]))
        st.caption(f"Field Confidence: {final_report['Field Confidence']}%")

        st.progress(int(final_report["Verification Confidence"]))
        st.caption(f"Overall Verification Confidence: {final_report['Verification Confidence']}%")

    # ---------- FIELD LEVEL ANALYSIS ----------
    if "Field Validation" in final_report:

        st.markdown("### 🔍 Field-Level Analysis")

        st.markdown("<div class='card'>", unsafe_allow_html=True)

    for field, info in final_report["Field Validation"].items():
        status = "✅" if info["valid"] else "⚠️"
        color = "success" if info["valid"] else "warning"

        st.markdown(
            f"<span class='{color}'>{status} <b>{field}</b></span> — "
            f"<span class='info'>{info['reason']}</span>",
            unsafe_allow_html=True
        )

    st.markdown("</div>", unsafe_allow_html=True)


    # ---------- SUSPICIOUS FLAGS ----------
    if final_report.get("Suspicious Fields"):
        st.warning("⚠️ Suspicious / Missing Fields Detected")
        for s in final_report["Suspicious Fields"]:
            st.write("•", s)

    # ---------- OVERALL INTEGRITY ----------
    integrity = final_report.get("Overall Integrity", "UNKNOWN")
    if integrity == "HIGH":
        st.success("🛡️ Overall Document Integrity: HIGH")
    else:
        st.error("🚨 Overall Document Integrity: REVIEW REQUIRED")


    # ---------- EXPORT PDF ----------
    pdf_path = "verification_report.pdf"
    generate_pdf(final_report, pdf_path)

    with open(pdf_path, "rb") as f:
        st.download_button(
            label="📄 Download Verification Report (PDF)",
            data=f,
            file_name="AI_Govt_ID_Report.pdf",
            mime="application/pdf"
        ) 


# ---------- COMBINED TEXT ----------
if all_text:
    st.subheader("📄 Combined Extracted Text")
    st.text_area("All Text", all_text, height=300)

