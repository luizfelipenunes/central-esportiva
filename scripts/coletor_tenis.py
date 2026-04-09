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
CALENDAR_FILE = DB_DIR / "tennis_calendar_2026.json"

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
    "masters 1000", "wta 1000", "grand slam", "monte carlo",
    "monte-carlo", "rolex monte"
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

def ler_calendario_local() -> List[dict]:
    try:
        if not CALENDAR_FILE.exists():
            print("[tenis] arquivo de calendário não encontrado")
            return []
        with open(CALENDAR_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[tenis] erro ao ler calendário local: {e}")
        return []

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
    combined = (nome + " " + ut_nome).lower()
    if any(k in combined for k in TOURNAMENT_KEYWORDS):
        return True
    if priority <= 2:
        return True
    return False

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
        return rankings if isinstance(rankings, list) else []
    except Exception as e:
        print(f"[tenis] erro rankings {tour}: {e}")
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
    return list(jogadores)

def parse_event(event: dict, top_jogadores: List[str]) -> Optional[dict]:
    try:
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

        nome_display = ut_nome or torneio_nome

        if not eh_torneio_relevante(torneio_nome, ut_nome, priority):
            return None

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

        relevante = any(j in titulo_lower for j in top_jogadores)
        if not relevante:
            return None

        timestamp = event.get("startTimestamp") or event.get("timestamp")
        if not timestamp:
            return None

        data_utc = datetime.fromtimestamp(int(timestamp), tz=timezone.utc)

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

def criar_evento_calendario_local(torneio: dict) -> Optional[dict]:
    try:
        nome = torneio.get("nome", "")
        inicio_str = torneio.get("inicio", "")
        fim_str = torneio.get("fim", "")
        transmissao = torneio.get("transmissao", "ESPN / Disney+")
        tour = torneio.get("tour", "ATP")

        if not nome or not inicio_str:
            return None

        try:
            data_utc = datetime.strptime(inicio_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except:
            return None

        dias = (data_utc.date() - datetime.now(TZ_BRASIL).date()).days

        # Only show tournaments within next 60 days or currently active
        if dias < -1 or dias > 60:
            return None

        fim_info = ""
        if fim_str:
            try:
                fim_dt = datetime.strptime(fim_str, "%Y-%m-%d")
                fim_info = f" até {fim_dt.strftime('%d/%m')}"
            except:
                pass

        status = "futuro" if dias >= 0 else "resultado"

        return {
            "esporte": "Tênis",
            "competicao": nome,
            "titulo": nome,
            "mandante": None,
            "visitante": None,
            "data_utc": data_utc.isoformat(),
            "status": status,
            "resultado": None,
            "transmissao": transmissao,
            "destaque": False,
            "fonte": "calendario_local",
            "rodada": None,
            "estadio": None,
            "cidade": None,
            "uf": None,
        }
    except Exception as e:
        print(f"[tenis] erro ao criar evento calendário local: {e}")
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
    ontem = agora - timedelta(days=1)
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

    # Step 2 — Fetch yesterday, today and tomorrow events (twice a day)
    if deve_buscar_fixtures(cache):
        print("[tenis] buscando eventos de ontem, hoje e amanha...")
        events_ontem = fetch_events_by_date(ontem.day, ontem.month, ontem.year)
        time.sleep(1)
        events_hoje = fetch_events_by_date(agora.day, agora.month, agora.year)
        time.sleep(1)
        events_amanha = fetch_events_by_date(amanha.day, amanha.month, amanha.year)

        todas = events_ontem + events_hoje + events_amanha

        # Deduplicate by event id
        vistos = set()
        todas_unicas = []
        for e in todas:
            eid = e.get("id")
            if eid and eid in vistos:
                continue
            if eid:
                vistos.add(eid)
            todas_unicas.append(e)

        cache["fixtures_hoje"] = todas_unicas
        cache["fixtures_updated"] = agora_iso
        print(f"[tenis] {len(todas_unicas)} eventos unicos encontrados")
    else:
        print("[tenis] usando cache de fixtures...")

    # Step 3 — Parse events
    todas = cache.get("fixtures_hoje", [])
    for event in todas:
        evento = parse_event(event, top_jogadores)
        if evento:
            eventos.append(evento)

    # Deduplicate parsed events by title
    vistos_titulos = set()
    eventos_unicos = []
    for ev in eventos:
        chave = ev["titulo"] + (ev.get("data_utc", "")[:10])
        if chave not in vistos_titulos:
            vistos_titulos.add(chave)
            eventos_unicos.append(ev)

    eventos = eventos_unicos
    print(f"[tenis] {len(eventos)} partidas relevantes")

    # Step 4 — Fallback: local hardcoded calendar
    if len(eventos) == 0:
        print("[tenis] usando calendario local como fallback...")
        calendario = ler_calendario_local()
        vistos = set()
        for torneio in calendario:
            evento = criar_evento_calendario_local(torneio)
            if evento and evento["competicao"] not in vistos:
                vistos.add(evento["competicao"])
                eventos.append(evento)
                print(f"[tenis] calendario: {evento['titulo']}")

    salvar_cache(cache)

    print(f"[tenis] total final: {len(eventos)} eventos")
    return eventos
