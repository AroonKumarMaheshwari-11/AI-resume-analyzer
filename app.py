import streamlit as st
import re
import html
import urllib.parse
import requests
import csv
import os
import datetime
import time
import json
import hashlib
import secrets
from pathlib import Path
import plotly.graph_objects as go
from pypdf import PdfReader

# Optional local AI engine. Sentence-Transformers runs fully locally after the
# model is downloaded; no paid API key is required. The app falls back to the
# deterministic analyzer if the package/model is unavailable.
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
except Exception:
    SentenceTransformer = None
    np = None

try:
    import fitz  # PyMuPDF: often extracts modern multi-column resumes better than pypdf
except Exception:
    fitz = None

st.set_page_config(page_title="AI Resume Analyzer | Aroon Kumar Maheshwari", page_icon="📄", layout="wide")
# Hide Streamlit's developer toolbar/menu in the user-facing app.
try:
    st.set_option("client.toolbarMode", "minimal")
except Exception:
    pass

# ---------------------------
# Design system — Dark Navy + Electric Blue
# ---------------------------
BG = "#0B1120"
CARD_BG = "#111827"
CARD_BG_2 = "#172033"
PRIMARY = "#3B82F6"
LIGHT_BLUE = "#60A5FA"
TEXT = "#F8FAFC"
MUTED = "#94A3B8"
BORDER = "#243047"
SUCCESS = "#22C55E"
WARNING = "#F59E0B"
ERROR = "#EF4444"

st.markdown(f"""
<style>
    .stApp {{ background-color: {BG}; }}
    section[data-testid="stSidebar"] {{
        background-color: {CARD_BG};
        border-right: 1px solid {BORDER};
    }}
    section[data-testid="stSidebar"] * {{ color: {TEXT} !important; }}
    h1, h2, h3, h4 {{ color: {TEXT} !important; font-weight: 700; }}
    p, span, label, .stMarkdown, li {{ color: {TEXT}; }}
    .stCaption, .stCaption p {{ color: {MUTED} !important; }}

    .stTextArea textarea {{
        background-color: {CARD_BG_2} !important;
        color: {TEXT} !important;
        border: 1px solid {BORDER} !important;
        border-radius: 10px !important;
    }}
    .stTextInput input {{
        background-color: {CARD_BG_2} !important;
        color: {TEXT} !important;
        border: 1px solid {BORDER} !important;
        border-radius: 10px !important;
        caret-color: {TEXT} !important;
    }}
    .stTextInput input::placeholder {{
        color: {MUTED} !important;
        opacity: 1 !important;
    }}
    [data-testid="stFileUploaderDropzone"] {{
        background-color: {CARD_BG_2} !important;
        border: 1.5px dashed {BORDER} !important;
        border-radius: 12px !important;
    }}
    [data-testid="stFileUploaderDropzone"] * {{ color: {MUTED} !important; }}

    /* Uploaded file preview row (was rendering white/unstyled) */
    [data-testid="stFileUploaderFile"],
    [data-testid="stFileUploaderFileName"],
    div[data-testid="stFileUploader"] section > div,
    div[data-testid="stFileUploader"] ul,
    div[data-testid="stFileUploader"] li {{
        background-color: {CARD_BG_2} !important;
        color: {TEXT} !important;
        border-radius: 10px !important;
    }}
    div[data-testid="stFileUploader"] * {{
        color: {TEXT} !important;
    }}
    div[data-testid="stFileUploader"] small {{
        color: {MUTED} !important;
    }}
    div[data-testid="stFileUploader"] svg {{
        fill: {LIGHT_BLUE} !important;
    }}

    .stButton > button {{
        background-color: {PRIMARY};
        color: {TEXT};
        border: none;
        border-radius: 10px;
        font-weight: 600;
        padding: 0.6rem 1.7rem;
        transition: 0.15s ease;
    }}
    .stButton > button:hover {{
        background-color: {LIGHT_BLUE};
        box-shadow: 0 0 14px rgba(59,130,246,0.4);
    }}
    .stDownloadButton > button {{
        background-color: {CARD_BG_2};
        color: {LIGHT_BLUE};
        border: 1px solid {PRIMARY};
        border-radius: 10px;
        font-weight: 600;
    }}

    .hero {{ padding: 4px 0 10px 0; }}
    .hero-title {{ font-size: 42px; font-weight: 800; color: {TEXT}; margin-bottom: 2px; }}
    .hero-subtitle {{ font-size: 16px; color: {MUTED}; margin-bottom: 12px; }}
    .badge {{
        display: inline-block;
        background: rgba(59,130,246,0.12);
        color: {LIGHT_BLUE};
        border: 1px solid rgba(59,130,246,0.35);
        padding: 5px 14px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.06em;
    }}

    .card {{
        background: {CARD_BG};
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 20px;
        border: 1px solid {BORDER};
        box-shadow: 0 4px 18px rgba(0,0,0,0.22);
    }}
    .card-title {{ font-size: 19px; font-weight: 700; color: {TEXT}; margin-bottom: 4px; }}
    .card-subtitle {{ font-size: 13px; color: {MUTED}; margin-bottom: 14px; }}

    .metric-card {{
        background: {CARD_BG};
        border: 1px solid {BORDER};
        border-radius: 16px;
        padding: 20px 22px;
        box-shadow: 0 4px 18px rgba(0,0,0,0.22);
    }}
    .metric-icon {{ font-size: 21px; margin-bottom: 6px; }}
    .metric-value {{ font-size: 29px; font-weight: 800; color: {TEXT}; line-height: 1.1; }}
    .metric-label {{ font-size: 13px; color: {MUTED}; margin-top: 4px; }}

    .pill {{
        display: inline-block;
        padding: 5px 13px;
        border-radius: 999px;
        font-size: 12.5px;
        font-weight: 600;
        margin: 3px 6px 3px 0;
    }}
    .pill-blue {{ background: rgba(59,130,246,0.14); color: {LIGHT_BLUE}; border: 1px solid rgba(59,130,246,0.3); }}
    .pill-good {{ background: rgba(34,197,94,0.14); color: {SUCCESS}; border: 1px solid rgba(34,197,94,0.3); }}
    .pill-bad {{ background: rgba(239,68,68,0.14); color: {ERROR}; border: 1px solid rgba(239,68,68,0.3); }}
    .pill-warn {{ background: rgba(245,158,11,0.14); color: {WARNING}; border: 1px solid rgba(245,158,11,0.3); }}
    .pill-neutral {{ background: rgba(148,163,184,0.12); color: {MUTED}; border: 1px solid rgba(148,163,184,0.25); }}

    .status-badge {{
        padding: 10px 14px;
        border-radius: 10px;
        font-size: 13.5px;
        font-weight: 600;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    .status-yes {{ background: rgba(34,197,94,0.10); color: {SUCCESS}; border: 1px solid rgba(34,197,94,0.28); }}
    .status-no {{ background: rgba(239,68,68,0.10); color: {ERROR}; border: 1px solid rgba(239,68,68,0.28); }}

    .rec-card {{
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 10px;
        background: {CARD_BG_2};
        border-left: 4px solid {PRIMARY};
    }}
    .rec-high {{ border-left-color: {ERROR}; }}
    .rec-medium {{ border-left-color: {WARNING}; }}
    .rec-suggestion {{ border-left-color: {PRIMARY}; }}
    .rec-tag {{
        font-size: 11px; font-weight: 700; letter-spacing: 0.04em;
        text-transform: uppercase; margin-bottom: 3px; display: block;
    }}
    .rec-tag-high {{ color: {ERROR}; }}
    .rec-tag-medium {{ color: {WARNING}; }}
    .rec-tag-suggestion {{ color: {LIGHT_BLUE}; }}

    .ba-box {{ border-radius: 10px; padding: 12px 16px; margin-bottom: 8px; font-size: 14px; }}
    .ba-before {{ background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.25); }}
    .ba-after {{ background: rgba(34,197,94,0.08); border: 1px solid rgba(34,197,94,0.25); }}

    .job-card {{
        background: {CARD_BG_2};
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
    }}
    .job-title {{ font-size: 16px; font-weight: 700; color: {TEXT}; }}
    .job-company {{ font-size: 13.5px; color: {MUTED}; margin-bottom: 6px; }}
    .job-apply {{
        display: inline-block; margin-top: 8px; color: {LIGHT_BLUE};
        font-weight: 700; font-size: 13.5px; text-decoration: none;
    }}

    .career-card {{
        background: {CARD_BG_2};
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 18px 22px;
        margin-bottom: 14px;
    }}

    .footer-box {{
        text-align: center;
        padding: 22px 0 6px 0;
        color: {MUTED};
        font-size: 13px;
        border-top: 1px solid {BORDER};
        margin-top: 10px;
    }}
    .footer-box b {{ color: {LIGHT_BLUE}; }}

    .analysis-loader {{
        margin: 18px 0; padding: 26px; border: 1px solid #243047;
        border-radius: 18px; background: linear-gradient(135deg, #111827, #172033);
        text-align: center; box-shadow: 0 12px 35px rgba(0,0,0,.25);
    }}
    .ai-orbit {{ width: 92px; height: 92px; margin: 0 auto 16px; position: relative;
        border: 3px solid rgba(96,165,250,.18); border-top-color: #60A5FA;
        border-right-color: #3B82F6; border-radius: 50%; animation: spin 1s linear infinite; }}
    .ai-orbit:after {{ content: "AI"; position:absolute; inset: 18px; display:flex; align-items:center;
        justify-content:center; border-radius:50%; background:#0B1120; color:#60A5FA;
        font-weight:800; letter-spacing:2px; box-shadow: 0 0 25px rgba(59,130,246,.35); }}
    .analysis-pulse {{ color:#94A3B8; animation:pulse 1.4s ease-in-out infinite; }}
    .analysis-step {{ color:#F8FAFC; font-size:15px; margin-top:7px; font-weight:600; }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    @keyframes pulse {{ 0%,100%{{opacity:.45}} 50%{{opacity:1}} }}

    /* Completely remove Streamlit's user-facing developer chrome. */
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    footer,
    [data-testid="stStatusWidget"] {{ display: none !important; }}
    .boot-splash {{ position: fixed; inset: 0; z-index: 9999999; background: radial-gradient(circle at center, #101C35 0%, #070D19 55%, #040812 100%); display: flex; align-items: center; justify-content: center; flex-direction: column; gap: 14px; opacity: 1; visibility: visible; transition: opacity .55s ease, visibility .55s ease; pointer-events: all; }}
    .boot-splash.boot-hidden {{ opacity: 0; visibility: hidden; pointer-events: none; }}
    .boot-splash {{ animation: splashFade .55s ease 2.15s forwards; }}
    @keyframes splashFade {{ to {{ opacity: 0; visibility: hidden; pointer-events: none; }} }}
    .boot-ring {{ width: 78px; height: 78px; border-radius: 50%; border: 3px solid rgba(96,165,250,.16); border-top-color: #60A5FA; border-right-color: #3B82F6; animation: spin .9s linear infinite; box-shadow: 0 0 45px rgba(59,130,246,.25); }}
    .boot-title {{ color: #F8FAFC; font-size: 21px; font-weight: 850; letter-spacing: .11em; text-align:center; }}
    .boot-sub {{ color: #94A3B8; font-size: 12px; letter-spacing: .05em; text-align:center; }}
    .boot-dots::after {{ content:""; animation: bootDots 1.2s steps(4,end) infinite; }}
    @keyframes bootDots {{ 0%{{content:"";}} 25%{{content:".";}} 50%{{content:"..";}} 75%{{content:"...";}} 100%{{content:"";}} }}
    .nav-loading-link {{ position:relative; display:inline-flex !important; align-items:center; gap:7px; }}
    .nav-loading-link:focus::after {{ content:""; width:13px; height:13px; border:2px solid rgba(148,163,184,.28); border-top-color:#60A5FA; border-right-color:#3B82F6; border-radius:50%; animation:spin .65s linear 2.5; margin-left:5px; flex:none; }}
    .app-loading-overlay {{ position: fixed; inset: 0; z-index: 9999998; display:flex; align-items:center; justify-content:center; background:rgba(4,8,18,.78); backdrop-filter:blur(8px); opacity:0; visibility:hidden; transition:opacity .18s ease, visibility .18s ease; pointer-events:none; }}
    .app-loading-overlay.active {{ opacity:1; visibility:visible; }}
    .app-loading-card {{ min-width:280px; padding:22px 28px; border:1px solid rgba(96,165,250,.28); border-radius:18px; background:rgba(17,24,39,.94); box-shadow:0 20px 70px rgba(0,0,0,.45); text-align:center; }}
    .app-loading-spinner {{ width:42px; height:42px; margin:0 auto 12px; border-radius:50%; border:3px solid rgba(96,165,250,.18); border-top-color:#60A5FA; border-right-color:#3B82F6; animation:spin .8s linear infinite; }}
    .app-loading-title {{ color:#F8FAFC; font-weight:800; font-size:14px; letter-spacing:.05em; }}
    .app-loading-sub {{ color:#94A3B8; font-size:11px; margin-top:5px; }}
    .admin-shell {{ max-width: 1200px; margin: 0 auto; }}
    .admin-hero {{ background: linear-gradient(135deg, #111827, #0F1B31); border: 1px solid #243047; border-radius: 18px; padding: 26px; margin-bottom: 18px; }}
    .admin-title {{ font-size: 32px; font-weight: 850; color: #F8FAFC; }}
    .admin-sub {{ color: #94A3B8; margin-top: 4px; }}
    .security-note {{ border: 1px solid rgba(34,197,94,.25); background: rgba(34,197,94,.07); border-radius: 12px; padding: 12px 15px; color: #86EFAC; }}

</style>
""", unsafe_allow_html=True)

