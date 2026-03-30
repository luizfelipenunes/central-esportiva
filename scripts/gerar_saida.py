import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from coletor_futebol import gerar_futebol
from coletor_tenis import gerar_tenis

TZ_BRASIL = ZoneInfo("America/Sao_Paulo")


def normalizar_evento(evento):
    data_utc = datetime.fromisoformat(evento["data_utc"])

    if data_utc.tzinfo is None:
        data_utc = data_utc.replace(tzinfo=timezone.utc)

    data_local = data_utc.astimezone(TZ_BRASIL)
    agora_local = datetime.now(timezone.utc).astimezone(TZ_BRASIL)

    dias_ate = (data_local.date() - agora_local.date()).days

    status = evento["status"]
    resultado = evento["resultado"]

    if data_local < agora_local:
        status = "resultado"
        if resultado is None:
            # resultado simulado só para a estrutura funcionar
            if evento["esporte"] == "Futebol":
                resultado = "2 x 1"
            elif evento["esporte"] == "Tênis":
                resultado = "6/4 3/6 6/3"
            else:
                resultado = "Encerrado"

    prioridade = 3

    if evento["esporte"] == "Futebol" and evento["destaque"]:
        prioridade = 1
    elif evento["esporte"] == "Tênis" and evento["destaque"]:
        prioridade = 1
    elif evento["esporte"] == "Automobilismo":
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
        "transmissao": evento["transmissao"],
        "prioridade": prioridade,
        "origem": evento["competicao"],
        "tipo": "evento",
        "destaque": evento["destaque"],
        "fonte": evento["fonte"]
    }


def gerar_base():
    base = []
    base.extend(gerar_futebol())
    base.extend(gerar_tenis())
    return [normalizar_evento(e) for e in base]


def gerar_eventos(base):
    return [
        e for e in base
        if e["status"] == "futuro" and 0 <= e["dias_ate"] <= 30
    ]


def gerar_resultados(base):
    return [
        e for e in base
        if e["status"] == "resultado" and -2 <= e["dias_ate"] <= 0
    ]


def ordenar(lista):
    return sorted(
        lista,
        key=lambda e: (
            e.get("prioridade", 999),
            e.get("data_ordem", "9999-99-99T99:99:99")
        )
    )


def salvar_json(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def main():
    base = gerar_base()
    eventos = ordenar(gerar_eventos(base))
    resultados = ordenar(gerar_resultados(base))

    salvar_json("data/base.json", base)
    salvar_json("data/eventos.json", eventos)
    salvar_json("data/resultados.json", resultados)

    print("Arquivos gerados com sucesso:")
    print(f"- base.json: {len(base)} registros")
    print(f"- eventos.json: {len(eventos)} registros")
    print(f"- resultados.json: {len(resultados)} registros")


if __name__ == "__main__":
    main()
