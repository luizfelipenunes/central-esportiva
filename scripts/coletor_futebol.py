import re
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


CURRENT_YEAR = datetime.now().year
TZ_BRASIL = ZoneInfo("America/Sao_Paulo")

URLS = {
    "Copa do Brasil": f"https://www.cbf.com.br/futebol-brasileiro/tabelas/copa-do-brasil/masculino/{CURRENT_YEAR}",
}


# =========================
# UTIL
# =========================

def normalizar_texto(texto: str) -> str:
    texto = texto.replace("\xa0", " ")
    texto = texto.replace("\u200b", " ")
    texto = texto.replace("\u200c", " ")
    texto = texto.replace("\u200d", " ")
    texto = texto.replace("–", "-")
    texto = texto.replace("—", "-")
    texto = re.sub(r"[ \t]+", " ", texto)
    return texto.strip()


def destacar_futebol(titulo: str) -> bool:
    return "vasco" in titulo.lower()


def transmissao_padrao(_: str) -> str:
    return "A confirmar"


def inferir_status(data_utc: Optional[datetime], resultado: Optional[str]) -> str:
    if resultado:
        return "resultado"

    if data_utc and data_utc < datetime.now(timezone.utc):
        return "resultado"

    return "futuro"


def deduplicar(eventos: List[dict]) -> List[dict]:
    vistos = set()
    saida = []

    for evento in eventos:
        chave = (
            evento["competicao"],
            evento["titulo"],
            evento["data_utc"],
            evento["fonte"],
        )
        if chave in vistos:
            continue

        vistos.add(chave)
        saida.append(evento)

    return saida


# =========================
# ESPN (BRASILEIRÃO)
# =========================

def coletar_brasileirao_espn():
    url = "https://www.espn.com.br/futebol/calendario/_/liga/bra.1"
    headers = {"User-Agent": "Mozilla/5.0"}

    print("[futebol] coletando Brasileirão via ESPN...")

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    eventos = []

    jogos = soup.select("table tbody tr")

    for jogo in jogos:
        colunas = jogo.find_all("td")

        if len(colunas) < 3:
            continue

        try:
            data_str = colunas[0].get_text(strip=True)
            titulo = colunas[1].get_text(" ", strip=True)

            if " vs " not in titulo.lower():
                continue

            data = datetime.strptime(data_str, "%d/%m/%Y %H:%M")

            data_utc = data.replace(tzinfo=TZ_BRASIL).astimezone(timezone.utc)

            evento = {
                "esporte": "Futebol",
                "competicao": "Brasileirão",
                "titulo": titulo,
                "data_utc": data_utc.isoformat(),
                "status": "futuro",
                "resultado": None,
                "transmissao": "A confirmar",
                "destaque": destacar_futebol(titulo),
                "fonte": "ESPN",
            }

            eventos.append(evento)

        except Exception:
            continue

    print(f"[futebol] Brasileirão (ESPN): {len(eventos)} eventos coletados")

    return eventos


# =========================
# CBF (COPA DO BRASIL)
# =========================

def extrair_linhas_renderizadas(page) -> List[str]:
    texto = page.locator("body").inner_text(timeout=20000)
    linhas = [normalizar_texto(linha) for linha in texto.splitlines()]
    return [linha for linha in linhas if linha]


def eh_data_hora(linha: str) -> bool:
    return bool(re.search(r"\d{2}/\d{2}/\d{4}\s*-\s*\d{2}:\d{2}", linha))


def parse_data_hora_para_utc(linha: str) -> Optional[datetime]:
    match = re.search(r"(\d{2})/(\d{2})/(\d{4})\s*-\s*(\d{2}):(\d{2})", linha)
    if not match:
        return None

    dia, mes, ano, hora, minuto = match.groups()

    dt_local = datetime(
        int(ano),
        int(mes),
        int(dia),
        int(hora),
        int(minuto),
        tzinfo=TZ_BRASIL,
    )

    return dt_local.astimezone(timezone.utc)


def eh_ruido(linha: str) -> bool:
    if re.fullmatch(r"\d+", linha):
        return True
    if re.fullmatch(r"\(\d+\)", linha):
        return True
    if linha in {"Ano", "Competições", "TABELAS"}:
        return True
    return False


def buscar_data_proxima(linhas: List[str], idx: int, alcance=20):
    for i in range(max(0, idx - alcance), min(len(linhas), idx + alcance)):
        if eh_data_hora(linhas[i]):
            return parse_data_hora_para_utc(linhas[i])
    return None


def parse_confrontos_cbf(linhas: List[str], competicao: str, fonte: str):
    eventos = []

    for i, linha in enumerate(linhas):
        if linha not in {"X", "x"}:
            continue

        try:
            mandante = linhas[i - 2]
            visitante = linhas[i + 2]

            if eh_ruido(mandante) or eh_ruido(visitante):
                continue

            data_utc = buscar_data_proxima(linhas, i)

            if not data_utc:
                continue

            resultado = None

            if linhas[i - 1].isdigit() and linhas[i + 1].isdigit():
                resultado = f"{linhas[i - 1]} x {linhas[i + 1]}"

            evento = {
                "esporte": "Futebol",
                "competicao": competicao,
                "titulo": f"{mandante} vs {visitante}",
                "data_utc": data_utc.isoformat(),
                "status": inferir_status(data_utc, resultado),
                "resultado": resultado,
                "transmissao": "A confirmar",
                "destaque": destacar_futebol(f"{mandante} vs {visitante}"),
                "fonte": fonte,
            }

            eventos.append(evento)

        except Exception:
            continue

    return eventos


def coletar_copa_do_brasil():
    eventos = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        url = URLS["Copa do Brasil"]

        print(f"[futebol] coletando Copa do Brasil via CBF...")

        page.goto(url, wait_until="networkidle")

        linhas = extrair_linhas_renderizadas(page)

        eventos = parse_confrontos_cbf(linhas, "Copa do Brasil", url)

        browser.close()

    print(f"[futebol] Copa do Brasil: {len(eventos)} eventos coletados")

    return eventos


# =========================
# FUNÇÃO PRINCIPAL
# =========================

def gerar_futebol():
    eventos = []

    # Copa do Brasil (CBF)
    eventos.extend(coletar_copa_do_brasil())

    # Brasileirão (ESPN)
    eventos.extend(coletar_brasileirao_espn())

    eventos = [e for e in eventos if e.get("data_utc")]
    eventos = deduplicar(eventos)
    eventos.sort(key=lambda e: e["data_utc"])

    print(f"[futebol] total final: {len(eventos)}")

    for evento in eventos[:10]:
        print(f"[futebol] final -> {evento}")

    return eventos
