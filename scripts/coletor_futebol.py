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
EQUIPES_FILE = DB_DIR / "equipes.json"
TRANSMISSOES_FILE = DB_DIR / "transmissoes.json"

FOOTBALL_DATA_BASE = "https://api.football-data.org/v4"

COMPETITIONS = {
    "Brasileirão":  "BSA",
    "Libertadores": "CLI",
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
# FOOTBALL-DATA.ORG
# =========================

def get_headers_fd() -> dict:
    api_key = os.environ.get("FOOTBALL_DATA_KEY", "")
    return {
        "X-Auth-Token": api_key
    }

def fetch_matches_fd(competition_code: str) -> List[dict]:
    url = f"{FOOTBALL_DATA_BASE}/competitions/{competition_code}/matches"
    try:
        response = requests.get(url, headers=get_headers_fd(), timeout=30)
        if response.status_code == 403:
            print(f"[futebol] ERRO 403: competição {competition_code} não disponível no plano free")
            return []
        response.raise_for_status()
        data = response.json()
        matches = data.get("matches", [])
        print(f"[futebol] {competition_code}: {len(matches)} jogos recebidos")
        return matches
    except Exception as e:
        print(f"[futebol] erro ao buscar {competition_code}: {e}")
        return []

def parse_match_fd(match: dict, competicao: str) -> Optional[dict]:
    try:
        mandante = match["homeTeam"]["name"]
        visitante = match["awayTeam"]["name"]
        titulo = f"{mandante} vs {visitante}"

        date_str = match.get("utcDate")
        if not date_str:
            return None
        data_utc = datetime.fromisoformat(date_str.replace("Z", "+00:00"))

        resultado = None
        status_api = match.get("status", "")
        score = match.get("score", {})
        full_time = score.get("fullTime", {})
        home_goals = full_time.get("home")
        away_goals = full_time.get("away")

        if status_api == "FINISHED" and home_goals is not None and away_goals is not None:
            resultado = f"{home_goals} x {away_goals}"

        dados_mandante = buscar_dados_mandante(mandante)
        rodada = match.get("matchday")

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
            "fonte": f"football-data.org / {competicao}",
            "rodada": rodada,
            "estadio": dados_mandante.get("estadio"),
            "cidade": dados_mandante.get("cidade"),
            "uf": dados_mandante.get("uf"),
        }
    except Exception as e:
        print(f"[futebol] erro ao parsear match: {e}")
        return None

def coletar_football_data(competicao: str, code: str) -> List[dict]:
    print(f"[futebol] coletando {competicao}...")
    matches = fetch_matches_fd(code)
    eventos = []
    for match in matches:
        evento = parse_match_fd(match, competicao)
        if evento:
            eventos.append(evento)
    print(f"[futebol] {competicao}: {len(eventos)} eventos")
    time.sleep(6)
    return eventos

# =========================
# PRINCIPAL
# =========================

def gerar_futebol() -> List[dict]:
    eventos = []

    for competicao, code in COMPETITIONS.items():
        try:
            eventos.extend(coletar_football_data(competicao, code))
        except Exception as e:
            print(f"[futebol] erro em {competicao}: {e}")

    eventos = [e for e in eventos if e.get("data_utc")]
    eventos = deduplicar(eventos)
    eventos.sort(key=lambda e: e["data_utc"])

    print(f"[futebol] total final: {len(eventos)}")
    return eventos
