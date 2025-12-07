# app.py
import streamlit as st
import requests
import json

# CHANGE THIS if running backend locally:
# BACKEND_URL = "http://127.0.0.1:8000"
BACKEND_URL = "https://invoice-qc-service-lakshmi.onrender.com"

st.set_page_config(
    page_title="Invoice QC System",
    layout="wide",
    page_icon="🧾",
)

st.title("🧾 Invoice QC System (Multilingual + AI Chat)")


# ============================================================
# SIDEBAR → UPLOAD
# ============================================================
st.sidebar.header("📤 Upload Invoices")

uploaded_files = st.sidebar.file_uploader(
    "Select one or more invoice files (PDF, PNG, JPG)",
    type=["pdf", "png", "jpg", "jpeg"],
    accept_multiple_files=True,
)

# OCR status info
try:
    ocr_res = requests.get(f"{BACKEND_URL}/ocr-status", timeout=3)
    ocr_ok = ocr_res.json().get("ocr_available", False)
except Exception:
    ocr_ok = False

if not ocr_ok:
    st.sidebar.warning("OCR not available on server — image invoices may not parse well.")
else:
    st.sidebar.info("OCR available: image invoices will be OCR’ed server-side.")

process_btn = st.sidebar.button("Process Invoices")


# ============================================================
# PROCESS PDFs/IMAGES
# ============================================================
if process_btn and uploaded_files:
    with st.spinner("Extracting + validating invoices..."):
        files = []
        for f in uploaded_files:
            mime = getattr(f, "type", None) or "application/octet-stream"
            files.append(("files", (f.name, f, mime)))

        try:
            res = requests.post(f"{BACKEND_URL}/extract-and-validate-pdfs", files=files)
        except Exception as e:
            st.error(f"❌ Could not reach backend: {e}")
            st.stop()

        if res.status_code != 200:
            st.error("❌ Backend returned an error.")
            st.text(res.text)
            st.stop()

        data = res.json()
        st.session_state["invoices"] = data["invoices"]
        st.session_state["summary"] = data["summary"]
        st.session_state["results"] = data["results"]
        st.session_state.setdefault("messages", [])

        st.success("Invoices processed successfully!")


# ============================================================
# SHOW EXTRACTED INVOICES
# ============================================================
if "invoices" in st.session_state:
    st.subheader("📄 Extracted Invoice Data")
    st.json(st.session_state["invoices"])

# ============================================================
# SHOW VALIDATION SUMMARY
# ============================================================
if "summary" in st.session_state:
    st.subheader("✅ Validation Summary")
    st.json(st.session_state["summary"])


# ============================================================
# CHATBOT SECTION
# ============================================================
if "invoices" in st.session_state:
    st.subheader("💬 Ask the AI About Your Invoices (Any Language!)")

    # Existing chat history
    for msg in st.session_state["messages"]:
        role = "🧑 User" if msg["role"] == "user" else "🤖 AI"
        st.markdown(f"**{role}:** {msg['content']}")

    user_input = st.text_input("Ask your question:")

    if st.button("Send"):
        if not user_input.strip():
            st.warning("Please type a question.")
        else:
            payload = {
                "invoices": st.session_state["invoices"],
                "summary": st.session_state["summary"],
                "question": user_input,
            }

            try:
                res = requests.post(f"{BACKEND_URL}/chat-direct", json=payload)
            except Exception as e:
                st.error(f"❌ Could not reach backend: {e}")
                st.stop()

            if res.status_code != 200:
                st.error("❌ Chat endpoint error.")
                st.text(res.text)
            else:
                data = res.json()
                answer = data.get("answer", "No answer returned.")

                st.session_state["messages"].append(
                    {"role": "user", "content": user_input}
                )
                st.session_state["messages"].append(
                    {"role": "assistant", "content": answer}
                )

                st.rerun()
