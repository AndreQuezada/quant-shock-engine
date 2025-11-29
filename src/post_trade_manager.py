import time
from datetime import datetime, timedelta
# Importación CORREGIDA: Ahora se importan desde src/utils.py
from src.utils import fetch_market_state, submit_order 

def manage_position(order_result, entry_price):
    """Monitors the position after the fill and executes the exit strategy (TP/SL)."""
    
    position_data = {
        'order_id': order_result['order_id'],
        'entry_price': entry_price,
        'is_open': True,
        'max_exit_time': datetime.now() + timedelta(minutes=5) 
    }

    TARGET_PROFIT_PERCENT = 0.15 
    target_price = entry_price * (1 + TARGET_PROFIT_PERCENT)
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏳ Monitoring Position. TP Target: {target_price:.4f}")

    while position_data['is_open']:
        time.sleep(2) 
        
        current_market_price, _ = fetch_market_state(position_data['order_id']) 
        
        # 1. Lógica de Take Profit (TP)
        if current_market_price >= target_price:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🟢 TAKE PROFIT. Price reached: {current_market_price}")
            # **Aquí se enviaría la orden de VENTA final usando submit_order()**
            position_data['is_open'] = False
            break
            
        # 2. Lógica de Salida por Tiempo (Time-Based Stop Loss)
        if datetime.now() > position_data['max_exit_time']:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔴 STOP LOSS by Time. Forced liquidation.")
            # **Aquí se enviaría la orden de VENTA forzada**
            position_data['is_open'] = False
            break
            
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Position {position_data['order_id']} closed.")