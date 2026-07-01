# AI-RESUME-SCANNER
import streamlit as st
import PyPDF2
import json
from groq import Groq

# -------------------------
# PAGE SETTINGS
# -------------------------
st.set_page_config(
    page_title="AI Resume Scanner",
    page_icon="📄",
    layout="wide"
)

st.title("📄 AI Resume Scanner")
st.write("Upload your resume and get ATS score with AI analysis.")

# -------------------------
# GROQ SETUP
# -------------------------
client = Groq(api_key=st.secrets["GROQ_API_KEY"])


def ask_ai(prompt):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",   # Updated model
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content


# -------------------------
# PDF TEXT EXTRACTION
# -------------------------
def extract_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text
    return text


# -------------------------
# LAYOUT
# -------------------------
left, right = st.columns([1, 1])

with left:
    st.subheader("Upload Resume")

    resume_file = st.file_uploader(
        "Upload PDF Resume",
        type=["pdf"]
    )

    job_role = st.text_input(
        "Target Job Role",
        placeholder="e.g. Data Scientist"
    )

    job_desc = st.text_area(
        "Job Description (Optional)",
        height=150
    )

    scan_btn = st.button(
        "Scan Resume",
        use_container_width=True
    )

# -------------------------
# ANALYSIS
# -------------------------
with right:
    if scan_btn:

        if not resume_file:
            st.error("Please upload a PDF resume.")
        elif not job_role:
            st.error("Please enter job role.")
        else:
            with st.spinner("Scanning Resume..."):

                resume_text = extract_pdf(resume_file)

                prompt = f"""
You are an ATS and HR expert.

Analyze this resume for the role: {job_role}

Job description:
{job_desc}

Resume text:
{resume_text[:3000]}

Return ONLY valid JSON.

JSON format:
{{
  "ats_score": 0-100,
  "overall_rating": "Excellent/Good/Average/Poor",
  "strengths": ["","",""],
  "weaknesses": ["","",""],
  "missing_keywords": ["","","","",""],
  "improvement_tips": ["","",""],
  "summary": "Two sentence summary"
}}
"""

                try:
                    raw = ask_ai(prompt).strip()

                    # Clean markdown JSON
                    if "```" in raw:
                        raw = raw.split("```")[1]
                        if raw.startswith("json"):
                            raw = raw[4:]

                    result = json.loads(raw)

                    score = result["ats_score"]

                    if score >= 75:
                        color = "green"
                    elif score >= 50:
                        color = "orange"
                    else:
                        color = "red"

                    st.markdown(
                        f"""
<div style='text-align:center;
padding:20px;
background:#1a1a2e;
border-radius:12px;
border:2px solid {color};'>
<h1 style='color:{color};font-size:64px'>{score}</h1>
<p style='color:white;'>ATS Score / 100</p>
<p style='color:white;'>{result["overall_rating"]}</p>
</div>
""",
                        unsafe_allow_html=True
                    )

                    st.info(result["summary"])

                    c1, c2 = st.columns(2)

                    with c1:
                        st.success("Strengths")
                        for item in result["strengths"]:
                            st.write("•", item)

                        st.error("Weaknesses")
                        for item in result["weaknesses"]:
                            st.write("•", item)

                    with c2:
                        st.warning("Missing Keywords")
                        for item in result["missing_keywords"]:
                            st.write("•", item)

                        st.info("Improvement Tips")
                        for item in result["improvement_tips"]:
                            st.write("•", item)

                except Exception as e:
                    st.error(f"Error: {e}")
