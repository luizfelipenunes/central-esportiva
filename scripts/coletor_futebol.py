import re
from datetime import datetime, timezone
from typing import List, Optional

from playwright.sync_api import sync_playwright


CURRENT_YEAR = datetime.now().year

URLS = {
    "Brasileirão": f"https://www.cbf.com.br/futebol-brasileiro/tabelas/campeonato-brasileiro/serie-a/{CURRENT_YEAR}",
    "Copa do Brasil": f"https://www.cbf.com.br/futebol-brasileiro/tabelas/copa-do-brasil/masculino/{CURRENT_YEAR}",
}


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


def parse_data_hora(linha: str) -> Optional[datetime]:
    match = re.search(r"(\d{2})/(\d{2})/(\d{4})\s*-\s*(\d{2}):(\d{2})", linha)
    if not match:
        return None

    dia, mes, ano, hora, minuto = match.groups()
    return datetime(
        int(ano),
        int(mes),
        int(dia),
        int(hora),
        int(minuto),
        tzinfo=timezone.utc,
    )


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


def montar_evento(
    competicao: str,
    mandante: str,
    visitante: str,
    data_utc: Optional[datetime],
    resultado: Optional[str],
    fonte: str,
) -> Optional[dict]:
    mandante = normalizar_texto(mandante)
    visitante = normalizar_texto(visitante)

    if not mandante or not visitante:
        return None

    titulo = f"{mandante} vs {visitante}"

    return {
        "esporte": "Futebol",
        "competicao": competicao,
        "titulo": titulo,
        "data_utc": data_utc.isoformat() if data_utc else None,
        "status": inferir_status(data_utc, resultado),
        "resultado": resultado,
        "transmissao": transmissao_padrao(competicao),
        "destaque": destacar_futebol(titulo),
        "fonte": fonte,
    }


def extrair_linhas_renderizadas(page) -> List[str]:
    texto = page.locator("body").inner_text(timeout=15000)
    linhas = [normalizar_texto(l) for l in texto.splitlines()]
    return [l for l in linhas if l]


def parse_blocos_jogos(linhas: List[str], competicao: str, fonte: str) -> List[dict]:
    eventos = []

    for i, linha in enumerate(linhas):
        if not re.match(r"^Jogo\s+\d+", linha, re.IGNORECASE):
            continue

        idx_x = None
        for j in range(i - 1, max(-1, i - 8), -1):
            if linhas[j].upper() == "X":
                idx_x = j
                break

        if idx_x is None or idx_x - 1 < 0 or idx_x + 1 >= len(linhas):
            continue

        mandante = linhas[idx_x - 1]
        visitante = linhas[idx_x + 1]

        futuras = linhas[i + 1 : i + 6]
        data_utc = parse_data_hora(futuras[0]) if futuras else None

        resultado = None
        evento = montar_evento(
            competicao=competicao,
            mandante=mandante,
            visitante=visitante,
            data_utc=data_utc,
            resultado=resultado,
            fonte=fonte,
        )
        if evento and evento["data_utc"]:
            eventos.append(evento)

    return eventos


def coletar_competicao(page, competicao: str, url: str) -> List[dict]:
    print(f"[futebol] abrindo {competicao}: {url}")
    page.goto(url, wait_until="networkidle", timeout=60000)

    linhas = extrair_linhas_renderizadas(page)

    print(f"[futebol] {competicao}: {len(linhas)} linhas renderizadas")
    print(f"[futebol] {competicao}: primeiras 40 linhas:")
    for linha in linhas[:40]:
        print(f"  {linha}")

    eventos = parse_blocos_jogos(linhas, competicao, url)
    print(f"[futebol] {competicao}: {len(eventos)} eventos extraídos")
    return eventos


def gerar_futebol():
    eventos = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for competicao, url in URLS.items():
            eventos.extend(coletar_competicao(page, competicao, url))

        browser.close()

    eventos = deduplicar(eventos)
    eventos.sort(key=lambda e: e["data_utc"])

    print(f"[futebol] total final: {len(eventos)}")

    if not eventos:
        raise RuntimeError(
            "Nenhum evento de futebol foi extraído da CBF. "
            "A estrutura da página pode ter mudado."
        )

    return eventos
