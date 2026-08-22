"""
TEMPORARY diagnostic patch. Run once from your project folder:
    python add_docx_debug_logging.py

This makes the real underlying Word-file error print to the Streamlit Cloud
server logs (Manage app -> logs) instead of being hidden behind the generic
friendly message. After we find and fix the real bug, we'll remove this.
"""
import sys

APP_FILE = "app.py"

with open(APP_FILE, "r", encoding="utf-8") as f:
    content = f.read()

marker = "print('[DOCX DEBUG]'"
if marker in content:
    print("Debug logging already added -- nothing to do.")
    sys.exit(0)

old = '''    except Exception as exc:
        raise ValueError(
            "Couldn't read this Word file. It may be corrupted, or in an "
            "unsupported format (only .docx is supported, not the older .doc)."
        ) from exc'''

new = '''    except Exception as exc:
        import traceback
        print("[DOCX DEBUG]", repr(exc))
        traceback.print_exc()
        raise ValueError(
            "Couldn't read this Word file. It may be corrupted, or in an "
            "unsupported format (only .docx is supported, not the older .doc)."
        ) from exc'''

if old not in content:
    print("ERROR: could not find the docx except block. No changes made.")
    sys.exit(1)

content = content.replace(old, new, 1)

with open(APP_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print("Added temporary debug logging around the Word-file error.")
