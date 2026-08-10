# 📄 AI Resume Analyzer

**AI-powered ATS scoring, job matching & career insights.**

A dark-themed resume analysis tool that scores resumes for ATS (Applicant Tracking System) compatibility, matches candidates to relevant career paths from a structured 45-role knowledge base, and surfaces live remote job listings — all in a single Streamlit web app.

🔗 **Live demo:** [ai-resume-analyzer-6fyqzmczo7xbmn2afrmzkg.streamlit.app](https://ai-resume-analyzer-6fyqzmczo7xbmn2afrmzkg.streamlit.app/)

---

## ✨ Features

- **ATS Compatibility Score** — 0–100 score with a visual gauge, based on resume structure, writing quality, and (optionally) job-description keyword match
- **Score Breakdown** — weighted bar chart across Resume Sections, Keywords, Action Verbs, Quantifiable Results, and Resume Length
- **Resume Health Check** — detects standard sections (Contact Info, Summary, Experience, Education, Skills, Projects, Certifications)
- **Certification Detection** — pulls real certification names from the resume text
- **Job Description Matching** — compares resume keywords against a pasted job posting
- **Writing Quality Analysis** — flags weak/generic phrases and rewards strong action verbs
- **Smart Recommendations** — prioritized suggestions (High / Medium / Suggestion)
- **Best Career Matches** — weighted matching across a 45-role knowledge base spanning 11 industries
- **Hybrid Local AI** — optional semantic skill matching via `sentence-transformers` (runs fully locally, no paid API key required)
- **Live Remote Job Listings** — pulled from the RemoteOK public API
- **Downloadable Analysis Report**

---

## 🛠️ Tech Stack

- **Python 3**
- **Streamlit** — UI framework
- **Plotly** — gauge & breakdown charts
- **pypdf** + **PyMuPDF** — PDF text extraction
- **sentence-transformers** — local semantic matching (optional)
- **pandas** — analytics dashboard
- **Requests** — RemoteOK live job API integration

---

## 🔐 Security

This project follows standard secure-development practice. No credentials, passwords, or secrets are stored in the source code — everything sensitive is configured privately outside the repository, following the setup guide.

Admin/setup instructions are maintained privately and are not part of this public repository.

---

## 🚀 Run Locally

```bash
git clone https://github.com/AroonKumarMaheshwari-11/AI-resume-analyzer.git
cd AI-resume-analyzer
pip install -r requirements.txt
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## ☁️ Deployment

Deployed on [Streamlit Community Cloud](https://streamlit.io/cloud). Every push to `main` auto-redeploys the live app.

---

## 🧠 How Career Matching Works

Each of the 45 career profiles is scored using weighted signals (core keywords, skills, certifications, tools). A role only qualifies as a match if it clears a minimum threshold of relevant signals, preventing a single incidental keyword from producing a misleading recommendation. Closely related roles are grouped by family, so results read as distinct career directions.

---

## 📌 Disclaimer

This tool provides a **heuristic-based estimate** for guidance purposes only. It is not a guarantee of how any specific company's real ATS software will score a resume.

---

## 👤 Developer

**AI Resume Analyzer** • Developed by **Aroon Kumar Maheshwari**
Built with Python • Streamlit • Plotly • pypdf • PyMuPDF
