import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

# Webhook récupéré depuis les secrets GitHub
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

def get_economic_news():
    url = "https://www.forexfactory.com/calendar"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    rows = soup.select("tr.calendar__row")
    today_news = []
    for row in rows:
        time = row.select_one("td.calendar__time")
        event = row.select_one("td.calendar__event")
        impact = row.select_one("td.calendar__impact span")
        if not (time and event and impact):
            continue
        today_news.append(f"- {time.text.strip()} | {impact['title']} | {event.text.strip()}")

    return "\n".join(today_news) or "Aucune annonce économique détectée aujourd’hui."

def summarize(news):
    lines = news.splitlines()
    if not lines:
        return "Aucune donnée à résumer."
    return f"Résumé automatique ({len(lines)} lignes) :\n" + "\n".join(lines[:3])

def send_to_discord(msg):
    if not WEBHOOK_URL:
        print("⚠️ Webhook Discord non défini.")
        return
    payload = {"content": msg}
    response = requests.post(WEBHOOK_URL, json=payload)
    if response.status_code != 204:
        print(f"❌ Erreur Discord : {response.status_code} - {response.text}")
    else:
        print("✅ Message envoyé sur Discord")

def main():
    print("🔍 Récupération des annonces économiques...")
    news = get_economic_news()
    print("📢 Envoi des annonces...")
    send_to_discord(f"📢 **Annonces économiques (TEST MANUEL)**\n{news}")

    print("🧠 Génération du résumé...")
    summary = summarize(news)
    print("📊 Envoi du résumé...")
    send_to_discord(f"📊 **Résumé économique (TEST MANUEL)**\n{summary}")

if __name__ == "__main__":
    main()
