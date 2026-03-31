import json
import os
import time
from datetime import datetime, timezone
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

BRASILEIROS = [
    "fonseca", "monteiro", "meligeni", "haddad", "haddad maia",
    "silva", "seyboth", "seyboth wild"
]

TOURNAMENT_KEYWORDS = [
    "grand slam", "masters 1000", "wta 1000", "australian open",
    "roland garros", "wimbledon", "us open", "miami", "madrid",
    "rome", "montreal", "cincinnati", "shanghai", "paris",
    "indian wells", "toronto", "beijing", "dubai", "doha"
]

# =========================
# UTIL
# =========================

def get_headers() -> dict:
    api_key = os.environ.get("TENNIS_RAPIDAPI_KEY", "").strip()
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

def fetch_calendar(tour: str) -> List[dict]:
    print(f"[tenis] buscando calendário {tour}...")
    url = f"{API_BASE}/{tour}/tournament/calendar/{CURRENT_YEAR}"
    try:
        r = requests.get(url, headers=get_headers(), timeout=30)
        print(f"[tenis] calendar {tour} status: {r.status_code}")
        if r.status_code != 200:
            return []
        data = r.json()
        tournaments = (
            data.get("data") or
            data.get("tournaments") or
            data.get("results") or
            (data if isinstance(data, list) else [])
        )
        print(f"[tenis] {tour}: {len(tournaments)} torneios")
        return tournaments if isinstance(tournaments, list) else []
    except Exception as e:
        print(f"[tenis] erro ao buscar calendário {tour}: {e}")
        return []

def fetch_rankings(tour: str) -> List[dict]:
    print(f"[tenis] buscando ranking {tour}...")
    url = f"{API_BASE}/{tour}/ranking/singles/"
    try:
        r = requests.get(url, headers=get_headers(), timeout=30)
        print(f"[tenis] ranking {tour} status: {r.status_code}")
        if r.status_code != 200:
            return []
        data = r.json()
        rankings = (
            data.get("data") or
            data.get("rankings") or
            data.get("results") or
            (data if isinstance(data, list) else [])
        )
        return rankings if isinstance(rankings, list) else []
    except Exception as e:
        print(f"[tenis] erro ao buscar ranking {tour}: {e}")
        return []

def fetch_fixtures(tour: str, tournament_id: str) -> List[dict]:
    print(f"[tenis] buscando fixtures {tour} torneio {tournament_id}...")
    url = f"{API_BASE}/{tour}/fixtures/tournament/{tournament_id}"
    params = {
        "pageSize": "100",
        "pageNo": "1",
        "filter": "PlayerGroup:both;"
    }
    try:
        r = requests.get(url, headers=get_headers(), params=params, timeout=30)
        print(f"[tenis] fixtures {tour}/{tournament_id} status: {r.status_code}")
        if r.status_code != 200:
            return []
        data = r.json()
        fixtures = (
            data.get("data") or
            data.get("fixtures") or
            data.get("results") or
            (data if isinstance(data, list) else [])
        )
        return fixtures if isinstance(fixtures, list) else []
    except Exception as e:
        print(f"[tenis] erro ao buscar fixtures {tour}/{tournament_id}: {e}")
        return []

# =========================
# PARSE
# =========================

def extrair_top_jogadores(cache: dict) -> List[str]:
    jogadores = set(BRASILEIROS)
    for tour in ["rankings_atp", "rankings_wta"]:
        for r in cache.get(tour, []):
            nome = ""
            if isinstance(r, dict):
                nome = (
                    r.get("player", {}).get("name", "") or
                    r.get("name", "") or
                    r.get("playerName", "")
                )
            if nome:
                jogadores.add(nome.lower())
    return list(jogadores)

def eh_torneio_relevante(torneio: dict) -> bool:
    nome = (torneio.get("name", "") or torneio.get("tournamentName", "") or "").lower()
    categoria = str(
        torneio.get("category", {}).get("name", "") or
        torneio.get("categoryName", "") or
        torneio.get("type", "") or ""
    ).lower()

    combined = nome + " " + categoria
    return any(k in combined for k in TOURNAMENT_KEYWORDS)

