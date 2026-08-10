# 📄 AI Resume Analyzer

**AI-powered ATS scoring, job matching & career insights — built secure by design.**

A dark-themed resume analysis tool that scores resumes for ATS (Applicant Tracking System) compatibility, matches candidates to relevant career paths from a structured 45-role knowledge base, and surfaces live remote job listings — all in a single Streamlit web app.

🔗 **Live demo:** [ai-resume-analyzer-7g3gbzi6jxpwdwwj3fe6qn.streamlit.app](https://ai-resume-analyzer-7g3gbzi6jxpwdwwj3fe6qn.streamlit.app/)

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
- **pypdf** + **PyMuPDF** — PDF text extraction (multi-parser for better accuracy)
- **sentence-transformers** — local semantic matching (optional)
- **pandas** — admin analytics dashboard
- **Requests** — RemoteOK live job API integration

---

## 🔐 Security

This project was built and hardened following standard secure-development practice. It does **not** ship with any hardcoded credentials, secrets, or plaintext passwords in source control.

| Area | Protection |
|---|---|
| **Admin authentication** | Username + password, never hardcoded. Loaded only from `st.secrets` or environment variables. |
| **Password storage** | Salted **PBKDF2-HMAC-SHA256** (310,000 iterations) — passwords are never stored or logged in plaintext. |
| **Password comparison** | Constant-time comparison (`secrets.compare_digest`) to prevent timing attacks. |
| **Brute-force protection** | Account locks for 10 minutes after 5 failed login attempts. |
| **Session handling** | Authenticated admin sessions expire automatically after 30 minutes of inactivity. |
| **Admin route** | Not linked anywhere in the public UI — only reachable via a hidden `?admin=1` query route, and still requires full authentication. |
| **First-run setup** | A separate, high-entropy `ADMIN_SETUP_KEY` is required to bootstrap the admin account, so no unauthenticated visitor can self-register as admin. |
| **XSS prevention** | All dynamic content rendered via `unsafe_allow_html` (resume-derived text, third-party API data) is passed through `html.escape()` before rendering. |
| **URL validation** | External job-listing links are scheme-validated (`http(s)://` only) before being rendered as clickable links. |
| **Input handling** | Uploads over 10 MB are rejected before processing; corrupt/encrypted PDFs fail gracefully instead of crashing or leaking a traceback. |
| **Secrets hygiene** | `.gitignore` excludes `.env`, `.streamlit/secrets.toml`, `.streamlit/admin_auth.json`, `activity_log.jsonl`, and `usage_log.csv` — none of these are ever committed. |
| **Data minimization** | Resume text itself is never written to the audit log — only limited metadata (filename, file size, ATS score, category, timestamp). |

### Setting up your own admin credentials

Never reuse a password suggested by someone else. Generate your own.

1. Copy `.streamlit/secrets.toml.example` → `.streamlit/secrets.toml` (this file is git-ignored and stays local).
2. Fill in your own values:
   ```toml
   ADMIN_USERNAME = "your_own_username"
   ADMIN_PASSWORD = "your_own_long_unique_password"
   ADMIN_SETUP_KEY = "a_random_24+_character_string"
   ```
3. Run the app, open `?admin=1`, enter the setup key once, then create your admin login.
4. For production (Streamlit Community Cloud), set the same three values under **App → Settings → Secrets** — never in code, README, or a screenshot.

**If a credential is ever accidentally exposed** (e.g. pushed to a public repo): treat it as compromised immediately — rotate/replace it. Deleting the file afterward is not enough, since Git history retains old commits.

Full operational detail lives in [`ADMIN_GUIDE.md`](./ADMIN_GUIDE.md).

---

## 🚀 Run Locally

```bash
git clone https://github.com/AroonKumarMaheshwari-11/AI-resume-analyzer.git
cd AI-resume-analyzer
pip install -r requirements.txt
streamlit run app.py
```

The app opens at `http://localhost:8501`. The admin panel stays fully disabled until you configure your own credentials (see **Security** above).

---

## ☁️ Deployment

Deployed on [Streamlit Community Cloud](https://streamlit.io/cloud). Every push to `main` auto-redeploys the live app. Production secrets are set in the platform's **Secrets** panel — never committed to the repository.

---

## 🧠 How Career Matching Works

Each of the 45 career profiles is scored using weighted signals (core keywords ×3, skills ×2, certifications ×2, tools ×1). A role only qualifies as a match if it clears both a minimum number of distinct signals *and* a minimum total weight, preventing a single incidental keyword from producing a misleading recommendation. Closely related roles are grouped by family, so results read as distinct career directions.

---

## 📌 Disclaimer

This tool provides a **heuristic-based estimate** for guidance purposes only. It is not a guarantee of how any specific company's real ATS software will score a resume.

---

## 👤 Developer

**AI Resume Analyzer** • Developed by **Aroon Kumar Maheshwari**
Built with Python • Streamlit • Plotly • pypdf • PyMuPDF
