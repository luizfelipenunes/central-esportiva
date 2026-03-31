import json
import os
import time
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

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

CBF_URLS = {
    "Copa do Brasil":  f"https://www.cbf.com.br/futebol-brasileiro/tabelas/copa-do-brasil/masculino/{CURRENT_YEAR}",
    "Sul-Americana":   f"https://www.cbf.com.br/futebol-brasileiro/tabelas/copa-sul-americana/{CURRENT_YEAR}",
}

HEADERS_CBF = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )
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
    api_key = os.environ.get("FOOTBALL_DATA_KEY", "")
    print(f"[futebol] API key football-data presente: {'sim' if api_key else 'NAO - chave vazia!'}")
    print(f"[futebol] Buscando {competition_code}...")

    try:
        response = requests.get(url, headers=get_headers_fd(), timeout=30)
        print(f"[futebol] status HTTP: {response.status_code}")
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
    print(f"[futebol] coletando {competicao} via football-data.org...")
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
# API-SPORTS TEST
# =========================

def testar_api_sports():
    api_key = os.environ.get("API_FOOTBALL_KEY", "")
    headers = {"x-apisports-key": api_key}

    testes = [
        ("Copa do Brasil 2025", "https://v3.football.api-sports.io/fixtures?league=73&season=2025"),
        ("Sul-Americana 2025", "https://v3.football.api-sports.io/fixtures?league=11&season=2025"),
        ("Copa do Brasil 2026", "https://v3.football.api-sports.io/fixtures?league=73&season=2026"),
        ("Sul-Americana 2026", "https://v3.football.api-sports.io/fixtures?league=11&season=2026"),
    ]

    for nome, url in testes:
        try:
            r = requests.get(url, headers=headers, timeout=30)
            data = r.json()
            print(f"[teste] {nome}: status={r.status_code}, errors={data.get('errors')}, results={data.get('results')}")
        except Exception as e:
            print(f"[teste] {nome}: ERRO {e}")

# =========================
# CBF SCRAPER
# =========================

def normalizar_texto(texto: str) -> str:
    texto = (texto or "").replace("\xa0", " ")
    texto = re.sub(r"[ \t]+", " ", texto)
    return texto.strip()

def eh_data_hora_cbf(linha: str) -> bool:
    return bool(re.search(r"\d{2}/\d{2}/\d{4}\s*-\s*\d{2}:\d{2}", linha))

def parse_data_hora_cbf(linha: str) -> Optional[datetime]:
    match = re.search(r"(\d{2})/(\d{2})/(\d{4})\s*-\s*(\d{2}):(\d{2})", linha)
    if not match:
        return None
    dia, mes, ano, hora, minuto = match.groups()
    dt_local = datetime(int(ano), int(mes), int(dia), int(hora), int(minuto), tzinfo=TZ_BRASIL)
    return dt_local.astimezone(timezone.utc)

def coletar_cbf(competicao: str, url: str) -> List[dict]:
    print(f"[futebol] coletando {competicao} via CBF (requests)...")
    try:
        response = requests.get(url, headers=HEADERS_CBF, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        texto = soup.get_text("\n")
        linhas = [normalizar_texto(l) for l in texto.splitlines()]
        linhas = [l for l in linhas if l]
    except Exception as e:
        print(f"[futebol] erro ao buscar CBF {competicao}: {e}")
        return []

    eventos = []
    for i, linha in enumerate(linhas):
        if linha not in {"X", "x"}:
            continue

        mandante = None
        visitante = None

        for j in range(i - 1, max(-1, i - 8), -1):
            l = linhas[j]
            if l in {"X", "x"} or eh_data_hora_cbf(l) or re.fullmatch(r"\d+", l):
                continue
            mandante = l
            break

        for j in range(i + 1, min(len(linhas), i + 8)):
            l = linhas[j]
            if l in {"X", "x"} or eh_data_hora_cbf(l) or re.fullmatch(r"\d+", l):
                continue
            visitante = l
            break

        if not mandante or not visitante:
            continue

        data_utc = None
        for j in range(max(0, i - 20), min(len(linhas), i + 20)):
            if eh_data_hora_cbf(linhas[j]):
                data_utc = parse_data_hora_cbf(linhas[j])
                break

        if not data_utc:
            continue

        titulo = f"{mandante} vs {visitante}"
        eventos.append({
            "esporte": "Futebol",
            "competicao": competicao,
            "titulo": titulo,
            "mandante": mandante,
            "visitante": visitante,
            "data_utc": data_utc.isoformat(),
            "status": inferir_status(data_utc, None),
            "resultado": None,
            "transmissao": buscar_transmissao(competicao),
            "destaque": destacar_futebol(titulo),
            "fonte": url,
            "rodada": None,
            "estadio": None,
            "cidade": None,
            "uf": None,
        })

    print(f"[futebol] {competicao}: {len(eventos)} eventos")
    return eventos

# =========================
# PRINCIPAL
# =========================

def gerar_futebol() -> List[dict]:
    testar_api_sports()

    eventos = []

    for competicao, code in COMPETITIONS.items():
        try:
            eventos.extend(coletar_football_data(competicao, code))
        except Exception as e:
            print(f"[futebol] erro em {competicao}: {e}")

    for competicao, url in CBF_URLS.items():
        try:
            eventos.extend(coletar_cbf(competicao, url))
        except Exception as e:
            print(f"[futebol] erro em {competicao}: {e}")

    eventos = [e for e in eventos if e.get("data_utc")]
    eventos = deduplicar(eventos)
    eventos.sort(key=lambda e: e["data_utc"])

    print(f"[futebol] total final: {len(eventos)}")
    return eventos
