<<<<<<< HEAD
# fraud-detection-ocr-api
A FastAPI-based service that combines fraud detection and OCR receipt processing
=======
# 🕵️‍♂️ Mini-Gateway Fraud Detection & Receipt OCR API

This project is a **prototype fraud detection gateway** that combines **machine learning** with **receipt OCR extraction** — fully containerized with **FastAPI** + **Streamlit** + **Docker**.

---

## 📌 **Features**

✅ Predicts fraud risk score for credit card transactions  
✅ Uses a trained & calibrated ML model (`calibrated_model/SVM/gradient_boosting_model` with probability calibration)  
✅ Supports receipt image OCR with `Tesseract` inside Docker  
✅ Provides an interactive **Streamlit UI**  
✅ Fully packaged with Docker — easy to share & run

---

## 🚀 **How It Works**

1. **User uploads**:
   - Transaction details (category, amount, location, etc.)
   - Receipt image (`.jpg` / `.png`)

2. **Backend**:
   - Extracts `merchant_name` & `total_amount` using `Tesseract OCR`
   - Preprocesses transaction data (encodes categorical, scales numeric)
   - Loads trained & calibrated model (`calibrated_model.pkl`)
   - Predicts `fraud_score` & `fraud_risk_level`

3. **Frontend (Streamlit)**:
   - Simple form for inputs
   - Displays score, risk level & OCR results

---

## ⚙️ **Project Structure**
├── backend.py 
├── frontend.py
├── svm_model.pkl 
├── scaler.pkl
├── calibrated_model.pkl
├── feature_order.pkl
├── uploaded_receipts/ 
├── Dockerfile
├── requirements.txt 
└── README.md 


---

## 🐳 **Run with Docker**

1️⃣ **Build the image:**
docker build -t fraud-ocr-app .

2️⃣ **Run the container:**
docker run -p 8000:8000 -p 8501:8501 fraud-ocr-app


>>>>>>> 0424e7a (Initial commit: Fraud Detection and OCR API)
