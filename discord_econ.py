import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from collections import defaultdict

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

FEED_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"

IMPACT_LEVELS = {
    "High": "🔴",
    "Medium": "🟡"
}

CURRENCY_FLAGS = {
    "USD": "🇺🇸",
    "EUR": "🇪🇺",
    "GBP": "🇬🇧",
    "JPY": "🇯🇵",
    "AUD": "🇦🇺",
    "NZD": "🇳🇿",
    "CAD": "🇨🇦",
    "CHF": "🇨🇭",
    "CNY": "🇨🇳"
}

def fetch_events():
    resp = requests.get(FEED_URL)
    soup = BeautifulSoup(resp.content, "xml")
    items = soup.find_all("item")

    today = datetime.utcnow().date()
    events = []

    for item in items:
        try:
            date_str = item.pubDate.text.strip()
            pub_date = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
            if pub_date.date() != today:
                continue

            impact = item.find("field", {"name": "impact"}).text.strip()
            if impact not in IMPACT_LEVELS:
                continue

            title = item.title.text.strip()
            country = item.find("field", {"name": "country"}).text.strip()
            currency = item.find("field", {"name": "currency"}).text.strip()
            actual = item.find("field", {"name": "actual"}).text.strip()
            forecast = item.find("field", {"name": "forecast"}).text.strip()
            previous = item.find("field", {"name": "previous"}).text.strip()
            time = pub_date.strftime("%H:%M")

            events.append({
                "impact": impact,
                "title": title,
                "currency": currency,
                "country": country,
                "actual": actual,
                "forecast": forecast,
                "previous": previous,
                "time": time
            })
        except Exception:
            continue

    return events

def summarize_events(events):
    grouped = defaultdict(list)

    for event in events:
        currency = event["currency"]
        grouped[currency].append(event)

    summary_lines = []

    for currency, evts in grouped.items():
        flag = CURRENCY_FLAGS.get(currency, "")
        header = f"{flag} {event['country']} ({currency})"
        summary_lines.append(header)

        for e in evts:
            info = f"{e['title']}\n"
            if e['actual'] or e['forecast'] or e['previous']:
                info += f"Résultat : {e['actual']} (prévu : {e['forecast']}, précédent : {e['previous']})\n"
            else:
                info += "(pas de données chiffrées disponibles)\n"

            # Résumé simple
            if e['impact'] == "High":
                insight = "→ Impact potentiellement important sur les marchés."
            elif e['impact'] == "Medium":
                insight = "→ Peut influencer modérément la devise concernée."
            else:
                insight = ""

            summary_lines.append(info + insight + "\n")

    if not summary_lines:
        return "Aucun événement économique significatif à résumer aujourd’hui."

    final = "**📊 Résumé économique du jour**\n\n" + "\n".join(summary_lines)
    return final

def send_to_discord(message):
    if not DISCORD_WEBHOOK:
        print("Webhook Discord non défini.")
        return

    data = {"content": message}
    response = requests.post(DISCORD_WEBHOOK, json=data)

    if response.status_code != 204:
        print(f"Erreur envoi Discord : {response.status_code} - {response.text}")

def main():
    events = fetch_events()
    summary = summarize_events(events)
    send_to_discord(summary)

if __name__ == "__main__":
    main()
