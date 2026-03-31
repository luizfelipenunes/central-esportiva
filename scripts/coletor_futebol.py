import json
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
EQUIPES_FILE = DB_DIR / "equipes.json"
TRANSMISSOES_FILE = DB_DIR / "transmissoes.json"

API_BASE = "https://v3.football.api-sports.io"

# League IDs on API-Football
LEAGUES = {
    "Brasileirão":        {"id": 71,  "name": "Brasileirão"},
    "Copa do Brasil":     {"id": 73,  "name": "Copa do Brasil"},
    "Libertadores":       {"id": 13,  "name": "Copa Libertadores"},
    "Sul-Americana":      {"id": 11,  "name": "Copa Sul-Americana"},
}

# =========================
# UTIL
# =========================

def ler_json(caminho: Path, default):
    try:
        if not caminho.exists():
            return default
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[futebol] erro ao ler {caminho.name}: {e}")
        return default

EQUIPES_DB = ler_json(EQUIPES_FILE, {})
TRANSMISSOES_DB = ler_json(TRANSMISSOES_FILE, {})

def buscar_transmissao(competicao: str) -> str:
    dados = TRANSMISSOES_DB.get(competicao, {})
    return dados.get("padrao", "A confirmar")

def buscar_dados_mandante(time_nome: str) -> dict:
    dados = EQUIPES_DB.get(time_nome, {})
    return {
        "estadio": dados.get("estadio_padrao"),
        "cidade": dados.get("cidade"),
        "uf": dados.get("uf"),
    }

def destacar_futebol(titulo: str) -> bool:
    return "vasco" in titulo.lower()

def inferir_status(data_utc: datetime, resultado: Optional[str]) -> str:
    if resultado:
        return "resultado"
    if data_utc < datetime.now(timezone.utc):
        return "resultado"
    return "futuro"

def deduplicar(eventos: List[dict]) -> List[dict]:
    vistos = set()
    saida = []
    for evento in eventos:
        chave = (evento["competicao"], evento["titulo"], evento["data_utc"])
        if chave in vistos:
            continue
        vistos.add(chave)
        saida.append(evento)
    return saida

# =========================
# API
# =========================

def get_headers() -> dict:
    import os
    api_key = os.environ.get("API_FOOTBALL_KEY", "")
    return {
        "x-apisports-key": api_key
    }

def fetch_fixtures(league_id: int, season: int) -> List[dict]:
    url = f"{API_BASE}/fixtures"
    params = {
        "league": league_id,
        "season": season,
    }
    try:
        response = requests.get(url, headers=get_headers(), params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        fixtures = data.get("response", [])
        print(f"[futebol] league {league_id}: {len(fixtures)} fixtures recebidos")
        return fixtures
    except Exception as e:
        print(f"[futebol] erro ao buscar league {league_id}: {e}")
        return []

# =========================
# PARSE
# =========================

def parse_fixture(fixture: dict, competicao: str) -> Optional[dict]:
    try:
        info = fixture["fixture"]
        teams = fixture["teams"]
        goals = fixture["goals"]
        league = fixture["league"]

        mandante = teams["home"]["name"]
        visitante = teams["away"]["name"]
        titulo = f"{mandante} vs {visitante}"

        # Date
        date_str = info.get("date")
        if not date_str:
            return None
        data_utc = datetime.fromisoformat(date_str.replace("Z", "+00:00"))

        # Result
        resultado = None
        home_goals = goals.get("home")
        away_goals = goals.get("away")
        if home_goals is not None and away_goals is not None:
            status_api = info.get("status", {}).get("short", "")
            if status_api in ("FT", "AET", "PEN", "AWD", "WO"):
                resultado = f"{home_goals} x {away_goals}"

        dados_mandante = buscar_dados_mandante(mandante)

        return {
            "esporte": "Futebol",
            "competicao": competicao,
            "titulo": titulo,
            "mandante": mandante,
            "visitante": visitante,
            "data_utc": data_utc.isoformat(),
            "status": inferir_status(data_utc, resultado),
            "resultado": resultado,
            "transmissao": buscar_transmissao(competicao),
            "destaque": destacar_futebol(titulo),
            "fonte": f"api-sports.io / league {league.get('id')}",
            "rodada": league.get("round"),
            "estadio": dados_mandante.get("estadio") or info.get("venue", {}).get("name"),
            "cidade": dados_mandante.get("cidade") or info.get("venue", {}).get("city"),
            "uf": dados_mandante.get("uf"),
        }
    except Exception as e:
        print(f"[futebol] erro ao parsear fixture: {e}")
        return None

# =========================
# COLLECTORS
# =========================

def coletar_liga(competicao: str, league_id: int) -> List[dict]:
    print(f"[futebol] coletando {competicao}...")
    fixtures = fetch_fixtures(league_id, CURRENT_YEAR)
    eventos = []
    for fixture in fixtures:
        evento = parse_fixture(fixture, competicao)
        if evento:
            eventos.append(evento)
    print(f"[futebol] {competicao}: {len(eventos)} eventos")
    time.sleep(0.5)  # be polite to the API
    return eventos

# =========================
# PRINCIPAL
# =========================

def gerar_futebol() -> List[dict]:
    eventos = []

    for nome, liga in LEAGUES.items():
        try:
            eventos.extend(coletar_liga(nome, liga["id"]))
        except Exception as e:
            print(f"[futebol] erro em {nome}: {e}")

    eventos = [e for e in eventos if e.get("data_utc")]
    eventos = deduplicar(eventos)
    eventos.sort(key=lambda e: e["data_utc"])

    print(f"[futebol] total final: {len(eventos)}")
    return eventos
