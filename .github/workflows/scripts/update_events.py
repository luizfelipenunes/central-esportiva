import json
import datetime as dt
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

API_KEY = "3"
BASE_URL = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/"
TZ = ZoneInfo("America/Sao_Paulo")
NOW = dt.datetime.now(TZ)
HORIZON_DAYS = 120
END_DATE = NOW + dt.timedelta(days=HORIZON_DAYS)

COMPETITIONS = [
    {"id": "4370", "nome": "Formula 1", "esporte": "Automobilismo", "seasons": ["2026"]},
    {"id": "4486", "nome": "Formula 2", "esporte": "Automobilismo", "seasons": ["2026"]},
    {"id": "4407", "nome": "MotoGP", "esporte": "Automobilismo", "seasons": ["2026"]},
    {"id": "4373", "nome": "IndyCar", "esporte": "Automobilismo", "seasons": ["2026"]},
    {"id": "4413", "nome": "WEC", "esporte": "Automobilismo", "seasons": ["2026"]},
    {"id": "4488", "nome": "IMSA", "esporte": "Automobilismo", "seasons": ["2026"]},
    {"id": "4351", "nome": "Brasileirão", "esporte": "Futebol", "seasons": ["2026"]},
    {"id": "4725", "nome": "Copa do Brasil", "esporte": "Futebol", "seasons": ["2026"]},
    {"id": "4501", "nome": "Libertadores", "esporte": "Futebol", "seasons": ["2026"]},
    {"id": "4724", "nome": "Sul-Americana", "esporte": "Futebol", "seasons": ["2026"]},
    {"id": "4480", "nome": "Champions League", "esporte": "Futebol", "seasons": ["2025-2026", "2026"]},
    {"id": "4429", "nome": "Copa do Mundo", "esporte": "Futebol", "seasons": ["2026"]},
    {"id": "4464", "nome": "ATP World Tour", "esporte": "Tenis", "seasons": ["2026"]},
]

TEAM_TARGETS = [
    {"nome": "Boston Celtics", "esporte": "NBA"},
    {"nome": "Seattle Seahawks", "esporte": "NFL"},
]

GRAND_SLAMS = [
    "Australian Open",
    "Roland Garros",
    "French Open",
    "Wimbledon",
    "US Open",
]

def fetch_json(endpoint: str, params: dict | None = None) -> dict:
    url = BASE_URL + endpoint
    if params:
        url += "?" + urlencode(params)
    req = Request(url, headers={"User-Agent": "CentralEsportiva/1.0"})
    with urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))

def parse_event_datetime(event: dict) -> dt.datetime | None:
    ts = event.get("strTimestamp")
    if ts:
        try:
            parsed = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=dt.timezone.utc)
            return parsed.astimezone(TZ)
        except Exception:
            pass

    date_value = event.get("dateEvent") or event.get("dateEventLocal")
    time_value = event.get("strTime") or "00:00:00"

    if not date_value:
        return None

    try:
        parsed = dt.datetime.fromisoformat(f"{date_value}T{time_value[:8]}")
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed.astimezone(TZ)
    except Exception:
        return None

def within_horizon(event_dt: dt.datetime | None) -> bool:
    if not event_dt:
        return False
    return NOW <= event_dt <= END_DATE

def format_dt(event_dt: dt.datetime) -> str:
    return event_dt.strftime("%d/%m/%Y %H:%M")

def is_vasco_event(event: dict) -> bool:
    text = " ".join([
        event.get("strEvent", ""),
        event.get("strHomeTeam", ""),
        event.get("strAwayTeam", ""),
    ]).lower()
    return "vasco" in text

