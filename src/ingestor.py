import websocket
import json
from datetime import datetime
import threading
import os
from dotenv import load_dotenv
import time

# --- Importar la secuencia de trading ---
from src.engine import initiate_trading_sequence 

# Configuration - AllSportsAPI WebSocket
load_dotenv()
API_KEY = os.getenv("ALLSPORTS_API_KEY") 
WEBSOCKET_URL = f"wss://wss.allsportsapi.com/live_events?APIkey={API_KEY}&timezone=+00:00"
previous_scores = {}

# --- Funciones de WebSocket (on_message es la clave) ---

def on_message(ws, message):    
    try:        
        data = json.loads(message)                
        for match in data:
            match_id = match.get('event_key', 'N/A')
            home_team = match.get('event_home_team', 'Unknown')
            away_team = match.get('event_away_team', 'Unknown')
            current_result = match.get('event_final_result', '0 - 0')
            minute = match.get('event_status', 'N/A')
            
            try:
                home_score, away_score = map(int, current_result.replace(' ', '').split('-'))
                current = (home_score, away_score)
            except:
                continue                        
            
            if match_id in previous_scores:
                prev_home, prev_away = previous_scores[match_id]
                
                if current != (prev_home, prev_away):
                    # --- GOAL DETECTED! ---
                    ingest_time = datetime.now() 
                    scorer = home_team if home_score > prev_home else away_team
                    
                    # 2. Event normalizer: Crear esquema compacto para el Decision Engine
                    event_data = {
                        'ingest_time': ingest_time,
                        'match_id': match_id,
                        'scorer_team': scorer,
                        'current_score': current_result,
                        'home_team': home_team,
                        'away_team': away_team
                    }
                    
                    # 3. Disparo del Decision Engine en un Hilo Separado (Paralelización)
                    threading.Thread(target=initiate_trading_sequence, args=(event_data,)).start()
                    
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚽ Goal Alert: {home_team} vs {away_team} -> {current_result}")
                    
                # Update stored score
                previous_scores[match_id] = current
        
    except json.JSONDecodeError as e:
        print(f"Error parsing message: {e}")    
    except Exception as e:        
        print(f"Error processing match: {e}")

# --- Funciones de Conexión (Resto del código original) ---

def on_error(ws, error):    
    print(f"WebSocket Error: {error}")
    
def on_close(ws, close_status_code, close_msg):    
    print(f"\n⚠️ WebSocket connection closed")    
    print("Attempting to reconnect in 5 seconds...")

def on_open(ws):    
    print("="*70)    
    print("⚽ REAL-TIME SOCCER GOAL MONITOR")    
    print(f"Connected at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def start_monitor():
    """Start the WebSocket connection"""
    websocket.enableTrace(False)
    
    if API_KEY == "TU_CLAVE_DE_LIVE_SCORE":
        print("\n⚠️ API KEY SETUP REQUIRED in .env file.")
        return

    ws = websocket.WebSocketApp(        
        WEBSOCKET_URL,        
        on_open=on_open,        
        on_message=on_message,        
        on_error=on_error,        
        on_close=on_close    
    )        
    
    while True:
        try:
            ws.run_forever()
        except KeyboardInterrupt:
            print("\n🛑 Monitor stopped by user")
            ws.close()
            break
        except Exception as e:
            print(f"Connection error: {e}")
            time.sleep(5)