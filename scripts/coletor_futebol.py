import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


CURRENT_YEAR = datetime.now().year
TZ_BRASIL = ZoneInfo("America/Sao_Paulo")

BASE_DIR = Path(__file__).resolve().parent.parent
RODADAS_FILE = BASE_DIR / "data" / "rodadas_brasileirao.json"

URLS = {
    "Brasileirão": "https://www.espn.com.br/futebol/calendario/_/liga/bra.1",
    "Copa do Brasil": f"https://www.cbf.com.br/futebol-brasileiro/tabelas/copa-do-brasil/masculino/{CURRENT_YEAR}",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )
}

TEAM_NAME_MAP = {
    "VOL": "Volta Redonda",
    "BAR": "Barra",
    "SPO": "Sport",
    "ATH": "Athletico Paranaense",
    "NOV": "Nova Iguaçu",
    "FOR": "Fortaleza",
    "JAC": "Jacuipense",
    "GRE": "Grêmio",
    "SAO": "São Bernardo",
    "CEA": "Ceará",
    "VIL": "Vila Nova",
    "CON": "Confiança",
    "ATL": "Atlético-GO",
    "PON": "Ponte Preta",
    "MAR": "Maranhão",
    "GOI": "Goiás",
    "JUV": "Juventude",
    "AGU": "Águia de Marabá",
    "LON": "Londrina",
    "OPE": "Operário-PR",
    "CRB": "CRB",
    "FIG": "Figueirense",
    "POR": "Portuguesa",
    "PAY": "Paysandu",
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


def slugify(texto: str) -> str:
    texto = normalizar_texto(texto).lower()
    texto = (
        texto.replace("ã", "a")
        .replace("á", "a")
        .replace("à", "a")
        .replace("â", "a")
        .replace("ä", "a")
        .replace("é", "e")
        .replace("ê", "e")
        .replace("è", "e")
        .replace("ë", "e")
        .replace("í", "i")
        .replace("ì", "i")
        .replace("ï", "i")
        .replace("ó", "o")
        .replace("ô", "o")
        .replace("õ", "o")
        .replace("ò", "o")
        .replace("ö", "o")
        .replace("ú", "u")
        .replace("ù", "u")
        .replace("ü", "u")
        .replace("ç", "c")
    )
    texto = re.sub(r"[^a-z0-9]+", "-", texto)
    return texto.strip("-")


def titulo_time(nome: str) -> str:
    nome = normalizar_texto(nome)
    if not nome:
        return nome

    nome_upper = nome.upper()
    if nome_upper in TEAM_NAME_MAP:
        return TEAM_NAME_MAP[nome_upper]

    return nome


def destacar_futebol(titulo: str) -> bool:
    return "vasco" in titulo.lower()


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
            evento.get("resultado"),
            evento.get("rodada"),
        )
        if chave in vistos:
            continue

        vistos.add(chave)
        saida.append(evento)

    return saida


def criar_evento(
    competicao: str,
    mandante: str,
    visitante: str,
    data_utc: datetime,
    resultado: Optional[str],
    fonte: str,
    rodada: Optional[int] = None,
) -> dict:
    mandante_fmt = titulo_time(mandante)
    visitante_fmt = titulo_time(visitante)
    titulo = f"{mandante_fmt} vs {visitante_fmt}"

    return {
        "esporte": "Futebol",
        "competicao": competicao,
        "titulo": titulo,
        "data_utc": data_utc.isoformat(),
        "status": inferir_status(data_utc, resultado),
        "resultado": resultado,
        "transmissao": "A confirmar",
        "destaque": destacar_futebol(titulo),
        "fonte": fonte,
        "rodada": rodada,
    }


def carregar_rodadas_brasileirao() -> dict:
    if not RODADAS_FILE.exists():
        print(f"[futebol] aviso: arquivo de rodadas não encontrado em {RODADAS_FILE}")
        return {}

    try:
        with open(RODADAS_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)

        if not isinstance(dados, dict):
            print("[futebol] aviso: rodadas_brasileirao.json não é um objeto JSON")
            return {}

        print(f"[futebol] mapa de rodadas carregado: {len(dados)} chaves")
        return dados

    except Exception as e:
        print(f"[futebol] erro ao carregar rodadas_brasileirao.json: {e}")
        return {}


