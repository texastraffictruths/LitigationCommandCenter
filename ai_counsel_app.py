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
st.set_page_config(page_title="AI Litigation Command Center", layout="wide")

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
        "checklist": [],
        "outputs": {
            "strategy": "",
            "civil_rights": "",
            "constitution": "",
            "research": "",
            "drafts": "",
            "citations": "",
            "compliance": "",
            "final_review": ""
        }
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

def update_checklist(item):
    if item not in case_data["checklist"]:
        case_data["checklist"].append(item)
        save_case(case_id, case_data)

def log_output(agent, content):
    case_data["outputs"][agent] = content
    save_case(case_id, case_data)

# ---------------------------
# PRELOADED PROMPTS FOR AGENTS
# ---------------------------
AGENT_PROMPTS = {
    "Maxwell (Strategy)": "Build a litigation strategy matrix for this case. Identify claims, legal standards, anticipated defenses, and discovery targets.",
    "Justice (Civil Rights)": "Analyze compliance with 42 U.S.C. §1983 and list missing civil rights elements.",
    "Patriot (Constitution)": "Analyze constitutional conflicts and suggest additional Texas and U.S. constitutional arguments.",
    "Atlas (Research)": "Provide 3 controlling cases on the key issues with proper citations.",
    "Lexi (Drafting)": "Draft a Rule-compliant complaint or motion using the case facts and provided legal authority.",
    "Caleb (Citations)": "Verify all citations for accuracy and Bluebook compliance. Flag invalid authorities.",
    "Regina (Compliance)": "Audit this draft against FRCP and local court rules. List all procedural defects.",
    "Dominic (Final Review)": "Perform final litigation readiness review: structure, argument layering, compliance lock."
}

# ---------------------------
# UI LAYOUT
# ---------------------------
st.title("⚖️ AI Litigation Command Center")

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
            case_data["summary"] += "\n" + raw_text[:500]  # Store snippet
            save_case(case_id, case_data)
            st.success("✅ File processed and added to Summary.")

    # ---------------------------
    # ORCHESTRATION WORKFLOW UI
    # ---------------------------
    st.markdown("### 🧠 Litigation Workflow Engine")
    st.write("Select an Agent to Execute a Task")

    agents = list(AGENT_PROMPTS.keys())
    selected_agent = st.selectbox("Choose Agent", agents)
    custom_input = st.text_area("Task Details or Leave Blank to Use Default Prompt")

    if st.button("Run Task"):
        # For now, simulate agent response (future: connect to LLM)
        task_prompt = custom_input if custom_input else AGENT_PROMPTS[selected_agent]
        response = f"### {selected_agent} Output\n\nPrompt:\n{task_prompt}\n\n(This will be replaced with AI-generated content connected to verified law.)"
        # Save to appropriate section
        agent_key = selected_agent.split(" ")[0].lower()
        log_output(agent_key, response)
        st.success(f"✅ {selected_agent} task completed. Output saved.")

    # ---------------------------
    # OUTPUT DASHBOARD
    # ---------------------------
    tabs = st.tabs(["Strategy", "Civil Rights", "Constitution", "Research", "Drafts", "Citations", "Compliance", "Final Review", "Checklist"])
    with tabs[0]:
        st.markdown(case_data["outputs"]["strategy"] or "No strategy yet.")
    with tabs[1]:
        st.markdown(case_data["outputs"]["civil_rights"] or "No civil rights analysis yet.")
    with tabs[2]:
        st.markdown(case_data["outputs"]["constitution"] or "No constitutional analysis yet.")
    with tabs[3]:
        st.markdown(case_data["outputs"]["research"] or "No research yet.")
    with tabs[4]:
        st.markdown(case_data["outputs"]["drafts"] or "No drafts yet.")
    with tabs[5]:
        st.markdown(case_data["outputs"]["citations"] or "No citation check yet.")
    with tabs[6]:
        st.markdown(case_data["outputs"]["compliance"] or "No compliance report yet.")
    with tabs[7]:
        st.markdown(case_data["outputs"]["final_review"] or "No final review yet.")
    with tabs[8]:
        st.write(case_data["checklist"] or "Checklist empty.")
