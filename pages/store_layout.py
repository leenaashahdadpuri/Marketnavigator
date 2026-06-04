import streamlit as st
import fitz
import cv2
import numpy as np
import pandas as pd
import plotly.express as px

from PIL import Image
from io import BytesIO

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="Store Layout Generator",
    layout="wide"
)

st.title("🏬 Store Layout Generator")

st.markdown("""
Upload a store layout PDF.

Current Features:
- PDF Upload
- PDF Preview
- Metadata Extraction
- Rack Detection
- Coordinate Generation
- Layout Visualization

Future Features:
- PostgreSQL Storage
- Navigation Graph Generation
- Route Optimization
- AR Anchor Generation
""")

# ---------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------

def pdf_page_to_image(page):

    pix = page.get_pixmap(
        matrix=fitz.Matrix(2, 2)
    )

    image = Image.frombytes(
        "RGB",
        [pix.width, pix.height],
        pix.samples
    )

    return image


def detect_racks(pil_image):

    image = np.array(pil_image)

    original = image.copy()

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_RGB2GRAY
    )

    blur = cv2.GaussianBlur(
        gray,
        (5, 5),
        0
    )

    _, thresh = cv2.threshold(
        blur,
        180,
        255,
        cv2.THRESH_BINARY_INV
    )

    contours, _ = cv2.findContours(
        thresh,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    racks = []

    rack_number = 1

    for contour in contours:

        x, y, w, h = cv2.boundingRect(
            contour
        )

        area = w * h

        # Ignore tiny objects
        if area < 3000:
            continue

        aspect_ratio = w / h

        # Filter obvious noise
        if w < 30 or h < 30:
            continue

        rack_code = f"RACK-{rack_number:03}"

        racks.append(
            {
                "rack_code": rack_code,
                "x": x,
                "y": y,
                "width": w,
                "height": h,
                "area": area,
                "aspect_ratio": round(
                    aspect_ratio,
                    2
                )
            }
        )

        cv2.rectangle(
            original,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            3
        )

        cv2.putText(
            original,
            rack_code,
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 0, 0),
            2
        )

        rack_number += 1

    return original, racks


# ---------------------------------------------------
# PDF UPLOAD
# ---------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload Store Layout PDF",
    type=["pdf"]
)

# ---------------------------------------------------
# PROCESS PDF
# ---------------------------------------------------

if uploaded_file:

    try:

        pdf_bytes = uploaded_file.read()

        pdf = fitz.open(
            stream=pdf_bytes,
            filetype="pdf"
        )

        st.success(
            "PDF uploaded successfully"
        )

        # -----------------------------------------
        # PDF INFO
        # -----------------------------------------

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

        # -----------------------------------------
        # PAGE PROCESSING
        # -----------------------------------------

        st.subheader("🖼 Layout Pages")

        all_racks = []

        for page_number in range(
            pdf.page_count
        ):

            page = pdf[
                page_number
            ]

            image = pdf_page_to_image(
                page
            )

            with st.expander(
                f"Page {page_number + 1}"
            ):

                st.image(
                    image,
                    caption="Original Layout",
                    use_container_width=True
                )

                detect_button = st.button(
                    f"Detect Racks Page {page_number + 1}"
                )

                if detect_button:

                    processed_image, racks = (
                        detect_racks(image)
                    )

                    st.subheader(
                        "Detected Rack Layout"
                    )

                    st.image(
                        processed_image,
                        use_container_width=True
                    )

                    if len(racks):

                        rack_df = pd.DataFrame(
                            racks
                        )

                        all_racks.extend(
                            racks
                        )

                        st.success(
                            f"{len(racks)} racks detected"
                        )

                        st.dataframe(
                            rack_df,
                            use_container_width=True
                        )

                        # -------------------------
                        # Layout Visualization
                        # -------------------------

                        st.subheader(
                            "Layout Map"
                        )

                        fig = px.scatter(
                            rack_df,
                            x="x",
                            y="y",
                            text="rack_code",
                            size="area",
                            title="Detected Rack Coordinates"
                        )

                        fig.update_traces(
                            textposition="top center"
                        )

                        fig.update_yaxes(
                            autorange="reversed"
                        )

                        st.plotly_chart(
                            fig,
                            use_container_width=True
                        )

                        # -------------------------
                        # Export CSV
                        # -------------------------

                        csv = (
                            rack_df
                            .to_csv(
                                index=False
                            )
                            .encode("utf-8")
                        )

                        st.download_button(
                            label="⬇ Download Rack Coordinates",
                            data=csv,
                            file_name="detected_racks.csv",
                            mime="text/csv"
                        )

                    else:

                        st.warning(
                            "No racks detected."
                        )

        # -----------------------------------------
        # FUTURE ROADMAP
        # -----------------------------------------

        st.divider()

        st.subheader(
            "🚀 Next Phase"
        )

        st.info(
            """
            Next implementation steps:

            1. Save racks into PostgreSQL
            2. Create aisles automatically
            3. Build navigation graph
            4. Generate shortest paths
            5. Create AR anchor locations
            6. Build FastAPI validation services
            """
        )

    except Exception as ex:

        st.error(
            f"Error processing PDF: {str(ex)}"
        )