def infer_transmissao(nome_competicao: str, esporte: str, titulo: str) -> str:
    nome = nome_competicao.lower()
    titulo_lower = titulo.lower()

    if "formula 1" in nome:
        return "Globo / SporTV / F1TV"
    if "formula 2" in nome:
        return "SporTV / F1TV"
    if "motogp" in nome:
        return "ESPN / Disney+"
    if "indycar" in nome:
        return "ESPN / Disney+"
    if nome == "wec":
        return "BandSports / YouTube"
    if nome == "imsa":
        return "IMSA TV / YouTube"

    if esporte == "NBA":
        return "ESPN / SporTV / NBA League Pass"
    if esporte == "NFL":
        return "ESPN / SporTV / NFL Game Pass"
    if esporte == "Tenis":
        return "ESPN / Disney+"

    if "copa do mundo" in nome:
        return "CazéTV / Globo / SporTV"
    if "champions" in nome:
        return "TNT Sports / Max / SBT"
    if "libertadores" in nome:
        return "Globo / ESPN / Disney+"
    if "sul-americana" in nome:
        return "ESPN / Disney+"
    if "copa do brasil" in nome:
        return "Globo / SporTV / Prime Video"
    if "brasileirão" in nome or "brasileirao" in nome:
        return "Globo / SporTV / Premiere"

    if "vasco" in titulo_lower:
        return "Globo / SporTV / Premiere"

    return "A confirmar"

def build_title(event: dict, competition_name: str, esporte: str) -> str:
    home = event.get("strHomeTeam") or ""
    away = event.get("strAwayTeam") or ""
    event_name = event.get("strEvent") or ""

    if esporte in {"Futebol", "NBA", "NFL", "Tenis"} and home and away:
        return f"{home} x {away} ({competition_name})"

    if competition_name == "ATP World Tour":
        return event_name

    return f"{competition_name} — {event_name}" if event_name else competition_name

def prioridade_evento(event: dict, esporte: str) -> int:
    if is_vasco_event(event):
        return 1
    if esporte == "Automobilismo":
        return 2
    if esporte in {"NBA", "NFL", "Tenis"}:
        return 3
    return 4

def normalize_event(event: dict, competition_name: str, esporte: str) -> dict | None:
    event_dt = parse_event_datetime(event)
    if not within_horizon(event_dt):
        return None

    titulo = build_title(event, competition_name, esporte)

    if competition_name == "ATP World Tour":
        title_text = titulo.lower()
        if ("joão fonseca" not in title_text and "joao fonseca" not in title_text
                and not any(gs.lower() in title_text for gs in GRAND_SLAMS)):
            return None

    prioridade = prioridade_evento(event, esporte)

    return {
        "esporte": esporte,
        "titulo": titulo,
        "data": format_dt(event_dt),
        "transmissao": infer_transmissao(competition_name, esporte, titulo),
        "prioridade": prioridade,
        "timestamp": event_dt.isoformat(),
    }

def fetch_league_events(competition: dict) -> list[dict]:
    all_events = []
    for season in competition["seasons"]:
        try:
            data = fetch_json("eventsseason.php", {"id": competition["id"], "s": season})
            events = data.get("events") or []
            for event in events:
                normalized = normalize_event(event, competition["nome"], competition["esporte"])
                if normalized:
                    all_events.append(normalized)
        except Exception as exc:
            print(f"Erro em {competition['nome']} ({season}): {exc}")
    return all_events

def fetch_team_events(team_name: str, esporte: str) -> list[dict]:
    try:
        search = fetch_json("searchteams.php", {"t": team_name})
        teams = search.get("teams") or []
        if not teams:
            return []

        team_id = teams[0].get("idTeam")
        if not team_id:
            return []

        data = fetch_json("eventsnext.php", {"id": team_id})
        events = data.get("events") or []

        result = []
        for event in events:
            normalized = normalize_event(event, team_name, esporte)
            if normalized:
                normalized["titulo"] = normalized["titulo"].replace(f"({team_name})", "")
                result.append(normalized)
        return result
    except Exception as exc:
        print(f"Erro em time {team_name}: {exc}")
        return []

def dedupe(events: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for event in events:
        key = (event["titulo"], event["timestamp"])
        if key in seen:
            continue
        seen.add(key)
        result.append(event)
    return result

def main():
    events = []

    for competition in COMPETITIONS:
        events.extend(fetch_league_events(competition))

    for team in TEAM_TARGETS:
        events.extend(fetch_team_events(team["nome"], team["esporte"]))

    events = dedupe(events)
    events.sort(key=lambda e: (e["prioridade"], e["timestamp"]))

    for event in events:
        event.pop("timestamp", None)

    with open("eventos.json", "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

    print(f"{len(events)} eventos salvos em eventos.json")

if __name__ == "__main__":
    main()
