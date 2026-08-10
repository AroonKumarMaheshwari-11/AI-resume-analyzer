# AI Resume Analyzer — AI Upgrade

This version uses a hybrid local AI architecture:

- **Multi-parser PDF extraction:** PyMuPDF + pypdf, selecting the richest extraction for column/sidebar CVs.
- **Contact extraction:** scans the complete document for email, phone, LinkedIn and GitHub rather than requiring a Contact heading.
- **Explicit skill detection:** skill aliases and multi-word/technical names.
- **Local semantic AI:** `sentence-transformers` with `all-MiniLM-L6-v2` runs locally and free after the first model download.
- **AI-inferred skills:** can infer a skill from project/experience wording even when the exact skill phrase is absent.
- **AI career matching:** combines semantic similarity with explicit resume evidence. Missing certifications do not block a job/career recommendation.
- **No paid API key:** no OpenAI/Anthropic/Gemini API is required.

## Run

```powershell
pip install -r requirements.txt
streamlit run app.py
```

The first AI analysis downloads the small MiniLM embedding model. After that it is cached locally. Internet is only needed once for the model download; inference is local.

## Important limitation

A scanned/image-only PDF contains no machine-readable text. This version detects that condition instead of pretending it analyzed the CV. OCR can be added separately if needed.
