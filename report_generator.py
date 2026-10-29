
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


def generate_comparison_pdf(document_a, document_b, results):
    """
    Generate a PDF comparison report.

    document_a and document_b:
        Dictionaries containing filename and text.

    results:
        Dictionary returned by compare_documents().

    Returns:
        PDF file as bytes.
    """

    required_fields = [
        "summary_a",
        "summary_b",
        "similarities",
        "differences",
        "key_details",
        "overall_conclusion",
        "limitations",
    ]

    if not isinstance(results, dict):
        raise ValueError("Comparison results must be a dictionary.")

    for field in required_fields:
        if field not in results:
            raise ValueError(
                f"Comparison results are missing: {field}"
            )

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        title="AI Document Comparison Report",
        author="AI Document Comparison Assistant",
    )

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontSize=20,
            leading=25,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#183153"),
            spaceAfter=18,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading1"],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#183153"),
            spaceBefore=12,
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SubHeading",
            parent=styles["Heading2"],
            fontSize=11,
            leading=14,
            spaceBefore=8,
            spaceAfter=4,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ReportBody",
            parent=styles["BodyText"],
            fontSize=9,
            leading=13,
            spaceAfter=6,
            wordWrap="CJK",
        )
    )

    styles.add(
        ParagraphStyle(
            name="SmallCell",
            parent=styles["BodyText"],
            fontSize=7.5,
            leading=10,
            wordWrap="CJK",
        )
    )

    story = []

    def add_paragraph(text, style="ReportBody"):
        """Add safely escaped text to the PDF."""
        if text is None:
            text = ""

        if not isinstance(text, str):
            text = str(text)

        # Escape text so document content cannot break PDF markup.
        safe_text = escape(text).replace("\n", "<br/>")
        story.append(Paragraph(safe_text, styles[style]))

    def add_section(title):
        story.append(
            Paragraph(
                escape(title),
                styles["SectionHeading"],
            )
        )

    def add_evidence(label, value):
        add_paragraph(f"{label}: {value}")

    def add_empty_message(message):
        add_paragraph(message)

    # --------------------------------------------------
    # Report title
    # --------------------------------------------------

    story.append(
        Paragraph(
            "AI Document Comparison Report",
            styles["ReportTitle"],
        )
    )

    add_paragraph(
        "This report compares two PDF documents using their "
        "extracted text. Findings should be checked against "
        "the original documents when accuracy is important."
    )

    # --------------------------------------------------
    # Document A
    # --------------------------------------------------

    add_section("1. Document A")

    add_paragraph(
        f"File name: {document_a.get('filename', 'Document A')}"
    )

    add_paragraph("Summary", "SubHeading")
    add_paragraph(results["summary_a"])

    # --------------------------------------------------
    # Document B
    # --------------------------------------------------

    add_section("2. Document B")

    add_paragraph(
        f"File name: {document_b.get('filename', 'Document B')}"
    )

    add_paragraph("Summary", "SubHeading")
    add_paragraph(results["summary_b"])

    # --------------------------------------------------
    # Similarities
    # --------------------------------------------------

    add_section("3. Similarities")

    similarities = results["similarities"]

    if similarities:
        for index, item in enumerate(similarities, start=1):
            story.append(
                Paragraph(
                    f"Similarity {index}",
                    styles["SubHeading"],
                )
            )

            add_paragraph(item["finding"])
            add_evidence("Evidence from Document A", item["evidence_a"])
            add_evidence("Evidence from Document B", item["evidence_b"])
    else:
        add_empty_message(
            "No supported similarities were identified."
        )

    # --------------------------------------------------
    # Differences
    # --------------------------------------------------

    add_section("4. Differences")

    differences = results["differences"]

    if differences:
        for index, item in enumerate(differences, start=1):
            story.append(
                Paragraph(
                    f"Difference {index}: {item['topic']}",
                    styles["SubHeading"],
                )
            )

            add_paragraph(
                f"Document A: {item['document_a']}"
            )
            add_paragraph(
                f"Document B: {item['document_b']}"
            )
            add_evidence(
                "Evidence from Document A",
                item["evidence_a"],
            )
            add_evidence(
                "Evidence from Document B",
                item["evidence_b"],
            )
    else:
        add_empty_message(
            "No supported differences were identified."
        )

    # --------------------------------------------------
    # Key Details Comparison
    # --------------------------------------------------

    add_section("5. Key Details Comparison")

    key_details = results["key_details"]

    if key_details:
        table_data = [
            [
                Paragraph("<b>Category</b>", styles["SmallCell"]),
                Paragraph("<b>Document A</b>", styles["SmallCell"]),
                Paragraph("<b>Document B</b>", styles["SmallCell"]),
                Paragraph("<b>Evidence A</b>", styles["SmallCell"]),
                Paragraph("<b>Evidence B</b>", styles["SmallCell"]),
            ]
        ]

        for item in key_details:
            table_data.append(
                [
                    Paragraph(
                        escape(str(item["category"])),
                        styles["SmallCell"],
                    ),
                    Paragraph(
                        escape(str(item["detail_a"])),
                        styles["SmallCell"],
                    ),
                    Paragraph(
                        escape(str(item["detail_b"])),
                        styles["SmallCell"],
                    ),
                    Paragraph(
                        escape(str(item["evidence_a"])),
                        styles["SmallCell"],
                    ),
                    Paragraph(
                        escape(str(item["evidence_b"])),
                        styles["SmallCell"],
                    ),
                ]
            )

        table = Table(
            table_data,
            colWidths=[
                2.2 * cm,
                3.0 * cm,
                3.0 * cm,
                3.2 * cm,
                3.2 * cm,
            ],
            repeatRows=1,
            hAlign="LEFT",
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#DCE6F1"),
                    ),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )

        story.append(table)
    else:
        add_empty_message(
            "No key details were identified for comparison."
        )

    # --------------------------------------------------
    # Overall Conclusion
    # --------------------------------------------------

    add_section("6. Overall Conclusion")
    add_paragraph(results["overall_conclusion"])

    # --------------------------------------------------
    # Limitations
    # --------------------------------------------------

    add_section("7. Limitations")

    limitations = results["limitations"]

    if limitations:
        for limitation in limitations:
            add_paragraph(f"- {limitation}")
    else:
        add_empty_message(
            "No limitations were reported by the AI. "
            "Check the extraction warnings and original PDFs "
            "before relying on this report."
        )

    # --------------------------------------------------
    # Footer with page numbers
    # --------------------------------------------------

    def add_page_number(canvas, document):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)
        canvas.drawCentredString(
            A4[0] / 2,
            1.0 * cm,
            f"Page {document.page}",
        )
        canvas.restoreState()

    doc.build(
        story,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number,
    )

    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes
