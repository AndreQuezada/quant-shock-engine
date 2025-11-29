import os
import threading
from datetime import datetime
import time
import json
import requests
import hmac, hashlib
from dotenv import load_dotenv

# Post-Trade Manager
from src.utils import create_kalshi_signature, safe_api_call, fetch_market_state, submit_order 
from src.post_trade_manager import manage_position 


load_dotenv()
API_KEY = os.getenv("KALSHI_API_KEY") 
API_SECRET = os.getenv("KALSHI_API_SECRET")
BANKROLL = float(os.getenv("BANKROLL", 10000.00))

# --- Controles de Riesgo Globales (Paso 8) ---
TRADING_HALTED = False 
MAX_DAILY_DRAWDOWN = -0.05 
KALSHI_DEMO_URL = "https://demo-api.kalshi.com/v1" 

# Las funciones fetch_market_state y submit_order FUERON ELIMINADAS de aquí

def calculate_order_size():
    """Calculates the order size based on risk parameters (Paso 7)."""
    MAX_PER_TRADE = float(os.getenv("MAX_PER_TRADE", 100.00))
    K_FRACTION = 0.005
    size = min(MAX_PER_TRADE, BANKROLL * K_FRACTION)
    return round(size, 2)

# --- Función Principal de Trading (Decision Engine) ---
def initiate_trading_sequence(event_data):
    """4. Decision Engine: Runs on a separate thread upon goal detection."""
    if TRADING_HALTED: 
        return

    ingest_time = event_data['ingest_time']
    match_id = event_data['match_id']
    
    current_odds, liquidity = fetch_market_state(match_id)
    
    was_underdog = True 
    threshold = 0.5
    
    if was_underdog and current_odds < threshold and liquidity >= 500:
        
        order_size = calculate_order_size()
        order_result = submit_order(match_id, current_odds, order_size)
        
        if order_result:
            threading.Thread(target=manage_position, args=(order_result, current_odds)).start()

            latency_ms = (datetime.now() - ingest_time).total_seconds() * 1000
            print(f"[{datetime.now().strftime('%H:%M:%S.%f')}] ✅ Trade Initiated. Latency: {latency_ms:.2f} ms")
        
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')}] ❌ No Trade: Mispricing or Liquidity Fail.")