import json
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Optional, Dict
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
    "roland garros", "wimbledon", "us open", "miami open",
    "madrid", "rome", "montreal", "cincinnati", "shanghai",
    "paris", "indian wells", "toronto", "beijing", "dubai",
    "doha", "miami masters", "italian open", "french open",
    "rolex", "bnp paribas", "internazionali"
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

def hoje_str() -> str:
    return datetime.now(TZ_BRASIL).strftime("%Y-%m-%d")

def amanha_str() -> str:
    return (datetime.now(TZ_BRASIL) + timedelta(days=1)).strftime("%Y-%m-%d")

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

def eh_torneio_relevante(nome_torneio: str) -> bool:
    nome = nome_torneio.lower()
    return any(k in nome for k in TOURNAMENT_KEYWORDS)

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

# =========================
# API CALLS
# =========================

def fetch_fixtures_date(tour: str, date_str: str) -> List[dict]:
    url = f"{API_BASE}/{tour}/fixtures/{date_str}"
    try:
        r = requests.get(url, headers=get_headers(), timeout=30)
        print(f"[tenis] fixtures {tour} {date_str}: status {r.status_code}")
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
        print(f"[tenis] erro fixtures {tour} {date_str}: {e}")
        return []

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
        return tournaments if isinstance(tournaments, list) else []
    except Exception as e:
        print(f"[tenis] erro calendário {tour}: {e}")
        return []

# =========================
# PARSE
# =========================

def extrair_top_jogadores(cache: dict) -> List[str]:
    jogadores = set(BRASILEIROS)
    for nome in cache.get("jogadores_vistos", []):
        jogadores.add(nome.lower())
    return list(jogadores)

def construir_mapa_torneios(cache: dict) -> Dict[str, dict]:
    mapa = {}
    for torneio in cache.get("calendar", []):
        tid = str(torneio.get("id", "") or torneio.get("tournamentId", ""))
        nome = torneio.get("name", "") or torneio.get("tournamentName", "") or ""
        inicio = ""
        for campo in ["startDate", "dateFrom", "start", "date"]:
            val = torneio.get(campo, "")
            if val:
                inicio = val
                break
        fim = ""
        for campo in ["endDate", "dateTo", "end"]:
            val = torneio.get(campo, "")
            if val:
                fim = val
                break
        if tid and nome:
            mapa[tid] = {
                "nome": nome,
                "inicio": inicio,
                "fim": fim,
                "tour": torneio.get("tour", "atp")
            }
    return mapa

def parse_fixture(fixture: dict, top_jogadores: List[str], mapa_torneios: Dict[str, dict]) -> Optional[dict]:
    try:
        # Get tournament name from map
        tid = str(fixture.get("tournamentId", ""))
        torneio_info = mapa_torneios.get(tid, {})
        torneio_nome = torneio_info.get("nome", "")

        # If not in map, skip — we don't know the tournament name
        if not torneio_nome:
            return None

        # Only Grand Slams and Masters 1000
        if not eh_torneio_relevante(torneio_nome):
            return None

        # Extract player names
        p1 = fixture.get("player1", {}) or {}
        p2 = fixture.get("player2", {}) or {}

        nome_p1 = p1.get("name", "") if isinstance(p1, dict) else str(p1)
        nome_p2 = p2.get("name", "") if isinstance(p2, dict) else str(p2)

        if not nome_p1 or not nome_p2:
            return None

        titulo = f"{nome_p1} vs {nome_p2}"
        titulo_lower = titulo.lower()

        # Only include if involves top player or Brazilian
        relevante = any(j in titulo_lower for j in top_jogadores)
        if not relevante:
            return None

        # Date
        date_str = fixture.get("date", "")
        if not date_str:
            return None

        try:
            data_utc = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except:
            return None

        # Result
        resultado = None
        score = str(fixture.get("score", "") or fixture.get("result", "") or "")
        status_raw = fixture.get("status", {})
        status_name = ""
        if isinstance(status_raw, dict):
            status_name = str(status_raw.get("name", "") or "").lower()
        elif isinstance(status_raw, str):
            status_name = status_raw.lower()

        if score and any(s in status_name for s in ["finish", "complet", "played", "ended"]):
            resultado = score

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
            "fonte": "tennis-api-atp-wta-itf",
            "rodada": str(fixture.get("roundId", "") or ""),
            "estadio": None,
            "cidade": None,
            "uf": None,
        }
    except Exception as e:
        print(f"[tenis] erro ao parsear fixture: {e}")
        return None

