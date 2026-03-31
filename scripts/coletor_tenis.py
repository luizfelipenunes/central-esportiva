import json
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Optional
from zoneinfo import ZoneInfo

import requests

TZ_BRASIL = ZoneInfo("America/Sao_Paulo")
CURRENT_YEAR = datetime.now().year

BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "data" / "db"
CACHE_FILE = DB_DIR / "tennis_cache.json"

API_BASE = "https://tennisapi1.p.rapidapi.com/api/tennis"

BRASILEIROS = [
    "fonseca", "monteiro", "meligeni", "haddad", "haddad maia",
    "seyboth", "seyboth wild"
]

TOURNAMENT_KEYWORDS = [
    "australian open", "roland garros", "wimbledon", "us open",
    "miami open", "indian wells", "madrid", "rome", "montreal",
    "cincinnati", "shanghai", "paris", "toronto", "beijing",
    "dubai", "doha", "italian open", "french open",
    "masters 1000", "wta 1000", "grand slam"
]

# =========================
# UTIL
# =========================

def get_headers() -> dict:
    api_key = os.environ.get("TENNIS_API_KEY2", "").strip()
    return {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "tennisapi1.p.rapidapi.com"
    }

def ler_cache() -> dict:
    try:
        if not CACHE_FILE.exists():
            return {}
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[tenis] erro ao ler cache: {e}")
        return {}

def salvar_cache(dados: dict):
    try:
        DB_DIR.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[tenis] erro ao salvar cache: {e}")

def dias_ate_data(data_str: str) -> int:
    try:
        data = datetime.strptime(data_str[:10], "%Y-%m-%d").replace(tzinfo=TZ_BRASIL)
        agora = datetime.now(TZ_BRASIL)
        return (data.date() - agora.date()).days
    except:
        return 999

def destacar_tenis(titulo: str) -> bool:
    t = titulo.lower()
    return any(br in t for br in BRASILEIROS)

def inferir_status_tenis(timestamp: Optional[int], resultado: Optional[str]) -> str:
    if resultado:
        return "resultado"
    if timestamp:
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        if dt < datetime.now(timezone.utc):
            return "resultado"
    return "futuro"

def eh_torneio_relevante(nome: str, ut_nome: str, priority: int) -> bool:
    # Check by priority — Grand Slams and Masters 1000 have lower priority numbers (higher importance)
    if priority <= 2:
        return True

    # Check by unique tournament name
    combined = (nome + " " + ut_nome).lower()
    return any(k in combined for k in TOURNAMENT_KEYWORDS)

def deve_buscar_fixtures(cache: dict) -> bool:
    ultima = cache.get("fixtures_updated", "")
    if not ultima:
        return True
    try:
        ultima_dt = datetime.fromisoformat(ultima)
        horas = (datetime.now(timezone.utc) - ultima_dt).total_seconds() / 3600
        return horas >= 12
    except:
        return True

def deve_buscar_calendario(cache: dict) -> bool:
    ultima = cache.get("calendar_updated", "")
    if not ultima:
        return True
    try:
        ultima_dt = datetime.fromisoformat(ultima)
        dias = (datetime.now(timezone.utc) - ultima_dt).total_seconds() / 86400
        return dias >= 7
    except:
        return True

def deve_buscar_rankings(cache: dict) -> bool:
    ultima = cache.get("rankings_updated", "")
    if not ultima:
        return True
    try:
        ultima_dt = datetime.fromisoformat(ultima)
        horas = (datetime.now(timezone.utc) - ultima_dt).total_seconds() / 3600
        return horas >= 24
    except:
        return True

# =========================
# API CALLS
# =========================

def fetch_events_by_date(day: int, month: int, year: int) -> List[dict]:
    url = f"{API_BASE}/events/{day}/{month}/{year}"
    try:
        r = requests.get(url, headers=get_headers(), timeout=30)
        print(f"[tenis] events {day}/{month}/{year}: status {r.status_code}")
        if r.status_code != 200:
            return []
        data = r.json()
        events = (
            data.get("events") or
            data.get("data") or
            (data if isinstance(data, list) else [])
        )
        return events if isinstance(events, list) else []
    except Exception as e:
        print(f"[tenis] erro events {day}/{month}/{year}: {e}")
        return []

def fetch_rankings(tour: str) -> List[dict]:
    url = f"{API_BASE}/rankings/{tour}"
    try:
        r = requests.get(url, headers=get_headers(), timeout=30)
        print(f"[tenis] rankings {tour}: status {r.status_code}")
        if r.status_code != 200:
            return []
        data = r.json()
        rankings = (
            data.get("rankings") or
            data.get("data") or
            (data if isinstance(data, list) else [])
        )
        if rankings:
            print(f"[tenis] ranking exemplo: {json.dumps(rankings[0], indent=2)[:300]}")
        return rankings if isinstance(rankings, list) else []
    except Exception as e:
        print(f"[tenis] erro rankings {tour}: {e}")
        return []

