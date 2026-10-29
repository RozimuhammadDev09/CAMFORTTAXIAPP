import threading
import time
import sys
import os

# Fix Windows console encoding for emojis
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db
from config import APP_NAME, SERVER_HOST, SERVER_PORT
import server
import bot

def run_flask():
    print(f"🚀 [API Server] Starting on http://{SERVER_HOST}:{SERVER_PORT}")
    server.app.run(host=SERVER_HOST, port=SERVER_PORT, debug=False, use_reloader=False)

def run_telegram_bot():
    print(f"🤖 [Telegram Bot] Starting polling for @camfort_taxi_zakaz_bot...")
    while True:
        try:
            bot.bot.infinity_polling(timeout=15, long_polling_timeout=15)
        except (KeyboardInterrupt, SystemExit):
            break
        except BaseException as e:
            print(f"⚠️ [Telegram Bot] Re-establishing connection: {e}")
            time.sleep(3)

if __name__ == "__main__":
    print(f"==================================================")
    print(f"   {APP_NAME} - SYSTEM BACKEND & TELEGRAM BOT")
    print(f"==================================================")
    init_db()

    # Thread 1: Flask REST API
    t_api = threading.Thread(target=run_flask, daemon=True)
    t_api.start()

    # Thread 2: Telegram Bot
    try:
        run_telegram_bot()
    except KeyboardInterrupt:
        print("\nStopping services...")