def criar_evento_calendario(torneio: dict, tour: str) -> Optional[dict]:
    try:
        nome = torneio.get("nome", "") or torneio.get("name", "") or ""

        if not nome or not eh_torneio_relevante(nome):
            return None

        inicio_str = torneio.get("inicio", "") or torneio.get("startDate", "") or ""
        fim_str = torneio.get("fim", "") or torneio.get("endDate", "") or ""

        if not inicio_str:
            return None

        dias = dias_ate_data(inicio_str)
        if dias < 0 or dias > 30:
            return None

        try:
            data_utc = datetime.strptime(inicio_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except:
            return None

        tour_label = "ATP" if tour == "atp" else "WTA"
        fim_info = f" até {fim_str[:10]}" if fim_str else ""

        return {
            "esporte": "Tênis",
            "competicao": nome,
            "titulo": f"🎾 {tour_label} • {nome}{fim_info}",
            "mandante": None,
            "visitante": None,
            "data_utc": data_utc.isoformat(),
            "status": "futuro",
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
    hoje = hoje_str()
    amanha = amanha_str()

    # Step 1 — Always update calendar first to build tournament ID map
    if deve_buscar_calendario(cache):
        print("[tenis] atualizando calendário...")
        torneios_atp = [dict(t, tour="atp") for t in fetch_calendar("atp")]
        time.sleep(1)
        torneios_wta = [dict(t, tour="wta") for t in fetch_calendar("wta")]
        cache["calendar"] = torneios_atp + torneios_wta
        cache["calendar_updated"] = agora_iso
        print(f"[tenis] calendário: {len(cache['calendar'])} torneios")

    mapa_torneios = construir_mapa_torneios(cache)
    print(f"[tenis] mapa de torneios: {len(mapa_torneios)} entradas")

    top_jogadores = extrair_top_jogadores(cache)
    print(f"[tenis] monitorando {len(top_jogadores)} jogadores")

    # Step 2 — Fetch today and tomorrow fixtures (twice a day)
    if deve_buscar_fixtures(cache):
        print(f"[tenis] buscando fixtures de {hoje} e {amanha}...")
        fixtures_hoje_atp = fetch_fixtures_date("atp", hoje)
        time.sleep(1)
        fixtures_hoje_wta = fetch_fixtures_date("wta", hoje)
        time.sleep(1)
        fixtures_amanha_atp = fetch_fixtures_date("atp", amanha)
        time.sleep(1)
        fixtures_amanha_wta = fetch_fixtures_date("wta", amanha)

        todas_fixtures = (
            fixtures_hoje_atp +
            fixtures_hoje_wta +
            fixtures_amanha_atp +
            fixtures_amanha_wta
        )

        cache["fixtures_hoje"] = todas_fixtures
        cache["fixtures_updated"] = agora_iso
        print(f"[tenis] {len(todas_fixtures)} fixtures encontradas")

        # Debug — show unique tournament IDs found
        tids = set(str(f.get("tournamentId", "")) for f in todas_fixtures)
        print(f"[tenis] tournament IDs nas fixtures: {tids}")
        for tid in tids:
            nome = mapa_torneios.get(tid, {}).get("nome", "NAO ENCONTRADO")
            print(f"[tenis] ID {tid} = {nome}")
    else:
        print("[tenis] usando fixtures do cache...")

    # Step 3 — Parse fixtures
    todas_fixtures = cache.get("fixtures_hoje", [])
    for fixture in todas_fixtures:
        evento = parse_fixture(fixture, top_jogadores, mapa_torneios)
        if evento:
            eventos.append(evento)

    print(f"[tenis] {len(eventos)} partidas relevantes encontradas")

    # Step 4 — Fallback: show upcoming tournaments from calendar
    if len(eventos) == 0:
        print("[tenis] usando calendário como fallback...")
        for torneio in cache.get("calendar", []):
            tour = torneio.get("tour", "atp")
            evento = criar_evento_calendario(torneio, tour)
            if evento:
                eventos.append(evento)
                print(f"[tenis] calendário: {evento['titulo']}")

    salvar_cache(cache)

    print(f"[tenis] total final: {len(eventos)} eventos")
    return eventos
