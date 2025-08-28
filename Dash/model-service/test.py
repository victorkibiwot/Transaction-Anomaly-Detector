import requests

url = "http://127.0.0.1:8000/predict"
payload = {
    "amount": 500.0,
    "account_balance": 3000.0,
    "amount_to_balance_ratio": 0.1667,
    "zscore_amount": 0.8
}
response = requests.post(url, json=payload)
print(response.json())