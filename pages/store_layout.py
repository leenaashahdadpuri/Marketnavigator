import streamlit as st
import fitz
import cv2
import numpy as np
import pandas as pd
import plotly.express as px

from PIL import Image
from sqlalchemy import create_engine, text

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Store Layout Generator",
    layout="wide"
)

st.title("🏬 Store Layout Generator")

# =====================================================
# DATABASE CONNECTION
# =====================================================

try:

    DB_URL = (
        f"postgresql://"
        f"{st.secrets['DB_USER']}:"
        f"{st.secrets['DB_PASSWORD']}@"
        f"{st.secrets['DB_HOST']}:"
        f"{st.secrets['DB_PORT']}/"
        f"{st.secrets['DB_NAME']}"
    )

    engine = create_engine(DB_URL)

    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    st.success("✅ PostgreSQL Connected")

except Exception as ex:

    st.error(
        f"Database Connection Failed: {str(ex)}"
    )

    st.stop()

# =====================================================
# HELPER FUNCTIONS
# =====================================================

def create_tables():

    with engine.begin() as conn:

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS stores
        (
            id BIGSERIAL PRIMARY KEY,
            store_name VARCHAR(200)
        )
        """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS racks
        (
            id BIGSERIAL PRIMARY KEY,

            store_id BIGINT,

            rack_code VARCHAR(100) UNIQUE,

            x_coordinate INTEGER,
            y_coordinate INTEGER,

            width INTEGER,
            height INTEGER,

            area INTEGER,

            created_at TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP
        )
        """))


def pdf_page_to_image(page):

    pix = page.get_pixmap(
        matrix=fitz.Matrix(2, 2)
    )

    img = Image.frombytes(
        "RGB",
        [pix.width, pix.height],
        pix.samples
    )

    return img


def detect_racks(pil_image):

    image = np.array(pil_image)

    original = image.copy()

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_RGB2GRAY
    )

    _, thresh = cv2.threshold(
        gray,
        180,
        255,
        cv2.THRESH_BINARY_INV
    )

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (5, 5)
    )

    thresh = cv2.morphologyEx(
        thresh,
        cv2.MORPH_CLOSE,
        kernel,
        iterations=2
    )

    contours, _ = cv2.findContours(
        thresh,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    racks = []

    rack_number = 1

    img_height, img_width = image.shape[:2]

    min_area = (
        img_height * img_width
    ) * 0.001

    max_area = (
        img_height * img_width
    ) * 0.20

    for contour in contours:

        perimeter = cv2.arcLength(
            contour,
            True
        )

        approx = cv2.approxPolyDP(
            contour,
            0.02 * perimeter,
            True
        )

        if len(approx) != 4:
            continue

        x, y, w, h = cv2.boundingRect(
            contour
        )

        area = w * h

        if area < min_area:
            continue

        if area > max_area:
            continue

        aspect_ratio = w / h

        if aspect_ratio > 5:
            continue

        if aspect_ratio < 0.2:
            continue

        rack_code = (
            f"RACK-{rack_number:03}"
        )

        racks.append({
            "rack_code": rack_code,
            "x": int(x),
            "y": int(y),
            "width": int(w),
            "height": int(h),
            "area": int(area)
        })

        cv2.rectangle(
            original,
            (x, y),
            (x+w, y+h),
            (0, 255, 0),
            3
        )

        cv2.putText(
            original,
            rack_code,
            (x, y-10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 0, 0),
            2
        )

        rack_number += 1

    return original, racks


def save_racks_to_db(rack_df):

    with engine.begin() as conn:

        for _, row in rack_df.iterrows():

            conn.execute(
                text("""
                INSERT INTO racks
                (
                    rack_code,
                    x_coordinate,
                    y_coordinate,
                    width,
                    height,
                    area
                )
                VALUES
                (
                    :rack_code,
                    :x,
                    :y,
                    :width,
                    :height,
                    :area
                )

                ON CONFLICT (rack_code)

                DO UPDATE SET

                x_coordinate =
                EXCLUDED.x_coordinate,

                y_coordinate =
                EXCLUDED.y_coordinate,

                width =
                EXCLUDED.width,

                height =
                EXCLUDED.height,

                area =
                EXCLUDED.area
                """),
                row.to_dict()
            )

# =====================================================
# INIT TABLES
# =====================================================

create_tables()

# =====================================================
# PDF UPLOAD
# =====================================================

uploaded_file = st.file_uploader(
    "Upload Store Layout PDF",
    type=["pdf"]
)

if uploaded_file:

    pdf_bytes = uploaded_file.read()

    pdf = fitz.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    st.subheader("PDF Information")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Pages",
            pdf.page_count
        )

    with col2:
        st.metric(
            "Title",
            pdf.metadata.get("title")
            or "N/A"
        )

    # ==============================================
    # PAGE LOOP
    # ==============================================

    for page_number in range(
        pdf.page_count
    ):

        page = pdf[
            page_number
        ]

        image = pdf_page_to_image(
            page
        )

        st.subheader(
            f"Page {page_number + 1}"
        )

        st.image(
            image,
            use_container_width=True
        )

        if st.button(
            f"Detect Racks Page {page_number+1}"
        ):

            processed_image, racks = (
                detect_racks(image)
            )

            st.image(
                processed_image,
                caption="Detected Racks",
                use_container_width=True
            )

            if racks:

                rack_df = pd.DataFrame(
                    racks
                )

                st.success(
                    f"{len(racks)} racks detected"
                )

                st.dataframe(
                    rack_df,
                    use_container_width=True
                )

                # ==================================
                # SAVE TO DB
                # ==================================

                if st.button(
                    "💾 Save Racks To PostgreSQL"
                ):

                    save_racks_to_db(
                        rack_df
                    )

                    st.success(
                        f"{len(rack_df)} racks saved"
                    )

                # ==================================
                # VISUALIZATION
                # ==================================

                fig = px.scatter(
                    rack_df,
                    x="x",
                    y="y",
                    text="rack_code",
                    size="area",
                    title="Detected Rack Layout"
                )

                fig.update_yaxes(
                    autorange="reversed"
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

                # ==================================
                # CSV EXPORT
                # ==================================

                csv = (
                    rack_df
                    .to_csv(index=False)
                    .encode("utf-8")
                )

                st.download_button(
                    "⬇ Download Rack CSV",
                    csv,
                    "racks.csv",
                    "text/csv"
                )

# =====================================================
# VIEW SAVED RACKS
# =====================================================

st.divider()

st.subheader("📦 Saved Racks")

if st.button("Load Saved Racks"):

    query = """
    SELECT *
    FROM racks
    ORDER BY rack_code
    """

    saved_df = pd.read_sql(
        query,
        engine
    )

    st.dataframe(
        saved_df,
        use_container_width=True
    )