def fetch_calendar(month: int, year: int) -> List[dict]:
    url = f"{API_BASE}/calendar/{month}/{year}"
    try:
        r = requests.get(url, headers=get_headers(), timeout=30)
        print(f"[tenis] calendar {month}/{year}: status {r.status_code}")
        if r.status_code != 200:
            return []
        data = r.json()
        tournaments = (
            data.get("uniqueTournaments") or
            data.get("tournaments") or
            data.get("data") or
            (data if isinstance(data, list) else [])
        )
        return tournaments if isinstance(tournaments, list) else []
    except Exception as e:
        print(f"[tenis] erro calendar {month}/{year}: {e}")
        return []

# =========================
# PARSE
# =========================

def extrair_top_jogadores(cache: dict) -> List[str]:
    jogadores = set(BRASILEIROS)
    for tour in ["rankings_atp", "rankings_wta"]:
        entries = cache.get(tour, [])[:10]
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            player = entry.get("player") or entry.get("team") or entry
            if isinstance(player, dict):
                nome = (
                    player.get("name", "") or
                    player.get("shortName", "") or ""
                )
                if nome:
                    jogadores.add(nome.lower())
    print(f"[tenis] top jogadores: {list(jogadores)}")
    return list(jogadores)

def parse_event(event: dict, top_jogadores: List[str]) -> Optional[dict]:
    try:
        # Get tournament info
        tournament = event.get("tournament") or {}
        if isinstance(tournament, dict):
            torneio_nome = tournament.get("name", "") or ""
            ut = tournament.get("uniqueTournament", {})
            ut_nome = ut.get("name", "") if isinstance(ut, dict) else ""
            cat = tournament.get("category", {})
            priority = int(cat.get("priority", 99)) if isinstance(cat, dict) else 99
        else:
            torneio_nome = str(tournament)
            ut_nome = ""
            priority = 99

        # Use uniqueTournament name if available, otherwise tournament name
        nome_display = ut_nome or torneio_nome

        if not eh_torneio_relevante(torneio_nome, ut_nome, priority):
            return None

        # Get player names
        home = event.get("homeTeam") or event.get("home") or {}
        away = event.get("awayTeam") or event.get("away") or {}

        if isinstance(home, dict):
            nome_home = home.get("name", "") or home.get("shortName", "") or ""
        else:
            nome_home = str(home)

        if isinstance(away, dict):
            nome_away = away.get("name", "") or away.get("shortName", "") or ""
        else:
            nome_away = str(away)

        if not nome_home or not nome_away:
            return None

        titulo = f"{nome_home} vs {nome_away}"
        titulo_lower = titulo.lower()

        # Only top players or Brazilians
        relevante = any(j in titulo_lower for j in top_jogadores)
        if not relevante:
            return None

        # Date from timestamp
        timestamp = event.get("startTimestamp") or event.get("timestamp")
        if not timestamp:
            return None

        data_utc = datetime.fromtimestamp(int(timestamp), tz=timezone.utc)

        # Result
        resultado = None
        status = event.get("status", {})
        status_type = ""
        if isinstance(status, dict):
            status_type = str(status.get("type", "") or status.get("code", "")).lower()

        if "finished" in status_type or "ended" in status_type or status_type == "ft":
            home_score = event.get("homeScore", {})
            away_score = event.get("awayScore", {})
            if isinstance(home_score, dict) and isinstance(away_score, dict):
                h = home_score.get("current", "") or home_score.get("display", "")
                a = away_score.get("current", "") or away_score.get("display", "")
                if h != "" and a != "":
                    resultado = f"{h} x {a}"

        # Round
        rodada = None
        round_info = event.get("roundInfo") or event.get("round") or {}
        if isinstance(round_info, dict):
            rodada = round_info.get("name") or round_info.get("round")

        return {
            "esporte": "Tênis",
            "competicao": nome_display,
            "titulo": titulo,
            "mandante": None,
            "visitante": None,
            "data_utc": data_utc.isoformat(),
            "status": inferir_status_tenis(int(timestamp), resultado),
            "resultado": resultado,
            "transmissao": "ESPN / Disney+",
            "destaque": destacar_tenis(titulo),
            "fonte": "tennisapi1",
            "rodada": str(rodada) if rodada else None,
            "estadio": None,
            "cidade": None,
            "uf": None,
        }
    except Exception as e:
        print(f"[tenis] erro ao parsear evento: {e}")
        return None

