from datetime import datetime, timezone
from typing import List, Optional
from zoneinfo import ZoneInfo
import requests
import time

TZ_BRASIL = ZoneInfo("America/Sao_Paulo")
CURRENT_YEAR = datetime.now().year
API_BASE = "https://api.jolpi.ca/ergast/f1"

def fetch_json(url: str) -> dict:
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[f1] erro ao buscar {url}: {e}")
        return {}

def inferir_status(data_utc: datetime, resultado: Optional[str]) -> str:
    if resultado:
        return "resultado"
    if data_utc < datetime.now(timezone.utc):
        return "resultado"
    return "futuro"

def parse_sessao(
    nome_evento: str,
    tipo_sessao: str,
    date_str: str,
    time_str: str,
    circuito: str,
    cidade: str,
    pais: str,
    rodada: str,
    resultado: Optional[str] = None,
) -> Optional[dict]:
    try:
        time_str = time_str if time_str else "00:00:00Z"
        dt_str = f"{date_str}T{time_str}".replace("Z", "+00:00")
        data_utc = datetime.fromisoformat(dt_str)

        # Transmission by session type
        transmissao_map = {
            "Treino Livre 1": "Bandsports",
            "Treino Livre 2": "Bandsports",
            "Treino Livre 3": "Bandsports",
            "Classificação":  "Band / Bandsports",
            "Corrida":        "Band",
            "Sprint":         "Band / Bandsports",
            "Sprint Quali":   "Bandsports",
        }

        titulo = f"F1 {nome_evento} — {tipo_sessao}"

        return {
            "esporte": "Automobilismo",
            "competicao": "Formula 1",
            "titulo": titulo,
            "mandante": None,
            "visitante": None,
            "data_utc": data_utc.isoformat(),
            "status": inferir_status(data_utc, resultado),
            "resultado": resultado,
            "transmissao": transmissao_map.get(tipo_sessao, "Band / Bandsports"),
            "destaque": tipo_sessao == "Corrida",
            "fonte": "jolpi.ca/ergast/f1",
            "rodada": rodada,
            "estadio": circuito,
            "cidade": cidade,
            "uf": pais,
        }
    except Exception as e:
        print(f"[f1] erro ao parsear sessão {tipo_sessao}: {e}")
        return None


def coletar_calendario_f1() -> List[dict]:
    print("[f1] coletando calendário completo F1...")
    url = f"{API_BASE}/{CURRENT_YEAR}/races.json?limit=100"
    data = fetch_json(url)
    races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
    print(f"[f1] {len(races)} GPs encontrados")
    return races


def coletar_resultados_f1(races: List[dict]) -> dict:
    print("[f1] coletando resultados F1...")
    url = f"{API_BASE}/{CURRENT_YEAR}/results.json?limit=100"
    data = fetch_json(url)
    result_races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])

    resultados = {}
    for race in result_races:
        nome = race.get("raceName", "")
        results = race.get("Results", [])
        if results:
            top3 = [r["Driver"]["familyName"] for r in results[:3]]
            resultados[nome] = " / ".join(top3)

    return resultados


def coletar_sprint_races(races: List[dict]) -> dict:
    print("[f1] coletando resultados Sprint...")
    url = f"{API_BASE}/{CURRENT_YEAR}/sprint.json?limit=100"
    data = fetch_json(url)
    sprint_races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])

    sprints = {}
    for race in sprint_races:
        nome = race.get("raceName", "")
        results = race.get("SprintResults", [])
        if results:
            top3 = [r["Driver"]["familyName"] for r in results[:3]]
            sprints[nome] = " / ".join(top3)

    return sprints


def gerar_formula1() -> List[dict]:
    races = coletar_calendario_f1()
    resultados = coletar_resultados_f1(races)
    sprints = coletar_sprint_races(races)

    eventos = []

    for race in races:
        try:
            nome = race.get("raceName", "GP F1")
            circuito = race.get("Circuit", {}).get("circuitName", "")
            cidade = race.get("Circuit", {}).get("Location", {}).get("locality", "")
            pais = race.get("Circuit", {}).get("Location", {}).get("country", "")
            rodada = race.get("round", "")

            resultado_corrida = resultados.get(nome)
            resultado_sprint = sprints.get(nome)

            # Sessions map: key in API response → display name
            sessoes = [
                ("FirstPractice",  "Treino Livre 1"),
                ("SecondPractice", "Treino Livre 2"),
                ("ThirdPractice",  "Treino Livre 3"),
                ("SprintQualifying", "Sprint Quali"),
                ("Sprint",         "Sprint"),
                ("Qualifying",     "Classificação"),
            ]

            for chave_api, nome_sessao in sessoes:
                sessao = race.get(chave_api)
                if not sessao:
                    continue
                date_str = sessao.get("date", "")
                time_str = sessao.get("time", "00:00:00Z")
                if not date_str:
                    continue

                res = resultado_sprint if "Sprint" in nome_sessao else None
                evento = parse_sessao(
                    nome, nome_sessao, date_str, time_str,
                    circuito, cidade, pais, rodada, res
                )
                if evento:
                    eventos.append(evento)

            # Race itself
            evento_corrida = parse_sessao(
                nome, "Corrida",
                race.get("date", ""),
                race.get("time", "00:00:00Z"),
                circuito, cidade, pais, rodada,
                resultado_corrida
            )
            if evento_corrida:
                eventos.append(evento_corrida)

        except Exception as e:
            print(f"[f1] erro ao processar GP {race.get('raceName')}: {e}")

    eventos.sort(key=lambda e: e["data_utc"])
    print(f"[f1] total: {len(eventos)} sessões")
    return eventos
