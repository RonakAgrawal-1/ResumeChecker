import streamlit as st
import re
from PyPDF2 import PdfReader
from io import BytesIO
import docx2txt
from skills_keywords import skills_keywords
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Function to extract the candidate's name from the resume
def extract_candidate_name(text):
    try:
        name_pattern = r'\b[A-Z][a-zA-Z]* [A-Z][a-zA-Z]*\b'
        candidate_name = re.search(name_pattern, text)
        return candidate_name.group() if candidate_name else "Name not found"
    except Exception as e:
        return {"error": str(e)}

# Function to extract GitHub link from the resume text
def extract_github_link(text):
    try:
        # Search for GitHub link keywords in the text
        github_keywords = ["github.com/", "https://github.com/"]
        for keyword in github_keywords:
            if keyword in text.lower():
                start_index = text.lower().index(keyword)
                end_index = text.find(" ", start_index)
                github_link = text[start_index:end_index].strip()
                return github_link

        return "GitHub link not found"
    except Exception as e:
        return {"error": str(e)}

# Function to extract the GitHub username from the URL
def extract_username_from_url(github_link):
    parsed_url = urlparse(github_link)
    if parsed_url.netloc == "github.com":
        # Extract the username from the URL path
        path_parts = parsed_url.path.strip("/").split("/")
        if len(path_parts) >= 1:
            return path_parts[0]
    return None

# Function to fetch user repositories
def fetch_user_repositories(username):
    url = f"https://api.github.com/users/{username}/repos"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return []

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

# Function to extract text from a DOCX file
def extract_text_from_docx(uploaded_file):
    try:
        text = docx2txt.process(uploaded_file)
        return text
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
    page_title="Resume and GitHub Analyzer",
    page_icon=":page_with_curl:"
)

# Introduction Section
st.write("First skill keyword:", skills_keywords[0])
st.title("Welcome to the Resume and GitHub Profile Analyzer!")
st.write("This tool helps you extract and analyze information from resumes and GitHub profiles.")
st.write("Follow these steps to get started:")
st.markdown("1. Upload a resume in PDF or DOC/DOCX format using the 'Upload Resume' section below.")
st.markdown("2. Enter the job description in the 'Enter Job Description' section below.")
st.markdown("3. Click the 'Analyze' button to see the results.")

# Create a sidebar for inputs
st.sidebar.title("Resume and GitHub Analyzer")

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

            # Extract GitHub link from the candidate's resume text
            github_link = extract_github_link(resume_text)
            st.subheader("GitHub Link")
            if "error" in github_link:
                st.write(f"Error: {github_link['error']}")
            else:
                # Check if the link is missing "https://" and add it if necessary
                if not github_link.startswith("https://"):
                    github_link = "https://" + github_link
                st.write(f"The candidate's GitHub link is: [{github_link}]({github_link})")

            # Analyze GitHub profile if a link is found
            if github_link and not "GitHub link not found" in github_link:
                username = extract_username_from_url(github_link)
                if username:
                    user_repositories = fetch_user_repositories(username)
                    if user_repositories:
                        st.subheader(f"GitHub Repositories for {username}:")
                        repo_names = []
                        repo_languages = set()
                        for repo in user_repositories:
                            repo_name = repo.get("name", "")
                            repo_language = repo.get("language", "")
                            if repo_name:
                                repo_names.append(repo_name)
                            if repo_language:
                                repo_languages.add(repo_language)

                        # Format the repository names and technologies
                        formatted_repo_names = [f"- {name}" for name in repo_names]
                        formatted_repo_languages = [f"- {language}" for language in repo_languages]

                        st.write("Repositories:")
                        for name in formatted_repo_names:
                            st.write(name)

                        st.write("Technologies:")
                        for language in formatted_repo_languages:
                            st.write(language)
                    else:
                        st.write(f"No repositories found for {github_link}.")
                else:
                    st.write("Invalid GitHub profile link. Please check the link format.")
            else:
                st.write("No GitHub link found in the resume.")

            # Candidate Name
            st.subheader("Candidate Name")
            candidate_name = extract_candidate_name(resume_text)
            st.write(f"The candidate's name is: {candidate_name}")

            # Matching Score
            st.subheader("Matching Score")
            extracted_skills = extract_candidate_skills(resume_text)
            score, common_skills = calculate_matching_score(extracted_skills, job_description_text)

            # Define colors based on the matching score
            if score >= 0.8:
                score_color = "green"
            elif 0.5 <= score < 0.8:
                score_color = "orange"
            else:
                score_color = "red"

            # Create a circular progress bar
            progress_html = f"""
                <div style="text-align: center;">
                    <svg width="120" height="120" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="60" cy="60" r="54" fill="none" stroke="#e6e6e6" stroke-width="12"></circle>
                        <circle cx="60" cy="60" r="54" fill="none" stroke="{score_color}" stroke-width="12"
                                stroke-dasharray="{score * 339}" stroke-dashoffset="0" transform="rotate(-90 60 60)">
                        </circle>
                        <text x="50%" y="50%" text-anchor="middle" dominant-baseline="middle" font-size="24" fill="{score_color}">
                            {int(score * 100)}%
                        </text>
                    </svg>
                </div>
            """

            st.markdown(progress_html, unsafe_allow_html=True)
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
