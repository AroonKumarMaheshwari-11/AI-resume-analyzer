"""
Run this once from inside your project folder:
    python fix_bytesio_bug.py

Fixes the real bug: BytesIO was only imported locally inside
extract_text_from_pdf, so extract_text_from_docx crashed with
NameError: name 'BytesIO' is not defined.

Also removes the temporary debug logging we added earlier, since we
found the real problem and don't need it anymore.

Safe to re-run.
"""
import sys

APP_FILE = "app.py"

with open(APP_FILE, "r", encoding="utf-8") as f:
    content = f.read()

changed = False

# Split off everything before the first function definition -- that's the
# "module level" region where top-of-file imports live.
header, _, rest = content.partition("\ndef ")

# 1. Remove the redundant/buggy local import inside extract_text_from_pdf
#    (this is what caused DocxDocument's use of BytesIO to be undefined).
local_import_block = "        try:\n            from io import BytesIO\n            reader = PdfReader(BytesIO(raw))"
local_import_replacement = "        try:\n            reader = PdfReader(BytesIO(raw))"
if local_import_block in content:
    content = content.replace(local_import_block, local_import_replacement, 1)
    header, _, rest = content.partition("\ndef ")
    changed = True
    print("Removed local (function-scoped) BytesIO import inside extract_text_from_pdf.")

# 2. Ensure a module-level BytesIO import exists in the header region only.
if "from io import BytesIO" not in header:
    old_import = "from pypdf import PdfReader"
    if old_import not in content:
        print("ERROR: could not find the PdfReader import line. No changes made.")
        sys.exit(1)
    content = content.replace(old_import, old_import + "\nfrom io import BytesIO", 1)
    changed = True
    print("Added module-level 'from io import BytesIO' import.")
else:
    print("Module-level BytesIO import already present.")

# 3. Remove the temporary debug logging added earlier.
debug_old = '''    except Exception as exc:
        import traceback
        print("[DOCX DEBUG]", repr(exc))
        traceback.print_exc()
        raise ValueError(
            "Couldn't read this Word file. It may be corrupted, or in an "
            "unsupported format (only .docx is supported, not the older .doc)."
        ) from exc'''

debug_new = '''    except Exception as exc:
        raise ValueError(
            "Couldn't read this Word file. It may be corrupted, or in an "
            "unsupported format (only .docx is supported, not the older .doc)."
        ) from exc'''

if debug_old in content:
    content = content.replace(debug_old, debug_new, 1)
    changed = True
    print("Removed temporary debug logging.")
else:
    print("Debug logging block not found (already removed or never applied) -- skipping.")

if not changed:
    print("Nothing to change -- file already looks correct.")
    sys.exit(0)

with open(APP_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print("Done. Word (.docx) upload should now work correctly.")
