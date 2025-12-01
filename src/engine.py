import os
import threading
from datetime import datetime
import time
import json
import requests
import hmac, hashlib
from dotenv import load_dotenv

# --- Import Utilities and Post-Trade Manager ---
# IMPORTANT: These functions were moved to resolve the circular import (ImportError).
from src.utils import create_kalshi_signature, safe_api_call, fetch_market_state, submit_order 
from src.post_trade_manager import manage_position 

# ----------------------------------------------------
# 1. INITIAL CONFIGURATION AND ENVIRONMENT LOAD
# ----------------------------------------------------
load_dotenv() # Load variables from .env file

# --- Global Parameters (Read from .env) ---
API_KEY = os.getenv("KALSHI_API_KEY") 
API_SECRET = os.getenv("KALSHI_API_SECRET")
BANKROLL = float(os.getenv("BANKROLL", 10000.00))

# NEW CONFIGURATION: Minimum time requirement for goal validity
MIN_GOAL_MINUTE = int(os.getenv("MIN_GOAL_MINUTE", 30)) 

# --- Risk Controls ---
TRADING_HALTED = False 
MAX_DAILY_DRAWDOWN = -0.05 
KALSHI_DEMO_URL = "https://demo-api.kalshi.co/trade-api/v2"
# ----------------------------------------------------
# HELPER FUNCTIONS
# ----------------------------------------------------

def calculate_order_size():
    """Calculates the order size based on risk parameters."""
    MAX_PER_TRADE = float(os.getenv("MAX_PER_TRADE", 100.00))
    K_FRACTION = 0.005
    size = min(MAX_PER_TRADE, BANKROLL * K_FRACTION)
    return round(size, 2)

def check_underdog_status_pre_event(match_id):
    """
    [REAL LOGIC PLACEHOLDER] Verifica si el equipo que anotó era el menos favorito (underdog).
    En un entorno real, esto consultaría datos pre-evento. Para la sumisión, 
    establecemos una función con retorno seguro.
    """
    # Aquí iría la lógica de API/DB, pero por ahora, retorna un valor seguro.
    return False 


# ----------------------------------------------------
# --- CORE TRADING FUNCTION (Decision Engine) ---
# ----------------------------------------------------
def initiate_trading_sequence(event_data):
    """
    4. Decision Engine: Runs on a separate thread upon goal detection.
    Applies eligibility rules, risk checks, and triggers order execution.
    """
    if TRADING_HALTED: 
        return

    ingest_time = event_data['ingest_time']
    match_id = event_data['match_id']
    
    # Market State Fetcher (from src/utils.py)
    current_odds, liquidity = fetch_market_state(match_id)
    
    # --- 1. PROCESS GOAL MINUTE FILTER ---
    goal_minute_str = event_data.get('minute', '0')
    
    # Clean the string (e.g., "30'") to get the integer number
    try:
        goal_minute = int(goal_minute_str.split('\'')[0].strip())
    except ValueError:
        goal_minute = 0
        
    # Apply the minimum time filter
    is_past_min_time = (goal_minute >= MIN_GOAL_MINUTE)
    # -----------------------------------------------

    
    # Core Decision Logic (Paso 7)
    # was_underdog = True # <-- LÍNEA DE SIMULACIÓN ELIMINADA
    was_underdog = check_underdog_status_pre_event(match_id) # <-- LLAMADA A FUNCIÓN REAL
    threshold = 0.5
    
    # FINAL ELIGIBILITY CHECK
    if was_underdog and current_odds < threshold and liquidity >= 500 and is_past_min_time: 
        
        order_size = calculate_order_size()
        order_result = submit_order(match_id, current_odds, order_size)
        
        if order_result:
            # Post-trade Manager (runs in a new thread for monitoring)
            threading.Thread(target=manage_position, args=(order_result, current_odds)).start()

            # Latency Monitoring
            latency_ms = (datetime.now() - ingest_time).total_seconds() * 1000
            print(f"[{datetime.now().strftime('%H:%M:%S.%f')}] ✅ Trade Initiated. Latency: {latency_ms:.2f} ms")
        
    else:
        # Log the reason for the no-trade decision
        reason = []
        if not is_past_min_time:
            reason.append(f"Time < {MIN_GOAL_MINUTE} min ({goal_minute} min)")
        if not was_underdog or current_odds >= threshold:
            reason.append("Mispricing Fail")
        if liquidity < 500:
            reason.append("Low Liquidity")
            
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')}] ❌ No Trade: {', '.join(reason)}.")