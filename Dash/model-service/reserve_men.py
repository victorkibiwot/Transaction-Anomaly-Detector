from fastapi import FastAPI, HTTPException, Request
from predict import make_prediction
from schemas import PredictionRequest, PredictionResponse, TransactionRequest, TransactionResponse
from model import load_scaler
import psycopg2
import numpy as np
import os
from dotenv import load_dotenv


app = FastAPI(title="XGBoost Model API")

scaler = load_scaler()

# DB connection
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
conn = psycopg2.connect(DATABASE_URL)


@app.post("/transactions", response_model=TransactionResponse)
def record_transaction(data: TransactionRequest, request: Request):
    with conn.cursor() as cur:
        # 1. Fetch user balance before deduction
        cur.execute("SELECT account_balance FROM users WHERE user_id = %s", (data.user_id,))
        user_row = cur.fetchone()
        if not user_row:
            raise HTTPException(status_code=404, detail="User not found.")
        pre_balance = float(user_row[0])
        post_balance = pre_balance - data.amount  # this will be used for recording

        # 2. Get previous transactions to compute mean/std
        cur.execute("SELECT amount FROM transactions WHERE user_id = %s", (data.user_id,))
        rows = cur.fetchall()
        amounts = [float(row[0]) for row in rows]

        mean_amount = np.mean(amounts) if amounts else 0
        std_amount = np.std(amounts) if amounts else 1  # avoid division by zero

        # 3. Compute zscore and ratio
        zscore = (data.amount - mean_amount) / std_amount if std_amount != 0 else 0
        ratio = data.amount / pre_balance if pre_balance > 0 else 0

        # 4. Make prediction (based on PRE-DEDUCTION balance)
        pred_input = {
            "amount": data.amount,
            "account_balance": pre_balance,
            "amount_to_balance_ratio": ratio,
            "zscore_amount": zscore
        }

        # Prepare input data as PredictionRequest
        pred_input_model = PredictionRequest(**pred_input)

        # Call prediction route
        pred_result = make_prediction(pred_input_model)

        # 5. Insert transaction with POST-DEDUCTION balance
        cur.execute(
            "INSERT INTO transactions (user_id, amount, account_balance, created_at) VALUES (%s, %s, %s, now()) RETURNING id",
            (data.user_id, data.amount, post_balance)
        )

        transaction_id = cur.fetchone()[0]

        # 6. Insert anomaly if predicted as such
        if pred_result.prediction == 1:
            cur.execute(
                """
                INSERT INTO anomalies (transaction_id, amount, prediction, probability, prev_balance, amount_to_balance_ratio, zscore_amount, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, now())
                """,
                (transaction_id, data.amount, bool(pred_result.prediction), pred_result.probability, pre_balance, ratio, zscore)
            )

        # 7. Update user balance (subtract the amount)
        cur.execute("UPDATE users SET account_balance = %s WHERE user_id = %s", (post_balance, data.user_id))

        conn.commit()

    return TransactionResponse(
        prediction=pred_result.prediction,
        probability=pred_result.probability,
        message="Transaction processed and recorded."
    )

@app.post("/predict", response_model=PredictionResponse)
def predict(data: PredictionRequest):
    prediction = make_prediction(data)
    return prediction

@app.get("/")
def root():
    return {"message": "Anomaly Detection Model API is live."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
