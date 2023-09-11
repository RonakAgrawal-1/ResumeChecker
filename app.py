import streamlit as st
import re
from PyPDF2 import PdfReader
from io import BytesIO
import docx2txt
from skills_keywords import skills_keywords

# Function to extract text from a DOC file
def extract_text_from_docx(uploaded_file):
    try:
        text = docx2txt.process(uploaded_file)
        return text
    except Exception as e:
        return {"error": str(e)}

# Function to extract text from a PDF file
def extract_text_from_pdf(uploaded_file):
    try:
        resume_content = uploaded_file.read()
        pdf = PdfReader(BytesIO(resume_content))
        text = ""
        for page in pdf.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        return {"error": str(e)}

# Function to extract the candidate's name from the resume
def extract_candidate_name(text):
    try:
        name_pattern = r'\b[A-Z][a-zA-Z]* [A-Z][a-zA-Z]*\b'
        candidate_name = re.search(name_pattern, text)
        return candidate_name.group() if candidate_name else "Name not found"
    except Exception as e:
        return {"error": str(e)}

# Function to extract skills from the resume text
def extract_candidate_skills(text):
    try:
        skills = list(set([skill.lower().capitalize() for skill in skills_keywords if re.search(rf'\b{skill}\b', text, re.IGNORECASE)]))
        return skills
    except Exception as e:
        return {"error": str(e)}

# Function to extract skills from the user-provided job description text
def extract_job_description_skills(job_description_text):
    try:
        skills = list(set([skill.lower().capitalize() for skill in skills_keywords if re.search(rf'\b{skill}\b', job_description_text, re.IGNORECASE)]))
        return skills
    except Exception as e:
        return {"error": str(e)}

# Function to calculate the matching score based on skills
def calculate_matching_score(candidate_skills, job_description_text):
    job_skills = extract_job_description_skills(job_description_text)
    common_skills = list(set(candidate_skills) & set(job_skills))
    
    if job_skills:
        score = len(common_skills) / len(job_skills)
    else:
        score = 0.0
    
    return score, common_skills

# Set Streamlit page title and icon
st.set_page_config(
    page_title="Resume Info Extractor",
    page_icon=":page_with_curl:"
)

# Introduction Section
st.title("Welcome to the Resume Information Extractor!")
st.write("This tool helps you extract and analyze information from resumes.")
st.write("Follow these steps to get started:")
st.markdown("1. Upload a resume in PDF or DOC/DOCX format using the 'Upload Resume' section in the sidebar.")
st.markdown("2. Enter the job description in the 'Enter Job Description' section in the sidebar.")
st.markdown("3. Click the 'Analyze' button in the sidebar to see the results.")

# Create a sidebar for inputs
st.sidebar.title("Resume Info Extractor")

# Upload Resume Section in Sidebar
st.sidebar.subheader("Step 1: Upload Resume")
uploaded_file = st.sidebar.file_uploader("Upload your resume (PDF or DOC/DOCX)")

# Enter Job Description Section in Sidebar
st.sidebar.subheader("Step 2: Enter Job Description")
job_description_text = st.sidebar.text_area("Enter the job description")

# Analyze Button in Sidebar
if st.sidebar.button("Analyze"):
    if not uploaded_file or not job_description_text:
        st.warning("Please complete both steps to analyze.")
    else:
        with st.spinner("Analyzing..."):
            # Extract text from the uploaded resume file
            if uploaded_file.type == "application/pdf":
                resume_text = extract_text_from_pdf(uploaded_file)
            elif uploaded_file.type in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
                resume_text = extract_text_from_docx(uploaded_file)
            else:
                st.error("Unsupported file format. Please upload a PDF or DOC/DOCX file.")
                st.stop()

            # Extract skills from the candidate's resume text
            extracted_skills = extract_candidate_skills(resume_text)
            
            # Calculate the matching score
            score, common_skills = calculate_matching_score(extracted_skills, job_description_text)

            # Display Results Section
            st.title("Analysis Results")

            # Candidate Name
            st.subheader("Candidate Name")
            candidate_name = extract_candidate_name(resume_text)
            st.write(f"The candidate's name is: {candidate_name}")

            # Matching Score
            st.subheader("Matching Score")
            st.write(f"The matching score with the job description is: {score:.2%}")

            # Skills Extracted
            st.subheader("Skills Extracted from Resume")
            if extracted_skills:
                st.write(", ".join(extracted_skills))
            else:
                st.warning("No skills found in the resume.")

            # Common Skills
            st.subheader("Common Skills with Job Description")
            if common_skills:
                st.write(", ".join(common_skills))
            else:
                st.warning("No common skills found between the job description and the candidate's skills.")
