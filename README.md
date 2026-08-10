# 📄 AI Resume Analyzer

**AI-powered ATS scoring, job matching & career insights**

A modern, dark-themed resume analysis tool that scores resumes for ATS (Applicant Tracking System) compatibility, matches candidates to relevant career paths from a structured 45-role knowledge base, and surfaces live remote job listings — all in a single Streamlit web app.

🔗 **Live demo:** [ai-resume-analyzer-7g3gbzi6jxpwdwwj3fe6qn.streamlit.app](https://ai-resume-analyzer-7g3gbzi6jxpwdwwj3fe6qn.streamlit.app/)

---

## ✨ Features

- **ATS Compatibility Score** — 0–100 score with a visual gauge, based on resume structure, writing quality, and (optionally) job-description keyword match
- **Score Breakdown** — weighted bar chart across Resume Sections, Keywords, Action Verbs, Quantifiable Results, and Resume Length
- **Resume Health Check** — detects standard sections (Contact Info, Summary, Experience, Education, Skills, Projects, Certifications)
- **Certification Detection** — pulls real certification names from the resume text (not just section headings)
- **Job Description Matching** — compares resume keywords against a pasted job posting, showing matched vs. missing keywords
- **Writing Quality Analysis** — flags weak/generic phrases and rewards strong action verbs
- **Smart Recommendations** — prioritized, rule-based suggestions (High / Medium / Suggestion)
- **Resume Improvement Examples** — before/after rewrite templates for weak phrases
- **Best Career Matches** — weighted matching against a structured knowledge base of **45 career profiles** across 11 industries (AI/GenAI, Data, Software, Cloud/DevOps, Cybersecurity, FinTech, Healthcare, Green Energy, Business, Marketing/Design, Education)
- **Live Remote Job Listings** — real, currently-open remote jobs pulled from the RemoteOK public API, filtered to match the candidate's top career category
- **Downloadable Analysis Report** — full results exportable as a `.txt` file

---

## 🖼️ Screenshots

![App Screenshot](Screenshot%202026-08-09%20235939.png)

---

## 🛠️ Tech Stack

- **Python**
- **Streamlit** — UI framework
- **Plotly** — gauge & breakdown charts
- **PyPDF2** — PDF text extraction
- **Requests** — RemoteOK live job API integration

---

## 🚀 Run Locally

```bash
git clone https://github.com/AroonKumarMaheshwari-11/AI-resume-analyzer.git
cd AI-resume-analyzer
pip install -r requirements.txt
python -m streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## ☁️ Deployment

This app is deployed for free on [Streamlit Community Cloud](https://streamlit.io/cloud). Any push to the `main` branch automatically redeploys the live app.

---

## 🧠 How the Career Matching Works

Instead of simple flat keyword matching, each of the 45 career profiles is scored using **weighted signals**:

| Signal type      | Weight |
|-------------------|--------|
| Core keywords      | 3      |
| Skills              | 2      |
| Certifications      | 2      |
| Tools                | 1      |

A career is only shown as a match if it clears **both** a minimum number of distinct matched signals *and* a minimum total weight — this prevents a single incidental keyword (e.g. a short acronym that happens to appear inside an unrelated word) from producing a misleading recommendation. Closely related roles (e.g. AI Engineer / ML Engineer) are grouped by family, and only the strongest role per family is shown, so results read as distinct career directions.

---

## 📌 Disclaimer

This tool provides a **heuristic-based estimate** for guidance purposes only. It is not a guarantee of how any specific company's real ATS software will score a resume.

---

## 👤 Developer

**AI Resume Analyzer** • Developed by **Aroon Kumar Maheshwari**
Built with Python • Streamlit • Plotly • PyPDF2

---

## 🔒 Security notes (fixed for internship submission)

- Admin password is now read from `st.secrets["ADMIN_PASSWORD"]` (or the
  `ADMIN_PASSWORD` environment variable) — never hardcoded. Set it via
  Streamlit Cloud's "Secrets" panel, or a local `.env` (see `.env.example`).
  If it isn't set, the admin panel simply stays disabled.
- `usage_log.csv` (real visitor data) is no longer committed and is now in
  `.gitignore`.
- All dynamic content inserted via `unsafe_allow_html=True` — resume-derived
  text (certifications) and third-party API data (RemoteOK job listings) —
  is now HTML-escaped to prevent XSS. Job listing URLs are scheme-validated.
- PDF extraction is wrapped in error handling with a friendly message
  instead of crashing/showing a traceback on corrupt or encrypted files.
- Uploads over 10 MB are rejected before processing.
- Switched from the unmaintained `PyPDF2` to `pypdf`.
