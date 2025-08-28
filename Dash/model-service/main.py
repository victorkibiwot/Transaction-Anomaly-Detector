from fastapi import FastAPI, HTTPException
from predict import make_prediction
from schemas import PredictionRequest, PredictionResponse, TransactionRequest, TransactionResponse
from model import load_scaler
import psycopg2
from psycopg2 import pool
import numpy as np
import os
from dotenv import load_dotenv
import warnings
warnings.filterwarnings("ignore", message="X does not have valid feature names")


app = FastAPI(title="XGBoost Model API")
scaler = load_scaler()

# Load env
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Create connection pool
db_pool = psycopg2.pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    dsn=DATABASE_URL
)

def run_db_query(query, params=None, fetch=False, fetchone=False):
    """Helper for safe DB queries with auto commit/rollback."""
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            if fetchone:
                result = cur.fetchone()
            elif fetch:
                result = cur.fetchall()
            else:
                result = None
        conn.commit()
        return result
    except Exception:
        conn.rollback()
        raise
    finally:
        db_pool.putconn(conn)

@app.post("/transactions", response_model=TransactionResponse)
def record_transaction(data: TransactionRequest):
    # 1. Fetch user balance
    user_row = run_db_query(
        "SELECT account_balance FROM users WHERE user_id = %s",
        (data.user_id,),
        fetchone=True
    )
    if not user_row:
        raise HTTPException(status_code=404, detail="User not found.")

    pre_balance = float(user_row[0])

    # 2️⃣ Overdraft check
    if data.amount > pre_balance:
        raise HTTPException(status_code=400, detail="Insufficient funds.")
    
    post_balance = pre_balance - data.amount

    # 2. Get previous transactions for stats
    rows = run_db_query(
        "SELECT amount FROM transactions WHERE user_id = %s",
        (data.user_id,),
        fetch=True
    )
    amounts = [float(row[0]) for row in rows]
    mean_amount = float(np.mean(amounts)) if amounts else 0.0
    std_amount = float(np.std(amounts)) if amounts else 1.0

    # 3. Compute features
    zscore = float((data.amount - mean_amount) / std_amount) if std_amount != 0 else 0.0
    ratio = float(data.amount / pre_balance) if pre_balance > 0 else 0.0

    # 4. Predict
    pred_input_model = PredictionRequest(
        amount=data.amount,
        account_balance=pre_balance,
        amount_to_balance_ratio=ratio,
        zscore_amount=zscore
    )
    pred_result = make_prediction(pred_input_model)

    # 5. Insert transaction
    transaction_id = run_db_query(
        """
        INSERT INTO transactions (user_id, amount, account_balance, created_at)
        VALUES (%s, %s, %s, now()) RETURNING id
        """,
        (data.user_id, data.amount, post_balance),
        fetchone=True
    )[0]

    # 6. If anomaly, insert into anomalies table
    if pred_result.prediction == 1:
        run_db_query(
            """
            INSERT INTO anomalies (transaction_id, amount, prediction, probability, prev_balance, amount_to_balance_ratio, zscore_amount, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, now())
            """,
            (transaction_id, data.amount, bool(pred_result.prediction), pred_result.probability, pre_balance, ratio, zscore)
        )

    # 7. Update user balance
    run_db_query(
        "UPDATE users SET account_balance = %s WHERE user_id = %s",
        (post_balance, data.user_id)
    )

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
