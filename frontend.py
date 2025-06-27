import streamlit as st
import requests
import os

# === Page setup ===
st.set_page_config(
    page_title="Mini-Gateway Fraud Detector & OCR",
    page_icon="🕵️‍♂️",
    layout="centered"
)

st.title("🕵️‍♂️ Mini-Gateway Fraud Detector & Receipt OCR")
st.markdown("Fill in the transaction details and upload a receipt image to check the fraud risk.")

# === Form ===
with st.form("fraud_form"):
    category = st.selectbox(
        "Transaction Category",
        ["shopping", "food_dining", "travel", "gas_transport", "entertainment"]
    )
    amt = st.number_input("Transaction Amount ($)", min_value=0.0, value=50.0)
    gender = st.selectbox("Customer Gender", ["M", "F"])
    city_pop = st.number_input("City Population", min_value=0, value=50000)
    merch_lat = st.number_input("Merchant Latitude", value=40.7128)
    merch_long = st.number_input("Merchant Longitude", value=-74.0060)
    uploaded_file = st.file_uploader(
        "Upload a receipt image (PNG/JPG)", type=["png", "jpg", "jpeg"]
    )
    submit_btn = st.form_submit_button("🔍 Submit")

if submit_btn:
    if uploaded_file is None:
        st.error("⚠️ Please upload a receipt image.")
    else:
        # === Save the uploaded file ===
        receipt_dir = "uploaded_receipts"
        os.makedirs(receipt_dir, exist_ok=True)
        receipt_path = os.path.join(receipt_dir, uploaded_file.name)
        with open(receipt_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.info(f"📸 Receipt saved at `{receipt_path}`")

        # === Prepare payload ===
        payload = {
            "transaction": {
                "category": category,
                "amt": amt,
                "gender": gender,
                "city_pop": city_pop,
                "merch_lat": merch_lat,
                "merch_long": merch_long
            },
            "receipt_path": receipt_path
        }

        # === Call FastAPI ===
        try:
            api_url = "http://127.0.0.1:8000/score"  # adjust if needed
            response = requests.post(api_url, json=payload)

            if response.status_code == 200:
                result = response.json()
                st.success(f"✅ Fraud Score: `{result['fraud_score']}`")
                st.write(f"**Risk Level:** {result['fraud_risk_level']}")
                st.write(f"**Merchant Name:** {result['merchant_name']}")
                st.write(f"**Total Amount (OCR):** ${result['total_amount']:.2f}")
                st.write("**Features Used:**", result["features_used"])
            else:
                st.error(f"API Error {response.status_code}: {response.text}")

        except Exception as e:
            st.error(f"🚫 Failed to connect to FastAPI: {e}")
