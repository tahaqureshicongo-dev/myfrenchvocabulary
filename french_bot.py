import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import asyncio
import schedule
import time
import requests
from telegram import Bot

# Render Port Binding for Health Check
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

TOKEN = "8952477275:AAHde9By_daqvVvXgmAai5np-6LreGywpWs"
CHAT_ID = "7690989029"
RENDER_URL = "https://myfrenchvocabulary.onrender.com"

# Live Online Dictionary API integration
def fetch_from_online_dictionary():
    try:
        # Free Random French Vocabulary API
        response = requests.get("https://french-words-api.vercel.app/api/random", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("word"), data.get("meaning"), data.get("example")
    except Exception as e:
        print(f"Dictionary API error: {e}")
    
    # Fallback backup word in case API times out
    return "Bonjour", "Hello", "Bonjour, comment allez-vous?"

async def send_word():
    bot = Bot(token=TOKEN)
    word, meaning, example = fetch_from_online_dictionary()
    
    message = (
        f"🇫🇷 *Automated Daily French Word*\n\n"
        f"🗣 *Word:* {word}\n"
        f"💡 *Meaning:* {meaning}\n"
        f"📝 *Example:* _{example}_"
    )
    
    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
    print(f"Fetched & Sent Online Word: {word}")

def job():
    asyncio.run(send_word())

# Har 1 ghante mein online dictionary se naya word fetch karega
schedule.every(1).hours.do(job)

# Self-Ping for Render Keep-Alive
def keep_alive():
    while True:
        time.sleep(600)
        try:
            requests.get(RENDER_URL, timeout=10)
        except Exception:
            pass

threading.Thread(target=keep_alive, daemon=True).start()

print("Automated Dictionary French Bot Active...")

# Immediate test execution
job()

while True:
    schedule.run_pending()
    time.sleep(1)
