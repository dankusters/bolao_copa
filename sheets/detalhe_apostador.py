from sheets.client import get_worksheet


def buscar_nomes_apostadores() -> list[str]:
    ws = get_worksheet("apostadores")
    return [
        r["nome"]
        for r in ws.get_all_records()
        if str(r.get("nome", "")).strip()
    ]


def buscar_extrato_apostador(nome: str) -> list[dict]:
    ws_bet = get_worksheet("bet")
    bets = [
        b for b in ws_bet.get_all_records()
        if str(b.get("nome", "")).strip().lower() == nome.strip().lower()
    ]
    if not bets:
        return []

    ws_jogos = get_worksheet("jogos")
    jogos_map = {
        str(r["id_jogo"]): r
        for r in ws_jogos.get_all_records()
        if str(r.get("id_jogo", "")).strip()
    }

    resultado = []
    for b in bets:
        jogo = jogos_map.get(str(b.get("id_jogo", "")).strip())
        if not jogo:
            continue
        if not str(jogo.get("gols_mandante", "")).strip() or not str(jogo.get("gols_visitante", "")).strip():
            continue
        resultado.append({"bet": b, "jogo": jogo})

    return resultado
