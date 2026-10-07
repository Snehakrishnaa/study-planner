import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from PIL import Image
import pytesseract
import json

# ------------------ SETUP ------------------
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel('gemini-2.5-flash')

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ------------------ SESSION STATE ------------------
if "plan" not in st.session_state:
    st.session_state["plan"] = ""

if "extracted_syllabus_text" not in st.session_state:
    st.session_state["extracted_syllabus_text"] = ""

if "extracted_pyq_text" not in st.session_state:
    st.session_state["extracted_pyq_text"] = ""

# ------------------ AI FUNCTION ------------------
def generate_plan(syllabus, pyqs, days, hours, difficulty):
    prompt = f"""
    You are an AI study planner.

    Syllabus:
    {syllabus}

    Previous Year Questions:
    {pyqs}

    Days: {days}
    Hours per day: {hours}
    Difficulty: {difficulty}

    Instructions:
    - Use ONLY syllabus topics
    - Prioritize based on PYQs
    - Each day must include time allocation (in hours)
    - Return STRICT JSON format

    Format:
    {{
      "high_priority": ["topic1"],
      "medium_priority": ["topic1"],
      "low_priority": ["topic1"],
      "study_plan": [
        "Day 1: Topic (2 hrs)",
        "Day 2: Topic (3 hrs)"
      ]
    }}
    """

    response = model.generate_content(prompt)
    return response.text

# ------------------ PDF FUNCTION ------------------
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def create_pdf(text):
    file_path = "study_plan.pdf"
    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()

    content = []

    for line in text.split("\n"):
        content.append(Paragraph(line, styles["Normal"]))
        content.append(Spacer(1, 10))

    doc.build(content)

    return file_path

# ------------------ UI ------------------
st.set_page_config(page_title="AI Study Planner", layout="centered")

st.title("📚 AI Study Planner")

# ------------------ INPUTS ------------------
subject = st.text_input("Enter subject")
syllabus = st.text_area("Enter Syllabus", key="syllabus_box")

pyqs = st.text_area("Enter PYQs", key="pyq_box")

days = st.number_input("Days", 1, 60, 7)
hours = st.number_input("Hours per day", 1, 12, 3)

difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])

# ------------------ IMAGE UPLOAD ------------------
st.subheader("📸 Upload Images (Optional)")

syllabus_image = st.file_uploader("Upload Syllabus Image", type=["png", "jpg"])
pyq_image = st.file_uploader("Upload PYQ Image", type=["png", "jpg"])

# OCR extraction
if syllabus_image is not None:
    image = Image.open(syllabus_image)
    st.image(image, caption="Syllabus Image", width="stretch")

    if st.session_state["extracted_syllabus_text"] == "":
        st.session_state["extracted_syllabus_text"] = pytesseract.image_to_string(image)

    st.write(st.session_state["extracted_syllabus_text"])

if pyq_image is not None:
    image = Image.open(pyq_image)
    st.image(image, caption="PYQ Image", width="stretch")

    if st.session_state["extracted_pyq_text"] == "":
        st.session_state["extracted_pyq_text"] = pytesseract.image_to_string(image)

    st.write(st.session_state["extracted_pyq_text"])

# ------------------ GENERATE ------------------
if st.button("Generate Plan"):
    if not syllabus:
        st.error("Please enter syllabus")
    else:
        with st.spinner("Generating..."):
            final_syllabus = syllabus + "\n" + st.session_state["extracted_syllabus_text"]
            final_pyqs = pyqs + "\n" + st.session_state["extracted_pyq_text"]

            plan = generate_plan(final_syllabus, final_pyqs, days, hours, difficulty)

            st.session_state["plan"] = plan

# ------------------ REVIEW ------------------
if st.session_state["plan"]:
    st.subheader("📝 Review and Edit Plan")

    edited_plan = st.text_area(
        "Modify if needed:",
        st.session_state["plan"],
        height=300,
        key="edit_plan_box"
    )

    if st.button("Approve Final Plan"):
        st.success("✅ Final Plan")

        try:
            cleaned = edited_plan.strip().replace("```json", "").replace("```", "")
            data = json.loads(cleaned)

            st.markdown("### 🔥 High Priority")
            st.write(data["high_priority"])

            st.markdown("### ⚖️ Medium Priority")
            st.write(data["medium_priority"])

            st.markdown("### 💤 Low Priority")
            st.write(data["low_priority"])

            st.markdown("### 📅 Study Plan")
            for day in data["study_plan"]:
                st.write(day)

        except Exception as e:
            st.error("Parsing failed")
            st.write(edited_plan)

        # PDF download
        pdf_file = create_pdf(edited_plan)

        with open(pdf_file, "rb") as f:
            st.download_button(
                "📥 Download PDF",
                f,
                file_name="study_plan.pdf",
                mime="application/pdf"
            )

# ------------------ CLEAR ------------------
if st.button("Clear Data"):
    st.session_state["plan"] = ""
    st.session_state["extracted_syllabus_text"] = ""
    st.session_state["extracted_pyq_text"] = ""