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

API_BASE = "https://tennis-api-atp-wta-itf.p.rapidapi.com/tennis/v2"

# Grand Slams and Masters 1000 category IDs
# ATP Masters 1000 = category 2, Grand Slams = category 1
# WTA 1000 = category 2, Grand Slams = category 1
TOURNAMENT_CATEGORIES = ["1", "2"]  # Grand Slam, Masters/WTA 1000

# Brazilian players to highlight
BRASILEIROS = [
    "fonseca", "monteiro", "meligeni", "haddad", "haddad maia",
    "silva", "seyboth", "seyboth wild"
]

# =========================
# UTIL
# =========================

def get_headers() -> dict:
    api_key = os.environ.get("TENNIS_RAPIDAPI_KEY", "")
    return {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "tennis-api-atp-wta-itf.p.rapidapi.com",
        "Content-Type": "application/json"
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

def hoje_str() -> str:
    return datetime.now(TZ_BRASIL).strftime("%Y-%m-%d")

def dias_ate_data(data_str: str) -> int:
    try:
        data = datetime.strptime(data_str[:10], "%Y-%m-%d").replace(tzinfo=TZ_BRASIL)
        agora = datetime.now(TZ_BRASIL)
        return (data.date() - agora.date()).days
    except:
        return 999

def destacar_tenis(titulo: str) -> bool:
    t = titulo.lower()
    for br in BRASILEIROS:
        if br in t:
            return True
    return False

def inferir_status_tenis(data_str: str, resultado: Optional[str]) -> str:
    if resultado:
        return "resultado"
    try:
        data_utc = datetime.fromisoformat(data_str)
        if data_utc < datetime.now(timezone.utc):
            return "resultado"
    except:
        pass
    return "futuro"

# =========================
# API CALLS
# =========================

def fetch_calendar() -> List[dict]:
    print("[tenis] buscando calendário...")
    url = f"{API_BASE}/tournament/calendar"
    params = {"year": str(CURRENT_YEAR)}
    try:
        r = requests.get(url, headers=get_headers(), params=params, timeout=30)
        print(f"[tenis] calendar status: {r.status_code}")
        data = r.json()
        tournaments = data.get("data", data.get("tournaments", data if isinstance(data, list) else []))
        print(f"[tenis] {len(tournaments)} torneios no calendário")
        return tournaments if isinstance(tournaments, list) else []
    except Exception as e:
        print(f"[tenis] erro ao buscar calendário: {e}")
        return []

def fetch_fixtures(tournament_id: str) -> List[dict]:
    print(f"[tenis] buscando fixtures do torneio {tournament_id}...")
    url = f"{API_BASE}/tournament/fixtures"
    params = {"tournamentId": tournament_id, "year": str(CURRENT_YEAR)}
    try:
        r = requests.get(url, headers=get_headers(), params=params, timeout=30)
        print(f"[tenis] fixtures status: {r.status_code}")
        data = r.json()
        fixtures = data.get("data", data.get("fixtures", data if isinstance(data, list) else []))
        return fixtures if isinstance(fixtures, list) else []
    except Exception as e:
        print(f"[tenis] erro ao buscar fixtures {tournament_id}: {e}")
        return []

def fetch_rankings(tour: str) -> List[dict]:
    print(f"[tenis] buscando ranking {tour}...")
    url = f"{API_BASE}/player/rankings"
    params = {"tour": tour, "limit": "10"}
    try:
        r = requests.get(url, headers=get_headers(), params=params, timeout=30)
        print(f"[tenis] ranking {tour} status: {r.status_code}")
        data = r.json()
        rankings = data.get("data", data.get("rankings", data if isinstance(data, list) else []))
        return rankings if isinstance(rankings, list) else []
    except Exception as e:
        print(f"[tenis] erro ao buscar ranking {tour}: {e}")
        return []

# =========================
# PARSE
# =========================

def extrair_top_jogadores(cache: dict) -> List[str]:
    jogadores = set()

    rankings_atp = cache.get("rankings_atp", [])
    rankings_wta = cache.get("rankings_wta", [])

    for r in rankings_atp + rankings_wta:
        nome = r.get("player", {}).get("name", "") or r.get("name", "")
        if nome:
            jogadores.add(nome.lower())

    for br in BRASILEIROS:
        jogadores.add(br)

    return list(jogadores)

def eh_torneio_relevante(torneio: dict) -> bool:
    categoria = str(torneio.get("category", {}).get("id", "") or torneio.get("categoryId", ""))
    nome = (torneio.get("name", "") or "").lower()

    if categoria in TOURNAMENT_CATEGORIES:
        return True

    # Fallback by name
    keywords = ["grand slam", "masters 1000", "wta 1000", "australian open",
                "roland garros", "wimbledon", "us open", "miami", "madrid",
                "rome", "montreal", "cincinnati", "shanghai", "paris",
                "indian wells", "toronto", "beijing", "dubai", "doha"]
    return any(k in nome for k in keywords)

def parse_fixture(fixture: dict, torneio_nome: str, top_jogadores: List[str]) -> Optional[dict]:
    try:
        # Extract player names
        home = fixture.get("home", {}) or {}
        away = fixture.get("away", {}) or {}

        nome_home = home.get("name", "") or home.get("player", {}).get("name", "") or ""
        nome_away = away.get("name", "") or away.get("player", {}).get("name", "") or ""

        if not nome_home or not nome_away:
            return None

        titulo = f"{nome_home} vs {nome_away}"

        # Check if involves top player or Brazilian
        titulo_lower = titulo.lower()
        relevante = any(j in titulo_lower for j in top_jogadores)
        if not relevante:
            return None

        # Date
        date_str = fixture.get("date", "") or fixture.get("startDate", "")
        if not date_str:
            return None

        try:
            data_utc = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except:
            return None

        # Result
        resultado = None
        score = fixture.get("score", "") or fixture.get("result", "")
        status_api = str(fixture.get("status", {}).get("name", "") or fixture.get("statusId", "")).lower()
        if score and ("finish" in status_api or "complete" in status_api or "played" in status_api):
            resultado = str(score)

        destaque = destacar_tenis(titulo)

        return {
            "esporte": "Tênis",
            "competicao": torneio_nome,
            "titulo": titulo,
            "mandante": None,
            "visitante": None,
            "data_utc": data_utc.isoformat(),
            "status": inferir_status_tenis(data_utc.isoformat(), resultado),
            "resultado": resultado,
            "transmissao": "ESPN / Disney+",
            "destaque": destaque,
            "fonte": "tennis-api-atp-wta-itf",
            "rodada": fixture.get("round", {}).get("name") or fixture.get("roundName"),
            "mandante": None,
            "visitante": None,
            "estadio": None,
            "cidade": None,
            "uf": None,
        }
    except Exception as e:
        print(f"[tenis] erro ao parsear fixture: {e}")
        return None

def criar_evento_torneio(torneio: dict) -> Optional[dict]:
    try:
        nome = torneio.get("name", "Torneio de Tênis")
        inicio_str = torneio.get("startDate", "") or torneio.get("dateFrom", "")
        fim_str = torneio.get("endDate", "") or torneio.get("dateTo", "")

        if not inicio_str:
            return None

        try:
            data_utc = datetime.fromisoformat(inicio_str.replace("Z", "+00:00"))
            if data_utc.tzinfo is None:
                data_utc = data_utc.replace(tzinfo=timezone.utc)
        except:
            # Try parsing as date only
            try:
                data_utc = datetime.strptime(inicio_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except:
                return None

        fim_info = f" até {fim_str[:10]}" if fim_str else ""

        return {
            "esporte": "Tênis",
            "competicao": nome,
            "titulo": f"🎾 {nome}{fim_info}",
            "mandante": None,
            "visitante": None,
            "data_utc": data_utc.isoformat(),
            "status": inferir_status_tenis(data_utc.isoformat(), None),
            "resultado": None,
            "transmissao": "ESPN / Disney+",
            "destaque": False,
            "fonte": "tennis-api-atp-wta-itf / calendar",
            "rodada": None,
            "estadio": torneio.get("venue", {}).get("name") if isinstance(torneio.get("venue"), dict) else None,
            "cidade": torneio.get("venue", {}).get("city") if isinstance(torneio.get("venue"), dict) else None,
            "uf": torneio.get("venue", {}).get("country") if isinstance(torneio.get("venue"), dict) else None,
        }
    except Exception as e:
        print(f"[tenis] erro ao criar evento torneio: {e}")
        return None

# =========================
# SMART CACHE LOGIC
# =========================

def deve_buscar_calendario(cache: dict) -> bool:
    ultima = cache.get("calendar_updated", "")
    if not ultima:
        return True
    dias = dias_ate_data(ultima)
    # Refresh calendar once a week
    return abs(dias) >= 7

def deve_buscar_rankings(cache: dict) -> bool:
    ultima = cache.get("rankings_updated", "")
    if not ultima:
        return True
    dias = dias_ate_data(ultima)
    return abs(dias) >= 1

def deve_buscar_fixtures(torneio: dict, cache: dict) -> bool:
    tid = str(torneio.get("id", ""))
    inicio_str = torneio.get("startDate", "") or torneio.get("dateFrom", "")
    fim_str = torneio.get("endDate", "") or torneio.get("dateTo", "")

    if not inicio_str:
        return False

    dias_inicio = dias_ate_data(inicio_str)
    dias_fim = dias_ate_data(fim_str) if fim_str else dias_inicio + 7

    # Tournament is over
    if dias_fim < -1:
        return False

    # Tournament hasn't started yet — try from 7 days before
    if dias_inicio > 7:
        return False

    # Check if we already have fixtures for this tournament today
    fixtures_cache = cache.get("fixtures", {})
    torneio_cache = fixtures_cache.get(tid, {})
    ultima_busca = torneio_cache.get("updated", "")

    if not ultima_busca:
        return True

    # During active tournament — fetch twice a day
    if dias_inicio <= 0 <= abs(dias_fim):
        ultima_dt = datetime.fromisoformat(ultima_busca)
        agora = datetime.now(timezone.utc)
        horas_desde_ultima = (agora - ultima_dt).total_seconds() / 3600
        return horas_desde_ultima >= 12

    # Pre-tournament countdown (1-7 days before) — fetch once a day
    ultima_dt = datetime.fromisoformat(ultima_busca)
    agora = datetime.now(timezone.utc)
    horas_desde_ultima = (agora - ultima_dt).total_seconds() / 3600
    return horas_desde_ultima >= 24

# =========================
# PRINCIPAL
# =========================

def gerar_tenis() -> List[dict]:
    print("[tenis] iniciando coleta inteligente...")
    cache = ler_cache()
    eventos = []
    agora_iso = datetime.now(timezone.utc).isoformat()

    # Step 1 — Update rankings if needed
    if deve_buscar_rankings(cache):
        print("[tenis] atualizando rankings...")
        cache["rankings_atp"] = fetch_rankings("ATP")
        cache["rankings_wta"] = fetch_rankings("WTA")
        cache["rankings_updated"] = agora_iso
        time.sleep(1)

    top_jogadores = extrair_top_jogadores(cache)
    print(f"[tenis] monitorando {len(top_jogadores)} jogadores")

    # Step 2 — Update calendar if needed
    if deve_buscar_calendario(cache):
        print("[tenis] atualizando calendário...")
        torneios = fetch_calendar()
        relevantes = [t for t in torneios if eh_torneio_relevante(t)]
        cache["calendar"] = relevantes
        cache["calendar_updated"] = agora_iso
        print(f"[tenis] {len(relevantes)} torneios relevantes encontrados")
        time.sleep(1)

    torneios = cache.get("calendar", [])

    if not cache.get("fixtures"):
        cache["fixtures"] = {}

    # Step 3 — Fetch fixtures for relevant tournaments
    for torneio in torneios:
        tid = str(torneio.get("id", ""))
        nome = torneio.get("name", "Torneio")
        inicio_str = torneio.get("startDate", "") or torneio.get("dateFrom", "")

        if not tid or not inicio_str:
            continue

        if deve_buscar_fixtures(torneio, cache):
            print(f"[tenis] buscando fixtures: {nome}...")
            fixtures = fetch_fixtures(tid)

            cache["fixtures"][tid] = {
                "updated": agora_iso,
                "data": fixtures
            }
            time.sleep(1)

        # Parse fixtures into events
        fixtures_data = cache.get("fixtures", {}).get(tid, {}).get("data", [])

        if fixtures_data:
            for fixture in fixtures_data:
                evento = parse_fixture(fixture, nome, top_jogadores)
                if evento:
                    eventos.append(evento)
        else:
            # No fixtures yet — show tournament as a single event
            evento_torneio = criar_evento_torneio(torneio)
            if evento_torneio:
                dias = dias_ate_data(inicio_str)
                if -30 <= dias <= 30:
                    eventos.append(evento_torneio)

    salvar_cache(cache)

    print(f"[tenis] total: {len(eventos)} eventos")
    return eventos
