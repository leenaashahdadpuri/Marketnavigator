import streamlit as st
import fitz  # PyMuPDF
from pdf2image import convert_from_bytes
from PIL import Image
import io

st.set_page_config(
    page_title="Store Layout Upload",
    layout="wide"
)

st.title("🏬 Store Layout Upload")

st.markdown("""
Upload a store layout PDF.

The application will:
1. Read PDF metadata
2. Show page previews
3. Convert pages to images
4. Prepare data for rack detection
""")

uploaded_file = st.file_uploader(
    "Upload Store Layout PDF",
    type=["pdf"]
)

if uploaded_file:

    pdf_bytes = uploaded_file.read()

    st.success("PDF uploaded successfully")

    # ----------------------------------
    # Read PDF Metadata
    # ----------------------------------

    pdf_doc = fitz.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    st.subheader("PDF Information")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Pages",
            pdf_doc.page_count
        )

    metadata = pdf_doc.metadata

    with col2:
        st.metric(
            "Title",
            metadata.get("title", "N/A")
        )

    with col3:
        st.metric(
            "Author",
            metadata.get("author", "N/A")
        )

    # ----------------------------------
    # Convert Pages to Images
    # ----------------------------------

    st.subheader("Page Preview")

    pages = convert_from_bytes(pdf_bytes)

    for page_no, page in enumerate(pages):

        st.markdown(f"### Page {page_no + 1}")

        st.image(
            page,
            use_container_width=True
        )

        # Future AI processing
        image_bytes = io.BytesIO()

        page.save(
            image_bytes,
            format="PNG"
        )

        st.caption(
            "Ready for rack detection"
        )
