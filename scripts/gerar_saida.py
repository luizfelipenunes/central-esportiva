import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from coletor_futebol import gerar_futebol
from coletor_tenis import gerar_tenis
from coletor_formula1 import gerar_formula1

TZ_BRASIL = ZoneInfo("America/Sao_Paulo")

BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "data" / "db"
DB_EVENTOS_FILE = DB_DIR / "eventos.json"


def normalizar_evento(evento):
    data_utc = datetime.fromisoformat(evento["data_utc"])
    if data_utc.tzinfo is None:
        data_utc = data_utc.replace(tzinfo=timezone.utc)

    data_local = data_utc.astimezone(TZ_BRASIL)
    agora_local = datetime.now(timezone.utc).astimezone(TZ_BRASIL)
    dias_ate = (data_local.date() - agora_local.date()).days

    status = evento["status"]
    resultado = evento.get("resultado")

    if data_local < agora_local and status == "futuro":
        status = "resultado"

    prioridade = 3
    if evento.get("destaque"):
        prioridade = 1
    elif evento["esporte"] in ["Automobilismo"]:
        prioridade = 2
    elif evento["esporte"] in ["NBA", "NFL"]:
        prioridade = 2

    return {
        "esporte": evento["esporte"],
        "competicao": evento["competicao"],
        "titulo": evento["titulo"],
        "data": data_local.strftime("%d/%m"),
        "hora": data_local.strftime("%H:%M"),
        "data_ordem": data_local.isoformat(),
        "dias_ate": dias_ate,
        "status": status,
        "resultado": resultado,
        "transmissao": evento.get("transmissao"),
        "prioridade": prioridade,
        "origem": evento["competicao"],
        "tipo": "evento",
        "destaque": evento.get("destaque", False),
        "fonte": evento.get("fonte"),
        "rodada": evento.get("rodada"),
        "mandante": evento.get("mandante"),
        "visitante": evento.get("visitante"),
        "estadio": evento.get("estadio"),
        "cidade": evento.get("cidade"),
        "uf": evento.get("uf"),
    }


def salvar_json(caminho, dados):
    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def gerar_base_bruta():
    base = []
    base.extend(gerar_futebol())
    base.extend(gerar_formula1())
    base.extend(gerar_tenis())
    return base


def gerar_eventos(base):
    # Standard 30-day window for all sports
    eventos = [
        e for e in base
        if e["status"] == "futuro" and 0 <= e["dias_ate"] <= 30
    ]

    # Always include the next F1 GP weekend even if beyond 30 days
    f1_futuros = [
        e for e in base
        if e["esporte"] == "Automobilismo"
        and e["status"] == "futuro"
        and e["dias_ate"] > 30
    ]

    print(f"[debug] f1_futuros count: {len(f1_futuros)}")
    if f1_futuros:
        primeiro = min(f1_futuros, key=lambda e: e["dias_ate"])
        print(f"[debug] proximo round: {primeiro.get('rodada')}, dias_ate: {primeiro.get('dias_ate')}, titulo: {primeiro.get('titulo')}")
        proximo_round = primeiro.get("rodada")
        proximo_gp = [e for e in f1_futuros if e.get("rodada") == proximo_round]
        print(f"[debug] sessoes do proximo GP: {len(proximo_gp)}")
        eventos.extend(proximo_gp)

    return eventos


def gerar_resultados(base):
    return [
        e for e in base
        if e["status"] == "resultado" and -3 <= e["dias_ate"] <= 0
    ]


def ordenar(lista):
    return sorted(lista, key=lambda e: (
        e.get("prioridade", 999),
        e.get("data_ordem", "9999-99-99T99:99:99")
    ))


def main():
    base_bruta = gerar_base_bruta()

    DB_DIR.mkdir(parents=True, exist_ok=True)
    salvar_json(DB_EVENTOS_FILE, base_bruta)

    base = [normalizar_evento(e) for e in base_bruta]

    # Filter out broken entries with no team names
    base = [e for e in base if e["titulo"] != "None vs None"]

    eventos = ordenar(gerar_eventos(base))
    resultados = ordenar(gerar_resultados(base))

    salvar_json("data/base.json", base)
    salvar_json("data/eventos.json", eventos)
    salvar_json("data/resultados.json", resultados)

    print(f"\n✅ Arquivos gerados:")
    print(f"   data/db/eventos.json : {len(base_bruta)} registros")
    print(f"   data/base.json       : {len(base)} registros")
    print(f"   data/eventos.json    : {len(eventos)} registros")
    print(f"   data/resultados.json : {len(resultados)} registros")


if __name__ == "__main__":
    main()
