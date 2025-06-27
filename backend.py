from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import joblib
import cv2
import pytesseract
import re
import numpy as np
import os
import platform
from typing import Dict

# === FastAPI Setup ===
app = FastAPI(
    title="Mini-Gateway Fraud & OCR Inference API",
    description="Predicts fraud score and extracts key receipt data from images.",
    version="1.0.0"
)

# === Load Model and Preprocessing Artifacts ===
model = joblib.load("calibrated_model.pkl")
scaler = joblib.load("scaler.pkl")
feature_order = joblib.load("feature_order.pkl")

# === Label Encoders as Mapping ===
label_encoders = {
    'category': {
        "shopping": 0,
        "food_dining": 1,
        "travel": 2,
        "gas_transport": 3,
        "entertainment": 4
    },
    'gender': {
        "M": 0,
        "F": 1
    }
}

# === Define Numerical Columns ===
numerical_cols = ['amt', 'merch_lat', 'merch_long', 'city_pop']

# === Tesseract Path: smart for local + Docker ===
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# === Pydantic Schema ===
class TransactionRequest(BaseModel):
    transaction: Dict
    receipt_path: str

# === OCR + Parsing ===
def process_receipt(image_path: str) -> Dict[str, any]:
    try:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError(f"Failed to load image: {image_path}")

        # Binarize & deskew
        img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        coords = np.column_stack(np.where(img > 0))
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        (h, w) = img.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        img = cv2.warpAffine(img, M, (w, h))

        # OCR
        text = pytesseract.image_to_string(img, config='--psm 6')
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        # Extract merchant name
        merchant_name = "UNKNOWN"
        blacklist = {"thank", "purchase", "visit", "welcome", "please", "receipt"}
        for line in lines[:6]:
            if any(word in line.lower() for word in blacklist):
                continue
            if not re.search(r'\d|\$|[0-9]+(\.[0-9]{2})?', line) and len(line.strip()) > 3:
                merchant_name = re.sub(r'[^a-zA-Z0-9 &]', '', line)
                break

        # Extract total
        total_amount = 0.0
        for line in reversed(lines):
            if 'total' in line.lower():
                match = re.search(r'(\d+\.\d{2})', line)
                if match:
                    total_amount = float(match.group(1))
                    break
        if total_amount == 0.0:
            matches = re.findall(r'(\d+\.\d{2})', text)
            if matches:
                total_amount = float(matches[-1])

        return {"merchant_name": merchant_name, "total_amount": total_amount}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

# === Main Endpoint ===
@app.post("/score")
async def score(request: TransactionRequest):
    try:
        transaction = request.transaction
        receipt_path = request.receipt_path

        if not os.path.exists(receipt_path):
            raise HTTPException(status_code=400, detail="Receipt image not found.")

        df = pd.DataFrame([transaction])

        # Encode categorical using mapping
        for col in ['category', 'gender']:
            if col not in df.columns:
                raise HTTPException(status_code=400, detail=f"Missing '{col}' in transaction")
            if df[col].values[0] not in label_encoders[col]:
                raise HTTPException(status_code=400, detail=f"Invalid value for '{col}': {df[col].values[0]}")
            df[col] = df[col].map(label_encoders[col])

        # Align features
        final_df = pd.DataFrame(columns=feature_order)
        for col in feature_order:
            final_df[col] = df[col] if col in df.columns else 0

        # Scale numerical
        final_df[numerical_cols] = scaler.transform(final_df[numerical_cols])

        # Predict
        fraud_score = float(model.predict_proba(final_df)[0][1])

        receipt_data = process_receipt(receipt_path)

        return {
            "fraud_score": round(fraud_score, 4),
            "fraud_risk_level": (
                "High" if fraud_score >= 0.85 else
                "Medium" if fraud_score >= 0.5 else
                "Low"
            ),
            "merchant_name": receipt_data["merchant_name"],
            "total_amount": round(receipt_data["total_amount"], 2),
            "features_used": feature_order
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
