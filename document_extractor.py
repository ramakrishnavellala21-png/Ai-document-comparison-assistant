
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader
from docx import Document


def extract_document(uploaded_file):
    """Extract text from a Streamlit PDF, DOCX, or TXT upload."""

    filename = uploaded_file.name
    extension = Path(filename).suffix.lower()
    file_bytes = uploaded_file.getvalue()

    if extension == ".pdf":
        reader = PdfReader(BytesIO(file_bytes))
        pages = []

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            pages.append(f"[Page {page_number}]\n{text}")

        extracted_text = "\n\n".join(pages)

    elif extension == ".docx":
        document = Document(BytesIO(file_bytes))
        paragraphs = [
            paragraph.text
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        ]
        extracted_text = "\n".join(paragraphs)

        # Also include text from Word tables.
        for table in document.tables:
            for row in table.rows:
                extracted_text += "\n" + " | ".join(
                    cell.text for cell in row.cells
                )

    elif extension == ".txt":
        extracted_text = file_bytes.decode("utf-8-sig")

    else:
        raise ValueError(
            f"Unsupported file type: {extension}"
        )

    if not extracted_text.strip():
        raise ValueError(
            f"No readable text was found in {filename}. "
            "If this is a scanned PDF, OCR support is needed."
        )

    return {
        "filename": filename,
        "text": extracted_text,
    }
