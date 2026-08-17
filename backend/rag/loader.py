# Step 1 of RAG: read a PDF / TXT / DOCX file and pull out its plain text.

import io

import docx
from pypdf import PdfReader

SUPPORTED_EXTENSIONS = [".pdf", ".txt", ".docx"]


def extract_text(filename: str, file_bytes: bytes) -> str:
    """Pick the right reader based on the file extension and return the text."""
    lower_name = filename.lower()

    if lower_name.endswith(".pdf"):
        return _read_pdf(file_bytes)
    if lower_name.endswith(".docx"):
        return _read_docx(file_bytes)
    if lower_name.endswith(".txt"):
        return file_bytes.decode("utf-8", errors="ignore")

    raise ValueError("Only PDF, TXT and DOCX files are supported")


def _read_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def _read_docx(file_bytes: bytes) -> str:
    document = docx.Document(io.BytesIO(file_bytes))
    paragraphs = [paragraph.text for paragraph in document.paragraphs]
    return "\n".join(paragraphs)
