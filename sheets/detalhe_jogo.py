from sheets.client import get_worksheet
from sheets.apostas import _parse_data_hora, _eh_jogo_do_dia


def buscar_apostas_do_dia() -> list[dict]:
    """Retorna todos os jogos do dia com as apostas de cada um, independente de resultado."""
    ws_jogos = get_worksheet("jogos")
    jogos_hoje = []

    for r in ws_jogos.get_all_records():
        dt = _parse_data_hora(str(r.get("data_hora", "")))
        if dt and _eh_jogo_do_dia(dt):
            jogos_hoje.append(r)

    if not jogos_hoje:
        return []

    ws_bet = get_worksheet("bet")
    bets = ws_bet.get_all_records()
    ids_hoje = {str(j["id_jogo"]) for j in jogos_hoje}
    bets_hoje = [b for b in bets if str(b.get("id_jogo", "")).strip() in ids_hoje]

    resultado = []
    for jogo in jogos_hoje:
        id_jogo = str(jogo["id_jogo"])
        apostas_jogo = [b for b in bets_hoje if str(b.get("id_jogo", "")).strip() == id_jogo]
        resultado.append({"jogo": jogo, "apostas": apostas_jogo})

    return resultado


def buscar_detalhe_por_jogo(limite: int = 6) -> list[dict]:
    """Retorna os últimos jogos atualizados com resultado, com as apostas de cada um."""
    ws_jogos = get_worksheet("jogos")
    jogos_com_resultado = []

    for r in ws_jogos.get_all_records():
        dt = _parse_data_hora(str(r.get("data_hora", "")))
        if not dt:
            continue
        gm = str(r.get("gols_mandante", "")).strip()
        gv = str(r.get("gols_visitante", "")).strip()
        if gm and gv:
            jogos_com_resultado.append((dt, r))

    if not jogos_com_resultado:
        return []

    jogos_com_resultado.sort(key=lambda x: x[0])
    jogos_recentes = [r for _, r in jogos_com_resultado[-limite:]]

    ws_bet = get_worksheet("bet")
    bets = ws_bet.get_all_records()
    ids = {str(j["id_jogo"]) for j in jogos_recentes}
    bets_filtrados = [b for b in bets if str(b.get("id_jogo", "")).strip() in ids]

    resultado = []
    for jogo in jogos_recentes:
        id_jogo = str(jogo["id_jogo"])
        apostas_jogo = [b for b in bets_filtrados if str(b.get("id_jogo", "")).strip() == id_jogo]
        resultado.append({"jogo": jogo, "apostas": apostas_jogo})

    return resultado
