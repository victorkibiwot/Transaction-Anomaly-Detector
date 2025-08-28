import joblib

MODEL_PATH = "trained_model.pkl"
SCALER_PATH = "scaler.pkl"

def load_model():
    model = joblib.load(MODEL_PATH)
    return model

def load_scaler():
    scaler = joblib.load(SCALER_PATH)
    return scaler
