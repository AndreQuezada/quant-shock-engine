# Goal Shock Quant Engine: Low-Latency Sports Trading System

## Project Summary
This low-latency Python system exploits short-term market mispricing on Kalshi/Polymarket by initiating trades within seconds after an **underdog scores a goal**. The engine targets football match winner markets by betting on the rapid odds correction following a goal shock, aiming to execute trades within the critical few-second window.

## Architecture and Design Decisions
The system is built on a **concurrent architecture** to minimize end-to-end latency:

1. **Live-Event Ingestor (src/ingestor.py):** Uses WebSockets (or a fast feed) to detect goals and immediately **delegates the event to a separate thread** (`threading.Thread`) to prevent blocking the data feed.
2. **Decision Engine (src/engine.py):** Runs the core logic concurrently with the **Market State Fetcher** to determine eligibility based on the underdog rule.
3. **Order Executor:** Uses the **Kalshi Signed Header Scheme** for secure authentication and submits **IOC (Immediate-or-Cancel)** orders for speed.
4. **Post-Trade Manager (src/post_trade_manager.py):** Monitors successful fills and enforces the **Take-Profit / Time-Based Exit Strategy**.

## Risk and Safety Controls
- **Exposure Limits:** Includes checks for Max Trade Size and Max Daily Drawdown (simulated).
- **Security:** Implements **HMAC-SHA256 signing** for all transactional API calls.
- **Resilience:** Uses **Exponential Backoff** on API calls to handle rate limits and avoid blocks.

## Setup & Run Instructions
1. **Prerequisites:** Ensure Python 3.x is installed, and the terminal is in the project root with the `(venv)` activated.
2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt