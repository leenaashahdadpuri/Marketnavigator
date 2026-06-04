import streamlit as st

st.title("Product Validation")

barcode = st.text_input("Barcode")

rack = st.selectbox(
    "Rack",
    [
        "RACK-A-01",
        "RACK-B-05"
    ]
)

shelf = st.number_input("Shelf")

bin_no = st.number_input("Bin")

if st.button("Validate"):

    result = validate_product(
        barcode,
        rack,
        shelf,
        bin_no
    )

    if result["status"] == "VALID":
        st.success("Product is correctly placed")
    else:
        st.error("Incorrect location")

        st.write(
            result["expected_location"]
        )
