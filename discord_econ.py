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

def safe_get(field):
    return field.text.strip() if field and field.text else "—"

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

            impact = safe_get(item.find("field", {"name": "impact"}))
            if impact not in {"High", "Medium"}:
                continue

            event = {
                "title": safe_get(item.title),
                "currency": safe_get(item.find("field", {"name": "currency"})),
                "country": safe_get(item.find("field", {"name": "country"})),
                "impact": impact,
                "actual": safe_get(item.find("field", {"name": "actual"})),
                "forecast": safe_get(item.find("field", {"name": "forecast"})),
                "previous": safe_get(item.find("field", {"name": "previous"})),
                "time": pub_date.strftime("%H:%M")
            }
            filtered_events.append(event)
        except Exception as e:
            print(f"⚠️ Erreur parsing événement : {e}")
            continue

    print(f"✅ Événements valides trouvés : {len(filtered_events)}")
    return filtered_events

def summarize_events(events):
    if not events:
        return "📊 Aucun événement économique significatif à résumer aujourd’hui."

    grouped = defaultdict(list)
    for e in events:
        grouped[e["currency"]].append(e)

    lines = ["**📊 Résumé économique du jour**\n"]
    for currency, evts in grouped.items():
        flag = CURRENCY_FLAGS.get(currency, "🌍")
        lines.append(f"{flag} **{evts[0]['country']} ({currency})**")

        for e in evts:
            bloc = f"**{e['title']}** à {e['time']}\n"
            if e['actual'] != "—" or e['forecast'] != "—" or e['previous'] != "—":
                bloc += f"Résultat : {e['actual']} (prévu : {e['forecast']}, précédent : {e['previous']})\n"
            bloc += "→ "
            bloc += "📈 Fort impact" if e['impact'] == "High" else "📉 Impact modéré"
            lines.append(bloc + "\n")

    return "\n".join(lines)

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
    print("🔍 Récupération des événements économiques du jour...")
    events = fetch_events()
    print("🧠 Création du résumé...")
    summary = summarize_events(events)
    print("📤 Envoi du message à Discord...")
    send_to_discord(summary)

if __name__ == "__main__":
    main()
