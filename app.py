
from io import BytesIO

import streamlit as st
from pypdf import PdfReader

from comparison import compare_documents, ComparisonError
from report_generator import generate_comparison_pdf


# --------------------------------------------------
# Streamlit page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="AI Document Comparison Assistant",
    page_icon="📄",
    layout="wide",
)

st.title("AI Document Comparison Assistant")

st.write(
    "Upload two text-based PDF documents to compare their "
    "summaries, similarities, differences, and important details."
)


# --------------------------------------------------
# Session state
# --------------------------------------------------

if "upload_version" not in st.session_state:
    st.session_state.upload_version = 0

if "comparison_bundle" not in st.session_state:
    st.session_state.comparison_bundle = None


def reset_application():
    """Clear results and create fresh upload widgets."""
    st.session_state.comparison_bundle = None
    st.session_state.upload_version += 1


# --------------------------------------------------
# PDF extraction and validation
# --------------------------------------------------

def extract_pdf(uploaded_file):
    """
    Validate an uploaded PDF and extract text page by page.

    Returns:
        {
            "filename": str,
            "text": str,
            "limitations": list
        }
    """

    if uploaded_file is None:
        raise ValueError("Please upload both PDF documents.")

    pdf_bytes = uploaded_file.getvalue()

    if not pdf_bytes:
        raise ValueError(
            f"{uploaded_file.name} is empty."
        )

    if not pdf_bytes.startswith(b"%PDF-"):
        raise ValueError(
            f"{uploaded_file.name} is not a valid PDF file."
        )

    try:
        reader = PdfReader(BytesIO(pdf_bytes), strict=False)

        if reader.is_encrypted:
            raise ValueError(
                f"{uploaded_file.name} is password-protected. "
                "Please upload an accessible PDF."
            )

        if len(reader.pages) == 0:
            raise ValueError(
                f"{uploaded_file.name} contains no pages."
            )

        extracted_pages = []
        limitations = []

        for page_number, page in enumerate(
            reader.pages, start=1
        ):
            try:
                page_text = page.extract_text() or ""

                if page_text.strip():
                    extracted_pages.append(
                        f"[Page {page_number}]\n{page_text.strip()}"
                    )
                else:
                    limitations.append(
                        f"{uploaded_file.name}, page {page_number}: "
                        "No readable text was extracted. "
                        "The page may be scanned, image-only, or blank."
                    )

            except Exception:
                limitations.append(
                    f"{uploaded_file.name}, page {page_number}: "
                    "Text extraction failed."
                )

        document_text = "\n\n".join(extracted_pages).strip()

        if not document_text:
            raise ValueError(
                f"No readable text could be extracted from "
                f"{uploaded_file.name}. If it is a scanned PDF, "
                "OCR support is required."
            )

        return {
            "filename": uploaded_file.name,
            "text": document_text,
            "limitations": limitations,
        }

    except ValueError:
        raise

    except Exception as exc:
        raise ValueError(
            f"Could not read {uploaded_file.name}. "
            "Please check that the PDF is valid and accessible."
        ) from exc


# --------------------------------------------------
# Upload interface
# --------------------------------------------------

st.subheader("Upload your documents")

upload_key = st.session_state.upload_version

col_a, col_b = st.columns(2)

with col_a:
    file_a = st.file_uploader(
        "Document A (PDF)",
        type=["pdf"],
        key=f"document_a_{upload_key}",
        help="Upload the first PDF document.",
    )

with col_b:
    file_b = st.file_uploader(
        "Document B (PDF)",
        type=["pdf"],
        key=f"document_b_{upload_key}",
        help="Upload the second PDF document.",
    )


# Display uploaded filenames

if file_a is not None:
    st.success(f"Document A: {file_a.name}")

if file_b is not None:
    st.success(f"Document B: {file_b.name}")


# --------------------------------------------------
# Compare and reset buttons
# --------------------------------------------------

col_compare, col_reset = st.columns(2)

with col_compare:
    compare_clicked = st.button(
        "Compare Documents",
        type="primary",
        use_container_width=True,
    )

with col_reset:
    st.button(
        "Reset / Compare Again",
        on_click=reset_application,
        use_container_width=True,
    )


# --------------------------------------------------
# Process documents
# --------------------------------------------------

if compare_clicked:

    if file_a is None or file_b is None:
        st.error(
            "Please upload both Document A and Document B."
        )

    else:
        try:
            with st.spinner(
                "Reading PDFs and comparing documents. "
                "This may take a few minutes..."
            ):
                document_a = extract_pdf(file_a)
                document_b = extract_pdf(file_b)

                # Display useful document information
                st.session_state.comparison_bundle = None

                results = compare_documents(
                    document_a,
                    document_b,
                )

                # Include PDF extraction warnings in the report.
                results = dict(results)

                ai_limitations = list(
                    results.get("limitations", [])
                )

                extraction_limitations = (
                    document_a["limitations"]
                    + document_b["limitations"]
                )

                results["limitations"] = (
                    extraction_limitations + ai_limitations
                )

                st.session_state.comparison_bundle = {
                    "document_a": document_a,
                    "document_b": document_b,
                    "results": results,
                }

            st.success("Comparison completed successfully.")

        except ComparisonError as exc:
            st.error(f"Comparison failed: {exc}")

        except ValueError as exc:
            st.error(str(exc))

        except Exception:
            st.error(
                "An unexpected error occurred. "
                "Please check your terminal logs and try again."
            )


