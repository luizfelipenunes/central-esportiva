from datetime import datetime, timedelta, timezone

def gerar_futebol():
    agora = datetime.now(timezone.utc)

    jogos = [
        {
            "competicao": "Brasileirão",
            "titulo": "Vasco da Gama vs Palmeiras",
            "data": agora + timedelta(days=2, hours=1),
            "transmissao": "Globo / SporTV / Premiere"
        },
        {
            "competicao": "Brasileirão",
            "titulo": "Athletico Paranaense vs Botafogo",
            "data": agora + timedelta(days=5),
            "transmissao": "Globo / SporTV / Premiere"
        },
        {
            "competicao": "Copa do Brasil",
            "titulo": "Bahia vs Remo",
            "data": agora + timedelta(days=12),
            "transmissao": "Globo / SporTV / Prime Video"
        },
        {
            "competicao": "Libertadores",
            "titulo": "Independiente Rivadavia vs Bolívar",
            "data": agora + timedelta(days=10),
            "transmissao": "Globo / ESPN / Disney+"
        },
        {
            "competicao": "Sul-Americana",
            "titulo": "Barracas Central vs Vasco da Gama",
            "data": agora + timedelta(days=10, hours=2),
            "transmissao": "ESPN / Disney+"
        }
    ]

    eventos = []

    for jogo in jogos:
        titulo_lower = jogo["titulo"].lower()

        eventos.append({
            "esporte": "Futebol",
            "competicao": jogo["competicao"],
            "titulo": jogo["titulo"],
            "data_utc": jogo["data"].isoformat(),
            "status": "futuro",
            "resultado": None,
            "transmissao": jogo["transmissao"],
            "destaque": "vasco" in titulo_lower,
            "fonte": "simulado_futebol"
        })

    return eventos
