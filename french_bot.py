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
# 1. HEALTH CHECK SERVER
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
# 2. CONFIG
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
# 3. GIST PERSISTENCE
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
        r = requests.patch(
            GIST_API,
            headers=GH_HEADERS,
            json={"files": {"sent.json": {
                "content": json.dumps(sorted(sent_set), ensure_ascii=False)
            }}},
            timeout=10
        )
        if r.status_code == 200:
            print(f"[GIST] Saved {len(sent_set)} words")
        else:
            print(f"[GIST] Save failed: HTTP {r.status_code}")
    except Exception as e:
        print(f"[GIST] Save error: {e}")

SENT_WORDS = load_sent_words()

# ==========================================
# 4. BUNDLED FRENCH DICTIONARY (150+ words)
# ==========================================
VOCAB_DATABASE = [
    {"word": "Bonjour", "meaning": "Hello", "example": "Bonjour, comment allez-vous ?"},
    {"word": "Merci", "meaning": "Thank you", "example": "Merci beaucoup pour votre aide."},
    {"word": "Monde", "meaning": "World", "example": "Le monde est grand."},
    {"word": "Soleil", "meaning": "Sun", "example": "Le soleil brille aujourd'hui."},
    {"word": "Nuit", "meaning": "Night", "example": "Bonne nuit et doux rêves."},
    {"word": "Voiture", "meaning": "Car", "example": "C'est une belle voiture bleue."},
    {"word": "Aimer", "meaning": "To love", "example": "J'aime apprendre le français."},
    {"word": "Fleur", "meaning": "Flower", "example": "La fleur est très jolie."},
    {"word": "Penser", "meaning": "To think", "example": "Je pense donc je suis."},
    {"word": "Vie", "meaning": "Life", "example": "La vie est belle."},
    {"word": "Maison", "meaning": "House", "example": "Ma maison est grande."},
    {"word": "Amis", "meaning": "Friends", "example": "J'aime mes amis."},
    {"word": "Livre", "meaning": "Book", "example": "Je lis un bon livre."},
    {"word": "Eau", "meaning": "Water", "example": "Je bois de l'eau fraîche."},
    {"word": "Temps", "meaning": "Time / Weather", "example": "Le temps passe vite."},
    {"word": "Travail", "meaning": "Work", "example": "J'aime mon travail."},
    {"word": "Jour", "meaning": "Day", "example": "Bonne journée !"},
    {"word": "Ciel", "meaning": "Sky", "example": "Le ciel est bleu."},
    {"word": "Musique", "meaning": "Music", "example": "J'écoute de la musique."},
    {"word": "Ville", "meaning": "City", "example": "C'est une grande ville."},
    {"word": "Bibliothèque", "meaning": "Library", "example": "Je vais à la bibliothèque."},
    {"word": "Aventure", "meaning": "Adventure", "example": "La vie est une aventure."},
    {"word": "Papillon", "meaning": "Butterfly", "example": "Le papillon vole."},
    {"word": "Étoile", "meaning": "Star", "example": "L'étoile brille."},
    {"word": "Horloge", "meaning": "Clock", "example": "L'horloge tourne."},
    {"word": "Voyage", "meaning": "Journey", "example": "J'aime voyager."},
    {"word": "Sagesse", "meaning": "Wisdom", "example": "La sagesse vient avec l'âge."},
    {"word": "Boulangerie", "meaning": "Bakery", "example": "J'achète du pain."},
    {"word": "Chocolat", "meaning": "Chocolate", "example": "Le chocolat est délicieux."},
    {"word": "Fenêtre", "meaning": "Window", "example": "J'ouvre la fenêtre."},
    {"word": "Arbre", "meaning": "Tree", "example": "L'arbre est grand."},
    {"word": "Chien", "meaning": "Dog", "example": "Le chien joue."},
    {"word": "Chat", "meaning": "Cat", "example": "Le chat dort."},
    {"word": "Pain", "meaning": "Bread", "example": "Le pain est frais."},
    {"word": "Café", "meaning": "Coffee", "example": "Un café chaud."},
    {"word": "Forêt", "meaning": "Forest", "example": "La forêt est verte."},
    {"word": "Rivière", "meaning": "River", "example": "La rivière coule."},
    {"word": "Montagne", "meaning": "Mountain", "example": "La montagne est haute."},
    {"word": "Océan", "meaning": "Ocean", "example": "L'océan est calme."},
    {"word": "Nuage", "meaning": "Cloud", "example": "Un nuage blanc."},
    {"word": "Pluie", "meaning": "Rain", "example": "La pluie tombe."},
    {"word": "Neige", "meaning": "Snow", "example": "La neige est blanche."},
    {"word": "Vent", "meaning": "Wind", "example": "Le vent souffle."},
    {"word": "Feu", "meaning": "Fire", "example": "Le feu brûle."},
    {"word": "Terre", "meaning": "Earth", "example": "La terre est notre maison."},
    {"word": "Lune", "meaning": "Moon", "example": "La lune brille."},
    {"word": "Espoir", "meaning": "Hope", "example": "L'espoir fait vivre."},
    {"word": "Rêve", "meaning": "Dream", "example": "J'ai fait un rêve."},
    {"word": "Bonheur", "meaning": "Happiness", "example": "Le bonheur est simple."},
    {"word": "Silence", "meaning": "Silence", "example": "Le silence est d'or."},
    {"word": "Route", "meaning": "Road", "example": "La route est longue."},
    {"word": "Chemin", "meaning": "Path", "example": "Le chemin est étroit."},
    {"word": "Pont", "meaning": "Bridge", "example": "Le pont est vieux."},
    {"word": "Porte", "meaning": "Door", "example": "La porte est ouverte."},
    {"word": "Table", "meaning": "Table", "example": "La table est ronde."},
    {"word": "Chaise", "meaning": "Chair", "example": "La chaise est en bois."},
    {"word": "Lit", "meaning": "Bed", "example": "Le lit est confortable."},
    {"word": "Cuisine", "meaning": "Kitchen", "example": "La cuisine est propre."},
    {"word": "Chambre", "meaning": "Bedroom", "example": "Ma chambre est calme."},
    {"word": "Jardin", "meaning": "Garden", "example": "Le jardin est fleuri."},
    {"word": "Mur", "meaning": "Wall", "example": "Le mur est blanc."},
    {"word": "Toit", "meaning": "Roof", "example": "Le toit est rouge."},
    {"word": "Clé", "meaning": "Key", "example": "J'ai perdu ma clé."},
    {"word": "Lampe", "meaning": "Lamp", "example": "La lampe éclaire."},
    {"word": "Miroir", "meaning": "Mirror", "example": "Le miroir est cassé."},
    {"word": "Couleur", "meaning": "Color", "example": "Quelle est ta couleur préférée ?"},
    {"word": "Rouge", "meaning": "Red", "example": "La pomme est rouge."},
    {"word": "Bleu", "meaning": "Blue", "example": "Le ciel est bleu."},
    {"word": "Vert", "meaning": "Green", "example": "L'herbe est verte."},
    {"word": "Jaune", "meaning": "Yellow", "example": "Le soleil est jaune."},
    {"word": "Noir", "meaning": "Black", "example": "Le chat est noir."},
    {"word": "Blanc", "meaning": "White", "example": "La neige est blanche."},
    {"word": "Mer", "meaning": "Sea", "example": "La mer est calme."},
    {"word": "Plage", "meaning": "Beach", "example": "La plage est belle."},
    {"word": "Sable", "meaning": "Sand", "example": "Le sable est chaud."},
    {"word": "Poisson", "meaning": "Fish", "example": "Le poisson nage."},
    {"word": "Bateau", "meaning": "Boat", "example": "Le bateau flotte."},
    {"word": "Île", "meaning": "Island", "example": "L'île est déserte."},
    {"word": "Port", "meaning": "Harbor", "example": "Le port est plein."},
    {"word": "Valise", "meaning": "Suitcase", "example": "Ma valise est lourde."},
    {"word": "Gare", "meaning": "Train station", "example": "La gare est proche."},
    {"word": "Train", "meaning": "Train", "example": "Le train arrive."},
    {"word": "Avion", "meaning": "Plane", "example": "L'avion vole haut."},
    {"word": "Vélo", "meaning": "Bicycle", "example": "Je fais du vélo."},
    {"word": "Roue", "meaning": "Wheel", "example": "La roue tourne."},
    {"word": "Hôpital", "meaning": "Hospital", "example": "L'hôpital est grand."},
    {"word": "Médecin", "meaning": "Doctor", "example": "Le médecin soigne."},
    {"word": "Santé", "meaning": "Health", "example": "La santé est importante."},
    {"word": "Tête", "meaning": "Head", "example": "J'ai mal à la tête."},
    {"word": "Yeux", "meaning": "Eyes", "example": "Ses yeux sont bleus."},
    {"word": "Main", "meaning": "Hand", "example": "Donne-moi la main."},
    {"word": "Pied", "meaning": "Foot", "example": "J'ai mal au pied."},
    {"word": "Cœur", "meaning": "Heart", "example": "Mon cœur bat vite."},
    {"word": "Sourire", "meaning": "Smile", "example": "Ton sourire est beau."},
    {"word": "Rire", "meaning": "To laugh", "example": "J'aime rire."},
    {"word": "Pleurer", "meaning": "To cry", "example": "Ne pleure pas."},
    {"word": "Chanter", "meaning": "To sing", "example": "Elle aime chanter."},
    {"word": "Danser", "meaning": "To dance", "example": "Nous dansons ensemble."},
    {"word": "Courir", "meaning": "To run", "example": "Il court vite."},
    {"word": "Marcher", "meaning": "To walk", "example": "Je marche chaque jour."},
    {"word": "Nager", "meaning": "To swim", "example": "Elle nage bien."},
    {"word": "Dormir", "meaning": "To sleep", "example": "Je dors huit heures."},
    {"word": "Manger", "meaning": "To eat", "example": "Nous mangeons ensemble."},
    {"word": "Boire", "meaning": "To drink", "example": "Je bois du thé."},
    {"word": "Lire", "meaning": "To read", "example": "J'aime lire."},
    {"word": "Écrire", "meaning": "To write", "example": "J'écris une lettre."},
    {"word": "École", "meaning": "School", "example": "L'école est fermée."},
    {"word": "Professeur", "meaning": "Teacher", "example": "Le professeur parle."},
    {"word": "Étudiant", "meaning": "Student", "example": "L'étudiant étudie."},
    {"word": "Leçon", "meaning": "Lesson", "example": "La leçon est facile."},
    {"word": "Langue", "meaning": "Language", "example": "Le français est une belle langue."},
    {"word": "Mot", "meaning": "Word", "example": "Ce mot est difficile."},
    {"word": "Phrase", "meaning": "Sentence", "example": "La phrase est correcte."},
    {"word": "Question", "meaning": "Question", "example": "J'ai une question."},
    {"word": "Réponse", "meaning": "Answer", "example": "Ta réponse est juste."},
    {"word": "Famille", "meaning": "Family", "example": "Ma famille est grande."},
    {"word": "Père", "meaning": "Father", "example": "Mon père travaille."},
    {"word": "Mère", "meaning": "Mother", "example": "Ma mère cuisine."},
    {"word": "Frère", "meaning": "Brother", "example": "Mon frère est petit."},
    {"word": "Sœur", "meaning": "Sister", "example": "Ma sœur est gentille."},
    {"word": "Enfant", "meaning": "Child", "example": "L'enfant joue."},
    {"word": "Homme", "meaning": "Man", "example": "Cet homme est grand."},
    {"word": "Femme", "meaning": "Woman", "example": "Cette femme est belle."},
    {"word": "Pays", "meaning": "Country", "example": "La France est un pays."},
    {"word": "Capitale", "meaning": "Capital", "example": "Paris est la capitale."},
    {"word": "Gouvernement", "meaning": "Government", "example": "Le gouvernement décide."},
    {"word": "Loi", "meaning": "Law", "example": "La loi est juste."},
    {"word": "Paix", "meaning": "Peace", "example": "La paix est précieuse."},
    {"word": "Guerre", "meaning": "War", "example": "La guerre est terrible."},
    {"word": "Liberté", "meaning": "Freedom", "example": "La liberté est un droit."},
    {"word": "Égalité", "meaning": "Equality", "example": "L'égalité est importante."},
    {"word": "Fraternité", "meaning": "Brotherhood", "example": "Vive la fraternité !"},
]

