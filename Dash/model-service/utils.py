import numpy as np
from schemas import PredictionRequest

def prepare_features(data: PredictionRequest, scaler):
    raw = np.array([
        data.amount,
        data.account_balance,
        data.amount_to_balance_ratio,
        data.zscore_amount
    ]).reshape(1, -1)
    
    scaled = scaler.transform(raw)
    return scaled