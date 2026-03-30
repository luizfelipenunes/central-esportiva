import re
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from playwright.sync_api import sync_playwright


CURRENT_YEAR = datetime.now().year

URLS = {
    "Brasileirão": f"https://www.cbf.com.br/futebol-brasileiro/tabelas/campeonato-brasileiro/serie-a/{CURRENT_YEAR}",
    "Copa do Brasil": f"https://www.cbf.com.br/futebol-brasileiro/tabelas/copa-do-brasil/masculino/{CURRENT_YEAR}",
}

TZ_BRASIL = timezone.utc  # usado só como fallback interno


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


def extrair_linhas_renderizadas(page) -> List[str]:
    texto = page.locator("body").inner_text(timeout=20000)
    linhas = [normalizar_texto(l) for l in texto.splitlines()]
    return [l for l in linhas if l]


def eh_data_hora(linha: str) -> bool:
    return bool(re.search(r"\d{2}/\d{2}/\d{4}\s*-\s*\d{2}:\d{2}", linha))


def parse_data_hora_para_utc(linha: str) -> Optional[datetime]:
    match = re.search(r"(\d{2})/(\d{2})/(\d{4})\s*-\s*(\d{2}):(\d{2})", linha)
    if not match:
        return None

    dia, mes, ano, hora, minuto = match.groups()

    # horário da CBF está em horário local do Brasil
    dt_local = datetime(
        int(ano),
        int(mes),
        int(dia),
        int(hora),
        int(minuto),
    )

    # considera horário de Brasília (-03:00) e converte para UTC
    dt_utc = dt_local.replace(
        tzinfo=timezone.utc
    ) - (datetime.now().astimezone().utcoffset() or datetime.now(timezone.utc).utcoffset() or datetime.timedelta())

    # fallback seguro: assume Brasília = UTC-3
    dt_utc = datetime(
        int(ano),
        int(mes),
        int(dia),
        int(hora) + 3,
        int(minuto),
        tzinfo=timezone.utc,
    )

    return dt_utc


def eh_ruido(linha: str) -> bool:
    ruídos_exatos = {
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
        "Classificação PTS J V E D GP GC SG CA CV % Recentes Próx",
        "Fases da competições",
        "Fases da competição",
        "GRUPO ÚNICO",
    }

    if linha in ruídos_exatos:
        return True

    if re.match(r"^\d+$", linha):
        return True

    if re.match(r"^\(\d+\)$", linha):
        return True

    if re.match(r"^(1ª|2ª|3ª|4ª)\s+Fase$", linha, re.IGNORECASE):
        return True

    if linha in {"Oitavas de Final", "Quartas de Final", "Semi Finais", "Semifinais", "Final"}:
        return True

    if re.match(r"^GRUPO\s+\d+$", linha, re.IGNORECASE):
        return True

    if linha in {"X", "x"}:
        return False

    if eh_data_hora(linha):
        return False

    return False


def limpar_time(valor: str) -> str:
    valor = valor.strip()
    valor = re.sub(r"\s+", " ", valor)
    return valor


def parse_time_placar_compacto(valor: str) -> Tuple[str, Optional[int], Optional[int]]:
    """
    Exemplos:
    - VOL
    - BAR
    - Flamengo
    - Bahia2
    - Amé1(3)
    """
    valor = limpar_time(valor)

    match = re.match(r"^(.*?)(\d+)\((\d+)\)$", valor)
    if match:
        time, gols, pens = match.groups()
        return limpar_time(time), int(gols), int(pens)

    match = re.match(r"^(.*?)(\d+)$", valor)
    if match:
        time, gols = match.groups()
        time = limpar_time(time)
        if time:
            return time, int(gols), None

    return valor, None, None


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


def buscar_data_proxima(linhas: List[str], indice_x: int, alcance: int = 12) -> Optional[datetime]:
    inicio = max(0, indice_x - alcance)
    fim = min(len(linhas), indice_x + alcance + 1)

    for i in range(inicio, fim):
        if eh_data_hora(linhas[i]):
            return parse_data_hora_para_utc(linhas[i])

    return None


