import re
from datetime import datetime, timezone
from typing import List, Optional, Tuple

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )
}

TIMEOUT = 30

URLS = {
    "Brasileirão": "https://www.cbf.com.br/futebol-brasileiro/tabelas/campeonato-brasileiro/serie-a",
    "Copa do Brasil": "https://www.cbf.com.br/futebol-brasileiro/tabelas/copa-do-brasil/masculino",
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


def baixar_html(url: str) -> str:
    resposta = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    resposta.raise_for_status()
    return resposta.text


def html_para_linhas(html: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    texto = soup.get_text("\n")
    texto = normalizar_texto(texto)

    linhas = []
    for linha in texto.splitlines():
        linha = normalizar_texto(linha)
        if not linha:
            continue

        # ruídos comuns
        if linha in {
            "Image",
            "Veja também",
            "Documentos da competição",
            "Fases da competições",
            "Fases da competição",
        }:
            continue

        if "Política de Privacidade" in linha:
            continue
        if "Todos os direitos reservados" in linha:
            continue
        if linha == "CBF - Confederação Brasileira de Futebol":
            continue

        linhas.append(linha)

    return linhas


def eh_rodada(linha: str) -> bool:
    return bool(re.match(r"^Rodada\s+\d+$", linha, re.IGNORECASE))


def eh_grupo(linha: str) -> bool:
    return bool(re.match(r"^GRUPO\s+.+$", linha, re.IGNORECASE))


def eh_jogo(linha: str) -> bool:
    return bool(re.match(r"^Jogo\s+\d+", linha, re.IGNORECASE))


def eh_fase(linha: str) -> bool:
    fases = {
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
        "Preliminar",
        "PRELIMINAR",
    }
    return linha in fases


def parse_data_hora(linha: str) -> Tuple[Optional[datetime], Optional[str]]:
    match = re.search(r"(\d{2})/(\d{2})/(\d{4})\s*-\s*(\d{2}):(\d{2})", linha)
    if not match:
        return None, None

    dia, mes, ano, hora, minuto = match.groups()
    dt = datetime(
        int(ano),
        int(mes),
        int(dia),
        int(hora),
        int(minuto),
        tzinfo=timezone.utc,  # será convertido no gerar_saida.py
    )
    return dt, f"{hora}:{minuto}"


def parse_local(linha: str) -> Tuple[Optional[str], Optional[str]]:
    match = re.match(r"(.+?)\s*-\s*([A-Z]{2})$", linha)
    if match:
        cidade, uf = match.groups()
        return cidade.strip(), uf.strip()
    return linha.strip(), None


def limpar_time(valor: str) -> str:
    valor = valor.strip()
    valor = re.sub(r"\s+", " ", valor)
    return valor


def parse_time_placar(valor: str) -> Tuple[str, Optional[int], Optional[int]]:
    """
    Exemplos da CBF:
    - 'Flamengo'
    - 'Bah2'
    - 'Amé1(3)'
    - 'Tir1(5)'
    """
    valor = limpar_time_placar_bruto(valor)

    # gols + pênaltis
    match = re.match(r"^(.*?)(\d+)\((\d+)\)$", valor)
    if match:
        time, gols, pens = match.groups()
        return limpar_time(time), int(gols), int(pens)

    # só gols
    match = re.match(r"^(.*?)(\d+)$", valor)
    if match:
        time, gols = match.groups()
        time = limpar_time(time)
        if time:
            return time, int(gols), None

    return limpar_time(valor), None, None


def limpar_time_placar_bruto(valor: str) -> str:
    valor = valor.replace(" .", ".")
    valor = valor.replace("·", "")
    valor = valor.replace("•", "")
    valor = valor.replace("  ", " ")
    return valor.strip()


def inferir_status(data_utc: Optional[datetime], placar_mandante: Optional[int], placar_visitante: Optional[int]) -> str:
    if placar_mandante is not None and placar_visitante is not None:
        return "resultado"

    if data_utc is not None and data_utc < datetime.now(timezone.utc):
        return "resultado"

    return "futuro"


def deduplicar(eventos: List[dict]) -> List[dict]:
    vistos = set()
    unicos = []

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
        unicos.append(evento)

    return unicos


def destaque_futebol(titulo: str) -> bool:
    return "vasco" in titulo.lower()


def transmissao_padrao(competicao: str) -> str:
    if competicao == "Brasileirão":
        return "A confirmar"
    if competicao == "Copa do Brasil":
        return "A confirmar"
    return "A confirmar"


def montar_evento(
    competicao: str,
    mandante: str,
    visitante: str,
    data_utc: Optional[datetime],
    placar_mandante: Optional[int],
    placar_visitante: Optional[int],
    fonte_url: str,
) -> Optional[dict]:
    if not mandante or not visitante:
        return None

    titulo = f"{mandante} vs {visitante}"
    resultado = None

    if placar_mandante is not None and placar_visitante is not None:
        resultado = f"{placar_mandante} x {placar_visitante}"

    return {
        "esporte": "Futebol",
        "competicao": competicao,
        "titulo": titulo,
        "data_utc": data_utc.isoformat() if data_utc else None,
        "status": inferir_status(data_utc, placar_mandante, placar_visitante),
        "resultado": resultado,
        "transmissao": transmissao_padrao(competicao),
        "destaque": destaque_futebol(titulo),
        "fonte": fonte_url,
    }


def extrair_eventos_pagina(linhas: List[str], competicao: str, fonte_url: str) -> List[dict]:
    eventos = []

    fase_atual = None
    rodada_atual = None
    grupo_atual = None

    for i, linha in enumerate(linhas):
        if eh_fase(linha):
            fase_atual = linha
            continue

        if eh_rodada(linha):
            rodada_atual = linha
            continue

        if eh_grupo(linha):
            grupo_atual = linha
            continue

        if not eh_jogo(linha):
            continue

        # procura o X imediatamente acima do bloco do jogo
        idx_x = None
        for j in range(i - 1, max(-1, i - 8), -1):
            if linhas[j].upper() == "X":
                idx_x = j
                break

        if idx_x is None:
            continue

        if idx_x - 1 < 0 or idx_x + 1 >= len(linhas):
            continue

        mandante_raw = linhas[idx_x - 1]
        visitante_raw = linhas[idx_x + 1]

        mandante, placar_mandante, _ = parse_time_placar(mandante_raw)
        visitante, placar_visitante, _ = parse_time_placar(visitante_raw)

        # bloco à frente do "Jogo"
        futuras = linhas[i + 1 : i + 6]

        data_utc = None
        if futuras:
            data_utc, _ = parse_data_hora(futuras[0])

        evento = montar_evento(
            competicao=competicao,
            mandante=mandante,
            visitante=visitante,
            data_utc=data_utc,
            placar_mandante=placar_mandante,
            placar_visitante=placar_visitante,
            fonte_url=fonte_url,
        )

        if evento:
            eventos.append(evento)

    return eventos


def gerar_futebol():
    eventos = []

    for competicao, url in URLS.items():
        try:
            html = baixar_html(url)
            linhas = html_para_linhas(html)
            eventos.extend(extrair_eventos_pagina(linhas, competicao, url))
        except Exception as e:
            print(f"[futebol] erro ao coletar {competicao}: {e}")

    # remove itens sem data
    eventos = [e for e in eventos if e.get("data_utc")]

    # remove duplicados
    eventos = deduplicar(eventos)

    # ordena por data
    eventos.sort(key=lambda e: e["data_utc"])

    return eventos
