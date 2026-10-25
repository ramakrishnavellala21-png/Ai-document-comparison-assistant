
import unittest
from io import BytesIO

from reportlab.pdfgen import canvas

from document_reader import (
    DocumentError,
    extract_document,
)


def make_pdf(text):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(72, 750, text)
    pdf.save()
    return buffer.getvalue()


class TestDocumentReader(unittest.TestCase):

    def test_valid_pdf(self):
        data = make_pdf("Payment period: 30 days")

        result = extract_document(data, "contract.pdf")

        self.assertEqual(result["page_count"], 1)
        self.assertIn("30 days", result["text"])
        self.assertEqual(result["filename"], "contract.pdf")

    def test_empty_file(self):
        with self.assertRaises(DocumentError):
            extract_document(b"", "empty.pdf")

    def test_wrong_file_type(self):
        with self.assertRaises(DocumentError):
            extract_document(b"hello", "notes.txt")

    def test_pdf_with_no_readable_text(self):
        # This begins with a PDF header but is not a valid PDF.
        with self.assertRaises(DocumentError):
            extract_document(b"%PDF-invalid", "broken.pdf")


if __name__ == "__main__":
    unittest.main()
