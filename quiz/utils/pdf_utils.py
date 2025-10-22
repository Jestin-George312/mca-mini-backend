# quiz/utils/pdf_utils.py

import pdfplumber
import io # ✅ Import io

# ✅ Change 'pdf_path' to 'pdf_bytes'
def extract_text_from_pdf(pdf_bytes):
    """
    Extract readable text from PDF bytes using pdfplumber.
    Returns the combined text of all pages.
    """
    text = ""
    try:
        # ✅ Use io.BytesIO() to read the bytes
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"[ERROR] Failed to extract PDF text: {e}")
    return text.strip()