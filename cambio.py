import requests
import json
from datetime import datetime

def get_rate():
    url = "https://api.apis.net.pe/v1/tipo-cambio-sunat"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            res = {
                "purchase": float(data['compra']),
                "sale": float(data['venta']),
                "date": data['fecha'],
                "isLive": True
            }
        else: raise Exception("Error API")
    except:
        res = {"purchase": 3.82, "sale": 3.85, "date": "OFFLINE", "isLive": False}
    
    with open('rate.json', 'w', encoding='utf-8') as f:
        json.dump(res, f, indent=2)
    print("✅ Cambio actualizado")

if __name__ == "__main__":
    get_rate()