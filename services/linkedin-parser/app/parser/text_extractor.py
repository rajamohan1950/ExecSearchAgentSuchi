import io
import logging

import pdfplumber
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


def extract_with_pdfplumber(pdf_bytes: bytes) -> str | None:
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            if pages:
                return "\n".join(pages)
    except Exception as e:
        logger.warning(f"pdfplumber extraction failed: {e}")
    return None


def extract_with_pymupdf(pdf_bytes: bytes) -> str | None:
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages = []
        for page in doc:
            text = page.get_text()
            if text.strip():
                pages.append(text)
        doc.close()
        if pages:
            return "\n".join(pages)
    except Exception as e:
        logger.warning(f"PyMuPDF extraction failed: {e}")
    return None


def extract_text(pdf_bytes: bytes) -> str:
    text = extract_with_pdfplumber(pdf_bytes)
    if text and len(text.strip()) > 50:
        return text

    text = extract_with_pymupdf(pdf_bytes)
    if text and len(text.strip()) > 50:
        return text

    raise ValueError("Could not extract meaningful text from PDF")