def criar_evento_calendario(torneio: dict) -> Optional[dict]:
    try:
        nome = torneio.get("name", "") or torneio.get("tournament", {}).get("name", "") or ""
        if not nome or not eh_torneio_relevante(nome, "", 99):
            return None

        start_ts = torneio.get("startDateTimestamp") or torneio.get("startTimestamp")
        end_ts = torneio.get("endDateTimestamp") or torneio.get("endTimestamp")

        if not start_ts:
            return None

        data_utc = datetime.fromtimestamp(int(start_ts), tz=timezone.utc)
        dias = (data_utc.date() - datetime.now(TZ_BRASIL).date()).days

        if dias < -1 or dias > 30:
            return None

        fim_info = ""
        if end_ts:
            fim_dt = datetime.fromtimestamp(int(end_ts), tz=timezone.utc)
            fim_info = f" até {fim_dt.strftime('%d/%m')}"

        return {
            "esporte": "Tênis",
            "competicao": nome,
            "titulo": f"🎾 {nome}{fim_info}",
            "mandante": None,
            "visitante": None,
            "data_utc": data_utc.isoformat(),
            "status": "futuro" if dias >= 0 else "resultado",
            "resultado": None,
            "transmissao": "ESPN / Disney+",
            "destaque": False,
            "fonte": "tennisapi1 / calendar",
            "rodada": None,
            "estadio": None,
            "cidade": None,
            "uf": None,
        }
    except Exception as e:
        print(f"[tenis] erro ao criar evento calendário: {e}")
        return None

# =========================
# PRINCIPAL
# =========================

def gerar_tenis() -> List[dict]:
    print("[tenis] iniciando coleta...")
    cache = ler_cache()
    eventos = []
    agora_iso = datetime.now(timezone.utc).isoformat()
    agora = datetime.now(TZ_BRASIL)
    amanha = agora + timedelta(days=1)

    # Step 1 — Update rankings once a day
    if deve_buscar_rankings(cache):
        print("[tenis] atualizando rankings...")
        cache["rankings_atp"] = fetch_rankings("atp")
        time.sleep(1)
        cache["rankings_wta"] = fetch_rankings("wta")
        cache["rankings_updated"] = agora_iso
        time.sleep(1)

    top_jogadores = extrair_top_jogadores(cache)
    print(f"[tenis] monitorando {len(top_jogadores)} jogadores")

    # Step 2 — Fetch today and tomorrow events (twice a day)
    if deve_buscar_fixtures(cache):
        print(f"[tenis] buscando eventos de hoje e amanhã...")
        events_hoje = fetch_events_by_date(agora.day, agora.month, agora.year)
        time.sleep(1)
        events_amanha = fetch_events_by_date(amanha.day, amanha.month, amanha.year)

        todas = events_hoje + events_amanha
        cache["fixtures_hoje"] = todas
        cache["fixtures_updated"] = agora_iso
        print(f"[tenis] {len(todas)} eventos encontrados")

        # Debug — show unique tournaments
        torneios_vistos = {}
        for e in todas[:100]:
            t = e.get("tournament", {})
            nome = t.get("name", "")
            cat = t.get("category", {})
            cat_nome = cat.get("name", "")
            priority = cat.get("priority", "?")
            ut = t.get("uniqueTournament", {})
            ut_nome = ut.get("name", "") if isinstance(ut, dict) else ""
            chave = f"{nome} | {ut_nome} | {cat_nome} | priority={priority}"
            if chave not in torneios_vistos:
                torneios_vistos[chave] = True
                print(f"[tenis] torneio visto: {chave}")
    else:
        print("[tenis] usando cache de fixtures...")

    # Step 3 — Parse events
    todas = cache.get("fixtures_hoje", [])
    for event in todas:
        evento = parse_event(event, top_jogadores)
        if evento:
            eventos.append(evento)

    print(f"[tenis] {len(eventos)} partidas relevantes")

    # Step 4 — Fallback: calendar
    if len(eventos) == 0:
        print("[tenis] usando calendário como fallback...")

        if deve_buscar_calendario(cache):
            print("[tenis] atualizando calendário...")
            cal_este_mes = fetch_calendar(agora.month, agora.year)
            time.sleep(1)
            proximo_mes = agora + timedelta(days=31)
            cal_proximo_mes = fetch_calendar(proximo_mes.month, proximo_mes.year)
            cache["calendar"] = cal_este_mes + cal_proximo_mes
            cache["calendar_updated"] = agora_iso
            print(f"[tenis] calendário: {len(cache['calendar'])} torneios")

        for torneio in cache.get("calendar", []):
            evento = criar_evento_calendario(torneio)
            if evento:
                eventos.append(evento)
                print(f"[tenis] calendário: {evento['titulo']}")

    salvar_cache(cache)

    print(f"[tenis] total final: {len(eventos)} eventos")
    return eventos