def buscar_rodada_brasileirao(mandante: str, visitante: str, mapa_rodadas: dict) -> Optional[int]:
    chave = f"{slugify(titulo_time(mandante))}__{slugify(titulo_time(visitante))}"
    rodada = mapa_rodadas.get(chave)

    if rodada is None:
        print(f"[futebol] rodada não encontrada para chave: {chave}")

    return rodada


# =========================
# ESPN - BRASILEIRÃO
# =========================

def baixar_html(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


def html_para_linhas(html: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    texto = soup.get_text("\n")
    linhas = [normalizar_texto(l) for l in texto.splitlines()]
    return [l for l in linhas if l]


def eh_cabecalho_data_espn(linha: str) -> bool:
    linha_lower = linha.lower()

    padroes = [
        r"^(segunda-feira|terça-feira|terca-feira|quarta-feira|quinta-feira|sexta-feira|sábado|sabado|domingo),\s*\d{1,2}\s+de\s+\w+",
        r"^(segunda|terça|terca|quarta|quinta|sexta|sábado|sabado|domingo),\s*\d{1,2}\s+de\s+\w+",
        r"^\d{1,2}\s+de\s+\w+",
    ]

    return any(re.match(p, linha_lower) for p in padroes)


def parse_data_espn(linha: str) -> Optional[datetime]:
    linha_lower = linha.lower()

    meses = {
        "janeiro": 1,
        "fevereiro": 2,
        "março": 3,
        "marco": 3,
        "abril": 4,
        "maio": 5,
        "junho": 6,
        "julho": 7,
        "agosto": 8,
        "setembro": 9,
        "outubro": 10,
        "novembro": 11,
        "dezembro": 12,
    }

    match = re.search(r"(\d{1,2})\s+de\s+([a-zçãé]+)", linha_lower)
    if not match:
        return None

    dia = int(match.group(1))
    mes_nome = match.group(2)
    mes = meses.get(mes_nome)

    if not mes:
        return None

    ano = CURRENT_YEAR
    agora = datetime.now(TZ_BRASIL)

    if mes == 12 and agora.month == 1:
        ano -= 1
    elif mes == 1 and agora.month == 12:
        ano += 1

    return datetime(ano, mes, dia, tzinfo=TZ_BRASIL)


def eh_hora(linha: str) -> bool:
    return bool(re.fullmatch(r"\d{1,2}:\d{2}", linha))


def eh_placar(linha: str) -> bool:
    return bool(re.fullmatch(r"\d+\s*-\s*\d+", linha))


def eh_separador_versus(linha: str) -> bool:
    return linha.lower() in {"v", "vs", "x"}


def eh_ruido_espn(linha: str) -> bool:
    ruidos = {
        "espn",
        "futebol",
        "times",
        "campeonatos",
        "resultados",
        "calendário",
        "calendario",
        "brasileirão",
        "brasileirão série a",
        "série a",
        "serie a",
        "agenda",
        "agenda do time",
        "escolha uma liga",
        "campeonato brasileiro",
        "campeonato brasileiro série b",
        "brazilian serie c",
        "classificação",
        "bola de prata",
        "notícias",
        "programação",
        "podcasts",
        "disney plus",
        "mais esportes",
        "nfl",
        "nba",
        "tênis",
        "tenis",
        "f1",
        "olimpíadas",
        "olimpiadas",
        "ir para o conteúdo principal",
        "ir para o menu principal",
        "busca",
    }

    return linha.lower() in ruidos


def montar_datetime_brasil_para_utc(data_base: datetime, hora_str: str) -> datetime:
    hora, minuto = hora_str.split(":")
    dt_local = datetime(
        data_base.year,
        data_base.month,
        data_base.day,
        int(hora),
        int(minuto),
        tzinfo=TZ_BRASIL,
    )
    return dt_local.astimezone(timezone.utc)


def parse_blocos_espn(linhas: List[str], mapa_rodadas: dict) -> List[dict]:
    eventos = []
    data_atual: Optional[datetime] = None

    i = 0
    while i < len(linhas):
        linha = linhas[i]

        if eh_cabecalho_data_espn(linha):
            data_atual = parse_data_espn(linha)
            i += 1
            continue

        if data_atual is None:
            i += 1
            continue

        if i + 3 < len(linhas):
            time_a = linhas[i]
            sep = linhas[i + 1]
            time_b = linhas[i + 2]
            info = linhas[i + 3]

            if (
                time_a
                and time_b
                and not eh_ruido_espn(time_a)
                and not eh_ruido_espn(time_b)
                and eh_separador_versus(sep)
            ):
                resultado = None
                data_utc = None

                if eh_hora(info):
                    data_utc = montar_datetime_brasil_para_utc(data_atual, info)

                elif eh_placar(info):
                    resultado = info.replace("-", " x ")
                    data_utc = datetime(
                        data_atual.year,
                        data_atual.month,
                        data_atual.day,
                        21,
                        0,
                        tzinfo=TZ_BRASIL,
                    ).astimezone(timezone.utc)

                if data_utc:
                    rodada = buscar_rodada_brasileirao(time_a, time_b, mapa_rodadas)

                    evento = criar_evento(
                        competicao="Brasileirão",
                        mandante=time_a,
                        visitante=time_b,
                        data_utc=data_utc,
                        resultado=resultado,
                        fonte=URLS["Brasileirão"],
                        rodada=rodada,
                    )
                    eventos.append(evento)
                    i += 4
                    continue

        i += 1

    return eventos


def coletar_brasileirao_espn(mapa_rodadas: dict) -> List[dict]:
    print("[futebol] coletando Brasileirão via ESPN...")
    html = baixar_html(URLS["Brasileirão"])
    linhas = html_para_linhas(html)

    print(f"[futebol] Brasileirão: {len(linhas)} linhas extraídas")
    print("[futebol] Brasileirão: primeiras 40 linhas:")
    for linha in linhas[:40]:
        print(f"  {linha}")

    eventos = parse_blocos_espn(linhas, mapa_rodadas)

    print(f"[futebol] Brasileirão (ESPN): {len(eventos)} eventos coletados")
    for evento in eventos[:10]:
        print(f"[futebol] Brasileirão exemplo -> {evento}")

    return eventos


# =========================
# CBF - COPA DO BRASIL
# =========================

def extrair_linhas_renderizadas(page) -> List[str]:
    texto = page.locator("body").inner_text(timeout=20000)
    linhas = [normalizar_texto(linha) for linha in texto.splitlines()]
    return [linha for linha in linhas if linha]


def eh_data_hora_cbf(linha: str) -> bool:
    return bool(re.search(r"\d{2}/\d{2}/\d{4}\s*-\s*\d{2}:\d{2}", linha))


def parse_data_hora_cbf_para_utc(linha: str) -> Optional[datetime]:
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


def eh_ruido_cbf(linha: str) -> bool:
    ruidos_exatos = {
        "CREDENCIAMENTO",
        "CBF ACADEMY",
        "STJD",
        "BID",
        "CANAL DE ETICA",
        "PORTAL DE GOVERNANÇA",
        "A CBF",
        "SELEÇÃO BRASILEIRA",
        "FUTEBOL BRASILEIRO",
        "CBF TV",
        "NOTÍCIAS",
        "TABELAS",
        "TIMES",
        "ATLETAS",
        "RANKING",
        "JOGOS DE HOJE",
        "Ano",
        "Competições",
        "Masculino",
        "Feminino",
        "Sub-20",
        "Sub-17",
        "COPA DO BRASIL - PROFISSIONAL",
        "Fases da competições",
        "Fases da competição",
        "1ª Fase",
        "2ª Fase",
        "3ª Fase",
        "4ª fase",
        "4ª Fase",
        "Oitavas de Final",
        "Quartas de Final",
        "Semi Finais",
        "Semifinais",
        "Final",
    }

    if linha in ruidos_exatos:
        return True

    if re.fullmatch(r"GRUPO\s+\d+", linha, re.IGNORECASE):
        return True

    return False


def buscar_data_proxima_cbf(linhas: List[str], indice_x: int, alcance: int = 20) -> Optional[datetime]:
    inicio = max(0, indice_x - alcance)
    fim = min(len(linhas), indice_x + alcance + 1)

    for i in range(inicio, fim):
        if eh_data_hora_cbf(linhas[i]):
            return parse_data_hora_cbf_para_utc(linhas[i])

    return None


def buscar_time_anterior_cbf(linhas: List[str], indice_x: int, limite: int = 8) -> Optional[str]:
    for i in range(indice_x - 1, max(-1, indice_x - limite), -1):
        linha = linhas[i]

        if linha in {"X", "x"}:
            continue
        if eh_ruido_cbf(linha):
            continue
        if eh_data_hora_cbf(linha):
            continue
        if re.fullmatch(r"\d+", linha):
            continue
        if re.fullmatch(r"\(\d+\)", linha):
            continue

        return linha

    return None


def buscar_time_posterior_cbf(linhas: List[str], indice_x: int, limite: int = 8) -> Optional[str]:
    for i in range(indice_x + 1, min(len(linhas), indice_x + limite + 1)):
        linha = linhas[i]

        if linha in {"X", "x"}:
            continue
        if eh_ruido_cbf(linha):
            continue
        if eh_data_hora_cbf(linha):
            continue
        if re.fullmatch(r"\d+", linha):
            continue
        if re.fullmatch(r"\(\d+\)", linha):
            continue

        return linha

    return None


def buscar_placar_proximo_cbf(linhas: List[str], indice_x: int) -> Optional[str]:
    placar_casa = None
    placar_fora = None

    for i in range(indice_x - 3, indice_x):
        if 0 <= i < len(linhas) and re.fullmatch(r"\d+", linhas[i]):
            placar_casa = linhas[i]

    for i in range(indice_x + 1, indice_x + 4):
        if 0 <= i < len(linhas) and re.fullmatch(r"\d+", linhas[i]):
            placar_fora = linhas[i]
            break

    if placar_casa is not None and placar_fora is not None:
        return f"{placar_casa} x {placar_fora}"

    return None


def parse_confrontos_cbf(linhas: List[str]) -> List[dict]:
    eventos = []

    for i, linha in enumerate(linhas):
        if linha not in {"X", "x"}:
            continue

        mandante = buscar_time_anterior_cbf(linhas, i)
        visitante = buscar_time_posterior_cbf(linhas, i)

        if not mandante or not visitante:
            continue

        data_utc = buscar_data_proxima_cbf(linhas, i)
        if not data_utc:
            continue

        resultado = buscar_placar_proximo_cbf(linhas, i)

        evento = criar_evento(
            competicao="Copa do Brasil",
            mandante=mandante,
            visitante=visitante,
            data_utc=data_utc,
            resultado=resultado,
            fonte=URLS["Copa do Brasil"],
            rodada=None,
        )
        eventos.append(evento)

    return eventos


def coletar_copa_do_brasil() -> List[dict]:
    print("[futebol] coletando Copa do Brasil via CBF...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URLS["Copa do Brasil"], wait_until="networkidle", timeout=60000)

        linhas = extrair_linhas_renderizadas(page)

        print(f"[futebol] Copa do Brasil: {len(linhas)} linhas renderizadas")
        print("[futebol] Copa do Brasil: primeiras 40 linhas:")
        for linha in linhas[:40]:
            print(f"  {linha}")

        eventos = parse_confrontos_cbf(linhas)
        browser.close()

    print(f"[futebol] Copa do Brasil: {len(eventos)} eventos coletados")
    for evento in eventos[:10]:
        print(f"[futebol] Copa do Brasil exemplo -> {evento}")

    return eventos


# =========================
# PRINCIPAL
# =========================

def gerar_futebol() -> List[dict]:
    eventos = []
    mapa_rodadas = carregar_rodadas_brasileirao()

    try:
        eventos.extend(coletar_copa_do_brasil())
    except Exception as e:
        print(f"[futebol] erro na Copa do Brasil: {e}")

    try:
        eventos.extend(coletar_brasileirao_espn(mapa_rodadas))
    except Exception as e:
        print(f"[futebol] erro no Brasileirão: {e}")

    eventos = [e for e in eventos if e.get("data_utc")]
    eventos = deduplicar(eventos)
    eventos.sort(key=lambda e: e["data_utc"])

    print(f"[futebol] total final: {len(eventos)}")
    for evento in eventos[:15]:
        print(f"[futebol] final -> {evento}")

    return eventos
