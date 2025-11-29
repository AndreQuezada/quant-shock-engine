import hmac
import hashlib
import time
import requests
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# --- Cargar Credenciales y Configuraciones ---
# Las cargamos aquí para que submit_order pueda usar API_SECRET y API_KEY
load_dotenv()
API_KEY = os.getenv("KALSHI_API_KEY") 
API_SECRET = os.getenv("KALSHI_API_SECRET")
BANKROLL = float(os.getenv("BANKROLL", 10000.00))

# --- FUNCIONES DE SEGURIDAD Y FIRMA (Paso 5) ---

def create_kalshi_signature(method, path, body, timestamp, secret_key):
    """Generates the HMAC-SHA256 signature required by Kalshi."""
    
    if body:
        hashed_body = hashlib.sha256(body.encode('utf-8')).hexdigest()
        sign_string = f"{timestamp}{method}{path}{hashed_body}"
    else:
        sign_string = f"{timestamp}{method}{path}"
        
    signature = hmac.new(
        secret_key.encode('utf-8'), 
        sign_string.encode('utf-8'), 
        hashlib.sha256
    ).hexdigest()
    
    return signature

# --- GESTIÓN DE RIESGO Y CONEXIÓN (Paso 8) ---
MAX_RETRIES = 5

def safe_api_call(method, url, headers, data=None):
    """Performs an API call with Exponential Backoff for handling Rate Limits (429)."""
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.request(method, url, headers=headers, json=data, timeout=5)
            
            if response.status_code == 429:
                wait_time = 2 ** attempt
                print(f"⚠️ Rate Limit reached. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            
            response.raise_for_status()
            return response
        
        except requests.exceptions.RequestException as e:
            if attempt == MAX_RETRIES - 1:
                raise e
            print(f"Connection error on attempt {attempt+1}: {e}")
            time.sleep(1) 
            
# --- Mapeo de Nombres (Paso 9) ---
TEAM_NAME_MAP = {"Liverpool": "LIVERPOOL_FC", "Man City": "MANCHESTER_CITY"}

def normalize_team_name(name):
    """Normalizes the team name to match the exchange API."""
    return TEAM_NAME_MAP.get(name, name)

# --- FUNCIONES DE API MOVIDAS DESDE engine.py (Para resolver la dependencia) ---

def fetch_market_state(match_id):
    """3. Market State Fetcher: Fetches current odds and liquidity (SIMULATED)."""
    time.sleep(0.05) 
    current_odds = 0.45 
    liquidity = 2500  
    return current_odds, liquidity

def submit_order(match_id, price, size):
    """5. Order Executor: Submits the signed order to the Kalshi Demo Exchange."""
    
    order_data = {
        "market_id": match_id,
        "action": "BUY",
        "quantity": size,
        "price": price,
        "order_type": "IOC"
    }
    
    timestamp = str(int(time.time() * 1000))
    path = "/trade/v1/order"
    body = json.dumps(order_data)
    
    # Usa las claves cargadas en este módulo
    signature = create_kalshi_signature("POST", path, body, timestamp, API_SECRET)
    
    headers = {
        "KALSHI-ACCESS-KEY": API_KEY,
        "KALSHI-ACCESS-TIMESTAMP": timestamp,
        "KALSHI-ACCESS-SIGNATURE": signature,
        "Content-Type": "application/json"
    }
    
    try:
        # Simulación de FILL exitoso
        order_fill_id = f"SIM_{int(time.time())}"
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')}] 🎯 Order Submitted: {order_fill_id}")
        return {"order_id": order_fill_id, "fill_price": price} 
    
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Order Submission FAILED: {e}")
        return None