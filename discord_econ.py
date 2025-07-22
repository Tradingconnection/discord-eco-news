import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

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
    return f"Résumé : {len(lines)} annonces.\n" + "\n".join(lines[:3])

def send_to_discord(msg):
    payload = {"content": msg}
    requests.post(WEBHOOK_URL, json=payload)

def main():
    now = datetime.utcnow().strftime("%H:%M")
    news = get_economic_news()
    if now == "08:00":
        send_to_discord(f"📢 **Annonces économiques (08h00 UTC)**\n{news}")
    elif now == "20:00":
        summary = summarize(news)
        send_to_discord(f"📊 **Résumé (20h00 UTC)**\n{summary}")

if __name__ == "__main__":
    main()
