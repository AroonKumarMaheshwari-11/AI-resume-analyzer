# AI Resume Analyzer — Fixed Build

## What was fixed

1. **Streamlit secrets crash**
   - Missing `.streamlit/secrets.toml` no longer crashes the app.
   - Admin authentication falls back safely to `ADMIN_PASSWORD` environment variable.

2. **Resume PDF extraction**
   - Uses layout-aware extraction first and retries with normal pypdf extraction when the first pass returns too little text.
   - Normalizes PDF whitespace and broken hyphenated lines.
   - Rewinds uploaded files before retrying.

3. **Skills analysis**
   - Added a dedicated **Skills Analysis** section.
   - Detects common technical and professional skills, including Python, Java, JavaScript, SQL, React, Node.js, Docker, Power BI, etc.
   - Handles common aliases such as NodeJS/Node.js, JS/JavaScript, PowerBI/Power BI and similar forms.
   - Career matching now uses the same alias-aware skill matching.

4. **PDF extraction diagnostics**
   - Added an expandable **PDF extraction check** so you can immediately see whether the skills are actually being extracted from the PDF.

## Run

Open PowerShell in this folder:

```powershell
cd "C:\Users\PMYLS\Desktop\AI-resume-analyzer-fixed"
python -m pip install -r requirements.txt
streamlit run app.py
```

Do **not** launch a Streamlit app with `python app.py`.

The browser should open at:

`http://localhost:8501`

## Admin password (optional)

The admin panel stays disabled unless you configure a password.

Option A — create `.streamlit\secrets.toml`:

```toml
ADMIN_PASSWORD = "your-strong-password"
```

Option B — PowerShell environment variable for the current terminal:

```powershell
$env:ADMIN_PASSWORD="your-strong-password"
streamlit run app.py
```

## If a skill is still not detected

After analysis, open:

**🔎 PDF extraction check**

If the skill is visible there, the parser read it and it can be added to the skill vocabulary if it is a specialized term.

If the skill is NOT visible there, the PDF is probably image/scanned based or the text is stored in a non-standard way. Re-export the CV as a text/selectable PDF.