# ---------------------------
# Static knowledge bases
# ---------------------------

SECTION_KEYWORDS = {
    "Contact Info": [r"email", r"@", r"phone", r"linkedin", r"github"],
    "Summary/Objective": [r"summary", r"objective", r"profile"],
    "Experience": [r"experience", r"employment", r"work history", r"internship"],
    "Education": [r"education", r"university", r"degree", r"bachelor", r"college"],
    "Skills": [r"skills", r"technical skills", r"proficienc"],
    "Projects": [r"projects", r"portfolio"],
    "Certifications": [r"certificat"],
}

ACTION_VERBS = [
    "achieved", "built", "created", "designed", "developed", "led", "improved",
    "increased", "reduced", "managed", "launched", "implemented", "optimized",
    "delivered", "automated", "analyzed", "engineered", "streamlined", "resolved",
    "trained", "collaborated", "spearheaded", "generated",
    # Healthcare / clinical action verbs
    "assessed", "administered", "monitored", "evaluated", "documented", "coordinated",
    "educated", "treated", "assisted", "maintained", "supported", "observed",
    "counseled", "screened", "diagnosed", "supervised",
    # Software / engineering
    "deployed", "debugged", "integrated", "architected", "refactored", "tested",
    # Data
    "modeled", "visualized", "forecasted", "transformed", "interpreted", "validated",
    # Cybersecurity
    "detected", "investigated", "secured", "mitigated", "audited", "remediated",
    # Marketing / business
    "promoted", "converted", "negotiated", "forecast", "scaled",
]

WEAK_PHRASES = [
    "responsible for", "duties included", "worked on", "helped with", "team player",
    "hard worker", "detail oriented", "go-getter", "think outside the box"
]

CERT_PROVIDERS = [
    "google", "oracle", "cisco", "microsoft", "aws", "amazon web services", "hp life",
    "coursera", "edx", "udemy", "ibm", "meta", "comptia", "pmi", "salesforce", "azure"
]

# Known certification acronyms/names that don't necessarily contain the word "certificat"
KNOWN_CERT_KEYWORDS = [
    "bls", "acls", "ccna", "ccnp", "comptia", "security+", "ceh", "pmp",
    "aws certified", "azure certified", "google certified", "oracle certified",
    "cisco certified", "basic life support", "advanced cardiovascular life support",
    "registered nurse license", "nursing license", "rn license",
]

# Lines that are ONLY a section heading (e.g. "CERTIFICATIONS") and not an actual
# certification name — these must never be counted as a detected certification.
CERT_HEADER_ONLY = {
    "certification", "certifications", "certificate", "certificates",
    "certifications:", "certificates:", "licenses and certifications",
    "licenses & certifications", "certifications and licenses",
}

FAMILY_PLATFORMS = {
    "AI / GenAI": [
        ("Upwork", "Dedicated AI Services category with strong contract volume."),
        ("Fiverr", "Good for beginners — buyers come to you via gig listings."),
        ("LinkedIn", "Direct outreach to startups building AI features."),
    ],
    "Data": [
        ("Upwork", "Consistent demand for data cleaning, reporting & analytics projects."),
        ("Fiverr", "Good for productized data-analysis gig packages."),
        ("LinkedIn", "Most full-time data roles are posted here."),
    ],
    "Software": [
        ("Upwork", "Huge volume of software/backend/frontend development contracts."),
        ("Freelancer.com", "Bidding-based, good for smaller development tasks."),
        ("LinkedIn", "Primary channel for full-time software roles."),
    ],
    "Cloud / DevOps": [
        ("Upwork", "Cloud deployment/infrastructure tasks are common short gigs."),
        ("LinkedIn", "Cloud certifications are strong signals for recruiters here."),
    ],
    "Cybersecurity": [
        ("Upwork", "Dedicated Cybersecurity category with steady demand."),
        ("LinkedIn", "Many security roles are filled via networking/referrals."),
    ],
    "FinTech / Finance": [
        ("LinkedIn", "Primary channel for finance and fintech hiring."),
        ("Indeed", "Wide range of financial analyst and fintech postings."),
    ],
    "Healthcare": [
        ("LinkedIn", "Most healthcare hiring happens through direct listings/referrals here."),
        ("Indeed", "Large volume of clinical and healthcare job postings."),
    ],
    "Green / Energy / Engineering": [
        ("LinkedIn", "Growing channel for renewable energy and engineering roles."),
        ("Indeed", "Regular postings for energy & engineering positions."),
    ],
    "Business / Product / Operations": [
        ("LinkedIn", "Primary channel for business, product & operations roles."),
        ("Upwork", "Freelance business analysis and PM contracts available."),
    ],
    "Marketing / Design / Customer": [
        ("Upwork", "Strong marketplace for marketing, design & content gigs."),
        ("Fiverr", "Great for productized design/marketing service packages."),
        ("LinkedIn", "Direct outreach for full-time marketing/design roles."),
    ],
    "Education / Human-centered": [
        ("LinkedIn", "Primary channel for education and counseling roles."),
        ("Indeed", "Wide range of teaching and human-services postings."),
    ],
}


def _profile(family, core, skills=None, tools=None, certifications=None, job_titles=None):
    """Helper to build a compact, structured career profile."""
    return {
        "family": family,
        "core": core,
        "skills": skills or [],
        "tools": tools or [],
        "certifications": certifications or [],
        "job_titles": job_titles or [],
    }