def parse_fixture(fixture: dict, torneio_nome: str, tour: str, top_jogadores: List[str]) -> Optional[dict]:
    try:
        home = fixture.get("home", {}) or {}
        away = fixture.get("away", {}) or {}

        if isinstance(home, str):
            nome_home = home
        else:
            nome_home = (
                home.get("name", "") or
                home.get("player", {}).get("name", "") or
                home.get("playerName", "") or ""
            )

        if isinstance(away, str):
            nome_away = away
        else:
            nome_away = (
                away.get("name", "") or
                away.get("player", {}).get("name", "") or
                away.get("playerName", "") or ""
            )

        if not nome_home or not nome_away:
            return None

        titulo = f"{nome_home} vs {nome_away}"
        titulo_lower = titulo.lower()

        relevante = any(j in titulo_lower for j in top_jogadores)
        if not relevante:
            return None

        date_str = (
            fixture.get("date", "") or
            fixture.get("startDate", "") or
            fixture.get("matchDate", "") or ""
        )
        if not date_str:
            return None

        try:
            data_utc = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except:
            try:
                data_utc = datetime.strptime(date_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except:
                return None

        resultado = None
        score = fixture.get("score", "") or fixture.get("result", "") or fixture.get("scoreStr", "")
        status_raw = fixture.get("status", {})
        status_name = ""
        if isinstance(status_raw, dict):
            status_name = str(status_raw.get("name", "") or status_raw.get("type", "")).lower()
        elif isinstance(status_raw, str):
            status_name = status_raw.lower()

        if score and any(s in status_name for s in ["finish", "complet", "played", "ended"]):
            resultado = str(score)

        rodada = None
        round_raw = fixture.get("round", {})
        if isinstance(round_raw, dict):
            rodada = round_raw.get("name") or round_raw.get("roundName")
        elif isinstance(round_raw, str):
            rodada = round_raw

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
            "destaque": destacar_tenis(titulo),
            "fonte": f"tennis-api-atp-wta-itf / {tour}",
            "rodada": rodada,
            "estadio": None,
            "cidade": None,
            "uf": None,
        }
    except Exception as e:
        print(f"[tenis] erro ao parsear fixture: {e}")
        return None

