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

def coletar_corridas_f1() -> List[dict]:
    print("[f1] coletando calendário F1...")
    url = f"{API_BASE}/{CURRENT_YEAR}/races.json"
    data = fetch_json(url)

    races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
    print(f"[f1] {len(races)} corridas encontradas")

    eventos = []
    for race in races:
        try:
            nome = race.get("raceName", "Corrida F1")
            circuito = race.get("Circuit", {})
            local = circuito.get("circuitName", "")
            cidade = circuito.get("Location", {}).get("locality", "")
            pais = circuito.get("Location", {}).get("country", "")

            date_str = race.get("date", "")
            time_str = race.get("time", "00:00:00Z")
            if not date_str:
                continue

            dt_str = f"{date_str}T{time_str}".replace("Z", "+00:00")
            data_utc = datetime.fromisoformat(dt_str)

            resultado = None
            eventos.append({
                "esporte": "Automobilismo",
                "competicao": "Formula 1",
                "titulo": nome,
                "mandante": None,
                "visitante": None,
                "data_utc": data_utc.isoformat(),
                "status": inferir_status(data_utc, resultado),
                "resultado": resultado,
                "transmissao": "Band / Bandsports",
                "destaque": False,
                "fonte": f"jolpi.ca/ergast/f1",
                "rodada": race.get("round"),
                "estadio": local,
                "cidade": cidade,
                "uf": pais,
            })
        except Exception as e:
            print(f"[f1] erro ao parsear corrida: {e}")

    return eventos

def coletar_resultados_f1() -> List[dict]:
    print("[f1] coletando resultados F1...")
    url = f"{API_BASE}/{CURRENT_YEAR}/results.json?limit=100"
    data = fetch_json(url)

    races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
    resultados = {}

    for race in races:
        nome = race.get("raceName", "")
        results = race.get("Results", [])
        if results:
            top3 = [r["Driver"]["familyName"] for r in results[:3]]
            resultados[nome] = " / ".join(top3)

    return resultados

def gerar_formula1() -> List[dict]:
    eventos = coletar_corridas_f1()
    resultados = coletar_resultados_f1()

    # Enrich with results where available
    for evento in eventos:
        nome = evento["titulo"]
        if nome in resultados:
            evento["resultado"] = resultados[nome]
            evento["status"] = "resultado"

    print(f"[f1] total: {len(eventos)} eventos")
    return eventos