# Structured career knowledge base. Not an exhaustive 155-role hard-coded set
# (that would mean shallow, low-signal entries) — instead a curated set of
# ~45 roles spanning every requested industry, each with real, meaningful
# signals. The scoring engine below is weighted and family-aware, so it
# scales cleanly if more roles are added later.
CAREER_CATEGORIES = {
    # ---------------- AI / GenAI ----------------
    "AI / ML Engineer": _profile(
        "AI / GenAI",
        core=["machine learning", "deep learning", "neural network", "model training",
              "computer vision", "natural language processing", "nlp"],
        skills=["tensorflow", "pytorch", "scikit-learn", "keras", "opencv", "classification"],
        tools=["huggingface", "jupyter"],
        job_titles=["AI/ML Engineer (Entry-Level)", "Machine Learning Intern", "Applied AI Engineer"],
    ),
    "Generative AI / LLM Engineer": _profile(
        "AI / GenAI",
        core=["generative ai", "large language model", "llm", "prompt engineering",
              "retrieval augmented generation", "rag"],
        skills=["langchain", "openai api", "vector database", "fine-tuning"],
        tools=["huggingface", "pinecone", "chromadb"],
        job_titles=["Generative AI Engineer", "LLM Engineer", "Prompt Engineer"],
    ),
    "AI Research Engineer": _profile(
        "AI / GenAI",
        core=["ai research", "research paper", "experiment design", "model evaluation",
              "responsible ai", "ai safety"],
        skills=["python", "pytorch", "statistics"],
        job_titles=["AI Research Engineer", "AI Researcher", "AI Safety Researcher"],
    ),

    # ---------------- Data ----------------
    "Data Scientist": _profile(
        "Data",
        core=["data science", "predictive modeling", "statistical analysis", "hypothesis testing",
              "feature engineering", "machine learning"],
        skills=["python", "r programming", "pandas", "scikit-learn"],
        job_titles=["Data Scientist", "Junior Data Scientist"],
    ),
    "Data Analyst": _profile(
        "Data",
        core=["data analysis", "data visualization", "data cleaning", "reporting", "dashboard"],
        skills=["excel", "sql", "power bi", "tableau", "pandas", "statistics"],
        job_titles=["Junior Data Analyst", "Business Intelligence Analyst"],
    ),
    "Data Engineer": _profile(
        "Data",
        core=["data pipeline", "etl", "data warehouse", "data engineering", "big data"],
        skills=["sql", "spark", "airflow", "python"],
        job_titles=["Junior Data Engineer", "Big Data Engineer"],
    ),
    "Business Intelligence Analyst": _profile(
        "Data",
        core=["business intelligence", "bi reporting", "data governance", "kpi dashboard"],
        skills=["sql", "power bi", "tableau"],
        job_titles=["BI Analyst", "BI Developer"],
    ),

    # ---------------- Software ----------------
    "Python Backend Developer": _profile(
        "Software",
        core=["backend development", "rest api", "api development", "microservices"],
        skills=["python", "flask", "django", "fastapi", "sql", "database"],
        tools=["git", "github", "docker"],
        job_titles=["Junior Python Developer", "Backend Developer Intern", "API Integration Developer"],
    ),
    "Full-Stack Developer": _profile(
        "Software",
        core=["full-stack development", "frontend development", "backend development", "web application"],
        skills=["javascript", "react", "node.js", "html", "css", "sql"],
        job_titles=["Junior Full-Stack Developer", "Web Application Developer"],
    ),
    "Frontend Developer": _profile(
        "Software",
        core=["frontend development", "user interface", "responsive design", "web development"],
        skills=["javascript", "react", "html", "css", "typescript"],
        job_titles=["Junior Frontend Developer", "React Developer"],
    ),
    "Mobile App Developer": _profile(
        "Software",
        core=["mobile app development", "android development", "ios development"],
        skills=["kotlin", "swift", "flutter", "react native", "java"],
        job_titles=["Junior Mobile App Developer", "Android Developer", "iOS Developer"],
    ),
    "Software Engineer": _profile(
        "Software",
        core=["software engineering", "software development", "object-oriented programming",
              "software architecture", "system design"],
        skills=["java", "python", "c++", "data structures", "algorithms"],
        job_titles=["Junior Software Engineer", "Software Engineer I"],
    ),

    # ---------------- Cloud / DevOps ----------------
    "Cloud Engineer": _profile(
        "Cloud / DevOps",
        core=["cloud computing", "cloud infrastructure", "cloud architecture", "cloud migration"],
        skills=["aws", "microsoft azure", "oracle cloud infrastructure", "google cloud platform"],
        job_titles=["Cloud Support Associate", "Junior Cloud Engineer"],
    ),
    "DevOps Engineer": _profile(
        "Cloud / DevOps",
        core=["devops", "ci/cd pipeline", "infrastructure as code", "cloud deployment"],
        skills=["docker", "kubernetes", "jenkins", "terraform"],
        job_titles=["Junior DevOps Engineer", "Site Reliability Engineer (Entry-Level)"],
    ),
    "Platform / Infrastructure Engineer": _profile(
        "Cloud / DevOps",
        core=["platform engineering", "systems administration", "network infrastructure"],
        skills=["kubernetes", "docker", "linux", "networking"],
        job_titles=["Platform Engineer", "Infrastructure Engineer", "Systems Engineer"],
    ),

    # ---------------- Cybersecurity ----------------
    "Cybersecurity Analyst": _profile(
        "Cybersecurity",
        core=["cybersecurity", "cyber security", "network security", "threat detection",
              "vulnerability assessment", "security awareness"],
        skills=["firewall", "siem", "incident response"],
        certifications=["ceh", "comptia security+", "ccna"],
        job_titles=["Junior Cybersecurity Analyst", "Security Awareness Trainee"],
    ),
    "SOC / Security Operations Analyst": _profile(
        "Cybersecurity",
        core=["soc analyst", "security operations", "incident response", "log analysis",
              "threat monitoring"],
        skills=["siem", "firewall", "intrusion detection"],
        job_titles=["SOC Analyst (Entry-Level)", "Security Operations Engineer"],
    ),
    "Penetration Tester / Ethical Hacker": _profile(
        "Cybersecurity",
        core=["penetration testing", "ethical hacking", "vulnerability scanning",
              "red team", "exploit development"],
        skills=["kali linux", "metasploit", "burp suite"],
        certifications=["ceh", "oscp"],
        job_titles=["Junior Penetration Tester", "Ethical Hacker (Entry-Level)"],
    ),

    # ---------------- FinTech / Finance ----------------
    "Financial Analyst": _profile(
        "FinTech / Finance",
        core=["financial analysis", "financial modeling", "budgeting", "forecasting",
              "variance analysis"],
        skills=["excel", "financial statements", "valuation"],
        job_titles=["Junior Financial Analyst", "Investment Analyst"],
    ),
    "Risk / Compliance Analyst": _profile(
        "FinTech / Finance",
        core=["risk analysis", "compliance", "regulatory reporting", "aml", "fraud detection"],
        skills=["risk assessment", "credit analysis"],
        job_titles=["Risk Analyst", "Compliance Analyst", "AML Analyst"],
    ),
    "FinTech / Blockchain Developer": _profile(
        "FinTech / Finance",
        core=["fintech", "blockchain", "smart contract", "web3", "payments"],
        skills=["solidity", "python", "cryptocurrency"],
        job_titles=["FinTech Engineer", "Blockchain Developer", "Web3 Developer"],
    ),

    # ---------------- Healthcare ----------------
    "Registered Nurse": _profile(
        "Healthcare",
        core=["nursing", "registered nurse", "patient care", "clinical assessment",
              "medication administration", "vital signs", "patient monitoring",
              "care plan", "infection control", "wound care", "iv therapy"],
        certifications=["bls", "acls", "pals"],
        job_titles=["Registered Nurse (RN)", "Staff Nurse", "Clinical Nurse"],
    ),
    "Clinical Pharmacist": _profile(
        "Healthcare",
        core=["pharmacist", "pharmacy", "medication therapy", "prescription",
              "drug interaction", "clinical pharmacy", "pharmacology", "dispensing",
              "medication safety", "formulary"],
        job_titles=["Clinical Pharmacist", "Staff Pharmacist"],
    ),
    "Medical Laboratory Technologist": _profile(
        "Healthcare",
        core=["medical laboratory", "clinical laboratory", "specimen collection",
              "blood analysis", "microbiology", "hematology", "phlebotomy",
              "diagnostic testing"],
        job_titles=["Medical Laboratory Technologist", "Clinical Lab Technician"],
    ),
    "Physical / Occupational Therapist": _profile(
        "Healthcare",
        core=["physical therapy", "occupational therapy", "rehabilitation",
              "patient mobility", "treatment plan", "therapeutic exercise"],
        job_titles=["Physical Therapist", "Occupational Therapist"],
    ),
    "Healthcare Administrator": _profile(
        "Healthcare",
        core=["healthcare administration", "hospital operations", "medical records",
              "healthcare management", "medical billing", "health information management"],
        job_titles=["Healthcare Administrator", "Hospital Operations Coordinator"],
    ),
    "Medical Coder / Health Information Technician": _profile(
        "Healthcare",
        core=["medical coding", "icd-10", "medical billing", "health information technician"],
        job_titles=["Medical Coder", "Health Information Technician"],
    ),
    "Radiologic / Medical Imaging Technologist": _profile(
        "Healthcare",
        core=["radiologic technology", "medical imaging", "x-ray", "mri", "ct scan"],
        job_titles=["Radiologic Technologist", "Medical Imaging Specialist"],
    ),
    "Dental Hygienist / Assistant": _profile(
        "Healthcare",
        core=["dental hygienist", "dental assistant", "oral health", "dental procedures",
              "periodontal", "chairside assistance"],
        job_titles=["Dental Hygienist", "Dental Assistant"],
    ),
    "Mental Health Counselor / Social Worker": _profile(
        "Healthcare",
        core=["mental health counseling", "social work", "case management",
              "counseling session", "client advocacy"],
        job_titles=["Mental Health Counselor", "Social Worker"],
    ),

    # ---------------- Green / Energy / Engineering ----------------
    "Renewable Energy Engineer": _profile(
        "Green / Energy / Engineering",
        core=["renewable energy", "solar energy", "wind energy", "energy systems"],
        skills=["autocad", "energy modeling"],
        job_titles=["Renewable Energy Engineer", "Solar Energy Engineer", "Wind Energy Engineer"],
    ),
    "Environmental / Sustainability Engineer": _profile(
        "Green / Energy / Engineering",
        core=["environmental engineering", "sustainability", "environmental impact assessment",
              "emissions reduction"],
        job_titles=["Environmental Engineer", "Sustainability Specialist"],
    ),
    "EV / Battery Engineer": _profile(
        "Green / Energy / Engineering",
        core=["electric vehicle", "ev engineering", "battery engineering", "battery management system"],
        job_titles=["EV Engineer", "Battery Engineer"],
    ),
    "Robotics / Automation Engineer": _profile(
        "Green / Energy / Engineering",
        core=["robotics", "automation engineering", "plc programming", "industrial automation"],
        skills=["python", "control systems"],
        job_titles=["Robotics Engineer", "Automation Engineer"],
    ),

    # ---------------- Business / Product / Operations ----------------
    "Business Analyst": _profile(
        "Business / Product / Operations",
        core=["business analysis", "requirements gathering", "process improvement",
              "stakeholder management"],
        skills=["sql", "excel"],
        job_titles=["Junior Business Analyst", "Business Systems Analyst"],
    ),
    "Product Manager": _profile(
        "Business / Product / Operations",
        core=["product management", "product roadmap", "product strategy", "user stories",
              "agile", "scrum"],
        job_titles=["Associate Product Manager", "Product Owner"],
    ),
    "Project / Program Manager": _profile(
        "Business / Product / Operations",
        core=["project management", "program management", "project planning",
              "risk management", "agile", "scrum"],
        certifications=["pmp"],
        job_titles=["Junior Project Manager", "Program Coordinator"],
    ),
    "Operations / Supply Chain Analyst": _profile(
        "Business / Product / Operations",
        core=["supply chain", "logistics", "operations management", "inventory management",
              "procurement"],
        job_titles=["Supply Chain Analyst", "Operations Analyst", "Logistics Specialist"],
    ),

    # ---------------- Marketing / Design / Customer ----------------
    "Digital Marketing Specialist": _profile(
        "Marketing / Design / Customer",
        core=["digital marketing", "seo", "performance marketing", "campaign management",
              "social media marketing", "content strategy"],
        skills=["google analytics", "google ads", "email marketing"],
        job_titles=["Digital Marketing Specialist", "SEO Specialist", "Performance Marketing Specialist"],
    ),
    "UX / UI Designer": _profile(
        "Marketing / Design / Customer",
        core=["ux design", "ui design", "user research", "wireframing", "prototyping",
              "usability testing"],
        skills=["figma", "adobe xd", "sketch"],
        job_titles=["Junior UX Designer", "UI Designer", "Product Designer"],
    ),
    "Content Strategist / Writer": _profile(
        "Marketing / Design / Customer",
        core=["content strategy", "content creation", "copywriting", "technical writing",
              "editorial calendar"],
        job_titles=["Content Strategist", "Content Creator", "Technical Writer"],
    ),
    "Customer Success / Sales Development": _profile(
        "Marketing / Design / Customer",
        core=["customer success", "customer onboarding", "account management",
              "sales development", "lead generation"],
        job_titles=["Customer Success Manager", "Sales Development Representative"],
    ),

    # ---------------- Education / Human-centered ----------------
    "Teacher / Instructor": _profile(
        "Education / Human-centered",
        core=["teaching", "curriculum design", "lesson planning", "classroom management",
              "student assessment"],
        job_titles=["Secondary School Teacher", "University Lecturer", "Instructional Designer"],
    ),
    "Corporate Trainer / L&D Specialist": _profile(
        "Education / Human-centered",
        core=["corporate training", "learning and development", "workforce development",
              "training program design"],
        job_titles=["Corporate Trainer", "Learning & Development Specialist"],
    ),
    "Career / Academic Counselor": _profile(
        "Education / Human-centered",
        core=["career counseling", "academic advising", "student support",
              "workforce development"],
        job_titles=["Career Counselor", "Workforce Development Specialist"],
    ),
}

# Category-specific recommendation tips (kept intentionally short — no invented facts)
CATEGORY_SPECIFIC_TIPS = {
    "Registered Nurse": [
        "Add measurable patient-care outcomes where appropriate (e.g. patient load, units served).",
        "Include relevant clinical certifications such as BLS/ACLS if you hold them.",
        "Mention specific clinical specialties or departments you've worked in, if applicable.",
    ],
    "Clinical Pharmacist": [
        "Highlight specific clinical pharmacy responsibilities (e.g. medication therapy management).",
        "Include relevant pharmacy licensure or certifications if applicable.",
        "Mention specific practice settings (hospital, retail, clinical) if relevant.",
    ],
    "Medical Laboratory Technologist": [
        "Mention specific lab systems, testing types, or accreditations you've worked with.",
        "Include relevant lab certifications if applicable.",
    ],
    "Healthcare Administrator": [
        "Highlight measurable operational improvements (e.g. process efficiency, patient satisfaction).",
        "Mention relevant healthcare systems or software you've used (e.g. EHR platforms).",
    ],
    "Dental Hygienist / Assistant": [
        "Mention specific procedures or patient volumes handled, if applicable.",
        "Include relevant dental certifications or licensure if applicable.",
    ],
    "Data Scientist": [
        "Highlight specific model performance metrics where applicable (accuracy, precision, recall).",
        "Mention the scale of data you've worked with, if relevant.",
    ],
    "Cybersecurity Analyst": [
        "Mention specific tools or frameworks used (SIEM, firewalls, incident response).",
        "Include relevant certifications such as CompTIA Security+ or CEH if applicable.",
    ],
    "Digital Marketing Specialist": [
        "Quantify campaign results where possible (CTR, conversion rate, ROI).",
        "Mention specific platforms/tools used (Google Ads, Analytics, Meta Ads).",
    ],
}


PLATFORM_SEARCH_URLS = {
    "Upwork": "https://www.upwork.com/nx/search/jobs/?q={query}",
    "Fiverr": "https://www.fiverr.com/search/gigs?query={query}",
    "Freelancer.com": "https://www.freelancer.com/jobs/search/?keyword={query}",
    "LinkedIn": "https://www.linkedin.com/jobs/search/?keywords={query}",
    "Indeed": "https://www.indeed.com/jobs?q={query}",
}

BEFORE_AFTER_TEMPLATES = {
    "responsible for": (
        "Responsible for developing Python applications.",
        "Developed Python applications that improved [process/metric] efficiency."
    ),
    "duties included": (
        "Duties included managing project timelines.",
        "Managed project timelines, ensuring on-time delivery across [X] projects."
    ),
    "worked on": (
        "Worked on a machine learning model for classification.",
        "Built a machine learning classification model achieving [X]% accuracy."
    ),
    "helped with": (
        "Helped with debugging and testing the application.",
        "Debugged and tested the application, resolving [X] critical issues."
    ),
    "team player": (
        "I am a team player who works well with others.",
        "Collaborated with a [X]-person team to deliver [project/feature] on schedule."
    ),
    "hard worker": (
        "I am a hard worker dedicated to my tasks.",
        "Consistently delivered [task/project] ahead of schedule through focused effort."
    ),
    "detail oriented": (
        "I am detail oriented in my work.",
        "Reviewed and refined [deliverable], reducing errors by [X]%."
    ),
}


# ---------------------------
# Core PDF & text analysis
# ---------------------------

MAX_UPLOAD_MB = 10


