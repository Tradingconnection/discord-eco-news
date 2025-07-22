import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from collections import defaultdict

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
FEED_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"

def fetch_events():
    try:
        response = requests.get(FEED_URL, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Erreur de requête : {e}")
        return []

    soup = BeautifulSoup(response.content, "xml")
    items = soup.find_all("item")
    today = datetime.utcnow().date()

    print(f"📆 Date actuelle UTC : {today}")
    print(f"📄 Nombre total d'éléments XML : {len(items)}")

    filtered_events = []
    for item in items:
        try:
            pub_date_raw = item.pubDate.text.strip()
            pub_date = datetime.strptime(pub_date_raw, "%a, %d %b %Y %H:%M:%S %z")
            item_date = pub_date.date()

            print(f"🕒 {pub_date_raw} → {item_date} | Titre: {item.title.text.strip()}")

            if item_date != today:
                continue  # Filtre par date UTC

            title = item.title.text.strip()
            impact = item.find("field", {"name": "impact"}).text.strip()
            currency = item.find("field", {"name": "currency"}).text.strip()
            country = item.find("field", {"name": "country"}).text.strip()

            filtered_events.append(f"{currency} – {title} ({impact})")

        except Exception as e:
            print(f"⚠️ Erreur parsing : {e}")
            continue

    print(f"\n✅ Événements du jour trouvés : {len(filtered_events)}")
    for e in filtered_events:
        print("📌", e)

    return filtered_events

def send_to_discord(message):
    if not DISCORD_WEBHOOK:
        print("❌ Webhook Discord manquant.")
        return

    response = requests.post(DISCORD_WEBHOOK, json={"content": message})
    if response.status_code != 204:
        print(f"❌ Erreur Discord : {response.status_code} – {response.text}")
    else:
        print("✅ Message envoyé avec succès.")

def main():
    print("🔍 Récupération brute des événements...")
    events = fetch_events()

    if events:
        message = "**🧪 DEBUG – Événements détectés aujourd’hui :**\n" + "\n".join(events)
    else:
        message = "❌ Aucun événement trouvé dans le XML pour aujourd’hui."

    send_to_discord(message)

if __name__ == "__main__":
    main()
