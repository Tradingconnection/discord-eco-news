import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from collections import defaultdict

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
FEED_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"

CURRENCY_FLAGS = {
    "USD": "🇺🇸", "EUR": "🇪🇺", "GBP": "🇬🇧", "JPY": "🇯🇵",
    "AUD": "🇦🇺", "NZD": "🇳🇿", "CAD": "🇨🇦", "CHF": "🇨🇭", "CNY": "🇨🇳"
}

def fetch_events():
    try:
        response = requests.get(FEED_URL, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Erreur de requête : {e}")
        return []

    soup = BeautifulSoup(response.content, "xml")
    items = soup.find_all("item")
    today = datetime.utcnow().date()

    filtered_events = []
    for item in items:
        try:
            pub_date = datetime.strptime(item.pubDate.text.strip(), "%a, %d %b %Y %H:%M:%S %z")
            if pub_date.date() != today:
                continue

            impact = item.find("field", {"name": "impact"}).text.strip()
            if impact not in {"High", "Medium"}:
                continue

            event = {
                "time": pub_date.strftime("%H:%M"),
                "title": item.title.text.strip(),
                "currency": item.find("field", {"name": "currency"}).text.strip(),
                "country": item.find("field", {"name": "country"}).text.strip(),
                "impact": impact,
                "actual": item.find("field", {"name": "actual"}).text.strip(),
                "forecast": item.find("field", {"name": "forecast"}).text.strip(),
                "previous": item.find("field", {"name": "previous"}).text.strip()
            }
            filtered_events.append(event)

        except Exception as e:
            print(f"⚠️ Erreur de parsing : {e}")
            continue

    return filtered_events

def build_summary(events):
    if not events:
        return "❌ Aucun événement économique significatif trouvé aujourd’hui."

    grouped = defaultdict(list)
    for e in events:
        grouped[e["currency"]].append(e)

    lines = ["📊 **Résumé économique (08h00 UTC)**\n"]
    for currency, evts in grouped.items():
        flag = CURRENCY_FLAGS.get(currency, "🌍")
        country = evts[0]["country"]
        lines.append(f"**{flag} {country} ({currency})**")

        for e in evts:
            detail = f"**{e['time']}** | {e['title']}"
            if e["actual"] or e["forecast"] or e["previous"]:
                detail += f"\nRésultat : {e['actual']} (prévu : {e['forecast']}, précédent : {e['previous']})"
            lines.append(detail + "\n")

    return "\n".join(lines)

def send_to_discord(message):
    if not DISCORD_WEBHOOK:
        print("❌ Webhook Discord manquant.")
        return

    response = requests.post(DISCORD_WEBHOOK, json={"content": message})
    if response.status_code != 204:
        print(f"❌ Erreur Discord : {response.status_code} – {response.text}")
    else:
        print("✅ Message envoyé à Discord.")

def main():
    print("🔍 Vérification des événements économiques pour aujourd’hui...")
    events = fetch_events()
    message = build_summary(events)
    send_to_discord(message)

if __name__ == "__main__":
    main()
