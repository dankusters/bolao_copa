from datetime import date
from sheets.client import get_worksheet
from sheets.apostas import _parse_data_hora


def buscar_detalhe_por_jogo() -> list[dict]:
    """Retorna jogos do dia que já têm resultado, com as apostas de cada um."""
    ws_jogos = get_worksheet("jogos")
    hoje = date.today()
    jogos_hoje_com_resultado = []

    for r in ws_jogos.get_all_records():
        dt = _parse_data_hora(str(r.get("data_hora", "")))
        if not dt or dt.date() != hoje:
            continue
        gm = str(r.get("gols_mandante", "")).strip()
        gv = str(r.get("gols_visitante", "")).strip()
        if gm and gv:
            jogos_hoje_com_resultado.append(r)

    if not jogos_hoje_com_resultado:
        return []

    ws_bet = get_worksheet("bet")
    bets = ws_bet.get_all_records()
    ids_hoje = {str(j["id_jogo"]) for j in jogos_hoje_com_resultado}
    bets_hoje = [b for b in bets if str(b.get("id_jogo", "")).strip() in ids_hoje]

    resultado = []
    for jogo in jogos_hoje_com_resultado:
        id_jogo = str(jogo["id_jogo"])
        apostas_jogo = [b for b in bets_hoje if str(b.get("id_jogo", "")).strip() == id_jogo]
        resultado.append({"jogo": jogo, "apostas": apostas_jogo})

    return resultado