def _normalize_resume_text(text: str) -> str:
    """Normalize PDF extraction without destroying section/line information."""
    if not text:
        return ""
    text = text.replace("\u00a0", " ").replace("\u2011", "-")
    # Repair words split across a line by a PDF hyphenation.
    text = re.sub(r"(?<=[A-Za-z])-\s*\n\s*(?=[A-Za-z])", "", text)
    # Keep line breaks because section detection and certification detection
    # benefit from them, but collapse excessive whitespace.
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extraction_quality(text: str) -> int:
    """Score extracted text by useful resume signals, not just character count."""
    if not text:
        return 0
    low = text.lower()
    score = min(len(re.sub(r"\s+", "", text)) // 20, 80)
    score += 25 if re.search(r"[\w.+-]+@[\w.-]+\.[a-z]{2,}", low) else 0
    score += min(len(detect_skills(text)) if 'detect_skills' in globals() else 0, 20)
    score += sum(5 for p in SECTION_KEYWORDS.values() if any(re.search(x, low) for x in p))
    return score


def extract_text_from_pdf(file) -> str:
    """Extract text using several free PDF strategies and keep the richest result.

    Resume PDFs are unusually difficult because contact details/skills often live
    in sidebars and tables. We try PyMuPDF and both pypdf modes, then select the
    extraction with the strongest resume signals. This is much safer than blindly
    trusting the first parser result.
    """
    try:
        raw = file.getvalue() if hasattr(file, "getvalue") else file.read()
        if not raw:
            raise ValueError("The uploaded PDF is empty.")
        candidates = []

        # Strategy 1: PyMuPDF, sorted reading order.
        if fitz is not None:
            try:
                doc = fitz.open(stream=raw, filetype="pdf")
                if getattr(doc, "needs_pass", False):
                    raise ValueError("This PDF is password-protected. Please upload an unprotected PDF.")
                txt = "\n".join(page.get_text("text", sort=True) or "" for page in doc)
                candidates.append(_normalize_resume_text(txt))
                doc.close()
            except ValueError:
                raise
            except Exception:
                pass

        # Strategy 2/3: pypdf layout + normal extraction.
        try:
            from io import BytesIO
            reader = PdfReader(BytesIO(raw))
            if getattr(reader, "is_encrypted", False):
                raise ValueError("This PDF is password-protected. Please upload an unprotected PDF.")
            layout_pages, normal_pages = [], []
            for page in reader.pages:
                try:
                    layout_pages.append(page.extract_text(extraction_mode="layout") or "")
                except Exception:
                    layout_pages.append("")
                try:
                    normal_pages.append(page.extract_text() or "")
                except Exception:
                    normal_pages.append("")
            candidates.append(_normalize_resume_text("\n".join(layout_pages)))
            candidates.append(_normalize_resume_text("\n".join(normal_pages)))
        except ValueError:
            raise
        except Exception as exc:
            if not candidates:
                raise exc

        candidates = [x for x in candidates if len(re.sub(r"\s+", "", x)) >= 20]
        if not candidates:
            raise ValueError(
                "Couldn't extract readable text from this PDF. It may be a scanned/image-only CV. "
                "Please export a text-based PDF or OCR the CV first."
            )
        # De-duplicate then choose the candidate containing the most useful resume signals.
        unique = list(dict.fromkeys(candidates))
        return max(unique, key=_extraction_quality)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(
            "Couldn't read this PDF. It may be corrupted, encrypted, scanned, "
            "or in an unsupported format. Try exporting the CV as a text-based PDF."
        ) from exc


def contains_keyword(text_lower: str, keyword: str) -> bool:
    """Word-boundary-safe substring check — prevents false positives like
    'oci' matching inside 'association' or 'rn' matching inside 'learning'."""
    pattern = r'(?<![a-zA-Z0-9])' + re.escape(keyword.lower()) + r'(?![a-zA-Z0-9])'
    return re.search(pattern, text_lower) is not None


def check_sections(text: str):
    text_lower = text.lower()
    return {s: any(re.search(p, text_lower) for p in pats) for s, pats in SECTION_KEYWORDS.items()}


def extract_contact_info(text: str):
    """Extract contact details independently of section headings.

    Resume layouts frequently put contact details in a header/side column, so
    relying on a 'Contact' heading is unreliable. We therefore scan the entire
    extracted document with conservative patterns.
    """
    email_matches = re.findall(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text, re.I)
    phone_matches = re.findall(
        r"(?<!\d)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3}[\s.-]?\d{3,4}(?:[\s.-]?\d{2,4})?(?!\d)",
        text,
    )
    linkedin = re.findall(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+", text, re.I)
    github = re.findall(r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9._-]+", text, re.I)
    # Keep only phone-like strings that contain at least 7 digits.
    phones = []
    for p in phone_matches:
        digits = re.sub(r"\D", "", p)
        if 7 <= len(digits) <= 15 and digits not in {re.sub(r"\D", "", x) for x in phones}:
            phones.append(p.strip())
    return {
        "emails": list(dict.fromkeys(email_matches))[:3],
        "phones": phones[:3],
        "linkedin": list(dict.fromkeys(linkedin))[:3],
        "github": list(dict.fromkeys(github))[:3],
    }


@st.cache_resource(show_spinner=False)
def load_local_ai_model():
    """Load a small, free local embedding model once per Streamlit process."""
    if SentenceTransformer is None:
        return None
    try:
        # ~90 MB model, CPU-friendly and widely used for semantic similarity.
        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        return None


def _resume_sentences(text: str):
    lines = [re.sub(r"\s+", " ", x).strip() for x in text.splitlines() if x.strip()]
    chunks = []
    for line in lines:
        if len(line) >= 12:
            chunks.append(line[:500])
        # Also split long prose/bullets into sentence-sized chunks.
        if len(line) > 180:
            chunks.extend([x.strip()[:400] for x in re.split(r"[.!?;]", line) if len(x.strip()) >= 12])
    return list(dict.fromkeys(chunks))[:300]


def ai_semantic_skill_inference(resume_text: str, explicit_skills=None, threshold=0.48):
    """Infer skills from meaning, not just exact words.

    Example: 'built RESTful services with Flask' can support REST API even when
    the literal phrase 'REST API' is absent. Inferred skills are kept separate
    from explicitly detected skills so the UI remains honest.
    """
    model = load_local_ai_model()
    if model is None:
        return [], None
    explicit = {x.lower() for x in (explicit_skills or [])}
    terms = _all_known_skill_terms()
    chunks = _resume_sentences(resume_text)
    if not chunks:
        return [], "AI model loaded, but there was not enough readable text."
    try:
        term_emb = model.encode(terms, normalize_embeddings=True, show_progress_bar=False)
        chunk_emb = model.encode(chunks, normalize_embeddings=True, show_progress_bar=False)
        sims = np.matmul(chunk_emb, term_emb.T)
        inferred = []
        for j, term in enumerate(terms):
            canonical = SKILL_ALIASES.get(term.lower(), term)
            if canonical.lower() in explicit:
                continue
            best = float(np.max(sims[:, j]))
            if best >= threshold:
                inferred.append((best, canonical))
        inferred.sort(reverse=True)
        unique = []
        seen = set()
        for score, skill in inferred:
            k = skill.lower()
            if k not in seen:
                seen.add(k)
                unique.append({"skill": skill, "confidence": round(score * 100)})
            if len(unique) >= 25:
                break
        return unique, "Local AI semantic matching"
    except Exception as exc:
        return [], f"AI inference unavailable: {type(exc).__name__}"


def ai_career_matches(resume_text: str, explicit_skills=None, top_n=5):
    """Hybrid AI career matching: semantic embeddings + explicit evidence.

    Certification is only one signal. A missing certification must never block a
    career recommendation when the resume demonstrates relevant skills/projects.
    """
    model = load_local_ai_model()
    explicit = {x.lower() for x in (explicit_skills or [])}
    profiles = []
    for role, data in CAREER_CATEGORIES.items():
        terms = data["core"] + data["skills"] + data["tools"] + data["certifications"] + data["job_titles"]
        description = role + ". " + ", ".join(dict.fromkeys(terms))
        profiles.append((role, data, description))

    semantic = {}
    if model is not None:
        try:
            resume_chunks = _resume_sentences(resume_text)
            resume_blob = " ".join(resume_chunks[:80])
            emb = model.encode([resume_blob], normalize_embeddings=True, show_progress_bar=False)
            prof_emb = model.encode([x[2] for x in profiles], normalize_embeddings=True, show_progress_bar=False)
            scores = np.matmul(emb, prof_emb.T)[0]
            semantic = {profiles[i][0]: float(scores[i]) for i in range(len(profiles))}
        except Exception:
            semantic = {}

    candidates = []
    text_lower = resume_text.lower()
    for role, data, _ in profiles:
        role_terms = list(dict.fromkeys(data["core"] + data["skills"] + data["tools"]))
        # Match both raw resume text and the AI's inferred/canonical skills.
        # This lets a semantic inference such as "REST API" contribute to a
        # Backend Developer match even when that exact phrase was not printed.
        explicit_role_hits = [sk for sk in explicit if any(sk == term.lower() for term in role_terms)]
        matched_core = [k for k in data["core"] if contains_skill(text_lower, k) or k.lower() in explicit_role_hits]
        matched_skills = [k for k in data["skills"] if contains_skill(text_lower, k) or k.lower() in explicit_role_hits]
        matched_tools = [k for k in data["tools"] if contains_skill(text_lower, k) or k.lower() in explicit_role_hits]
        matched_certs = [k for k in data["certifications"] if contains_skill(text_lower, k)]
        matched_all = list(dict.fromkeys(matched_core + matched_skills + matched_tools + matched_certs))
        explicit_weight = len(matched_core) * 3 + len(matched_skills) * 2 + len(matched_tools) + len(matched_certs) * 2
        sim = semantic.get(role, 0.0)
        # Convert cosine similarity into a useful 0-100 signal. Exact evidence
        # gets more weight so generic semantic similarity cannot dominate.
        semantic_score = max(0, min(100, round((sim - 0.22) / 0.50 * 100))) if sim else 0
        evidence_score = min(100, explicit_weight * 12)
        # Coverage rewards a resume that actually contains several role-relevant
        # skills. This prevents a generic semantic match from dominating.
        role_signal_count = len(set(matched_all))
        coverage_score = min(100, role_signal_count * 18)
        final_score = round(evidence_score * 0.45 + semantic_score * 0.35 + coverage_score * 0.20)
        # Do not require certifications or two keywords. One strong skill is
        # enough to open a career path, while semantic evidence can rescue
        # paraphrased project/experience descriptions.
        if role_signal_count < 1 and semantic_score < 52:
            continue
        candidates.append({
            "category": role,
            "family": data["family"],
            "score": final_score,
            "weight": explicit_weight,
            "semantic_score": semantic_score,
            "matched_keywords": matched_all,
            "job_titles": data["job_titles"] or [role],
            "platforms": FAMILY_PLATFORMS.get(data["family"], []),
        })

    best_per_family = {}
    for c in candidates:
        fam = c["family"]
        if fam not in best_per_family or c["score"] > best_per_family[fam]["score"]:
            best_per_family[fam] = c
    return sorted(best_per_family.values(), key=lambda x: x["score"], reverse=True)[:top_n]


def broaden_career_matches(resume_text: str, detected_skills, inferred_skills=None, top_n=5):
    """Final safety net: recommend realistic career directions even when the
    embedding model is unavailable or a resume uses unusual wording. This is
    still evidence-based: roles are scored only from skills present/inferred.
    """
    all_skills = list(dict.fromkeys([*(detected_skills or []), *[x.get("skill") for x in (inferred_skills or []) if x.get("skill")]]))
    low = resume_text.lower()
    results = []
    for role, data in CAREER_CATEGORIES.items():
        terms = list(dict.fromkeys(data.get("core", []) + data.get("skills", []) + data.get("tools", [])))
        hits = [t for t in terms if contains_skill(low, t)]
        # inferred skill names are canonical; compare them against role terms
        for sk in all_skills:
            if any(sk.lower() == t.lower() or contains_skill((sk+" ").lower(), t) for t in terms):
                if sk not in hits:
                    hits.append(sk)
        if not hits:
            continue
        score = min(96, 35 + len(set(hits))*13)
        results.append({
            "category": role, "family": data["family"], "score": score,
            "weight": len(hits), "semantic_score": 0,
            "matched_keywords": list(dict.fromkeys(hits))[:10],
            "job_titles": data.get("job_titles") or [role],
            "platforms": FAMILY_PLATFORMS.get(data["family"], []),
        })
    results.sort(key=lambda x:(x["score"], x["weight"]), reverse=True)
    return results[:top_n]



# Common resume skills that may not belong to a single career profile.
# These are used for the dedicated Skills Analysis panel and as additional
# signals for career matching.
COMMON_RESUME_SKILLS = [
    "python", "java", "javascript", "typescript", "c", "c++", "c#", "php", "ruby", "go",
    "kotlin", "swift", "r", "sql", "html", "css", "react", "angular", "vue", "node.js",
    "express.js", "django", "flask", "fastapi", "spring", "laravel", "asp.net",
    "git", "github", "docker", "kubernetes", "jenkins", "terraform",
    "aws", "azure", "google cloud", "gcp", "linux", "networking",
    "machine learning", "deep learning", "artificial intelligence", "ai", "nlp",
    "computer vision", "tensorflow", "pytorch", "scikit-learn", "keras", "opencv",
    "pandas", "numpy", "matplotlib", "data analysis", "data visualization",
    "statistics", "excel", "power bi", "tableau", "mongodb", "mysql", "postgresql",
    "oracle", "firebase", "rest api", "api development", "graphql",
    "data structures", "algorithms", "object-oriented programming", "oop",
    "problem solving", "communication", "leadership", "teamwork", "project management",
    "agile", "scrum", "figma", "photoshop", "canva", "content writing",
    "digital marketing", "seo", "customer service", "sales", "research",
]

SKILL_ALIASES = {
    "js": "javascript",
    "ts": "typescript",
    "reactjs": "react",
    "nodejs": "node.js",
    "postgres": "postgresql",
    "mongo": "mongodb",
    "powerbi": "power bi",
    "scikit learn": "scikit-learn",
    "machine-learning": "machine learning",
    "deep-learning": "deep learning",
    "restful api": "rest api",
    "oop": "object-oriented programming",
}

ACRONYM_WHITELIST = {
    "rn", "bls", "acls", "ehr", "sql", "aws", "gcp", "api", "css", "html",
    "php", "ai", "ml", "nlp", "ccna", "pmp", "ceh", "cpr", "icu", "or", "er"
}

GENERIC_JD_STOPWORDS = {
    "the", "and", "for", "with", "you", "are", "our", "will", "your",
    "this", "that", "have", "has", "from", "who", "job", "role",
    "team", "years", "year", "work", "working", "able", "ability",
    "company", "looking", "strong", "excellent", "knowledge", "required",
    "preferred", "plus", "etc", "using", "use", "also", "may", "must",
    "join", "apply", "send", "resume", "candidate", "candidates", "position",
    "opportunity", "environment", "including", "based", "new", "please",
}


def _all_known_skill_terms():
    """Build one de-duplicated skill vocabulary from the career database."""
    terms = set(COMMON_RESUME_SKILLS)
    for data in CAREER_CATEGORIES.values():
        terms.update(data.get("core", []))
        terms.update(data.get("skills", []))
        terms.update(data.get("tools", []))
    return sorted(terms, key=lambda x: (-len(x), x))


def contains_skill(text_lower: str, skill: str) -> bool:
    """Skill-aware matcher with a small alias layer for common spellings."""
    if contains_keyword(text_lower, skill):
        return True
    target = skill.lower()
    aliases = [alias for alias, canonical in SKILL_ALIASES.items()
               if canonical.lower() == target]
    return any(contains_keyword(text_lower, alias) for alias in aliases)


def detect_skills(resume_text: str):
    """Return skills explicitly present in the extracted resume text.

    Matching is case-insensitive and word-boundary safe. Multi-word skills
    and punctuation-heavy skills such as C++, C#, Node.js and .NET are handled
    by the same matcher.
    """
    text_lower = resume_text.lower()
    found = []
    for skill in _all_known_skill_terms():
        canonical = SKILL_ALIASES.get(skill.lower(), skill)
        if contains_skill(text_lower, skill):
            found.append(canonical)
    # De-duplicate aliases/case variants while preserving useful ordering.
    unique = []
    seen = set()
    for skill in found:
        key = skill.lower()
        if key not in seen:
            seen.add(key)
            unique.append(skill)
    return unique


def skill_section_lines(resume_text: str):
    """Extract likely skill lines so we can show what the PDF parser saw."""
    lines = [re.sub(r"\s+", " ", x).strip() for x in resume_text.splitlines()]
    lines = [x for x in lines if x]
    patterns = (
        r"^(technical\s+)?skills?\s*:?\s*$",
        r"^key\s+skills?\s*:?\s*$",
        r"^core\s+skills?\s*:?\s*$",
        r"^technical\s+proficienc(y|ies)\s*:?\s*$",
        r"^proficienc(y|ies)\s*:?\s*$",
    )
    for i, line in enumerate(lines):
        if any(re.search(p, line, re.I) for p in patterns):
            # Capture the heading plus the next few lines until another
            # obvious resume section heading appears.
            collected = []
            for nxt in lines[i + 1:i + 7]:
                if re.match(r"^(experience|education|projects?|certifications?|summary|objective|profile)\b", nxt, re.I):
                    break
                collected.append(nxt)
            return collected
    return []


def analyze_skills(resume_text: str):
    skills = detect_skills(resume_text)
    lines = skill_section_lines(resume_text)
    return {
        "skills": skills,
        "count": len(skills),
        "section_lines": lines,
        "has_skill_section": bool(lines) or bool(re.search(
            r"\b(skills?|technical skills?|proficienc(y|ies))\b", resume_text, re.I
        )),
    }


def keyword_match_score(resume_text: str, job_description: str):
    if not job_description.strip():
        return None, [], []
    raw_words = [w.rstrip('.') for w in re.findall(r"[A-Za-z][A-Za-z\+\#\.]{1,}", job_description)]
    jd_keywords = set()
    for w in raw_words:
        lw = w.lower()
        if lw in GENERIC_JD_STOPWORDS:
            continue
        if len(lw) <= 3 and lw not in ACRONYM_WHITELIST:
            continue
        jd_keywords.add(lw)
    jd_keywords = sorted(jd_keywords)
    if not jd_keywords:
        return None, [], []
    resume_lower = resume_text.lower()
    matched = [kw for kw in jd_keywords if contains_keyword(resume_lower, kw)]
    missing = [kw for kw in jd_keywords if kw not in matched]
    score = round(len(matched) / len(jd_keywords) * 100)
    return score, matched, missing


def analyze_action_verbs(text: str):
    text_lower = text.lower()
    used = [v for v in ACTION_VERBS if contains_keyword(text_lower, v)]
    weak = [p for p in WEAK_PHRASES if contains_keyword(text_lower, p)]
    return used, weak


def has_quantifiable_results(text: str) -> bool:
    return bool(re.search(r"\d+%|\$\d+|\d+\+|\d+x\b|increased by \d|reduced by \d", text.lower()))


def word_count_check(text: str) -> int:
    return len(text.split())


def detect_certifications(text: str):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    cert_lines = []
    for line in lines:
        low = line.lower()
        # Skip lines that are ONLY a section heading like "CERTIFICATIONS"
        cleaned = re.sub(r'^[\-\*•\u2022\s]+', '', low).rstrip(':').strip()
        if cleaned in CERT_HEADER_ONLY:
            continue
        if not (4 <= len(line) <= 140):
            continue
        has_cert_word = "certificat" in low and cleaned not in CERT_HEADER_ONLY
        has_provider = any(contains_keyword(low, p) for p in CERT_PROVIDERS)
        has_known_cert = any(k in low for k in KNOWN_CERT_KEYWORDS)
        if has_cert_word or has_provider or has_known_cert:
            cert_lines.append(line)
    seen, unique = set(), []
    for c in cert_lines:
        key = c.lower()
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique[:10]


def compute_overall_score(sections_found, used_verbs, weak_phrases, has_numbers,
                           word_count, keyword_score):
    score, max_score = 0, 0
    max_score += 30
    score += (sum(sections_found.values()) / len(sections_found)) * 30
    max_score += 15
    score += min(len(used_verbs) / 8, 1) * 15
    score -= min(len(weak_phrases) * 3, 10)
    max_score += 15
    score += 15 if has_numbers else 0
    max_score += 10
    if 350 <= word_count <= 800:
        score += 10
    elif 200 <= word_count < 350 or 800 < word_count <= 1000:
        score += 5
    if keyword_score is not None:
        max_score += 30
        score += (keyword_score / 100) * 30
    return max(0, min(100, round((score / max_score) * 100) if max_score else 0))


def compute_resume_quality(sections_found, used_verbs, weak_phrases, has_numbers, word_count):
    """Quality score excluding job-description keyword matching."""
    score, max_score = 0, 0
    max_score += 35
    score += (sum(sections_found.values()) / len(sections_found)) * 35
    max_score += 25
    score += min(len(used_verbs) / 8, 1) * 25
    score -= min(len(weak_phrases) * 4, 15)
    max_score += 25
    score += 25 if has_numbers else 0
    max_score += 15
    if 350 <= word_count <= 800:
        score += 15
    elif 200 <= word_count < 350 or 800 < word_count <= 1000:
        score += 7
    return max(0, min(100, round((score / max_score) * 100) if max_score else 0))


def score_color(score):
    if score >= 80:
        return SUCCESS
    elif score >= 60:
        return WARNING
    return ERROR


def match_explanation(score):
    if score is None:
        return None
    if score >= 80:
        return "Excellent — your resume matches most of the important keywords in this job description."
    elif score >= 60:
        return "Good match — a few relevant keywords are missing but the core alignment is solid."
    elif score >= 40:
        return "Moderate match — consider adding more keywords from the job description."
    return "Low match — this resume may need significant tailoring for this specific role."


def generate_recommendations(sections_found, used_verbs, weak_phrases, has_numbers,
                              word_count, keyword_score, top_career=None):
    recs = []
    missing_sections = [s for s, v in sections_found.items() if not v]
    if missing_sections:
        recs.append({"text": f"Add missing resume sections: {', '.join(missing_sections)}.", "priority": "High"})
    if weak_phrases:
        recs.append({"text": "Replace weak/generic phrases with specific, results-driven statements.", "priority": "High"})
    if keyword_score is not None and keyword_score < 50:
        recs.append({"text": "Add more keywords from the job description to improve ATS match rate.", "priority": "High"})
    if not has_numbers:
        recs.append({"text": "Quantify your achievements with numbers, percentages, or dollar amounts.", "priority": "Medium"})
    if len(used_verbs) < 5:
        recs.append({"text": "Use more strong action verbs at the start of bullet points.", "priority": "Medium"})
    if word_count < 350:
        recs.append({"text": "Your resume looks short — add more detail about your experience and projects.", "priority": "Medium"})
    elif word_count > 1000:
        recs.append({"text": "Your resume is long — trim it to the most relevant, impactful points.", "priority": "Medium"})

    if top_career and top_career in CATEGORY_SPECIFIC_TIPS:
        for tip in CATEGORY_SPECIFIC_TIPS[top_career]:
            recs.append({"text": tip, "priority": "Suggestion"})
    elif not missing_sections and not weak_phrases and has_numbers and len(used_verbs) >= 5:
        recs.append({"text": "Your resume is in strong shape — consider adding a relevant certification to stand out further.", "priority": "Suggestion"})
    return recs


def generate_before_after(weak_phrases_found):
    examples = []
    for phrase in weak_phrases_found:
        if phrase in BEFORE_AFTER_TEMPLATES:
            before, after = BEFORE_AFTER_TEMPLATES[phrase]
            examples.append((before, after))
    return examples


def make_gauge(score):
    color = score_color(score)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={'suffix': "/100", 'font': {'size': 40, 'color': TEXT}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': MUTED, 'tickfont': {'color': MUTED}},
            'bar': {'color': color, 'thickness': 0.3},
            'bgcolor': CARD_BG_2,
            'borderwidth': 0,
            'steps': [
                {'range': [0, 60], 'color': "#2a1420"},
                {'range': [60, 80], 'color': "#2a2414"},
                {'range': [80, 100], 'color': "#122a1c"},
            ],
        }
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=25, b=10),
                       paper_bgcolor="rgba(0,0,0,0)", font={'color': TEXT})
    return fig


