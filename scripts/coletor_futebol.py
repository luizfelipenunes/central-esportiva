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

    # Mantendo UTC para não mexer no seu gerar_saida.py
    dt = datetime(
        int(ano),
        int(mes),
        int(dia),
        int(hora),
        int(minuto),
        tzinfo=timezone.utc,
    )
    return dt, f"{hora}:{minuto}"


def limpar_time_placar_bruto(valor: str) -> str:
    valor = valor.replace(" .", ".")
    valor = valor.replace("·", "")
    valor = valor.replace("•", "")
    valor = valor.replace("  ", " ")
    return valor.strip()


def limpar_time(valor: str) -> str:
    valor = valor.strip()
    valor = re.sub(r"\s+", " ", valor)
    return valor


def parse_time_placar(valor: str) -> Tuple[str, Optional[int], Optional[int]]:
    """
    Exemplos:
    - Flamengo
    - Bahia2
    - Amé1(3)
    - Tir1(5)
    """
    valor = limpar_time_placar_bruto(valor)

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

    return limpar_time(valor), None, None


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

    for i, linha in enumerate(linhas):
        if not eh_jogo(linha):
            continue

        print(f"[futebol] {competicao}: encontrado bloco de jogo -> {linha}")

        idx_x = None
        for j in range(i - 1, max(-1, i - 8), -1):
            if linhas[j].upper() == "X":
                idx_x = j
                break

        if idx_x is None:
            print(f"[futebol] {competicao}: jogo ignorado porque não encontrou 'X' perto do bloco {linha}")
            continue

        if idx_x - 1 < 0 or idx_x + 1 >= len(linhas):
            print(f"[futebol] {competicao}: jogo ignorado por índice inválido no bloco {linha}")
            continue

        mandante_raw = linhas[idx_x - 1]
        visitante_raw = linhas[idx_x + 1]

        mandante, placar_mandante, _ = parse_time_placar(mandante_raw)
        visitante, placar_visitante, _ = parse_time_placar(visitante_raw)

        futuras = linhas[i + 1 : i + 6]

        data_utc = None
        if futuras:
            data_utc, _ = parse_data_hora(futuras[0])

        print(
            f"[futebol] {competicao}: mandante='{mandante_raw}' | visitante='{visitante_raw}' "
            f"| data_linha='{futuras[0] if futuras else None}' | data_utc='{data_utc}'"
        )

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
        print(f"[futebol] iniciando coleta: {competicao} -> {url}")

        try:
            html = baixar_html(url)
            print(f"[futebol] {competicao}: HTML baixado com sucesso ({len(html)} caracteres)")

            linhas = html_para_linhas(html)
            print(f"[futebol] {competicao}: {len(linhas)} linhas extraídas")

            print(f"[futebol] {competicao}: primeiras 30 linhas para diagnóstico:")
            for linha in linhas[:30]:
                print(f"  {linha}")

            eventos_comp = extrair_eventos_pagina(linhas, competicao, url)
            print(f"[futebol] {competicao}: {len(eventos_comp)} eventos extraídos antes do filtro")

            eventos.extend(eventos_comp)

        except Exception as e:
            print(f"[futebol] erro ao coletar {competicao}: {e}")
            raise

    print(f"[futebol] total antes de remover sem data: {len(eventos)}")

    eventos = [e for e in eventos if e.get("data_utc")]

    print(f"[futebol] total após remover sem data: {len(eventos)}")

    eventos = deduplicar(eventos)

    print(f"[futebol] total após deduplicação: {len(eventos)}")

    eventos.sort(key=lambda e: e["data_utc"])

    print("[futebol] exemplos finais:")
    for evento in eventos[:5]:
        print(f"[futebol] exemplo final: {evento}")

    return eventos
