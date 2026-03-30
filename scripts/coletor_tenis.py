from datetime import datetime, timedelta, timezone

def gerar_tenis():
    agora = datetime.now(timezone.utc)

    partidas = [
        {
            "competicao": "Miami Open",
            "titulo": "João Fonseca vs Carlos Alcaraz",
            "data": agora + timedelta(days=1, hours=3),
            "transmissao": "ESPN / Disney+"
        },
        {
            "competicao": "Miami Open",
            "titulo": "Jannik Sinner vs Daniil Medvedev",
            "data": agora + timedelta(days=1, hours=7),
            "transmissao": "ESPN / Disney+"
        },
        {
            "competicao": "Monte Carlo Masters 1000",
            "titulo": "João Fonseca vs Casper Ruud",
            "data": agora + timedelta(days=15),
            "transmissao": "ESPN / Disney+"
        }
    ]

    eventos = []

    for partida in partidas:
        titulo_lower = partida["titulo"].lower()

        eventos.append({
            "esporte": "Tênis",
            "competicao": partida["competicao"],
            "titulo": partida["titulo"],
            "data_utc": partida["data"].isoformat(),
            "status": "futuro",
            "resultado": None,
            "transmissao": partida["transmissao"],
            "destaque": "joão fonseca" in titulo_lower or "joao fonseca" in titulo_lower,
            "fonte": "simulado_tenis"
        })

    return eventos
