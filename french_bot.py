import os
import json
import time
import html
import random
import asyncio
import threading
import requests
import schedule
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Bot

# ==========================================
# 1. HEALTH CHECK SERVER (Render ke liye)
# ==========================================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot status: OK & Running")

    def log_message(self, format, *args):
        pass

def run_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(('0.0.0.0', port), HealthHandler).serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# ==========================================
# 2. CONFIG (Sab env vars se)
# ==========================================
TOKEN         = os.environ["BOT_TOKEN"]
CHAT_ID       = os.environ["CHAT_ID"]
RENDER_URL    = os.environ.get("RENDER_URL", "")
GIST_ID       = os.environ["GIST_ID"]
GITHUB_TOKEN  = os.environ["GITHUB_TOKEN"]

GIST_API = f"https://api.github.com/gists/{GIST_ID}"
GH_HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# ==========================================
# 3. PERSISTENCE - GitHub Gist
# ==========================================
def load_sent_words():
    try:
        r = requests.get(GIST_API, headers=GH_HEADERS, timeout=10)
        content = r.json()["files"]["sent.json"]["content"]
        data = json.loads(content)
        print(f"[GIST] Loaded {len(data)} sent words")
        return set(w.lower() for w in data)
    except Exception as e:
        print(f"[GIST] Load failed: {e}")
        return set()

def save_sent_words(sent_set):
    try:
        requests.patch(
            GIST_API,
            headers=GH_HEADERS,
            json={"files": {"sent.json": {
                "content": json.dumps(sorted(sent_set), ensure_ascii=False)
            }}},
            timeout=10
        )
    except Exception as e:
        print(f"[GIST] Save failed: {e}")

SENT_WORDS = load_sent_words()

# ==========================================
# 4. FALLBACK DICTIONARY
# ==========================================
VOCAB_DATABASE = [
    {"word": "Bonjour", "meaning": "Hello / Good morning", "example": "Bonjour, comment allez-vous ?"},
    {"word": "Merci", "meaning": "Thank you", "example": "Merci beaucoup pour votre aide."},
    {"word": "Monde", "meaning": "World", "example": "Le monde est grand."},
    {"word": "Soleil", "meaning": "Sun", "example": "Le soleil brille aujourd'hui."},
    {"word": "Nuit", "meaning": "Night", "example": "Bonne nuit et doux rêves."},
    {"word": "Voiture", "meaning": "Car", "example": "C'est une belle voiture bleue."},
    {"word": "Aimer", "meaning": "To love / like", "example": "J'aime apprendre le français."},
    {"word": "Fleur", "meaning": "Flower", "example": "La fleur est très jolie."},
    {"word": "Penser", "meaning": "To think", "example": "Je pense donc je suis."},
    {"word": "Vie", "meaning": "Life", "example": "La vie est belle et pleine de surprises."},
    {"word": "Maison", "meaning": "House", "example": "Ma maison est grande."},
    {"word": "Amis", "meaning": "Friends", "example": "J'aime passer du temps avec mes amis."},
    {"word": "Livre", "meaning": "Book", "example": "Je lis un bon livre."},
    {"word": "Eau", "meaning": "Water", "example": "Je bois de l'eau fraîche."},
    {"word": "Temps", "meaning": "Time / Weather", "example": "Le temps passe vite."},
    {"word": "Travail", "meaning": "Work", "example": "J'aime mon travail."},
    {"word": "Jour", "meaning": "Day", "example": "Passez une bonne journée !"},
    {"word": "Ciel", "meaning": "Sky", "example": "Le ciel est bleu clair."},
    {"word": "Musique", "meaning": "Music", "example": "J'écoute de la musique."},
    {"word": "Ville", "meaning": "City", "example": "C'est une grande ville."},
    {"word": "Bibliothèque", "meaning": "Library", "example": "Je vais à la bibliothèque pour lire."},
    {"word": "Aventure", "meaning": "Adventure", "example": "La vie est une grande aventure."},
    {"word": "Papillon", "meaning": "Butterfly", "example": "Le papillon vole dans le jardin."},
    {"word": "Étoile", "meaning": "Star", "example": "L'étoile brille dans le ciel nocturne."},
    {"word": "Horloge", "meaning": "Clock", "example": "L'horloge tourne silencieusement."},
    {"word": "Voyage", "meaning": "Journey / Travel", "example": "J'aime faire un long voyage."},
    {"word": "Sagesse", "meaning": "Wisdom", "example": "La sagesse vient avec l'expérience."},
    {"word": "Boulangerie", "meaning": "Bakery", "example": "J'achète du pain à la boulangerie."},
    {"word": "Chocolat", "meaning": "Chocolate", "example": "Le chocolat chaud est délicieux."},
    {"word": "Fenêtre", "meaning": "Window", "example": "J'ouvre la fenêtre ce matin."},
    {"word": "Arbre", "meaning": "Tree", "example": "L'arbre est très grand dans la cour."},
    {"word": "Chien", "meaning": "Dog", "example": "Le chien joue joyeusement."},
    {"word": "Chat", "meaning": "Cat", "example": "Le chat dort paisiblement."},
    {"word": "Pain", "meaning": "Bread", "example": "Le pain frais sent très bon."},
    {"word": "Café", "meaning": "Coffee", "example": "Un bon café chaud le matin."},
    {"word": "Forêt", "meaning": "Forest", "example": "Nous marchons dans la forêt."},
    {"word": "Rivière", "meaning": "River", "example": "La rivière coule doucement."},
    {"word": "Montagne", "meaning": "Mountain", "example": "La montagne est couverte de neige."},
    {"word": "Océan", "meaning": "Ocean", "example": "L'océan est calme aujourd'hui."},
    {"word": "Nuage", "meaning": "Cloud", "example": "Un nuage blanc traverse le ciel."},
    {"word": "Pluie", "meaning": "Rain", "example": "La pluie tombe doucement."},
    {"word": "Neige", "meaning": "Snow", "example": "La neige couvre les toits."},
    {"word": "Vent", "meaning": "Wind", "example": "Le vent souffle fort."},
    {"word": "Feu", "meaning": "Fire", "example": "Le feu brûle dans la cheminée."},
    {"word": "Terre", "meaning": "Earth / Land", "example": "La terre est notre maison."},
    {"word": "Lune", "meaning": "Moon", "example": "La lune éclaire la nuit."},
    {"word": "Espoir", "meaning": "Hope", "example": "L'espoir fait vivre."},
    {"word": "Rêve", "meaning": "Dream", "example": "J'ai fait un beau rêve."},
    {"word": "Bonheur", "meaning": "Happiness", "example": "Le bonheur est dans les petites choses."},
    {"word": "Silence", "meaning": "Silence", "example": "Le silence est parfois précieux."},
]

