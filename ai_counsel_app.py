import streamlit as st
import os
import uuid
import json
import tempfile
from PyPDF2 import PdfReader
from docx import Document
from PIL import Image
import pytesseract

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(page_title="AI Counsel", layout="wide")

# Base folder for cases
BASE_DIR = "cases"
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)

# ---------------------------
# UTIL FUNCTIONS
# ---------------------------
def create_case(case_title):
    case_id = str(uuid.uuid4())[:8]
    case_dir = os.path.join(BASE_DIR, case_id)
    os.makedirs(case_dir)
    case_data = {
        "id": case_id,
        "title": case_title,
        "summary": "",
        "timeline": [],
        "evidence": [],
        "violations": [],
        "checklist": []
    }
    save_case(case_id, case_data)
    return case_id

def save_case(case_id, data):
    with open(os.path.join(BASE_DIR, case_id, "case.json"), "w") as f:
        json.dump(data, f, indent=4)

def load_case(case_id):
    with open(os.path.join(BASE_DIR, case_id, "case.json"), "r") as f:
        return json.load(f)

def extract_text_from_file(file):
    text = ""
    if file.name.endswith(".pdf"):
        reader = PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ""
    elif file.name.endswith(".docx"):
        doc = Document(file)
        for p in doc.paragraphs:
            text += p.text + "\n"
    elif file.name.lower().endswith(('.png', '.jpg', '.jpeg')):
        img = Image.open(file)
        text += pytesseract.image_to_string(img)
    return text.strip()

def classify_text(raw_text):
    # Placeholder for classification logic
    summary = raw_text[:500] + "..." if len(raw_text) > 500 else raw_text
    timeline = [line for line in raw_text.split("\n") if any(word in line.lower() for word in ["date", "time", "on", "at"])]
    evidence = [line for line in raw_text.split("\n") if "exhibit" in line.lower() or "photo" in line.lower()]
    violations = [line for line in raw_text.split("\n") if any(word in line.lower() for word in ["violation", "amendment", "rights"])]
    return summary, timeline, evidence, violations

# ---------------------------
# UI LAYOUT
# ---------------------------
st.title("⚖️ AI Counsel - Your Legal Second Chair")

menu = st.sidebar.radio("Navigation", ["Dashboard", "Open Case"])

if menu == "Dashboard":
    st.header("Create a New Case")
    case_title = st.text_input("Case Title")
    if st.button("Create Case") and case_title:
        case_id = create_case(case_title)
        st.success(f"✅ Case created with ID: {case_id}")
        st.session_state["active_case"] = case_id

elif menu == "Open Case":
    case_dirs = [d for d in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, d))]
    if not case_dirs:
        st.warning("No cases found. Create a new case first.")
    else:
        case_id = st.selectbox("Select Case ID", case_dirs)
        if st.button("Load Case"):
            st.session_state["active_case"] = case_id

# ---------------------------
# ACTIVE CASE VIEW
# ---------------------------
if "active_case" in st.session_state:
    case_id = st.session_state["active_case"]
    case_data = load_case(case_id)

    st.subheader(f"📂 Case: {case_data['title']} ({case_id})")

    # File Upload
    uploaded_file = st.file_uploader("Upload legal file (PDF, DOCX, JPG, PNG):", type=["pdf", "docx", "jpg", "jpeg", "png"])
    if uploaded_file:
        raw_text = extract_text_from_file(uploaded_file)
        if raw_text:
            summary, timeline, evidence, violations = classify_text(raw_text)
            case_data["summary"] += "\n" + summary
            case_data["timeline"].extend(timeline)
            case_data["evidence"].extend(evidence)
            case_data["violations"].extend(violations)
            save_case(case_id, case_data)
            st.success("✅ File processed and data updated.")

    # Sidebar Tabs
    tabs = st.tabs(["Summary", "Timeline", "Evidence", "Violations", "Checklist"])
    with tabs[0]:
        st.text_area("Summary", value=case_data["summary"], height=300)
    with tabs[1]:
        st.write(case_data["timeline"])
    with tabs[2]:
        st.write(case_data["evidence"])
    with tabs[3]:
        st.write(case_data["violations"])
    with tabs[4]:
        st.write(case_data["checklist"])
