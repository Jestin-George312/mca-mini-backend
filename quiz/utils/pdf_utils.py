import pdfplumber

def extract_text_from_pdf(pdf_path):
    """
    Extract readable text from a PDF file using pdfplumber.
    Returns the combined text of all pages.
    """
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"[ERROR] Failed to extract PDF text: {e}")
    return text.strip()