def buscar_time_anterior(linhas: List[str], indice_x: int, limite: int = 6) -> Tuple[Optional[str], Optional[int]]:
    candidatos = []
    inicio = max(0, indice_x - limite)

    for i in range(inicio, indice_x):
        linha = linhas[i]
        if linha in {"X", "x"}:
            continue
        if eh_data_hora(linha):
            continue
        if eh_ruido(linha):
            continue
        candidatos.append((i, linha))

    if not candidatos:
        return None, None

    idx, valor = candidatos[-1]
    return valor, idx


def buscar_time_posterior(linhas: List[str], indice_x: int, limite: int = 6) -> Tuple[Optional[str], Optional[int]]:
    fim = min(len(linhas), indice_x + limite + 1)

    for i in range(indice_x + 1, fim):
        linha = linhas[i]
        if linha in {"X", "x"}:
            continue
        if eh_data_hora(linha):
            continue
        if eh_ruido(linha):
            continue
        return linha, i

    return None, None


def montar_resultado_proximo(linhas: List[str], idx_mandante: int, idx_visitante: int) -> Optional[str]:
    """
    Detecta placares espalhados em linhas próximas:
    VOL
    0
    (1)
    X
    BAR
    0
    (3)
    """
    placar_casa = None
    placar_fora = None

    for i in range(idx_mandante + 1, min(idx_mandante + 4, len(linhas))):
        if re.fullmatch(r"\d+", linhas[i]):
            placar_casa = linhas[i]
            break

    for i in range(idx_visitante + 1, min(idx_visitante + 4, len(linhas))):
        if re.fullmatch(r"\d+", linhas[i]):
            placar_fora = linhas[i]
            break

    if placar_casa is not None and placar_fora is not None:
        return f"{placar_casa} x {placar_fora}"

    return None


def parse_confrontos_generico(linhas: List[str], competicao: str, fonte: str) -> List[dict]:
    eventos = []

    for i, linha in enumerate(linhas):
        if linha not in {"X", "x"}:
            continue

        mandante_raw, idx_m = buscar_time_anterior(linhas, i)
        visitante_raw, idx_v = buscar_time_posterior(linhas, i)

        if not mandante_raw or not visitante_raw:
            continue

        mandante, _, _ = parse_time_placar_compacto(mandante_raw)
        visitante, _, _ = parse_time_placar_compacto(visitante_raw)

        if not mandante or not visitante:
            continue

        if mandante == visitante:
            continue

        data_utc = buscar_data_proxima(linhas, i, alcance=15)
        if not data_utc:
            continue

        resultado = None
        if idx_m is not None and idx_v is not None:
            resultado = montar_resultado_proximo(linhas, idx_m, idx_v)

        evento = montar_evento(
            competicao=competicao,
            mandante=mandante,
            visitante=visitante,
            data_utc=data_utc,
            resultado=resultado,
            fonte=fonte,
        )

        if evento:
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

    eventos = parse_confrontos_generico(linhas, competicao, url)
    print(f"[futebol] {competicao}: {len(eventos)} eventos extraídos antes da deduplicação")

    for evento in eventos[:5]:
        print(f"[futebol] {competicao}: exemplo -> {evento}")

    return eventos


def gerar_futebol():
    eventos = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for competicao, url in URLS.items():
            eventos.extend(coletar_competicao(page, competicao, url))

        browser.close()

    eventos = [e for e in eventos if e.get("data_utc")]
    eventos = deduplicar(eventos)
    eventos.sort(key=lambda e: e["data_utc"])

    print(f"[futebol] total final: {len(eventos)}")

    for evento in eventos[:10]:
        print(f"[futebol] final -> {evento}")

    if not eventos:
        raise RuntimeError(
            "Nenhum evento de futebol foi extraído. A estrutura da página pode ter mudado."
        )

    return eventos
