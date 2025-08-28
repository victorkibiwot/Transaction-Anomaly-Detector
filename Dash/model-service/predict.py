from model import load_model, load_scaler
from utils import prepare_features
from schemas import PredictionRequest, PredictionResponse


# Load once on import (good for performance)
model = load_model()
scaler = load_scaler()

def make_prediction(data: PredictionRequest) -> PredictionResponse:
    features = prepare_features(data, scaler)  # ← Pass scaler here
    proba = model.predict_proba(features)[0]
    prediction = int(model.predict(features)[0])
    return PredictionResponse(prediction=prediction, probability=proba[prediction])
