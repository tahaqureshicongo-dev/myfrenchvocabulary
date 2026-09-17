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

# Background HTTP Server for Render Health Check
threading.Thread(target=run_server, daemon=True).start()

TOKEN = "8952477275:AAHde9By_daqvVvXgmAai5np-6LreGywpWs"
CHAT_ID = "7690989029"
RENDER_URL = "https://myfrenchvocabulary.onrender.com"

def get_random_french_word():
    import random
    auto_words = [
        {"word": "Monde", "meaning": "World", "example": "Le monde est grand."},
        {"word": "Soleil", "meaning": "Sun", "example": "Le soleil brille."},
        {"word": "Nuit", "meaning": "Night", "example": "Bonne nuit!"},
        {"word": "Voiture", "meaning": "Car", "example": "C'est une belle voiture."},
        {"word": "Aimer", "meaning": "To love", "example": "J'aime le français."},
        {"word": "Fleur", "meaning": "Flower", "example": "La fleur est rouge."},
        {"word": "Penser", "meaning": "To think", "example": "Je pense donc je suis."},
        {"word": "Vie", "meaning": "Life", "example": "La vie est belle."}
    ]
    try:
        url = "https://french-words-api.vercel.app/api/random"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            return data.get("word"), data.get("meaning"), data.get("example")
    except Exception:
        pass
    
    item = random.choice(auto_words)
    return item["word"], item["meaning"], item["example"]

async def send_word():
    bot = Bot(token=TOKEN)
    word, meaning, example = get_random_french_word()
    
    message = (
        f"🇫🇷 *Automated Daily French Word*\n\n"
        f"🗣 *Word:* {word}\n"
        f"💡 *Meaning:* {meaning}\n"
        f"📝 *Example:* _{example}_"
    )
    
    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
    print(f"Sent Automated Word: {word}")

def job():
    asyncio.run(send_word())

# Har 1 ghante mein automatic word bhejne ka schedule
schedule.every(1).hours.do(job)

# SELF-PING FUNCTION: Render ko sleep mode se bachane ke liye
def keep_alive():
    while True:
        time.sleep(600)  # Har 10 minute baad chalega
        try:
            requests.get(RENDER_URL, timeout=10)
            print("Self-ping successful! Server kept awake.")
        except Exception as e:
            print(f"Self-ping failed: {e}")

# Background Thread mein Self-Ping start karna
threading.Thread(target=keep_alive, daemon=True).start()

print("Automated French Vocab Bot active ho gaya hai...")

# Initial test execution (Deploy hotay hi test message bhejega)
job()

while True:
    schedule.run_pending()
    time.sleep(1)
