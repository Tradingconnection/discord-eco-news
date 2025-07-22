import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

# 🔐 Récupération du webhook depuis les secrets GitHub
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

def get_economic_news():
    """
    Scrape les annonces économiques depuis ForexFactory.
    """
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
    """
    Résume les premières lignes des annonces du jour.
    """
    lines = news.splitlines()
    if not lines:
        return "Aucune donnée à résumer."
    return f"Résumé automatique ({len(lines)} lignes) :\n" + "\n".join(lines[:3])

def send_to_discord(msg):
    """
    Envoie un message via le webhook Discord.
    """
    if not WEBHOOK_URL:
        print("❌ Webhook Discord non défini.")
        return

    payload = {"content": msg}
    response = requests.post(WEBHOOK_URL, json=payload)

    if response.status_code != 204:
        print(f"❌ Erreur Discord : {response.status_code} - {response.text}")
    else:
        print("✅ Message envoyé sur Discord")

def main():
    """
    Exécute l’envoi en fonction de l’heure UTC (08h ou 20h).
    """
    now = datetime.utcnow().strftime("%H:%M")
    print(f"⏱ Heure actuelle UTC : {now}")
    
    news = get_economic_news()

    if now == "08:00":
        print("📢 Envoi des annonces économiques...")
        send_to_discord(f"📢 **Annonces économiques (08h00 UTC)**\n{news}")

    elif now == "20:00":
        print("📊 Envoi du résumé économique...")
        summary = summarize(news)
        send_to_discord(f"📊 **Résumé économique (20h00 UTC)**\n{summary}")

    else:
        print("🕗 Pas d'envoi prévu à cette heure.")

if __name__ == "__main__":
    main()
