from pydantic import BaseModel

class PredictionRequest(BaseModel):
    amount: float
    account_balance: float
    amount_to_balance_ratio: float
    zscore_amount: float

class PredictionResponse(BaseModel):
    prediction: int
    probability: float

class TransactionRequest(BaseModel):
    user_id: str
    amount: float

class TransactionResponse(BaseModel):
    prediction: int
    probability: float
    message: str
