import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

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
import asyncio
import schedule
import time
import requests
from telegram import Bot

TOKEN = "8952477275:AAHde9By_daqvVvXgmAai5np-6LreGywpWs"
CHAT_ID = "7690989029"

# Internet se random daily French word fetch karne ka function
def get_random_french_word():
    try:
        # Free Random Word API
        response = requests.get("https://random-word-api.herokuapp.com/word?number=1")
        if response.status_code == 200:
            raw_word = response.json()[0]
            
            # French Dictionary API se meaning aur details fetch karna
            dict_res = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{raw_word}")
            
            # French words ki free API fallback list (Automated Random Fetch)
            url = f"https://french-words-api.vercel.app/api/random"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                return data.get("word"), data.get("meaning"), data.get("example")
    except Exception:
        pass
    
    # Backup auto-generator list agar internet slow ho
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

# Har 1 ghante mein automatic naya random word bhejega
schedule.every(1).hours.do(job)

print("Automated French Vocab Bot active ho gaya hai...")

while True:
    schedule.run_pending()
    time.sleep(1)