def criar_evento_torneio(torneio: dict, tour: str) -> Optional[dict]:
    try:
        nome = (
            torneio.get("name", "") or
            torneio.get("tournamentName", "") or
            "Torneio de Tênis"
        )
        inicio_str = (
            torneio.get("startDate", "") or
            torneio.get("dateFrom", "") or
            torneio.get("start", "") or ""
        )
        fim_str = (
            torneio.get("endDate", "") or
            torneio.get("dateTo", "") or
            torneio.get("end", "") or ""
        )

        if not inicio_str:
            return None

        try:
            data_utc = datetime.fromisoformat(inicio_str.replace("Z", "+00:00"))
            if data_utc.tzinfo is None:
                data_utc = data_utc.replace(tzinfo=timezone.utc)
        except:
            try:
                data_utc = datetime.strptime(inicio_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except:
                return None

        fim_info = f" até {fim_str[:10]}" if fim_str else ""
        tour_label = "ATP" if tour == "atp" else "WTA"

        return {
            "esporte": "Tênis",
            "competicao": nome,
            "titulo": f"🎾 {tour_label} • {nome}{fim_info}",
            "mandante": None,
            "visitante": None,
            "data_utc": data_utc.isoformat(),
            "status": inferir_status_tenis(data_utc.isoformat(), None),
            "resultado": None,
            "transmissao": "ESPN / Disney+",
            "destaque": False,
            "fonte": f"tennis-api-atp-wta-itf / {tour} / calendar",
            "rodada": None,
            "estadio": None,
            "cidade": None,
            "uf": None,
        }
    except Exception as e:
        print(f"[tenis] erro ao criar evento torneio: {e}")
        return None

# =========================
# SMART CACHE LOGIC
# =========================

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

def deve_buscar_fixtures(torneio: dict, cache: dict) -> bool:
    tid = str(torneio.get("id", "") or torneio.get("tournamentId", ""))
    inicio_str = (
        torneio.get("startDate", "") or
        torneio.get("dateFrom", "") or
        torneio.get("start", "") or ""
    )
    fim_str = (
        torneio.get("endDate", "") or
        torneio.get("dateTo", "") or
        torneio.get("end", "") or ""
    )

    if not inicio_str:
        return False

    dias_inicio = dias_ate_data(inicio_str)
    dias_fim = dias_ate_data(fim_str) if fim_str else dias_inicio + 7

    if dias_fim < -1:
        return False

    if dias_inicio > 7:
        return False

    fixtures_cache = cache.get("fixtures", {})
    torneio_cache = fixtures_cache.get(tid, {})
    ultima_busca = torneio_cache.get("updated", "")

    if not ultima_busca:
        return True

    try:
        ultima_dt = datetime.fromisoformat(ultima_busca)
        horas = (datetime.now(timezone.utc) - ultima_dt).total_seconds() / 3600

        if dias_inicio <= 0 and dias_fim >= 0:
            return horas >= 12

        return horas >= 24
    except:
        return True

# =========================
# PRINCIPAL
# =========================

def gerar_tenis() -> List[dict]:
    print("[tenis] iniciando coleta inteligente...")
    cache = ler_cache()
    eventos = []
    agora_iso = datetime.now(timezone.utc).isoformat()

    # Step 1 — Update rankings
    if deve_buscar_rankings(cache):
        print("[tenis] atualizando rankings...")
        cache["rankings_atp"] = fetch_rankings("atp")
        cache["rankings_wta"] = fetch_rankings("wta")
        cache["rankings_updated"] = agora_iso
        time.sleep(1)

    top_jogadores = extrair_top_jogadores(cache)
    print(f"[tenis] monitorando {len(top_jogadores)} jogadores")

    # Step 2 — Update calendar
    if deve_buscar_calendario(cache):
        print("[tenis] atualizando calendário...")
        torneios_atp = [dict(t, tour="atp") for t in fetch_calendar("atp")]
        time.sleep(1)
        torneios_wta = [dict(t, tour="wta") for t in fetch_calendar("wta")]
        time.sleep(1)

        todos = torneios_atp + torneios_wta
        relevantes = [t for t in todos if eh_torneio_relevante(t)]
        cache["calendar"] = relevantes
        cache["calendar_updated"] = agora_iso
        print(f"[tenis] {len(relevantes)} torneios relevantes de {len(todos)} total")

    torneios = cache.get("calendar", [])

    # DEBUG — show tournament details
    print(f"[tenis] torneios no cache: {len(torneios)}")
    for t in torneios:
        nome = t.get("name", "") or t.get("tournamentName", "") or "?"
        inicio = t.get("startDate", "") or t.get("dateFrom", "") or t.get("start", "") or "?"
        fim = t.get("endDate", "") or t.get("dateTo", "") or t.get("end", "") or "?"
        tid = str(t.get("id", "") or t.get("tournamentId", "") or "?")
        dias = dias_ate_data(inicio) if inicio != "?" else 999
        print(f"[tenis] torneio: {nome} | id={tid} | inicio={inicio} | fim={fim} | dias_ate={dias}")

    if not cache.get("fixtures"):
        cache["fixtures"] = {}

    # Step 3 — Fetch fixtures for relevant tournaments
    for torneio in torneios:
        tid = str(torneio.get("id", "") or torneio.get("tournamentId", ""))
        nome = torneio.get("name", "") or torneio.get("tournamentName", "") or "Torneio"
        tour = torneio.get("tour", "atp")
        inicio_str = (
            torneio.get("startDate", "") or
            torneio.get("dateFrom", "") or
            torneio.get("start", "") or ""
        )

        if not tid or not inicio_str:
            continue

        if deve_buscar_fixtures(torneio, cache):
            fixtures = fetch_fixtures(tour, tid)
            cache["fixtures"][tid] = {
                "updated": agora_iso,
                "data": fixtures
            }
            time.sleep(1)

        fixtures_data = cache.get("fixtures", {}).get(tid, {}).get("data", [])

        if fixtures_data:
            count = 0
            for fixture in fixtures_data:
                evento = parse_fixture(fixture, nome, tour, top_jogadores)
                if evento:
                    eventos.append(evento)
                    count += 1
            if count > 0:
                print(f"[tenis] {nome}: {count} partidas relevantes")
        else:
            evento_torneio = criar_evento_torneio(torneio, tour)
            if evento_torneio:
                dias = dias_ate_data(inicio_str)
                if -30 <= dias <= 30:
                    eventos.append(evento_torneio)
                    print(f"[tenis] {nome}: mostrando como evento de calendário")

    salvar_cache(cache)

    print(f"[tenis] total: {len(eventos)} eventos")
    return eventos
