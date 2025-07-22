import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
from collections import defaultdict

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

def get_economic_news():
    """
    Scrape les annonces économiques depuis ForexFactory et retourne une liste enrichie.
    """
    url = "https://www.forexfactory.com/calendar"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    rows = soup.select("tr.calendar__row")
    events = []

    for row in rows:
        try:
            time = row.select_one("td.calendar__time")
            event = row.select_one("td.calendar__event")
            impact = row.select_one("td.calendar__impact span")
            country = row.select_one("td.calendar__flag")
            actual = row.select_one("td.calendar__actual")
            forecast = row.select_one("td.calendar__forecast")
            previous = row.select_one("td.calendar__previous")

            if not (time and event and impact and country):
                continue

            impact_text = impact['title']
            emoji = "🔴" if "High" in impact_text else "🟡" if "Medium" in impact_text else "🟢"

            events.append({
                "heure": time.text.strip(),
                "pays": country['title'],
                "event": event.text.strip(),
                "impact": impact_text,
                "emoji": emoji,
                "résultat": actual.text.strip() if actual else "-",
                "prévision": forecast.text.strip() if forecast else "-",
                "précédent": previous.text.strip() if previous else "-"
            })

        except Exception as e:
            print("Erreur parsing ligne :", e)

    return events

def get_flag_emoji(pays):
    flags = {
        "United States": "🇺🇸",
        "Eurozone": "🇪🇺",
        "Germany": "🇩🇪",
        "France": "🇫🇷",
        "United Kingdom": "🇬🇧",
        "Japan": "🇯🇵",
        "Canada": "🇨🇦",
        "Australia": "🇦🇺",
        "Switzerland": "🇨🇭",
        "China": "🇨🇳",
        "New Zealand": "🇳🇿"
    }
    return flags.get(pays, "🌍")

def format_news(events):
    """
    Formate les événements économiques groupés par pays.
    """
    if not events:
        return "Aucune annonce économique aujourd’hui."

    grouped = defaultdict(list)
    for e in events:
        ligne = (
            f'{e["emoji"]} {e["heure"]} | {e["event"]}\n'
            f'Résultat : {e["résultat"]} | Prévu : {e["prévision"]} | Précédent : {e["précédent"]}'
        )
        grouped[e["pays"]].append(ligne)

    message = "📢 **Annonces économiques - 08h00 UTC**\n\n"
    for pays, lignes in grouped.items():
        flag = get_flag_emoji(pays)
        message += f"{flag} **{pays}**\n" + "\n".join(lignes) + "\n\n"

    return message.strip()

def summarize(events):
    """
    (Temporaire) Résume les événements par les 3 les plus importants.
    À remplacer à l'étape suivante.
    """
    if not events:
        return "Aucune donnée à résumer."

    high_impact = [e for e in events if "High" in e["impact"]]
    summary = f"🔴 High Impact ({len(high_impact)})\n"

    for e in high_impact[:3]:
        summary += (
            f"- {e['heure']} | {get_flag_emoji(e['pays'])} {e['pays']} | {e['event']}\n"
            f"Résultat : {e['résultat']} | Prévu : {e['prévision']} | Précédent : {e['précédent']}\n"
        )

    return summary.strip()

def send_to_discord(msg):
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
    now = datetime.utcnow().strftime("%H:%M")
    print(f"⏱ Heure actuelle UTC : {now}")

    events = get_economic_news()

    if now == "08:00":
        msg = format_news(events)
        send_to_discord(msg)

    elif now == "20:00":
        summary = summarize(events)
        send_to_discord(f"📊 **Résumé économique (20h00 UTC)**\n{summary}")

    else:
        print("🕗 Pas d'envoi prévu à cette heure.")

if __name__ == "__main__":
    main()
