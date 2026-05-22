from sheets.client import get_worksheet
from sheets.apostas import _parse_data_hora

_DIVISOR_FAMILIA: dict[str, int] = {
    "Camargo-Marques": 4,
    "Camargo-Kusters": 4,
    "Camargo-Camargo": 3,
    "Camargo-Lamunier": 2,
}


def buscar_ranking_familia() -> tuple[list[dict], dict | None]:
    ultima_atualizacao = _ultimo_jogo_atualizado()

    ws_apostadores = get_worksheet("apostadores")
    familias = list({
        str(r.get("família", "")).strip()
        for r in ws_apostadores.get_all_records()
        if str(r.get("família", "")).strip()
    })

    ws_bet = get_worksheet("bet")
    bets = ws_bet.get_all_records()

    stats: dict[str, dict] = {f: {"pontos": 0, "placar_mosca": 0, "resultado": 0} for f in familias}

    for b in bets:
        familia = str(b.get("família", "")).strip()
        if not familia or familia.startswith("#"):
            continue
        if familia not in stats:
            stats[familia] = {"pontos": 0, "placar_mosca": 0, "resultado": 0}
        stats[familia]["pontos"] += _to_int(b.get("pontos_totais", 0))
        if _to_int(b.get("ponto_placar", 0)) > 0:
            stats[familia]["placar_mosca"] += 1
        if _to_int(b.get("ponto_situacao", 0)) > 0:
            stats[familia]["resultado"] += 1

    for familia, dados in stats.items():
        divisor = _DIVISOR_FAMILIA.get(familia, 1)
        total = dados["pontos"]
        dados["pontos"] = round(total / divisor, 2) if total and divisor else 0

    ranking = [{"nome": familia, **dados} for familia, dados in stats.items()]
    ranking.sort(key=lambda x: x["pontos"], reverse=True)

    return ranking, ultima_atualizacao


def buscar_ranking() -> tuple[list[dict], dict | None]:
    ultima_atualizacao = _ultimo_jogo_atualizado()

    ws_apostadores = get_worksheet("apostadores")
    nomes = [r["nome"] for r in ws_apostadores.get_all_records() if str(r.get("nome", "")).strip()]

    ws_bet = get_worksheet("bet")
    bets = ws_bet.get_all_records()

    stats: dict[str, dict] = {n: {"pontos": 0, "placar_mosca": 0, "resultado": 0} for n in nomes}

    for b in bets:
        nome = str(b.get("nome", "")).strip()
        if nome not in stats:
            stats[nome] = {"pontos": 0, "placar_mosca": 0, "resultado": 0}
        stats[nome]["pontos"] += _to_int(b.get("pontos_totais", 0))
        if _to_int(b.get("ponto_placar", 0)) > 0:
            stats[nome]["placar_mosca"] += 1
        if _to_int(b.get("ponto_situacao", 0)) > 0:
            stats[nome]["resultado"] += 1

    ranking = [{"nome": nome, **dados} for nome, dados in stats.items() if nome]
    ranking.sort(key=lambda x: x["pontos"], reverse=True)

    return ranking, ultima_atualizacao


def _ultimo_jogo_atualizado() -> dict | None:
    ws = get_worksheet("jogos")
    ultimo_jogo = None
    ultima_dt = None
    for r in ws.get_all_records():
        gm = str(r.get("gols_mandante", "")).strip()
        gv = str(r.get("gols_visitante", "")).strip()
        if gm and gv:
            dt = _parse_data_hora(str(r.get("data_hora", "")))
            if dt and (ultima_dt is None or dt > ultima_dt):
                ultima_dt = dt
                ultimo_jogo = r
    return ultimo_jogo


def _to_int(val) -> int:
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0