# --------------------------------------------------
# Display saved comparison results
# --------------------------------------------------

bundle = st.session_state.comparison_bundle

if bundle is not None:

    document_a = bundle["document_a"]
    document_b = bundle["document_b"]
    results = bundle["results"]

    st.divider()
    st.header("Comparison Results")

    # ----------------------------------------------
    # Document previews
    # ----------------------------------------------

    st.subheader("Document A")
    st.write(f"**File:** {document_a['filename']}")
    st.write(f"**Extracted characters:** {len(document_a['text']):,}")

    with st.expander("Preview extracted text from Document A"):
        st.text(document_a["text"][:2000])

    st.subheader("Document B")
    st.write(f"**File:** {document_b['filename']}")
    st.write(f"**Extracted characters:** {len(document_b['text']):,}")

    with st.expander("Preview extracted text from Document B"):
        st.text(document_b["text"][:2000])

    # ----------------------------------------------
    # Summary A and Summary B
    # ----------------------------------------------

    summary_a_tab, summary_b_tab, similarities_tab, \
        differences_tab, details_tab, conclusion_tab, \
        limitations_tab = st.tabs([
            "Document A Summary",
            "Document B Summary",
            "Similarities",
            "Differences",
            "Key Details Comparison",
            "Overall Conclusion",
            "Limitations",
        ])

    with summary_a_tab:
        st.subheader("Document A")
        st.caption(document_a["filename"])
        st.write(results["summary_a"])

    with summary_b_tab:
        st.subheader("Document B")
        st.caption(document_b["filename"])
        st.write(results["summary_b"])

    # ----------------------------------------------
    # Similarities
    # ----------------------------------------------

    with similarities_tab:
        st.subheader("Similarities")

        if results["similarities"]:
            for index, item in enumerate(
                results["similarities"], start=1
            ):
                st.markdown(
                    f"**{index}. {item['finding']}**"
                )
                st.write(
                    f"Evidence from Document A: "
                    f"{item['evidence_a']}"
                )
                st.write(
                    f"Evidence from Document B: "
                    f"{item['evidence_b']}"
                )
                st.divider()
        else:
            st.info("No supported similarities were identified.")

    # ----------------------------------------------
    # Differences
    # ----------------------------------------------

    with differences_tab:
        st.subheader("Differences")

        if results["differences"]:
            for index, item in enumerate(
                results["differences"], start=1
            ):
                st.markdown(
                    f"**{index}. {item['topic']}**"
                )

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Document A**")
                    st.write(item["document_a"])
                    st.caption(
                        f"Evidence: {item['evidence_a']}"
                    )

                with col2:
                    st.markdown("**Document B**")
                    st.write(item["document_b"])
                    st.caption(
                        f"Evidence: {item['evidence_b']}"
                    )

                st.divider()
        else:
            st.info("No supported differences were identified.")

    # ----------------------------------------------
    # Key Details Comparison
    # ----------------------------------------------

    with details_tab:
        st.subheader("Key Details Comparison")

        if results["key_details"]:
            import pandas as pd

            details_table = pd.DataFrame([
                {
                    "Category": item["category"],
                    "Document A": item["detail_a"],
                    "Document B": item["detail_b"],
                    "Evidence A": item["evidence_a"],
                    "Evidence B": item["evidence_b"],
                }
                for item in results["key_details"]
            ])

            st.dataframe(
                details_table,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No key details were identified.")

    # ----------------------------------------------
    # Overall Conclusion
    # ----------------------------------------------

    with conclusion_tab:
        st.subheader("Overall Conclusion")
        st.write(results["overall_conclusion"])

    # ----------------------------------------------
    # Limitations
    # ----------------------------------------------

    with limitations_tab:
        st.subheader("Limitations")

        if results["limitations"]:
            for limitation in results["limitations"]:
                st.warning(limitation)
        else:
            st.info(
                "No limitations were reported. "
                "Please still verify the results against the "
                "original documents."
            )

    # ----------------------------------------------
    # Generate and download PDF report
    # ----------------------------------------------

    st.divider()
    st.subheader("Download Comparison Report")

    try:
        pdf_report = generate_comparison_pdf(
            document_a,
            document_b,
            results,
        )

        st.download_button(
            label="Download Comparison Report (PDF)",
            data=pdf_report,
            file_name="document_comparison_report.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
        )

    except Exception as exc:
        st.error(
            "Could not generate the PDF report. "
            "Please check report_generator.py and the terminal logs."
        )
        print(
            f"PDF report generation error: "
            f"{type(exc).__name__}: {exc}"
        )
