import hmac
import hashlib
import time
import requests
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# --- Configuración de URL de la API de DEMO ---
KALSHI_DEMO_TRADE_URL = "https://demo-api.kalshi.co/trade-api/v2" 
KALSHI_DEMO_READ_URL = "https://demo-api.kalshi.co/v1" # Usar v1 para lectura pública

# --- Cargar Credenciales y Configuraciones ---
load_dotenv()
API_KEY = os.getenv("KALSHI_API_KEY") 
API_SECRET = os.getenv("KALSHI_API_SECRET")
BANKROLL = float(os.getenv("BANKROLL", 10000.00))

# --- FUNCIONES DE SEGURIDAD Y FIRMA (AUTHENTICATION) ---
def create_kalshi_signature(method, path, body, timestamp, secret_key):
    """Generates the HMAC-SHA256 signature required by Kalshi."""
    # ... (código existente, no modificado) ...
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

# --- GESTIÓN DE RIESGO Y CONEXIÓN (RESILIENCE) ---
MAX_RETRIES = 5

def safe_api_call(method, url, headers, data=None):
    """Performs an API call with Exponential Backoff for handling Rate Limits (429)."""
    # ... (código existente, no modificado) ...
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

# ------------------------------------------------------------------------
# --- FUNCIONES DE API (PRODUCCIÓN REAL - SIN MOCK DATA) ---
# ------------------------------------------------------------------------

def fetch_market_state(match_id):
    """3. Market State Fetcher: Fetches current odds and liquidity from Kalshi Demo (Real Call)."""
    
    # Endpoint de lectura v1 de Kalshi (asumiendo llamadas GET públicas)
    path = f"/markets/{match_id}" 
    url = f"{KALSHI_DEMO_READ_URL}{path}"
    
    try:
        # Llamada directa sin simulación de tiempo
        response = requests.get(url, timeout=0.5) 
        response.raise_for_status()
        
        data = response.json()
        
        # Extracción de valores reales (asunción de la estructura JSON de Kalshi)
        current_price = data['market']['price'] / 100 
        liquidity = data['market']['open_interest']
        
        return current_price, liquidity
        
    except Exception as e:
        print(f"⚠️ Failed to fetch real market state for {match_id}: {e}. Returning safe values.")
        # Devuelve valores que NO ACTIVARÁN el trading si falla la conexión
        return 0.50, 0 


def submit_order(match_id, price, size):
    """5. Order Executor: Submits the signed order to the Kalshi Demo Exchange (REAL CALL)."""
    
    order_data = {
        "market_id": match_id,
        "action": "BUY",
        "quantity": size,
        "price": price, 
        "order_type": "IOC"
    }
    
    timestamp = str(int(time.time() * 1000))
    path = "/order" # Path relativo para el endpoint de trade (v2)
    body = json.dumps(order_data)
    
    # 2. Generar Firma
    signature = create_kalshi_signature("POST", path, body, timestamp, API_SECRET)
    
    # 3. Headers
    headers = {
        "KALSHI-ACCESS-KEY": API_KEY,
        "KALSHI-ACCESS-TIMESTAMP": timestamp,
        "KALSHI-ACCESS-SIGNATURE": signature,
        "Content-Type": "application/json"
    }
    
    # 4. Enviar la orden usando la función resiliente
    try:
        response = safe_api_call("POST", f"{KALSHI_DEMO_TRADE_URL}{path}", headers=headers, data=order_data)
        data = response.json()
        
        # Retorna el resultado real de la orden (ID y precio de FILL)
        order_fill_id = data.get('order_id', 'UNKNOWN')
        fill_price = data.get('fill_price', price)

        print(f"[{datetime.now().strftime('%H:%M:%S.%f')}] 🎯 PRODUCTION-READY ORDER SENT: {order_fill_id}")
        return {"order_id": order_fill_id, "fill_price": fill_price}
    
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ PRODUCTION ORDER FAILED: {e}")
        return None