import os
from dotenv import load_dotenv
from src.ingestor import start_monitor
import time

if __name__ == "__main__":
    # 1. Cargar Variables de Entorno (.env)
    load_dotenv()
    
    print("="*50)
    print("      Goal Shock Quant Engine Starting")
    print("="*50)
    
    # 2. Verificar que las claves críticas estén configuradas
    if not os.getenv("KALSHI_API_KEY") or not os.getenv("ALLSPORTS_API_KEY"):
        print("🛑 ERROR: Please configure API keys in the .env file.")
    else:
        # 3. Iniciar el monitor (WebSocket)
        print("✅ Starting Live Score Monitor...")
        start_monitor()