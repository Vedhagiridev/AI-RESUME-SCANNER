import streamlit as st
import PyPDF2
import json
import os
from groq import Groq
from dotenv import load_dotenv

# ---------------------------
# Load API Key
# ---------------------------
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

client = Groq(api_key=api_key)

# ---------------------------
# AI Function
# ---------------------------
def ask_ai(prompt):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content


# ---------------------------
# PDF Text Extraction
# ---------------------------
def extract_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text

    return text


# ---------------------------
# Streamlit UI
# ---------------------------
st.set_page_config(page_title="AI Resume Scanner", layout="wide")

st.title("AI Resume Scanner")
st.write("Upload resume and get ATS score")

left, right = st.columns(2)

with left:
    st.subheader("Upload Resume")

    resume_file = st.file_uploader(
        "Upload PDF Resume",
        type=["pdf"]
    )

    job_role = st.text_input(
        "Target Job Role",
        placeholder="Example: Data Scientist"
    )

    job_desc = st.text_area(
        "Job Description (Optional)",
        height=150
    )

    scan_btn = st.button(
        "Scan Resume",
        use_container_width=True
    )


with right:
    if scan_btn:

        if not resume_file:
            st.error("Please upload resume")
        elif not job_role:
            st.error("Please enter job role")
        else:
            with st.spinner("Scanning Resume..."):

                resume_text = extract_pdf(resume_file)

                prompt = f"""
You are an ATS and HR expert.

Analyze this resume for role: {job_role}

Resume:
{resume_text[:3000]}

Job Description:
{job_desc}

Return ONLY valid JSON.

Format:
{{
"ats_score": 0-100,
"overall_rating": "Excellent/Good/Average/Poor",
"strengths": ["","",""],
"weaknesses": ["","",""],
"missing_keywords": ["","","","",""],
"improvement_tips": ["","",""],
"summary": "2 sentence summary"
}}
"""

                raw = ask_ai(prompt).strip()

                try:
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
<div style='text-align:center;padding:20px;
background:#1a1a2e;border-radius:12px;
border:2px solid {color};'>
<h1 style='color:{color};font-size:64px'>{score}</h1>
<p>ATS Score / 100</p>
<p>{result["overall_rating"]}</p>
</div>
""",
                        unsafe_allow_html=True
                    )

                    st.info(result["summary"])

                    c1, c2 = st.columns(2)

                    with c1:
                        st.success("Strengths")
                        for s in result["strengths"]:
                            st.write("- " + s)

                        st.error("Weaknesses")
                        for w in result["weaknesses"]:
                            st.write("- " + w)

                    with c2:
                        st.warning("Missing Keywords")
                        for k in result["missing_keywords"]:
                            st.write("- " + k)

                        st.info("Improvement Tips")
                        for t in result["improvement_tips"]:
                            st.write("- " + t)

                except Exception as e:
                    st.error("Error parsing AI response")
                    st.code(raw)