# ==========================================
# 5. LIVE API FETCH (English -> French)
# ==========================================
def fetch_live_word():
    try:
        r1 = requests.get(
            "https://random-word-api.herokuapp.com/word?number=1",
            timeout=8
        )
        en_word = r1.json()[0]

        r2 = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": en_word, "langpair": "en|fr"},
            timeout=8
        )
        data = r2.json()

        if data.get("responseStatus") == 200:
            fr_word = data["responseData"]["translatedText"].strip()
            if (fr_word and
                fr_word.lower() != en_word.lower() and
                1 < len(fr_word) < 40):
                return {
                    "word": fr_word,
                    "meaning": en_word,
                    "example": f"Exemple : le mot « {fr_word} » est utilisé ici."
                }
    except Exception as e:
        print(f"[API] Live fetch failed: {e}")
    return None

# ==========================================
# 6. MAIN PICKER
# ==========================================
def get_unique_word():
    for _ in range(3):
        item = fetch_live_word()
        if item and item["word"].lower() not in SENT_WORDS:
            SENT_WORDS.add(item["word"].lower())
            save_sent_words(SENT_WORDS)
            return item["word"], item["meaning"], item["example"]

    remaining = [w for w in VOCAB_DATABASE
                 if w["word"].lower() not in SENT_WORDS]

    if not remaining:
        print("[INFO] All words exhausted, resetting history...")
        SENT_WORDS.clear()
        save_sent_words(SENT_WORDS)
        remaining = VOCAB_DATABASE

    item = random.choice(remaining)
    SENT_WORDS.add(item["word"].lower())
    save_sent_words(SENT_WORDS)
    return item["word"], item["meaning"], item["example"]

# ==========================================
# 7. TELEGRAM DELIVERY
# ==========================================
async def send_word():
    bot = Bot(token=TOKEN)
    word, meaning, example = get_unique_word()

    message = (
        f"🇫🇷 <b>French Word of the Hour</b>\n\n"
        f"🗣 <b>Word:</b> {html.escape(word)}\n"
        f"💡 <b>Meaning:</b> {html.escape(meaning)}\n"
        f"📝 <b>Example:</b> <i>{html.escape(example)}</i>\n\n"
        f"<code>Total sent: {len(SENT_WORDS)}</code>"
    )

    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="HTML")
    print(f"[SENT] {word}")

def job():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(send_word())
    except Exception as e:
        print(f"[JOB ERROR] {e}")
    finally:
        loop.close()

# ==========================================
# 8. SCHEDULER + KEEP ALIVE
# ==========================================
schedule.every(1).hours.do(job)

def keep_alive():
    while True:
        time.sleep(300)
        if RENDER_URL:
            try:
                requests.get(RENDER_URL, timeout=10)
            except Exception:
                pass

threading.Thread(target=keep_alive, daemon=True).start()

# ==========================================
# 9. START
# ==========================================
if __name__ == "__main__":
    print(f"🤖 Bot initialized. {len(SENT_WORDS)} words already sent.")
    print("⏰ First message will be sent in 1 hour (no startup spam).")
    while True:
        schedule.run_pending()
        time.sleep(10)
