import json
from datetime import datetime, timedelta

def gerar_futebol():

    agora = datetime.utcnow()

    eventos = []

    # EXEMPLO (depois vamos substituir por fonte real)
    jogos = [
        {
            "competicao": "Brasileirão",
            "titulo": "Vasco vs Palmeiras",
            "data": agora + timedelta(days=2)
        },
        {
            "competicao": "Brasileirão",
            "titulo": "Flamengo vs Santos",
            "data": agora + timedelta(days=3)
        }
    ]

    for j in jogos:

        eventos.append({
            "esporte": "Futebol",
            "competicao": j["competicao"],
            "titulo": j["titulo"],
            "data_utc": j["data"].isoformat(),
            "status": "futuro",
            "resultado": None,
            "destaque": "vasco" in j["titulo"].lower(),
            "fonte": "simulado"
        })

    return eventos
