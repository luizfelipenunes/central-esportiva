import json
import datetime as dt
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

API_KEY = "3"
BASE_URL = "https://www.thesportsdb.com/api/v1/json/{}/".format(API_KEY)
TZ = ZoneInfo("America/Sao_Paulo")
NOW = dt.datetime.now(TZ)
END_DATE = NOW + dt.timedelta(days=120)

COMPETITIONS = [
    {"id": "4370", "nome": "Formula 1", "esporte": "Automobilismo", "temporadas": ["2026"]},
    {"id": "4486", "nome": "Formula 2", "esporte": "Automobilismo", "temporadas": ["2026"]},
    {"id": "4407", "nome": "MotoGP", "esporte": "Automobilismo", "temporadas": ["2026"]},
    {"id": "4373", "nome": "IndyCar", "esporte": "Automobilismo", "temporadas": ["2026"]},
    {"id": "4413", "nome": "WEC", "esporte": "Automobilismo", "temporadas": ["2026"]},
    {"id": "4488", "nome": "IMSA", "esporte": "Automobilismo", "temporadas": ["2026"]},
    {"id": "4351", "nome": "Brasileirão", "esporte": "Futebol", "temporadas": ["2026"]},
    {"id": "4725", "nome": "Copa do Brasil", "esporte": "Futebol", "temporadas": ["2026"]},
    {"id": "4501", "nome": "Libertadores", "esporte": "Futebol", "temporadas": ["2026"]},
    {"id": "4724", "nome": "Sul-Americana", "esporte": "Futebol", "temporadas": ["2026"]},
    {"id": "4480", "nome": "Champions League", "esporte": "Futebol", "temporadas": ["2025-2026", "2026"]},
    {"id": "4429", "nome": "Copa do Mundo", "esporte": "Futebol", "temporadas": ["2026"]},
]

TIMES = [
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

def fetch_json(endpoint, params=None):
    url = BASE_URL + endpoint
    if params:
        url += "?" + urlencode(params)
    req = Request(url, headers={"User-Agent": "CentralEsportiva/1.0"})
    with urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))

def parse_event_datetime(event):
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
        parsed = dt.datetime.fromisoformat("{}T{}".format(date_value, time_value[:8]))
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed.astimezone(TZ)
    except Exception:
        return None

def dentro_do_periodo(event_dt):
    if not event_dt:
        return False
    return NOW <= event_dt <= END_DATE

def formatar_data(event_dt):
    return event_dt.strftime("%d/%m/%Y %H:%M")

def eh_vasco(event):
    texto = " ".join([
        event.get("strEvent", ""),
        event.get("strHomeTeam", ""),
        event.get("strAwayTeam", "")
    ]).lower()
    return "vasco" in texto

def inferir_transmissao(nome_competicao, esporte, titulo):
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

def montar_titulo(event, competition_name, esporte):
    home = event.get("strHomeTeam") or ""
    away = event.get("strAwayTeam") or ""
    event_name = event.get("strEvent") or ""

    if esporte in ["Futebol", "NBA", "NFL"] and home and away:
        return "{} x {} ({})".format(home, away, competition_name)

    return "{} — {}".format(competition_name, event_name) if event_name else competition_name

def prioridade(event, esporte):
    if eh_vasco(event):
        return 1
    if esporte == "Automobilismo":
        return 2
    if esporte in ["NBA", "NFL", "Tenis"]:
        return 3
    return 4

def normalizar_evento(event, competition_name, esporte):
    event_dt = parse_event_datetime(event)
    if not dentro_do_periodo(event_dt):
        return None

    titulo = montar_titulo(event, competition_name, esporte)

    return {
        "esporte": esporte,
        "titulo": titulo,
        "data": formatar_data(event_dt),
        "transmissao": inferir_transmissao(competition_name, esporte, titulo),
        "prioridade": prioridade(event, esporte),
        "timestamp": event_dt.isoformat(),
    }

def buscar_eventos_liga(comp):
    eventos = []
    for temporada in comp["temporadas"]:
        try:
            data = fetch_json("eventsseason.php", {"id": comp["id"], "s": temporada})
            lista = data.get("events") or []
            for event in lista:
                normalizado = normalizar_evento(event, comp["nome"], comp["esporte"])
                if normalizado:
                    eventos.append(normalizado)
        except Exception as exc:
            print("Erro em {} ({}): {}".format(comp["nome"], temporada, exc))
    return eventos

def buscar_eventos_time(team_name, esporte):
    try:
        search = fetch_json("searchteams.php", {"t": team_name})
        teams = search.get("teams") or []
        if not teams:
            return []

        team_id = teams[0].get("idTeam")
        if not team_id:
            return []

        data = fetch_json("eventsnext.php", {"id": team_id})
        lista = data.get("events") or []

        eventos = []
        for event in lista:
            normalizado = normalizar_evento(event, team_name, esporte)
            if normalizado:
                normalizado["titulo"] = normalizado["titulo"].replace(" ({})".format(team_name), "")
                eventos.append(normalizado)
        return eventos
    except Exception as exc:
        print("Erro em time {}: {}".format(team_name, exc))
        return []

def remover_duplicados(eventos):
    vistos = set()
    resultado = []
    for event in eventos:
        chave = (event["titulo"], event["timestamp"])
        if chave in vistos:
            continue
        vistos.add(chave)
        resultado.append(event)
    return resultado

def main():
    eventos = []

    for comp in COMPETITIONS:
        eventos.extend(buscar_eventos_liga(comp))

    for time in TIMES:
        eventos.extend(buscar_eventos_time(time["nome"], time["esporte"]))

    eventos = remover_duplicados(eventos)
    eventos.sort(key=lambda e: (e["prioridade"], e["timestamp"]))

    for event in eventos:
        event.pop("timestamp", None)

    with open("eventos.json", "w", encoding="utf-8") as f:
        json.dump(eventos, f, ensure_ascii=False, indent=2)

    print("{} eventos salvos em eventos.json".format(len(eventos)))

if __name__ == "__main__":
    main()
