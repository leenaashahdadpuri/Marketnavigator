 import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import pandas as pd

# --------------------------------------------------
# Page Configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Store Layout Upload",
    layout="wide"
)

st.title("🏬 Store Layout Generator")

st.markdown("""
Upload a store layout PDF.

This module will:

- Upload and validate PDF
- Extract PDF metadata
- Display PDF pages
- Convert pages into images
- Prepare layout images for rack detection
- Serve as the foundation for future AR mapping
""")

# --------------------------------------------------
# PDF Upload
# --------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload Store Layout PDF",
    type=["pdf"]
)

# --------------------------------------------------
# Process PDF
# --------------------------------------------------

if uploaded_file:

    try:

        pdf_bytes = uploaded_file.read()

        pdf = fitz.open(
            stream=pdf_bytes,
            filetype="pdf"
        )

        st.success("PDF uploaded successfully")

        # --------------------------------------------------
        # Metadata Section
        # --------------------------------------------------

        st.subheader("📄 PDF Information")

        metadata = pdf.metadata

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Pages",
                pdf.page_count
            )

        with col2:
            st.metric(
                "Title",
                metadata.get("title") or "N/A"
            )

        with col3:
            st.metric(
                "Author",
                metadata.get("author") or "N/A"
            )

        # --------------------------------------------------
        # Metadata Table
        # --------------------------------------------------

        with st.expander("View Full Metadata"):

            metadata_df = pd.DataFrame(
                metadata.items(),
                columns=["Property", "Value"]
            )

            st.dataframe(
                metadata_df,
                use_container_width=True
            )

        # --------------------------------------------------
        # Page Preview
        # --------------------------------------------------

        st.subheader("🖼 PDF Page Preview")

        for page_number in range(pdf.page_count):

            page = pdf[page_number]

            pix = page.get_pixmap(
                matrix=fitz.Matrix(2, 2)
            )

            img = Image.frombytes(
                "RGB",
                [pix.width, pix.height],
                pix.samples
            )

            with st.expander(
                f"Page {page_number + 1}"
            ):

                st.image(
                    img,
                    use_container_width=True
                )

                st.info(
                    "This image will be used in future steps for rack detection and AR coordinate generation."
                )

        # --------------------------------------------------
        # Future Processing Placeholder
        # --------------------------------------------------

        st.divider()

        st.subheader("🚀 Next Step")

        st.success(
            """
            PDF successfully processed.

            Next phase:
            - Detect racks using OpenCV
            - Extract rack coordinates
            - Generate navigation graph
            - Store coordinates in PostgreSQL
            - Create AR anchor points
            """
        )

    except Exception as ex:

        st.error(
            f"Error processing PDF: {str(ex)}"
        )
