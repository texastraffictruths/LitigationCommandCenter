import streamlit as st
import os
import uuid
import json
import re
import time
from PyPDF2 import PdfReader
from docx import Document
from PIL import Image
import pytesseract

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(page_title="AI Counsel", layout="wide")

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
    summary = raw_text[:500] + "..." if len(raw_text) > 500 else raw_text
    timeline = [line for line in raw_text.split("\n") if any(word in line.lower() for word in ["date","time","on","at"])]
    evidence = [line for line in raw_text.split("\n") if "exhibit" in line.lower() or "photo" in line.lower()]
    violations = [line for line in raw_text.split("\n") if any(word in line.lower() for word in ["violation","amendment","rights"])]
    return summary, timeline, evidence, violations

# ---------------------------
# HANDLER FUNCTIONS
# ---------------------------
def add_checklist_item(item):
    if item not in case_data["checklist"]:
        case_data["checklist"].append(item)

def process_user_input(text):
    lower_text = text.lower()
    case_data["summary"] += f"\nUser: {text}"

    # Detect timeline (dates)
    if re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', lower_text) or any(m in lower_text for m in ["january","february","march","april","may","june","july","august","september","october","november","december"]):
        case_data["timeline"].append(text)
    else:
        add_checklist_item("Confirm date and time of incident")

    # Evidence detection
    if any(word in lower_text for word in ["photo","screenshot","exhibit","document","receipt"]):
        case_data["evidence"].append(text)
        add_checklist_item("Upload referenced evidence")

    # Violations detection
    if any(word in lower_text for word in ["rights","amendment","constitutional","illegal","violation","due process","excessive force"]):
        case_data["violations"].append(text)

    save_case(case_id, case_data)

def generate_follow_up():
    if "Confirm date and time of incident" in case_data["checklist"]:
        return "Can you provide the exact date and time of the incident?"
    elif not case_data["violations"]:
        return "Do you believe any of your constitutional rights were impacted? If so, which ones?"
    elif not case_data["evidence"]:
        return "Do you have any evidence like photos or documents?"
    else:
        return "Please walk me through the sequence of events step by step."

def explain_concept(concept):
    law_library = {
        "excessive force": {
            "definition": "Excessive force refers to force that exceeds what a reasonable officer would deem necessary under the circumstances.",
            "source": "Graham v. Connor, 490 U.S. 386 (1989)"
        },
        "due process": {
            "definition": "Due process means the government must follow fair and consistent procedures before depriving you of life, liberty, or property.",
            "source": "U.S. Const. amend. XIV"
        },
        "section 1983": {
            "definition": "42 U.S.C. § 1983 provides a civil cause of action for the deprivation of constitutional rights under color of state law.",
            "source": "42 U.S.C. § 1983"
        }
    }
    concept_key = concept.lower().strip()
    if concept_key in law_library:
        return f"**Definition:** {law_library[concept_key]['definition']}\n**Source:** {law_library[concept_key]['source']}"
    else:
        return "⚠ No verified source found for that concept. Please confirm manually."

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

    # Handler Section
    st.subheader("🧑‍⚖️ Handler Interview Mode")
    if "chat_log" not in st.session_state:
        st.session_state["chat_log"] = []

    user_input = st.text_input("Describe what happened or ask a legal term:")
    if st.button("Submit"):
        if user_input.strip():
            st.session_state["chat_log"].append({"role":"user","text":user_input})
            process_user_input(user_input)

            if "what is" in user_input.lower() or "explain" in user_input.lower():
                concept = user_input.split(" ", 2)[-1]
                response = explain_concept(concept)
            else:
                response = generate_follow_up()

            st.session_state["chat_log"].append({"role":"handler","text":response})

    # Display chat history
    for msg in st.session_state["chat_log"]:
        if msg["role"] == "user":
            st.write(f"**You:** {msg['text']}")
        else:
            st.info(f"Handler: {msg['text']}")

    # Quick Actions
    st.markdown("### ⚡ Quick Actions")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Explain 'Section 1983'"):
            response = explain_concept("section 1983")
            st.session_state["chat_log"].append({"role":"handler","text":response})
    with col2:
        if st.button("Summarize Facts"):
            summary_preview = case_data["summary"][:500] + "..." if len(case_data["summary"]) > 500 else case_data["summary"]
            st.session_state["chat_log"].append({"role":"handler","text":f"Here's a quick summary:\n{summary_preview}"})
    with col3:
        if st.button("Show Missing Info"):
            if case_data["checklist"]:
                st.session_state["chat_log"].append({"role":"handler","text":f"You still need to complete:\n{', '.join(case_data['checklist'])}"})
            else:
                st.session_state["chat_log"].append({"role":"handler","text":"All checklist items completed so far!"})

    # Show Tabs
    tabs = st.tabs(["Summary","Timeline","Evidence","Violations","Checklist"])
    with tabs[0]: st.text_area("Summary", value=case_data["summary"], height=300)
    with tabs[1]: st.write(case_data["timeline"])
    with tabs[2]: st.write(case_data["evidence"])
    with tabs[3]: st.write(case_data["violations"])
    with tabs[4]: st.write(case_data["checklist"])