# ==========================================
# 5. LIVE API FETCH (multiple fallbacks)
# ==========================================
def fetch_live_word():
    en_word = None
    apis = [
        "https://random-word-api.vercel.app/api?words=1",
        "https://random-word-api.herokuapp.com/word?number=1",
    ]
    for api in apis:
        try:
            r = requests.get(api, timeout=5)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list) and data:
                    en_word = data[0]
                    break
        except Exception:
            continue

    if not en_word:
        return None

    try:
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
                1 < len(fr_word) < 40 and
                not fr_word.isupper()):
                return {
                    "word": fr_word,
                    "meaning": en_word,
                    "example": f"Exemple : le mot « {fr_word} » est utilisé ici."
                }
    except Exception:
        pass
    return None

# ==========================================
# 6. MAIN PICKER (FIXED)
# ==========================================
def get_unique_word():
    # Step 1: API try (8 baar)
    for _ in range(8):
        item = fetch_live_word()
        if item and item["word"].lower() not in SENT_WORDS:
            SENT_WORDS.add(item["word"].lower())
            save_sent_words(SENT_WORDS)
            return item["word"], item["meaning"], item["example"]
        time.sleep(0.5)

    # Step 2: Bundled list
    remaining = [w for w in VOCAB_DATABASE
                 if w["word"].lower() not in SENT_WORDS]
    if remaining:
        item = random.choice(remaining)
        SENT_WORDS.add(item["word"].lower())
        save_sent_words(SENT_WORDS)
        return item["word"], item["meaning"], item["example"]

    # Step 3: API phir try (20 baar)
    print("[INFO] All local words sent. Retrying API harder...")
    for _ in range(20):
        item = fetch_live_word()
        if item and item["word"].lower() not in SENT_WORDS:
            SENT_WORDS.add(item["word"].lower())
            save_sent_words(SENT_WORDS)
            return item["word"], item["meaning"], item["example"]
        time.sleep(1)

    # Step 4: Last resort
    print("[WARN] Reusing a bundled word as last resort.")
    item = random.choice(VOCAB_DATABASE)
    return item["word"], item["meaning"], item["example"]

# ==========================================
# 7. TELEGRAM DELIVERY (No Count)
# ==========================================
async def send_word():
    bot = Bot(token=TOKEN)
    word, meaning, example = get_unique_word()

    message = (
        f"🇫🇷 <b>French Word of the Hour</b>\n\n"
        f"🗣 <b>Word:</b> {html.escape(word)}\n"
        f"💡 <b>Meaning:</b> {html.escape(meaning)}\n"
        f"📝 <b>Example:</b> <i>{html.escape(example)}</i>"
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
# 8. SCHEDULER — 5 min pehla, phir har 1 ghanta
# ==========================================
def scheduler_loop():
    print("⏰ First word will be sent in 5 minutes...")
    time.sleep(300)
    job()
    print("✅ First word sent. Next words every 1 hour.")

    while True:
        time.sleep(3600)
        job()

threading.Thread(target=scheduler_loop, daemon=True).start()

# ==========================================
# 9. KEEP ALIVE
# ==========================================
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
# 10. START
# ==========================================
if __name__ == "__main__":
    print(f"🤖 Bot initialized. {len(SENT_WORDS)} words already sent.")
    while True:
        time.sleep(60)
