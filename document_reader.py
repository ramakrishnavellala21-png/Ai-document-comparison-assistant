
from io import BytesIO
from pypdf import PdfReader


MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_PAGES = 200


class DocumentError(Exception):
    """Raised when a document cannot be processed."""


def extract_document(file_bytes, filename):
    """
    Validate a PDF and extract page-level text.

    Returns a dictionary containing metadata, page text,
    and any pages that produced no readable text.
    """

    if not filename or not filename.lower().endswith(".pdf"):
        raise DocumentError("Please upload a PDF file.")

    if not file_bytes:
        raise DocumentError(
            f"{filename} is empty. Please choose another file."
        )

    if len(file_bytes) > MAX_FILE_SIZE:
        raise DocumentError(
            f"{filename} exceeds the 10 MB upload limit."
        )

    if not file_bytes.startswith(b"%PDF-"):
        raise DocumentError(
            f"{filename} does not appear to be a valid PDF."
        )

    try:
        reader = PdfReader(BytesIO(file_bytes), strict=True)

        if reader.is_encrypted:
            raise DocumentError(
                f"{filename} is encrypted. "
                "Please upload an unencrypted PDF."
            )

        page_count = len(reader.pages)

        if page_count == 0:
            raise DocumentError(
                f"{filename} contains no pages."
            )

        if page_count > MAX_PAGES:
            raise DocumentError(
                f"{filename} exceeds the {MAX_PAGES}-page limit."
            )

        pages = []
        unreadable_pages = []

        for page_number, page in enumerate(
            reader.pages, start=1
        ):
            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""

            text = text.strip()

            if not text:
                unreadable_pages.append(page_number)

            pages.append({
                "page": page_number,
                "text": text,
            })

    except DocumentError:
        raise
    except Exception as exc:
        raise DocumentError(
            f"{filename} could not be read as a PDF. "
            "The file may be damaged or malformed."
        ) from exc

    full_text = "\n\n".join(
        f"[Page {page['page']}]\n{page['text']}"
        for page in pages
        if page["text"]
    )

    if not full_text.strip():
        raise DocumentError(
            f"No readable text was extracted from {filename}. "
            "It may be a scanned PDF. OCR may be required."
        )

    return {
        "filename": filename,
        "page_count": page_count,
        "character_count": len(full_text),
        "pages": pages,
        "text": full_text,
        "unreadable_pages": unreadable_pages,
    }