def make_breakdown_chart(sections_found, used_verbs, has_numbers, word_count, keyword_score):
    categories = ["Resume Sections", "Keywords", "Action Verbs", "Quantifiable Results", "Resume Length"]
    values = [
        round(sum(sections_found.values()) / len(sections_found) * 100),
        keyword_score if keyword_score is not None else 0,
        round(min(len(used_verbs) / 8, 1) * 100),
        100 if has_numbers else 0,
        100 if 350 <= word_count <= 800 else (50 if 200 <= word_count <= 1000 else 20),
    ]
    fig = go.Figure(go.Bar(
        x=values, y=categories, orientation='h',
        marker=dict(color=PRIMARY, line=dict(color=LIGHT_BLUE, width=0)),
        text=[f"{v}%" for v in values], textposition="outside", textfont=dict(color=TEXT),
    ))
    fig.update_layout(
        height=280, margin=dict(l=10, r=30, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(range=[0, 110], showgrid=False, color=MUTED),
        yaxis=dict(color=TEXT), font=dict(color=TEXT),
    )
    return fig


def match_careers(resume_text: str, top_n: int = 3, min_signals: int = 2,
                   min_weight: int = 6, target_weight: int = 12, min_score: int = 15):
    """Match resume text against the structured career knowledge base using
    weighted signals instead of flat keyword counting.

    Weighting: core keywords = 3, skills = 2, tools = 1, certifications = 2.
    A role only qualifies as a real match if it has BOTH a minimum number of
    distinct matched signals (min_signals) AND a minimum total weight
    (min_weight) — this is what prevents one incidental keyword (e.g. a short
    acronym that happens to appear inside an unrelated word) from producing a
    misleading recommendation. Overlapping/related roles (e.g. AI Engineer vs
    ML Engineer) are grouped by family and only the strongest role per family
    is kept, so results read as distinct career directions rather than
    near-duplicates."""
    text_lower = resume_text.lower()
    candidates = []

    for role, data in CAREER_CATEGORIES.items():
        matched_core = [k for k in data["core"] if contains_skill(text_lower, k)]
        matched_skills = [k for k in data["skills"] if contains_skill(text_lower, k)]
        matched_tools = [k for k in data["tools"] if contains_skill(text_lower, k)]
        matched_certs = [k for k in data["certifications"] if contains_skill(text_lower, k)]

        matched_all = matched_core + matched_skills + matched_tools + matched_certs
        distinct_signals = len(matched_all)
        weight = (len(matched_core) * 3 + len(matched_skills) * 2
                  + len(matched_tools) * 1 + len(matched_certs) * 2)

        if distinct_signals < min_signals or weight < min_weight:
            continue

        score = min(100, round(weight / target_weight * 100))
        if score < min_score:
            continue

        candidates.append({
            "category": role,
            "family": data["family"],
            "score": score,
            "weight": weight,
            "matched_keywords": matched_all,
            "job_titles": data["job_titles"] or [role],
            "platforms": FAMILY_PLATFORMS.get(data["family"], []),
        })

    # Keep only the strongest role per family so closely related roles
    # (e.g. AI Engineer / ML Engineer / AI Research Engineer) don't crowd
    # out other distinct career directions in the top results.
    best_per_family = {}
    for c in candidates:
        fam = c["family"]
        if fam not in best_per_family or c["weight"] > best_per_family[fam]["weight"]:
            best_per_family[fam] = c

    results = list(best_per_family.values())
    results.sort(key=lambda r: (r["score"], r["weight"]), reverse=True)
    return results[:top_n]



def build_search_url(platform_name: str, job_title: str):
    base = PLATFORM_SEARCH_URLS.get(platform_name)
    if not base:
        return None
    return base.format(query=urllib.parse.quote(job_title))


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_remoteok_jobs():
    try:
        resp = requests.get(
            "https://remoteok.com/api",
            headers={"User-Agent": "Mozilla/5.0 (ResumeAnalyzerApp)"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return [j for j in data if isinstance(j, dict) and j.get("position")]
    except Exception:
        return []


def filter_jobs_by_keywords(jobs, keywords, limit=6, min_matches=2):
    """Only return jobs with at least `min_matches` distinct keyword hits,
    using word-boundary matching, to avoid loosely-related jobs (e.g. a
    'Customer Support' role matching on a single generic word)."""
    keywords_lower = sorted(set(k.lower() for k in keywords if len(k) >= 4))
    scored = []
    for job in jobs:
        haystack = " ".join([
            job.get("position", ""), job.get("description", ""),
            " ".join(job.get("tags", []) or []),
        ]).lower()
        hit_count = sum(1 for kw in keywords_lower if contains_keyword(haystack, kw))
        if hit_count >= min_matches:
            scored.append((hit_count, job))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [job for _, job in scored[:limit]]


USAGE_LOG_FILE = "usage_log.csv"
LOG_COLUMNS = ["timestamp", "name", "ats_score", "resume_quality", "keyword_match",
               "word_count", "top_career_match"]


def log_usage(name, ats_score, quality_score, keyword_score, word_count, top_career):
    """Append one row per analysis to a local CSV log — lets the developer see
    who tried the tool and what result they got. Skips writing if an
    identical entry for the same name was just logged a few seconds ago
    (guards against duplicate rows from double-clicking Analyze). Best-effort:
    if writing fails (e.g. read-only filesystem on some hosts), the app
    should not crash."""
    try:
        clean_name = name.strip() if name else "Anonymous"
        new_row = [
            clean_name, str(ats_score), str(quality_score),
            str(keyword_score) if keyword_score is not None else "N/A",
            str(word_count), top_career or "N/A",
        ]

        if os.path.isfile(USAGE_LOG_FILE):
            with open(USAGE_LOG_FILE, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            if rows:
                last = rows[-1]
                last_row = [last["name"], last["ats_score"], last["resume_quality"],
                            last["keyword_match"], last["word_count"], last["top_career_match"]]
                if last_row == new_row:
                    last_time = datetime.datetime.strptime(last["timestamp"], "%Y-%m-%d %H:%M:%S")
                    if (datetime.datetime.now() - last_time).total_seconds() < 5:
                        return  # duplicate — skip

        file_exists = os.path.isfile(USAGE_LOG_FILE)
        with open(USAGE_LOG_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(LOG_COLUMNS)
            writer.writerow([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")] + new_row)
    except Exception:
        pass


def read_usage_log():
    if not os.path.isfile(USAGE_LOG_FILE):
        return []
    with open(USAGE_LOG_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def generate_report_text(name_hint, overall, quality, keyword_score, word_count,
                          sections_found, used_verbs, weak_phrases, has_numbers,
                          matched_kw, missing_kw, certifications, recommendations, career_matches):
    lines = []
    lines.append("AI RESUME ANALYZER — ANALYSIS REPORT")
    lines.append("=" * 45)
    lines.append(f"ATS Score: {overall}/100")
    lines.append(f"Resume Quality: {quality}/100")
    lines.append(f"Keyword Match: {keyword_score if keyword_score is not None else 'N/A (no job description provided)'}")
    lines.append(f"Word Count: {word_count}")
    lines.append("")
    lines.append("RESUME SECTIONS DETECTED")
    lines.append("-" * 45)
    for s, present in sections_found.items():
        lines.append(f"[{'x' if present else ' '}] {s}")
    lines.append("")
    lines.append("WRITING QUALITY")
    lines.append("-" * 45)
    lines.append(f"Action verbs found: {', '.join(used_verbs) if used_verbs else 'None'}")
    lines.append(f"Weak phrases found: {', '.join(weak_phrases) if weak_phrases else 'None'}")
    lines.append(f"Quantifiable results present: {'Yes' if has_numbers else 'No'}")
    lines.append("")
    if matched_kw or missing_kw:
        lines.append("JOB DESCRIPTION KEYWORD MATCH")
        lines.append("-" * 45)
        lines.append(f"Matched: {', '.join(matched_kw) if matched_kw else 'None'}")
        lines.append(f"Missing: {', '.join(missing_kw) if missing_kw else 'None'}")
        lines.append("")
    lines.append("CERTIFICATIONS DETECTED")
    lines.append("-" * 45)
    lines.append(", ".join(certifications) if certifications else "None detected")
    lines.append("")
    lines.append("SMART RECOMMENDATIONS")
    lines.append("-" * 45)
    for r in recommendations:
        lines.append(f"[{r['priority']}] {r['text']}")
    lines.append("")
    if career_matches:
        lines.append("BEST CAREER MATCHES")
        lines.append("-" * 45)
        for m in career_matches:
            lines.append(f"{m['category']} — {m['score']}% match")
            lines.append(f"  Suggested titles: {', '.join(m['job_titles'])}")
    lines.append("")
    lines.append("Generated by AI Resume Analyzer — Developed by Aroon Kumar Maheshwari")
    return "\n".join(lines)


# ---------------------------
# Secure admin console
# ---------------------------
ADMIN_DIR = Path(".streamlit")
ADMIN_AUTH_FILE = ADMIN_DIR / "admin_auth.json"
ACTIVITY_LOG_FILE = Path("activity_log.jsonl")
ADMIN_SESSION_MINUTES = 30
PBKDF2_ITERATIONS = 310_000
MAX_ADMIN_ATTEMPTS = 5
ADMIN_LOCK_MINUTES = 10
ADMIN_SETUP_KEY_MIN_LENGTH = 24

def _secret_value(key, default=""):
    try:
        value = st.secrets.get(key, default)
        if value is not None:
            return value
    except Exception:
        pass
    return os.environ.get(key, default)

def _hash_password(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return {"salt": salt.hex(), "hash": digest.hex(), "iterations": PBKDF2_ITERATIONS}

def _verify_password(password, record):
    try:
        salt=bytes.fromhex(record["salt"]); iterations=int(record.get("iterations", PBKDF2_ITERATIONS))
        digest=hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations).hex()
        return secrets.compare_digest(digest, record["hash"])
    except Exception: return False

def _load_admin_auth():
    if ADMIN_AUTH_FILE.exists():
        try: return json.loads(ADMIN_AUTH_FILE.read_text(encoding="utf-8"))
        except Exception: return None
    username=str(_secret_value("ADMIN_USERNAME", "")).strip(); password=str(_secret_value("ADMIN_PASSWORD", ""))
    if username and password:
        ADMIN_DIR.mkdir(parents=True, exist_ok=True)
        data={"username":username,"password":_hash_password(password),"created_at":datetime.datetime.now().isoformat(timespec="seconds")}
        try: ADMIN_AUTH_FILE.write_text(json.dumps(data,indent=2),encoding="utf-8")
        except Exception: pass
        return data
    return None

def _save_admin_auth(username,password):
    ADMIN_DIR.mkdir(parents=True,exist_ok=True)
    data={"username":username.strip(),"password":_hash_password(password),"updated_at":datetime.datetime.now().isoformat(timespec="seconds")}
    ADMIN_AUTH_FILE.write_text(json.dumps(data,indent=2),encoding="utf-8"); return data

def log_activity(event,details=None,user=None,success=True):
    try:
        payload={"timestamp":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"event":event,"success":bool(success),"user":user or "Anonymous","details":details or {}}
        with ACTIVITY_LOG_FILE.open("a",encoding="utf-8") as f: f.write(json.dumps(payload,ensure_ascii=False)+"\n")
    except Exception: pass

def read_activity_log():
    if not ACTIVITY_LOG_FILE.exists(): return []
    rows=[]
    try:
        for line in ACTIVITY_LOG_FILE.read_text(encoding="utf-8").splitlines():
            if line.strip(): rows.append(json.loads(line))
    except Exception: pass
    return rows

def _admin_is_authenticated():
    until=st.session_state.get("admin_authenticated_until")
    return bool(st.session_state.get("admin_authenticated") and until and time.time()<until)

def _admin_logout():
    st.session_state.admin_authenticated=False; st.session_state.admin_authenticated_until=0; st.session_state.admin_username=""
    log_activity("admin_logout",user="Admin"); st.rerun()

def render_admin_console():
    auth=_load_admin_auth()
    st.markdown('<div class="admin-shell">',unsafe_allow_html=True)
    st.markdown("""<div class="admin-hero"><div class="admin-title">🛡️ Admin Control Center</div><div class="admin-sub">Private audit dashboard • security • analytics • activity monitoring</div></div>""",unsafe_allow_html=True)
    if not auth:
        # Never expose an unauthenticated "create admin" form. A public first-run
        # setup page would let anyone who discovers ?admin=1 claim the account.
        setup_key = str(_secret_value("ADMIN_SETUP_KEY", "")).strip()
        if len(setup_key) < ADMIN_SETUP_KEY_MIN_LENGTH:
            st.error("Admin account is not initialized.")
            st.markdown(
                "For first-time setup, create `.streamlit/secrets.toml` (or set environment variables) "
                "with **ADMIN_USERNAME**, **ADMIN_PASSWORD**, and a random **ADMIN_SETUP_KEY** of at least "
                f"{ADMIN_SETUP_KEY_MIN_LENGTH} characters, then restart Streamlit."
            )
            st.code('ADMIN_USERNAME = "your_admin_username"\nADMIN_PASSWORD = "use-a-long-unique-password"\nADMIN_SETUP_KEY = "generate-a-long-random-setup-key-here"', language="toml")
            st.caption("The setup key is only used to bootstrap the local hashed credential file and is never displayed after setup.")
            st.markdown('</div>',unsafe_allow_html=True); st.stop()

        st.markdown('<div class="security-note">🔐 Secure first-run initialization. A setup key is required before an administrator account can be created.</div>',unsafe_allow_html=True)
        with st.form("admin_setup_form"):
            setup_input=st.text_input("One-time setup key",type="password",autocomplete="off")
            u=st.text_input("Admin username",placeholder="Choose an administrator username",autocomplete="username")
            p1=st.text_input("Create password",type="password",placeholder="At least 12 characters",autocomplete="new-password")
            p2=st.text_input("Confirm password",type="password",autocomplete="new-password")
            if st.form_submit_button("Create Secure Admin Account", type="primary"):
                if not secrets.compare_digest(setup_input, setup_key):
                    log_activity("admin_setup_failed",{"reason":"invalid_setup_key"},user="Unknown",success=False)
                    st.error("Invalid setup key.")
                elif len(u.strip())<4: st.error("Username must be at least 4 characters.")
                elif len(p1)<12: st.error("Password must be at least 12 characters.")
                elif p1!=p2: st.error("Passwords do not match.")
                else:
                    _save_admin_auth(u,p1)
                    log_activity("admin_account_created",{"username":u.strip()},user=u.strip())
                    st.success("Admin account created. Please log in.")
                    st.rerun()
        st.markdown('</div>',unsafe_allow_html=True); st.stop()
    if not _admin_is_authenticated():
        if st.session_state.get("admin_lock_until",0)>time.time():
            remaining=int(st.session_state.admin_lock_until-time.time()); st.error(f"Too many failed login attempts. Try again in about {max(1,remaining//60+1)} minute(s)."); st.stop()
        with st.form("admin_login_form"):
            username=st.text_input("Username",autocomplete="username")
            password=st.text_input("Password",type="password",autocomplete="current-password")
            if st.form_submit_button("🔐 Secure Login",type="primary"):
                if username.strip()==auth.get("username") and _verify_password(password,auth.get("password",{})):
                    st.session_state.admin_authenticated=True; st.session_state.admin_authenticated_until=time.time()+ADMIN_SESSION_MINUTES*60; st.session_state.admin_username=username.strip(); st.session_state.admin_attempts=0
                    log_activity("admin_login",{"session_minutes":ADMIN_SESSION_MINUTES},user=username.strip()); st.rerun()
                else:
                    attempts=int(st.session_state.get("admin_attempts",0))+1; st.session_state.admin_attempts=attempts
                    log_activity("admin_login_failed",{"attempt":attempts},user=username.strip() or "Unknown",success=False)
                    if attempts>=MAX_ADMIN_ATTEMPTS: st.session_state.admin_lock_until=time.time()+ADMIN_LOCK_MINUTES*60; st.error("Too many failed attempts. Admin login is temporarily locked.")
                    else: st.error("Invalid username or password.")
        st.caption(f"Session security: {ADMIN_SESSION_MINUTES}-minute inactivity window • failed-login protection enabled"); st.markdown('</div>',unsafe_allow_html=True); st.stop()
    st.session_state.admin_authenticated_until=time.time()+ADMIN_SESSION_MINUTES*60
    c1,c2=st.columns([8,1])
    with c1: st.success(f"Authenticated as **{st.session_state.get('admin_username','Admin')}**")
    with c2:
        if st.button("Logout",key="admin_logout"): _admin_logout()
    activity=read_activity_log(); usage=[]
    try:
        if Path("usage_log.csv").exists():
            with Path("usage_log.csv").open(newline="",encoding="utf-8") as f: usage=list(csv.DictReader(f))
    except Exception: pass
    analyses=[r for r in activity if r.get("event")=="analysis_completed"]; failed=[r for r in activity if r.get("event") in {"analysis_failed","admin_login_failed"}]
    unique_users=len({str(r.get("user","Anonymous")).strip().lower() for r in analyses})
    scores=[]
    for r in analyses:
        try: scores.append(float(r.get("details",{}).get("ats_score")))
        except (TypeError,ValueError): pass
    avg_score=round(sum(scores)/len(scores),1) if scores else 0
    st.markdown("### 📊 Overview")
    m=st.columns(5); metrics=[("🧠",len(analyses),"Analyses"),("👥",unique_users,"Users"),("📈",avg_score,"Avg ATS"),("⚠️",len(failed),"Failures"),("📝",len(usage),"Legacy logs")]
    for col,(icon,val,label) in zip(m,metrics): col.markdown(f'<div class="metric-card"><div class="metric-icon">{icon}</div><div class="metric-value">{val}</div><div class="metric-label">{label}</div></div>',unsafe_allow_html=True)
    st.markdown("### 📋 Activity Monitor")
    if activity:
        import pandas as pd
        rows=[{"Time":r.get("timestamp",""),"Event":r.get("event",""),"User":r.get("user",""),"Success":"✓" if r.get("success",True) else "✕","Details":json.dumps(r.get("details",{}),ensure_ascii=False)} for r in reversed(activity)]
        df=pd.DataFrame(rows); event_filter=st.multiselect("Filter events",sorted(df["Event"].unique().tolist()),default=[])
        if event_filter: df=df[df["Event"].isin(event_filter)]
        st.dataframe(df,use_container_width=True,hide_index=True); st.download_button("📥 Export full activity (CSV)",df.to_csv(index=False).encode("utf-8"),"admin_activity.csv","text/csv")
    else: st.info("No activity has been recorded yet.")
    st.markdown("### 🔐 Change Admin Password")
    with st.form("change_admin_password"):
        current=st.text_input("Current password",type="password"); new1=st.text_input("New password",type="password"); new2=st.text_input("Confirm new password",type="password")
        if st.form_submit_button("Update Password"):
            if not _verify_password(current,auth.get("password",{})): log_activity("password_change_failed",user=st.session_state.get("admin_username","Admin"),success=False); st.error("Current password is incorrect.")
            elif len(new1)<12: st.error("New password must be at least 12 characters.")
            elif new1!=new2: st.error("New passwords do not match.")
            else: _save_admin_auth(auth["username"],new1); log_activity("password_changed",user=auth["username"]); st.success("Password changed successfully. Your current session remains active.")
    st.markdown('</div>',unsafe_allow_html=True)

try: _admin_mode=str(st.query_params.get("admin",""))=="1"
except Exception: _admin_mode=False
if _admin_mode:
    render_admin_console()
    st.stop()

# Record a lightweight app/session event once per browser session.
if not st.session_state.get("_activity_session_logged"):
    log_activity("app_opened", {"page":"public_analyzer"}, user="Anonymous")
    st.session_state["_activity_session_logged"] = True

# ---------------------------
# HERO
# ---------------------------

if not st.session_state.get("_boot_animation_shown"):
    st.session_state["_boot_animation_shown"] = True
    st.markdown("""
    <div class="boot-splash" id="bootSplash" aria-live="polite">
      <div class="boot-ring"></div>
      <div class="boot-title">AI RESUME ANALYZER</div>
      <div class="boot-sub">Secure AI engine is loading<span class="boot-dots"></span></div>
    </div>
    """, unsafe_allow_html=True)

st.markdown(f"""
<div class="hero">
    <span class="badge">AI POWERED</span>
    <div class="hero-title">AI Resume Analyzer</div>
    <div class="hero-subtitle">AI-powered ATS scoring, job matching & career insights</div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### How it works")
    st.markdown("1️⃣ Enter your name\n\n2️⃣ Upload your resume (PDF)\n\n3️⃣ Optionally paste a job description\n\n4️⃣ Get your ATS score, career matches & live jobs")
    st.divider()
    st.markdown("Built with **Python • Streamlit • Plotly • PyPDF2**")


# ---------------------------
# INPUT AREA
# ---------------------------

st.markdown('<div class="card"><div class="card-title">👤 Your Name</div><div class="card-subtitle">So Aroon can see who tried the tool and what result they got.</div>', unsafe_allow_html=True)
visitor_name = st.text_input("Your name", placeholder="e.g. Ali", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown('<div class="card"><div class="card-title">📤 Resume</div><div class="card-subtitle">Upload your resume as a PDF file</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"], label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card"><div class="card-title">🎯 Job Description</div><div class="card-subtitle">Optional — paste a job posting to check keyword match</div>', unsafe_allow_html=True)
    job_description = st.text_area(
        "Job description", height=140,
        placeholder="Paste the job posting here...", label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)

# Log a resume selection once per browser session without storing its contents.
if uploaded_file is not None:
    _upload_signature = f"{uploaded_file.name}:{uploaded_file.size}"
    if st.session_state.get("_last_upload_signature") != _upload_signature:
        log_activity(
            "resume_uploaded",
            {"file_name": uploaded_file.name, "file_size_bytes": uploaded_file.size},
            user=visitor_name.strip() or "Anonymous",
        )
        st.session_state["_last_upload_signature"] = _upload_signature

analyze_btn = st.button("🔍  Analyze Resume →", type="primary")

# ---------------------------
# ANALYSIS
# ---------------------------

if analyze_btn:
    if not visitor_name.strip():
        log_activity("analysis_validation_failed", {"reason":"missing_name"}, user="Anonymous", success=False)
        st.error("Please enter your name before analyzing.")
    elif not uploaded_file:
        log_activity("analysis_validation_failed", {"reason":"missing_resume"}, user=visitor_name.strip(), success=False)
        st.error("Please upload a PDF resume first.")
    elif uploaded_file.size > MAX_UPLOAD_MB * 1024 * 1024:
        log_activity("analysis_validation_failed", {"reason":"file_too_large", "file_size_bytes":uploaded_file.size}, user=visitor_name.strip(), success=False)
        st.error(f"File is too large ({uploaded_file.size / (1024*1024):.1f} MB). Please upload a PDF under {MAX_UPLOAD_MB} MB.")
    else:
        # Animated analysis workspace: the user can see that the AI is actually
        # processing the PDF instead of staring at a frozen page.
        loader = st.empty()
        def show_analysis_step(step, message):
            loader.markdown(f"""<div class='analysis-loader'>
                <div class='ai-orbit'></div>
                <div class='analysis-pulse'>AI RESUME ENGINE • PROCESSING</div>
                <div class='analysis-step'>{step}/6 — {html.escape(message)}</div>
            </div>""", unsafe_allow_html=True)

        try:
            log_activity("analysis_started", {"file_name": uploaded_file.name, "file_size_bytes": uploaded_file.size}, user=visitor_name.strip())
            show_analysis_step(1, "Reading every page and reconstructing the resume layout")
            text = extract_text_from_pdf(uploaded_file)
            time.sleep(0.25)
            if not text.strip():
                st.error("Couldn't extract text from this PDF. Make sure it is a text PDF or OCR it first.")
                loader.empty()
                st.stop()

            show_analysis_step(2, "Finding contact details, sections, education and certifications")
            sections_found = check_sections(text)
            certifications = detect_certifications(text)
            contact_info = extract_contact_info(text)
            time.sleep(0.2)

            show_analysis_step(3, "Detecting explicit skills across the entire CV")
            skill_analysis = analyze_skills(text)
            time.sleep(0.2)

            show_analysis_step(4, "Using local AI to infer skills from projects and experience")
            ai_inferred_skills, ai_status = ai_semantic_skill_inference(text, skill_analysis["skills"])
            combined_skills = list(dict.fromkeys(skill_analysis["skills"] + [x["skill"] for x in ai_inferred_skills]))
            time.sleep(0.25)

            show_analysis_step(5, "Matching your complete skill profile to career paths")
            used_verbs, weak_phrases = analyze_action_verbs(text)
            has_numbers = has_quantifiable_results(text)
            word_count = word_count_check(text)
            keyword_score, matched_kw, missing_kw = keyword_match_score(text, job_description)
            career_matches = ai_career_matches(text, explicit_skills=combined_skills, top_n=5)
            if not career_matches:
                career_matches = broaden_career_matches(text, skill_analysis["skills"], ai_inferred_skills, top_n=5)
            time.sleep(0.3)

            show_analysis_step(6, "Finding live jobs that match your detected skills")
            overall = compute_overall_score(sections_found, used_verbs, weak_phrases,
                                             has_numbers, word_count, keyword_score)
            quality = compute_resume_quality(sections_found, used_verbs, weak_phrases,
                                              has_numbers, word_count)
            top_career_name = career_matches[0]["category"] if career_matches else None
        except ValueError as e:
            loader.empty()
            st.error(str(e))
            st.stop()
        loader.empty()
        recommendations = generate_recommendations(sections_found, used_verbs, weak_phrases,
                                                     has_numbers, word_count, keyword_score,
                                                     top_career=top_career_name)
        before_after = generate_before_after(weak_phrases)

        log_usage(visitor_name, overall, quality, keyword_score, word_count, top_career_name)
        log_activity("analysis_completed", {"file_name": uploaded_file.name, "file_size_bytes": uploaded_file.size, "word_count": word_count, "ats_score": overall, "resume_quality": quality, "top_career": top_career_name or "N/A", "skills_detected": len(skill_analysis.get("skills", [])), "ai_skills_inferred": len(ai_inferred_skills), "certifications_detected": len(certifications)}, user=visitor_name.strip())

        # ---------------------------
        # EXECUTIVE SUMMARY
        # ---------------------------
        st.markdown("---")
        m1, m2, m3, m4 = st.columns(4)
        metrics = [
            (m1, "🎯", f"{overall}/100", "ATS Score"),
            (m2, "🔑", f"{keyword_score}%" if keyword_score is not None else "—", "Keyword Match"),
            (m3, "✨", f"{quality}%", "Resume Quality"),
            (m4, "📝", f"{word_count}", "Word Count"),
        ]
        for col, icon, value, label in metrics:
            with col:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-icon">{icon}</div>
                    <div class="metric-value">{value}</div>
                    <div class="metric-label">{label}</div>
                </div>
                """, unsafe_allow_html=True)

        # ---------------------------
        # ATS GAUGE + BREAKDOWN
        # ---------------------------
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">ATS Compatibility</div>', unsafe_allow_html=True)
        gcol1, gcol2 = st.columns([1, 1.3])
        with gcol1:
            st.plotly_chart(make_gauge(overall), use_container_width=True)
            status = "Excellent" if overall >= 80 else ("Good" if overall >= 60 else "Needs Improvement")
            st.markdown(f"<p style='text-align:center; color:{score_color(overall)}; font-weight:700; font-size:16px;'>{status}</p>", unsafe_allow_html=True)
        with gcol2:
            st.markdown("**Score Breakdown**")
            st.plotly_chart(make_breakdown_chart(sections_found, used_verbs, has_numbers, word_count, keyword_score), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # ---------------------------
        # RESUME HEALTH
        # ---------------------------
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">📋 Resume Health</div>', unsafe_allow_html=True)
        hcols = st.columns(4)
        for i, (section, present) in enumerate(sections_found.items()):
            with hcols[i % 4]:
                cls = "status-yes" if present else "status-no"
                icon = "✅" if present else "⚠️"
                st.markdown(f"<div class='status-badge {cls}'>{icon} {section}</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # ---------------------------
        # CONTACT INFO ANALYSIS
        # ---------------------------
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">📇 Contact Information</div>', unsafe_allow_html=True)
        contact_cols = st.columns(4)
        contact_items = [
            ("📧 Email", contact_info["emails"]),
            ("📱 Phone", contact_info["phones"]),
            ("💼 LinkedIn", contact_info["linkedin"]),
            ("🐙 GitHub", contact_info["github"]),
        ]
        for col, (label, values) in zip(contact_cols, contact_items):
            with col:
                if values:
                    st.markdown(f"**{label}**")
                    for value in values:
                        st.write(value)
                else:
                    st.caption(f"{label}: not detected")
        st.markdown('</div>', unsafe_allow_html=True)

        # ---------------------------
        # SKILLS ANALYSIS
        # ---------------------------
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">🧠 Skills Analysis</div>', unsafe_allow_html=True)
        if skill_analysis["skills"]:
            st.write(
                f"**{skill_analysis['count']} skill(s) detected from your resume:**"
            )
            skill_pills = "".join(
                f"<span class='pill pill-blue'>{html.escape(skill)}</span>"
                for skill in skill_analysis["skills"]
            )
            st.markdown(skill_pills, unsafe_allow_html=True)
            if skill_analysis["section_lines"]:
                with st.expander("What the PDF extractor read from your Skills section"):
                    st.code("\n".join(skill_analysis["section_lines"]))
        elif skill_analysis["has_skill_section"]:
            st.warning(
                "A Skills/Proficiency section was found, but no known skills "
                "could be matched. The PDF may use an unusual skill name, "
                "image-based text, or a formatting pattern not yet recognized."
            )
            if skill_analysis["section_lines"]:
                with st.expander("Show extracted Skills section"):
                    st.code("\n".join(skill_analysis["section_lines"]))
        else:
            st.warning(
                "No Skills section was detected. The analyzer will still scan the entire CV "
                "and can infer skills from project/experience language."
            )

        if ai_inferred_skills:
            st.markdown("**🤖 AI-inferred skills (semantic evidence)**")
            st.caption("These are inferred from the meaning of your CV, not just exact keyword matches.")
            inferred_pills = "".join(
                f"<span class='pill pill-good'>{html.escape(x['skill'])} · {x['confidence']}%</span>"
                for x in ai_inferred_skills
            )
            st.markdown(inferred_pills, unsafe_allow_html=True)
        elif ai_status:
            st.caption(ai_status)
        st.markdown('</div>', unsafe_allow_html=True)

        with st.expander("🔎 PDF extraction check"):
            st.caption(
                "If a skill appears in your PDF but not above, check this text. "
                "If the skill is missing here, the PDF is likely image-based or "
                "uses a layout that does not contain selectable text."
            )
            st.text_area(
                "Extracted resume text",
                text,
                height=220,
                key="extracted_resume_text",
            )

        # ---------------------------
        # CERTIFICATIONS
        # ---------------------------
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">🏆 Certifications</div>', unsafe_allow_html=True)
        if certifications:
            st.write(f"**{len(certifications)} certification(s) detected:**")
            # Certifications are raw lines extracted from the uploaded PDF —
            # untrusted user content — so they MUST be HTML-escaped before
            # being inserted into markup, otherwise a crafted resume could
            # inject a script/HTML payload (stored XSS).
            pills = "".join([f"<span class='pill pill-blue'>{html.escape(c)}</span>" for c in certifications])
            st.markdown(pills, unsafe_allow_html=True)
        else:
            st.info("No certifications detected. Relevant certifications can strengthen some resumes, but they aren't required.")
        st.markdown('</div>', unsafe_allow_html=True)

        # ---------------------------
        # JOB MATCH ANALYSIS
        # ---------------------------
        if keyword_score is not None:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">🎯 Job Match Analysis</div>', unsafe_allow_html=True)
            st.markdown(f"<h2 style='color:{score_color(keyword_score)}; margin-top:0;'>{keyword_score}% Match</h2>", unsafe_allow_html=True)
            st.progress(keyword_score / 100)
            st.caption(match_explanation(keyword_score))
            jcol1, jcol2 = st.columns(2)
            with jcol1:
                st.write(f"**Matched Keywords ({len(matched_kw)})**")
                if matched_kw:
                    st.markdown("".join([f"<span class='pill pill-good'>{html.escape(k)}</span>" for k in matched_kw[:25]]), unsafe_allow_html=True)
            with jcol2:
                st.write(f"**Missing Keywords ({len(missing_kw)})**")
                if missing_kw:
                    st.markdown("".join([f"<span class='pill pill-warn'>{html.escape(k)}</span>" for k in missing_kw[:25]]), unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # ---------------------------
        # WRITING QUALITY
        # ---------------------------
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">✍️ Writing Quality</div>', unsafe_allow_html=True)
        wcol1, wcol2 = st.columns(2)
        with wcol1:
            st.write(f"**Action verbs detected ({len(used_verbs)})**")
            if used_verbs:
                st.markdown("".join([f"<span class='pill pill-good'>{v}</span>" for v in sorted(used_verbs)]), unsafe_allow_html=True)
            else:
                st.info("None detected — start bullet points with strong verbs like *built, led, improved*.")
        with wcol2:
            st.write("**Quantifiable results**")
            if has_numbers:
                st.markdown("<span class='pill pill-good'>✅ Found in resume</span>", unsafe_allow_html=True)
            else:
                st.markdown("<span class='pill pill-bad'>❌ Not found</span>", unsafe_allow_html=True)
        if weak_phrases:
            st.write(f"**Weak phrases detected ({len(weak_phrases)})**")
            st.markdown("".join([f"<span class='pill pill-bad'>{p}</span>" for p in weak_phrases]), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # ---------------------------
        # SMART RECOMMENDATIONS
        # ---------------------------
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">💡 Smart Recommendations</div>', unsafe_allow_html=True)
        st.caption("Rule-based suggestions generated from your resume analysis.")
        if recommendations:
            for r in recommendations:
                p = r["priority"]
                cls = "rec-high" if p == "High" else ("rec-medium" if p == "Medium" else "rec-suggestion")
                tagcls = "rec-tag-high" if p == "High" else ("rec-tag-medium" if p == "Medium" else "rec-tag-suggestion")
                icon = "🔴" if p == "High" else ("🟡" if p == "Medium" else "🔵")
                st.markdown(f"""
                <div class="rec-card {cls}">
                    <span class="rec-tag {tagcls}">{icon} {p} Priority</span>
                    {r['text']}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("Your resume looks strong across all checks!")
        st.markdown('</div>', unsafe_allow_html=True)

        # ---------------------------
        # RESUME IMPROVEMENT (BEFORE/AFTER)
        # ---------------------------
        if before_after:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">✨ Resume Improvement Examples</div>', unsafe_allow_html=True)
            st.caption("Generic rewrite templates based on weak phrases found in your resume. Fill in the brackets with your real numbers/details.")
            for before, after in before_after:
                st.markdown(f"<div class='ba-box ba-before'><b>Before:</b> {before}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='ba-box ba-after'><b>Suggested:</b> {after}</div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # ---------------------------
        # CAREER MATCHES
        # ---------------------------
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">🚀 Best Career Matches</div>', unsafe_allow_html=True)
        if career_matches:
            medals = ["🥇", "🥈", "🥉"]
            for i, match in enumerate(career_matches):
                medal = medals[i] if i < len(medals) else "•"
                st.markdown(f"""
                <div class="career-card">
                    <div style="font-size:17px; font-weight:700; margin-bottom:8px;">{medal} {match['category']} — {match['score']}% match</div>
                </div>
                """, unsafe_allow_html=True)
                st.write("**Matching skills:**")
                st.markdown("".join([f"<span class='pill pill-blue'>{k}</span>" for k in match["matched_keywords"]]), unsafe_allow_html=True)
                st.write("**Suggested job titles:**")
                st.markdown("".join([f"<span class='pill pill-good'>{t}</span>" for t in match["job_titles"]]), unsafe_allow_html=True)
                st.write("**Recommended platforms:**")
                primary_title = match["job_titles"][0]
                for platform_name, note in match["platforms"]:
                    url = build_search_url(platform_name, primary_title)
                    link = f' — <a class="nav-loading-link" href="{url}" target="_blank" rel="noopener noreferrer" style="color:{LIGHT_BLUE}; font-weight:700;">🔗 Search on {platform_name}</a>' if url else ""
                    st.markdown(f"<div class='ba-box' style='background:{CARD_BG_2}; border:1px solid {BORDER};'>🌐 <b>{platform_name}</b> — {note}{link}</div>", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.info("No confident career match could be established from the readable evidence in this CV. The analyzer still checked explicit skills, AI-inferred skills, projects, experience, and role semantics. Try a text-based/OCR PDF if important content was not extracted.")
        st.markdown('</div>', unsafe_allow_html=True)

        # ---------------------------
        # LIVE REMOTE JOBS
        # ---------------------------
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">🌍 Live Remote Opportunities</div>', unsafe_allow_html=True)
        st.caption("Real, currently-open remote jobs matched to your top skill category (via RemoteOK).")
        with st.spinner("Fetching live listings..."):
            all_jobs = fetch_remoteok_jobs()

        if not all_jobs:
            st.info("Live listings are temporarily unavailable. Check your internet connection or try again shortly.")
        elif career_matches:
            live_jobs = []
            # First use role-specific evidence from the top career matches.
            for match in career_matches[:3]:
                live_jobs = filter_jobs_by_keywords(all_jobs, match["matched_keywords"], limit=6, min_matches=1)
                if live_jobs:
                    break
            # Then use the user's actual detected/inferred skills. This is
            # important because RemoteOK may not use the same role label as us.
            if not live_jobs:
                job_skill_terms = list(dict.fromkeys(skill_analysis["skills"] + [x["skill"] for x in ai_inferred_skills]))
                live_jobs = filter_jobs_by_keywords(all_jobs, job_skill_terms, limit=6, min_matches=1)

            if not live_jobs:
                st.info("No relevant live jobs found right now. The career match above is still based on your resume; RemoteOK may simply have no matching live listing at this moment.")
            else:
                for job in live_jobs:
                    # This data comes from a third-party API (RemoteOK) —
                    # untrusted external content. Every field must be
                    # HTML-escaped before insertion, and the URL must be
                    # scheme-validated, or a malicious/compromised listing
                    # could inject a script into every visitor's browser.
                    position = html.escape(job.get("position", "Untitled Role"))
                    company = html.escape(job.get("company", "Unknown Company"))
                    location = html.escape(job.get("location", "Remote"))
                    raw_url = job.get("url", "#")
                    url = raw_url if isinstance(raw_url, str) and raw_url.startswith(("http://", "https://")) else "#"
                    tags = job.get("tags", []) or []
                    tag_pills = "".join([f"<span class='pill pill-neutral'>{html.escape(str(t))}</span>" for t in tags[:6]])
                    st.markdown(f"""
                    <div class="job-card">
                        <div class="job-title">{position}</div>
                        <div class="job-company">{company} • {location}</div>
                        {tag_pills}<br>
                        <a class="job-apply nav-loading-link" href="{url}" target="_blank" rel="noopener noreferrer">View & Apply →</a>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            # Even if the role classifier has no result, don't tell the user
            # that live jobs are impossible. Try the detected skill profile.
            fallback_skill_terms = list(dict.fromkeys(skill_analysis["skills"] + [x["skill"] for x in ai_inferred_skills]))
            live_jobs = filter_jobs_by_keywords(all_jobs, fallback_skill_terms, limit=6, min_matches=1) if fallback_skill_terms else []
            if live_jobs:
                for job in live_jobs:
                    position = html.escape(job.get("position", "Untitled Role"))
                    company = html.escape(job.get("company", "Unknown Company"))
                    location = html.escape(job.get("location", "Remote"))
                    raw_url = job.get("url", "#")
                    url = raw_url if isinstance(raw_url, str) and raw_url.startswith(("http://", "https://")) else "#"
                    tags = job.get("tags", []) or []
                    tag_pills = "".join([f"<span class='pill pill-neutral'>{html.escape(str(t))}</span>" for t in tags[:6]])
                    st.markdown(f"""<div class='job-card'><div class='job-title'>{position}</div><div class='job-company'>{company} • {location}</div>{tag_pills}<br><a class='job-apply nav-loading-link' href='{url}' target='_blank' rel='noopener noreferrer'>View & Apply →</a></div>""", unsafe_allow_html=True)
            else:
                st.info("No live listing matched the detected skills right now. Try again later; live availability changes continuously.")
        st.markdown('</div>', unsafe_allow_html=True)

        # ---------------------------
        # DOWNLOAD REPORT
        # ---------------------------
        report_text = generate_report_text(
            "resume", overall, quality, keyword_score, word_count, sections_found,
            used_verbs, weak_phrases, has_numbers, matched_kw, missing_kw,
            certifications, recommendations, career_matches
        )
        st.download_button(
            "📥 Download Analysis Report",
            data=report_text,
            file_name="resume_analysis_report.txt",
            mime="text/plain",
        )

# ---------------------------
# FOOTER
# ---------------------------
st.markdown(f"""
<div class="footer-box">
    AI Resume Analyzer • Developed by <b>Aroon Kumar Maheshwari</b><br>
    Built with Python • Streamlit • Plotly • PyPDF2
</div>
""", unsafe_allow_html=True)